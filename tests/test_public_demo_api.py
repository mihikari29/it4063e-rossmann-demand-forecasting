"""In-process HTTP contract tests over generated controlled-synthetic fixtures only."""

from __future__ import annotations

import builtins
import hashlib
import socket
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rossmann_forecasting.app import demo_api, demo_bundle
from rossmann_forecasting.app.demo_provider import DemoProfile, SyntheticProvenance
from rossmann_forecasting.app.demo_services import DemoServices
from rossmann_forecasting.app.services import ApplicationServices

_LABEL = "CONTROLLED SYNTHETIC DEMONSTRATION \u2014 NOT OBSERVED ROSSMANN DATA"
_ROUTES = {
    "/health",
    "/api/v1/catalog",
    "/api/v1/history",
    "/api/v1/forecasts",
    "/api/v1/uncertainty",
    "/api/v1/model-comparison",
    "/api/v1/inventory",
}


@pytest.fixture(scope="module")
def release_bytes() -> tuple[bytes, bytes]:
    return demo_bundle.generate_release_bytes(Path.cwd())


@pytest.fixture
def pinned_release(tmp_path: Path, release_bytes: tuple[bytes, bytes]) -> tuple[Path, str, Path]:
    repository = tmp_path / "fixture-repository"
    release_dir = repository / "artifacts" / "public_demo" / demo_bundle.RELEASE_ID
    release_dir.mkdir(parents=True)
    bundle_bytes, manifest_bytes = release_bytes
    bundle_path = release_dir / demo_bundle.BUNDLE_FILENAME
    manifest_path = release_dir / demo_bundle.MANIFEST_FILENAME
    bundle_path.write_bytes(bundle_bytes)
    manifest_path.write_bytes(manifest_bytes)
    pin = hashlib.sha256(manifest_bytes).hexdigest()
    return repository, pin, bundle_path


@pytest.fixture
def demo_client(pinned_release: tuple[Path, str, Path]):
    repository, pin, _ = pinned_release
    app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=repository,
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _assert_success(response, view_id: str) -> dict:
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"evidence_label", "data", "provenance"}
    assert body["evidence_label"] == _LABEL
    assert body["provenance"]["evidence_kind"] == "controlled_synthetic_demo"
    assert body["provenance"]["view_id"] == view_id
    assert "provenance" not in body["data"]
    return body


def test_factory_requires_explicit_synthetic_profile_and_lowercase_manifest_pin(
    pinned_release: tuple[Path, str, Path],
) -> None:
    repository, pin, _ = pinned_release
    with pytest.raises(TypeError):
        demo_api.create_demo_app(expected_manifest_sha256=pin)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        demo_api.create_demo_app(profile=DemoProfile.CONTROLLED_SYNTHETIC)  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        demo_api.create_demo_app(
            profile="controlled_synthetic_demo",  # type: ignore[arg-type]
            expected_manifest_sha256=pin,
            repository_root=repository,
        )
    for invalid_pin in ("", "A" * 64, "0" * 63, "g" * 64, 123):
        with pytest.raises(ValueError):
            demo_api.create_demo_app(
                profile=DemoProfile.CONTROLLED_SYNTHETIC,
                expected_manifest_sha256=invalid_pin,  # type: ignore[arg-type]
                repository_root=repository,
            )
    with pytest.raises(TypeError):
        demo_api.create_demo_app(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=str(repository),  # type: ignore[arg-type]
        )


def test_module_has_no_global_app_and_disables_generated_documentation(
    pinned_release: tuple[Path, str, Path],
) -> None:
    repository, pin, _ = pinned_release
    assert not hasattr(demo_api, "app")
    app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=repository,
    )
    routes = {route.path: route for route in app.routes}
    assert set(routes) == _ROUTES
    assert all(routes[path].methods == {"GET"} for path in _ROUTES)
    with TestClient(app) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404


def test_health_is_process_liveness_even_when_release_is_missing(tmp_path: Path) -> None:
    app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256="0" * 64,
        repository_root=tmp_path / "empty-repository",
    )
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "semantics": "process_liveness_only",
        }
        assert "ready" not in response.text.lower()
        unavailable = client.get("/api/v1/catalog")
        assert unavailable.status_code == 503
        assert unavailable.json()["error"]["code"] == "demo_release_unavailable"


def test_missing_synthetic_release_never_falls_back_to_canonical_services(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("canonical services must not be initialized")

    monkeypatch.setattr(ApplicationServices, "__init__", forbidden)
    app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256="0" * 64,
        repository_root=tmp_path / "no-release",
    )
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/catalog").status_code == 503


def test_wrong_pin_and_corrupt_bundle_fail_closed_with_sanitized_503(
    pinned_release: tuple[Path, str, Path],
) -> None:
    repository, pin, bundle_path = pinned_release
    wrong_pin_app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256="0" * 64,
        repository_root=repository,
    )
    with TestClient(wrong_pin_app) as client:
        response = client.get("/api/v1/catalog")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "demo_release_invalid"
    assert str(repository) not in response.text

    bundle_path.write_bytes(bundle_path.read_bytes() + b"tampered")
    corrupt_app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=repository,
    )
    with TestClient(corrupt_app) as client:
        response = client.get("/api/v1/catalog")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "demo_release_invalid"
    assert "tampered" not in response.text


def test_provider_is_opened_once_and_analytical_requests_do_not_retry(
    monkeypatch: pytest.MonkeyPatch,
    pinned_release: tuple[Path, str, Path],
) -> None:
    repository, pin, _ = pinned_release
    original_open = DemoServices.open.__func__
    calls = 0

    def counted_open(cls, **kwargs):
        nonlocal calls
        calls += 1
        return original_open(cls, **kwargs)

    monkeypatch.setattr(DemoServices, "open", classmethod(counted_open))
    app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=repository,
    )
    assert calls == 1
    with TestClient(app) as client:
        assert client.get("/api/v1/catalog").status_code == 200
        assert client.get("/api/v1/catalog").status_code == 200
    assert calls == 1


def test_catalog_returns_verified_typed_data_and_single_top_level_provenance(
    demo_client: TestClient,
) -> None:
    body = _assert_success(demo_client.get("/api/v1/catalog"), "catalog")
    assert body["provenance"]["manifest_sha256"]
    assert body["data"]["bundle_ready"] is True
    assert body["data"]["supported_store_ids"] == [101, 202, 303]
    assert body["data"]["source_declaration"]["rossmann_data_included"] is False
    assert body["data"]["source_declaration"]["model_runs_included"] is False
    assert body["data"]["source_declaration"]["model_execution"] == "none"
    assert len(body["data"]["views"]) == 6


def test_repeated_requests_are_deterministic_and_do_not_share_mutable_results(
    demo_client: TestClient,
) -> None:
    first = demo_client.get("/api/v1/catalog")
    second = demo_client.get("/api/v1/catalog")
    assert first.content == second.content


@pytest.mark.parametrize("store_id", [101, 202, 303])
def test_history_route_preserves_sparse_null_and_zero_values(
    demo_client: TestClient, store_id: int
) -> None:
    body = _assert_success(
        demo_client.get(
            "/api/v1/history",
            params={
                "store_id": str(store_id),
                "start_date": "2015-05-09",
                "end_date": "2015-07-03",
            },
        ),
        "sales_history",
    )
    rows = body["data"]["rows"]
    dates = [row["date"] for row in rows]
    assert dates == sorted(dates)
    if store_id == 101:
        by_date = {row["date"]: row for row in rows}
        assert by_date["2015-05-23"]["sales_value"] == 0
        assert "2015-05-22" not in by_date
    if store_id == 202:
        assert any(row["sales_value"] is None for row in rows)


@pytest.mark.parametrize("store_id", [101, 202, 303])
@pytest.mark.parametrize("origin", ["2015-05-22", "2015-06-05", "2015-06-19"])
def test_forecast_route_serves_saved_store_origin_paths(
    demo_client: TestClient, store_id: int, origin: str
) -> None:
    body = _assert_success(
        demo_client.get(
            "/api/v1/forecasts",
            params={"store_id": str(store_id), "forecast_origin": origin},
        ),
        "forecast_issuance",
    )
    assert len(body["data"]["points"]) == 14
    assert body["data"]["model_execution"] == "none"
    if store_id == 303 and origin == "2015-06-19":
        point = body["data"]["points"][3]
        assert point["raw_forecast_value"] == 13686
        assert point["raw_forecast_available"] is True
        assert point["synthetic_open_eligibility"] == "unknown"
        assert point["operational_forecast_value"] is None
        assert point["operational_forecast_available"] is False


@pytest.mark.parametrize(
    ("store_id", "origin", "fit_id"),
    [
        (store, origin, fit)
        for store in (101, 202, 303)
        for origin, fit in (("2015-06-05", "demo_fit_a"), ("2015-06-19", "demo_fit_b"))
    ],
)
def test_uncertainty_route_accepts_only_saved_fit_pairings(
    demo_client: TestClient, store_id: int, origin: str, fit_id: str
) -> None:
    body = _assert_success(
        demo_client.get(
            "/api/v1/uncertainty",
            params={
                "store_id": str(store_id),
                "forecast_origin": origin,
                "fit_id": fit_id,
            },
        ),
        "forecast_uncertainty",
    )
    assert len(body["data"]["daily_intervals"]) == 28


def test_model_comparison_uses_closed_saved_filters_and_a_500_row_ceiling(
    demo_client: TestClient,
) -> None:
    response = demo_client.get(
        "/api/v1/model-comparison",
        params={"candidate_id": "demo_path_a", "scope": "pooled", "metric": "mae", "limit": "500"},
    )
    body = _assert_success(response, "model_comparison")
    assert len(body["data"]["rows"]) == 1
    assert body["data"]["rows"][0]["value"] == pytest.approx(278.9423076923077)

    maximum = demo_client.get("/api/v1/model-comparison", params={"limit": "500"})
    maximum_body = _assert_success(maximum, "model_comparison")
    assert len(maximum_body["data"]["rows"]) == 69

    empty = demo_client.get(
        "/api/v1/model-comparison",
        params={"candidate_id": "demo_path_a", "scope": "pooled", "store_id": "101"},
    )
    empty_body = _assert_success(empty, "model_comparison")
    assert empty_body["data"]["state"] == "empty"
    assert empty_body["data"]["rows"] == []


@pytest.mark.parametrize(
    "params",
    [
        {"case_id": "synthetic_demo_reference_20150605"},
        {"case_id": "synthetic_demo_adverse_20150605", "store_id": "303"},
    ],
)
def test_inventory_route_supports_both_cases_and_preserves_case_aggregates(
    demo_client: TestClient, params: dict[str, str]
) -> None:
    body = _assert_success(
        demo_client.get("/api/v1/inventory", params=params), "inventory_comparison"
    )
    assert body["data"]["aggregate_scope"] == "all_stores_in_case"
    assert len(body["data"]["case_level_comparisons"]) == 10
    if params["case_id"] == "synthetic_demo_adverse_20150605":
        assert body["data"]["policy_pairs"][0]["comparable"] is False
        assert body["data"]["policy_pairs"][0]["forecast_minus_baseline_cost"] is None
        assert body["data"]["case_level_comparisons"][0]["matched_store_count"] == 2
    else:
        unfiltered = demo_client.get(
            "/api/v1/inventory",
            params={"case_id": "synthetic_demo_reference_20150605"},
        ).json()
        assert (
            body["data"]["case_level_comparisons"] == unfiltered["data"]["case_level_comparisons"]
        )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/history",
        "/api/v1/forecasts",
        "/api/v1/uncertainty",
        "/api/v1/inventory",
    ],
)
def test_routes_reject_missing_required_query_fields(demo_client: TestClient, path: str) -> None:
    assert demo_client.get(path).status_code == 422


@pytest.mark.parametrize(
    "params",
    [
        "store_id=101&start_date=2015-05-09&end_date=2015-05-09&extra=1",
        "store_id=101&store_id=202&start_date=2015-05-09&end_date=2015-05-09",
    ],
)
def test_history_rejects_unknown_or_repeated_query_keys(
    demo_client: TestClient, params: str
) -> None:
    assert demo_client.get(f"/api/v1/history?{params}").status_code == 422


@pytest.mark.parametrize("date_text", ["2015-5-09", "2015/05/09", "2015-02-30", "２０１５-05-09"])
def test_history_rejects_noncanonical_or_invalid_dates(
    demo_client: TestClient, date_text: str
) -> None:
    response = demo_client.get(
        "/api/v1/history",
        params={"store_id": "101", "start_date": date_text, "end_date": "2015-05-09"},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("start_date", "end_date"),
    [("2015-05-09", "2015-07-04"), ("2015-06-01", "2015-05-31")],
)
def test_history_rejects_out_of_release_and_reversed_ranges(
    demo_client: TestClient, start_date: str, end_date: str
) -> None:
    response = demo_client.get(
        "/api/v1/history",
        params={"store_id": "101", "start_date": start_date, "end_date": end_date},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("store_id", ["0", "001", "101.0", "true", "404", "９０１"])
def test_history_rejects_unsupported_and_noncanonical_store_ids(
    demo_client: TestClient, store_id: str
) -> None:
    response = demo_client.get(
        "/api/v1/history",
        params={"store_id": store_id, "start_date": "2015-05-09", "end_date": "2015-05-09"},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("limit", ["0", "01", "1.0", "true", "501", "-1"])
def test_model_comparison_rejects_noncanonical_or_out_of_range_limits(
    demo_client: TestClient, limit: str
) -> None:
    assert demo_client.get("/api/v1/model-comparison", params={"limit": limit}).status_code == 422


def test_unknown_fit_inventory_case_and_comparison_filters_are_rejected(
    demo_client: TestClient,
) -> None:
    assert (
        demo_client.get(
            "/api/v1/uncertainty",
            params={"store_id": "101", "forecast_origin": "2015-06-05", "fit_id": "demo_fit_b"},
        ).status_code
        == 422
    )
    assert demo_client.get("/api/v1/inventory", params={"case_id": "anything"}).status_code == 422
    assert (
        demo_client.get(
            "/api/v1/model-comparison", params={"candidate_id": "canonical_lightgbm"}
        ).status_code
        == 422
    )


def test_request_limits_get_bodies_and_query_lengths(demo_client: TestClient) -> None:
    body_response = demo_client.request("GET", "/api/v1/catalog", content=b"unexpected")
    assert body_response.status_code == 422
    too_long = demo_client.get("/health?x=" + "a" * 4096)
    assert too_long.status_code == 422
    oversized_value = demo_client.get("/api/v1/model-comparison?candidate_id=" + "a" * 129)
    assert oversized_value.status_code == 422


def test_unsupported_method_and_path_are_sanitized_with_allow_header(
    demo_client: TestClient,
) -> None:
    method = demo_client.post("/api/v1/catalog")
    assert method.status_code == 405
    assert method.headers["allow"] == "GET"
    assert method.json()["error"]["code"] == "method_not_allowed"
    missing = demo_client.get("/api/v1/not-an-endpoint")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"
    assert "access-control-allow-origin" not in method.headers


def test_unexpected_errors_are_sanitized(
    monkeypatch: pytest.MonkeyPatch, demo_client: TestClient
) -> None:
    def fail_with_secret(_self):
        raise RuntimeError("secret-path=C:\\private\\bundle.json token=hidden")

    monkeypatch.setattr(DemoServices, "catalog", fail_with_secret)
    response = demo_client.get("/api/v1/catalog")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "An internal error occurred."}
    }
    assert "private" not in response.text
    assert "hidden" not in response.text


def test_requests_after_construction_need_no_files_or_network(
    monkeypatch: pytest.MonkeyPatch, pinned_release: tuple[Path, str, Path]
) -> None:
    repository, pin, _ = pinned_release
    app = demo_api.create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=repository,
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("post-construction filesystem or socket access")

    with TestClient(app) as client:
        monkeypatch.setattr(builtins, "open", forbidden)
        monkeypatch.setattr(Path, "open", forbidden)
        monkeypatch.setattr(socket, "create_connection", forbidden)
        monkeypatch.setattr(socket.socket, "connect", forbidden)
        response = client.get("/api/v1/catalog")
        assert response.status_code == 200


@dataclass(frozen=True)
class _OversizedResult:
    provenance: SyntheticProvenance
    text: str


@dataclass(frozen=True)
class _LargeCollectionResult:
    provenance: SyntheticProvenance
    values: tuple[str, ...]


@dataclass(frozen=True)
class _LargeIntegerResult:
    provenance: SyntheticProvenance
    number: int


def test_serializer_rejects_oversized_values_and_aggregate_results() -> None:
    provenance = SyntheticProvenance(
        release_id="synthetic",
        evidence_kind="controlled_synthetic_demo",
        bundle_sha256="0" * 64,
        manifest_sha256="0" * 64,
        schema_version="1",
        source_kind="authored_fixture_arithmetic",
        view_id="catalog",
        selected_rows=1,
    )
    with pytest.raises(TypeError, match="serialization limits"):
        demo_api._success_response(_OversizedResult(provenance, "x" * 4097))
    with pytest.raises(TypeError, match="serialization limits"):
        demo_api._success_response(_LargeIntegerResult(provenance, 1 << 300))
    large_collection = _LargeCollectionResult(provenance, ("x" * 4096,) * 600)
    with pytest.raises(TypeError, match="serialization limits"):
        demo_api._success_response(large_collection)
    with pytest.raises(TypeError, match="unsupported value"):
        demo_api._json_value(["mutable lists are not DTO tuples"], demo_api._SerializationBudget())
