"""Deterministic, in-memory WP1 Milestone 1 fixture evidence and verification.

This module accepts only synthetic fixture bytes and candidate frames. It has no filesystem,
network, fitting, forecast-generation, L2 aggregation, publication, or authorization interface.
Canonical hashes and the separate receipt establish fixture consistency only. They do not prove
synthetic origin, custody, historical forecast provenance, real-source permission, or safe peak
memory use. WP1-S7-01 remains unresolved under its original contract.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.data.wp1_preparation import (
    OBSERVATION_COLUMNS,
    PROMO_MEMBERSHIP_COLUMNS,
    WP1PreparationError,
    _candidate_open_value,
    _candidate_sales_value,
    _candidate_store_key,
    build_promo_membership,
    prepare_candidate_records,
    prepare_target_observations,
)
from rossmann_forecasting.forecasting.model_selection import (
    BASE_COLUMNS,
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    EvidenceReviewRequired,
)
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
)

SCHEMA_VERSION = 1
PURPOSE = "wp1_synthetic_fixture_milestone_1"
DEVELOPMENT_CUTOFF = LAST_DEVELOPMENT_DATE.date().isoformat()
OBSERVATIONS_NAME = "source/target_observations.json"
PROMO_NAME = "source/promo_membership.json"
CANDIDATE_NAMES = {candidate: f"candidates/{candidate}.json" for candidate in CANDIDATE_IDS}
_REASON_FIELDS = ("unavailable_reason", "fit_failure_reason")
_REFERENCE_SOURCE_COLUMNS = (
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
_OBSERVATION_SCHEMA = tuple(OBSERVATION_COLUMNS)
_PROMO_SCHEMA = tuple(PROMO_MEMBERSHIP_COLUMNS)
_SECURITY_LIMITATIONS = (
    "Caller must provide reviewed project-controlled synthetic fixture inputs; "
    "origin is unauthenticated.",
    "Hashes, manifests and receipts establish identity consistency only and grant no permission.",
    "Candidate raw forecasts and historical execution provenance are not authenticated "
    "by this fixture contract.",
    "Promo is retrospective membership and is not established as known at the forecast origin.",
    "No real-source access, custody, binding, loading, L4, Phase 13 or publication "
    "authority is granted.",
    "No hard peak-memory limit is enforced; WP1-S7-01 remains unresolved under the "
    "original contract.",
    "Protected 2015-07-04 through 2015-07-31 outcomes are outside this fixture contract.",
)
_PROVENANCE = {
    "source_input": "caller-supplied synthetic Rossmann-style CSV bytes",
    "candidate_input": "caller-supplied synthetic records for the three accepted "
    "Phase 7 candidates",
    "verification": "separate synthetic CSV scan and source-derived target-roster comparison",
    "retained_source_fields": list(OBSERVATION_COLUMNS),
    "retained_candidate_fields": "accepted candidate raw field, keys, labels, masks "
    "and original reason fields",
}
_AUTHORIZATION_LIMITATIONS = {
    "operational_permission": False,
    "authority_source": "none; fixture identity records are not authorization",
    "real_source_access": False,
    "l4_execution": False,
    "publication": False,
}
_AUTHORIZATION_BOOLEAN_FIELDS = (
    "operational_permission",
    "real_source_access",
    "l4_execution",
    "publication",
)
_MANIFEST_FIELDS = {
    "schema_version",
    "purpose",
    "development_cutoff",
    "approved_windows",
    "candidate_identities",
    "source_reference_identity",
    "source_derived_roster_identity",
    "enabled_dimensions",
    "h_segmentation_enabled",
    "schemas",
    "populations",
    "prepared_payloads",
    "preparation_provenance",
    "authorization_limitations",
    "security_limitations",
}
_RECEIPT_FIELDS = {
    "schema_version",
    "purpose",
    "receipt_type",
    "preparation_manifest_sha256",
    "payload_inventory_sha256",
    "authorization_granted",
    "limitations",
}


class WP1FixtureEvidenceError(ValueError):
    """Synthetic WP1 fixture evidence failed canonical or scientific validation."""


@dataclass(frozen=True, slots=True)
class WP1FixtureSnapshot:
    """Immutable byte snapshot; payload names are logical and are never opened as paths."""

    payloads: tuple[tuple[str, bytes], ...]
    preparation_manifest: bytes
    preparation_receipt: bytes


@dataclass(frozen=True, slots=True)
class WP1FixtureVerification:
    """Identity and count findings only; carries no mutable frames or execution authority."""

    preparation_manifest_sha256: str
    preparation_receipt_sha256: str
    payload_inventory_sha256: str
    source_reference_identity_sha256: str
    source_derived_roster_sha256: str
    observed_target_rows: int
    store_count: int
    date_count: int
    candidate_row_counts: tuple[tuple[str, int], ...]
    enabled_dimensions: tuple[str, ...]
    limitations: tuple[str, ...] = _SECURITY_LIMITATIONS


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise WP1FixtureEvidenceError(
            "fixture evidence contains a non-canonical JSON value"
        ) from None


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WP1FixtureEvidenceError("fixture JSON contains a duplicate object key")
        result[key] = value
    return result


def _load_canonical_json(content: bytes, *, label: str) -> Any:
    if not isinstance(content, bytes):
        raise WP1FixtureEvidenceError(f"{label} must be immutable bytes")
    try:
        value = json.loads(
            content.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda _token: (_ for _ in ()).throw(
                WP1FixtureEvidenceError("fixture JSON contains a non-finite number")
            ),
        )
    except WP1FixtureEvidenceError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise WP1FixtureEvidenceError(f"{label} is not valid canonical UTF-8 JSON") from None
    if _canonical_json(value) != content:
        raise WP1FixtureEvidenceError(f"{label} is not encoded as canonical JSON")
    return value


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _iso_date(value: Any) -> str:
    if isinstance(value, (pd.Timestamp, datetime)):
        if (
            value.tzinfo is not None
            or value.hour
            or value.minute
            or value.second
            or value.microsecond
            or getattr(value, "nanosecond", 0)
        ):
            raise WP1FixtureEvidenceError("fixture date must be a timezone-free midnight")
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise WP1FixtureEvidenceError("fixture date must use canonical YYYY-MM-DD") from None
        if parsed.isoformat() != value:
            raise WP1FixtureEvidenceError("fixture date must use canonical YYYY-MM-DD")
        return value
    raise WP1FixtureEvidenceError("fixture date has an unsupported value")


def _nullable_integer(value: Any, *, field: str, minimum: int, maximum: int) -> int | None:
    if (
        value is None
        or value is pd.NA
        or (isinstance(value, (float, np.floating)) and math.isnan(float(value)))
    ):
        return None
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise WP1FixtureEvidenceError(f"{field} must be an integer or missing")
    integer = int(value)
    if not minimum <= integer <= maximum:
        raise WP1FixtureEvidenceError(f"{field} is outside its supported range")
    return integer


def _number(value: Any, *, field: str, nullable: bool) -> float | None:
    if (
        value is None
        or value is pd.NA
        or (isinstance(value, (float, np.floating)) and math.isnan(value))
    ):
        if nullable:
            return None
        raise WP1FixtureEvidenceError(f"{field} is required")
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise WP1FixtureEvidenceError(f"{field} must be numeric or missing")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError):
        raise WP1FixtureEvidenceError(f"{field} must be finite and non-negative") from None
    if not math.isfinite(result) or result < 0:
        raise WP1FixtureEvidenceError(f"{field} must be finite and non-negative")
    return result


def _sales_label(value: Any) -> int | float | None:
    """Retain the original numeric JSON type so integer labels are compared without float loss."""

    if (
        value is None
        or value is pd.NA
        or (isinstance(value, (float, np.floating)) and math.isnan(float(value)))
    ):
        return None
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise WP1FixtureEvidenceError("candidate actual_sales must be numeric or missing")
    if isinstance(value, (int, np.integer)):
        result: int | float = int(value)
        if not 0 <= result <= 2**63 - 1:
            raise WP1FixtureEvidenceError("candidate actual_sales is outside non-negative int64")
        return result
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise WP1FixtureEvidenceError("candidate actual_sales must be finite and non-negative")
    return result


def _boolean(value: Any, *, field: str) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if type(value) is int and value in (0, 1):
        return bool(value)
    raise WP1FixtureEvidenceError(f"{field} must be an explicit boolean")


def _approved_windows() -> list[dict[str, str]]:
    return [
        {
            "name": window.name,
            "forecast_origin": window.forecast_origin.date().isoformat(),
            "target_start": window.target_start.date().isoformat(),
            "target_end": window.target_end.date().isoformat(),
        }
        for window in APPROVED_DEVELOPMENT_WINDOWS
    ]


def _observation_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame) or frame.columns.duplicated().any():
        raise WP1FixtureEvidenceError("source observation schema is invalid")
    if tuple(frame.columns) != _OBSERVATION_SCHEMA or frame.empty:
        raise WP1FixtureEvidenceError("source observations do not match the exact nonempty schema")
    rows: list[dict[str, Any]] = []
    for store, timestamp, sales, source_open, promo in frame.itertuples(index=False, name=None):
        store_value = _nullable_integer(store, field="Store", minimum=1, maximum=2**63 - 1)
        if store_value is None:
            raise WP1FixtureEvidenceError("Store keys cannot be missing")
        sales_value = _nullable_integer(sales, field="Sales", minimum=0, maximum=2**63 - 1)
        open_value = _nullable_integer(source_open, field="Open", minimum=0, maximum=1)
        promo_value = _nullable_integer(promo, field="Promo", minimum=0, maximum=1)
        date_text = _iso_date(timestamp)
        rows.append(
            {
                "Store": store_value,
                "Date": date_text,
                "Sales": sales_value,
                "Open": open_value,
                "Promo": promo_value,
            }
        )
    rows.sort(key=lambda item: (item["Store"], item["Date"]))
    keys = [(row["Store"], row["Date"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise WP1FixtureEvidenceError("source observations contain duplicate keys")
    return rows


def _candidate_columns(candidate_id: str, reason_fields: tuple[str, ...]) -> tuple[str, ...]:
    return (
        *BASE_COLUMNS,
        FORECAST_COLUMNS[candidate_id],
        "forecast_available",
        "primary_evaluation_eligible",
        *reason_fields,
    )


def _candidate_payload_rows(
    candidate_id: str, frame: pd.DataFrame, original_frame: pd.DataFrame
) -> tuple[tuple[str, ...], list[dict[str, Any]]]:
    if frame.columns.duplicated().any():
        raise WP1FixtureEvidenceError("candidate payload contains duplicate fields")
    reason_fields = tuple(field for field in _REASON_FIELDS if field in frame.columns)
    columns = _candidate_columns(candidate_id, reason_fields)
    if set(frame.columns).intersection({"operational_forecast", "routed_forecast"}):
        raise WP1FixtureEvidenceError("candidate payload contains a non-raw forecast field")
    internal = {"raw_model_forecast", "forecast_unavailable_reason", "candidate_id"}
    if set(frame.columns) != set(columns).union(internal) or len(frame.columns) != len(
        columns
    ) + len(internal):
        raise WP1FixtureEvidenceError("candidate payload does not match its exact raw schema")

    original_by_key: dict[tuple[int, str, str], dict[str, Any]] = {}
    for original in original_frame.to_dict(orient="records"):
        key = (
            _candidate_store_key(original["Store"], candidate_id=candidate_id),
            _iso_date(original["forecast_origin"]),
            _iso_date(original["Date"]),
        )
        if key in original_by_key:
            raise WP1FixtureEvidenceError("original candidate records contain duplicate keys")
        original_by_key[key] = original

    rows: list[dict[str, Any]] = []
    raw_column = FORECAST_COLUMNS[candidate_id]
    for record in frame.to_dict(orient="records"):
        key = (
            _candidate_store_key(record["Store"], candidate_id=candidate_id),
            _iso_date(record["forecast_origin"]),
            _iso_date(record["Date"]),
        )
        original = original_by_key.get(key)
        if original is None:
            raise WP1FixtureEvidenceError(
                "normalized candidate key is absent from original records"
            )
        original_store = _candidate_store_key(original["Store"], candidate_id=candidate_id)
        normalized_store = _candidate_store_key(record["Store"], candidate_id=candidate_id)
        if original_store != normalized_store:
            raise WP1FixtureEvidenceError(
                "normalized candidate Store differs from its original key"
            )
        original_sales = _candidate_sales_value(
            original.get("actual_sales"), candidate_id=candidate_id
        )
        prepared_sales = _candidate_sales_value(
            record.get("actual_sales"), candidate_id=candidate_id
        )
        if original_sales != prepared_sales:
            raise WP1FixtureEvidenceError(
                "prepared candidate Sales differs from its original label"
            )
        original_open = _candidate_open_value(
            original.get("source_open"), candidate_id=candidate_id
        )
        prepared_open = _candidate_open_value(record.get("source_open"), candidate_id=candidate_id)
        if original_open != prepared_open:
            raise WP1FixtureEvidenceError("prepared candidate Open differs from its original label")
        normalized_raw = _number(record.get("raw_model_forecast"), field=raw_column, nullable=True)
        mapped_raw = _number(record.get(raw_column), field=raw_column, nullable=True)
        if normalized_raw != mapped_raw:
            raise WP1FixtureEvidenceError(
                "mapped raw forecast disagrees with Phase 7 normalization"
            )
        values: dict[str, Any] = {
            "Store": original_store,
            "forecast_origin": _iso_date(record.get("forecast_origin")),
            "Date": _iso_date(record.get("Date")),
            "horizon": _nullable_integer(
                record.get("horizon"), field="horizon", minimum=1, maximum=14
            ),
            "validation_window": record.get("validation_window"),
            "actual_sales": original_sales,
            "source_open": original_open,
            raw_column: normalized_raw,
            "forecast_available": _boolean(
                record.get("forecast_available"), field="forecast_available"
            ),
            "primary_evaluation_eligible": _boolean(
                record.get("primary_evaluation_eligible"), field="primary_evaluation_eligible"
            ),
        }
        if values["Store"] is None or values["horizon"] is None:
            raise WP1FixtureEvidenceError("candidate keys and horizons cannot be missing")
        if not isinstance(values["validation_window"], str):
            raise WP1FixtureEvidenceError("candidate validation window must be text")
        for field in reason_fields:
            reason = original.get(field)
            if (
                reason is None
                or reason is pd.NA
                or (isinstance(reason, (float, np.floating)) and math.isnan(float(reason)))
            ):
                values[field] = None
            elif isinstance(reason, str) and reason.strip():
                values[field] = reason
            else:
                raise WP1FixtureEvidenceError(
                    "original reason fields must be nonempty text or missing"
                )
        rows.append(values)
    rows.sort(key=lambda item: (item["Store"], item["forecast_origin"], item["Date"]))
    return columns, rows


def _membership_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame) or frame.columns.duplicated().any():
        raise WP1FixtureEvidenceError("Promo membership schema is invalid")
    if tuple(frame.columns) != _PROMO_SCHEMA or frame.empty:
        raise WP1FixtureEvidenceError("Promo membership does not match the exact nonempty schema")
    rows: list[dict[str, Any]] = []
    for store, origin, target, promo in frame.itertuples(index=False, name=None):
        rows.append(
            {
                "Store": _nullable_integer(store, field="Store", minimum=1, maximum=2**63 - 1),
                "forecast_origin": _iso_date(origin),
                "Date": _iso_date(target),
                "Promo": _nullable_integer(promo, field="Promo", minimum=0, maximum=1),
            }
        )
    rows.sort(key=lambda item: (item["Store"], item["forecast_origin"], item["Date"]))
    keys = [(row["Store"], row["forecast_origin"], row["Date"]) for row in rows]
    if any(row["Store"] is None for row in rows) or len(set(keys)) != len(keys):
        raise WP1FixtureEvidenceError("Promo membership has missing or duplicate keys")
    return rows


def _table_bytes(columns: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    return _canonical_json({"columns": list(columns), "rows": rows})


def _roster_bytes(observations: list[dict[str, Any]]) -> bytes:
    mapped = []
    for row in observations:
        target = date.fromisoformat(row["Date"])
        window = next(
            candidate
            for candidate in APPROVED_DEVELOPMENT_WINDOWS
            if candidate.target_start.date() <= target <= candidate.target_end.date()
        )
        mapped.append(
            {
                "Store": row["Store"],
                "forecast_origin": window.forecast_origin.date().isoformat(),
                "Date": row["Date"],
            }
        )
    mapped.sort(key=lambda item: (item["Store"], item["forecast_origin"], item["Date"]))
    return _canonical_json(mapped)


def _population_counts(
    observations: list[dict[str, Any]],
    candidate_rows: dict[str, list[dict[str, Any]]],
    promo_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "source_observations": {
            "rows": len(observations),
            "stores": len({row["Store"] for row in observations}),
            "dates": len({row["Date"] for row in observations}),
            "missing_sales": sum(row["Sales"] is None for row in observations),
            "missing_open": sum(row["Open"] is None for row in observations),
            "missing_promo": sum(row["Promo"] is None for row in observations),
        },
        "candidate_rows": {
            candidate: len(candidate_rows[candidate]) for candidate in CANDIDATE_IDS
        },
        "promo_membership_rows": len(promo_rows),
    }


def create_wp1_fixture_snapshot(
    source_csv_bytes: bytes,
    candidate_records: dict[str, pd.DataFrame],
) -> WP1FixtureSnapshot:
    """Prepare a canonical fixture snapshot from synthetic CSV bytes and candidate records."""

    try:
        observations_frame = prepare_target_observations(source_csv_bytes)
        candidates = prepare_candidate_records(candidate_records)
        membership_frame = build_promo_membership(observations_frame)
        observations = _observation_rows(observations_frame)
        membership = _membership_rows(membership_frame)
        candidate_columns: dict[str, tuple[str, ...]] = {}
        candidate_rows: dict[str, list[dict[str, Any]]] = {}
        for candidate in CANDIDATE_IDS:
            candidate_columns[candidate], candidate_rows[candidate] = _candidate_payload_rows(
                candidate, candidates[candidate], candidate_records[candidate]
            )
    except WP1PreparationError as exc:
        raise WP1FixtureEvidenceError("synthetic WP1 fixture preparation failed") from exc
    except EvidenceReviewRequired as exc:
        raise WP1FixtureEvidenceError(
            "synthetic candidate evidence failed accepted Phase 7 validation"
        ) from exc

    payloads: dict[str, bytes] = {
        OBSERVATIONS_NAME: _table_bytes(_OBSERVATION_SCHEMA, observations),
        PROMO_NAME: _table_bytes(_PROMO_SCHEMA, membership),
    }
    for candidate in CANDIDATE_IDS:
        payloads[CANDIDATE_NAMES[candidate]] = _table_bytes(
            candidate_columns[candidate], candidate_rows[candidate]
        )
    payload_inventory = {
        name: {"byte_count": len(content), "sha256": _sha256(content)}
        for name, content in sorted(payloads.items())
    }
    candidate_identities = [
        {
            "candidate_id": candidate,
            "raw_column": FORECAST_COLUMNS[candidate],
            "original_reason_fields": [
                field for field in _REASON_FIELDS if field in candidate_columns[candidate]
            ],
        }
        for candidate in CANDIDATE_IDS
    ]
    observation_bytes = payloads[OBSERVATIONS_NAME]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "purpose": PURPOSE,
        "development_cutoff": DEVELOPMENT_CUTOFF,
        "approved_windows": _approved_windows(),
        "candidate_identities": candidate_identities,
        "source_reference_identity": {
            "identity_kind": "canonical_target_observations_sha256",
            "sha256": _sha256(observation_bytes),
        },
        "source_derived_roster_identity": {
            "identity_kind": "sorted_store_origin_date_sha256",
            "sha256": _sha256(_roster_bytes(observations)),
        },
        "enabled_dimensions": ["Promo"],
        "h_segmentation_enabled": False,
        "schemas": {
            "source_observations": list(_OBSERVATION_SCHEMA),
            "candidates": {
                candidate: list(candidate_columns[candidate]) for candidate in CANDIDATE_IDS
            },
            "promo_membership": list(_PROMO_SCHEMA),
        },
        "populations": _population_counts(observations, candidate_rows, membership),
        "prepared_payloads": payload_inventory,
        "preparation_provenance": _PROVENANCE,
        "authorization_limitations": _AUTHORIZATION_LIMITATIONS,
        "security_limitations": list(_SECURITY_LIMITATIONS),
    }
    manifest_bytes = _canonical_json(manifest)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "purpose": PURPOSE,
        "receipt_type": "synthetic_fixture_preparation_consistency",
        "preparation_manifest_sha256": _sha256(manifest_bytes),
        "payload_inventory_sha256": _sha256(_canonical_json(payload_inventory)),
        "authorization_granted": False,
        "limitations": list(_SECURITY_LIMITATIONS),
    }
    receipt_bytes = _canonical_json(receipt)
    return WP1FixtureSnapshot(
        payloads=tuple((name, payloads[name]) for name in sorted(payloads)),
        preparation_manifest=manifest_bytes,
        preparation_receipt=receipt_bytes,
    )


def _reference_int(token: str, *, field: str, nullable: bool, binary: bool = False) -> int | None:
    if token == "" and nullable:
        return None
    digits = token[1:] if token[:1] in {"+", "-"} else token
    if (
        not token
        or token.strip() != token
        or not digits
        or any(character < "0" or character > "9" for character in digits)
    ):
        raise WP1FixtureEvidenceError(f"independent source reference has invalid {field}")
    try:
        value = int(token)
    except ValueError:
        raise WP1FixtureEvidenceError(f"independent source reference has invalid {field}") from None
    if not -(2**63) <= value <= 2**63 - 1:
        raise WP1FixtureEvidenceError(f"independent source reference has invalid {field}")
    if binary and value not in (0, 1):
        raise WP1FixtureEvidenceError(f"independent source reference has invalid {field}")
    if field == "Store" and value <= 0:
        raise WP1FixtureEvidenceError("independent source reference has invalid Store")
    if field == "Sales" and value < 0:
        raise WP1FixtureEvidenceError("independent source reference has invalid Sales")
    return value


def _independent_reference_observations(source_csv_bytes: bytes) -> list[dict[str, Any]]:
    """Independently scan synthetic CSV bytes; intentionally does not call the preparer."""

    if not isinstance(source_csv_bytes, bytes):
        raise WP1FixtureEvidenceError("independent source reference must be immutable bytes")
    try:
        text = source_csv_bytes.decode("utf-8", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        names = reader.fieldnames
        if names != list(_REFERENCE_SOURCE_COLUMNS) or len(set(names or ())) != len(
            _REFERENCE_SOURCE_COLUMNS
        ):
            raise WP1FixtureEvidenceError("independent source reference schema is unsupported")
        rows: list[dict[str, Any]] = []
        for source_row in reader:
            token = source_row.get("Date")
            if not isinstance(token, str):
                raise WP1FixtureEvidenceError("independent source reference Date is invalid")
            try:
                target_date = date.fromisoformat(token)
            except ValueError:
                raise WP1FixtureEvidenceError(
                    "independent source reference Date is invalid"
                ) from None
            if target_date.isoformat() != token:
                raise WP1FixtureEvidenceError("independent source reference Date is noncanonical")
            if target_date > LAST_DEVELOPMENT_DATE.date():
                continue
            if not any(
                window.target_start.date() <= target_date <= window.target_end.date()
                for window in APPROVED_DEVELOPMENT_WINDOWS
            ):
                continue
            # A malformed protected row has already been classified and skipped above. Only
            # approved target rows have their remaining fields and width interpreted here.
            if None in source_row or any(
                source_row.get(name) is None for name in _REFERENCE_SOURCE_COLUMNS
            ):
                raise WP1FixtureEvidenceError(
                    "independent source reference target row is malformed"
                )
            store = _reference_int(source_row["Store"], field="Store", nullable=False)
            sales = _reference_int(source_row["Sales"], field="Sales", nullable=True)
            source_open = _reference_int(
                source_row["Open"], field="Open", nullable=True, binary=True
            )
            promo = _reference_int(source_row["Promo"], field="Promo", nullable=True, binary=True)
            rows.append(
                {
                    "Store": store,
                    "Date": target_date.isoformat(),
                    "Sales": sales,
                    "Open": source_open,
                    "Promo": promo,
                }
            )
    except WP1FixtureEvidenceError:
        raise
    except (UnicodeDecodeError, csv.Error, StopIteration):
        raise WP1FixtureEvidenceError(
            "independent source reference is not valid UTF-8 CSV"
        ) from None
    if not rows:
        raise WP1FixtureEvidenceError(
            "independent source reference contains no target observations"
        )
    rows.sort(key=lambda item: (item["Store"], item["Date"]))
    keys = [(row["Store"], row["Date"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise WP1FixtureEvidenceError("independent source reference has duplicate target keys")
    return rows


def _exact_object(value: Any, fields: set[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields or len(value) != len(fields):
        raise WP1FixtureEvidenceError(f"{label} contains missing or unsupported fields")
    return value


def _decode_rows(
    content: bytes, expected_columns: tuple[str, ...], *, label: str
) -> list[dict[str, Any]]:
    value = _load_canonical_json(content, label=label)
    table = _exact_object(value, {"columns", "rows"}, label=label)
    if table["columns"] != list(expected_columns) or not isinstance(table["rows"], list):
        raise WP1FixtureEvidenceError(f"{label} schema is invalid")
    rows: list[dict[str, Any]] = []
    for item in table["rows"]:
        row = _exact_object(item, set(expected_columns), label=label)
        rows.append(row)
    return rows


def _validate_observation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise WP1FixtureEvidenceError("source observation payload is empty")
    checked: list[dict[str, Any]] = []
    for row in rows:
        store = _nullable_integer(row["Store"], field="Store", minimum=1, maximum=2**63 - 1)
        sales = _nullable_integer(row["Sales"], field="Sales", minimum=0, maximum=2**63 - 1)
        source_open = _nullable_integer(row["Open"], field="Open", minimum=0, maximum=1)
        promo = _nullable_integer(row["Promo"], field="Promo", minimum=0, maximum=1)
        target = _iso_date(row["Date"])
        if store is None:
            raise WP1FixtureEvidenceError("source observation Store cannot be missing")
        if not any(
            window.target_start.date().isoformat() <= target <= window.target_end.date().isoformat()
            for window in APPROVED_DEVELOPMENT_WINDOWS
        ):
            raise WP1FixtureEvidenceError("source observation Date is outside approved windows")
        checked.append(
            {"Store": store, "Date": target, "Sales": sales, "Open": source_open, "Promo": promo}
        )
    checked.sort(key=lambda item: (item["Store"], item["Date"]))
    keys = [(row["Store"], row["Date"]) for row in checked]
    if len(set(keys)) != len(keys):
        raise WP1FixtureEvidenceError("source observation payload has duplicate keys")
    if rows != checked:
        raise WP1FixtureEvidenceError("source observation payload rows are not canonically sorted")
    return checked


def _validate_candidate_rows(
    candidate_id: str, columns: tuple[str, ...], rows: list[dict[str, Any]]
) -> pd.DataFrame:
    raw = FORECAST_COLUMNS[candidate_id]
    reasons = tuple(field for field in _REASON_FIELDS if field in columns)
    if columns != _candidate_columns(candidate_id, reasons):
        raise WP1FixtureEvidenceError("candidate schema does not match its accepted raw identity")
    records: list[dict[str, Any]] = []
    input_keys: list[tuple[int, str, str]] = []
    for row in rows:
        store = _nullable_integer(row["Store"], field="Store", minimum=1, maximum=2**63 - 1)
        horizon = _nullable_integer(row["horizon"], field="horizon", minimum=1, maximum=14)
        origin = _iso_date(row["forecast_origin"])
        target = _iso_date(row["Date"])
        actual = _sales_label(row["actual_sales"])
        source_open = _number(row["source_open"], field="source_open", nullable=True)
        forecast = _number(row[raw], field=raw, nullable=True)
        if store is None or horizon is None:
            raise WP1FixtureEvidenceError("candidate key and horizon fields cannot be missing")
        if not isinstance(row["validation_window"], str):
            raise WP1FixtureEvidenceError("candidate validation window must be text")
        if source_open not in (None, 0.0, 1.0):
            raise WP1FixtureEvidenceError("candidate source Open must be 0, 1, or missing")
        available = _boolean(row["forecast_available"], field="forecast_available")
        eligible = _boolean(row["primary_evaluation_eligible"], field="primary_evaluation_eligible")
        if available != (forecast is not None):
            raise WP1FixtureEvidenceError("candidate availability disagrees with raw forecast")
        if eligible != (source_open == 1 and actual is not None and forecast is not None):
            raise WP1FixtureEvidenceError(
                "candidate eligibility disagrees with source labels and availability"
            )
        record: dict[str, Any] = {
            "Store": store,
            "forecast_origin": pd.Timestamp(origin),
            "Date": pd.Timestamp(target),
            "horizon": horizon,
            "validation_window": row["validation_window"],
            "actual_sales": actual,
            "source_open": source_open,
            raw: forecast,
            "forecast_available": available,
            "primary_evaluation_eligible": eligible,
        }
        for field in reasons:
            reason = row[field]
            if reason is not None and (not isinstance(reason, str) or not reason.strip()):
                raise WP1FixtureEvidenceError(
                    "original reason fields must be nonempty text or missing"
                )
            record[field] = reason
        records.append(record)
        input_keys.append((store, origin, target))
    if input_keys != sorted(input_keys) or len(set(input_keys)) != len(input_keys):
        raise WP1FixtureEvidenceError("candidate payload rows are unsorted or duplicated")
    frame = pd.DataFrame(records, columns=columns)
    # Keep Python integer labels intact through the independent source comparison. The Phase 7
    # validator still receives its unchanged accepted numeric contract after this check.
    frame["actual_sales"] = pd.Series([record["actual_sales"] for record in records], dtype=object)
    return frame


def _compare_reference(
    observation_rows: list[dict[str, Any]],
    candidate_rows_by_candidate: dict[str, list[dict[str, Any]]],
    promo_rows: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]],
) -> None:
    if observation_rows != reference_rows:
        raise WP1FixtureEvidenceError(
            "prepared source observations disagree with independent reference"
        )

    expected_by_key: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in reference_rows:
        target_date = date.fromisoformat(row["Date"])
        window = next(
            window
            for window in APPROVED_DEVELOPMENT_WINDOWS
            if window.target_start.date() <= target_date <= window.target_end.date()
        )
        expected_by_key[(row["Store"], window.forecast_origin.date().isoformat(), row["Date"])] = (
            row
        )

    expected_keys = set(expected_by_key)
    for candidate in CANDIDATE_IDS:
        candidate_keys: set[tuple[int, str, str]] = set()
        candidate_rows = candidate_rows_by_candidate[candidate]
        for record in candidate_rows:
            key = (
                record["Store"],
                record["forecast_origin"],
                record["Date"],
            )
            candidate_keys.add(key)
            expected = expected_by_key.get(key)
            if expected is None:
                raise WP1FixtureEvidenceError(
                    "candidate contains a target absent from independent source"
                )
            actual = record["actual_sales"]
            source_open = record["source_open"]
            expected_sales = expected["Sales"]
            expected_open = expected["Open"]
            if actual != expected_sales:
                raise WP1FixtureEvidenceError(
                    "candidate Sales label differs from independent source"
                )
            if (None if pd.isna(source_open) else source_open) != expected_open:
                raise WP1FixtureEvidenceError(
                    "candidate Open label differs from independent source"
                )
        if candidate_keys != expected_keys or len(candidate_keys) != len(candidate_rows):
            raise WP1FixtureEvidenceError(
                "candidate target population differs from independent source"
            )

    expected_promo = []
    for key, row in sorted(expected_by_key.items()):
        expected_promo.append(
            {
                "Store": key[0],
                "forecast_origin": key[1],
                "Date": key[2],
                "Promo": row["Promo"],
            }
        )
    if promo_rows != expected_promo:
        raise WP1FixtureEvidenceError(
            "Promo membership is incomplete or differs from independent source"
        )


def _validate_manifest(
    manifest: Any, receipt: Any, payloads: dict[str, bytes]
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _exact_object(manifest, _MANIFEST_FIELDS, label="preparation manifest")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise WP1FixtureEvidenceError("preparation manifest schema version is unsupported")
    if manifest["purpose"] != PURPOSE or manifest["development_cutoff"] != DEVELOPMENT_CUTOFF:
        raise WP1FixtureEvidenceError("preparation manifest purpose or cutoff is unsupported")
    if manifest["approved_windows"] != _approved_windows():
        raise WP1FixtureEvidenceError(
            "preparation manifest windows differ from the accepted contract"
        )
    if manifest["enabled_dimensions"] != ["Promo"]:
        raise WP1FixtureEvidenceError("preparation manifest dimensions are unsupported")
    if type(manifest["h_segmentation_enabled"]) is not bool or manifest["h_segmentation_enabled"]:
        raise WP1FixtureEvidenceError("preparation manifest cannot enable H segmentation")
    if manifest["preparation_provenance"] != _PROVENANCE:
        raise WP1FixtureEvidenceError("preparation manifest provenance declaration is invalid")
    authorization = _exact_object(
        manifest["authorization_limitations"],
        set(_AUTHORIZATION_LIMITATIONS),
        label="preparation authorization declaration",
    )
    for field in _AUTHORIZATION_BOOLEAN_FIELDS:
        if type(authorization[field]) is not bool:
            raise WP1FixtureEvidenceError(
                "preparation authorization declaration Boolean fields must be JSON booleans"
            )
    if authorization != _AUTHORIZATION_LIMITATIONS:
        raise WP1FixtureEvidenceError("preparation manifest authorization declaration is invalid")
    if manifest["security_limitations"] != list(_SECURITY_LIMITATIONS):
        raise WP1FixtureEvidenceError("preparation manifest security limitations are incomplete")

    expected_names = {OBSERVATIONS_NAME, PROMO_NAME, *CANDIDATE_NAMES.values()}
    if set(payloads) != expected_names:
        raise WP1FixtureEvidenceError("fixture payload inventory is incomplete or unsupported")
    inventory = manifest["prepared_payloads"]
    if not isinstance(inventory, dict) or set(inventory) != expected_names:
        raise WP1FixtureEvidenceError("manifest payload inventory is incomplete or unsupported")
    for name, content in payloads.items():
        identity = _exact_object(
            inventory[name], {"byte_count", "sha256"}, label="payload identity"
        )
        if type(identity["byte_count"]) is not int or identity["byte_count"] != len(content):
            raise WP1FixtureEvidenceError("prepared payload byte count differs from its manifest")
        digest = identity["sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise WP1FixtureEvidenceError("prepared payload digest has invalid syntax")
        if _sha256(content) != digest:
            raise WP1FixtureEvidenceError("prepared payload identity differs from its manifest")

    receipt = _exact_object(receipt, _RECEIPT_FIELDS, label="preparation receipt")
    expected_receipt = {
        "schema_version": SCHEMA_VERSION,
        "purpose": PURPOSE,
        "receipt_type": "synthetic_fixture_preparation_consistency",
        "preparation_manifest_sha256": _sha256(_canonical_json(manifest)),
        "payload_inventory_sha256": _sha256(_canonical_json(inventory)),
        "authorization_granted": False,
        "limitations": list(_SECURITY_LIMITATIONS),
    }
    if (
        type(receipt["schema_version"]) is not int
        or type(receipt["authorization_granted"]) is not bool
    ):
        raise WP1FixtureEvidenceError("preparation receipt scalar types are invalid")
    if receipt != expected_receipt:
        raise WP1FixtureEvidenceError(
            "preparation receipt identity or limitations are inconsistent"
        )
    return manifest, receipt


def verify_wp1_fixture_snapshot(
    snapshot: WP1FixtureSnapshot,
    independent_source_reference: bytes,
) -> WP1FixtureVerification:
    """Verify a fixture snapshot against a separately supplied synthetic source reference.

    The verifier checks exact payload/manifest/receipt identities, scans the reference with a
    separate parser, derives the source target roster, compares that roster against every candidate,
    and checks complete Promo membership. It never returns frames or performs L2 analysis.
    """

    if not isinstance(snapshot, WP1FixtureSnapshot):
        raise WP1FixtureEvidenceError("fixture snapshot must be an immutable WP1FixtureSnapshot")
    if not isinstance(snapshot.payloads, tuple) or any(
        not isinstance(item, tuple)
        or len(item) != 2
        or not isinstance(item[0], str)
        or not isinstance(item[1], bytes)
        for item in snapshot.payloads
    ):
        raise WP1FixtureEvidenceError("fixture payload snapshot is malformed")
    names = [item[0] for item in snapshot.payloads]
    if len(set(names)) != len(names):
        raise WP1FixtureEvidenceError("fixture payload snapshot contains duplicate logical names")
    payloads = dict(snapshot.payloads)
    manifest = _load_canonical_json(snapshot.preparation_manifest, label="preparation manifest")
    receipt = _load_canonical_json(snapshot.preparation_receipt, label="preparation receipt")
    manifest, receipt = _validate_manifest(manifest, receipt, payloads)

    schemas = _exact_object(
        manifest["schemas"],
        {"source_observations", "candidates", "promo_membership"},
        label="manifest schemas",
    )
    if schemas["source_observations"] != list(_OBSERVATION_SCHEMA) or schemas[
        "promo_membership"
    ] != list(_PROMO_SCHEMA):
        raise WP1FixtureEvidenceError("manifest source schemas are unsupported")
    candidate_schemas = _exact_object(
        schemas["candidates"], set(CANDIDATE_IDS), label="candidate schemas"
    )
    identities = manifest["candidate_identities"]
    if not isinstance(identities, list) or len(identities) != len(CANDIDATE_IDS):
        raise WP1FixtureEvidenceError("manifest candidate identities are incomplete")
    declared_reasons: dict[str, tuple[str, ...]] = {}
    for expected_candidate, identity in zip(CANDIDATE_IDS, identities, strict=True):
        identity = _exact_object(
            identity,
            {"candidate_id", "raw_column", "original_reason_fields"},
            label="candidate identity",
        )
        if (
            identity["candidate_id"] != expected_candidate
            or identity["raw_column"] != FORECAST_COLUMNS[expected_candidate]
        ):
            raise WP1FixtureEvidenceError(
                "manifest candidate identity is not an accepted raw candidate"
            )
        reasons = identity["original_reason_fields"]
        if not isinstance(reasons, list) or reasons != [
            field for field in _REASON_FIELDS if field in reasons
        ]:
            raise WP1FixtureEvidenceError("manifest original reason-field declaration is invalid")
        declared_reasons[expected_candidate] = tuple(reasons)
        expected_schema = list(_candidate_columns(expected_candidate, tuple(reasons)))
        if candidate_schemas[expected_candidate] != expected_schema:
            raise WP1FixtureEvidenceError("manifest candidate schema disagrees with its identity")

    observation_rows = _validate_observation_rows(
        _decode_rows(payloads[OBSERVATIONS_NAME], _OBSERVATION_SCHEMA, label="source observations")
    )
    promo_rows = _decode_rows(payloads[PROMO_NAME], _PROMO_SCHEMA, label="Promo membership")
    candidate_payload_rows: dict[str, list[dict[str, Any]]] = {}
    expected_candidate_frames: dict[str, pd.DataFrame] = {}
    for candidate in CANDIDATE_IDS:
        columns = tuple(candidate_schemas[candidate])
        raw_rows = _decode_rows(
            payloads[CANDIDATE_NAMES[candidate]], columns, label=f"{candidate} candidate payload"
        )
        candidate_payload_rows[candidate] = raw_rows
        expected_candidate_frames[candidate] = _validate_candidate_rows(
            candidate, columns, raw_rows
        )

    try:
        prepare_candidate_records(expected_candidate_frames)
    except WP1PreparationError:
        raise WP1FixtureEvidenceError(
            "candidate payload failed accepted Phase 7 validation"
        ) from None
    except EvidenceReviewRequired:
        raise WP1FixtureEvidenceError(
            "candidate payload failed accepted Phase 7 validation"
        ) from None

    reference_rows = _independent_reference_observations(independent_source_reference)
    _compare_reference(observation_rows, candidate_payload_rows, promo_rows, reference_rows)

    observation_content = payloads[OBSERVATIONS_NAME]
    roster_content = _roster_bytes(reference_rows)
    if manifest["source_reference_identity"] != {
        "identity_kind": "canonical_target_observations_sha256",
        "sha256": _sha256(observation_content),
    }:
        raise WP1FixtureEvidenceError("source reference identity is inconsistent")
    if manifest["source_derived_roster_identity"] != {
        "identity_kind": "sorted_store_origin_date_sha256",
        "sha256": _sha256(roster_content),
    }:
        raise WP1FixtureEvidenceError("source-derived roster identity is inconsistent")

    promo_rows = _membership_payload_validate(promo_rows)
    expected_populations = _population_counts(observation_rows, candidate_payload_rows, promo_rows)
    if _canonical_json(manifest["populations"]) != _canonical_json(expected_populations):
        raise WP1FixtureEvidenceError("manifest population counts disagree with prepared payloads")
    if _canonical_json(observation_rows) != _canonical_json(reference_rows):
        raise WP1FixtureEvidenceError("source reference observations differ after canonicalization")

    inventory_digest = _sha256(_canonical_json(manifest["prepared_payloads"]))
    return WP1FixtureVerification(
        preparation_manifest_sha256=_sha256(snapshot.preparation_manifest),
        preparation_receipt_sha256=_sha256(snapshot.preparation_receipt),
        payload_inventory_sha256=inventory_digest,
        source_reference_identity_sha256=_sha256(_table_bytes(_OBSERVATION_SCHEMA, reference_rows)),
        source_derived_roster_sha256=_sha256(roster_content),
        observed_target_rows=len(observation_rows),
        store_count=len({row["Store"] for row in observation_rows}),
        date_count=len({row["Date"] for row in observation_rows}),
        candidate_row_counts=tuple(
            (candidate, len(candidate_payload_rows[candidate])) for candidate in CANDIDATE_IDS
        ),
        enabled_dimensions=("Promo",),
    )


def _membership_payload_validate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise WP1FixtureEvidenceError("Promo membership payload is empty")
    checked: list[dict[str, Any]] = []
    for row in rows:
        store = _nullable_integer(row["Store"], field="Store", minimum=1, maximum=2**63 - 1)
        if store is None:
            raise WP1FixtureEvidenceError("Promo membership Store cannot be missing")
        origin = _iso_date(row["forecast_origin"])
        target = _iso_date(row["Date"])
        promo = _nullable_integer(row["Promo"], field="Promo", minimum=0, maximum=1)
        window = next(
            (
                window
                for window in APPROVED_DEVELOPMENT_WINDOWS
                if window.target_start.date().isoformat()
                <= target
                <= window.target_end.date().isoformat()
            ),
            None,
        )
        if window is None or window.forecast_origin.date().isoformat() != origin:
            raise WP1FixtureEvidenceError("Promo membership key is outside its approved window")
        checked.append({"Store": store, "forecast_origin": origin, "Date": target, "Promo": promo})
    checked.sort(key=lambda item: (item["Store"], item["forecast_origin"], item["Date"]))
    keys = [(row["Store"], row["forecast_origin"], row["Date"]) for row in checked]
    if len(set(keys)) != len(keys):
        raise WP1FixtureEvidenceError("Promo membership contains duplicate keys")
    return checked
