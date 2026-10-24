"""Read-only Streamlit presentation for the verified controlled-synthetic services."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import streamlit as st

from rossmann_forecasting.app.contracts import (
    ForecastQuery,
    HistoryQuery,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.demo_provider import (
    DemoInvalidRequestError,
    DemoProviderError,
    DemoReleaseIntegrityError,
    DemoReleaseUnavailableError,
    SyntheticProvenance,
)
from rossmann_forecasting.app.demo_services import DemoCatalog, DemoServices

EVIDENCE_LABEL = "CONTROLLED SYNTHETIC DEMONSTRATION — NOT OBSERVED ROSSMANN DATA"
_HISTORY_MIN = date(2015, 5, 9)
_HISTORY_MAX = date(2015, 7, 3)
_MAX_HISTORY_DAYS = 56
_MAX_COMPARISON_ROWS = 500
_SCREEN_NAMES = (
    "Overview & Evidence",
    "Historical Sales",
    "Forecast Explorer and Uncertainty",
    "Model Comparison",
    "Inventory Comparison",
)


def _records(rows: Any) -> list[dict[str, Any]]:
    return [asdict(row) for row in rows]


def _show_provenance(provenance: SyntheticProvenance) -> None:
    st.caption(
        "Synthetic source identity; this hash does not establish empirical validity "
        "or release rights."
    )
    st.dataframe([asdict(provenance)], hide_index=True, width="stretch")


def _show_banner(limitation: str, provenance: SyntheticProvenance | None = None) -> None:
    st.warning(EVIDENCE_LABEL)
    st.caption(limitation)
    if provenance is None:
        st.caption("No verified release identity is available in this state.")
    else:
        st.caption(
            f"Verified release_id={provenance.release_id}; "
            f"evidence_kind={provenance.evidence_kind}; "
            f"schema_version={provenance.schema_version}; "
            f"source_kind={provenance.source_kind}; "
            f"manifest_sha256={provenance.manifest_sha256}"
        )


def render_unavailable(message: str) -> None:
    """Render a sanitized startup failure without exposing configuration or host details."""
    st.title("Controlled Synthetic Demonstration")
    _show_banner(
        "No analytical values are displayed because a pinned synthetic release is unavailable."
    )
    st.error(message)


def _provider_error_message(error: Exception) -> str:
    if isinstance(error, DemoInvalidRequestError):
        return "This synthetic query is outside the supported release options."
    if isinstance(error, DemoReleaseUnavailableError):
        return (
            "The pinned synthetic release is unavailable. Check the local setup and release files."
        )
    if isinstance(error, DemoReleaseIntegrityError):
        return "The synthetic release did not pass its configured integrity check."
    if isinstance(error, DemoProviderError):
        return "The synthetic release cannot provide this view."
    return "This synthetic view is temporarily unavailable. No details were exposed."


def _safe_query(call: Any) -> Any | None:
    try:
        return call()
    except (DemoInvalidRequestError, DemoProviderError) as error:
        st.warning(_provider_error_message(error))
    except Exception:
        st.error("This synthetic view is temporarily unavailable. No details were exposed.")
    return None


def _view_availability(catalog: DemoCatalog, view_id: str) -> bool:
    entry = next((item for item in catalog.views if item.view_id == view_id), None)
    if entry is None:
        st.warning("This analytical view is not listed in the verified catalog.")
        return False
    if entry.state != "available":
        st.info(f"This saved view is {entry.state}. {entry.availability_summary}")
        return False
    return True


def _show_overview(services: DemoServices, catalog: DemoCatalog) -> None:
    st.header("Overview & Evidence")
    _show_banner(
        "Saved fixture values illustrate a forecasting and decision-support workflow; "
        "no model is run here.",
        catalog.provenance,
    )
    st.subheader("Verified bundle and view availability")
    st.dataframe(
        [
            {
                "bundle_ready": catalog.bundle_ready,
                "page_render_state": "This page is rendering.",
            }
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Bundle readiness describes the pinned data package. Each view below has its own "
        "availability. This page does not report API or process health."
    )
    st.dataframe(_records(catalog.views), hide_index=True, width="stretch")

    st.subheader("Fixed synthetic identities")
    st.dataframe(
        [
            {"item": "Release ID", "saved identity": catalog.provenance.release_id},
            {"item": "Schema version", "saved identity": catalog.provenance.schema_version},
            {"item": "Evidence kind", "saved identity": catalog.provenance.evidence_kind},
            {"item": "Stores", "saved identity": ", ".join(map(str, catalog.supported_store_ids))},
            {"item": "Forecast origins", "saved identity": ", ".join(catalog.forecast_origins)},
            {
                "item": "Fit pairings",
                "saved identity": "; ".join(
                    f"{pair.fit_id} / {pair.forecast_origin}" for pair in catalog.fit_pairings
                ),
            },
            {
                "item": "Comparison paths",
                "saved identity": ", ".join(catalog.comparison_candidate_ids),
            },
            {"item": "Inventory cases", "saved identity": ", ".join(catalog.inventory_case_ids)},
            {"item": "Sales unit", "saved identity": catalog.sales_unit},
            {"item": "Inventory-cost proxy unit", "saved identity": catalog.inventory_cost_unit},
        ],
        hide_index=True,
        width="stretch",
    )
    st.subheader("Source declaration and limitations")
    st.dataframe([asdict(catalog.source_declaration)], hide_index=True, width="stretch")
    st.write(list(catalog.limitations))
    _show_provenance(catalog.provenance)


def _open_label(value: bool | None) -> str:
    if value is None:
        return "Unknown"
    return "Open" if value else "Closed"


def _history_chart(rows: tuple[Any, ...], start: date, end: date) -> None:
    by_date = {date.fromisoformat(row.date): row.sales_value for row in rows}
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    values = [by_date.get(day) for day in days]
    chart_values = [float(value) if value is not None else float("nan") for value in values]
    figure, axis = plt.subplots(figsize=(10, 3.5))
    axis.plot(days, chart_values, color="#2f6f8f", marker="o", markersize=3)
    axis.set_title("Saved synthetic Sales values (monetary turnover)")
    axis.set_xlabel("Date")
    axis.set_ylabel("Sales")
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    figure.autofmt_xdate()
    figure.tight_layout()
    try:
        st.pyplot(figure, clear_figure=False)
    finally:
        plt.close(figure)


def _show_history(services: DemoServices, catalog: DemoCatalog) -> None:
    st.header("Historical Sales")
    _show_banner(
        "These are saved synthetic monetary Sales values, not observed Rossmann history "
        "or a forecast.",
        catalog.provenance,
    )
    if not _view_availability(catalog, "sales_history"):
        return
    store_id = st.selectbox("Store", catalog.supported_store_ids, key="demo_history_store")
    start = st.date_input(
        "Start date",
        value=_HISTORY_MIN,
        min_value=_HISTORY_MIN,
        max_value=_HISTORY_MAX,
        key="demo_history_start",
    )
    end = st.date_input(
        "End date",
        value=_HISTORY_MAX,
        min_value=_HISTORY_MIN,
        max_value=_HISTORY_MAX,
        key="demo_history_end",
    )
    if start > end:
        st.info("Choose a start date on or before the end date.")
        return
    if (end - start).days + 1 > _MAX_HISTORY_DAYS:
        st.info("Select no more than 56 inclusive calendar days.")
        return
    result = _safe_query(lambda: services.sales_history(HistoryQuery(store_id, start, end)))
    if result is None:
        return
    st.caption(
        f"Store {store_id} · {start.isoformat()} through {end.isoformat()} · "
        f"{result.state.value} · {len(result.rows)} saved rows"
    )
    if not result.rows:
        st.info("No saved synthetic rows match this date selection.")
    else:
        _history_chart(result.rows, start, end)
        st.subheader("Saved synthetic Sales values")
        records = []
        for row in result.rows:
            record = asdict(row)
            record["synthetic_open"] = _open_label(row.synthetic_open)
            record["sales_value_display"] = (
                row.sales_value if row.sales_value is not None else "Null (saved value unavailable)"
            )
            records.append(record)
        st.dataframe(records, hide_index=True, width="stretch")
    _show_provenance(result.provenance)


def _forecast_chart(points: tuple[Any, ...]) -> None:
    dates = [date.fromisoformat(point.date) for point in points]
    raw = [
        float(point.raw_forecast_value)
        if point.raw_forecast_available and point.raw_forecast_value is not None
        else float("nan")
        for point in points
    ]
    operational = [
        float(point.operational_forecast_value)
        if point.operational_forecast_available and point.operational_forecast_value is not None
        else float("nan")
        for point in points
    ]
    figure, axis = plt.subplots(figsize=(10, 3.5))
    axis.plot(dates, raw, label="Raw forecast", marker="o", markersize=3, color="#2f6f8f")
    axis.plot(
        dates, operational, label="Operational forecast", marker="o", markersize=3, color="#cc7a29"
    )
    axis.set_title("Saved forecast paths")
    axis.set_xlabel("Target date")
    axis.set_ylabel("Sales")
    axis.legend()
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    figure.autofmt_xdate()
    figure.tight_layout()
    try:
        st.pyplot(figure, clear_figure=False)
    finally:
        plt.close(figure)


def _show_forecast(services: DemoServices, catalog: DemoCatalog) -> None:
    st.header("Forecast Explorer and Uncertainty")
    _show_banner(
        "Saved synthetic paths and uncertainty summaries are displayed without executing "
        "or calibrating a model.",
        catalog.provenance,
    )
    if not _view_availability(catalog, "forecast_issuance"):
        return
    store_id = st.selectbox("Store", catalog.supported_store_ids, key="demo_forecast_store")
    origin_text = st.selectbox(
        "Forecast origin", catalog.forecast_origins, key="demo_forecast_origin"
    )
    horizons = st.multiselect(
        "Display horizons",
        tuple(range(1, 15)),
        default=list(range(1, 15)),
        key="demo_forecast_horizons",
    )
    issuance = _safe_query(
        lambda: services.forecast_issuance(ForecastQuery(store_id, date.fromisoformat(origin_text)))
    )
    if issuance is not None:
        st.caption(
            f"Forecast origin: {origin_text} · trajectory: {issuance.trajectory_id} · "
            f"model_execution = {issuance.model_execution}"
        )
        selected_points = tuple(point for point in issuance.points if point.horizon in horizons)
        if not selected_points:
            st.info("Select one or more horizons to display saved forecast values.")
        else:
            _forecast_chart(selected_points)
            rows = []
            for point in selected_points:
                row = asdict(point)
                row["trajectory_id"] = issuance.trajectory_id
                row["model_execution"] = issuance.model_execution
                row["raw_forecast_display"] = (
                    point.raw_forecast_value
                    if point.raw_forecast_available
                    else "Unavailable (saved null)"
                )
                row["operational_forecast_display"] = (
                    point.operational_forecast_value
                    if point.operational_forecast_available
                    else "Unavailable (saved null)"
                )
                rows.append(row)
            st.dataframe(rows, hide_index=True, width="stretch")
        _show_provenance(issuance.provenance)

    st.subheader("Saved uncertainty")
    pairing = next(
        (item for item in catalog.fit_pairings if item.forecast_origin == origin_text), None
    )
    if pairing is None:
        st.info("No approved synthetic uncertainty view exists for this forecast origin.")
        return
    if not _view_availability(catalog, "forecast_uncertainty"):
        return
    uncertainty = _safe_query(
        lambda: services.forecast_uncertainty(
            UncertaintyQuery(store_id, date.fromisoformat(origin_text), pairing.fit_id)
        )
    )
    if uncertainty is None:
        return
    st.caption(f"Fit pairing: {pairing.fit_id} / {origin_text} · {uncertainty.interpretation}")
    if uncertainty.unavailable_reason:
        st.info(
            f"Saved uncertainty state: {uncertainty.state}. "
            f"Reason: {uncertainty.unavailable_reason}"
        )
    st.write("Daily intervals (saved values; monetary units retained)")
    st.dataframe(_records(uncertainty.daily_intervals), hide_index=True, width="stretch")
    st.write("Cumulative uncertainty (saved probabilities 0.90, 0.95 and 0.98)")
    st.dataframe(_records(uncertainty.cumulative_uncertainty), hide_index=True, width="stretch")
    _show_provenance(uncertainty.provenance)


def _optional_select(label: str, values: tuple[Any, ...], key: str) -> Any | None:
    options = ("All", *values)
    selected = st.selectbox(label, options, key=key)
    return None if selected == "All" else selected


def _show_comparison(services: DemoServices, catalog: DemoCatalog) -> None:
    st.header("Model Comparison")
    _show_banner(
        "This is a fixed synthetic comparison panel; it does not establish real-world "
        "model superiority or select a winner.",
        catalog.provenance,
    )
    if not _view_availability(catalog, "model_comparison"):
        return
    baseline = _safe_query(
        lambda: services.model_comparison(ModelComparisonQuery(limit=_MAX_COMPARISON_ROWS))
    )
    if baseline is None:
        return
    labels = {item.candidate_id: item.label for item in baseline.candidate_labels}
    candidate_ids = tuple(item.candidate_id for item in baseline.candidate_labels)
    populations = tuple(sorted({row.population for row in baseline.rows}))
    scopes = tuple(sorted({row.scope for row in baseline.rows}))
    windows = tuple(
        sorted(
            {row.validation_window for row in baseline.rows if row.validation_window is not None}
        )
    )
    metrics = tuple(sorted({row.metric for row in baseline.rows}))
    candidate = _optional_select("Candidate", candidate_ids, "demo_comparison_candidate")
    population = _optional_select("Population", populations, "demo_comparison_population")
    scope = _optional_select("Scope", scopes, "demo_comparison_scope")
    window = _optional_select("Validation window", windows, "demo_comparison_window")
    metric = _optional_select("Metric", metrics, "demo_comparison_metric")
    horizon = None
    store_id = None
    if scope == "horizon":
        available_horizons = tuple(
            sorted({row.horizon for row in baseline.rows if row.horizon is not None})
        )
        horizon = _optional_select("Horizon", available_horizons, "demo_comparison_horizon")
    if scope == "store":
        available_stores = tuple(
            sorted({row.store_id for row in baseline.rows if row.store_id is not None})
        )
        store_id = _optional_select("Store", available_stores, "demo_comparison_store")
    limit = st.number_input(
        "Maximum result rows",
        min_value=1,
        max_value=_MAX_COMPARISON_ROWS,
        value=200,
        step=1,
        key="demo_comparison_limit",
    )
    result = _safe_query(
        lambda: services.model_comparison(
            ModelComparisonQuery(
                candidate_id=candidate,
                population=population,
                scope=scope,
                validation_window=window,
                horizon=horizon,
                store_id=store_id,
                metric=metric,
                limit=int(limit),
            )
        )
    )
    if result is None:
        return
    st.caption(
        f"Population: {result.population} · validation window: "
        f"{result.validation_window} · {len(result.rows)} saved rows"
    )
    if not result.rows:
        st.info("No saved comparison rows match this valid filter combination.")
    else:
        rows = []
        for row in result.rows:
            record = asdict(row)
            record["candidate_label"] = labels.get(row.candidate_id, row.candidate_id)
            rows.append(record)
        st.dataframe(rows, hide_index=True, width="stretch")
    with st.expander("Saved metric definitions"):
        st.dataframe(_records(result.metric_definitions), hide_index=True, width="stretch")
    _show_provenance(result.provenance)


def _policy_rows(pairs: tuple[Any, ...]) -> list[dict[str, Any]]:
    rows = []
    for pair in pairs:
        rows.append(
            {
                "case_id": pair.case_id,
                "store_id": pair.store_id,
                "comparable": pair.comparable,
                "forecast_minus_baseline_cost": pair.forecast_minus_baseline_cost,
                "difference_unavailable_reason": pair.difference_unavailable_reason,
                "baseline_policy_id": pair.baseline.policy_id,
                "baseline_episode_status": pair.baseline.episode_status,
                "baseline_cost_proxy": pair.baseline.simulated_holding_plus_shortfall_cost,
                "baseline_target_value": pair.baseline.target_value,
                "baseline_target_available": pair.baseline.target_available,
                "baseline_availability_reason": pair.baseline.availability_reason,
                "forecast_policy_id": pair.forecast.policy_id,
                "forecast_episode_status": pair.forecast.episode_status,
                "forecast_cost_proxy": pair.forecast.simulated_holding_plus_shortfall_cost,
                "forecast_target_value": pair.forecast.target_value,
                "forecast_target_available": pair.forecast.target_available,
                "forecast_availability_reason": pair.forecast.availability_reason,
                "demand_total": pair.forecast.demand_total,
                "fulfilled_total": pair.forecast.fulfilled_total,
                "unmet_total": pair.forecast.unmet_total,
            }
        )
    return rows


def _show_inventory(services: DemoServices, catalog: DemoCatalog) -> None:
    st.header("Inventory Comparison")
    _show_banner(
        "Inventory figures are synthetic inventory-cost proxy examples, not observed "
        "stock or documented savings.",
        catalog.provenance,
    )
    if not _view_availability(catalog, "inventory_comparison"):
        return
    case_id = st.selectbox("Synthetic case", catalog.inventory_case_ids, key="demo_inventory_case")
    store_id = _optional_select(
        "Store-level detail", catalog.supported_store_ids, "demo_inventory_store"
    )
    result = _safe_query(
        lambda: services.inventory_comparison(InventoryComparisonQuery(case_id, store_id))
    )
    if result is None:
        return
    st.caption(f"Aggregate scope: {result.aggregate_scope}")
    st.caption(
        "Units: demand, fulfilled, unmet, available target and inventory-state values use "
        "synthetic_retail_equivalent_turnover_value (illustrative monetary-equivalent values; "
        "no currency is implied). Baseline and forecast cost proxies and signed "
        "forecast-minus-baseline cost differences use synthetic_cost_proxy_units (not realized "
        "costs or documented savings). Value-fill rates, stockout-rate proxies, receipt-cycle "
        "service rates and relative differences are dimensionless ratios. Store/population "
        "counts and population-count denominators remain counts."
    )
    st.subheader("All Stores in the selected synthetic case")
    st.dataframe(_records(result.case_level_comparisons), hide_index=True, width="stretch")
    st.subheader(
        "Selected Store policy detail" if store_id is not None else "All Store policy detail"
    )
    if not result.policy_pairs:
        st.info("No policy-pair detail is available for this selection.")
    else:
        st.dataframe(_policy_rows(result.policy_pairs), hide_index=True, width="stretch")
    st.caption(
        "Signed differences and unavailable reasons are shown as saved. Case-wide "
        "aggregates retain their full saved population under Store filtering."
    )
    _show_provenance(result.provenance)


def run_demo_dashboard(services: DemoServices) -> None:
    """Render the five-screen dashboard using an already verified service instance."""
    if not isinstance(services, DemoServices):
        render_unavailable("A verified controlled-synthetic service instance is required.")
        return
    try:
        catalog = services.catalog()
    except (DemoInvalidRequestError, DemoProviderError) as error:
        render_unavailable(_provider_error_message(error))
        return
    except Exception:
        render_unavailable(
            "The verified synthetic catalog is temporarily unavailable. No details were exposed."
        )
        return

    st.title("Controlled Synthetic Demonstration")
    page = st.sidebar.radio(
        "Synthetic demonstration screen", _SCREEN_NAMES, key="demo_dashboard_screen"
    )
    if page == "Overview & Evidence":
        _show_overview(services, catalog)
    elif page == "Historical Sales":
        _show_history(services, catalog)
    elif page == "Forecast Explorer and Uncertainty":
        _show_forecast(services, catalog)
    elif page == "Model Comparison":
        _show_comparison(services, catalog)
    else:
        _show_inventory(services, catalog)
