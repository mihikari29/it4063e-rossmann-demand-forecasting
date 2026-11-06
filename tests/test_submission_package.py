"""Packaging fixtures test copy integrity and path gates, not academic document accuracy."""

import hashlib
import json

import pytest

from rossmann_forecasting.submission_package import stage_submission_package


def test_package_validates_source_hashes_and_retains_blocked_status(tmp_path):
    root = tmp_path
    directories = {
        name: root / "reports/generated" / name
        for name in ("report", "presentation", "rendered", "monitoring", "notebook")
    }
    files = {
        "report": {"submission_report.pdf": b"authored PDF byte fixture"},
        "presentation": {"rossmann_presentation.pptx": b"authored PPTX byte fixture"},
        "rendered": {"rossmann_presentation.pdf": b"render byte fixture"},
        "notebook": {"executed_monitoring.ipynb": b"{}"},
        "monitoring": {
            name: b"fixture"
            for name in (
                "monitoring_report.html",
                "rolling_mae.png",
                "issued_forecasts.json",
                "available_labels.json",
            )
        },
    }
    files["monitoring"]["monitoring_summary.json"] = json.dumps(
        {"evidence_kind": "controlled_synthetic_fixture"}
    ).encode()
    for name, directory in directories.items():
        directory.mkdir(parents=True)
        for filename, content in files[name].items():
            (directory / filename).write_bytes(content)
        (directory / "manifest.json").write_text(
            json.dumps(
                {
                    "output_sha256": {
                        filename: hashlib.sha256(content).hexdigest()
                        for filename, content in files[name].items()
                    }
                }
            )
        )
    for relative in (
        "reports/submission_report.md",
        "reports/presentation.md",
        "notebooks/03_model_monitoring.ipynb",
        "uv.lock",
        "docs/LOCAL_DEMO_DEPLOYMENT.md",
        "docs/PUBLIC_RELEASE_CANDIDATE.md",
        "docs/ANALYTICAL_READINESS.md",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("authored fixture")
    for name, field, source in (
        ("report", "report", root / "reports/submission_report.md"),
        ("presentation", "markdown", root / "reports/presentation.md"),
        ("rendered", "presentation", directories["presentation"] / "rossmann_presentation.pptx"),
        ("notebook", "notebook", root / "notebooks/03_model_monitoring.ipynb"),
    ):
        path = directories[name] / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["source_sha256"] = {field: hashlib.sha256(source.read_bytes()).hexdigest()}
        path.write_text(json.dumps(manifest))
    # Git metadata belongs to the real trusted repository; the fixture root has none.
    import subprocess
    from unittest.mock import patch

    original = subprocess.check_output

    def git_result(command, **kwargs):
        return "" if "--porcelain" in command else "a" * 40

    output = root / "reports/generated/package"
    with patch("rossmann_forecasting.submission_package.subprocess.check_output", git_result):
        result = stage_submission_package(root, output, **directories)
        assert result["configuration"]["overall_submission_status"] == "BLOCKED"
        assert "NEEDS HUMAN REVIEW" in (output / "SUBMISSION_CHECKLIST.md").read_text()
        for name, pin in result["output_sha256"].items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == pin
        with pytest.raises(FileExistsError):
            stage_submission_package(root, output, **directories)
        render_manifest = directories["rendered"] / "manifest.json"
        original_render = render_manifest.read_text()
        mismatched = json.loads(original_render)
        mismatched["source_sha256"]["presentation"] = "0" * 64
        render_manifest.write_text(json.dumps(mismatched))
        with pytest.raises(ValueError, match="generation/source binding"):
            stage_submission_package(
                root, root / "reports/generated/mixed-generation", **directories
            )
        render_manifest.write_text(original_render)
        (directories["report"] / "submission_report.pdf").write_bytes(b"changed")
        with pytest.raises(ValueError, match="origin manifest"):
            stage_submission_package(root, root / "reports/generated/bad", **directories)
        with pytest.raises(ValueError, match="reports/generated"):
            stage_submission_package(root, root / "data/raw/not-allowed", **directories)
    assert subprocess.check_output is original


def test_alias_preflight_occurs_before_any_manifest_read_or_hash(monkeypatch, tmp_path):
    import rossmann_forecasting.submission_package as packaging

    def reject(*args):
        raise ValueError("Aliased fixture path")

    def forbidden(*args, **kwargs):
        raise AssertionError("Content was accessed before alias preflight")

    monkeypatch.setattr(packaging, "require_plain_file", reject)
    monkeypatch.setattr(packaging, "_sha", forbidden)
    monkeypatch.setattr(type(tmp_path), "read_text", forbidden)
    directories = {
        name: tmp_path / "reports/generated" / name
        for name in ("report", "presentation", "rendered", "monitoring", "notebook")
    }
    with pytest.raises(ValueError, match="Aliased fixture"):
        stage_submission_package(tmp_path, tmp_path / "reports/generated/package", **directories)
