"""Synthetic regression coverage for the approved Phase 5 candidate."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.forecasting import holt_winters as hw
from rossmann_forecasting.forecasting.holt_winters_evaluation import (
    build_development_holt_winters_evaluation,
    build_paired_comparison_records,
    build_window_holt_winters_evaluation_records,
    summarize_fit_diagnostics,
    summarize_holt_winters_development,
    summarize_paired_comparison,
)
from rossmann_forecasting.forecasting.holt_winters_runner import _json_safe
from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics
from rossmann_forecasting.forecasting.runner import _read_development_history
from rossmann_forecasting.forecasting.seasonal_naive import forecast_seasonal_naive
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    ValidationWindow,
    assemble_evaluation_records,
)

ORIGIN = pd.Timestamp("2015-05-22")


def _history(days: int = 35, *, store: int = 1, origin: pd.Timestamp = ORIGIN) -> pd.DataFrame:
    dates = pd.date_range(end=origin, periods=days, freq="D")
    return pd.DataFrame(
        {"Store": store, "Date": dates, "Sales": 100.0 + np.arange(days, dtype=float)}
    )


def _targets(dates: list[pd.Timestamp | str], *, store: int = 1) -> pd.DataFrame:
    return pd.DataFrame({"Store": store, "Date": pd.to_datetime(dates)})


class _FakeFit:
    def __init__(self, values: list[float], *, calls: list[int], warning: bool = False):
        self.values = values
        self.calls = calls
        self.mle_retvals = {"success": True, "warnflag": 0}
        self.warning = warning

    def forecast(self, steps: int) -> list[float]:
        self.calls.append(steps)
        if self.warning:
            warnings.warn("expected synthetic warning", RuntimeWarning, stacklevel=1)
        return self.values


def _patch_model(monkeypatch: pytest.MonkeyPatch, values: list[float] | None = None):
    received: list[tuple[pd.Series, dict[str, object]]] = []
    forecast_calls: list[int] = []

    class FakeModel:
        def fit(self, *, optimized: bool) -> _FakeFit:
            assert optimized is True
            return _FakeFit(values or [10.0] * 14, calls=forecast_calls)

    def fake_constructor(series: pd.Series, **kwargs: object) -> FakeModel:
        received.append((series.copy(deep=True), kwargs))
        return FakeModel()

    monkeypatch.setattr(hw, "ExponentialSmoothing", fake_constructor)
    return received, forecast_calls


def test_extracts_full_latest_contiguous_segment_and_stops_at_gaps() -> None:
    history = _history(days=40)
    history = history.loc[~history["Date"].eq(ORIGIN - pd.Timedelta(days=5))].copy()
    target = _targets([ORIGIN + pd.Timedelta(days=1)])

    result = hw.forecast_holt_winters(
        target,
        actual_history_through_origin=history,
        forecast_origin=ORIGIN,
    )

    diagnostic = result.diagnostics.iloc[0]
    assert diagnostic["contiguous_history_rows"] == 5
    assert diagnostic["history_stop_reason"] == "missing_calendar_date"
    assert diagnostic["fit_failure_reason"] == "insufficient_contiguous_history"
    assert diagnostic["training_history_rows"] == 0
    assert result.internal_forecasts["forecast_available"].eq(False).all()


@pytest.mark.parametrize(("days", "available"), [(27, False), (28, True)])
def test_minimum_contiguous_history_is_exact(monkeypatch, days: int, available: bool) -> None:
    received, calls = _patch_model(monkeypatch)
    result = hw.forecast_holt_winters(
        _targets([ORIGIN + pd.Timedelta(days=1)]),
        actual_history_through_origin=_history(days),
        forecast_origin=ORIGIN,
    )
    assert bool(result.diagnostics.loc[0, "model_fit_success"]) is available
    assert result.diagnostics.loc[0, "training_history_rows"] == (days if available else 0)
    assert len(received) == int(available)
    assert calls == ([14] if available else [])


def test_fit_receives_only_origin_censored_sales_and_forecasts_fourteen_once(monkeypatch) -> None:
    received, calls = _patch_model(monkeypatch)
    history = _history(days=42)
    original = history.copy(deep=True)
    targets = _targets([ORIGIN + pd.Timedelta(days=8)])
    result = hw.forecast_holt_winters(
        targets,
        actual_history_through_origin=history,
        forecast_origin=ORIGIN,
    )

    assert len(received) == 1
    series, kwargs = received[0]
    assert series.index.max() == ORIGIN
    assert series.size == 42
    assert series.name == "Sales"
    assert set(kwargs) == {
        "trend",
        "damped_trend",
        "seasonal",
        "seasonal_periods",
        "initialization_method",
        "use_boxcox",
    }
    assert kwargs == {
        "trend": "add",
        "damped_trend": False,
        "seasonal": "add",
        "seasonal_periods": 7,
        "initialization_method": "estimated",
        "use_boxcox": False,
    }
    assert calls == [14]
    assert len(result.internal_forecasts) == 14
    assert result.forecasts["horizon"].tolist() == [8]
    assert result.forecasts.loc[0, "Date"] == ORIGIN + pd.Timedelta(days=8)
    pd.testing.assert_frame_equal(history, original)


def test_exactly_observed_target_keys_are_emitted_and_input_fields_are_narrow(monkeypatch) -> None:
    _patch_model(monkeypatch)
    targets = _targets([ORIGIN + pd.Timedelta(days=1), ORIGIN + pd.Timedelta(days=14)])
    result = hw.forecast_holt_winters(
        targets,
        actual_history_through_origin=_history(),
        forecast_origin=ORIGIN,
    )
    assert result.forecasts["horizon"].tolist() == [1, 14]
    assert len(result.forecasts) == 2
    assert not result.forecasts.duplicated(["Store", "forecast_origin", "Date"]).any()
    with pytest.raises(ValueError, match="exactly Store and Date"):
        hw.forecast_holt_winters(
            targets.assign(Sales=100),
            actual_history_through_origin=_history(),
            forecast_origin=ORIGIN,
        )
    with pytest.raises(ValueError, match="exactly Store, Date, and Sales"):
        hw.forecast_holt_winters(
            targets,
            actual_history_through_origin=_history().assign(Customers=1),
            forecast_origin=ORIGIN,
        )


def test_missing_origin_invalid_sales_and_future_actuals_are_unavailable_or_rejected(
    monkeypatch,
) -> None:
    _patch_model(monkeypatch)
    target = _targets([ORIGIN + pd.Timedelta(days=1)])
    no_origin = _history().loc[lambda frame: frame["Date"].lt(ORIGIN)]
    missing = hw.forecast_holt_winters(
        target, actual_history_through_origin=no_origin, forecast_origin=ORIGIN
    )
    assert missing.diagnostics.loc[0, "fit_failure_reason"] == "missing_origin_row"

    invalid = _history()
    invalid.loc[invalid["Date"].eq(ORIGIN), "Sales"] = np.inf
    unavailable = hw.forecast_holt_winters(
        target, actual_history_through_origin=invalid, forecast_origin=ORIGIN
    )
    assert unavailable.diagnostics.loc[0, "fit_failure_reason"] == "unusable_origin_sales"

    future = pd.concat(
        [
            _history(),
            pd.DataFrame({"Store": [1], "Date": [ORIGIN + pd.Timedelta(days=1)], "Sales": [1]}),
        ]
    )
    with pytest.raises(ValueError, match="after forecast_origin"):
        hw.forecast_holt_winters(
            target, actual_history_through_origin=future, forecast_origin=ORIGIN
        )


def test_negative_model_outputs_are_preserved_and_clipped(monkeypatch) -> None:
    outputs = [-5.0, 3.0] + [1.0] * 12

    class FakeFit:
        mle_retvals = {"success": False, "warnflag": 1}

        def forecast(self, steps: int) -> list[float]:
            assert steps == 14
            return outputs

    class FakeModel:
        def fit(self, *, optimized: bool) -> FakeFit:
            assert optimized
            return FakeFit()

    monkeypatch.setattr(hw, "ExponentialSmoothing", lambda *args, **kwargs: FakeModel())
    result = hw.forecast_holt_winters(
        _targets([ORIGIN + pd.Timedelta(days=1), ORIGIN + pd.Timedelta(days=2)]),
        actual_history_through_origin=_history(),
        forecast_origin=ORIGIN,
    )
    assert result.forecasts["model_forecast_unclipped"].tolist() == [-5.0, 3.0]
    assert result.forecasts["raw_statistical_forecast"].tolist() == [0.0, 3.0]
    assert result.forecasts["forecast_was_clipped"].tolist() == [True, False]
    assert result.diagnostics.loc[0, "forecast_was_clipped_count"] == 1
    assert result.diagnostics.loc[0, "minimum_unclipped_forecast"] == -5.0
    assert not bool(result.diagnostics.loc[0, "optimizer_converged"])
    assert result.diagnostics.loc[0, "optimizer_warnflag"] == 1
    summary = summarize_fit_diagnostics(result.diagnostics.assign(validation_window="test"))
    pooled = summary.loc[summary["scope"].eq("pooled_development")].iloc[0]
    assert pooled["forecast_was_clipped_count"] == 1
    assert pooled["forecast_was_clipped_rate"] == pytest.approx(1 / 14)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("construction", "model_construction:RuntimeError"),
        ("fit", "model_fit:RuntimeError"),
        ("forecast", "forecast:RuntimeError"),
        ("length", "invalid_forecast_length"),
        ("nonnumeric", "non_numeric_forecast"),
        ("nonfinite", "non_finite_forecast"),
    ],
)
def test_failures_are_explicit_and_never_fallback(monkeypatch, mode: str, expected: str) -> None:
    class FakeFit:
        def forecast(self, steps: int):
            if mode == "forecast":
                raise RuntimeError("secret details are not persisted")
            if mode == "length":
                return [1.0] * 13
            if mode == "nonnumeric":
                return ["bad"] * 14
            if mode == "nonfinite":
                return [np.nan] * 14
            return [1.0] * 14

    class FakeModel:
        def fit(self, *, optimized: bool):
            if mode == "fit":
                raise RuntimeError("secret details are not persisted")
            return FakeFit()

    def constructor(*args, **kwargs):
        if mode == "construction":
            raise RuntimeError("secret details are not persisted")
        return FakeModel()

    monkeypatch.setattr(hw, "ExponentialSmoothing", constructor)
    result = hw.forecast_holt_winters(
        _targets([ORIGIN + pd.Timedelta(days=1)]),
        actual_history_through_origin=_history(),
        forecast_origin=ORIGIN,
    )
    assert result.diagnostics.loc[0, "fit_failure_reason"] == expected
    assert not bool(result.diagnostics.loc[0, "model_fit_success"])
    assert result.forecasts["raw_statistical_forecast"].isna().all()
    assert result.forecasts["forecast_available"].eq(False).all()
    assert "secret details" not in str(result.diagnostics.to_dict())


def test_warning_categories_are_captured_and_aggregated(monkeypatch) -> None:
    def constructor(series: pd.Series, **kwargs: object):
        class FakeModel:
            def fit(self, *, optimized: bool) -> _FakeFit:
                return _FakeFit([5.0] * 14, calls=[], warning=True)

        return FakeModel()

    monkeypatch.setattr(hw, "ExponentialSmoothing", constructor)
    result = hw.forecast_holt_winters(
        _targets([ORIGIN + pd.Timedelta(days=1)]),
        actual_history_through_origin=_history(),
        forecast_origin=ORIGIN,
    )
    assert result.diagnostics.loc[0, "warning_count"] == 1
    assert result.diagnostics.loc[0, "warning_categories"] == "RuntimeWarning"


def _window_data() -> pd.DataFrame:
    dates = pd.date_range(ORIGIN - pd.Timedelta(days=34), ORIGIN + pd.Timedelta(days=14), freq="D")
    return pd.DataFrame(
        {
            "Store": 1,
            "Date": dates,
            "Sales": np.arange(len(dates), dtype=float) + 100.0,
            "Open": 1.0,
            "Customers": 7,
        }
    )


def _window() -> ValidationWindow:
    return ValidationWindow(
        "synthetic",
        ORIGIN,
        ORIGIN + pd.Timedelta(days=1),
        ORIGIN + pd.Timedelta(days=14),
    )


def test_future_sales_and_open_mutations_do_not_change_forecasts_and_routing_is_postfit(
    monkeypatch,
) -> None:
    _patch_model(monkeypatch)
    data = _window_data()
    targets = data["Date"].gt(ORIGIN)
    data.loc[data["Date"].eq(ORIGIN + pd.Timedelta(days=1)), "Open"] = 0
    data.loc[data["Date"].eq(ORIGIN + pd.Timedelta(days=2)), "Open"] = np.nan
    mutated = data.copy(deep=True)
    mutated.loc[targets, "Sales"] = 900_000
    mutated.loc[targets, "Open"] = 0
    original = data.copy(deep=True)

    first, _, _ = build_window_holt_winters_evaluation_records(data, _window())
    second, _, _ = build_window_holt_winters_evaluation_records(mutated, _window())
    pd.testing.assert_series_equal(
        first["raw_statistical_forecast"], second["raw_statistical_forecast"]
    )
    assert (
        first.loc[first["Date"].eq(ORIGIN + pd.Timedelta(days=1)), "operational_forecast"].iloc[0]
        == 0
    )
    assert pd.isna(
        first.loc[first["Date"].eq(ORIGIN + pd.Timedelta(days=2)), "operational_forecast"].iloc[0]
    )
    assert (
        first.loc[first["Date"].eq(ORIGIN + pd.Timedelta(days=3)), "operational_forecast"].iloc[0]
        == 10
    )
    assert not first.loc[
        first["Date"].eq(ORIGIN + pd.Timedelta(days=1)), "primary_evaluation_eligible"
    ].iloc[0]
    assert "Customers" not in first.columns
    assert "raw_baseline_forecast" not in first.columns
    pd.testing.assert_frame_equal(data, original)


def test_metric_column_adapter_preserves_phase4_metric_values() -> None:
    raw = pd.Series([10.0, 20.0, np.nan])
    records = pd.DataFrame(
        {
            "actual_sales": [11.0, 0.0, 50.0],
            "source_open": [1.0, 1.0, 1.0],
            "raw_baseline_forecast": raw,
            "raw_statistical_forecast": raw,
            "forecast_available": raw.notna(),
            "primary_evaluation_eligible": [True, True, False],
            "horizon": [1, 2, 3],
            "validation_window": ["validation_1"] * 3,
        }
    )
    baseline = summarize_forecast_metrics(records, scope="test")
    candidate = summarize_forecast_metrics(
        records, scope="test", forecast_column="raw_statistical_forecast"
    )
    assert candidate == baseline


def test_runner_json_output_normalizes_nonfinite_and_numpy_scalars() -> None:
    import json

    cleaned = _json_safe({"missing": np.nan, "count": np.int64(7), "nested": [np.float64(2.5)]})
    assert json.loads(json.dumps(cleaned, allow_nan=False)) == {
        "missing": None,
        "count": 7,
        "nested": [2.5],
    }


def test_paired_comparison_uses_identical_open_label_rows_and_guardrail_suppresses_winner() -> None:
    targets = _targets([ORIGIN + pd.Timedelta(days=1), ORIGIN + pd.Timedelta(days=2)])
    raw = pd.DataFrame(
        {
            "Store": [1, 1],
            "forecast_origin": [ORIGIN, ORIGIN],
            "Date": targets["Date"],
            "horizon": [1, 2],
            "raw_baseline_forecast": [9.0, np.nan],
        }
    )
    labels = targets.assign(Sales=[10.0, 20.0], Open=[1.0, 1.0])
    naive = assemble_evaluation_records(raw, labels, validation_window="validation_1")
    statistical = naive.rename(columns={"raw_baseline_forecast": "raw_statistical_forecast"}).copy()
    statistical.loc[1, "raw_statistical_forecast"] = 19.0
    statistical["model_forecast_unclipped"] = statistical["raw_statistical_forecast"]
    paired = build_paired_comparison_records(statistical, naive)
    assert len(paired) == 1
    assert paired["Date"].iloc[0] == targets["Date"].iloc[0]
    summary = summarize_paired_comparison(paired, interpretation_allowed=False)
    window = summary.loc[summary["validation_window"].eq("validation_1")].iloc[0]
    assert window["paired_row_count"] == 1
    assert window["holt_winters_mae"] == window["seasonal_naive_mae"] == 1.0
    assert pd.isna(window["lower_paired_mae_model"])
    assert "suppressed" in window["comparison_interpretation"]


def test_standalone_guardrail_and_approved_windows_are_explicit(monkeypatch) -> None:
    _patch_model(monkeypatch)
    dates = pd.date_range("2015-04-15", "2015-07-03", freq="D")
    data = pd.DataFrame({"Store": 1, "Date": dates, "Sales": 100.0, "Open": 1.0})
    records = build_development_holt_winters_evaluation(data).records
    # Three windows provide 42 open labels; one unavailable forecast falls below the 99% rule.
    records.loc[records.index[0], "raw_statistical_forecast"] = np.nan
    records.loc[records.index[0], "forecast_available"] = False
    records.loc[records.index[0], "primary_evaluation_eligible"] = False
    summary = summarize_holt_winters_development(records)
    assert not summary["coverage_guardrail_passed"]
    assert summary["requires_coverage_review"]
    assert len(APPROVED_DEVELOPMENT_WINDOWS) == 3
    assert set(records["validation_window"].unique()) == {
        window.name for window in APPROVED_DEVELOPMENT_WINDOWS
    }


def test_seasonal_naive_comparator_is_recomputed_from_same_sales_history() -> None:
    history = _history(days=35)
    targets = _targets([ORIGIN + pd.Timedelta(days=1), ORIGIN + pd.Timedelta(days=14)])
    naive = forecast_seasonal_naive(
        targets, actual_history_through_origin=history, forecast_origin=ORIGIN
    )
    assert naive["raw_baseline_forecast"].tolist() == [
        history["Sales"].iloc[-7],
        history["Sales"].iloc[-1],
    ]


def test_parquet_reader_filters_protected_holdout_before_return(tmp_path: Path) -> None:
    dates = pd.date_range("2015-05-01", "2015-07-31", freq="D")
    source = pd.DataFrame({"Store": 1, "Date": dates, "Sales": 10.0, "Open": 1})
    path = tmp_path / "train.parquet"
    source.to_parquet(path, engine="pyarrow", index=False)

    visible = _read_development_history(path)

    assert visible["Date"].max() == pd.Timestamp("2015-07-03")
    assert visible["Date"].between("2015-07-04", "2015-07-31").sum() == 0


def test_holdout_target_dates_are_rejected_by_evaluation_window() -> None:
    with pytest.raises(ValueError, match="before the final holdout"):
        window = ValidationWindow(
            "invalid",
            pd.Timestamp("2015-07-03"),
            pd.Timestamp("2015-07-04"),
            pd.Timestamp("2015-07-17"),
        )
        build_window_holt_winters_evaluation_records(_window_data(), window)
