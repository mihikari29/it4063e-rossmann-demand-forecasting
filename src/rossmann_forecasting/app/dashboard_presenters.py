"""Pure, path-free presentation helpers for the Phase 12 dashboard."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.app.contracts import (
    ArtifactErrorCode,
    ArtifactReadError,
    ArtifactSelector,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ArtifactProvenance,
    ResourceStatus,
)

_ERROR_MESSAGES = {
    ArtifactErrorCode.UNAVAILABLE: (
        "A required saved resource is unavailable. Static project information remains available."
    ),
    ArtifactErrorCode.INTEGRITY: (
        "A saved catalog failed its integrity check. Unverified catalog details are hidden."
    ),
    ArtifactErrorCode.SCHEMA: (
        "A saved catalog does not match its accepted schema. Unverified catalog details are hidden."
    ),
    ArtifactErrorCode.DUPLICATE_KEY: (
        "A saved catalog contains invalid keys. Unverified catalog details are hidden."
    ),
    ArtifactErrorCode.UNSUPPORTED_SELECTOR: "The requested saved resource is unsupported.",
    ArtifactErrorCode.INVALID_REQUEST: "The saved-resource request is invalid.",
    ArtifactErrorCode.UNSAFE_PATH: "A saved resource failed a path-safety check.",
}


@dataclass(frozen=True, slots=True)
class ErrorNotice:
    """A fixed safe message for display, with only allowlisted logical identifiers."""

    code: str
    message: str
    selector: str | None


def display_scalar(value: Any) -> str | int | float | bool | None:
    """Convert one scalar without collapsing nulls into zero or exposing object reprs."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        return display_scalar(value.item())
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return str(value.value)
    if isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("A non-finite display value is not supported.")
        return value
    raise TypeError("A non-scalar display value is not supported.")


def resource_status_records(resources: tuple[ResourceStatus, ...]) -> list[dict[str, Any]]:
    """Return the actual readiness fields, omitting an unvalidated manifest digest."""
    records = []
    for resource in resources:
        if not isinstance(resource, ResourceStatus):
            raise TypeError("Unexpected resource-status value.")
        records.append(
            {
                "selector": display_scalar(resource.selector),
                "phase": display_scalar(resource.phase),
                "run_id": display_scalar(resource.run_id),
                "validation_level": display_scalar(resource.validation_level),
                "output_present": display_scalar(resource.output_present),
                "manifest_validated": display_scalar(resource.manifest_validated),
                "manifest_sha256": (
                    display_scalar(resource.manifest_sha256)
                    if resource.manifest_validated
                    else None
                ),
                "output_hash_verified": display_scalar(resource.output_hash_verified),
                "error_code": display_scalar(resource.error_code),
            }
        )
    return records


def catalog_provenance_records(catalog: ApplicationCatalog) -> list[dict[str, Any]]:
    """Expose only provenance DTOs returned after a successful service read."""
    records = []
    for provenance in (catalog.scenario_provenance, catalog.inventory_case_provenance):
        if provenance is None:
            continue
        if not isinstance(provenance, ArtifactProvenance):
            raise TypeError("Unexpected catalog-provenance value.")
        records.append(
            {
                "selector": display_scalar(provenance.selector),
                "phase": display_scalar(provenance.phase),
                "run_id": display_scalar(provenance.run_id),
                "manifest_sha256": display_scalar(provenance.manifest_sha256),
                "output_sha256": display_scalar(provenance.output_sha256),
                "selected_rows": display_scalar(provenance.selected_rows),
                "manifest_rows": display_scalar(provenance.manifest_rows),
            }
        )
    return records


def error_notice(error: Exception) -> ErrorNotice:
    """Map known service errors to fixed copy; never echo exception text or paths."""
    if isinstance(error, ArtifactReadError) and isinstance(error.code, ArtifactErrorCode):
        return ErrorNotice(
            code=error.code.value,
            message=_ERROR_MESSAGES[error.code],
            selector=(
                error.selector.value if isinstance(error.selector, ArtifactSelector) else None
            ),
        )
    return ErrorNotice(
        code="internal_error",
        message="The saved-resource check could not be completed. Error details are hidden.",
        selector=None,
    )
