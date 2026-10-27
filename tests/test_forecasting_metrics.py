"""Regression tests for explicit Phase 4 evaluation populations and metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.forecasting.holt_winters_evaluation import (
    summarize_holt_winters_development,
)
from rossmann_forecasting.forecasting.lightgbm_evaluation import summarize_lightgbm_development
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


@pytest.mark.parametrize(
    "summarizer,forecast_column",
    [
        pytest.param(
            summarize_holt_winters_development, "raw_statistical_forecast", id="holt_winters"
        ),
        pytest.param(summarize_lightgbm_development, "raw_lightgbm_forecast", id="lightgbm"),
    ],
)
@pytest.mark.parametrize("empty", [False, True], ids=["populated", "empty"])
@pytest.mark.parametrize(
    "missing_columns,error_type,error_args",
    [
        (("validation_window",), KeyError, ("validation_window",)),
        (
            ("horizon",),
            ValueError,
            ("Forecast records are missing metric fields: ['horizon'].",),
        ),
        (("validation_window", "horizon"), KeyError, ("validation_window",)),
        (
            ("horizon", "actual_sales"),
            ValueError,
            ("Forecast records are missing metric fields: ['actual_sales', 'horizon'].",),
        ),
    ],
)
def test_model_summary_preserves_original_missing_field_errors(
    summarizer, forecast_column, empty, missing_columns, error_type, error_args
) -> None:
    records = _records([10.0], [8.0], [1.0]).rename(
        columns={"raw_baseline_forecast": forecast_column}
    )
    if empty:
        records = records.iloc[:0]
    records = records.drop(columns=list(missing_columns))
    original = records.copy(deep=True)

    with pytest.raises(error_type) as error:
        summarizer(records)

    assert type(error.value) is error_type
    assert error.value.args == error_args
    assert str(error.value) == str(error_type(*error_args))
    pd.testing.assert_frame_equal(records, original)


@pytest.mark.parametrize(
    "missing_columns",
    [("validation_window",), ("horizon",), ("validation_window", "horizon")],
)
def test_baseline_summary_preserves_explicit_development_field_guard(missing_columns) -> None:
    records = _records([10.0], [8.0], [1.0]).drop(columns=list(missing_columns))

    with pytest.raises(ValueError) as error:
        summarize_development_evaluation(records)

    assert type(error.value) is ValueError
    assert error.value.args == (
        "Development forecast records require validation_window and horizon.",
    )


@pytest.mark.parametrize(
    "summarizer,forecast_column,extra_keys",
    [
        pytest.param(
            summarize_holt_winters_development,
            "raw_statistical_forecast",
            ("clipping",),
            id="holt_winters",
        ),
        pytest.param(summarize_lightgbm_development, "raw_lightgbm_forecast", (), id="lightgbm"),
    ],
)
@pytest.mark.parametrize(
    "actual,forecast,open_values",
    [
        ([10.0, 30.0, 0.0, 7.0], [8.0, 31.0, 0.0, None], [1.0, 1.0, 1.0, 1.0]),
        ([10.0, 0.0, None, 5.0], [8.0, 20.0, 4.0, 6.0], [1.0, 0.0, 1.0, None]),
        ([0.0, 0.0], [0.0, 4.0], [1.0, 1.0]),
        ([10.0, 20.0], [None, None], [1.0, 1.0]),
        ([], [], []),
    ],
    ids=["partial", "mixed_labels", "zero_denominators", "unavailable", "empty"],
)
def test_model_summary_retains_shared_metric_tables_and_output_schema(
    summarizer, forecast_column, extra_keys, actual, forecast, open_values
) -> None:
    baseline_records = _records(actual, forecast, open_values)
    baseline_records["validation_window"] = [
        f"validation_{index % 3 + 1}" for index in range(len(baseline_records))
    ]
    expected = summarize_development_evaluation(baseline_records)
    records = baseline_records.rename(columns={"raw_baseline_forecast": forecast_column})
    records["model_forecast_unclipped"] = records[forecast_column]
    records["forecast_was_clipped"] = False
    original = records.copy(deep=True)

    actual_summary = summarizer(records)

    assert tuple(actual_summary) == (
        "by_window",
        "pooled",
        "by_horizon",
        *extra_keys,
        "coverage_guardrail_threshold",
        "coverage_guardrail_passed",
        "requires_coverage_review",
    )
    for key in ("by_window", "by_horizon"):
        pd.testing.assert_frame_equal(actual_summary[key], expected[key], check_exact=True)
    assert actual_summary["pooled"] == expected["pooled"]
    assert actual_summary["coverage_guardrail_threshold"] == 0.99
    pd.testing.assert_frame_equal(records, original)
