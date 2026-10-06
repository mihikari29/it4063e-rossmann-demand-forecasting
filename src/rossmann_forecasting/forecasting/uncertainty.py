"""Development-only empirical uncertainty estimates for the selected Phase 7 model.

This module implements accepted ADR-021 policy. It consumes saved, hash-verified Phase 7
artifacts only; it never fits or refits a point model and has no source-data/holdout reader.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from rossmann_forecasting.forecasting.model_selection import (
    CandidateEvidence,
    sha256_file,
    verify_candidate_manifests,
)
from rossmann_forecasting.forecasting.validation import LAST_DEVELOPMENT_DATE

POLICY_VERSION = "phase-8-uncertainty-v1"
SELECTED_CANDIDATE_ID = "global_lightgbm_gbdt_regression_l1"
MODEL_SELECTION_RUN_ID = "365f22d4c3f94722a594ab934a22c4f6"
INPUT_DIRECTORY = Path("data/processed/model_selection")
OUTPUT_DIRECTORY = Path("data/processed/uncertainty")
OUTPUT_FILENAMES = (
    "calibration_config.json",
    "daily_residual_quantiles.csv",
    "cumulative_error_quantiles.csv",
    "daily_intervals.parquet",
    "cumulative_uncertainty.parquet",
    "coverage_diagnostics.csv",
)
INPUT_OUTPUTS = (
    "development_residual_paths.parquet",
    "selected_development_forecasts.parquet",
    "selected_model_config.json",
    "refit_recipe.json",
    "selection_decision.json",
    "model_comparison.csv",
)
CANDIDATE_OUTPUT_PATHS = {
    "seasonal_naive": {
        "data/processed/seasonal_naive/coverage_by_window.csv",
        "data/processed/seasonal_naive/development_forecasts.parquet",
        "data/processed/seasonal_naive/metrics_by_horizon.csv",
        "data/processed/seasonal_naive/metrics_by_window.csv",
        "data/processed/seasonal_naive/metrics_pooled.json",
    },
    "holt_winters_additive_weekly": {
        "data/processed/holt_winters/clipping_diagnostics.csv",
        "data/processed/holt_winters/coverage_guardrail.json",
        "data/processed/holt_winters/development_forecasts.parquet",
        "data/processed/holt_winters/fit_diagnostics.csv",
        "data/processed/holt_winters/fit_diagnostics_summary.csv",
        "data/processed/holt_winters/internal_14_step_forecasts.parquet",
        "data/processed/holt_winters/metrics_by_horizon.csv",
        "data/processed/holt_winters/metrics_by_window.csv",
        "data/processed/holt_winters/metrics_pooled.json",
        "data/processed/holt_winters/paired_forecasts.parquet",
        "data/processed/holt_winters/paired_metrics.csv",
    },
    "global_lightgbm_gbdt_regression_l1": {
        "artifacts/lightgbm/model_validation_1.txt",
        "artifacts/lightgbm/model_validation_2.txt",
        "artifacts/lightgbm/model_validation_3.txt",
        "data/processed/lightgbm/clipping_diagnostics.csv",
        "data/processed/lightgbm/configuration.json",
        "data/processed/lightgbm/coverage_guardrail.json",
        "data/processed/lightgbm/development_forecasts.parquet",
        "data/processed/lightgbm/fit_diagnostics.csv",
        "data/processed/lightgbm/inner_validation_forecasts.parquet",
        "data/processed/lightgbm/internal_recursive_paths.parquet",
        "data/processed/lightgbm/metrics_by_horizon.csv",
        "data/processed/lightgbm/metrics_by_window.csv",
        "data/processed/lightgbm/metrics_pooled.json",
        "data/processed/lightgbm/paired_vs_holt_winters_forecasts.parquet",
        "data/processed/lightgbm/paired_vs_holt_winters_metrics.csv",
        "data/processed/lightgbm/paired_vs_seasonal_naive_forecasts.parquet",
        "data/processed/lightgbm/paired_vs_seasonal_naive_metrics.csv",
        "data/processed/lightgbm/tuning_results.csv",
    },
}
KEY_COLUMNS = ["Store", "forecast_origin", "Date"]
PATH_COLUMNS = ["Store", "forecast_origin", "horizon"]
REQUIRED_COLUMNS = {
    *KEY_COLUMNS,
    "horizon",
    "validation_window",
    "target_key_observed",
    "actual_sales",
    "source_open",
    "raw_forecast",
    "operational_forecast",
    "raw_residual",
    "operational_residual",
    "raw_primary_error_available",
    "operational_error_available",
    "primary_evaluation_eligible",
    "forecast_available",
    "operational_forecast_available",
    "candidate_id",
    "model_config_identity",
    "model_configuration_sha256",
    "model_selection_run_id",
    "source_manifest_sha256",
}
WINDOWS = {
    "validation_1": {
        "origin": pd.Timestamp("2015-05-22"),
        "first_date": pd.Timestamp("2015-05-23"),
        "last_date": pd.Timestamp("2015-06-05"),
    },
    "validation_2": {
        "origin": pd.Timestamp("2015-06-05"),
        "first_date": pd.Timestamp("2015-06-06"),
        "last_date": pd.Timestamp("2015-06-19"),
    },
    "validation_3": {
        "origin": pd.Timestamp("2015-06-19"),
        "first_date": pd.Timestamp("2015-06-20"),
        "last_date": pd.Timestamp("2015-07-03"),
    },
}
ORIGIN_TO_WINDOW = {item["origin"]: name for name, item in WINDOWS.items()}


@dataclass(frozen=True)
class FitSpec:
    fit_id: str
    calibration_windows: tuple[str, ...]
    assessment_window: str
    issue_origin: pd.Timestamp


FIT_SPECS = (
    FitSpec(
        fit_id="A",
        calibration_windows=("validation_1",),
        assessment_window="validation_2",
        issue_origin=WINDOWS["validation_2"]["origin"],
    ),
    FitSpec(
        fit_id="B",
        calibration_windows=("validation_1", "validation_2"),
        assessment_window="validation_3",
        issue_origin=WINDOWS["validation_3"]["origin"],
    ),
)
DAILY_TAILS = (("lower", Fraction(1, 40)), ("upper", Fraction(39, 40)))
CUMULATIVE_LEVELS = (Fraction(90, 100), Fraction(95, 100), Fraction(98, 100))


class UncertaintyIntegrityError(ValueError):
    """Saved inputs violate the accepted Phase 8 integrity or chronology contract."""


def _canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def exact_daily_ranks(n: int) -> tuple[int, int]:
    """Return exact 1-indexed lower/upper ranks for the accepted daily tails."""
    if n < 0:
        raise ValueError("Sample count cannot be negative.")
    return (n + 1) // 40, (39 * (n + 1) + 39) // 40


def exact_upper_rank(n: int, level: Fraction | float | str) -> int:
    """Return ceil((n+1)*p) using exact rational arithmetic."""
    probability = level if isinstance(level, Fraction) else Fraction(str(level))
    if n < 0 or probability <= 0 or probability >= 1:
        raise ValueError("Require n >= 0 and a probability strictly between zero and one.")
    numerator = (n + 1) * probability.numerator
    denominator = probability.denominator
    return (numerator + denominator - 1) // denominator


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def _git_output(root: Path, *args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def _git_worktree_modified(root: Path) -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, check=False, capture_output=True, text=True
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def _assert_ignored(root: Path) -> None:
    test_file = (OUTPUT_DIRECTORY / "run_id" / "manifest.json").as_posix()
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", test_file],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise UncertaintyIntegrityError(
            f"Generated output path is not ignored by Git: {test_file}."
        )


def _verify_parquet_cutoff(path: Path, expected_rows: int) -> None:
    parquet = pq.ParquetFile(path)
    if parquet.metadata.num_rows != expected_rows:
        raise UncertaintyIntegrityError(f"Input parquet row count mismatch: {path}.")
    schema_names = parquet.schema.names
    if "Date" not in schema_names:
        raise UncertaintyIntegrityError(f"Input parquet has no Date field: {path}.")
    date_index = schema_names.index("Date")
    maximum: pd.Timestamp | None = None
    for row_group_index in range(parquet.metadata.num_row_groups):
        statistics = parquet.metadata.row_group(row_group_index).column(date_index).statistics
        if statistics is None or statistics.max is None:
            raise UncertaintyIntegrityError(f"Input parquet lacks Date statistics: {path}.")
        current = pd.Timestamp(statistics.max)
        maximum = current if maximum is None else max(maximum, current)
    if maximum is None or maximum > LAST_DEVELOPMENT_DATE:
        raise UncertaintyIntegrityError(
            "Development artifact metadata crosses the 2015-07-03 holdout boundary."
        )


def _assert_candidate_artifact_paths_safe(root: Path) -> None:
    """Reject manifest paths outside the reviewed development-artifact allowlist pre-hash."""
    folders = {
        "seasonal_naive": "seasonal_naive",
        "holt_winters_additive_weekly": "holt_winters",
        "global_lightgbm_gbdt_regression_l1": "lightgbm",
    }
    for candidate_id, folder in folders.items():
        path = root / "data" / "processed" / folder / "manifest.json"
        if not path.is_file():
            raise UncertaintyIntegrityError(f"Required candidate manifest is missing: {path}.")
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UncertaintyIntegrityError(
                f"Cannot read candidate manifest metadata for {candidate_id}: {error}."
            ) from error
        entries = manifest.get("outputs") if isinstance(manifest, dict) else None
        if not isinstance(entries, dict) or not entries:
            entries = manifest.get("artifacts") if isinstance(manifest, dict) else None
        if not isinstance(entries, dict) or not entries:
            raise UncertaintyIntegrityError(
                f"Candidate manifest has no artifact metadata: {candidate_id}."
            )
        declared_paths: set[str] = set()
        for key, item in entries.items():
            relative = item.get("path", key) if isinstance(item, dict) else key
            if not isinstance(relative, str):
                raise UncertaintyIntegrityError(
                    f"Candidate artifact path is malformed: {candidate_id}."
                )
            declared_paths.add(Path(relative).as_posix())
        if declared_paths != CANDIDATE_OUTPUT_PATHS[candidate_id]:
            raise UncertaintyIntegrityError(
                f"Candidate manifest contains an unreviewed artifact path: {candidate_id}."
            )
        if (
            manifest.get("development_only_through") != LAST_DEVELOPMENT_DATE.date().isoformat()
            or manifest.get("final_holdout_forecast_or_evaluation") is not False
        ):
            raise UncertaintyIntegrityError(
                f"Candidate manifest does not certify development-only outputs: {candidate_id}."
            )
        for key, metadata in entries.items():
            relative = metadata.get("path", key) if isinstance(metadata, dict) else key
            artifact = root / Path(relative)
            if not isinstance(metadata, dict) or not isinstance(metadata.get("sha256"), str):
                raise UncertaintyIntegrityError(
                    f"Candidate artifact metadata is malformed: {candidate_id}."
                )
            if not artifact.is_file():
                raise UncertaintyIntegrityError(
                    f"Candidate development artifact is missing: {relative}."
                )
            if artifact.suffix == ".parquet":
                rows = metadata.get("rows")
                if not isinstance(rows, int) or rows <= 0:
                    raise UncertaintyIntegrityError(
                        f"Candidate parquet row count is missing: {relative}."
                    )
                _verify_parquet_cutoff(artifact, rows)


def _verify_phase7_inputs(root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Verify only saved Phase 7 development evidence; never open raw source data."""
    base = root / INPUT_DIRECTORY
    manifest_path = base / "manifest.json"
    if not manifest_path.is_file():
        raise UncertaintyIntegrityError(f"Phase 7 selection manifest is missing: {manifest_path}.")
    try:
        selection_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UncertaintyIntegrityError(
            f"Cannot read Phase 7 selection manifest: {error}."
        ) from error
    if not isinstance(selection_manifest, dict):
        raise UncertaintyIntegrityError("Phase 7 selection manifest must be a JSON object.")
    expected_manifest_state = {
        "command": "rossmann-model-selection",
        "status": "selected",
        "publication_state": "complete",
        "input_integrity_status": "passed",
        "record_integrity_status": "passed",
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selection_run_id": MODEL_SELECTION_RUN_ID,
        "final_holdout_forecast_or_evaluation": False,
        "final_holdout_outcomes_read_or_hashed": False,
        "phase_8_started": False,
    }
    for field, expected in expected_manifest_state.items():
        if selection_manifest.get(field) != expected:
            raise UncertaintyIntegrityError(
                f"Phase 7 selection manifest has unexpected {field}: "
                f"{selection_manifest.get(field)!r}."
            )
    input_metadata = selection_manifest.get("outputs")
    selected_metadata = selection_manifest.get("selected_model_artifacts")
    if not isinstance(input_metadata, dict) or not isinstance(selected_metadata, dict):
        raise UncertaintyIntegrityError("Phase 7 selection output metadata is malformed.")
    if set(input_metadata) != set(INPUT_OUTPUTS):
        raise UncertaintyIntegrityError("Phase 7 output manifest has unexpected artifact entries.")
    selected_output_names = {
        "development_residual_paths.parquet",
        "selected_development_forecasts.parquet",
        "selected_model_config.json",
        "refit_recipe.json",
    }
    if set(selected_metadata) != selected_output_names:
        raise UncertaintyIntegrityError(
            "Phase 7 selected-artifact manifest has unexpected entries."
        )
    input_hashes: dict[str, dict[str, Any]] = {}
    for name in INPUT_OUTPUTS:
        metadata = input_metadata.get(name)
        if not isinstance(metadata, dict) or not isinstance(metadata.get("sha256"), str):
            raise UncertaintyIntegrityError(f"Phase 7 manifest omits required output {name}.")
        path = base / name
        if not path.is_file():
            raise UncertaintyIntegrityError(f"Phase 7 published output is missing: {name}.")
        if name in {
            "development_residual_paths.parquet",
            "selected_development_forecasts.parquet",
        }:
            rows = metadata.get("rows")
            if not isinstance(rows, int) or rows <= 0:
                raise UncertaintyIntegrityError(f"Phase 7 parquet row count is missing: {name}.")
            _verify_parquet_cutoff(path, rows)
        if sha256_file(path) != metadata["sha256"]:
            raise UncertaintyIntegrityError(f"Phase 7 published output hash mismatch: {name}.")
        input_hashes[name] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": metadata["sha256"],
            "rows": metadata.get("rows"),
        }
    for name in selected_output_names:
        metadata = selected_metadata.get(name)
        if not isinstance(metadata, dict) or metadata.get("sha256") != input_hashes[name]["sha256"]:
            raise UncertaintyIntegrityError(
                f"Selected Phase 7 artifact identity differs from output manifest: {name}."
            )

    _assert_candidate_artifact_paths_safe(root)
    evidence: dict[str, CandidateEvidence] = verify_candidate_manifests(root)
    recorded_manifests = selection_manifest.get("input_manifests")
    if not isinstance(recorded_manifests, dict) or set(recorded_manifests) != set(evidence):
        raise UncertaintyIntegrityError("Phase 7 candidate manifest lineage is malformed.")
    candidate_lineage: dict[str, Any] = {}
    for candidate_id, candidate_evidence in evidence.items():
        recorded = recorded_manifests[candidate_id]
        if not isinstance(recorded, dict):
            raise UncertaintyIntegrityError(
                f"Candidate manifest lineage is malformed: {candidate_id}."
            )
        if recorded.get("sha256") != candidate_evidence.manifest_sha256:
            raise UncertaintyIntegrityError(f"Candidate manifest hash mismatch: {candidate_id}.")
        candidate_lineage[candidate_id] = {
            "manifest_path": candidate_evidence.manifest_path.relative_to(root).as_posix(),
            "manifest_sha256": candidate_evidence.manifest_sha256,
            "artifact_hashes": dict(sorted(candidate_evidence.artifact_hashes.items())),
            "legacy_lineage_disclosure": candidate_evidence.manifest.get(
                "legacy_provenance_disclosure"
            ),
        }

    config_path = base / "selected_model_config.json"
    recipe_path = base / "refit_recipe.json"
    try:
        model_config = json.loads(config_path.read_text(encoding="utf-8"))
        recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
        decision = json.loads((base / "selection_decision.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UncertaintyIntegrityError(f"Cannot read selected model recipe: {error}.") from error
    if not all(isinstance(value, dict) for value in (model_config, recipe, decision)):
        raise UncertaintyIntegrityError(
            "Selected model, recipe and decision inputs must be objects."
        )
    source_identity = model_config.get("source_identity")
    if not isinstance(source_identity, dict):
        raise UncertaintyIntegrityError("Selected model source identity is malformed.")
    recipe_file_hash = sha256_file(recipe_path)
    if (
        model_config.get("candidate_id") != SELECTED_CANDIDATE_ID
        or model_config.get("selection_run_id") != MODEL_SELECTION_RUN_ID
        or model_config.get("fit_performed") is not False
        or model_config.get("refit_recipe_sha256") != recipe_file_hash
        or recipe.get("candidate_id") != SELECTED_CANDIDATE_ID
        or recipe.get("selection_run_id") != MODEL_SELECTION_RUN_ID
        or recipe.get("fit_performed") is not False
        or recipe.get("recipe_only_no_fitted_model") is not True
        or model_config.get("configuration") != recipe.get("configuration")
        or recipe.get("provenance_identity") != source_identity
    ):
        raise UncertaintyIntegrityError(
            "Selected model config/refit recipe identity is inconsistent."
        )
    if (
        decision.get("status") != "selected"
        or decision.get("selected_candidate_id") != SELECTED_CANDIDATE_ID
        or decision.get("selected_model_identity") != SELECTED_CANDIDATE_ID
        or decision.get("selection_run_id") != MODEL_SELECTION_RUN_ID
        or decision.get("final_holdout_accessed") is not False
    ):
        raise UncertaintyIntegrityError("Phase 7 decision record does not match selected identity.")
    selected_evidence = evidence.get(SELECTED_CANDIDATE_ID)
    if selected_evidence is None:
        raise UncertaintyIntegrityError("Selected LightGBM candidate manifest is unavailable.")
    if source_identity.get("source_manifest_sha256") != selected_evidence.manifest_sha256:
        raise UncertaintyIntegrityError(
            "Selected model config points to a different candidate manifest."
        )
    if source_identity.get("configuration_sha256") != selected_evidence.manifest.get(
        "configuration_sha256"
    ):
        raise UncertaintyIntegrityError(
            "Selected model config points to a different model configuration."
        )
    recipe_hash = _sha256_bytes(_canonical_json_bytes(recipe))

    residual_path = base / "development_residual_paths.parquet"
    forecast_path = base / "selected_development_forecasts.parquet"
    row_filter = [("Date", "<=", LAST_DEVELOPMENT_DATE.to_pydatetime())]
    residuals = pd.read_parquet(residual_path, filters=row_filter)
    forecasts = pd.read_parquet(forecast_path, filters=row_filter)
    if len(residuals) != input_hashes[residual_path.name]["rows"]:
        raise UncertaintyIntegrityError("Filtered residual input row count differs from manifest.")
    if len(forecasts) != input_hashes[forecast_path.name]["rows"]:
        raise UncertaintyIntegrityError("Filtered forecast input row count differs from manifest.")
    _validate_selected_forecast_identity(residuals, forecasts)
    paths = validate_development_paths(residuals, recipe_hash, selected_evidence.manifest_sha256)
    lineage = {
        "selection_manifest_path": manifest_path.relative_to(root).as_posix(),
        "selection_manifest_sha256": sha256_file(manifest_path),
        "selection_run_id": MODEL_SELECTION_RUN_ID,
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selected_model_config_sha256": input_hashes["selected_model_config.json"]["sha256"],
        "refit_recipe_file_sha256": recipe_file_hash,
        "refit_recipe_canonical_sha256": recipe_hash,
        "selected_candidate_manifest_sha256": selected_evidence.manifest_sha256,
        "candidate_lineage": candidate_lineage,
        "phase7_outputs": input_hashes,
        "legacy_lineage_disclosure": selection_manifest.get("legacy_lineage_disclosure"),
        "selection_manifest_status": selection_manifest["status"],
    }
    return paths, lineage


def _verify_phase7_inputs_unchanged(root: Path, expected_lineage: dict[str, Any]) -> None:
    """Re-hash every allowlisted Phase 7 input and compare with its pre-compute identity."""
    try:
        _, current_lineage = _verify_phase7_inputs(root)
    except UncertaintyIntegrityError as error:
        raise UncertaintyIntegrityError(
            "Post-computation Phase 7 input integrity recheck failed; refusing publication."
        ) from error
    if _canonical_json_bytes(current_lineage) != _canonical_json_bytes(expected_lineage):
        raise UncertaintyIntegrityError(
            "Post-computation Phase 7 input identities changed; refusing publication."
        )


def _validate_selected_forecast_identity(residuals: pd.DataFrame, forecasts: pd.DataFrame) -> None:
    required = {"Store", "forecast_origin", "Date", "raw_forecast", "candidate_id"}
    if not required.issubset(forecasts.columns):
        raise UncertaintyIntegrityError("Selected forecast artifact is missing identity columns.")
    keys = KEY_COLUMNS
    if residuals.duplicated(keys).any() or forecasts.duplicated(keys).any():
        raise UncertaintyIntegrityError("Selected forecast artifacts contain duplicate keys.")
    left = residuals[keys + ["raw_forecast", "candidate_id"]].sort_values(keys)
    right = forecasts[keys + ["raw_forecast", "candidate_id"]].sort_values(keys)
    if not left[keys].reset_index(drop=True).equals(right[keys].reset_index(drop=True)):
        raise UncertaintyIntegrityError("Selected forecast artifacts have different row keys.")
    if not np.allclose(
        pd.to_numeric(left["raw_forecast"], errors="coerce"),
        pd.to_numeric(right["raw_forecast"], errors="coerce"),
        rtol=0,
        atol=0,
        equal_nan=True,
    ):
        raise UncertaintyIntegrityError("Selected raw forecasts differ between Phase 7 artifacts.")
    if (
        not left["candidate_id"].eq(SELECTED_CANDIDATE_ID).all()
        or not right["candidate_id"].eq(SELECTED_CANDIDATE_ID).all()
    ):
        raise UncertaintyIntegrityError("Selected forecast candidate identity is inconsistent.")


def validate_development_paths(
    frame: pd.DataFrame,
    recipe_hash: str | None = None,
    selected_manifest_hash: str | None = None,
) -> pd.DataFrame:
    """Validate saved residual signs, masks, routing, keys and chronology before estimation."""
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise UncertaintyIntegrityError(f"Residual artifact is missing columns: {sorted(missing)}.")
    data = frame.copy(deep=True)
    data["forecast_origin"] = pd.to_datetime(data["forecast_origin"], errors="coerce")
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    if data[["forecast_origin", "Date"]].isna().any().any():
        raise UncertaintyIntegrityError("Residual artifact contains invalid dates.")
    store_values = pd.to_numeric(data["Store"], errors="coerce")
    if (
        store_values.isna().any()
        or not np.isfinite(store_values.to_numpy(dtype="float64")).all()
        or store_values.lt(1).any()
        or not np.equal(store_values, np.floor(store_values)).all()
    ):
        raise UncertaintyIntegrityError("Residual artifact has an invalid Store identifier.")
    data["Store"] = store_values.astype("int64")
    if data.duplicated(PATH_COLUMNS).any() or data.duplicated(KEY_COLUMNS).any():
        raise UncertaintyIntegrityError(
            "Residual artifact has duplicate Store-origin-horizon keys."
        )
    data["horizon"] = pd.to_numeric(data["horizon"], errors="coerce")
    if data["horizon"].isna().any() or not data["horizon"].isin(range(1, 15)).all():
        raise UncertaintyIntegrityError("Residual artifact has horizons outside h1-h14.")
    data["horizon"] = data["horizon"].astype("int8")
    if data["Date"].max() > LAST_DEVELOPMENT_DATE:
        raise UncertaintyIntegrityError("Residual artifact crosses the development cutoff.")
    if (
        not data["Date"]
        .eq(data["forecast_origin"] + pd.to_timedelta(data["horizon"], unit="D"))
        .all()
    ):
        raise UncertaintyIntegrityError("Residual Date does not equal origin plus its horizon.")
    if not data["validation_window"].isin(WINDOWS).all():
        raise UncertaintyIntegrityError(
            "Residual artifact includes an unapproved validation window."
        )
    expected_window = data["forecast_origin"].map(ORIGIN_TO_WINDOW)
    if expected_window.isna().any() or not data["validation_window"].eq(expected_window).all():
        raise UncertaintyIntegrityError("Residual window and approved forecast origin disagree.")
    for window_name, window in WINDOWS.items():
        rows = data.loc[data["validation_window"].eq(window_name)]
        if not rows.empty and (
            rows["Date"].min() < window["first_date"]
            or rows["Date"].max() > window["last_date"]
            or rows["forecast_origin"].nunique() != 1
            or rows["forecast_origin"].iloc[0] != window["origin"]
        ):
            raise UncertaintyIntegrityError(f"Saved dates do not match {window_name} chronology.")

    for column in (
        "actual_sales",
        "source_open",
        "raw_forecast",
        "operational_forecast",
        "raw_residual",
        "operational_residual",
    ):
        original_values = data[column]
        converted = pd.to_numeric(original_values, errors="coerce")
        if (original_values.notna() & converted.isna()).any():
            raise UncertaintyIntegrityError(f"Saved numeric field {column} is malformed.")
        data[column] = converted
    for column in (
        "target_key_observed",
        "raw_primary_error_available",
        "operational_error_available",
        "primary_evaluation_eligible",
        "forecast_available",
        "operational_forecast_available",
    ):
        if data[column].isna().any():
            raise UncertaintyIntegrityError(f"Saved mask {column} contains null values.")
        if not data[column].isin([True, False, 0, 1]).all():
            raise UncertaintyIntegrityError(f"Saved mask {column} is not boolean.")
        data[column] = data[column].astype(bool)
    if not data["source_open"].dropna().isin([0.0, 1.0]).all():
        raise UncertaintyIntegrityError(
            "Saved source Open contains values outside 0, 1 or unknown."
        )
    if data["actual_sales"].dropna().lt(0).any():
        raise UncertaintyIntegrityError("Observed monetary Sales cannot be negative.")
    absent_keys = ~data["target_key_observed"]
    if data.loc[absent_keys, ["actual_sales", "source_open"]].notna().any().any():
        raise UncertaintyIntegrityError("Absent Store-Date keys cannot carry Sales or source Open.")
    if data["raw_forecast"].dropna().lt(0).any():
        raise UncertaintyIntegrityError("Saved clipped raw forecasts must be nonnegative.")
    finite_raw = np.isfinite(data["raw_forecast"].to_numpy(dtype=float, na_value=np.nan))
    finite_actual = np.isfinite(data["actual_sales"].to_numpy(dtype=float, na_value=np.nan))
    finite_operational = np.isfinite(
        data["operational_forecast"].to_numpy(dtype=float, na_value=np.nan)
    )
    finite_raw_resid = np.isfinite(data["raw_residual"].to_numpy(dtype=float, na_value=np.nan))
    finite_op_resid = np.isfinite(
        data["operational_residual"].to_numpy(dtype=float, na_value=np.nan)
    )
    target_key = data["target_key_observed"].to_numpy(dtype=bool)
    open_values = data["source_open"].to_numpy(dtype=float, na_value=np.nan)
    expected_raw = target_key & (open_values == 1) & finite_actual & finite_raw & finite_raw_resid
    expected_operational = target_key & finite_actual & finite_operational & finite_op_resid
    if not np.array_equal(data["raw_primary_error_available"].to_numpy(dtype=bool), expected_raw):
        raise UncertaintyIntegrityError("Raw primary error mask disagrees with saved components.")
    if not np.array_equal(data["primary_evaluation_eligible"].to_numpy(dtype=bool), expected_raw):
        raise UncertaintyIntegrityError("Primary evaluation mask disagrees with raw error mask.")
    if not np.array_equal(
        data["operational_error_available"].to_numpy(dtype=bool), expected_operational
    ):
        raise UncertaintyIntegrityError("Operational error mask disagrees with saved components.")
    if not np.array_equal(data["forecast_available"].to_numpy(dtype=bool), finite_raw):
        raise UncertaintyIntegrityError("Raw forecast availability mask disagrees with its values.")
    if not np.array_equal(
        data["operational_forecast_available"].to_numpy(dtype=bool), finite_operational
    ):
        raise UncertaintyIntegrityError(
            "Operational forecast availability mask disagrees with its values."
        )

    open_rows = data["source_open"].eq(1)
    closed_rows = data["source_open"].eq(0)
    unknown_rows = data["source_open"].isna()
    if not np.allclose(
        data.loc[open_rows, "operational_forecast"],
        data.loc[open_rows, "raw_forecast"],
        rtol=1e-12,
        atol=1e-9,
        equal_nan=True,
    ):
        raise UncertaintyIntegrityError("Open operational forecasts differ from raw forecasts.")
    if not data.loc[closed_rows, "operational_forecast"].eq(0.0).all():
        raise UncertaintyIntegrityError("Closed operational forecasts must route to zero.")
    if data.loc[unknown_rows, "operational_forecast"].notna().any():
        raise UncertaintyIntegrityError(
            "Unknown Open rows must have unavailable operational points."
        )
    raw_valid = finite_actual & finite_raw
    op_valid = finite_actual & finite_operational
    raw_expected_residual = data["actual_sales"].to_numpy(dtype=float, na_value=np.nan) - data[
        "raw_forecast"
    ].to_numpy(dtype=float, na_value=np.nan)
    op_expected_residual = data["actual_sales"].to_numpy(dtype=float, na_value=np.nan) - data[
        "operational_forecast"
    ].to_numpy(dtype=float, na_value=np.nan)
    raw_saved = data["raw_residual"].to_numpy(dtype=float, na_value=np.nan)
    op_saved = data["operational_residual"].to_numpy(dtype=float, na_value=np.nan)
    if not np.allclose(
        raw_saved[raw_valid], raw_expected_residual[raw_valid], rtol=1e-12, atol=1e-8
    ):
        raise UncertaintyIntegrityError(
            "Raw residual sign/value differs from actual minus raw point."
        )
    if not np.allclose(op_saved[op_valid], op_expected_residual[op_valid], rtol=1e-12, atol=1e-8):
        raise UncertaintyIntegrityError(
            "Operational residual sign/value differs from actual minus routed point."
        )
    if np.isfinite(raw_saved[~raw_valid]).any() or np.isfinite(op_saved[~op_valid]).any():
        raise UncertaintyIntegrityError("Unavailable components have a numeric saved residual.")

    identity_columns = {
        "candidate_id": SELECTED_CANDIDATE_ID,
        "model_config_identity": SELECTED_CANDIDATE_ID,
        "model_selection_run_id": MODEL_SELECTION_RUN_ID,
    }
    for column, expected in identity_columns.items():
        if not data[column].eq(expected).all():
            raise UncertaintyIntegrityError(f"Saved row identity differs for {column}.")
    if recipe_hash is not None and not data["model_configuration_sha256"].eq(recipe_hash).all():
        raise UncertaintyIntegrityError("Saved rows point to a different canonical model recipe.")
    if (
        selected_manifest_hash is not None
        and not data["source_manifest_sha256"].eq(selected_manifest_hash).all()
    ):
        raise UncertaintyIntegrityError("Saved rows point to a different candidate manifest.")

    data = data.sort_values(KEY_COLUMNS, kind="mergesort").reset_index(drop=True)
    return data


def _prefix_observations(paths: pd.DataFrame) -> pd.DataFrame:
    """Create exact ascending-h operational prefixes without zero filling."""
    prefix_rows: list[dict[str, Any]] = []
    for (store, origin), path in paths.groupby(["Store", "forecast_origin"], sort=True):
        by_horizon = {
            int(row.horizon): row
            for row in path.sort_values("horizon", kind="mergesort").itertuples()
        }
        validation_window = str(path["validation_window"].iloc[0])
        schedule_known = True
        labels_complete = True
        point_complete = True
        error_complete = True
        error_sum = 0.0
        actual_sum = 0.0
        point_sum = 0.0
        closed_nonzero_count = 0
        for k in range(1, 15):
            component = by_horizon.get(k)
            if component is None:
                component_key_observed = False
                source_open = np.nan
                actual = np.nan
                point = np.nan
                residual = np.nan
                operational_mask = False
            else:
                component_key_observed = bool(component.target_key_observed)
                source_open = component.source_open
                actual = component.actual_sales
                point = component.operational_forecast
                residual = component.operational_residual
                operational_mask = bool(component.operational_error_available)
            schedule_known = (
                schedule_known
                and component_key_observed
                and _is_finite(source_open)
                and float(source_open) in (0.0, 1.0)
            )
            labels_complete = labels_complete and _is_finite(actual)
            point_complete = point_complete and _is_finite(point)
            error_complete = error_complete and operational_mask and _is_finite(residual)
            if _is_finite(actual):
                actual_sum += float(actual)
            if _is_finite(point):
                point_sum += float(point)
            if _is_finite(residual):
                error_sum += float(residual)
            if (
                _is_finite(source_open)
                and float(source_open) == 0.0
                and _is_finite(actual)
                and float(actual) != 0.0
            ):
                closed_nonzero_count += 1
            issued_complete = schedule_known and point_complete
            actual_prefix_complete = schedule_known and labels_complete
            complete_error_prefix = actual_prefix_complete and issued_complete and error_complete
            reason = None
            if not schedule_known:
                reason = "opening_schedule_unknown_or_target_key_missing"
            elif not actual_prefix_complete:
                reason = "incomplete_actual_sales_prefix"
            elif not issued_complete:
                reason = "incomplete_operational_forecast_prefix"
            elif not complete_error_prefix:
                reason = "operational_error_mask_or_residual_unavailable"
            prefix_rows.append(
                {
                    "Store": int(store),
                    "forecast_origin": pd.Timestamp(origin),
                    "validation_window": validation_window,
                    "k": k,
                    "prefix_error": error_sum if complete_error_prefix else np.nan,
                    "actual_total": actual_sum if actual_prefix_complete else np.nan,
                    "operational_total_forecast": point_sum if issued_complete else np.nan,
                    "issued_prefix_complete": bool(issued_complete),
                    "actual_prefix_complete": bool(actual_prefix_complete),
                    "error_prefix_complete": bool(complete_error_prefix),
                    "excluded_reason": reason,
                    "closed_actual_nonzero_count": closed_nonzero_count,
                    "schedule_assumption": "saved_source_open_assumed_known_at_origin",
                }
            )
    return (
        pd.DataFrame(prefix_rows)
        .sort_values(["Store", "forecast_origin", "k"], kind="mergesort")
        .reset_index(drop=True)
    )


def _is_finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _quantile_record(
    values: np.ndarray,
    rank: int,
    minimum: int,
) -> tuple[float | None, str | None]:
    count = len(values)
    if count < minimum:
        return None, "insufficient_calibration"
    if rank < 1 or rank > count:
        return None, "quantile_rank_unavailable"
    ordered = np.sort(values.astype("float64", copy=True), kind="mergesort")
    result = float(ordered[rank - 1])
    if not math.isfinite(result):
        return None, "nonfinite_quantile"
    return result, None


def _build_quantile_tables(
    calibration: pd.DataFrame, fit: FitSpec
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    daily_rows: list[dict[str, Any]] = []
    eligible = calibration.loc[calibration["raw_primary_error_available"]]
    for horizon in range(1, 15):
        all_rows = calibration.loc[calibration["horizon"].eq(horizon)]
        stratum = eligible.loc[eligible["horizon"].eq(horizon)]
        values = stratum["raw_residual"].to_numpy(dtype="float64")
        low_rank, high_rank = exact_daily_ranks(len(values))
        ranks = {"lower": low_rank, "upper": high_rank}
        for tail, probability in DAILY_TAILS:
            q, reason = _quantile_record(values, ranks[tail], minimum=40)
            daily_rows.append(
                {
                    "fit_id": fit.fit_id,
                    "horizon": horizon,
                    "tail": tail,
                    "tail_level": float(probability),
                    "error_population": "raw_primary_source_open_1_signed_sales_error",
                    "n": len(values),
                    "distinct_stores": int(stratum["Store"].nunique()),
                    "distinct_origins": int(stratum["forecast_origin"].nunique()),
                    "observed_open_0": int(all_rows["source_open"].eq(0).sum()),
                    "observed_open_1": int(all_rows["source_open"].eq(1).sum()),
                    "observed_open_unknown": int(all_rows["source_open"].isna().sum()),
                    "candidate_rows": len(all_rows),
                    "forecast_available_count": int(all_rows["forecast_available"].sum()),
                    "unavailable_component_reasons": json.dumps(
                        {
                            "target_key_missing": int((~all_rows["target_key_observed"]).sum()),
                            "sales_label_missing": int(all_rows["actual_sales"].isna().sum()),
                            "raw_forecast_unavailable": int(
                                (~all_rows["forecast_available"]).sum()
                            ),
                            "raw_residual_unavailable": int(
                                (
                                    all_rows["target_key_observed"]
                                    & all_rows["source_open"].eq(1)
                                    & all_rows["actual_sales"].map(_is_finite)
                                    & all_rows["forecast_available"]
                                    & ~all_rows["raw_residual"].map(_is_finite)
                                ).sum()
                            ),
                            "source_open_not_1": int((~all_rows["source_open"].eq(1)).sum()),
                        },
                        sort_keys=True,
                    ),
                    "last_calibration_label": (
                        stratum["Date"].max().date().isoformat() if not stratum.empty else None
                    ),
                    "rank_1_indexed": ranks[tail],
                    "signed_quantile": q,
                    "available": q is not None,
                    "unavailable_reason": reason,
                    "policy_version": POLICY_VERSION,
                    "selected_candidate_id": SELECTED_CANDIDATE_ID,
                    "calibration_windows": "+".join(fit.calibration_windows),
                }
            )

    calibration_prefixes = _prefix_observations(calibration)
    cumulative_rows: list[dict[str, Any]] = []
    total_paths = int(calibration[["Store", "forecast_origin"]].drop_duplicates().shape[0])
    for k in range(1, 15):
        all_at_k = calibration_prefixes.loc[calibration_prefixes["k"].eq(k)]
        complete = all_at_k.loc[all_at_k["error_prefix_complete"]]
        values = complete["prefix_error"].to_numpy(dtype="float64")
        for level in CUMULATIVE_LEVELS:
            rank = exact_upper_rank(len(values), level)
            q, reason = _quantile_record(values, rank, minimum=50)
            cumulative_rows.append(
                {
                    "fit_id": fit.fit_id,
                    "k": k,
                    "p": float(level),
                    "error_population": "complete_operational_signed_sales_prefix_error",
                    "total_store_origin_paths": total_paths,
                    "complete_prefixes": len(complete),
                    "excluded_prefixes": total_paths - len(complete),
                    "excluded_reason_counts": json.dumps(
                        all_at_k.loc[~all_at_k["error_prefix_complete"], "excluded_reason"]
                        .fillna("unavailable")
                        .value_counts()
                        .sort_index()
                        .to_dict(),
                        sort_keys=True,
                    ),
                    "distinct_stores": int(complete["Store"].nunique()),
                    "distinct_origins": int(complete["forecast_origin"].nunique()),
                    "last_calibration_label": (
                        str(
                            calibration.loc[
                                calibration["validation_window"].isin(fit.calibration_windows),
                                "Date",
                            ]
                            .max()
                            .date()
                        )
                        if not calibration.empty
                        else None
                    ),
                    "rank_1_indexed": rank,
                    "signed_quantile": q,
                    "available": q is not None,
                    "unavailable_reason": reason,
                    "prefix_definition": "exact_h1_through_k_complete_origin_anchored_path",
                    "schedule_assumption": "saved_source_open_assumed_known_at_origin",
                    "policy_version": POLICY_VERSION,
                    "selected_candidate_id": SELECTED_CANDIDATE_ID,
                    "calibration_windows": "+".join(fit.calibration_windows),
                }
            )
    return (
        pd.DataFrame(daily_rows),
        pd.DataFrame(cumulative_rows),
        calibration_prefixes,
    )


def _interval_from_point(
    point: Any, quantiles: dict[str, float | None], reasons: dict[str, str | None]
) -> dict[str, Any]:
    raw_point = float(point) if _is_finite(point) else np.nan
    q_low = quantiles.get("lower")
    q_high = quantiles.get("upper")
    reason = reasons.get("lower") or reasons.get("upper")
    record = {
        "point_forecast": raw_point,
        "q_low_signed": q_low,
        "q_high_signed": q_high,
        "pre_support_lower": np.nan,
        "pre_support_upper": np.nan,
        "lower": np.nan,
        "upper": np.nan,
        "width": np.nan,
        "lower_support_clipped": False,
        "upper_support_clipped": False,
        "available": False,
        "unavailable_reason": reason,
    }
    if not math.isfinite(raw_point):
        record["unavailable_reason"] = "nonfinite_point_forecast"
        return record
    if raw_point < 0:
        record["unavailable_reason"] = "negative_point_forecast"
        return record
    if q_low is None or q_high is None:
        record["unavailable_reason"] = reason or "insufficient_calibration"
        return record
    pre_lower = raw_point + float(q_low)
    pre_upper = raw_point + float(q_high)
    record["pre_support_lower"] = pre_lower
    record["pre_support_upper"] = pre_upper
    record["lower_support_clipped"] = pre_lower < 0
    record["upper_support_clipped"] = pre_upper < 0
    if not math.isfinite(pre_lower) or not math.isfinite(pre_upper) or pre_lower > pre_upper:
        record["unavailable_reason"] = "invalid_bounds"
        return record
    lower = max(0.0, pre_lower)
    upper = max(0.0, pre_upper)
    width = upper - lower
    if not math.isfinite(width) or width < 0:
        record["unavailable_reason"] = "invalid_bounds"
        return record
    record.update(
        {
            "lower": lower,
            "upper": upper,
            "width": width,
            "available": True,
            "unavailable_reason": None,
        }
    )
    return record


def _daily_interval_records(
    rows: pd.DataFrame,
    daily_quantiles: pd.DataFrame,
    fit: FitSpec,
    role: str,
) -> pd.DataFrame:
    lookup: dict[tuple[int, str], tuple[float | None, str | None]] = {}
    for row in daily_quantiles.itertuples(index=False):
        lookup[(int(row.horizon), str(row.tail))] = (
            float(row.signed_quantile) if pd.notna(row.signed_quantile) else None,
            row.unavailable_reason,
        )
    records: list[dict[str, Any]] = []
    ordered = rows.sort_values(KEY_COLUMNS, kind="mergesort")
    for row in ordered.itertuples(index=False):
        common = {
            "fit_id": fit.fit_id,
            "Store": int(row.Store),
            "forecast_origin": pd.Timestamp(row.forecast_origin),
            "Date": pd.Timestamp(row.Date),
            "horizon": int(row.horizon),
            "validation_window": str(row.validation_window),
            "role": role,
            "selected_candidate_id": SELECTED_CANDIDATE_ID,
            "model_selection_run_id": MODEL_SELECTION_RUN_ID,
            "schedule_provenance": "saved_source_open_assumed_known_at_origin",
            "schedule_assumption_flag": True,
            "units": "monetary_sales_turnover",
        }
        q = {tail: lookup[(int(row.horizon), tail)][0] for tail in ("lower", "upper")}
        q_reason = {tail: lookup[(int(row.horizon), tail)][1] for tail in ("lower", "upper")}
        raw = _interval_from_point(row.raw_forecast, q, q_reason)
        records.append({**common, "interval_kind": "raw", **raw})
        if (
            pd.notna(row.source_open)
            and float(row.source_open) == 0.0
            and bool(row.target_key_observed)
        ):
            operational = {
                "point_forecast": 0.0,
                "q_low_signed": q["lower"],
                "q_high_signed": q["upper"],
                "pre_support_lower": 0.0,
                "pre_support_upper": 0.0,
                "lower": 0.0,
                "upper": 0.0,
                "width": 0.0,
                "lower_support_clipped": False,
                "upper_support_clipped": False,
                "available": True,
                "unavailable_reason": None,
            }
            operational["closure_assumption_applied"] = True
        elif (
            pd.notna(row.source_open)
            and float(row.source_open) == 1.0
            and bool(row.target_key_observed)
        ):
            operational = {**raw, "closure_assumption_applied": False}
            if not _is_finite(row.operational_forecast):
                operational = {
                    **operational,
                    "available": False,
                    "unavailable_reason": "nonfinite_point_forecast",
                }
        else:
            operational = {
                **_interval_from_point(np.nan, q, q_reason),
                "available": False,
                "unavailable_reason": "opening_schedule_unknown",
                "closure_assumption_applied": False,
            }
        records.append({**common, "interval_kind": "operational", **operational})
    result = pd.DataFrame(records)
    labels = ordered[
        KEY_COLUMNS
        + [
            "actual_sales",
            "source_open",
            "target_key_observed",
            "raw_primary_error_available",
            "operational_error_available",
            "raw_residual",
            "operational_residual",
        ]
    ].rename(columns={"source_open": "assessment_source_open"})
    result = result.merge(labels, on=KEY_COLUMNS, how="left", validate="many_to_one")
    raw_hit = (
        result["interval_kind"].eq("raw")
        & result["raw_primary_error_available"].fillna(False)
        & result["available"]
    )
    operational_hit = (
        result["interval_kind"].eq("operational")
        & result["operational_error_available"].fillna(False)
        & result["available"]
    )
    result["outcome_joined_after_issuance"] = True
    result["hit"] = pd.Series(pd.NA, index=result.index, dtype="boolean")
    result["lower_miss"] = pd.Series(pd.NA, index=result.index, dtype="boolean")
    result["upper_miss"] = pd.Series(pd.NA, index=result.index, dtype="boolean")
    valid = raw_hit | operational_hit
    result.loc[valid, "hit"] = (
        result.loc[valid, "lower"].le(result.loc[valid, "actual_sales"])
        & result.loc[valid, "actual_sales"].le(result.loc[valid, "upper"])
    ).to_numpy()
    result.loc[valid, "lower_miss"] = (
        result.loc[valid, "actual_sales"].lt(result.loc[valid, "lower"]).to_numpy()
    )
    result.loc[valid, "upper_miss"] = (
        result.loc[valid, "actual_sales"].gt(result.loc[valid, "upper"]).to_numpy()
    )
    return result.sort_values(
        ["fit_id", "Store", "forecast_origin", "Date", "interval_kind"], kind="mergesort"
    ).reset_index(drop=True)


def _cumulative_issued_records(
    assessment: pd.DataFrame,
    cumulative_quantiles: pd.DataFrame,
    prefixes: pd.DataFrame,
    fit: FitSpec,
) -> pd.DataFrame:
    q_lookup = {
        (int(row.k), Fraction(str(row.p))): (
            float(row.signed_quantile) if pd.notna(row.signed_quantile) else None,
            row.unavailable_reason,
            int(row.complete_prefixes),
        )
        for row in cumulative_quantiles.itertuples(index=False)
    }
    prefix_lookup = prefixes.set_index(["Store", "forecast_origin", "k"])
    records: list[dict[str, Any]] = []
    paths = (
        assessment[["Store", "forecast_origin"]]
        .drop_duplicates()
        .sort_values(["Store", "forecast_origin"], kind="mergesort")
    )
    for path_key in paths.itertuples(index=False, name=None):
        store, origin = path_key
        for k in range(1, 15):
            prefix = prefix_lookup.loc[(int(store), pd.Timestamp(origin), k)]
            for level in CUMULATIVE_LEVELS:
                q, q_reason, n = q_lookup[(k, level)]
                point_complete = bool(prefix["issued_prefix_complete"])
                point_sum = (
                    float(prefix["operational_total_forecast"]) if point_complete else np.nan
                )
                reason = None
                q_value: float | None = q
                if not point_complete:
                    reason = str(
                        prefix["excluded_reason"] or "incomplete_operational_forecast_prefix"
                    )
                elif q is None:
                    reason = q_reason or "insufficient_calibration"
                raw_upper = point_sum + q if point_complete and q is not None else np.nan
                upper = max(0.0, raw_upper) if _is_finite(raw_upper) else np.nan
                bounds_available = _is_finite(upper)
                if not bounds_available and reason is None:
                    reason = "invalid_bounds"
                actual_complete = bool(prefix["actual_prefix_complete"])
                actual_total = float(prefix["actual_total"]) if actual_complete else np.nan
                error_complete = bool(prefix["error_prefix_complete"])
                actual_error = float(prefix["prefix_error"]) if error_complete else np.nan
                records.append(
                    {
                        "fit_id": fit.fit_id,
                        "Store": int(store),
                        "forecast_origin": pd.Timestamp(origin),
                        "k": k,
                        "p": float(level),
                        "selected_candidate_id": SELECTED_CANDIDATE_ID,
                        "model_selection_run_id": MODEL_SELECTION_RUN_ID,
                        "calibration_windows": "+".join(fit.calibration_windows),
                        "assessment_window": fit.assessment_window,
                        "schedule_provenance": "saved_source_open_assumed_known_at_origin",
                        "schedule_assumption_flag": True,
                        "units": "monetary_sales_turnover",
                        "total_calibration_prefixes": n,
                        "issued_prefix_complete": point_complete,
                        "actual_prefix_complete": actual_complete,
                        "error_prefix_complete": error_complete,
                        "issued_prefix_unavailable_reason": reason,
                        "D_k": point_sum,
                        "q_p_signed": q_value,
                        "pre_support_upper": raw_upper,
                        "U_k": upper,
                        "support_clipped_at_zero": bool(bounds_available and raw_upper < 0),
                        "SafetyStock_k": max(0.0, upper - point_sum)
                        if bounds_available
                        else np.nan,
                        "Target_k": max(point_sum, upper) if bounds_available else np.nan,
                        "actual_total": actual_total,
                        "actual_cumulative_error": actual_error,
                        "hit": (actual_total <= upper)
                        if actual_complete and bounds_available
                        else pd.NA,
                        "closed_actual_nonzero_count": int(prefix["closed_actual_nonzero_count"]),
                    }
                )
    return (
        pd.DataFrame(records)
        .sort_values(["fit_id", "Store", "forecast_origin", "k", "p"], kind="mergesort")
        .reset_index(drop=True)
    )


def _daily_diagnostics(intervals: pd.DataFrame, fit: FitSpec, role: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    source = intervals.loc[intervals["fit_id"].eq(fit.fit_id)]
    for kind in ("raw", "operational"):
        branch = source.loc[source["interval_kind"].eq(kind)]
        if kind == "raw":
            label_eligible = (
                branch["target_key_observed"].fillna(False).astype(bool)
                & branch["assessment_source_open"].eq(1)
                & branch["actual_sales"].map(_is_finite)
            )
            error_available = branch["raw_primary_error_available"].fillna(False).astype(bool)
            populations = {"raw_primary_open": (label_eligible, error_available)}
        else:
            open_values = branch["assessment_source_open"]
            known_label = (
                branch["target_key_observed"].fillna(False).astype(bool)
                & branch["actual_sales"].map(_is_finite)
                & open_values.isin([0, 1])
            )
            op_mask = branch["operational_error_available"].fillna(False).astype(bool)
            populations = {
                "operational_open": (known_label & open_values.eq(1), op_mask & open_values.eq(1)),
                "operational_closed": (
                    known_label & open_values.eq(0),
                    op_mask & open_values.eq(0),
                ),
                "operational_pooled": (known_label, op_mask),
            }
        for population, (label_mask, error_mask) in populations.items():
            pop = branch.assign(_label_eligible=label_mask, _error_available=error_mask)
            path_complete = pop.groupby(["Store", "forecast_origin"], sort=True)[
                "_error_available"
            ].all()
            complete_path_count = int(path_complete.sum())
            total_path_count = int(len(path_complete))
            for horizon, stratum in pop.groupby("horizon", sort=True):
                eligible = stratum["_label_eligible"].astype(bool)
                error_available = stratum["_error_available"].astype(bool)
                interval_available = stratum["available"].astype(bool)
                hit_rows = stratum.loc[error_available & interval_available]
                hit_values = hit_rows["hit"].dropna().astype(bool)
                widths = hit_rows["width"].dropna().astype(float)
                expected = len(stratum)
                count_eligible = int(eligible.sum())
                available_for_labels = int((eligible & interval_available).sum())
                closed_violation = (
                    int(
                        (
                            stratum["assessment_source_open"].eq(0)
                            & stratum["actual_sales"].notna()
                            & stratum["actual_sales"].gt(0)
                        ).sum()
                    )
                    if kind == "operational" and population != "operational_open"
                    else 0
                )
                rows.append(
                    {
                        "fit_id": fit.fit_id,
                        "role": role,
                        "assessment_origin": (
                            fit.issue_origin.date().isoformat()
                            if role == "chronological_assessment"
                            else None
                        ),
                        "population": population,
                        "h_or_k": int(horizon),
                        "target_weekday": stratum["Date"].iloc[0].day_name(),
                        "p_or_tail_scope": "daily_95pct_two_sided",
                        "diagnostic": "daily_interval_coverage",
                        "expected_target_count": expected,
                        "observed_key_count": int(
                            stratum["target_key_observed"].fillna(False).sum()
                        ),
                        "label_eligible_count": count_eligible,
                        "forecast_available_count": int(
                            stratum["point_forecast"].map(_is_finite).sum()
                        ),
                        "interval_available_count": int(interval_available.sum()),
                        "interval_available_eligible_count": available_for_labels,
                        "interval_availability_over_eligible": (
                            available_for_labels / count_eligible if count_eligible else np.nan
                        ),
                        "usable_hit_denominator": len(hit_values),
                        "hits": int(hit_values.sum()),
                        "coverage": float(hit_values.mean()) if len(hit_values) else np.nan,
                        "lower_misses": int(hit_rows["lower_miss"].fillna(False).sum()),
                        "upper_misses": int(hit_rows["upper_miss"].fillna(False).sum()),
                        "mean_width": float(widths.mean()) if len(widths) else np.nan,
                        "median_width": float(widths.median()) if len(widths) else np.nan,
                        "lower_support_clipped_count": int(
                            (
                                error_available
                                & interval_available
                                & stratum["lower_support_clipped"]
                            ).sum()
                        ),
                        "upper_support_clipped_count": int(
                            (
                                error_available
                                & interval_available
                                & stratum["upper_support_clipped"]
                            ).sum()
                        ),
                        "zero_width_count": int(
                            (error_available & interval_available & stratum["width"].eq(0)).sum()
                        ),
                        "open_0_count": int(stratum["assessment_source_open"].eq(0).sum()),
                        "open_1_count": int(stratum["assessment_source_open"].eq(1).sum()),
                        "open_unknown_count": int(stratum["assessment_source_open"].isna().sum()),
                        "closed_branch_assumption_violations": closed_violation,
                        "complete_14_day_paths": complete_path_count,
                        "complete_14_day_path_rate": (
                            complete_path_count / total_path_count if total_path_count else np.nan
                        ),
                        "covariate_diagnostics": "unavailable_not_in_phase7_export",
                        "unavailable_reason_counts": json.dumps(
                            stratum.loc[~interval_available, "unavailable_reason"]
                            .fillna("unavailable")
                            .value_counts()
                            .sort_index()
                            .to_dict(),
                            sort_keys=True,
                        ),
                        "calibration_n": np.nan,
                        "complete_prefixes": np.nan,
                        "excluded_prefixes": np.nan,
                        "bound_available_count": np.nan,
                        "actual_prefix_count": np.nan,
                        "calibration_distinct_stores": np.nan,
                        "calibration_distinct_origins": np.nan,
                    }
                )
    return pd.DataFrame(rows)


def _cumulative_diagnostics(
    records: pd.DataFrame,
    quantiles: pd.DataFrame,
    fit: FitSpec,
    role: str,
    calibration_prefixes: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if role == "calibration_descriptive":
        assert calibration_prefixes is not None
        prefix_source = calibration_prefixes
        paths = int(calibration_prefixes[["Store", "forecast_origin"]].drop_duplicates().shape[0])
        for qrow in quantiles.itertuples(index=False):
            if qrow.fit_id != fit.fit_id:
                continue
            k = int(qrow.k)
            p = float(qrow.p)
            at_k = prefix_source.loc[prefix_source["k"].eq(k)]
            complete = at_k.loc[at_k["error_prefix_complete"]]
            q = float(qrow.signed_quantile) if pd.notna(qrow.signed_quantile) else np.nan
            # Calibration coverage is retrospective/descriptive and never an issued record.
            bounds: list[float] = []
            hits: list[bool] = []
            for item in complete.itertuples(index=False):
                d = float(item.operational_total_forecast)
                u = max(0.0, d + q) if math.isfinite(q) else np.nan
                bounds.append(u)
                hits.append(bool(item.actual_total <= u) if math.isfinite(u) else False)
            available = int(sum(math.isfinite(x) for x in bounds))
            hit_count = int(sum(hits)) if available else 0
            rows.append(
                {
                    "fit_id": fit.fit_id,
                    "role": role,
                    "assessment_origin": None,
                    "population": "operational_prefix_conditional_replay",
                    "h_or_k": k,
                    "p_or_tail_scope": p,
                    "diagnostic": "cumulative_prefix_coverage",
                    "expected_target_count": paths,
                    "observed_key_count": np.nan,
                    "label_eligible_count": len(complete),
                    "forecast_available_count": int(at_k["issued_prefix_complete"].sum()),
                    "interval_available_count": available,
                    "interval_available_eligible_count": available,
                    "interval_availability_over_eligible": (
                        available / len(complete) if len(complete) else np.nan
                    ),
                    "usable_hit_denominator": available,
                    "hits": hit_count,
                    "coverage": hit_count / available if available else np.nan,
                    "lower_misses": np.nan,
                    "upper_misses": int(available - hit_count),
                    "mean_width": np.nan,
                    "median_width": np.nan,
                    "lower_support_clipped_count": np.nan,
                    "upper_support_clipped_count": np.nan,
                    "zero_width_count": np.nan,
                    "open_0_count": np.nan,
                    "open_1_count": np.nan,
                    "open_unknown_count": np.nan,
                    "closed_branch_assumption_violations": int(
                        at_k["closed_actual_nonzero_count"].sum()
                    ),
                    "unavailable_reason_counts": json.dumps(
                        at_k.loc[~at_k["error_prefix_complete"], "excluded_reason"]
                        .fillna("unavailable")
                        .value_counts()
                        .sort_index()
                        .to_dict(),
                        sort_keys=True,
                    ),
                    "calibration_n": int(qrow.complete_prefixes),
                    "complete_prefixes": len(complete),
                    "excluded_prefixes": paths - len(complete),
                    "target_weekday": None,
                    "bound_available_count": available,
                    "actual_prefix_count": len(complete),
                    "calibration_distinct_stores": int(complete["Store"].nunique()),
                    "calibration_distinct_origins": int(complete["forecast_origin"].nunique()),
                    "complete_14_day_paths": np.nan,
                    "complete_14_day_path_rate": np.nan,
                    "covariate_diagnostics": "unavailable_not_in_phase7_export",
                }
            )
        return pd.DataFrame(rows)

    fit_records = records.loc[records["fit_id"].eq(fit.fit_id)]
    for (k, p), stratum in fit_records.groupby(["k", "p"], sort=True):
        complete_actual = stratum["actual_prefix_complete"].astype(bool)
        bound_available = stratum["U_k"].map(_is_finite)
        usable = complete_actual & bound_available
        hits = stratum.loc[usable, "hit"].dropna().astype(bool)
        n_total = int(stratum[["Store", "forecast_origin"]].drop_duplicates().shape[0])
        qrow = quantiles.loc[
            quantiles["fit_id"].eq(fit.fit_id) & quantiles["k"].eq(k) & quantiles["p"].eq(p)
        ]
        calibration_n = int(qrow["complete_prefixes"].iloc[0]) if not qrow.empty else 0
        rows.append(
            {
                "fit_id": fit.fit_id,
                "role": role,
                "assessment_origin": fit.issue_origin.date().isoformat(),
                "population": "operational_prefix_conditional_replay",
                "h_or_k": int(k),
                "p_or_tail_scope": float(p),
                "diagnostic": "cumulative_prefix_coverage",
                "expected_target_count": n_total,
                "observed_key_count": int(stratum["actual_prefix_complete"].sum()),
                "label_eligible_count": int(complete_actual.sum()),
                "forecast_available_count": int(stratum["issued_prefix_complete"].sum()),
                "interval_available_count": int(bound_available.sum()),
                "interval_available_eligible_count": int(usable.sum()),
                "interval_availability_over_eligible": (
                    usable.sum() / complete_actual.sum() if complete_actual.sum() else np.nan
                ),
                "usable_hit_denominator": len(hits),
                "hits": int(hits.sum()),
                "coverage": float(hits.mean()) if len(hits) else np.nan,
                "lower_misses": np.nan,
                "upper_misses": int(len(hits) - int(hits.sum())),
                "mean_width": np.nan,
                "median_width": np.nan,
                "lower_support_clipped_count": np.nan,
                "upper_support_clipped_count": np.nan,
                "zero_width_count": np.nan,
                "open_0_count": np.nan,
                "open_1_count": np.nan,
                "open_unknown_count": np.nan,
                "closed_branch_assumption_violations": int(
                    stratum["closed_actual_nonzero_count"].sum()
                ),
                "unavailable_reason_counts": json.dumps(
                    stratum.loc[~bound_available, "issued_prefix_unavailable_reason"]
                    .fillna("unavailable")
                    .value_counts()
                    .sort_index()
                    .to_dict(),
                    sort_keys=True,
                ),
                "calibration_n": calibration_n,
                "complete_prefixes": int(complete_actual.sum()),
                "excluded_prefixes": n_total - int(complete_actual.sum()),
                "bound_available_count": int(bound_available.sum()),
                "actual_prefix_count": int(complete_actual.sum()),
                "calibration_distinct_stores": int(qrow["distinct_stores"].iloc[0])
                if not qrow.empty
                else 0,
                "calibration_distinct_origins": int(qrow["distinct_origins"].iloc[0])
                if not qrow.empty
                else 0,
                "target_weekday": None,
                "complete_14_day_paths": np.nan,
                "complete_14_day_path_rate": np.nan,
                "covariate_diagnostics": "unavailable_not_in_phase7_export",
            }
        )
    return pd.DataFrame(rows)


def calculate_uncertainty(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Calculate fixed Fit A/B tables and chronological diagnostics from validated rows."""
    validated = validate_development_paths(frame)
    daily_tables: list[pd.DataFrame] = []
    cumulative_tables: list[pd.DataFrame] = []
    interval_tables: list[pd.DataFrame] = []
    issued_tables: list[pd.DataFrame] = []
    diagnostic_tables: list[pd.DataFrame] = []
    for fit in FIT_SPECS:
        calibration = validated.loc[
            validated["validation_window"].isin(fit.calibration_windows)
        ].copy()
        assessment = validated.loc[validated["validation_window"].eq(fit.assessment_window)].copy()
        if calibration.empty or assessment.empty:
            raise UncertaintyIntegrityError(
                f"Fit {fit.fit_id} has missing calibration or assessment data."
            )
        if (
            calibration["Date"].max() > fit.issue_origin
            or not assessment["Date"].gt(fit.issue_origin).all()
        ):
            raise UncertaintyIntegrityError(f"Fit {fit.fit_id} violates issue-time chronology.")
        if not assessment["forecast_origin"].eq(fit.issue_origin).all():
            raise UncertaintyIntegrityError(
                f"Fit {fit.fit_id} uses an unsupported assessment origin."
            )
        daily_quantiles, cumulative_quantiles, calibration_prefixes = _build_quantile_tables(
            calibration, fit
        )
        calibration_daily = _daily_interval_records(
            calibration, daily_quantiles, fit, role="calibration_descriptive"
        )
        assessment_daily = _daily_interval_records(
            assessment, daily_quantiles, fit, role="chronological_assessment"
        )
        calibration_prefixes = calibration_prefixes.loc[
            calibration_prefixes["validation_window"].isin(fit.calibration_windows)
        ].copy()
        assessment_prefixes = _prefix_observations(assessment)
        cumulative_issued = _cumulative_issued_records(
            assessment, cumulative_quantiles, assessment_prefixes, fit
        )
        daily_tables.append(daily_quantiles)
        cumulative_tables.append(cumulative_quantiles)
        interval_tables.append(assessment_daily)
        issued_tables.append(cumulative_issued)
        diagnostic_tables.extend(
            [
                _daily_diagnostics(calibration_daily, fit, "calibration_descriptive"),
                _daily_diagnostics(assessment_daily, fit, "chronological_assessment"),
                _cumulative_diagnostics(
                    pd.DataFrame(),
                    cumulative_quantiles,
                    fit,
                    "calibration_descriptive",
                    calibration_prefixes,
                ),
                _cumulative_diagnostics(
                    cumulative_issued,
                    cumulative_quantiles,
                    fit,
                    "chronological_assessment",
                ),
            ]
        )
    return {
        "daily_residual_quantiles": pd.concat(daily_tables, ignore_index=True),
        "cumulative_error_quantiles": pd.concat(cumulative_tables, ignore_index=True),
        "daily_intervals": pd.concat(interval_tables, ignore_index=True),
        "cumulative_uncertainty": pd.concat(issued_tables, ignore_index=True),
        "coverage_diagnostics": pd.concat(diagnostic_tables, ignore_index=True),
    }


def _calibration_config(lineage: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "status": "IMPLEMENTED_UNDER_REVIEW",
        "selected_candidate_id": SELECTED_CANDIDATE_ID,
        "selection_run_id": MODEL_SELECTION_RUN_ID,
        "selected_model_configuration_file_sha256": lineage["selected_model_config_sha256"],
        "refit_recipe_file_sha256": lineage["refit_recipe_file_sha256"],
        "refit_recipe_canonical_sha256": lineage["refit_recipe_canonical_sha256"],
        "daily_error": {
            "sign": "actual_sales_minus_saved_clipped_raw_forecast",
            "population": "source_open_equals_1_and_observed_sales_and_forecast_available",
            "pooling": "equally_weighted_store_origin_rows_within_exact_horizon_only",
            "horizons": list(range(1, 15)),
            "tail_levels": {"lower": "1/40", "upper": "39/40"},
            "one_indexed_ranks": {
                "lower": "floor((n+1)/40)",
                "upper": "ceil(39*(n+1)/40)",
            },
            "rank_clamping": "none; both ranks must be in 1..n",
            "minimum_samples": 40,
            "interpolation": "none",
            "ties": "retained_with_multiplicity",
            "fallback": "none",
            "support": "independently clip lower and upper endpoints to zero",
        },
        "cumulative_error": {
            "sign": "ascending_horizon_sum(actual_sales_minus_operational_forecast)",
            "prefixes": list(range(1, 15)),
            "levels": ["0.90", "0.95", "0.98"],
            "one_indexed_rank": "ceil((n+1)*p)",
            "rank_clamping": "none; rank must be in 1..n",
            "minimum_complete_prefixes": 50,
            "incomplete_component": "exclude every prefix containing the component; never fill",
            "support_equations": {
                "D_k": "sum(h=1..k, operational_forecast_h)",
                "U_k": "max(0, D_k + q_p(E_k))",
                "SafetyStock_k": "max(0, U_k - D_k)",
                "Target_k": "max(D_k, U_k)",
            },
            "fallback": "none; never sum marginal daily bounds",
        },
        "fits": [
            {
                "fit_id": fit.fit_id,
                "calibration_windows": list(fit.calibration_windows),
                "calibration_labels_through": fit.issue_origin.date().isoformat(),
                "calibration_date_ranges": [
                    {
                        "window": window_name,
                        "first_date": WINDOWS[window_name]["first_date"].date().isoformat(),
                        "last_date": WINDOWS[window_name]["last_date"].date().isoformat(),
                    }
                    for window_name in fit.calibration_windows
                ],
                "assessment_window": fit.assessment_window,
                "assessment_origin": fit.issue_origin.date().isoformat(),
                "assessment_target_dates": {
                    "first_date": WINDOWS[fit.assessment_window]["first_date"].date().isoformat(),
                    "last_date": WINDOWS[fit.assessment_window]["last_date"].date().isoformat(),
                },
                "assessment_targets_after_origin": True,
            }
            for fit in FIT_SPECS
        ],
        "schedule_assumption": {
            "identifier": "saved_source_open_assumed_known_at_origin",
            "scope": "conditional historical development replay only",
            "externally_verified": False,
            "closed_day_operational_route": "zero monetary turnover",
            "unknown_open": "unavailable",
        },
        "freeze_state": {
            "policy_implemented_and_validated": True,
            "fitted_quantile_tables_frozen": False,
            "fit_b_values_pending_external_implementation_results_review": True,
        },
        "boundaries": {
            "development_cutoff_inclusive": LAST_DEVELOPMENT_DATE.date().isoformat(),
            "protected_holdout": "2015-07-04 through 2015-07-31",
            "holdout_open_sales_customers_read_loaded_or_hashed": False,
            "model_refit_or_tuning": False,
            "seed": "not_applicable_deterministic_order_statistics",
            "units": "monetary_sales_turnover_not_physical_demand",
        },
        "selected_lineage": {
            "selection_manifest_sha256": lineage["selection_manifest_sha256"],
            "selected_candidate_manifest_sha256": lineage["selected_candidate_manifest_sha256"],
            "legacy_lineage_disclosure": lineage["legacy_lineage_disclosure"],
        },
    }


def _output_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    if path.suffix == ".parquet":
        parquet = pq.ParquetFile(path)
        metadata["rows"] = parquet.metadata.num_rows
        metadata["columns"] = parquet.schema.names
    elif path.suffix == ".csv":
        with path.open(encoding="utf-8") as stream:
            metadata["rows"] = max(0, sum(1 for _ in stream) - 1)
    return metadata


def _verify_staged_outputs(stage: Path) -> dict[str, dict[str, Any]]:
    outputs: dict[str, dict[str, Any]] = {}
    for name in OUTPUT_FILENAMES:
        path = stage / name
        if not path.is_file() or path.stat().st_size == 0:
            raise UncertaintyIntegrityError(
                f"Staged uncertainty output is missing or empty: {name}."
            )
        outputs[name] = _output_metadata(path)
        if path.suffix == ".parquet":
            pd.read_parquet(path)
        elif path.suffix == ".csv":
            pd.read_csv(path)
        elif path.suffix == ".json":
            document = json.loads(path.read_text(encoding="utf-8"))
            if name == "calibration_config.json":
                if not isinstance(document, dict):
                    raise UncertaintyIntegrityError("Calibration config must be a JSON object.")
                hash_material = {
                    key: value
                    for key, value in document.items()
                    if key not in {"config_canonical_sha256", "config_hash_excludes_self_field"}
                }
                if (
                    document.get("config_hash_excludes_self_field") is not True
                    or document.get("config_canonical_sha256")
                    != _sha256_bytes(_canonical_json_bytes(hash_material))
                    or document.get("policy_version") != POLICY_VERSION
                    or document.get("selected_candidate_id") != SELECTED_CANDIDATE_ID
                ):
                    raise UncertaintyIntegrityError("Calibration config identity or hash mismatch.")
    return outputs


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in ("numpy", "pandas", "pyarrow"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _source_files_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/rossmann_forecasting/forecasting/uncertainty.py",
        "scripts/run_forecast_uncertainty.py",
    ):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
    return digest.hexdigest()


def _write_current_pointer(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _json_write(temporary, value)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run_uncertainty(root: str | Path | None = None, *, run_id: str | None = None) -> dict[str, Any]:
    """Verify Phase 7 evidence and atomically publish one immutable Phase 8 development run."""
    repository = Path(root or Path.cwd()).resolve()
    _assert_ignored(repository)
    paths, lineage = _verify_phase7_inputs(repository)
    results = calculate_uncertainty(paths)
    config = _calibration_config(lineage)
    config["config_hash_scope"] = (
        "canonical JSON of configuration fields, excluding config_canonical_sha256 and "
        "config_hash_excludes_self_field"
    )
    config["config_canonical_sha256"] = _sha256_bytes(_canonical_json_bytes(config))
    config["config_hash_excludes_self_field"] = True

    output_root = repository / OUTPUT_DIRECTORY
    output_root.mkdir(parents=True, exist_ok=True)
    _assert_ignored(repository)
    identifier = run_id or uuid.uuid4().hex
    if not identifier or any(
        char not in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
        for char in identifier
    ):
        raise ValueError("run_id may contain only letters, digits, hyphens and underscores.")
    final_dir = output_root / identifier
    if final_dir.exists():
        raise FileExistsError(f"Uncertainty run directory already exists: {final_dir}.")
    stage = Path(tempfile.mkdtemp(prefix=f".stage-{identifier}-", dir=output_root))
    try:
        _json_write(stage / "calibration_config.json", config)
        results["daily_residual_quantiles"].to_csv(
            stage / "daily_residual_quantiles.csv", index=False, na_rep="", float_format="%.17g"
        )
        results["cumulative_error_quantiles"].to_csv(
            stage / "cumulative_error_quantiles.csv", index=False, na_rep="", float_format="%.17g"
        )
        for name in ("daily_intervals", "cumulative_uncertainty"):
            results[name].to_parquet(
                stage / f"{name}.parquet", engine="pyarrow", index=False, compression="zstd"
            )
        results["coverage_diagnostics"].to_csv(
            stage / "coverage_diagnostics.csv", index=False, na_rep="", float_format="%.17g"
        )
        output_metadata = _verify_staged_outputs(stage)
        # Revalidate all reviewed Phase 7 manifests/artifacts after calculation and staging, but
        # before writing the run manifest or publishing the run directory/current pointer.
        _verify_phase7_inputs_unchanged(repository, lineage)
        daily_has_unavailable = bool((~results["daily_residual_quantiles"]["available"]).any())
        cumulative_has_unavailable = bool(
            (~results["cumulative_error_quantiles"]["available"]).any()
        )
        manifest = {
            "command": "python scripts/run_forecast_uncertainty.py",
            "run_id": identifier,
            "status": (
                "complete_with_unavailable_strata"
                if daily_has_unavailable or cumulative_has_unavailable
                else "complete"
            ),
            "policy_version": POLICY_VERSION,
            "selection_run_id": MODEL_SELECTION_RUN_ID,
            "selected_candidate_id": SELECTED_CANDIDATE_ID,
            "fit_b_quantiles_frozen": False,
            "external_fit_b_results_review_pending": True,
            "inputs": lineage,
            "configuration": {
                "path": "calibration_config.json",
                "sha256": output_metadata["calibration_config.json"]["sha256"],
            },
            "outputs": output_metadata,
            "code_provenance": {
                "git_revision": _git_output(repository, "rev-parse", "HEAD"),
                "worktree_modified": _git_worktree_modified(repository),
                "source_files": [
                    "src/rossmann_forecasting/forecasting/uncertainty.py",
                    "scripts/run_forecast_uncertainty.py",
                ],
                "source_sha256": _source_files_hash(repository),
                "uv_lock_sha256": sha256_file(repository / "uv.lock"),
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "packages": _package_versions(),
            },
            "counts": {
                "input_residual_rows": len(paths),
                "distinct_stores": int(paths["Store"].nunique()),
                "distinct_origins": int(paths["forecast_origin"].nunique()),
                "raw_primary_error_rows": int(paths["raw_primary_error_available"].sum()),
                "operational_error_rows": int(paths["operational_error_available"].sum()),
                "date_min": paths["Date"].min().date().isoformat(),
                "date_max": paths["Date"].max().date().isoformat(),
                "windows": {
                    window: int(paths["validation_window"].eq(window).sum()) for window in WINDOWS
                },
            },
            "boundaries": {
                "development_cutoff_inclusive": LAST_DEVELOPMENT_DATE.date().isoformat(),
                "protected_holdout": "2015-07-04 through 2015-07-31",
                "holdout_open_sales_customers_opened_loaded_or_hashed": False,
                "source_dataset_opened_or_hashed": False,
                "model_refit_or_tuning": False,
                "phase_9_or_later_work": False,
            },
            "schedule_assumption": "saved_source_open_assumed_known_at_origin",
            "schedule_is_externally_verified": False,
            "all_outputs_monetary_sales_turnover": True,
            "legacy_lineage_disclosure": lineage["legacy_lineage_disclosure"],
        }
        # All table bytes are staged and re-read before the run manifest is the last staged file.
        _json_write(stage / "manifest.json", manifest)
        staged_manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        if staged_manifest.get("outputs") != output_metadata:
            raise UncertaintyIntegrityError("Staged run manifest output inventory is inconsistent.")
        if final_dir.exists():
            raise FileExistsError(f"Uncertainty run directory already exists: {final_dir}.")
        os.replace(stage, final_dir)
        pointer = {
            "run_id": identifier,
            "manifest_path": f"{identifier}/manifest.json",
            "manifest_sha256": sha256_file(final_dir / "manifest.json"),
            "status": manifest["status"],
        }
        _write_current_pointer(output_root / "current.json", pointer)
        return {"run_id": identifier, "run_directory": final_dir, "manifest": manifest}
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
