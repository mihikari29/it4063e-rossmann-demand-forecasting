"""Run the approved Phase 6 tuning and development-only LightGBM backtest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from rossmann_forecasting.data.acquisition import sha256_file
from rossmann_forecasting.data.paths import repository_root
from rossmann_forecasting.data.preparation import SOURCE_SNAPSHOT_SHA256
from rossmann_forecasting.features.contract import (
    FEATURE_CONTRACT_VERSION,
    PREDICTOR_COLUMNS,
    PREDICTOR_DTYPES,
    predictor_schema,
)
from rossmann_forecasting.forecasting.lightgbm import (
    CATEGORICAL_COLUMNS,
    FIXED_PARAMETERS,
    FORECAST_COLUMN,
    FUTURE_COVARIATE_COLUMNS,
    MODEL_NAME,
    InvalidFeatureSchema,
    fit_lightgbm,
    prepare_training_data,
    recursive_lightgbm_forecasts,
)
from rossmann_forecasting.forecasting.lightgbm_evaluation import (
    INNER_WINDOW,
    attach_lightgbm_labels,
    compare_development_baselines,
    summarize_lightgbm_development,
    tune_global_lightgbm,
)
from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics
from rossmann_forecasting.forecasting.runner import (
    _read_development_history,
    _repository_path,
)
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
)

_PROCESSED_RELATIVE_DIR = Path("data") / "processed" / "lightgbm"
_MODEL_RELATIVE_DIR = Path("artifacts") / "lightgbm"
_PROCESSED_OUTPUT_NAMES = (
    "configuration.json",
    "tuning_results.csv",
    "inner_validation_forecasts.parquet",
    "fit_diagnostics.csv",
    "internal_recursive_paths.parquet",
    "development_forecasts.parquet",
    "metrics_by_window.csv",
    "metrics_pooled.json",
    "metrics_by_horizon.csv",
    "coverage_guardrail.json",
    "clipping_diagnostics.csv",
    "paired_vs_seasonal_naive_forecasts.parquet",
    "paired_vs_seasonal_naive_metrics.csv",
    "paired_vs_holt_winters_forecasts.parquet",
    "paired_vs_holt_winters_metrics.csv",
    "manifest.json",
)
_MODEL_OUTPUT_NAMES = tuple(f"model_{window.name}.txt" for window in APPROVED_DEVELOPMENT_WINDOWS)


def _date_expression(dataset: ds.Dataset, start: pd.Timestamp | None, end: pd.Timestamp):
    date_type = dataset.schema.field("Date").type
    expression = ds.field("Date") <= pa.scalar(end.to_pydatetime(), type=date_type)
    if start is not None:
        expression = expression & (
            ds.field("Date") >= pa.scalar(start.to_pydatetime(), type=date_type)
        )
    return expression


def _read_censored_parquet(
    path: Path,
    *,
    columns: tuple[str, ...] | list[str],
    start: pd.Timestamp | None = None,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Project and date-filter a Parquet input before its rows reach modeling code."""

    dataset = ds.dataset(path, format="parquet")
    missing = set(columns).difference(dataset.schema.names)
    if missing:
        raise ValueError(f"{path.name} is missing projected columns: {sorted(missing)}.")
    table = dataset.to_table(columns=list(columns), filter=_date_expression(dataset, start, end))
    result = table.to_pandas()
    if "Date" in result:
        result["Date"] = pd.to_datetime(result["Date"], errors="raise").dt.normalize()
        if result["Date"].gt(LAST_DEVELOPMENT_DATE).any():
            raise AssertionError("A censored Phase 6 read exposed a final-holdout date.")
        if start is not None and result["Date"].lt(start).any():
            raise AssertionError(
                "A censored Phase 6 read exposed a row before its requested start."
            )
    return result


def _dataframe_sha256(frame: pd.DataFrame) -> str:
    schema = json.dumps(
        [(column, str(frame[column].dtype)) for column in frame.columns],
        separators=(",", ":"),
    ).encode("utf-8")
    values = pd.util.hash_pandas_object(frame, index=False, categorize=True).to_numpy(
        dtype=np.uint64
    )
    return hashlib.sha256(schema + values.tobytes()).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.bool_, np.integer, np.floating)):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_json_safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _assert_ignored(root: Path, relative_paths: list[Path]) -> None:
    for relative_path in relative_paths:
        relative = relative_path.as_posix()
        check = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", relative],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            raise RuntimeError(f"Refusing to write non-ignored Phase 6 artifact: {relative}")


class _InnerForecastWriter:
    """Append checkpoint forecasts as Parquet row groups without retaining all trials in RAM."""

    _COLUMNS = (
        "trial",
        "checkpoint_round",
        "Store",
        "forecast_origin",
        "Date",
        "horizon",
        "model_forecast_unclipped",
        FORECAST_COLUMN,
        "forecast_was_clipped",
        "operational_forecast",
        "actual_sales",
        "source_open",
        "forecast_available",
        "primary_evaluation_eligible",
        "validation_window",
        "unavailable_reason",
    )

    def __init__(self, path: Path) -> None:
        self.path = path
        self.writer: pq.ParquetWriter | None = None

    def append(
        self,
        trial: str,
        checkpoint_round: int,
        raw_path: pd.DataFrame,
        evaluated: pd.DataFrame,
    ) -> None:
        del raw_path  # The evaluated rows retain only target keys from the complete path.
        rows = evaluated.copy()
        rows["trial"] = trial
        rows["checkpoint_round"] = checkpoint_round
        rows["Store"] = pd.to_numeric(rows["Store"], errors="raise").astype("int64")
        rows["checkpoint_round"] = rows["checkpoint_round"].astype("int16")
        rows["horizon"] = rows["horizon"].astype("int8")
        for column in (
            "model_forecast_unclipped",
            FORECAST_COLUMN,
            "operational_forecast",
            "actual_sales",
            "source_open",
        ):
            rows[column] = pd.to_numeric(rows[column], errors="coerce").astype("float64")
        rows["forecast_was_clipped"] = rows["forecast_was_clipped"].astype("boolean")
        for column in ("forecast_available", "primary_evaluation_eligible"):
            rows[column] = rows[column].astype(bool)
        rows["trial"] = rows["trial"].astype("string")
        rows["validation_window"] = rows["validation_window"].astype("string")
        rows["unavailable_reason"] = rows["unavailable_reason"].astype("string")
        table = pa.Table.from_pandas(rows.loc[:, self._COLUMNS], preserve_index=False)
        if self.writer is None:
            self.writer = pq.ParquetWriter(self.path, table.schema, compression="zstd")
        else:
            table = table.cast(self.writer.schema)
        self.writer.write_table(table)

    def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        elif not self.path.exists():
            empty = pd.DataFrame(
                {
                    "trial": pd.Series(dtype="string"),
                    "checkpoint_round": pd.Series(dtype="int16"),
                    "Store": pd.Series(dtype="int64"),
                    "forecast_origin": pd.Series(dtype="datetime64[ns]"),
                    "Date": pd.Series(dtype="datetime64[ns]"),
                    "horizon": pd.Series(dtype="int8"),
                    "model_forecast_unclipped": pd.Series(dtype="float64"),
                    FORECAST_COLUMN: pd.Series(dtype="float64"),
                    "forecast_was_clipped": pd.Series(dtype="boolean"),
                    "operational_forecast": pd.Series(dtype="float64"),
                    "actual_sales": pd.Series(dtype="float64"),
                    "source_open": pd.Series(dtype="float64"),
                    "forecast_available": pd.Series(dtype="bool"),
                    "primary_evaluation_eligible": pd.Series(dtype="bool"),
                    "validation_window": pd.Series(dtype="string"),
                    "unavailable_reason": pd.Series(dtype="string"),
                }
            )
            empty.to_parquet(self.path, engine="pyarrow", index=False, compression="zstd")


def _read_training_features(features_path: Path, origin: pd.Timestamp) -> pd.DataFrame:
    columns = [*PREDICTOR_COLUMNS, "Date", "Sales", "Open", "training_label_eligible"]
    rows = _read_censored_parquet(
        features_path,
        columns=columns,
        end=origin,
    )
    try:
        for column, dtype in PREDICTOR_DTYPES.items():
            rows[column] = rows[column].astype(dtype)
    except (TypeError, ValueError) as error:
        raise InvalidFeatureSchema(
            "Parquet predictor values cannot restore phase-3-v1 dtypes."
        ) from error
    return rows


def _read_actual_history(train_path: Path, origin: pd.Timestamp) -> pd.DataFrame:
    return _read_censored_parquet(
        train_path,
        columns=("Store", "Date", "Sales"),
        end=origin,
    )


def _read_future_covariates(train_path: Path) -> pd.DataFrame:
    return _read_censored_parquet(
        train_path,
        columns=FUTURE_COVARIATE_COLUMNS,
        start=INNER_WINDOW.target_start,
        end=LAST_DEVELOPMENT_DATE,
    )


def _read_target_keys(train_path: Path, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return _read_censored_parquet(
        train_path,
        columns=("Store", "Date"),
        start=start,
        end=end,
    )


def _read_target_labels(train_path: Path, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return _read_censored_parquet(
        train_path,
        columns=("Store", "Date", "Sales", "Open"),
        start=start,
        end=end,
    )


def _input_snapshot_identifiers(interim_dir: Path, processed_dir: Path) -> dict[str, Any]:
    preparation_path = interim_dir / "preparation_manifest.json"
    feature_path = processed_dir / "feature_manifest.json"
    if not preparation_path.is_file() or not feature_path.is_file():
        raise FileNotFoundError(
            "Phase 2 and Phase 3 manifests are required for Phase 6 provenance."
        )
    preparation = json.loads(preparation_path.read_text(encoding="utf-8"))
    features = json.loads(feature_path.read_text(encoding="utf-8"))
    source_hashes = preparation.get("source_sha256")
    if source_hashes != SOURCE_SNAPSHOT_SHA256:
        raise ValueError("Recorded Phase 2 source snapshot differs from the approved snapshot.")
    return {
        "phase2_source_snapshot_sha256": source_hashes,
        "phase2_train_snapshot_sha256": preparation.get("outputs", {})
        .get("train.parquet", {})
        .get("sha256"),
        "phase3_feature_snapshot_sha256": features.get("outputs", {})
        .get("features_train.parquet", {})
        .get("sha256"),
        "source_manifest_command": preparation.get("command"),
        "feature_manifest_contract": features.get("feature_contract_version"),
    }


def _git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _working_tree_source_sha256(root: Path) -> str:
    """Identify the exact dirty source tree used by a pre-commit development run."""

    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()
    digest = hashlib.sha256(diff)
    for relative in sorted(untracked):
        path = root / relative
        if path.is_file():
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _normalize_diagnostic_dicts(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        if result[column].map(lambda value: isinstance(value, dict)).any():
            result[column] = result[column].map(
                lambda value: (
                    json.dumps(_json_safe(value), sort_keys=True)
                    if isinstance(value, dict)
                    else value
                )
            )
    return result


def _clipping_diagnostics(paths: pd.DataFrame) -> pd.DataFrame:
    groups: list[tuple[str, str | None, pd.DataFrame]] = [
        ("validation_window", window.name, paths.loc[paths["validation_window"].eq(window.name)])
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    groups.append(("pooled_development", None, paths))
    rows: list[dict[str, Any]] = []
    for scope, window, subset in groups:
        available = pd.to_numeric(subset["model_forecast_unclipped"], errors="coerce").notna()
        clipped = subset["forecast_was_clipped"].fillna(False).astype(bool)
        rows.append(
            {
                "scope": scope,
                "validation_window": window,
                "recursive_path_rows": len(subset),
                "finite_predictions": int(available.sum()),
                "clipped_predictions": int(clipped.sum()),
                "clipped_rate_of_finite": float(clipped.sum() / available.sum())
                if available.any()
                else None,
                "minimum_unclipped_prediction": float(
                    pd.to_numeric(
                        subset.loc[available, "model_forecast_unclipped"], errors="coerce"
                    ).min()
                )
                if available.any()
                else None,
            }
        )
    return pd.DataFrame(rows)


def run_lightgbm_development_backtest(
    *,
    interim_dir: str | Path | None = None,
    processed_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run Phase 6's frozen finite tuning and three outer origins; never read the holdout."""

    root = repository_root()
    resolved_interim = _repository_path(interim_dir, root / "data" / "interim")
    resolved_processed = _repository_path(processed_dir, root / "data" / "processed")
    train_path = resolved_interim / "train.parquet"
    features_path = resolved_processed / "features_train.parquet"
    processed_output = root / _PROCESSED_RELATIVE_DIR
    model_output = root / _MODEL_RELATIVE_DIR
    ignored_paths = [
        _PROCESSED_RELATIVE_DIR,
        *(_PROCESSED_RELATIVE_DIR / name for name in _PROCESSED_OUTPUT_NAMES),
        _MODEL_RELATIVE_DIR,
        *(_MODEL_RELATIVE_DIR / name for name in _MODEL_OUTPUT_NAMES),
    ]
    _assert_ignored(root, ignored_paths)
    if not train_path.is_file() or not features_path.is_file():
        raise FileNotFoundError("Prepared Phase 2 train and Phase 3 feature Parquet are required.")
    snapshot_identifiers = _input_snapshot_identifiers(resolved_interim, resolved_processed)
    if snapshot_identifiers["feature_manifest_contract"] != FEATURE_CONTRACT_VERSION:
        raise ValueError("Phase 3 artifact does not identify the frozen phase-3-v1 contract.")

    input_hashes: dict[str, Any] = {}
    inner_training = _read_training_features(features_path, INNER_WINDOW.forecast_origin)
    inner_history = _read_actual_history(train_path, INNER_WINDOW.forecast_origin)
    future_covariates = _read_future_covariates(train_path)
    inner_keys = _read_target_keys(
        train_path,
        INNER_WINDOW.target_start,
        INNER_WINDOW.target_end,
    )
    input_hashes["inner_training_through_2015_04_24"] = _dataframe_sha256(inner_training)
    input_hashes["inner_actual_history_through_2015_04_24"] = _dataframe_sha256(inner_history)
    input_hashes["future_covariates_2015_04_25_through_2015_07_03"] = _dataframe_sha256(
        future_covariates
    )
    input_hashes["inner_requested_keys_2015_04_25_through_2015_05_08"] = _dataframe_sha256(
        inner_keys
    )
    inner_label_cache: dict[str, pd.DataFrame] = {}

    def load_inner_labels() -> pd.DataFrame:
        if "labels" not in inner_label_cache:
            labels = _read_target_labels(
                train_path,
                INNER_WINDOW.target_start,
                INNER_WINDOW.target_end,
            )
            inner_label_cache["labels"] = labels
            input_hashes["inner_target_labels_after_raw_path"] = _dataframe_sha256(labels)
        return inner_label_cache["labels"]

    processed_output.mkdir(parents=True, exist_ok=True)
    model_output.mkdir(parents=True, exist_ok=True)
    inner_path = processed_output / "inner_validation_forecasts.parquet"
    inner_writer = _InnerForecastWriter(inner_path)

    def save_inner_checkpoint(
        trial: str,
        checkpoint_round: int,
        raw_path: pd.DataFrame,
        evaluated: pd.DataFrame,
    ) -> None:
        inner_writer.append(trial, checkpoint_round, raw_path, evaluated)

    try:
        tuning = tune_global_lightgbm(
            inner_training,
            actual_history_through_origin=inner_history,
            future_covariates=future_covariates,
            target_keys=inner_keys,
            target_labels=load_inner_labels,
            checkpoint_callback=save_inner_checkpoint,
        )
    finally:
        inner_writer.close()
    (processed_output / "tuning_results.csv").write_text(
        tuning.tuning_results.to_csv(index=False, lineterminator="\n", float_format="%.12g"),
        encoding="utf-8",
    )
    diagnostics_rows = tuning.fit_diagnostics.copy()
    if not tuning.coverage_passed or tuning.selected_trial is None:
        _normalize_diagnostic_dicts(diagnostics_rows).to_csv(
            processed_output / "fit_diagnostics.csv", index=False, float_format="%.12g"
        )
        configuration = {
            "candidate": MODEL_NAME,
            "target": "Rossmann monetary Sales at Store × Date",
            "feature_contract_version": FEATURE_CONTRACT_VERSION,
            "predictor_columns": list(PREDICTOR_COLUMNS),
            "predictor_schema": predictor_schema(),
            "lightgbm_version": lgb.__version__,
            "tuning_selected": False,
            "tuning_stop_reason": tuning.stop_reason,
            "open_label_coverage_guardrail": 0.99,
            "final_holdout_forecast_or_evaluation": False,
        }
        _write_json(processed_output / "configuration.json", configuration)
        failure_manifest = {
            "command": "rossmann-lightgbm",
            "code_revision": _git_revision(root),
            "code_worktree_modified": True,
            "working_tree_source_sha256": _working_tree_source_sha256(root),
            "configuration_sha256": sha256_file(processed_output / "configuration.json"),
            "input_snapshot_identifiers": snapshot_identifiers,
            "censored_input_sha256": input_hashes,
            "tuning_coverage_passed": False,
            "tuning_stop_reason": tuning.stop_reason,
            "final_holdout_forecast_or_evaluation": False,
            "outer_evaluation_run": False,
            "artifacts": {
                path.name: sha256_file(path)
                for path in [
                    processed_output / "configuration.json",
                    processed_output / "tuning_results.csv",
                    inner_path,
                    processed_output / "fit_diagnostics.csv",
                ]
            },
        }
        _write_json(processed_output / "manifest.json", failure_manifest)
        return {
            "tuning_coverage_passed": False,
            "tuning_stop_reason": tuning.stop_reason,
            "outer_evaluation_run": False,
            "processed_output_directory": _PROCESSED_RELATIVE_DIR.as_posix(),
            "manifest": (_PROCESSED_RELATIVE_DIR / "manifest.json").as_posix(),
        }

    inner_labels = load_inner_labels()
    inner_records = tuning.selected_inner_records
    inner_summary = summarize_forecast_metrics(
        inner_records,
        scope="inner_validation",
        forecast_column=FORECAST_COLUMN,
    )
    frozen_parameters = dict(tuning.selected_parameters or {})
    outer_paths: list[pd.DataFrame] = []
    outer_records: list[pd.DataFrame] = []
    outer_models: dict[str, Path] = {}

    for window in APPROVED_DEVELOPMENT_WINDOWS:
        fit_rows = _read_training_features(features_path, window.forecast_origin)
        actual_history = _read_actual_history(train_path, window.forecast_origin)
        target_keys = _read_target_keys(train_path, window.target_start, window.target_end)
        input_hashes[f"{window.name}_training_through_{window.forecast_origin.date()}"] = (
            _dataframe_sha256(fit_rows)
        )
        input_hashes[f"{window.name}_actual_history_through_{window.forecast_origin.date()}"] = (
            _dataframe_sha256(actual_history)
        )
        input_hashes[f"{window.name}_requested_target_keys"] = _dataframe_sha256(target_keys)
        prepared = prepare_training_data(fit_rows, forecast_origin=window.forecast_origin)
        fit_start = time.perf_counter()
        fitted = fit_lightgbm(
            prepared,
            num_boost_round=int(tuning.selected_rounds or 0),
            trial_parameters=frozen_parameters,
        )
        fit_seconds = time.perf_counter() - fit_start
        raw_path = recursive_lightgbm_forecasts(
            target_keys,
            future_covariates=future_covariates,
            actual_history_through_origin=actual_history,
            forecast_origin=window.forecast_origin,
            model=fitted,
            forecast_horizon=14,
        )
        raw_path["validation_window"] = window.name
        outer_paths.append(raw_path)
        model_path = model_output / f"model_{window.name}.txt"
        if fitted.booster is not None:
            fitted.booster.save_model(str(model_path))
            outer_models[window.name] = model_path
        reason_counts = raw_path["unavailable_reason"].dropna().value_counts().to_dict()
        diagnostics_rows = pd.concat(
            [
                diagnostics_rows,
                pd.DataFrame(
                    [
                        {
                            "phase": "outer_evaluation",
                            "trial": tuning.selected_trial,
                            "validation_window": window.name,
                            "forecast_origin": window.forecast_origin,
                            "fit_row_count": prepared.eligible_row_count,
                            "category_vocabulary_hashes": fitted.category_vocabulary_hashes,
                            "fit_status": "success" if fitted.booster is not None else "failed",
                            "fit_failure_reason": fitted.failure_reason,
                            "selected_rounds": tuning.selected_rounds,
                            "training_seconds": fit_seconds,
                            "raw_path_rows": len(raw_path),
                            "available_raw_predictions": int(raw_path["forecast_available"].sum()),
                            "clipped_raw_predictions": int(
                                raw_path["forecast_was_clipped"].fillna(False).sum()
                            ),
                            "unavailable_reasons": reason_counts,
                            "unseen_state_holiday_count": int(
                                raw_path["unseen_state_holiday"].sum()
                            ),
                            "unseen_store_type_count": int(raw_path["unseen_store_type"].sum()),
                            "unseen_assortment_count": int(raw_path["unseen_assortment"].sum()),
                            "outer_model_path": model_path.relative_to(root).as_posix()
                            if model_path.exists()
                            else None,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        target_labels = _read_target_labels(train_path, window.target_start, window.target_end)
        input_hashes[f"{window.name}_target_labels_after_raw_path"] = _dataframe_sha256(
            target_labels
        )
        outer_records.append(
            attach_lightgbm_labels(
                raw_path,
                target_keys,
                target_labels,
                validation_window=window.name,
            )
        )

    candidate_records = pd.concat(outer_records, ignore_index=True)
    full_paths = pd.concat(outer_paths, ignore_index=True)
    if full_paths["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        raise AssertionError("A LightGBM path crossed the final-holdout boundary.")
    if candidate_records["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        raise AssertionError("LightGBM evaluation labels crossed the final-holdout boundary.")
    standalone = summarize_lightgbm_development(candidate_records)
    paired = compare_development_baselines(
        candidate_records,
        _read_development_history(train_path),
        interpretation_allowed=standalone["coverage_guardrail_passed"],
    )
    clipping = _clipping_diagnostics(full_paths)
    all_unavailable_reasons = (
        candidate_records["unavailable_reason"].dropna().value_counts().sort_index().to_dict()
    )

    configuration = {
        "candidate": MODEL_NAME,
        "target": "Untransformed Rossmann monetary Sales at Store × Date",
        "forecast_horizon_calendar_days": 14,
        "forecast_strategy": "recursive; feedback is prior clipped raw prediction",
        "objective": "regression_l1",
        "primary_metric": "MAE",
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "predictor_columns": list(PREDICTOR_COLUMNS),
        "predictor_schema": predictor_schema(),
        "categorical_predictors": list(CATEGORICAL_COLUMNS),
        "category_vocabulary_policy": "ordered vocabularies learned from eligible fit rows only",
        "unknown_store_category": "unseen_store_category; no prediction or fallback",
        "unknown_non_store_category": "categorical missing; count by column",
        "allowed_numeric_missing": "preserve NaN; LightGBM native missing handling",
        "zero_as_missing": False,
        "training_label_eligibility": "Date <= origin and training_label_eligible == True",
        "feature_history": "all observed Sales through origin, including closed-day zero Sales",
        "holdout_firewall_through": LAST_DEVELOPMENT_DATE.date().isoformat(),
        "future_covariate_availability_assumption": (
            "Supplied/planned calendar, holiday, promotion, Promo2 schedule, competition, and "
            "static Store metadata are assumed available at each forecast origin; historical "
            "publication times were not empirically verified."
        ),
        "raw_open_routing": (
            "Raw recursion completes before Open; closed routes to 0, open to raw, unknown to null."
        ),
        "known_closed_day_history_mismatch": (
            "Historical state includes actual closed-day zero Sales; raw recursive future state "
            "does not automatically inject closure zeros."
        ),
        "tuning_origin": INNER_WINDOW.forecast_origin.date().isoformat(),
        "tuning_target_start": INNER_WINDOW.target_start.date().isoformat(),
        "tuning_target_end": INNER_WINDOW.target_end.date().isoformat(),
        "trial_parameters": frozen_parameters,
        "selected_trial": tuning.selected_trial,
        "selected_boosting_rounds": tuning.selected_rounds,
        "shared_parameters": FIXED_PARAMETERS,
        "open_label_coverage_guardrail": 0.99,
        "selected_inner_recursive_open_label_mae": inner_summary["mae"],
        "selected_inner_open_label_coverage": inner_summary["open_label_forecast_coverage_rate"],
        "outer_windows": [
            {
                "name": window.name,
                "origin": window.forecast_origin.date().isoformat(),
                "start": window.target_start.date().isoformat(),
                "end": window.target_end.date().isoformat(),
            }
            for window in APPROVED_DEVELOPMENT_WINDOWS
        ],
        "python_version": sys.version.split()[0],
        "lightgbm_version": lgb.__version__,
        "thread_configuration": {"device_type": "cpu", "num_threads": 4},
        "final_holdout_forecast_or_evaluation": False,
    }
    config_path = processed_output / "configuration.json"
    _write_json(config_path, configuration)
    tuning.tuning_results.to_csv(
        processed_output / "tuning_results.csv", index=False, float_format="%.12g"
    )
    _normalize_diagnostic_dicts(diagnostics_rows).to_csv(
        processed_output / "fit_diagnostics.csv", index=False, float_format="%.12g"
    )
    full_paths.to_parquet(
        processed_output / "internal_recursive_paths.parquet",
        engine="pyarrow",
        index=False,
        compression="zstd",
    )
    candidate_records.to_parquet(
        processed_output / "development_forecasts.parquet",
        engine="pyarrow",
        index=False,
        compression="zstd",
    )
    standalone["by_window"].to_csv(
        processed_output / "metrics_by_window.csv", index=False, float_format="%.12g"
    )
    _write_json(processed_output / "metrics_pooled.json", standalone["pooled"])
    standalone["by_horizon"].to_csv(
        processed_output / "metrics_by_horizon.csv", index=False, float_format="%.12g"
    )
    guardrail = {
        "threshold": standalone["coverage_guardrail_threshold"],
        "passed": standalone["coverage_guardrail_passed"],
        "requires_coverage_review": standalone["requires_coverage_review"],
        "comparison_interpretation_allowed": standalone["coverage_guardrail_passed"],
        "coverage_by_window": standalone["by_window"]
        .loc[
            :,
            [
                "validation_window",
                "open_label_rows",
                "open_label_forecast_available_rows",
                "open_label_coverage_denominator_rows",
                "open_label_forecast_coverage_rate",
            ],
        ]
        .to_dict(orient="records"),
    }
    _write_json(processed_output / "coverage_guardrail.json", guardrail)
    clipping.to_csv(
        processed_output / "clipping_diagnostics.csv", index=False, float_format="%.12g"
    )
    paired_artifact_names = {
        "seasonal_naive": (
            "paired_vs_seasonal_naive_forecasts.parquet",
            "paired_vs_seasonal_naive_metrics.csv",
        ),
        "holt_winters": (
            "paired_vs_holt_winters_forecasts.parquet",
            "paired_vs_holt_winters_metrics.csv",
        ),
    }
    for baseline, (forecast_name, metric_name) in paired_artifact_names.items():
        pair_records, pair_metrics = paired[baseline]
        pair_records.to_parquet(
            processed_output / forecast_name,
            engine="pyarrow",
            index=False,
            compression="zstd",
        )
        pair_metrics.to_csv(
            processed_output / metric_name,
            index=False,
            float_format="%.12g",
        )

    artifact_paths = [
        processed_output / name for name in _PROCESSED_OUTPUT_NAMES if name != "manifest.json"
    ] + [path for path in outer_models.values()]
    lock_path = root / "uv.lock"
    manifest = {
        "command": "rossmann-lightgbm",
        "code_revision": _git_revision(root),
        "code_worktree_modified": True,
        "working_tree_source_sha256": _working_tree_source_sha256(root),
        "target": configuration["target"],
        "development_only_through": LAST_DEVELOPMENT_DATE.date().isoformat(),
        "final_holdout_forecast_or_evaluation": False,
        "holdout_firewall": {
            "start": "2015-07-04",
            "end": "2015-07-31",
            "development_read_ceiling": LAST_DEVELOPMENT_DATE.date().isoformat(),
            "source_rows_filtered_at_parquet_read": True,
            "holdout_outcomes_read_or_hashed_by_phase6": False,
            "holdout_forecasts_emitted": False,
        },
        "input_snapshot_identifiers": snapshot_identifiers,
        "censored_input_sha256": input_hashes,
        "configuration_sha256": sha256_file(config_path),
        "selected_trial": tuning.selected_trial,
        "selected_boosting_rounds": tuning.selected_rounds,
        "selected_trial_parameters": frozen_parameters,
        "tuning_checkpoint_count": len(tuning.tuning_results),
        "tuning_stop_reason": tuning.stop_reason,
        "selected_inner_recursive_open_label_mae": inner_summary["mae"],
        "selected_inner_open_label_coverage": inner_summary["open_label_forecast_coverage_rate"],
        "predictor_contract_identity": {
            "version": FEATURE_CONTRACT_VERSION,
            "ordered_columns": list(PREDICTOR_COLUMNS),
            "schema": predictor_schema(),
        },
        "category_vocabulary_hashes_by_origin": {
            row.get("validation_window", row.get("trial")): _json_safe(
                row.get("category_vocabulary_hashes")
            )
            for row in diagnostics_rows.to_dict(orient="records")
            if isinstance(row.get("category_vocabulary_hashes"), dict)
        },
        "row_counts": {
            "inner_requested_keys": len(inner_keys),
            "inner_target_labels": len(inner_labels),
            "outer_recursive_path_rows": len(full_paths),
            "outer_requested_target_rows": len(candidate_records),
            "outer_primary_eligible_rows": int(
                candidate_records["primary_evaluation_eligible"].sum()
            ),
        },
        "date_counts": {
            "inner_start": INNER_WINDOW.target_start.date().isoformat(),
            "inner_end": INNER_WINDOW.target_end.date().isoformat(),
            "outer_min": min(window.target_start for window in APPROVED_DEVELOPMENT_WINDOWS)
            .date()
            .isoformat(),
            "outer_max": max(window.target_end for window in APPROVED_DEVELOPMENT_WINDOWS)
            .date()
            .isoformat(),
        },
        "clipping_diagnostics": clipping.to_dict(orient="records"),
        "unavailable_reasons_by_outer_key": all_unavailable_reasons,
        "outer_coverage_guardrail": guardrail,
        "paired_comparison_row_counts": {
            name: int(len(values[0])) for name, values in paired.items()
        },
        "environment": {
            "python_version": sys.version,
            "lightgbm_version": lgb.__version__,
            "platform": platform.platform(),
            "os_name": os.name,
            "cpu_count": os.cpu_count(),
            "device_type": "cpu",
            "num_threads": 4,
            "uv_lock_sha256": sha256_file(lock_path),
        },
        "serialized_outer_models": {
            name: {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
            }
            for name, path in outer_models.items()
        },
        "artifacts": {
            path.relative_to(root).as_posix(): {
                "sha256": sha256_file(path),
                "rows": _artifact_rows(path),
            }
            for path in artifact_paths
        },
    }
    _write_json(processed_output / "manifest.json", manifest)
    return {
        "processed_output_directory": _PROCESSED_RELATIVE_DIR.as_posix(),
        "artifact_output_directory": _MODEL_RELATIVE_DIR.as_posix(),
        "lightgbm_version": lgb.__version__,
        "selected_trial": tuning.selected_trial,
        "selected_parameters": frozen_parameters,
        "selected_rounds": tuning.selected_rounds,
        "inner_recursive_mae": inner_summary["mae"],
        "inner_open_label_coverage": inner_summary["open_label_forecast_coverage_rate"],
        "metrics_by_window": standalone["by_window"].to_dict(orient="records"),
        "metrics_pooled": standalone["pooled"],
        "coverage_guardrail_passed": standalone["coverage_guardrail_passed"],
        "unavailable_reasons": all_unavailable_reasons,
        "paired_row_counts": {name: int(len(values[0])) for name, values in paired.items()},
        "final_holdout_forecast_or_evaluation": False,
        "manifest": (_PROCESSED_RELATIVE_DIR / "manifest.json").as_posix(),
    }


def _artifact_rows(path: Path) -> int | None:
    if path.suffix == ".parquet":
        return pq.ParquetFile(path).metadata.num_rows
    if path.suffix == ".csv":
        return sum(1 for _ in path.open(encoding="utf-8")) - 1
    return None


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the approved Phase 6 global LightGBM development evaluation only."
    )
    parser.add_argument("--interim-dir", help="Phase 2 prepared data directory.")
    parser.add_argument("--processed-dir", help="Phase 3 feature data directory.")
    args = parser.parse_args(argv)
    result = run_lightgbm_development_backtest(
        interim_dir=args.interim_dir,
        processed_dir=args.processed_dir,
    )
    print(json.dumps(_json_safe(result), indent=2, sort_keys=True, allow_nan=False))
    return 0 if result.get("tuning_coverage_passed", True) else 2


if __name__ == "__main__":
    raise SystemExit(cli_main())
