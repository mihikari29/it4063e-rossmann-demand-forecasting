"""Synthetic-only tests for the read-only, unbound CC-02 bundle verifier."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from rossmann_forecasting.data import cc02_development as verification


def _parquet(
    *,
    dates: list[datetime | None] | None = None,
    stores: list[int | None] | None = None,
    sales: list[int] | None = None,
    sales_type: pa.DataType | None = None,
) -> bytes:
    if sales_type is None:
        sales_type = pa.int64()
    date_values = dates or [
        datetime(2015, 1, 1),
        datetime(2015, 1, 2),
        datetime(2015, 1, 1),
        datetime(2015, 1, 2),
    ]
    store_values = stores or [1, 1, 2, 2]
    sales_values = sales or [100, 110, 200, 210]
    schema = pa.schema(
        [
            pa.field("Store", pa.int64()),
            pa.field("Date", pa.timestamp("us")),
            pa.field("Sales", sales_type),
        ]
    )
    table = pa.Table.from_arrays(
        [
            pa.array(store_values, type=pa.int64()),
            pa.array(date_values, type=pa.timestamp("us")),
            pa.array(sales_values, type=sales_type),
        ],
        schema=schema,
    )
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink, compression="zstd", row_group_size=2)
    return sink.getvalue().to_pybytes()


def _snapshots(
    data_bytes: bytes | None = None,
    *,
    manifest_updates: dict[str, object] | None = None,
) -> tuple[bytes, bytes, bytes]:
    data_bytes = _parquet() if data_bytes is None else data_bytes
    frame = pq.ParquetFile(pa.BufferReader(data_bytes)).read().to_pandas()
    dates = pd.to_datetime(frame["Date"]).dropna()
    stores = frame["Store"].dropna()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "artifact_id": "synthetic-cc02-bundle",
        "purpose": verification.PURPOSE,
        "source_lineage_reference": "synthetic-lineage",
        "custodian_preparation_authorization_reference": "synthetic-preparation",
        "provider_loading_approval_reference": "synthetic-provider:PENDING",
        "preflight_reference": "synthetic-preflight:PENDING",
        "data_file": verification.DATA_FILENAME,
        "data_sha256": hashlib.sha256(data_bytes).hexdigest(),
        "data_bytes": len(data_bytes),
        "row_count": len(frame),
        "store_count": int(stores.nunique()),
        "columns": ["Store", "Date", "Sales"],
        "dtypes": {"Store": "int64", "Date": "datetime64[us]", "Sales": "int64"},
        "sort_order": ["Store", "Date"],
        "date_min": dates.min().date().isoformat(),
        "date_max": dates.max().date().isoformat(),
    }
    if manifest_updates:
        manifest.update(manifest_updates)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    refs = {
        "custodian_preparation": manifest["custodian_preparation_authorization_reference"],
        "provider_loading": manifest["provider_loading_approval_reference"],
        "preflight": manifest["preflight_reference"],
    }
    receipt = {
        "schema_version": 1,
        "designation": verification.PREPARATION_RECORD_DESIGNATION,
        "source": {"lineage_reference": manifest["source_lineage_reference"]},
        "preparation": {
            "artifact_id": manifest["artifact_id"],
            "authorization_references": refs,
        },
        "output": {
            "data_file": verification.DATA_FILENAME,
            "data_sha256": manifest["data_sha256"],
            "data_bytes": manifest["data_bytes"],
            "manifest_sha256": manifest_sha256,
            "manifest_bytes": len(manifest_bytes),
            "row_count": manifest["row_count"],
            "store_count": manifest["store_count"],
            "columns": manifest["columns"],
            "dtypes": manifest["dtypes"],
            "date_min": manifest["date_min"],
            "date_max": manifest["date_max"],
        },
    }
    receipt_bytes = (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return data_bytes, manifest_bytes, receipt_bytes


def test_valid_synthetic_bundle_returns_exact_snapshot_identities() -> None:
    data_bytes, manifest_bytes, receipt_bytes = _snapshots()

    result = verification.verify_development_bundle_snapshot(
        data_bytes, manifest_bytes, receipt_bytes
    )

    assert result.data_sha256 == hashlib.sha256(data_bytes).hexdigest()
    assert result.manifest_sha256 == hashlib.sha256(manifest_bytes).hexdigest()
    assert result.preparation_receipt_sha256 == hashlib.sha256(receipt_bytes).hexdigest()
    assert (result.row_count, result.store_count) == (4, 2)
    assert (result.date_min, result.date_max) == ("2015-01-01", "2015-01-02")


@pytest.mark.parametrize(
    ("data_bytes", "message"),
    [
        (
            _parquet(
                dates=[None, datetime(2015, 1, 2), datetime(2015, 1, 1), datetime(2015, 1, 2)]
            ),
            "Date values cannot be null",
        ),
        (
            _parquet(
                dates=[
                    datetime(2015, 1, 1, 12),
                    datetime(2015, 1, 2),
                    datetime(2015, 1, 1),
                    datetime(2015, 1, 2),
                ]
            ),
            "calendar timestamps at midnight",
        ),
        (
            _parquet(
                dates=[
                    datetime(2015, 1, 1),
                    datetime(2015, 1, 2),
                    datetime(2015, 1, 1),
                    datetime(2015, 7, 4),
                ]
            ),
            "date ceiling",
        ),
        (
            _parquet(stores=[2, 2, 1, 1]),
            "sorted by Store then Date",
        ),
        (
            _parquet(stores=[1, 1, 1, 2]),
            "unique .* keys",
        ),
    ],
    ids=["null-date", "midday-date", "protected-date", "invalid-order", "duplicate-key"],
)
def test_invalid_decoded_partition_rows_are_rejected(data_bytes: bytes, message: str) -> None:
    snapshots = _snapshots(data_bytes)
    with pytest.raises(verification.DevelopmentInputError, match=message):
        verification.verify_development_bundle_snapshot(*snapshots)


def test_duplicate_manifest_keys_and_nonstandard_constants_are_rejected() -> None:
    data_bytes, manifest_bytes, receipt_bytes = _snapshots()
    duplicate = manifest_bytes.replace(
        b'"schema_version":1,', b'"schema_version":1,"schema_version":1,', 1
    )
    with pytest.raises(verification.DevelopmentInputError, match="duplicate key"):
        verification.verify_development_bundle_snapshot(data_bytes, duplicate, receipt_bytes)

    nonstandard = manifest_bytes.replace(b'"schema_version":1', b'"schema_version":NaN', 1)
    with pytest.raises(verification.DevelopmentInputError, match="unsupported JSON value"):
        verification.verify_development_bundle_snapshot(data_bytes, nonstandard, receipt_bytes)


def test_duplicate_preparation_receipt_keys_and_nonstandard_constants_are_rejected() -> None:
    data_bytes, manifest_bytes, receipt_bytes = _snapshots()
    duplicate = receipt_bytes.replace(
        b'"schema_version":1,', b'"schema_version":1,"schema_version":1,', 1
    )
    with pytest.raises(verification.DevelopmentInputError, match="duplicate key"):
        verification.verify_development_bundle_snapshot(data_bytes, manifest_bytes, duplicate)

    nonstandard = receipt_bytes.replace(b'"schema_version":1', b'"schema_version":NaN', 1)
    with pytest.raises(verification.DevelopmentInputError, match="unsupported JSON value"):
        verification.verify_development_bundle_snapshot(data_bytes, manifest_bytes, nonstandard)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"extra": "field"}, "unsupported field set"),
        ({"purpose": "other"}, "purpose violates"),
        ({"data_bytes": True}, "data_bytes must be a positive integer"),
        ({"row_count": 0}, "row_count must be a positive integer"),
        ({"row_count": 3}, "row count does not match"),
        ({"store_count": 1}, "Store count differs"),
        ({"date_min": "2015-01-02"}, "Date bounds differ"),
        ({"date_max": "2015-07-04"}, "date_max exceeds"),
    ],
    ids=[
        "extra-field",
        "wrong-purpose",
        "boolean-size",
        "zero-row-count",
        "wrong-row-count",
        "wrong-store-count",
        "wrong-date-min",
        "protected-date-max",
    ],
)
def test_invalid_manifest_semantics_and_counts_are_rejected(
    updates: dict[str, object], message: str
) -> None:
    snapshots = _snapshots(manifest_updates=updates)
    with pytest.raises(verification.DevelopmentInputError, match=message):
        verification.verify_development_bundle_snapshot(*snapshots)


def test_incompatible_parquet_physical_schema_is_rejected() -> None:
    snapshots = _snapshots(_parquet(sales_type=pa.float64()))
    with pytest.raises(verification.DevelopmentInputError, match="Sales physical type"):
        verification.verify_development_bundle_snapshot(*snapshots)


def test_provider_byte_row_and_row_group_limits_are_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = _snapshots()
    data_bytes, manifest_bytes, receipt_bytes = snapshots

    monkeypatch.setattr(verification, "MAX_DATA_BYTES", len(data_bytes) - 1)
    with pytest.raises(
        verification.DevelopmentInputError, match="data exceeds the provider byte limit"
    ):
        verification.verify_development_bundle_snapshot(*snapshots)
    monkeypatch.setattr(verification, "MAX_DATA_BYTES", 128 * 1024 * 1024)

    monkeypatch.setattr(verification, "MAX_MANIFEST_BYTES", len(manifest_bytes) - 1)
    with pytest.raises(
        verification.DevelopmentInputError, match="manifest exceeds the provider byte limit"
    ):
        verification.verify_development_bundle_snapshot(*snapshots)
    monkeypatch.setattr(verification, "MAX_MANIFEST_BYTES", 64 * 1024)

    monkeypatch.setattr(verification, "MAX_PREPARATION_RECEIPT_BYTES", len(receipt_bytes) - 1)
    with pytest.raises(
        verification.DevelopmentInputError, match="receipt exceeds the verification byte limit"
    ):
        verification.verify_development_bundle_snapshot(*snapshots)
    monkeypatch.setattr(verification, "MAX_PREPARATION_RECEIPT_BYTES", 1024 * 1024)

    monkeypatch.setattr(verification, "MAX_ROWS", 3)
    with pytest.raises(
        verification.DevelopmentInputError, match="row_count exceeds the provider row limit"
    ):
        verification.verify_development_bundle_snapshot(*snapshots)
    monkeypatch.setattr(verification, "MAX_ROWS", 1_200_000)

    monkeypatch.setattr(verification, "MAX_ROW_GROUPS", 1)
    with pytest.raises(verification.DevelopmentInputError, match="row-group count exceeds"):
        verification.verify_development_bundle_snapshot(*snapshots)


def test_manifest_data_hash_and_preparation_receipt_must_match() -> None:
    data_bytes, manifest_bytes, receipt_bytes = _snapshots()
    changed_bytes = bytes([data_bytes[0] ^ 1]) + data_bytes[1:]
    with pytest.raises(verification.DevelopmentInputError, match="SHA-256 differs"):
        verification.verify_development_bundle_snapshot(
            changed_bytes, manifest_bytes, receipt_bytes
        )

    bad_receipt = json.loads(receipt_bytes)
    bad_receipt["output"]["row_count"] += 1
    bad_receipt_bytes = json.dumps(bad_receipt).encode()
    with pytest.raises(verification.DevelopmentInputError, match="receipt does not match"):
        verification.verify_development_bundle_snapshot(
            data_bytes, manifest_bytes, bad_receipt_bytes
        )


def test_replacing_path_after_snapshot_does_not_change_verified_bytes(tmp_path: Path) -> None:
    original = _snapshots()
    replacement = _snapshots(_parquet(sales=[101, 111, 201, 211]))[0]
    data_path = tmp_path / verification.DATA_FILENAME
    data_path.write_bytes(original[0])
    data_snapshot = data_path.read_bytes()
    manifest_snapshot, receipt_snapshot = original[1:]

    data_path.write_bytes(replacement)
    assert data_path.read_bytes() != data_snapshot
    result = verification.verify_development_bundle_snapshot(
        data_snapshot, manifest_snapshot, receipt_snapshot
    )
    assert result.data_sha256 == hashlib.sha256(data_snapshot).hexdigest()
    assert result.data_sha256 != hashlib.sha256(data_path.read_bytes()).hexdigest()
