"""Explicit local entrypoint for the controlled-synthetic Streamlit dashboard."""

from __future__ import annotations

import os
import re
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from rossmann_forecasting.app.demo_provider import (
    DemoProfile,
    DemoProviderError,
    DemoReleaseIntegrityError,
    DemoReleaseUnavailableError,
)
from rossmann_forecasting.app.demo_services import DemoServices

_PIN_PATTERN = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_CACHE_KEY = "_controlled_synthetic_demo_cache_key"
_CACHE_SERVICES = "_controlled_synthetic_demo_services"
_CACHE_ERROR = "_controlled_synthetic_demo_error"


def _clear_cache(session_state: MutableMapping[str, Any]) -> None:
    for key in (_CACHE_KEY, _CACHE_SERVICES, _CACHE_ERROR):
        session_state.pop(key, None)


def _open_session_services(
    *,
    profile_value: str | None,
    manifest_pin: str | None,
    session_state: MutableMapping[str, Any],
    repository_root: Path | None = None,
) -> tuple[DemoServices | None, str | None]:
    """Cache one verified immutable service per session and exact trusted config pair."""
    if profile_value != DemoProfile.CONTROLLED_SYNTHETIC.value:
        _clear_cache(session_state)
        return None, "Set the explicit controlled-synthetic profile in local process configuration."
    if manifest_pin is None or _PIN_PATTERN.fullmatch(manifest_pin) is None:
        _clear_cache(session_state)
        return (
            None,
            "Set a separate lowercase 64-character manifest SHA-256 pin "
            "in local process configuration.",
        )

    cache_key = (profile_value, manifest_pin)
    if session_state.get(_CACHE_KEY) == cache_key:
        return session_state.get(_CACHE_SERVICES), session_state.get(_CACHE_ERROR)
    _clear_cache(session_state)
    try:
        services = DemoServices.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=manifest_pin,
            repository_root=repository_root,
        )
    except DemoReleaseUnavailableError:
        services, error = (
            None,
            "The pinned synthetic release is unavailable. Check the local setup and release files.",
        )
    except DemoReleaseIntegrityError:
        services, error = None, "The synthetic release did not pass its configured integrity check."
    except DemoProviderError:
        services, error = None, "The synthetic release cannot be opened with this configuration."
    except Exception:
        services, error = (
            None,
            "The synthetic release is temporarily unavailable. No details were exposed.",
        )
    else:
        error = None
    session_state[_CACHE_KEY] = cache_key
    session_state[_CACHE_SERVICES] = services
    session_state[_CACHE_ERROR] = error
    return services, error


def main() -> None:
    """Read explicit process configuration at execution time and render the isolated dashboard."""
    import streamlit as st

    services, error = _open_session_services(
        profile_value=os.environ.get("ROSSMANN_DEMO_PROFILE"),
        manifest_pin=os.environ.get("ROSSMANN_DEMO_MANIFEST_SHA256"),
        session_state=st.session_state,
    )
    if services is None:
        from rossmann_forecasting.app.demo_dashboard import render_unavailable

        render_unavailable(error or "The synthetic release is unavailable.")
        return
    from rossmann_forecasting.app.demo_dashboard import run_demo_dashboard

    run_demo_dashboard(services)


if __name__ == "__main__":
    main()
