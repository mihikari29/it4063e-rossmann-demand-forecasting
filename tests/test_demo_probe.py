from __future__ import annotations

import httpx
import pytest

from rossmann_forecasting.app.demo_probe import probe_local_api


@pytest.mark.parametrize(
    ("mode", "expected", "live"),
    [
        ("ready", "SYNTHETIC_BUNDLE_READY", True),
        ("timeout", "TIMEOUT", False),
        ("offline", "CONNECTION_UNAVAILABLE", False),
        ("503", "HTTP_ERROR", True),
        ("static", "INVALID_JSON_RESPONSE", False),
        ("mock", "INVALID_HEALTH_RESPONSE", False),
    ],
)
def test_http_success_timeout_unavailable_and_fake_health(mode, expected, live):
    calls = []

    def respond(request):
        calls.append(request.url.path)
        assert request.extensions["timeout"]["read"] == 5
        if mode == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        if mode == "offline":
            raise httpx.ConnectError("unavailable", request=request)
        if mode == "static":
            return httpx.Response(200, text="<html>static mock</html>")
        if mode == "mock":
            return httpx.Response(200, json={"status": "healthy"})
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "semantics": "process_liveness_only"})
        if mode == "503":
            return httpx.Response(503, json={"error": "unavailable"})
        return httpx.Response(
            200,
            json={
                "data": {"bundle_ready": True},
                "provenance": {"evidence_kind": "controlled_synthetic_demo"},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = probe_local_api(client)
    assert result["state"] == expected
    assert result["live"] is live
    assert result["bundle_ready"] is (mode == "ready")
    assert len(calls) == (2 if live else 1)
