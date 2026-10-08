"""Read-only shared services over the pinned Phase 7–10 development results."""

from __future__ import annotations

import math
from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from enum import StrEnum
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.app.artifacts import (
    _ARTIFACTS,
    _DEFAULT_READER,
    MAX_STORE_ID,
    PHASE7_FORECAST_ORIGINS,
    PHASE8_FIT_ORIGINS,
    _ArtifactReader,
)
from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactReadError,
    ArtifactReadiness,
    ArtifactSchemaError,
    ArtifactSelector,
    ArtifactTable,
    ArtifactUnavailableError,
    ForecastQuery,
    HistoryQuery,
    InvalidArtifactRequestError,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    Phase,
    UncertaintyQuery,
)
from rossmann_forecasting.inventory.simulation import POLICY_IDS


class ViewState(StrEnum):
    AVAILABLE = "available"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ArtifactProvenance:
    selector: str
    phase: str | None
    run_id: str | None
    manifest_sha256: str | None
    output_sha256: str | None
    selected_rows: int
    manifest_rows: int | None


@dataclass(frozen=True, slots=True)
class ResourceStatus:
    selector: str
    phase: str
    run_id: str
    manifest_sha256: str
    validation_level: str
    output_present: bool
    manifest_validated: bool
    output_hash_verified: bool
    error_code: str | None


@dataclass(frozen=True, slots=True)
class ScenarioEntry:
    scenario_id: str
    family: str
    mode: str
    forecast_origin: str
    replicate: int
    horizon_days: int
    schedule_mode: str
    demand_basis: str
    stress_spec_id: str
    calibration_transport_valid: bool


@dataclass(frozen=True, slots=True)
class ApplicationCatalog:
    phases: tuple[str, ...]
    selectors: tuple[str, ...]
    supported_store_ids: tuple[int, ...]
    phase7_forecast_origins: tuple[str, ...]
    phase8_fits: tuple[tuple[str, str], ...]
    scenario_catalog_state: str
    scenarios: tuple[ScenarioEntry, ...]
    inventory_case_state: str
    inventory_case_ids: tuple[str, ...]
    resources: tuple[ResourceStatus, ...]
    scenario_provenance: ArtifactProvenance | None
    inventory_case_provenance: ArtifactProvenance | None


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    date: str
    horizon: int
    raw_forecast: float | None
    operational_forecast: float | None
    forecast_available: bool
    operational_forecast_available: bool
    candidate_id: str
    model_selection_run_id: str


@dataclass(frozen=True, slots=True)
class ForecastIssuanceView:
    state: str
    query: ForecastQuery
    points: tuple[ForecastPoint, ...]
    provenance: ArtifactProvenance


@dataclass(frozen=True, slots=True)
class DailyInterval:
    date: str
    horizon: int
    interval_kind: str
    point_forecast: float | None
    lower: float | None
    upper: float | None
    width: float | None
    available: bool
    unavailable_reason: str | None
    units: str
    schedule_assumption_flag: bool


@dataclass(frozen=True, slots=True)
class CumulativeUncertainty:
    prefix_days: int
    probability: float
    issued_prefix_complete: bool
    unavailable_reason: str | None
    demand_value: float | None
    signed_error_quantile: float | None
    upper_turnover_value: float | None
    safety_stock_value: float | None
    target_value: float | None
    units: str
    schedule_assumption_flag: bool


@dataclass(frozen=True, slots=True)
class ForecastUncertaintyView:
    state: str
    query: UncertaintyQuery
    daily_intervals: tuple[DailyInterval, ...]
    cumulative_uncertainty: tuple[CumulativeUncertainty, ...]
    interpretation: str
    provenance: tuple[ArtifactProvenance, ...]


@dataclass(frozen=True, slots=True)
class ModelComparisonRow:
    candidate_id: str
    population: str
    paired_with: str | None
    scope: str
    validation_window: str | None
    horizon: int | None
    week_block_start_horizon: int | None
    week_block_end_horizon: int | None
    store_id: int | None
    metric: str
    value: float | None
    numerator: float | None
    denominator: float | None
    unavailable_reason: str | None
    paired_mae_delta: float | None
    paired_mae_change_fraction: float | None


@dataclass(frozen=True, slots=True)
class ModelComparisonView:
    state: str
    rows: tuple[ModelComparisonRow, ...]
    provenance: ArtifactProvenance


@dataclass(frozen=True, slots=True)
class PolicyResult:
    policy_id: str
    episode_status: str
    episode_complete: bool
    target_available: bool
    availability_reason: str | None
    valid_matched_comparison: bool
    simulated_holding_plus_shortfall_cost: float | None
    demand_total: float | None
    fulfilled_total: float | None
    unmet_total: float | None
    target_value: float | None
    synthetic: bool
    calibration_transport_valid: bool
    schedule_assumption: str


@dataclass(frozen=True, slots=True)
class InventoryPolicyPair:
    case_id: str
    store_id: int
    comparable: bool
    forecast_minus_baseline_cost: float | None
    difference_unavailable_reason: str | None
    baseline: PolicyResult
    forecast: PolicyResult


@dataclass(frozen=True, slots=True)
class InventoryAggregate:
    case_id: str
    metric: str
    requested_store_count: int
    baseline_standalone_store_count: int
    forecast_standalone_store_count: int
    matched_store_count: int
    baseline_numerator: float | None
    baseline_denominator: float | None
    forecast_numerator: float | None
    forecast_denominator: float | None
    baseline_value: float | None
    forecast_value: float | None
    forecast_minus_baseline: float | None
    forecast_minus_baseline_relative: float | None
    relative_difference_null_reason: str | None
    null_reason: str | None
    interpretation: str


@dataclass(frozen=True, slots=True)
class InventoryComparisonView:
    state: str
    case_id: str
    store_id: int | None
    case_level_comparisons: tuple[InventoryAggregate, ...]
    policy_pairs: tuple[InventoryPolicyPair, ...]
    provenance: tuple[ArtifactProvenance, ...]


@dataclass(frozen=True, slots=True)
class SalesHistoryRow:
    store_id: int
    date: str
    sales: float | None
    open: float | None


@dataclass(frozen=True, slots=True)
class SalesHistoryView:
    state: str
    rows: tuple[SalesHistoryRow, ...]
    through_date: str
    selector: str


class ApplicationServices:
    """Small composition layer; every resource still passes through the M1 reader."""

    def __init__(self, reader: _ArtifactReader | None = None) -> None:
        self._reader = _DEFAULT_READER if reader is None else reader

    def catalog(self) -> ApplicationCatalog:
        scenario_table: ArtifactTable | None = None
        comparison_table: ArtifactTable | None = None
        scenario_state = ViewState.AVAILABLE
        case_state = ViewState.AVAILABLE
        try:
            scenario_table = self._reader.read(ArtifactSelector.PHASE9_SCENARIO_CATALOG)
        except ArtifactUnavailableError:
            scenario_state = ViewState.UNAVAILABLE
        try:
            comparison_table = self._reader.read(ArtifactSelector.PHASE10_COMPARISON)
        except ArtifactUnavailableError:
            case_state = ViewState.UNAVAILABLE

        scenarios = (
            tuple(
                _scenario_entry(row)
                for row in _ordered_records(scenario_table.frame, sort_by=("scenario_id",))
            )
            if scenario_table is not None
            else ()
        )
        if scenario_table is not None and not scenarios:
            scenario_state = ViewState.EMPTY
        case_ids = (
            tuple(sorted(set(comparison_table.frame["case_id"].dropna().tolist())))
            if comparison_table is not None
            else ()
        )
        if comparison_table is not None and not case_ids:
            case_state = ViewState.EMPTY
        resources = tuple(_resource_status(item) for item in self._reader.inspect_readiness())
        return ApplicationCatalog(
            phases=tuple(phase.value for phase in Phase),
            selectors=tuple(item.selector for item in resources)
            + (ArtifactSelector.HISTORICAL_SALES.value,),
            supported_store_ids=tuple(range(1, MAX_STORE_ID + 1)),
            phase7_forecast_origins=tuple(item.isoformat() for item in PHASE7_FORECAST_ORIGINS),
            phase8_fits=tuple(
                (fit_id, origin.isoformat()) for fit_id, origin in PHASE8_FIT_ORIGINS.items()
            ),
            scenario_catalog_state=scenario_state.value,
            scenarios=scenarios,
            inventory_case_state=case_state.value,
            inventory_case_ids=case_ids,
            resources=resources,
            scenario_provenance=_provenance(scenario_table) if scenario_table else None,
            inventory_case_provenance=_provenance(comparison_table) if comparison_table else None,
        )

    def forecast_issuance(self, query: ForecastQuery) -> ForecastIssuanceView:
        table = self._reader.read_forecasts(query)
        rows = tuple(
            _forecast_point(row)
            for row in _ordered_records(table.frame, sort_by=("Date", "horizon"))
        )
        return ForecastIssuanceView(
            state=_view_state(rows),
            query=query,
            points=rows,
            provenance=_provenance(table),
        )

    def forecast_uncertainty(self, query: UncertaintyQuery) -> ForecastUncertaintyView:
        daily_table = self._reader.read_daily_intervals(query)
        cumulative_table = self._reader.read_cumulative_uncertainty(query)
        daily = tuple(
            _daily_interval(row)
            for row in _ordered_records(daily_table.frame, sort_by=("Date", "interval_kind"))
        )
        cumulative = tuple(
            _cumulative_uncertainty(row)
            for row in _ordered_records(cumulative_table.frame, sort_by=("k", "p"))
        )
        state = ViewState.AVAILABLE if daily or cumulative else ViewState.EMPTY
        return ForecastUncertaintyView(
            state=state.value,
            query=query,
            daily_intervals=daily,
            cumulative_uncertainty=cumulative,
            interpretation=(
                "Saved development empirical intervals and cumulative prefix quantiles retain "
                "their recorded availability and assumptions. They are not a 95% performance "
                "guarantee, coverage claim, or recalibrated estimate."
            ),
            provenance=(_provenance(daily_table), _provenance(cumulative_table)),
        )

    def model_comparison(self, query: ModelComparisonQuery) -> ModelComparisonView:
        table = self._reader.read_model_comparison(query)
        rows = tuple(
            _model_comparison_row(row)
            for row in _ordered_records(
                table.frame,
                sort_by=(
                    "candidate_id",
                    "population",
                    "scope",
                    "validation_window",
                    "horizon",
                    "Store",
                    "metric",
                ),
            )
        )
        return ModelComparisonView(
            state=_view_state(rows), rows=rows, provenance=_provenance(table)
        )

    def inventory_comparison(self, query: InventoryComparisonQuery) -> InventoryComparisonView:
        comparisons = self._reader.read_inventory_comparison(query)
        if comparisons.frame.empty:
            raise InvalidArtifactRequestError(ArtifactSelector.PHASE10_COMPARISON)
        summary = self._reader.read_inventory_artifact(
            ArtifactSelector.PHASE10_POLICY_SUMMARY, query
        )
        targets = self._reader.read_inventory_artifact(
            ArtifactSelector.PHASE10_POLICY_TARGETS, query
        )
        pairs = _policy_pairs(summary, targets)
        aggregates = tuple(_inventory_aggregate(row) for row in _ordered_records(comparisons.frame))
        return InventoryComparisonView(
            state=_view_state(pairs),
            case_id=query.case_id,
            store_id=query.store_id,
            case_level_comparisons=aggregates,
            policy_pairs=pairs,
            provenance=(
                _provenance(comparisons),
                _provenance(summary),
                _provenance(targets),
            ),
        )

    def sales_history(self, query: HistoryQuery) -> SalesHistoryView:
        selector = ArtifactSelector.HISTORICAL_SALES
        try:
            frame = self._reader.read_history_sales(query)
        except ArtifactReadError:
            raise
        except Exception:
            raise ArtifactSchemaError(selector) from None
        rows = tuple(_sales_history_row(row) for row in _ordered_records(frame, sort_by=("Date",)))
        return SalesHistoryView(
            state=_view_state(rows),
            rows=rows,
            through_date="2015-07-03",
            selector=selector.value,
        )


def json_safe(value: Any) -> Any:
    """Convert service DTOs to JSON primitives while refusing non-finite numbers."""
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: json_safe(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Service DTO contains a non-finite number.")
    return value


def _resource_status(item: ArtifactReadiness) -> ResourceStatus:
    return ResourceStatus(
        selector=item.selector.value,
        phase=item.phase.value,
        run_id=item.run_id,
        manifest_sha256=item.manifest_sha256,
        validation_level=item.level.value,
        output_present=item.output_present,
        manifest_validated=item.manifest_validated,
        output_hash_verified=item.output_hash_verified,
        error_code=item.error_code.value if item.error_code is not None else None,
    )


def _provenance(table: ArtifactTable) -> ArtifactProvenance:
    phase = _ARTIFACTS[table.selector].phase.value
    return ArtifactProvenance(
        selector=table.selector.value,
        phase=phase,
        run_id=table.run_id,
        manifest_sha256=table.manifest_sha256,
        output_sha256=table.output_sha256,
        selected_rows=table.selected_rows,
        manifest_rows=table.manifest_rows,
    )


def _view_state(items: tuple[Any, ...]) -> str:
    return ViewState.AVAILABLE.value if items else ViewState.EMPTY.value


def _ordered_records(
    frame: pd.DataFrame, *, sort_by: tuple[str, ...] | None = None
) -> list[dict[str, Any]]:
    if sort_by and not frame.empty:
        frame = frame.sort_values(list(sort_by), kind="stable")
    return frame.to_dict(orient="records")


def _is_null(value: Any) -> bool:
    if value is None or value is pd.NA or value is pd.NaT:
        return True
    return bool(pd.isna(value))


def _text(value: Any, selector: ArtifactSelector, *, optional: bool = False) -> str | None:
    if _is_null(value):
        if optional:
            return None
        raise ArtifactSchemaError(selector)
    if not isinstance(value, str) or not value:
        raise ArtifactSchemaError(selector)
    return value


def _integer(value: Any, selector: ArtifactSelector, *, optional: bool = False) -> int | None:
    if _is_null(value):
        if optional:
            return None
        raise ArtifactSchemaError(selector)
    if isinstance(value, (bool, np.bool_)):
        raise ArtifactSchemaError(selector)
    try:
        result = int(value)
        if float(value) != result:
            raise ArtifactSchemaError(selector)
    except ArtifactSchemaError:
        raise
    except Exception:
        raise ArtifactSchemaError(selector) from None
    return result


def _number(value: Any, selector: ArtifactSelector) -> float | None:
    if _is_null(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        raise ArtifactSchemaError(selector)
    try:
        result = float(value)
    except Exception:
        raise ArtifactSchemaError(selector) from None
    if not math.isfinite(result):
        raise ArtifactSchemaError(selector)
    return result


def _boolean(value: Any, selector: ArtifactSelector) -> bool:
    if _is_null(value) or not isinstance(value, (bool, np.bool_)):
        raise ArtifactSchemaError(selector)
    return bool(value)


def _date_text(value: Any, selector: ArtifactSelector) -> str:
    if _is_null(value):
        raise ArtifactSchemaError(selector)
    try:
        timestamp = pd.Timestamp(value)
    except Exception:
        raise ArtifactSchemaError(selector) from None
    if pd.isna(timestamp) or timestamp.tz is not None:
        raise ArtifactSchemaError(selector)
    if timestamp != timestamp.normalize():
        raise ArtifactSchemaError(selector)
    return timestamp.date().isoformat()


def _provenance_row(row: dict[str, Any], selector: ArtifactSelector) -> tuple[str, str]:
    candidate = _text(row.get("selected_candidate_id", row.get("candidate_id")), selector)
    run_id = _text(row.get("model_selection_run_id"), selector)
    return candidate, run_id


def _scenario_entry(row: dict[str, Any]) -> ScenarioEntry:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    return ScenarioEntry(
        scenario_id=_text(row["scenario_id"], selector),
        family=_text(row["family"], selector),
        mode=_text(row["mode"], selector),
        forecast_origin=_date_text(row["forecast_origin"], selector),
        replicate=_integer(row["replicate"], selector),
        horizon_days=_integer(row["horizon_days"], selector),
        schedule_mode=_text(row["schedule_mode"], selector),
        demand_basis=_text(row["demand_basis"], selector),
        stress_spec_id=_text(row["stress_spec_id"], selector),
        calibration_transport_valid=_boolean(row["calibration_transport_valid"], selector),
    )


def _forecast_point(row: dict[str, Any]) -> ForecastPoint:
    selector = ArtifactSelector.PHASE7_FORECASTS
    candidate, run_id = _provenance_row(row, selector)
    return ForecastPoint(
        date=_date_text(row["Date"], selector),
        horizon=_integer(row["horizon"], selector),
        raw_forecast=_number(row["raw_forecast"], selector),
        operational_forecast=_number(row["operational_forecast"], selector),
        forecast_available=_boolean(row["forecast_available"], selector),
        operational_forecast_available=_boolean(row["operational_forecast_available"], selector),
        candidate_id=candidate,
        model_selection_run_id=run_id,
    )


def _daily_interval(row: dict[str, Any]) -> DailyInterval:
    selector = ArtifactSelector.PHASE8_DAILY_INTERVALS
    return DailyInterval(
        date=_date_text(row["Date"], selector),
        horizon=_integer(row["horizon"], selector),
        interval_kind=_text(row["interval_kind"], selector),
        point_forecast=_number(row["point_forecast"], selector),
        lower=_number(row["lower"], selector),
        upper=_number(row["upper"], selector),
        width=_number(row["width"], selector),
        available=_boolean(row["available"], selector),
        unavailable_reason=_text(row["unavailable_reason"], selector, optional=True),
        units=_text(row["units"], selector),
        schedule_assumption_flag=_boolean(row["schedule_assumption_flag"], selector),
    )


def _cumulative_uncertainty(row: dict[str, Any]) -> CumulativeUncertainty:
    selector = ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY
    return CumulativeUncertainty(
        prefix_days=_integer(row["k"], selector),
        probability=_number(row["p"], selector),
        issued_prefix_complete=_boolean(row["issued_prefix_complete"], selector),
        unavailable_reason=_text(row["issued_prefix_unavailable_reason"], selector, optional=True),
        demand_value=_number(row["D_k"], selector),
        signed_error_quantile=_number(row["q_p_signed"], selector),
        upper_turnover_value=_number(row["U_k"], selector),
        safety_stock_value=_number(row["SafetyStock_k"], selector),
        target_value=_number(row["Target_k"], selector),
        units=_text(row["units"], selector),
        schedule_assumption_flag=_boolean(row["schedule_assumption_flag"], selector),
    )


def _model_comparison_row(row: dict[str, Any]) -> ModelComparisonRow:
    selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    return ModelComparisonRow(
        candidate_id=_text(row["candidate_id"], selector),
        population=_text(row["population"], selector),
        paired_with=_text(row["paired_with"], selector, optional=True),
        scope=_text(row["scope"], selector),
        validation_window=_text(row["validation_window"], selector, optional=True),
        horizon=_integer(row["horizon"], selector, optional=True),
        week_block_start_horizon=_integer(row["week_block_start_horizon"], selector, optional=True),
        week_block_end_horizon=_integer(row["week_block_end_horizon"], selector, optional=True),
        store_id=_integer(row["Store"], selector, optional=True),
        metric=_text(row["metric"], selector),
        value=_number(row["value"], selector),
        numerator=_number(row["numerator"], selector),
        denominator=_number(row["denominator"], selector),
        unavailable_reason=_text(row["unavailable_reason"], selector, optional=True),
        paired_mae_delta=_number(row["paired_mae_delta"], selector),
        paired_mae_change_fraction=_number(row["paired_mae_change_fraction"], selector),
    )


def _inventory_aggregate(row: dict[str, Any]) -> InventoryAggregate:
    selector = ArtifactSelector.PHASE10_COMPARISON
    return InventoryAggregate(
        case_id=_text(row["case_id"], selector),
        metric=_text(row["metric"], selector),
        requested_store_count=_integer(row["requested_store_count"], selector),
        baseline_standalone_store_count=_integer(row["baseline_standalone_store_count"], selector),
        forecast_standalone_store_count=_integer(row["forecast_standalone_store_count"], selector),
        matched_store_count=_integer(row["matched_store_count"], selector),
        baseline_numerator=_number(row["baseline_numerator"], selector),
        baseline_denominator=_number(row["baseline_denominator"], selector),
        forecast_numerator=_number(row["forecast_numerator"], selector),
        forecast_denominator=_number(row["forecast_denominator"], selector),
        baseline_value=_number(row["baseline_value"], selector),
        forecast_value=_number(row["forecast_value"], selector),
        forecast_minus_baseline=_number(row["forecast_minus_baseline"], selector),
        forecast_minus_baseline_relative=_number(row["forecast_minus_baseline_relative"], selector),
        relative_difference_null_reason=_text(
            row["relative_difference_null_reason"], selector, optional=True
        ),
        null_reason=_text(row["null_reason"], selector, optional=True),
        interpretation=_text(row["interpretation"], selector),
    )


def _policy_result(summary: dict[str, Any], target: dict[str, Any]) -> PolicyResult:
    selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    return PolicyResult(
        policy_id=_text(summary["policy_id"], selector),
        episode_status=_text(summary["episode_status"], selector),
        episode_complete=_boolean(summary["episode_complete"], selector),
        target_available=_boolean(summary["target_available"], selector),
        availability_reason=_text(summary["availability_reason"], selector, optional=True),
        valid_matched_comparison=_boolean(summary["valid_matched_comparison"], selector),
        simulated_holding_plus_shortfall_cost=_number(
            summary["SimulatedHoldingPlusShortfallCost"], selector
        ),
        demand_total=_number(summary["demand_total"], selector),
        fulfilled_total=_number(summary["fulfilled_total"], selector),
        unmet_total=_number(summary["unmet_total"], selector),
        target_value=_number(target["target_value"], ArtifactSelector.PHASE10_POLICY_TARGETS),
        synthetic=_boolean(target["synthetic"], ArtifactSelector.PHASE10_POLICY_TARGETS),
        calibration_transport_valid=_boolean(
            target["calibration_transport_valid"], ArtifactSelector.PHASE10_POLICY_TARGETS
        ),
        schedule_assumption=_text(
            target["schedule_assumption"], ArtifactSelector.PHASE10_POLICY_TARGETS
        ),
    )


def _policy_pairs(
    summary_table: ArtifactTable, target_table: ArtifactTable
) -> tuple[InventoryPolicyPair, ...]:
    summary_selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    target_selector = ArtifactSelector.PHASE10_POLICY_TARGETS
    summaries = {
        (row["case_id"], int(row["Store"]), row["policy_id"]): row
        for row in _ordered_records(summary_table.frame, sort_by=("case_id", "Store", "policy_id"))
    }
    targets = {
        (row["case_id"], int(row["Store"]), row["policy_id"]): row
        for row in _ordered_records(target_table.frame, sort_by=("case_id", "Store", "policy_id"))
    }
    if not summaries and not targets:
        return ()
    if set(summaries) != set(targets):
        raise ArtifactIntegrityError(summary_selector)
    pairs: list[InventoryPolicyPair] = []
    store_keys = sorted({(case_id, store_id) for case_id, store_id, _ in summaries})
    identity_fields = (
        "scenario_id",
        "forecast_origin",
        "family",
        "mode",
        "replicate",
        "sensitivity_variant",
    )
    for case_id, store_id in store_keys:
        store_policy_ids = {
            policy_id
            for selected_case, selected_store, policy_id in summaries
            if selected_case == case_id and selected_store == store_id
        }
        if store_policy_ids != set(POLICY_IDS):
            raise ArtifactIntegrityError(summary_selector)
        summary_pair = [summaries.get((case_id, store_id, policy)) for policy in POLICY_IDS]
        target_pair = [targets.get((case_id, store_id, policy)) for policy in POLICY_IDS]
        if any(row is None for row in (*summary_pair, *target_pair)):
            raise ArtifactIntegrityError(summary_selector)
        baseline_summary, forecast_summary = summary_pair
        baseline_target, forecast_target = target_pair
        assert baseline_summary is not None
        assert forecast_summary is not None
        assert baseline_target is not None
        assert forecast_target is not None
        if any(
            baseline_summary[field] != forecast_summary[field]
            or baseline_summary[field] != baseline_target[field]
            or baseline_summary[field] != forecast_target[field]
            for field in identity_fields
        ):
            raise ArtifactIntegrityError(summary_selector)
        for summary, target in zip(summary_pair, target_pair, strict=True):
            assert summary is not None and target is not None
            if not _same_nullable(
                summary["target_available"], target["target_available"]
            ) or not _same_nullable(summary["availability_reason"], target["availability_reason"]):
                raise ArtifactIntegrityError(target_selector)
        if (
            baseline_summary["valid_matched_comparison"]
            != forecast_summary["valid_matched_comparison"]
        ):
            raise ArtifactIntegrityError(summary_selector)
        baseline = _policy_result(baseline_summary, baseline_target)
        forecast = _policy_result(forecast_summary, forecast_target)
        complete = baseline.episode_complete and forecast.episode_complete
        targets_available = baseline.target_available and forecast.target_available
        comparable = (
            baseline.valid_matched_comparison
            and forecast.valid_matched_comparison
            and complete
            and targets_available
        )
        cost_difference = None
        unavailable_reason = None
        if comparable:
            if (
                baseline.simulated_holding_plus_shortfall_cost is None
                or forecast.simulated_holding_plus_shortfall_cost is None
            ):
                unavailable_reason = "cost_unavailable"
            else:
                cost_difference = (
                    forecast.simulated_holding_plus_shortfall_cost
                    - baseline.simulated_holding_plus_shortfall_cost
                )
                if not math.isfinite(cost_difference):
                    raise ArtifactSchemaError(summary_selector)
        elif not baseline.valid_matched_comparison:
            unavailable_reason = "not_valid_matched_comparison"
        elif not complete:
            unavailable_reason = "episode_incomplete"
        else:
            unavailable_reason = "target_unavailable"
        pairs.append(
            InventoryPolicyPair(
                case_id=str(case_id),
                store_id=store_id,
                comparable=comparable and cost_difference is not None,
                forecast_minus_baseline_cost=cost_difference,
                difference_unavailable_reason=unavailable_reason,
                baseline=baseline,
                forecast=forecast,
            )
        )
    return tuple(pairs)


def _sales_history_row(row: dict[str, Any]) -> SalesHistoryRow:
    selector = ArtifactSelector.HISTORICAL_SALES
    return SalesHistoryRow(
        store_id=_integer(row["Store"], selector),
        date=_date_text(row["Date"], selector),
        sales=_number(row["Sales"], selector),
        open=_number(row["Open"], selector),
    )


def _same_nullable(left: Any, right: Any) -> bool:
    left_null = _is_null(left)
    right_null = _is_null(right)
    return left_null and right_null or (not left_null and not right_null and left == right)


def _to_json_value(value: Any) -> Any:
    return json_safe(value)
