"""Synthetic monitoring workspace alongside the unchanged saved-service dashboard."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from rossmann_forecasting.monitoring import build_monitoring_summary, synthetic_monitoring_inputs


def monitoring_workspace() -> None:
    st.title("Descriptive synthetic monitoring")
    st.warning("CONTROLLED SYNTHETIC FIXTURE - NO ROSSMANN OR PRODUCTION OBSERVATIONS")
    st.caption(
        "Separate authored monitoring fixture; no LightGBM execution, fitted uncertainty "
        "or claim that these rows belong to the saved-service demonstration bundle."
    )
    key = "_course_synthetic_monitoring"
    if key not in st.session_state:
        forecasts, labels = synthetic_monitoring_inputs()
        st.session_state[key] = build_monitoring_summary(
            forecasts,
            labels,
            as_of="2015-07-03",
            reference_start="2015-06-06",
            reference_end="2015-06-19",
            current_start="2015-06-20",
            current_end="2015-07-03",
            generated_at=datetime.now(UTC).isoformat(),
        )
    summary = st.session_state[key]
    st.write(f"Evidence state: {summary['status']}")
    st.caption(
        f"Calculated {summary['generated_at']}; labels available as of {summary['as_of']}. "
        "This is evidence availability, not system health."
    )
    st.write(
        {
            "reference_window": summary["reference_window"],
            "current_window": summary["current_window"],
            "model_id": summary["model_id"],
        }
    )
    stores = [row["Store"] for row in summary["current"]["by_store"]]
    store = st.selectbox("Monitoring Store", ["Pooled", *stores])
    days = st.selectbox("Trailing calendar days", [1, 7, 14], index=1)
    current = (
        summary["current"]["pooled"]
        if store == "Pooled"
        else next(row for row in summary["current"]["by_store"] if row["Store"] == store)
    )
    fields = (
        "requested_forecast_keys",
        "observed_target_rows",
        "missing_actual_rows",
        "eligible_rows",
        "mae",
        "rmse",
        "mape",
        "mape_rows",
        "wape",
    )
    st.dataframe(
        pd.DataFrame([{"metric": name, "value": current[name]} for name in fields]),
        hide_index=True,
        width="stretch",
    )
    rows = []
    for window in summary["windows"]:
        if window["nominal_days"] != days:
            continue
        metrics = (
            window["pooled"]
            if store == "Pooled"
            else next(item for item in window["by_store"] if item["Store"] == store)
        )
        rows.append(
            {
                "window_end": window["end"],
                "mae": metrics["mae"],
                "eligible_pairs": metrics["eligible_rows"],
                "partial": window["partial"],
            }
        )
    st.line_chart(pd.DataFrame(rows).set_index("window_end")[["mae"]])
    st.caption(
        "MAE/RMSE: monetary turnover units; MAPE: percent on positive actuals; WAPE: ratio. "
        "Startup windows are partial; missing evidence is not zero."
    )
    st.dataframe(rows, hide_index=True, width="stretch")
    st.subheader("Descriptive feature comparison")
    st.dataframe(
        [
            {
                "feature": row["feature"],
                "state": row["state"],
                "reference_n": row["reference"]["available"],
                "current_n": row["current"]["available"],
                "median_difference": row["median_difference"],
            }
            for row in summary["feature_comparison"]
        ],
        hide_index=True,
        width="stretch",
    )
    st.info(summary["human_review"])
    for limitation in summary["limitations"]:
        st.caption(limitation)


def main() -> None:
    workspace = st.sidebar.radio(
        "Course workspace", ["Saved synthetic services", "Synthetic monitoring"]
    )
    if workspace == "Synthetic monitoring":
        monitoring_workspace()
    else:
        from demo_streamlit_app import main as saved_dashboard

        saved_dashboard()
