"""A cloud preparation output includes only named code and freshly authored synthetic content."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from rossmann_forecasting.deployment_candidate import SOURCE_FILES, prepare_deployment_candidate


def test_candidate_is_allowlisted_synthetic_pinned_and_never_overwritten(tmp_path):
    output = tmp_path / "candidate"
    manifest = prepare_deployment_candidate(output, Path.cwd())
    assert manifest["configuration"]["public_release_authorized"] is False
    assert set(manifest["source_sha256"]) == set(SOURCE_FILES)
    assert not (output / "data").exists()
    assert not (output / ".git").exists()
    assert not (output / "src/rossmann_forecasting/app/api.py").exists()
    assert not (output / "src/rossmann_forecasting/phase13").exists()
    config = (output / "render.yaml").read_text()
    assert config.count("plan: free") == 2
    assert config.count("autoDeploy: false") == 2
    assert manifest["configuration"]["manifest_pin"] in config
    for name, pin in manifest["output_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == pin
    monitoring = json.loads((output / "monitoring/monitoring_summary.json").read_text())
    assert monitoring["evidence_kind"] == "controlled_synthetic_fixture"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(output / "src")
    environment["ROSSMANN_DEMO_PROFILE"] = "controlled_synthetic_demo"
    environment["ROSSMANN_DEMO_MANIFEST_SHA256"] = manifest["configuration"]["manifest_pin"]
    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastapi.testclient import TestClient; "
            "from rossmann_forecasting.app.demo_runtime import create_app; "
            "import rossmann_forecasting.app.course_dashboard; "
            "import rossmann_forecasting.app.demo_probe; "
            "client=TestClient(create_app()); "
            "assert client.get('/api/v1/catalog').status_code == 200",
        ],
        cwd=output,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert smoke.returncode == 0, smoke.stderr
    with pytest.raises(FileExistsError):
        prepare_deployment_candidate(output, Path.cwd())
