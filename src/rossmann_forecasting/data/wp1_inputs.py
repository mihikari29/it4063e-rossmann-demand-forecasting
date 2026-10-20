"""Restricted WP1 v1 trusted-fixture conformance, never authenticated authority.

This verifier is not designed for untrusted or real Rossmann input decoding.
Callers must supply only reviewed, project-controlled synthetic fixture-generator bytes
or controlled synthetic test mutations. This is a caller precondition, not a guarantee
the verifier can authenticate. Hashes, manifests, receipts, custodian/authorization
references, input_kind, environment variables and bindings do not establish trust.
Do not use this module to prepare, verify, bind or load actual WP1 development datasets
or call it from a production ingestion path. All names/references are inert identifiers;
no loader, filesystem operation, aggregation, execution or approval issuer exists here.

Input byte limits precede decoding. Footer estimates are untrusted admission/rejection
hints. Arrow logical-output limits run after materialization; decoding may allocate more
than accepted output. Python, Arrow, pandas and native temporary allocations have no hard
process-memory budget. Malformed or erroneous fixtures may exhaust memory or terminate
the process. The owner accepts this residual risk only in restricted fixture testing.
WP1-S7-01: UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE CONTRACT APPROVED.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from rossmann_forecasting.forecasting.model_selection import (
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    KEY_COLUMNS,
    EvidenceReviewRequired,
    validate_candidate_records,
)
from rossmann_forecasting.forecasting.scenario_evaluation import build_scenario_population
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
)

SCHEMA_VERSION = 1
PURPOSE = "wp1_scenario_fixture_inputs"
DEVELOPMENT_CUTOFF = LAST_DEVELOPMENT_DATE.date().isoformat()
METADATA_FIELDS = ("Promo", "StoreType", "Assortment", "StateHoliday", "SchoolHoliday")
PERMITTED_USES = ("synthetic_fixture_verification", "synthetic_fixture_compatibility")
MAX_FILES = 10
MAX_MANIFEST_BYTES = 64 * 1024
MAX_RECEIPT_BYTES = 64 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024  # includes the receipt
MAX_PARQUET_BYTES = 8 * 1024 * 1024
MAX_ROWS = 50_000  # each table, at most five tables
MAX_COLUMNS = 12
MAX_ROW_GROUPS = 64
MAX_FOOTER_BYTES = 128 * 1024
MAX_DECODED_BYTES = 16 * 1024 * 1024  # Post-read output threshold, not a hard allocation cap.
MAX_TOTAL_DECODED_BYTES = 64 * 1024 * 1024  # Cumulative output threshold, not peak memory.
MAX_TEXT_LENGTH = 1024
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 10_000

_ROSTER = "M/observed_keys.parquet"
_MEMBERSHIP = "C/membership.parquet"
_CONFIGURATION = "M/lightgbm_configuration.json"
_CANDIDATE_FILES = {candidate: f"M/{candidate}.parquet" for candidate in CANDIDATE_IDS}
_ORIGINAL_FILES = {
    candidate: f"M/original_manifests/{candidate}.json" for candidate in CANDIDATE_IDS
}
_ORIGINAL_COMMANDS = dict(
    zip(
        CANDIDATE_IDS,
        ("rossmann-seasonal-naive", "rossmann-holt-winters", "rossmann-lightgbm"),
        strict=True,
    )
)
_REASON_FIELDS = ("unavailable_reason", "fit_failure_reason")
_CLAIM_LEVELS = (
    "observed_retrospective",
    "assumed_known_at_origin",
    "documented_known_at_origin",
)
_MANIFEST_FIELDS = {
    "schema_version",
    "purpose",
    "input_kind",
    "bundle_id",
    "development_cutoff",
    "h_enabled",
    "candidates",
    "metadata_fields",
    "windows",
    "files",
    "field_schemas",
    "population",
    "observed_key_sha256",
    "payload_sha256",
    "source_lineage_references",
    "observed_key_lineage_reference",
    "preparation",
    "availability_claims",
}
_PREPARATION_FIELDS = {
    "execution_id",
    "reference",
    "code_revision",
    "lock_sha256",
    "environment_references",
    "custodian_label",
    "authorization_reference",
}
_LIMITATIONS = (
    "Fixture-only conformance; caller must supply reviewed project-controlled synthetic fixtures.",
    "Technical conformance and byte identity only; no authorization or signer authentication.",
    "Synthetic input status, original evidence authenticity and physical custody are unverified.",
    "Origin and custody are unauthenticated; hashes, receipts and bindings do not establish trust.",
    "Real observed-roster independence/completeness is unverified; matching rows do not prove it.",
    "All availability claims are unverified declarations; use retrospective conditional grouping.",
    "Historical availability remains unverified, including declared known-at-origin claims.",
    "Future-date Promo is not a pre-origin plan; holidays do not prove published schedules.",
    "A Store snapshot does not prove historically unchanged StoreType or Assortment.",
    "Source Open is evaluation information, not a proven origin-known operational schedule.",
    "SN/HW legacy provenance and the recorded modified LightGBM worktree are not repaired here.",
    "Archive references are inert; referenced artifacts and historical execution are unverified.",
    "No permission to access real sources or prepare, verify, bind or load actual WP1 datasets.",
    "No hard peak-memory guarantee; Arrow output checks run after materialization.",
    "Python, Arrow, pandas and native temporaries have no hard process-memory budget.",
    "Malformed or erroneous fixtures may exhaust memory or terminate the process.",
    "WP1-S7-01: UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE CONTRACT APPROVED.",
    "No approval to execute L4 or grant real custody, execution or public release authority.",
    "No causal, inventory, savings or production-resource claim; real M/C/H and L4 remain NO-GO.",
)


class ScenarioInputError(ValueError):
    """A supplied fixture or reference record violates the restricted v1 contract."""


@dataclass(frozen=True)
class PayloadIdentity:
    logical_name: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class AvailabilityClaim:
    field: str
    original_source_identity: str
    level: str
    assumption_or_evidence_reference: str
    permitted_interpretation: str
    status: str = "unverified_declaration"


@dataclass(frozen=True)
class CandidateInputIdentity:
    candidate_id: str
    raw_column: str
    original_manifest_sha256: str
    original_evidence_reference: str
    original_reason_fields: tuple[str, ...]
    unavailable_reason_counts: tuple[tuple[str, int], ...]
    legacy_provenance_limitations: tuple[str, ...]
    # SN/HW have no separate configuration payload under the accepted archival contract.
    configuration_sha256: str | None


@dataclass(frozen=True)
class ScenarioInputVerification:
    """Frozen fixture-only findings and limitations; no trust, memory or execution grant."""

    bundle_id: str
    purpose: str
    schema_version: int
    development_cutoff: str
    manifest_sha256: str
    payload_sha256: str
    preparation_receipt_sha256: str
    verification_reference: str
    payloads: tuple[PayloadIdentity, ...]
    observed_key_sha256: str
    row_count: int
    store_count: int
    date_count: int
    origin_count: int
    date_min: str
    date_max: str
    candidate_ids: tuple[str, ...]
    candidates: tuple[CandidateInputIdentity, ...]
    enabled_scenario_dimensions: tuple[str, ...]
    source_lineage_references: tuple[str, ...]
    observed_key_lineage_reference: str
    availability_claims: tuple[AvailabilityClaim, ...]
    preparation_execution_id: str
    preparation_reference: str
    findings: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioInputBinding:
    """Synthetic identity-consistency labels only; constructing this grants no authority."""

    reference: str
    bundle_id: str
    purpose: str
    schema_version: int
    development_cutoff: str
    manifest_sha256: str
    payload_sha256: str
    preparation_receipt_sha256: str
    candidate_ids: tuple[str, ...]
    enabled_scenario_dimensions: tuple[str, ...]
    preparation_execution_id: str
    preparation_reference: str
    verification_reference: str
    permitted_uses: tuple[str, ...]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ScenarioInputError(message)


def _object(value: Any, fields: set[str], name: str) -> dict[str, Any]:
    _require(isinstance(value, dict) and set(value) == fields, f"Invalid {name} fields.")
    return value


def _reference(value: Any) -> str:
    _require(
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= MAX_TEXT_LENGTH
        and not any(ord(char) < 32 for char in value),
        "Invalid reference/text declaration.",
    )
    return value


def _references(value: Any) -> tuple[str, ...]:
    _require(isinstance(value, list) and 0 < len(value) <= 32, "Invalid reference list.")
    result = tuple(_reference(item) for item in value)
    _require(len(set(result)) == len(result), "Duplicate references.")
    return result


def _hash(value: Any, *, length: int = 64) -> str:
    _require(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value) is not None,
        "Invalid hash/revision declaration.",
    )
    return value


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _json(content: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in items:
            _require(key not in output, "Duplicate JSON keys.")
            output[key] = value
        return output

    def constant(_: str) -> None:
        raise ScenarioInputError("Invalid JSON numerical constant.")

    try:
        result = json.loads(
            content.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant
        )
        pending = [(result, 0)]
        nodes = 0
        while pending:
            value, depth = pending.pop()
            nodes += 1
            _require(
                depth <= MAX_JSON_DEPTH and nodes <= MAX_JSON_NODES,
                "JSON structural limits exceeded.",
            )
            if isinstance(value, str):
                _require(len(value) <= MAX_TEXT_LENGTH, "JSON string limit exceeded.")
            elif isinstance(value, float):
                _require(math.isfinite(value), "Invalid JSON non-finite number.")
            elif isinstance(value, dict):
                pending.extend((item, depth + 1) for pair in value.items() for item in pair)
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value)
        _require(isinstance(result, dict), "JSON must be an object.")
        return result
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ScenarioInputError):
            raise
        raise ScenarioInputError("Invalid strict UTF-8 JSON.") from None


def _snapshot(files: Mapping[str, bytes], receipt: bytes) -> dict[str, bytes]:
    _require(isinstance(files, Mapping), "Snapshot requires an in-memory mapping.")
    _require(
        isinstance(receipt, bytes) and len(receipt) <= MAX_RECEIPT_BYTES,
        "Receipt must be bounded immutable bytes.",
    )
    _require(0 < len(files) <= MAX_FILES, "Logical file count limit exceeded.")
    snapshot: dict[str, bytes] = {}
    total = len(receipt)
    for name, content in files.items():
        _require(
            isinstance(name, str)
            and len(name) <= 160
            and re.fullmatch(
                r"[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*/[A-Za-z0-9_]+\.(?:json|parquet)"
                r"|manifest\.json",
                name,
            )
            is not None,
            "Invalid logical filename; paths and aliases are forbidden.",
        )
        _require(name not in snapshot, "Duplicate logical filename.")
        _require(len(snapshot) < MAX_FILES, "Logical file count limit exceeded.")
        limit = (
            MAX_MANIFEST_BYTES
            if name == "manifest.json"
            else MAX_PARQUET_BYTES
            if name.endswith(".parquet")
            else MAX_ARCHIVE_BYTES
        )
        _require(
            isinstance(content, bytes) and 0 < len(content) <= limit,
            "Payload must be bounded immutable bytes.",
        )
        total += len(content)
        _require(total <= MAX_TOTAL_BYTES, "Total supplied byte limit exceeded.")
        snapshot[name] = content
    _require(len(snapshot) == len(files), "Conflicting mapping identities.")
    _require("manifest.json" in snapshot, "Missing manifest.json.")
    return snapshot


def _manifest(content: bytes) -> dict[str, Any]:
    manifest = _object(_json(content), _MANIFEST_FIELDS, "manifest")
    _require(
        type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
        "Unsupported schema version.",
    )
    _require(
        manifest["purpose"] == PURPOSE and manifest["input_kind"] == "synthetic_fixture",
        "Only the synthetic fixture purpose is supported.",
    )
    _require(
        isinstance(manifest["bundle_id"], str)
        and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", manifest["bundle_id"]) is not None,
        "Invalid bundle identity.",
    )
    _require(
        manifest["development_cutoff"] == DEVELOPMENT_CUTOFF and manifest["h_enabled"] is False,
        "Invalid development cutoff or H-enabled state.",
    )
    fields = manifest["metadata_fields"]
    _require(
        isinstance(fields, list) and fields == [x for x in METADATA_FIELDS if x in fields],
        "Invalid enabled metadata fields.",
    )
    expected_windows = [
        {
            "name": w.name,
            "forecast_origin": w.forecast_origin.date().isoformat(),
            "target_start": w.target_start.date().isoformat(),
            "target_end": w.target_end.date().isoformat(),
        }
        for w in APPROVED_DEVELOPMENT_WINDOWS
    ]
    _require(manifest["windows"] == expected_windows, "Unapproved origins/windows.")
    _hash(manifest["observed_key_sha256"])
    _hash(manifest["payload_sha256"])
    _references(manifest["source_lineage_references"])
    _reference(manifest["observed_key_lineage_reference"])
    prep = _object(manifest["preparation"], _PREPARATION_FIELDS, "preparation")
    for field in _PREPARATION_FIELDS - {"code_revision", "lock_sha256", "environment_references"}:
        _reference(prep[field])
    _hash(prep["code_revision"], length=40)
    _hash(prep["lock_sha256"])
    _references(prep["environment_references"])
    population = _object(
        manifest["population"],
        {
            "row_count",
            "store_count",
            "date_count",
            "origin_count",
            "date_min",
            "date_max",
        },
        "population",
    )
    for field in ("row_count", "store_count", "date_count", "origin_count"):
        _require(
            type(population[field]) is int and 0 < population[field] <= MAX_ROWS,
            "Invalid declared population count.",
        )
    return manifest


def _claims(manifest: dict[str, Any]) -> tuple[AvailabilityClaim, ...]:
    fields = manifest["metadata_fields"]
    declarations = _object(manifest["availability_claims"], set(fields), "availability claims")
    result = []
    for field in fields:
        claim = _object(
            declarations[field],
            {
                "original_source_identity",
                "level",
                "assumption_or_evidence_reference",
                "permitted_interpretation",
            },
            "availability claim",
        )
        for value in claim.values():
            _reference(value)
        _require(claim["level"] in _CLAIM_LEVELS, "Unsupported availability claim level.")
        _require(
            claim["original_source_identity"] in manifest["source_lineage_references"],
            "Availability claim source is absent from declared lineage.",
        )
        _require(
            claim["permitted_interpretation"] == "retrospective_conditional_grouping",
            "Availability declaration cannot permit origin-known or causal inference.",
        )
        result.append(AvailabilityClaim(field=field, **claim))
    return tuple(result)


def _inventory(snapshot: dict[str, bytes], manifest: dict[str, Any]) -> tuple[PayloadIdentity, ...]:
    expected = {_ROSTER, _CONFIGURATION, *_CANDIDATE_FILES.values(), *_ORIGINAL_FILES.values()}
    if manifest["metadata_fields"]:
        expected.add(_MEMBERSHIP)
    _require(set(snapshot) == expected | {"manifest.json"}, "Snapshot inventory mismatch.")
    inventory = _object(manifest["files"], expected, "file inventory")
    identities = []
    for name in sorted(expected):
        entry = _object(inventory[name], {"bytes", "sha256"}, "file identity")
        _require(
            type(entry["bytes"]) is int and entry["bytes"] == len(snapshot[name]),
            "Payload byte count mismatch.",
        )
        actual_hash = _sha(snapshot[name])
        _require(_hash(entry["sha256"]) == actual_hash, "Payload SHA-256 mismatch.")
        identities.append(PayloadIdentity(name, len(snapshot[name]), actual_hash))
    _require(
        _sha(_canonical(inventory)) == manifest["payload_sha256"],
        "Payload inventory digest mismatch.",
    )
    return tuple(identities)


def _column_types(
    name: str, reason_fields: tuple[str, ...], fields: list[str]
) -> dict[str, set[str]]:
    types = {
        "Store": {"int64"},
        "forecast_origin": {"timestamp[ns]", "timestamp[us]"},
        "Date": {"timestamp[ns]", "timestamp[us]"},
    }
    text = {"string", "large_string", "null"}
    numeric = {"int64", "double"}
    if name in _CANDIDATE_FILES.values():
        candidate = next(c for c, path in _CANDIDATE_FILES.items() if path == name)
        types.update(
            {
                "horizon": {"int8", "int16", "int64"},
                "validation_window": text - {"null"},
                "actual_sales": numeric,
                "source_open": numeric,
                FORECAST_COLUMNS[candidate]: numeric,
                "forecast_available": {"bool"},
                "primary_evaluation_eligible": {"bool"},
            }
        )
        types.update({field: text for field in reason_fields})
    elif name == _MEMBERSHIP:
        for field in fields:
            types[field] = (
                text | numeric | {"bool"}
                if field in {"Promo", "SchoolHoliday"}
                else text | numeric
                if field == "StateHoliday"
                else text
            )
    return types


def _inspect_parquet(
    content: bytes,
    declared: Any,
    allowed: dict[str, set[str]],
) -> tuple[pq.ParquetFile, int]:
    # Footer and Thrift bounds apply before constructing Arrow schema/metadata objects.
    _require(
        len(content) >= 12 and content[:4] == b"PAR1" and content[-4:] == b"PAR1",
        "Malformed Parquet envelope.",
    )
    footer_bytes = int.from_bytes(content[-8:-4], "little")
    _require(
        0 < footer_bytes <= MAX_FOOTER_BYTES and footer_bytes <= len(content) - 12,
        "Parquet footer limit exceeded.",
    )
    try:
        parquet = pq.ParquetFile(
            pa.BufferReader(content),
            thrift_string_size_limit=MAX_FOOTER_BYTES,
            thrift_container_size_limit=MAX_JSON_NODES,
        )
        metadata = parquet.metadata
        _require(
            0 < metadata.num_rows <= MAX_ROWS
            and metadata.num_columns <= MAX_COLUMNS
            and 0 < metadata.num_row_groups <= MAX_ROW_GROUPS,
            "Parquet metadata limits exceeded.",
        )
        schema = parquet.schema_arrow
        _require(
            len(schema.names) == len(set(schema.names)) and set(schema.names) == set(allowed),
            "Parquet columns violate the fixed schema.",
        )
        actual_schema = [{"name": field.name, "type": str(field.type)} for field in schema]
        _require(declared == actual_schema, "Declared field schema differs from Parquet.")
        for field in schema:
            _require(str(field.type) in allowed[field.name], "Unsupported Parquet physical type.")
        for group_index in range(metadata.num_row_groups):
            group = metadata.row_group(group_index)
            for column_index in range(group.num_columns):
                _require(
                    group.column(column_index).file_path in (None, ""),
                    "External Parquet column paths are forbidden.",
                )
        # Footer totals are untrusted estimates and cannot bound decoder allocations.
        decoded = sum(metadata.row_group(i).total_byte_size for i in range(metadata.num_row_groups))
        _require(0 <= decoded <= MAX_DECODED_BYTES, "Parquet uncompressed byte limit exceeded.")
        return parquet, decoded
    except ScenarioInputError:
        raise
    except Exception:
        raise ScenarioInputError("Malformed or unsupported in-memory Parquet metadata.") from None


def _decode_parquet(parquet: pq.ParquetFile) -> tuple[pd.DataFrame, int]:
    try:
        # PyArrow may allocate decoded pages and dictionary-expanded values inside read().
        # The output-size check below runs afterward and is not a hard allocation limit.
        table = parquet.read(use_threads=False)
        _require(table.nbytes <= MAX_DECODED_BYTES, "Decoded Arrow byte limit exceeded.")
        if "horizon" in table.column_names:
            # Check the original Arrow integers before pandas conversion or Phase 7's int16 cast.
            horizon = table.column("horizon")
            _require(
                pa.types.is_integer(horizon.type) and horizon.null_count == 0,
                "Original candidate horizons must be non-null integers from 1 through 14.",
            )
            minimum = pc.min(horizon).as_py()
            maximum = pc.max(horizon).as_py()
            _require(
                minimum >= 1 and maximum <= 14,
                "Original candidate horizons must be from 1 through 14.",
            )
        for field in table.schema:
            if pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
                maximum = pc.max(pc.utf8_length(table[field.name])).as_py()
                _require(
                    maximum is None or maximum <= MAX_TEXT_LENGTH, "Decoded string limit exceeded."
                )
        # Drop inert pandas metadata: it must not change the validated physical schema/index.
        frame = table.replace_schema_metadata(None).to_pandas(ignore_metadata=True)
        return frame, table.nbytes
    except ScenarioInputError:
        raise
    except Exception:
        raise ScenarioInputError("Malformed or unsupported in-memory Parquet.") from None


def _keys(frame: pd.DataFrame, *, roster: bool = False) -> pd.DataFrame:
    _require(frame["Store"].notna().all() and frame["Store"].gt(0).all(), "Invalid Store keys.")
    for column in ("forecast_origin", "Date"):
        values = frame[column]
        _require(
            values.notna().all()
            and values.dt.tz is None
            and values.eq(values.dt.normalize()).all(),
            "Invalid midnight/date keys.",
        )
    # Screen chronology before labels can reach the accepted evaluation layers, and
    # before converting arbitrary microsecond dates to the bounded nanosecond range.
    valid = pd.Series(False, index=frame.index)
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        valid |= frame["forecast_origin"].eq(window.forecast_origin) & frame["Date"].between(
            window.target_start, window.target_end
        )
    _require(
        valid.all() and frame["Date"].le(LAST_DEVELOPMENT_DATE).all(),
        "Canonical keys include unapproved/protected dates.",
    )
    _require(not frame.duplicated(list(KEY_COLUMNS)).any(), "Duplicate canonical keys.")
    canonical = frame.loc[:, list(KEY_COLUMNS)].copy()
    for column in ("forecast_origin", "Date"):
        canonical[column] = canonical[column].astype("datetime64[ns]")
    keys = canonical.sort_values(list(KEY_COLUMNS), kind="mergesort")
    keys = keys.reset_index(drop=True)
    if roster:
        _require(
            canonical.reset_index(drop=True).equals(keys),
            "Observed-key roster must be deterministically sorted.",
        )
    return keys


def _key_digest(keys: pd.DataFrame) -> str:
    # v1: ascending Store/origin/Date, ASCII Store\tISO origin\tISO Date\n, no header.
    digest = hashlib.sha256()
    for store, origin, target in keys.itertuples(index=False, name=None):
        digest.update(
            f"{store}\t{origin.date().isoformat()}\t{target.date().isoformat()}\n".encode("ascii")
        )
    return digest.hexdigest()


def _membership(frame: pd.DataFrame, keys: pd.DataFrame, fields: list[str]) -> None:
    _require(_keys(frame).equals(keys), "Metadata keys must exactly match the observed roster.")
    for field in fields:
        for value in frame[field].dropna().tolist():
            if field in {"Promo", "SchoolHoliday"}:
                _require(value in (0, 1, "0", "1"), "Invalid binary metadata code.")
            elif field == "StateHoliday" and not isinstance(value, str):
                _require(
                    not isinstance(value, bool) and value == 0, "Invalid numeric StateHoliday code."
                )
            else:
                _require(isinstance(value, str) and bool(value), "Invalid textual category code.")
        if field in {"StoreType", "Assortment"}:
            _require(
                frame.groupby("Store")[field].nunique(dropna=False).le(1).all(),
                "Contradictory static Store metadata.",
            )


def _receipt(content: bytes, manifest: dict[str, Any], manifest_hash: str) -> str:
    receipt = _object(
        _json(content),
        _PREPARATION_FIELDS
        | {
            "schema_version",
            "purpose",
            "bundle_id",
            "source_lineage_references",
            "manifest_sha256",
            "payload_sha256",
        },
        "preparation receipt",
    )
    expected = {
        **manifest["preparation"],
        **{
            field: manifest[field]
            for field in (
                "schema_version",
                "purpose",
                "bundle_id",
                "source_lineage_references",
                "payload_sha256",
            )
        },
        "manifest_sha256": manifest_hash,
    }
    _require(
        type(receipt["schema_version"]) is int and receipt == expected,
        "Preparation receipt identities are inconsistent.",
    )
    return _sha(content)


def verify_trusted_scenario_fixture_snapshot(
    files: Mapping[str, bytes],
    preparation_receipt_bytes: bytes,
) -> ScenarioInputVerification:
    """Check only reviewed project-controlled synthetic fixtures and controlled mutations.

    This verifier is not designed for untrusted or real Rossmann input decoding.
    The caller must establish the fixture precondition; synthetic origin is unauthenticated.
    Never use it for actual WP1 preparation, verification, binding, loading or production
    ingestion. Byte checks precede decoding, footer estimates are untrusted hints, and
    Arrow output checks follow materialization. There is no hard peak-memory guarantee;
    erroneous fixtures may exhaust memory or terminate the process. Every successful
    result carries these limitations and grants no real-source access or L4 approval.

    Payload SHA-256 is the hash of compact sorted UTF-8 JSON of the exact manifest
    `files` inventory (manifest excluded, avoiding a circular hash). The independent
    roster uses the explicitly documented ASCII key encoding in `_key_digest`.
    Archived JSON is bounded, parsed strictly, retained by byte hash and otherwise inert.
    Its original variable field sets are not the v1 envelope schema.
    """
    snapshot = _snapshot(files, preparation_receipt_bytes)
    manifest = _manifest(snapshot["manifest.json"])
    claims = _claims(manifest)
    identities = _inventory(snapshot, manifest)
    manifest_hash = _sha(snapshot["manifest.json"])
    receipt_hash = _receipt(preparation_receipt_bytes, manifest, manifest_hash)
    candidates = _object(manifest["candidates"], set(CANDIDATE_IDS), "candidates")
    tables = {_ROSTER, *_CANDIDATE_FILES.values()}
    if manifest["metadata_fields"]:
        tables.add(_MEMBERSHIP)
    schemas = _object(manifest["field_schemas"], tables, "field schemas")
    reason_fields: dict[str, tuple[str, ...]] = {}
    for candidate in CANDIDATE_IDS:
        entry = _object(
            candidates[candidate],
            {
                "raw_column",
                "original_evidence_reference",
                "original_reason_fields",
                "legacy_provenance_limitations",
            },
            "candidate declaration",
        )
        _require(entry["raw_column"] == FORECAST_COLUMNS[candidate], "Wrong candidate raw column.")
        _reference(entry["original_evidence_reference"])
        reasons = entry["original_reason_fields"]
        _require(
            isinstance(reasons, list) and reasons == [x for x in _REASON_FIELDS if x in reasons],
            "Invalid original reason-field declaration.",
        )
        reason_fields[candidate] = tuple(reasons)
        _references(entry["legacy_provenance_limitations"])
        original = _json(snapshot[_ORIGINAL_FILES[candidate]])
        _require(
            original.get("candidate_id") in (None, candidate)
            and original.get("command") in (None, _ORIGINAL_COMMANDS[candidate])
            and original.get("development_only_through") == DEVELOPMENT_CUTOFF
            and original.get("final_holdout_forecast_or_evaluation") is False,
            "Original manifest candidate/development identity mismatch.",
        )
        if candidate == CANDIDATE_IDS[2]:
            _require(
                original.get("configuration_sha256") == _sha(snapshot[_CONFIGURATION]),
                "Original LightGBM configuration hash mismatch.",
            )
    _json(snapshot[_CONFIGURATION])  # archived bytes only; no model/config execution
    inspected: dict[str, pq.ParquetFile] = {}
    decoded_total = 0
    for name in sorted(tables):
        candidate = next((c for c, path in _CANDIDATE_FILES.items() if path == name), None)
        allowed = _column_types(
            name, reason_fields[candidate] if candidate else (), manifest["metadata_fields"]
        )
        parquet, decoded_size = _inspect_parquet(snapshot[name], schemas[name], allowed)
        decoded_total += decoded_size
        _require(decoded_total <= MAX_TOTAL_DECODED_BYTES, "Total decoded byte limit exceeded.")
        inspected[name] = parquet
    frames: dict[str, pd.DataFrame] = {}
    decoded_total = 0
    for name, parquet in inspected.items():
        frame, decoded_size = _decode_parquet(parquet)
        decoded_total += decoded_size
        _require(decoded_total <= MAX_TOTAL_DECODED_BYTES, "Total decoded byte limit exceeded.")
        _keys(frame, roster=name == _ROSTER)
        frames[name] = frame
    roster = _keys(frames[_ROSTER], roster=True)
    records = {candidate: frames[path] for candidate, path in _CANDIDATE_FILES.items()}
    try:
        normalized = validate_candidate_records(records)
        population = build_scenario_population(records)
    except EvidenceReviewRequired:
        raise ScenarioInputError(
            "Candidate population failed accepted Phase 7/L1 validation."
        ) from None
    keys = _keys(population)
    _require(
        keys.equals(roster), "Independent observed-key roster differs from candidate population."
    )
    key_hash = _key_digest(keys)
    _require(key_hash == manifest["observed_key_sha256"], "Observed-key digest mismatch.")
    counts = {
        "row_count": len(keys),
        "store_count": int(keys["Store"].nunique()),
        "date_count": int(keys["Date"].nunique()),
        "origin_count": int(keys["forecast_origin"].nunique()),
        "date_min": keys["Date"].min().date().isoformat(),
        "date_max": keys["Date"].max().date().isoformat(),
    }
    _require(counts == manifest["population"], "Declared population counts/date bounds mismatch.")
    if manifest["metadata_fields"]:
        _membership(frames[_MEMBERSHIP], keys, manifest["metadata_fields"])
    candidate_identities = []
    for candidate in CANDIDATE_IDS:
        reasons = normalized[candidate]["forecast_unavailable_reason"].dropna()
        _require(
            all(isinstance(reason, str) and bool(reason) for reason in reasons),
            "Original unavailable reasons must be nonempty strings.",
        )
        entry = candidates[candidate]
        candidate_identities.append(
            CandidateInputIdentity(
                candidate,
                FORECAST_COLUMNS[candidate],
                _sha(snapshot[_ORIGINAL_FILES[candidate]]),
                entry["original_evidence_reference"],
                reason_fields[candidate],
                tuple(
                    sorted((reason, int(count)) for reason, count in reasons.value_counts().items())
                ),
                tuple(entry["legacy_provenance_limitations"]),
                _sha(snapshot[_CONFIGURATION]) if candidate == CANDIDATE_IDS[2] else None,
            )
        )
    verification_ref = "wp1-v1:" + _sha(_canonical([manifest_hash, receipt_hash]))
    return ScenarioInputVerification(
        bundle_id=manifest["bundle_id"],
        purpose=PURPOSE,
        schema_version=SCHEMA_VERSION,
        development_cutoff=DEVELOPMENT_CUTOFF,
        manifest_sha256=manifest_hash,
        payload_sha256=manifest["payload_sha256"],
        preparation_receipt_sha256=receipt_hash,
        verification_reference=verification_ref,
        payloads=identities,
        observed_key_sha256=key_hash,
        **counts,
        candidate_ids=CANDIDATE_IDS,
        candidates=tuple(candidate_identities),
        enabled_scenario_dimensions=tuple(manifest["metadata_fields"]),
        source_lineage_references=tuple(manifest["source_lineage_references"]),
        observed_key_lineage_reference=manifest["observed_key_lineage_reference"],
        availability_claims=claims,
        preparation_execution_id=manifest["preparation"]["execution_id"],
        preparation_reference=manifest["preparation"]["reference"],
        findings=(
            "Exact byte inventory, receipt consistency and bounded schemas checked.",
            "Phase 7/L1 candidate labels, raw paths, masks and sparse keys checked.",
            "Independent declared roster and complete metadata key population checked.",
            "H disabled; no aggregation or external operation performed.",
        ),
        limitations=_LIMITATIONS,
    )


def validate_scenario_input_binding(
    binding: ScenarioInputBinding | None,
    verification: ScenarioInputVerification,
) -> None:
    """Check synthetic identity consistency only; no authentication or later-gate approval.

    Never use this binding for actual WP1 inputs, production loading, real evaluation,
    Phase 13, source custody/approval issuance or public release/publication.
    """
    _require(isinstance(binding, ScenarioInputBinding), "Missing/invalid external binding.")
    _require(isinstance(verification, ScenarioInputVerification), "Invalid verification record.")
    _require(
        binding.purpose == verification.purpose == PURPOSE,
        "Only synthetic fixture bindings are supported.",
    )
    _reference(binding.reference)
    _require(type(binding.schema_version) is int, "Invalid binding schema version.")
    for field in (
        "bundle_id",
        "purpose",
        "schema_version",
        "development_cutoff",
        "manifest_sha256",
        "payload_sha256",
        "preparation_receipt_sha256",
        "candidate_ids",
        "enabled_scenario_dimensions",
        "preparation_execution_id",
        "preparation_reference",
        "verification_reference",
    ):
        _require(
            getattr(binding, field) == getattr(verification, field), f"Binding {field} mismatch."
        )
    uses = binding.permitted_uses
    _require(
        isinstance(uses, tuple)
        and bool(uses)
        and all(isinstance(use, str) and use in PERMITTED_USES for use in uses)
        and len(set(uses)) == len(uses),
        "Unsupported binding permitted uses.",
    )
