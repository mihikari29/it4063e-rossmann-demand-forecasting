"""Synthetic-fixture tests for the Phase 11 shared read-only services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from test_app_artifacts import (
    _DOMAIN_STRINGS,
    _FIXTURE_SCHEMAS,
    FixtureStore,
    _artifact_path,
    _sample_arrow_value,
)

from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactSelector,
    ForecastQuery,
    InvalidArtifactRequestError,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.services import ApplicationServices, json_safe
from rossmann_forecasting.inventory.simulation import (
    POLICY_IDS,
    POLICY_SUMMARY_SCHEMA,
    POLICY_TARGET_SCHEMA,
)

_FIXTURE_SCENARIO_ID = "fixture-scenario"
_FIXTURE_VARIANT = "reference"
_FIXTURE_CASE_ID = f"{_FIXTURE_SCENARIO_ID}--{_FIXTURE_VARIANT}"


@pytest.fixture
def fixture_store(tmp_path) -> FixtureStore:
    return FixtureStore(tmp_path)


def _write_policy_pair(
    fixture_store: FixtureStore,
    *,
    baseline_episode_complete: bool = True,
    forecast_episode_complete: bool = True,
    baseline_target_available: bool = True,
    forecast_target_available: bool = True,
    baseline_valid_matched_comparison: bool | None = None,
    forecast_valid_matched_comparison: bool | None = None,
    baseline_episode_reason: str | None = None,
    forecast_episode_reason: str | None = None,
    baseline_target_reason: str | None = None,
    forecast_target_reason: str | None = None,
    baseline_cost: float | None = 100.0,
    forecast_cost: float | None = 150.0,
    target_value_overrides: dict[str, float | None] | None = None,
    omit_policy_ids: tuple[str, ...] = (),
    target_case_id: str = _FIXTURE_CASE_ID,
) -> None:
    comparison_selector = ArtifactSelector.PHASE10_COMPARISON
    comparison_path = _artifact_path(fixture_store, comparison_selector)
    comparison_bytes = comparison_path.read_bytes()
    assert b"fixture-case" in comparison_bytes
    comparison_path.write_bytes(
        comparison_bytes.replace(b"fixture-case", _FIXTURE_CASE_ID.encode("utf-8"))
    )
    fixture_store.refresh_output(comparison_selector)

    policy_states = {}
    for index, policy_id in enumerate(POLICY_IDS):
        is_baseline = index == 0
        episode_complete = baseline_episode_complete if is_baseline else forecast_episode_complete
        target_available = baseline_target_available if is_baseline else forecast_target_available
        valid = (
            baseline_valid_matched_comparison if is_baseline else forecast_valid_matched_comparison
        )
        if valid is None:
            valid = episode_complete and target_available
        target_reason = baseline_target_reason if is_baseline else forecast_target_reason
        if target_available:
            target_reason = None
        elif target_reason is None:
            target_reason = "anchor_unavailable" if is_baseline else "insufficient_calibration"
        episode_reason = baseline_episode_reason if is_baseline else forecast_episode_reason
        if episode_complete:
            episode_reason = None
            episode_status = "complete"
        else:
            if episode_reason is None:
                episode_reason = target_reason if not target_available else "missing_consumption"
            episode_status = "incomplete_episode" if target_available else episode_reason
        policy_states[policy_id] = {
            "episode_complete": episode_complete,
            "target_available": target_available,
            "valid_matched_comparison": valid,
            "episode_status": episode_status,
            "episode_reason": episode_reason,
            "target_reason": target_reason,
            "cost": (baseline_cost if is_baseline else forecast_cost) if episode_complete else None,
        }

    for selector, schema in (
        (ArtifactSelector.PHASE10_POLICY_SUMMARY, POLICY_SUMMARY_SCHEMA),
        (ArtifactSelector.PHASE10_POLICY_TARGETS, POLICY_TARGET_SCHEMA),
    ):
        rows = []
        for index, policy_id in enumerate(POLICY_IDS):
            if policy_id in omit_policy_ids:
                continue
            state = policy_states[policy_id]
            is_baseline = index == 0
            row = {field.name: _sample_arrow_value(field) for field in schema}
            row.update(
                {
                    "case_id": _FIXTURE_CASE_ID,
                    "scenario_id": _FIXTURE_SCENARIO_ID,
                    "Store": 1,
                    "forecast_origin": date(2015, 6, 19),
                    "family": "synthetic_base",
                    "mode": "synthetic_stress",
                    "replicate": 1,
                    "sensitivity_variant": _FIXTURE_VARIANT,
                    "policy_id": policy_id,
                    "episode_status": state["episode_status"],
                    "episode_complete": state["episode_complete"],
                    "target_available": state["target_available"],
                    "availability_reason": state["episode_reason"],
                    "valid_matched_comparison": state["valid_matched_comparison"],
                }
            )
            if selector is ArtifactSelector.PHASE10_POLICY_SUMMARY:
                row["SimulatedHoldingPlusShortfallCost"] = state["cost"]
                row["historical_open_assumption_violation"] = (
                    not state["valid_matched_comparison"] and state["episode_complete"]
                )
                row["common_input_identity"] = "fixture-input-identity"
                if state["episode_complete"]:
                    cost = state["cost"]
                    row.update(
                        {
                            "calendar_days": 14,
                            "demand_total": 10.0,
                            "fulfilled_total": 10.0,
                            "unmet_total": 0.0,
                            "positive_demand_days": 1,
                            "positive_demand_stockout_days": 0,
                            "ending_inventory_sum": 140.0,
                            "holding_cost_total": cost,
                            "unmet_penalty_total": 0.0,
                            "ValueFillRate": 1.0,
                            "PositiveDemandStockoutRate": 0.0,
                            "AverageInventoryValue": 10.0,
                            "UnmetTurnoverValue": 0.0,
                            "SimulatedHoldingCost": cost,
                            "SimulatedUnmetPenalty": 0.0,
                        }
                    )
                else:
                    for field in POLICY_SUMMARY_SCHEMA.names:
                        if field not in {
                            "case_id",
                            "scenario_id",
                            "Store",
                            "forecast_origin",
                            "family",
                            "mode",
                            "replicate",
                            "sensitivity_variant",
                            "policy_id",
                            "episode_status",
                            "episode_complete",
                            "target_available",
                            "availability_reason",
                            "valid_matched_comparison",
                            "historical_open_assumption_violation",
                            "calendar_days",
                            "common_input_identity",
                        }:
                            row[field] = None
                    row["calendar_days"] = 0
            else:
                row.update(
                    {
                        "SupplierLeadTime": 2,
                        "ReviewPeriod": 1,
                        "ProtectionPeriod": 3,
                        "buffer_probability": 0.95,
                        "mean_open_sales_value": 100.0 if baseline_target_available else None,
                        "open_days_in_protection_period": 2,
                        "forecast_protection_demand_value": 180.0,
                        "cumulative_signed_quantile": 70.0 if state["target_available"] else None,
                        "upper_turnover_value": 250.0 if state["target_available"] else None,
                        "safety_stock_value": 70.0 if state["target_available"] else None,
                        "target_value": 200.0 if is_baseline else 250.0,
                        "initial_stock_value": 10.0,
                        "ProcurementCostRatio": 0.5,
                        "AnnualHoldingRate": 0.1,
                        "GoodwillPenaltyRate": 0.75,
                        "fit_id": "B",
                        "model_id": "global_lightgbm_gbdt_regression_l1",
                        "upstream_identity": "fixture-upstream-identity",
                        "synthetic": True,
                        "calibration_transport_valid": False,
                        "schedule_assumption": "phase9_scenario_open_known_at_origin",
                        "buffer_interpretation": (
                            "historical_mean_open_day_target"
                            if is_baseline
                            else "uncalibrated_synthetic_heuristic"
                        ),
                        "target_available": state["target_available"],
                        "availability_reason": state["target_reason"],
                    }
                )
                if not baseline_target_available:
                    row["mean_open_sales_value"] = None
                if is_baseline and not state["target_available"]:
                    row["open_days_in_protection_period"] = 0
                if not state["target_available"]:
                    row["target_value"] = None
                if target_value_overrides and policy_id in target_value_overrides:
                    row["target_value"] = target_value_overrides[policy_id]
                row["case_id"] = target_case_id
            rows.append(row)
        path = _artifact_path(fixture_store, selector)
        pq.write_table(pa.Table.from_pylist(rows, schema=schema), path)
        fixture_store.refresh_output(selector)


def test_catalog_reports_only_supported_metadata_and_real_validation_levels(
    fixture_store: FixtureStore,
) -> None:
    service = ApplicationServices(fixture_store.reader())

    catalog = service.catalog()
    payload = json_safe(catalog)
    json.dumps(payload, allow_nan=False)

    assert catalog.phases == ("phase7", "phase8", "phase9", "phase10")
    assert "historical_sales" in catalog.selectors
    assert all("ledger" not in item for item in catalog.selectors)
    assert catalog.supported_store_ids[0] == 1
    assert catalog.supported_store_ids[-1] == 1115
    assert catalog.phase7_forecast_origins == ("2015-05-22", "2015-06-05", "2015-06-19")
    assert catalog.phase8_fits == (("A", "2015-06-05"), ("B", "2015-06-19"))
    assert catalog.scenario_catalog_state == "available"
    assert [item.scenario_id for item in catalog.scenarios] == ["fixture-scenario"]
    assert catalog.inventory_case_ids == ("fixture-case",)
    readiness = {item.selector: item.validation_level for item in catalog.resources}
    assert readiness[ArtifactSelector.PHASE9_SCENARIO_CATALOG.value] == "output_verified"
    assert readiness[ArtifactSelector.PHASE10_COMPARISON.value] == "output_verified"
    assert readiness[ArtifactSelector.PHASE10_POLICY_SUMMARY.value] == "manifest_validated"
    resource_by_selector = {item.selector: item for item in catalog.resources}
    assert resource_by_selector[ArtifactSelector.PHASE10_POLICY_SUMMARY.value].output_present
    assert resource_by_selector[ArtifactSelector.PHASE10_POLICY_SUMMARY.value].manifest_validated
    assert not resource_by_selector[
        ArtifactSelector.PHASE10_POLICY_SUMMARY.value
    ].output_hash_verified
    assert resource_by_selector[ArtifactSelector.PHASE9_SCENARIO_CATALOG.value].output_hash_verified
    assert "data/" not in json.dumps(payload)


def test_forecast_issuance_has_a_whitelisted_json_safe_shape(fixture_store: FixtureStore) -> None:
    service = ApplicationServices(fixture_store.reader())

    result = service.forecast_issuance(ForecastQuery(1, date(2015, 6, 19)))
    payload = json_safe(result)
    encoded = json.dumps(payload, allow_nan=False)

    assert result.state == "available"
    assert len(result.points) == 1
    assert result.points[0].date == "2015-06-20"
    assert result.points[0].horizon == 1
    assert result.points[0].candidate_id == _DOMAIN_STRINGS["candidate_id"]
    assert "actual_sales" not in encoded
    assert "source_open" not in encoded
    assert "assessment" not in encoded
    assert result.provenance.selected_rows == 1
    assert result.provenance.manifest_rows == 1


def test_uncertainty_preserves_null_strata_and_omits_assessment_outcomes(
    fixture_store: FixtureStore,
) -> None:
    for selector in (
        ArtifactSelector.PHASE8_DAILY_INTERVALS,
        ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY,
    ):
        schema = _FIXTURE_SCHEMAS[selector]
        row = {field.name: _sample_arrow_value(field) for field in schema}
        row["fit_id"] = "B"
        row["Store"] = 1
        row["forecast_origin"] = pd.Timestamp("2015-06-19")
        row["unavailable_reason"] = None
        row["issued_prefix_unavailable_reason"] = None
        row["lower"] = None
        row["upper"] = None
        row["available"] = False
        if selector is ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY:
            row["issued_prefix_complete"] = False
            row["D_k"] = None
            row["q_p_signed"] = None
            row["U_k"] = None
            row["SafetyStock_k"] = None
            row["Target_k"] = None
        path = _artifact_path(fixture_store, selector)
        pq.write_table(pa.Table.from_pylist([row], schema=schema), path)
        fixture_store.refresh_output(selector)

    result = ApplicationServices(fixture_store.reader()).forecast_uncertainty(
        UncertaintyQuery(1, date(2015, 6, 19), "B")
    )
    payload = json_safe(result)
    encoded = json.dumps(payload, allow_nan=False)

    assert result.state == "available"
    assert result.daily_intervals[0].available is False
    assert result.daily_intervals[0].lower is None
    assert result.cumulative_uncertainty[0].issued_prefix_complete is False
    assert result.cumulative_uncertainty[0].target_value is None
    assert "actual_sales" not in encoded
    assert "assessment_source_open" not in encoded
    assert "95% performance guarantee" in result.interpretation


def test_model_comparison_keeps_population_denominator_and_unavailability(
    fixture_store: FixtureStore,
) -> None:
    result = ApplicationServices(fixture_store.reader()).model_comparison(
        ModelComparisonQuery(candidate_id="global_lightgbm_gbdt_regression_l1", metric="mae")
    )

    assert result.state == "available"
    row = result.rows[0]
    assert row.population == "standalone"
    assert row.metric == "mae"
    assert row.value == 12.5
    assert row.numerator == 12.5
    assert row.denominator == 1.0
    assert row.unavailable_reason is None


def test_inventory_pairs_policies_and_preserves_signed_adverse_cost_difference(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(fixture_store, baseline_cost=100.0, forecast_cost=150.0)

    result = ApplicationServices(fixture_store.reader()).inventory_comparison(
        InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1)
    )

    assert result.state == "available"
    assert len(result.case_level_comparisons) == 1
    assert len(result.policy_pairs) == 1
    pair = result.policy_pairs[0]
    assert pair.baseline.policy_id == POLICY_IDS[0]
    assert pair.forecast.policy_id == POLICY_IDS[1]
    assert pair.comparable is True
    assert pair.forecast_minus_baseline_cost == 50.0
    assert pair.difference_unavailable_reason is None
    assert result.case_level_comparisons[0].baseline_value is None
    unfiltered = ApplicationServices(fixture_store.reader()).inventory_comparison(
        InventoryComparisonQuery(_FIXTURE_CASE_ID)
    )
    assert result.case_level_comparisons == unfiltered.case_level_comparisons


def test_inventory_preserves_available_target_with_incomplete_episode(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(
        fixture_store,
        forecast_episode_complete=False,
        forecast_episode_reason="missing_consumption",
    )

    result = ApplicationServices(fixture_store.reader()).inventory_comparison(
        InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1)
    )
    pair = result.policy_pairs[0]

    assert pair.forecast.target_available is True
    assert pair.forecast.target_unavailability_reason is None
    assert pair.forecast.episode_complete is False
    assert pair.forecast.episode_status == "incomplete_episode"
    assert pair.forecast.availability_reason == "missing_consumption"
    assert pair.comparable is False
    assert pair.forecast_minus_baseline_cost is None
    assert pair.forecast.simulated_holding_plus_shortfall_cost is None
    assert pair.difference_unavailable_reason == "missing_consumption"


def test_inventory_incomplete_pair_with_missing_costs_has_explicit_reason(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(
        fixture_store,
        baseline_episode_complete=False,
        forecast_episode_complete=False,
        baseline_episode_reason="missing_consumption",
        forecast_episode_reason="missing_consumption",
        baseline_cost=None,
        forecast_cost=None,
    )

    pair = (
        ApplicationServices(fixture_store.reader())
        .inventory_comparison(InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1))
        .policy_pairs[0]
    )

    assert pair.comparable is False
    assert pair.baseline.simulated_holding_plus_shortfall_cost is None
    assert pair.forecast.simulated_holding_plus_shortfall_cost is None
    assert pair.forecast_minus_baseline_cost is None
    assert pair.difference_unavailable_reason == "missing_consumption"


def test_inventory_keeps_independent_baseline_and_forecast_availability(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(
        fixture_store,
        forecast_episode_complete=False,
        forecast_target_available=False,
    )

    pair = (
        ApplicationServices(fixture_store.reader())
        .inventory_comparison(InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1))
        .policy_pairs[0]
    )

    assert pair.baseline.episode_complete is True
    assert pair.baseline.target_available is True
    assert pair.baseline.valid_matched_comparison is True
    assert pair.baseline.simulated_holding_plus_shortfall_cost == 100.0
    assert pair.forecast.episode_complete is False
    assert pair.forecast.target_available is False
    assert pair.forecast.target_unavailability_reason == "insufficient_calibration"
    assert pair.forecast.availability_reason == "insufficient_calibration"
    assert pair.forecast.valid_matched_comparison is False
    assert pair.forecast.simulated_holding_plus_shortfall_cost is None
    assert pair.comparable is False
    assert pair.forecast_minus_baseline_cost is None
    assert pair.difference_unavailable_reason == "insufficient_calibration"


def test_inventory_keeps_reverse_asymmetric_policy_validity(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(
        fixture_store,
        baseline_episode_complete=False,
        baseline_target_available=False,
        forecast_valid_matched_comparison=True,
    )

    pair = (
        ApplicationServices(fixture_store.reader())
        .inventory_comparison(InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1))
        .policy_pairs[0]
    )

    assert pair.baseline.valid_matched_comparison is False
    assert pair.baseline.target_available is False
    assert pair.forecast.valid_matched_comparison is True
    assert pair.forecast.target_available is True
    assert pair.comparable is False
    assert pair.forecast_minus_baseline_cost is None
    assert pair.difference_unavailable_reason == "anchor_unavailable"


@pytest.mark.parametrize(
    ("forecast_target_available", "target_value_overrides"),
    [
        (True, {POLICY_IDS[0]: None, POLICY_IDS[1]: None}),
        (False, {POLICY_IDS[1]: 250.0}),
    ],
    ids=("available-target-with-null-value", "unavailable-target-with-value"),
)
def test_inventory_rejects_target_flag_value_inconsistency(
    fixture_store: FixtureStore,
    forecast_target_available: bool,
    target_value_overrides: dict[str, float | None],
) -> None:
    _write_policy_pair(
        fixture_store,
        forecast_episode_complete=forecast_target_available,
        forecast_target_available=forecast_target_available,
        target_value_overrides=target_value_overrides,
    )

    with pytest.raises(ArtifactIntegrityError):
        ApplicationServices(fixture_store.reader()).inventory_comparison(
            InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1)
        )


def test_inventory_preserves_exact_negative_signed_cost_difference(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(fixture_store, baseline_cost=150.0, forecast_cost=100.0)

    pair = (
        ApplicationServices(fixture_store.reader())
        .inventory_comparison(InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1))
        .policy_pairs[0]
    )

    assert pair.comparable is True
    assert pair.forecast_minus_baseline_cost == -50.0
    assert pair.difference_unavailable_reason is None


def test_inventory_rejects_summary_target_key_mismatch(fixture_store: FixtureStore) -> None:
    _write_policy_pair(fixture_store, target_case_id="different-case")

    with pytest.raises(ArtifactIntegrityError):
        ApplicationServices(fixture_store.reader()).inventory_comparison(
            InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1)
        )


def test_inventory_rejects_unrecognized_policy_id(fixture_store: FixtureStore) -> None:
    _write_policy_pair(fixture_store)
    selector = ArtifactSelector.PHASE10_POLICY_TARGETS
    path = _artifact_path(fixture_store, selector)
    rows = pq.ParquetFile(path).read().to_pylist()
    rows[0]["policy_id"] = "unrecognized_policy"
    pq.write_table(pa.Table.from_pylist(rows, schema=POLICY_TARGET_SCHEMA), path)
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactIntegrityError):
        ApplicationServices(fixture_store.reader()).inventory_comparison(
            InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1)
        )


def test_inventory_rejects_missing_policy_id(fixture_store: FixtureStore) -> None:
    _write_policy_pair(fixture_store, omit_policy_ids=(POLICY_IDS[0],))

    with pytest.raises(ArtifactIntegrityError):
        ApplicationServices(fixture_store.reader()).inventory_comparison(
            InventoryComparisonQuery(_FIXTURE_CASE_ID, store_id=1)
        )


def test_json_safe_serializes_nested_missing_sentinels_and_keeps_exact_values() -> None:
    @dataclass(frozen=True)
    class NestedDto:
        missing: object
        date_value: date
        large_integer: int

    payload = json_safe(
        {
            "direct": pd.NaT,
            "pandas_na": pd.NA,
            "items": [pd.NaT],
            "nested": {"missing": pd.NaT},
            "dto": NestedDto(pd.NaT, date(2024, 1, 2), 9_007_199_254_740_993),
            "finite": 2.5,
            "none": None,
        }
    )
    encoded = json.dumps(payload, allow_nan=False)

    assert json.loads(encoded) == {
        "direct": None,
        "pandas_na": None,
        "items": [None],
        "nested": {"missing": None},
        "dto": {
            "missing": None,
            "date_value": "2024-01-02",
            "large_integer": 9_007_199_254_740_993,
        },
        "finite": 2.5,
        "none": None,
    }
    assert "NaT" not in encoded
    for value in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="non-finite"):
            json_safe(value)


def test_unknown_inventory_case_is_rejected_before_policy_table_reads(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = fixture_store.reader()
    monkeypatch.setattr(
        reader,
        "read_inventory_artifact",
        lambda *args, **kwargs: pytest.fail("policy data read for an unknown case"),
    )

    with pytest.raises(InvalidArtifactRequestError):
        ApplicationServices(reader).inventory_comparison(
            InventoryComparisonQuery("unknown-case", store_id=1)
        )


def test_known_case_with_no_selected_store_is_an_empty_view(fixture_store: FixtureStore) -> None:
    result = ApplicationServices(fixture_store.reader()).inventory_comparison(
        InventoryComparisonQuery("fixture-case", store_id=2)
    )

    assert result.state == "empty"
    assert result.case_level_comparisons
    assert result.policy_pairs == ()


def test_history_wrapper_preserves_m1_projection_and_cutoff(fixture_store: FixtureStore) -> None:
    from rossmann_forecasting.app.contracts import HistoryQuery

    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([1, 1], type=pa.int64()),
                "Date": pa.array(
                    [pd.Timestamp("2015-07-03"), pd.Timestamp("2015-07-04")],
                    type=pa.timestamp("ns"),
                ),
                "Sales": pa.array([100, 200], type=pa.int64()),
                "Open": pa.array([1, 1], type=pa.int64()),
                "Customers": pa.array([10, 20], type=pa.int64()),
            }
        ),
        source,
    )

    result = ApplicationServices(fixture_store.reader()).sales_history(
        HistoryQuery(1, date(2015, 7, 3), date(2015, 7, 3))
    )
    payload = json_safe(result)

    assert len(result.rows) == 1
    assert result.rows[0].date == "2015-07-03"
    assert "Customers" not in json.dumps(payload)
    assert "2015-07-04" not in json.dumps(payload)
