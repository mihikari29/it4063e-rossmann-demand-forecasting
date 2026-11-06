"""Stage exact local academic/synthetic outputs with an evidence index and checksums."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from rossmann_forecasting.artifact_paths import require_plain_file


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _generated_directory(root: Path, value: Path) -> Path:
    path = root / value if not value.is_absolute() else value
    allowed = root / "reports/generated"
    if not path.resolve().is_relative_to(allowed.resolve()) or path.resolve() == allowed.resolve():
        raise ValueError("Input/output must be a specific directory under reports/generated.")
    for component in (path, *path.parents):
        if component.is_symlink() or component.is_junction():
            raise ValueError("Aliased generated paths are unsupported.")
        if component == root:
            break
    return path


def stage_submission_package(
    root: Path,
    output: Path,
    *,
    report: Path,
    presentation: Path,
    rendered: Path,
    monitoring: Path,
    notebook: Path,
) -> dict:
    """Copy named artifacts only; the package remains blocked for final course submission."""
    output = _generated_directory(root, output)
    inputs = {
        name: _generated_directory(root, value)
        for name, value in (
            ("report", report),
            ("presentation", presentation),
            ("rendered", rendered),
            ("monitoring", monitoring),
            ("notebook", notebook),
        )
    }
    if output.exists():
        raise FileExistsError("Choose a new submission staging directory.")
    copies = [
        (
            inputs["report"] / "submission_report.pdf",
            "report/submission_report.pdf",
            "academic_draft",
            "scripts/export_submission_report.py",
        ),
        (
            inputs["presentation"] / "rossmann_presentation.pptx",
            "presentation/rossmann_presentation.pptx",
            "editable_academic_draft",
            "scripts/export_presentation.py",
        ),
        (
            inputs["rendered"] / "rossmann_presentation.pdf",
            "presentation/rossmann_presentation.pdf",
            "powerpoint_render",
            "scripts/render_presentation.ps1",
        ),
        (
            inputs["notebook"] / "executed_monitoring.ipynb",
            "notebooks/executed_monitoring.ipynb",
            "controlled_synthetic_fixture",
            "nbclient.NotebookClient.execute",
        ),
    ]
    for name in (
        "monitoring_report.html",
        "monitoring_summary.json",
        "rolling_mae.png",
        "issued_forecasts.json",
        "available_labels.json",
        "manifest.json",
    ):
        copies.append(
            (
                inputs["monitoring"] / name,
                "monitoring/" + name,
                "controlled_synthetic_fixture",
                "scripts/generate_monitoring_artifacts.py",
            )
        )
    for name, target in (
        ("report", "report"),
        ("presentation", "presentation"),
        ("rendered", "rendered"),
        ("notebook", "notebook"),
    ):
        copies.append(
            (
                inputs[name] / "manifest.json",
                f"evidence/{target}_origin_manifest.json",
                "origin_provenance",
                "original generator; unchanged copy",
            )
        )
    for name in ("submission_report.md", "presentation.md"):
        copies.append(
            (root / "reports" / name, "sources/" + name, "editable_source", "repository source")
        )
    for source, target in (
        ("docs/LOCAL_DEMO_DEPLOYMENT.md", "guides/LOCAL_DEMO_DEPLOYMENT.md"),
        ("docs/PUBLIC_RELEASE_CANDIDATE.md", "guides/PUBLIC_RELEASE_CANDIDATE.md"),
        ("docs/ANALYTICAL_READINESS.md", "guides/ANALYTICAL_READINESS.md"),
    ):
        copies.append((root / source, target, "operator_instructions", "repository source"))
    copies.append(
        (
            root / "notebooks/03_model_monitoring.ipynb",
            "sources/03_model_monitoring.ipynb",
            "editable_synthetic_source",
            "repository source",
        )
    )
    # All selected paths, ancestors and manifests are checked before any content read/hash.
    for source in [*(source for source, _, _, _ in copies), root / "uv.lock"]:
        require_plain_file(source, root)
    manifests = {}
    for name in ("report", "presentation", "rendered", "monitoring", "notebook"):
        manifest = json.loads((inputs[name] / "manifest.json").read_text(encoding="utf-8"))
        manifests[name] = manifest
        selected = [
            source
            for source, _, _, _ in copies
            if source.parent == inputs[name] and source.name != "manifest.json"
        ]
        for source in selected:
            if manifest["output_sha256"].get(source.name) != _sha(source):
                raise ValueError(f"Source artifact differs from its origin manifest: {source.name}")
    bindings = (
        ("report", "report", root / "reports/submission_report.md"),
        ("presentation", "markdown", root / "reports/presentation.md"),
        ("rendered", "presentation", inputs["presentation"] / "rossmann_presentation.pptx"),
        ("notebook", "notebook", root / "notebooks/03_model_monitoring.ipynb"),
    )
    for name, field, source in bindings:
        if manifests[name].get("source_sha256", {}).get(field) != _sha(source):
            raise ValueError(f"Mismatched artifact generation/source binding: {name}")
    summary = json.loads((inputs["monitoring"] / "monitoring_summary.json").read_text())
    if summary["evidence_kind"] != "controlled_synthetic_fixture":
        raise ValueError("Only the authored synthetic monitoring report is supported.")
    output.mkdir(parents=True)
    entries = []
    for source, target, category, generator in copies:
        destination = output / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        entries.append(
            {
                "path": target,
                "source": source.relative_to(root).as_posix(),
                "generator": generator,
                "evidence_category": category,
                "validation_status": "checksum_verified; human acceptance pending",
                "verification_command": "compare SHA-256 with source/origin manifest",
                "sha256": _sha(destination),
            }
        )
    index = (
        "# Evidence index\n\nLocal generated package; "
        "not a public release or final course acceptance.\n\n"
    )
    index += "| File | Category | Source / generator | Validation |\n|---|---|---|---|\n"
    for entry in entries:
        index += (
            f"| [{entry['path']}]({entry['path']}) | {entry['evidence_category']} | "
            f"{entry['generator']} | Checksum verified; human review pending |\n"
        )
    index += (
        "\nOrigin manifests may describe additional local PNGs not copied into this package. "
        "Checksums and exact source paths are in package_manifest.json. Guide links referring "
        "to repository files resolve in the original source repository.\n"
    )
    (output / "EVIDENCE_INDEX.md").write_text(index, encoding="utf-8")
    (output / "SUBMISSION_CHECKLIST.md").write_text(
        "# Submission checklist\n\nOverall: **BLOCKED** for final course submission.\n\n"
        "| Deliverable / gate | State | Evidence / next action |\n|---|---|---|\n"
        "| Report PDF / editable PPTX | READY | Artifact bytes/provenance verified |\n"
        "| Synthetic monitoring / notebook | READY | Explicit synthetic, executed evidence |\n"
        "| Claims / AI disclosure | NEEDS HUMAN REVIEW | Team understanding/acceptance |\n"
        "| Source code on GitHub | BLOCKED | Requires authorized push/Draft PR |\n"
        "| Public API/dashboard | BLOCKED | Content/security/resource/owner release gates |\n"
        "| Real scenario / STL / final replay | BLOCKED | Safe-input and execution gates |\n"
        "| Report/presentation | NEEDS HUMAN REVIEW | Review course limitations |\n",
        encoding="utf-8",
    )
    (output / "REPRODUCIBILITY.md").write_text(
        "# Reproducibility and source location\n\n"
        "Source repository: https://github.com/mihikari29/it4063e-rossmann-demand-forecasting\n\n"
        "This candidate may exist only as local commits on feat/course-submission-integration. "
        "Do not assume it is available from GitHub until an authorized push/Draft PR is verified. "
        "The package manifest records the local revision and exact file identities.\n\n"
        "Use the source repository's uv.lock, uv 0.12.23 and Python 3.12/3.14. "
        "Run `uv sync --locked --extra dev --extra api --extra dashboard --extra reporting`. "
        "Run full fixtures from a tracked-files-only checkout, without real data/artifacts.\n\n"
        "Export slides: `uv run --locked --extra reporting python scripts/export_presentation.py "
        "--output-dir reports/generated/submission/<new-id>`. Render with "
        "`scripts/render_presentation.ps1` using installed PowerPoint; inspect all 15 slides. "
        "The PDF report source is unchanged; its original provenance remains in evidence/.\n\n"
        "See the copied guides for loopback commands, release gates and analytical dependencies. "
        "No source-wide preparation, protected read/hash, final replay or public upload is "
        "authorized by this package. READY means artifact availability, not course acceptance.\n",
        encoding="utf-8",
    )
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "command": sys.argv,
        "configuration": {
            "inputs": {name: path.relative_to(root).as_posix() for name, path in inputs.items()},
            "overall_submission_status": "BLOCKED",
        },
        "seed": None,
        "python": platform.python_version(),
        "code_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "worktree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
        ),
        "lock_sha256": _sha(root / "uv.lock"),
        "generator_sha256": _sha(Path(__file__)),
        "entries": entries,
        "source_sha256": {entry["source"]: entry["sha256"] for entry in entries},
        "output_sha256": {
            path.relative_to(output).as_posix(): _sha(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    (output / "package_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result
