"""Typed read-only service tests over temporary controlled-synthetic releases."""

from __future__ import annotations

import builtins
import hashlib
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from rossmann_forecasting.app import demo_bundle
from rossmann_forecasting.app.contracts import (
    ForecastQuery,
    HistoryQuery,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.demo_provider import DemoInvalidRequestError, DemoProfile
from rossmann_forecasting.app.demo_services import DemoServices, DemoViewState


@pytest.fixture(scope="module")
def release_bytes() -> tuple[bytes, bytes]:
    return demo_bundle.generate_release_bytes(Path.cwd())


@pytest.fixture
def demo_services(tmp_path: Path, release_bytes: tuple[bytes, bytes]) -> tuple[DemoServices, Path]:
    repository = tmp_path / "fixture-repository"
    release_dir = repository / "artifacts" / "public_demo" / demo_bundle.RELEASE_ID
    release_dir.mkdir(parents=True)
    bundle_bytes, manifest_bytes = release_bytes
    (release_dir / demo_bundle.BUNDLE_FILENAME).write_bytes(bundle_bytes)
    (release_dir / demo_bundle.MANIFEST_FILENAME).write_bytes(manifest_bytes)
    services = DemoServices.open(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        repository_root=repository,
    )
    return services, release_dir


def test_catalog_exposes_fixed_synthetic_population_and_view_availability(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    catalog = services.catalog()

    assert catalog.bundle_ready is True
    assert catalog.supported_store_ids == (101, 202, 303)
    assert catalog.forecast_origins == ("2015-05-22", "2015-06-05", "2015-06-19")
    assert [(pair.fit_id, pair.forecast_origin) for pair in catalog.fit_pairings] == [
        ("demo_fit_a", "2015-06-05"),
        ("demo_fit_b", "2015-06-19"),
    ]
    assert len(catalog.views) == 6
    assert catalog.provenance.evidence_kind == "controlled_synthetic_demo"
    assert catalog.provenance.view_id == "catalog"
    assert catalog.provenance.selected_rows == 1
    assert catalog.source_declaration.model_execution == "none"


def test_services_cannot_be_constructed_without_the_verified_factory() -> None:
    with pytest.raises(TypeError, match="DemoServices.open"):
        DemoServices()


def test_history_preserves_sparse_dates_zero_and_null(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    history = services.sales_history(HistoryQuery(101, date(2015, 5, 9), date(2015, 7, 3)))
    by_date = {row.date: row for row in history.rows}

    assert history.state is DemoViewState.AVAILABLE
    assert [row.date for row in history.rows] == sorted(row.date for row in history.rows)
    assert by_date["2015-05-09"].sales_value == 11062
    assert by_date["2015-05-23"].sales_value == 0
    assert "2015-05-22" not in by_date
    null_history = services.sales_history(HistoryQuery(202, date(2015, 6, 1), date(2015, 6, 1)))
    assert len(null_history.rows) == 1
    assert null_history.rows[0].sales_value is None


def test_history_rejects_out_of_allowlist_and_oversized_ranges(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    for query in (
        HistoryQuery(404, date(2015, 5, 9), date(2015, 5, 9)),
        HistoryQuery(101, date(2015, 5, 8), date(2015, 5, 9)),
        HistoryQuery(101, date(2015, 5, 9), date(2015, 7, 4)),
        HistoryQuery(101, date(2015, 7, 3), date(2015, 5, 9)),
    ):
        with pytest.raises(DemoInvalidRequestError):
            services.sales_history(query)


def test_forecast_returns_both_saved_paths_and_unknown_eligibility(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    ordinary = services.forecast_issuance(ForecastQuery(101, date(2015, 5, 22)))
    assert len(ordinary.points) == 14
    assert ordinary.points[0].horizon == 1
    assert ordinary.points[0].raw_forecast_value == 11358
    assert ordinary.points[0].operational_forecast_value == 11358
    assert ordinary.points[-1].horizon == 14
    assert ordinary.model_execution == "none"

    unknown = services.forecast_issuance(ForecastQuery(303, date(2015, 6, 19)))
    point = unknown.points[3]
    assert point.horizon == 4
    assert point.raw_forecast_value == 13686
    assert point.raw_forecast_available is True
    assert point.synthetic_open_eligibility == "unknown"
    assert point.operational_forecast_value is None
    assert point.operational_forecast_available is False


def test_forecast_rejects_unapproved_origins_and_stores(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    for query in (
        ForecastQuery(404, date(2015, 5, 22)),
        ForecastQuery(101, date(2015, 5, 23)),
    ):
        with pytest.raises(DemoInvalidRequestError):
            services.forecast_issuance(query)


def test_uncertainty_preserves_saved_and_unavailable_values(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    result = services.forecast_uncertainty(UncertaintyQuery(303, date(2015, 6, 19), "demo_fit_b"))

    assert result.state == "available"
    assert len(result.daily_intervals) == 28
    assert {row.probability for row in result.cumulative_uncertainty[:3]} == {
        0.9,
        0.95,
        0.98,
    }
    unavailable_daily = next(
        row
        for row in result.daily_intervals
        if row.horizon == 4 and row.interval_kind == "operational"
    )
    assert unavailable_daily.available is False
    assert unavailable_daily.lower is None
    assert unavailable_daily.unavailable_reason == "synthetic_future_eligibility_unknown"
    unavailable_cumulative = next(
        row
        for row in result.cumulative_uncertainty
        if row.prefix_days == 4 and row.probability == 0.9
    )
    assert unavailable_cumulative.issued_prefix_complete is False
    assert unavailable_cumulative.demand_value is None
    assert result.provenance.selected_rows == 70


def test_uncertainty_rejects_unmatched_fit_pairings(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    with pytest.raises(DemoInvalidRequestError):
        services.forecast_uncertainty(UncertaintyQuery(101, date(2015, 6, 5), "demo_fit_b"))


def test_model_comparison_filters_saved_rows_and_keeps_null_metrics(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    pooled = services.model_comparison(
        ModelComparisonQuery(candidate_id="demo_path_a", scope="pooled", metric="mae", limit=500)
    )
    assert len(pooled.rows) == 1
    assert pooled.rows[0].value == 278.9423076923077
    assert pooled.rows[0].population == "synthetic_open_label_rows"
    assert pooled.provenance.evidence_kind == "controlled_synthetic_demo"

    unavailable = services.model_comparison(
        ModelComparisonQuery(candidate_id="demo_path_a", scope="horizon", horizon=2, metric="mae")
    )
    assert len(unavailable.rows) == 1
    assert unavailable.rows[0].value is None
    assert unavailable.rows[0].unavailable_reason is not None


def test_model_comparison_enforces_closed_filters_and_row_limit(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    all_rows = services.model_comparison(ModelComparisonQuery(limit=500))
    assert len(all_rows.rows) == 69
    for query in (
        ModelComparisonQuery(candidate_id="canonical_lightgbm"),
        ModelComparisonQuery(horizon=15),
        ModelComparisonQuery(store_id=404),
        ModelComparisonQuery(limit=501),
        ModelComparisonQuery(limit=1),
    ):
        with pytest.raises(DemoInvalidRequestError):
            services.model_comparison(query)


def test_inventory_filter_keeps_case_aggregates_and_saved_unavailability(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    reference = services.inventory_comparison(
        InventoryComparisonQuery("synthetic_demo_reference_20150605", store_id=101)
    )
    assert len(reference.policy_pairs) == 1
    assert reference.policy_pairs[0].forecast_minus_baseline_cost == -30
    assert len(reference.case_level_comparisons) == 10
    assert reference.aggregate_scope == "all_stores_in_case"
    assert reference.case_level_comparisons[0].requested_store_count == 3

    adverse = services.inventory_comparison(
        InventoryComparisonQuery("synthetic_demo_adverse_20150605", store_id=303)
    )
    assert len(adverse.policy_pairs) == 1
    assert adverse.policy_pairs[0].comparable is False
    assert adverse.policy_pairs[0].forecast_minus_baseline_cost is None
    assert adverse.policy_pairs[0].forecast.availability_reason == (
        "synthetic_fixture_input_unavailable"
    )
    assert adverse.case_level_comparisons[0].forecast_minus_baseline is None
    assert adverse.case_level_comparisons[0].matched_store_count == 2


def test_inventory_rejects_unknown_case_or_store(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    for query in (
        InventoryComparisonQuery("phase10_case"),
        InventoryComparisonQuery("synthetic_demo_reference_20150605", store_id=404),
    ):
        with pytest.raises(DemoInvalidRequestError):
            services.inventory_comparison(query)


def test_queries_use_the_verified_snapshot_after_release_files_disappear(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, release_dir = demo_services
    import shutil

    shutil.rmtree(release_dir)
    history = services.sales_history(HistoryQuery(101, date(2015, 5, 9), date(2015, 5, 9)))
    assert history.rows[0].sales_value == 11062
    assert services.catalog().bundle_ready is True


def test_all_six_responses_have_consistent_synthetic_provenance(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services
    responses = (
        services.catalog(),
        services.sales_history(HistoryQuery(101, date(2015, 5, 9), date(2015, 5, 9))),
        services.forecast_issuance(ForecastQuery(101, date(2015, 5, 22))),
        services.forecast_uncertainty(UncertaintyQuery(101, date(2015, 6, 5), "demo_fit_a")),
        services.model_comparison(ModelComparisonQuery(candidate_id="demo_path_a")),
        services.inventory_comparison(
            InventoryComparisonQuery("synthetic_demo_reference_20150605")
        ),
    )
    provenance = tuple(response.provenance for response in responses)

    assert [item.view_id for item in provenance] == [
        "catalog",
        "sales_history",
        "forecast_issuance",
        "forecast_uncertainty",
        "model_comparison",
        "inventory_comparison",
    ]
    assert all(item.release_id == demo_bundle.RELEASE_ID for item in provenance)
    assert all(item.evidence_kind == "controlled_synthetic_demo" for item in provenance)
    assert all(item.schema_version == "1.0.0" for item in provenance)
    assert all(item.source_kind == "authored_fixture_arithmetic" for item in provenance)
    assert all(len(item.bundle_sha256) == len(item.manifest_sha256) == 64 for item in provenance)
    assert all(item.selected_rows >= 0 for item in provenance)


def test_service_queries_have_no_filesystem_or_network_side_effects(
    demo_services: tuple[DemoServices, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    services, _ = demo_services

    catalog = services.catalog()
    with pytest.raises(FrozenInstanceError):
        catalog.bundle_ready = False  # type: ignore[misc]

    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("A service query attempted an external side effect.")

    monkeypatch.setattr(builtins, "open", blocked)
    monkeypatch.setattr(Path, "open", blocked)
    monkeypatch.setattr(Path, "read_bytes", blocked)
    monkeypatch.setattr(Path, "read_text", blocked)
    monkeypatch.setattr(Path, "write_bytes", blocked)
    monkeypatch.setattr(Path, "write_text", blocked)
    monkeypatch.setattr(Path, "mkdir", blocked)
    monkeypatch.setattr(Path, "unlink", blocked)
    monkeypatch.setattr(os, "open", blocked)
    monkeypatch.setattr(os, "mkdir", blocked)
    monkeypatch.setattr(os, "remove", blocked)
    monkeypatch.setattr(os, "rename", blocked)
    monkeypatch.setattr(os, "replace", blocked)
    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)

    services.catalog()
    services.sales_history(HistoryQuery(101, date(2015, 5, 9), date(2015, 5, 9)))
    services.forecast_issuance(ForecastQuery(101, date(2015, 5, 22)))
    services.forecast_uncertainty(UncertaintyQuery(101, date(2015, 6, 5), "demo_fit_a"))
    services.model_comparison(ModelComparisonQuery(candidate_id="demo_path_a"))
    services.inventory_comparison(InventoryComparisonQuery("synthetic_demo_reference_20150605"))


def test_concurrent_reads_return_stable_immutable_results(
    demo_services: tuple[DemoServices, Path],
) -> None:
    services, _ = demo_services

    def read_representative_values(_: int) -> tuple[int | None, int | None, int | None]:
        history = services.sales_history(HistoryQuery(101, date(2015, 5, 9), date(2015, 5, 9)))
        forecast = services.forecast_issuance(ForecastQuery(101, date(2015, 5, 22)))
        comparison = services.inventory_comparison(
            InventoryComparisonQuery("synthetic_demo_reference_20150605", store_id=101)
        )
        return (
            history.rows[0].sales_value,
            forecast.points[0].raw_forecast_value,
            comparison.policy_pairs[0].forecast_minus_baseline_cost,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = tuple(executor.map(read_representative_values, range(32)))

    assert results == ((11062, 11358, -30),) * 32
