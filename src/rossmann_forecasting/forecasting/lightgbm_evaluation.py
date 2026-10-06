"""Fixed inner tuning and development-only evaluation for global LightGBM."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import lightgbm as lgb
import pandas as pd

from rossmann_forecasting.forecasting.holt_winters import FORECAST_COLUMN as HW_FORECAST_COLUMN
from rossmann_forecasting.forecasting.holt_winters_evaluation import (
    build_development_holt_winters_evaluation,
)
from rossmann_forecasting.forecasting.lightgbm import (
    FORECAST_COLUMN,
    fit_lightgbm,
    make_lightgbm_dataset,
    prepare_training_data,
    recursive_lightgbm_forecasts,
    select_requested_raw_forecasts,
)
from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    ValidationWindow,
    assemble_evaluation_records,
    build_development_evaluation_records,
)

INNER_WINDOW = ValidationWindow(
    name="inner_validation",
    forecast_origin=pd.Timestamp("2015-04-24"),
    target_start=pd.Timestamp("2015-04-25"),
    target_end=pd.Timestamp("2015-05-08"),
)
COVERAGE_GUARDRAIL = 0.99
TRIALS = (
    {
        "trial": "A",
        "learning_rate": 0.05,
        "num_leaves": 15,
        "max_depth": 4,
        "min_data_in_leaf": 200,
    },
    {
        "trial": "B",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": 5,
        "min_data_in_leaf": 200,
    },
    {
        "trial": "C",
        "learning_rate": 0.03,
        "num_leaves": 15,
        "max_depth": 4,
        "min_data_in_leaf": 100,
    },
    {
        "trial": "D",
        "learning_rate": 0.03,
        "num_leaves": 31,
        "max_depth": 5,
        "min_data_in_leaf": 100,
    },
)
TRIAL_PARAMETERS = {
    trial["trial"]: {key: value for key, value in trial.items() if key != "trial"}
    for trial in TRIALS
}
TRIAL_ORDER = {trial["trial"]: index for index, trial in enumerate(TRIALS)}


@dataclass(frozen=True)
class TuningResult:
    """Checkpoint evidence and the recipe frozen before any outer forecast."""

    tuning_results: pd.DataFrame
    fit_diagnostics: pd.DataFrame
    selected_trial: str | None
    selected_parameters: dict[str, Any] | None
    selected_rounds: int | None
    selected_inner_records: pd.DataFrame | None
    selected_inner_path: pd.DataFrame | None
    coverage_passed: bool
    stop_reason: str


def attach_lightgbm_labels(
    raw_path: pd.DataFrame,
    requested_target_keys: pd.DataFrame,
    target_labels: pd.DataFrame | Callable[[], pd.DataFrame],
    *,
    validation_window: str,
) -> pd.DataFrame:
    """Attach Sales/Open after the raw recursive path has been generated."""

    requested_forecasts = select_requested_raw_forecasts(raw_path, requested_target_keys)
    raw = requested_forecasts.loc[
        :,
        [
            "Store",
            "forecast_origin",
            "Date",
            "horizon",
            FORECAST_COLUMN,
        ],
    ].rename(columns={FORECAST_COLUMN: "raw_baseline_forecast"})
    evaluated = assemble_evaluation_records(
        raw,
        target_labels.loc[:, ["Store", "Date", "Sales", "Open"]],
        validation_window=validation_window,
    ).rename(columns={"raw_baseline_forecast": FORECAST_COLUMN})
    audit_columns = [
        "Store",
        "forecast_origin",
        "Date",
        "model_forecast_unclipped",
        "forecast_was_clipped",
        "unavailable_reason",
        "unseen_state_holiday",
        "unseen_store_type",
        "unseen_assortment",
    ]
    audit = requested_forecasts.loc[:, audit_columns]
    result = evaluated.merge(
        audit,
        on=["Store", "forecast_origin", "Date"],
        how="left",
        validate="one_to_one",
        sort=False,
    )
    result["forecast_available"] = result[FORECAST_COLUMN].notna()
    result["primary_evaluation_eligible"] = (
        result["source_open"].eq(1)
        & result["actual_sales"].notna()
        & result[FORECAST_COLUMN].notna()
    )
    return result


def summarize_lightgbm_development(records: pd.DataFrame) -> dict[str, Any]:
    """Use the shared approved metric function for windows, pooled rows and horizons."""

    by_window = [
        summarize_forecast_metrics(
            records.loc[records["validation_window"].eq(window.name)],
            scope="validation_window",
            validation_window=window.name,
            forecast_column=FORECAST_COLUMN,
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    pooled = summarize_forecast_metrics(
        records,
        scope="pooled_development",
        forecast_column=FORECAST_COLUMN,
    )
    by_horizon = [
        summarize_forecast_metrics(
            records.loc[pd.to_numeric(records["horizon"], errors="coerce").eq(step)],
            scope="development_horizon",
            horizon=step,
            forecast_column=FORECAST_COLUMN,
        )
        for step in range(1, 15)
    ]
    window_frame = pd.DataFrame(by_window)
    rates = pd.to_numeric(window_frame["open_label_forecast_coverage_rate"], errors="coerce")
    passed = bool(rates.notna().all() and rates.ge(COVERAGE_GUARDRAIL).all())
    return {
        "by_window": window_frame,
        "pooled": pooled,
        "by_horizon": pd.DataFrame(by_horizon),
        "coverage_guardrail_threshold": COVERAGE_GUARDRAIL,
        "coverage_guardrail_passed": passed,
        "requires_coverage_review": not passed,
    }


def _checkpoint_summary(records: pd.DataFrame) -> dict[str, Any]:
    metrics = summarize_forecast_metrics(
        records,
        scope="inner_validation",
        forecast_column=FORECAST_COLUMN,
    )
    coverage = metrics["open_label_forecast_coverage_rate"]
    return {
        "recursive_open_label_mae": metrics["mae"],
        "open_label_rows": metrics["open_label_rows"],
        "open_label_forecast_available_rows": metrics["open_label_forecast_available_rows"],
        "open_label_coverage_denominator_rows": metrics["open_label_coverage_denominator_rows"],
        "open_label_coverage_rate": coverage,
        "all_target_rows": metrics["observed_target_rows"],
        "all_target_forecast_available_rows": metrics["forecast_available_rows"],
        "all_target_coverage_rate": metrics["raw_forecast_coverage_rate"],
        "checkpoint_eligible_by_coverage": bool(
            coverage is not None and coverage >= COVERAGE_GUARDRAIL
        ),
    }


def tune_global_lightgbm(
    training_rows: pd.DataFrame,
    *,
    actual_history_through_origin: pd.DataFrame,
    future_covariates: pd.DataFrame,
    target_keys: pd.DataFrame,
    target_labels: pd.DataFrame,
    checkpoint_callback: Callable[[str, int, pd.DataFrame, pd.DataFrame], None] | None = None,
) -> TuningResult:
    """Run only the four approved trials with recursive 10-round checkpoints."""

    prepared = prepare_training_data(
        training_rows,
        forecast_origin=INNER_WINDOW.forecast_origin,
    )
    if prepared.eligible_row_count == 0:
        empty = pd.DataFrame(
            [
                {
                    "trial": trial["trial"],
                    "checkpoint_round": None,
                    "stop_reason": "no_eligible_training_rows",
                    "is_selected_trial": False,
                }
                for trial in TRIALS
            ]
        )
        return TuningResult(
            empty,
            pd.DataFrame(),
            None,
            None,
            None,
            None,
            None,
            False,
            "no_eligible_training_rows",
        )
    fit_set = make_lightgbm_dataset(prepared)
    result_rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    per_trial_best: dict[str, dict[str, Any]] = {}
    cached_target_labels: pd.DataFrame | None = None

    for trial in TRIALS:
        trial_name = trial["trial"]
        trial_params = TRIAL_PARAMETERS[trial_name]
        booster: lgb.Booster | None = None
        best_any_mae: float | None = None
        stale_checkpoints = 0
        best_eligible: dict[str, Any] | None = None
        stop_reason = "hard_cap_400_rounds"
        last_round = 0
        for checkpoint_round in range(10, 401, 10):
            fit_started = time.perf_counter()
            fitted = fit_lightgbm(
                prepared,
                num_boost_round=10,
                trial_parameters=trial_params,
                dataset=fit_set,
                init_model=booster,
            )
            fit_seconds = time.perf_counter() - fit_started
            if fitted.booster is None:
                stop_reason = fitted.failure_reason or "model_fit_failure"
                diagnostics.append(
                    {
                        "phase": "inner_tuning",
                        "trial": trial_name,
                        "forecast_origin": INNER_WINDOW.forecast_origin,
                        "fit_row_count": prepared.eligible_row_count,
                        "category_vocabulary_hashes": fitted.category_vocabulary_hashes,
                        "fit_status": "failed",
                        "fit_failure_reason": stop_reason,
                        "checkpoint_round": checkpoint_round,
                        "training_seconds": fit_seconds,
                    }
                )
                result_rows.append(
                    {
                        "trial": trial_name,
                        **trial_params,
                        "checkpoint_round": checkpoint_round,
                        "stop_reason": stop_reason,
                        "recursive_open_label_mae": None,
                        "open_label_coverage_rate": None,
                        "checkpoint_eligible_by_coverage": False,
                        "is_trial_best_eligible_checkpoint": False,
                    }
                )
                break
            booster = fitted.booster
            last_round = checkpoint_round
            raw_path = recursive_lightgbm_forecasts(
                target_keys,
                future_covariates=future_covariates,
                actual_history_through_origin=actual_history_through_origin,
                forecast_origin=INNER_WINDOW.forecast_origin,
                model=fitted,
                forecast_horizon=14,
            )
            recursive_seconds = time.perf_counter() - fit_started - fit_seconds
            # This is the first operation after completing the checkpoint's full raw path that
            # joins the independent inner target label projection.
            if cached_target_labels is None:
                cached_target_labels = target_labels() if callable(target_labels) else target_labels
            evaluated = attach_lightgbm_labels(
                raw_path,
                target_keys,
                cached_target_labels,
                validation_window=INNER_WINDOW.name,
            )
            summary = _checkpoint_summary(evaluated)
            summary_row = {
                "trial": trial_name,
                **trial_params,
                "checkpoint_round": checkpoint_round,
                **summary,
                "is_trial_best_eligible_checkpoint": False,
                "stale_checkpoints_after_this": None,
                "stop_reason": None,
                "training_seconds": fit_seconds,
                "recursive_forecast_seconds": recursive_seconds,
            }
            if checkpoint_callback is not None:
                checkpoint_callback(trial_name, checkpoint_round, raw_path, evaluated)
            mae = summary["recursive_open_label_mae"]
            if mae is not None and (best_any_mae is None or mae < best_any_mae):
                best_any_mae = mae
                stale_checkpoints = 0
            else:
                stale_checkpoints += 1
            if summary["checkpoint_eligible_by_coverage"] and mae is not None:
                if best_eligible is None or mae < best_eligible["mae"]:
                    best_eligible = {
                        "mae": mae,
                        "round": checkpoint_round,
                        "records": evaluated.copy(),
                        "path": raw_path.copy(),
                    }
            summary_row["stale_checkpoints_after_this"] = stale_checkpoints
            if best_eligible is not None and checkpoint_round == best_eligible["round"]:
                summary_row["is_trial_best_eligible_checkpoint"] = True
            if stale_checkpoints >= 5:
                stop_reason = "five_checkpoints_without_strict_mae_improvement"
            elif checkpoint_round == 400:
                stop_reason = "hard_cap_400_rounds"
            summary_row["stop_reason"] = (
                stop_reason if stop_reason != "hard_cap_400_rounds" else None
            )
            result_rows.append(summary_row)
            diagnostics.append(
                {
                    "phase": "inner_tuning",
                    "trial": trial_name,
                    "forecast_origin": INNER_WINDOW.forecast_origin,
                    "fit_row_count": prepared.eligible_row_count,
                    "category_vocabulary_hashes": fitted.category_vocabulary_hashes,
                    "fit_status": "success",
                    "fit_failure_reason": None,
                    "checkpoint_round": checkpoint_round,
                    "raw_path_rows": len(raw_path),
                    "available_raw_predictions": int(raw_path["forecast_available"].sum()),
                    "clipped_raw_predictions": int(
                        raw_path["forecast_was_clipped"].fillna(False).sum()
                    ),
                    "unavailable_reasons": raw_path["unavailable_reason"]
                    .dropna()
                    .value_counts()
                    .to_dict(),
                }
            )
            if stale_checkpoints >= 5:
                break
        trial_checkpoint_rows = [
            index for index, row in enumerate(result_rows) if row.get("trial") == trial_name
        ]
        if trial_checkpoint_rows:
            result_rows[trial_checkpoint_rows[-1]]["stop_reason"] = stop_reason
            for checkpoint_index in trial_checkpoint_rows:
                result_rows[checkpoint_index]["is_trial_best_eligible_checkpoint"] = (
                    best_eligible is not None
                    and result_rows[checkpoint_index].get("checkpoint_round")
                    == best_eligible["round"]
                )
        if best_eligible is not None:
            per_trial_best[trial_name] = {
                **best_eligible,
                "trial": trial_name,
                "parameters": trial_params,
                "num_leaves": trial_params["num_leaves"],
                "min_data_in_leaf": trial_params["min_data_in_leaf"],
                "stop_reason": stop_reason,
                "last_round": last_round,
            }

    if not per_trial_best:
        return TuningResult(
            pd.DataFrame(result_rows),
            pd.DataFrame(diagnostics),
            None,
            None,
            None,
            None,
            None,
            False,
            "no_checkpoint_met_99_percent_open_label_coverage",
        )
    selected = min(
        per_trial_best.values(),
        key=lambda item: (
            item["mae"],
            item["num_leaves"],
            -item["min_data_in_leaf"],
            TRIAL_ORDER[item["trial"]],
        ),
    )
    table = pd.DataFrame(result_rows)
    if not table.empty:
        table["is_selected_trial"] = table["trial"].eq(selected["trial"])
        table["is_selected_checkpoint"] = table["trial"].eq(selected["trial"]) & table[
            "checkpoint_round"
        ].eq(selected["round"])
        table["selected_trial"] = selected["trial"]
        table["selected_rounds"] = selected["round"]
        table["selection_eligible"] = table["checkpoint_eligible_by_coverage"].fillna(False)
    return TuningResult(
        table,
        pd.DataFrame(diagnostics),
        selected["trial"],
        selected["parameters"],
        selected["round"],
        selected["records"],
        selected["path"],
        True,
        selected["stop_reason"],
    )


def _paired_records(
    candidate_records: pd.DataFrame,
    baseline_records: pd.DataFrame,
    *,
    baseline_column: str,
    baseline_name: str,
) -> pd.DataFrame:
    keys = ["Store", "forecast_origin", "Date"]
    candidate = candidate_records.loc[
        :,
        keys + ["horizon", "validation_window", "actual_sales", "source_open", FORECAST_COLUMN],
    ].copy()
    baseline = baseline_records.loc[
        :,
        keys + ["horizon", "validation_window", "actual_sales", "source_open", baseline_column],
    ].copy()
    if candidate.duplicated(keys).any() or baseline.duplicated(keys).any():
        raise ValueError("Paired comparison inputs must have unique Store-origin-Date keys.")
    merged = candidate.merge(
        baseline,
        on=keys,
        how="outer",
        suffixes=("_lightgbm", f"_{baseline_name}"),
        indicator=True,
        validate="one_to_one",
        sort=False,
    )
    if not merged["_merge"].eq("both").all():
        raise ValueError("Candidate and baseline target-key populations differ.")
    for column in ("horizon", "validation_window", "actual_sales", "source_open"):
        left = merged[f"{column}_lightgbm"]
        right = merged[f"{column}_{baseline_name}"]
        if not (left.eq(right) | (left.isna() & right.isna())).all():
            raise ValueError(f"Paired labels or metadata disagree for {column}.")
    eligible = (
        merged["source_open_lightgbm"].eq(1)
        & merged["actual_sales_lightgbm"].notna()
        & merged[FORECAST_COLUMN].notna()
        & merged[baseline_column].notna()
    )
    selected = merged.loc[eligible].copy()
    result = pd.DataFrame(
        {
            "Store": selected["Store"],
            "forecast_origin": selected["forecast_origin"],
            "Date": selected["Date"],
            "horizon": selected["horizon_lightgbm"].astype("int8"),
            "validation_window": selected["validation_window_lightgbm"],
            "actual_sales": selected["actual_sales_lightgbm"].astype("float64"),
            "source_open": selected["source_open_lightgbm"].astype("float64"),
            FORECAST_COLUMN: selected[FORECAST_COLUMN].astype("float64"),
            "baseline_forecast": selected[baseline_column].astype("float64"),
        }
    ).reset_index(drop=True)
    result["forecast_available"] = True
    result["primary_evaluation_eligible"] = True
    result["baseline_name"] = baseline_name
    return result


def summarize_paired_lightgbm_comparison(
    paired: pd.DataFrame,
    *,
    baseline_name: str,
    interpretation_allowed: bool,
) -> pd.DataFrame:
    """Summarize both candidates on exact paired eligible keys and suppress if coverage fails."""

    populations: list[tuple[str, str | None, int | None, pd.DataFrame]] = [
        (
            "validation_window",
            window.name,
            None,
            paired.loc[paired["validation_window"].eq(window.name)],
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    populations.append(("pooled_development", None, None, paired))
    populations.extend(
        (
            "development_horizon",
            None,
            horizon,
            paired.loc[paired["horizon"].eq(horizon)],
        )
        for horizon in range(1, 15)
    )
    summaries: list[dict[str, Any]] = []
    for scope, window, horizon, rows in populations:
        lightgbm_metrics = summarize_forecast_metrics(
            rows,
            scope=scope,
            validation_window=window,
            horizon=horizon,
            forecast_column=FORECAST_COLUMN,
        )
        baseline_metrics = summarize_forecast_metrics(
            rows,
            scope=scope,
            validation_window=window,
            horizon=horizon,
            forecast_column="baseline_forecast",
        )
        delta = None
        relative = None
        relative_reason = None
        lower = None
        if lightgbm_metrics["mae"] is not None and baseline_metrics["mae"] is not None:
            delta = lightgbm_metrics["mae"] - baseline_metrics["mae"]
            if baseline_metrics["mae"] > 0:
                relative = delta / baseline_metrics["mae"]
            else:
                relative_reason = f"{baseline_name} paired MAE is zero."
            if lightgbm_metrics["mae"] < baseline_metrics["mae"]:
                lower = "lightgbm"
            elif lightgbm_metrics["mae"] > baseline_metrics["mae"]:
                lower = baseline_name
            else:
                lower = "tie"
        if not interpretation_allowed:
            lower = None
        summaries.append(
            {
                "scope": scope,
                "validation_window": window,
                "horizon": horizon,
                "paired_row_count": len(rows),
                "lightgbm_mae": lightgbm_metrics["mae"],
                "lightgbm_rmse": lightgbm_metrics["rmse"],
                "lightgbm_mape": lightgbm_metrics["mape"],
                "lightgbm_wape": lightgbm_metrics["wape"],
                f"{baseline_name}_mae": baseline_metrics["mae"],
                f"{baseline_name}_rmse": baseline_metrics["rmse"],
                f"{baseline_name}_mape": baseline_metrics["mape"],
                f"{baseline_name}_wape": baseline_metrics["wape"],
                f"mae_difference_lightgbm_minus_{baseline_name}": delta,
                "relative_mae_change": relative,
                "relative_mae_change_unavailable_reason": relative_reason,
                "lower_paired_mae_model": lower,
                "comparison_interpretation": (
                    "descriptive_paired_comparison"
                    if interpretation_allowed
                    else "suppressed_by_open_label_coverage_guardrail"
                ),
                "paired_mape_rows": lightgbm_metrics["mape_rows"],
                "paired_zero_actual_rows_excluded_from_mape": lightgbm_metrics[
                    "zero_actual_rows_excluded_from_mape"
                ],
                "paired_wape_actual_denominator": lightgbm_metrics["wape_actual_denominator"],
            }
        )
    return pd.DataFrame(summaries)


def compare_development_baselines(
    candidate_records: pd.DataFrame,
    development_history: pd.DataFrame,
    *,
    interpretation_allowed: bool,
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    """Recompute both reviewed baselines and make exact eligible-key paired comparisons."""

    seasonal_records = build_development_evaluation_records(development_history)
    seasonal_records = seasonal_records.loc[
        seasonal_records["validation_window"].isin(
            [window.name for window in APPROVED_DEVELOPMENT_WINDOWS]
        )
    ].copy()
    hw_evaluation = build_development_holt_winters_evaluation(development_history)
    hw_records = hw_evaluation.records
    pairs: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for name, baseline, forecast_column in (
        ("seasonal_naive", seasonal_records, "raw_baseline_forecast"),
        ("holt_winters", hw_records, HW_FORECAST_COLUMN),
    ):
        paired = _paired_records(
            candidate_records,
            baseline,
            baseline_column=forecast_column,
            baseline_name=name,
        )
        summary = summarize_paired_lightgbm_comparison(
            paired,
            baseline_name=name,
            interpretation_allowed=interpretation_allowed,
        )
        pairs[name] = (paired, summary)
    return pairs
