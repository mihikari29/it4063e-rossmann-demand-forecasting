"""Synthetic-only tests for the frozen Phase 13 fresh-fit raw issuer."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import rossmann_forecasting.phase13.issuer as issuer_module
from rossmann_forecasting.features.contract import PREDICTOR_COLUMNS, predictor_schema
from rossmann_forecasting.features.pipeline import build_inference_features
from rossmann_forecasting.forecasting.lightgbm import (
    CATEGORICAL_COLUMNS,
    FUTURE_COVARIATE_COLUMNS,
    FittedLightGBM,
    lightgbm_parameters,
)
from rossmann_forecasting.phase13.contracts import (
    BLOCK1_DATES,
    OUTCOME_PROJECTION_COLUMNS,
    RECURSIVE_HISTORY_COLUMNS,
    TRAINING_INPUT_COLUMNS,
    AvailabilityAssumption,
    FutureCovariates,
    Phase13InputError,
    RequestedForecastGrid,
    SourceProvenance,
)
from rossmann_forecasting.phase13.issuer import (
    SAVE_LOAD_ATOL,
    SAVE_LOAD_RTOL,
    ModelOriginMismatchError,
    Phase13FreshFitIssuer,
)
from rossmann_forecasting.phase13.providers import (
    ISSUANCE_CAPABILITIES,
    ProviderRole,
    SourceBinding,
    SyntheticBlock1ReleaseBundle,
    SyntheticFrameStore,
    SyntheticInputProvider,
    SyntheticOutcomeAuthorization,
    SyntheticOutcomeProvider,
)

ORIGIN_1 = date(2015, 7, 3)
ORIGIN_2 = date(2015, 7, 17)
STORES = (1, 2)


def _provenance(
    source_id: str,
    assumption: AvailabilityAssumption = AvailabilityAssumption.OBSERVED_THROUGH_ORIGIN,
) -> SourceProvenance:
    return SourceProvenance(
        source_id=source_id,
        version="m2-synthetic-fixture-v1",
        provenance="Artificial in-memory rows created by tests; no Rossmann files.",
        availability_assumption=assumption,
    )


def _covariates(keys: list[tuple[int, pd.Timestamp]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for store, day in keys:
        rows.append(
            {
                "Store": store,
                "DayOfWeek": day.isoweekday(),
                "Date": day,
                "Promo": int(day.day % 9 == 0),
                "StateHoliday": "0",
                "SchoolHoliday": 0,
                "StoreType": "a" if store == 1 else "b",
                "Assortment": "a",
                "CompetitionDistance": float(100 + 10 * store),
                "CompetitionOpenSinceMonth": 1,
                "CompetitionOpenSinceYear": 2010,
                "Promo2": 0,
                "Promo2SinceWeek": pd.NA,
                "Promo2SinceYear": pd.NA,
                "PromoInterval": pd.NA,
            }
        )
    return pd.DataFrame(rows, columns=FUTURE_COVARIATE_COLUMNS)


def _training_source() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for store in STORES:
        for day in pd.date_range("2014-01-01", ORIGIN_1, freq="D"):
            opened = day.dayofweek != 6
            sales: float | None = (
                0.0 if not opened else float(900 + store * 37 + day.dayofyear * 1.7)
            )
            if store == 1 and day.date() == date(2015, 3, 2):
                sales = None
            rows.append(
                {
                    "Store": store,
                    "DayOfWeek": day.isoweekday(),
                    "Date": day,
                    "Promo": int(day.day % 9 == 0),
                    "StateHoliday": "0",
                    "SchoolHoliday": 0,
                    "StoreType": "a" if store == 1 else "b",
                    "Assortment": "a",
                    "CompetitionDistance": float(100 + 10 * store),
                    "CompetitionOpenSinceMonth": 1,
                    "CompetitionOpenSinceYear": 2010,
                    "Promo2": 0,
                    "Promo2SinceWeek": pd.NA,
                    "Promo2SinceYear": pd.NA,
                    "PromoInterval": pd.NA,
                    "Sales": sales,
                    "Open": int(opened),
                    "training_label_eligible": bool(opened and sales is not None),
                }
            )
    return pd.DataFrame(rows, columns=TRAINING_INPUT_COLUMNS)


def _history_source(training: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = _training_source() if training is None else training
    return (
        rows.loc[rows["Sales"].notna(), ["Store", "Date", "Sales"]]
        .reset_index(drop=True)
        .loc[:, RECURSIVE_HISTORY_COLUMNS]
    )


def _provider(
    grid: RequestedForecastGrid,
    *,
    future_covariates: pd.DataFrame | None = None,
    extra_frames: dict[str, pd.DataFrame] | None = None,
    prior_block1_covariates: FutureCovariates | None = None,
    prior_block1_release_bundle: SyntheticBlock1ReleaseBundle | None = None,
) -> tuple[SyntheticInputProvider, SyntheticFrameStore, tuple[str, str, str]]:
    train_ref = "memory://phase13/m2-training"
    history_ref = "memory://phase13/m2-history"
    covariate_ref = f"memory://phase13/m2-future-{grid.origin.value.isoformat()}"
    frames = {
        train_ref: _training_source(),
        history_ref: _history_source(),
        covariate_ref: (
            _covariates(list(grid.keys))
            if future_covariates is None
            else future_covariates.copy(deep=True)
        ),
    }
    frames.update(extra_frames or {})
    reader = SyntheticFrameStore(frames)
    sources = (
        SourceBinding(ProviderRole.TRAINING, train_ref, _provenance("m2-training")),
        SourceBinding(ProviderRole.RECURSIVE_HISTORY, history_ref, _provenance("m2-history")),
        SourceBinding(
            ProviderRole.FUTURE_COVARIATES,
            covariate_ref,
            _provenance(
                f"m2-future-{grid.origin.value.isoformat()}",
                AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN,
            ),
        ),
    )
    provider = SyntheticInputProvider(
        grid=grid,
        reader=reader,
        sources=sources,
        capabilities=ISSUANCE_CAPABILITIES,
        planned_open_provenance=_provenance(
            "m2-synthetic-planned-open", AvailabilityAssumption.SYNTHETIC_RULE
        ),
        prior_block1_covariates=prior_block1_covariates,
        prior_block1_release_bundle=prior_block1_release_bundle,
    )
    return provider, reader, (train_ref, history_ref, covariate_ref)


def _issue_and_capture(provider: SyntheticInputProvider):
    original_fit = issuer_module.fit_lightgbm
    captured: list[tuple[FittedLightGBM, object]] = []

    def capture(prepared, **kwargs):
        fitted = original_fit(prepared, **kwargs)
        captured.append((fitted, prepared))
        return fitted

    with patch.object(issuer_module, "fit_lightgbm", side_effect=capture):
        issuance = Phase13FreshFitIssuer().issue(provider)
    assert len(captured) == 1
    return issuance, captured[0][0], captured[0][1]


@pytest.fixture(scope="module")
def block1_issue():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    provider, reader, references = _provider(grid)
    issuance, fitted, prepared = _issue_and_capture(provider)
    return SimpleNamespace(
        grid=grid,
        provider=provider,
        reader=reader,
        references=references,
        issuance=issuance,
        fitted=fitted,
        prepared=prepared,
    )


def _outcome(day: date, *, value_shift: float = 0.0) -> pd.DataFrame:
    rows = []
    for store in STORES:
        opened = day.weekday() != 6
        sales = 0.0 if not opened else float(850 + store * 21 + day.day + value_shift)
        rows.append((store, pd.Timestamp(day), sales, int(opened)))
    return pd.DataFrame(rows, columns=OUTCOME_PROJECTION_COLUMNS)


def _release_provider(
    *, block2_shift: float = 0.0
) -> tuple[SyntheticOutcomeProvider, SyntheticFrameStore, dict[date, str]]:
    frames: dict[str, pd.DataFrame] = {}
    sources: dict[date, SourceBinding] = {}
    tokens: dict[date, str] = {}
    for day in (*BLOCK1_DATES, *(ORIGIN_2 + timedelta(days=lead) for lead in range(1, 15))):
        reference = f"memory://phase13/m2-outcome-{day.isoformat()}"
        shift = block2_shift if day > BLOCK1_DATES[-1] else 0.0
        frames[reference] = _outcome(day, value_shift=shift)
        sources[day] = SourceBinding(
            ProviderRole.PROTECTED_OUTCOME,
            reference,
            _provenance("m2-synthetic-outcome-source", AvailabilityAssumption.SYNTHETIC_RULE),
        )
        tokens[day] = f"synthetic-token-{day.isoformat()}"
    reader = SyntheticFrameStore(frames)
    provider = SyntheticOutcomeProvider(
        reader=reader,
        provider_id="m2-synthetic-outcome-provider",
        store_ids=STORES,
        date_sources=sources,
        authorization_allowlist=tokens,
    )
    return provider, reader, tokens


def _release_block1(provider: SyntheticOutcomeProvider, tokens: dict[date, str]) -> None:
    for day in BLOCK1_DATES:
        provider.read_day(
            day,
            SyntheticOutcomeAuthorization(
                provider_id=provider.provider_id,
                outcome_date=day,
                token_id=tokens[day],
            ),
        )


def _block2_provider(*, block2_shift: float = 0.0):
    block1_grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    block1_covariates = FutureCovariates(
        _covariates(list(block1_grid.keys)),
        grid=block1_grid,
        provenance=_provenance(
            "m2-issued-block1-covariates", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN
        ),
    )
    outcomes, outcome_reader, tokens = _release_provider(block2_shift=block2_shift)
    _release_block1(outcomes, tokens)
    bundle = outcomes.create_block1_release_bundle(block1_covariates)
    grid = RequestedForecastGrid(ORIGIN_2, store_ids=STORES)
    provider, input_reader, references = _provider(
        grid,
        prior_block1_covariates=block1_covariates,
        prior_block1_release_bundle=bundle,
    )
    return SimpleNamespace(
        provider=provider,
        grid=grid,
        input_reader=input_reader,
        outcome_reader=outcome_reader,
        outcome_provider=outcomes,
        references=references,
    )


def test_issuer_emits_exact_h14_accounted_grid_and_frozen_fit(block1_issue):
    result = block1_issue.issuance
    records = result.to_frame()
    assert result.origin == ORIGIN_1
    assert result.requested_key_count == 28
    assert result.all_requested_keys_accounted
    assert result.complete_path_available
    assert result.available_row_count == 28
    assert result.unavailable_row_count == 0
    assert result.requested_boost_rounds == 180
    assert result.actual_tree_count == 180
    assert result.model_name == "global_lightgbm_gbdt_regression_l1"
    assert result.training_counts.input_rows == len(_training_source())
    assert result.training_counts.missing_label_excluded_rows == 1
    assert result.training_counts.valid_observed_label_rows == len(_training_source()) - 1
    assert result.training_counts.observed_closed_history_rows > 0
    assert (
        result.training_counts.eligible_source_open_rows
        == result.training_counts.fitted_eligible_rows
    )
    assert block1_issue.fitted.fit_row_count == result.training_counts.fitted_eligible_rows
    assert block1_issue.fitted.model_parameters == lightgbm_parameters(
        {"learning_rate": 0.05, "num_leaves": 15, "max_depth": 4, "min_data_in_leaf": 200}
    )
    assert tuple(block1_issue.fitted.category_vocabularies) == CATEGORICAL_COLUMNS
    assert tuple(records.columns).count("raw_forecast") == 1
    assert tuple(records.columns).count("unclipped_forecast") == 1
    assert tuple(records.columns).count("recursive_state_value") == 1
    assert tuple(records.columns).count("requested_key") == 1
    assert not any(
        name.casefold() in {"sales", "open", "customers", "open_resolved"}
        or "customer" in name.casefold()
        for name in records.columns
    )
    assert set(records["horizon"]) == set(range(1, 15))
    for store in STORES:
        part = records.loc[records["Store"].eq(store)].sort_values("horizon")
        assert part["Date"].tolist() == [pd.Timestamp(day) for day in block1_issue.grid.dates]
        assert part["horizon"].tolist() == list(range(1, 15))
        np.testing.assert_allclose(
            part["raw_forecast"], part["recursive_state_value"], rtol=0.0, atol=0.0
        )
    grid = block1_issue.grid.to_frame()
    grid["Date"] = pd.to_datetime(grid["Date"]).astype("datetime64[ns]")
    assert_frame_equal(records[["Store", "Date"]].reset_index(drop=True), grid)


def test_only_two_precommitted_origins_are_constructible():
    for origin in (ORIGIN_1, ORIGIN_2):
        grid = RequestedForecastGrid(origin, store_ids=STORES)
        assert len(grid.dates) == 14
    with pytest.raises(Phase13InputError, match="Unsupported Phase 13 forecast origin"):
        RequestedForecastGrid("2015-07-10", store_ids=STORES)


def test_fitted_origin_mismatch_fails_before_recursive_prediction(block1_issue, monkeypatch):
    provider, _, _ = _provider(block1_issue.grid)
    wrong = replace(
        block1_issue.fitted,
        forecast_origin=pd.Timestamp(ORIGIN_2),
    )
    monkeypatch.setattr(issuer_module, "fit_lightgbm", lambda prepared, **kwargs: wrong)
    monkeypatch.setattr(
        issuer_module,
        "recursive_lightgbm_forecasts",
        lambda *args, **kwargs: pytest.fail("recursive prediction ran for a mismatched fit"),
    )
    with pytest.raises(ModelOriginMismatchError, match="differs from issuer origin"):
        Phase13FreshFitIssuer().issue(provider)


def test_missing_label_rows_are_excluded_without_losing_closed_history(block1_issue):
    counts = block1_issue.issuance.training_counts
    assert (
        counts.input_rows == counts.valid_observed_label_rows + counts.missing_label_excluded_rows
    )
    assert counts.valid_observed_label_rows == counts.input_rows - 1
    assert counts.observed_closed_history_rows > 0
    # The observed Sunday zero from the origin remains the exact one-day history feature.
    records = block1_issue.issuance.to_frame()
    sunday_origin = date(2015, 6, 28)
    assert sunday_origin in _history_source()["Date"].dt.date.tolist()
    assert (
        0.0
        in _history_source()
        .loc[_history_source()["Date"].dt.date.eq(sunday_origin), "Sales"]
        .tolist()
    )
    assert records["raw_forecast"].notna().all()


def test_future_open_and_customers_cannot_enter_issuer_inputs(block1_issue, monkeypatch):
    grid = block1_issue.grid
    bad_future = _covariates(list(grid.keys)).assign(Customers=123.0)
    provider, _, _ = _provider(grid, future_covariates=bad_future)
    called = False

    def forbidden_fit(prepared, **kwargs):
        nonlocal called
        called = True
        return block1_issue.fitted

    monkeypatch.setattr(issuer_module, "fit_lightgbm", forbidden_fit)
    with pytest.raises(Phase13InputError, match="source fields/order"):
        Phase13FreshFitIssuer().issue(provider)
    assert not called

    bad_future = _covariates(list(grid.keys)).assign(Open=1)
    provider, _, _ = _provider(grid, future_covariates=bad_future)
    with pytest.raises(Phase13InputError, match="source fields/order"):
        Phase13FreshFitIssuer().issue(provider)
    assert not called


def test_raw_issue_ignores_planned_open_and_sealed_future_outcomes(block1_issue, monkeypatch):
    sealed_a = "memory://phase13/sealed-outcome-a"
    sealed_b = "memory://phase13/sealed-outcome-b"
    outcomes_a = pd.DataFrame({"Sales": [1.0], "Open": [1], "Customers": [10]})
    outcomes_b = pd.DataFrame({"Sales": [999_999.0], "Open": [0], "Customers": [90_000]})
    provider_a, _, _ = _provider(block1_issue.grid, extra_frames={sealed_a: outcomes_a})
    provider_b, reader_b, _ = _provider(block1_issue.grid, extra_frames={sealed_b: outcomes_b})
    monkeypatch.setattr(
        issuer_module, "fit_lightgbm", lambda prepared, **kwargs: block1_issue.fitted
    )
    monkeypatch.setattr(
        SyntheticInputProvider,
        "read_planned_open",
        lambda *args, **kwargs: pytest.fail("raw issue consulted planned Open"),
    )
    result_a = Phase13FreshFitIssuer().issue(provider_a)
    result_b = Phase13FreshFitIssuer().issue(provider_b)
    assert reader_b.read_calls == tuple(block1_issue.references)
    assert result_a.input_identities == result_b.input_identities
    assert_frame_equal(result_a.to_frame(), result_b.to_frame())


def test_recursive_state_uses_origin_actuals_and_prior_raw_predictions(block1_issue, monkeypatch):
    provider, _, _ = _provider(block1_issue.grid)
    captured: list[pd.DataFrame] = []
    original_predict = FittedLightGBM.predict_features

    def capture_predict(self, features):
        captured.append(features[["Store", "sales_lag_1"]].copy())
        return original_predict(self, features)

    monkeypatch.setattr(
        issuer_module, "fit_lightgbm", lambda prepared, **kwargs: block1_issue.fitted
    )
    monkeypatch.setattr(FittedLightGBM, "predict_features", capture_predict)
    result = Phase13FreshFitIssuer().issue(provider)
    records = result.to_frame()
    history = _history_source()
    origin_values = history.loc[history["Date"].eq(pd.Timestamp(ORIGIN_1))].set_index("Store")[
        "Sales"
    ]
    for store in STORES:
        assert captured[0].set_index("Store").loc[store, "sales_lag_1"] == origin_values.loc[store]
        by_horizon = records.loc[records["Store"].eq(store)].set_index("horizon")
        assert (
            captured[1].set_index("Store").loc[store, "sales_lag_1"]
            == by_horizon.loc[1, "raw_forecast"]
        )
        assert (
            captured[2].set_index("Store").loc[store, "sales_lag_1"]
            == by_horizon.loc[2, "raw_forecast"]
        )


def test_missing_future_key_and_required_covariate_stay_explicit(block1_issue, monkeypatch):
    grid = block1_issue.grid
    future = _covariates(list(grid.keys))
    missing_key_date = pd.Timestamp(grid.dates[2])
    missing_covariate_date = pd.Timestamp(grid.dates[4])
    drop_key = future["Store"].eq(1) & pd.to_datetime(future["Date"]).eq(missing_key_date)
    future = future.loc[~drop_key].copy()
    assert not (future["Store"].eq(1) & pd.to_datetime(future["Date"]).eq(missing_key_date)).any()
    future.loc[
        future["Store"].eq(2) & pd.to_datetime(future["Date"]).eq(missing_covariate_date),
        "Promo",
    ] = pd.NA
    provider, _, _ = _provider(grid, future_covariates=future)
    captured: list[pd.DataFrame] = []
    original_predict = FittedLightGBM.predict_features

    def capture_predict(self, features):
        captured.append(features[["Store", "sales_lag_1"]].copy())
        return original_predict(self, features)

    monkeypatch.setattr(
        issuer_module, "fit_lightgbm", lambda prepared, **kwargs: block1_issue.fitted
    )
    monkeypatch.setattr(FittedLightGBM, "predict_features", capture_predict)
    result = Phase13FreshFitIssuer().issue(provider)
    records = result.to_frame()
    missing_key = records.loc[records["Store"].eq(1) & records["Date"].eq(missing_key_date)].iloc[0]
    assert not missing_key["forecast_available"]
    assert missing_key["unavailable_reason"] == "missing_target_key"
    assert pd.isna(missing_key["raw_forecast"])
    missing_covariate = records.loc[
        records["Store"].eq(2) & records["Date"].eq(missing_covariate_date)
    ].iloc[0]
    assert not missing_covariate["forecast_available"]
    assert missing_covariate["unavailable_reason"] == "missing_required_covariate:promo"
    assert pd.isna(missing_covariate["raw_forecast"])
    assert result.all_requested_keys_accounted
    assert result.available_row_count == 26
    assert result.unavailable_row_count == 2
    assert not result.complete_path_available
    # h4 has no d-1 value for Store 1; it stays null rather than borrowing an earlier row or zero.
    h4_store1 = captured[3].set_index("Store").loc[1, "sales_lag_1"]
    assert pd.isna(h4_store1)
    assert len(records) == grid.requested_key_count


def test_fit_failure_is_unavailable_and_never_falls_back(block1_issue, monkeypatch):
    provider, _, _ = _provider(block1_issue.grid)

    def failed_fit(prepared, **kwargs):
        return FittedLightGBM(
            booster=None,
            category_vocabularies=prepared.category_vocabularies,
            fit_row_count=prepared.eligible_row_count,
            forecast_origin=prepared.origin,
            model_parameters=lightgbm_parameters(
                {"learning_rate": 0.05, "num_leaves": 15, "max_depth": 4, "min_data_in_leaf": 200}
            ),
            failure_reason="model_fit_failure",
        )

    monkeypatch.setattr(issuer_module, "fit_lightgbm", failed_fit)
    result = Phase13FreshFitIssuer().issue(provider)
    records = result.to_frame()
    assert result.all_requested_keys_accounted
    assert not result.complete_path_available
    assert result.actual_tree_count is None
    assert result.available_row_count == 0
    assert result.unavailable_row_count == 28
    assert not records["forecast_available"].any()
    assert records["unavailable_reason"].eq("model_fit_failure").all()
    assert (
        records[["raw_forecast", "unclipped_forecast", "recursive_state_value"]].isna().all().all()
    )


def test_issue_is_reproducible_for_same_synthetic_fit_inputs(block1_issue):
    provider_a, _, _ = _provider(block1_issue.grid)
    provider_b, _, _ = _provider(block1_issue.grid)
    first, first_model, _ = _issue_and_capture(provider_a)
    second, second_model, _ = _issue_and_capture(provider_b)
    assert first.input_identities == second.input_identities
    assert first.recipe_identity == second.recipe_identity
    assert first.model_identity == second.model_identity
    assert first.fit_identity == second.fit_identity
    assert first_model.booster.num_trees() == second_model.booster.num_trees() == 180
    assert_frame_equal(first.to_frame(), second.to_frame(), check_exact=True)


def test_booster_round_trip_preserves_adapter_recipe_origin_and_predictions(
    block1_issue, tmp_path: Path
):
    assert SAVE_LOAD_RTOL == 1e-12
    assert SAVE_LOAD_ATOL == 1e-9
    fitted = block1_issue.fitted
    assert fitted.booster is not None
    target_day = pd.Timestamp(ORIGIN_1) + pd.Timedelta(days=1)
    future = _covariates(list(block1_issue.grid.keys))
    one_day = future.loc[pd.to_datetime(future["Date"]).eq(target_day)].copy()
    history = _history_source()
    features, _ = build_inference_features(
        one_day,
        actual_history_through_origin=history,
        forecast_origin=ORIGIN_1,
    )
    model_inputs, _ = fitted.predict_features(features.loc[:, PREDICTOR_COLUMNS])
    model_path = tmp_path / "synthetic-phase13-booster.txt"
    state_path = tmp_path / "synthetic-phase13-adapter.json"
    fitted.booster.save_model(str(model_path))
    state = {
        "origin": pd.Timestamp(fitted.forecast_origin).date().isoformat(),
        "model_parameters": fitted.model_parameters,
        "fit_row_count": fitted.fit_row_count,
        "category_vocabularies": {
            column: [int(value) if column == "Store" else str(value) for value in values]
            for column, values in fitted.category_vocabularies.items()
        },
        "category_vocabulary_order": list(CATEGORICAL_COLUMNS),
        "ordered_features": list(PREDICTOR_COLUMNS),
        "feature_schema": predictor_schema(),
        "recipe_identity": block1_issue.issuance.recipe_identity,
        "feature_schema_identity": block1_issue.issuance.feature_schema_identity,
        "tree_count": int(fitted.booster.num_trees()),
    }
    state_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    restored_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert restored_state["origin"] == ORIGIN_1.isoformat()
    assert restored_state["recipe_identity"] == block1_issue.issuance.recipe_identity
    assert restored_state["ordered_features"] == list(PREDICTOR_COLUMNS)
    assert restored_state["category_vocabulary_order"] == list(CATEGORICAL_COLUMNS)
    assert restored_state["feature_schema"] == predictor_schema()
    assert (
        restored_state["feature_schema_identity"] == block1_issue.issuance.feature_schema_identity
    )

    restored_vocabularies = {
        column: tuple(restored_state["category_vocabularies"][column])
        for column in CATEGORICAL_COLUMNS
    }
    restored = FittedLightGBM(
        booster=lgb.Booster(model_file=str(model_path)),
        category_vocabularies=restored_vocabularies,
        fit_row_count=restored_state["fit_row_count"],
        forecast_origin=pd.Timestamp(restored_state["origin"]),
        model_parameters=restored_state["model_parameters"],
    )
    assert restored.booster.num_trees() == restored.booster.current_iteration() == 180
    assert restored.category_vocabularies == fitted.category_vocabularies
    reloaded_predictions, _ = restored.predict_features(features.loc[:, PREDICTOR_COLUMNS])
    np.testing.assert_allclose(
        model_inputs,
        reloaded_predictions,
        rtol=SAVE_LOAD_RTOL,
        atol=SAVE_LOAD_ATOL,
    )


def test_block2_requires_verified_block1_handoff_and_reads_no_new_outcomes():
    grid = RequestedForecastGrid(ORIGIN_2, store_ids=STORES)
    block1_grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    block1_covariates = FutureCovariates(
        _covariates(list(block1_grid.keys)),
        grid=block1_grid,
        provenance=_provenance(
            "m2-issued-block1-covariates", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN
        ),
    )
    with pytest.raises(Phase13InputError, match="verified Block 1 release handoff"):
        _provider(grid, prior_block1_covariates=block1_covariates)

    block2 = _block2_provider()
    reads_before = block2.outcome_reader.read_calls
    assert len(reads_before) == len(BLOCK1_DATES)
    assert all(
        date.fromisoformat(reference[-10:]) <= BLOCK1_DATES[-1] for reference in reads_before
    )
    issuance, fitted, _ = _issue_and_capture(block2.provider)
    assert issuance.origin == ORIGIN_2
    assert issuance.actual_tree_count == 180
    assert issuance.available_row_count == block2.grid.requested_key_count
    assert issuance.unavailable_row_count == 0
    assert fitted.forecast_origin == pd.Timestamp(ORIGIN_2)
    assert block2.outcome_reader.read_calls == reads_before
    assert len(issuance.to_frame()) == block2.grid.requested_key_count


def test_unreleased_block2_mutation_cannot_change_scheduled_block2_issuance(
    block1_issue, monkeypatch
):
    first = _block2_provider(block2_shift=0.0)
    second = _block2_provider(block2_shift=900_000.0)
    assert first.outcome_reader.read_calls == second.outcome_reader.read_calls
    first_result, fitted, _ = _issue_and_capture(first.provider)
    monkeypatch.setattr(issuer_module, "fit_lightgbm", lambda prepared, **kwargs: fitted)
    second_result = Phase13FreshFitIssuer().issue(second.provider)
    assert first_result.input_identities == second_result.input_identities
    assert_frame_equal(first_result.to_frame(), second_result.to_frame(), check_exact=True)
    assert first.outcome_reader.read_calls == second.outcome_reader.read_calls
    assert len(first.outcome_reader.read_calls) == len(BLOCK1_DATES)
    assert all(
        date.fromisoformat(reference[-10:]) <= BLOCK1_DATES[-1]
        for reference in first.outcome_reader.read_calls
    )


def test_provider_references_are_memory_only_and_no_source_file_reader_is_needed(
    block1_issue, monkeypatch
):
    provider, reader, references = _provider(block1_issue.grid)
    assert all(reference.startswith("memory://phase13/") for reference in references)
    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: pytest.fail("file CSV read"))
    monkeypatch.setattr(
        pd, "read_parquet", lambda *args, **kwargs: pytest.fail("file Parquet read")
    )
    monkeypatch.setattr(
        issuer_module, "fit_lightgbm", lambda prepared, **kwargs: block1_issue.fitted
    )
    result = Phase13FreshFitIssuer().issue(provider)
    assert len(reader.read_calls) == 3
    assert result.all_requested_keys_accounted
