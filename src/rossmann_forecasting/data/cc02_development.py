"""Load one externally approved, development-only CC-02 Sales partition.

This module validates application-level bindings and bundle contents. It cannot establish who
created a binding, prove physical custody, or replace operating-system access controls.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from rossmann_forecasting.analysis.seasonal_decomposition import (
    MAX_ELIGIBLE_DATE,
    SOURCE_COLUMNS,
    DecompositionRun,
    InputProvenance,
)

PURPOSE = "cc02_development_only_sales"
DEVELOPMENT_CEILING = "2015-07-03"
DATA_FILENAME = "sales.parquet"
MANIFEST_FILENAME = "partition_manifest.json"
MAX_DATA_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_ROWS = 1_200_000
MAX_ROW_GROUPS = 10_000
MAX_PREPARATION_RECEIPT_BYTES = 1024 * 1024
PREPARATION_RECORD_DESIGNATION = (
    "CC-02 development-only partition preparation record; no approval or permission is conveyed"
)
_ARTIFACT_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "artifact_id",
        "purpose",
        "source_lineage_reference",
        "custodian_preparation_authorization_reference",
        "provider_loading_approval_reference",
        "preflight_reference",
        "data_file",
        "data_sha256",
        "data_bytes",
        "row_count",
        "store_count",
        "columns",
        "dtypes",
        "sort_order",
        "date_min",
        "date_max",
    }
)


class DevelopmentInputError(ValueError):
    """Raised when an approval binding or its single approved bundle is invalid."""


@dataclass(frozen=True, slots=True)
class DevelopmentInputApproval:
    """Externally established approval binding for one immutable local bundle.

    Constructing this record is not an authorization mechanism. A trusted caller must obtain its
    values from the separately reviewed approval process before passing it to the loader.
    """

    artifact_id: str
    purpose: str
    bundle_location: str
    data_filename: str
    manifest_filename: str
    expected_data_sha256: str
    expected_manifest_sha256: str
    development_ceiling: str
    source_lineage_reference: str
    custodian_preparation_authorization_reference: str
    provider_loading_approval_reference: str
    preflight_reference: str


@dataclass(frozen=True, slots=True)
class ApprovedDevelopmentSales:
    """Copy-safe projection and provenance returned only after full bundle validation."""

    _frame: pd.DataFrame = field(repr=False, compare=False)
    artifact_id: str
    data_sha256: str
    manifest_sha256: str
    provenance: InputProvenance

    @property
    def frame(self) -> pd.DataFrame:
        """Return a deep copy so callers cannot mutate this validated snapshot."""

        return self._frame.copy(deep=True)


@dataclass(frozen=True, slots=True)
class DevelopmentBundleVerification:
    """Content identities and counts from a read-only, unbound bundle verification."""

    artifact_id: str
    data_sha256: str
    manifest_sha256: str
    preparation_receipt_sha256: str
    data_bytes: int
    row_count: int
    store_count: int
    date_min: str
    date_max: str


def _approved_bundle_root() -> Path:
    """Return the one repository-relative allowlisted input root."""

    # absolute() normalizes the repository path without silently resolving a junction or symlink.
    repository = Path(__file__).absolute().parents[3]
    return repository / "data" / "interim" / "cc02_development"


def _valid_reference(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise DevelopmentInputError(f"{field_name} must be a non-empty external reference")
    return value


def _valid_sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise DevelopmentInputError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def validate_development_binding(approval: DevelopmentInputApproval | None) -> None:
    """Validate binding authority metadata and exact path allowlist before reading files.

    This checks the supplied record and lexical bundle identity. It does not authenticate the
    approver, inspect file bytes, or establish the partition's custody history.
    """

    if not isinstance(approval, DevelopmentInputApproval):
        raise DevelopmentInputError("an external DevelopmentInputApproval binding is required")
    if not isinstance(approval.artifact_id, str) or not _ARTIFACT_ID.fullmatch(
        approval.artifact_id
    ):
        raise DevelopmentInputError("artifact_id must be a simple lowercase identifier")
    if approval.purpose != PURPOSE:
        raise DevelopmentInputError(f"approval purpose must be exactly {PURPOSE!r}")
    if approval.data_filename != DATA_FILENAME:
        raise DevelopmentInputError(f"approved data filename must be {DATA_FILENAME!r}")
    if approval.manifest_filename != MANIFEST_FILENAME:
        raise DevelopmentInputError(f"approved manifest filename must be {MANIFEST_FILENAME!r}")
    _valid_sha256(approval.expected_data_sha256, "expected_data_sha256")
    _valid_sha256(approval.expected_manifest_sha256, "expected_manifest_sha256")
    if approval.development_ceiling != DEVELOPMENT_CEILING:
        raise DevelopmentInputError(f"development ceiling must be exactly {DEVELOPMENT_CEILING}")
    for field_name in (
        "source_lineage_reference",
        "custodian_preparation_authorization_reference",
        "provider_loading_approval_reference",
        "preflight_reference",
    ):
        _valid_reference(getattr(approval, field_name), field_name)

    if not isinstance(approval.bundle_location, str) or not approval.bundle_location:
        raise DevelopmentInputError("bundle_location must be the exact approved local path")
    supplied = Path(approval.bundle_location)
    if not supplied.is_absolute():
        raise DevelopmentInputError("bundle_location must be an absolute local path")
    if ".." in supplied.parts:
        raise DevelopmentInputError("bundle_location cannot contain traversal components")
    expected = _approved_bundle_root() / approval.artifact_id
    if _normalized_path(supplied) != _normalized_path(expected):
        raise DevelopmentInputError(
            "bundle_location is outside the fixed CC-02 development bundle allowlist"
        )


def _normalized_path(path: Path) -> str:
    return os.path.normcase(str(path.absolute()))


def _is_reparse_point(info: os.stat_result) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISLNK(info.st_mode) or bool(attributes & reparse_flag)


def _assert_regular_path_without_aliases(path: Path) -> None:
    """Reject missing, non-regular, symlink, and reparse components before file access."""

    components = [*reversed(path.parents), path]
    final_info: os.stat_result | None = None
    for component in components:
        try:
            info = component.lstat()
        except OSError as error:
            raise DevelopmentInputError(
                f"approved bundle path is unavailable: {component}"
            ) from error
        if _is_reparse_point(info):
            raise DevelopmentInputError(f"approved bundle path contains an alias: {component}")
        final_info = info
    if final_info is None or not stat.S_ISREG(final_info.st_mode):
        raise DevelopmentInputError(f"approved bundle file is not a regular file: {path.name}")


def _read_approved_bytes(path: Path, *, max_bytes: int) -> bytes:
    """Read one bounded snapshot from an already allowlisted regular file."""

    try:
        with path.open("rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
                raise DevelopmentInputError(f"approved file exceeds the {max_bytes}-byte limit")
            content = source.read(max_bytes + 1)
            after = os.fstat(source.fileno())
    except DevelopmentInputError:
        raise
    except OSError as error:
        raise DevelopmentInputError(f"could not read approved file {path.name}") from error
    if len(content) > max_bytes:
        raise DevelopmentInputError(f"approved file exceeds the {max_bytes}-byte limit")
    if len(content) != before.st_size or after.st_size != before.st_size:
        raise DevelopmentInputError(f"approved file changed while being read: {path.name}")
    return content


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DevelopmentInputError(f"manifest contains duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise DevelopmentInputError(f"manifest contains unsupported JSON value {value!r}")


def _parse_manifest(content: bytes) -> dict[str, Any]:
    try:
        manifest = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except DevelopmentInputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DevelopmentInputError("partition manifest is not valid UTF-8 JSON") from error
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_KEYS:
        raise DevelopmentInputError("partition manifest has an unsupported field set")
    return manifest


def validate_development_sales_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the exact three-column CC-02 frame and return a deep copy.

    Sales uses native NumPy ``int64`` or ``float64``. The floating representation preserves null,
    NaN, and infinity values for the existing CC-02 segment-breaking behavior; zeros are retained.
    """

    if not isinstance(frame, pd.DataFrame):
        raise DevelopmentInputError("decoded partition must be a pandas DataFrame")
    if tuple(frame.columns) != SOURCE_COLUMNS:
        raise DevelopmentInputError("partition columns must be exactly Store, Date, Sales in order")
    source = frame.copy(deep=True)
    if source.empty:
        raise DevelopmentInputError("development partition must contain at least one row")
    if str(source["Store"].dtype) != "int64":
        raise DevelopmentInputError("Store must use native int64 without coercion")
    if source["Store"].isna().any() or source["Store"].le(0).any():
        raise DevelopmentInputError("Store values must be positive and non-null")
    if str(source["Date"].dtype) not in {"datetime64[ns]", "datetime64[us]"}:
        raise DevelopmentInputError("Date must use timezone-naive datetime64[ns] or datetime64[us]")
    if source["Date"].isna().any():
        raise DevelopmentInputError("Date values cannot be null")
    if source["Date"].dt.tz is not None:
        raise DevelopmentInputError("Date must be timezone-naive")
    if not source["Date"].eq(source["Date"].dt.normalize()).all():
        raise DevelopmentInputError("Date values must be calendar timestamps at midnight")
    if source["Date"].gt(MAX_ELIGIBLE_DATE).any():
        raise DevelopmentInputError(
            f"partition contains Date after the development ceiling {DEVELOPMENT_CEILING}"
        )
    if str(source["Sales"].dtype) not in {"int64", "float64"}:
        raise DevelopmentInputError("Sales must use native int64 or float64 without coercion")
    if source.duplicated(["Store", "Date"]).any():
        raise DevelopmentInputError("partition must have unique (Store, Date) keys")
    if not pd.MultiIndex.from_frame(source[["Store", "Date"]]).is_monotonic_increasing:
        raise DevelopmentInputError("partition must be sorted by Store then Date ascending")
    return source


def _validate_manifest(manifest: dict[str, Any], approval: DevelopmentInputApproval) -> None:
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise DevelopmentInputError("partition manifest schema_version must be integer 1")
    expected_values = {
        "artifact_id": approval.artifact_id,
        "purpose": PURPOSE,
        "source_lineage_reference": approval.source_lineage_reference,
        "custodian_preparation_authorization_reference": (
            approval.custodian_preparation_authorization_reference
        ),
        "provider_loading_approval_reference": approval.provider_loading_approval_reference,
        "preflight_reference": approval.preflight_reference,
        "data_file": DATA_FILENAME,
        "data_sha256": approval.expected_data_sha256,
        "columns": list(SOURCE_COLUMNS),
        "dtypes": {"Store": "int64", "Date": None, "Sales": None},
        "sort_order": ["Store", "Date"],
    }
    for key, expected in expected_values.items():
        value = manifest[key]
        if key == "dtypes":
            if not isinstance(value, dict) or set(value) != set(SOURCE_COLUMNS):
                raise DevelopmentInputError("manifest dtypes must declare exactly the three fields")
            if (
                value["Store"] != "int64"
                or not isinstance(value["Date"], str)
                or value["Date"] not in {"datetime64[ns]", "datetime64[us]"}
            ):
                raise DevelopmentInputError("manifest Store/Date dtypes are unsupported")
            if not isinstance(value["Sales"], str) or value["Sales"] not in {
                "int64",
                "float64",
            }:
                raise DevelopmentInputError("manifest Sales dtype must be int64 or float64")
        elif value != expected:
            raise DevelopmentInputError(f"manifest {key} does not match the external approval")

    integer_fields = ("data_bytes", "row_count", "store_count")
    for key in integer_fields:
        if type(manifest[key]) is not int or manifest[key] <= 0:
            raise DevelopmentInputError(f"manifest {key} must be a positive integer")
    if manifest["data_bytes"] > MAX_DATA_BYTES:
        raise DevelopmentInputError("manifest data_bytes exceeds the provider size limit")
    if manifest["row_count"] > MAX_ROWS:
        raise DevelopmentInputError("manifest row_count exceeds the provider row limit")
    if manifest["store_count"] > manifest["row_count"]:
        raise DevelopmentInputError("manifest store_count cannot exceed row_count")
    for key in ("date_min", "date_max"):
        value = manifest[key]
        if not isinstance(value, str):
            raise DevelopmentInputError(f"manifest {key} must be an ISO calendar date")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise DevelopmentInputError(f"manifest {key} must be an ISO calendar date") from error
        if parsed.isoformat() != value or parsed > date.fromisoformat(DEVELOPMENT_CEILING):
            raise DevelopmentInputError(f"manifest {key} exceeds or violates the date ceiling")
    if manifest["date_min"] > manifest["date_max"]:
        raise DevelopmentInputError("manifest date_min must not be after date_max")


def _decode_parquet(content: bytes, manifest: dict[str, Any]) -> pd.DataFrame:
    try:
        parquet = pq.ParquetFile(pa.BufferReader(content))
        metadata = parquet.metadata
        if metadata.num_rows != manifest["row_count"] or metadata.num_rows > MAX_ROWS:
            raise DevelopmentInputError("Parquet row count does not match the approved manifest")
        if metadata.num_row_groups > MAX_ROW_GROUPS:
            raise DevelopmentInputError("Parquet row-group count exceeds the provider limit")
        schema = parquet.schema_arrow
        if schema.names != list(SOURCE_COLUMNS):
            raise DevelopmentInputError(
                "Parquet columns must be exactly Store, Date, Sales in order"
            )
        expected_types = {
            "Store": pa.int64(),
            "Date": pa.timestamp("ns" if manifest["dtypes"]["Date"] == "datetime64[ns]" else "us"),
            "Sales": pa.int64() if manifest["dtypes"]["Sales"] == "int64" else pa.float64(),
        }
        for name, expected_type in expected_types.items():
            if schema.field(name).type != expected_type:
                raise DevelopmentInputError(f"Parquet {name} physical type is not supported")
        frame = parquet.read().to_pandas()
    except DevelopmentInputError:
        raise
    except Exception as error:
        raise DevelopmentInputError(
            "approved partition bytes are not a valid supported Parquet file"
        ) from error
    validated = validate_development_sales_frame(frame)
    if str(validated["Sales"].dtype) != manifest["dtypes"]["Sales"]:
        raise DevelopmentInputError("decoded Sales dtype differs from the approved manifest")
    return validated


def _validate_unbound_manifest(manifest: dict[str, Any]) -> None:
    """Validate manifest semantics without treating references as an approval binding."""

    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise DevelopmentInputError("partition manifest schema_version must be integer 1")
    if not isinstance(manifest["artifact_id"], str) or not _ARTIFACT_ID.fullmatch(
        manifest["artifact_id"]
    ):
        raise DevelopmentInputError("manifest artifact_id must be a simple lowercase identifier")
    for key, expected in (
        ("purpose", PURPOSE),
        ("data_file", DATA_FILENAME),
        ("columns", list(SOURCE_COLUMNS)),
        ("sort_order", ["Store", "Date"]),
        (
            "dtypes",
            {"Store": "int64", "Date": "datetime64[us]", "Sales": "int64"},
        ),
    ):
        if manifest[key] != expected:
            raise DevelopmentInputError(
                f"partition manifest {key} violates the preparation contract"
            )
    for key in (
        "source_lineage_reference",
        "custodian_preparation_authorization_reference",
        "provider_loading_approval_reference",
        "preflight_reference",
    ):
        _valid_reference(manifest[key], f"manifest {key}")
    _valid_sha256(manifest["data_sha256"], "manifest data_sha256")
    for key in ("data_bytes", "row_count", "store_count"):
        if type(manifest[key]) is not int or manifest[key] <= 0:
            raise DevelopmentInputError(f"manifest {key} must be a positive integer")
    if manifest["data_bytes"] > MAX_DATA_BYTES:
        raise DevelopmentInputError("manifest data_bytes exceeds the provider size limit")
    if manifest["row_count"] > MAX_ROWS:
        raise DevelopmentInputError("manifest row_count exceeds the provider row limit")
    if manifest["store_count"] > manifest["row_count"]:
        raise DevelopmentInputError("manifest store_count cannot exceed row_count")
    for key in ("date_min", "date_max"):
        value = manifest[key]
        if not isinstance(value, str):
            raise DevelopmentInputError(f"manifest {key} must be an ISO calendar date")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise DevelopmentInputError(f"manifest {key} must be an ISO calendar date") from None
        if parsed.isoformat() != value or parsed > date.fromisoformat(DEVELOPMENT_CEILING):
            raise DevelopmentInputError(f"manifest {key} exceeds or violates the date ceiling")
    if manifest["date_min"] > manifest["date_max"]:
        raise DevelopmentInputError("manifest date_min must not be after date_max")


def _parse_preparation_receipt(content: bytes) -> dict[str, Any]:
    try:
        receipt = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except DevelopmentInputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DevelopmentInputError("preparation receipt is not valid UTF-8 JSON") from None
    if not isinstance(receipt, dict):
        raise DevelopmentInputError("preparation receipt must be a JSON object")
    return receipt


def verify_development_bundle_snapshot(
    data_bytes: bytes, manifest_bytes: bytes, preparation_receipt_bytes: bytes
) -> DevelopmentBundleVerification:
    """Verify three already-read byte snapshots without issuing or constructing a binding.

    This function establishes consistency of these bytes and the preparation receipt. It does not
    authenticate approval records, establish custody, or authorize provider loading or STL.
    """

    if not isinstance(data_bytes, bytes) or not isinstance(manifest_bytes, bytes):
        raise DevelopmentInputError("bundle verification requires immutable byte snapshots")
    if not isinstance(preparation_receipt_bytes, bytes):
        raise DevelopmentInputError("bundle verification requires an immutable receipt snapshot")
    if len(data_bytes) > MAX_DATA_BYTES:
        raise DevelopmentInputError("partition data exceeds the provider byte limit")
    if len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise DevelopmentInputError("partition manifest exceeds the provider byte limit")
    if len(preparation_receipt_bytes) > MAX_PREPARATION_RECEIPT_BYTES:
        raise DevelopmentInputError("preparation receipt exceeds the verification byte limit")

    manifest = _parse_manifest(manifest_bytes)
    _validate_unbound_manifest(manifest)
    data_sha256 = hashlib.sha256(data_bytes).hexdigest()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    receipt_sha256 = hashlib.sha256(preparation_receipt_bytes).hexdigest()
    if len(data_bytes) != manifest["data_bytes"]:
        raise DevelopmentInputError("partition data byte count differs from the manifest")
    if data_sha256 != manifest["data_sha256"]:
        raise DevelopmentInputError("partition data SHA-256 differs from the manifest")

    frame = _decode_parquet(data_bytes, manifest)
    if len(frame) != manifest["row_count"]:
        raise DevelopmentInputError("decoded row count differs from the manifest")
    store_count = int(frame["Store"].nunique())
    if store_count != manifest["store_count"]:
        raise DevelopmentInputError("decoded Store count differs from the manifest")
    actual_date_min = frame["Date"].min().date().isoformat()
    actual_date_max = frame["Date"].max().date().isoformat()
    if (actual_date_min, actual_date_max) != (manifest["date_min"], manifest["date_max"]):
        raise DevelopmentInputError("decoded Date bounds differ from the manifest")

    receipt = _parse_preparation_receipt(preparation_receipt_bytes)
    try:
        receipt_preparation = receipt["preparation"]
        receipt_source = receipt["source"]
        receipt_output = receipt["output"]
        receipt_authorizations = receipt_preparation["authorization_references"]
        if not all(
            isinstance(section, dict)
            for section in (
                receipt_preparation,
                receipt_source,
                receipt_output,
                receipt_authorizations,
            )
        ):
            raise TypeError
        receipt_checks = (
            type(receipt["schema_version"]) is int
            and receipt["schema_version"] == 1
            and receipt["designation"] == PREPARATION_RECORD_DESIGNATION
            and receipt_source["lineage_reference"] == manifest["source_lineage_reference"]
            and receipt_preparation["artifact_id"] == manifest["artifact_id"]
            and receipt_authorizations["custodian_preparation"]
            == manifest["custodian_preparation_authorization_reference"]
            and receipt_authorizations["provider_loading"]
            == manifest["provider_loading_approval_reference"]
            and receipt_authorizations["preflight"] == manifest["preflight_reference"]
            and receipt_output["data_file"] == DATA_FILENAME
            and receipt_output["data_sha256"] == data_sha256
            and type(receipt_output["data_bytes"]) is int
            and receipt_output["data_bytes"] == len(data_bytes)
            and receipt_output["manifest_sha256"] == manifest_sha256
            and type(receipt_output["manifest_bytes"]) is int
            and receipt_output["manifest_bytes"] == len(manifest_bytes)
            and type(receipt_output["row_count"]) is int
            and receipt_output["row_count"] == len(frame)
            and type(receipt_output["store_count"]) is int
            and receipt_output["store_count"] == store_count
            and receipt_output["columns"] == list(SOURCE_COLUMNS)
            and receipt_output["dtypes"] == manifest["dtypes"]
            and receipt_output["date_min"] == actual_date_min
            and receipt_output["date_max"] == actual_date_max
        )
    except (KeyError, TypeError):
        receipt_checks = False
    if not receipt_checks:
        raise DevelopmentInputError(
            "preparation receipt does not match the verified bundle and manifest snapshots"
        )

    return DevelopmentBundleVerification(
        artifact_id=manifest["artifact_id"],
        data_sha256=data_sha256,
        manifest_sha256=manifest_sha256,
        preparation_receipt_sha256=receipt_sha256,
        data_bytes=len(data_bytes),
        row_count=len(frame),
        store_count=store_count,
        date_min=actual_date_min,
        date_max=actual_date_max,
    )


def load_approved_development_sales(
    approval: DevelopmentInputApproval | None,
) -> ApprovedDevelopmentSales:
    """Load only the single bundle named by a trusted external approval binding.

    The loader reads the pinned manifest before the data file, validates both exact byte snapshots,
    then decodes the same in-memory Parquet bytes it hashed. The fixed limits (128 MiB data,
    64 KiB manifest, 1.2 million rows) bound local memory use for this small analysis input.
    """

    if approval is None:
        raise DevelopmentInputError("an external DevelopmentInputApproval binding is required")
    validate_development_binding(approval)
    bundle = Path(approval.bundle_location)
    data_path = bundle / DATA_FILENAME
    manifest_path = bundle / MANIFEST_FILENAME
    _assert_regular_path_without_aliases(manifest_path)
    _assert_regular_path_without_aliases(data_path)

    manifest_bytes = _read_approved_bytes(manifest_path, max_bytes=MAX_MANIFEST_BYTES)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_sha256 != approval.expected_manifest_sha256:
        raise DevelopmentInputError("partition manifest SHA-256 differs from external approval")
    manifest = _parse_manifest(manifest_bytes)
    _validate_manifest(manifest, approval)

    data_bytes = _read_approved_bytes(data_path, max_bytes=MAX_DATA_BYTES)
    if len(data_bytes) != manifest["data_bytes"]:
        raise DevelopmentInputError("partition byte size differs from the approved manifest")
    data_sha256 = hashlib.sha256(data_bytes).hexdigest()
    if data_sha256 != approval.expected_data_sha256 or data_sha256 != manifest["data_sha256"]:
        raise DevelopmentInputError("partition SHA-256 differs from external approval or manifest")

    frame = _decode_parquet(data_bytes, manifest)
    actual_bounds = (
        frame["Date"].min().date().isoformat(),
        frame["Date"].max().date().isoformat(),
    )
    if actual_bounds != (manifest["date_min"], manifest["date_max"]):
        raise DevelopmentInputError("partition date bounds differ from the approved manifest")
    if len(frame) != manifest["row_count"] or frame["Store"].nunique() != manifest["store_count"]:
        raise DevelopmentInputError("partition row/store counts differ from the approved manifest")

    provenance = InputProvenance(
        source_kind="approved_development_only",
        source_id=approval.artifact_id,
        preflight_reference=approval.preflight_reference,
        partition_data_sha256=data_sha256,
        partition_manifest_sha256=manifest_sha256,
        source_lineage_reference=approval.source_lineage_reference,
        custodian_preparation_authorization_reference=(
            approval.custodian_preparation_authorization_reference
        ),
        provider_loading_approval_reference=approval.provider_loading_approval_reference,
    )
    return ApprovedDevelopmentSales(
        _frame=frame.copy(deep=True),
        artifact_id=approval.artifact_id,
        data_sha256=data_sha256,
        manifest_sha256=manifest_sha256,
        provenance=provenance,
    )


def decompose_approved_development_sales(
    approval: DevelopmentInputApproval,
) -> DecompositionRun:
    """Load a verified bundle and pass only its copy-safe projection to the CC-02 API."""

    approved = load_approved_development_sales(approval)
    from rossmann_forecasting.analysis.seasonal_decomposition import (
        decompose_development_sales,
    )

    return decompose_development_sales(approved.frame, provenance=approved.provenance)
