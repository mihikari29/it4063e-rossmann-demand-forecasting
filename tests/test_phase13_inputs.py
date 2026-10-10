"""Synthetic-only Phase 13 input contract and default-deny provider tests."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

import rossmann_forecasting.phase13.contracts as phase13_contracts
from rossmann_forecasting.forecasting.lightgbm import FUTURE_COVARIATE_COLUMNS
from rossmann_forecasting.phase13.contracts import (
    BLOCK1_DATES,
    OUTCOME_PROJECTION_COLUMNS,
    PLANNED_OPEN_COLUMNS,
    PROTECTED_DATES,
    RECURSIVE_HISTORY_COLUMNS,
    TRAINING_INPUT_COLUMNS,
    AvailabilityAssumption,
    FutureCovariates,
    OriginCensoredTrainingInputs,
    Phase13InputError,
    RecursiveHistoryInputs,
    RequestedForecastGrid,
    SourceProvenance,
    SyntheticPlannedOpen,
    build_synthetic_planned_open,
)
from rossmann_forecasting.phase13.providers import (
    ISSUANCE_CAPABILITIES,
    ProviderRole,
    SourceBinding,
    SyntheticFrameStore,
    SyntheticInputProvider,
    SyntheticOutcomeAuthorization,
    SyntheticOutcomeProvider,
    _guarded_synthetic_read,
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
        version="synthetic-fixture-v1",
        provenance="Artificial in-memory fixture rows; not Rossmann data.",
        availability_assumption=assumption,
    )


def _covariates(keys: list[tuple[int, date]]) -> pd.DataFrame:
    rows = []
    for store, day in keys:
        rows.append(
            {
                "Store": store,
                "DayOfWeek": day.isoweekday(),
                "Date": pd.Timestamp(day),
                "Promo": 0,
                "StateHoliday": "0",
                "SchoolHoliday": 0,
                "StoreType": "a",
                "Assortment": "a",
                "CompetitionDistance": 100.0 + store,
                "CompetitionOpenSinceMonth": 1,
                "CompetitionOpenSinceYear": 2010,
                "Promo2": 0,
                "Promo2SinceWeek": pd.NA,
                "Promo2SinceYear": pd.NA,
                "PromoInterval": pd.NA,
            }
        )
    return pd.DataFrame(rows, columns=FUTURE_COVARIATE_COLUMNS)


def _training_rows() -> pd.DataFrame:
    keys = [(1, date(2015, 6, 29)), (1, ORIGIN_1), (2, ORIGIN_1)]
    frame = _covariates(keys)
    frame["Sales"] = [0.0, 10.0, 20.0]
    frame["Open"] = [0, 1, 1]
    frame["training_label_eligible"] = [False, True, True]
    return frame.loc[:, TRAINING_INPUT_COLUMNS]


def _history_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            (1, pd.Timestamp("2015-06-29"), 0.0),
            (1, pd.Timestamp("2015-07-03"), 10.0),
            (2, pd.Timestamp("2015-07-03"), 20.0),
        ],
        columns=RECURSIVE_HISTORY_COLUMNS,
    )


def _outcome_frame(day: date) -> pd.DataFrame:
    if day == date(2015, 7, 4):
        sales, opened = 11.0, 1
    elif day == date(2015, 7, 5):
        sales, opened = 17.0, 1
    elif day == date(2015, 7, 6):
        sales, opened = 4.0, 0
    else:
        sales, opened = float(day.day + 20), 1
    return pd.DataFrame([(1, pd.Timestamp(day), sales, opened)], columns=OUTCOME_PROJECTION_COLUMNS)


def _outcome_provider() -> tuple[SyntheticOutcomeProvider, SyntheticFrameStore, dict[date, str]]:
    frames: dict[str, pd.DataFrame] = {}
    sources = {}
    tokens = {}
    token_ids = {}
    for day in PROTECTED_DATES:
        reference = f"memory://phase13/outcome-{day.isoformat()}"
        token_id = f"fixture-token-{day.isoformat()}"
        frames[reference] = _outcome_frame(day)
        sources[day] = SourceBinding(
            ProviderRole.PROTECTED_OUTCOME,
            reference,
            _provenance("protected-fixture", AvailabilityAssumption.SYNTHETIC_RULE),
        )
        tokens[day] = token_id
        token_ids[day] = token_id
    reader = SyntheticFrameStore(frames)
    provider = SyntheticOutcomeProvider(
        reader=reader,
        provider_id="synthetic-outcome-provider",
        store_ids=STORES,
        date_sources=sources,
        authorization_allowlist=tokens,
    )
    return provider, reader, token_ids


def _authorize_read(provider: SyntheticOutcomeProvider, tokens: dict[date, str], day: date):
    return provider.read_day(
        day,
        SyntheticOutcomeAuthorization(
            provider_id=provider.provider_id,
            outcome_date=day,
            token_id=tokens[day],
        ),
    )


def _input_provider(
    grid: RequestedForecastGrid,
    *,
    prior_covariates: FutureCovariates | None = None,
    prior_outcomes=(),
    outcome_decoy: pd.DataFrame | None = None,
) -> tuple[SyntheticInputProvider, SyntheticFrameStore]:
    train_ref = "memory://phase13/train-base"
    history_ref = "memory://phase13/history-base"
    covariate_ref = f"memory://phase13/covariates-{grid.origin.value.isoformat()}"
    frames = {
        train_ref: _training_rows(),
        history_ref: _history_rows(),
        covariate_ref: _covariates(list(grid.keys)),
    }
    if outcome_decoy is not None:
        frames["memory://phase13/sealed-outcome-decoy"] = outcome_decoy.copy(deep=True)
    reader = SyntheticFrameStore(frames)
    bindings = (
        SourceBinding(ProviderRole.TRAINING, train_ref, _provenance("training-base")),
        SourceBinding(ProviderRole.RECURSIVE_HISTORY, history_ref, _provenance("history-base")),
        SourceBinding(
            ProviderRole.FUTURE_COVARIATES,
            covariate_ref,
            _provenance(
                f"covariates-{grid.origin.value.isoformat()}",
                AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN,
            ),
        ),
    )
    provider = SyntheticInputProvider(
        grid=grid,
        reader=reader,
        sources=bindings,
        capabilities=ISSUANCE_CAPABILITIES,
        planned_open_provenance=_provenance(
            "weekly-synthetic-open", AvailabilityAssumption.SYNTHETIC_RULE
        ),
        prior_block1_covariates=prior_covariates,
        prior_block1_outcomes=prior_outcomes,
    )
    return provider, reader


def _release_block1(provider: SyntheticOutcomeProvider, tokens: dict[date, str]):
    return tuple(_authorize_read(provider, tokens, day) for day in BLOCK1_DATES)


def test_supported_origins_have_exact_ordered_h14_grid_independent_of_labels():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    assert grid.dates == tuple(ORIGIN_1 + timedelta(days=lead) for lead in range(1, 15))
    assert grid.requested_key_count == 28
    assert len(grid.to_frame()) == 28
    grid.validate_complete_keys(grid.to_frame())

    full_grid = RequestedForecastGrid(ORIGIN_1)
    assert full_grid.is_full_roster
    assert full_grid.requested_key_count == 15_610

    with pytest.raises(Phase13InputError, match="Unsupported Phase 13 forecast origin"):
        RequestedForecastGrid("2015-07-10", store_ids=STORES)
    missing_label_grid = RequestedForecastGrid(ORIGIN_1, store_ids=(1,))
    assert missing_label_grid.requested_key_count == 14
    assert len(missing_label_grid.to_frame()) == 14


def test_grid_rejects_missing_duplicate_unsorted_and_out_of_roster_keys():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=(1,))
    full = grid.to_frame()
    with pytest.raises(Phase13InputError, match="complete ordered H14"):
        grid.validate_complete_keys(full.iloc[:-1].copy())
    duplicate = pd.concat([full.iloc[:-1], full.iloc[[-2]]], ignore_index=True)
    with pytest.raises(Phase13InputError, match="duplicate Store"):
        grid.validate_complete_keys(duplicate)
    unsorted = full.iloc[::-1].reset_index(drop=True)
    with pytest.raises(Phase13InputError, match="ordered by Store then Date"):
        grid.validate_complete_keys(unsorted)
    with pytest.raises(Phase13InputError, match="roster"):
        RequestedForecastGrid(ORIGIN_1, store_ids=(1, 1116))
    with pytest.raises(Phase13InputError, match="integer"):
        RequestedForecastGrid(ORIGIN_1, store_ids=(True,))


def test_training_contract_rejects_future_rows_and_customers_before_use():
    rows = _training_rows()
    future = _covariates([(1, date(2015, 7, 4))])
    future["Sales"] = 12.0
    future["Open"] = 1
    future["training_label_eligible"] = True
    mixed = pd.concat([rows, future.loc[:, list(TRAINING_INPUT_COLUMNS)]], ignore_index=True)
    mixed = mixed.sort_values(["Store", "Date"], kind="stable").reset_index(drop=True)
    with pytest.raises(Phase13InputError, match="after the fit origin"):
        OriginCensoredTrainingInputs(
            mixed,
            origin=ORIGIN_1,
            store_ids=STORES,
            provenance=_provenance("training"),
        )

    forbidden = rows.copy()
    forbidden["Customers"] = 100
    with pytest.raises(Phase13InputError, match="fields/order"):
        OriginCensoredTrainingInputs(
            forbidden,
            origin=ORIGIN_1,
            store_ids=STORES,
            provenance=_provenance("training"),
        )


def test_training_keeps_closed_day_sales_and_separate_fit_eligibility():
    provider, _ = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    training = provider.read_training_inputs().to_frame()
    closed = training.loc[
        (training["Store"] == 1) & (training["Date"] == pd.Timestamp("2015-06-29"))
    ]
    assert len(closed) == 1
    assert closed.iloc[0]["Sales"] == 0.0
    assert closed.iloc[0]["Open"] == 0
    assert not bool(closed.iloc[0]["training_label_eligible"])


def test_recursive_history_preserves_sparse_dates_and_closed_day_values():
    provider, _ = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    history = provider.read_recursive_history_inputs().to_frame()
    assert len(history) == 3
    assert not ((history["Store"] == 1) & (history["Date"] == pd.Timestamp("2015-06-30"))).any()
    assert (
        history.loc[
            (history["Store"] == 1) & (history["Date"] == pd.Timestamp("2015-06-29")), "Sales"
        ].item()
        == 0.0
    )


def test_training_and_history_contracts_reject_duplicate_or_unrostered_keys():
    history = _history_rows()
    duplicate = pd.concat([history, history.iloc[[0]]], ignore_index=True)
    with pytest.raises(Phase13InputError, match="duplicate Store"):
        RecursiveHistoryInputs(
            duplicate,
            origin=ORIGIN_1,
            store_ids=STORES,
            provenance=_provenance("history"),
        )
    outside = history.copy()
    outside.loc[0, "Store"] = 1116
    with pytest.raises(Phase13InputError, match="roster"):
        RecursiveHistoryInputs(
            outside.sort_values(["Store", "Date"], kind="stable"),
            origin=ORIGIN_1,
            store_ids=(1, 1116),
            provenance=_provenance("history"),
        )


def test_future_covariates_require_exact_label_free_schema_and_origin_window():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    valid = FutureCovariates(
        _covariates(list(grid.keys)),
        grid=grid,
        provenance=_provenance("covars", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN),
    )
    assert tuple(valid.to_frame().columns) == FUTURE_COVARIATE_COLUMNS
    assert len(valid.to_frame()) == grid.requested_key_count

    unavailable = FutureCovariates(
        _covariates(list(grid.keys[:-1])),
        grid=grid,
        provenance=_provenance(
            "partially-unavailable-covars", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN
        ),
    )
    assert len(unavailable.to_frame()) == grid.requested_key_count - 1
    assert grid.requested_key_count == 28

    with_label = _covariates(list(grid.keys))
    with_label["Sales"] = 0.0
    with pytest.raises(Phase13InputError, match="fields/order"):
        FutureCovariates(
            with_label,
            grid=grid,
            provenance=_provenance("bad", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN),
        )
    wrong_dow = _covariates([grid.keys[0]])
    wrong_dow.loc[0, "DayOfWeek"] = 7 if wrong_dow.loc[0, "DayOfWeek"] != 7 else 1
    with pytest.raises(Phase13InputError, match="DayOfWeek conflicts"):
        FutureCovariates(
            wrong_dow,
            grid=grid,
            provenance=_provenance("bad-dow", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN),
        )
    overlapping = _covariates([(1, ORIGIN_1)])
    with pytest.raises(Phase13InputError, match="within this origin's H14"):
        FutureCovariates(
            overlapping,
            grid=grid,
            provenance=_provenance("overlap", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN),
        )


def test_missing_covariate_provenance_fails_closed():
    with pytest.raises(Phase13InputError, match="Source version and provenance"):
        SourceProvenance(
            source_id="covariates",
            version="",
            provenance="",
            availability_assumption=AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN,
        )
    with pytest.raises(Phase13InputError, match="typed source provenance"):
        FutureCovariates(
            _covariates([(1, date(2015, 7, 4))]),
            grid=RequestedForecastGrid(ORIGIN_1, store_ids=STORES),
            provenance=None,
        )


def test_synthetic_planned_open_uses_weekday_rule_and_keeps_unknown_unknown():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=(1,))
    schedule = build_synthetic_planned_open(
        grid, provenance=_provenance("weekly-rule", AvailabilityAssumption.SYNTHETIC_RULE)
    )
    frame = schedule.to_frame()
    assert "Open" not in frame and "ScenarioOpen" not in frame
    sunday = frame.loc[frame["Date"] == pd.Timestamp("2015-07-05"), "planned_open"].item()
    assert not bool(sunday)

    unknown = pd.DataFrame([(1, pd.Timestamp("2015-07-05"), pd.NA)], columns=PLANNED_OPEN_COLUMNS)
    partial = SyntheticPlannedOpen(
        unknown,
        grid=grid,
        provenance=_provenance("partial-weekly-rule", AvailabilityAssumption.SYNTHETIC_RULE),
    )
    assert pd.isna(partial.to_frame().iloc[0]["planned_open"])

    with_actual_open = unknown.assign(Open=1)
    with pytest.raises(Phase13InputError, match="fields/order"):
        SyntheticPlannedOpen(
            with_actual_open,
            grid=grid,
            provenance=_provenance("bad-schedule", AvailabilityAssumption.SYNTHETIC_RULE),
        )


def test_issuance_provider_cannot_read_outcomes_and_uses_only_bound_inputs():
    decoy = pd.DataFrame(
        [(1, pd.Timestamp(day), 999.0, 0, 77) for day in PROTECTED_DATES],
        columns=("Store", "Date", "Sales", "Open", "Customers"),
    )
    provider, reader = _input_provider(
        RequestedForecastGrid(ORIGIN_1, store_ids=STORES), outcome_decoy=decoy
    )
    assert ProviderRole.PROTECTED_OUTCOME not in provider.capabilities
    assert not hasattr(provider, "read_day")
    inputs = provider.read_future_covariates()
    pd.testing.assert_frame_equal(
        inputs.to_frame(), _covariates(list(provider.grid.keys)), check_dtype=False
    )
    assert all("outcome" not in reference for reference in reader.read_calls)


def test_future_outcome_mutations_do_not_change_issuance_input_identity_or_values():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    first = pd.DataFrame(
        [(1, pd.Timestamp(day), 1.0, 1, 10) for day in PROTECTED_DATES],
        columns=("Store", "Date", "Sales", "Open", "Customers"),
    )
    changed = first.copy()
    changed["Sales"] = 123_456.0
    changed["Open"] = 0
    changed["Customers"] = 987_654
    provider_a, _ = _input_provider(grid, outcome_decoy=first)
    provider_b, _ = _input_provider(grid, outcome_decoy=changed)
    covariates_a = provider_a.read_future_covariates()
    covariates_b = provider_b.read_future_covariates()
    assert covariates_a.identity == covariates_b.identity
    pd.testing.assert_frame_equal(covariates_a.to_frame(), covariates_b.to_frame())


def test_planned_open_is_independent_of_future_actual_open_and_sales_are_unchanged():
    outcomes, _, tokens = _outcome_provider()
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    provider, _ = _input_provider(grid)
    schedule = provider.read_planned_open().to_frame()
    _authorize_read(outcomes, tokens, date(2015, 7, 4))
    sunday = _authorize_read(outcomes, tokens, date(2015, 7, 5)).to_frame()
    planned_sunday = schedule.loc[
        (schedule["Store"] == 1) & (schedule["Date"] == pd.Timestamp("2015-07-05")),
        "planned_open",
    ].item()
    actual_sunday = sunday.loc[sunday["Store"] == 1].iloc[0]
    assert not bool(planned_sunday)
    assert actual_sunday["Sales"] == 17.0
    assert actual_sunday["Open"] == 1


def test_outcome_access_requires_date_token_allowlist_and_chronology_before_read():
    provider, reader, tokens = _outcome_provider()
    with pytest.raises(Phase13InputError, match="allowlisted order"):
        provider.read_day(
            date(2015, 7, 5),
            SyntheticOutcomeAuthorization(
                provider.provider_id, date(2015, 7, 5), tokens[date(2015, 7, 5)]
            ),
        )
    assert reader.read_calls == ()

    with pytest.raises(Phase13InputError, match="authorization is required"):
        provider.read_day(date(2015, 7, 4), None)
    assert reader.read_calls == ()

    wrong_token = SyntheticOutcomeAuthorization(
        provider.provider_id, date(2015, 7, 4), "wrong-token"
    )
    with pytest.raises(Phase13InputError, match="does not match"):
        provider.read_day(date(2015, 7, 4), wrong_token)
    assert reader.read_calls == ()


def test_date_specific_outcome_projection_cannot_expose_later_dates_or_customers():
    provider, reader, tokens = _outcome_provider()
    projection = _authorize_read(provider, tokens, date(2015, 7, 4))
    frame = projection.to_frame()
    assert tuple(frame.columns) == OUTCOME_PROJECTION_COLUMNS
    assert frame["Date"].eq(pd.Timestamp("2015-07-04")).all()
    assert "Customers" not in frame
    assert reader.read_calls == ("memory://phase13/outcome-2015-07-04",)

    with pytest.raises(Phase13InputError, match="authorization is required"):
        provider.read_day(date(2015, 7, 5), None)
    assert reader.read_calls == ("memory://phase13/outcome-2015-07-04",)


def test_block2_history_uses_only_authorized_block1_outcomes():
    outcomes, _, tokens = _outcome_provider()
    released = _release_block1(outcomes, tokens)
    released_history = outcomes.released_history_through(ORIGIN_2).to_frame()
    assert set(released_history["Date"].dt.date) == set(BLOCK1_DATES)
    assert not released_history["Date"].gt(pd.Timestamp(ORIGIN_2)).any()
    assert len(released) == 14

    block1, _ = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    prior_covariates = block1.read_future_covariates()
    block2, _ = _input_provider(
        RequestedForecastGrid(ORIGIN_2, store_ids=STORES),
        prior_covariates=prior_covariates,
        prior_outcomes=released,
    )
    history = block2.read_recursive_history_inputs().to_frame()
    assert history["Date"].max() == pd.Timestamp(ORIGIN_2)
    assert set(history.loc[history["Date"].gt(pd.Timestamp(ORIGIN_1)), "Date"].dt.date) == set(
        BLOCK1_DATES
    )

    training = block2.read_training_inputs().to_frame()
    assert training["Date"].max() == pd.Timestamp(ORIGIN_2)
    assert set(training.loc[training["Date"].gt(pd.Timestamp(ORIGIN_1)), "Date"].dt.date) == set(
        BLOCK1_DATES
    )
    assert "Customers" not in training


def test_unreleased_block2_outcomes_remain_inaccessible_after_block1_release():
    outcomes, reader, tokens = _outcome_provider()
    _release_block1(outcomes, tokens)
    released = outcomes.released_history_through(ORIGIN_2).to_frame()
    assert released["Date"].max() == pd.Timestamp(ORIGIN_2)
    before = reader.read_calls
    with pytest.raises(Phase13InputError, match="authorization is required"):
        outcomes.read_day(date(2015, 7, 18), None)
    assert reader.read_calls == before
    assert all(
        pd.Timestamp(day).date() <= ORIGIN_2
        for day in outcomes.released_history_through(ORIGIN_2).to_frame()["Date"]
    )


def test_block2_provider_rejects_missing_or_out_of_order_prior_release_before_read():
    provider1, provider1_reader = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    prior_covariates = provider1.read_future_covariates()
    outcomes, _, tokens = _outcome_provider()
    released = _release_block1(outcomes, tokens)
    with pytest.raises(Phase13InputError, match="chronological order"):
        _input_provider(
            RequestedForecastGrid(ORIGIN_2, store_ids=STORES),
            prior_covariates=prior_covariates,
            prior_outcomes=released[::-1],
        )

    with pytest.raises(Phase13InputError, match="origin"):
        provider1.read_training_inputs(origin=ORIGIN_2)
    assert provider1_reader.read_calls == ("memory://phase13/covariates-2015-07-03",)


def test_provider_guards_unknown_role_path_and_field_before_fake_reader():
    class SpyReader:
        calls: list[str]

        def __init__(self):
            self.calls = []

        def read_memory(self, reference: str) -> pd.DataFrame:
            self.calls.append(reference)
            return _training_rows()

    spy = SpyReader()
    binding = SourceBinding(
        ProviderRole.TRAINING, "memory://phase13/train-base", _provenance("training")
    )
    with pytest.raises(Phase13InputError, match="Unknown Phase 13 provider role"):
        _guarded_synthetic_read(
            spy,
            binding,
            requested_role="unrecognized",
            capabilities=ISSUANCE_CAPABILITIES,
            requested_fields=TRAINING_INPUT_COLUMNS,
            expected_fields=TRAINING_INPUT_COLUMNS,
        )
    with pytest.raises(Phase13InputError, match="capability"):
        _guarded_synthetic_read(
            spy,
            binding,
            requested_role=ProviderRole.PROTECTED_OUTCOME,
            capabilities=ISSUANCE_CAPABILITIES,
            requested_fields=OUTCOME_PROJECTION_COLUMNS,
            expected_fields=OUTCOME_PROJECTION_COLUMNS,
        )
    with pytest.raises(Phase13InputError, match="fields do not match"):
        _guarded_synthetic_read(
            spy,
            binding,
            requested_role=ProviderRole.TRAINING,
            capabilities=ISSUANCE_CAPABILITIES,
            requested_fields=("Store", "Date", "Customers"),
            expected_fields=TRAINING_INPUT_COLUMNS,
        )
    unsafe_binding = SimpleNamespace(
        role=ProviderRole.TRAINING,
        reference="C:\\private\\train.parquet",
    )
    with pytest.raises(Phase13InputError, match="Only recognized memory"):
        _guarded_synthetic_read(
            spy,
            unsafe_binding,
            requested_role=ProviderRole.TRAINING,
            capabilities=ISSUANCE_CAPABILITIES,
            requested_fields=TRAINING_INPUT_COLUMNS,
            expected_fields=TRAINING_INPUT_COLUMNS,
        )
    with pytest.raises(Phase13InputError, match="non-path identifier"):
        SourceProvenance(
            source_id="C:/private/train.parquet",
            version="1",
            provenance="not accepted",
            availability_assumption=AvailabilityAssumption.OBSERVED_THROUGH_ORIGIN,
        )
    assert spy.calls == []


def test_provider_returns_copy_safe_frames_and_store_seals_constructor_input():
    source_rows = _training_rows()
    store = SyntheticFrameStore({"memory://phase13/train-sealed": source_rows})
    source_rows.loc[0, "Sales"] = 555_555.0
    sealed = store.read_memory("memory://phase13/train-sealed")
    assert sealed.loc[0, "Sales"] == 0.0
    sealed.loc[0, "Sales"] = 777_777.0
    assert store.read_memory("memory://phase13/train-sealed").loc[0, "Sales"] == 0.0

    provider, provider_store = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    first = provider.read_training_inputs().to_frame()
    first.loc[0, "Sales"] = 999_999.0
    second = provider.read_training_inputs().to_frame()
    assert second.loc[0, "Sales"] == 0.0
    assert provider_store.read_calls.count("memory://phase13/train-base") == 2


def test_same_authorized_input_has_stable_identity_and_unauthorized_outcome_is_not_hashed(
    monkeypatch,
):
    provider, _ = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    first = provider.read_future_covariates()
    second = provider.read_future_covariates()
    assert first.identity == second.identity

    outcome_provider, reader, _ = _outcome_provider()
    hash_calls = []
    original = phase13_contracts._canonical_identity

    def counted_hash(*args, **kwargs):
        hash_calls.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(phase13_contracts, "_canonical_identity", counted_hash)
    with pytest.raises(Phase13InputError, match="authorization is required"):
        outcome_provider.read_day(BLOCK1_DATES[0], None)
    assert hash_calls == []
    assert reader.read_calls == ()
    authorized = _authorize_read(outcome_provider, _outcome_provider()[2], BLOCK1_DATES[0])
    assert authorized.identity
    assert len(hash_calls) == 1


def test_contracts_reject_open_resolved_customers_scenario_and_schedule_identity_changes():
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    covariates = _covariates(list(grid.keys))
    covariates["Open_resolved"] = 1
    with pytest.raises(Phase13InputError, match="fields/order"):
        FutureCovariates(
            covariates,
            grid=grid,
            provenance=_provenance("unsafe", AvailabilityAssumption.RETROSPECTIVELY_ASSUMED_KNOWN),
        )
    schedule = grid.to_frame()
    schedule["planned_open"] = True
    schedule["ScenarioOpen"] = True
    with pytest.raises(Phase13InputError, match="fields/order"):
        SyntheticPlannedOpen(
            schedule,
            grid=grid,
            provenance=_provenance("schedule", AvailabilityAssumption.SYNTHETIC_RULE),
        )
    with pytest.raises(Phase13InputError, match="Unknown synthetic planned-Open rule"):
        SyntheticPlannedOpen(
            grid.to_frame().assign(planned_open=True),
            grid=grid,
            provenance=_provenance("schedule", AvailabilityAssumption.SYNTHETIC_RULE),
            rule_id="inferred-from-future-open",
        )


def test_missing_and_overlapping_inputs_fail_closed_without_filling_zero():
    with pytest.raises(Phase13InputError, match="without nulls"):
        RecursiveHistoryInputs(
            pd.DataFrame(
                [(1, pd.Timestamp("2015-07-03"), pd.NA)], columns=RECURSIVE_HISTORY_COLUMNS
            ),
            origin=ORIGIN_1,
            store_ids=STORES,
            provenance=_provenance("missing-history"),
        )
    provider, _ = _input_provider(RequestedForecastGrid(ORIGIN_1, store_ids=STORES))
    future_training = _training_rows()
    future_training.loc[future_training.index[-1], "Date"] = pd.Timestamp("2015-07-04")
    with pytest.raises(Phase13InputError, match="after the fit origin"):
        OriginCensoredTrainingInputs(
            future_training,
            origin=ORIGIN_1,
            store_ids=STORES,
            provenance=_provenance("overlap"),
        )
    assert provider.read_recursive_history_inputs().to_frame()["Sales"].notna().all()
