"""Open-day development metrics and explicit raw-forecast coverage summaries."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.forecasting.validation import APPROVED_DEVELOPMENT_WINDOWS

_REQUIRED_COLUMNS = {
    "actual_sales",
    "source_open",
    "raw_baseline_forecast",
    "forecast_available",
    "primary_evaluation_eligible",
    "horizon",
    "validation_window",
}


def _validated_metric_frame(
    records: pd.DataFrame,
    *,
    forecast_column: str = "raw_baseline_forecast",
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    required_columns = _REQUIRED_COLUMNS.difference({"raw_baseline_forecast"}) | {forecast_column}
    missing = required_columns.difference(records.columns)
    if missing:
        raise ValueError(f"Forecast records are missing metric fields: {sorted(missing)}.")

    data = records.copy()
    actual = pd.to_numeric(data["actual_sales"], errors="coerce")
    invalid_actual = data["actual_sales"].notna() & actual.isna()
    if actual.notna().any():
        values = actual.dropna().to_numpy(dtype=np.float64)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("actual_sales must be finite and non-negative when present.")
    if invalid_actual.any():
        raise ValueError("actual_sales contains non-numeric values.")

    raw = pd.to_numeric(data[forecast_column], errors="coerce")
    if raw.notna().any():
        available = raw.dropna().to_numpy(dtype=np.float64)
        if not np.isfinite(available).all() or (available < 0).any():
            raise ValueError("Available raw forecasts must be finite and non-negative.")
    raw_available = raw.notna()
    if data["forecast_available"].isna().any():
        raise ValueError("forecast_available must not be missing.")
    recorded_available = data["forecast_available"].astype(bool)
    if not recorded_available.equals(raw_available.astype(bool)):
        raise ValueError("forecast_available must match raw forecast nullness.")

    source_open = pd.to_numeric(data["source_open"], errors="coerce")
    invalid_open = data["source_open"].notna() & source_open.isna()
    invalid_open |= source_open.notna() & ~source_open.isin([0, 1])
    if invalid_open.any():
        raise ValueError("source_open must be 0, 1, or missing.")

    open_label = source_open.eq(1) & actual.notna()
    eligible = open_label & raw_available
    if data["primary_evaluation_eligible"].isna().any():
        raise ValueError("primary_evaluation_eligible must not be missing.")
    recorded_eligible = data["primary_evaluation_eligible"].astype(bool)
    if not recorded_eligible.equals(eligible.astype(bool)):
        raise ValueError(
            "primary_evaluation_eligible must equal source_open == 1, observed Sales, "
            "and available raw forecast."
        )

    data["actual_sales"] = actual.astype("float64")
    data[forecast_column] = raw.astype("float64")
    data["source_open"] = source_open.astype("float64")
    return data, raw_available, open_label


def summarize_forecast_metrics(
    records: pd.DataFrame,
    *,
    scope: str,
    validation_window: str | None = None,
    horizon: int | None = None,
    forecast_column: str = "raw_baseline_forecast",
) -> dict[str, Any]:
    """Calculate approved metrics plus explicit forecast-availability denominators."""

    data, raw_available, open_label = _validated_metric_frame(
        records, forecast_column=forecast_column
    )
    eligible = data["primary_evaluation_eligible"].astype(bool)
    target_rows = len(data)
    available_rows = int(raw_available.sum())
    open_label_rows = int(open_label.sum())
    open_available_rows = int((open_label & raw_available).sum())

    if target_rows:
        all_coverage: float | None = available_rows / target_rows
        all_coverage_reason = None
    else:
        all_coverage = None
        all_coverage_reason = "No observed target rows in this summary population."
    if open_label_rows:
        open_coverage: float | None = open_available_rows / open_label_rows
        open_coverage_reason = None
    else:
        open_coverage = None
        open_coverage_reason = "No observed Open=1 targets with Sales in this population."

    eligible_rows = int(eligible.sum())
    actual = data.loc[eligible, "actual_sales"].to_numpy(dtype=np.float64)
    forecast = data.loc[eligible, forecast_column].to_numpy(dtype=np.float64)
    absolute_error = np.abs(actual - forecast)

    if eligible_rows:
        mae: float | None = float(absolute_error.mean())
        rmse: float | None = float(np.sqrt(np.square(actual - forecast).mean()))
        metrics_reason = None
    else:
        mae = None
        rmse = None
        metrics_reason = "No primary evaluation-eligible rows."

    positive_actual = actual > 0
    mape_rows = int(positive_actual.sum())
    zero_actual_excluded = int((actual == 0).sum())
    if mape_rows:
        mape: float | None = float(
            (
                np.abs(actual[positive_actual] - forecast[positive_actual])
                / actual[positive_actual]
            ).mean()
            * 100.0
        )
        mape_reason = None
    else:
        mape = None
        mape_reason = (
            "No primary eligible rows have actual_sales > 0." if eligible_rows else metrics_reason
        )
    mape_coverage = mape_rows / eligible_rows if eligible_rows else None

    wape_denominator = float(actual.sum())
    if eligible_rows and wape_denominator > 0:
        wape: float | None = float(absolute_error.sum() / wape_denominator)
        wape_reason = None
    else:
        wape = None
        wape_reason = (
            "Sum of actual_sales is zero for primary eligible rows."
            if eligible_rows
            else metrics_reason
        )

    return {
        "scope": scope,
        "validation_window": validation_window,
        "horizon": horizon,
        "observed_target_rows": target_rows,
        "forecast_available_rows": available_rows,
        "forecast_available_denominator_rows": target_rows,
        "raw_forecast_coverage_rate": all_coverage,
        "raw_forecast_coverage_unavailable_reason": all_coverage_reason,
        "open_label_rows": open_label_rows,
        "open_label_forecast_available_rows": open_available_rows,
        "open_label_coverage_denominator_rows": open_label_rows,
        "open_label_forecast_coverage_rate": open_coverage,
        "open_label_coverage_unavailable_reason": open_coverage_reason,
        "eligible_rows": eligible_rows,
        "mae": mae,
        "rmse": rmse,
        "metrics_unavailable_reason": metrics_reason,
        "mape": mape,
        "mape_rows": mape_rows,
        "zero_actual_rows_excluded_from_mape": zero_actual_excluded,
        "mape_coverage": mape_coverage,
        "mape_unavailable_reason": mape_reason,
        "wape": wape,
        "wape_actual_denominator": wape_denominator,
        "wape_unavailable_reason": wape_reason,
    }


def summarize_development_evaluation(records: pd.DataFrame) -> dict[str, Any]:
    """Summarize each approved window, pooled development rows, and horizons 1..14."""

    if "validation_window" not in records or "horizon" not in records:
        raise ValueError("Development forecast records require validation_window and horizon.")

    by_window = [
        summarize_forecast_metrics(
            records.loc[records["validation_window"].eq(window.name)],
            scope="validation_window",
            validation_window=window.name,
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    pooled = summarize_forecast_metrics(records, scope="pooled_development")
    by_horizon = [
        summarize_forecast_metrics(
            records.loc[pd.to_numeric(records["horizon"], errors="coerce").eq(step)],
            scope="development_horizon",
            horizon=step,
        )
        for step in range(1, 15)
    ]
    coverage_fields = (
        "scope",
        "validation_window",
        "observed_target_rows",
        "forecast_available_rows",
        "forecast_available_denominator_rows",
        "raw_forecast_coverage_rate",
        "raw_forecast_coverage_unavailable_reason",
        "open_label_rows",
        "open_label_forecast_available_rows",
        "open_label_coverage_denominator_rows",
        "open_label_forecast_coverage_rate",
        "open_label_coverage_unavailable_reason",
    )
    return {
        "by_window": pd.DataFrame(by_window),
        "pooled": pooled,
        "by_horizon": pd.DataFrame(by_horizon),
        "coverage_by_window": pd.DataFrame(by_window).loc[:, coverage_fields],
    }
