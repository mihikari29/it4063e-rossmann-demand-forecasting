"""Phase 5 development-only Holt-Winters evaluation and paired comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from rossmann_forecasting.forecasting.holt_winters import (
    FORECAST_COLUMN,
    forecast_holt_winters,
)
from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
    ValidationWindow,
    _validated_development_history,
    assemble_evaluation_records,
    validate_development_windows,
)

COVERAGE_GUARDRAIL = 0.99
PAIR_KEYS = ["Store", "forecast_origin", "Date"]


@dataclass(frozen=True)
class HoltWintersEvaluation:
    """Development records plus label-free paths and one-row-per-fit diagnostics."""

    records: pd.DataFrame
    internal_forecasts: pd.DataFrame
    diagnostics: pd.DataFrame


def build_window_holt_winters_evaluation_records(
    historical_development: pd.DataFrame,
    window: ValidationWindow,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate label-free forecasts first, then attach source labels and routing fields."""

    validate_development_windows((window,))
    data = _validated_development_history(historical_development)
    target_mask = data["Date"].between(window.target_start, window.target_end)
    target_keys = data.loc[target_mask, ["Store", "Date"]].copy()
    if target_keys.empty:
        raise ValueError(f"No observed target rows exist for {window.name}.")

    actual_history = data.loc[
        data["Date"].le(window.forecast_origin), ["Store", "Date", "Sales"]
    ].copy()
    model_result = forecast_holt_winters(
        target_keys,
        actual_history_through_origin=actual_history,
        forecast_origin=window.forecast_origin,
        horizon=14,
    )

    # This is intentionally the first point at which target labels are selected.
    target_labels = data.loc[target_mask, ["Store", "Date", "Sales", "Open"]].copy()
    base = model_result.forecasts.loc[
        :, ["Store", "forecast_origin", "Date", "horizon", FORECAST_COLUMN]
    ].rename(columns={FORECAST_COLUMN: "raw_baseline_forecast"})
    evaluation = assemble_evaluation_records(
        base,
        target_labels,
        validation_window=window.name,
    )

    metadata_columns = [
        "Store",
        "forecast_origin",
        "Date",
        "statistical_model",
        "model_fit_success",
        "fit_failure_reason",
        "model_forecast_unclipped",
        FORECAST_COLUMN,
        "forecast_was_clipped",
        "training_history_start",
        "training_history_end",
        "training_history_rows",
    ]
    metadata = model_result.forecasts.loc[:, metadata_columns]
    evaluation = evaluation.merge(
        metadata,
        on=PAIR_KEYS,
        how="left",
        validate="one_to_one",
        sort=False,
    )
    evaluation["forecast_available"] = evaluation[FORECAST_COLUMN].notna()
    evaluation["primary_evaluation_eligible"] = (
        evaluation["source_open"].eq(1)
        & evaluation["actual_sales"].notna()
        & evaluation[FORECAST_COLUMN].notna()
    )
    # The Phase 4 assembler uses its own field name internally; do not expose that alias as if
    # the Holt-Winters candidate were the Seasonal Naive baseline.
    evaluation = evaluation.drop(columns="raw_baseline_forecast")
    diagnostics = model_result.diagnostics.assign(validation_window=window.name)
    internal = model_result.internal_forecasts.assign(validation_window=window.name)
    return evaluation, internal, diagnostics


def build_development_holt_winters_evaluation(
    historical_development: pd.DataFrame,
) -> HoltWintersEvaluation:
    """Evaluate exactly the approved Phase 4 windows, all before the holdout."""

    validate_development_windows()
    data = _validated_development_history(historical_development)
    outputs = [
        build_window_holt_winters_evaluation_records(data, window)
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    records = pd.concat([result[0] for result in outputs], ignore_index=True)
    internal = pd.concat([result[1] for result in outputs], ignore_index=True)
    diagnostics = pd.concat([result[2] for result in outputs], ignore_index=True)
    if records["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        raise AssertionError("Holt-Winters evaluation emitted a final-holdout target.")
    if records.duplicated(PAIR_KEYS).any():
        raise AssertionError("Holt-Winters evaluation contains duplicate forecast keys.")
    return HoltWintersEvaluation(records, internal, diagnostics)


def summarize_holt_winters_development(records: pd.DataFrame) -> dict[str, Any]:
    """Summarize standalone Phase 4-compatible metrics and forecast coverage."""

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
        records, scope="pooled_development", forecast_column=FORECAST_COLUMN
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
    guardrail_passed = bool(rates.notna().all() and rates.ge(COVERAGE_GUARDRAIL).all())
    clipping = _clipping_summary(records)
    return {
        "by_window": window_frame,
        "pooled": pooled,
        "by_horizon": pd.DataFrame(by_horizon),
        "clipping": clipping,
        "coverage_guardrail_threshold": COVERAGE_GUARDRAIL,
        "coverage_guardrail_passed": guardrail_passed,
        "requires_coverage_review": not guardrail_passed,
    }


def _clipping_summary(records: pd.DataFrame) -> pd.DataFrame:
    populations: list[tuple[str, str | None, pd.DataFrame]] = [
        (
            "validation_window",
            window.name,
            records.loc[records["validation_window"].eq(window.name)],
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    populations.append(("pooled_development", None, records))
    rows: list[dict[str, object]] = []
    for scope, window, subset in populations:
        unclipped = pd.to_numeric(subset["model_forecast_unclipped"], errors="coerce")
        clipped = subset["forecast_was_clipped"].fillna(False).astype(bool)
        rows.append(
            {
                "scope": scope,
                "validation_window": window,
                "observed_target_rows": len(subset),
                "available_unclipped_forecast_rows": int(unclipped.notna().sum()),
                "forecast_was_clipped_count": int(clipped.sum()),
                "forecast_was_clipped_rate": (
                    float(clipped.sum() / unclipped.notna().sum())
                    if unclipped.notna().any()
                    else None
                ),
                "minimum_unclipped_forecast": (
                    float(unclipped.min()) if unclipped.notna().any() else None
                ),
            }
        )
    return pd.DataFrame(rows)


def build_paired_comparison_records(
    holt_winters_records: pd.DataFrame,
    seasonal_naive_records: pd.DataFrame,
) -> pd.DataFrame:
    """Reconcile candidate outputs on common keys and keep only identical eligible rows."""

    left = holt_winters_records.loc[
        :,
        PAIR_KEYS
        + ["horizon", "validation_window", "actual_sales", "source_open", FORECAST_COLUMN],
    ].copy()
    right = seasonal_naive_records.loc[
        :,
        PAIR_KEYS
        + ["horizon", "validation_window", "actual_sales", "source_open", "raw_baseline_forecast"],
    ].copy()
    if left.duplicated(PAIR_KEYS).any() or right.duplicated(PAIR_KEYS).any():
        raise ValueError("Paired model records must have unique forecast composite keys.")
    merged = left.merge(
        right,
        on=PAIR_KEYS,
        how="outer",
        validate="one_to_one",
        suffixes=("_holt_winters", "_seasonal_naive"),
        indicator=True,
        sort=False,
    )
    if not merged["_merge"].eq("both").all():
        raise ValueError("Holt-Winters and Seasonal Naive target key populations differ.")
    for label in ("horizon", "validation_window", "actual_sales", "source_open"):
        first = merged[f"{label}_holt_winters"]
        second = merged[f"{label}_seasonal_naive"]
        equal = first.eq(second) | (first.isna() & second.isna())
        if not equal.all():
            raise ValueError(f"Paired model records disagree on shared {label} values.")
    paired_mask = (
        merged[FORECAST_COLUMN].notna()
        & merged["raw_baseline_forecast"].notna()
        & merged["source_open_holt_winters"].eq(1)
        & merged["actual_sales_holt_winters"].notna()
    )
    selected = merged.loc[paired_mask].copy()
    result = pd.DataFrame(
        {
            "Store": selected["Store"],
            "forecast_origin": selected["forecast_origin"],
            "Date": selected["Date"],
            "horizon": selected["horizon_holt_winters"].astype("int8"),
            "validation_window": selected["validation_window_holt_winters"],
            "actual_sales": selected["actual_sales_holt_winters"].astype("float64"),
            "source_open": selected["source_open_holt_winters"].astype("float64"),
            FORECAST_COLUMN: selected[FORECAST_COLUMN].astype("float64"),
            "raw_baseline_forecast": selected["raw_baseline_forecast"].astype("float64"),
        }
    ).reset_index(drop=True)
    result["forecast_available"] = True
    result["primary_evaluation_eligible"] = True
    return result


def summarize_paired_comparison(
    paired_records: pd.DataFrame,
    *,
    interpretation_allowed: bool,
) -> pd.DataFrame:
    """Report both models on identical rows and precommitted MAE comparison fields."""

    populations: list[tuple[str, str | None, int | None, pd.DataFrame]] = [
        (
            "validation_window",
            window.name,
            None,
            paired_records.loc[paired_records["validation_window"].eq(window.name)],
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    populations.append(("pooled_development", None, None, paired_records))
    populations.extend(
        (
            "development_horizon",
            None,
            step,
            paired_records.loc[paired_records["horizon"].eq(step)],
        )
        for step in range(1, 15)
    )

    output: list[dict[str, object]] = []
    for scope, window, horizon, population in populations:
        common = {
            "paired_row_count": len(population),
            "validation_window": window,
            "horizon": horizon,
        }
        statistical = summarize_forecast_metrics(
            population,
            scope=scope,
            validation_window=window,
            horizon=horizon,
            forecast_column=FORECAST_COLUMN,
        )
        baseline = summarize_forecast_metrics(
            population,
            scope=scope,
            validation_window=window,
            horizon=horizon,
            forecast_column="raw_baseline_forecast",
        )
        delta = None
        relative = None
        relative_reason = None
        lower_model = None
        if statistical["mae"] is not None and baseline["mae"] is not None:
            delta = statistical["mae"] - baseline["mae"]
            if baseline["mae"] > 0:
                relative = delta / baseline["mae"]
            else:
                relative_reason = "Seasonal Naive paired MAE is zero."
            if statistical["mae"] < baseline["mae"]:
                lower_model = "holt_winters"
            elif statistical["mae"] > baseline["mae"]:
                lower_model = "seasonal_naive"
            else:
                lower_model = "tie"
        if not interpretation_allowed:
            lower_model = None
        output.append(
            {
                **common,
                "holt_winters_mae": statistical["mae"],
                "holt_winters_rmse": statistical["rmse"],
                "holt_winters_mape": statistical["mape"],
                "holt_winters_wape": statistical["wape"],
                "seasonal_naive_mae": baseline["mae"],
                "seasonal_naive_rmse": baseline["rmse"],
                "seasonal_naive_mape": baseline["mape"],
                "seasonal_naive_wape": baseline["wape"],
                "mae_difference_holt_winters_minus_seasonal_naive": delta,
                "relative_mae_change": relative,
                "relative_mae_change_unavailable_reason": relative_reason,
                "lower_paired_mae_model": lower_model,
                "comparison_interpretation": (
                    "allowed_by_coverage_guardrail"
                    if interpretation_allowed
                    else "suppressed_by_open_label_coverage_guardrail"
                ),
                "paired_mape_rows": statistical["mape_rows"],
                "paired_zero_actual_rows_excluded_from_mape": statistical[
                    "zero_actual_rows_excluded_from_mape"
                ],
                "paired_wape_actual_denominator": statistical["wape_actual_denominator"],
            }
        )
    return pd.DataFrame(output)


def summarize_fit_diagnostics(diagnostics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate fit, failure, warning, convergence, and full-path clipping counts."""

    rows: list[dict[str, object]] = []
    populations = [
        (
            "validation_window",
            window.name,
            diagnostics.loc[diagnostics["validation_window"].eq(window.name)],
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    populations.append(("pooled_development", None, diagnostics))
    for scope, window, subset in populations:
        successful_horizons = pd.to_numeric(
            subset.loc[subset["model_fit_success"], "forecast_horizon"], errors="coerce"
        )
        successful_forecast_steps = int(successful_horizons.sum())
        failure_counts = subset["fit_failure_reason"].dropna().value_counts().sort_index()
        warning_counts: dict[str, int] = {}
        for categories in subset["warning_categories"].dropna():
            for category in str(categories).split("|"):
                warning_counts[category] = warning_counts.get(category, 0) + 1
        rows.append(
            {
                "scope": scope,
                "validation_window": window,
                "store_origin_fits": len(subset),
                "successful_fits": int(subset["model_fit_success"].sum()),
                "unavailable_fits": int((~subset["model_fit_success"].astype(bool)).sum()),
                "failure_categories": "|".join(
                    f"{category}:{count}" for category, count in failure_counts.items()
                ),
                "warning_count": int(subset["warning_count"].sum()),
                "warning_categories": "|".join(
                    f"{category}:{count}" for category, count in sorted(warning_counts.items())
                ),
                "optimizer_nonconverged_fits": int(subset["optimizer_converged"].eq(False).sum()),
                "forecast_was_clipped_count": int(subset["forecast_was_clipped_count"].sum()),
                "forecast_was_clipped_rate": (
                    float(subset["forecast_was_clipped_count"].sum() / successful_forecast_steps)
                    if successful_forecast_steps
                    else None
                ),
                "minimum_unclipped_forecast": (
                    float(subset["minimum_unclipped_forecast"].min())
                    if subset["minimum_unclipped_forecast"].notna().any()
                    else None
                ),
            }
        )
    return pd.DataFrame(rows)


def evaluate_phase5_development(
    historical_development: pd.DataFrame,
    seasonal_naive_records: pd.DataFrame,
) -> dict[str, Any]:
    """Build candidate and fair-pair summaries from a shared, development-only input."""

    result = build_development_holt_winters_evaluation(historical_development)
    standalone = summarize_holt_winters_development(result.records)
    paired = build_paired_comparison_records(result.records, seasonal_naive_records)
    paired_summary = summarize_paired_comparison(
        paired, interpretation_allowed=standalone["coverage_guardrail_passed"]
    )
    return {
        "evaluation": result,
        "standalone": standalone,
        "paired_records": paired,
        "paired_summary": paired_summary,
        "fit_diagnostics_summary": summarize_fit_diagnostics(result.diagnostics),
    }
