"""Regression tests for explicit Phase 4 evaluation populations and metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.forecasting.metrics import (
    summarize_development_evaluation,
    summarize_forecast_metrics,
)


def _records(
    actual: list[float | None],
    forecast: list[float | None],
    open_values: list[float | None],
) -> pd.DataFrame:
    raw = pd.Series(forecast, dtype="float64")
    actual_sales = pd.Series(actual, dtype="float64")
    source_open = pd.Series(open_values, dtype="float64")
    return pd.DataFrame(
        {
            "actual_sales": actual_sales,
            "source_open": source_open,
            "raw_baseline_forecast": raw,
            "forecast_available": raw.notna(),
            "primary_evaluation_eligible": (source_open.eq(1) & actual_sales.notna() & raw.notna()),
            "horizon": range(1, len(raw) + 1),
            "validation_window": ["validation_1"] * len(raw),
        }
    )


def test_closed_rows_excluded_but_open_zero_sales_retained_and_mape_reported() -> None:
    records = _records(
        actual=[0.0, 100.0, 50.0, 10.0],
        forecast=[20.0, 120.0, 0.0, None],
        open_values=[1.0, 1.0, 0.0, 1.0],
    )

    summary = summarize_forecast_metrics(records, scope="test")

    assert summary["observed_target_rows"] == 4
    assert summary["eligible_rows"] == 2
    assert summary["mae"] == 20.0
    assert summary["rmse"] == pytest.approx(np.sqrt(400.0))
    assert summary["mape"] == 20.0
    assert summary["mape_rows"] == 1
    assert summary["zero_actual_rows_excluded_from_mape"] == 1
    assert summary["mape_coverage"] == 0.5
    assert summary["wape"] == pytest.approx(40.0 / 100.0)
    assert summary["forecast_available_rows"] == 3
    assert summary["forecast_available_denominator_rows"] == 4
    assert summary["raw_forecast_coverage_rate"] == 0.75
    assert summary["open_label_rows"] == 3
    assert summary["open_label_forecast_available_rows"] == 2


def test_wape_zero_denominator_and_empty_population_have_reasons() -> None:
    zero_actual = _records([0.0], [4.0], [1.0])
    zero_summary = summarize_forecast_metrics(zero_actual, scope="zero")
    assert zero_summary["wape"] is None
    assert "actual_sales is zero" in zero_summary["wape_unavailable_reason"]
    assert zero_summary["mape"] is None
    assert zero_summary["mape_rows"] == 0

    empty = _records([], [], [])
    empty_summary = summarize_forecast_metrics(empty, scope="empty")
    assert empty_summary["mae"] is None
    assert empty_summary["rmse"] is None
    assert empty_summary["mape"] is None
    assert empty_summary["wape"] is None
    assert empty_summary["metrics_unavailable_reason"]
    assert empty_summary["raw_forecast_coverage_rate"] is None
    assert empty_summary["raw_forecast_coverage_unavailable_reason"]
    assert empty_summary["open_label_forecast_coverage_rate"] is None
    assert empty_summary["open_label_coverage_unavailable_reason"]


def test_pooled_metrics_are_computed_from_rows_and_horizon_table_is_complete() -> None:
    first = _records([10.0], [0.0], [1.0]).assign(validation_window="validation_1")
    second = _records([100.0, 100.0], [80.0, 80.0], [1.0, 1.0]).assign(
        validation_window="validation_2"
    )
    records = pd.concat([first, second], ignore_index=True)

    result = summarize_development_evaluation(records)

    assert result["pooled"]["mae"] == pytest.approx(50.0 / 3.0)
    assert result["by_window"].loc[0, "mae"] == 10.0
    assert result["by_window"].loc[1, "mae"] == 20.0
    assert result["by_horizon"].shape[0] == 14
    assert result["by_horizon"]["horizon"].tolist() == list(range(1, 15))
    assert result["by_horizon"].loc[2, "mae"] is None or pd.isna(result["by_horizon"].loc[2, "mae"])
