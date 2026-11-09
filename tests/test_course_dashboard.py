"""The separate workspace displays calculated synthetic evidence rather than system health."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_monitoring_workspace_store_calendar_controls_and_provenance():
    app = AppTest.from_file(Path.cwd() / "course_demo_app.py", default_timeout=30).run()
    app.sidebar.radio[0].set_value("Synthetic monitoring").run()
    assert not app.exception
    assert "NO ROSSMANN OR PRODUCTION" in app.warning[0].value
    assert any("Evidence state: DESCRIPTIVE_ONLY" in item.value for item in app.markdown)
    pooled = app.dataframe[0].value
    assert pooled.loc[pooled["metric"].eq("eligible_rows"), "value"].iloc[0] == 36
    app.selectbox[0].set_value(101).run()
    app.selectbox[1].set_value(14).run()
    assert not app.exception
    selected = app.dataframe[0].value
    assert selected.loc[selected["metric"].eq("eligible_rows"), "value"].iloc[0] == 12
    assert app.dataframe[1].value["partial"].iloc[0]
    assert not any("Healthy" in item.value for item in app.markdown)
