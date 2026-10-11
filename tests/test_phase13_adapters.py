"""Golden synthetic-only Phase 13 M3 adapter tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from fractions import Fraction
from hashlib import sha256

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import rossmann_forecasting.forecasting.uncertainty as uncertainty_module
from rossmann_forecasting.forecasting.lightgbm import MODEL_NAME
from rossmann_forecasting.forecasting.model_selection import CANDIDATE_IDS
from rossmann_forecasting.phase13.adapters import (
    CALIBRATION_WINDOWS,
    CUMULATIVE_ERROR_POPULATION,
    CUMULATIVE_LEVELS,
    DAILY_ERROR_POPULATION,
    FIT_B_ID,
    FROZEN_FIT_B_METADATA,
    HISTORICAL_SCHEDULE_ASSUMPTION,
    POLICY_IDS,
    PREFIX_DEFINITION,
    SYNTHETIC_TARGET_SEMANTICS,
    UNCERTAINTY_POLICY_VERSION,
    FitBCanonicalMetadata,
    FitBTransportMetadata,
    OriginFrozenStandingTargets,
    Phase13AdapterError,
    Phase13M3Adapter,
    SyntheticFitBQuantileFixture,
    SyntheticHistoricalMeanAnchor,
    SyntheticHistoricalMeanAnchorCollection,
    load_canonical_fit_b_quantiles,
)
from rossmann_forecasting.phase13.contracts import (
    HORIZON,
    PLANNED_OPEN_COLUMNS,
    SUPPORTED_ORIGINS,
    SYNTHETIC_OPEN_RULE_ID,
    AvailabilityAssumption,
    Phase13InputError,
    RequestedForecastGrid,
    SourceProvenance,
    SyntheticPlannedOpen,
)
from rossmann_forecasting.phase13.issuer import (
    NUM_BOOST_ROUND,
    Phase13IssuanceError,
    RawForecastIssuance,
    TrainingRowCounts,
    _frozen_recipe,
    _identity,
    _schema_identity,
)

ORIGIN_1 = date(2015, 7, 3)
ORIGIN_2 = date(2015, 7, 17)
STORES = (1, 2)
DAILY_COLUMNS = (
    "fit_id",
    "horizon",
    "tail",
    "tail_level",
    "error_population",
    "n",
    "rank_1_indexed",
    "signed_quantile",
    "available",
    "unavailable_reason",
    "policy_version",
    "selected_candidate_id",
    "calibration_windows",
)
CUMULATIVE_COLUMNS = (
    "fit_id",
    "k",
    "p",
    "error_population",
    "n",
    "rank_1_indexed",
    "signed_quantile",
    "available",
    "unavailable_reason",
    "prefix_definition",
    "schedule_assumption",
    "policy_version",
    "selected_candidate_id",
    "calibration_windows",
)


def _sha(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _daily_rank(n: int, tail: str) -> int:
    return (n + 1) // 40 if tail == "lower" else (39 * (n + 1) + 39) // 40


def _upper_rank(n: int, probability: float) -> int:
    value = (n + 1) * Fraction(str(probability))
    return (value.numerator + value.denominator - 1) // value.denominator


def _raw_issuance(
    origin: date = ORIGIN_1,
    *,
    unavailable: set[tuple[int, int]] | None = None,
    records_override: pd.DataFrame | None = None,
) -> RawForecastIssuance:
    unavailable = unavailable or set()
    grid = RequestedForecastGrid(origin, store_ids=STORES)
    recipe_identity = _identity(_frozen_recipe())
    schema_identity = _schema_identity()
    model_identity = _sha(f"model-{origin.isoformat()}")
    fit_identity = _sha(f"fit-{origin.isoformat()}")
    input_identities = (
        ("requested_grid", grid.identity),
        ("training", _sha("training")),
        ("recursive_history", _sha("history")),
        ("future_covariates", _sha(f"covariates-{origin.isoformat()}")),
    )
    identity_map = dict(input_identities)
    rows = []
    for store, target_date in grid.keys:
        horizon = (target_date - origin).days
        is_available = (store, horizon) not in unavailable
        point = 10.0 if horizon == 1 else float(store * 100 + horizon * 10)
        rows.append(
            {
                "requested_key": f"{store}:{target_date.isoformat()}",
                "Store": store,
                "Date": pd.Timestamp(target_date),
                "forecast_origin": pd.Timestamp(origin),
                "horizon": horizon,
                "model": MODEL_NAME,
                "raw_forecast": point if is_available else None,
                "unclipped_forecast": point if is_available else None,
                "recursive_state_value": point if is_available else None,
                "forecast_was_clipped": False if is_available else pd.NA,
                "forecast_available": is_available,
                "unavailable_reason": None if is_available else "missing_required_covariate:promo",
                "unseen_store_category": False,
                "unseen_state_holiday": False,
                "unseen_store_type": False,
                "unseen_assortment": False,
                "model_identity": model_identity,
                "fit_identity": fit_identity,
                "recipe_identity": recipe_identity,
                "feature_schema_identity": schema_identity,
                "requested_grid_identity": grid.identity,
                "training_input_identity": identity_map["training"],
                "recursive_history_identity": identity_map["recursive_history"],
                "future_covariate_identity": identity_map["future_covariates"],
            }
        )
    records = (
        records_override.copy(deep=True)
        if records_override is not None
        else pd.DataFrame.from_records(rows)
    )
    available_count = int(records["forecast_available"].astype(bool).sum())
    complete = available_count == grid.requested_key_count
    return RawForecastIssuance(
        origin=origin,
        grid_identity=grid.identity,
        recipe_identity=recipe_identity,
        feature_schema_identity=schema_identity,
        fit_identity=fit_identity,
        model_identity=model_identity,
        model_name=CANDIDATE_IDS[2],
        requested_key_count=grid.requested_key_count,
        available_row_count=available_count,
        unavailable_row_count=grid.requested_key_count - available_count,
        all_requested_keys_accounted=len(records) == grid.requested_key_count,
        complete_path_available=complete,
        requested_boost_rounds=NUM_BOOST_ROUND,
        actual_tree_count=NUM_BOOST_ROUND,
        training_counts=TrainingRowCounts(1, 1, 0, 0, 1, 1),
        input_identities=input_identities,
        category_vocabulary_hashes=(),
        _records=records,
    )


def _planned_open(
    origin: date = ORIGIN_1,
    *,
    unknown: set[tuple[int, int]] | None = None,
    omit: set[tuple[int, int]] | None = None,
    extra_columns: dict[str, object] | None = None,
) -> SyntheticPlannedOpen:
    unknown = unknown or set()
    omit = omit or set()
    grid = RequestedForecastGrid(origin, store_ids=STORES)
    frame = grid.to_frame()
    frame["planned_open"] = pd.array(
        [pd.Timestamp(day).weekday() != 6 for day in frame["Date"]],
        dtype="boolean",
    )
    if unknown:
        mask = pd.Series(
            [
                (int(store), (pd.Timestamp(day) - pd.Timestamp(origin)).days) in unknown
                for store, day in frame[["Store", "Date"]].itertuples(index=False, name=None)
            ],
            index=frame.index,
        )
        frame.loc[mask, "planned_open"] = pd.NA
    if omit:
        mask = pd.Series(
            [
                (int(store), (pd.Timestamp(day) - pd.Timestamp(origin)).days) in omit
                for store, day in frame[["Store", "Date"]].itertuples(index=False, name=None)
            ],
            index=frame.index,
        )
        frame = frame.loc[~mask].copy()
    for column, value in (extra_columns or {}).items():
        frame[column] = value
    provenance = SourceProvenance(
        source_id="phase13.synthetic.planned-open",
        version="fixture-v1",
        provenance="Artificial Monday-Saturday open and Sunday closed fixture.",
        availability_assumption=AvailabilityAssumption.SYNTHETIC_RULE,
    )
    return SyntheticPlannedOpen(
        frame.loc[:, PLANNED_OPEN_COLUMNS] if not extra_columns else frame,
        grid=grid,
        provenance=provenance,
        rule_id=SYNTHETIC_OPEN_RULE_ID,
    )


def _daily_table(
    *,
    unsupported_horizons: set[int] | None = None,
    sample_counts: dict[int, int] | None = None,
) -> pd.DataFrame:
    unsupported_horizons = unsupported_horizons or set()
    sample_counts = sample_counts or {}
    rows = []
    for horizon in range(1, HORIZON + 1):
        n = sample_counts.get(horizon, 39 if horizon in unsupported_horizons else 100)
        for tail in ("lower", "upper"):
            q = (
                (-20.0 if tail == "lower" else -15.0)
                if horizon == 1
                else (-15.0 if tail == "lower" else 5.0)
                if horizon == 2
                else (-10.0 if tail == "lower" else 10.0)
            )
            unsupported = n < 40
            rows.append(
                {
                    "fit_id": FIT_B_ID,
                    "horizon": horizon,
                    "tail": tail,
                    "tail_level": 0.025 if tail == "lower" else 0.975,
                    "error_population": DAILY_ERROR_POPULATION,
                    "n": n,
                    "rank_1_indexed": _daily_rank(n, tail),
                    "signed_quantile": None if unsupported else q,
                    "available": not unsupported,
                    "unavailable_reason": ("insufficient_calibration" if unsupported else None),
                    "policy_version": UNCERTAINTY_POLICY_VERSION,
                    "selected_candidate_id": CANDIDATE_IDS[2],
                    "calibration_windows": CALIBRATION_WINDOWS,
                }
            )
    return pd.DataFrame.from_records(rows, columns=DAILY_COLUMNS)


def _cumulative_table(
    *,
    unsupported_keys: set[tuple[int, float]] | None = None,
    sample_counts: dict[tuple[int, float], int] | None = None,
) -> pd.DataFrame:
    unsupported_keys = unsupported_keys or set()
    sample_counts = sample_counts or {}
    unsupported_prefixes = {k for k, _probability in unsupported_keys}
    rows = []
    for k in range(1, HORIZON + 1):
        for probability in CUMULATIVE_LEVELS:
            n = sample_counts.get(
                (k, probability),
                49 if k in unsupported_prefixes else 100,
            )
            q_by_probability = {0.90: -5.0, 0.95: 2.0, 0.98: 4.0}
            unsupported = n < 50
            rows.append(
                {
                    "fit_id": FIT_B_ID,
                    "k": k,
                    "p": probability,
                    "error_population": CUMULATIVE_ERROR_POPULATION,
                    "n": n,
                    "rank_1_indexed": _upper_rank(n, probability),
                    "signed_quantile": (None if unsupported else q_by_probability[probability] * k),
                    "available": not unsupported,
                    "unavailable_reason": ("insufficient_calibration" if unsupported else None),
                    "prefix_definition": PREFIX_DEFINITION,
                    "schedule_assumption": HISTORICAL_SCHEDULE_ASSUMPTION,
                    "policy_version": UNCERTAINTY_POLICY_VERSION,
                    "selected_candidate_id": CANDIDATE_IDS[2],
                    "calibration_windows": CALIBRATION_WINDOWS,
                }
            )
    return pd.DataFrame.from_records(rows, columns=CUMULATIVE_COLUMNS)


def _fixture(
    raw: RawForecastIssuance,
    *,
    daily_unsupported: set[int] | None = None,
    cumulative_unsupported: set[tuple[int, float]] | None = None,
    daily_sample_counts: dict[int, int] | None = None,
    cumulative_sample_counts: dict[tuple[int, float], int] | None = None,
    daily: pd.DataFrame | None = None,
    cumulative: pd.DataFrame | None = None,
    metadata: FitBCanonicalMetadata = FROZEN_FIT_B_METADATA,
) -> SyntheticFitBQuantileFixture:
    return SyntheticFitBQuantileFixture(
        _daily_table(
            unsupported_horizons=daily_unsupported,
            sample_counts=daily_sample_counts,
        )
        if daily is None
        else daily,
        _cumulative_table(
            unsupported_keys=cumulative_unsupported,
            sample_counts=cumulative_sample_counts,
        )
        if cumulative is None
        else cumulative,
        fixture_id="synthetic://phase13/fit-b-quantiles-golden-v1",
        transport=FitBTransportMetadata(
            selected_model_id=raw.model_name,
            recipe_identity=raw.recipe_identity,
            feature_schema_identity=raw.feature_schema_identity,
        ),
        calibration_metadata=metadata,
    )


def _anchor_collection(
    origin: date = ORIGIN_1,
    *,
    means: dict[int, float] | None = None,
    unavailable: dict[int, str] | None = None,
    missing: set[int] | None = None,
) -> SyntheticHistoricalMeanAnchorCollection:
    means = {store: 100.0 for store in STORES} if means is None else means
    unavailable = {} if unavailable is None else unavailable
    missing = set() if missing is None else missing
    provenance = SourceProvenance(
        source_id="phase13.synthetic.mean-anchor",
        version="fixture-v1",
        provenance="Artificial per-Store origin-bound mean anchor.",
        availability_assumption=AvailabilityAssumption.SYNTHETIC_RULE,
    )
    anchors = tuple(
        SyntheticHistoricalMeanAnchor(
            store_id=store,
            forecast_origin=origin,
            identity=f"synthetic://phase13/mean-anchor/store-{store}/{origin.isoformat()}",
            provenance=provenance,
            available=store not in unavailable,
            mean_open_sales_value=(None if store in unavailable else means[store]),
            unavailable_reason=unavailable.get(store),
        )
        for store in STORES
        if store not in missing
    )
    return SyntheticHistoricalMeanAnchorCollection(
        origin=origin,
        store_ids=STORES,
        anchors=anchors,
    )


def _issue(
    origin: date = ORIGIN_1,
    *,
    unknown: set[tuple[int, int]] | None = None,
    unavailable: set[tuple[int, int]] | None = None,
    fixture: SyntheticFitBQuantileFixture | None = None,
) -> tuple[RawForecastIssuance, SyntheticPlannedOpen, SyntheticFitBQuantileFixture, object]:
    raw = _raw_issuance(origin, unavailable=unavailable)
    schedule = _planned_open(origin, unknown=unknown)
    quantiles = fixture or _fixture(raw)
    result = Phase13M3Adapter().issue(raw, schedule, quantiles)
    return raw, schedule, quantiles, result


@pytest.mark.parametrize("origin", SUPPORTED_ORIGINS)
def test_exact_two_origin_m2_linkage_and_h14_ordering(origin: date) -> None:
    raw, _schedule, _fixture_value, result = _issue(origin)
    frame = result.to_frame()
    expected_dates = tuple(origin + timedelta(days=lead) for lead in range(1, 15))
    assert result.origin == origin
    assert tuple(frame["Date"].drop_duplicates().dt.date) == expected_dates
    assert tuple(frame["horizon"].drop_duplicates()) == tuple(range(1, 15))
    assert len(frame) == raw.requested_key_count == len(STORES) * HORIZON
    assert frame[["Store", "Date"]].equals(raw.to_frame()[["Store", "Date"]])
    assert frame["fit_identity"].eq(raw.fit_identity).all()
    assert result.fresh_model_fit_identity == raw.fit_identity


def test_preserves_every_raw_forecast_status_and_m2_identity() -> None:
    raw = _raw_issuance(unavailable={(2, 4)})
    schedule = _planned_open()
    quantiles = _fixture(raw)
    before = raw.to_frame()
    result = Phase13M3Adapter().issue(raw, schedule, quantiles)
    output = result.to_frame()
    for column in (
        "raw_forecast",
        "forecast_available",
        "unavailable_reason",
        "unclipped_forecast",
        "recursive_state_value",
        "forecast_was_clipped",
        "model_identity",
        "fit_identity",
        "recipe_identity",
        "feature_schema_identity",
        "requested_grid_identity",
        "training_input_identity",
        "recursive_history_identity",
        "future_covariate_identity",
    ):
        assert_series_equal(output[column], before[column], check_names=False)
    assert_frame_equal(raw.to_frame(), before)
    assert result.input_identities == raw.input_identities


def test_sunday_closure_routes_zero_without_changing_raw_point_or_interval() -> None:
    raw, _schedule, _fixture_value, result = _issue()
    frame = result.to_frame()
    sunday = frame.loc[frame["Date"].eq(pd.Timestamp("2015-07-05"))].iloc[0]
    assert not sunday["planned_open"]
    assert sunday["raw_forecast"] == 120.0
    assert sunday["operational_forecast"] == 0.0
    assert bool(sunday["closure_routing_applied"])
    assert sunday["raw_interval_lower"] == 105.0
    assert sunday["raw_interval_upper"] == 125.0
    assert sunday["operational_interval_lower"] == 0.0
    assert sunday["operational_interval_upper"] == 0.0
    assert bool(sunday["operational_interval_closure_routed"])
    raw_rows = raw.to_frame()
    assert (
        raw_rows.loc[
            raw_rows["Date"].eq(pd.Timestamp("2015-07-05")) & raw_rows["Store"].eq(1),
            "raw_forecast",
        ]
        .eq(120.0)
        .all()
    )


def test_unknown_planned_open_stays_unavailable_and_does_not_route_as_closed() -> None:
    raw, _schedule, _fixture_value, result = _issue(unknown={(1, 1)})
    row = result.to_frame().loc[lambda frame: frame["Store"].eq(1) & frame["horizon"].eq(1)].iloc[0]
    assert pd.isna(row["planned_open"])
    assert not bool(row["operational_forecast_available"])
    assert row["operational_forecast"] is None or pd.isna(row["operational_forecast"])
    assert row["operational_unavailable_reason"] == "planned_open_unknown"
    assert not bool(row["closure_routing_applied"])
    assert not bool(row["operational_interval_available"])
    assert row["operational_interval_unavailable_reason"] == "planned_open_unknown"


def test_outcome_fields_are_rejected_at_typed_input_boundary() -> None:
    raw = _raw_issuance()
    frame = _planned_open().to_frame().assign(Customers=1)
    provenance = SourceProvenance(
        source_id="phase13.synthetic.bad-schedule",
        version="fixture-v1",
        provenance="Artificial bad-schema test.",
        availability_assumption=AvailabilityAssumption.SYNTHETIC_RULE,
    )
    grid = RequestedForecastGrid(ORIGIN_1, store_ids=STORES)
    with pytest.raises(Phase13InputError, match="fields/order"):
        SyntheticPlannedOpen(frame, grid=grid, provenance=provenance)
    forged_raw = raw.to_frame().assign(Sales=1.0)
    with pytest.raises(Phase13IssuanceError, match="forbidden outcome fields"):
        replace(raw, _records=forged_raw)


def test_daily_signed_quantiles_clip_lower_endpoint_and_keep_raw_separate() -> None:
    _raw, _schedule, _fixture_value, result = _issue()
    row = (
        result.daily_intervals_to_frame()
        .loc[lambda frame: frame["Store"].eq(1) & frame["horizon"].eq(1)]
        .iloc[0]
    )
    assert row["q_low_signed"] == -20.0
    assert row["q_high_signed"] == -15.0
    assert row["raw_interval_pre_lower"] == -10.0
    assert row["raw_interval_pre_upper"] == -5.0
    assert bool(row["raw_interval_lower_clipped"])
    assert bool(row["raw_interval_upper_clipped"])
    assert row["raw_interval_lower"] == row["raw_interval_upper"] == 0.0
    assert row["raw_interval_width"] == 0.0
    assert row["operational_interval_lower"] == 0.0


def test_daily_interval_does_not_force_point_containment() -> None:
    _raw, _schedule, _fixture_value, result = _issue()
    row = (
        result.daily_intervals_to_frame()
        .loc[lambda frame: frame["Store"].eq(1) & frame["horizon"].eq(1)]
        .iloc[0]
    )
    assert row["raw_forecast"] == 10.0
    assert row["raw_interval_upper"] == 0.0
    assert not row["raw_interval_lower"] <= row["raw_forecast"] <= row["raw_interval_upper"]


def test_daily_sample_floor_rank_and_saved_unavailable_reason_are_preserved() -> None:
    raw = _raw_issuance()
    fixture = _fixture(raw, daily_sample_counts={3: 39})
    result = Phase13M3Adapter().issue(raw, _planned_open(), fixture)
    row = result.daily_intervals_to_frame().loc[lambda frame: frame["horizon"].eq(3)].iloc[0]
    assert row["daily_lower_n"] == 39
    assert row["daily_lower_rank_1_indexed"] == 1
    assert not bool(row["daily_lower_available"])
    assert row["daily_lower_unavailable_reason"] == "insufficient_calibration"
    assert not bool(row["raw_interval_available"])
    assert row["raw_interval_unavailable_reason"] == (
        "daily_lower_quantile_unavailable:insufficient_calibration"
    )


def test_exact_cumulative_prefix_and_probability_lookup_uses_saved_signed_q() -> None:
    _raw, _schedule, _fixture_value, result = _issue()
    prefixes = result.prefixes_to_frame()
    row = prefixes.loc[prefixes["Store"].eq(1) & prefixes["k"].eq(3) & prefixes["p"].eq(0.95)].iloc[
        0
    ]
    assert row["cumulative_signed_quantile"] == 6.0
    assert row["cumulative_quantile_n"] == 100
    assert row["cumulative_quantile_rank_1_indexed"] == 96
    assert row["operational_cumulative_forecast"] == 140.0
    assert row["upper_turnover"] == 146.0
    assert row["safety_stock"] == 6.0
    assert row["target"] == 146.0
    assert bool(row["available"])


def test_negative_and_positive_cumulative_quantiles_remain_distinguishable() -> None:
    _raw, _schedule, _fixture_value, result = _issue()
    prefixes = result.prefixes_to_frame()
    negative = prefixes.loc[
        prefixes["Store"].eq(1) & prefixes["k"].eq(3) & prefixes["p"].eq(0.90)
    ].iloc[0]
    positive = prefixes.loc[
        prefixes["Store"].eq(1) & prefixes["k"].eq(3) & prefixes["p"].eq(0.95)
    ].iloc[0]
    assert negative["cumulative_signed_quantile"] == -15.0
    assert negative["target"] == negative["operational_cumulative_forecast"]
    assert negative["safety_stock"] == 0.0
    assert positive["cumulative_signed_quantile"] == 6.0
    assert positive["target"] > positive["operational_cumulative_forecast"]


def test_incomplete_operational_prefix_invalidates_only_dependent_prefixes() -> None:
    _raw, _schedule, _fixture_value, result = _issue(unavailable={(1, 4)})
    prefixes = result.prefixes_to_frame()
    store = prefixes.loc[prefixes["Store"].eq(1)]
    assert store.loc[store["k"].eq(3), "available"].all()
    assert not store.loc[store["k"].ge(4), "available"].any()
    assert (
        store.loc[store["k"].eq(4), "unavailable_reason"]
        .eq(
            "operational_forecast_unavailable_at_h4:raw_forecast_unavailable:"
            "missing_required_covariate:promo"
        )
        .all()
    )
    assert prefixes.loc[prefixes["Store"].eq(2) & prefixes["k"].eq(14), "available"].all()


def test_explicit_unsupported_cumulative_reason_propagates_without_hiding_q() -> None:
    raw = _raw_issuance()
    fixture = _fixture(raw, cumulative_unsupported={(3, 0.95)})
    result = Phase13M3Adapter().issue(raw, _planned_open(), fixture)
    prefixes = result.prefixes_to_frame()
    row = prefixes.loc[prefixes["Store"].eq(1) & prefixes["k"].eq(3) & prefixes["p"].eq(0.95)].iloc[
        0
    ]
    assert bool(row["complete_operational_prefix"])
    assert not bool(row["quantile_available"])
    assert pd.isna(row["cumulative_signed_quantile"])
    assert row["quantile_unavailable_reason"] == "insufficient_calibration"
    assert row["unavailable_reason"] == "insufficient_calibration"


def test_unsupported_horizon_and_prefix_are_not_borrowed_from_neighbors() -> None:
    raw = _raw_issuance()
    fixture = _fixture(
        raw,
        daily_unsupported={3},
        cumulative_unsupported={(3, 0.95)},
    )
    result = Phase13M3Adapter().issue(raw, _planned_open(), fixture)
    intervals = result.daily_intervals_to_frame()
    assert not intervals.loc[intervals["horizon"].eq(3), "raw_interval_available"].any()
    assert intervals.loc[intervals["horizon"].eq(4), "raw_interval_available"].all()
    prefixes = result.prefixes_to_frame()
    assert not prefixes.loc[prefixes["k"].eq(3), "available"].any()
    assert prefixes.loc[prefixes["k"].eq(4) & prefixes["p"].eq(0.95), "available"].all()


def test_adapter_never_invokes_phase8_quantile_fitting_api(monkeypatch) -> None:
    def forbidden(*_args, **_kwargs):
        pytest.fail("M3 attempted to calculate calibration quantiles.")

    monkeypatch.setattr(uncertainty_module, "_build_quantile_tables", forbidden)
    monkeypatch.setattr(uncertainty_module, "calculate_uncertainty", forbidden)
    _raw, _schedule, _fixture_value, result = _issue()
    assert result.prefixes_to_frame()["available"].all()


def test_historical_calibration_identity_stays_separate_from_july_fit_identity() -> None:
    raw, _schedule, _fixture_value, result = _issue()
    records = result.daily_intervals_to_frame()
    assert result.calibration_metadata.calibration_fit_id == FIT_B_ID
    assert records["calibration_fit_identity"].eq(FIT_B_ID).all()
    assert records["fresh_model_fit_identity"].eq(raw.fit_identity).all()
    assert raw.fit_identity != FIT_B_ID
    assert result.transport_status == "unvalidated_june_fit_b_to_july_assumption"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selected_model_id", "other_model"),
        ("recipe_identity", "0" * 64),
        ("feature_schema_identity", "1" * 64),
        ("daily_error_population", "wrong_daily_population"),
        ("cumulative_error_population", "wrong_cumulative_population"),
        ("prefix_definition", "h2_through_k"),
        ("historical_schedule_assumption", "actual_open"),
        ("application_schedule_rule_id", "wrong_schedule"),
        ("transport_status", "validated"),
    ],
)
def test_incompatible_transport_metadata_fails_before_adapter_calculations(
    monkeypatch, field: str, value: str
) -> None:
    raw = _raw_issuance()
    good = _fixture(raw)
    bad_transport = replace(good.transport, **{field: value})
    bad = SyntheticFitBQuantileFixture(
        good.daily_to_frame(),
        good.cumulative_to_frame(),
        fixture_id=good.fixture_id,
        transport=bad_transport,
    )
    monkeypatch.setattr(
        "rossmann_forecasting.phase13.adapters._raw_interval",
        lambda *_args, **_kwargs: pytest.fail("Calculation preceded transport validation."),
    )
    with pytest.raises(Phase13AdapterError, match="transport compatibility mismatch"):
        Phase13M3Adapter().issue(raw, _planned_open(), bad)


@pytest.mark.parametrize(
    ("field", "new_value", "message"),
    [
        ("origin", date(2015, 7, 4), "origin"),
        ("model_name", "other_model", "model identity"),
        ("grid_identity", "2" * 64, "grid"),
        ("recipe_identity", "3" * 64, "recipe identity"),
        ("feature_schema_identity", "4" * 64, "feature schema"),
    ],
)
def test_mismatched_m2_model_origin_grid_recipe_and_schema_fail_closed(
    field: str, new_value: object, message: str
) -> None:
    raw = _raw_issuance()
    forged = replace(raw, **{field: new_value})
    with pytest.raises(Phase13AdapterError, match=message):
        Phase13M3Adapter().issue(forged, _planned_open(), _fixture(raw))


def test_m2_provenance_mismatch_and_schedule_grid_mismatch_fail_closed() -> None:
    raw = _raw_issuance()
    identities = tuple(
        (role, _sha("forged-training")) if role == "training" else (role, value)
        for role, value in raw.input_identities
    )
    forged = replace(raw, input_identities=identities)
    with pytest.raises(Phase13AdapterError, match="provenance"):
        Phase13M3Adapter().issue(forged, _planned_open(), _fixture(raw))

    wrong_schedule = _planned_open(ORIGIN_2)
    with pytest.raises(Phase13AdapterError, match="Planned-Open grid"):
        Phase13M3Adapter().issue(raw, wrong_schedule, _fixture(raw))


def test_m2_record_provenance_mismatch_is_rejected_before_interval_work(monkeypatch) -> None:
    raw = _raw_issuance()
    records = raw.to_frame()
    records.loc[0, "recursive_history_identity"] = _sha("wrong-history")
    forged = replace(raw, _records=records)
    monkeypatch.setattr(
        "rossmann_forecasting.phase13.adapters._raw_interval",
        lambda *_args, **_kwargs: pytest.fail("Interval work followed invalid provenance."),
    )
    with pytest.raises(Phase13AdapterError, match="row recursive_history_identity"):
        Phase13M3Adapter().issue(forged, _planned_open(), _fixture(raw))


def test_fixture_hash_verification_detects_table_content_tampering() -> None:
    raw = _raw_issuance()
    fixture = _fixture(raw)
    original_daily_hash = fixture.daily_fixture_sha256
    tampered_daily = fixture.daily_to_frame()
    tampered_daily.loc[
        tampered_daily["horizon"].eq(4) & tampered_daily["tail"].eq("upper"), "signed_quantile"
    ] = 9876.5
    with pytest.raises(Phase13AdapterError, match="daily fixture SHA-256"):
        SyntheticFitBQuantileFixture(
            tampered_daily,
            fixture.cumulative_to_frame(),
            fixture_id=fixture.fixture_id,
            transport=fixture.transport,
            expected_daily_fixture_sha256=original_daily_hash,
        )


def test_fixture_snapshots_are_defensive_and_not_canonical_claims() -> None:
    raw = _raw_issuance()
    fixture = _fixture(raw)
    daily = fixture.daily_to_frame()
    daily.loc[0, "signed_quantile"] = 999.0
    assert fixture.daily_to_frame().loc[0, "signed_quantile"] != 999.0
    assert fixture.content_classification == "synthetic_fixture_content_only"
    assert fixture.daily_fixture_sha256 != fixture.calibration_metadata.daily_table_sha256
    with pytest.raises(Phase13AdapterError, match="Pinned historical"):
        _fixture(
            raw,
            metadata=replace(
                FROZEN_FIT_B_METADATA,
                daily_table_sha256=fixture.daily_fixture_sha256,
            ),
        )
    with pytest.raises(Phase13AdapterError, match="daily fixture SHA-256"):
        SyntheticFitBQuantileFixture(
            fixture.daily_to_frame(),
            fixture.cumulative_to_frame(),
            fixture_id=fixture.fixture_id,
            transport=fixture.transport,
            expected_daily_fixture_sha256=FROZEN_FIT_B_METADATA.daily_table_sha256,
        )


def test_canonical_fit_b_loader_fails_closed_without_access() -> None:
    with pytest.raises(Phase13AdapterError, match="separate authorization and hash verification"):
        load_canonical_fit_b_quantiles("canonical path is not an input")


def test_exact_quantile_keys_duplicates_probabilities_and_ranks_are_validated() -> None:
    raw = _raw_issuance()
    good = _fixture(raw)
    duplicate = pd.concat(
        [good.daily_to_frame(), good.daily_to_frame().iloc[[0]]], ignore_index=True
    )
    with pytest.raises(Phase13AdapterError, match="duplicate exact keys"):
        SyntheticFitBQuantileFixture(
            duplicate,
            good.cumulative_to_frame(),
            fixture_id=good.fixture_id,
            transport=good.transport,
        )
    bad_rank = good.cumulative_to_frame()
    mask = bad_rank["k"].eq(2) & bad_rank["p"].eq(0.95)
    bad_rank.loc[mask, "rank_1_indexed"] += 1
    with pytest.raises(Phase13AdapterError, match="saved rank"):
        SyntheticFitBQuantileFixture(
            good.daily_to_frame(),
            bad_rank,
            fixture_id=good.fixture_id,
            transport=good.transport,
        )


def test_daily_fixture_rejects_different_sample_counts_between_tails() -> None:
    raw = _raw_issuance()
    good = _fixture(raw)
    daily = good.daily_to_frame()
    mask = daily["horizon"].eq(3) & daily["tail"].eq("upper")
    daily.loc[mask, "n"] = 101
    daily.loc[mask, "rank_1_indexed"] = _daily_rank(101, "upper")
    with pytest.raises(Phase13AdapterError, match="tails must share the same calibration sample"):
        SyntheticFitBQuantileFixture(
            daily,
            good.cumulative_to_frame(),
            fixture_id=good.fixture_id,
            transport=good.transport,
        )


def test_cumulative_fixture_rejects_different_sample_counts_between_probabilities() -> None:
    raw = _raw_issuance()
    good = _fixture(raw)
    cumulative = good.cumulative_to_frame()
    mask = cumulative["k"].eq(4) & cumulative["p"].eq(0.95)
    cumulative.loc[mask, "n"] = 101
    cumulative.loc[mask, "rank_1_indexed"] = _upper_rank(101, 0.95)
    with pytest.raises(Phase13AdapterError, match="must share the same complete-sample count"):
        SyntheticFitBQuantileFixture(
            good.daily_to_frame(),
            cumulative,
            fixture_id=good.fixture_id,
            transport=good.transport,
        )


def test_one_probability_can_keep_saved_nonfinite_reason_with_common_prefix_count() -> None:
    raw = _raw_issuance()
    good = _fixture(raw)
    cumulative = good.cumulative_to_frame()
    mask = cumulative["k"].eq(3) & cumulative["p"].eq(0.95)
    cumulative.loc[mask, "signed_quantile"] = None
    cumulative.loc[mask, "available"] = False
    cumulative.loc[mask, "unavailable_reason"] = "nonfinite_quantile"
    fixture = _fixture(raw, cumulative=cumulative)
    result = Phase13M3Adapter().issue(raw, _planned_open(), fixture)
    prefix = (
        result.prefixes_to_frame()
        .loc[lambda frame: frame["Store"].eq(1) & frame["k"].eq(3)]
        .set_index("p")
    )
    assert prefix["cumulative_quantile_n"].nunique() == 1
    assert bool(prefix.loc[0.90, "quantile_available"])
    assert not bool(prefix.loc[0.95, "quantile_available"])
    assert prefix.loc[0.95, "quantile_unavailable_reason"] == "nonfinite_quantile"
    assert bool(prefix.loc[0.98, "quantile_available"])


def test_below_floor_cumulative_prefix_marks_all_probabilities_unavailable() -> None:
    fixture = _fixture(_raw_issuance(), cumulative_unsupported={(3, 0.95)})
    rows = fixture.cumulative_to_frame().loc[lambda frame: frame["k"].eq(3)]
    assert rows["n"].eq(49).all()
    assert not rows["available"].any()
    assert rows["unavailable_reason"].eq("insufficient_calibration").all()
    assert rows["rank_1_indexed"].tolist() == [
        _upper_rank(49, probability) for probability in CUMULATIVE_LEVELS
    ]


def test_baseline_and_forecast_targets_match_phase10_equations() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    anchors = _anchor_collection(issuance.origin)
    targets = issuance.build_standing_targets(anchors).to_frame()
    key = (
        targets["Store"].eq(1) & targets["lead_time"].eq(2) & targets["buffer_probability"].eq(0.95)
    )
    baseline = targets.loc[key & targets["policy_id"].eq(POLICY_IDS[0])].iloc[0]
    forecast = targets.loc[key & targets["policy_id"].eq(POLICY_IDS[1])].iloc[0]
    assert baseline["protection_period"] == 3
    assert baseline["open_days_in_protection_period"] == 2
    assert baseline["target_value"] == 100.0 * 2
    assert forecast["forecast_protection_demand_value"] == 140.0
    assert forecast["cumulative_signed_quantile"] == 6.0
    assert forecast["upper_turnover_value"] == 146.0
    assert forecast["safety_stock_value"] == 6.0
    assert forecast["target_value"] == 146.0
    assert baseline["target_available"] and forecast["target_available"]
    assert baseline["input_semantics"] == SYNTHETIC_TARGET_SEMANTICS
    assert not forecast["calibration_transport_valid"]


def test_store_bound_anchor_golden_targets_and_provenance_are_distinct() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    anchors = _anchor_collection(issuance.origin, means={1: 100.0, 2: 500.0})
    targets = issuance.build_standing_targets(anchors)
    frame = targets.to_frame()
    baseline = frame.loc[
        frame["lead_time"].eq(2)
        & frame["buffer_probability"].eq(0.95)
        & frame["policy_id"].eq(POLICY_IDS[0])
    ].set_index("Store")
    assert baseline.loc[1, "open_days_in_protection_period"] == 2
    assert baseline.loc[2, "open_days_in_protection_period"] == 2
    assert baseline.loc[1, "target_value"] == 200.0
    assert baseline.loc[2, "target_value"] == 1000.0
    assert baseline.loc[1, "anchor_identity"] != baseline.loc[2, "anchor_identity"]
    assert baseline.loc[1, "anchor_source_id"] == baseline.loc[2, "anchor_source_id"]
    assert baseline.loc[1, "anchor_collection_identity"] == anchors.identity
    assert targets.anchor_collection_identity == anchors.identity


def test_store_specific_anchor_availability_zero_and_missing_key_do_not_borrow() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    unavailable = _anchor_collection(
        issuance.origin, means={1: 0.0, 2: 500.0}, unavailable={1: "store_1_anchor_unavailable"}
    )
    unavailable_frame = issuance.build_standing_targets(unavailable).to_frame()
    baseline = unavailable_frame.loc[
        unavailable_frame["lead_time"].eq(2)
        & unavailable_frame["buffer_probability"].eq(0.95)
        & unavailable_frame["policy_id"].eq(POLICY_IDS[0])
    ].set_index("Store")
    assert not baseline.loc[1, "target_available"]
    assert baseline.loc[1, "availability_reason"] == "store_1_anchor_unavailable"
    assert pd.isna(baseline.loc[1, "target_value"])
    assert baseline.loc[2, "target_available"]
    assert baseline.loc[2, "target_value"] == 1000.0

    zero_and_positive = _anchor_collection(issuance.origin, means={1: 0.0, 2: 500.0})
    zero_frame = issuance.build_standing_targets(zero_and_positive).to_frame()
    zero_baseline = zero_frame.loc[
        zero_frame["lead_time"].eq(2)
        & zero_frame["buffer_probability"].eq(0.95)
        & zero_frame["policy_id"].eq(POLICY_IDS[0])
    ].set_index("Store")
    assert zero_baseline["target_available"].all()
    assert zero_baseline.loc[1, "target_value"] == 0.0
    assert zero_baseline.loc[2, "target_value"] == 1000.0

    missing = _anchor_collection(issuance.origin, means={1: 0.0, 2: 500.0}, missing={1})
    missing_frame = issuance.build_standing_targets(missing).to_frame()
    missing_baseline = missing_frame.loc[
        missing_frame["lead_time"].eq(2)
        & missing_frame["buffer_probability"].eq(0.95)
        & missing_frame["policy_id"].eq(POLICY_IDS[0])
    ].set_index("Store")
    assert not missing_baseline.loc[1, "target_available"]
    assert missing_baseline.loc[1, "availability_reason"] == "anchor_missing"
    assert pd.isna(missing_baseline.loc[1, "target_value"])
    assert pd.isna(missing_baseline.loc[1, "anchor_identity"])
    assert missing_baseline.loc[2, "target_value"] == 1000.0


def test_anchor_collection_rejects_duplicate_and_cross_origin_keys() -> None:
    valid = _anchor_collection()
    with pytest.raises(Phase13AdapterError, match="duplicate Store/origin keys"):
        SyntheticHistoricalMeanAnchorCollection(
            origin=ORIGIN_1,
            store_ids=STORES,
            anchors=(*valid.anchors, valid.anchors[0]),
        )
    other_origin_anchor = _anchor_collection(ORIGIN_2).anchors[0]
    with pytest.raises(Phase13AdapterError, match="cross-origin anchor"):
        SyntheticHistoricalMeanAnchorCollection(
            origin=ORIGIN_1,
            store_ids=STORES,
            anchors=(other_origin_anchor,),
        )


def test_target_builder_rejects_wrong_origin_and_store_universe() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    with pytest.raises(Phase13AdapterError, match="origin differs"):
        issuance.build_standing_targets(_anchor_collection(ORIGIN_2))
    smaller_roster = SyntheticHistoricalMeanAnchorCollection(
        origin=issuance.origin,
        store_ids=(1,),
        anchors=(_anchor_collection(issuance.origin).anchors[0],),
    )
    with pytest.raises(Phase13AdapterError, match="Store universe differs"):
        issuance.build_standing_targets(smaller_roster)


def test_all_approved_lead_times_probabilities_and_paired_policy_rows_are_present() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    anchors = _anchor_collection(issuance.origin)
    targets = issuance.build_standing_targets(anchors).to_frame()
    assert set(targets["lead_time"]) == set(range(2, 8))
    assert set(targets["review_period"]) == {1}
    assert set(targets["protection_period"]) == set(range(3, 9))
    assert set(targets["buffer_probability"]) == set(CUMULATIVE_LEVELS)
    assert set(targets["policy_id"]) == set(POLICY_IDS)
    assert len(targets.loc[targets["Store"].eq(1)]) == 6 * 3 * 2
    for lead_time in (2, 7):
        protection = lead_time + 1
        p = 0.98 if lead_time == 7 else 0.90
        row = targets.loc[
            targets["Store"].eq(1)
            & targets["lead_time"].eq(lead_time)
            & targets["buffer_probability"].eq(p)
            & targets["policy_id"].eq(POLICY_IDS[1])
        ].iloc[0]
        expected_demand = float(
            issuance.to_frame()
            .loc[
                issuance.to_frame()["Store"].eq(1) & issuance.to_frame()["horizon"].le(protection),
                "operational_forecast",
            ]
            .sum()
        )
        expected_q = (4.0 if p == 0.98 else -5.0) * protection
        expected_upper = max(0.0, expected_demand + expected_q)
        assert row["protection_period"] == protection
        assert row["forecast_protection_demand_value"] == expected_demand
        assert row["cumulative_signed_quantile"] == expected_q
        assert row["upper_turnover_value"] == expected_upper
        assert row["safety_stock_value"] == max(0.0, expected_upper - expected_demand)
        assert row["target_value"] == max(expected_demand, expected_upper)


@pytest.mark.parametrize(
    "forgery",
    (
        "duplicate_keys",
        "missing_policy_rows",
        "wrong_origin",
        "negative_available_target",
        "null_available_target",
        "available_target_has_reason",
        "numeric_unavailable_target",
        "mismatched_identity",
    ),
)
def test_origin_frozen_target_constructor_rejects_forged_snapshots(forgery: str) -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    anchors = _anchor_collection(
        issuance.origin,
        unavailable={1: "store_1_anchor_unavailable"}
        if forgery == "numeric_unavailable_target"
        else {},
    )
    valid = issuance.build_standing_targets(anchors)
    records = valid.to_frame()

    if forgery == "duplicate_keys":
        records = pd.concat([records, records.iloc[[0]]], ignore_index=True)
    elif forgery == "missing_policy_rows":
        records = records.loc[
            ~(records["Store"].eq(1) & records["policy_id"].eq(POLICY_IDS[0]))
        ].copy()
    elif forgery == "wrong_origin":
        records["forecast_origin"] = ORIGIN_2
    elif forgery == "negative_available_target":
        index = records.index[records["target_available"]][0]
        records.loc[index, "target_value"] = -1.0
    elif forgery == "null_available_target":
        index = records.index[records["target_available"]][0]
        records.loc[index, "target_value"] = None
    elif forgery == "available_target_has_reason":
        index = records.index[records["target_available"]][0]
        records.loc[index, "availability_reason"] = "spurious_reason"
    elif forgery == "numeric_unavailable_target":
        index = records.index[~records["target_available"]][0]
        records.loc[index, "target_value"] = 0.0
    elif forgery == "mismatched_identity":
        records.loc[records.index[0], "issuance_identity"] = "0" * 64

    with pytest.raises(Phase13AdapterError):
        OriginFrozenStandingTargets(
            origin=valid.origin,
            store_ids=valid.store_ids,
            issuance_identity=valid.issuance_identity,
            anchor_collection_identity=valid.anchor_collection_identity,
            records=records,
        )


def test_origin_frozen_target_constructor_rejects_schema_and_outcome_fields() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    valid = issuance.build_standing_targets(_anchor_collection(issuance.origin))
    omitted = valid.to_frame().drop(columns=["policy_id"])
    with pytest.raises(Phase13AdapterError, match="typed schema"):
        OriginFrozenStandingTargets(
            origin=valid.origin,
            store_ids=valid.store_ids,
            issuance_identity=valid.issuance_identity,
            anchor_collection_identity=valid.anchor_collection_identity,
            records=omitted,
        )
    forbidden = valid.to_frame().assign(Sales=1.0)
    with pytest.raises(Phase13AdapterError, match="forbidden outcome fields"):
        OriginFrozenStandingTargets(
            origin=valid.origin,
            store_ids=valid.store_ids,
            issuance_identity=valid.issuance_identity,
            anchor_collection_identity=valid.anchor_collection_identity,
            records=forbidden,
        )


@pytest.mark.parametrize("identity_field", ("issuance_identity", "anchor_collection_identity"))
def test_origin_frozen_target_constructor_requires_sha256_identities(identity_field: str) -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    valid = issuance.build_standing_targets(_anchor_collection(issuance.origin))
    identities = {
        "issuance_identity": valid.issuance_identity,
        "anchor_collection_identity": valid.anchor_collection_identity,
    }
    identities[identity_field] = "invalid"
    with pytest.raises(Phase13AdapterError, match="must be SHA-256"):
        OriginFrozenStandingTargets(
            origin=valid.origin,
            store_ids=valid.store_ids,
            issuance_identity=identities["issuance_identity"],
            anchor_collection_identity=identities["anchor_collection_identity"],
            records=valid.to_frame(),
        )


def test_zero_historical_mean_anchor_is_available_zero_not_missing() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue()
    anchors = _anchor_collection(issuance.origin, means={1: 0.0, 2: 0.0})
    targets = issuance.build_standing_targets(anchors).to_frame()
    baseline = targets.loc[targets["policy_id"].eq(POLICY_IDS[0])]
    assert baseline["target_available"].all()
    assert baseline["target_value"].eq(0.0).all()
    assert baseline["availability_reason"].isna().all()


def test_anchor_and_forecast_prefix_availability_are_independent() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue(unavailable={(1, 4)})
    anchors = _anchor_collection(issuance.origin, unavailable={1: "synthetic_anchor_unavailable"})
    targets = issuance.build_standing_targets(anchors).to_frame()
    l2 = targets.loc[
        targets["Store"].eq(1) & targets["lead_time"].eq(2) & targets["buffer_probability"].eq(0.95)
    ]
    baseline = l2.loc[l2["policy_id"].eq(POLICY_IDS[0])].iloc[0]
    forecast = l2.loc[l2["policy_id"].eq(POLICY_IDS[1])].iloc[0]
    assert not baseline["target_available"]
    assert baseline["availability_reason"] == "synthetic_anchor_unavailable"
    assert forecast["target_available"]
    assert forecast["target_value"] == 146.0

    l3 = targets.loc[
        targets["Store"].eq(1) & targets["lead_time"].eq(3) & targets["buffer_probability"].eq(0.95)
    ]
    assert not l3.loc[l3["policy_id"].eq(POLICY_IDS[1]), "target_available"].any()


def test_no_baseline_or_point_only_fallback_when_exact_q_is_unavailable() -> None:
    raw = _raw_issuance()
    fixture = _fixture(raw, cumulative_unsupported={(3, 0.95)})
    result = Phase13M3Adapter().issue(raw, _planned_open(), fixture)
    anchors = _anchor_collection(result.origin)
    targets = result.build_standing_targets(anchors).to_frame()
    mask = (
        targets["Store"].eq(1) & targets["lead_time"].eq(2) & targets["buffer_probability"].eq(0.95)
    )
    baseline = targets.loc[mask & targets["policy_id"].eq(POLICY_IDS[0])].iloc[0]
    forecast = targets.loc[mask & targets["policy_id"].eq(POLICY_IDS[1])].iloc[0]
    assert baseline["target_available"]
    assert baseline["target_value"] == 200.0
    assert not forecast["target_available"]
    assert pd.isna(forecast["target_value"])
    assert forecast["availability_reason"] == "insufficient_calibration"


def test_unknown_schedule_prefix_keeps_target_unavailable_without_zero_fallback() -> None:
    _raw, _schedule, _fixture_value, issuance = _issue(unknown={(1, 3)})
    anchors = _anchor_collection(issuance.origin)
    targets = issuance.build_standing_targets(anchors).to_frame()
    subset = targets.loc[
        targets["Store"].eq(1) & targets["lead_time"].eq(2) & targets["buffer_probability"].eq(0.95)
    ]
    assert not subset["target_available"].any()
    assert subset["availability_reason"].eq("unknown_schedule_in_protection_prefix").all()
    assert subset["target_value"].isna().all()


def test_known_closure_routes_even_when_raw_forecast_is_unavailable() -> None:
    raw, _schedule, _fixture_value, result = _issue(unavailable={(1, 2)})
    row = result.to_frame().loc[lambda frame: frame["Store"].eq(1) & frame["horizon"].eq(2)].iloc[0]
    assert not bool(row["forecast_available"])
    assert pd.isna(row["raw_forecast"])
    assert not bool(row["raw_interval_available"])
    assert row["raw_interval_unavailable_reason"] == (
        "raw_forecast_unavailable:missing_required_covariate:promo"
    )
    assert bool(row["operational_forecast_available"])
    assert row["operational_forecast"] == 0.0
    assert bool(row["closure_routing_applied"])
    assert bool(row["operational_interval_available"])
    assert row["operational_interval_lower"] == row["operational_interval_upper"] == 0.0
    assert (
        raw.to_frame()
        .loc[raw.to_frame()["horizon"].eq(2) & raw.to_frame()["Store"].eq(1), "raw_forecast"]
        .isna()
        .all()
    )


def test_sparse_missing_schedule_row_remains_unknown() -> None:
    raw = _raw_issuance()
    schedule = _planned_open(omit={(1, 1)})
    result = Phase13M3Adapter().issue(raw, schedule, _fixture(raw))
    row = result.to_frame().loc[lambda frame: frame["Store"].eq(1) & frame["horizon"].eq(1)].iloc[0]
    assert pd.isna(row["planned_open"])
    assert row["operational_unavailable_reason"] == "planned_open_unknown"


def test_no_future_outcome_reader_is_invoked_by_m3(monkeypatch) -> None:
    from rossmann_forecasting.phase13.providers import SyntheticOutcomeProvider

    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("M3 queried a future outcome provider.")

    monkeypatch.setattr(SyntheticOutcomeProvider, "read_day", forbidden)
    _raw, _schedule, _fixture_value, result = _issue()
    assert result.to_frame().shape[0] == len(STORES) * HORIZON
    assert calls == []


def test_mutating_sealed_outcome_fixture_cannot_change_any_issued_output() -> None:
    raw = _raw_issuance()
    schedule = _planned_open()
    fixture = _fixture(raw)
    sealed_a = pd.DataFrame({"Sales": [1.0], "Customers": [2], "Open": [0]})
    first = Phase13M3Adapter().issue(raw, schedule, fixture)
    sealed_b = sealed_a.copy(deep=True)
    sealed_b.loc[0, ["Sales", "Customers", "Open"]] = [999999.0, 8000, 1]
    second = Phase13M3Adapter().issue(raw, schedule, fixture)
    assert not sealed_a.equals(sealed_b)
    assert_frame_equal(first.to_frame(), second.to_frame(), check_exact=True)
    assert_frame_equal(first.prefixes_to_frame(), second.prefixes_to_frame(), check_exact=True)


def test_each_origin_freezes_a_distinct_paired_target_set_without_daily_refresh() -> None:
    results = []
    targets_by_origin = []
    for origin in SUPPORTED_ORIGINS:
        raw, _schedule, _fixture_value, result = _issue(origin)
        anchors = _anchor_collection(origin)
        targets = result.build_standing_targets(anchors)
        frame = targets.to_frame()
        assert result.origin == origin
        assert targets.origin == origin
        assert frame["forecast_origin"].eq(origin).all()
        assert frame["model_fit_identity"].eq(raw.fit_identity).all()
        key = [
            "Store",
            "forecast_origin",
            "lead_time",
            "review_period",
            "protection_period",
            "buffer_probability",
            "policy_id",
        ]
        assert not frame.duplicated(key).any()
        assert "horizon" not in frame.columns
        saved_value = frame.iloc[0]["target_value"]
        returned = targets.to_frame()
        returned.loc[0, "target_value"] = -1.0
        assert targets.to_frame().iloc[0]["target_value"] == saved_value
        results.append(result)
        targets_by_origin.append(targets)
    assert results[0].origin != results[1].origin
    assert results[0].fresh_model_fit_identity != results[1].fresh_model_fit_identity
    assert targets_by_origin[0].issuance_identity != targets_by_origin[1].issuance_identity
