"""Bounded real HTTP verification; a static response is never a backend availability claim."""

from __future__ import annotations

from typing import Any

import httpx


def probe_local_api(client: httpx.Client) -> dict[str, Any]:
    """Probe fixed loopback endpoints with timeouts; distinguish liveness and bundle readiness."""
    result: dict[str, Any] = {"live": False, "bundle_ready": False, "state": "UNAVAILABLE"}
    try:
        health = client.get("http://127.0.0.1:8000/health", timeout=5)
        health.raise_for_status()
        if health.json() != {"status": "ok", "semantics": "process_liveness_only"}:
            return {**result, "state": "INVALID_HEALTH_RESPONSE"}
        result["live"] = True
        catalog = client.get("http://127.0.0.1:8000/api/v1/catalog", timeout=5)
        catalog.raise_for_status()
        body = catalog.json()
        if (
            body.get("provenance", {}).get("evidence_kind") != "controlled_synthetic_demo"
            or body.get("data", {}).get("bundle_ready") is not True
        ):
            return {**result, "state": "INVALID_CATALOG_RESPONSE"}
        return {**result, "bundle_ready": True, "state": "SYNTHETIC_BUNDLE_READY"}
    except httpx.TimeoutException:
        return {**result, "state": "TIMEOUT"}
    except httpx.HTTPStatusError as error:
        return {**result, "state": "HTTP_ERROR", "http_status": error.response.status_code}
    except httpx.RequestError:
        return {**result, "state": "CONNECTION_UNAVAILABLE"}
    except (ValueError, TypeError, AttributeError):
        return {**result, "state": "INVALID_JSON_RESPONSE"}
