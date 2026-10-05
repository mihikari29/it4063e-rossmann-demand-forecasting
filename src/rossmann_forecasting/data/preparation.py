"""Source-faithful Rossmann preparation and deterministic Parquet outputs."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow

from rossmann_forecasting.data.acquisition import EXPECTED_SOURCE_FILES, sha256_file
from rossmann_forecasting.data.paths import repository_root, resolve_data_dir

SOURCE_SNAPSHOT_SHA256 = {
    "train.csv": "f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc",
    "test.csv": "e75f79972de046d88c2fd55da19df627f5ca654aaf418090d4d30c60ea7dbe26",
    "store.csv": "f56bd124a2849489e6bbb5c000f5fc9640204355e316475c918ae4d089afb344",
    "sample_submission.csv": "592d892eb07072ddfa3773f13c4822ce5d01981243134c8d512ae30f016805db",
}
MIN_OPEN_RESOLUTION_MATCHES = 30
OPEN_MATCH_FIELDS = ("DayOfWeek", "Promo", "StateHoliday", "SchoolHoliday")


def _assert_store_day_keys(frame: pd.DataFrame, name: str) -> None:
    required = {"Store", "Date"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{name} must include Store and Date columns.")
    if frame[["Store", "Date"]].isna().any(axis=None):
        raise ValueError(f"{name} contains missing Store × Date keys.")
    duplicates = frame.duplicated(["Store", "Date"])
    if duplicates.any():
        sample = frame.loc[duplicates, ["Store", "Date"]].head(3).to_dict("records")
        raise ValueError(f"{name} contains duplicate Store × Date keys: {sample}")


def _parse_date(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    result = frame.copy()
    if "Date" not in result:
        raise ValueError(f"{name} is missing required Date column.")
    result["Date"] = pd.to_datetime(result["Date"], format="%Y-%m-%d", errors="raise").astype(
        "datetime64[ns]"
    )
    return result


def join_store_metadata(
    store_days: pd.DataFrame, stores: pd.DataFrame, *, name: str
) -> pd.DataFrame:
    """Join unique store metadata without changing source row count or keys."""

    if "Store" not in stores:
        raise ValueError("Store metadata is missing Store column.")
    if stores["Store"].isna().any():
        raise ValueError("Store metadata contains missing Store keys.")
    if stores["Store"].duplicated().any():
        duplicates = stores.loc[stores["Store"].duplicated(), "Store"].head(5).tolist()
        raise ValueError(f"Store metadata must be unique by Store; duplicates: {duplicates}")

    base = _parse_date(store_days, name)
    _assert_store_day_keys(base, name)
    if not base["Store"].isin(stores["Store"]).all():
        missing_stores = sorted(base.loc[~base["Store"].isin(stores["Store"]), "Store"].unique())
        raise ValueError(f"{name} contains stores with no metadata row: {missing_stores[:10]}")

    before_keys = pd.MultiIndex.from_frame(base[["Store", "Date"]])
    metadata_columns = [column for column in stores.columns if column != "Store"]
    overlap = set(metadata_columns).intersection(base.columns)
    if overlap:
        raise ValueError(f"Store metadata columns overlap source fields: {sorted(overlap)}")
    joined = base.merge(
        stores, on="Store", how="left", validate="many_to_one", sort=False, indicator=True
    )
    if joined["_merge"].ne("both").any():
        raise ValueError(f"{name} includes a Store with unmatched metadata.")
    joined = joined.drop(columns="_merge")
    if len(joined) != len(base):
        raise AssertionError(f"{name} row count changed during metadata join.")
    _assert_store_day_keys(joined, f"joined {name}")
    after_keys = pd.MultiIndex.from_frame(joined[["Store", "Date"]])
    if not before_keys.equals(after_keys):
        raise AssertionError(f"{name} Store × Date keys or order changed during metadata join.")
    return joined


def build_prepared_tables(
    train: pd.DataFrame, test: pd.DataFrame, stores: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return distinct, source-preserving train and future-covariate tables."""

    train_joined = join_store_metadata(train, stores, name="train")
    test_joined = join_store_metadata(test, stores, name="test")
    if {"Sales", "Customers"}.intersection(test_joined.columns):
        raise ValueError("The test covariate table must not contain Sales or Customers.")
    if int(train_joined["Open"].isna().sum()) != int(train["Open"].isna().sum()):
        raise AssertionError("Train Open missingness changed during preparation.")
    if int(test_joined["Open"].isna().sum()) != int(test["Open"].isna().sum()):
        raise AssertionError("Test Open missingness changed during preparation.")
    return train_joined, test_joined


def derive_test_open_resolution(
    train: pd.DataFrame, test: pd.DataFrame, *, minimum_matches: int = MIN_OPEN_RESOLUTION_MATCHES
) -> pd.DataFrame:
    """Create an audited Open view; resolve unknowns only on unanimous historical matches.

    The source ``Open`` field is never changed. A candidate is emitted only when at least
    ``minimum_matches`` historical rows for the same store and exact known calendar/promotion
    context all share one observed Open state. Candidate resolutions remain explicitly uncertain.
    """

    required = {"Store", "Date", "Open", *OPEN_MATCH_FIELDS}
    if not required.issubset(train.columns) or not required.issubset(test.columns):
        raise ValueError("Train and test must contain Store/Date/Open and all exact-match fields.")
    if {"Sales", "Customers"}.intersection(test.columns):
        raise ValueError("Open resolution must not read future Sales or Customers.")

    result = test[["Store", "Date", "Open", *OPEN_MATCH_FIELDS]].copy()
    result["Open_resolved"] = result["Open"]
    result["Open_resolution_method"] = "source"
    result["historical_match_rows"] = 0
    result["historical_open_rate"] = pd.Series(pd.NA, index=result.index, dtype="Float64")
    result["resolution_uncertain"] = False
    unknown_indexes = result.index[result["Open"].isna()]

    for index in unknown_indexes:
        target = result.loc[index]
        matches = train.loc[train["Store"].eq(target["Store"]) & train["Date"].lt(target["Date"])]
        for field in OPEN_MATCH_FIELDS:
            matches = matches.loc[matches[field].eq(target[field])]
        known = matches["Open"].dropna()
        result.loc[index, "historical_match_rows"] = len(known)
        if len(known):
            result.loc[index, "historical_open_rate"] = float(known.mean())
        if len(known) >= minimum_matches and known.nunique() == 1:
            resolution = int(known.iloc[0])
            result.loc[index, "Open_resolved"] = resolution
            result.loc[index, "Open_resolution_method"] = "historical_exact_context_consensus"
            result.loc[index, "resolution_uncertain"] = True
        else:
            result.loc[index, "Open_resolution_method"] = "unresolved_insufficient_or_mixed_history"
            result.loc[index, "resolution_uncertain"] = True

    result["Open_resolved"] = result["Open_resolved"].astype("Float64")
    result["historical_match_rows"] = result["historical_match_rows"].astype("int64")
    return result


def _verify_source_snapshot(raw_dir: Path) -> dict[str, str]:
    actual = {}
    for name in EXPECTED_SOURCE_FILES:
        path = raw_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Required Rossmann input is missing: {path}")
        actual[name] = sha256_file(path)
        expected = SOURCE_SNAPSHOT_SHA256[name]
        if actual[name] != expected:
            raise ValueError(
                f"Source hash mismatch for {name}: expected {expected}, got {actual[name]}. "
                "Stop and review the source snapshot; do not process a mixed or changed dataset."
            )
    return actual


def run_preparation(
    raw_data_dir: str | Path | None = None,
    interim_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Verify official inputs and write compressed joined Parquet datasets."""

    raw_dir = resolve_data_dir(raw_data_dir)
    destination = (
        Path(interim_dir).expanduser()
        if interim_dir is not None
        else repository_root() / "data" / "interim"
    )
    if not destination.is_absolute():
        destination = repository_root() / destination
    destination.mkdir(parents=True, exist_ok=True)

    source_hashes = _verify_source_snapshot(raw_dir)
    train = pd.read_csv(raw_dir / "train.csv", low_memory=False)
    test = pd.read_csv(raw_dir / "test.csv", low_memory=False)
    stores = pd.read_csv(raw_dir / "store.csv", low_memory=False)
    prepared_train, prepared_test = build_prepared_tables(train, test, stores)
    open_resolution = derive_test_open_resolution(prepared_train, prepared_test)

    outputs = {}
    for filename, frame in (
        ("train.parquet", prepared_train),
        ("test.parquet", prepared_test),
        ("test_open_resolution.parquet", open_resolution),
    ):
        path = destination / filename
        frame.to_parquet(path, engine="pyarrow", index=False, compression="zstd")
        outputs[filename] = {
            "rows": len(frame),
            "columns": list(frame.columns),
            "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }

    if source_hashes != _verify_source_snapshot(raw_dir):
        raise RuntimeError("A raw source file changed during preparation; outputs are untrusted.")

    manifest = {
        "command": "rossmann-prepare",
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "pyarrow_version": pyarrow.__version__,
        "source_sha256": source_hashes,
        "outputs": outputs,
    }
    (destination / "preparation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Prepare source-faithful Rossmann Parquet tables.")
    parser.add_argument("--raw-data-dir", help="Raw CSV directory (default: data/raw/rossmann).")
    parser.add_argument("--interim-dir", help="Output directory (default: data/interim).")
    args = parser.parse_args()
    manifest = run_preparation(args.raw_data_dir, args.interim_dir)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
