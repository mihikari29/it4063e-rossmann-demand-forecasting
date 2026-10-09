"""M2 presenter, Streamlit, and isolated-reader integration coverage."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from streamlit.testing.v1 import AppTest
from test_app_artifacts import FixtureStore, _artifact_path

from rossmann_forecasting.app.artifacts import _ArtifactReader
from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactSelector,
    ArtifactUnavailableError,
    ForecastQuery,
    HistoryQuery,
    UnavailableReason,
    UncertaintyQuery,
)
from rossmann_forecasting.app.dashboard_presenters import (
    SUPPORTED_CUMULATIVE_PROBABILITIES,
    SUPPORTED_FIT_ORIGINS,
    SUPPORTED_FORECAST_ORIGINS,
    validate_history_selection,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ApplicationServices,
    ArtifactProvenance,
    CumulativeUncertainty,
    DailyInterval,
    ForecastIssuanceView,
    ForecastPoint,
    ForecastUncertaintyView,
    SalesHistoryRow,
    SalesHistoryView,
)


def _dashboard_test_app(services: object) -> None:
    from rossmann_forecasting.app.dashboard import run_dashboard

    run_dashboard(services=services)


def _app(services: object, screen: str = "Forecast Explorer") -> AppTest:
    app = AppTest.from_function(_dashboard_test_app, kwargs={"services": services}).run()
    if screen != "Overview & Evidence":
        app.sidebar.radio[0].set_value(screen).run()
    return app


def _visible_text(app: AppTest) -> str:
    names = (
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
    for name in names:
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


def _provenance(selector: str, phase: str) -> ArtifactProvenance:
    return ArtifactProvenance(
        selector=selector,
        phase=phase,
        run_id=f"{phase}-fixture-run",
        manifest_sha256=f"{phase}-manifest-sha",
        output_sha256=f"{phase}-output-sha",
        selected_rows=2,
        manifest_rows=20,
    )


def _catalog(
    *,
    stores: tuple[int, ...] = (1, 2, 1115),
    origins: tuple[str, ...] = SUPPORTED_FORECAST_ORIGINS,
    fits: tuple[tuple[str, str], ...] = (("A", "2015-06-05"), ("B", "2015-06-19")),
) -> ApplicationCatalog:
    return ApplicationCatalog(
        phases=("phase7", "phase8", "phase9", "phase10"),
        selectors=("phase7_forecasts", "phase8_daily_intervals", "historical_sales"),
        supported_store_ids=stores,
        phase7_forecast_origins=origins,
        phase8_fits=fits,
        scenario_catalog_state="empty",
        scenarios=(),
        inventory_case_state="empty",
        inventory_case_ids=(),
        resources=(),
        scenario_provenance=None,
        inventory_case_provenance=None,
    )


def _point(
    query: ForecastQuery,
    horizon: int,
    *,
    raw: float | None,
    operational: float | None,
    raw_available: bool,
    operational_available: bool,
) -> ForecastPoint:
    return ForecastPoint(
        date=(query.forecast_origin + timedelta(days=horizon)).isoformat(),
        horizon=horizon,
        raw_forecast=raw,
        operational_forecast=operational,
        forecast_available=raw_available,
        operational_forecast_available=operational_available,
        candidate_id="global_lightgbm_gbdt_regression_l1",
        model_selection_run_id="frozen-selection-run",
    )


def _forecast_view(query: ForecastQuery) -> ForecastIssuanceView:
    points = (
        _point(
            query,
            1,
            raw=0.0,
            operational=None,
            raw_available=True,
            operational_available=False,
        ),
        _point(
            query,
            3,
            raw=None,
            operational=33.25,
            raw_available=False,
            operational_available=True,
        ),
        _point(
            query,
            8,
            raw=80.5,
            operational=80.5,
            raw_available=True,
            operational_available=True,
        ),
    )
    return ForecastIssuanceView(
        state="available",
        query=query,
        points=points,
        provenance=_provenance("phase7_forecasts", "phase7"),
    )


def _daily(
    query: UncertaintyQuery,
    horizon: int,
    *,
    kind: str = "raw",
    point: float | None = 15.0,
    lower: float | None = 10.0,
    upper: float | None = 20.0,
    available: bool = True,
    reason: str | None = None,
) -> DailyInterval:
    return DailyInterval(
        date=(query.forecast_origin + timedelta(days=horizon)).isoformat(),
        horizon=horizon,
        interval_kind=kind,
        point_forecast=point,
        lower=lower,
        upper=upper,
        width=upper - lower if lower is not None and upper is not None else None,
        available=available,
        unavailable_reason=reason,
        units="sales_value",
        schedule_assumption_flag=(kind == "operational"),
    )


def _cumulative(
    *,
    k: int = 14,
    p: float = 0.95,
    complete: bool = True,
    reason: str | None = None,
    demand: float | None = 100.0,
    quantile: float | None = -7.25,
    upper: float | None = 92.75,
    safety: float | None = 0.0,
    target: float | None = 100.0,
) -> CumulativeUncertainty:
    return CumulativeUncertainty(
        prefix_days=k,
        probability=p,
        issued_prefix_complete=complete,
        unavailable_reason=reason,
        demand_value=demand,
        signed_error_quantile=quantile,
        upper_turnover_value=upper,
        safety_stock_value=safety,
        target_value=target,
        units="sales_value",
        schedule_assumption_flag=True,
    )


def _uncertainty_view(query: UncertaintyQuery) -> ForecastUncertaintyView:
    intervals = (
        _daily(query, 1),
        _daily(query, 2, available=False, lower=None, upper=None, reason="unknown_schedule"),
        _daily(query, 3, kind="operational", point=7.5, lower=0.0, upper=2.0),
        _daily(query, 8),
    )
    return ForecastUncertaintyView(
        state="available",
        query=query,
        daily_intervals=intervals,
        cumulative_uncertainty=(
            _cumulative(),
            _cumulative(
                k=2,
                complete=False,
                reason="incomplete_prefix",
                demand=None,
                quantile=None,
                upper=None,
                safety=None,
                target=None,
            ),
            _cumulative(
                k=14,
                p=0.98,
                complete=True,
                demand=100.0,
                quantile=None,
                upper=None,
                safety=None,
                target=None,
            ),
        ),
        interpretation="Saved empirical values retain their recorded availability and assumptions.",
        provenance=(
            _provenance("phase8_daily_intervals", "phase8"),
            _provenance("phase8_cumulative_uncertainty", "phase8"),
        ),
    )


class _DashboardSpy:
    def __init__(self, *, catalog: ApplicationCatalog | None = None) -> None:
        self.catalog_value = _catalog() if catalog is None else catalog
        self.catalog_calls = 0
        self.history_queries: list[HistoryQuery] = []
        self.forecast_queries: list[ForecastQuery] = []
        self.uncertainty_queries: list[UncertaintyQuery] = []
        self.history_error: Exception | None = None
        self.forecast_errors: list[Exception | None] = []
        self.forecast_value: ForecastIssuanceView | None = None
        self.uncertainty_error: Exception | None = None
        self.uncertainty_value: ForecastUncertaintyView | None = None

    def catalog(self) -> ApplicationCatalog:
        self.catalog_calls += 1
        return self.catalog_value

    def sales_history(self, query: HistoryQuery) -> SalesHistoryView:
        self.history_queries.append(query)
        if self.history_error is not None:
            raise self.history_error
        rows = (
            SalesHistoryRow(query.store_id, query.start_date.isoformat(), 0.0, None),
            SalesHistoryRow(
                query.store_id, (query.start_date + timedelta(days=2)).isoformat(), None, 0.0
            ),
        )
        return SalesHistoryView("available", rows, "2015-07-03", "historical_sales")

    def forecast_issuance(self, query: ForecastQuery) -> ForecastIssuanceView:
        self.forecast_queries.append(query)
        error = self.forecast_errors.pop(0) if self.forecast_errors else None
        if error is not None:
            raise error
        return self.forecast_value or _forecast_view(query)

    def forecast_uncertainty(self, query: UncertaintyQuery) -> ForecastUncertaintyView:
        self.uncertainty_queries.append(query)
        if self.uncertainty_error is not None:
            raise self.uncertainty_error
        return self.uncertainty_value or _uncertainty_view(query)


def _widget(app: AppTest, collection: str, label: str):
    return next(item for item in getattr(app, collection) if item.label == label)


def _apply(app: AppTest) -> AppTest:
    return _widget(app, "button", "Apply selection").click().run()


def test_history_screen_uses_catalog_and_only_applied_history_service() -> None:
    services = _DashboardSpy()
    app = _app(services, "Historical Sales")

    assert services.catalog_calls == 2
    assert services.history_queries == []
    assert "retrospective development history" in _visible_text(app).lower()

    app = _apply(app)

    assert not app.exception
    assert services.history_queries == [HistoryQuery(1, date(2015, 5, 9), date(2015, 7, 3))]
    visible = _visible_text(app)
    assert "Observed source rows returned: 2" in visible
    assert "Source Open status" in visible
    assert "Unknown Open is not a closure" in visible
    assert "2015-05-09" in visible
    assert "Customers" not in visible
    assert "Promo" not in visible


def test_history_empty_missing_and_integrity_errors_are_clear_and_sanitized() -> None:
    class EmptyHistory(_DashboardSpy):
        def sales_history(self, query: HistoryQuery) -> SalesHistoryView:
            self.history_queries.append(query)
            return SalesHistoryView("empty", (), "2015-07-03", "historical_sales")

    empty_app = _apply(_app(EmptyHistory(), "Historical Sales"))
    assert "No observed rows for this selection" in _visible_text(empty_app)
    assert not empty_app.dataframe

    missing = _DashboardSpy()
    missing.history_error = ArtifactUnavailableError(
        ArtifactSelector.HISTORICAL_SALES, UnavailableReason.MISSING_ARTIFACT
    )
    missing_app = _apply(_app(missing, "Historical Sales"))
    missing_text = _visible_text(missing_app)
    assert "resource file is missing" in missing_text
    assert "historical_sales" in missing_text
    assert not missing_app.dataframe

    corrupt = _DashboardSpy()
    corrupt.history_error = ArtifactIntegrityError(ArtifactSelector.HISTORICAL_SALES)
    corrupt_app = _apply(_app(corrupt, "Historical Sales"))
    corrupt_text = _visible_text(corrupt_app)
    assert "integrity check" in corrupt_text
    assert "artifact_integrity_error" in corrupt_text
    assert not corrupt_app.dataframe


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (date(2013, 1, 1), date(2013, 1, 1), "2013-01-01"),
        (date(2015, 7, 3), date(2015, 7, 3), "2015-07-03"),
    ],
)
def test_history_form_dispatches_valid_start_and_end_boundaries(
    start: date, end: date, expected: str
) -> None:
    services = _DashboardSpy()
    app = _app(services, "Historical Sales")
    _widget(app, "date_input", "Start date").set_value(start)
    _widget(app, "date_input", "End date").set_value(end)
    app = _apply(app)

    assert services.history_queries == [HistoryQuery(1, start, end)]
    assert expected in _visible_text(app)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (date(2015, 7, 3), date(2015, 7, 4)),
        (date(2015, 2, 1), date(2015, 1, 31)),
        (date(2014, 7, 2), date(2015, 7, 3)),
    ],
)
def test_history_form_rejects_cutoff_reversal_and_oversize_before_dispatch(
    start: date, end: date
) -> None:
    services = _DashboardSpy()
    app = _app(services, "Historical Sales")
    _widget(app, "date_input", "Start date").set_value(start)
    _widget(app, "date_input", "End date").set_value(end)
    app = _apply(app)

    assert services.history_queries == []
    assert any(item.value for item in app.error)


@pytest.mark.parametrize("origin_text", SUPPORTED_FORECAST_ORIGINS)
def test_forecast_screen_requests_each_supported_origin_and_fit_mapping(origin_text: str) -> None:
    services = _DashboardSpy()
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value(origin_text)
    app = _apply(app)

    origin = date.fromisoformat(origin_text)
    assert services.forecast_queries == [ForecastQuery(1, origin)]
    if origin_text == "2015-05-22":
        assert services.uncertainty_queries == []
        assert "No supported Phase 8 uncertainty fit" in _visible_text(app)
        assert "No uncertainty service request was sent" in _visible_text(app)
    else:
        fit_id = "A" if origin_text == "2015-06-05" else "B"
        assert services.uncertainty_queries == [UncertaintyQuery(1, origin, fit_id)]
        assert f"Fit {fit_id}" in _visible_text(app)
        if fit_id == "A":
            assert "Fit A has documented unavailable horizons" in _visible_text(app)


def test_h7_filters_display_only_and_preserves_exact_raw_operational_forecasts() -> None:
    services = _DashboardSpy()
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    _widget(app, "radio", "Displayed horizon").set_value("H7 · first 7 days")
    app = _apply(app)

    assert services.forecast_queries == [ForecastQuery(1, date(2015, 6, 19))]
    assert services.uncertainty_queries == [UncertaintyQuery(1, date(2015, 6, 19), "B")]
    visible = _visible_text(app)
    assert "Visible saved rows: 2" in visible
    assert "H14 request" in visible
    assert "Operational available" in visible
    assert "33.25" in visible
    assert "80.5" not in visible
    assert "actual_sales" not in visible
    assert "source_open" not in visible


def test_forecast_store_origin_change_uses_new_labels_and_failed_query_clears_results() -> None:
    services = _DashboardSpy()
    app = _app(services)
    app = _apply(app)
    assert "candidate-a" not in _visible_text(app)
    assert "global_lightgbm_gbdt_regression_l1" in _visible_text(app)

    services.forecast_errors.append(RuntimeError("C:\\private\\saved.parquet"))
    _widget(app, "selectbox", "Store").set_value(2)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-05")
    app = _apply(app)

    assert services.forecast_queries == [
        ForecastQuery(1, date(2015, 5, 22)),
        ForecastQuery(2, date(2015, 6, 5)),
    ]
    visible = _visible_text(app)
    assert "internal_error" in visible
    assert "private" not in visible
    assert "global_lightgbm_gbdt_regression_l1" not in visible
    assert not app.dataframe


def test_uncertainty_preserves_reasons_negative_quantile_independent_provenance_and_caveats() -> (
    None
):
    services = _DashboardSpy()
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    app = _apply(app)
    visible = _visible_text(app)

    assert "unknown_schedule" in visible
    assert "-7.25" in visible
    assert "92.75" in visible
    assert "phase8_daily_intervals" in visible
    assert "phase8_cumulative_uncertainty" in visible
    assert "do not guarantee actual 95% coverage" in visible
    assert "sparse weekday support" in visible
    assert "below-nominal development coverage" in visible
    assert "Unknown opening schedules affect operational interpretations" in visible
    assert "not SKU units" in visible
    assert "origin-anchored" in visible


def test_uncertainty_h7_is_daily_only_cumulative_prefix_remains_selected() -> None:
    services = _DashboardSpy()
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    _widget(app, "radio", "Displayed horizon").set_value("H7 · first 7 days")
    _widget(app, "selectbox", "Cumulative prefix k").set_value(2)
    app = _apply(app)

    visible = _visible_text(app)
    assert "Daily raw empirical intervals · H7 display only" in visible
    assert "Saved cumulative prefix · k=2 · p=0.95" in visible
    assert "incomplete_prefix" in visible
    assert "2015-06-27" not in visible  # the saved H8 daily row is display-filtered
    assert "retain their saved k and H14 issuance meaning" in visible


def test_operational_interval_selection_uses_saved_operational_rows() -> None:
    services = _DashboardSpy()
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    _widget(app, "radio", "Daily uncertainty series").set_value("Operational")
    app = _apply(app)

    visible = _visible_text(app)
    assert "Daily operational empirical intervals" in visible
    assert "7.5" in visible
    assert "unknown_schedule" not in visible
    assert services.uncertainty_queries == [UncertaintyQuery(1, date(2015, 6, 19), "B")]


def test_complete_cumulative_prefix_with_missing_saved_values_is_not_filled() -> None:
    services = _DashboardSpy()
    query = UncertaintyQuery(1, date(2015, 6, 19), "B")
    complete_missing = _cumulative(
        k=14,
        p=0.98,
        complete=True,
        reason="quantile_unavailable",
        demand=100.0,
        quantile=None,
        upper=None,
        safety=None,
        target=None,
    )
    base_view = _uncertainty_view(query)
    services.uncertainty_value = replace(
        base_view,
        cumulative_uncertainty=base_view.cumulative_uncertainty + (complete_missing,),
    )
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    _widget(app, "selectbox", "Saved probability p").set_value(0.98)
    app = _apply(app)

    visible = _visible_text(app)
    assert "quantile_unavailable" in visible
    assert "one or more saved numerical values are unavailable" in visible
    assert "Target" in visible


def test_all_unavailable_daily_intervals_keep_reasons_and_render_no_band_data() -> None:
    services = _DashboardSpy()
    query = UncertaintyQuery(1, date(2015, 6, 19), "B")
    base_view = _uncertainty_view(query)
    unavailable = tuple(
        _daily(
            query,
            horizon,
            available=False,
            point=None,
            lower=None,
            upper=None,
            reason="insufficient_tail_sample",
        )
        for horizon in (1, 2)
    )
    services.uncertainty_value = replace(base_view, daily_intervals=unavailable)
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    app = _apply(app)

    visible = _visible_text(app)
    assert "insufficient_tail_sample" in visible
    assert "Available" in visible


def test_active_screen_dispatch_and_uncertainty_error_do_not_keep_uncertainty_panel() -> None:
    services = _DashboardSpy()
    app = _app(services, "Overview & Evidence")
    assert services.catalog_calls == 1
    assert not services.forecast_queries and not services.history_queries

    app.sidebar.radio[0].set_value("Model Comparison").run()
    app.sidebar.radio[0].set_value("Inventory Comparison").run()
    assert services.catalog_calls == 1
    assert not services.forecast_queries and not services.history_queries

    app.sidebar.radio[0].set_value("Forecast Explorer").run()
    services.uncertainty_error = RuntimeError("C:\\private\\uncertainty.parquet")
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    app = _apply(app)
    visible = _visible_text(app)
    assert "internal_error" in visible
    assert "private" not in visible
    assert "Uncertainty artifact provenance" not in visible
    assert "Forecast artifact provenance" in visible


def test_stale_service_dto_identity_is_never_labeled_as_the_new_selection() -> None:
    services = _DashboardSpy()
    services.forecast_value = _forecast_view(ForecastQuery(1, date(2015, 5, 22)))
    app = _app(services)
    _widget(app, "selectbox", "Store").set_value(2)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-05")
    app = _apply(app)

    visible = _visible_text(app)
    assert "internal_error" in visible
    assert "Applied forecast" not in visible
    assert "Frozen candidate identity" not in visible
    assert not app.dataframe

    services.forecast_value = None
    services.uncertainty_value = _uncertainty_view(UncertaintyQuery(1, date(2015, 6, 5), "A"))
    app = _apply(app)
    visible = _visible_text(app)
    assert "Applied forecast" in visible
    assert "internal_error" in visible
    assert "Uncertainty artifact provenance" not in visible


def _write_history_source(
    root, rows: list[tuple[int, datetime, float | None, float | None]]
) -> None:
    path = root / "data/interim/train.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([row[0] for row in rows], type=pa.int64()),
                "Date": pa.array([row[1] for row in rows], type=pa.timestamp("ns")),
                "Sales": pa.array([row[2] for row in rows], type=pa.float64()),
                "Open": pa.array([row[3] for row in rows], type=pa.float64()),
            }
        ),
        path,
    )


def test_real_application_services_history_reader_keeps_boundary_zero_and_unknown_open(
    tmp_path,
) -> None:
    _write_history_source(
        tmp_path,
        [
            (1, datetime(2013, 1, 1), 0.0, None),
            (1, datetime(2015, 7, 3), None, 1.0),
        ],
    )
    services = ApplicationServices(_ArtifactReader(root=tmp_path))
    lower = services.sales_history(HistoryQuery(1, date(2013, 1, 1), date(2013, 1, 1)))
    upper = services.sales_history(HistoryQuery(1, date(2015, 7, 3), date(2015, 7, 3)))

    assert lower.rows == (SalesHistoryRow(1, "2013-01-01", 0.0, None),)
    assert upper.rows == (SalesHistoryRow(1, "2015-07-03", None, 1.0),)


@pytest.mark.parametrize("failure", ["missing", "corrupt"])
def test_real_services_history_missing_and_corrupt_source_are_safe(tmp_path, failure: str) -> None:
    fixtures = FixtureStore(tmp_path)
    history_path = tmp_path / "data/interim/train.parquet"
    if failure == "corrupt":
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_bytes(b"not a Parquet source")
    app = _apply(_app(ApplicationServices(fixtures.reader()), "Historical Sales"))

    visible = _visible_text(app)
    if failure == "missing":
        assert "resource file is missing" in visible
        assert "artifact_unavailable" in visible
    else:
        assert "accepted schema" in visible
        assert "artifact_schema_error" in visible
    assert "not a Parquet source" not in visible
    assert not app.dataframe


@pytest.mark.parametrize("failure", ["missing", "corrupt"])
def test_real_services_forecast_missing_and_corrupt_outputs_are_sanitized(
    tmp_path, failure: str
) -> None:
    fixtures = FixtureStore(tmp_path)
    selector = ArtifactSelector.PHASE7_FORECASTS
    path = _artifact_path(fixtures, selector)
    if failure == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b"corruption")
    services = ApplicationServices(fixtures.reader())
    app = _app(services)
    _widget(app, "selectbox", "Forecast origin").set_value("2015-06-19")
    app = _apply(app)

    visible = _visible_text(app)
    if failure == "missing":
        assert "resource file is missing" in visible
    else:
        assert "integrity check" in visible
    assert "phase7_forecasts" in visible
    assert "corruption" not in visible
    assert not app.dataframe


def test_fixture_services_forecast_and_uncertainty_views_keep_provenance_and_no_outcomes(
    tmp_path,
) -> None:
    fixture_store = FixtureStore(tmp_path)
    services = ApplicationServices(fixture_store.reader())
    query = ForecastQuery(1, date(2015, 6, 19))
    forecast = services.forecast_issuance(query)
    uncertainty_query = UncertaintyQuery(1, date(2015, 6, 19), "B")
    uncertainty = services.forecast_uncertainty(uncertainty_query)
    forecast_text = str(forecast)
    uncertainty_text = str(uncertainty)

    assert forecast.provenance.selector == "phase7_forecasts"
    assert uncertainty.provenance[0].selector == "phase8_daily_intervals"
    assert uncertainty.provenance[1].selector == "phase8_cumulative_uncertainty"
    assert "actual_sales" not in forecast_text
    assert "source_open" not in forecast_text
    assert "assessment_source_open" not in uncertainty_text


def test_history_cutoff_is_checked_before_any_history_service_dispatch() -> None:
    services = _DashboardSpy()
    _app(services, "Historical Sales")
    assert (
        validate_history_selection(
            1, date(2015, 7, 3), date(2015, 7, 4), services.catalog_value.supported_store_ids
        )
        is not None
    )
    assert services.history_queries == []


def test_supported_uncertainty_controls_are_closed_sets() -> None:
    assert SUPPORTED_FIT_ORIGINS == {"A": "2015-06-05", "B": "2015-06-19"}
    assert SUPPORTED_CUMULATIVE_PROBABILITIES == (0.90, 0.95, 0.98)


def test_dashboard_has_no_api_loopback_inference_comparison_or_ledger_access() -> None:
    from pathlib import Path

    source = Path("src/rossmann_forecasting/app/dashboard.py").read_text(encoding="utf-8")
    assert "create_app" not in source
    assert "httpx" not in source
    assert "requests." not in source
    assert "model_comparison(" not in source
    assert "inventory_comparison(" not in source
    assert "simulation_ledger" not in source
    assert "PHASE10_POLICY" not in source
