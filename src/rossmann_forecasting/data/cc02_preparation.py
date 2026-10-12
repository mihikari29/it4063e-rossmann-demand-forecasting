"""Fixture-tested preparation for a CC-02 development-only Sales partition.

The transformation helpers accept a bounded byte snapshot; they do not open a source file. The
production CLI defaults to no source access and delegates its one-use path to a fixed-source
custodian gate. Preparation configuration references are provenance labels, not authenticated
permissions.
"""

from __future__ import annotations

import csv
import ctypes
import errno
import hashlib
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from rossmann_forecasting.data import cc02_development as provider

SOURCE_COLUMNS = (
    "Store",
    "DayOfWeek",
    "Date",
    "Sales",
    "Customers",
    "Open",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
)
OUTPUT_COLUMNS = provider.SOURCE_COLUMNS
DEVELOPMENT_CEILING = provider.DEVELOPMENT_CEILING
PURPOSE = provider.PURPOSE
DATA_FILENAME = provider.DATA_FILENAME
MANIFEST_FILENAME = provider.MANIFEST_FILENAME
MAX_DATA_BYTES = provider.MAX_DATA_BYTES
MAX_MANIFEST_BYTES = provider.MAX_MANIFEST_BYTES
MAX_ROWS = provider.MAX_ROWS
MAX_ROW_GROUPS = provider.MAX_ROW_GROUPS

REFERENCE_SOURCE_BYTES = 38_057_952
REFERENCE_SOURCE_SHA256 = "f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc"
EXPECTED_SOURCE_PATH = Path("data/raw/rossmann/train.csv")
EXPECTED_HEADER = SOURCE_COLUMNS
_ARTIFACT_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SIGNED_INTEGER = re.compile(r"[+-]?[0-9]+\Z")
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1
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


class PreparationError(ValueError):
    """Raised when a synthetic source snapshot or staged bundle is invalid."""


@dataclass(frozen=True, slots=True)
class PreparationConfiguration:
    """Inert source identity and provenance labels for one preparation.

    These values are not credentials or permissions. The fixture-only API never authenticates
    them. The production command constructs this record only after its separate authorization
    packet and custody-evidence checks pass.
    """

    artifact_id: str
    expected_source_bytes: int
    expected_source_sha256: str
    source_lineage_reference: str
    custodian_preparation_authorization_reference: str
    provider_loading_approval_reference: str
    preflight_reference: str


@dataclass(frozen=True, slots=True)
class PreparationResult:
    """Published synthetic bundle identity and its separate preparation receipt."""

    bundle_path: Path
    receipt_path: Path
    data_sha256: str
    manifest_sha256: str
    data_bytes: int
    row_count: int
    store_count: int


def _validate_configuration(config: PreparationConfiguration) -> None:
    if not isinstance(config, PreparationConfiguration):
        raise PreparationError("preparation configuration is required")
    if not isinstance(config.artifact_id, str) or not _ARTIFACT_ID.fullmatch(config.artifact_id):
        raise PreparationError("artifact_id must be a simple lowercase identifier")
    if type(config.expected_source_bytes) is not int or config.expected_source_bytes <= 0:
        raise PreparationError("expected source byte count must be a positive integer")
    if not isinstance(config.expected_source_sha256, str) or not _SHA256.fullmatch(
        config.expected_source_sha256
    ):
        raise PreparationError("expected source identity must include a lowercase SHA-256")
    for name in (
        "source_lineage_reference",
        "custodian_preparation_authorization_reference",
        "provider_loading_approval_reference",
        "preflight_reference",
    ):
        value = getattr(config, name)
        if not isinstance(value, str) or not value or value.strip() != value:
            raise PreparationError(f"{name} must be a non-empty external reference")


def _parse_signed_int64(token: str, field: str) -> int:
    if not _SIGNED_INTEGER.fullmatch(token):
        raise PreparationError(f"eligible {field} value is not a base-10 integer")

    sign = token[0] if token[0] in "+-" else ""
    digits = token[1:] if sign else token
    significant_digits = digits.lstrip("0")
    if not significant_digits:
        return 0

    magnitude_limit = "9223372036854775808" if sign == "-" else "9223372036854775807"
    if len(significant_digits) > len(magnitude_limit) or (
        len(significant_digits) == len(magnitude_limit) and significant_digits > magnitude_limit
    ):
        raise PreparationError(f"eligible {field} value is outside signed int64")

    normalized_token = f"{sign}{significant_digits}"
    value = int(normalized_token)
    if not _INT64_MIN <= value <= _INT64_MAX:
        raise PreparationError(f"eligible {field} value is outside signed int64")
    return value


def _extract_development_sales(
    source_bytes: bytes, config: PreparationConfiguration
) -> pd.DataFrame:
    """Validate and project a verified byte snapshot without opening any path."""

    _validate_configuration(config)
    if not isinstance(source_bytes, bytes):
        raise PreparationError("source snapshot must be immutable bytes")
    if len(source_bytes) != config.expected_source_bytes:
        raise PreparationError("source snapshot byte count differs from the configured identity")
    if hashlib.sha256(source_bytes).hexdigest() != config.expected_source_sha256:
        raise PreparationError("source snapshot SHA-256 differs from the configured identity")

    try:
        decoded = source_bytes.decode("utf-8", errors="strict")
        reader = csv.reader(io.StringIO(decoded, newline=""), strict=True)
        header = next(reader, None)
        if header != list(EXPECTED_HEADER) or len(set(header or ())) != len(EXPECTED_HEADER):
            raise PreparationError(
                "source header is missing, duplicated, reordered, or unsupported"
            )

        stores: list[int] = []
        dates: list[datetime] = []
        sales: list[int] = []
        keys: set[tuple[int, date]] = set()
        for row in reader:
            if len(row) != len(EXPECTED_HEADER):
                raise PreparationError("source CSV contains a malformed record")
            date_token = row[2]
            try:
                parsed_date = date.fromisoformat(date_token)
            except ValueError:
                raise PreparationError("source CSV contains an invalid calendar date") from None
            if parsed_date.isoformat() != date_token:
                raise PreparationError("source CSV date is not canonical YYYY-MM-DD")
            if parsed_date.isoformat() > DEVELOPMENT_CEILING:
                # Do not parse, summarize, or retain protected row values after date classification.
                continue

            store = _parse_signed_int64(row[0], "Store")
            if store <= 0:
                raise PreparationError("eligible Store values must be positive")
            value = _parse_signed_int64(row[3], "Sales")
            key = (store, parsed_date)
            if key in keys:
                raise PreparationError("eligible source contains duplicate Store × Date keys")
            keys.add(key)
            stores.append(store)
            dates.append(datetime(parsed_date.year, parsed_date.month, parsed_date.day))
            sales.append(value)
    except PreparationError:
        raise
    except (UnicodeDecodeError, csv.Error, StopIteration):
        raise PreparationError("source snapshot is not a valid UTF-8 CSV") from None

    if not stores:
        raise PreparationError("source snapshot contains no eligible development records")

    frame = pd.DataFrame(
        {
            "Store": pd.Series(stores, dtype="int64"),
            "Date": pd.Series(pd.DatetimeIndex(dates).as_unit("us")),
            "Sales": pd.Series(sales, dtype="int64"),
        }
    )
    frame = frame.sort_values(["Store", "Date"], kind="stable", ignore_index=True)
    try:
        validated = provider.validate_development_sales_frame(frame)
    except (TypeError, ValueError):
        raise PreparationError(
            "prepared development projection violates the accepted provider contract"
        ) from None
    if len(validated) != len(stores):
        raise PreparationError("eligible row retention check failed")
    return validated


def _approved_bundle_root() -> Path:
    """Return the same fixed repository-relative allowlist root as the accepted provider."""

    repository = Path(__file__).absolute().parents[3]
    return repository / "data" / "interim" / "cc02_development"


def _receipt_root() -> Path:
    repository = Path(__file__).absolute().parents[3]
    return repository / "reports" / "generated" / "cc02_custodian"


def _is_alias(info: os.stat_result) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & reparse_flag)


def _assert_no_aliases(path: Path) -> None:
    """Reject symlink/reparse components without resolving them through another path."""

    if ".." in path.parts:
        raise PreparationError("preparation path cannot contain traversal components")
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            raise PreparationError("preparation path cannot be inspected safely") from None
        if _is_alias(info):
            raise PreparationError("preparation path contains a symlink or reparse point")


def _safe_json_bytes(value: dict[str, Any]) -> bytes:
    try:
        return (
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise PreparationError("preparation metadata is not valid JSON") from None


def _runtime_identity() -> dict[str, Any]:
    repository = Path(__file__).absolute().parents[3]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        lock_sha256 = hashlib.sha256((repository / "uv.lock").read_bytes()).hexdigest()
    except (OSError, subprocess.SubprocessError):
        raise PreparationError(
            "code revision and locked environment identity are unavailable"
        ) from None
    return {
        "code_revision": revision,
        "code_worktree_dirty": dirty,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "pyarrow": pa.__version__,
        "uv_lock_sha256": lock_sha256,
    }


def _build_manifest(
    config: PreparationConfiguration, frame: pd.DataFrame, data_path: Path
) -> tuple[dict[str, Any], bytes]:
    data_size = data_path.stat().st_size
    if data_size <= 0 or data_size > MAX_DATA_BYTES:
        raise PreparationError("staged Parquet is empty or exceeds the provider byte limit")
    parquet = pq.ParquetFile(data_path)
    if parquet.metadata.num_rows > MAX_ROWS:
        raise PreparationError("staged Parquet exceeds the provider row limit")
    if parquet.metadata.num_row_groups > MAX_ROW_GROUPS:
        raise PreparationError("staged Parquet exceeds the provider row-group limit")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "artifact_id": config.artifact_id,
        "purpose": PURPOSE,
        "source_lineage_reference": config.source_lineage_reference,
        "custodian_preparation_authorization_reference": (
            config.custodian_preparation_authorization_reference
        ),
        "provider_loading_approval_reference": config.provider_loading_approval_reference,
        "preflight_reference": config.preflight_reference,
        "data_file": DATA_FILENAME,
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "data_bytes": data_size,
        "row_count": len(frame),
        "store_count": int(frame["Store"].nunique()),
        "columns": list(OUTPUT_COLUMNS),
        "dtypes": {"Store": "int64", "Date": "datetime64[us]", "Sales": "int64"},
        "sort_order": ["Store", "Date"],
        "date_min": frame["Date"].min().date().isoformat(),
        "date_max": frame["Date"].max().date().isoformat(),
    }
    if set(manifest) != _MANIFEST_KEYS:
        raise PreparationError("prepared manifest does not match the accepted provider field set")
    content = _safe_json_bytes(manifest)
    if len(content) > MAX_MANIFEST_BYTES:
        raise PreparationError("prepared manifest exceeds the provider byte limit")
    return manifest, content


def _write_file(path: Path, content: bytes) -> None:
    with path.open("xb") as destination:
        destination.write(content)
        destination.flush()
        os.fsync(destination.fileno())


def _rename_final_directory(staging: Path, destination: Path) -> None:
    """Publish a complete sibling directory with an atomic no-replace operation."""

    if destination.exists() or destination.is_symlink():
        raise FileExistsError("immutable preparation destination already exists")
    if os.name == "nt":
        # Windows os.rename fails when the destination exists, unlike POSIX rename.
        os.rename(staging, destination)
        return
    if platform.system() == "Linux":
        # Linux renameat2(RENAME_NOREPLACE) closes the check/rename race without dependencies.
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise PreparationError("atomic no-replace directory rename is unavailable")
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        result = renameat2(-100, os.fsencode(staging), -100, os.fsencode(destination), 1)
        if result != 0:
            error_number = ctypes.get_errno()
            if error_number == errno.ENOSYS:
                raise PreparationError("atomic no-replace directory rename is unavailable")
            raise OSError(error_number, os.strerror(error_number), str(destination))
        return
    raise PreparationError("atomic no-replace directory rename is unsupported on this platform")


def _preparation_receipt(
    config: PreparationConfiguration,
    manifest: dict[str, Any],
    manifest_bytes: bytes,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "designation": "fixture-only preparation output; no permission is conveyed",
        "source": {
            "documented_path": EXPECTED_SOURCE_PATH.as_posix(),
            "expected_bytes": config.expected_source_bytes,
            "expected_sha256": config.expected_source_sha256,
            "lineage_reference": config.source_lineage_reference,
        },
        "preparation": {
            "artifact_id": config.artifact_id,
            "date_rule": f"Date <= {DEVELOPMENT_CEILING}",
            "fields_read_for_projection": ["Store", "Date", "Sales"],
            "fields_emitted": list(OUTPUT_COLUMNS),
            "transform": (
                "strict date filter, exact signed-int64 projection, duplicate rejection, "
                "stable Store/Date sort"
            ),
            "random_seed": None,
            "randomness": "not applicable; deterministic transformation",
            "authorization_references": {
                "custodian_preparation": config.custodian_preparation_authorization_reference,
                "provider_loading": config.provider_loading_approval_reference,
                "preflight": config.preflight_reference,
            },
            "permission_status": "not authenticated or activated by this component",
        },
        "runtime": runtime,
        "output": {
            "data_file": DATA_FILENAME,
            "data_sha256": manifest["data_sha256"],
            "data_bytes": manifest["data_bytes"],
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "manifest_bytes": len(manifest_bytes),
            "row_count": manifest["row_count"],
            "store_count": manifest["store_count"],
            "columns": manifest["columns"],
            "dtypes": manifest["dtypes"],
            "date_min": manifest["date_min"],
            "date_max": manifest["date_max"],
            "checks": [
                "exact configured source byte count and SHA-256",
                "strict source CSV header and record width",
                "development ceiling and every eligible row retained once",
                "unique Store/Date keys and deterministic order",
                "provider schema, limits, and manifest field set",
            ],
        },
    }


def _prepare_partition_from_bytes(
    config: PreparationConfiguration,
    source_bytes: bytes,
    *,
    bundle_root: Path,
    receipt_root: Path,
) -> PreparationResult:
    """Internal byte-snapshot seam for synthetic tests; it never opens a source path."""

    _validate_configuration(config)
    if not bundle_root.is_absolute() or not receipt_root.is_absolute():
        raise PreparationError("bundle and receipt roots must be absolute paths")
    _assert_no_aliases(bundle_root)
    _assert_no_aliases(receipt_root)

    frame = _extract_development_sales(source_bytes, config)
    final_bundle = bundle_root / config.artifact_id
    final_receipt_dir = receipt_root / config.artifact_id
    _assert_no_aliases(final_bundle)
    _assert_no_aliases(final_receipt_dir)
    if final_bundle.exists() or final_receipt_dir.exists() or final_bundle.is_symlink():
        raise FileExistsError("immutable preparation destination already exists")

    bundle_root.mkdir(parents=True, exist_ok=True)
    receipt_root.mkdir(parents=True, exist_ok=True)
    _assert_no_aliases(bundle_root)
    _assert_no_aliases(receipt_root)
    if final_bundle.exists() or final_receipt_dir.exists() or final_bundle.is_symlink():
        raise FileExistsError("immutable preparation destination already exists")

    staging = Path(tempfile.mkdtemp(prefix=f".stage-{config.artifact_id}-", dir=bundle_root))
    try:
        data_path = staging / DATA_FILENAME
        arrow_schema = pa.schema(
            [
                pa.field("Store", pa.int64(), nullable=False),
                pa.field("Date", pa.timestamp("us", tz=None), nullable=False),
                pa.field("Sales", pa.int64(), nullable=False),
            ]
        )
        table = pa.Table.from_arrays(
            [
                pa.array(frame["Store"], type=pa.int64(), from_pandas=False),
                pa.array(frame["Date"], type=pa.timestamp("us"), from_pandas=False),
                pa.array(frame["Sales"], type=pa.int64(), from_pandas=False),
            ],
            schema=arrow_schema,
        )
        pq.write_table(
            table,
            data_path,
            version="2.6",
            compression="zstd",
            compression_level=3,
            row_group_size=100_000,
            use_dictionary=False,
            data_page_version="1.0",
            coerce_timestamps="us",
            allow_truncated_timestamps=False,
            use_deprecated_int96_timestamps=False,
            write_statistics=True,
            store_schema=True,
        )

        decoded = pq.read_table(data_path).to_pandas()
        try:
            decoded = provider.validate_development_sales_frame(decoded)
        except (TypeError, ValueError):
            raise PreparationError(
                "staged Parquet does not satisfy the accepted provider frame contract"
            ) from None
        if str(decoded["Date"].dtype) != "datetime64[us]" or str(decoded["Sales"].dtype) != "int64":
            raise PreparationError(
                "staged Parquet decoded dtypes differ from the preparation contract"
            )
        if not decoded.equals(frame):
            raise PreparationError(
                "staged Parquet values differ from the retained source projection"
            )

        manifest, manifest_bytes = _build_manifest(config, decoded, data_path)
        staged_manifest = staging / MANIFEST_FILENAME
        temporary_manifest = staging / f".{MANIFEST_FILENAME}.tmp"
        _write_file(temporary_manifest, manifest_bytes)
        os.rename(temporary_manifest, staged_manifest)

        # The manifest is the last file published inside staging. Validate its exact bounded bytes.
        if staged_manifest.stat().st_size > MAX_MANIFEST_BYTES:
            raise PreparationError("staged manifest exceeds the provider byte limit")
        if json.loads(staged_manifest.read_text(encoding="utf-8")) != manifest:
            raise PreparationError("staged manifest differs from the validated manifest")

        runtime = _runtime_identity()
        receipt = _preparation_receipt(config, manifest, manifest_bytes, runtime)
        receipt_bytes = _safe_json_bytes(receipt)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        data_sha256 = manifest["data_sha256"]

        # The final rename is atomic and refuses to replace a destination on supported platforms.
        _rename_final_directory(staging, final_bundle)

        try:
            final_receipt_dir.mkdir(parents=False, exist_ok=False)
            receipt_path = final_receipt_dir / "preparation_record.json"
            _write_file(receipt_path, receipt_bytes)
        except BaseException:
            # The bundle is complete but deliberately remains without an approval binding.
            # Keep it for explicit review/reconciliation; never remove an immutable publication.
            raise PreparationError(
                "bundle was published but the separate receipt could not be written; "
                "no approval was issued"
            ) from None

        return PreparationResult(
            bundle_path=final_bundle,
            receipt_path=receipt_path,
            data_sha256=data_sha256,
            manifest_sha256=manifest_sha256,
            data_bytes=manifest["data_bytes"],
            row_count=manifest["row_count"],
            store_count=manifest["store_count"],
        )
    except BaseException:
        if staging.exists():
            try:
                shutil.rmtree(staging)
            except OSError:
                # An orphaned hidden staging directory is inert and requires reviewed cleanup.
                pass
        raise


def input_contract() -> dict[str, Any]:
    """Return the no-source-access contract advertised by the production command."""

    return {
        "status": "fixture-only preparation helpers exist; real-source execution is disabled",
        "production_source": EXPECTED_SOURCE_PATH.as_posix(),
        "documented_source_bytes": REFERENCE_SOURCE_BYTES,
        "documented_source_sha256": REFERENCE_SOURCE_SHA256,
        "output_root": "data/interim/cc02_development/<artifact_id>/",
        "output_files": [DATA_FILENAME, MANIFEST_FILENAME],
        "columns": list(OUTPUT_COLUMNS),
        "date_ceiling": DEVELOPMENT_CEILING,
        "current_cli_behavior": (
            "describes this contract or fails closed; --execute-once requires a fixed, "
            "hash-bound external authorization packet and never accepts a source-path override"
        ),
        "authorization": (
            "this component does not authenticate or grant source-access, preparation, provider, "
            "analysis, or publication permission; the external approval process "
            "remains authoritative"
        ),
        "custody_note": (
            "a future custodian read mechanically includes protected bytes in the mixed source; "
            "provider loading, STL execution, and findings publication need separate approval"
        ),
    }


def cli_main(argv: list[str] | None = None) -> int:
    """Describe the contract or invoke the separately gated one-time custodian procedure."""

    import argparse

    parser = argparse.ArgumentParser(
        prog="rossmann-prepare-cc02-development",
        description=(
            "Describe the fixture-tested CC-02 contract. A fixed, hash-bound external "
            "authorization packet is required for one-time source preparation."
        ),
    )
    parser.add_argument(
        "--describe-input-contract",
        action="store_true",
        help="Print the contract without opening a data file.",
    )
    parser.add_argument(
        "--execute-once",
        action="store_true",
        help=(
            "Run the fixed-source procedure once using its external authorization packet; "
            "there is no source-path or approval-reference override."
        ),
    )
    args = parser.parse_args(argv)
    if args.describe_input_contract:
        if args.execute_once:
            parser.error("--describe-input-contract and --execute-once are mutually exclusive")
        from rossmann_forecasting.data.cc02_custodian_execution import authorization_contract

        contract = input_contract()
        contract["execution_authorization"] = authorization_contract()
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0
    if args.execute_once:
        from rossmann_forecasting.data.cc02_custodian_execution import (
            run_fixed_source_preparation_once,
        )

        try:
            result = run_fixed_source_preparation_once()
        except PreparationError as error:
            parser.exit(
                2, f"custodian preparation stopped before/within the authorized run: {error}\n"
            )
        print(
            json.dumps(
                {
                    "bundle_path": result.bundle_path.as_posix(),
                    "receipt_path": result.receipt_path.as_posix(),
                    "data_sha256": result.data_sha256,
                    "manifest_sha256": result.manifest_sha256,
                    "data_bytes": result.data_bytes,
                    "row_count": result.row_count,
                    "store_count": result.store_count,
                    "next_gate": (
                        "independent bundle verification; this command does not load the provider "
                        "or run STL"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    parser.error(
        "no source was opened; use --describe-input-contract or, only after the external "
        "custodian authorization gate, --execute-once"
    )
