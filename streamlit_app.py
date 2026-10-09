"""Streamlit entrypoint for the read-only dashboard."""

from rossmann_forecasting.app.dashboard import run_dashboard

if __name__ == "__main__":
    run_dashboard()
