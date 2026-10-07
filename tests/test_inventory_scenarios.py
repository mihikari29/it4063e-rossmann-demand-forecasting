from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pytest

from rossmann_forecasting.features.contract import PREDICTOR_COLUMNS
from rossmann_forecasting.inventory import scenarios


def _history(
    store: int,
    origin: date,
    *,
    open_rows: int = 28,
    sales: int = 100,
    missing: set[int] | None = None,
    unknown: set[int] | None = None,
    closed_positive: bool = False,
) -> pd.DataFrame:
    missing = missing or set()
    unknown = unknown or set()
    start = origin - timedelta(days=55)
    rows = []
    for offset in range(56):
        if offset in missing:
            continue
        if offset in unknown:
            open_value = None
        else:
            open_value = 1 if offset < open_rows else 0
        value = sales if open_value == 1 else 0
        if closed_positive and open_value == 0 and offset == open_rows:
            value = 17
        rows.append(
            {
                "Store": store,
                "Date": start + timedelta(days=offset),
                "Sales": value,
                "Open": open_value,
            }
        )
    return pd.DataFrame(rows, columns=scenarios.HISTORY_COLUMNS)


def _histories(stores: tuple[int, ...] = (1, 2, 3, 4)) -> dict[date, pd.DataFrame]:
    result = {}
    for origin in scenarios.ALLOWED_ORIGINS:
        pieces = [
            _history(1, origin, open_rows=28, sales=100, unknown={55}, closed_positive=True),
            _history(2, origin, open_rows=28, sales=0),
            _history(3, origin, open_rows=27, sales=25, missing={40}),
        ]
        frame = pd.concat(pieces, ignore_index=True)
        result[origin] = frame.loc[frame["Store"].isin(stores)].reset_index(drop=True)
    return result


@pytest.fixture(scope="module")
def small_bundle():
    config = scenarios.default_config(stores=[1, 2, 3, 4])
    tables = scenarios.generate_scenario_tables(config, _histories())
    return config, tables


def _find_row(table: pa.Table, **criteria):
    matches = [
        row
        for row in table.to_pylist()
        if all(row[name] == value for name, value in criteria.items())
    ]
    assert len(matches) == 1
    return matches[0]


def test_exact_open_history_threshold_and_hand_computed_anchor():
    origin = scenarios.ALLOWED_ORIGINS[0]
    frame_28 = _history(1, origin, open_rows=28, sales=100)
    anchor_28 = scenarios.compute_origin_anchors(frame_28, origin=origin, stores=[1]).to_pylist()[0]
    assert anchor_28["open_rows"] == 28
    assert anchor_28["mean_open_sales_value"] == 100
    frame_27 = _history(1, origin, open_rows=27, sales=100)
    anchor_27 = scenarios.compute_origin_anchors(frame_27, origin=origin, stores=[1]).to_pylist()[0]
    assert anchor_27["open_rows"] == 27
    assert anchor_27["anchor_available"] is False
    assert anchor_27["mean_open_sales_value"] is None
    assert anchor_27["unavailable_reason"] == "insufficient_open_history"
    assert scenarios.initial_stock_on_hand_value(100, 5) == 500
    assert scenarios.initial_stock_on_hand_value(None, 5) is None


def test_cost_formulas_and_display_conversion_are_monetary_only():
    assert scenarios.holding_cost_rate(0.70, 0.20) == pytest.approx(0.14 / 365)
    assert scenarios.stockout_penalty(0.70, 0.50) == pytest.approx(0.80)
    assert scenarios.holding_cost_rate(0.70, 0.20) * 100 == pytest.approx(14 / 365)
    assert 100 / 10 == 10  # Display-only equivalent units do not change the V-to-K formulas.


def test_hand_computed_synthetic_demand_and_missingness_precedence():
    value, reason = scenarios.synthetic_demand_value(
        100,
        1,
        weekday_factor=1,
        trend_factor=1,
        promotion_factor=1.2,
        noise_factor=1,
        demand_stress_factor=2,
    )
    assert value == 240
    assert reason is None
    assert scenarios.synthetic_demand_value(
        100,
        0,
        weekday_factor=1,
        trend_factor=1,
        promotion_factor=1,
        noise_factor=1,
        demand_stress_factor=1,
    ) == (0.0, None)
    assert scenarios.synthetic_demand_value(
        100,
        None,
        weekday_factor=1,
        trend_factor=1,
        promotion_factor=1,
        noise_factor=1,
        demand_stress_factor=1,
    ) == (None, "unknown_scenario_open")
    assert scenarios.synthetic_demand_value(
        None,
        0,
        weekday_factor=1,
        trend_factor=1,
        promotion_factor=1,
        noise_factor=1,
        demand_stress_factor=1,
        anchor_available=False,
        unavailable_reason="insufficient_open_history",
    ) == (None, "insufficient_open_history")


def test_sha256_golden_vectors_and_rejection_sampling(monkeypatch):
    expected_key = [
        "phase-9-synthetic-v1",
        4209,
        0,
        "2015-06-05",
        ["store", 1],
        "SupplierLeadTime",
        0,
    ]
    independently_encoded = json.dumps(
        expected_key, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    independent_digest = hashlib.sha256(independently_encoded).digest()
    assert independent_digest.hex() == (
        "374910b69500887ad251efb8c810c88031a21948820847c170e227d7957ca513"
    )
    assert scenarios.keyed_digest(0, "2015-06-05", ["store", 1], "SupplierLeadTime").hex() == (
        "374910b69500887ad251efb8c810c88031a21948820847c170e227d7957ca513"
    )
    assert scenarios.keyed_uniform(0, "2015-06-05", ["store", 1], "SupplierLeadTime").hex() == (
        "0x1.ba4885b4a8044p-3"
    )
    assert (
        scenarios.keyed_discrete(0, "2015-06-05", ["store", 1], "SupplierLeadTime", range(2, 8))
        == 6
    )
    assert (
        scenarios.keyed_digest(4, "2015-06-19", ["date", "2015-06-22"], "CommonShock").hex()
        == "0d7670f306e059c41b37f881a3e3a95a66ade7b5db1847bb8f483c72f1f59aec"
    )
    assert (
        scenarios.keyed_digest(
            2, "2015-06-05", ["store_date", 42, "2015-06-10"], "StoreDateNoise"
        ).hex()
        == "205207d499de77e2a6208c3d2874e908583807078cc81bd5ee40ac61ed0a2b17"
    )

    counters = []

    def rejection_draw(replicate, origin, scope, role, counter=0):
        counters.append(counter)
        integer = (2**64 - 1) if counter == 0 else 5
        return integer.to_bytes(8, "big") + bytes(24)

    monkeypatch.setattr(scenarios, "keyed_digest", rejection_draw)
    assert (
        scenarios.keyed_discrete(0, "2015-06-05", ["store", 1], "SupplierLeadTime", [10, 20, 30])
        == 30
    )
    assert counters == [0, 1]

    monkeypatch.setattr(scenarios, "keyed_digest", lambda *args, **kwargs: bytes.fromhex("ff" * 32))
    with pytest.raises(scenarios.ScenarioIntegrityError, match="100 attempts"):
        scenarios.keyed_discrete(0, "2015-06-05", ["store", 1], "SupplierLeadTime", [1, 2, 3])


def test_history_validation_preserves_missing_dates_unknown_open_and_closed_sales():
    origin = scenarios.ALLOWED_ORIGINS[0]
    frame = _history(
        1, origin, open_rows=28, sales=100, unknown={55}, missing={40}, closed_positive=True
    )
    anchor = scenarios.compute_origin_anchors(frame, origin=origin, stores=[1]).to_pylist()[0]
    assert anchor["observed_rows"] == 55
    assert anchor["missing_calendar_days"] == 1
    assert anchor["open_rows"] == 28
    assert anchor["closed_rows"] == 26
    assert anchor["unknown_open_rows"] == 1
    assert anchor["closed_positive_sales_rows"] == 1
    assert anchor["anchor_available"] is True
    assert len(frame) == 55  # No absent calendar record was filled.


def test_scenario_generation_retains_cold_start_zero_and_historical_reference(small_bundle):
    config, tables = small_bundle
    validation = scenarios.validate_scenario_tables(tables, config)
    assert validation["status"] == "passed"
    assert validation["actual_counts"] == {
        "scenario_catalog.parquet": 82,
        "origin_anchors.parquet": 8,
        "store_parameters.parquet": 328,
        "scenario_daily.parquet": 4592,
    }
    anchor = _find_row(
        tables["origin_anchors.parquet"], Store=1, forecast_origin=scenarios.ALLOWED_ORIGINS[0]
    )
    assert anchor["mean_open_sales_value"] == 100
    assert anchor["open_sales_sum"] == 2800
    assert anchor["history_start"] == date(2015, 4, 11)
    assert anchor["history_end"] == date(2015, 6, 5)

    zero_anchor = _find_row(
        tables["origin_anchors.parquet"], Store=2, forecast_origin=scenarios.ALLOWED_ORIGINS[0]
    )
    assert zero_anchor["anchor_available"] is True
    assert zero_anchor["zero_anchor"] is True
    zero_params = _find_row(
        tables["store_parameters.parquet"],
        scenario_id="synthetic_base-20150605-r00",
        Store=2,
    )
    assert zero_params["InitialStockOnHandValue"] == 0
    assert zero_params["InitialOnOrderValue"] == 0
    assert zero_params["InitialBackordersValue"] == 0
    assert zero_params["InitialInventoryPositionValue"] == 0

    cold_anchor = _find_row(
        tables["origin_anchors.parquet"], Store=3, forecast_origin=scenarios.ALLOWED_ORIGINS[0]
    )
    assert cold_anchor["open_rows"] == 27
    assert cold_anchor["missing_calendar_days"] == 1
    assert cold_anchor["unavailable_reason"] == "insufficient_open_history"
    cold_params = _find_row(
        tables["store_parameters.parquet"],
        scenario_id="synthetic_base-20150605-r00",
        Store=3,
    )
    assert cold_params["InitialStockOnHandValue"] is None
    assert cold_params["InitialInventoryPositionValue"] is None

    no_history = _find_row(
        tables["origin_anchors.parquet"], Store=4, forecast_origin=scenarios.ALLOWED_ORIGINS[0]
    )
    assert no_history["observed_rows"] == 0
    assert no_history["missing_calendar_days"] == 56
    assert no_history["unavailable_reason"] == "no_store_history"
    cold_days = tables["scenario_daily.parquet"].to_pandas()
    cold_days = cold_days.loc[
        cold_days["scenario_id"].eq("synthetic_base-20150605-r00") & cold_days["Store"].eq(3)
    ]
    assert len(cold_days) == 14
    assert cold_days["SyntheticDemandValue"].isna().all()
    assert not cold_days["synthetic_demand_available"].any()
    assert cold_days["unavailable_reason"].eq("insufficient_open_history").all()

    historical = tables["scenario_daily.parquet"].to_pandas()
    historical = historical.loc[
        historical["scenario_id"].eq("historical_replay_reference-20150605-r00")
    ]
    assert len(historical) == 4 * 14
    synthetic_context = list(scenarios.DAILY_SCHEMA.names[4:16])
    assert historical[synthetic_context].isna().all().all()
    assert not historical["synthetic_demand_available"].any()
    assert historical["unavailable_reason"].eq("historical_outcomes_not_loaded").all()


def test_parameter_cost_stock_and_scenario_overrides_are_paired(small_bundle):
    _, tables = small_bundle
    params = tables["store_parameters.parquet"]
    base = _find_row(params, scenario_id="synthetic_base-20150605-r00", Store=1)
    promo = _find_row(params, scenario_id="promo_peak-20150605-r00", Store=1)
    trend = _find_row(params, scenario_id="trend_ramp-20150605-r00", Store=1)
    long_lead = _find_row(params, scenario_id="long_lead_low_stock-20150605-r00", Store=1)
    coupled = _find_row(params, scenario_id="coupled_peak_delay-20150605-r00", Store=1)
    assert base["InitialStockOnHandValue"] == base["InventoryCoverageDays"] * 100
    assert base["HoldingCostRate"] == pytest.approx(
        base["ProcurementCostRatio"] * base["AnnualHoldingRate"] / 365
    )
    assert base["StockoutPenalty"] == pytest.approx(
        (1 - base["ProcurementCostRatio"]) + base["GoodwillPenaltyRate"]
    )
    for other in (promo, trend, long_lead, coupled):
        for field in (
            "ProcurementCostRatio",
            "AnnualHoldingRate",
            "GoodwillPenaltyRate",
            "AverageUnitValue",
            "PromotionResponseSlope",
            "PlannedPromoBlock",
            "PlannedDiscountDepth",
        ):
            assert other[field] == base[field]
    assert long_lead["SupplierLeadTime"] == 7
    assert long_lead["ProtectionPeriod"] == 8
    assert long_lead["InventoryCoverageDays"] == 1
    assert trend["TrendEndChange"] == 0.30
    assert coupled["TrendEndChange"] == 0.30
    assert coupled["SupplierLeadTime"] == 7
    assert coupled["ProtectionPeriod"] == 8
    assert coupled["InventoryCoverageDays"] == 1

    daily = tables["scenario_daily.parquet"].to_pandas()
    origin = scenarios.ALLOWED_ORIGINS[0]
    focus_date = origin + timedelta(days=4)
    rows = daily.loc[
        daily["Date"].eq(focus_date)
        & daily["Store"].eq(1)
        & daily["scenario_id"].isin(
            [
                "synthetic_base-20150605-r00",
                "promo_peak-20150605-r00",
                "coupled_peak_delay-20150605-r00",
            ]
        )
    ].set_index("scenario_id")
    assert bool(rows.loc["promo_peak-20150605-r00", "SyntheticPromo"])
    assert rows.loc["promo_peak-20150605-r00", "DiscountDepth"] == 0.40
    assert rows.loc["promo_peak-20150605-r00", "DemandStressFactor"] == 1.50
    assert rows.loc["coupled_peak_delay-20150605-r00", "DemandStressFactor"] == 2.0
    assert (
        rows.loc["promo_peak-20150605-r00", "CommonShock"]
        == rows.loc["synthetic_base-20150605-r00", "CommonShock"]
    )
    assert (
        rows.loc["promo_peak-20150605-r00", "StoreDateNoise"]
        == rows.loc["synthetic_base-20150605-r00", "StoreDateNoise"]
    )

    cross_store = daily.loc[
        daily["Date"].eq(focus_date)
        & daily["scenario_id"].eq("synthetic_base-20150605-r00")
        & daily["Store"].isin([1, 2])
    ]
    assert cross_store["CommonShock"].nunique() == 1
    assert cross_store["StoreDateNoise"].nunique() == 2


def test_calendar_closure_reopening_pulse_zero_turnover_and_weekday_factors(small_bundle):
    _, tables = small_bundle
    daily = tables["scenario_daily.parquet"].to_pandas()
    origin = scenarios.ALLOWED_ORIGINS[0]
    closure = daily.loc[
        daily["scenario_id"].eq("calendar_closure-20150605-r00") & daily["Store"].eq(1)
    ].set_index("horizon")
    assert bool(closure.loc[8, "SyntheticHolidayClosure"])
    assert closure.loc[8, "ScenarioOpen"] == 0
    assert closure.loc[8, "SyntheticDemandValue"] == 0
    assert closure.loc[9, "ScenarioOpen"] == 0  # The planned Sunday closure remains.
    assert closure.loc[10, "ScenarioOpen"] == 1
    assert closure.loc[10, "DemandStressFactor"] == 1.50
    assert not bool(closure.loc[10, "SyntheticHolidayClosure"])

    zero = daily.loc[daily["scenario_id"].eq("zero_turnover-20150605-r00") & daily["Store"].eq(1)]
    assert zero["SyntheticDemandValue"].eq(0).all()
    assert zero["DemandStressFactor"].eq(0).all()
    assert all(
        value == scenarios.WEEKDAY_FACTORS[(origin + timedelta(days=horizon)).weekday()]
        for horizon, value in zip(zero["horizon"], zero["WeekdayFactor"], strict=True)
    )


def test_keyed_draws_are_common_across_scenarios_and_change_by_replicate(small_bundle):
    _, tables = small_bundle
    daily = tables["scenario_daily.parquet"].to_pandas()
    selected = daily.loc[
        daily["Store"].eq(1)
        & daily["Date"].eq(scenarios.ALLOWED_ORIGINS[0] + timedelta(days=5))
        & daily["scenario_id"].isin(
            [
                "synthetic_base-20150605-r00",
                "synthetic_base-20150605-r01",
                "demand_slump-20150605-r00",
            ]
        )
    ].set_index("scenario_id")
    assert (
        selected.loc["synthetic_base-20150605-r00", "CommonShock"]
        == selected.loc["demand_slump-20150605-r00", "CommonShock"]
    )
    assert (
        selected.loc["synthetic_base-20150605-r00", "StoreDateNoise"]
        == selected.loc["demand_slump-20150605-r00", "StoreDateNoise"]
    )
    assert (
        selected.loc["synthetic_base-20150605-r00", "CommonShock"]
        != selected.loc["synthetic_base-20150605-r01", "CommonShock"]
        or selected.loc["synthetic_base-20150605-r00", "StoreDateNoise"]
        != selected.loc["synthetic_base-20150605-r01", "StoreDateNoise"]
    )


def test_duplicate_schema_future_and_forbidden_feature_violations_fail(small_bundle):
    config, tables = small_bundle
    scenarios.validate_scenario_tables(tables, config)

    duplicate_rows = tables["scenario_catalog.parquet"].to_pylist()
    duplicate_rows[-1] = dict(duplicate_rows[0])
    duplicate = pa.Table.from_pylist(duplicate_rows, schema=scenarios.CATALOG_SCHEMA)
    invalid = dict(tables)
    invalid["scenario_catalog.parquet"] = duplicate
    with pytest.raises(scenarios.ScenarioIntegrityError, match="duplicate|sorted"):
        scenarios.validate_scenario_tables(invalid, config)

    wrong_schema = tables["scenario_catalog.parquet"].select(
        list(reversed(tables["scenario_catalog.parquet"].column_names))
    )
    invalid = dict(tables)
    invalid["scenario_catalog.parquet"] = wrong_schema
    with pytest.raises(scenarios.ScenarioIntegrityError, match="schema"):
        scenarios.validate_scenario_tables(invalid, config)

    future_rows = tables["scenario_daily.parquet"].to_pylist()
    future_rows[-1]["Date"] = date(2015, 7, 4)
    invalid = dict(tables)
    invalid["scenario_daily.parquet"] = pa.Table.from_pylist(
        future_rows, schema=scenarios.DAILY_SCHEMA
    )
    with pytest.raises(scenarios.ScenarioIntegrityError, match="sorted|origin|boundary"):
        scenarios.validate_scenario_tables(invalid, config)

    forbidden = {"Sales", "actual_sales", "Customers", "source_open", "Promo", "Open"}
    generated_names = set(scenarios.DAILY_SCHEMA.names) | set(scenarios.PARAMETER_SCHEMA.names)
    assert not forbidden.intersection(generated_names)
    assert not set(PREDICTOR_COLUMNS).intersection(
        {"ScenarioOpen", "SyntheticPromo", "SyntheticDemandValue", "DemandStressFactor"}
    )


def test_input_schema_duplicates_and_future_rows_fail_closed():
    origin = scenarios.ALLOWED_ORIGINS[0]
    valid = _history(1, origin)
    with_customer = valid.assign(Customers=10)
    with pytest.raises(scenarios.ScenarioIntegrityError, match="exactly"):
        scenarios.validate_history_frame(with_customer, origin=origin, stores=[1])
    duplicated = pd.concat([valid, valid.iloc[[0]]], ignore_index=True)
    with pytest.raises(scenarios.ScenarioIntegrityError, match="duplicate"):
        scenarios.validate_history_frame(duplicated, origin=origin, stores=[1])
    future = pd.concat(
        [valid, pd.DataFrame([{"Store": 1, "Date": date(2015, 7, 4), "Sales": 10, "Open": 1}])],
        ignore_index=True,
    )
    with pytest.raises(scenarios.ScenarioIntegrityError, match="outside the exact origin window"):
        scenarios.validate_history_frame(future, origin=origin, stores=[1])
    invalid_open = valid.copy()
    invalid_open.loc[0, "Open"] = 2
    with pytest.raises(scenarios.ScenarioIntegrityError, match="Open"):
        scenarios.validate_history_frame(invalid_open, origin=origin, stores=[1])
    negative_sales = valid.copy()
    negative_sales.loc[0, "Sales"] = -1
    with pytest.raises(scenarios.ScenarioIntegrityError, match="nonnegative"):
        scenarios.validate_history_frame(negative_sales, origin=origin, stores=[1])


def test_reader_pushes_store_and_exact_date_predicates_before_materialization(monkeypatch):
    captured = {}

    class FakeDataset:
        schema = pa.schema(
            [
                pa.field("Store", pa.int64()),
                pa.field("Date", pa.timestamp("ns")),
                pa.field("Sales", pa.int64()),
                pa.field("Open", pa.int8()),
            ]
        )

        def to_table(self, *, columns, filter, use_threads):
            captured.update(columns=columns, filter=filter, use_threads=use_threads)
            return pa.Table.from_pydict(
                {
                    "Store": pa.array([], type=pa.int64()),
                    "Date": pa.array([], type=pa.timestamp("ns")),
                    "Sales": pa.array([], type=pa.int64()),
                    "Open": pa.array([], type=pa.int8()),
                }
            )

    monkeypatch.setattr(scenarios.ds, "dataset", lambda path, format: FakeDataset())
    result = scenarios.read_censored_history("fake.parquet", origin="2015-06-05", stores=[2, 1])
    assert result.empty
    assert captured["columns"] == ["Store", "Date", "Sales", "Open"]
    predicate = str(captured["filter"])
    assert "Date" in predicate and "Store" in predicate
    assert "2015-04-11" in predicate and "2015-06-05" in predicate
    assert captured["use_threads"] is False

    def forbidden_dataset(*args, **kwargs):
        raise AssertionError("An unsupported origin must fail before opening the source.")

    monkeypatch.setattr(scenarios.ds, "dataset", forbidden_dataset)
    with pytest.raises(scenarios.ScenarioIntegrityError, match="Unsupported origin"):
        scenarios.read_censored_history("forbidden.parquet", origin="2015-07-03", stores=[1])


def test_logical_hashes_ignore_history_row_order_output_row_order_and_chunking(small_bundle):
    config, tables = small_bundle
    reversed_history = {
        origin: frame.iloc[::-1].reset_index(drop=True) for origin, frame in _histories().items()
    }
    reordered = scenarios.generate_scenario_tables(config, reversed_history)
    for name, key in scenarios.TABLE_KEYS.items():
        assert scenarios.logical_table_sha256(tables[name], key) == scenarios.logical_table_sha256(
            reordered[name], key
        )
    daily = tables["scenario_daily.parquet"]
    permutation = np.random.default_rng(7).permutation(daily.num_rows)
    shuffled = daily.take(pa.array(permutation, type=pa.int64()))
    assert scenarios.logical_table_sha256(
        shuffled, scenarios.TABLE_KEYS["scenario_daily.parquet"]
    ) == scenarios.logical_table_sha256(daily, scenarios.TABLE_KEYS["scenario_daily.parquet"])
    chunks = [daily.slice(0, 133), daily.slice(133, 1000), daily.slice(1133)]
    assert scenarios._logical_sha256_batches(
        chunks, scenarios.DAILY_SCHEMA, scenarios.TABLE_KEYS["scenario_daily.parquet"]
    ) == scenarios.logical_table_sha256(daily, scenarios.TABLE_KEYS["scenario_daily.parquet"])


def test_store_subset_retains_same_paired_draw_rows(small_bundle):
    _, full = small_bundle
    subset_config = scenarios.default_config(stores=[1])
    subset = scenarios.generate_scenario_tables(
        subset_config,
        {origin: frame.loc[frame["Store"].eq(1)] for origin, frame in _histories().items()},
    )
    full_daily = full["scenario_daily.parquet"].filter(
        pc.equal(full["scenario_daily.parquet"]["Store"], 1)
    )
    assert scenarios.logical_table_sha256(
        full_daily, scenarios.TABLE_KEYS["scenario_daily.parquet"]
    ) == scenarios.logical_table_sha256(
        subset["scenario_daily.parquet"], scenarios.TABLE_KEYS["scenario_daily.parquet"]
    )


def test_phase7_phase8_identity_and_fit_chronology_fail_closed():
    valid_phase7 = {
        "command": "rossmann-model-selection",
        "status": "selected",
        "publication_state": "complete",
        "input_integrity_status": "passed",
        "record_integrity_status": "passed",
        "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
        "selection_run_id": "365f22d4c3f94722a594ab934a22c4f6",
        "final_holdout_forecast_or_evaluation": False,
        "final_holdout_outcomes_read_or_hashed": False,
        "phase_8_started": False,
        "policy_version": "phase-7-adr-020-v1",
    }
    scenarios.validate_phase7_selection_identity(valid_phase7)
    with pytest.raises(scenarios.ScenarioIntegrityError, match="selected_candidate_id"):
        scenarios.validate_phase7_selection_identity(
            {**valid_phase7, "selected_candidate_id": "seasonal_naive"}
        )

    valid_phase8 = {
        "run_id": "phase8-impl-20261006-provenance-review",
        "policy_version": "phase-8-uncertainty-v1",
        "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
        "selection_run_id": "365f22d4c3f94722a594ab934a22c4f6",
        "fit_b_quantiles_frozen": False,
        "external_fit_b_results_review_pending": True,
    }
    scenarios.validate_phase8_manifest_identity(valid_phase8)
    with pytest.raises(scenarios.ScenarioIntegrityError, match="fit_b_quantiles_frozen"):
        scenarios.validate_phase8_manifest_identity(
            {**valid_phase8, "fit_b_quantiles_frozen": True}
        )

    fit_specs = [
        {
            "fit_id": "A",
            "assessment_window": "validation_2",
            "assessment_origin": "2015-06-05",
            "assessment_targets_after_origin": True,
            "assessment_target_dates": {"first_date": "2015-06-06", "last_date": "2015-06-19"},
            "calibration_windows": ["validation_1"],
            "calibration_labels_through": "2015-06-05",
            "calibration_date_ranges": [
                {"first_date": "2015-05-23", "last_date": "2015-06-05", "window": "validation_1"}
            ],
        },
        {
            "fit_id": "B",
            "assessment_window": "validation_3",
            "assessment_origin": "2015-06-19",
            "assessment_targets_after_origin": True,
            "assessment_target_dates": {"first_date": "2015-06-20", "last_date": "2015-07-03"},
            "calibration_windows": ["validation_1", "validation_2"],
            "calibration_labels_through": "2015-06-19",
            "calibration_date_ranges": [
                {"first_date": "2015-05-23", "last_date": "2015-06-05", "window": "validation_1"},
                {"first_date": "2015-06-06", "last_date": "2015-06-19", "window": "validation_2"},
            ],
        },
    ]
    scenarios.validate_phase8_fit_chronology(fit_specs)
    wrong_fit_b = [dict(row) for row in fit_specs]
    wrong_fit_b[1]["assessment_origin"] = "2015-06-05"
    with pytest.raises(scenarios.ScenarioIntegrityError, match="chronology"):
        scenarios.validate_phase8_fit_chronology(wrong_fit_b)


def test_atomic_pointer_failure_preserves_previous_run_and_current_pointer(tmp_path, monkeypatch):
    output_root = tmp_path / "data/processed/synthetic_inventory"
    output_root.mkdir(parents=True)
    old_run = output_root / "old-run"
    old_run.mkdir()
    (old_run / "sentinel.txt").write_text("previous", encoding="utf-8")
    current = output_root / "current.json"
    current.write_text('{"run_id":"old-run"}\n', encoding="utf-8")
    original_pointer = current.read_bytes()
    original_sentinel = (old_run / "sentinel.txt").read_bytes()
    stage = output_root / ".stage-new"
    stage.mkdir()
    (stage / "manifest.json").write_text("{}\n", encoding="utf-8")
    final = output_root / "new-run"
    real_replace = scenarios.os.replace

    def fail_current_replace(source, destination):
        if Path(destination) == current:
            raise OSError("injected pointer failure")
        real_replace(source, destination)

    monkeypatch.setattr(scenarios.os, "replace", fail_current_replace)
    with pytest.raises(OSError, match="injected pointer"):
        scenarios._atomic_publish(stage, final, output_root, {"run_id": "new-run"})
    assert not final.exists()
    assert current.read_bytes() == original_pointer
    assert (old_run / "sentinel.txt").read_bytes() == original_sentinel


def test_existing_run_id_is_immutable_and_preserves_current_pointer(tmp_path):
    output_root = tmp_path / "data/processed/synthetic_inventory"
    output_root.mkdir(parents=True)
    existing = output_root / "existing-run"
    existing.mkdir()
    sentinel = existing / "sentinel.txt"
    sentinel.write_text("original", encoding="utf-8")
    original_sentinel = sentinel.read_bytes()
    current = output_root / "current.json"
    current.write_text('{"run_id":"existing-run"}\n', encoding="utf-8")
    original_pointer = current.read_bytes()
    stage = output_root / ".stage-existing"
    stage.mkdir()
    (stage / "sentinel.txt").write_text("replacement", encoding="utf-8")

    with pytest.raises(FileExistsError, match="run ID already exists"):
        scenarios._atomic_publish(stage, existing, output_root, {"run_id": "existing-run"})

    assert sentinel.read_bytes() == original_sentinel
    assert current.read_bytes() == original_pointer
    assert stage.exists()


def test_config_rejects_unapproved_origins_and_rng_isolation_has_no_feature_aliases():
    config = scenarios.default_config(stores=[1])
    config["forecast_origins"] = ["2015-07-03", "2015-06-19"]
    with pytest.raises(scenarios.ScenarioIntegrityError, match="Only the June 5 and June 19"):
        scenarios._validate_config(config)
    assert not {"Sales", "Customers", "Open", "Promo"}.intersection(scenarios.DAILY_SCHEMA.names)
    assert "ScenarioOpen" not in PREDICTOR_COLUMNS
    assert "SyntheticPromo" not in PREDICTOR_COLUMNS
    assert "SyntheticDemandValue" not in PREDICTOR_COLUMNS
