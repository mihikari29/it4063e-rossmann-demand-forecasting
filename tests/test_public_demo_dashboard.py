"""Offline AppTest coverage for the isolated controlled-synthetic Streamlit dashboard."""

from __future__ import annotations

import hashlib
import importlib
import math
import socket
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib
import pytest
from streamlit.testing.v1 import AppTest

matplotlib.use("Agg", force=True)

from rossmann_forecasting.app import demo_bundle
from rossmann_forecasting.app.contracts import (
    ForecastQuery,
    HistoryQuery,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.demo_provider import DemoProfile
from rossmann_forecasting.app.demo_services import DemoServices

_LABEL = "CONTROLLED SYNTHETIC DEMONSTRATION — NOT OBSERVED ROSSMANN DATA"


# AppTest executes this helper in an isolated script namespace, so its injected
# arguments must not depend on annotations imported from this test module.
def _dashboard_app(services) -> None:
    from rossmann_forecasting.app.demo_dashboard import run_demo_dashboard

    run_demo_dashboard(services)


def _entrypoint_app() -> None:
    from demo_streamlit_app import main

    main()


def _app(services: DemoServices, page: str | None = None) -> AppTest:
    app = AppTest.from_function(_dashboard_app, kwargs={"services": services}).run()
    assert not app.exception
    if page is not None:
        app.sidebar.radio[0].set_value(page).run()
    return app


def _visible(app: AppTest) -> str:
    parts = []
    for name in (
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
    ):
        for element in getattr(app, name, ()):
            if hasattr(element, "value"):
                parts.append(str(element.value))
    for element in app.dataframe:
        value = getattr(element, "value", None)
        if hasattr(value, "to_string"):
            parts.append(value.to_string(index=False))
        else:
            parts.append(str(value))
    return "\n".join(parts)


def _frame_records(element: Any) -> list[dict[str, Any]]:
    value = element.value
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    return list(value)


def _set_key(app: AppTest, collection_name: str, key: str, value: Any) -> None:
    collection = getattr(app, collection_name)
    item = next(element for element in collection if element.key == key)
    item.set_value(value).run()


@pytest.fixture(scope="module")
def release_bytes() -> tuple[bytes, bytes]:
    return demo_bundle.generate_release_bytes(Path.cwd())


def test_dashboard_fixture_preserves_the_reviewed_synthetic_bundle_bytes(
    release_bytes: tuple[bytes, bytes],
) -> None:
    bundle, _manifest = release_bytes
    assert len(bundle) == 326074
    assert hashlib.sha256(bundle).hexdigest() == (
        "9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb"
    )


@pytest.fixture
def release_repository(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> tuple[Path, str, Path]:
    repository = tmp_path / "synthetic-demo-repository"
    release_dir = repository / "artifacts" / "public_demo" / demo_bundle.RELEASE_ID
    release_dir.mkdir(parents=True)
    bundle, manifest = release_bytes
    bundle_path = release_dir / demo_bundle.BUNDLE_FILENAME
    bundle_path.write_bytes(bundle)
    (release_dir / demo_bundle.MANIFEST_FILENAME).write_bytes(manifest)
    return repository, hashlib.sha256(manifest).hexdigest(), bundle_path


@pytest.fixture
def services(release_repository: tuple[Path, str, Path]) -> DemoServices:
    repository, pin, _ = release_repository
    return DemoServices.open(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=repository,
    )


def _redirect_open(monkeypatch: pytest.MonkeyPatch, repository: Path) -> list[tuple[Any, ...]]:
    original = DemoServices.open.__func__
    calls: list[tuple[Any, ...]] = []

    def open_fixture(cls, **kwargs):
        calls.append((kwargs["profile"], kwargs["expected_manifest_sha256"]))
        kwargs["repository_root"] = repository
        return original(cls, **kwargs)

    monkeypatch.setattr(DemoServices, "open", classmethod(open_fixture))
    return calls


def _set_demo_environment(
    monkeypatch: pytest.MonkeyPatch, pin: str, profile: str = "controlled_synthetic_demo"
) -> None:
    monkeypatch.setenv("ROSSMANN_DEMO_PROFILE", profile)
    monkeypatch.setenv("ROSSMANN_DEMO_MANIFEST_SHA256", pin)


def test_overview_displays_verified_catalog_all_views_and_machine_readable_provenance(
    services: DemoServices,
) -> None:
    app = _app(services, "Overview & Evidence")
    text = _visible(app)

    assert not app.exception
    assert _LABEL in text
    assert "rossmann-course-demo-synthetic-v1" in text
    assert "controlled_synthetic_demo" in text
    assert "101, 202, 303" in text
    assert "2015-05-22" in text and "2015-06-05" in text and "2015-06-19" in text
    assert "demo_fit_a / 2015-06-05" in text and "demo_fit_b / 2015-06-19" in text
    for view_id in (
        "catalog",
        "sales_history",
        "forecast_issuance",
        "forecast_uncertainty",
        "model_comparison",
        "inventory_comparison",
    ):
        assert view_id in text
    assert "rossmann_data_included" in text and "False" in text
    assert "bundle_ready" in text and "page_render_state" in text
    assert "manifest_sha256" in text and "selected_rows" in text
    assert "Frozen LightGBM winner" not in text
    assert "empirical calibration" not in text.lower()


@pytest.mark.parametrize("store_id", [101, 202, 303])
def test_history_controls_show_saved_rows_and_provenance_for_each_store(
    services: DemoServices, store_id: int
) -> None:
    app = _app(services, "Historical Sales")
    _set_key(app, "selectbox", "demo_history_store", store_id)
    text = _visible(app)

    assert not app.exception
    assert _LABEL in text
    assert f"Store {store_id}" in text
    assert "Saved synthetic Sales values" in text
    assert "sales_value" in text and "synthetic_open" in text
    assert "view_id" in text and "sales_history" in text
    rows = _frame_records(app.dataframe[0])
    assert rows
    assert all(row["store_id"] == store_id for row in rows)
    assert len(rows) <= 56
    assert [row["date"] for row in rows] == sorted(row["date"] for row in rows)
    if store_id == 101:
        by_date = {row["date"]: row for row in rows}
        assert "2015-05-22" not in by_date
        assert by_date["2015-05-23"]["sales_value"] == 0
    elif store_id == 202:
        june_first = next(row for row in rows if row["date"] == "2015-06-01")
        assert math.isnan(june_first["sales_value"])
        assert june_first["sales_value_display"] == "Null (saved value unavailable)"
        assert june_first["synthetic_open"] == "Open"
    else:
        unknown_open = next(row for row in rows if row["date"] == "2015-06-13")
        assert math.isnan(unknown_open["sales_value"])
        assert unknown_open["sales_value_display"] == "Null (saved value unavailable)"
        assert unknown_open["synthetic_open"] == "Unknown"


def test_history_empty_range_is_not_fabricated_and_reversed_dates_are_rejected(
    services: DemoServices,
) -> None:
    app = _app(services, "Historical Sales")
    _set_key(app, "date_input", "demo_history_start", date(2015, 5, 22))
    _set_key(app, "date_input", "demo_history_end", date(2015, 5, 22))
    assert not app.exception
    assert "No saved synthetic rows match" in _visible(app)
    assert len(app.dataframe) == 1  # provenance remains visible for a valid empty query

    reversed_app = _app(services, "Historical Sales")
    _set_key(reversed_app, "date_input", "demo_history_start", date(2015, 6, 1))
    _set_key(reversed_app, "date_input", "demo_history_end", date(2015, 5, 31))
    assert not reversed_app.exception
    assert "Choose a start date" in _visible(reversed_app)
    assert not reversed_app.dataframe


@pytest.mark.parametrize("origin", ["2015-05-22", "2015-06-05", "2015-06-19"])
def test_forecast_screen_uses_all_saved_origins_and_horizons(
    services: DemoServices, origin: str
) -> None:
    app = _app(services, "Forecast Explorer and Uncertainty")
    _set_key(app, "selectbox", "demo_forecast_origin", origin)
    text = _visible(app)

    assert not app.exception
    assert _LABEL in text
    assert origin in text
    assert "model_execution" in text and "trajectory_id" in text
    forecast_rows = _frame_records(app.dataframe[0])
    assert len(forecast_rows) == 14
    assert [row["horizon"] for row in forecast_rows] == list(range(1, 15))
    assert all(row["model_execution"] == "none" for row in forecast_rows)
    if origin == "2015-05-22":
        assert "No approved synthetic uncertainty view exists" in text
        assert len(app.dataframe) == 2  # forecast plus its provenance only
    else:
        assert "demo_fit_a" in text if origin == "2015-06-05" else "demo_fit_b" in text
        assert "probability" in text and "schedule_assumption_flag" in text
        assert "cumulative_uncertainty" in text or "prefix_days" in text


def test_forecast_unknown_open_and_incomplete_saved_uncertainty_remain_unavailable(
    services: DemoServices,
) -> None:
    app = _app(services, "Forecast Explorer and Uncertainty")
    _set_key(app, "selectbox", "demo_forecast_store", 303)
    _set_key(app, "selectbox", "demo_forecast_origin", "2015-06-19")
    text = _visible(app)

    assert not app.exception
    forecast_rows = _frame_records(app.dataframe[0])
    known_closed = next(row for row in forecast_rows if row["horizon"] == 2)
    assert known_closed["raw_forecast_value"] == 14718
    assert known_closed["synthetic_open_eligibility"] == "known_closed"
    assert known_closed["operational_forecast_value"] == 0
    assert known_closed["operational_forecast_available"] is True
    fourth = next(row for row in forecast_rows if row["horizon"] == 4)
    assert fourth["raw_forecast_value"] == 13686
    assert fourth["raw_forecast_available"] is True
    assert fourth["synthetic_open_eligibility"] == "unknown"
    assert math.isnan(fourth["operational_forecast_value"])
    assert fourth["operational_forecast_display"] == "Unavailable (saved null)"
    assert fourth["operational_forecast_available"] is False
    cumulative = next(
        frame for frame in app.dataframe if "issued_prefix_complete" in _frame_records(frame)[0]
    )
    assert any(row["issued_prefix_complete"] is False for row in _frame_records(cumulative))
    assert "0.9" in text or "0.90" in text
    assert "unavailable_reason" in text


def test_forecast_empty_horizon_selection_is_explicit(services: DemoServices) -> None:
    app = _app(services, "Forecast Explorer and Uncertainty")
    _set_key(app, "multiselect", "demo_forecast_horizons", [])
    assert not app.exception
    assert "Select one or more horizons" in _visible(app)
    assert len(app.dataframe) == 1  # issuance provenance only; no forecast rows are fabricated


def test_may_22_does_not_query_a_different_uncertainty_pairing(
    services: DemoServices, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    original = DemoServices.forecast_uncertainty

    def counted(self, query):
        nonlocal calls
        calls += 1
        return original(self, query)

    monkeypatch.setattr(DemoServices, "forecast_uncertainty", counted)
    app = _app(services, "Forecast Explorer and Uncertainty")
    assert not app.exception
    assert "No approved synthetic uncertainty view exists" in _visible(app)
    assert calls == 0


def test_model_comparison_uses_saved_rows_and_valid_empty_intersections(
    services: DemoServices,
) -> None:
    app = _app(services, "Model Comparison")
    text = _visible(app)
    assert not app.exception
    assert _LABEL in text
    assert "demo_path_a" in text and "demo_path_b" in text and "demo_path_c" in text
    assert "Synthetic fixed path A" in text
    rows = _frame_records(app.dataframe[0])
    assert len(rows) == 69
    known = next(
        row
        for row in rows
        if row["candidate_id"] == "demo_path_a"
        and row["scope"] == "pooled"
        and row["metric"] == "mae"
    )
    assert known["value"] == pytest.approx(278.9423076923077)
    assert known["numerator"] == 29010
    assert known["denominator"] == 104.0
    assert "canonical_lightgbm" not in text and "Winner" not in text

    empty_app = _app(services, "Model Comparison")
    _set_key(empty_app, "selectbox", "demo_comparison_candidate", "demo_path_a")
    _set_key(empty_app, "selectbox", "demo_comparison_scope", "horizon")
    _set_key(empty_app, "selectbox", "demo_comparison_metric", "mape")
    assert not empty_app.exception
    assert "No saved comparison rows match" in _visible(empty_app)


def test_comparison_row_limit_is_bounded_and_over_limit_results_are_sanitized(
    services: DemoServices,
) -> None:
    app = _app(services, "Model Comparison")
    _set_key(app, "number_input", "demo_comparison_limit", 500)
    assert not app.exception
    assert len(_frame_records(app.dataframe[0])) == 69
    _set_key(app, "number_input", "demo_comparison_limit", 1)
    assert not app.exception
    text = _visible(app)
    assert "outside the supported release options" in text
    assert "Traceback" not in text


@pytest.mark.parametrize("store_id,expected_delta", [(101, -30), (202, -40), (303, -50)])
def test_inventory_filter_changes_only_policy_detail_and_keeps_signed_values(
    services: DemoServices, store_id: int, expected_delta: int
) -> None:
    app = _app(services, "Inventory Comparison")
    _set_key(app, "selectbox", "demo_inventory_store", store_id)
    text = _visible(app)
    assert not app.exception
    assert _LABEL in text
    assert "All Stores in the selected synthetic case" in text
    assert "Selected Store policy detail" in text
    aggregates = _frame_records(app.dataframe[0])
    detail = _frame_records(app.dataframe[1])
    assert len(aggregates) == 10
    assert len(detail) == 1 and detail[0]["store_id"] == store_id
    assert detail[0]["forecast_minus_baseline_cost"] == expected_delta
    filtered_result = services.inventory_comparison(
        InventoryComparisonQuery("synthetic_demo_reference_20150605", store_id=store_id)
    )
    unfiltered_result = services.inventory_comparison(
        InventoryComparisonQuery("synthetic_demo_reference_20150605")
    )
    assert filtered_result.case_level_comparisons == unfiltered_result.case_level_comparisons
    assert [
        (row.metric, row.baseline_denominator, row.forecast_denominator)
        for row in filtered_result.case_level_comparisons
    ] == [
        (row.metric, row.baseline_denominator, row.forecast_denominator)
        for row in unfiltered_result.case_level_comparisons
    ]

    adverse = _app(services, "Inventory Comparison")
    _set_key(adverse, "selectbox", "demo_inventory_case", "synthetic_demo_adverse_20150605")
    _set_key(adverse, "selectbox", "demo_inventory_store", 303)
    adverse_text = _visible(adverse)
    assert not adverse.exception
    adverse_detail = _frame_records(adverse.dataframe[1])
    assert len(adverse_detail) == 1
    assert adverse_detail[0]["forecast_minus_baseline_cost"] is None
    assert (
        adverse_detail[0]["difference_unavailable_reason"] == "synthetic_fixture_input_unavailable"
    )
    assert "physical stock" not in adverse_text.lower()
    assert "documented savings" in adverse_text.lower()


def test_navigation_does_not_reuse_inventory_or_store_selector_values(
    services: DemoServices,
) -> None:
    app = _app(services, "Inventory Comparison")
    _set_key(app, "selectbox", "demo_inventory_case", "synthetic_demo_adverse_20150605")
    _set_key(app, "selectbox", "demo_inventory_store", 303)
    assert "synthetic_demo_adverse_20150605" in _visible(app)

    app.sidebar.radio[0].set_value("Historical Sales").run()
    history_text = _visible(app)
    assert not app.exception
    assert "Store 303" not in history_text
    assert "Store 101" in history_text
    assert "synthetic_demo_adverse_20150605" not in history_text


def test_verified_service_queries_do_not_reopen_release_files(
    services: DemoServices, monkeypatch: pytest.MonkeyPatch
) -> None:
    import rossmann_forecasting.app.demo_provider as provider_module

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a verified service query must not reopen a release file")

    monkeypatch.setattr(provider_module, "_read_bounded", forbidden)
    assert services.catalog().bundle_ready
    assert services.sales_history(HistoryQuery(101, date(2015, 5, 9), date(2015, 5, 10))).rows
    assert services.forecast_issuance(ForecastQuery(101, date(2015, 5, 22))).points
    assert services.forecast_uncertainty(
        UncertaintyQuery(101, date(2015, 6, 5), "demo_fit_a")
    ).daily_intervals
    assert services.model_comparison(ModelComparisonQuery(limit=500)).rows
    assert services.inventory_comparison(
        InventoryComparisonQuery("synthetic_demo_reference_20150605")
    ).policy_pairs


def test_entrypoint_configuration_failures_are_sanitized_and_never_fall_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rossmann_forecasting.app.services import ApplicationServices

    def forbidden(*_args, **_kwargs):
        raise AssertionError("canonical services must not be constructed")

    monkeypatch.setattr(ApplicationServices, "__init__", forbidden)
    monkeypatch.setattr(DemoServices, "open", forbidden)
    monkeypatch.delenv("ROSSMANN_DEMO_PROFILE", raising=False)
    monkeypatch.delenv("ROSSMANN_DEMO_MANIFEST_SHA256", raising=False)
    app = AppTest.from_function(_entrypoint_app).run()
    assert not app.exception
    assert _LABEL in _visible(app)
    assert "Set the explicit controlled-synthetic profile" in _visible(app)
    assert "ROSSMANN_DEMO_MANIFEST_SHA256" not in _visible(app)


@pytest.mark.parametrize(
    ("profile", "pin", "expected"),
    [
        ("canonical", "a" * 64, "Set the explicit controlled-synthetic profile"),
        ("controlled_synthetic_demo", "A" * 64, "lowercase 64-character"),
    ],
)
def test_invalid_explicit_profile_and_malformed_pin_fail_closed(
    monkeypatch: pytest.MonkeyPatch, profile: str, pin: str, expected: str
) -> None:
    _set_demo_environment(monkeypatch, pin, profile)
    app = AppTest.from_function(_entrypoint_app).run()
    assert not app.exception
    text = _visible(app)
    assert _LABEL in text and expected in text
    assert "Traceback" not in text and "C:\\Users" not in text


@pytest.mark.parametrize("failure", ["missing", "wrong_pin", "tampered"])
def test_missing_wrong_pin_and_tampered_release_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    release_repository: tuple[Path, str, Path],
    failure: str,
) -> None:
    repository, good_pin, bundle_path = release_repository
    _redirect_open(monkeypatch, repository)
    if failure == "missing":
        import shutil

        shutil.rmtree(repository / "artifacts")
        pin = good_pin
        expected_message = "pinned synthetic release is unavailable"
    elif failure == "wrong_pin":
        pin = "0" * 64
        expected_message = "did not pass its configured integrity check"
    else:
        bundle_path.write_bytes(bundle_path.read_bytes() + b"tampered")
        pin = good_pin
        expected_message = "did not pass its configured integrity check"
    _set_demo_environment(monkeypatch, pin)
    app = AppTest.from_function(_entrypoint_app).run()
    text = _visible(app)
    assert not app.exception
    assert _LABEL in text and expected_message in text
    assert str(tmp_path) not in text
    assert "tampered" not in text
    assert "Traceback" not in text


def test_entrypoint_caches_by_session_config_and_clears_old_service_on_change(
    monkeypatch: pytest.MonkeyPatch, release_repository: tuple[Path, str, Path]
) -> None:
    repository, pin, _ = release_repository
    calls = _redirect_open(monkeypatch, repository)
    _set_demo_environment(monkeypatch, pin)
    app = AppTest.from_function(_entrypoint_app).run()
    assert not app.exception
    assert _LABEL in _visible(app)
    assert len(calls) == 1
    app.sidebar.radio[0].set_value("Historical Sales").run()
    assert not app.exception
    assert len(calls) == 1

    monkeypatch.setenv("ROSSMANN_DEMO_MANIFEST_SHA256", "0" * 64)
    app.run()
    text = _visible(app)
    assert not app.exception
    assert "did not pass its configured integrity check" in text
    assert "Saved synthetic Sales values" not in text
    assert len(calls) == 2


def test_importing_entrypoint_does_not_open_or_scan_a_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import demo_streamlit_app

    def forbidden(*_args, **_kwargs):
        raise AssertionError("importing the entrypoint must not construct services")

    monkeypatch.setattr(DemoServices, "open", forbidden)
    importlib.reload(demo_streamlit_app)
    assert callable(demo_streamlit_app.main)


def test_dashboard_does_not_open_network_connections(
    services: DemoServices, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("the synthetic dashboard must remain offline")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    app = _app(services, "Overview & Evidence")
    assert not app.exception
    assert _LABEL in _visible(app)
