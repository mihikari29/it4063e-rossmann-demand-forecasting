"""Run Phase 5 Holt-Winters evaluation on development dates only."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from rossmann_forecasting.data.acquisition import sha256_file
from rossmann_forecasting.data.paths import repository_root, resolve_data_dir
from rossmann_forecasting.forecasting.holt_winters_evaluation import evaluate_phase5_development
from rossmann_forecasting.forecasting.runner import (
    _input_provenance,
    _read_development_history,
    _repository_path,
)
from rossmann_forecasting.forecasting.validation import (
    LAST_DEVELOPMENT_DATE,
    build_development_evaluation_records,
)

_OUTPUT_RELATIVE_DIR = Path("data") / "processed" / "holt_winters"
_OUTPUT_NAMES = (
    "development_forecasts.parquet",
    "internal_14_step_forecasts.parquet",
    "fit_diagnostics.csv",
    "fit_diagnostics_summary.csv",
    "metrics_by_window.csv",
    "metrics_pooled.json",
    "metrics_by_horizon.csv",
    "coverage_guardrail.json",
    "paired_forecasts.parquet",
    "paired_metrics.csv",
    "clipping_diagnostics.csv",
    "manifest.json",
)


def _assert_outputs_ignored(root: Path, output_dir: Path) -> None:
    for filename in _OUTPUT_NAMES:
        relative = (output_dir / filename).relative_to(root).as_posix()
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", relative],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Refusing to write non-ignored generated output: {relative}")


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy summary scalars and non-finite values for strict JSON output."""

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def run_holt_winters_development_backtest(
    *,
    raw_data_dir: str | Path | None = None,
    interim_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Generate auditable Phase 5 artifacts with the protected holdout excluded at read time."""

    root = repository_root()
    raw_dir = resolve_data_dir(raw_data_dir)
    prepared_dir = _repository_path(interim_dir, root / "data" / "interim")
    train_path = prepared_dir / "train.parquet"
    output_dir = root / _OUTPUT_RELATIVE_DIR
    _assert_outputs_ignored(root, output_dir)

    provenance_before = _input_provenance(raw_dir, prepared_dir)
    # The parquet predicate and projection happen before either model can receive target labels.
    development = _read_development_history(train_path)
    seasonal_naive = build_development_evaluation_records(development)
    evaluation = evaluate_phase5_development(development, seasonal_naive)
    standalone = evaluation["standalone"]
    candidate = evaluation["evaluation"]

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: output_dir / name for name in _OUTPUT_NAMES}
    candidate.records.to_parquet(
        paths["development_forecasts.parquet"],
        engine="pyarrow",
        index=False,
        compression="zstd",
    )
    candidate.internal_forecasts.to_parquet(
        paths["internal_14_step_forecasts.parquet"],
        engine="pyarrow",
        index=False,
        compression="zstd",
    )
    candidate.diagnostics.to_csv(paths["fit_diagnostics.csv"], index=False, float_format="%.12g")
    evaluation["fit_diagnostics_summary"].to_csv(
        paths["fit_diagnostics_summary.csv"], index=False, float_format="%.12g"
    )
    standalone["by_window"].to_csv(
        paths["metrics_by_window.csv"], index=False, float_format="%.12g"
    )
    paths["metrics_pooled.json"].write_text(
        json.dumps(standalone["pooled"], indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    standalone["by_horizon"].to_csv(
        paths["metrics_by_horizon.csv"], index=False, float_format="%.12g"
    )
    guardrail = {
        "threshold": standalone["coverage_guardrail_threshold"],
        "passed": standalone["coverage_guardrail_passed"],
        "requires_coverage_review": standalone["requires_coverage_review"],
        "coverage_by_window": standalone["by_window"]
        .loc[
            :,
            [
                "validation_window",
                "open_label_rows",
                "open_label_forecast_available_rows",
                "open_label_coverage_denominator_rows",
                "open_label_forecast_coverage_rate",
            ],
        ]
        .to_dict(orient="records"),
    }
    paths["coverage_guardrail.json"].write_text(
        json.dumps(guardrail, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    evaluation["paired_records"].to_parquet(
        paths["paired_forecasts.parquet"],
        engine="pyarrow",
        index=False,
        compression="zstd",
    )
    evaluation["paired_summary"].to_csv(
        paths["paired_metrics.csv"], index=False, float_format="%.12g"
    )
    standalone["clipping"].to_csv(
        paths["clipping_diagnostics.csv"], index=False, float_format="%.12g"
    )

    provenance_after = _input_provenance(raw_dir, prepared_dir)
    if provenance_before != provenance_after:
        raise RuntimeError("Raw or Phase 2 input hashes changed during the development backtest.")
    if candidate.records["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        raise AssertionError("A holdout date was emitted by the development-only runner.")

    manifest = {
        "command": "rossmann-holt-winters",
        "statistical_model": (
            "Additive Holt-Winters, additive trend, undamped, weekly additive seasonality"
        ),
        "configuration": {
            "trend": "add",
            "damped_trend": False,
            "seasonal": "add",
            "seasonal_periods": 7,
            "initialization_method": "estimated",
            "optimized": True,
            "use_boxcox": False,
            "minimum_contiguous_history_days": 28,
            "history_calendar": "observed daily rows including closed-day Sales; no gap filling",
            "fallback": None,
            "forecast_horizon_days": 14,
            "open_label_coverage_guardrail": standalone["coverage_guardrail_threshold"],
        },
        "target": "Rossmann monetary Sales at Store × Date",
        "development_only_through": LAST_DEVELOPMENT_DATE.date().isoformat(),
        "final_holdout_forecast_or_evaluation": False,
        "coverage_guardrail_passed": standalone["coverage_guardrail_passed"],
        "comparative_interpretation_suppressed": standalone["requires_coverage_review"],
        "input_provenance": provenance_after,
        "outputs": {
            name: {
                "path": path.relative_to(root).as_posix(),
                "rows": _output_rows(name, candidate, evaluation),
                "sha256": sha256_file(path),
            }
            for name, path in paths.items()
            if name != "manifest.json"
        },
    }
    paths["manifest.json"].write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "output_directory": output_dir.relative_to(root).as_posix(),
        "forecast_records": len(candidate.records),
        "store_origin_fits": len(candidate.diagnostics),
        "coverage_guardrail_passed": standalone["coverage_guardrail_passed"],
        "metrics_by_window": standalone["by_window"].to_dict(orient="records"),
        "metrics_pooled": standalone["pooled"],
        "fit_diagnostics_summary": evaluation["fit_diagnostics_summary"].to_dict(orient="records"),
        "paired_metrics": evaluation["paired_summary"].to_dict(orient="records"),
        "input_provenance_unchanged": provenance_before == provenance_after,
        "manifest": paths["manifest.json"].relative_to(root).as_posix(),
    }


def _output_rows(name: str, candidate: Any, evaluation: dict[str, Any]) -> int | None:
    table_rows = {
        "development_forecasts.parquet": len(candidate.records),
        "internal_14_step_forecasts.parquet": len(candidate.internal_forecasts),
        "fit_diagnostics.csv": len(candidate.diagnostics),
        "fit_diagnostics_summary.csv": len(evaluation["fit_diagnostics_summary"]),
        "metrics_by_window.csv": len(evaluation["standalone"]["by_window"]),
        "metrics_by_horizon.csv": len(evaluation["standalone"]["by_horizon"]),
        "paired_forecasts.parquet": len(evaluation["paired_records"]),
        "paired_metrics.csv": len(evaluation["paired_summary"]),
        "clipping_diagnostics.csv": len(evaluation["standalone"]["clipping"]),
    }
    return table_rows.get(name)


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate additive Holt-Winters on the three development windows only."
    )
    parser.add_argument("--raw-data-dir", help="Immutable Rossmann source directory.")
    parser.add_argument("--interim-dir", help="Phase 2 prepared data directory.")
    args = parser.parse_args(argv)
    result = run_holt_winters_development_backtest(
        raw_data_dir=args.raw_data_dir,
        interim_dir=args.interim_dir,
    )
    print(json.dumps(_json_safe(result), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
