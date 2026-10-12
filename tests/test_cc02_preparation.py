"""Synthetic-only tests for the fixture-gated CC-02 custodian preparation helpers."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from rossmann_forecasting.analysis import seasonal_decomposition as analysis
from rossmann_forecasting.data import cc02_development as provider
from rossmann_forecasting.data import cc02_preparation as preparation


def _record(
    store: str | int,
    day: str,
    sales: str | int,
    *,
    open_value: str | int = 1,
) -> list[str]:
    return [str(store), "1", day, str(sales), "27", str(open_value), "0", "0", "0"]


def _csv_bytes(
    rows: list[list[str]],
    *,
    header: tuple[str, ...] | list[str] = preparation.EXPECTED_HEADER,
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _config(
    source: bytes,
    *,
    artifact_id: str = "fixture-cc02-preparation",
    source_lineage_reference: str = "synthetic-only:source-lineage:v1",
    preparation_reference: str = "synthetic-only:preparation-authorization:v1",
    provider_reference: str = "synthetic-only:provider-loading:PENDING:v1",
    preflight_reference: str = "synthetic-only:preflight:PENDING:v1",
) -> preparation.PreparationConfiguration:
    return preparation.PreparationConfiguration(
        artifact_id=artifact_id,
        expected_source_bytes=len(source),
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        source_lineage_reference=source_lineage_reference,
        custodian_preparation_authorization_reference=preparation_reference,
        provider_loading_approval_reference=provider_reference,
        preflight_reference=preflight_reference,
    )


def _roots(tmp_path: Path, suffix: str = "") -> tuple[Path, Path]:
    base = tmp_path / suffix if suffix else tmp_path
    return (
        base / "data" / "interim" / "cc02_development",
        base / "reports" / "generated" / "cc02_custodian",
    )


def _prepare(
    tmp_path: Path,
    source: bytes,
    *,
    config: preparation.PreparationConfiguration | None = None,
    suffix: str = "",
) -> preparation.PreparationResult:
    bundle_root, receipt_root = _roots(tmp_path, suffix)
    return preparation._prepare_partition_from_bytes(
        config or _config(source), source, bundle_root=bundle_root, receipt_root=receipt_root
    )


def _manifest(bundle: Path) -> tuple[dict[str, object], bytes]:
    content = (bundle / preparation.MANIFEST_FILENAME).read_bytes()
    return json.loads(content), content


def _assert_published_bundle_integrity(bundle: Path) -> dict[str, object]:
    assert {path.name for path in bundle.iterdir()} == {
        preparation.DATA_FILENAME,
        preparation.MANIFEST_FILENAME,
    }
    manifest, _ = _manifest(bundle)
    data_bytes = (bundle / preparation.DATA_FILENAME).read_bytes()
    assert manifest["data_sha256"] == hashlib.sha256(data_bytes).hexdigest()
    assert manifest["data_bytes"] == len(data_bytes)
    assert set(manifest) == preparation._MANIFEST_KEYS
    assert (
        pq.ParquetFile(bundle / preparation.DATA_FILENAME).metadata.num_rows
        == manifest["row_count"]
    )
    return manifest


def _fixture_approval(bundle: Path) -> provider.DevelopmentInputApproval:
    manifest, manifest_bytes = _manifest(bundle)
    return provider.DevelopmentInputApproval(
        artifact_id=str(manifest["artifact_id"]),
        purpose=preparation.PURPOSE,
        bundle_location=str(bundle.absolute()),
        data_filename=preparation.DATA_FILENAME,
        manifest_filename=preparation.MANIFEST_FILENAME,
        expected_data_sha256=str(manifest["data_sha256"]),
        expected_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        development_ceiling=preparation.DEVELOPMENT_CEILING,
        source_lineage_reference=str(manifest["source_lineage_reference"]),
        custodian_preparation_authorization_reference=str(
            manifest["custodian_preparation_authorization_reference"]
        ),
        provider_loading_approval_reference=str(manifest["provider_loading_approval_reference"]),
        preflight_reference=str(manifest["preflight_reference"]),
    )


def test_extraction_keeps_each_eligible_row_and_ignores_post_cutoff_values() -> None:
    protected_sales = "987654321012345678"
    source = _csv_bytes(
        [
            _record(2, "2015-07-03", 0, open_value=0),
            _record(1, "2015-01-02", -4, open_value=0),
            _record(1, "2015-01-01", 5),
            _record(3, "2015-07-01", 0, open_value=0),
            _record("not-a-store", "2015-07-04", protected_sales),
        ]
    )

    frame = preparation._extract_development_sales(source, _config(source))

    assert list(frame.columns) == ["Store", "Date", "Sales"]
    assert tuple(str(frame[column].dtype) for column in frame.columns) == (
        "int64",
        "datetime64[us]",
        "int64",
    )
    assert list(zip(frame.Store, frame.Sales, strict=True)) == [(1, 5), (1, -4), (2, 0), (3, 0)]
    assert list(frame.Date.dt.strftime("%Y-%m-%d")) == [
        "2015-01-01",
        "2015-01-02",
        "2015-07-03",
        "2015-07-01",
    ]
    assert protected_sales not in frame.astype(str).to_string()


def test_source_identity_and_configuration_are_checked_before_transformation() -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    config = _config(source)
    with pytest.raises(preparation.PreparationError, match="byte count"):
        preparation._extract_development_sales(source + b"x", config)
    with pytest.raises(preparation.PreparationError, match="SHA-256"):
        preparation._extract_development_sales(
            source, replace(config, expected_source_sha256="0" * 64)
        )
    with pytest.raises(preparation.PreparationError, match="artifact_id"):
        preparation._extract_development_sales(source, replace(config, artifact_id="../not-safe"))
    with pytest.raises(preparation.PreparationError, match="reference"):
        preparation._extract_development_sales(source, replace(config, preflight_reference=" "))


@pytest.mark.parametrize(
    "header",
    [
        preparation.EXPECTED_HEADER[:-1],
        list(preparation.EXPECTED_HEADER[:-1]) + ["Sales"],
        list(reversed(preparation.EXPECTED_HEADER)),
        list(preparation.EXPECTED_HEADER[:-1]) + ["Unexpected"],
    ],
    ids=["missing", "duplicate", "reordered", "unsupported"],
)
def test_unsupported_headers_are_rejected(header: list[str] | tuple[str, ...]) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)], header=header)
    with pytest.raises(preparation.PreparationError, match="header"):
        preparation._extract_development_sales(source, _config(source))


@pytest.mark.parametrize(
    "source",
    [
        b"\\xff,DayOfWeek,Date,Sales,Customers,Open,Promo,StateHoliday,SchoolHoliday\\n",
        _csv_bytes([_record(1, "2015-07-03", 10)[:-1]]),
        _csv_bytes([_record(1, "2015-07-03", 10)]) + b'1,1,"unterminated',
    ],
    ids=["invalid-utf8", "short-row", "malformed-quoting"],
)
def test_invalid_source_encoding_and_csv_records_fail_closed(source: bytes) -> None:
    with pytest.raises(preparation.PreparationError):
        preparation._extract_development_sales(source, _config(source))


@pytest.mark.parametrize("token", ["2015-7-03", "2015-02-29", "not-a-date", "2015-07-03T00:00"])
def test_invalid_or_noncanonical_dates_are_rejected(token: str) -> None:
    source = _csv_bytes([_record(1, token, 1)])
    with pytest.raises(preparation.PreparationError, match="date"):
        preparation._extract_development_sales(source, _config(source))


@pytest.mark.parametrize(
    ("store", "sales", "message"),
    [
        ("0", "1", "positive"),
        ("-1", "1", "positive"),
        ("9223372036854775808", "1", "int64"),
        ("1.0", "1", "integer"),
        ("1", "1.5", "integer"),
        ("1", str(2**63), "int64"),
        ("1", "", "integer"),
    ],
)
def test_invalid_eligible_numeric_values_are_rejected(store: str, sales: str, message: str) -> None:
    source = _csv_bytes([_record(store, "2015-07-03", sales)])
    with pytest.raises(preparation.PreparationError, match=message):
        preparation._extract_development_sales(source, _config(source))


def test_signed_int64_boundaries_and_normalized_tokens_preserve_values() -> None:
    long_zeros = "0" * 5_000
    source = _csv_bytes(
        [
            _record("+0001", "2015-07-03", "+0005"),
            _record("0002", "2015-07-02", "-0000"),
            _record("0003", "2015-07-01", long_zeros),
            _record(long_zeros + "4", "2015-06-30", long_zeros + "123"),
            _record("5", "2015-06-29", "9223372036854775807"),
            _record("6", "2015-06-28", "-9223372036854775808"),
        ]
    )

    frame = preparation._extract_development_sales(source, _config(source))

    assert frame["Store"].tolist() == [1, 2, 3, 4, 5, 6]
    assert frame["Sales"].tolist() == [5, 0, 0, 123, 9223372036854775807, -9223372036854775808]


@pytest.mark.parametrize(
    ("store", "sales", "field", "positive_store"),
    [
        ("1", "9223372036854775808", "Sales", False),
        ("1", "-9223372036854775809", "Sales", False),
        ("1", "9" * 5_000, "Sales", False),
        ("1", "-" + "9" * 5_000, "Sales", False),
        ("9" * 5_000, "1", "Store", False),
        ("1a", "1", "Store", False),
        ("1_0", "1", "Store", False),
        ("1", "not-a-number", "Sales", False),
        ("1", "1.5", "Sales", False),
        ("0", "1", "Store", True),
        ("0000", "1", "Store", True),
        ("+0000", "1", "Store", True),
        ("-0000", "1", "Store", True),
    ],
    ids=[
        "positive-overflow",
        "negative-overflow",
        "long-positive-overflow",
        "long-negative-overflow",
        "long-store-token",
        "alphabetic-store-token",
        "nondecimal-store-token",
        "alphabetic-sales-token",
        "nondecimal-sales-token",
        "store-zero",
        "zero-padded-store",
        "signed-zero-store",
        "negative-zero-store",
    ],
)
def test_invalid_eligible_integer_tokens_fail_without_publishing(
    tmp_path: Path, store: str, sales: str, field: str, positive_store: bool
) -> None:
    source = _csv_bytes([_record(store, "2015-07-03", sales)])
    bundle_root, _ = _roots(tmp_path)
    token = store if field == "Store" else sales

    with pytest.raises(preparation.PreparationError) as caught:
        _prepare(tmp_path, source)

    message = str(caught.value)
    assert token not in message
    if field == "Store" and not positive_store:
        assert "outside signed int64" in message or "base-10 integer" in message
    if positive_store:
        assert "must be positive" in message
    assert not (bundle_root / "fixture-cc02-preparation").exists()
    assert not list(bundle_root.glob(".stage-fixture-cc02-preparation-*"))


def test_extremely_long_post_cutoff_sales_token_is_ignored_before_numeric_parsing() -> None:
    source = _csv_bytes(
        [
            _record(1, "2015-07-03", 10),
            _record(2, "2015-07-04", "INVALID-PROTECTED-SALES-" + "x" * 5_000),
        ]
    )

    frame = preparation._extract_development_sales(source, _config(source))

    assert frame.to_dict("records") == [
        {"Store": 1, "Date": pd.Timestamp("2015-07-03"), "Sales": 10}
    ]


def test_malformed_date_is_rejected_without_echoing_its_token() -> None:
    secret_date = "PROTECTED-DATE-CANARY"
    source = _csv_bytes([_record(1, secret_date, 1)])
    with pytest.raises(preparation.PreparationError) as caught:
        preparation._extract_development_sales(source, _config(source))
    assert secret_date not in str(caught.value)


def test_duplicate_eligible_store_date_keys_are_rejected() -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 1), _record(1, "2015-07-03", 2)])
    with pytest.raises(preparation.PreparationError, match="duplicate"):
        preparation._extract_development_sales(source, _config(source))


def test_publication_writes_exact_provider_schema_and_separate_safe_receipt(tmp_path: Path) -> None:
    protected_value = "987654321012345678"
    protected_day = "2015-07-04"
    source = _csv_bytes(
        [
            _record(2, "2015-07-03", 0, open_value=0),
            _record(1, "2015-06-01", 4),
            _record(1, protected_day, protected_value),
        ]
    )
    result = _prepare(tmp_path, source)

    manifest, manifest_bytes = _manifest(result.bundle_path)
    data_path = result.bundle_path / preparation.DATA_FILENAME
    data_bytes = data_path.read_bytes()
    parquet = pq.ParquetFile(data_path)
    frame = parquet.read().to_pandas()
    receipt_bytes = result.receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)

    assert set(manifest) == preparation._MANIFEST_KEYS
    assert len(manifest) == 17
    assert manifest["schema_version"] == 1
    assert manifest["purpose"] == "cc02_development_only_sales"
    assert manifest["columns"] == ["Store", "Date", "Sales"]
    assert manifest["dtypes"] == {"Store": "int64", "Date": "datetime64[us]", "Sales": "int64"}
    assert manifest["sort_order"] == ["Store", "Date"]
    assert manifest["row_count"] == 2
    assert manifest["store_count"] == 2
    assert manifest["date_min"] == "2015-06-01"
    assert manifest["date_max"] == "2015-07-03"
    assert manifest["data_file"] == "sales.parquet"
    assert manifest["data_sha256"] == hashlib.sha256(data_bytes).hexdigest()
    assert manifest["data_bytes"] == len(data_bytes)
    assert hashlib.sha256(manifest_bytes).hexdigest() == result.manifest_sha256
    assert parquet.schema_arrow.names == ["Store", "Date", "Sales"]
    assert parquet.schema_arrow.field("Store").type == pa.int64()
    assert parquet.schema_arrow.field("Date").type == pa.timestamp("us")
    assert parquet.schema_arrow.field("Sales").type == pa.int64()
    assert tuple(str(frame[column].dtype) for column in frame.columns) == (
        "int64",
        "datetime64[us]",
        "int64",
    )
    assert frame.to_dict("records") == [
        {"Store": 1, "Date": pd.Timestamp("2015-06-01"), "Sales": 4},
        {"Store": 2, "Date": pd.Timestamp("2015-07-03"), "Sales": 0},
    ]
    assert receipt["designation"] == provider.PREPARATION_RECORD_DESIGNATION
    assert (
        receipt["preparation"]["permission_status"]
        == "not authenticated or activated by this component"
    )
    assert receipt["runtime"]["uv_lock_sha256"]
    assert receipt["output"]["data_sha256"] == result.data_sha256
    assert result.receipt_path.parent != result.bundle_path
    assert protected_value.encode() not in data_bytes
    assert protected_value.encode() not in manifest_bytes
    assert protected_value.encode() not in receipt_bytes
    assert protected_day.encode() not in manifest_bytes
    assert protected_day.encode() not in receipt_bytes
    assert not (result.bundle_path / "preparation_record.json").exists()


def test_deterministic_parquet_and_manifest_identity_for_same_projection(tmp_path: Path) -> None:
    rows = [
        _record(2, "2015-07-03", 0, open_value=0),
        _record(1, "2015-06-02", 5),
        _record(1, "2015-06-01", 6),
    ]
    source_a = _csv_bytes(rows)
    source_b = _csv_bytes(list(reversed(rows)))
    config_a = _config(source_a)
    config_b = replace(
        _config(source_b),
        custodian_preparation_authorization_reference="synthetic-only:preparation-authorization:v2",
        provider_loading_approval_reference="synthetic-only:provider-loading:PENDING:v2",
        preflight_reference="synthetic-only:preflight:PENDING:v2",
    )
    first = _prepare(tmp_path, source_a, config=config_a, suffix="first")
    second = _prepare(tmp_path, source_a, config=config_a, suffix="second")
    shuffled = _prepare(tmp_path, source_b, config=config_b, suffix="shuffled")

    assert (first.bundle_path / preparation.DATA_FILENAME).read_bytes() == (
        second.bundle_path / preparation.DATA_FILENAME
    ).read_bytes()
    assert (first.bundle_path / preparation.MANIFEST_FILENAME).read_bytes() == (
        second.bundle_path / preparation.MANIFEST_FILENAME
    ).read_bytes()
    assert first.data_sha256 == second.data_sha256
    assert first.manifest_sha256 == second.manifest_sha256
    assert (first.bundle_path / preparation.DATA_FILENAME).read_bytes() == (
        shuffled.bundle_path / preparation.DATA_FILENAME
    ).read_bytes()
    first_manifest, _ = _manifest(first.bundle_path)
    shuffled_manifest, _ = _manifest(shuffled.bundle_path)
    for key in (
        "custodian_preparation_authorization_reference",
        "provider_loading_approval_reference",
        "preflight_reference",
    ):
        first_manifest.pop(key)
        shuffled_manifest.pop(key)
    assert first_manifest == shuffled_manifest


def test_excluded_sales_change_does_not_change_retained_projection(tmp_path: Path) -> None:
    development = _record(1, "2015-07-03", 10)
    protected_a = _record(1, "2015-07-04", 100)
    protected_b = _record(1, "2015-07-04", 987654321)
    source_a = _csv_bytes([development, protected_a])
    source_b = _csv_bytes([development, protected_b])
    first = _prepare(tmp_path, source_a, suffix="a")
    second = _prepare(
        tmp_path,
        source_b,
        config=_config(
            source_b,
            preparation_reference="synthetic-only:preparation-authorization:reauthorized",
            provider_reference="synthetic-only:provider-loading:PENDING:reauthorized",
            preflight_reference="synthetic-only:preflight:PENDING:reauthorized",
        ),
        suffix="b",
    )

    assert (first.bundle_path / preparation.DATA_FILENAME).read_bytes() == (
        second.bundle_path / preparation.DATA_FILENAME
    ).read_bytes()
    assert list(
        pq.read_table(first.bundle_path / preparation.DATA_FILENAME).column("Sales").to_pylist()
    ) == [10]


def test_row_group_and_size_limits_are_enforced_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10), _record(2, "2015-07-02", 20)])
    monkeypatch.setattr(preparation, "MAX_ROWS", 1)
    with pytest.raises(preparation.PreparationError, match="row limit"):
        _prepare(tmp_path, source)
    monkeypatch.setattr(preparation, "MAX_ROWS", provider.MAX_ROWS)
    monkeypatch.setattr(preparation, "MAX_DATA_BYTES", 1)
    with pytest.raises(preparation.PreparationError, match="byte limit"):
        _prepare(tmp_path, source, suffix="data-limit")
    monkeypatch.setattr(preparation, "MAX_DATA_BYTES", provider.MAX_DATA_BYTES)
    monkeypatch.setattr(preparation, "MAX_MANIFEST_BYTES", 1)
    with pytest.raises(preparation.PreparationError, match="manifest.*byte limit"):
        _prepare(tmp_path, source, suffix="manifest-limit")
    monkeypatch.setattr(preparation, "MAX_MANIFEST_BYTES", provider.MAX_MANIFEST_BYTES)
    monkeypatch.setattr(preparation, "MAX_ROW_GROUPS", 0)
    with pytest.raises(preparation.PreparationError, match="row-group limit"):
        _prepare(tmp_path, source, suffix="row-group-limit")

    assert not (
        tmp_path / "data" / "interim" / "cc02_development" / "fixture-cc02-preparation"
    ).exists()


@pytest.mark.parametrize("occupied_kind", ["empty-directory", "bundle-file", "receipt"])
def test_existing_destinations_are_rejected_without_modification(
    tmp_path: Path, occupied_kind: str
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    config = _config(source)
    bundle_root, receipt_root = _roots(tmp_path)
    final_bundle = bundle_root / config.artifact_id
    final_receipt_dir = receipt_root / config.artifact_id
    if occupied_kind == "empty-directory":
        final_bundle.mkdir(parents=True)
    elif occupied_kind == "bundle-file":
        final_bundle.mkdir(parents=True)
        (final_bundle / "keep.txt").write_text("keep", encoding="utf-8")
    else:
        final_receipt_dir.mkdir(parents=True)
        (final_receipt_dir / "preparation_record.json").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        preparation._prepare_partition_from_bytes(
            config, source, bundle_root=bundle_root, receipt_root=receipt_root
        )

    if occupied_kind == "bundle-file":
        assert (final_bundle / "keep.txt").read_text(encoding="utf-8") == "keep"
    if occupied_kind == "receipt":
        assert (final_receipt_dir / "preparation_record.json").read_text(encoding="utf-8") == "keep"
    assert not list(bundle_root.glob(".stage-*"))


def test_writer_failure_cleans_only_current_staging_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    unrelated = tmp_path / "data" / "interim" / "cc02_development" / ".stage-unrelated"
    unrelated.mkdir(parents=True)

    def fail_write(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic writer failure")

    monkeypatch.setattr(preparation.pq, "write_table", fail_write)
    with pytest.raises(OSError, match="synthetic writer failure"):
        _prepare(tmp_path, source)

    assert list(unrelated.iterdir()) == []
    assert not list(unrelated.parent.glob(".stage-fixture-cc02-preparation-*"))
    assert not (unrelated.parent / "fixture-cc02-preparation").exists()


def test_receipt_write_failure_keeps_published_bundle_and_unrelated_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    config = _config(source)
    bundle_root, receipt_root = _roots(tmp_path)
    unrelated = bundle_root / ".stage-unrelated" / "keep.txt"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"unrelated bytes")
    original = preparation._write_file
    failure_canary = "SENSITIVE-RECEIPT-FAILURE-CANARY"
    receipt_write_attempted = False

    def fail_receipt(path: Path, content: bytes) -> None:
        nonlocal receipt_write_attempted
        if path.name == "preparation_record.json":
            assert (bundle_root / config.artifact_id).is_dir()
            receipt_write_attempted = True
            raise OSError(failure_canary)
        original(path, content)

    monkeypatch.setattr(preparation, "_write_file", fail_receipt)
    with pytest.raises(preparation.PreparationError, match="no approval was issued") as caught:
        _prepare(tmp_path, source, config=config)

    bundle = bundle_root / config.artifact_id
    manifest = _assert_published_bundle_integrity(bundle)
    receipt_dir = receipt_root / config.artifact_id
    assert receipt_write_attempted
    assert receipt_dir.is_dir()
    assert list(receipt_dir.iterdir()) == []
    assert not (receipt_dir / "preparation_record.json").exists()
    assert manifest["provider_loading_approval_reference"].endswith("PENDING:v1")
    assert failure_canary not in str(caught.value)
    assert unrelated.read_bytes() == b"unrelated bytes"
    assert not list(bundle_root.glob(f".stage-{config.artifact_id}-*"))


def test_late_receipt_directory_collision_preserves_marker_and_unbound_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    config = _config(source)
    bundle_root, receipt_root = _roots(tmp_path)
    unrelated = receipt_root / "unrelated" / "keep.txt"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"unrelated receipt bytes")
    final_receipt_dir = receipt_root / config.artifact_id
    marker = final_receipt_dir / "keep.bin"
    original = preparation._rename_final_directory
    collision_canary = "SENSITIVE-RECEIPT-COLLISION-CANARY"
    collision_injected = False

    def publish_then_collide(staging: Path, destination: Path) -> None:
        nonlocal collision_injected
        original(staging, destination)
        assert destination.is_dir()
        final_receipt_dir.mkdir()
        marker.write_bytes(collision_canary.encode("ascii"))
        collision_injected = True

    monkeypatch.setattr(preparation, "_rename_final_directory", publish_then_collide)
    with pytest.raises(preparation.PreparationError, match="no approval was issued") as caught:
        _prepare(tmp_path, source, config=config)

    bundle = bundle_root / config.artifact_id
    manifest = _assert_published_bundle_integrity(bundle)
    assert collision_injected
    assert marker.read_bytes() == collision_canary.encode("ascii")
    assert {path.name for path in final_receipt_dir.iterdir()} == {"keep.bin"}
    assert not (final_receipt_dir / "preparation_record.json").exists()
    assert manifest["provider_loading_approval_reference"].endswith("PENDING:v1")
    assert collision_canary not in str(caught.value)
    assert unrelated.read_bytes() == b"unrelated receipt bytes"
    assert not list(bundle_root.glob(f".stage-{config.artifact_id}-*"))


def test_manifest_publication_failure_cleans_staging_and_never_publishes_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    original = preparation.os.rename

    def fail_manifest(
        source_path: os.PathLike[str] | str, destination: os.PathLike[str] | str
    ) -> None:
        if Path(source_path).name.startswith(".partition_manifest.json"):
            raise OSError("synthetic manifest publication failure")
        original(source_path, destination)

    monkeypatch.setattr(preparation.os, "rename", fail_manifest)
    bundle_root, _ = _roots(tmp_path)
    with pytest.raises(OSError, match="manifest publication"):
        _prepare(tmp_path, source)
    assert not (bundle_root / "fixture-cc02-preparation").exists()
    assert not list(bundle_root.glob(".stage-*"))


def test_final_rename_collision_preserves_preexisting_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])
    bundle_root, _ = _roots(tmp_path)
    final = bundle_root / "fixture-cc02-preparation"
    original = preparation._rename_final_directory

    def collide(staging: Path, destination: Path) -> None:
        assert (staging / preparation.DATA_FILENAME).is_file()
        assert (staging / preparation.MANIFEST_FILENAME).is_file()
        destination.mkdir()
        (destination / "keep.txt").write_text("preexisting", encoding="utf-8")
        raise FileExistsError("synthetic final rename collision")

    monkeypatch.setattr(preparation, "_rename_final_directory", collide)
    with pytest.raises(FileExistsError, match="collision"):
        _prepare(tmp_path, source)
    monkeypatch.setattr(preparation, "_rename_final_directory", original)
    assert (final / "keep.txt").read_text(encoding="utf-8") == "preexisting"
    assert not list(bundle_root.glob(".stage-*"))


def test_final_directory_rename_never_replaces_even_an_empty_destination(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    destination = tmp_path / "destination"
    staging.mkdir()
    (staging / "new.txt").write_text("new", encoding="utf-8")
    destination.mkdir()

    with pytest.raises(FileExistsError):
        preparation._rename_final_directory(staging, destination)

    assert staging.is_dir()
    assert (staging / "new.txt").read_text(encoding="utf-8") == "new"
    assert destination.is_dir()
    assert list(destination.iterdir()) == []


def test_traversal_and_injected_reparse_aliases_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(preparation.PreparationError, match="traversal"):
        preparation._assert_no_aliases(tmp_path / ".." / "outside")

    alias_root = tmp_path / "alias-root"
    alias_root.mkdir()
    original_inode = alias_root.stat().st_ino
    monkeypatch.setattr(preparation, "_is_alias", lambda info: info.st_ino == original_inode)
    with pytest.raises(preparation.PreparationError, match="reparse"):
        preparation._assert_no_aliases(alias_root / "child")


def test_real_symlink_path_is_rejected_when_host_allows_directory_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"directory symlinks are unavailable: {error}")
    with pytest.raises(preparation.PreparationError, match="symlink or reparse"):
        preparation._assert_no_aliases(alias / "child")


def test_no_external_approval_object_or_stl_call_is_created_by_preparation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _csv_bytes([_record(1, "2015-07-03", 10)])

    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("preparation must not execute STL")

    monkeypatch.setattr(analysis, "decompose_development_sales", unexpected)
    result = _prepare(tmp_path, source)
    _, manifest_bytes = _manifest(result.bundle_path)
    receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
    assert b"synthetic-only:provider-loading:PENDING:v1" in manifest_bytes
    assert "not authenticated" in receipt["preparation"]["permission_status"]
    assert not isinstance(result, provider.DevelopmentInputApproval)


def test_production_command_only_describes_contract_or_fails_without_file_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def unexpected_open(*args: object, **kwargs: object) -> object:
        pytest.fail("production CLI must not open any data path")

    monkeypatch.setattr(Path, "open", unexpected_open)
    monkeypatch.setattr(Path, "read_bytes", unexpected_open)
    monkeypatch.setattr(provider, "_read_approved_bytes", unexpected_open)

    assert preparation.cli_main(["--describe-input-contract"]) == 0
    described = json.loads(capsys.readouterr().out)
    assert described["date_ceiling"] == "2015-07-03"
    assert "includes protected-period bytes" in described["custody_note"]
    assert "fails closed" in described["default_execution"]
    assert "no data-file I/O" in described["contract_description"]
    assert "--execute-once" in described["one_time_execution"]
    assert "not approving authority" in described["authorization"]
    assert "separate approval" in described["downstream_gates"]
    with pytest.raises(SystemExit):
        preparation.cli_main([])
    with pytest.raises(SystemExit):
        preparation.cli_main(["--source", str(tmp_path / "train.csv")])


def test_synthetic_partition_loads_through_accepted_provider_and_runs_stl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start = date(2015, 4, 11)
    rows = [
        _record(7, (start + timedelta(days=index)).isoformat(), 900 + 17 * index + index % 7)
        for index in range(84)
    ]
    source = _csv_bytes(rows)
    result = _prepare(tmp_path, source)
    bundle_root, _ = _roots(tmp_path)
    monkeypatch.setattr(provider, "_approved_bundle_root", lambda: bundle_root)
    approval = _fixture_approval(result.bundle_path)

    loaded = provider.load_approved_development_sales(approval)
    run = provider.decompose_approved_development_sales(approval)
    output_manifest = analysis.export_decomposition_outputs(run, tmp_path / "stl-output")
    exported = json.loads(output_manifest.read_text(encoding="utf-8"))

    assert len(loaded.frame) == 84
    assert len(run.components) == 84
    assert run.provenance.source_kind == "approved_development_only"
    assert run.provenance.partition_data_sha256 == result.data_sha256
    assert run.provenance.partition_manifest_sha256 == result.manifest_sha256
    assert exported["source"]["partition_snapshot"]["data_file_bytes_sha256"] == result.data_sha256
    assert (
        exported["source"]["partition_snapshot"]["manifest_file_bytes_sha256"]
        == result.manifest_sha256
    )
    assert exported["designation"] == "approved_development_only"
