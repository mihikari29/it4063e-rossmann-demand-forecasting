"""Read-only Streamlit dashboard for saved development evidence."""

from __future__ import annotations

import threading
from datetime import date, timedelta
from typing import Protocol

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import streamlit as st

from rossmann_forecasting.app.contracts import (
    ForecastQuery,
    HistoryQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.dashboard_presenters import (
    HISTORY_DEFAULT_END,
    HISTORY_DEFAULT_START,
    SUPPORTED_CUMULATIVE_PROBABILITIES,
    SUPPORTED_FIT_ORIGINS,
    SUPPORTED_FORECAST_ORIGINS,
    artifact_provenance_records,
    catalog_provenance_records,
    cumulative_table_records,
    error_notice,
    forecast_chart_records,
    forecast_display_counts,
    forecast_identity,
    forecast_table_records,
    history_chart_records,
    history_source_records,
    interval_band_segments,
    interval_table_records,
    resource_status_records,
    validate_history_selection,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ApplicationServices,
    ForecastIssuanceView,
    ForecastUncertaintyView,
    SalesHistoryView,
)


class _DashboardServices(Protocol):
    def catalog(self) -> ApplicationCatalog: ...

    def sales_history(self, query: HistoryQuery) -> SalesHistoryView: ...

    def forecast_issuance(self, query: ForecastQuery) -> ForecastIssuanceView: ...

    def forecast_uncertainty(self, query: UncertaintyQuery) -> ForecastUncertaintyView: ...


_SERVICE_LOCK = threading.RLock()
_SCREENS = (
    "Overview & Evidence",
    "Historical Sales",
    "Forecast Explorer",
    "Model Comparison",
    "Inventory Comparison",
)
_PLACEHOLDER_COPY = {
    "Model Comparison": "Saved model comparisons are not available in this milestone.",
    "Inventory Comparison": "Saved inventory comparisons are not available in this milestone.",
}


def run_dashboard(services: _DashboardServices | None = None) -> None:
    """Render one screen and dispatch only its existing application service methods."""
    st.set_page_config(
        page_title="Rossmann Forecasting | Business Analytics",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    provider = ApplicationServices() if services is None else services
    st.sidebar.title("Rossmann Forecasting")
    screen = st.sidebar.radio("Navigate", _SCREENS, key="dashboard_screen")

    if screen == "Overview & Evidence":
        _render_overview(provider)
    elif screen == "Historical Sales":
        _render_history(provider)
    elif screen == "Forecast Explorer":
        _render_forecast_explorer(provider)
    else:
        _render_placeholder(screen)


def _render_overview(services: _DashboardServices) -> None:
    st.title("Overview & Evidence")
    st.write(
        "This Business Analytics project studies store-level monetary turnover and shows how a "
        "forecast can inform a separately simulated inventory-value comparison."
    )

    first, second = st.columns(2)
    with first:
        st.subheader("Analytical workflow")
        st.markdown(
            "**Observed Store × Date Sales** → **14-day forecast (H14)** → "
            "**empirical uncertainty** → **conditional synthetic inventory-value comparison**"
        )
        st.caption(
            "The dashboard presents saved development evidence. It does not train a model or "
            "run an inventory simulation."
        )
    with second:
        st.subheader("Frozen development forecast")
        st.markdown("`global_lightgbm_gbdt_regression_l1` · trial A · 180 rounds")
        st.caption(
            "This is the approved development selection identity; it is not a final-holdout result."
        )

    with st.expander("Interpretation and limits", expanded=True):
        st.markdown(
            "- **Sales is monetary turnover**, not physical demand, SKU quantity "
            "or observed stock.\n"
            "- Inventory costs and equivalent-unit interpretations are synthetic assumptions, not "
            "measured business savings or validated optimal policies.\n"
            "- Forecasts and empirical intervals use development evidence through 2015-07-03. "
            "The 2015-07-04–2015-07-31 holdout remains protected and unreleased."
        )

    st.subheader("Saved resource readiness")
    st.caption("Retry the saved-resource checks for this screen with the button below.")
    refresh_requested = st.button("Refresh resource status", key="refresh_resource_status")
    catalog = _load_catalog(services)
    if catalog is None:
        return

    try:
        records = resource_status_records(catalog.resources)
        provenance = catalog_provenance_records(catalog)
    except Exception:
        _render_internal_error()
        return

    if refresh_requested:
        st.caption("Resource status refreshed from the catalog service.")

    _render_catalog_state(
        "Scenario catalog", catalog.scenario_catalog_state, len(catalog.scenarios)
    )
    _render_catalog_state(
        "Inventory case catalog", catalog.inventory_case_state, len(catalog.inventory_case_ids)
    )

    if records:
        st.dataframe(records, hide_index=True, width="stretch")
    else:
        st.info("The catalog service returned no resource-readiness records.")

    if provenance:
        st.subheader("Verified catalog provenance")
        st.dataframe(provenance, hide_index=True, width="stretch")
    else:
        st.info("No catalog provenance was returned for a successfully read catalog.")


def _render_history(services: _DashboardServices) -> None:
    st.title("Historical Sales")
    st.caption(
        "Retrospective development history through 2015-07-03. This display is not an "
        "origin-time fitting input or source-wide EDA. Sales is monetary turnover."
    )
    catalog = _load_catalog(services)
    if catalog is None:
        return
    try:
        stores = _catalog_stores(catalog)
    except Exception:
        _render_internal_error()
        return
    if not stores:
        st.info("The catalog has no supported Store selection.")
        return

    with st.form("historical_sales_form"):
        store_id = st.selectbox("Store", stores, key="history_store")
        first, second = st.columns(2)
        with first:
            start_date = st.date_input(
                "Start date",
                value=HISTORY_DEFAULT_START,
                help="Allowed range: 2013-01-01 through 2015-07-03, at most 366 inclusive days.",
                key="history_start_date",
            )
        with second:
            end_date = st.date_input(
                "End date",
                value=HISTORY_DEFAULT_END,
                help="Allowed range: 2013-01-01 through 2015-07-03, at most 366 inclusive days.",
                key="history_end_date",
            )
        submitted = st.form_submit_button("Apply selection")

    if not submitted:
        st.info("Choose a Store and date range, then apply the selection to read saved history.")
        return

    validation_error = validate_history_selection(
        store_id, start_date, end_date, catalog.supported_store_ids
    )
    if validation_error is not None:
        st.error(validation_error)
        return

    query = HistoryQuery(store_id, start_date, end_date)
    try:
        with _SERVICE_LOCK:
            view = services.sales_history(query)
    except Exception as error:
        _render_error(error)
        return

    try:
        _render_history_result(view, query)
    except Exception:
        _render_internal_error()


def _render_history_result(view: SalesHistoryView, query: HistoryQuery) -> None:
    if not isinstance(view, SalesHistoryView) or not isinstance(view.rows, tuple):
        raise TypeError("Unexpected historical Sales view.")
    if type(view.state) is not str or view.state not in ("available", "empty"):
        raise ValueError("Unexpected historical Sales state.")
    if view.selector != "historical_sales" or view.through_date != "2015-07-03":
        raise ValueError("Unexpected historical Sales identity.")
    if (view.state == "empty") != (not view.rows):
        raise ValueError("Historical Sales state does not match its rows.")

    row_count = len(view.rows)
    chart_records: list[dict[str, object]] = []
    source_records: list[dict[str, object]] = []
    open_records: list[dict[str, object]] = []
    dates: list[date] = []
    sales_values: list[int | float | None] = []
    if view.rows:
        if any(row.store_id != query.store_id for row in view.rows):
            raise ValueError("Historical Sales rows do not match the selected Store.")
        chart_records = history_chart_records(view.rows, query.start_date, query.end_date)
        source_records = history_source_records(view.rows)
        if any(
            date.fromisoformat(row["Date"]) < query.start_date
            or date.fromisoformat(row["Date"]) > query.end_date
            for row in source_records
        ):
            raise ValueError("Historical Sales rows do not match the selected date range.")
        dates = [date.fromisoformat(record["Date"]) for record in chart_records]
        sales_values = [record["Sales"] for record in chart_records]
        open_records = [
            {"Date": row["Date"], "Source Open": row["Source Open"]} for row in source_records
        ]

    st.subheader(
        f"Applied history · Store {query.store_id} · "
        f"{query.start_date.isoformat()} through {query.end_date.isoformat()}"
    )
    st.caption(f"Observed source rows returned: {row_count}")
    if view.state == "empty" or not view.rows:
        st.info("No observed rows for this selection.")
        return

    figure, axis = plt.subplots(figsize=(11, 4))
    try:
        axis.plot(dates, sales_values, marker="o", linewidth=1.4, label="Observed Sales")
        axis.set_title("Observed monetary Sales by date")
        axis.set_xlabel("Date")
        axis.set_ylabel("Sales (monetary turnover value)")
        date_locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
        axis.xaxis.set_major_locator(date_locator)
        axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))
        axis.tick_params(axis="x", labelrotation=45)
        axis.legend(loc="best")
        figure.tight_layout()
        st.pyplot(figure, clear_figure=True, width="stretch")
    finally:
        plt.close(figure)

    st.subheader("Source Open status")
    st.caption("Source Open is shown separately. Unknown Open is not a closure.")
    st.dataframe(open_records, hide_index=True, width="stretch")

    st.subheader("Bounded source rows")
    st.dataframe(source_records, hide_index=True, width="stretch")


def _render_forecast_explorer(services: _DashboardServices) -> None:
    st.title("Forecast Explorer")
    st.caption(
        "Saved historical development forecasts only. No current-day forecast, model inference, "
        "accuracy calculation, or future source labels are used."
    )
    catalog = _load_catalog(services)
    if catalog is None:
        return
    try:
        stores = _catalog_stores(catalog)
        origins = tuple(
            origin
            for origin in SUPPORTED_FORECAST_ORIGINS
            if origin in catalog.phase7_forecast_origins
        )
    except Exception:
        _render_internal_error()
        return
    if not stores or not origins:
        st.info("The catalog has no supported Store and forecast-origin selection.")
        return

    with st.form("forecast_explorer_form"):
        first, second = st.columns(2)
        with first:
            store_id = st.selectbox("Store", stores, key="forecast_store")
        with second:
            origin_text = st.selectbox("Forecast origin", origins, key="forecast_origin")
        horizon_label = st.radio(
            "Displayed horizon",
            ("H14 · all 14 days", "H7 · first 7 days"),
            index=0,
            horizontal=True,
            key="forecast_display_horizon",
        )
        max_horizon = 7 if horizon_label.startswith("H7") else 14
        forecast_series_label = st.radio(
            "Forecast series",
            ("Raw forecast", "Saved operational forecast"),
            index=0,
            horizontal=True,
            key="forecast_series",
        )
        interval_kind_label = st.radio(
            "Daily uncertainty series",
            ("Raw", "Operational"),
            index=0,
            horizontal=True,
            key="uncertainty_series",
        )
        uncertainty_first, uncertainty_second = st.columns(2)
        with uncertainty_first:
            prefix_days = st.selectbox("Cumulative prefix k", tuple(range(1, 15)), index=13)
        with uncertainty_second:
            probability = st.selectbox(
                "Saved probability p",
                SUPPORTED_CUMULATIVE_PROBABILITIES,
                index=1,
                format_func=lambda value: f"{value:.2f}",
            )
        submitted = st.form_submit_button("Apply selection")

    st.caption(
        "Results identify the last applied Store and origin. Changes take effect after Apply; "
        "the saved H14 issuance is always requested, and H7 filters display only."
    )
    if not submitted:
        return

    if isinstance(store_id, bool) or not isinstance(store_id, int) or store_id not in stores:
        st.error("Choose a Store from the supported catalog.")
        return
    if origin_text not in origins:
        st.error("Choose one of the supported Phase 7 forecast origins.")
        return
    origin = date.fromisoformat(origin_text)
    query = ForecastQuery(store_id=store_id, forecast_origin=origin)
    try:
        with _SERVICE_LOCK:
            forecast_view = services.forecast_issuance(query)
    except Exception as error:
        _render_error(error)
        return

    try:
        _render_forecast_result(
            forecast_view,
            query,
            max_horizon=max_horizon,
            series="raw" if forecast_series_label == "Raw forecast" else "operational",
        )
    except Exception:
        _render_internal_error()
        return

    try:
        fit_id = _supported_fit(catalog, origin_text)
    except Exception:
        st.subheader("Forecast uncertainty")
        _render_internal_error()
        return
    if fit_id is None:
        st.subheader("Forecast uncertainty")
        st.info(
            f"No supported Phase 8 uncertainty fit is paired with {origin_text}. "
            "No uncertainty service request was sent."
        )
        _render_uncertainty_methodology()
        return

    uncertainty_query = UncertaintyQuery(
        store_id=store_id,
        forecast_origin=origin,
        fit_id=fit_id,
    )
    try:
        with _SERVICE_LOCK:
            uncertainty_view = services.forecast_uncertainty(uncertainty_query)
    except Exception as error:
        st.subheader("Forecast uncertainty")
        _render_error(error)
        return

    st.subheader("Forecast uncertainty")
    try:
        _render_uncertainty_result(
            uncertainty_view,
            query=uncertainty_query,
            fit_id=fit_id,
            interval_kind="raw" if interval_kind_label == "Raw" else "operational",
            max_horizon=max_horizon,
            prefix_days=prefix_days,
            probability=probability,
        )
    except Exception:
        _render_internal_error()


def _render_forecast_result(
    view: ForecastIssuanceView,
    query: ForecastQuery,
    *,
    max_horizon: int,
    series: str,
) -> None:
    if not isinstance(view, ForecastIssuanceView) or not isinstance(view.points, tuple):
        raise TypeError("Unexpected forecast issuance view.")
    if view.query != query:
        raise ValueError("The forecast result does not match the applied query.")
    if type(view.state) is not str or view.state not in ("available", "empty"):
        raise ValueError("Unexpected forecast issuance state.")
    if (view.state == "empty") != (not view.points):
        raise ValueError("Forecast issuance state does not match its rows.")

    target_start = query.forecast_origin + timedelta(days=1)
    target_end = query.forecast_origin + timedelta(days=14)
    identities = forecast_identity(view.points)
    horizons = [point.horizon for point in view.points]
    if len(set(horizons)) != len(horizons):
        raise ValueError("Duplicate forecast horizons were returned.")
    if any(
        point.date != (query.forecast_origin + timedelta(days=point.horizon)).isoformat()
        for point in view.points
    ):
        raise ValueError("Forecast dates do not match their saved horizons.")
    counts = forecast_display_counts(view.points, max_horizon)
    chart = forecast_chart_records(view.points, query.forecast_origin, max_horizon, series)
    table = forecast_table_records(view.points, max_horizon)
    provenance = artifact_provenance_records((view.provenance,))
    series_label = "Raw forecast" if series == "raw" else "Saved operational forecast"

    figure = None
    if view.points:
        figure, axis = plt.subplots(figsize=(10, 4))
        try:
            axis.plot(
                [row["Horizon"] for row in chart],
                [row["Forecast"] for row in chart],
                marker="o",
                linewidth=1.5,
                label=series_label,
            )
            axis.axvline(
                0,
                color="black",
                linestyle="--",
                linewidth=1,
                label=f"Forecast origin · {query.forecast_origin.isoformat()}",
            )
            axis.set_title(f"Saved {series_label.lower()} · H{max_horizon} display")
            axis.set_xlabel("Forecast horizon (calendar days after origin)")
            axis.set_ylabel("Forecast (monetary Sales value)")
            axis.set_xticks(tuple(range(0, max_horizon + 1)))
            axis.legend(loc="best")
            figure.tight_layout()
        except Exception:
            plt.close(figure)
            raise

    try:
        st.subheader(
            f"Applied forecast · Store {query.store_id} · "
            f"Origin {query.forecast_origin.isoformat()}"
        )
        st.write(
            f"Forecast targets: {target_start.isoformat()} through {target_end.isoformat()} "
            "(supported H14 path)."
        )
        st.caption(
            "Operational routing is a conditional historical replay using opening information; "
            "it is not a live known-future schedule."
        )

        if identities:
            st.markdown("**Frozen candidate identity**")
            st.dataframe(identities, hide_index=True, width="stretch")
        else:
            st.info("No saved forecast rows were returned for this Store and origin.")

        st.caption(
            f"Visible saved rows: {counts['rows']} · raw available: {counts['raw_available']} · "
            f"operational available: {counts['operational_available']} · "
            f"displayed horizons: 1–{max_horizon} of the H14 request."
        )

        if figure is not None:
            st.pyplot(figure, clear_figure=True, width="stretch")
        if table:
            st.subheader("Exact saved forecast rows")
            st.dataframe(table, hide_index=True, width="stretch")

        st.subheader("Forecast artifact provenance")
        st.dataframe(provenance, hide_index=True, width="stretch")
    finally:
        if figure is not None:
            plt.close(figure)


def _render_uncertainty_result(
    view: ForecastUncertaintyView,
    *,
    query: UncertaintyQuery,
    fit_id: str,
    interval_kind: str,
    max_horizon: int,
    prefix_days: int,
    probability: float,
) -> None:
    if not isinstance(view, ForecastUncertaintyView):
        raise TypeError("Unexpected forecast uncertainty view.")
    if view.query != query:
        raise ValueError("The uncertainty result does not match the applied query.")
    if type(view.state) is not str or view.state not in ("available", "empty"):
        raise ValueError("Unexpected forecast uncertainty state.")
    if not isinstance(view.daily_intervals, tuple) or not isinstance(
        view.cumulative_uncertainty, tuple
    ):
        raise TypeError("Unexpected forecast uncertainty rows.")
    if type(view.interpretation) is not str:
        raise TypeError("Unexpected uncertainty interpretation.")
    if (view.state == "empty") != (not view.daily_intervals and not view.cumulative_uncertainty):
        raise ValueError("Forecast uncertainty state does not match its rows.")

    daily_records = interval_table_records(view.daily_intervals, interval_kind, max_horizon)
    daily_keys = [(row.interval_kind, row.horizon) for row in view.daily_intervals]
    if len(set(daily_keys)) != len(daily_keys):
        raise ValueError("Duplicate daily uncertainty horizons were returned.")
    if any(
        row.date != (query.forecast_origin + timedelta(days=row.horizon)).isoformat()
        for row in view.daily_intervals
    ):
        raise ValueError("Daily interval dates do not match their saved horizons.")
    segments = interval_band_segments(view.daily_intervals, interval_kind, max_horizon)
    cumulative_records = cumulative_table_records(
        view.cumulative_uncertainty, prefix_days, probability
    )
    cumulative_keys = [(row.prefix_days, row.probability) for row in view.cumulative_uncertainty]
    if len(set(cumulative_keys)) != len(cumulative_keys):
        raise ValueError("Duplicate cumulative uncertainty rows were returned.")
    provenance = artifact_provenance_records(view.provenance)
    if len(provenance) != 2:
        raise ValueError("Both uncertainty provenance records are required.")

    incomplete_warning: str | None = None
    if cumulative_records:
        cumulative_row = cumulative_records[0]
        reason = cumulative_row["Unavailable reason"]
        if not cumulative_row["Prefix complete"]:
            incomplete_warning = (
                "This origin-anchored prefix is incomplete."
                if reason is None
                else f"This origin-anchored prefix is incomplete: {reason}."
            )
        elif any(
            cumulative_row[field] is None
            for field in ("D_k", "Signed q", "U_k", "Safety stock", "Target")
        ):
            incomplete_warning = (
                "The prefix is marked complete, but one or more saved numerical values are "
                "unavailable."
                if reason is None
                else (
                    "The prefix is marked complete, but saved numerical values are unavailable: "
                    f"{reason}."
                )
            )

    figure = None
    if daily_records:
        figure, axis = plt.subplots(figsize=(10, 4))
        try:
            _draw_interval_segments(axis, segments)
            if not segments:
                axis.text(
                    0.5,
                    0.5,
                    "No available saved interval bands in this subset.",
                    ha="center",
                    va="center",
                    transform=axis.transAxes,
                )
            axis.axvline(0, color="black", linestyle="--", linewidth=1, label="Forecast origin")
            axis.set_title("Saved empirical interval values")
            axis.set_xlabel("Forecast horizon (calendar days after origin)")
            axis.set_ylabel("Sales value (units as saved in table)")
            axis.legend(loc="best")
            figure.tight_layout()
        except Exception:
            plt.close(figure)
            raise

    try:
        st.write(
            f"Store {query.store_id} · Fit {fit_id} · Origin {query.forecast_origin.isoformat()}"
        )
        _render_uncertainty_methodology(fit_id)
        st.write(view.interpretation)
        st.markdown(f"**Daily {interval_kind} empirical intervals · H{max_horizon} display only**")
        if daily_records:
            if figure is not None:
                st.pyplot(figure, clear_figure=True, width="stretch")
            st.dataframe(daily_records, hide_index=True, width="stretch")
        else:
            st.info("No saved daily interval rows match this series and displayed horizon.")

        st.markdown(f"**Saved cumulative prefix · k={prefix_days} · p={probability:.2f}**")
        st.caption(
            "Cumulative prefixes retain their saved k and H14 issuance meaning; H7 filters daily "
            "display rows only."
        )
        if not cumulative_records:
            st.info("No saved cumulative row matches this prefix and probability.")
        else:
            st.dataframe(cumulative_records, hide_index=True, width="stretch")
            if incomplete_warning is not None:
                st.warning(incomplete_warning)

        st.subheader("Uncertainty artifact provenance")
        st.dataframe(provenance, hide_index=True, width="stretch")
    finally:
        if figure is not None:
            plt.close(figure)


def _render_uncertainty_methodology(fit_id: str | None = None) -> None:
    st.markdown(
        "**Methodology limits**\n"
        "- Empirical nominal intervals do not guarantee actual 95% coverage.\n"
        "- Unknown opening schedules affect operational interpretations.\n"
        "- Uncertainty uses the project's accepted monetary-value semantics, not SKU units.\n"
        "- Cumulative buffers are origin-anchored and do not describe later rolling reviews."
    )
    if fit_id == "A":
        st.caption("Fit A has documented unavailable horizons, including h2, h3 and h9.")
    elif fit_id == "B":
        st.caption(
            "Fit B has sparse weekday support and below-nominal development coverage; see "
            "[canonical Phase 8 evidence](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/blob/main/docs/PROGRESS.md)."
        )


def _catalog_stores(catalog: ApplicationCatalog) -> tuple[int, ...]:
    return tuple(
        store_id
        for store_id in catalog.supported_store_ids
        if isinstance(store_id, int) and not isinstance(store_id, bool) and 1 <= store_id <= 1115
    )


def _supported_fit(catalog: ApplicationCatalog, origin_text: str) -> str | None:
    allowed = {
        (fit_id, fit_origin)
        for fit_id, fit_origin in catalog.phase8_fits
        if fit_id in SUPPORTED_FIT_ORIGINS and SUPPORTED_FIT_ORIGINS[fit_id] == fit_origin
    }
    for fit_id, fit_origin in SUPPORTED_FIT_ORIGINS.items():
        if fit_origin == origin_text and (fit_id, fit_origin) in allowed:
            return fit_id
    return None


def _load_catalog(services: _DashboardServices) -> ApplicationCatalog | None:
    try:
        with _SERVICE_LOCK:
            catalog = services.catalog()
    except Exception as error:
        _render_error(error)
        return None
    if not isinstance(catalog, ApplicationCatalog):
        _render_internal_error()
        return None
    return catalog


def _draw_interval_segments(axis, segments: list[list[dict[str, object]]]) -> None:
    """Draw saved intervals without hiding singleton ranges or joining gaps."""
    interval_label = "Saved empirical interval"
    point_label = "Saved point estimate"
    for segment in segments:
        horizons = [row["Horizon"] for row in segment]
        lower = [row["Lower"] for row in segment]
        upper = [row["Upper"] for row in segment]
        points = [row["Point estimate"] for row in segment]
        if len(segment) >= 2:
            axis.fill_between(
                horizons,
                lower,
                upper,
                color="C0",
                alpha=0.22,
                label=interval_label,
            )
        elif len(segment) == 1:
            horizon = horizons[0]
            axis.vlines(
                horizon,
                lower[0],
                upper[0],
                color="C0",
                linewidth=2.2,
                label=interval_label,
            )
            axis.plot(
                (horizon, horizon),
                (lower[0], upper[0]),
                color="C0",
                linestyle="none",
                marker="_",
                markersize=9,
                label="_nolegend_",
            )
        interval_label = "_nolegend_"
        if any(point is not None for point in points):
            axis.plot(
                horizons,
                points,
                color="C1",
                marker="o",
                linewidth=1.4,
                label=point_label,
            )
            point_label = "_nolegend_"


def _render_catalog_state(label: str, state: str, count: int) -> None:
    if state == "available":
        st.success(f"{label}: available ({count} entries)")
    elif state == "empty":
        st.info(f"{label}: verified but empty")
    elif state == "unavailable":
        st.warning(f"{label}: unavailable in this checkout")
    else:
        st.info(f"{label}: service-reported state `{state}`")


def _render_error(error: Exception) -> None:
    notice = error_notice(error)
    if notice.code == "artifact_unavailable":
        st.warning(notice.message)
    else:
        st.error(notice.message)
    st.caption(f"Error code: `{notice.code}`")
    if notice.selector is not None:
        st.caption(f"Logical resource: `{notice.selector}`")


def _render_internal_error() -> None:
    st.error("The request could not be completed. Error details are hidden.")
    st.caption("Error code: `internal_error`")


def _render_placeholder(screen: str) -> None:
    st.title(screen)
    st.info(_PLACEHOLDER_COPY[screen])
    st.caption("This screen does not query application services in M2.")
