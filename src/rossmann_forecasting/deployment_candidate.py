"""Prepare a source-allowlisted, synthetic-only two-service candidate without deployment."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from rossmann_forecasting.app.demo_bundle import (
    BUNDLE_FILENAME,
    MANIFEST_FILENAME,
    RELEASE_ID,
    generate_release_bytes,
    verify_release_directory,
)
from rossmann_forecasting.artifact_paths import require_plain_file
from rossmann_forecasting.monitoring_report import write_synthetic_monitoring_report

_PACKAGE_FILES = (
    "__init__.py",
    "monitoring.py",
    "monitoring_report.py",
    "app/__init__.py",
    "app/_http.py",
    "app/contracts.py",
    "app/demo_api.py",
    "app/demo_bundle.py",
    "app/demo_provider.py",
    "app/demo_services.py",
    "app/demo_dashboard.py",
    "app/demo_runtime.py",
    "app/course_dashboard.py",
    "app/demo_probe.py",
    "forecasting/__init__.py",
    "forecasting/metrics.py",
    "forecasting/validation.py",
    "forecasting/seasonal_naive.py",
    "features/__init__.py",
    "features/calendar.py",
    "features/keys.py",
    "features/history.py",
    "features/contract.py",
    "features/pipeline.py",
    "features/promotion.py",
    "features/competition.py",
)
SOURCE_FILES = (
    "pyproject.toml",
    "uv.lock",
    ".streamlit/config.toml",
    "demo_streamlit_app.py",
    "course_demo_app.py",
    "scripts/run_demo.py",
    "scripts/verify_local_demo.py",
    "scripts/build_public_demo_bundle.py",
    "scripts/generate_monitoring_artifacts.py",
    *("src/rossmann_forecasting/" + name for name in _PACKAGE_FILES),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_deployment_candidate(output: Path, root: Path) -> dict:
    """Copy only named source files, author fresh fixtures and record exact candidate bytes."""
    if output.exists():
        raise FileExistsError("Choose a new deployment candidate directory.")
    for name in (*SOURCE_FILES, "src/rossmann_forecasting/monitoring_report.py"):
        require_plain_file(root / name, root)
    require_plain_file(Path(__file__), root)
    output.mkdir(parents=True)
    for name in SOURCE_FILES:
        source = root / name
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    release = output / "artifacts/public_demo" / RELEASE_ID
    release.mkdir(parents=True)
    bundle, manifest = generate_release_bytes(root)
    (release / BUNDLE_FILENAME).write_bytes(bundle)
    (release / MANIFEST_FILENAME).write_bytes(manifest)
    pin = hashlib.sha256(manifest).hexdigest()
    verify_release_directory(release, expected_manifest_sha256=pin, repository_root=output)
    write_synthetic_monitoring_report(output / "monitoring", root)
    (output / "README.md").write_text(
        "# Controlled synthetic course demonstration candidate\n\n"
        "NOT RELEASED. No observed Rossmann rows, fitted model or protected outcomes.\n"
        "Two services use the same pinned bundle. The separate monitoring workspace uses\n"
        "an authored fixture and never claims real LightGBM inference or production performance.\n"
        "See the source repository docs/PUBLIC_RELEASE_CANDIDATE.md before any external action.\n"
        "Only owner-approved exact bytes/configuration may be published after release gates.\n",
        encoding="utf-8",
    )
    build = "pip install uv==0.12.23 && uv sync --locked --extra api --extra dashboard"
    api = (
        ".venv/bin/python -m uvicorn rossmann_forecasting.app.demo_runtime:create_app "
        "--factory --host 0.0.0.0 --port $PORT --no-access-log --workers 1 --limit-concurrency 8"
    )
    dashboard = (
        ".venv/bin/python -m streamlit run course_demo_app.py --server.address=0.0.0.0 "
        "--server.port=$PORT --server.headless=true --server.enableStaticServing=false "
        "--server.enableCORS=true --server.enableXsrfProtection=true "
        "--browser.gatherUsageStats=false"
    )
    yaml = "# CANDIDATE ONLY. No deployment/public listener is authorized.\nservices:\n"
    for name, command, health in (
        ("api", api, "/api/v1/catalog"),
        ("dashboard", dashboard, "/_stcore/health"),
    ):
        yaml += (
            f"  - type: web\n    name: rossmann-course-{name}-candidate\n    runtime: python\n"
            f"    plan: free\n    autoDeploy: false\n    buildCommand: {build}\n"
            f"    startCommand: {command}\n    healthCheckPath: {health}\n    envVars:\n"
            "      - key: PYTHON_VERSION\n        value: 3.12.15\n"
            "      - key: ROSSMANN_DEMO_PROFILE\n        value: controlled_synthetic_demo\n"
            f"      - key: ROSSMANN_DEMO_MANIFEST_SHA256\n        value: {pin}\n"
        )
    (output / "render.yaml").write_text(yaml, encoding="utf-8")
    (output / ".env.example").write_text(
        "# Non-secret fixture smoke configuration; not release approval.\n"
        "ROSSMANN_DEMO_PROFILE=controlled_synthetic_demo\n"
        f"ROSSMANN_DEMO_MANIFEST_SHA256={pin}\n",
        encoding="utf-8",
    )
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "command": sys.argv,
        "configuration": {
            "host_proposal": "two Render Free web services",
            "auto_deploy": False,
            "manifest_pin": pin,
            "public_release_authorized": False,
        },
        "seed": 4063,
        "python": platform.python_version(),
        "code_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "worktree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
        ),
        "lock_sha256": _sha(root / "uv.lock"),
        "generator_sha256": _sha(Path(__file__)),
        "source_sha256": {name: _sha(root / name) for name in SOURCE_FILES},
        "output_sha256": {
            str(path.relative_to(output)).replace("\\", "/"): _sha(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
        "limitations": [
            "No public deployment, host account selection or owner release approval.",
            "Linux build and host resource/security acceptance remain pending.",
            "Windows loopback smoke does not establish cloud readiness.",
        ],
    }
    (output / "candidate_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result
