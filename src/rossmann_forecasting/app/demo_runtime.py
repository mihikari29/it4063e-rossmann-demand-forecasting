"""Explicit environment-configured ASGI factory for the controlled synthetic profile."""

from __future__ import annotations

import os

from fastapi import FastAPI

from rossmann_forecasting.app.demo_api import create_demo_app
from rossmann_forecasting.app.demo_provider import DemoProfile


def create_app() -> FastAPI:
    """Fail closed on absent profile/pin; never discover canonical data or infer configuration."""
    if os.environ.get("ROSSMANN_DEMO_PROFILE") != DemoProfile.CONTROLLED_SYNTHETIC.value:
        raise ValueError("Set the explicit controlled synthetic demonstration profile.")
    return create_demo_app(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=os.environ.get("ROSSMANN_DEMO_MANIFEST_SHA256", ""),
    )
