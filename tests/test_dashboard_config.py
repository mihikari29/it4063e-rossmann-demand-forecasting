"""Deployment configuration keeps the dashboard local and read-only by default."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_streamlit_dashboard_security_and_localhost_defaults() -> None:
    config_path = Path(__file__).parents[1] / ".streamlit" / "config.toml"
    with config_path.open("rb") as config_file:
        config = tomllib.load(config_file)

    assert config["client"]["showErrorDetails"] == "none"
    assert config["server"]["address"] == "127.0.0.1"
    assert config["server"]["enableStaticServing"] is False
    assert config["server"]["fileWatcherType"] == "none"
    assert config["server"]["enableCORS"] is True
    assert config["server"]["enableXsrfProtection"] is True
    assert config["browser"]["gatherUsageStats"] is False
