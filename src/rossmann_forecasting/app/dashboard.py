"""Read-only Streamlit shell and M1 project overview."""

from __future__ import annotations

import threading
from typing import Protocol

import streamlit as st

from rossmann_forecasting.app.contracts import ArtifactReadError
from rossmann_forecasting.app.dashboard_presenters import (
    catalog_provenance_records,
    error_notice,
    resource_status_records,
)
from rossmann_forecasting.app.services import ApplicationCatalog, ApplicationServices


class _CatalogServices(Protocol):
    def catalog(self) -> ApplicationCatalog: ...


_SERVICE_LOCK = threading.RLock()
_SCREENS = (
    "Overview & Evidence",
    "Historical Sales",
    "Forecast Explorer",
    "Model Comparison",
    "Inventory Comparison",
)
_PLACEHOLDER_COPY = {
    "Historical Sales": "Historical Sales views are not available in this milestone.",
    "Forecast Explorer": "Forecast and uncertainty views are not available in this milestone.",
    "Model Comparison": "Saved model comparisons are not available in this milestone.",
    "Inventory Comparison": "Saved inventory comparisons are not available in this milestone.",
}


def run_dashboard(services: _CatalogServices | None = None) -> None:
    """Render the active screen only; injection keeps UI tests isolated from local files."""
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
    else:
        _render_placeholder(screen)


def _render_overview(services: _CatalogServices) -> None:
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
    st.caption("Use this control to retry the saved-resource checks for the current screen load.")
    refresh_requested = st.button("Refresh resource status", key="refresh_resource_status")
    try:
        with _SERVICE_LOCK:
            catalog = services.catalog()
    except ArtifactReadError as error:
        _render_error(error)
        return
    except Exception as error:  # UI boundary: keep unexpected paths/details out of the browser.
        _render_error(error)
        return

    try:
        records = resource_status_records(catalog.resources)
        provenance = catalog_provenance_records(catalog)
    except Exception:  # Keep untrusted DTO or conversion details out of the browser.
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
    st.error("The saved-resource check could not be completed. Error details are hidden.")
    st.caption("Error code: `internal_error`")


def _render_placeholder(screen: str) -> None:
    st.title(screen)
    st.info(_PLACEHOLDER_COPY[screen])
    st.caption("This screen does not query application services in M1.")
