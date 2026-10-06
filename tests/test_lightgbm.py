"""Synthetic contract coverage for the approved Phase 6 LightGBM implementation."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from rossmann_forecasting.data.preparation import SOURCE_SNAPSHOT_SHA256
from rossmann_forecasting.features.contract import (
    FEATURE_CONTRACT_VERSION,
    PREDICTOR_COLUMNS,
    PREDICTOR_DTYPES,
)
from rossmann_forecasting.features.history import (
    OriginHistoryFeatureCache,
    build_origin_history_features,
)
from rossmann_forecasting.forecasting.lightgbm import (
    CATEGORICAL_COLUMNS,
    FIXED_PARAMETERS,
    FORECAST_COLUMN,
    FUTURE_COVARIATE_COLUMNS,
    CategoricalAdapterIncompatibility,
    FittedLightGBM,
    InvalidFeatureSchema,
    adapt_prediction_features,
    fit_lightgbm,
    make_lightgbm_dataset,
    prepare_training_data,
    recursive_lightgbm_forecasts,
)
from rossmann_forecasting.forecasting.lightgbm_evaluation import (
    TRIAL_PARAMETERS,
    TRIALS,
    _paired_records,
    attach_lightgbm_labels,
    summarize_lightgbm_development,
)
from rossmann_forecasting.forecasting.lightgbm_runner import (
    _assert_ignored,
    _dataframe_sha256,
    _input_snapshot_identifiers,
    _read_censored_parquet,
)
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
)

ORIGIN = pd.Timestamp("2015-04-24")


def _feature_matrix(
    stores: list[int],
    dates: pd.DatetimeIndex,
    *,
    state_holidays: list[str] | None = None,
    store_types: list[str] | None = None,
    assortments: list[str] | None = None,
) -> pd.DataFrame:
    size = len(stores)
    frame = pd.DataFrame(
        {
            "Store": np.asarray(stores, dtype=np.int64),
            "day_of_week": dates.dayofweek.to_numpy(dtype=np.int8),
            "week_of_year": dates.isocalendar().week.to_numpy(dtype=np.int8),
            "month": dates.month.to_numpy(dtype=np.int8),
            "quarter": dates.quarter.to_numpy(dtype=np.int8),
            "year": dates.year.to_numpy(dtype=np.int16),
            "is_weekend": np.asarray(dates.dayofweek >= 5, dtype=bool),
            "is_month_start": np.asarray(dates.is_month_start, dtype=bool),
            "is_month_end": np.asarray(dates.is_month_end, dtype=bool),
            "state_holiday": pd.Series(state_holidays or ["0"] * size, dtype="string[python]"),
            "school_holiday": pd.Series([False] * size, dtype=bool),
            "promo": pd.Series([False] * size, dtype=bool),
            "promo2": pd.Series([False] * size, dtype=bool),
            "is_promo2_active": pd.Series([False] * size, dtype="boolean"),
            "store_type": pd.Series(store_types or ["a"] * size, dtype="string[python]"),
            "assortment": pd.Series(assortments or ["a"] * size, dtype="string[python]"),
            "competition_distance": np.full(size, 100.0, dtype=np.float64),
            "competition_has_opened": pd.Series([True] * size, dtype="boolean"),
            "competition_age_months": pd.Series([12] * size, dtype="Int16"),
            "sales_lag_1": np.full(size, 10.0, dtype=np.float64),
            "sales_lag_7": np.full(size, 10.0, dtype=np.float64),
            "sales_lag_14": np.full(size, 10.0, dtype=np.float64),
            "sales_lag_28": np.full(size, 10.0, dtype=np.float64),
            "sales_ma_7": np.full(size, 10.0, dtype=np.float64),
            "sales_ma_14": np.full(size, 10.0, dtype=np.float64),
            "sales_ma_28": np.full(size, 10.0, dtype=np.float64),
            "sales_std_7": np.zeros(size, dtype=np.float64),
            "sales_std_14": np.zeros(size, dtype=np.float64),
            "sales_std_28": np.zeros(size, dtype=np.float64),
        }
    )
    return frame.loc[:, PREDICTOR_COLUMNS].astype(PREDICTOR_DTYPES)


def _training_rows(
    *,
    stores: list[int] | None = None,
    dates: pd.DatetimeIndex | None = None,
    open_values: list[int] | None = None,
    sales: list[float] | None = None,
    states: list[str] | None = None,
    store_types: list[str] | None = None,
    assortments: list[str] | None = None,
) -> pd.DataFrame:
    dates = dates if dates is not None else pd.DatetimeIndex([ORIGIN - pd.Timedelta(days=1)])
    stores = stores if stores is not None else [1] * len(dates)
    open_values = open_values if open_values is not None else [1] * len(dates)
    sales = sales if sales is not None else [100.0] * len(dates)
    features = _feature_matrix(
        stores,
        dates,
        state_holidays=states,
        store_types=store_types,
        assortments=assortments,
    )
    features["Date"] = dates
    features["Sales"] = np.asarray(sales, dtype=np.float64)
    features["Open"] = np.asarray(open_values, dtype=np.float64)
    features["training_label_eligible"] = np.asarray(open_values, dtype=np.int8) == 1
    return features


def _actual_history(*, last_sales: float = 100.0, stores: tuple[int, ...] = (1,)) -> pd.DataFrame:
    dates = pd.date_range(ORIGIN - pd.Timedelta(days=29), ORIGIN, freq="D")
    rows: list[dict[str, object]] = []
    for store in stores:
        for date in dates:
            rows.append(
                {
                    "Store": store,
                    "Date": date,
                    "Sales": last_sales if date == ORIGIN else 80.0 + store,
                }
            )
    return pd.DataFrame(rows)


def _future_covariates(
    *,
    stores: tuple[int, ...] = (1,),
    dates: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    dates = dates if dates is not None else pd.date_range(ORIGIN + pd.Timedelta(days=1), periods=14)
    rows: list[dict[str, object]] = []
    for store in stores:
        for date in dates:
            rows.append(
                {
                    "Store": store,
                    "DayOfWeek": date.dayofweek + 1,
                    "Date": date,
                    "Promo": 0,
                    "StateHoliday": "0",
                    "SchoolHoliday": 0,
                    "StoreType": "a",
                    "Assortment": "a",
                    "CompetitionDistance": 100.0,
                    "CompetitionOpenSinceMonth": 1,
                    "CompetitionOpenSinceYear": 2010,
                    "Promo2": 0,
                    "Promo2SinceWeek": np.nan,
                    "Promo2SinceYear": np.nan,
                    "PromoInterval": None,
                }
            )
    return pd.DataFrame(rows, columns=FUTURE_COVARIATE_COLUMNS)


class _RecordingBooster:
    def __init__(
        self,
        output: float | list[float] | Callable[[pd.DataFrame, int], np.ndarray] = 50.0,
    ) -> None:
        self.output = output
        self.calls: list[pd.DataFrame] = []

    def predict(self, features: pd.DataFrame, *, num_threads: int = 4) -> np.ndarray:
        del num_threads
        self.calls.append(features.copy(deep=True))
        if callable(self.output):
            values = self.output(features, len(self.calls))
        elif isinstance(self.output, list):
            value = self.output[min(len(self.calls) - 1, len(self.output) - 1)]
            values = np.full(len(features), value)
        else:
            values = np.full(len(features), self.output)
        return np.asarray(values, dtype=np.float64)


class _RaisingBooster:
    def predict(self, features: pd.DataFrame, *, num_threads: int = 4) -> np.ndarray:
        del features, num_threads
        raise RuntimeError("simulated LightGBM prediction API failure")


def _model(
    output: float | list[float] | Callable[[pd.DataFrame, int], np.ndarray] = 50.0,
    *,
    stores: tuple[int, ...] = (1,),
) -> FittedLightGBM:
    booster = _RecordingBooster(output)
    categories = {
        "Store": stores,
        "state_holiday": ("0",),
        "store_type": ("a",),
        "assortment": ("a",),
    }
    return FittedLightGBM(
        booster,
        categories,
        30,
        ORIGIN,
        {"num_threads": 4, "zero_as_missing": False},
    )


def _requested_keys(
    stores: tuple[int, ...] = (1,), dates: pd.DatetimeIndex | None = None
) -> pd.DataFrame:
    dates = dates if dates is not None else pd.date_range(ORIGIN + pd.Timedelta(days=1), periods=14)
    return pd.DataFrame(
        [(store, date) for store in stores for date in dates], columns=["Store", "Date"]
    )


def _forecast(
    *,
    model: FittedLightGBM | None = None,
    covariates: pd.DataFrame | None = None,
    keys: pd.DataFrame | None = None,
    history: pd.DataFrame | None = None,
) -> pd.DataFrame:
    return recursive_lightgbm_forecasts(
        _requested_keys() if keys is None else keys,
        future_covariates=_future_covariates() if covariates is None else covariates,
        actual_history_through_origin=_actual_history() if history is None else history,
        forecast_origin=ORIGIN,
        model=_model() if model is None else model,
    )


def test_predictor_schema_order_and_forbidden_fields_are_exact() -> None:
    features = _feature_matrix([1], pd.DatetimeIndex([ORIGIN]))
    training = _training_rows()
    prepared = prepare_training_data(training, forecast_origin=ORIGIN)
    assert tuple(features.columns) == PREDICTOR_COLUMNS
    assert tuple(prepared.features.columns) == PREDICTOR_COLUMNS
    assert not {"Date", "Sales", "Customers", "Open", "training_label_eligible"}.intersection(
        prepared.features.columns
    )


def test_training_population_keeps_open_zero_and_excludes_closed_rows() -> None:
    training = _training_rows(
        stores=[1, 1],
        dates=pd.DatetimeIndex([ORIGIN - pd.Timedelta(days=1), ORIGIN]),
        open_values=[1, 0],
        sales=[0.0, 0.0],
    )
    prepared = prepare_training_data(training, forecast_origin=ORIGIN)
    assert prepared.eligible_row_count == 1
    assert prepared.labels.tolist() == [0.0]
    assert prepared.features["Store"].tolist() == [1]


def test_closed_day_sales_remain_in_raw_recursive_history() -> None:
    booster_model = _model()
    _forecast(model=booster_model, history=_actual_history(last_sales=0.0))
    booster = booster_model.booster
    assert isinstance(booster, _RecordingBooster)
    assert booster.calls[0]["sales_lag_1"].iloc[0] == 0.0


def test_fit_origin_rejects_training_rows_after_origin() -> None:
    future = _training_rows(
        dates=pd.DatetimeIndex([ORIGIN + pd.Timedelta(days=1)]),
    )
    with pytest.raises(InvalidFeatureSchema, match="after the fit origin"):
        prepare_training_data(future, forecast_origin=ORIGIN)


def test_fit_only_category_vocabulary_comes_from_eligible_rows() -> None:
    training = _training_rows(
        stores=[1, 2],
        dates=pd.DatetimeIndex([ORIGIN - pd.Timedelta(days=1), ORIGIN]),
        open_values=[1, 0],
        sales=[100.0, 0.0],
        states=["0", "unfitted"],
        store_types=["a", "d"],
        assortments=["a", "c"],
    )
    prepared = prepare_training_data(training, forecast_origin=ORIGIN)
    assert prepared.category_vocabularies == {
        "Store": (1,),
        "state_holiday": ("0",),
        "store_type": ("a",),
        "assortment": ("a",),
    }


def test_store_and_exact_four_fields_are_categorical_in_adapter() -> None:
    features = _feature_matrix([1], pd.DatetimeIndex([ORIGIN]))
    adapted = adapt_prediction_features(
        features,
        {
            "Store": (1,),
            "state_holiday": ("0",),
            "store_type": ("a",),
            "assortment": ("a",),
        },
    )
    assert tuple(adapted.features.columns) == PREDICTOR_COLUMNS
    assert (
        tuple(
            column
            for column in PREDICTOR_COLUMNS
            if isinstance(adapted.features[column].dtype, pd.CategoricalDtype)
        )
        == CATEGORICAL_COLUMNS
    )


def test_unseen_store_is_explicitly_unavailable() -> None:
    result = _forecast(
        model=_model(stores=(1,)),
        covariates=_future_covariates(stores=(2,)),
        keys=_requested_keys(stores=(2,)),
        history=_actual_history(stores=(1,)),
    )
    assert result["unavailable_reason"].eq("unseen_store_category").all()
    assert result[FORECAST_COLUMN].isna().all()


def test_unseen_non_store_category_maps_to_missing_and_is_counted() -> None:
    covariates = _future_covariates()
    covariates.loc[covariates["Date"].eq(ORIGIN + pd.Timedelta(days=1)), "StateHoliday"] = "x"
    result = _forecast(covariates=covariates)
    first = result.loc[result["horizon"].eq(1)].iloc[0]
    assert first["forecast_available"]
    assert first["unseen_state_holiday"]
    assert len(result.loc[result["unseen_state_holiday"]]) == 1


@pytest.mark.parametrize(
    ("column", "value", "reason"),
    [
        ("StateHoliday", None, "missing_required_covariate:state_holiday"),
        ("StoreType", None, "missing_required_covariate:store_type"),
        ("Assortment", None, "missing_required_covariate:assortment"),
        ("Promo", None, "missing_required_covariate:promo"),
        ("SchoolHoliday", None, "missing_required_covariate:school_holiday"),
        ("Promo2", None, "missing_required_covariate:promo2"),
    ],
)
def test_required_source_null_covariate_is_unavailable(
    column: str, value: object, reason: str
) -> None:
    covariates = _future_covariates()
    covariates.loc[covariates.index[0], column] = value
    result = _forecast(covariates=covariates)
    assert result.loc[result["horizon"].eq(1), "unavailable_reason"].iloc[0] == reason


def test_numeric_missing_stays_nan_and_real_zero_stays_zero() -> None:
    features = _feature_matrix([1], pd.DatetimeIndex([ORIGIN]))
    features.loc[0, "competition_distance"] = np.nan
    features.loc[0, "sales_lag_1"] = 0.0
    adapted = adapt_prediction_features(
        features,
        {
            "Store": (1,),
            "state_holiday": ("0",),
            "store_type": ("a",),
            "assortment": ("a",),
        },
    )
    assert np.isnan(adapted.features["competition_distance"].iloc[0])
    assert adapted.features["sales_lag_1"].iloc[0] == 0.0


def test_numeric_nullable_boolean_extension_converts_to_nan_or_zero() -> None:
    features = _feature_matrix([1], pd.DatetimeIndex([ORIGIN]))
    features["competition_has_opened"] = pd.Series([pd.NA], dtype="boolean")
    features["sales_ma_7"] = 0.0
    adapted = adapt_prediction_features(
        features,
        {
            "Store": (1,),
            "state_holiday": ("0",),
            "store_type": ("a",),
            "assortment": ("a",),
        },
    )
    assert np.isnan(adapted.features["competition_has_opened"].iloc[0])
    assert adapted.features["sales_ma_7"].iloc[0] == 0.0


def test_future_outcome_fields_are_rejected_at_covariate_boundary() -> None:
    covariates = _future_covariates()
    covariates["Sales"] = 999.0
    with pytest.raises(InvalidFeatureSchema, match="forbidden outcome fields"):
        _forecast(covariates=covariates)
    for column in ("Customers", "Open", "Open_resolved"):
        dirty = _future_covariates()
        dirty[column] = 1
        with pytest.raises(InvalidFeatureSchema, match="forbidden outcome fields"):
            _forecast(covariates=dirty)


def test_future_label_mutations_do_not_change_raw_recursive_path() -> None:
    path_one = _forecast(model=_model())
    path_two = _forecast(model=_model())
    labels = pd.DataFrame(
        {
            "Store": path_one["Store"],
            "Date": path_one["Date"],
            "Sales": 10_000.0,
            "Open": 1,
            "Customers": 500,
        }
    )
    mutated_labels = labels.assign(Sales=500.0, Open=0, Customers=-100)
    evaluated_one = attach_lightgbm_labels(
        path_one,
        _requested_keys(),
        labels,
        validation_window="validation_1",
    )
    evaluated_two = attach_lightgbm_labels(
        path_two,
        _requested_keys(),
        mutated_labels,
        validation_window="validation_1",
    )
    assert_series_equal(path_one[FORECAST_COLUMN], path_two[FORECAST_COLUMN])
    assert_series_equal(evaluated_one[FORECAST_COLUMN], evaluated_two[FORECAST_COLUMN])


def test_horizon_two_uses_prediction_feedback_not_target_actual() -> None:
    model = _model(output=25.0)
    result = _forecast(model=model)
    booster = model.booster
    assert isinstance(booster, _RecordingBooster)
    assert len(booster.calls) == 14
    assert booster.calls[1]["sales_lag_1"].iloc[0] == 25.0
    assert result.loc[result["horizon"].eq(2), FORECAST_COLUMN].iloc[0] == 25.0


def test_cached_recursive_history_matches_reference_builder_across_horizons() -> None:
    history = _actual_history(stores=(1, 2))
    cache = OriginHistoryFeatureCache(history, ORIGIN)
    prior_rows: list[dict[str, object]] = []
    for horizon in range(1, 6):
        target_date = ORIGIN + pd.Timedelta(days=horizon)
        targets = pd.DataFrame({"Store": [1, 2], "Date": [target_date, target_date]})
        cached = cache.features(targets)
        reference = build_origin_history_features(
            targets,
            actual_history_through_origin=history,
            forecast_origin=ORIGIN,
            prior_recursive_predictions=(pd.DataFrame(prior_rows) if prior_rows else None),
        )
        assert_frame_equal(cached, reference, check_exact=True)
        prior_rows.append({"Store": 1, "Date": target_date, "PredictedSales": 120.0 + horizon})
        if horizon != 2:  # A skipped prediction must leave a real calendar gap.
            prior_rows.append({"Store": 2, "Date": target_date, "PredictedSales": 220.0 + horizon})
        cache.append_predictions(pd.DataFrame(prior_rows[-(1 if horizon == 2 else 2) :]))


def test_missing_target_key_remains_in_requested_denominator() -> None:
    covariates = _future_covariates()
    absent = ORIGIN + pd.Timedelta(days=3)
    covariates = covariates.loc[covariates["Date"].ne(absent)].copy()
    result = _forecast(covariates=covariates)
    missing = result.loc[result["Date"].eq(absent)].iloc[0]
    assert missing["unavailable_reason"] == "missing_target_key"
    assert not missing["forecast_available"]
    assert len(result) == len(_requested_keys())


def test_missing_intermediate_covariate_row_is_not_synthesized() -> None:
    dates = pd.date_range(ORIGIN + pd.Timedelta(days=1), periods=14)
    target = _requested_keys(dates=pd.DatetimeIndex([dates[-1]]))
    covariates = _future_covariates(dates=dates).loc[lambda frame: frame["Date"].ne(dates[6])]
    path = _forecast(keys=target, covariates=covariates)
    gap = path.loc[path["Date"].eq(dates[6])].iloc[0]
    final = path.loc[path["Date"].eq(dates[-1])].iloc[0]
    assert gap["unavailable_reason"] == "missing_future_covariate_row"
    assert final["forecast_available"]
    assert len(path) == 14


def test_invalid_feature_order_and_dtype_fail_closed() -> None:
    features = _feature_matrix([1], pd.DatetimeIndex([ORIGIN]))
    reordered = features.loc[:, list(reversed(PREDICTOR_COLUMNS))]
    vocabularies = {
        "Store": (1,),
        "state_holiday": ("0",),
        "store_type": ("a",),
        "assortment": ("a",),
    }
    with pytest.raises(InvalidFeatureSchema, match="names/order"):
        adapt_prediction_features(reordered, vocabularies)
    wrong_dtype = features.copy()
    wrong_dtype["month"] = wrong_dtype["month"].astype("float64")
    with pytest.raises(InvalidFeatureSchema, match="dtypes"):
        adapt_prediction_features(wrong_dtype, vocabularies)
    with pytest.raises(CategoricalAdapterIncompatibility, match="vocabulary fields/order"):
        adapt_prediction_features(features, dict(reversed(list(vocabularies.items()))))


def test_negative_prediction_is_retained_clipped_and_fed_back_as_zero() -> None:
    model = _model(output=-3.0)
    result = _forecast(model=model)
    first = result.loc[result["horizon"].eq(1)].iloc[0]
    assert first["model_forecast_unclipped"] == -3.0
    assert first[FORECAST_COLUMN] == 0.0
    assert bool(first["forecast_was_clipped"])
    booster = model.booster
    assert isinstance(booster, _RecordingBooster)
    assert booster.calls[1]["sales_lag_1"].iloc[0] == 0.0


def test_non_finite_prediction_is_unavailable_and_not_fed_back() -> None:
    model = _model(output=[np.nan, 20.0])
    result = _forecast(model=model)
    first = result.loc[result["horizon"].eq(1)].iloc[0]
    second = result.loc[result["horizon"].eq(2)].iloc[0]
    booster = model.booster
    assert isinstance(booster, _RecordingBooster)
    assert first["unavailable_reason"] == "non_finite_prediction"
    assert pd.isna(first[FORECAST_COLUMN])
    assert np.isnan(booster.calls[1]["sales_lag_1"].iloc[0])
    assert second[FORECAST_COLUMN] == 20.0


def test_operational_open_routing_is_after_raw_forecasting() -> None:
    path = _forecast(model=_model(output=17.0))
    labels = pd.DataFrame(
        {
            "Store": [1, 1, 1],
            "Date": [ORIGIN + pd.Timedelta(days=i) for i in (1, 2, 3)],
            "Sales": [20.0, 20.0, 20.0],
            "Open": [1, 0, np.nan],
        }
    )
    records = attach_lightgbm_labels(
        path,
        _requested_keys(dates=pd.DatetimeIndex(labels["Date"])),
        labels,
        validation_window="validation_1",
    )
    assert records[FORECAST_COLUMN].tolist() == [17.0, 17.0, 17.0]
    assert records["operational_forecast"].iloc[0] == 17.0
    assert records["operational_forecast"].iloc[1] == 0.0
    assert pd.isna(records["operational_forecast"].iloc[2])


def test_unavailable_rows_remain_in_open_label_coverage_denominator() -> None:
    rows: list[dict[str, object]] = []
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        rows.append(
            {
                "Store": 1,
                "forecast_origin": window.forecast_origin,
                "Date": window.target_start,
                "horizon": 1,
                "validation_window": window.name,
                "actual_sales": 100.0,
                "source_open": 1.0,
                FORECAST_COLUMN: np.nan if window.name == "validation_2" else 90.0,
                "forecast_available": window.name != "validation_2",
                "primary_evaluation_eligible": window.name != "validation_2",
            }
        )
    summary = summarize_lightgbm_development(pd.DataFrame(rows))
    failed = summary["by_window"].set_index("validation_window").loc["validation_2"]
    assert failed["open_label_coverage_denominator_rows"] == 1
    assert failed["open_label_forecast_available_rows"] == 0
    assert summary["requires_coverage_review"]


def test_coverage_guardrail_accepts_99_percent_and_rejects_lower_coverage() -> None:
    rows: list[dict[str, object]] = []
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        missing_count = {"validation_1": 1, "validation_2": 2, "validation_3": 0}[window.name]
        for index in range(100):
            available = index >= missing_count
            rows.append(
                {
                    "Store": index + 1,
                    "forecast_origin": window.forecast_origin,
                    "Date": window.target_start,
                    "horizon": 1,
                    "validation_window": window.name,
                    "actual_sales": 100.0,
                    "source_open": 1.0,
                    FORECAST_COLUMN: 90.0 if available else np.nan,
                    "forecast_available": available,
                    "primary_evaluation_eligible": available,
                }
            )
    under = summarize_lightgbm_development(pd.DataFrame(rows))
    assert (
        under["by_window"]
        .set_index("validation_window")
        .loc["validation_1", "open_label_forecast_coverage_rate"]
        == 0.99
    )
    assert under["requires_coverage_review"]
    records = pd.DataFrame(rows)
    validation_2 = records["validation_window"].eq("validation_2")
    missing_idx = records.loc[validation_2 & ~records["forecast_available"]].index[-1]
    records.loc[missing_idx, FORECAST_COLUMN] = 90.0
    records.loc[missing_idx, "forecast_available"] = True
    records.loc[missing_idx, "primary_evaluation_eligible"] = True
    passed = summarize_lightgbm_development(records)
    assert passed["coverage_guardrail_passed"]


def test_paired_comparison_uses_only_identical_available_eligible_keys() -> None:
    window = APPROVED_DEVELOPMENT_WINDOWS[0]
    keys = pd.DataFrame(
        {
            "Store": [1, 2],
            "forecast_origin": [window.forecast_origin] * 2,
            "Date": [window.target_start, window.target_start],
            "horizon": [1, 1],
            "validation_window": [window.name] * 2,
            "actual_sales": [100.0, 200.0],
            "source_open": [1.0, 1.0],
            FORECAST_COLUMN: [90.0, 190.0],
            "forecast_available": [True, True],
            "primary_evaluation_eligible": [True, True],
        }
    )
    baseline = keys.rename(columns={FORECAST_COLUMN: "raw_baseline_forecast"}).copy()
    baseline.loc[1, "raw_baseline_forecast"] = np.nan
    baseline["forecast_available"] = baseline["raw_baseline_forecast"].notna()
    paired = _paired_records(
        keys,
        baseline,
        baseline_column="raw_baseline_forecast",
        baseline_name="seasonal_naive",
    )
    assert len(paired) == 1
    assert paired["Store"].tolist() == [1]


def test_input_frames_are_not_mutated_by_adapter_or_recursion() -> None:
    features = _feature_matrix([1], pd.DatetimeIndex([ORIGIN]))
    covariates = _future_covariates()
    history = _actual_history()
    keys = _requested_keys()
    copies = [frame.copy(deep=True) for frame in (features, covariates, history, keys)]
    model = _model()
    adapt_prediction_features(
        features,
        {
            "Store": (1,),
            "state_holiday": ("0",),
            "store_type": ("a",),
            "assortment": ("a",),
        },
    )
    _forecast(model=model, covariates=covariates, history=history, keys=keys)
    for original, copy in zip((features, covariates, history, keys), copies, strict=True):
        assert_frame_equal(original, copy)


def test_exact_lightgbm_lock_version_and_native_category_missing_behavior() -> None:
    assert lgb.__version__ == "4.7.0"
    dates = pd.date_range(ORIGIN - pd.Timedelta(days=19), periods=20)
    training = _training_rows(dates=dates, sales=[float(value) for value in range(20)])
    prepared = prepare_training_data(training, forecast_origin=ORIGIN)
    fitted = fit_lightgbm(
        prepared,
        num_boost_round=3,
        trial_parameters={
            "learning_rate": 0.1,
            "num_leaves": 3,
            "max_depth": 2,
            "min_data_in_leaf": 1,
        },
    )
    assert fitted.booster is not None
    future = _feature_matrix([1], pd.DatetimeIndex([ORIGIN + pd.Timedelta(days=1)]))
    future["state_holiday"] = pd.Series(["unseen"], dtype="string[python]")
    future["competition_distance"] = np.nan
    prediction, adapted = fitted.predict_features(future)
    assert np.isfinite(prediction).all()
    assert adapted.unseen_category_counts["state_holiday"] == 1
    assert pd.isna(adapted.features["state_holiday"].iloc[0])
    assert fitted.model_parameters["zero_as_missing"] is False


def test_frozen_shared_and_trial_parameters_match_approved_recipes() -> None:
    assert FIXED_PARAMETERS == {
        "boosting_type": "gbdt",
        "objective": "regression_l1",
        "metric": "l1",
        "device_type": "cpu",
        "num_threads": 4,
        "deterministic": True,
        "force_col_wise": True,
        "feature_fraction": 1.0,
        "bagging_fraction": 1.0,
        "bagging_freq": 0,
        "lambda_l2": 1.0,
        "max_bin": 63,
        "zero_as_missing": False,
        "verbosity": -1,
        "seed": 42,
        "data_random_seed": 42,
        "feature_fraction_seed": 42,
        "bagging_seed": 42,
    }
    assert TRIAL_PARAMETERS == {
        "A": {"learning_rate": 0.05, "num_leaves": 15, "max_depth": 4, "min_data_in_leaf": 200},
        "B": {"learning_rate": 0.05, "num_leaves": 31, "max_depth": 5, "min_data_in_leaf": 200},
        "C": {"learning_rate": 0.03, "num_leaves": 15, "max_depth": 4, "min_data_in_leaf": 100},
        "D": {"learning_rate": 0.03, "num_leaves": 31, "max_depth": 5, "min_data_in_leaf": 100},
    }
    assert tuple(trial["trial"] for trial in TRIALS) == ("A", "B", "C", "D")


def test_training_continuation_adds_only_the_requested_boosting_chunk() -> None:
    dates = pd.date_range(ORIGIN - pd.Timedelta(days=19), periods=20)
    prepared = prepare_training_data(
        _training_rows(dates=dates, sales=[float(value) for value in range(20)]),
        forecast_origin=ORIGIN,
    )
    dataset = make_lightgbm_dataset(prepared)
    assert dataset.params["feature_pre_filter"] is False
    trial = {
        "learning_rate": 0.1,
        "num_leaves": 3,
        "max_depth": 2,
        "min_data_in_leaf": 1,
    }
    first = fit_lightgbm(prepared, num_boost_round=3, trial_parameters=trial, dataset=dataset)
    assert first.booster is not None
    next_chunk = fit_lightgbm(
        prepared,
        num_boost_round=2,
        trial_parameters=trial,
        dataset=dataset,
        init_model=first.booster,
    )
    assert next_chunk.booster is not None
    assert next_chunk.booster.current_iteration() == 5


def test_shared_dataset_supports_lower_leaf_size_across_trials() -> None:
    dates = pd.date_range(ORIGIN - pd.Timedelta(days=19), periods=20)
    prepared = prepare_training_data(
        _training_rows(dates=dates, sales=[float(value) for value in range(20)]),
        forecast_origin=ORIGIN,
    )
    dataset = make_lightgbm_dataset(prepared)
    large_leaf_trial = {
        "learning_rate": 0.1,
        "num_leaves": 3,
        "max_depth": 2,
        "min_data_in_leaf": 200,
    }
    small_leaf_trial = {**large_leaf_trial, "min_data_in_leaf": 100}

    assert (
        fit_lightgbm(
            prepared, num_boost_round=2, trial_parameters=large_leaf_trial, dataset=dataset
        ).booster
        is not None
    )
    assert (
        fit_lightgbm(
            prepared, num_boost_round=2, trial_parameters=small_leaf_trial, dataset=dataset
        ).booster
        is not None
    )


def test_fixed_seed_fixture_fit_is_repeatable_in_same_environment() -> None:
    dates = pd.date_range(ORIGIN - pd.Timedelta(days=19), periods=20)
    training = _training_rows(dates=dates, sales=[float(value % 7) for value in range(20)])
    predictions: list[np.ndarray] = []
    for _ in range(2):
        prepared = prepare_training_data(training, forecast_origin=ORIGIN)
        fitted = fit_lightgbm(
            prepared,
            num_boost_round=4,
            trial_parameters={
                "learning_rate": 0.05,
                "num_leaves": 3,
                "max_depth": 2,
                "min_data_in_leaf": 1,
            },
        )
        assert fitted.booster is not None
        adapted = adapt_prediction_features(prepared.features, prepared.category_vocabularies)
        predictions.append(fitted.booster.predict(adapted.features))
    np.testing.assert_array_equal(predictions[0], predictions[1])


def test_no_eligible_rows_has_explicit_failure_without_fallback() -> None:
    training = _training_rows(open_values=[0], sales=[0.0])
    prepared = prepare_training_data(training, forecast_origin=ORIGIN)
    assert prepared.eligible_row_count == 0
    fitted = fit_lightgbm(prepared, num_boost_round=10)
    assert fitted.booster is None
    assert fitted.failure_reason == "no_eligible_training_rows"


@pytest.mark.parametrize(
    ("failure_reason", "expected_reason"),
    [
        ("model_fit_failure", "model_fit_failure"),
        ("categorical_adapter_incompatibility", "categorical_adapter_incompatibility"),
    ],
)
def test_fit_and_adapter_failures_are_explicit_without_fallback(
    failure_reason: str, expected_reason: str
) -> None:
    model = _model()
    if failure_reason == "model_fit_failure":
        model.booster = None
        model.failure_reason = failure_reason
    else:
        model.category_vocabularies = {"wrong": ("category",)}
    result = _forecast(model=model)
    assert result["unavailable_reason"].eq(expected_reason).all()
    assert result[FORECAST_COLUMN].isna().all()


def test_prediction_api_failure_uses_model_failure_reason_without_fallback() -> None:
    model = _model()
    model.booster = _RaisingBooster()

    result = _forecast(model=model)

    assert result["unavailable_reason"].eq("model_fit_failure").all()
    assert result[FORECAST_COLUMN].isna().all()


def test_recursive_state_construction_failure_is_explicit() -> None:
    covariates = _future_covariates()
    covariates.loc[covariates.index[0], "CompetitionOpenSinceMonth"] = 13
    result = _forecast(covariates=covariates)
    first = result.loc[result["horizon"].eq(1)].iloc[0]
    assert first["unavailable_reason"] == "recursive_state_construction_failure"
    assert pd.isna(first[FORECAST_COLUMN])


def test_unavailable_target_reason_is_counted_in_metrics() -> None:
    result = _forecast(
        model=_model(stores=(2,)), covariates=_future_covariates(), keys=_requested_keys()
    )
    assert result["unavailable_reason"].eq("unseen_store_category").all()
    assert result["forecast_available"].sum() == 0


def test_git_ignored_artifact_destinations_are_checked_before_write() -> None:
    root = Path(__file__).resolve().parents[1]
    _assert_ignored(root, [Path("data/processed/lightgbm"), Path("artifacts/lightgbm")])


def test_provenance_snapshots_are_loaded_from_prior_manifests(tmp_path: Path) -> None:
    interim = tmp_path / "interim"
    processed = tmp_path / "processed"
    interim.mkdir()
    processed.mkdir()
    preparation = {
        "command": "rossmann-prepare",
        "source_sha256": SOURCE_SNAPSHOT_SHA256,
        "outputs": {"train.parquet": {"sha256": "phase2-censored-source-id"}},
    }
    feature_manifest = {
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "outputs": {"features_train.parquet": {"sha256": "phase3-snapshot-id"}},
    }
    (interim / "preparation_manifest.json").write_text(json.dumps(preparation), encoding="utf-8")
    (processed / "feature_manifest.json").write_text(json.dumps(feature_manifest), encoding="utf-8")
    provenance = _input_snapshot_identifiers(interim, processed)
    assert provenance["phase2_source_snapshot_sha256"] == SOURCE_SNAPSHOT_SHA256
    assert provenance["phase2_train_snapshot_sha256"] == "phase2-censored-source-id"
    assert provenance["phase3_feature_snapshot_sha256"] == "phase3-snapshot-id"


def test_censored_dataframe_hash_is_stable_and_sensitive_to_used_rows() -> None:
    used = pd.DataFrame({"Store": [1, 1], "Sales": [10.0, 20.0]})
    assert _dataframe_sha256(used) == _dataframe_sha256(used.copy())
    changed = used.assign(Sales=[10.0, 21.0])
    assert _dataframe_sha256(used) != _dataframe_sha256(changed)


def test_read_boundary_filters_synthetic_holdout_before_downstream(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.parquet"
    table = pd.DataFrame(
        {
            "Store": [1, 1],
            "Date": [pd.Timestamp("2015-07-03"), pd.Timestamp("2015-07-04")],
            "Sales": [10.0, 999999.0],
        }
    )
    table.to_parquet(path, index=False)
    filtered = _read_censored_parquet(
        path,
        columns=("Store", "Date", "Sales"),
        end=LAST_DEVELOPMENT_DATE,
    )
    table.loc[1, "Sales"] = -999999.0
    table.to_parquet(path, index=False)
    mutated = _read_censored_parquet(
        path,
        columns=("Store", "Date", "Sales"),
        end=LAST_DEVELOPMENT_DATE,
    )
    assert filtered["Date"].max() == LAST_DEVELOPMENT_DATE
    assert filtered["Date"].max() <= LAST_DEVELOPMENT_DATE
    assert _dataframe_sha256(filtered) == _dataframe_sha256(mutated)


def test_phase3_contract_dtypes_remain_the_source_schema() -> None:
    assert len(PREDICTOR_COLUMNS) == 29
    assert PREDICTOR_DTYPES["Store"] == "int64"
    assert PREDICTOR_DTYPES["state_holiday"] == "string[python]"
    assert PREDICTOR_DTYPES["sales_lag_1"] == "float64"
