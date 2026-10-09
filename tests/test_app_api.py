"""Fixture-backed HTTP contract tests for the Phase 11 demo adapter."""

from __future__ import annotations

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
from test_app_services import (
    _FIXTURE_CASE_ID,
    _write_policy_pair,
)

from rossmann_forecasting.app.api import create_app
from rossmann_forecasting.app.artifacts import MAX_STORE_ID
from rossmann_forecasting.app.contracts import (
    ArtifactErrorCode,
    ArtifactSelector,
    ArtifactUnavailableError,
    ForecastQuery,
    InvalidArtifactRequestError,
    UnavailableReason,
)
from rossmann_forecasting.app.services import ApplicationServices
from rossmann_forecasting.inventory.simulation import (
    POLICY_SUMMARY_SCHEMA,
)


@pytest.fixture
def fixture_store(tmp_path) -> FixtureStore:
    return FixtureStore(tmp_path)


def _client(store: FixtureStore, *, services=None, raise_server_exceptions: bool = False):
    selected_services = services if services is not None else ApplicationServices(store.reader())
    return TestClient(
        create_app(selected_services), raise_server_exceptions=raise_server_exceptions
    )


def _error_payload(response, status_code: int, code: str) -> dict[str, object]:
    assert response.status_code == status_code
    payload = response.json()
    assert set(payload) == {"error"}
    assert set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code
    assert isinstance(payload["error"]["message"], str)
    return payload


def test_health_is_fixed_and_does_not_call_services(fixture_store: FixtureStore) -> None:
    class NeverCalledServices:
        def __getattr__(self, name: str):
            pytest.fail(f"health touched application services through {name}")

    with _client(fixture_store, services=NeverCalledServices()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "local_read_only"}


def test_app_exposes_only_the_seven_frozen_get_routes(fixture_store: FixtureStore) -> None:
    application = create_app(ApplicationServices(fixture_store.reader()))

    routes = {
        (route.path, method) for route in application.routes for method in (route.methods or set())
    }

    assert routes == {
        ("/health", "GET"),
        ("/api/v1/catalog", "GET"),
        ("/api/v1/forecasts", "GET"),
        ("/api/v1/uncertainty", "GET"),
        ("/api/v1/model-comparison", "GET"),
        ("/api/v1/inventory", "GET"),
        ("/api/v1/history", "GET"),
    }


def test_catalog_preserves_reader_validation_levels_and_json(fixture_store: FixtureStore) -> None:
    with _client(fixture_store) as client:
        response = client.get("/api/v1/catalog")

    assert response.status_code == 200
    payload = response.json()
    resources = {item["selector"]: item for item in payload["resources"]}
    assert (
        resources[ArtifactSelector.PHASE9_SCENARIO_CATALOG.value]["validation_level"]
        == "output_verified"
    )
    assert (
        resources[ArtifactSelector.PHASE10_POLICY_SUMMARY.value]["validation_level"]
        == "manifest_validated"
    )
    assert all("ledger" not in selector for selector in payload["selectors"])
    json.dumps(payload, allow_nan=False)


def test_forecasts_return_only_approved_issuance_fields(fixture_store: FixtureStore) -> None:
    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/forecasts",
            params={"store_id": 1, "forecast_origin": "2015-06-19"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "available"
    assert len(payload["points"]) == 1
    point = payload["points"][0]
    assert point["date"] == "2015-06-20"
    assert "actual_sales" not in point
    assert "source_open" not in point
    assert all("assessment" not in name for name in point)
    json.dumps(payload, allow_nan=False)


def test_uncertainty_keeps_daily_and_cumulative_unavailable_values(
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
        if selector is ArtifactSelector.PHASE8_DAILY_INTERVALS:
            row["Date"] = pd.Timestamp("2015-06-20")
            row["available"] = False
            row["unavailable_reason"] = "insufficient_tail_sample"
            row["lower"] = None
            row["upper"] = None
            row["width"] = None
        else:
            row["issued_prefix_complete"] = False
            row["issued_prefix_unavailable_reason"] = None
            for column in ("D_k", "q_p_signed", "U_k", "SafetyStock_k", "Target_k"):
                row[column] = None
        path = _artifact_path(fixture_store, selector)
        pq.write_table(pa.Table.from_pylist([row], schema=schema), path)
        fixture_store.refresh_output(selector)

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/uncertainty",
            params={"store_id": 1, "forecast_origin": "2015-06-19", "fit_id": "B"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["daily_intervals"][0]["available"] is False
    assert payload["daily_intervals"][0]["lower"] is None
    assert payload["daily_intervals"][0]["unavailable_reason"] == "insufficient_tail_sample"
    assert payload["cumulative_uncertainty"][0]["issued_prefix_complete"] is False
    assert payload["cumulative_uncertainty"][0]["target_value"] is None
    assert "interpretation" in payload
    assert "actual_sales" not in response.text
    assert "assessment_source_open" not in response.text
    json.dumps(payload, allow_nan=False)


def test_model_comparison_preserves_saved_producer_values(fixture_store: FixtureStore) -> None:
    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/model-comparison",
            params={"candidate_id": "global_lightgbm_gbdt_regression_l1", "metric": "mae"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"][0]["population"] == "standalone"
    assert payload["rows"][0]["value"] == 12.5
    assert payload["rows"][0]["numerator"] == 12.5
    assert payload["rows"][0]["denominator"] == 1.0
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize(
    ("baseline_cost", "forecast_cost", "expected"),
    [(100.0, 150.0, 50.0), (150.0, 100.0, -50.0)],
)
def test_inventory_preserves_signed_costs_and_case_wide_aggregates(
    fixture_store: FixtureStore, baseline_cost: float, forecast_cost: float, expected: float
) -> None:
    _write_policy_pair(fixture_store, baseline_cost=baseline_cost, forecast_cost=forecast_cost)

    with _client(fixture_store) as client:
        whole = client.get("/api/v1/inventory", params={"case_id": _FIXTURE_CASE_ID})
        one_store = client.get(
            "/api/v1/inventory", params={"case_id": _FIXTURE_CASE_ID, "store_id": 1}
        )

    assert whole.status_code == one_store.status_code == 200
    all_pairs, selected = whole.json(), one_store.json()
    assert all_pairs["policy_pairs"][0]["forecast_minus_baseline_cost"] == expected
    assert all_pairs["policy_pairs"][0]["comparable"] is True
    assert selected["policy_pairs"][0]["forecast_minus_baseline_cost"] == expected
    assert selected["case_level_comparisons"] == all_pairs["case_level_comparisons"]
    json.dumps(selected, allow_nan=False)


def test_inventory_preserves_an_incomplete_pair_with_null_difference(
    fixture_store: FixtureStore,
) -> None:
    _write_policy_pair(
        fixture_store,
        forecast_episode_complete=False,
        forecast_episode_reason="missing_consumption",
    )

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/inventory",
            params={"case_id": _FIXTURE_CASE_ID, "store_id": 1},
        )

    assert response.status_code == 200
    pair = response.json()["policy_pairs"][0]
    assert pair["comparable"] is False
    assert pair["forecast_minus_baseline_cost"] is None
    assert pair["difference_unavailable_reason"] == "missing_consumption"
    assert pair["forecast"]["target_available"] is True
    assert pair["forecast"]["episode_complete"] is False
    json.dumps(response.json(), allow_nan=False)


def test_history_exposes_only_bounded_cutoff_safe_fields(fixture_store: FixtureStore) -> None:
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

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/history",
            params={"store_id": 1, "start_date": "2015-07-03", "end_date": "2015-07-03"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["date"] == "2015-07-03"
    assert "Customers" not in response.text
    assert "2015-07-04" not in response.text
    json.dumps(payload, allow_nan=False)


def test_valid_history_query_with_no_rows_is_a_successful_empty_view(
    fixture_store: FixtureStore,
) -> None:
    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([1], type=pa.int64()),
                "Date": pa.array([pd.Timestamp("2015-07-03")], type=pa.timestamp("ns")),
                "Sales": pa.array([100], type=pa.int64()),
                "Open": pa.array([1], type=pa.int64()),
            }
        ),
        source,
    )

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/history",
            params={"store_id": 2, "start_date": "2015-07-03", "end_date": "2015-07-03"},
        )

    assert response.status_code == 200
    assert response.json()["state"] == "empty"
    assert response.json()["rows"] == []


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/api/v1/forecasts", {}),
        ("/api/v1/uncertainty", {"store_id": 1, "forecast_origin": "2015-06-19"}),
        ("/api/v1/model-comparison", {}),
        ("/api/v1/inventory", {}),
        ("/api/v1/history", {"store_id": 1}),
    ],
)
def test_missing_required_query_fields_use_sanitized_422(
    fixture_store: FixtureStore, path: str, params: dict[str, object]
) -> None:
    with _client(fixture_store) as client:
        response = client.get(path, params=params)

    _error_payload(response, 422, ArtifactErrorCode.INVALID_REQUEST.value)
    assert "detail" not in response.text


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/api/v1/forecasts", {"store_id": "secret", "forecast_origin": "2015-06-19"}),
        ("/api/v1/forecasts", {"store_id": MAX_STORE_ID + 1, "forecast_origin": "2015-06-19"}),
        ("/api/v1/forecasts", {"store_id": 1, "forecast_origin": "2015-06-32"}),
        ("/api/v1/forecasts", {"store_id": 1, "forecast_origin": "20150619"}),
        ("/api/v1/history", {"store_id": 1, "start_date": "2015-07-03", "end_date": "2015-07-04"}),
        ("/api/v1/model-comparison", {"candidate_id": "mae", "limit": 501}),
        ("/api/v1/model-comparison", {"limit": 50}),
        (
            "/api/v1/model-comparison",
            {"validation_window": "wrong-window", "metric": "mae"},
        ),
        ("/api/v1/uncertainty", {"store_id": 1, "forecast_origin": "2015-06-19", "fit_id": "A"}),
        ("/api/v1/inventory", {"case_id": "../../secret"}),
    ],
)
def test_bad_bounds_and_selectors_return_sanitized_422(
    fixture_store: FixtureStore, path: str, params: dict[str, object]
) -> None:
    with _client(fixture_store) as client:
        response = client.get(path, params=params)

    payload = _error_payload(response, 422, ArtifactErrorCode.INVALID_REQUEST.value)
    assert "secret" not in response.text
    assert "wrong-window" not in response.text
    assert payload["error"]["message"] == str(
        InvalidArtifactRequestError(ArtifactSelector.PHASE7_FORECASTS)
    )


def test_invalid_forecast_origin_fails_before_artifact_read(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    class NoForecastServices(ApplicationServices):
        forecast_calls = 0

        def forecast_issuance(self, query: ForecastQuery):
            self.forecast_calls += 1
            return super().forecast_issuance(query)

    reader = fixture_store.reader()
    manifest_reads = []
    trusted_file_reads = []
    original_read_manifest = reader._read_manifest
    original_trusted_file = reader._trusted_file

    def read_manifest(*args, **kwargs):
        manifest_reads.append(args)
        return original_read_manifest(*args, **kwargs)

    def trusted_file(*args, **kwargs):
        trusted_file_reads.append(args)
        return original_trusted_file(*args, **kwargs)

    monkeypatch.setattr(reader, "_read_manifest", read_manifest)
    monkeypatch.setattr(reader, "_trusted_file", trusted_file)
    service = NoForecastServices(reader)
    client = _client(fixture_store, services=service)
    response = client.get(
        "/api/v1/forecasts", params={"store_id": 1, "forecast_origin": "2015-06-06"}
    )

    _error_payload(response, 422, ArtifactErrorCode.INVALID_REQUEST.value)
    assert service.forecast_calls == 1
    assert manifest_reads == []
    assert trusted_file_reads == []


def test_query_names_are_closed_and_repeated_keys_are_rejected(
    fixture_store: FixtureStore,
) -> None:
    with _client(fixture_store) as client:
        extra = client.get(
            "/api/v1/forecasts",
            params={"store_id": 1, "forecast_origin": "2015-06-19", "selector": "secret"},
        )
        repeated = client.get("/api/v1/forecasts?store_id=1&store_id=2&forecast_origin=2015-06-19")
        unknown_path = client.get("/api/v1/files?path=secret")

    _error_payload(extra, 422, ArtifactErrorCode.INVALID_REQUEST.value)
    _error_payload(repeated, 422, ArtifactErrorCode.INVALID_REQUEST.value)
    _error_payload(unknown_path, 404, "not_found")
    assert "secret" not in extra.text + unknown_path.text


def test_cross_cutoff_history_is_rejected_before_source_path_access(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = fixture_store.reader()
    monkeypatch.setattr(
        reader,
        "_trusted_file",
        lambda *args, **kwargs: pytest.fail("history path accessed before cutoff validation"),
    )
    with _client(fixture_store, services=ApplicationServices(reader)) as client:
        response = client.get(
            "/api/v1/history",
            params={"store_id": 1, "start_date": "2015-07-03", "end_date": "2015-07-04"},
        )

    _error_payload(response, 422, ArtifactErrorCode.INVALID_REQUEST.value)


def test_missing_canonical_output_maps_to_503(fixture_store: FixtureStore) -> None:
    path = _artifact_path(fixture_store, ArtifactSelector.PHASE7_FORECASTS)
    path.unlink()

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/forecasts",
            params={"store_id": 1, "forecast_origin": "2015-06-19"},
        )

    _error_payload(response, 503, ArtifactErrorCode.UNAVAILABLE.value)
    assert str(fixture_store.root) not in response.text


def test_hash_failure_maps_to_503_without_revealing_paths(fixture_store: FixtureStore) -> None:
    path = _artifact_path(fixture_store, ArtifactSelector.PHASE7_FORECASTS)
    path.write_bytes(path.read_bytes() + b"corruption")

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/forecasts",
            params={"store_id": 1, "forecast_origin": "2015-06-19"},
        )

    _error_payload(response, 503, ArtifactErrorCode.INTEGRITY.value)
    assert str(fixture_store.root) not in response.text


def test_schema_failure_maps_to_503(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    path = _artifact_path(fixture_store, selector)
    values = pq.read_table(path).to_pydict()
    values["Store"] = [str(value) for value in values["Store"]]
    pq.write_table(pa.table(values), path)
    fixture_store.refresh_output(selector)

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/forecasts",
            params={"store_id": 1, "forecast_origin": "2015-06-19"},
        )

    _error_payload(response, 503, ArtifactErrorCode.SCHEMA.value)


def test_duplicate_canonical_keys_map_to_503(fixture_store: FixtureStore) -> None:
    _write_policy_pair(fixture_store)
    selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    path = _artifact_path(fixture_store, selector)
    row = pq.ParquetFile(path).read().to_pylist()[0]
    pq.write_table(
        pa.Table.from_pylist([row, row], schema=POLICY_SUMMARY_SCHEMA),
        path,
    )
    fixture_store.refresh_output(selector)

    with _client(fixture_store) as client:
        response = client.get(
            "/api/v1/inventory",
            params={"case_id": _FIXTURE_CASE_ID, "store_id": 1},
        )

    _error_payload(response, 503, ArtifactErrorCode.DUPLICATE_KEY.value)


def test_artifact_error_code_mapping_is_centralized(fixture_store: FixtureStore) -> None:
    class BrokenServices:
        def catalog(self):
            raise ArtifactUnavailableError(
                ArtifactSelector.PHASE9_SCENARIO_CATALOG, UnavailableReason.MISSING_ARTIFACT
            )

    with _client(fixture_store, services=BrokenServices()) as client:
        response = client.get("/api/v1/catalog")

    _error_payload(response, 503, ArtifactErrorCode.UNAVAILABLE.value)


def test_unexpected_errors_are_fixed_and_do_not_leak_exception_text(
    fixture_store: FixtureStore,
) -> None:
    class BrokenServices:
        def catalog(self):
            raise RuntimeError("C:\\private\\secret-path\\manifest.json")

    with _client(fixture_store, services=BrokenServices()) as client:
        response = client.get("/api/v1/catalog")

    payload = _error_payload(response, 500, "internal_error")
    assert "secret-path" not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text
    assert "C:\\" not in response.text
    assert payload["error"]["message"] == "An internal error occurred."


def test_mutation_methods_never_dispatch_and_do_not_change_fixture_outputs(
    fixture_store: FixtureStore,
) -> None:
    outputs = {
        path: (path.stat().st_size, path.stat().st_mtime_ns)
        for path in fixture_store.root.rglob("*")
        if path.is_file()
    }
    with _client(fixture_store) as client:
        responses = [
            client.request(method, "/api/v1/history?store_id=1")
            for method in ("POST", "PUT", "PATCH", "DELETE")
        ]
    assert all(response.status_code == 405 for response in responses)
    assert all(response.json()["error"]["code"] == "method_not_allowed" for response in responses)
    assert outputs == {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in outputs}


def test_405_preserves_framework_allow_header_without_dispatching_services(
    fixture_store: FixtureStore,
) -> None:
    class NeverCalledServices:
        def __getattr__(self, name: str):
            pytest.fail(f"unsupported method dispatched to application service {name}")

    with _client(fixture_store, services=NeverCalledServices()) as client:
        health = client.post("/health")
        catalog = client.post("/api/v1/catalog")
        missing = client.post("/not-a-route")

    for response in (health, catalog):
        assert response.status_code == 405
        assert response.headers["allow"] == "GET"
        assert response.json() == {
            "error": {
                "code": "method_not_allowed",
                "message": "The requested HTTP method is not allowed.",
            }
        }

    assert missing.status_code == 404
    assert missing.json() == {
        "error": {"code": "not_found", "message": "The requested endpoint does not exist."}
    }


def test_response_serialization_is_deterministic_and_documentation_routes_are_off(
    fixture_store: FixtureStore,
) -> None:
    with _client(fixture_store) as client:
        first = client.get("/api/v1/catalog")
        second = client.get("/api/v1/catalog")
        docs = client.get("/docs")
        schema = client.get("/openapi.json")

    assert first.content == second.content
    _error_payload(docs, 404, "not_found")
    _error_payload(schema, 404, "not_found")
    json.dumps(first.json(), allow_nan=False)
