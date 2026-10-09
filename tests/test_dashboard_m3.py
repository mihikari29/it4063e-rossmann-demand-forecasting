"""M3 presenter, Streamlit, chart, and isolated-reader integration tests."""

from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date
from unittest.mock import patch

import matplotlib
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from streamlit.testing.v1 import AppTest
from test_app_artifacts import (
    _ARTIFACTS,
    FixtureStore,
    _artifact_path,
    _csv_value,
    _sample_arrow_value,
)

from rossmann_forecasting.app.artifacts import _ArtifactReader
from rossmann_forecasting.app.contracts import (
    ArtifactSelector,
    InventoryComparisonQuery,
    ModelComparisonQuery,
)
from rossmann_forecasting.app.dashboard_presenters import (
    INVENTORY_BUFFER_090_CASE,
    INVENTORY_METRICS,
    INVENTORY_POLICY_IDS,
    INVENTORY_REFERENCE_CASE,
    MODEL_CANDIDATES,
    MODEL_COVERAGE_METRIC,
    MODEL_MAPE_DIAGNOSTICS,
    ModelComparisonTooLargeError,
    inventory_comparison_records,
    inventory_cost_direction,
    model_comparison_query_presets,
    model_comparison_records,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ApplicationServices,
    ArtifactProvenance,
    InventoryAggregate,
    InventoryComparisonView,
    InventoryPolicyPair,
    ModelComparisonRow,
    ModelComparisonView,
    PolicyResult,
    ScenarioEntry,
)
from rossmann_forecasting.inventory.simulation import (
    POLICY_SUMMARY_SCHEMA,
    POLICY_TARGET_SCHEMA,
)

matplotlib.use("Agg", force=True)


def _dashboard_test_app(services: object) -> None:
    from rossmann_forecasting.app.dashboard import run_dashboard

    run_dashboard(services=services)


def _app(services: object, screen: str) -> AppTest:
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


def _widget(app: AppTest, collection: str, label: str):
    return next(item for item in getattr(app, collection) if item.label == label)


def _apply(app: AppTest) -> AppTest:
    button = next((item for item in app.button if item.label == "Apply selection"), None)
    if button is None:
        raise AssertionError(
            f"Apply selection is unavailable. Visible UI: {_visible_text(app)}; "
            f"exceptions: {app.exception}"
        )
    return button.click().run()


def _provenance(selector: str, phase: str) -> ArtifactProvenance:
    return ArtifactProvenance(
        selector=selector,
        phase=phase,
        run_id=f"{phase}-fixture-run",
        manifest_sha256=f"{phase}-manifest-sha",
        output_sha256=f"{phase}-output-sha",
        selected_rows=3,
        manifest_rows=100,
    )


def _catalog(
    *,
    case_ids: tuple[str, ...] = ("opaque-case--reference", "opaque-case--buffer_090"),
    stores: tuple[int, ...] = (1, 2, 3),
    case_state: str | None = None,
) -> ApplicationCatalog:
    state = case_state or ("available" if case_ids else "empty")
    return ApplicationCatalog(
        phases=("phase7", "phase8", "phase9", "phase10"),
        selectors=("phase7_model_comparison", "phase10_comparison"),
        supported_store_ids=stores,
        phase7_forecast_origins=("2015-05-22", "2015-06-05", "2015-06-19"),
        phase8_fits=(("A", "2015-06-05"), ("B", "2015-06-19")),
        scenario_catalog_state="available",
        scenarios=(
            ScenarioEntry(
                "synthetic_base",
                "synthetic_base",
                "synthetic",
                "2015-06-05",
                0,
                14,
                "planned_open",
                "synthetic_turnover_value",
                "base",
                False,
            ),
        ),
        inventory_case_state=state,
        inventory_case_ids=case_ids,
        resources=(),
        scenario_provenance=_provenance("phase9_scenario_catalog", "phase9"),
        inventory_case_provenance=_provenance("phase10_comparison", "phase10"),
    )


class _SensitiveValue:
    def __repr__(self) -> str:
        return "C:\\private\\untrusted.parquet"


def _model_row(
    candidate: str,
    *,
    population: str = "three_way_common",
    scope: str = "pooled",
    metric: str = "mae",
    window: str | None = None,
    horizon: int | None = None,
    store_id: int | None = None,
    value: float | None = 10.0,
    numerator: float | None = 100.0,
    denominator: float | None = 10.0,
    reason: str | None = None,
) -> ModelComparisonRow:
    return ModelComparisonRow(
        candidate_id=candidate,
        population=population,
        paired_with=None,
        scope=scope,
        validation_window=window,
        horizon=horizon,
        week_block_start_horizon=1 if scope == "week_block" else None,
        week_block_end_horizon=7 if scope == "week_block" else None,
        store_id=store_id,
        metric=metric,
        value=value,
        numerator=numerator,
        denominator=denominator,
        unavailable_reason=reason,
        paired_mae_delta=1.25,
        paired_mae_change_fraction=0.125,
    )


def _model_view(rows: tuple[ModelComparisonRow, ...]) -> ModelComparisonView:
    return ModelComparisonView(
        state="available" if rows else "empty",
        rows=rows,
        provenance=_provenance("phase7_model_comparison", "phase7"),
    )


def _rows_for_query(query: ModelComparisonQuery) -> tuple[ModelComparisonRow, ...]:
    if query.metric == MODEL_COVERAGE_METRIC:
        return tuple(
            _model_row(
                candidate,
                population="standalone",
                scope="validation_window",
                metric=query.metric,
                window=window,
                value=0.5,
                numerator=5.0,
                denominator=10.0,
            )
            for candidate in MODEL_CANDIDATES
            for window in ("validation_1", "validation_2", "validation_3")
        )
    if query.scope == "horizon":
        return tuple(
            _model_row(
                candidate,
                scope="horizon",
                metric=query.metric or "mae",
                horizon=horizon,
                value=(
                    75.0
                    if query.metric == "mape_rows"
                    else 4.0
                    if query.metric == "zero_actual_rows_excluded_from_mape"
                    else 99.0
                    if candidate == MODEL_CANDIDATES[2] and horizon == 10
                    else 10.0 + horizon
                ),
                numerator=100.0 + horizon,
                denominator=10.0,
            )
            for candidate in MODEL_CANDIDATES
            for horizon in range(1, 15)
        )
    if query.scope == "week_block":
        rows = []
        for candidate_index, candidate in enumerate(MODEL_CANDIDATES):
            first = _model_row(
                candidate,
                scope="week_block",
                metric=query.metric or "mae",
                value=10.0 + candidate_index,
            )
            second = replace(
                first,
                week_block_start_horizon=8,
                week_block_end_horizon=14,
                value=11.0 + candidate_index,
            )
            rows.extend((first, second))
        return tuple(rows)
    if query.scope == "validation_window" and query.validation_window is None:
        windows = ("validation_1", "validation_2", "validation_3")
    else:
        windows = (query.validation_window,) if query.validation_window is not None else (None,)
    return tuple(
        _model_row(
            candidate,
            population=query.population or "three_way_common",
            scope=query.scope or "pooled",
            metric=query.metric or "mae",
            window=window,
            store_id=query.store_id,
            value=(
                75.0
                if query.metric == "mape_rows"
                else 4.0
                if query.metric == "zero_actual_rows_excluded_from_mape"
                else 15.0
                if query.metric == "mape"
                else 0.21
                if query.metric == "wape"
                else 2.0 + candidate_index
            ),
            numerator=20.0 + candidate_index,
            denominator=100.0,
        )
        for candidate_index, candidate in enumerate(MODEL_CANDIDATES)
        for window in windows
    )


def _policy_result(
    policy_id: str,
    *,
    episode_complete: bool = True,
    target_available: bool = True,
    target_value: float | None = 0.0,
    target_reason: str | None = None,
    cost: float | None = 100.0,
) -> PolicyResult:
    return PolicyResult(
        policy_id=policy_id,
        episode_status="complete" if episode_complete else "incomplete",
        episode_complete=episode_complete,
        target_available=target_available,
        target_unavailability_reason=target_reason,
        availability_reason=None if episode_complete else "episode_incomplete",
        valid_matched_comparison=episode_complete and target_available and cost is not None,
        simulated_holding_plus_shortfall_cost=cost,
        demand_total=500.0,
        fulfilled_total=450.0,
        unmet_total=50.0,
        target_value=target_value,
        synthetic=True,
        calibration_transport_valid=False,
        schedule_assumption="planned_synthetic_schedule",
    )


def _aggregate(metric: str, case_id: str) -> InventoryAggregate:
    values = {
        "SimulatedHoldingPlusShortfallCost": (100.0, 112.5, 12.5),
        "ValueFillRate": (0.9, 0.8, -0.1),
        "PositiveDemandStockoutRate": (0.1, 0.2, 0.1),
    }
    baseline, forecast, difference = values.get(metric, (1.0, 2.0, 1.0))
    return InventoryAggregate(
        case_id=case_id,
        metric=metric,
        requested_store_count=3,
        baseline_standalone_store_count=3,
        forecast_standalone_store_count=3,
        matched_store_count=2,
        baseline_numerator=baseline * 10,
        baseline_denominator=10.0,
        forecast_numerator=forecast * 20,
        forecast_denominator=20.0,
        baseline_value=baseline,
        forecast_value=forecast,
        forecast_minus_baseline=difference,
        forecast_minus_baseline_relative=0.125,
        relative_difference_null_reason=None,
        null_reason=None,
        interpretation="saved fixture interpretation",
    )


def _inventory_view(
    case_id: str,
    store_id: int | None,
    *,
    difference: float | None = -3.25,
    reason: str | None = None,
    empty_pair: bool = False,
    asymmetric: bool = False,
    incomplete: bool = False,
) -> InventoryComparisonView:
    aggregates = tuple(_aggregate(metric, case_id) for metric in INVENTORY_METRICS)
    stores = () if empty_pair else ((store_id,) if store_id is not None else (1, 2))
    pairs = []
    for selected_store in stores:
        if asymmetric:
            baseline = _policy_result("historical_mean_standing_target", target_value=0.0)
            forecast = _policy_result(
                "lightgbm_buffer_standing_target",
                target_available=False,
                target_value=None,
                target_reason="buffer_unavailable",
            )
            pair_difference = None
            pair_reason = "buffer_unavailable"
        elif incomplete:
            baseline = _policy_result("historical_mean_standing_target", episode_complete=False)
            forecast = _policy_result("lightgbm_buffer_standing_target")
            pair_difference = None
            pair_reason = "episode_incomplete"
        else:
            baseline = _policy_result("historical_mean_standing_target", target_value=0.0)
            forecast = _policy_result(
                "lightgbm_buffer_standing_target",
                target_value=45.0,
                cost=100.0 + (difference or 0.0),
            )
            pair_difference = difference
            pair_reason = reason
        comparable = pair_difference is not None
        pairs.append(
            InventoryPolicyPair(
                case_id=case_id,
                store_id=selected_store,
                comparable=comparable,
                forecast_minus_baseline_cost=pair_difference,
                difference_unavailable_reason=None if comparable else pair_reason,
                baseline=baseline,
                forecast=forecast,
            )
        )
    return InventoryComparisonView(
        state="available" if pairs else "empty",
        case_id=case_id,
        store_id=store_id,
        case_level_comparisons=aggregates,
        policy_pairs=tuple(pairs),
        provenance=(
            _provenance("phase10_comparison", "phase10"),
            _provenance("phase10_policy_summary", "phase10"),
            _provenance("phase10_policy_targets", "phase10"),
        ),
    )


class _DashboardSpy:
    def __init__(self, catalog: ApplicationCatalog | None = None) -> None:
        self.catalog_value = catalog or _catalog()
        self.catalog_calls = 0
        self.model_queries: list[ModelComparisonQuery] = []
        self.model_error: Exception | None = None
        self.model_corruption: str | None = None
        self.inventory_queries: list[InventoryComparisonQuery] = []
        self.inventory_error: Exception | None = None
        self.inventory_factory = None

    def catalog(self) -> ApplicationCatalog:
        self.catalog_calls += 1
        return self.catalog_value

    def model_comparison(self, query: ModelComparisonQuery) -> ModelComparisonView:
        self.model_queries.append(query)
        if self.model_error is not None:
            raise self.model_error
        view = _model_view(_rows_for_query(query))
        if self.model_corruption == "row":
            view = replace(
                view, rows=(replace(view.rows[0], value=_SensitiveValue()), *view.rows[1:])
            )
        elif self.model_corruption == "provenance":
            view = replace(
                view,
                provenance=replace(view.provenance, run_id="C:\\private\\model.csv"),
            )
        return view

    def inventory_comparison(self, query: InventoryComparisonQuery) -> InventoryComparisonView:
        self.inventory_queries.append(query)
        if self.inventory_error is not None:
            raise self.inventory_error
        if self.inventory_factory is not None:
            return self.inventory_factory(query)
        return _inventory_view(query.case_id, query.store_id)


def test_model_query_presets_are_bounded_and_use_fixed_filters() -> None:
    horizon = model_comparison_query_presets("horizon", "mae")
    assert horizon["primary"] == ModelComparisonQuery(
        population="three_way_common", scope="horizon", metric="mae", limit=42
    )
    assert horizon["horizon_mae"].limit == 42
    assert horizon["standalone_coverage"].population == "standalone"
    assert horizon["standalone_coverage"].metric == MODEL_COVERAGE_METRIC
    assert all(query.limit <= 500 for query in horizon.values())

    store = model_comparison_query_presets("store", "wape", store_id=9)
    assert store["primary"].store_id == 9
    assert store["primary"].limit == 200
    assert "mape_rows" not in store
    mape = model_comparison_query_presets("pooled", "mape")
    assert set(MODEL_MAPE_DIAGNOSTICS).issubset(mape)
    assert all(
        query.metric in ("mape_rows", "zero_actual_rows_excluded_from_mape")
        for key, query in mape.items()
        if key in MODEL_MAPE_DIAGNOSTICS
    )
    with pytest.raises(ValueError):
        model_comparison_query_presets("validation_window", "mae")
    with pytest.raises(ValueError):
        model_comparison_query_presets("pooled", "mae", store_id=1)


def test_model_presenter_preserves_exact_values_nulls_denominators_and_units() -> None:
    query = ModelComparisonQuery(
        population="three_way_common", scope="pooled", metric="wape", limit=200
    )
    rows = tuple(
        _model_row(candidate, metric="wape", value=0.125, numerator=25.0, denominator=200.0)
        for candidate in MODEL_CANDIDATES
    )
    records = model_comparison_records(_model_view(rows), query)
    assert [row["candidate_id"] for row in records] == list(MODEL_CANDIDATES)
    assert all(row["population"] == "three_way_common" for row in records)
    assert all(row["value"] == 0.125 for row in records)
    assert all(row["value_display"] == "12.5% (saved fraction 0.125)" for row in records)
    assert all(row["numerator"] == 25.0 and row["denominator"] == 200.0 for row in records)

    mape_row = replace(rows[0], metric="mape", value=12.5, denominator=160.0)
    mape_query = replace(query, metric="mape")
    mape_records = model_comparison_records(_model_view((mape_row,)), mape_query)
    assert mape_records[0]["value"] == 12.5
    assert mape_records[0]["value_display"] == "12.5% (percentage points)"

    unavailable = replace(rows[0], value=None, denominator=None, unavailable_reason="no_rows")
    null_records = model_comparison_records(_model_view((unavailable,)), query)
    assert null_records[0]["value"] is None
    assert null_records[0]["denominator"] is None
    assert null_records[0]["unavailable_reason"] == "no_rows"


def test_model_presenter_rejects_duplicate_dimensions_and_oversized_views() -> None:
    query = ModelComparisonQuery(
        population="three_way_common", scope="pooled", metric="mae", limit=2
    )
    duplicate = _model_row(MODEL_CANDIDATES[0])
    with pytest.raises(ValueError, match="Duplicate"):
        model_comparison_records(_model_view((duplicate, duplicate)), query)
    too_many = _model_view(tuple(_model_row(candidate) for candidate in MODEL_CANDIDATES))
    with pytest.raises(ModelComparisonTooLargeError):
        model_comparison_records(too_many, query)


def test_model_screen_compares_all_candidates_and_keeps_weak_h10_charted() -> None:
    from rossmann_forecasting.app import dashboard

    services = _DashboardSpy()
    captured = []
    with patch.object(
        dashboard.st, "pyplot", side_effect=lambda figure, **_: captured.append(figure)
    ):
        app = _apply(_app(services, "Model Comparison"))

    visible = _visible_text(app)
    assert not app.exception
    assert all(candidate in visible for candidate in MODEL_CANDIDATES)
    assert "three_way_common" in visible
    assert "standalone" in visible
    assert "h1–h14" in visible
    assert "99.0" in visible
    assert len(captured) == 2
    assert [bar.get_height() for bar in captured[0].axes[0].patches] == [2.0, 3.0, 4.0]
    horizon_lines = captured[1].axes[0].lines
    assert len(horizon_lines) == 3
    assert [line.get_ydata()[9] for line in horizon_lines] == [20.0, 20.0, 99.0]
    assert all(query.limit <= 500 for query in services.model_queries)
    assert any(
        query.metric == "open_label_forecast_coverage_rate" for query in services.model_queries
    )
    assert any(query.metric == "wape" for query in services.model_queries)


def test_model_screen_mape_diagnostics_and_separate_coverage_keep_denominators() -> None:
    services = _DashboardSpy()
    app = _app(services, "Model Comparison")
    _widget(app, "selectbox", "Metric").set_value("mape")
    app = _apply(app)

    visible = _visible_text(app)
    assert not app.exception
    assert "15% (percentage points)" in visible
    assert "21% (saved fraction 0.21)" in visible
    assert "50% (saved fraction 0.5)" in visible
    assert "mape_rows" in visible
    assert "zero_actual_rows_excluded_from_mape" in visible
    assert "denominator" in visible
    primary_queries = [query for query in services.model_queries if query.metric == "mape"]
    coverage_queries = [
        query for query in services.model_queries if query.metric == MODEL_COVERAGE_METRIC
    ]
    assert primary_queries and all(
        query.population == "three_way_common" for query in primary_queries
    )
    assert coverage_queries and all(query.population == "standalone" for query in coverage_queries)
    assert {query.metric for query in services.model_queries}.issuperset(
        {"mape_rows", "zero_actual_rows_excluded_from_mape"}
    )


@pytest.mark.parametrize("corruption", ("row", "provenance"))
def test_malformed_model_panel_is_atomic_and_sanitized(corruption: str) -> None:
    from rossmann_forecasting.app import dashboard

    services = _DashboardSpy()
    services.model_corruption = corruption
    captured = []
    with patch.object(
        dashboard.st, "pyplot", side_effect=lambda figure, **_: captured.append(figure)
    ):
        app = _apply(_app(services, "Model Comparison"))

    visible = _visible_text(app)
    assert not app.exception
    assert "internal_error" in visible
    assert "private" not in visible
    assert "C:\\private" not in visible
    assert not app.dataframe
    assert captured == []


def test_model_unexpected_service_failure_clears_prior_results_and_hides_exception() -> None:
    services = _DashboardSpy()
    app = _apply(_app(services, "Model Comparison"))
    assert "Primary comparison" in _visible_text(app)
    services.model_error = RuntimeError("C:\\private\\raw.csv")
    app = _apply(app)
    assert not app.exception
    assert "internal_error" in _visible_text(app)
    assert "private" not in _visible_text(app)
    assert "Primary comparison" not in _visible_text(app)
    assert not app.dataframe


def test_model_invalid_request_error_is_narrow_selection_and_clears_prior_results() -> None:
    from rossmann_forecasting.app.contracts import InvalidArtifactRequestError

    services = _DashboardSpy()
    app = _apply(_app(services, "Model Comparison"))
    assert "Primary comparison" in _visible_text(app)
    services.model_error = InvalidArtifactRequestError(ArtifactSelector.PHASE7_MODEL_COMPARISON)
    app = _apply(app)
    visible = _visible_text(app)
    assert not app.exception
    assert "Narrow the selection" in visible
    assert "Primary comparison" not in visible
    assert not app.dataframe


def test_model_scope_controls_submit_exact_window_and_store_queries() -> None:
    services = _DashboardSpy()
    app = _app(services, "Model Comparison")
    _widget(app, "selectbox", "Scope").set_value("validation_window")
    app = _apply(app)
    query = next(query for query in services.model_queries if query.scope == "validation_window")
    assert query.validation_window == "validation_1"
    assert query.store_id is None
    _widget(app, "selectbox", "Validation window").set_value("validation_3")
    app = _apply(app)
    query = [query for query in services.model_queries if query.scope == "validation_window"][-1]
    assert query.validation_window == "validation_3"

    _widget(app, "selectbox", "Scope").set_value("store")
    app = _apply(app)
    query = [query for query in services.model_queries if query.scope == "store"][-1]
    assert query.store_id == 1
    assert query.validation_window is None


def test_inventory_presenter_preserves_all_aggregate_fields_and_policy_nulls() -> None:
    query = InventoryComparisonQuery("opaque-case--reference", 1)
    view = _inventory_view(query.case_id, query.store_id, asymmetric=True)
    prepared = inventory_comparison_records(view, query)
    assert [row["metric"] for row in prepared["aggregates"]] == list(INVENTORY_METRICS)
    assert prepared["missing_metrics"] == []
    cost = prepared["aggregates"][0]
    assert cost["requested_store_count"] == 3
    assert cost["matched_store_count"] == 2
    assert cost["baseline_numerator"] == 1000.0
    assert cost["baseline_denominator"] == 10.0
    assert cost["forecast_numerator"] == 2250.0
    assert cost["forecast_denominator"] == 20.0
    assert cost["forecast_minus_baseline"] == 12.5
    baseline, forecast = prepared["policies"]
    assert baseline["target_available"] is True and baseline["target_value"] == 0.0
    assert forecast["target_available"] is False
    assert forecast["target_value"] is None
    assert forecast["target_unavailability_reason"] == "buffer_unavailable"
    assert prepared["pairs"][0]["forecast_minus_baseline_cost"] is None
    assert prepared["pairs"][0]["difference_unavailable_reason"] == "buffer_unavailable"


def test_inventory_presenter_rejects_comparability_inconsistent_with_policy_states() -> None:
    query = InventoryComparisonQuery("opaque-case--reference", 1)
    view = _inventory_view(query.case_id, query.store_id)
    inconsistent_pair = replace(
        view.policy_pairs[0],
        baseline=replace(view.policy_pairs[0].baseline, episode_complete=False),
    )
    malformed = replace(view, policy_pairs=(inconsistent_pair,))
    with pytest.raises(ValueError, match="comparability"):
        inventory_comparison_records(malformed, query)


@pytest.mark.parametrize(
    ("value", "reason", "expected"),
    [
        (5.0, None, "Adverse — higher simulated cost"),
        (-5.0, None, "Favorable — lower simulated cost, conditional on assumptions"),
        (0.0, None, "Equal simulated cost"),
        (None, "not_comparable", "Unavailable — not_comparable"),
    ],
)
def test_inventory_cost_direction_uses_saved_signed_value_and_reason(
    value: float | None, reason: str | None, expected: str
) -> None:
    assert inventory_cost_direction(value, reason) == expected


def test_inventory_case_list_exact_selection_and_store_change_keep_aggregate_scope() -> None:
    services = _DashboardSpy(
        _catalog(case_ids=("opaque-case--reference", "opaque-case--buffer_090"))
    )
    app = _app(services, "Inventory Comparison")
    case_widget = _widget(app, "selectbox", "Saved case")
    assert set(case_widget.options) == {"opaque-case--reference", "opaque-case--buffer_090"}
    assert case_widget.value == "opaque-case--reference"
    app = _apply(app)
    assert not app.exception
    assert "Whole saved case — all matched Stores" in _visible_text(app)
    assert "SimulatedHoldingPlusShortfallCost" in _visible_text(app)
    assert "ValueFillRate" in _visible_text(app)
    assert "PositiveDemandStockoutRate" in _visible_text(app)
    aggregate_before = next(
        element.value
        for element in app.dataframe
        if hasattr(element.value, "columns") and "metric" in element.value.columns
    )

    _widget(app, "selectbox", "Store (optional)").set_value(2)
    app = _apply(app)
    aggregate_after = next(
        element.value
        for element in app.dataframe
        if hasattr(element.value, "columns") and "metric" in element.value.columns
    )
    assert aggregate_before.to_dict("records") == aggregate_after.to_dict("records")
    assert services.inventory_queries[-1] == InventoryComparisonQuery("opaque-case--reference", 2)
    _widget(app, "selectbox", "Saved case").set_value("opaque-case--buffer_090")
    app = _apply(app)
    assert services.inventory_queries[-1].case_id == "opaque-case--buffer_090"


def test_inventory_reference_default_is_used_only_when_catalog_contains_it() -> None:
    with_reference = _app(
        _DashboardSpy(_catalog(case_ids=("other-case", INVENTORY_REFERENCE_CASE))),
        "Inventory Comparison",
    )
    assert _widget(with_reference, "selectbox", "Saved case").value == INVENTORY_REFERENCE_CASE
    without_reference = _app(
        _DashboardSpy(_catalog(case_ids=("first-case", INVENTORY_BUFFER_090_CASE))),
        "Inventory Comparison",
    )
    assert _widget(without_reference, "selectbox", "Saved case").value == "first-case"


def test_inventory_empty_store_pair_retains_whole_case_aggregates() -> None:
    services = _DashboardSpy()
    services.inventory_factory = lambda query: _inventory_view(
        query.case_id, query.store_id, empty_pair=True
    )
    app = _app(services, "Inventory Comparison")
    _widget(app, "selectbox", "Store (optional)").set_value(2)
    app = _apply(app)
    visible = _visible_text(app)
    assert not app.exception
    assert "Whole saved case — all matched Stores" in visible
    assert "No saved policy pair was returned for Store 2" in visible
    assert "SimulatedHoldingPlusShortfallCost" in visible
    assert (
        len(next(element.value for element in app.dataframe if "metric" in element.value.columns))
        == 10
    )


@pytest.mark.parametrize(
    ("difference", "expected"),
    [
        (4.5, "Adverse — higher simulated cost"),
        (-4.5, "Favorable — lower simulated cost, conditional on assumptions"),
        (0.0, "Equal simulated cost"),
    ],
)
def test_inventory_store_pair_shows_signed_cost_language(difference: float, expected: str) -> None:
    services = _DashboardSpy()
    services.inventory_factory = lambda query: _inventory_view(
        query.case_id, query.store_id, difference=difference
    )
    app = _apply(_app(services, "Inventory Comparison"))
    visible = _visible_text(app)
    assert expected in visible
    assert "savings" not in visible.lower()
    assert "optimal" not in visible.lower()
    assert "forecast-policy cost minus baseline-policy cost" in visible
    assert "general reviewed R=1, L=2–7 and P=L+1 context does not verify" in visible


def test_inventory_cost_chart_uses_saved_signed_difference_and_zero_reference() -> None:
    from rossmann_forecasting.app import dashboard

    services = _DashboardSpy()
    services.inventory_factory = lambda query: _inventory_view(
        query.case_id, query.store_id, difference=-3.25
    )
    captured = []
    with patch.object(
        dashboard.st, "pyplot", side_effect=lambda figure, **_: captured.append(figure)
    ):
        app = _apply(_app(services, "Inventory Comparison"))
    assert not app.exception
    assert len(captured) == 2
    widths = [figure.axes[0].patches[0].get_width() for figure in captured]
    assert widths == [12.5, -3.25]
    for figure in captured:
        FigureCanvasAgg(figure).draw()
        zero_reference = [line for line in figure.axes[0].lines if list(line.get_xdata()) == [0, 0]]
        assert zero_reference


def test_inventory_malformed_provenance_is_atomic_and_sanitized() -> None:
    from rossmann_forecasting.app import dashboard

    services = _DashboardSpy()

    def malformed(query: InventoryComparisonQuery) -> InventoryComparisonView:
        view = _inventory_view(query.case_id, query.store_id)
        bad = replace(view.provenance[0], output_sha256="C:\\private\\artifact.parquet")
        return replace(view, provenance=(bad, *view.provenance[1:]))

    services.inventory_factory = malformed
    captured = []
    with patch.object(
        dashboard.st, "pyplot", side_effect=lambda figure, **_: captured.append(figure)
    ):
        app = _apply(_app(services, "Inventory Comparison"))
    visible = _visible_text(app)
    assert not app.exception
    assert "internal_error" in visible
    assert "private" not in visible
    assert "Whole saved case — all matched Stores" not in visible
    assert not any("SimulatedHoldingPlusShortfallCost" in str(item.value) for item in app.dataframe)
    assert captured == []


def test_inventory_empty_and_unavailable_catalog_states_are_distinct() -> None:
    empty_services = _DashboardSpy(_catalog(case_ids=()))
    empty = _app(empty_services, "Inventory Comparison")
    assert "verified inventory case catalog contains no saved cases" in _visible_text(empty)
    assert not empty_services.inventory_queries

    unavailable = _app(
        _DashboardSpy(_catalog(case_ids=(), case_state="unavailable")), "Inventory Comparison"
    )
    assert "Saved inventory cases are unavailable" in _visible_text(unavailable)


def _write_csv_rows(fixtures: FixtureStore, selector: ArtifactSelector, rows: list[dict]) -> None:
    path = _artifact_path(fixtures, selector)
    columns = _ARTIFACTS[selector].csv_header
    assert columns is not None
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for updates in rows:
            row = {column: _csv_value(selector, column) for column in columns}
            row.update(updates)
            writer.writerow(["" if row[column] is None else row[column] for column in columns])
    fixtures.refresh_output(selector)
    spec = _ARTIFACTS[selector]
    fixtures.manifests[spec.phase]["outputs"][spec.filename]["rows"] = len(rows)
    fixtures.refresh_manifest(spec.phase)


def _model_fixture_rows() -> list[dict]:
    rows = []
    for candidate_index, candidate in enumerate(MODEL_CANDIDATES):
        rows.append(
            {
                "candidate_id": candidate,
                "population": "three_way_common",
                "scope": "pooled",
                "metric": "mae",
                "value": 2.0 + candidate_index,
                "numerator": 200.0 + candidate_index,
                "denominator": 100.0,
            }
        )
        rows.append(
            {
                "candidate_id": candidate,
                "population": "three_way_common",
                "scope": "pooled",
                "metric": "wape",
                "value": 0.21 + candidate_index / 100,
                "numerator": 210.0 + candidate_index,
                "denominator": 1000.0,
            }
        )
        for horizon in range(1, 15):
            rows.append(
                {
                    "candidate_id": candidate,
                    "population": "three_way_common",
                    "scope": "horizon",
                    "metric": "mae",
                    "horizon": horizon,
                    "value": 99.0 if candidate_index == 2 and horizon == 10 else 10.0 + horizon,
                    "numerator": 100.0 + horizon,
                    "denominator": 20.0,
                }
            )
        for window_index, window in enumerate(("validation_1", "validation_2", "validation_3")):
            rows.append(
                {
                    "candidate_id": candidate,
                    "population": "standalone",
                    "scope": "validation_window",
                    "validation_window": window,
                    "metric": MODEL_COVERAGE_METRIC,
                    "value": 0.5 + window_index / 10,
                    "numerator": 5.0 + window_index,
                    "denominator": 10.0,
                }
            )
    return rows


def _inventory_comparison_rows(case_id: str) -> list[dict]:
    rows = []
    for index, metric in enumerate(INVENTORY_METRICS):
        baseline = 100.0 + index
        forecast = 120.0 + index
        rows.append(
            {
                "case_id": case_id,
                "metric": metric,
                "requested_store_count": 2,
                "baseline_standalone_store_count": 2,
                "forecast_standalone_store_count": 2,
                "matched_store_count": 1,
                "baseline_numerator": baseline * 10,
                "baseline_denominator": 10.0,
                "forecast_numerator": forecast * 10,
                "forecast_denominator": 10.0,
                "baseline_value": baseline,
                "forecast_value": forecast,
                "forecast_minus_baseline": 20.0,
                "forecast_minus_baseline_relative": 0.2,
                "relative_difference_null_reason": None,
                "null_reason": None,
                "interpretation": f"fixture {metric} interpretation",
            }
        )
    return rows


def _write_inventory_parquets(fixtures: FixtureStore, case_id: str) -> None:
    shared = {
        "case_id": case_id,
        "scenario_id": "fixture-scenario",
        "Store": 1,
        "forecast_origin": date(2015, 6, 5),
        "family": "synthetic_base",
        "mode": "synthetic",
        "replicate": 0,
        "sensitivity_variant": "reference",
    }
    summaries = []
    targets = []
    for index, policy_id in enumerate(INVENTORY_POLICY_IDS):
        summary = {field.name: _sample_arrow_value(field) for field in POLICY_SUMMARY_SCHEMA}
        summary.update(
            {
                **shared,
                "policy_id": policy_id,
                "episode_status": "complete",
                "episode_complete": True,
                "target_available": True,
                "availability_reason": None,
                "valid_matched_comparison": True,
                "historical_open_assumption_violation": False,
                "SimulatedHoldingPlusShortfallCost": 100.0 + index * 20.0,
                "demand_total": 500.0,
                "fulfilled_total": 450.0,
                "unmet_total": 50.0,
            }
        )
        target = {field.name: _sample_arrow_value(field) for field in POLICY_TARGET_SCHEMA}
        target.update(
            {
                **shared,
                "policy_id": policy_id,
                "target_available": True,
                "availability_reason": None,
                "target_value": 0.0 if index == 0 else 50.0,
                "synthetic": True,
                "calibration_transport_valid": False,
                "schedule_assumption": "planned_synthetic_schedule",
            }
        )
        summaries.append(summary)
        targets.append(target)
    for selector, schema, rows in (
        (ArtifactSelector.PHASE10_POLICY_SUMMARY, POLICY_SUMMARY_SCHEMA, summaries),
        (ArtifactSelector.PHASE10_POLICY_TARGETS, POLICY_TARGET_SCHEMA, targets),
    ):
        pq.write_table(
            pa.Table.from_pylist(rows, schema=schema), _artifact_path(fixtures, selector)
        )
        fixtures.refresh_output(selector)


class _ReaderSpy:
    def __init__(self, reader: _ArtifactReader) -> None:
        self.reader = reader
        self.selectors: list[ArtifactSelector] = []

    def read(self, selector: ArtifactSelector):
        self.selectors.append(selector)
        return self.reader.read(selector)

    def read_model_comparison(self, query: ModelComparisonQuery):
        self.selectors.append(ArtifactSelector.PHASE7_MODEL_COMPARISON)
        return self.reader.read_model_comparison(query)

    def read_inventory_comparison(self, query: InventoryComparisonQuery):
        self.selectors.append(ArtifactSelector.PHASE10_COMPARISON)
        return self.reader.read_inventory_comparison(query)

    def read_inventory_artifact(self, selector: ArtifactSelector, query: InventoryComparisonQuery):
        self.selectors.append(selector)
        return self.reader.read_inventory_artifact(selector, query)

    def inspect_readiness(self):
        return self.reader.inspect_readiness()


class _ModelServiceAdapter:
    def __init__(self, services: ApplicationServices) -> None:
        self.services = services

    def catalog(self) -> ApplicationCatalog:
        return _catalog(case_ids=())

    def model_comparison(self, query: ModelComparisonQuery):
        return self.services.model_comparison(query)


def test_real_services_model_screen_reads_only_bounded_saved_comparison_fixtures(tmp_path) -> None:
    fixtures = FixtureStore(tmp_path)
    selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    _write_csv_rows(fixtures, selector, _model_fixture_rows())
    path = _artifact_path(fixtures, selector)
    before = path.read_bytes()
    reader = _ReaderSpy(fixtures.reader())
    services = _ModelServiceAdapter(ApplicationServices(reader))
    app = _apply(_app(services, "Model Comparison"))

    visible = _visible_text(app)
    assert not app.exception
    assert "99.0" in visible
    assert all(candidate in visible for candidate in MODEL_CANDIDATES)
    assert set(reader.selectors) == {ArtifactSelector.PHASE7_MODEL_COMPARISON}
    assert reader.selectors.count(ArtifactSelector.PHASE7_MODEL_COMPARISON) <= 4
    assert path.read_bytes() == before


def test_real_services_inventory_screen_reads_aggregates_and_selected_policy_pair_only(
    tmp_path,
) -> None:
    fixtures = FixtureStore(tmp_path)
    case_id = "fixture-case"
    _write_csv_rows(
        fixtures,
        ArtifactSelector.PHASE10_COMPARISON,
        _inventory_comparison_rows(case_id),
    )
    _write_inventory_parquets(fixtures, case_id)
    selectors = (
        ArtifactSelector.PHASE9_SCENARIO_CATALOG,
        ArtifactSelector.PHASE10_COMPARISON,
        ArtifactSelector.PHASE10_POLICY_SUMMARY,
        ArtifactSelector.PHASE10_POLICY_TARGETS,
    )
    before = {selector: _artifact_path(fixtures, selector).read_bytes() for selector in selectors}
    reader = _ReaderSpy(fixtures.reader())
    services = ApplicationServices(reader)
    app = _apply(_app(services, "Inventory Comparison"))

    visible = _visible_text(app)
    assert not app.exception
    assert "Whole saved case — all matched Stores" in visible
    assert "Selected Store — saved policy pair" in visible
    assert "fixture-case" in visible
    assert "0.0" in visible
    assert (
        len(next(element.value for element in app.dataframe if "metric" in element.value.columns))
        == 10
    )
    assert set(reader.selectors).issubset(set(selectors))
    assert ArtifactSelector.PHASE10_POLICY_SUMMARY in reader.selectors
    assert ArtifactSelector.PHASE10_POLICY_TARGETS in reader.selectors
    assert before == {
        selector: _artifact_path(fixtures, selector).read_bytes() for selector in selectors
    }
