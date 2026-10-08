"""Synthetic-fixture tests for the Phase 11 shared read-only services."""

from __future__ import annotations

import json
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


@pytest.fixture
def fixture_store(tmp_path) -> FixtureStore:
    return FixtureStore(tmp_path)


def _write_policy_pair(
    fixture_store: FixtureStore,
    *,
    episode_complete: bool = True,
    target_available: bool = True,
    valid_matched_comparison: bool = True,
    baseline_cost: float | None = 100.0,
    forecast_cost: float | None = 150.0,
    target_case_id: str = "fixture-case",
) -> None:
    for selector, schema in (
        (ArtifactSelector.PHASE10_POLICY_SUMMARY, POLICY_SUMMARY_SCHEMA),
        (ArtifactSelector.PHASE10_POLICY_TARGETS, POLICY_TARGET_SCHEMA),
    ):
        rows = []
        for index, policy_id in enumerate(POLICY_IDS):
            row = {field.name: _sample_arrow_value(field) for field in schema}
            row.update(
                {
                    "case_id": "fixture-case",
                    "scenario_id": "fixture-scenario",
                    "Store": 1,
                    "forecast_origin": date(2015, 6, 19),
                    "family": "synthetic_base",
                    "mode": "synthetic_stress",
                    "replicate": 1,
                    "sensitivity_variant": "reference",
                    "policy_id": policy_id,
                    "episode_status": "complete" if episode_complete else "incomplete",
                    "episode_complete": episode_complete,
                    "target_available": target_available,
                    "availability_reason": None if target_available else "fixture_unavailable",
                    "valid_matched_comparison": valid_matched_comparison,
                }
            )
            if selector is ArtifactSelector.PHASE10_POLICY_SUMMARY:
                row["SimulatedHoldingPlusShortfallCost"] = (
                    baseline_cost if index == 0 else forecast_cost
                )
            else:
                row["target_value"] = (200.0 if index == 0 else 250.0) if target_available else None
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
        InventoryComparisonQuery("fixture-case", store_id=1)
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


def test_inventory_keeps_incomplete_and_unavailable_pairs_without_filling_costs(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(
        fixture_store,
        episode_complete=False,
        target_available=False,
        valid_matched_comparison=False,
        baseline_cost=None,
        forecast_cost=None,
    )

    result = ApplicationServices(fixture_store.reader()).inventory_comparison(
        InventoryComparisonQuery("fixture-case", store_id=1)
    )
    pair = result.policy_pairs[0]

    assert pair.comparable is False
    assert pair.forecast_minus_baseline_cost is None
    assert pair.baseline.simulated_holding_plus_shortfall_cost is None
    assert pair.forecast.target_value is None
    assert pair.difference_unavailable_reason == "not_valid_matched_comparison"


def test_inventory_rejects_summary_target_key_mismatch(fixture_store: FixtureStore) -> None:
    _write_policy_pair(fixture_store, target_case_id="different-case")

    with pytest.raises(ArtifactIntegrityError):
        ApplicationServices(fixture_store.reader()).inventory_comparison(
            InventoryComparisonQuery("fixture-case", store_id=1)
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
            InventoryComparisonQuery("fixture-case", store_id=1)
        )


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
