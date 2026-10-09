"""Cross-layer HTTP tests using trusted synthetic reader artifacts."""

from __future__ import annotations

import hashlib
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient
from test_app_artifacts import (
    _FIXTURE_SCHEMAS,
    FixtureStore,
    _artifact_path,
    _sample_arrow_value,
)
from test_app_services import _FIXTURE_CASE_ID, _write_policy_pair

from rossmann_forecasting.app.api import create_app
from rossmann_forecasting.app.artifacts import CANONICAL_RUNS
from rossmann_forecasting.app.contracts import ArtifactSelector, Phase
from rossmann_forecasting.app.services import ApplicationServices
from rossmann_forecasting.inventory.simulation import (
    POLICY_IDS,
    POLICY_SUMMARY_SCHEMA,
    POLICY_TARGET_SCHEMA,
)


@pytest.fixture
def integration_store(tmp_path) -> FixtureStore:
    return FixtureStore(tmp_path)


def _write_uncertainty_paths(store: FixtureStore) -> None:
    daily_schema = _FIXTURE_SCHEMAS[ArtifactSelector.PHASE8_DAILY_INTERVALS]
    daily_rows = []
    for date_text, horizon, interval_kind, available in (
        ("2015-06-20", 1, "raw", True),
        ("2015-06-22", 3, "synthetic-unavailable", False),
    ):
        row = {field.name: _sample_arrow_value(field) for field in daily_schema}
        row.update(
            {
                "fit_id": "B",
                "Store": 1,
                "forecast_origin": pd.Timestamp("2015-06-19"),
                "Date": pd.Timestamp(date_text),
                "horizon": horizon,
                "interval_kind": interval_kind,
                "actual_sales": 9_999_999.0,
                "assessment_source_open": 0.0,
                "available": available,
                "unavailable_reason": None if available else "insufficient_tail_sample",
            }
        )
        if not available:
            row.update({"lower": None, "upper": None, "width": None})
        daily_rows.append(row)
    daily_path = _artifact_path(store, ArtifactSelector.PHASE8_DAILY_INTERVALS)
    pq.write_table(pa.Table.from_pylist(daily_rows, schema=daily_schema), daily_path)
    store.refresh_output(ArtifactSelector.PHASE8_DAILY_INTERVALS)

    cumulative_schema = _FIXTURE_SCHEMAS[ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY]
    cumulative_rows = []
    for k, complete in ((1, True), (2, False)):
        row = {field.name: _sample_arrow_value(field) for field in cumulative_schema}
        row.update(
            {
                "fit_id": "B",
                "Store": 1,
                "forecast_origin": pd.Timestamp("2015-06-19"),
                "k": k,
                "p": 0.95 if k == 1 else 0.975,
                "issued_prefix_complete": complete,
            }
        )
        if not complete:
            row.update(
                {
                    "D_k": None,
                    "q_p_signed": None,
                    "U_k": None,
                    "SafetyStock_k": None,
                    "Target_k": None,
                }
            )
        cumulative_rows.append(row)
    cumulative_path = _artifact_path(store, ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY)
    pq.write_table(pa.Table.from_pylist(cumulative_rows, schema=cumulative_schema), cumulative_path)
    store.refresh_output(ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY)


def _write_forecast_paths(store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    path = _artifact_path(store, selector)
    table = pq.read_table(path)
    rows = table.to_pylist()
    later_path = dict(rows[0])
    later_path.update(
        {
            "Date": pd.Timestamp("2015-06-22"),
            "horizon": 3,
            "raw_forecast": 31.0,
            "operational_forecast": 31.0,
            "actual_sales": 9_999_999.0,
        }
    )
    pq.write_table(pa.Table.from_pylist(rows + [later_path], schema=table.schema), path)
    store.refresh_output(selector)


def _add_second_policy_store(store: FixtureStore) -> None:
    summary_selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    summary_path = _artifact_path(store, summary_selector)
    summary_rows = pq.read_table(summary_path).to_pylist()
    second_store_rows = []
    for source in summary_rows:
        row = dict(source)
        row["Store"] = 2
        cost = 300.0 if row["policy_id"] == POLICY_IDS[0] else 400.0
        row.update(
            {
                "SimulatedHoldingPlusShortfallCost": cost,
                "SimulatedHoldingCost": cost,
                "holding_cost_total": cost,
            }
        )
        second_store_rows.append(row)
    pq.write_table(
        pa.Table.from_pylist(summary_rows + second_store_rows, schema=POLICY_SUMMARY_SCHEMA),
        summary_path,
    )
    store.refresh_output(summary_selector)

    target_selector = ArtifactSelector.PHASE10_POLICY_TARGETS
    target_path = _artifact_path(store, target_selector)
    target_rows = pq.read_table(target_path).to_pylist()
    second_store_rows = []
    for source in target_rows:
        row = dict(source)
        row["Store"] = 2
        second_store_rows.append(row)
    pq.write_table(
        pa.Table.from_pylist(target_rows + second_store_rows, schema=POLICY_TARGET_SCHEMA),
        target_path,
    )
    store.refresh_output(target_selector)


def _write_history_with_boundary_sentinels(store: FixtureStore) -> None:
    path = store.root / "data" / "interim" / "train.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([1, 1, 1, 2], type=pa.int64()),
                "Date": pa.array(
                    [
                        pd.Timestamp("2015-06-20"),
                        pd.Timestamp("2015-07-03"),
                        pd.Timestamp("2015-07-04"),
                        pd.Timestamp("2015-07-03"),
                    ],
                    type=pa.timestamp("ns"),
                ),
                "Sales": pa.array([100, 200, 9_999_999, 300], type=pa.int64()),
                "Open": pa.array([1, 1, 0, 1], type=pa.int64()),
                "Customers": pa.array([10, 20, 999_999, 30], type=pa.int64()),
            }
        ),
        path,
    )


def _refresh_downstream_lineage(store: FixtureStore) -> None:
    phase7 = store.expected_runs[Phase.PHASE7]
    phase8 = store.manifests[Phase.PHASE8]
    phase8["inputs"]["selection_manifest_sha256"] = phase7.manifest_sha256
    store.refresh_manifest(Phase.PHASE8)

    phase9_identity = CANONICAL_RUNS[Phase.PHASE9]
    bindings_path = (
        store.root / phase9_identity.manifest_relative_path.parent / "upstream_bindings.json"
    )
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    bindings["phase7"]["selection_manifest_sha256"] = phase7.manifest_sha256
    bindings["phase8"]["manifest_sha256"] = store.expected_runs[Phase.PHASE8].manifest_sha256
    canonical_payload = {
        key: value
        for key, value in bindings.items()
        if key not in {"canonical_sha256", "created_at_utc", "run_id"}
    }
    canonical_sha = hashlib.sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    bindings["canonical_sha256"] = canonical_sha
    binding_bytes = json.dumps(bindings, indent=2, sort_keys=True).encode("utf-8")
    bindings_path.write_bytes(binding_bytes)

    phase9 = store.manifests[Phase.PHASE9]
    phase9["inputs"]["phase7_selection_manifest_sha256"] = phase7.manifest_sha256
    phase9["inputs"]["phase8_manifest_sha256"] = store.expected_runs[Phase.PHASE8].manifest_sha256
    phase9["upstream_bindings"].update(
        {
            "sha256": hashlib.sha256(binding_bytes).hexdigest(),
            "canonical_sha256": canonical_sha,
        }
    )
    store.refresh_manifest(Phase.PHASE9)

    phase10 = store.manifests[Phase.PHASE10]
    phase10["inputs"]["phase7_selection_manifest_sha256"] = phase7.manifest_sha256
    phase10["inputs"]["phase8_manifest_sha256"] = store.expected_runs[Phase.PHASE8].manifest_sha256
    phase10["inputs"]["phase9_manifest_sha256"] = store.expected_runs[Phase.PHASE9].manifest_sha256
    store.refresh_manifest(Phase.PHASE10)


def _assert_fixture_provenance(payload: dict[str, object], store: FixtureStore) -> None:
    entries = payload["provenance"]
    if isinstance(entries, dict):
        entries = [entries]
    for provenance in entries:
        identity = store.expected_runs[Phase(provenance["phase"])]
        assert provenance["run_id"] == identity.run_id
        assert provenance["manifest_sha256"] == identity.manifest_sha256
        assert len(provenance["output_sha256"]) == 64


def test_process_health_does_not_require_canonical_artifacts() -> None:
    class NoArtifactServices:
        def __getattr__(self, name: str):
            pytest.fail(f"health inspected an artifact through service method {name}")

    with TestClient(create_app(NoArtifactServices())) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "local_read_only"}


def test_http_services_and_verified_fixture_artifacts_form_one_deterministic_chain(
    integration_store: FixtureStore,
) -> None:
    _write_policy_pair(integration_store, baseline_cost=100.0, forecast_cost=150.0)
    _add_second_policy_store(integration_store)
    _write_forecast_paths(integration_store)
    _write_uncertainty_paths(integration_store)
    _refresh_downstream_lineage(integration_store)
    _write_history_with_boundary_sentinels(integration_store)

    reader = integration_store.reader()
    trusted_paths = []
    original_trusted_file = reader._trusted_file

    def allowlisted_trusted_file(relative, selector, missing_reason):
        assert "ledger" not in relative.as_posix().lower()
        trusted_paths.append(relative)
        return original_trusted_file(relative, selector, missing_reason)

    reader._trusted_file = allowlisted_trusted_file
    application = create_app(ApplicationServices(reader))
    requests = (
        ("/health", {}),
        ("/api/v1/catalog", {}),
        ("/api/v1/forecasts", {"store_id": 1, "forecast_origin": "2015-06-19"}),
        (
            "/api/v1/uncertainty",
            {"store_id": 1, "forecast_origin": "2015-06-19", "fit_id": "B"},
        ),
        (
            "/api/v1/model-comparison",
            {
                "candidate_id": "global_lightgbm_gbdt_regression_l1",
                "metric": "mae",
                "population": "standalone",
            },
        ),
        ("/api/v1/inventory", {"case_id": _FIXTURE_CASE_ID}),
        (
            "/api/v1/history",
            {"store_id": 1, "start_date": "2015-06-20", "end_date": "2015-07-03"},
        ),
    )
    with TestClient(application) as client:
        response_pairs = [
            (client.get(path, params=params), client.get(path, params=params))
            for path, params in requests
        ]
        store_filtered = client.get(
            "/api/v1/inventory", params={"case_id": _FIXTURE_CASE_ID, "store_id": 1}
        )

    first = [pair[0] for pair in response_pairs]
    second = [pair[1] for pair in response_pairs]
    assert all(response.status_code == 200 for response in first + second), [
        (path, response.status_code, response.text)
        for (path, _), response in zip(requests, first, strict=True)
        if response.status_code != 200
    ]
    assert [response.content for response in first] == [response.content for response in second]
    payloads = [response.json() for response in first]
    for payload in payloads:
        json.dumps(payload, allow_nan=False)

    assert payloads[0] == {"status": "ok", "mode": "local_read_only"}
    catalog = payloads[1]
    assert catalog["selectors"][-1] == ArtifactSelector.HISTORICAL_SALES.value
    assert all("ledger" not in selector for selector in catalog["selectors"])
    resource_levels = {item["selector"]: item["validation_level"] for item in catalog["resources"]}
    assert resource_levels[ArtifactSelector.PHASE9_SCENARIO_CATALOG.value] == "output_verified"
    assert resource_levels[ArtifactSelector.PHASE10_POLICY_SUMMARY.value] == "manifest_validated"
    assert _FIXTURE_CASE_ID in catalog["inventory_case_ids"]

    forecasts = payloads[2]
    assert [point["horizon"] for point in forecasts["points"]] == [1, 3]
    assert [point["date"] for point in forecasts["points"]] == ["2015-06-20", "2015-06-22"]
    assert all(key not in json.dumps(forecasts) for key in ("actual_sales", "source_open"))
    _assert_fixture_provenance(forecasts, integration_store)

    uncertainty = payloads[3]
    assert [row["date"] for row in uncertainty["daily_intervals"]] == [
        "2015-06-20",
        "2015-06-22",
    ]
    assert uncertainty["daily_intervals"][1]["lower"] is None
    assert uncertainty["daily_intervals"][1]["unavailable_reason"] == "insufficient_tail_sample"
    assert [row["prefix_days"] for row in uncertainty["cumulative_uncertainty"]] == [1, 2]
    assert uncertainty["cumulative_uncertainty"][1]["target_value"] is None
    assert "assessment_source_open" not in json.dumps(uncertainty)
    _assert_fixture_provenance(uncertainty, integration_store)

    comparison = payloads[4]
    assert comparison["rows"][0]["population"] == "standalone"
    assert comparison["rows"][0]["value"] == 12.5
    assert comparison["rows"][0]["numerator"] == 12.5
    assert comparison["rows"][0]["denominator"] == 1.0
    _assert_fixture_provenance(comparison, integration_store)

    inventory = payloads[5]
    assert [
        (pair["store_id"], pair["forecast_minus_baseline_cost"])
        for pair in inventory["policy_pairs"]
    ] == [
        (1, 50.0),
        (2, 100.0),
    ]
    filtered = store_filtered.json()
    assert [pair["store_id"] for pair in filtered["policy_pairs"]] == [1]
    assert filtered["case_level_comparisons"] == inventory["case_level_comparisons"]
    json.dumps(filtered, allow_nan=False)
    _assert_fixture_provenance(inventory, integration_store)

    history = payloads[6]
    assert all(set(row) == {"store_id", "date", "sales", "open"} for row in history["rows"])
    assert [row["date"] for row in history["rows"]] == ["2015-06-20", "2015-07-03"]
    assert "999999" not in json.dumps(history)
    assert trusted_paths


def test_http_inventory_keeps_incomplete_pair_unavailable(integration_store: FixtureStore) -> None:
    _write_policy_pair(
        integration_store,
        forecast_episode_complete=False,
        forecast_episode_reason="missing_consumption",
    )
    with TestClient(create_app(ApplicationServices(integration_store.reader()))) as client:
        response = client.get(
            "/api/v1/inventory",
            params={"case_id": _FIXTURE_CASE_ID, "store_id": 1},
        )

    assert response.status_code == 200
    pair = response.json()["policy_pairs"][0]
    assert pair["comparable"] is False
    assert pair["forecast_minus_baseline_cost"] is None
    assert pair["difference_unavailable_reason"] == "missing_consumption"
    json.dumps(response.json(), allow_nan=False)


def test_empty_filtered_comparison_is_a_json_success(integration_store: FixtureStore) -> None:
    with TestClient(create_app(ApplicationServices(integration_store.reader()))) as client:
        response = client.get(
            "/api/v1/model-comparison",
            params={"candidate_id": "no-such-saved-candidate"},
        )

    assert response.status_code == 200
    assert response.json()["state"] == "empty"
    assert response.json()["rows"] == []
    json.dumps(response.json(), allow_nan=False)


def test_cross_cutoff_http_history_rejects_before_trusted_source_access(
    integration_store: FixtureStore,
) -> None:
    reader = integration_store.reader()
    accessed = []

    def fail_on_trusted_file(relative, selector, missing_reason):
        accessed.append(relative)
        pytest.fail("cross-cutoff history request reached the M1 trusted-path boundary")

    reader._trusted_file = fail_on_trusted_file
    with TestClient(create_app(ApplicationServices(reader))) as client:
        response = client.get(
            "/api/v1/history",
            params={"store_id": 1, "start_date": "2015-07-03", "end_date": "2015-07-04"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_artifact_request"
    assert accessed == []


def test_http_catalog_rejects_incompatible_phase10_lineage(integration_store: FixtureStore) -> None:
    inputs = integration_store.manifests[Phase.PHASE10]["inputs"]
    assert isinstance(inputs, dict)
    inputs["phase9_run_id"] = "untrusted-lineage-sentinel"
    integration_store.refresh_manifest(Phase.PHASE10)

    with TestClient(create_app(ApplicationServices(integration_store.reader()))) as client:
        response = client.get("/api/v1/catalog")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "artifact_integrity_error"
    assert "untrusted-lineage-sentinel" not in response.text
    assert "manifest" not in response.text.lower()
