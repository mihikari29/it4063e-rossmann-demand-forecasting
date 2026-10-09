"""Pure, path-free presentation helpers for the Phase 12 dashboard."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.app.contracts import (
    ArtifactErrorCode,
    ArtifactReadError,
    ArtifactSelector,
    UnavailableReason,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ArtifactProvenance,
    CumulativeUncertainty,
    DailyInterval,
    ForecastPoint,
    ResourceStatus,
    SalesHistoryRow,
)

_ERROR_MESSAGES = {
    ArtifactErrorCode.UNAVAILABLE: "A required resource is unavailable.",
    ArtifactErrorCode.INTEGRITY: (
        "A resource failed its integrity check. Unverified details are hidden."
    ),
    ArtifactErrorCode.SCHEMA: (
        "A resource does not match its accepted schema. Unverified details are hidden."
    ),
    ArtifactErrorCode.DUPLICATE_KEY: (
        "A resource contains invalid keys. Unverified details are hidden."
    ),
    ArtifactErrorCode.UNSUPPORTED_SELECTOR: "The requested resource is unsupported.",
    ArtifactErrorCode.INVALID_REQUEST: "The resource request is invalid.",
    ArtifactErrorCode.UNSAFE_PATH: "A resource failed a path-safety check.",
}

HISTORY_MIN_DATE = date(2013, 1, 1)
HISTORY_MAX_DATE = date(2015, 7, 3)
HISTORY_DEFAULT_START = date(2015, 5, 9)
HISTORY_DEFAULT_END = date(2015, 7, 3)
HISTORY_MAX_DAYS = 366
SUPPORTED_FORECAST_ORIGINS = ("2015-05-22", "2015-06-05", "2015-06-19")
SUPPORTED_FIT_ORIGINS = {"A": "2015-06-05", "B": "2015-06-19"}
SUPPORTED_CUMULATIVE_PROBABILITIES = (0.90, 0.95, 0.98)


def validate_history_selection(
    store_id: object,
    start_date: object,
    end_date: object,
    supported_store_ids: tuple[int, ...],
) -> str | None:
    """Return a fixed form error before dispatch for an invalid bounded history query."""
    if (
        isinstance(store_id, bool)
        or not isinstance(store_id, int)
        or store_id not in supported_store_ids
    ):
        return "Choose a Store from the supported catalog."
    if type(start_date) is not date or type(end_date) is not date:
        return "Choose valid start and end dates."
    if start_date < HISTORY_MIN_DATE or end_date > HISTORY_MAX_DATE:
        return "Dates must be from 2013-01-01 through 2015-07-03."
    if start_date > end_date:
        return "The start date must be on or before the end date."
    if (end_date - start_date).days + 1 > HISTORY_MAX_DAYS:
        return "Choose no more than 366 inclusive calendar days."
    return None


def history_source_records(rows: tuple[SalesHistoryRow, ...]) -> list[dict[str, Any]]:
    """Keep only the bounded source row fields and preserve null and zero values."""
    records = []
    for row in rows:
        if not isinstance(row, SalesHistoryRow):
            raise TypeError("Unexpected historical Sales row.")
        records.append(
            {
                "Date": row.date,
                "Sales": display_scalar(row.sales),
                "Source Open": display_scalar(row.open),
            }
        )
    return records


def history_chart_records(
    rows: tuple[SalesHistoryRow, ...], start_date: date, end_date: date
) -> list[dict[str, Any]]:
    """Build plotting-only calendar gaps; absent dates and null Sales remain null."""
    by_date: dict[str, SalesHistoryRow] = {}
    for row in rows:
        if not isinstance(row, SalesHistoryRow):
            raise TypeError("Unexpected historical Sales row.")
        if row.date in by_date:
            raise ValueError("Duplicate historical date.")
        by_date[row.date] = row
    records = []
    current = start_date
    while current <= end_date:
        date_text = current.isoformat()
        row = by_date.get(date_text)
        records.append(
            {
                "Date": date_text,
                "Sales": display_scalar(row.sales) if row is not None else None,
                "Observed row": row is not None,
            }
        )
        current += timedelta(days=1)
    return records


def forecast_table_records(
    points: tuple[ForecastPoint, ...], max_horizon: int
) -> list[dict[str, Any]]:
    """Return saved forecast rows only, retaining raw/operational nulls and flags separately."""
    if max_horizon not in (7, 14):
        raise ValueError("Unsupported forecast display horizon.")
    records = []
    for point in points:
        if not isinstance(point, ForecastPoint):
            raise TypeError("Unexpected forecast point.")
        if point.horizon <= max_horizon:
            records.append(
                {
                    "Date": point.date,
                    "Horizon": point.horizon,
                    "Raw forecast": display_scalar(point.raw_forecast),
                    "Raw available": point.forecast_available,
                    "Operational forecast": display_scalar(point.operational_forecast),
                    "Operational available": point.operational_forecast_available,
                    "Candidate": point.candidate_id,
                    "Selection run": point.model_selection_run_id,
                }
            )
    return sorted(records, key=lambda item: (item["Horizon"], item["Date"]))


def forecast_chart_records(
    points: tuple[ForecastPoint, ...], origin: date, max_horizon: int, series: str
) -> list[dict[str, Any]]:
    """Fill absent/unavailable horizons with plotting-only nulls to break the line."""
    if max_horizon not in (7, 14) or series not in ("raw", "operational"):
        raise ValueError("Unsupported forecast display selection.")
    by_horizon = {point.horizon: point for point in points if point.horizon <= max_horizon}
    records = []
    for horizon in range(1, max_horizon + 1):
        point = by_horizon.get(horizon)
        available = False
        value = None
        date_text = (origin + timedelta(days=horizon)).isoformat()
        if point is not None:
            date_text = point.date
            available = (
                point.forecast_available
                if series == "raw"
                else point.operational_forecast_available
            )
            value = point.raw_forecast if series == "raw" else point.operational_forecast
            if not available:
                value = None
        records.append({"Date": date_text, "Horizon": horizon, "Forecast": display_scalar(value)})
    return records


def forecast_display_counts(points: tuple[ForecastPoint, ...], max_horizon: int) -> dict[str, int]:
    rows = [point for point in points if point.horizon <= max_horizon]
    return {
        "rows": len(rows),
        "raw_available": sum(point.forecast_available for point in rows),
        "operational_available": sum(point.operational_forecast_available for point in rows),
    }


def forecast_identity(points: tuple[ForecastPoint, ...]) -> list[dict[str, str]]:
    """Expose candidate and selection-run identities actually present in saved rows."""
    identities = sorted({(point.candidate_id, point.model_selection_run_id) for point in points})
    return [{"Candidate": candidate, "Selection run": run_id} for candidate, run_id in identities]


def interval_table_records(
    intervals: tuple[DailyInterval, ...], interval_kind: str, max_horizon: int
) -> list[dict[str, Any]]:
    """Filter saved daily rows for display without filling, recalculating, or rounding."""
    if interval_kind not in ("raw", "operational") or max_horizon not in (7, 14):
        raise ValueError("Unsupported uncertainty display selection.")
    records = []
    for row in intervals:
        if not isinstance(row, DailyInterval):
            raise TypeError("Unexpected daily interval.")
        if row.interval_kind == interval_kind and row.horizon <= max_horizon:
            records.append(
                {
                    "Date": row.date,
                    "Horizon": row.horizon,
                    "Point estimate": display_scalar(row.point_forecast),
                    "Lower": display_scalar(row.lower),
                    "Upper": display_scalar(row.upper),
                    "Width": display_scalar(row.width),
                    "Available": row.available,
                    "Unavailable reason": row.unavailable_reason,
                    "Units": row.units,
                    "Schedule assumption": row.schedule_assumption_flag,
                }
            )
    return sorted(records, key=lambda item: (item["Horizon"], item["Date"]))


def interval_band_segments(
    intervals: tuple[DailyInterval, ...], interval_kind: str, max_horizon: int
) -> list[list[dict[str, Any]]]:
    """Return contiguous saved available bands; unavailable or absent horizons split segments."""
    table = interval_table_records(intervals, interval_kind, max_horizon)
    segments: list[list[dict[str, Any]]] = []
    previous_horizon: int | None = None
    previous_date: date | None = None
    for row in table:
        row_date = date.fromisoformat(row["Date"])
        plottable = row["Available"] and row["Lower"] is not None and row["Upper"] is not None
        contiguous = (
            plottable
            and segments
            and previous_horizon is not None
            and row["Horizon"] == previous_horizon + 1
            and previous_date is not None
            and row_date == previous_date + timedelta(days=1)
        )
        if not plottable:
            previous_horizon = None
            previous_date = None
            continue
        if not contiguous:
            segments.append([])
        segments[-1].append(row)
        previous_horizon = row["Horizon"]
        previous_date = row_date
    return segments


def cumulative_table_records(
    rows: tuple[CumulativeUncertainty, ...], prefix_days: int, probability: float
) -> list[dict[str, Any]]:
    """Select saved prefix rows exactly; signed quantiles are never clipped or summed."""
    records = []
    for row in rows:
        if not isinstance(row, CumulativeUncertainty):
            raise TypeError("Unexpected cumulative uncertainty row.")
        if row.prefix_days == prefix_days and row.probability == probability:
            records.append(
                {
                    "Prefix k": row.prefix_days,
                    "Probability": display_scalar(row.probability),
                    "Prefix complete": row.issued_prefix_complete,
                    "Unavailable reason": row.unavailable_reason,
                    "D_k": display_scalar(row.demand_value),
                    "Signed q": display_scalar(row.signed_error_quantile),
                    "U_k": display_scalar(row.upper_turnover_value),
                    "Safety stock": display_scalar(row.safety_stock_value),
                    "Target": display_scalar(row.target_value),
                    "Units": row.units,
                    "Schedule assumption": row.schedule_assumption_flag,
                }
            )
    return records


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
        message = _ERROR_MESSAGES[error.code]
        if error.code is ArtifactErrorCode.UNAVAILABLE and error.unavailable is not None:
            if error.unavailable.reason is UnavailableReason.MISSING_MANIFEST:
                message = "A required resource manifest is missing."
            elif error.unavailable.reason is UnavailableReason.MISSING_ARTIFACT:
                message = "A required resource file is missing."
        return ErrorNotice(
            code=error.code.value,
            message=message,
            selector=(
                error.selector.value if isinstance(error.selector, ArtifactSelector) else None
            ),
        )
    return ErrorNotice(
        code="internal_error",
        message="The request could not be completed. Error details are hidden.",
        selector=None,
    )
