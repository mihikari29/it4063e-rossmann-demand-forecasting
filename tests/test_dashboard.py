"""Fixture-backed AppTest coverage for the M1 Streamlit shell and overview."""

from __future__ import annotations

from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest
from test_app_artifacts import FixtureStore, _artifact_path

from rossmann_forecasting.app.artifacts import _ArtifactReader
from rossmann_forecasting.app.contracts import ArtifactSelector
from rossmann_forecasting.app.services import ApplicationServices


def _dashboard_test_app(services: object) -> None:
    from rossmann_forecasting.app.dashboard import run_dashboard

    run_dashboard(services=services)


def _app(services: object) -> AppTest:
    return AppTest.from_function(_dashboard_test_app, kwargs={"services": services}).run()


def _visible_text(app: AppTest) -> str:
    element_names = (
        "title",
        "header",
        "subheader",
        "markdown",
        "caption",
        "text",
        "info",
        "warning",
        "error",
        "success",
    )
    values = []
    for name in element_names:
        for element in getattr(app, name, ()):
            if hasattr(element, "value"):
                values.append(str(element.value))
    for element in app.dataframe:
        if hasattr(element, "value"):
            value = element.value
            values.append(
                value.to_string(index=False) if hasattr(value, "to_string") else str(value)
            )
    return "\n".join(values)


class _CatalogSpy:
    def __init__(self, services: ApplicationServices) -> None:
        self.services = services
        self.catalog_calls = 0
        self.model_queries = []
        self.inventory_queries = []

    def catalog(self):
        self.catalog_calls += 1
        return self.services.catalog()

    def model_comparison(self, query):
        self.model_queries.append(query)
        return self.services.model_comparison(query)

    def inventory_comparison(self, query):
        self.inventory_queries.append(query)
        return self.services.inventory_comparison(query)


class _ReaderSpy:
    def __init__(self, reader: object) -> None:
        self.reader = reader
        self.read_selectors: list[ArtifactSelector] = []

    def read(self, selector: ArtifactSelector):
        self.read_selectors.append(selector)
        return self.reader.read(selector)

    def inspect_readiness(self):
        return self.reader.inspect_readiness()


@pytest.fixture
def fixture_store(tmp_path) -> FixtureStore:
    return FixtureStore(tmp_path)


def test_overview_starts_with_fixture_catalog_and_displays_readiness(fixture_store) -> None:
    reader = _ReaderSpy(fixture_store.reader())
    spy = _CatalogSpy(ApplicationServices(reader))

    app = _app(spy)
    visible = _visible_text(app)

    assert not app.exception
    assert spy.catalog_calls == 1
    assert "Overview & Evidence" in visible
    assert "14-day forecast (H14)" in visible
    assert "global_lightgbm_gbdt_regression_l1" in visible
    assert "monetary turnover" in visible
    assert "synthetic assumptions" in visible
    assert "Saved resource readiness" in visible
    assert "Verified catalog provenance" in visible
    assert "output_verified" in visible
    assert reader.read_selectors == [
        ArtifactSelector.PHASE9_SCENARIO_CATALOG,
        ArtifactSelector.PHASE10_COMPARISON,
    ]


def test_missing_catalog_artifacts_render_unavailable_without_crashing(fixture_store) -> None:
    for selector in (
        ArtifactSelector.PHASE9_SCENARIO_CATALOG,
        ArtifactSelector.PHASE10_COMPARISON,
    ):
        _artifact_path(fixture_store, selector).unlink()

    app = _app(ApplicationServices(fixture_store.reader()))
    visible = _visible_text(app)

    assert not app.exception
    assert "Scenario catalog: unavailable in this checkout" in visible
    assert "Inventory case catalog: unavailable in this checkout" in visible
    assert "unavailable" in visible
    assert "Verified catalog provenance" not in visible
    assert "ArtifactReadError" not in visible


def test_refresh_resource_status_recovers_after_fixture_resource_is_restored(fixture_store) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    path = _artifact_path(fixture_store, selector)
    original_bytes = path.read_bytes()
    path.unlink()
    reader = _ReaderSpy(fixture_store.reader())
    spy = _CatalogSpy(ApplicationServices(reader))

    app = _app(spy)
    unavailable = _visible_text(app)

    assert not app.exception
    assert spy.catalog_calls == 1
    assert "Scenario catalog: unavailable in this checkout" in unavailable
    assert app.button[0].label == "Refresh resource status"

    path.write_bytes(original_bytes)
    app.button[0].click().run()
    recovered = _visible_text(app)

    assert not app.exception
    assert spy.catalog_calls == 2
    assert "Scenario catalog: available (1 entries)" in recovered
    assert "Verified catalog provenance" in recovered
    assert "Resource status refreshed from the catalog service." in recovered
    assert (
        reader.read_selectors
        == [
            ArtifactSelector.PHASE9_SCENARIO_CATALOG,
            ArtifactSelector.PHASE10_COMPARISON,
        ]
        * 2
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("resources", (object(),)),
        ("scenario_provenance", object()),
    ],
)
def test_invalid_catalog_presentation_value_is_sanitized_and_tables_are_hidden(
    fixture_store, field: str, value: object
) -> None:
    catalog = ApplicationServices(fixture_store.reader()).catalog()
    private_path = "C:\\private\\rossmann\\manifest.json"

    class InvalidPresentationService:
        def catalog(self):
            return replace(catalog, **{field: value})

    app = _app(InvalidPresentationService())
    visible = _visible_text(app)

    assert not app.exception
    assert "internal_error" in visible
    assert "Error details are hidden" in visible
    assert private_path not in visible
    assert not app.dataframe
    assert "Scenario catalog: available" not in visible
    assert "Verified catalog provenance" not in visible


def test_clean_checkout_keeps_static_overview_and_reports_resources_unavailable(tmp_path) -> None:
    services = ApplicationServices(_ArtifactReader(root=tmp_path))

    app = _app(services)
    visible = _visible_text(app)

    assert not app.exception
    assert "Overview & Evidence" in visible
    assert "global_lightgbm_gbdt_regression_l1" in visible
    assert "Saved resource readiness" in visible
    assert "unavailable" in visible
    assert "No catalog provenance was returned" in visible


def test_corrupt_catalog_has_integrity_state_and_never_displays_a_path(fixture_store) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    path = _artifact_path(fixture_store, selector)
    path.write_bytes(path.read_bytes() + b"corruption")
    private_path = str(path.resolve())

    app = _app(ApplicationServices(fixture_store.reader()))
    visible = _visible_text(app)

    assert not app.exception
    assert "artifact_integrity_error" in visible
    assert "failed its integrity check" in visible
    assert private_path not in visible
    assert "Verified catalog provenance" not in visible


def test_empty_catalog_is_distinct_from_missing_resources(fixture_store) -> None:
    catalog = ApplicationServices(fixture_store.reader()).catalog()

    class EmptyCatalog:
        def catalog(self):
            return replace(
                catalog,
                scenario_catalog_state="empty",
                scenarios=(),
                inventory_case_state="empty",
                inventory_case_ids=(),
                scenario_provenance=None,
                inventory_case_provenance=None,
            )

    app = _app(EmptyCatalog())
    visible = _visible_text(app)

    assert "Scenario catalog: verified but empty" in visible
    assert "Inventory case catalog: verified but empty" in visible
    assert "unavailable in this checkout" not in visible


def test_m3_screens_wait_for_apply_before_comparison_queries(fixture_store) -> None:
    spy = _CatalogSpy(ApplicationServices(fixture_store.reader()))
    app = _app(spy)
    assert spy.catalog_calls == 1

    for screen in (
        "Historical Sales",
        "Forecast Explorer",
        "Model Comparison",
        "Inventory Comparison",
    ):
        app.sidebar.radio[0].set_value(screen).run()
        assert not app.exception
        assert screen in _visible_text(app)
        if screen in (
            "Historical Sales",
            "Forecast Explorer",
            "Model Comparison",
            "Inventory Comparison",
        ):
            assert any(button.label == "Apply selection" for button in app.button)
    assert spy.catalog_calls == 4
    assert not spy.model_queries
    assert not spy.inventory_queries


def test_unexpected_service_error_is_sanitized() -> None:
    private_path = "C:\\private\\rossmann\\manifest.json"

    class FailingService:
        def catalog(self):
            raise RuntimeError(f"reader failed at {private_path}")

    app = _app(FailingService())
    visible = _visible_text(app)

    assert not app.exception
    assert "internal_error" in visible
    assert "Error details are hidden" in visible
    assert private_path not in visible
