"""Read-only provenance checks, local feature artifacts, and holdout-safe audit output."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow

from rossmann_forecasting.data.acquisition import EXPECTED_SOURCE_FILES, sha256_file
from rossmann_forecasting.data.paths import repository_root, resolve_data_dir
from rossmann_forecasting.data.preparation import SOURCE_SNAPSHOT_SHA256
from rossmann_forecasting.features.contract import (
    DYNAMIC_PREDICTOR_COLUMNS,
    FEATURE_CONTRACT_VERSION,
    PREDICTOR_COLUMNS,
    predictor_schema,
)
from rossmann_forecasting.features.pipeline import build_feature_tables

_PREPARED_INPUTS = ("train.parquet", "test.parquet", "test_open_resolution.parquet")
_POST_GAP_DATES = ("2015-01-01", "2015-01-02", "2015-01-08", "2015-01-15", "2015-01-29")


def _hash_files(paths: dict[str, Path]) -> dict[str, str]:
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required Phase 3 input files are missing: {missing}")
    return {name: sha256_file(path) for name, path in paths.items()}


def _verify_raw_snapshot(raw_dir: Path) -> dict[str, str]:
    hashes = _hash_files({name: raw_dir / name for name in EXPECTED_SOURCE_FILES})
    mismatches = {
        name: {"expected": SOURCE_SNAPSHOT_SHA256[name], "actual": value}
        for name, value in hashes.items()
        if value != SOURCE_SNAPSHOT_SHA256[name]
    }
    if mismatches:
        raise ValueError(f"Raw Rossmann snapshot hash mismatch; stop and review: {mismatches}")
    return hashes


def _verify_interim_manifest(interim_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    manifest_path = interim_dir / "preparation_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Phase 2 preparation manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_sha256") != SOURCE_SNAPSHOT_SHA256:
        raise ValueError(
            "Phase 2 manifest does not describe the approved Rossmann source snapshot."
        )
    hashes = _hash_files({name: interim_dir / name for name in _PREPARED_INPUTS})
    for name, value in hashes.items():
        recorded = manifest.get("outputs", {}).get(name, {}).get("sha256")
        if recorded != value:
            raise ValueError(f"Phase 2 prepared input hash differs from its manifest: {name}")
    return manifest, hashes


def _assert_key_preservation(source: pd.DataFrame, output: pd.DataFrame, name: str) -> None:
    expected = source[["Store", "Date"]].copy().reset_index(drop=True)
    actual = output[["Store", "Date"]].copy().reset_index(drop=True)
    pd.testing.assert_frame_equal(
        expected, actual, check_dtype=False, obj=f"{name} key preservation"
    )
    if output.duplicated(["Store", "Date"]).any():
        raise AssertionError(f"{name} contains duplicate Store × Date keys.")


def _development_coverage_audit(
    training_features: pd.DataFrame,
    *,
    holdout_start: pd.Timestamp,
) -> dict[str, Any]:
    """Summarize feature coverage on development rows only; never inspect Sales labels."""

    development = training_features.loc[training_features["Date"].lt(holdout_start)]
    if development.empty:
        raise ValueError("No development-period rows exist before the final holdout.")
    selected = development.loc[:, PREDICTOR_COLUMNS]
    null_counts = selected.isna().sum()
    row_count = len(development)
    earliest = {}
    for feature in DYNAMIC_PREDICTOR_COLUMNS:
        available = development.loc[development[feature].notna(), "Date"]
        earliest[feature] = available.min().date().isoformat() if not available.empty else None
    return {
        "development_start": development["Date"].min().date().isoformat(),
        "development_end": development["Date"].max().date().isoformat(),
        "development_rows": row_count,
        "predictor_null_counts": {name: int(value) for name, value in null_counts.items()},
        "predictor_null_rates": {
            name: float(value / row_count) for name, value in null_counts.items()
        },
        "dynamic_feature_earliest_available_date": earliest,
    }


def _gap_availability_audit(training_features: pd.DataFrame) -> dict[str, Any]:
    """Check the known shared gap and deterministic feature warm-up for a gap-affected store."""

    start = pd.Timestamp("2014-07-01")
    end = pd.Timestamp("2014-12-31")
    all_stores = set(training_features["Store"].unique())
    gap_stores = set(training_features.loc[training_features["Date"].between(start, end), "Store"])
    affected = sorted(all_stores - gap_stores)
    if not affected:
        return {"affected_store_found": False, "checked": False}

    store = int(affected[0])
    store_rows = training_features.loc[training_features["Store"].eq(store)].set_index("Date")
    expectations = {
        "2015-01-01": (),
        "2015-01-02": ("sales_lag_1",),
        "2015-01-08": (
            "sales_lag_1",
            "sales_lag_7",
            "sales_ma_7",
            "sales_std_7",
        ),
        "2015-01-15": (
            "sales_lag_1",
            "sales_lag_7",
            "sales_lag_14",
            "sales_ma_7",
            "sales_ma_14",
            "sales_std_7",
            "sales_std_14",
        ),
        "2015-01-29": DYNAMIC_PREDICTOR_COLUMNS,
    }
    checked = {}
    for raw_date, available_features in expectations.items():
        target_date = pd.Timestamp(raw_date)
        if target_date not in store_rows.index:
            raise AssertionError(f"Gap example Store {store} is missing expected date {raw_date}.")
        row = store_rows.loc[target_date]
        available = {name: bool(pd.notna(row[name])) for name in DYNAMIC_PREDICTOR_COLUMNS}
        expected_available = set(available_features)
        for name, is_available in available.items():
            if is_available != (name in expected_available):
                raise AssertionError(
                    f"Gap feature availability mismatch for Store {store}, {raw_date}, {name}."
                )
        checked[raw_date] = available
    return {"affected_store_found": True, "Store": store, "feature_availability": checked}


def _holdout_integrity_audit(
    training_features: pd.DataFrame,
    *,
    holdout_start: pd.Timestamp,
) -> dict[str, Any]:
    """Limit holdout interaction to mechanical schema, key, and type checks."""

    holdout = training_features.loc[training_features["Date"].ge(holdout_start)]
    if tuple(name for name in holdout.columns if name in PREDICTOR_COLUMNS) != PREDICTOR_COLUMNS:
        raise AssertionError("Holdout rows do not match the frozen predictor schema.")
    if holdout.duplicated(["Store", "Date"]).any():
        raise AssertionError("Holdout rows contain duplicate Store × Date keys.")
    dtype_status = {
        name: str(holdout[name].dtype) == str(training_features[name].dtype)
        for name in PREDICTOR_COLUMNS
    }
    if not all(dtype_status.values()):
        raise AssertionError("Holdout predictor dtype is inconsistent with development rows.")
    return {
        "mechanical_checks_only": True,
        "row_count": int(len(holdout)),
        "store_date_keys_unique": True,
        "predictor_dtypes_match": dtype_status,
        "target_or_feature_distributions_summarized": False,
        "forecast_metrics_computed": False,
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value).__name__} to JSON.")


def run_feature_build(
    interim_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    raw_data_dir: str | Path | None = None,
    forecast_origin: str | None = None,
) -> dict[str, Any]:
    """Build ignored Phase 3 feature products and a holdout-safe audit manifest."""

    root = repository_root()
    raw_dir = resolve_data_dir(raw_data_dir)
    interim = Path(interim_dir).expanduser() if interim_dir else root / "data" / "interim"
    destination = Path(output_dir).expanduser() if output_dir else root / "data" / "processed"
    if not interim.is_absolute():
        interim = root / interim
    if not destination.is_absolute():
        destination = root / destination

    raw_hashes_before = _verify_raw_snapshot(raw_dir)
    preparation_manifest, interim_hashes_before = _verify_interim_manifest(interim)
    train = pd.read_parquet(interim / "train.parquet", engine="pyarrow")
    inference = pd.read_parquet(interim / "test.parquet", engine="pyarrow")
    open_resolution = pd.read_parquet(interim / "test_open_resolution.parquet", engine="pyarrow")

    origin = forecast_origin or train["Date"].max().date().isoformat()
    train_features, inference_features, findings = build_feature_tables(
        train,
        inference,
        open_resolution=open_resolution,
        forecast_origin=origin,
    )
    _assert_key_preservation(train, train_features, "Training features")
    _assert_key_preservation(inference, inference_features, "Inference features")
    for column in PREDICTOR_COLUMNS:
        if train_features[column].dtype != inference_features[column].dtype:
            raise AssertionError(f"Train/inference predictor dtype mismatch: {column}")
    if "Customers" in inference_features or "Sales" in inference_features:
        raise AssertionError("Inference feature output must not contain Sales or Customers.")
    if set(PREDICTOR_COLUMNS).intersection(
        {"Date", "Sales", "Customers", "Open", "Open_resolved", "Id", "row_role"}
    ):
        raise AssertionError("An excluded key/label/audit column entered the predictor contract.")

    dates = pd.to_datetime(train["Date"], errors="raise")
    final_date = dates.max()
    holdout_start = final_date - pd.Timedelta(days=27)
    coverage_audit = _development_coverage_audit(
        train_features,
        holdout_start=holdout_start,
    )
    gap_audit = _gap_availability_audit(
        train_features.loc[train_features["Date"].lt(holdout_start)]
    )
    holdout_audit = _holdout_integrity_audit(train_features, holdout_start=holdout_start)

    destination.mkdir(parents=True, exist_ok=True)
    output_frames = {
        "features_train.parquet": train_features,
        "features_inference.parquet": inference_features,
    }
    output_hashes: dict[str, dict[str, Any]] = {}
    for filename, frame in output_frames.items():
        path = destination / filename
        frame.to_parquet(path, engine="pyarrow", index=False, compression="zstd")
        output_hashes[filename] = {
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "dtypes": {name: str(dtype) for name, dtype in frame.dtypes.items()},
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }

    raw_hashes_after = _verify_raw_snapshot(raw_dir)
    _, interim_hashes_after = _verify_interim_manifest(interim)
    if raw_hashes_before != raw_hashes_after:
        raise RuntimeError("Raw Rossmann files changed during Phase 3 feature generation.")
    if interim_hashes_before != interim_hashes_after:
        raise RuntimeError("Phase 2 interim files changed during Phase 3 feature generation.")

    origin_date = pd.Timestamp(origin).normalize()
    manifest = {
        "command": "rossmann-build-features",
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "pyarrow_version": pyarrow.__version__,
        "forecast_origin": origin_date.date().isoformat(),
        "source_sha256": raw_hashes_before,
        "interim_sha256": interim_hashes_before,
        "predictor_columns": list(PREDICTOR_COLUMNS),
        "predictor_schema": predictor_schema(),
        "development_period_audit": coverage_audit,
        "shared_gap_availability_audit": gap_audit,
        "final_holdout_firewall": {
            "start": holdout_start.date().isoformat(),
            "end": final_date.date().isoformat(),
            **holdout_audit,
        },
        "feature_findings": findings,
        "outputs": output_hashes,
        "scope": {
            "model_training": False,
            "forecast_metrics": False,
            "feature_selection": False,
            "holdout_distribution_used": False,
        },
        "phase2_preparation_manifest_source_sha256": preparation_manifest["source_sha256"],
    }
    manifest_path = destination / "feature_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return manifest


def cli_main() -> int:
    parser = argparse.ArgumentParser(
        description="Build forecast-origin-safe Rossmann train and inference features."
    )
    parser.add_argument("--interim-dir", help="Phase 2 inputs (default: data/interim).")
    parser.add_argument("--output-dir", help="Ignored products (default: data/processed).")
    parser.add_argument("--raw-data-dir", help="Immutable raw source (default: data/raw/rossmann).")
    parser.add_argument(
        "--forecast-origin", help="Inference origin as YYYY-MM-DD; default is last train date."
    )
    args = parser.parse_args()
    result = run_feature_build(
        interim_dir=args.interim_dir,
        output_dir=args.output_dir,
        raw_data_dir=args.raw_data_dir,
        forecast_origin=args.forecast_origin,
    )
    print(
        json.dumps(
            {
                "feature_contract_version": result["feature_contract_version"],
                "predictor_count": len(result["predictor_columns"]),
                "outputs": result["outputs"],
                "manifest": str(
                    (
                        Path(args.output_dir)
                        if args.output_dir
                        else repository_root() / "data/processed"
                    )
                    / "feature_manifest.json"
                ),
            },
            indent=2,
        )
    )
    return 0
