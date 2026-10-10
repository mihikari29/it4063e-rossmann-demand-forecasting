"""Pure, path-free presentation helpers for the Phase 12 dashboard."""

from __future__ import annotations

import math
import re
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
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UnavailableReason,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ArtifactProvenance,
    CumulativeUncertainty,
    DailyInterval,
    ForecastPoint,
    InventoryAggregate,
    InventoryComparisonView,
    InventoryPolicyPair,
    ModelComparisonRow,
    ModelComparisonView,
    PolicyResult,
    ResourceStatus,
    SalesHistoryRow,
    ScenarioEntry,
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
_SAFE_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
MODEL_CANDIDATES = (
    "seasonal_naive",
    "holt_winters_additive_weekly",
    "global_lightgbm_gbdt_regression_l1",
)
MODEL_SCOPES = ("pooled", "validation_window", "horizon", "week_block", "store")
MODEL_METRICS = ("mae", "rmse", "mape", "wape")
MODEL_VALIDATION_WINDOWS = ("validation_1", "validation_2", "validation_3")
MODEL_COMMON_POPULATION = "three_way_common"
MODEL_STANDALONE_POPULATION = "standalone"
MODEL_COVERAGE_METRIC = "open_label_forecast_coverage_rate"
MODEL_MAPE_DIAGNOSTICS = ("mape_rows", "zero_actual_rows_excluded_from_mape")
MODEL_SAVED_METRICS = (
    *MODEL_METRICS,
    *MODEL_MAPE_DIAGNOSTICS,
    "eligible_rows",
    "forecast_available_rows",
    "observed_target_rows",
    "open_label_rows",
    "open_label_forecast_available_rows",
    "raw_forecast_coverage_rate",
    MODEL_COVERAGE_METRIC,
    "wape_actual_denominator",
)
INVENTORY_POLICY_IDS = (
    "historical_mean_standing_target",
    "lightgbm_buffer_standing_target",
)
INVENTORY_METRICS = (
    "SimulatedHoldingPlusShortfallCost",
    "ValueFillRate",
    "PositiveDemandStockoutRate",
    "AverageInventoryValue",
    "UnmetTurnoverValue",
    "CompletedPositiveDemandReceiptCycleServiceRate",
    "terminal_on_hand_value",
    "terminal_on_order_value",
    "TerminalStockCostValue",
    "OutstandingProcurementCommitment",
)
INVENTORY_REFERENCE_CASE = "synthetic_base-20150605-r00--reference"
INVENTORY_BUFFER_090_CASE = "synthetic_base-20150605-r00--buffer_090"
_SAFE_CASE_ID = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")


class ModelComparisonTooLargeError(ValueError):
    """A returned model comparison exceeds the explicit presentation query limit."""


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
    return [_history_row_record(row) for row in rows]


def history_chart_records(
    rows: tuple[SalesHistoryRow, ...], start_date: date, end_date: date
) -> list[dict[str, Any]]:
    """Build plotting-only calendar gaps; absent dates and null Sales remain null."""
    by_date: dict[str, dict[str, Any]] = {}
    for row in rows:
        record = _history_row_record(row)
        if record["Date"] in by_date:
            raise ValueError("Duplicate historical date.")
        by_date[record["Date"]] = record
    records = []
    current = start_date
    while current <= end_date:
        date_text = current.isoformat()
        row = by_date.get(date_text)
        records.append(
            {
                "Date": date_text,
                "Sales": row["Sales"] if row is not None else None,
                "Observed row": row is not None,
            }
        )
        current += timedelta(days=1)
    return records


def _history_row_record(row: SalesHistoryRow) -> dict[str, Any]:
    if not isinstance(row, SalesHistoryRow):
        raise TypeError("Unexpected historical Sales row.")
    if type(row.store_id) is not int or row.store_id < 1:
        raise TypeError("Unexpected historical Store identifier.")
    open_value = _display_number(row.open)
    if open_value is not None and (isinstance(open_value, bool) or open_value not in (0, 1)):
        raise TypeError("Unexpected historical Open value.")
    return {
        "Date": _iso_date(row.date),
        "Sales": _display_number(row.sales),
        "Source Open": open_value,
    }


def forecast_table_records(
    points: tuple[ForecastPoint, ...], max_horizon: int
) -> list[dict[str, Any]]:
    """Return saved forecast rows only, retaining raw/operational nulls and flags separately."""
    if max_horizon not in (7, 14):
        raise ValueError("Unsupported forecast display horizon.")
    records = []
    for point in points:
        _validate_forecast_point(point)
        if point.horizon <= max_horizon:
            records.append(
                {
                    "Date": _iso_date(point.date),
                    "Horizon": point.horizon,
                    "Raw forecast": _display_number(point.raw_forecast),
                    "Raw available": point.forecast_available,
                    "Operational forecast": _display_number(point.operational_forecast),
                    "Operational available": point.operational_forecast_available,
                    "Candidate": _safe_identifier(point.candidate_id),
                    "Selection run": _safe_identifier(point.model_selection_run_id),
                }
            )
    return sorted(records, key=lambda item: (item["Horizon"], item["Date"]))


def forecast_chart_records(
    points: tuple[ForecastPoint, ...], origin: date, max_horizon: int, series: str
) -> list[dict[str, Any]]:
    """Fill absent/unavailable horizons with plotting-only nulls to break the line."""
    if max_horizon not in (7, 14) or series not in ("raw", "operational"):
        raise ValueError("Unsupported forecast display selection.")
    for point in points:
        _validate_forecast_point(point)
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
        records.append(
            {"Date": _iso_date(date_text), "Horizon": horizon, "Forecast": _display_number(value)}
        )
    return records


def forecast_display_counts(points: tuple[ForecastPoint, ...], max_horizon: int) -> dict[str, int]:
    if max_horizon not in (7, 14):
        raise ValueError("Unsupported forecast display horizon.")
    for point in points:
        _validate_forecast_point(point)
    rows = [point for point in points if point.horizon <= max_horizon]
    return {
        "rows": len(rows),
        "raw_available": sum(point.forecast_available for point in rows),
        "operational_available": sum(point.operational_forecast_available for point in rows),
    }


def forecast_identity(points: tuple[ForecastPoint, ...]) -> list[dict[str, str]]:
    """Expose candidate and selection-run identities actually present in saved rows."""
    for point in points:
        _validate_forecast_point(point)
    identities = sorted(
        {
            (_safe_identifier(point.candidate_id), _safe_identifier(point.model_selection_run_id))
            for point in points
        }
    )
    return [{"Candidate": candidate, "Selection run": run_id} for candidate, run_id in identities]


def interval_table_records(
    intervals: tuple[DailyInterval, ...], interval_kind: str, max_horizon: int
) -> list[dict[str, Any]]:
    """Filter saved daily rows for display without filling, recalculating, or rounding."""
    if interval_kind not in ("raw", "operational") or max_horizon not in (7, 14):
        raise ValueError("Unsupported uncertainty display selection.")
    records = []
    for row in intervals:
        _validate_daily_interval(row)
        if row.interval_kind == interval_kind and row.horizon <= max_horizon:
            records.append(
                {
                    "Date": _iso_date(row.date),
                    "Horizon": row.horizon,
                    "Point estimate": _display_number(row.point_forecast),
                    "Lower": _display_number(row.lower),
                    "Upper": _display_number(row.upper),
                    "Width": _display_number(row.width),
                    "Available": row.available,
                    "Unavailable reason": _nullable_identifier(row.unavailable_reason),
                    "Units": _safe_identifier(row.units),
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
        _validate_cumulative_row(row)
        if row.prefix_days == prefix_days and row.probability == probability:
            records.append(
                {
                    "Prefix k": row.prefix_days,
                    "Probability": display_scalar(row.probability),
                    "Prefix complete": row.issued_prefix_complete,
                    "Unavailable reason": _nullable_identifier(row.unavailable_reason),
                    "D_k": _display_number(row.demand_value),
                    "Signed q": _display_number(row.signed_error_quantile),
                    "U_k": _display_number(row.upper_turnover_value),
                    "Safety stock": _display_number(row.safety_stock_value),
                    "Target": _display_number(row.target_value),
                    "Units": _safe_identifier(row.units),
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


def artifact_provenance_records(
    provenance: tuple[ArtifactProvenance, ...],
) -> list[dict[str, Any]]:
    """Convert provenance scalars without accepting arbitrary objects or local paths."""
    if not isinstance(provenance, tuple):
        raise TypeError("Unexpected artifact-provenance collection.")
    records = []
    for item in provenance:
        if not isinstance(item, ArtifactProvenance):
            raise TypeError("Unexpected artifact-provenance value.")
        records.append(
            {
                "selector": _safe_identifier(item.selector),
                "phase": _nullable_identifier(item.phase),
                "run_id": _nullable_identifier(item.run_id),
                "manifest_sha256": _nullable_identifier(item.manifest_sha256),
                "output_sha256": _nullable_identifier(item.output_sha256),
                "selected_rows": _nonnegative_int(item.selected_rows),
                "manifest_rows": _nonnegative_int(item.manifest_rows, allow_none=True),
            }
        )
    return records


def _display_number(value: Any) -> int | float | None:
    converted = display_scalar(value)
    if converted is None:
        return None
    if isinstance(converted, bool) or not isinstance(converted, int | float):
        raise TypeError("A numeric display value is required.")
    return converted


def _safe_identifier(value: object) -> str:
    if type(value) is not str or _SAFE_IDENTIFIER.fullmatch(value) is None:
        raise TypeError("A safe presentation identifier is required.")
    return value


def _nullable_identifier(value: object) -> str | None:
    return None if value is None else _safe_identifier(value)


def _nonnegative_int(value: object, *, allow_none: bool = False) -> int | None:
    if value is None and allow_none:
        return None
    if type(value) is not int or value < 0:
        raise TypeError("A nonnegative provenance count is required.")
    return value


def _iso_date(value: object) -> str:
    if type(value) is not str:
        raise TypeError("An ISO date is required for presentation.")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("A canonical ISO date is required for presentation.")
    return value


def _validate_forecast_point(point: ForecastPoint) -> None:
    if not isinstance(point, ForecastPoint):
        raise TypeError("Unexpected forecast point.")
    _iso_date(point.date)
    if type(point.horizon) is not int or not 1 <= point.horizon <= 14:
        raise TypeError("Unexpected forecast horizon.")
    _display_number(point.raw_forecast)
    _display_number(point.operational_forecast)
    if (
        type(point.forecast_available) is not bool
        or type(point.operational_forecast_available) is not bool
    ):
        raise TypeError("Unexpected forecast availability flag.")
    _safe_identifier(point.candidate_id)
    _safe_identifier(point.model_selection_run_id)


def _validate_daily_interval(row: DailyInterval) -> None:
    if not isinstance(row, DailyInterval):
        raise TypeError("Unexpected daily interval.")
    _iso_date(row.date)
    if type(row.horizon) is not int or not 1 <= row.horizon <= 14:
        raise TypeError("Unexpected interval horizon.")
    kind = _safe_identifier(row.interval_kind)
    if kind not in ("raw", "operational"):
        raise TypeError("Unexpected interval kind.")
    for value in (row.point_forecast, row.lower, row.upper, row.width):
        _display_number(value)
    if type(row.available) is not bool or type(row.schedule_assumption_flag) is not bool:
        raise TypeError("Unexpected interval availability flag.")
    _nullable_identifier(row.unavailable_reason)
    _safe_identifier(row.units)


def _validate_cumulative_row(row: CumulativeUncertainty) -> None:
    if not isinstance(row, CumulativeUncertainty):
        raise TypeError("Unexpected cumulative uncertainty row.")
    if type(row.prefix_days) is not int or not 1 <= row.prefix_days <= 14:
        raise TypeError("Unexpected cumulative prefix horizon.")
    probability = _display_number(row.probability)
    if probability not in SUPPORTED_CUMULATIVE_PROBABILITIES:
        raise TypeError("Unexpected cumulative probability.")
    if (
        type(row.issued_prefix_complete) is not bool
        or type(row.schedule_assumption_flag) is not bool
    ):
        raise TypeError("Unexpected cumulative availability flag.")
    _nullable_identifier(row.unavailable_reason)
    for value in (
        row.demand_value,
        row.signed_error_quantile,
        row.upper_turnover_value,
        row.safety_stock_value,
        row.target_value,
    ):
        _display_number(value)
    _safe_identifier(row.units)


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


def model_comparison_query_presets(
    scope: str,
    metric: str,
    *,
    validation_window: str | None = None,
    store_id: int | None = None,
) -> dict[str, ModelComparisonQuery]:
    """Build the fixed bounded saved-row queries used by Model Comparison."""
    if scope not in MODEL_SCOPES or metric not in MODEL_METRICS:
        raise ValueError("Unsupported model comparison selection.")
    if scope == "validation_window":
        if validation_window not in MODEL_VALIDATION_WINDOWS:
            raise ValueError("A supported validation window is required.")
    elif validation_window is not None:
        raise ValueError("Validation window is only supported by that scope.")
    if scope == "store":
        if type(store_id) is not int or not 1 <= store_id <= 1115:
            raise ValueError("A supported Store is required.")
    elif store_id is not None:
        raise ValueError("Store selection is only supported by that scope.")

    limit = 42 if scope == "horizon" else 200
    base = {
        "population": MODEL_COMMON_POPULATION,
        "scope": scope,
        "validation_window": validation_window,
        "store_id": store_id,
    }
    if scope == "horizon":
        queries = {}
        queries["primary"] = ModelComparisonQuery(metric=metric, limit=limit, **base)
        queries["wape"] = ModelComparisonQuery(metric="wape", limit=limit, **base)
        if metric == "mape":
            for diagnostic in MODEL_MAPE_DIAGNOSTICS:
                queries[diagnostic] = ModelComparisonQuery(metric=diagnostic, limit=limit, **base)
    else:
        queries = {"scope_metrics": ModelComparisonQuery(metric=None, limit=500, **base)}
    return queries


def horizon_mae_query_preset() -> ModelComparisonQuery:
    """Build the fixed bounded common-population query for the saved h1-h14 MAE rows."""
    return ModelComparisonQuery(
        population=MODEL_COMMON_POPULATION, scope="horizon", metric="mae", limit=42
    )


def standalone_coverage_query_preset() -> ModelComparisonQuery:
    """Build the fixed bounded query for the distinct standalone coverage population."""
    return ModelComparisonQuery(
        population=MODEL_STANDALONE_POPULATION,
        scope="validation_window",
        metric=MODEL_COVERAGE_METRIC,
        limit=200,
    )


def model_comparison_records(
    view: ModelComparisonView, query: ModelComparisonQuery
) -> list[dict[str, Any]]:
    """Validate one returned model view and preserve each saved comparison row exactly."""
    if not isinstance(view, ModelComparisonView) or not isinstance(query, ModelComparisonQuery):
        raise TypeError("Unexpected model comparison result.")
    if type(view.state) is not str or view.state not in ("available", "empty"):
        raise ValueError("Unexpected model comparison state.")
    if not isinstance(view.rows, tuple) or (view.state == "empty") != (not view.rows):
        raise ValueError("Model comparison state does not match its rows.")
    if len(view.rows) > query.limit:
        raise ModelComparisonTooLargeError
    keys = set()
    records = []
    for row in view.rows:
        key = _validate_model_comparison_row(row, query)
        if key in keys:
            raise ValueError("Duplicate model comparison dimensions were returned.")
        keys.add(key)
        records.append(_model_comparison_record(row))
    provenance = artifact_provenance_records((view.provenance,))
    if len(provenance) != 1 or provenance[0]["selector"] != "phase7_model_comparison":
        raise ValueError("Unexpected model comparison provenance.")
    return records


def _validate_model_comparison_row(
    row: ModelComparisonRow, query: ModelComparisonQuery
) -> tuple[object, ...]:
    if not isinstance(row, ModelComparisonRow):
        raise TypeError("Unexpected model comparison row.")
    candidate = _safe_identifier(row.candidate_id)
    if candidate not in MODEL_CANDIDATES:
        raise ValueError("Unexpected model candidate.")
    population = _safe_identifier(row.population)
    paired_with = _nullable_identifier(row.paired_with)
    scope = _safe_identifier(row.scope)
    window = _nullable_identifier(row.validation_window)
    metric = _safe_identifier(row.metric)
    if query.metric is None and metric not in MODEL_SAVED_METRICS:
        raise ValueError("Unexpected saved model comparison metric.")
    if population not in (MODEL_COMMON_POPULATION, MODEL_STANDALONE_POPULATION):
        raise ValueError("Unexpected model comparison population.")
    if scope not in MODEL_SCOPES:
        raise ValueError("Unexpected model comparison scope.")
    if row.horizon is not None and (type(row.horizon) is not int or not 1 <= row.horizon <= 14):
        raise TypeError("Unexpected saved horizon.")
    if window is not None and window not in MODEL_VALIDATION_WINDOWS:
        raise ValueError("Unexpected validation window.")
    if row.store_id is not None and (
        type(row.store_id) is not int or not 1 <= row.store_id <= 1115
    ):
        raise TypeError("Unexpected saved Store.")
    for name, value in (
        ("week_block_start_horizon", row.week_block_start_horizon),
        ("week_block_end_horizon", row.week_block_end_horizon),
    ):
        if value is not None and (type(value) is not int or not 1 <= value <= 14):
            raise TypeError(f"Unexpected {name}.")
    if (
        row.week_block_start_horizon is not None
        and row.week_block_end_horizon is not None
        and row.week_block_start_horizon > row.week_block_end_horizon
    ):
        raise ValueError("Saved week-block bounds are inverted.")
    for value in (
        row.value,
        row.numerator,
        row.denominator,
        row.paired_mae_delta,
        row.paired_mae_change_fraction,
    ):
        _display_number(value)
    reason = _nullable_identifier(row.unavailable_reason)
    if (
        population != query.population
        or scope != query.scope
        or (query.metric is not None and metric != query.metric)
        or (query.validation_window is not None and window != query.validation_window)
        or (query.horizon is not None and row.horizon != query.horizon)
        or (query.store_id is not None and row.store_id != query.store_id)
    ):
        raise ValueError("Model comparison rows do not match the applied query.")
    if scope == "horizon" and row.horizon is None:
        raise ValueError("A saved horizon row has no horizon value.")
    if scope == "validation_window" and window is None:
        raise ValueError("A saved validation-window row has no window value.")
    if scope == "store" and row.store_id is None:
        raise ValueError("A saved Store row has no Store value.")
    if scope == "week_block" and (
        row.week_block_start_horizon is None or row.week_block_end_horizon is None
    ):
        raise ValueError("A saved week-block row has no bounds.")
    _ = reason
    return (
        candidate,
        population,
        paired_with,
        scope,
        window,
        row.horizon,
        row.week_block_start_horizon,
        row.week_block_end_horizon,
        row.store_id,
        metric,
    )


def _model_comparison_record(row: ModelComparisonRow) -> dict[str, Any]:
    return {
        "candidate_id": row.candidate_id,
        "population": row.population,
        "scope": row.scope,
        "validation_window": row.validation_window,
        "horizon": row.horizon,
        "paired_with": row.paired_with,
        "week_block_start_horizon": row.week_block_start_horizon,
        "week_block_end_horizon": row.week_block_end_horizon,
        "Store": row.store_id,
        "metric": row.metric,
        "value": _display_number(row.value),
        "value_display": _format_metric_value(row.metric, row.value),
        "numerator": _display_number(row.numerator),
        "denominator": _display_number(row.denominator),
        "unavailable_reason": row.unavailable_reason,
        "paired_mae_delta": _display_number(row.paired_mae_delta),
        "paired_mae_change_fraction": _display_number(row.paired_mae_change_fraction),
        "paired_mae_change_fraction_display": _format_fraction(row.paired_mae_change_fraction),
    }


def _format_metric_value(metric: str, value: int | float | None) -> str | None:
    if value is None:
        return None
    if metric == "mape":
        return f"{value:g}% (percentage points)"
    if metric in ("wape", MODEL_COVERAGE_METRIC):
        return f"{value * 100:g}% (saved fraction {value:g})"
    return f"{value:g}"


def _format_fraction(value: int | float | None) -> str | None:
    return None if value is None else f"{value * 100:g}% (saved fraction {value:g})"


def model_candidate_labels(records: list[dict[str, Any]]) -> dict[str, str]:
    """Describe saved candidate availability without manufacturing missing values."""
    labels = {}
    for candidate in MODEL_CANDIDATES:
        candidate_rows = [row for row in records if row["candidate_id"] == candidate]
        if not candidate_rows:
            labels[candidate] = "No saved row returned"
        elif any(row["value"] is not None for row in candidate_rows):
            labels[candidate] = "Saved value available"
        else:
            labels[candidate] = "Saved values unavailable"
    return labels


def inventory_case_ids(catalog: ApplicationCatalog) -> tuple[str, ...]:
    """Validate and retain the exact opaque case IDs supplied by the catalog."""
    if not isinstance(catalog, ApplicationCatalog) or not isinstance(
        catalog.inventory_case_ids, tuple
    ):
        raise TypeError("Unexpected inventory case catalog.")
    case_ids = []
    for value in catalog.inventory_case_ids:
        if type(value) is not str or _SAFE_CASE_ID.fullmatch(value) is None:
            raise TypeError("Unexpected inventory case identifier.")
        case_ids.append(value)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Duplicate inventory cases were returned.")
    return tuple(case_ids)


def inventory_store_ids(catalog: ApplicationCatalog) -> tuple[int, ...]:
    """Validate the supported Store IDs without silently dropping catalog entries."""
    if not isinstance(catalog, ApplicationCatalog) or not isinstance(
        catalog.supported_store_ids, tuple
    ):
        raise TypeError("Unexpected supported Store catalog.")
    stores = catalog.supported_store_ids
    if any(type(value) is not int or not 1 <= value <= 1115 for value in stores):
        raise TypeError("Unexpected supported Store identifier.")
    if len(set(stores)) != len(stores):
        raise ValueError("Duplicate supported Stores were returned.")
    return stores


def scenario_catalog_records(catalog: ApplicationCatalog) -> list[dict[str, Any]]:
    """Present scenario metadata independently from the selected inventory case."""
    if not isinstance(catalog, ApplicationCatalog) or not isinstance(catalog.scenarios, tuple):
        raise TypeError("Unexpected scenario catalog.")
    records = []
    seen = set()
    for scenario in catalog.scenarios:
        if not isinstance(scenario, ScenarioEntry):
            raise TypeError("Unexpected scenario catalog entry.")
        scenario_id = _safe_identifier(scenario.scenario_id)
        if scenario_id in seen:
            raise ValueError("Duplicate scenario identifiers were returned.")
        seen.add(scenario_id)
        records.append(
            {
                "scenario_id": scenario_id,
                "family": _safe_identifier(scenario.family),
                "mode": _safe_identifier(scenario.mode),
                "forecast_origin": _iso_date(scenario.forecast_origin),
                "replicate": _nonnegative_int(scenario.replicate),
                "horizon_days": _nonnegative_int(scenario.horizon_days),
                "schedule_mode": _safe_identifier(scenario.schedule_mode),
                "demand_basis": _safe_identifier(scenario.demand_basis),
                "stress_spec_id": _safe_identifier(scenario.stress_spec_id),
                "calibration_transport_valid": _strict_bool(scenario.calibration_transport_valid),
            }
        )
    return records


def inventory_comparison_records(
    view: InventoryComparisonView, query: InventoryComparisonQuery
) -> dict[str, Any]:
    """Validate a complete inventory DTO before the screen renders any saved result."""
    if not isinstance(view, InventoryComparisonView) or not isinstance(
        query, InventoryComparisonQuery
    ):
        raise TypeError("Unexpected inventory comparison result.")
    if view.case_id != query.case_id or view.store_id != query.store_id:
        raise ValueError("Inventory result identity does not match the applied selection.")
    if type(view.state) is not str or view.state not in ("available", "empty"):
        raise ValueError("Unexpected inventory comparison state.")
    if not isinstance(view.policy_pairs, tuple) or (view.state == "empty") != (
        not view.policy_pairs
    ):
        raise ValueError("Inventory comparison state does not match its policy pairs.")
    if not isinstance(view.case_level_comparisons, tuple):
        raise TypeError("Unexpected inventory aggregate collection.")
    if len(view.case_level_comparisons) > 32 or len(view.policy_pairs) > 2230:
        raise ValueError("Inventory comparison exceeded its reader limit.")

    aggregate_records = []
    aggregate_metrics = set()
    for aggregate in view.case_level_comparisons:
        record = _inventory_aggregate_record(aggregate, query.case_id)
        metric = record["metric"]
        if metric in aggregate_metrics:
            raise ValueError("Duplicate inventory aggregate metrics were returned.")
        aggregate_metrics.add(metric)
        aggregate_records.append(record)
    metric_order = {metric: index for index, metric in enumerate(INVENTORY_METRICS)}
    aggregate_records.sort(key=lambda record: metric_order[record["metric"]])

    policy_records = []
    pair_records = []
    pair_keys = set()
    for pair in view.policy_pairs:
        pair_record, rows = _inventory_pair_records(pair, query.case_id)
        key = (pair_record["case_id"], pair_record["Store"])
        if key in pair_keys:
            raise ValueError("Duplicate Store policy pairs were returned.")
        pair_keys.add(key)
        if query.store_id is not None and pair_record["Store"] != query.store_id:
            raise ValueError("Inventory policy pair does not match the selected Store.")
        pair_records.append(pair_record)
        policy_records.extend(rows)

    provenance = artifact_provenance_records(view.provenance)
    expected_selectors = (
        "phase10_comparison",
        "phase10_policy_summary",
        "phase10_policy_targets",
    )
    if tuple(row["selector"] for row in provenance) != expected_selectors:
        raise ValueError("Unexpected inventory comparison provenance.")
    return {
        "aggregates": aggregate_records,
        "missing_metrics": [
            metric for metric in INVENTORY_METRICS if metric not in aggregate_metrics
        ],
        "pairs": pair_records,
        "policies": policy_records,
        "provenance": provenance,
    }


def _inventory_aggregate_record(row: InventoryAggregate, expected_case_id: str) -> dict[str, Any]:
    if not isinstance(row, InventoryAggregate):
        raise TypeError("Unexpected inventory aggregate row.")
    case_id = _case_id(row.case_id)
    metric = _safe_identifier(row.metric)
    if case_id != expected_case_id or metric not in INVENTORY_METRICS:
        raise ValueError("Inventory aggregate identity is unsupported.")
    count_names = (
        "requested_store_count",
        "baseline_standalone_store_count",
        "forecast_standalone_store_count",
        "matched_store_count",
    )
    counts = {name: _nonnegative_int(getattr(row, name)) for name in count_names}
    numeric_names = (
        "baseline_numerator",
        "baseline_denominator",
        "forecast_numerator",
        "forecast_denominator",
        "baseline_value",
        "forecast_value",
        "forecast_minus_baseline",
        "forecast_minus_baseline_relative",
    )
    numeric = {name: _display_number(getattr(row, name)) for name in numeric_names}
    null_reason = _nullable_identifier(row.null_reason)
    relative_reason = _nullable_identifier(row.relative_difference_null_reason)
    interpretation = _safe_plain_text(row.interpretation, max_length=500)
    direction = None
    if metric == "SimulatedHoldingPlusShortfallCost":
        direction = inventory_cost_direction(numeric["forecast_minus_baseline"], null_reason)
    return {
        "case_id": case_id,
        "metric": metric,
        **counts,
        **numeric,
        "null_reason": null_reason,
        "relative_difference_null_reason": relative_reason,
        "interpretation": interpretation,
        "cost_direction": direction,
    }


def _inventory_pair_records(
    pair: InventoryPolicyPair, expected_case_id: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(pair, InventoryPolicyPair):
        raise TypeError("Unexpected inventory policy pair.")
    case_id = _case_id(pair.case_id)
    if (
        case_id != expected_case_id
        or type(pair.store_id) is not int
        or not 1 <= pair.store_id <= 1115
    ):
        raise ValueError("Inventory policy pair identity is unsupported.")
    if type(pair.comparable) is not bool:
        raise TypeError("Unexpected inventory comparability flag.")
    difference = _display_number(pair.forecast_minus_baseline_cost)
    reason = _nullable_identifier(pair.difference_unavailable_reason)
    if pair.comparable and (difference is None or reason is not None):
        raise ValueError("Inventory saved cost difference is inconsistent with comparability.")
    if not pair.comparable and (difference is not None or reason is None):
        raise ValueError("Inventory saved cost difference is inconsistent with comparability.")
    pair_record = {
        "case_id": case_id,
        "Store": pair.store_id,
        "comparable": pair.comparable,
        "forecast_minus_baseline_cost": difference,
        "difference_unavailable_reason": reason,
        "cost_direction": inventory_cost_direction(difference, reason),
    }
    if not isinstance(pair.baseline, PolicyResult) or not isinstance(pair.forecast, PolicyResult):
        raise TypeError("Unexpected saved policy result.")
    rows = [
        _policy_result_record(pair.baseline, INVENTORY_POLICY_IDS[0]),
        _policy_result_record(pair.forecast, INVENTORY_POLICY_IDS[1]),
    ]
    expected_comparable = all(
        row["episode_complete"]
        and row["target_available"]
        and row["valid_matched_comparison"]
        and row["simulated_holding_plus_shortfall_cost"] is not None
        for row in rows
    )
    if pair.comparable != expected_comparable:
        raise ValueError("Inventory comparability does not match the saved policy states.")
    for row in rows:
        row["case_id"] = case_id
        row["Store"] = pair.store_id
    return pair_record, rows


def _policy_result_record(row: PolicyResult, expected_policy_id: str) -> dict[str, Any]:
    policy_id = _safe_identifier(row.policy_id)
    if policy_id != expected_policy_id:
        raise ValueError("Unexpected saved inventory policy identity.")
    if any(
        type(value) is not bool
        for value in (
            row.episode_complete,
            row.target_available,
            row.valid_matched_comparison,
            row.synthetic,
            row.calibration_transport_valid,
        )
    ):
        raise TypeError("Unexpected saved policy flag.")
    target_reason = _nullable_identifier(row.target_unavailability_reason)
    target_value = _display_number(row.target_value)
    if row.target_available != (target_reason is None and target_value is not None):
        raise ValueError("Saved target availability does not match its value and reason.")
    numeric = {
        "simulated_holding_plus_shortfall_cost": _display_number(
            row.simulated_holding_plus_shortfall_cost
        ),
        "demand_total": _display_number(row.demand_total),
        "fulfilled_total": _display_number(row.fulfilled_total),
        "unmet_total": _display_number(row.unmet_total),
        "target_value": target_value,
    }
    return {
        "policy_id": policy_id,
        "episode_status": _safe_identifier(row.episode_status),
        "episode_complete": row.episode_complete,
        "target_available": row.target_available,
        "target_unavailability_reason": target_reason,
        "availability_reason": _nullable_identifier(row.availability_reason),
        "valid_matched_comparison": row.valid_matched_comparison,
        **numeric,
        "synthetic": row.synthetic,
        "calibration_transport_valid": row.calibration_transport_valid,
        "schedule_assumption": _safe_identifier(row.schedule_assumption),
    }


def inventory_cost_direction(
    value: int | float | None, unavailable_reason: str | None = None
) -> str:
    """Label the saved forecast-minus-baseline cost without calculating a difference."""
    converted = _display_number(value)
    reason = _nullable_identifier(unavailable_reason)
    if converted is None:
        return "Unavailable — " + (reason if reason is not None else "no saved reason")
    if converted > 0:
        return "Adverse — higher simulated cost"
    if converted < 0:
        return "Favorable — lower simulated cost, conditional on assumptions"
    return "Equal simulated cost"


def _case_id(value: object) -> str:
    if type(value) is not str or _SAFE_CASE_ID.fullmatch(value) is None:
        raise TypeError("A safe inventory case identifier is required.")
    return value


def _strict_bool(value: object) -> bool:
    if type(value) is not bool:
        raise TypeError("A Boolean display value is required.")
    return value


def _safe_plain_text(value: object, *, max_length: int) -> str:
    if (
        type(value) is not str
        or len(value) > max_length
        or any(ord(character) < 32 for character in value)
        or re.search(r"[A-Za-z]:\\|\\\\|/(?:[A-Za-z0-9_.-]+)", value)
    ):
        raise TypeError("Unexpected saved explanatory text.")
    return value
