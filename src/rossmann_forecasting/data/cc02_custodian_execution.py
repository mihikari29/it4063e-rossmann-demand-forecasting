"""One-use, fixed-source handoff from an authorized custodian to CC-02 preparation.

The command reads a fixed authorization packet and hashes its three separately held evidence
records before it can open the mixed Rossmann CSV. It records a no-replace execution marker before
source access, then passes one bounded byte snapshot to the already-reviewed preparation code.
The packet and references are not authenticated by this module: the custodian must verify the
owner's signed approvals and custody evidence out of band, as required by ADR-027.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import platform
import re
import stat
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rossmann_forecasting.data import cc02_preparation as preparation

AUTHORIZATION_RELATIVE_PATH = Path("data/authorizations/cc02_custodian_execution.json")
EVIDENCE_RELATIVE_ROOT = Path("data/authorizations/cc02_custodian")
EXECUTION_RECEIPTS_RELATIVE_ROOT = Path("reports/generated/cc02_custodian/execution_authorizations")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_ARTIFACT_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_EVIDENCE_NAMES = {
    "source_access_approval": "source_access_approval.json",
    "custody_record": "custody_record.json",
    "preparation_approval": "preparation_approval.json",
}
_MAX_AUTHORIZATION_BYTES = 64 * 1024
_MAX_EVIDENCE_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class EvidenceIdentity:
    record_id: str
    sha256: str


@dataclass(frozen=True, slots=True)
class CustodianExecutionAuthorization:
    """Structured execution packet; record IDs alone never satisfy its evidence checks."""

    execution_id: str
    custodian_name: str
    windows_user: str
    host_name: str
    valid_until_utc: str
    execution_commit: str
    lock_sha256: str
    source_path: str
    expected_source_bytes: int
    expected_source_sha256: str
    artifact_id: str
    source_lineage_reference: str
    custodian_preparation_authorization_reference: str
    provider_loading_approval_reference: str
    preflight_reference: str
    evidence: dict[str, EvidenceIdentity]


class CustodianExecutionError(preparation.PreparationError):
    """Raised before source access when the one-use custodian gate is incomplete or invalid."""


def _repository_root() -> Path:
    return Path(__file__).absolute().parents[3]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CustodianExecutionError(f"authorization contains duplicate key {key!r}")
        result[key] = value
    return result


def _read_regular_snapshot(path: Path, *, max_bytes: int, label: str) -> bytes:
    preparation._assert_no_aliases(path)
    try:
        with path.open("rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
                raise CustodianExecutionError(f"{label} is not a bounded regular file")
            content = source.read(max_bytes + 1)
            after = os.fstat(source.fileno())
    except CustodianExecutionError:
        raise
    except OSError:
        raise CustodianExecutionError(f"{label} could not be read") from None
    if (
        len(content) > max_bytes
        or len(content) != before.st_size
        or after.st_size != before.st_size
    ):
        raise CustodianExecutionError(f"{label} changed or exceeded its byte limit while read")
    return content


def _exact_object(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CustodianExecutionError(f"{label} has a missing or unsupported field set")
    return value


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value.strip() != value:
        raise CustodianExecutionError(f"{label} must be a non-empty string")
    return value


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise CustodianExecutionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _evidence_identity(value: object, label: str) -> EvidenceIdentity:
    record = _exact_object(value, {"record_id", "sha256"}, label)
    return EvidenceIdentity(
        record_id=_nonempty(record["record_id"], f"{label}.record_id"),
        sha256=_sha256(record["sha256"], f"{label}.sha256"),
    )


def _parse_authorization(
    content: bytes, *, require_documented_source: bool
) -> CustodianExecutionAuthorization:
    try:
        raw = json.loads(content.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except CustodianExecutionError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise CustodianExecutionError(
            "fixed custodian authorization is not valid UTF-8 JSON"
        ) from None

    packet = _exact_object(
        raw,
        {
            "schema_version",
            "execution_id",
            "custodian",
            "valid_until_utc",
            "procedure",
            "source_snapshot",
            "artifact_id",
            "source_lineage_reference",
            "custodian_preparation_authorization_reference",
            "provider_loading_approval_reference",
            "preflight_reference",
            "evidence",
        },
        "authorization",
    )
    if type(packet["schema_version"]) is not int or packet["schema_version"] != 1:
        raise CustodianExecutionError("authorization schema_version must be exactly 1")
    try:
        execution_id = str(uuid.UUID(_nonempty(packet["execution_id"], "execution_id")))
    except (ValueError, AttributeError):
        raise CustodianExecutionError("execution_id must be a canonical UUID") from None
    if execution_id != packet["execution_id"]:
        raise CustodianExecutionError("execution_id must be a lowercase canonical UUID")

    custodian = _exact_object(
        packet["custodian"], {"name", "windows_user", "host_name"}, "custodian"
    )
    procedure = _exact_object(packet["procedure"], {"commit", "lock_sha256"}, "procedure")
    source = _exact_object(
        packet["source_snapshot"], {"path", "bytes", "sha256"}, "source_snapshot"
    )
    evidence_raw = _exact_object(packet["evidence"], set(_EVIDENCE_NAMES), "evidence")
    evidence = {
        name: _evidence_identity(evidence_raw[name], f"evidence.{name}") for name in _EVIDENCE_NAMES
    }

    source_path = _nonempty(source["path"], "source_snapshot.path")
    source_bytes = source["bytes"]
    if type(source_bytes) is not int or source_bytes <= 0:
        raise CustodianExecutionError("source_snapshot.bytes must be a positive integer")
    source_sha256 = _sha256(source["sha256"], "source_snapshot.sha256")
    if require_documented_source and (
        source_path != preparation.EXPECTED_SOURCE_PATH.as_posix()
        or source_bytes != preparation.REFERENCE_SOURCE_BYTES
        or source_sha256 != preparation.REFERENCE_SOURCE_SHA256
    ):
        raise CustodianExecutionError(
            "authorization source identity must match the one documented Rossmann snapshot"
        )

    valid_until = _nonempty(packet["valid_until_utc"], "valid_until_utc")
    try:
        expires = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
    except ValueError:
        raise CustodianExecutionError("valid_until_utc must be an ISO-8601 UTC timestamp") from None
    if (
        expires.tzinfo is None
        or expires.utcoffset() is None
        or expires.utcoffset().total_seconds() != 0
    ):
        raise CustodianExecutionError("valid_until_utc must include a UTC offset")

    if not isinstance(procedure["commit"], str) or not _COMMIT.fullmatch(procedure["commit"]):
        raise CustodianExecutionError("procedure.commit must be a full lowercase Git commit")
    lock_sha256 = _sha256(procedure["lock_sha256"], "procedure.lock_sha256")
    artifact_id = _nonempty(packet["artifact_id"], "artifact_id")
    if not _ARTIFACT_ID.fullmatch(artifact_id):
        raise CustodianExecutionError("artifact_id must be a simple lowercase identifier")

    source_lineage_reference = _nonempty(
        packet["source_lineage_reference"], "source_lineage_reference"
    )
    preparation_reference = _nonempty(
        packet["custodian_preparation_authorization_reference"],
        "custodian_preparation_authorization_reference",
    )
    if source_lineage_reference != evidence["source_access_approval"].record_id:
        raise CustodianExecutionError(
            "source_lineage_reference must identify the hash-bound source-access approval"
        )
    if preparation_reference != evidence["preparation_approval"].record_id:
        raise CustodianExecutionError(
            "preparation reference must identify the hash-bound preparation approval"
        )

    return CustodianExecutionAuthorization(
        execution_id=execution_id,
        custodian_name=_nonempty(custodian["name"], "custodian.name"),
        windows_user=_nonempty(custodian["windows_user"], "custodian.windows_user"),
        host_name=_nonempty(custodian["host_name"], "custodian.host_name"),
        valid_until_utc=valid_until,
        execution_commit=procedure["commit"],
        lock_sha256=lock_sha256,
        source_path=source_path,
        expected_source_bytes=source_bytes,
        expected_source_sha256=source_sha256,
        artifact_id=artifact_id,
        source_lineage_reference=source_lineage_reference,
        custodian_preparation_authorization_reference=preparation_reference,
        provider_loading_approval_reference=_nonempty(
            packet["provider_loading_approval_reference"],
            "provider_loading_approval_reference",
        ),
        preflight_reference=_nonempty(packet["preflight_reference"], "preflight_reference"),
        evidence=evidence,
    )


def _verify_runtime_and_operator(
    authorization: CustodianExecutionAuthorization,
    *,
    runtime: dict[str, Any],
    windows_user: str,
    host_name: str,
    now: datetime,
) -> None:
    if runtime.get("code_worktree_dirty") is not False:
        raise CustodianExecutionError("execution requires a clean worktree")
    if authorization.execution_commit != runtime.get("code_revision"):
        raise CustodianExecutionError("authorization does not name the current execution commit")
    if authorization.lock_sha256 != runtime.get("uv_lock_sha256"):
        raise CustodianExecutionError("authorization does not name the current uv.lock identity")
    if authorization.windows_user.casefold() != windows_user.casefold():
        raise CustodianExecutionError("current Windows account is not the named custodian")
    if authorization.host_name.casefold() != host_name.casefold():
        raise CustodianExecutionError("current host is not the approved custodian host")
    expiry = datetime.fromisoformat(authorization.valid_until_utc.replace("Z", "+00:00"))
    if now.tzinfo is None or now.utcoffset() is None or now >= expiry:
        raise CustodianExecutionError(
            "custodian authorization is expired or runtime time is invalid"
        )


def _verify_evidence_files(
    authorization: CustodianExecutionAuthorization,
    *,
    evidence_root: Path,
) -> dict[str, str]:
    if not evidence_root.is_absolute():
        raise CustodianExecutionError("custodian evidence root must be absolute")
    folder = evidence_root / authorization.execution_id
    preparation._assert_no_aliases(folder)
    hashes: dict[str, str] = {}
    for key, filename in _EVIDENCE_NAMES.items():
        identity = authorization.evidence[key]
        content = _read_regular_snapshot(
            folder / filename, max_bytes=_MAX_EVIDENCE_BYTES, label=f"{key} evidence"
        )
        digest = hashlib.sha256(content).hexdigest()
        if digest != identity.sha256:
            raise CustodianExecutionError(f"{key} evidence SHA-256 differs from authorization")
        hashes[key] = digest
    return hashes


def _write_consumption_marker(
    authorization: CustodianExecutionAuthorization,
    *,
    evidence_hashes: dict[str, str],
    authorization_sha256: str,
    receipt_root: Path,
    started_at_utc: str,
) -> Path:
    if not receipt_root.is_absolute():
        raise CustodianExecutionError("execution receipt root must be absolute")
    preparation._assert_no_aliases(receipt_root)
    receipt_root.mkdir(parents=True, exist_ok=True)
    preparation._assert_no_aliases(receipt_root)
    receipt_path = receipt_root / f"{authorization.execution_id}.json"
    preparation._assert_no_aliases(receipt_path)
    marker = {
        "schema_version": 1,
        "designation": "one-use custodian execution consumed before source access",
        "execution_id": authorization.execution_id,
        "artifact_id": authorization.artifact_id,
        "custodian_name": authorization.custodian_name,
        "procedure_commit": authorization.execution_commit,
        "authorization_packet_sha256": authorization_sha256,
        "evidence_sha256": evidence_hashes,
        "source_snapshot": {
            "path": authorization.source_path,
            "bytes": authorization.expected_source_bytes,
            "sha256": authorization.expected_source_sha256,
        },
        "started_at_utc": started_at_utc,
        "source_access_armed": True,
    }
    try:
        preparation._write_file(receipt_path, preparation._safe_json_bytes(marker))
    except FileExistsError:
        raise CustodianExecutionError("this execution authorization was already consumed") from None
    return receipt_path


def _preflight_output_destination(root: Path, artifact_id: str, *, label: str) -> None:
    """Check a final immutable destination without creating or modifying any paths."""

    if not root.is_absolute() or ".." in root.parts:
        raise CustodianExecutionError(f"{label} output root must be absolute and traversal-free")
    destination = root / artifact_id
    try:
        preparation._assert_no_aliases(root)
        preparation._assert_no_aliases(destination)
    except preparation.PreparationError:
        raise CustodianExecutionError(f"{label} output path cannot be inspected safely") from None

    for component in [*reversed(root.parents), root]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            raise CustodianExecutionError(
                f"{label} output path cannot be inspected safely"
            ) from None
        if not stat.S_ISDIR(info.st_mode):
            raise CustodianExecutionError(f"{label} output ancestor is not a directory")

    try:
        destination.lstat()
    except FileNotFoundError:
        return
    except OSError:
        raise CustodianExecutionError(f"{label} output destination cannot be inspected") from None
    raise CustodianExecutionError(f"{label} immutable output destination already exists")


def _assert_execution_marker_absent(
    authorization: CustodianExecutionAuthorization, *, receipt_root: Path
) -> None:
    """Reject an already consumed identifier without creating or modifying the marker root."""

    marker_path = receipt_root / f"{authorization.execution_id}.json"
    try:
        preparation._assert_no_aliases(marker_path)
        marker_path.lstat()
    except FileNotFoundError:
        return
    except preparation.PreparationError:
        raise CustodianExecutionError("execution marker path cannot be inspected safely") from None
    except OSError:
        raise CustodianExecutionError("execution marker path cannot be inspected safely") from None
    raise CustodianExecutionError("this execution authorization was already consumed")


def _preflight_output_destinations(
    authorization: CustodianExecutionAuthorization,
    *,
    bundle_root: Path,
    preparation_receipt_root: Path,
) -> None:
    _preflight_output_destination(
        bundle_root, authorization.artifact_id, label="development bundle"
    )
    _preflight_output_destination(
        preparation_receipt_root,
        authorization.artifact_id,
        label="preparation receipt",
    )


def _read_fixed_source_snapshot(
    authorization: CustodianExecutionAuthorization,
    *,
    repository: Path,
) -> bytes:
    if authorization.source_path != preparation.EXPECTED_SOURCE_PATH.as_posix():
        raise CustodianExecutionError("only the fixed documented source path is permitted")
    source_path = repository / preparation.EXPECTED_SOURCE_PATH
    preparation._assert_no_aliases(source_path)
    try:
        with source_path.open("rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise CustodianExecutionError("fixed source is not a regular file")
            if before.st_size != authorization.expected_source_bytes:
                raise CustodianExecutionError("fixed source byte count differs from authorization")
            content = source.read(authorization.expected_source_bytes + 1)
            after = os.fstat(source.fileno())
    except CustodianExecutionError:
        raise
    except OSError:
        raise CustodianExecutionError("fixed Rossmann source could not be opened") from None
    if (
        len(content) != authorization.expected_source_bytes
        or len(content) != before.st_size
        or after.st_size != before.st_size
    ):
        raise CustodianExecutionError("fixed source changed or exceeded its approved size")
    if hashlib.sha256(content).hexdigest() != authorization.expected_source_sha256:
        raise CustodianExecutionError("fixed source SHA-256 differs from authorization")
    return content


def _execute_authorized_snapshot(
    authorization: CustodianExecutionAuthorization,
    *,
    authorization_bytes: bytes,
    evidence_root: Path,
    receipt_root: Path,
    bundle_root: Path,
    preparation_receipt_root: Path,
    source_reader: Callable[[], bytes],
    runtime: dict[str, Any],
    windows_user: str,
    host_name: str,
    now: datetime,
) -> preparation.PreparationResult:
    """Private seam for synthetic tests; production supplies only the fixed-source reader."""

    _verify_runtime_and_operator(
        authorization,
        runtime=runtime,
        windows_user=windows_user,
        host_name=host_name,
        now=now,
    )
    evidence_hashes = _verify_evidence_files(authorization, evidence_root=evidence_root)
    config = preparation.PreparationConfiguration(
        artifact_id=authorization.artifact_id,
        expected_source_bytes=authorization.expected_source_bytes,
        expected_source_sha256=authorization.expected_source_sha256,
        source_lineage_reference=authorization.source_lineage_reference,
        custodian_preparation_authorization_reference=(
            authorization.custodian_preparation_authorization_reference
        ),
        provider_loading_approval_reference=authorization.provider_loading_approval_reference,
        preflight_reference=authorization.preflight_reference,
    )
    preparation._validate_configuration(config)
    _assert_execution_marker_absent(authorization, receipt_root=receipt_root)
    _preflight_output_destinations(
        authorization,
        bundle_root=bundle_root,
        preparation_receipt_root=preparation_receipt_root,
    )
    _write_consumption_marker(
        authorization,
        evidence_hashes=evidence_hashes,
        authorization_sha256=hashlib.sha256(authorization_bytes).hexdigest(),
        receipt_root=receipt_root,
        started_at_utc=now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    )

    # No source reader is called until the structured packet, custodian identity, runtime, expiry,
    # evidence bytes, and one-use no-replace receipt have all passed.
    source_bytes = source_reader()
    return preparation._prepare_partition_from_bytes(
        config,
        source_bytes,
        bundle_root=bundle_root,
        receipt_root=preparation_receipt_root,
    )


def run_fixed_source_preparation_once() -> preparation.PreparationResult:
    """Run one approved preparation from the sole fixed source; never loads or analyzes it."""

    repository = _repository_root()
    authorization_path = repository / AUTHORIZATION_RELATIVE_PATH
    authorization_bytes = _read_regular_snapshot(
        authorization_path,
        max_bytes=_MAX_AUTHORIZATION_BYTES,
        label="fixed custodian authorization packet",
    )
    authorization = _parse_authorization(authorization_bytes, require_documented_source=True)
    runtime = preparation._runtime_identity()
    now = datetime.now(UTC)
    return _execute_authorized_snapshot(
        authorization,
        authorization_bytes=authorization_bytes,
        evidence_root=repository / EVIDENCE_RELATIVE_ROOT,
        receipt_root=repository / EXECUTION_RECEIPTS_RELATIVE_ROOT,
        bundle_root=preparation._approved_bundle_root(),
        preparation_receipt_root=preparation._receipt_root(),
        source_reader=lambda: _read_fixed_source_snapshot(authorization, repository=repository),
        runtime=runtime,
        windows_user=getpass.getuser(),
        host_name=platform.node(),
        now=now,
    )


def authorization_contract() -> dict[str, Any]:
    """Describe the external packet boundary without opening local source or approval files."""

    return {
        "packet_path": AUTHORIZATION_RELATIVE_PATH.as_posix(),
        "evidence_directory": EVIDENCE_RELATIVE_ROOT.as_posix() + "/<execution_id>/",
        "evidence_files": dict(_EVIDENCE_NAMES),
        "source_snapshot": {
            "path": preparation.EXPECTED_SOURCE_PATH.as_posix(),
            "bytes": preparation.REFERENCE_SOURCE_BYTES,
            "sha256": preparation.REFERENCE_SOURCE_SHA256,
        },
        "required_separate_evidence": [
            "owner source-access approval for the named custodian, mixed-source bytes, and scope",
            "custody evidence for that fixed snapshot and host",
            "owner preparation approval naming the exact execution commit and lock identity",
        ],
        "runtime_guards": [
            "exact documented source path, size, and SHA-256",
            "current named Windows account, host, clean Git commit, and uv.lock hash",
            "unexpired packet and hash-matched evidence files",
            "one-use no-replace execution marker before source open",
        ],
        "authority_note": (
            "packet fields and reference strings are not authenticated by Python; an external "
            "trusted approver and custodian must verify the signed evidence before the command"
        ),
        "downstream_gates": [
            "independent verification of the two-file bundle and immutable file hashes",
            "delegated external provider-binding approval for those exact hashes",
            "separate owner approval before provider loading and STL execution",
            "separate owner approval before findings publication",
        ],
    }
