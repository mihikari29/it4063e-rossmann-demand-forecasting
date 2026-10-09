"""Typed contracts shared by the read-only application layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

import pandas as pd


class Phase(StrEnum):
    """Canonical development-result phases exposed by the application layer."""

    PHASE7 = "phase7"
    PHASE8 = "phase8"
    PHASE9 = "phase9"
    PHASE10 = "phase10"


class ArtifactSelector(StrEnum):
    """Closed allowlist of artifacts; values are stable logical names, not paths."""

    PHASE7_FORECASTS = "phase7_forecasts"
    PHASE7_MODEL_COMPARISON = "phase7_model_comparison"
    PHASE8_DAILY_INTERVALS = "phase8_daily_intervals"
    PHASE8_CUMULATIVE_UNCERTAINTY = "phase8_cumulative_uncertainty"
    PHASE8_DAILY_QUANTILES = "phase8_daily_quantiles"
    PHASE8_CUMULATIVE_QUANTILES = "phase8_cumulative_quantiles"
    PHASE9_SCENARIO_CATALOG = "phase9_scenario_catalog"
    PHASE10_COMPARISON = "phase10_comparison"
    PHASE10_POLICY_SUMMARY = "phase10_policy_summary"
    PHASE10_POLICY_TARGETS = "phase10_policy_targets"
    HISTORICAL_SALES = "historical_sales"


class UnavailableReason(StrEnum):
    """Stable reasons a local resource can be unavailable."""

    MISSING_MANIFEST = "missing_manifest"
    MISSING_ARTIFACT = "missing_artifact"


class ArtifactErrorCode(StrEnum):
    """Sanitized error codes suitable for a future HTTP adapter."""

    UNAVAILABLE = "artifact_unavailable"
    INTEGRITY = "artifact_integrity_error"
    SCHEMA = "artifact_schema_error"
    DUPLICATE_KEY = "artifact_duplicate_key"
    UNSUPPORTED_SELECTOR = "unsupported_artifact_selector"
    INVALID_REQUEST = "invalid_artifact_request"
    UNSAFE_PATH = "unsafe_artifact_path"


class ArtifactValidationLevel(StrEnum):
    """Highest resource-validation level actually reached by an inspection."""

    UNAVAILABLE = "unavailable"
    PRESENT = "present"
    MANIFEST_VALIDATED = "manifest_validated"
    OUTPUT_VERIFIED = "output_verified"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class CanonicalRunIdentity:
    """Trusted, repository-relative identity for one accepted immutable run."""

    phase: Phase
    run_id: str
    manifest_relative_path: Path
    manifest_sha256: str
    run_id_field: str


@dataclass(frozen=True, slots=True)
class UnavailableResource:
    """Explicit unavailable result carried by a sanitized reader exception."""

    selector: ArtifactSelector
    reason: UnavailableReason
    value: None = None


@dataclass(frozen=True, slots=True)
class ArtifactTable:
    """A projected table with the canonical identities that authorize its contents."""

    selector: ArtifactSelector
    run_id: str
    manifest_sha256: str
    output_sha256: str
    frame: pd.DataFrame
    selected_rows: int = 0
    manifest_rows: int = 0


@dataclass(frozen=True, slots=True)
class ArtifactReadiness:
    """Sanitized readiness level for one fixed canonical selector."""

    selector: ArtifactSelector
    phase: Phase
    run_id: str
    manifest_sha256: str
    level: ArtifactValidationLevel
    output_present: bool
    manifest_validated: bool
    output_hash_verified: bool
    error_code: ArtifactErrorCode | None = None


@dataclass(frozen=True, slots=True)
class ForecastQuery:
    """One Store and accepted Phase 7 forecast origin."""

    store_id: int
    forecast_origin: date


@dataclass(frozen=True, slots=True)
class UncertaintyQuery:
    """One Store and one matching accepted Phase 8 fit/origin."""

    store_id: int
    forecast_origin: date
    fit_id: str


@dataclass(frozen=True, slots=True)
class ModelComparisonQuery:
    """Bounded exact-match filters over the fixed Phase 7 comparison dimensions."""

    candidate_id: str | None = None
    population: str | None = None
    scope: str | None = None
    validation_window: str | None = None
    horizon: int | None = None
    store_id: int | None = None
    metric: str | None = None
    limit: int = 200


@dataclass(frozen=True, slots=True)
class InventoryComparisonQuery:
    """One known Phase 10 case, optionally restricted to one Store."""

    case_id: str
    store_id: int | None = None


@dataclass(frozen=True, slots=True)
class HistoryQuery:
    """A single-store, date-bounded historical Sales request."""

    store_id: int
    start_date: date
    end_date: date


class ArtifactReadError(RuntimeError):
    """Base error with a fixed public message and no filesystem details."""

    def __init__(
        self,
        code: ArtifactErrorCode,
        message: str,
        *,
        selector: ArtifactSelector | None = None,
        unavailable: UnavailableResource | None = None,
    ) -> None:
        self.code = code
        self.selector = selector
        self.unavailable = unavailable
        super().__init__(message)


class ArtifactUnavailableError(ArtifactReadError):
    """A required canonical local file is not present."""

    def __init__(self, selector: ArtifactSelector, reason: UnavailableReason) -> None:
        super().__init__(
            ArtifactErrorCode.UNAVAILABLE,
            "The required canonical resource is unavailable.",
            selector=selector,
            unavailable=UnavailableResource(selector=selector, reason=reason),
        )


class ArtifactIntegrityError(ArtifactReadError):
    """A trusted identity, digest, manifest or data-boundary check failed."""

    def __init__(self, selector: ArtifactSelector) -> None:
        super().__init__(
            ArtifactErrorCode.INTEGRITY,
            "The canonical artifact failed an integrity check.",
            selector=selector,
        )


class ArtifactSchemaError(ArtifactReadError):
    """A canonical artifact does not satisfy its producer schema contract."""

    def __init__(self, selector: ArtifactSelector) -> None:
        super().__init__(
            ArtifactErrorCode.SCHEMA,
            "The canonical artifact does not satisfy its schema contract.",
            selector=selector,
        )


class DuplicateArtifactKeyError(ArtifactReadError):
    """A canonical table contains a null or duplicate primary key."""

    def __init__(self, selector: ArtifactSelector) -> None:
        super().__init__(
            ArtifactErrorCode.DUPLICATE_KEY,
            "The canonical artifact contains invalid primary keys.",
            selector=selector,
        )


class UnsupportedArtifactSelectorError(ArtifactReadError):
    """A logical selector is outside the fixed artifact allowlist."""

    def __init__(self) -> None:
        super().__init__(
            ArtifactErrorCode.UNSUPPORTED_SELECTOR,
            "The requested artifact selector is unsupported.",
        )


class InvalidArtifactRequestError(ArtifactReadError):
    """A typed internal request violates the reader's fixed bounds."""

    def __init__(self, selector: ArtifactSelector) -> None:
        super().__init__(
            ArtifactErrorCode.INVALID_REQUEST,
            "The artifact request is invalid or outside the supported range.",
            selector=selector,
        )


class UnsafeArtifactPathError(ArtifactReadError):
    """A canonical path traverses a symbolic link or leaves the repository root."""

    def __init__(self, selector: ArtifactSelector) -> None:
        super().__init__(
            ArtifactErrorCode.UNSAFE_PATH,
            "The canonical resource path is unsafe.",
            selector=selector,
        )
