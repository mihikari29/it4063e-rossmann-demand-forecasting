"""Synthetic regression tests for the Phase 4 weekly baseline and evaluator."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.forecasting.seasonal_naive import forecast_seasonal_naive
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    ValidationWindow,
    assemble_evaluation_records,
    build_window_evaluation_records,
    validate_development_windows,
)


def _history(*, remove_dates: tuple[str, ...] = ()) -> pd.DataFrame:
    dates = pd.date_range("2015-01-01", "2015-01-14", freq="D")
    history = pd.DataFrame({"Store": 1, "Date": dates, "Sales": dates.day.astype(float)})
    return history.loc[~history["Date"].isin(pd.to_datetime(remove_dates))].reset_index(drop=True)


def _targets(dates: list[str], *, store: int = 1) -> pd.DataFrame:
    return pd.DataFrame({"Store": store, "Date": pd.to_datetime(dates)})


def test_exact_same_store_calendar_week_and_recursive_horizons() -> None:
    origin = "2015-01-14"
    targets = _targets(["2015-01-15", "2015-01-21", "2015-01-22", "2015-01-28"])
    history = _history()
    original_targets = targets.copy(deep=True)
    original_history = history.copy(deep=True)

    result = forecast_seasonal_naive(
        targets,
        actual_history_through_origin=history,
        forecast_origin=origin,
    )

    assert result["horizon"].tolist() == [1, 7, 8, 14]
    assert result["raw_baseline_forecast"].tolist() == [8.0, 14.0, 8.0, 14.0]
    pd.testing.assert_frame_equal(targets, original_targets)
    pd.testing.assert_frame_equal(history, original_history)


def test_missing_exact_weekly_history_is_null_without_previous_row_fallback() -> None:
    history = _history(remove_dates=("2015-01-08",))
    targets = _targets(["2015-01-15", "2015-01-22"])

    result = forecast_seasonal_naive(
        targets,
        actual_history_through_origin=history,
        forecast_origin="2015-01-14",
    )

    assert result["raw_baseline_forecast"].isna().all()


def test_observed_zero_is_valid_and_recursive_dependency_propagates() -> None:
    history = _history()
    history.loc[history["Date"].eq(pd.Timestamp("2015-01-08")), "Sales"] = 0
    targets = _targets(["2015-01-15", "2015-01-22"])

    result = forecast_seasonal_naive(
        targets,
        actual_history_through_origin=history,
        forecast_origin="2015-01-14",
    )

    assert result["raw_baseline_forecast"].tolist() == [0.0, 0.0]


def test_sparse_h8_target_uses_internal_h1_state_and_emits_only_observed_keys() -> None:
    targets = _targets(["2015-01-22"])
    result = forecast_seasonal_naive(
        targets,
        actual_history_through_origin=_history(),
        forecast_origin="2015-01-14",
    )

    assert result[["Store", "Date"]].to_dict("records") == [
        {"Store": 1, "Date": pd.Timestamp("2015-01-22")}
    ]
    assert result["horizon"].tolist() == [8]
    assert result["raw_baseline_forecast"].tolist() == [8.0]


def test_store_histories_are_isolated() -> None:
    history = pd.concat(
        [_history(), _history().assign(Store=2, Sales=999.0)],
        ignore_index=True,
    )
    targets = pd.DataFrame({"Store": [1, 2], "Date": pd.to_datetime(["2015-01-15"] * 2)})

    result = forecast_seasonal_naive(
        targets,
        actual_history_through_origin=history,
        forecast_origin="2015-01-14",
    )

    assert result["raw_baseline_forecast"].tolist() == [8.0, 999.0]


def test_future_actuals_and_invalid_store_keys_are_rejected() -> None:
    targets = _targets(["2015-01-15"])
    future_history = pd.concat(
        [_history(), pd.DataFrame({"Store": [1], "Date": ["2015-01-15"], "Sales": [50]})],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="after forecast_origin"):
        forecast_seasonal_naive(
            targets,
            actual_history_through_origin=future_history,
            forecast_origin="2015-01-14",
        )

    invalid_targets = targets.assign(Store=1.5)
    with pytest.raises(ValueError, match="positive, exact integer identifiers"):
        forecast_seasonal_naive(
            invalid_targets,
            actual_history_through_origin=_history(),
            forecast_origin="2015-01-14",
        )


@pytest.mark.parametrize("sales", [np.nan, np.inf, -1.0])
def test_nonfinite_missing_or_negative_actual_history_sales_are_rejected(sales: float) -> None:
    history = _history()
    history.loc[history["Date"].eq(pd.Timestamp("2015-01-08")), "Sales"] = sales

    with pytest.raises(ValueError, match="finite and non-missing|non-negative"):
        forecast_seasonal_naive(
            _targets(["2015-01-15"]),
            actual_history_through_origin=history,
            forecast_origin="2015-01-14",
        )


def test_forecaster_rejects_nonmidnight_origin_extra_target_fields_and_long_horizon() -> None:
    with pytest.raises(ValueError, match="without a time component"):
        forecast_seasonal_naive(
            _targets(["2015-01-15"]),
            actual_history_through_origin=_history(),
            forecast_origin="2015-01-14 12:00",
        )
    with pytest.raises(ValueError, match="exactly Store and Date"):
        forecast_seasonal_naive(
            _targets(["2015-01-15"]).assign(Sales=100),
            actual_history_through_origin=_history(),
            forecast_origin="2015-01-14",
        )
    with pytest.raises(ValueError, match="within horizons 1..14"):
        forecast_seasonal_naive(
            _targets(["2015-01-29"]),
            actual_history_through_origin=_history(),
            forecast_origin="2015-01-14",
        )


def test_target_labels_and_open_do_not_change_raw_forecasts() -> None:
    origin = "2015-05-22"
    dates = pd.date_range("2015-05-16", "2015-06-05", freq="D")
    base = pd.DataFrame(
        {
            "Store": 1,
            "Date": dates,
            "Sales": dates.day.astype(float),
            "Open": 1,
            "Customers": 10,
        }
    )
    changed = base.copy(deep=True)
    targets = changed["Date"].gt(pd.Timestamp(origin))
    changed.loc[targets, "Sales"] = 900_000
    changed.loc[targets, "Open"] = 0
    changed.loc[targets, "Customers"] = 800_000
    window = ValidationWindow(
        "synthetic", pd.Timestamp(origin), pd.Timestamp("2015-05-23"), pd.Timestamp("2015-06-05")
    )

    first = build_window_evaluation_records(base, window)
    second = build_window_evaluation_records(changed, window)

    pd.testing.assert_series_equal(first["raw_baseline_forecast"], second["raw_baseline_forecast"])
    assert "Customers" not in first.columns
    assert first["actual_sales"].ne(second["actual_sales"]).all()
    assert first["source_open"].eq(1).all()
    assert second["source_open"].eq(0).all()


def test_open_routing_is_separate_from_raw_forecasts_and_unknown_stays_null() -> None:
    origin = pd.Timestamp("2015-01-14")
    keys = _targets(["2015-01-15", "2015-01-16", "2015-01-17"])
    raw = forecast_seasonal_naive(
        keys,
        actual_history_through_origin=_history(),
        forecast_origin=origin,
    )
    labels = keys.assign(Sales=[100.0, 200.0, 300.0], Open=[0.0, 1.0, np.nan])

    records = assemble_evaluation_records(raw, labels, validation_window="synthetic")

    assert records["raw_baseline_forecast"].tolist() == [8.0, 9.0, 10.0]
    assert records["operational_forecast"].iloc[0] == 0
    assert records["operational_forecast"].iloc[1] == 9
    assert pd.isna(records["operational_forecast"].iloc[2])
    assert not records["primary_evaluation_eligible"].iloc[0]
    assert records["primary_evaluation_eligible"].iloc[1]
    assert not records["primary_evaluation_eligible"].iloc[2]


def test_approved_windows_are_fourteen_days_ordered_and_before_holdout() -> None:
    validate_development_windows()
    assert len(APPROVED_DEVELOPMENT_WINDOWS) == 3
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        assert (window.target_end - window.target_start).days == 13
        assert window.target_start == window.forecast_origin + pd.Timedelta(days=1)
        assert window.target_end < pd.Timestamp("2015-07-04")


def test_output_keys_are_unique_and_horizon_matches_origin_delta() -> None:
    result = forecast_seasonal_naive(
        _targets(["2015-01-15", "2015-01-22"]),
        actual_history_through_origin=_history(),
        forecast_origin="2015-01-14",
    )

    assert not result.duplicated(["Store", "forecast_origin", "Date"]).any()
    assert ((result["Date"] - result["forecast_origin"]).dt.days == result["horizon"]).all()
