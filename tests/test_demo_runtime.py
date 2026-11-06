"""The runtime factory uses real HTTP contracts without a canonical-data fallback."""

from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from rossmann_forecasting.app import demo_bundle, demo_runtime


def test_factory_requires_explicit_environment(monkeypatch):
    monkeypatch.delenv("ROSSMANN_DEMO_PROFILE", raising=False)
    with pytest.raises(ValueError):
        demo_runtime.create_app()
    monkeypatch.setenv("ROSSMANN_DEMO_PROFILE", "controlled_synthetic_demo")
    monkeypatch.delenv("ROSSMANN_DEMO_MANIFEST_SHA256", raising=False)
    with pytest.raises(ValueError):
        demo_runtime.create_app()


def test_http_liveness_readiness_error_and_store_queries(monkeypatch, tmp_path):
    from rossmann_forecasting.app.demo_api import create_demo_app

    bundle, manifest = demo_bundle.generate_release_bytes(__import__("pathlib").Path.cwd())
    directory = tmp_path / "artifacts" / "public_demo" / demo_bundle.RELEASE_ID
    directory.mkdir(parents=True)
    (directory / demo_bundle.BUNDLE_FILENAME).write_bytes(bundle)
    (directory / demo_bundle.MANIFEST_FILENAME).write_bytes(manifest)
    monkeypatch.setenv("ROSSMANN_DEMO_PROFILE", "controlled_synthetic_demo")
    monkeypatch.setenv("ROSSMANN_DEMO_MANIFEST_SHA256", hashlib.sha256(manifest).hexdigest())
    monkeypatch.setattr(
        demo_runtime,
        "create_demo_app",
        lambda **kwargs: create_demo_app(**kwargs, repository_root=tmp_path),
    )
    with TestClient(demo_runtime.create_app()) as client:
        assert client.get("/health").json()["semantics"] == "process_liveness_only"
        catalog = client.get("/api/v1/catalog")
        assert catalog.status_code == 200
        assert catalog.json()["data"]["bundle_ready"] is True
        paths = [
            client.get(
                "/api/v1/forecasts", params={"store_id": store, "forecast_origin": "2015-06-19"}
            ).json()
            for store in (101, 202)
        ]
        assert paths[0]["data"] != paths[1]["data"]
        assert client.get("/api/v1/forecasts", params={"store_id": 999}).status_code == 422
    (directory / demo_bundle.BUNDLE_FILENAME).unlink()
    with TestClient(demo_runtime.create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/catalog").status_code == 503
