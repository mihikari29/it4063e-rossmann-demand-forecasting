"""Typed, read-only analytical views over a verified controlled-synthetic release."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from rossmann_forecasting.app.contracts import (
    ForecastQuery,
    HistoryQuery,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.demo_provider import (
    DemoInvalidRequestError,
    DemoProfile,
    DemoProvider,
    SyntheticProvenance,
)

type Number = int | float
type OptionalNumber = Number | None


class DemoViewState(StrEnum):
    AVAILABLE = "available"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class DemoFitPairing:
    fit_id: str
    forecast_origin: str


@dataclass(frozen=True, slots=True)
class DemoScenarioEntry:
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
class DemoViewAvailability:
    view_id: str
    state: str
    record_count: int
    unavailable_reason: str | None
    availability_summary: str


@dataclass(frozen=True, slots=True)
class DemoSourceDeclaration:
    kind: str
    rossmann_data_included: bool
    source_files_included: bool
    external_data_sources: tuple[str, ...]
    redistribution_rights: str
    model_runs_included: bool
    model_execution: str


@dataclass(frozen=True, slots=True)
class DemoCatalog:
    bundle_ready: bool
    supported_store_ids: tuple[int, ...]
    forecast_origins: tuple[str, ...]
    fit_pairings: tuple[DemoFitPairing, ...]
    comparison_candidate_ids: tuple[str, ...]
    inventory_case_ids: tuple[str, ...]
    scenario_catalog: tuple[DemoScenarioEntry, ...]
    views: tuple[DemoViewAvailability, ...]
    health_route_semantics: str
    sales_unit: str
    inventory_cost_unit: str
    source_declaration: DemoSourceDeclaration
    limitations: tuple[str, ...]
    provenance: SyntheticProvenance


@dataclass(frozen=True, slots=True)
class DemoSalesHistoryRow:
    store_id: int
    date: str
    sales_value: OptionalNumber
    synthetic_open: bool | None
    observation_state: str


@dataclass(frozen=True, slots=True)
class DemoSalesHistory:
    state: DemoViewState
    query: HistoryQuery
    rows: tuple[DemoSalesHistoryRow, ...]
    provenance: SyntheticProvenance


@dataclass(frozen=True, slots=True)
class DemoForecastPoint:
    date: str
    horizon: int
    raw_forecast_value: OptionalNumber
    raw_forecast_available: bool
    synthetic_open_eligibility: str
    operational_forecast_value: OptionalNumber
    operational_forecast_available: bool


@dataclass(frozen=True, slots=True)
class DemoForecastIssuance:
    state: DemoViewState
    query: ForecastQuery
    points: tuple[DemoForecastPoint, ...]
    trajectory_id: str
    model_execution: str
    provenance: SyntheticProvenance


@dataclass(frozen=True, slots=True)
class DemoDailyInterval:
    date: str
    horizon: int
    interval_kind: str
    point_forecast: OptionalNumber
    lower: OptionalNumber
    upper: OptionalNumber
    width: OptionalNumber
    available: bool
    unavailable_reason: str | None
    units: str
    schedule_assumption_flag: bool


@dataclass(frozen=True, slots=True)
class DemoCumulativeUncertainty:
    prefix_days: int
    probability: Number
    issued_prefix_complete: bool
    unavailable_reason: str | None
    demand_value: OptionalNumber
    signed_error_quantile: OptionalNumber
    upper_turnover_value: OptionalNumber
    safety_stock_value: OptionalNumber
    target_value: OptionalNumber
    units: str
    schedule_assumption_flag: bool


@dataclass(frozen=True, slots=True)
class DemoForecastUncertainty:
    state: str
    query: UncertaintyQuery
    daily_intervals: tuple[DemoDailyInterval, ...]
    cumulative_uncertainty: tuple[DemoCumulativeUncertainty, ...]
    interpretation: str
    unavailable_reason: str | None
    provenance: SyntheticProvenance


@dataclass(frozen=True, slots=True)
class DemoCandidateLabel:
    candidate_id: str
    label: str
    generation: str
    model_execution: str


@dataclass(frozen=True, slots=True)
class DemoMetricDefinition:
    metric: str
    definition: str


@dataclass(frozen=True, slots=True)
class DemoModelComparisonRow:
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
    value: OptionalNumber
    numerator: OptionalNumber
    denominator: OptionalNumber
    unavailable_reason: str | None
    paired_mae_delta: OptionalNumber
    paired_mae_change_fraction: OptionalNumber


@dataclass(frozen=True, slots=True)
class DemoModelComparison:
    state: DemoViewState
    query: ModelComparisonQuery
    population: str
    validation_window: str
    candidate_labels: tuple[DemoCandidateLabel, ...]
    metric_definitions: tuple[DemoMetricDefinition, ...]
    development_model_selection_claim: bool
    rows: tuple[DemoModelComparisonRow, ...]
    provenance: SyntheticProvenance


@dataclass(frozen=True, slots=True)
class DemoInventoryMeasurement:
    metric: str
    numerator: OptionalNumber
    denominator: OptionalNumber
    value: OptionalNumber
    unavailable_reason: str | None


@dataclass(frozen=True, slots=True)
class DemoInventoryPolicy:
    policy_id: str
    episode_status: str
    episode_complete: bool
    target_available: bool
    target_unavailability_reason: str | None
    availability_reason: str | None
    valid_matched_comparison: bool
    simulated_holding_plus_shortfall_cost: OptionalNumber
    demand_total: OptionalNumber
    fulfilled_total: OptionalNumber
    unmet_total: OptionalNumber
    target_value: OptionalNumber
    synthetic: bool
    calibration_transport_valid: bool
    schedule_assumption: str
    measurements: tuple[DemoInventoryMeasurement, ...]


@dataclass(frozen=True, slots=True)
class DemoInventoryPolicyPair:
    case_id: str
    store_id: int
    comparable: bool
    forecast_minus_baseline_cost: OptionalNumber
    difference_unavailable_reason: str | None
    baseline: DemoInventoryPolicy
    forecast: DemoInventoryPolicy


@dataclass(frozen=True, slots=True)
class DemoInventoryAggregate:
    case_id: str
    metric: str
    requested_store_count: int
    baseline_standalone_store_count: int
    forecast_standalone_store_count: int
    matched_store_count: int
    baseline_numerator: OptionalNumber
    baseline_denominator: OptionalNumber
    forecast_numerator: OptionalNumber
    forecast_denominator: OptionalNumber
    baseline_value: OptionalNumber
    forecast_value: OptionalNumber
    forecast_minus_baseline: OptionalNumber
    forecast_minus_baseline_relative: OptionalNumber
    relative_difference_null_reason: str | None
    null_reason: str | None
    interpretation: str


@dataclass(frozen=True, slots=True)
class DemoInventoryComparison:
    state: DemoViewState
    case_id: str
    store_id: int | None
    aggregate_scope: str
    case_level_comparisons: tuple[DemoInventoryAggregate, ...]
    policy_pairs: tuple[DemoInventoryPolicyPair, ...]
    provenance: SyntheticProvenance


def _number(value: Any) -> OptionalNumber:
    if value is None or type(value) in (int, float):
        return value
    raise DemoInvalidRequestError()


def _matches_filters(row: Any, query: ModelComparisonQuery) -> bool:
    return all(
        getattr(query, field) is None or row[field] == getattr(query, field)
        for field in (
            "candidate_id",
            "population",
            "scope",
            "validation_window",
            "horizon",
            "store_id",
            "metric",
        )
    )


_VERIFIED_SERVICES_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class DemoServices:
    """Six bounded read-only services over one explicit, verified synthetic profile."""

    _provider: DemoProvider

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise TypeError("Construct verified services with DemoServices.open().")

    @classmethod
    def _from_verified(cls, *, _token: object, provider: DemoProvider) -> DemoServices:
        if _token is not _VERIFIED_SERVICES_TOKEN or not isinstance(provider, DemoProvider):
            raise TypeError("Construct verified services with DemoServices.open().")
        services = object.__new__(cls)
        object.__setattr__(services, "_provider", provider)
        return services

    @classmethod
    def open(
        cls,
        *,
        profile: DemoProfile,
        expected_manifest_sha256: str,
        repository_root: Path | None = None,
    ) -> DemoServices:
        """Construct services only after a fixed release passes pinned validation."""
        provider = DemoProvider.open(
            profile=profile,
            expected_manifest_sha256=expected_manifest_sha256,
            repository_root=repository_root,
        )
        return cls._from_verified(_token=_VERIFIED_SERVICES_TOKEN, provider=provider)

    @property
    def profile(self) -> DemoProfile:
        return self._provider.profile

    def catalog(self) -> DemoCatalog:
        bundle = self._provider.bundle
        catalog_data = bundle["catalog"]
        population = bundle["populations"]
        comparison = bundle["comparison_panel"]
        resources = {row["view_id"]: row for row in catalog_data["resource_readiness"]}
        views = tuple(
            DemoViewAvailability(
                view_id=view_id,
                state=resources[view_id]["state"],
                record_count=resources[view_id]["record_count"],
                unavailable_reason=resources[view_id]["unavailable_reason"],
                availability_summary=catalog_data["view_availability"][view_id],
            )
            for view_id in (
                "catalog",
                "sales_history",
                "forecast_issuance",
                "forecast_uncertainty",
                "model_comparison",
                "inventory_comparison",
            )
        )
        scenarios = tuple(
            DemoScenarioEntry(
                scenario_id=item["scenario_id"],
                family=item["family"],
                mode=item["mode"],
                forecast_origin=item["forecast_origin"],
                replicate=item["replicate"],
                horizon_days=item["horizon_days"],
                schedule_mode=item["schedule_mode"],
                demand_basis=item["demand_basis"],
                stress_spec_id=item["stress_spec_id"],
                calibration_transport_valid=item["calibration_transport_valid"],
            )
            for item in catalog_data["scenario_catalog"]
        )
        declaration = bundle["source_declaration"]
        return DemoCatalog(
            bundle_ready=True,
            supported_store_ids=tuple(population["store_ids"]),
            forecast_origins=tuple(population["forecast_origins"]),
            fit_pairings=tuple(DemoFitPairing(**pair) for pair in population["fit_pairings"]),
            comparison_candidate_ids=tuple(
                item["candidate_id"] for item in comparison["candidate_labels"]
            ),
            inventory_case_ids=tuple(catalog_data["inventory_case_ids"]),
            scenario_catalog=scenarios,
            views=views,
            health_route_semantics=catalog_data["health_route_semantics"],
            sales_unit=bundle["sales_unit"],
            inventory_cost_unit=bundle["inventory_cost_unit"],
            source_declaration=DemoSourceDeclaration(
                kind=declaration["kind"],
                rossmann_data_included=declaration["rossmann_data_included"],
                source_files_included=declaration["source_files_included"],
                external_data_sources=tuple(declaration["external_data_sources"]),
                redistribution_rights=declaration["redistribution_rights"],
                model_runs_included=declaration["model_runs_included"],
                model_execution=declaration["model_execution"],
            ),
            limitations=self._provider.limitations,
            provenance=self._provider.provenance("catalog", 1),
        )

    def sales_history(self, query: HistoryQuery) -> DemoSalesHistory:
        allowlist = self._provider.query_allowlist["sales_history"]
        if not isinstance(query, HistoryQuery):
            raise DemoInvalidRequestError()
        if (
            type(query.store_id) is not int
            or query.store_id not in allowlist["store_ids"]
            or type(query.start_date) is not date
            or type(query.end_date) is not date
        ):
            raise DemoInvalidRequestError()
        start = query.start_date.isoformat()
        end = query.end_date.isoformat()
        if (
            start < allowlist["minimum_date"]
            or end > allowlist["maximum_date"]
            or end < start
            or (query.end_date - query.start_date).days + 1 > allowlist["maximum_calendar_days"]
        ):
            raise DemoInvalidRequestError()
        rows = tuple(
            DemoSalesHistoryRow(
                store_id=row["store_id"],
                date=row["date"],
                sales_value=_number(row["sales_value"]),
                synthetic_open=row["synthetic_open"],
                observation_state=row["observation_state"],
            )
            for row in self._provider.history_by_store[query.store_id]
            if start <= row["date"] <= end
        )
        return DemoSalesHistory(
            state=DemoViewState.AVAILABLE if rows else DemoViewState.EMPTY,
            query=query,
            rows=rows,
            provenance=self._provider.provenance("sales_history", len(rows)),
        )

    def forecast_issuance(self, query: ForecastQuery) -> DemoForecastIssuance:
        allowlist = self._provider.query_allowlist["forecast_issuance"]
        if (
            not isinstance(query, ForecastQuery)
            or type(query.store_id) is not int
            or query.store_id not in allowlist["store_ids"]
            or type(query.forecast_origin) is not date
            or query.forecast_origin.isoformat() not in allowlist["origins"]
        ):
            raise DemoInvalidRequestError()
        rows = self._provider.forecasts_by_query.get(
            (query.store_id, query.forecast_origin.isoformat()), ()
        )
        points = tuple(
            DemoForecastPoint(
                date=row["date"],
                horizon=row["horizon"],
                raw_forecast_value=_number(row["raw_forecast_value"]),
                raw_forecast_available=row["raw_forecast_available"],
                synthetic_open_eligibility=row["synthetic_open_eligibility"],
                operational_forecast_value=_number(row["operational_forecast_value"]),
                operational_forecast_available=row["operational_forecast_available"],
            )
            for row in rows
        )
        trajectory_id = rows[0]["trajectory_label"] if rows else ""
        return DemoForecastIssuance(
            state=DemoViewState.AVAILABLE if points else DemoViewState.EMPTY,
            query=query,
            points=points,
            trajectory_id=trajectory_id,
            model_execution="none",
            provenance=self._provider.provenance("forecast_issuance", len(points)),
        )

    def forecast_uncertainty(self, query: UncertaintyQuery) -> DemoForecastUncertainty:
        allowlist = self._provider.query_allowlist["forecast_uncertainty"]
        if (
            not isinstance(query, UncertaintyQuery)
            or type(query.store_id) is not int
            or query.store_id not in allowlist["store_ids"]
            or type(query.forecast_origin) is not date
            or type(query.fit_id) is not str
            or not any(
                pair["fit_id"] == query.fit_id
                and pair["forecast_origin"] == query.forecast_origin.isoformat()
                for pair in allowlist["fit_pairings"]
            )
        ):
            raise DemoInvalidRequestError()
        view = self._provider.uncertainty_by_query.get(
            (query.store_id, query.forecast_origin.isoformat(), query.fit_id)
        )
        if view is None:
            raise DemoInvalidRequestError()
        daily = tuple(
            DemoDailyInterval(
                date=row["date"],
                horizon=row["horizon"],
                interval_kind=row["interval_kind"],
                point_forecast=_number(row["point_forecast"]),
                lower=_number(row["lower"]),
                upper=_number(row["upper"]),
                width=_number(row["width"]),
                available=row["available"],
                unavailable_reason=row["unavailable_reason"],
                units=row["units"],
                schedule_assumption_flag=row["schedule_assumption_flag"],
            )
            for row in view["daily_intervals"]
        )
        cumulative = tuple(
            DemoCumulativeUncertainty(
                prefix_days=row["prefix_days"],
                probability=_number(row["probability"]),
                issued_prefix_complete=row["issued_prefix_complete"],
                unavailable_reason=row["unavailable_reason"],
                demand_value=_number(row["demand_value"]),
                signed_error_quantile=_number(row["signed_error_quantile"]),
                upper_turnover_value=_number(row["upper_turnover_value"]),
                safety_stock_value=_number(row["safety_stock_value"]),
                target_value=_number(row["target_value"]),
                units=row["units"],
                schedule_assumption_flag=row["schedule_assumption_flag"],
            )
            for row in view["cumulative_uncertainty"]
        )
        selected = len(daily) + len(cumulative)
        return DemoForecastUncertainty(
            state=view["state"],
            query=query,
            daily_intervals=daily,
            cumulative_uncertainty=cumulative,
            interpretation=view["interpretation"],
            unavailable_reason=view["unavailable_reason"],
            provenance=self._provider.provenance("forecast_uncertainty", selected),
        )

    def model_comparison(self, query: ModelComparisonQuery) -> DemoModelComparison:
        allowlist = self._provider.query_allowlist["model_comparison"]
        if not isinstance(query, ModelComparisonQuery):
            raise DemoInvalidRequestError()
        string_allowlists = {
            "candidate_id": allowlist["candidate_ids"],
            "population": (allowlist["population"],),
            "scope": allowlist["scopes"],
            "validation_window": (allowlist["validation_window"],),
            "metric": allowlist["metrics"],
        }
        for field, values in string_allowlists.items():
            value = getattr(query, field)
            if value is not None and (type(value) is not str or value not in values):
                raise DemoInvalidRequestError()
        populations = self._provider.bundle["populations"]
        if (
            query.horizon is not None
            and (type(query.horizon) is not int or query.horizon not in populations["horizons"])
        ) or (
            query.store_id is not None
            and (type(query.store_id) is not int or query.store_id not in populations["store_ids"])
        ):
            raise DemoInvalidRequestError()
        if type(query.limit) is not int or not 1 <= query.limit <= allowlist["maximum_rows"]:
            raise DemoInvalidRequestError()

        filtered = tuple(
            row for row in self._provider.comparison_rows if _matches_filters(row, query)
        )
        if len(filtered) > query.limit:
            raise DemoInvalidRequestError()
        rows = tuple(
            DemoModelComparisonRow(
                candidate_id=row["candidate_id"],
                population=row["population"],
                paired_with=row["paired_with"],
                scope=row["scope"],
                validation_window=row["validation_window"],
                horizon=row["horizon"],
                week_block_start_horizon=row["week_block_start_horizon"],
                week_block_end_horizon=row["week_block_end_horizon"],
                store_id=row["store_id"],
                metric=row["metric"],
                value=_number(row["value"]),
                numerator=_number(row["numerator"]),
                denominator=_number(row["denominator"]),
                unavailable_reason=row["unavailable_reason"],
                paired_mae_delta=_number(row["paired_mae_delta"]),
                paired_mae_change_fraction=_number(row["paired_mae_change_fraction"]),
            )
            for row in filtered
        )
        panel = self._provider.bundle["comparison_panel"]
        return DemoModelComparison(
            state=DemoViewState.AVAILABLE if rows else DemoViewState.EMPTY,
            query=query,
            population=panel["population"],
            validation_window=panel["validation_window"],
            candidate_labels=tuple(
                DemoCandidateLabel(
                    candidate_id=item["candidate_id"],
                    label=item["label"],
                    generation=item["generation"],
                    model_execution=item["model_execution"],
                )
                for item in panel["candidate_labels"]
            ),
            metric_definitions=tuple(
                DemoMetricDefinition(metric=name, definition=definition)
                for name, definition in panel["metric_definitions"].items()
                if name != "development_model_selection_claim"
            ),
            development_model_selection_claim=panel["metric_definitions"][
                "development_model_selection_claim"
            ],
            rows=rows,
            provenance=self._provider.provenance("model_comparison", len(rows)),
        )

    def inventory_comparison(self, query: InventoryComparisonQuery) -> DemoInventoryComparison:
        allowlist = self._provider.query_allowlist["inventory_comparison"]
        if (
            not isinstance(query, InventoryComparisonQuery)
            or type(query.case_id) is not str
            or query.case_id not in allowlist["case_ids"]
            or (
                query.store_id is not None
                and (
                    type(query.store_id) is not int or query.store_id not in allowlist["store_ids"]
                )
            )
        ):
            raise DemoInvalidRequestError()
        view = self._provider.inventory_by_case.get(query.case_id)
        if view is None:
            raise DemoInvalidRequestError()
        pairs = tuple(
            DemoInventoryPolicyPair(
                case_id=query.case_id,
                store_id=row["store_id"],
                comparable=row["comparable"],
                forecast_minus_baseline_cost=_number(row["forecast_minus_baseline_cost"]),
                difference_unavailable_reason=row["difference_unavailable_reason"],
                baseline=self._inventory_policy(row["baseline"]),
                forecast=self._inventory_policy(row["forecast"]),
            )
            for row in view["policy_pairs"]
            if query.store_id is None or row["store_id"] == query.store_id
        )
        aggregates = tuple(
            DemoInventoryAggregate(
                case_id=query.case_id,
                metric=row["metric"],
                requested_store_count=row["requested_store_count"],
                baseline_standalone_store_count=row["baseline_standalone_store_count"],
                forecast_standalone_store_count=row["forecast_standalone_store_count"],
                matched_store_count=row["matched_store_count"],
                baseline_numerator=_number(row["baseline_numerator"]),
                baseline_denominator=_number(row["baseline_denominator"]),
                forecast_numerator=_number(row["forecast_numerator"]),
                forecast_denominator=_number(row["forecast_denominator"]),
                baseline_value=_number(row["baseline_value"]),
                forecast_value=_number(row["forecast_value"]),
                forecast_minus_baseline=_number(row["forecast_minus_baseline"]),
                forecast_minus_baseline_relative=_number(row["forecast_minus_baseline_relative"]),
                relative_difference_null_reason=row["relative_difference_null_reason"],
                null_reason=row["null_reason"],
                interpretation=row["interpretation"],
            )
            for row in view["case_level_comparisons"]
        )
        selected = len(pairs) + len(aggregates)
        return DemoInventoryComparison(
            state=DemoViewState.AVAILABLE if pairs else DemoViewState.EMPTY,
            case_id=query.case_id,
            store_id=query.store_id,
            aggregate_scope="all_stores_in_case",
            case_level_comparisons=aggregates,
            policy_pairs=pairs,
            provenance=self._provider.provenance("inventory_comparison", selected),
        )

    @staticmethod
    def _inventory_policy(row: Any) -> DemoInventoryPolicy:
        return DemoInventoryPolicy(
            policy_id=row["policy_id"],
            episode_status=row["episode_status"],
            episode_complete=row["episode_complete"],
            target_available=row["target_available"],
            target_unavailability_reason=row["target_unavailability_reason"],
            availability_reason=row["availability_reason"],
            valid_matched_comparison=row["valid_matched_comparison"],
            simulated_holding_plus_shortfall_cost=_number(
                row["simulated_holding_plus_shortfall_cost"]
            ),
            demand_total=_number(row["demand_total"]),
            fulfilled_total=_number(row["fulfilled_total"]),
            unmet_total=_number(row["unmet_total"]),
            target_value=_number(row["target_value"]),
            synthetic=row["synthetic"],
            calibration_transport_valid=row["calibration_transport_valid"],
            schedule_assumption=row["schedule_assumption"],
            measurements=tuple(
                DemoInventoryMeasurement(
                    metric=item["metric"],
                    numerator=_number(item["numerator"]),
                    denominator=_number(item["denominator"]),
                    value=_number(item["value"]),
                    unavailable_reason=item["unavailable_reason"],
                )
                for item in row["measurements"]
            ),
        )
