"""Run the approved development-only Seasonal Naive backtest and save ignored artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

from rossmann_forecasting.data.acquisition import EXPECTED_SOURCE_FILES, sha256_file
from rossmann_forecasting.data.paths import repository_root, resolve_data_dir
from rossmann_forecasting.data.preparation import SOURCE_SNAPSHOT_SHA256
from rossmann_forecasting.forecasting.metrics import summarize_development_evaluation
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
    build_development_evaluation_records,
)

_OUTPUT_RELATIVE_DIR = Path("data") / "processed" / "seasonal_naive"
_OUTPUT_NAMES = (
    "development_forecasts.parquet",
    "metrics_by_window.csv",
    "metrics_pooled.json",
    "metrics_by_horizon.csv",
    "coverage_by_window.csv",
    "manifest.json",
)


def _repository_path(path: str | Path | None, default: Path) -> Path:
    candidate = default if path is None else Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repository_root() / candidate
    return candidate.resolve(strict=False)


def _input_provenance(raw_dir: Path, interim_dir: Path) -> dict[str, Any]:
    raw_hashes: dict[str, str] = {}
    for filename in EXPECTED_SOURCE_FILES:
        path = raw_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required immutable raw input is missing: {path}")
        raw_hashes[filename] = sha256_file(path)
    if raw_hashes != SOURCE_SNAPSHOT_SHA256:
        raise ValueError("Raw Rossmann files do not match the approved source snapshot.")

    manifest_path = interim_dir / "preparation_manifest.json"
    train_path = interim_dir / "train.parquet"
    if not manifest_path.is_file() or not train_path.is_file():
        raise FileNotFoundError("Phase 2 train.parquet and its preparation manifest are required.")
    phase2_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if phase2_manifest.get("source_sha256") != raw_hashes:
        raise ValueError("Phase 2 preparation manifest does not match the raw source snapshot.")
    train_hash = sha256_file(train_path)
    recorded_hash = phase2_manifest.get("outputs", {}).get("train.parquet", {}).get("sha256")
    if recorded_hash != train_hash:
        raise ValueError("Phase 2 train.parquet hash differs from its preparation manifest.")
    return {
        "raw_source_sha256": raw_hashes,
        "phase2_train_sha256": train_hash,
        "phase2_manifest_source_sha256": phase2_manifest["source_sha256"],
    }


def _read_development_history(train_path: Path) -> pd.DataFrame:
    """Read only needed columns and filter before any evaluator can access target labels."""

    dataset = ds.dataset(train_path, format="parquet")
    required = {"Store", "Date", "Sales", "Open"}
    missing = required.difference(dataset.schema.names)
    if missing:
        raise ValueError(f"Prepared train.parquet is missing columns: {sorted(missing)}.")
    date_type = dataset.schema.field("Date").type
    cutoff = pa.scalar(LAST_DEVELOPMENT_DATE.to_pydatetime(), type=date_type)
    table = dataset.to_table(
        columns=["Store", "Date", "Sales", "Open"],
        filter=ds.field("Date") <= cutoff,
    )
    history = table.to_pandas()
    if history.empty:
        raise ValueError("No historical development data remain through 2015-07-03.")
    dates = pd.to_datetime(history["Date"], errors="raise")
    if dates.gt(LAST_DEVELOPMENT_DATE).any():
        raise AssertionError("Date filter exposed a row after the protected development boundary.")

    observed_calendar = pd.DatetimeIndex(dates.drop_duplicates().sort_values())
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        actual_dates = observed_calendar[
            (observed_calendar >= window.target_start) & (observed_calendar <= window.target_end)
        ]
        expected_dates = pd.date_range(window.target_start, window.target_end, freq="D")
        if not actual_dates.equals(expected_dates):
            raise ValueError(f"Historical calendar is incomplete for {window.name}.")
    return history


def _assert_outputs_ignored(root: Path, output_dir: Path) -> None:
    for filename in _OUTPUT_NAMES:
        path = output_dir / filename
        relative = path.relative_to(root).as_posix()
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", relative],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Refusing to write non-ignored generated output: {relative}")


def run_development_backtest(
    *,
    raw_data_dir: str | Path | None = None,
    interim_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run only the three approved development windows and write ignored outputs."""

    root = repository_root()
    raw_dir = resolve_data_dir(raw_data_dir)
    prepared_dir = _repository_path(interim_dir, root / "data" / "interim")
    train_path = prepared_dir / "train.parquet"
    output_dir = root / _OUTPUT_RELATIVE_DIR
    _assert_outputs_ignored(root, output_dir)

    provenance_before = _input_provenance(raw_dir, prepared_dir)
    development = _read_development_history(train_path)
    forecasts = build_development_evaluation_records(development)
    summaries = summarize_development_evaluation(forecasts)

    output_dir.mkdir(parents=True, exist_ok=True)
    forecast_path = output_dir / "development_forecasts.parquet"
    window_path = output_dir / "metrics_by_window.csv"
    pooled_path = output_dir / "metrics_pooled.json"
    horizon_path = output_dir / "metrics_by_horizon.csv"
    coverage_path = output_dir / "coverage_by_window.csv"

    forecasts.to_parquet(forecast_path, engine="pyarrow", index=False, compression="zstd")
    summaries["by_window"].to_csv(window_path, index=False, float_format="%.12g")
    pooled_path.write_text(
        json.dumps(summaries["pooled"], indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    summaries["by_horizon"].to_csv(horizon_path, index=False, float_format="%.12g")
    summaries["coverage_by_window"].to_csv(coverage_path, index=False, float_format="%.12g")

    provenance_after = _input_provenance(raw_dir, prepared_dir)
    if provenance_before != provenance_after:
        raise RuntimeError("Raw or Phase 2 input hashes changed during the development backtest.")

    artifact_paths = {
        "development_forecasts.parquet": forecast_path,
        "metrics_by_window.csv": window_path,
        "metrics_pooled.json": pooled_path,
        "metrics_by_horizon.csv": horizon_path,
        "coverage_by_window.csv": coverage_path,
    }
    manifest = {
        "command": "rossmann-seasonal-naive",
        "methodology": "exact same-Store calendar d-7; recursive horizons 8-14; no teacher forcing",
        "target": "Rossmann monetary Sales at Store x Date",
        "horizon_days": 14,
        "development_only_through": LAST_DEVELOPMENT_DATE.date().isoformat(),
        "final_holdout_forecast_or_evaluation": False,
        "validation_windows": [
            {
                "name": window.name,
                "forecast_origin": window.forecast_origin.date().isoformat(),
                "target_start": window.target_start.date().isoformat(),
                "target_end": window.target_end.date().isoformat(),
                "calendar_days": 14,
            }
            for window in APPROVED_DEVELOPMENT_WINDOWS
        ],
        "input_provenance": provenance_after,
        "outputs": {
            name: {
                "path": path.relative_to(root).as_posix(),
                "rows": len(forecasts) if name == "development_forecasts.parquet" else None,
                "sha256": sha256_file(path),
            }
            for name, path in artifact_paths.items()
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    return {
        "output_directory": output_dir.relative_to(root).as_posix(),
        "forecast_records": len(forecasts),
        "metrics_by_window": summaries["by_window"].to_dict(orient="records"),
        "metrics_pooled": summaries["pooled"],
        "metrics_by_horizon": summaries["by_horizon"].to_dict(orient="records"),
        "coverage_by_window": summaries["coverage_by_window"].to_dict(orient="records"),
        "input_provenance_unchanged": provenance_before == provenance_after,
        "manifest": manifest_path.relative_to(root).as_posix(),
    }


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the approved Seasonal Naive evaluation on development windows only."
    )
    parser.add_argument("--raw-data-dir", help="Immutable Rossmann source directory.")
    parser.add_argument("--interim-dir", help="Phase 2 prepared data directory.")
    args = parser.parse_args(argv)
    result = run_development_backtest(
        raw_data_dir=args.raw_data_dir,
        interim_dir=args.interim_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
