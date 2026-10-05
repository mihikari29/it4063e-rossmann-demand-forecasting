"""Leakage-first tests for the approved Phase 3 Rossmann feature contract."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.features.calendar import build_calendar_features
from rossmann_forecasting.features.competition import build_competition_features
from rossmann_forecasting.features.contract import (
    COMPETITION_HELPER_COLUMNS,
    DYNAMIC_PREDICTOR_COLUMNS,
    PREDICTOR_COLUMNS,
)
from rossmann_forecasting.features.history import (
    build_historical_history_features,
    build_origin_history_features,
)
from rossmann_forecasting.features.pipeline import build_feature_tables, build_static_predictors
from rossmann_forecasting.features.promotion import build_promotion_features
from rossmann_forecasting.features.runner import (
    _development_coverage_audit,
    _holdout_integrity_audit,
)


def _rows(dates: pd.DatetimeIndex, *, store: int = 7, promo2: int = 0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Store": store,
            "DayOfWeek": dates.isocalendar().day.to_numpy(dtype="int64"),
            "Date": dates,
            "Open": 1,
            "Promo": 0,
            "StateHoliday": "0",
            "SchoolHoliday": 0,
            "StoreType": "a",
            "Assortment": "c",
            "CompetitionDistance": 250.0,
            "CompetitionOpenSinceMonth": 3.0,
            "CompetitionOpenSinceYear": 2014.0,
            "Promo2": promo2,
            "Promo2SinceWeek": np.nan if not promo2 else 1.0,
            "Promo2SinceYear": np.nan if not promo2 else 2015.0,
            "PromoInterval": None if not promo2 else "Jan,Apr,Jul,Oct",
        },
        index=pd.RangeIndex(len(dates)),
    )


def test_calendar_contract_derives_iso_fields_and_rejects_source_mismatch() -> None:
    rows = _rows(pd.date_range("2015-12-28", periods=5))
    result = build_calendar_features(rows)

    assert result["day_of_week"].tolist() == [1, 2, 3, 4, 5]
    assert result["week_of_year"].tolist() == [53, 53, 53, 53, 53]
    assert result["month"].tolist() == [12, 12, 12, 12, 1]
    assert result["quarter"].tolist() == [4, 4, 4, 4, 1]
    assert result["is_weekend"].eq(False).all()
    assert "Date" not in result

    wrong = rows.assign(DayOfWeek=7)
    with pytest.raises(ValueError, match="disagrees with ISO weekday"):
        build_calendar_features(wrong)


def test_promo2_iso_week_53_boundaries_structural_nulls_and_sept_normalization() -> None:
    rows = _rows(pd.DatetimeIndex(["2015-12-27", "2015-12-28", "2016-01-01"]), promo2=1)
    rows["Promo2SinceWeek"] = 53
    rows["PromoInterval"] = "Dec,Jan"
    features, findings = build_promotion_features(rows)
    assert features["is_promo2_active"].tolist() == [False, True, True]
    assert findings == []

    september = _rows(pd.DatetimeIndex(["2015-09-01"]), promo2=1)
    september["PromoInterval"] = "Mar,Jun,Sept,Dec"
    normalized, _ = build_promotion_features(september)
    assert bool(normalized.loc[0, "is_promo2_active"])

    nonparticipant = _rows(pd.DatetimeIndex(["2015-01-01"]))
    inactive, no_findings = build_promotion_features(nonparticipant)
    assert not inactive.loc[0, "is_promo2_active"]
    assert no_findings == []


def test_invalid_and_incomplete_promo2_schedule_stays_null_with_audit_finding() -> None:
    rows = _rows(pd.DatetimeIndex(["2014-12-29", "2014-12-30"]), promo2=1)
    rows["Store"] = [7, 8]
    rows.loc[0, "Promo2SinceYear"] = 2014
    rows.loc[0, "Promo2SinceWeek"] = 53  # 2014 has no ISO week 53.
    rows.loc[1, "Promo2SinceYear"] = np.nan
    features, findings = build_promotion_features(rows)

    assert features["is_promo2_active"].isna().all()
    assert len(findings) == 2
    assert {finding["Store"] for finding in findings} == {7, 8}
    assert all(finding["affected_rows"] == 1 for finding in findings)


def test_competition_status_and_age_use_completed_calendar_months() -> None:
    rows = pd.DataFrame(
        {
            "Store": [1, 1, 1, 2, 3],
            "Date": pd.to_datetime(
                ["2014-02-28", "2014-03-01", "2014-05-31", "2015-02-01", "2015-02-01"]
            ),
            "CompetitionOpenSinceMonth": [3.0, 3.0, 3.0, 12.0, np.nan],
            "CompetitionOpenSinceYear": [2014.0, 2014.0, 2014.0, 2014.0, np.nan],
        }
    )
    features, findings = build_competition_features(rows)

    assert features["competition_has_opened"].tolist() == [False, True, True, True, pd.NA]
    assert features["competition_age_months"].tolist() == [0, 0, 2, 2, pd.NA]
    assert len(findings) == 1
    assert findings[0]["affected_stores"] == 1
    assert not set(COMPETITION_HELPER_COLUMNS).intersection(features.columns)
    assert not set(COMPETITION_HELPER_COLUMNS).intersection(PREDICTOR_COLUMNS)


@pytest.mark.parametrize(
    "month,year,match",
    [
        (3.0, np.nan, "partially missing"),
        (13.0, 2014.0, "outside Phase 1 validation ranges"),
        (3.0, 1800.0, "outside Phase 1 validation ranges"),
    ],
)
def test_invalid_competition_metadata_fails_clearly(month, year, match) -> None:
    rows = pd.DataFrame(
        {
            "Store": [1],
            "Date": pd.to_datetime(["2015-01-01"]),
            "CompetitionOpenSinceMonth": [month],
            "CompetitionOpenSinceYear": [year],
        }
    )
    with pytest.raises(ValueError, match=match):
        build_competition_features(rows)


def test_exact_lags_missing_previous_calendar_date_and_zero_sales() -> None:
    history = pd.DataFrame(
        {
            "Store": [1, 1, 1],
            "Date": pd.to_datetime(["2015-01-01", "2015-01-03", "2015-01-04"]),
            "Sales": [10, 0, 40],
        }
    )
    targets = pd.DataFrame(
        {
            "Store": [1, 1],
            "Date": pd.to_datetime(["2015-01-03", "2015-01-05"]),
        }
    )
    result = build_historical_history_features(targets, history)

    assert pd.isna(result.loc[0, "sales_lag_1"])  # Jan 2 is absent; do not use prior row Jan 1.
    assert result.loc[1, "sales_lag_1"] == 40
    assert result.loc[0, "sales_ma_7"] != result.loc[0, "sales_ma_7"]

    zero_target = pd.DataFrame({"Store": [1], "Date": pd.to_datetime(["2015-01-04"])})
    zero_lag = build_historical_history_features(zero_target, history)
    assert zero_lag.loc[0, "sales_lag_1"] == 0


def test_rolling_windows_exclude_current_target_and_use_sample_standard_deviation() -> None:
    dates = pd.date_range("2015-01-01", periods=30)
    history = pd.DataFrame({"Store": 1, "Date": dates, "Sales": np.arange(1, 31, dtype="int64")})
    history.loc[29, "Sales"] = 1_000_000  # Target-date value must not enter its own features.
    target = pd.DataFrame({"Store": [1], "Date": [dates[-1]]})
    result = build_historical_history_features(target, history)

    prior_seven = np.arange(23, 30, dtype="float64")
    assert result.loc[0, "sales_ma_7"] == pytest.approx(prior_seven.mean())
    assert result.loc[0, "sales_std_7"] == pytest.approx(prior_seven.std(ddof=1))
    assert result.loc[0, "sales_ma_7"] != 1_000_000


def test_rolling_window_with_exact_endpoints_but_missing_middle_date_is_null() -> None:
    history = pd.DataFrame(
        {
            "Store": 1,
            "Date": pd.to_datetime(
                ["2015-01-01", "2015-01-02", "2015-01-04", "2015-01-05", "2015-01-06", "2015-01-07"]
            ),
            "Sales": [10, 20, 40, 50, 60, 70],
        }
    )
    target = pd.DataFrame({"Store": [1], "Date": [pd.Timestamp("2015-01-08")]})

    result = build_historical_history_features(target, history)

    assert result.loc[0, "sales_lag_7"] == 10
    assert pd.isna(result.loc[0, "sales_ma_7"])
    assert pd.isna(result.loc[0, "sales_std_7"])


def test_first_28_days_have_deterministic_exact_warmup_and_no_partial_windows() -> None:
    dates = pd.date_range("2015-01-01", periods=35)
    history = pd.DataFrame({"Store": 1, "Date": dates, "Sales": np.arange(35, dtype="int64")})
    targets = pd.DataFrame(
        {
            "Store": 1,
            "Date": pd.to_datetime(["2015-01-01", "2015-01-02", "2015-01-08", "2015-01-29"]),
        }
    )
    result = build_historical_history_features(targets, history)

    assert result.loc[0, list(DYNAMIC_PREDICTOR_COLUMNS)].isna().all()
    assert result.loc[1, "sales_lag_1"] == 0
    assert pd.isna(result.loc[1, "sales_ma_7"])
    assert result.loc[2, "sales_ma_7"] == pytest.approx(np.mean(np.arange(0, 7)))
    assert pd.isna(result.loc[2, "sales_ma_14"])
    assert result.loc[3, "sales_ma_28"] == pytest.approx(np.mean(np.arange(0, 28)))


def test_shared_gap_does_not_bridge_and_features_resume_after_complete_history() -> None:
    before_gap = pd.date_range("2014-06-29", "2014-06-30")
    after_gap = pd.date_range("2015-01-01", "2015-01-29")
    dates = before_gap.append(after_gap)
    history = pd.DataFrame(
        {"Store": 1, "Date": dates, "Sales": np.arange(len(dates), dtype="int64") + 1}
    )
    target_dates = pd.to_datetime(
        ["2015-01-01", "2015-01-02", "2015-01-08", "2015-01-15", "2015-01-29"]
    )
    targets = pd.DataFrame({"Store": 1, "Date": target_dates})
    result = build_historical_history_features(targets, history)

    assert result.loc[0, list(DYNAMIC_PREDICTOR_COLUMNS)].isna().all()
    assert pd.notna(result.loc[1, "sales_lag_1"])
    assert pd.isna(result.loc[1, "sales_lag_7"])
    assert pd.notna(result.loc[2, "sales_lag_7"])
    assert pd.notna(result.loc[2, "sales_ma_7"])
    assert pd.isna(result.loc[2, "sales_ma_14"])
    assert pd.notna(result.loc[3, "sales_ma_14"])
    assert pd.notna(result.loc[4, "sales_lag_28"])
    assert pd.notna(result.loc[4, "sales_ma_28"])


def test_origin_api_rejects_unrestricted_actual_history_and_accepts_prior_predictions() -> None:
    origin = pd.Timestamp("2015-01-03")
    actual = pd.DataFrame(
        {"Store": [1, 1, 1], "Date": pd.date_range("2015-01-01", periods=3), "Sales": [10, 20, 30]}
    )
    targets = pd.DataFrame({"Store": [1, 1], "Date": pd.to_datetime(["2015-01-04", "2015-01-05"])})
    with pytest.raises(ValueError, match="after forecast_origin"):
        build_origin_history_features(
            targets,
            actual_history_through_origin=pd.concat(
                [actual, pd.DataFrame({"Store": [1], "Date": ["2015-01-04"], "Sales": [999]})],
                ignore_index=True,
            ),
            forecast_origin=origin,
        )

    predictions = pd.DataFrame(
        {"Store": [1], "Date": [pd.Timestamp("2015-01-04")], "PredictedSales": [40.0]}
    )
    result = build_origin_history_features(
        targets,
        actual_history_through_origin=actual,
        forecast_origin=origin,
        prior_recursive_predictions=predictions,
    )
    assert result.loc[0, "sales_lag_1"] == 30
    assert result.loc[1, "sales_lag_1"] == 40


def test_actual_and_recursive_prediction_overlap_is_rejected_explicitly() -> None:
    origin = pd.Timestamp("2015-01-03")
    actual = pd.DataFrame(
        {
            "Store": [1, 1],
            "Date": pd.to_datetime(["2015-01-03", "2015-01-04"]),
            "Sales": [30, 999],
        }
    )
    predictions = pd.DataFrame(
        {
            "Store": [1],
            "Date": pd.to_datetime(["2015-01-04"]),
            "PredictedSales": [40],
        }
    )

    with pytest.raises(ValueError, match="overlapping Store × Date keys"):
        build_origin_history_features(
            pd.DataFrame({"Store": [1], "Date": pd.to_datetime(["2015-01-05"])}),
            actual_history_through_origin=actual,
            forecast_origin=origin,
            prior_recursive_predictions=predictions,
        )


def test_recursive_prediction_must_precede_a_requested_target_for_its_store() -> None:
    with pytest.raises(ValueError, match="strictly before a requested target date"):
        build_origin_history_features(
            pd.DataFrame({"Store": [1], "Date": pd.to_datetime(["2015-01-04"])}),
            actual_history_through_origin=pd.DataFrame(
                {"Store": [1], "Date": pd.to_datetime(["2015-01-03"]), "Sales": [30]}
            ),
            forecast_origin="2015-01-03",
            prior_recursive_predictions=pd.DataFrame(
                {
                    "Store": [1],
                    "Date": pd.to_datetime(["2015-01-05"]),
                    "PredictedSales": [40],
                }
            ),
        )


def test_mutating_actual_sales_after_origin_cannot_change_censored_features() -> None:
    origin = pd.Timestamp("2015-01-03")
    actual = pd.DataFrame(
        {"Store": 1, "Date": pd.date_range("2015-01-01", periods=5), "Sales": [10, 20, 30, 40, 50]}
    )
    targets = pd.DataFrame({"Store": [1], "Date": [pd.Timestamp("2015-01-04")]})
    first_history = actual.loc[actual["Date"].le(origin), ["Store", "Date", "Sales"]].copy()
    changed = actual.assign(Sales=[10, 20, 30, 999_999, -500])
    second_history = changed.loc[changed["Date"].le(origin), ["Store", "Date", "Sales"]].copy()

    first = build_origin_history_features(
        targets, actual_history_through_origin=first_history, forecast_origin=origin
    )
    second = build_origin_history_features(
        targets, actual_history_through_origin=second_history, forecast_origin=origin
    )
    pd.testing.assert_frame_equal(first, second)


def test_store_is_unchanged_key_and_predictor_and_static_columns_are_future_known() -> None:
    rows = _rows(pd.date_range("2015-01-01", periods=2), store=622)
    static, _ = build_static_predictors(rows)

    assert static["Store"].tolist() == [622, 622]
    assert str(static["Store"].dtype) == "int64"
    assert PREDICTOR_COLUMNS[0] == "Store"
    assert "Date" not in static
    assert "DayOfWeek" not in static
    assert set(DYNAMIC_PREDICTOR_COLUMNS).isdisjoint(static.columns)


def test_train_inference_contract_preserves_roles_store_and_excludes_forbidden_fields(
    tmp_path,
) -> None:
    train = _rows(pd.date_range("2015-01-01", periods=35), store=622)
    train["Sales"] = np.arange(35, dtype="int64")
    train["Customers"] = 25
    test = _rows(pd.date_range("2015-02-05", periods=2), store=622)
    test["Open"] = [np.nan, 1.0]
    test["Id"] = [1, 2]
    resolution = test[["Store", "Date"]].copy()
    resolution["Open_resolved"] = pd.array([1, 1], dtype="Float64")
    resolution["Open_resolution_method"] = "historical_exact_context_consensus"
    resolution["historical_match_rows"] = 40
    resolution["historical_open_rate"] = pd.array([1.0, 1.0], dtype="Float64")
    resolution["resolution_uncertain"] = True
    train_before = train.copy(deep=True)
    test_before = test.copy(deep=True)
    resolution_before = resolution.copy(deep=True)

    train_features, inference_features, _ = build_feature_tables(
        train, test, open_resolution=resolution
    )
    repeated_train, repeated_inference, _ = build_feature_tables(
        train, test, open_resolution=resolution
    )
    pd.testing.assert_frame_equal(train, train_before)
    pd.testing.assert_frame_equal(test, test_before)
    pd.testing.assert_frame_equal(resolution, resolution_before)
    pd.testing.assert_frame_equal(train_features, repeated_train)
    pd.testing.assert_frame_equal(inference_features, repeated_inference)
    assert tuple(name for name in train_features if name in PREDICTOR_COLUMNS) == PREDICTOR_COLUMNS
    assert (
        tuple(name for name in inference_features if name in PREDICTOR_COLUMNS) == PREDICTOR_COLUMNS
    )
    for column in PREDICTOR_COLUMNS:
        assert train_features[column].dtype == inference_features[column].dtype
    assert train_features["Store"].equals(pd.Series([622] * 35, dtype="int64", name="Store"))
    assert inference_features["Store"].equals(pd.Series([622] * 2, dtype="int64", name="Store"))
    assert train_features["Date"].dtype == "datetime64[ns]"
    assert "Date" not in PREDICTOR_COLUMNS
    assert "Customers" not in train_features and "Customers" not in inference_features
    assert "Sales" in train_features and "Sales" not in inference_features
    assert "Open" not in PREDICTOR_COLUMNS and "Open_resolved" not in PREDICTOR_COLUMNS
    assert inference_features["Open"].isna().tolist() == [True, False]
    assert inference_features["Open_resolved"].tolist() == [1.0, 1.0]
    assert train_features["training_label_eligible"].all()
    assert train_features["primary_evaluation_eligible"].all()
    assert inference_features["row_role"].eq("inference").all()

    train_path = tmp_path / "train.parquet"
    inference_path = tmp_path / "inference.parquet"
    train_features.to_parquet(train_path, engine="pyarrow", index=False)
    inference_features.to_parquet(inference_path, engine="pyarrow", index=False)
    train_roundtrip = pd.read_parquet(train_path, engine="pyarrow")
    inference_roundtrip = pd.read_parquet(inference_path, engine="pyarrow")
    for column in PREDICTOR_COLUMNS:
        assert train_roundtrip[column].dtype == inference_roundtrip[column].dtype


@pytest.mark.parametrize(
    "forbidden_column", ["CustomersDerived", "rolling_customers_7", "future_sales_average"]
)
def test_future_customers_or_sales_derived_fields_are_rejected(forbidden_column) -> None:
    train = _rows(pd.date_range("2015-01-01", periods=2))
    train["Sales"] = [10, 20]
    future = _rows(pd.date_range("2015-01-03", periods=1))
    future[forbidden_column] = [100]
    with pytest.raises(ValueError, match="forbidden Sales/Customers-derived fields"):
        build_feature_tables(train, future)


def test_development_audit_is_invariant_to_holdout_values_and_has_mechanical_holdout_checks() -> (
    None
):
    dates = pd.date_range("2015-01-01", periods=40)
    train = _rows(dates)
    train["Sales"] = np.arange(40, dtype="int64")
    train["Customers"] = 999
    features, _, _ = build_feature_tables(
        train,
        _rows(pd.date_range("2015-02-10", periods=2)),
    )
    holdout_start = pd.Timestamp("2015-02-08")

    first = _development_coverage_audit(features, holdout_start=holdout_start)
    changed = features.copy()
    changed.loc[changed["Date"].ge(holdout_start), "sales_lag_1"] = 9_999_999
    changed.loc[changed["Date"].ge(holdout_start), "Sales"] = 9_999_999
    second = _development_coverage_audit(changed, holdout_start=holdout_start)
    assert first == second
    mechanical = _holdout_integrity_audit(changed, holdout_start=holdout_start)
    assert mechanical["mechanical_checks_only"]
    assert mechanical["row_count"] == 2
    assert mechanical["target_or_feature_distributions_summarized"] is False
    assert mechanical["forecast_metrics_computed"] is False
