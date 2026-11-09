"""Offline, immutable synthetic monitoring reports sharing one calculation payload."""

from __future__ import annotations

import hashlib
import html
import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from rossmann_forecasting.monitoring import (  # noqa: E402
    build_monitoring_summary,
    synthetic_monitoring_inputs,
)


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def render_monitoring_html(summary: dict[str, Any]) -> str:
    """Render only derived values with the same status, timestamp and windows as JSON."""
    encoded = html.escape(json.dumps(summary, indent=2, allow_nan=False))
    status = html.escape(summary["status"])

    def table(rows: list[list[Any]]) -> str:
        cells = [
            "<tr>"
            + "".join(
                "<td>" + html.escape("unavailable" if value is None else str(value)) + "</td>"
                for value in row
            )
            + "</tr>"
            for row in rows
        ]
        return "<table>" + "".join(cells) + "</table>"

    performance = [["Metric / denominator", "Reference", "Current"]]
    for field in (
        "requested_forecast_keys",
        "observed_target_rows",
        "missing_actual_rows",
        "open_label_rows",
        "eligible_rows",
        "mae",
        "rmse",
        "mape",
        "mape_rows",
        "zero_actual_rows_excluded_from_mape",
        "wape",
        "wape_actual_denominator",
    ):
        performance.append(
            [field, summary["reference"]["pooled"][field], summary["current"]["pooled"][field]]
        )
    stores = [["Store", "Eligible pairs", "MAE", "RMSE", "MAPE (%)", "WAPE (ratio)"]]
    stores.extend(
        [
            [row[key] for key in ("Store", "eligible_rows", "mae", "rmse", "mape", "wape")]
            for row in summary["current"]["by_store"]
        ]
    )
    limitations = "".join("<li>" + html.escape(item) + "</li>" for item in summary["limitations"])
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Synthetic monitoring demonstration</title>
<style>body{{font:17px system-ui;max-width:1000px;margin:3rem auto;padding:1rem}}
pre{{white-space:pre-wrap;background:#f1f5f9;padding:1rem}}img{{max-width:100%}}
table{{border-collapse:collapse;margin:1rem 0}}td{{border:1px solid #cbd5e1;padding:.5rem}}
tr:first-child{{background:#e2e8f0;font-weight:bold}}</style>
<h1>Synthetic monitoring demonstration</h1>
<p>CONTROLLED SYNTHETIC FIXTURE. No LightGBM execution or production observations.</p>
<p>Evidence state: <strong>{status}</strong>. This is not system health.</p>
<p>Generated: {html.escape(summary["generated_at"])}; as of {summary["as_of"]}.</p>
<p>Reference: {summary["reference_window"]["start"]} to {summary["reference_window"]["end"]};
current: {summary["current_window"]["start"]} to {summary["current_window"]["end"]}.</p>
<h2>Open-label raw-forecast performance</h2>
<p>MAE/RMSE: monetary turnover units; MAPE: percent on positive actuals; WAPE: ratio.</p>
{table(performance)}
<h2>Current Store-level performance</h2>{table(stores)}
<img src="rolling_mae.png" alt="Synthetic trailing seven-calendar-day MAE">
<p>No numeric drift alarm, persistence rule or automatic retraining is active.</p>
<p>{html.escape(summary["human_review"])}</p><ul>{limitations}</ul>
<details><summary>Full calculation, populations and feature summaries</summary>
<pre>{encoded}</pre></details></html>"""


def write_synthetic_monitoring_report(output: Path, repository_root: Path) -> dict[str, Any]:
    """Publish a new offline fixture report; refuse to overwrite any existing directory."""
    if output.exists():
        raise FileExistsError("Monitoring output already exists; choose a new directory.")
    forecasts, labels = synthetic_monitoring_inputs()
    generated_at = datetime.now(UTC).isoformat()
    summary = build_monitoring_summary(
        forecasts,
        labels,
        as_of="2015-07-03",
        reference_start="2015-06-06",
        reference_end="2015-06-19",
        current_start="2015-06-20",
        current_end="2015-07-03",
        generated_at=generated_at,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".monitoring-", dir=output.parent) as temporary:
        stage = Path(temporary) / "report"
        stage.mkdir()
        for filename, value in (
            ("issued_forecasts.json", forecasts),
            ("available_labels.json", labels),
            ("monitoring_summary.json", summary),
        ):
            (stage / filename).write_bytes(_json(value))
        (stage / "monitoring_report.html").write_text(
            render_monitoring_html(summary), encoding="utf-8"
        )
        windows = [row for row in summary["windows"] if row["nominal_days"] == 7]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(
            [row["end"] for row in windows], [row["pooled"]["mae"] for row in windows], marker="o"
        )
        ax.set(
            title="Synthetic fixture: trailing 7-calendar-day MAE (startup windows partial)",
            ylabel="MAE (monetary turnover units)",
            xlabel="Window end",
        )
        ax.tick_params(axis="x", labelrotation=45)
        fig.tight_layout()
        fig.savefig(stage / "rolling_mae.png", dpi=150)
        plt.close(fig)
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repository_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        manifest = {
            "schema_version": "1.0.0",
            "evidence_kind": summary["evidence_kind"],
            "generated_at": generated_at,
            "command": sys.argv,
            "configuration": {
                "reference_window": summary["reference_window"],
                "current_window": summary["current_window"],
                "as_of": summary["as_of"],
            },
            "seed": None,
            "generator": "deterministic_calendar_fixture_no_randomness",
            "code_revision": revision,
            "worktree_dirty": dirty,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                name: importlib.metadata.version(name) for name in ("numpy", "pandas", "matplotlib")
            },
            "lock_sha256": _hash((repository_root / "uv.lock").read_bytes()),
            "code_sha256": {
                name: _hash((repository_root / name).read_bytes())
                for name in (
                    "src/rossmann_forecasting/monitoring.py",
                    "src/rossmann_forecasting/monitoring_report.py",
                    "src/rossmann_forecasting/forecasting/metrics.py",
                )
            },
            "source_sha256": {
                "issued_forecasts": _hash(_json(forecasts)),
                "available_labels": _hash(_json(labels)),
            },
            "output_sha256": {
                path.name: _hash(path.read_bytes()) for path in sorted(stage.iterdir())
            },
        }
        (stage / "manifest.json").write_bytes(_json(manifest))
        stage.rename(output)
    return summary
