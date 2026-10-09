"""Tests for null-safe dashboard-only display conversions."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.app.contracts import (
    ArtifactErrorCode,
    ArtifactIntegrityError,
    ArtifactSchemaError,
    ArtifactSelector,
    ArtifactUnavailableError,
    DuplicateArtifactKeyError,
    InvalidArtifactRequestError,
    UnavailableReason,
    UnsafeArtifactPathError,
    UnsupportedArtifactSelectorError,
)
from rossmann_forecasting.app.dashboard_presenters import (
    catalog_provenance_records,
    cumulative_table_records,
    display_scalar,
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
    ArtifactProvenance,
    CumulativeUncertainty,
    DailyInterval,
    ForecastPoint,
    ResourceStatus,
    SalesHistoryRow,
)


def _catalog(
    *,
    scenario_provenance: ArtifactProvenance | None = None,
    inventory_provenance: ArtifactProvenance | None = None,
) -> ApplicationCatalog:
    return ApplicationCatalog(
        phases=("phase7", "phase8", "phase9", "phase10"),
        selectors=(),
        supported_store_ids=(),
        phase7_forecast_origins=(),
        phase8_fits=(),
        scenario_catalog_state="unavailable",
        scenarios=(),
        inventory_case_state="empty",
        inventory_case_ids=(),
        resources=(),
        scenario_provenance=scenario_provenance,
        inventory_case_provenance=inventory_provenance,
    )


def test_display_scalar_preserves_null_zero_false_and_safe_dates() -> None:
    assert display_scalar(None) is None
    assert display_scalar(pd.NA) is None
    assert display_scalar(pd.NaT) is None
    assert display_scalar(0) == 0
    assert display_scalar(np.int64(0)) == 0
    assert display_scalar(False) is False
    assert display_scalar(date(2015, 7, 3)) == "2015-07-03"
    assert display_scalar(datetime(2015, 7, 3, tzinfo=UTC)) == "2015-07-03T00:00:00+00:00"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_display_scalar_rejects_non_finite_numbers(value: float) -> None:
    with pytest.raises(ValueError, match="non-finite"):
        display_scalar(value)


def test_resource_status_keeps_readiness_levels_and_hides_unvalidated_hash() -> None:
    resources = (
        ResourceStatus(
            selector="phase7_forecasts",
            phase="phase7",
            run_id="run-a",
            manifest_sha256="expected-hash",
            validation_level="present",
            output_present=True,
            manifest_validated=False,
            output_hash_verified=False,
            error_code=None,
        ),
        ResourceStatus(
            selector="phase8_daily_intervals",
            phase="phase8",
            run_id="run-b",
            manifest_sha256="verified-manifest-hash",
            validation_level="output_verified",
            output_present=True,
            manifest_validated=True,
            output_hash_verified=True,
            error_code=None,
        ),
        ResourceStatus(
            selector="phase10_policy_summary",
            phase="phase10",
            run_id="run-c",
            manifest_sha256="expected-c",
            validation_level="unavailable",
            output_present=False,
            manifest_validated=False,
            output_hash_verified=False,
            error_code="artifact_unavailable",
        ),
    )

    records = resource_status_records(resources)

    assert [item["validation_level"] for item in records] == [
        "present",
        "output_verified",
        "unavailable",
    ]
    assert records[0]["manifest_sha256"] is None
    assert records[1]["manifest_sha256"] == "verified-manifest-hash"
    assert records[2]["output_present"] is False
    assert records[2]["error_code"] == "artifact_unavailable"


def test_catalog_provenance_only_includes_returned_provenance() -> None:
    provenance = ArtifactProvenance(
        selector="phase9_scenario_catalog",
        phase="phase9",
        run_id="phase9-fixture",
        manifest_sha256="manifest-sha",
        output_sha256="output-sha",
        selected_rows=1,
        manifest_rows=1,
    )

    assert catalog_provenance_records(_catalog()) == []
    assert catalog_provenance_records(_catalog(scenario_provenance=provenance)) == [
        {
            "selector": "phase9_scenario_catalog",
            "phase": "phase9",
            "run_id": "phase9-fixture",
            "manifest_sha256": "manifest-sha",
            "output_sha256": "output-sha",
            "selected_rows": 1,
            "manifest_rows": 1,
        }
    ]


@pytest.mark.parametrize(
    ("error", "expected_code", "expected_message"),
    [
        (
            ArtifactUnavailableError(
                ArtifactSelector.PHASE9_SCENARIO_CATALOG, UnavailableReason.MISSING_ARTIFACT
            ),
            ArtifactErrorCode.UNAVAILABLE.value,
            "A required resource file is missing.",
        ),
        (
            ArtifactIntegrityError(ArtifactSelector.PHASE9_SCENARIO_CATALOG),
            ArtifactErrorCode.INTEGRITY.value,
            "A resource failed its integrity check. Unverified details are hidden.",
        ),
        (
            ArtifactSchemaError(ArtifactSelector.PHASE9_SCENARIO_CATALOG),
            ArtifactErrorCode.SCHEMA.value,
            "A resource does not match its accepted schema. Unverified details are hidden.",
        ),
        (
            DuplicateArtifactKeyError(ArtifactSelector.PHASE9_SCENARIO_CATALOG),
            ArtifactErrorCode.DUPLICATE_KEY.value,
            "A resource contains invalid keys. Unverified details are hidden.",
        ),
        (
            UnsupportedArtifactSelectorError(),
            ArtifactErrorCode.UNSUPPORTED_SELECTOR.value,
            "The requested resource is unsupported.",
        ),
        (
            InvalidArtifactRequestError(ArtifactSelector.PHASE9_SCENARIO_CATALOG),
            ArtifactErrorCode.INVALID_REQUEST.value,
            "The resource request is invalid.",
        ),
        (
            UnsafeArtifactPathError(ArtifactSelector.PHASE9_SCENARIO_CATALOG),
            ArtifactErrorCode.UNSAFE_PATH.value,
            "A resource failed a path-safety check.",
        ),
    ],
)
def test_artifact_error_notices_are_resource_neutral_and_keep_stable_codes(
    error: Exception, expected_code: str, expected_message: str
) -> None:
    notice = error_notice(error)

    assert notice.code == expected_code
    assert notice.message == expected_message
    assert "catalog" not in notice.message.lower()
    assert "C:\\private" not in notice.message


def test_unexpected_error_notice_is_fixed_and_path_free() -> None:
    notice = error_notice(RuntimeError("C:\\private\\root\\manifest.json"))

    assert notice.code == "internal_error"
    assert notice.message == "The request could not be completed. Error details are hidden."
    assert "C:\\private" not in notice.message


def _point(
    horizon: int,
    *,
    raw: float | None = 10.0,
    operational: float | None = 10.0,
    raw_available: bool = True,
    operational_available: bool = True,
    date_text: str | None = None,
) -> ForecastPoint:
    return ForecastPoint(
        date=date_text or (date(2015, 6, 19) + timedelta(days=horizon)).isoformat(),
        horizon=horizon,
        raw_forecast=raw,
        operational_forecast=operational,
        forecast_available=raw_available,
        operational_forecast_available=operational_available,
        candidate_id="candidate-a",
        model_selection_run_id="selection-run-a",
    )


def _interval(
    horizon: int,
    *,
    kind: str = "raw",
    point: float | None = 15.0,
    lower: float | None = 10.0,
    upper: float | None = 20.0,
    available: bool = True,
    reason: str | None = None,
    date_text: str | None = None,
) -> DailyInterval:
    return DailyInterval(
        date=date_text or (date(2015, 6, 19) + timedelta(days=horizon)).isoformat(),
        horizon=horizon,
        interval_kind=kind,
        point_forecast=point,
        lower=lower,
        upper=upper,
        width=None if lower is None or upper is None else upper - lower,
        available=available,
        unavailable_reason=reason,
        units="sales_value",
        schedule_assumption_flag=False,
    )


def _cumulative(
    *,
    k: int = 14,
    p: float = 0.95,
    complete: bool = True,
    reason: str | None = None,
    quantile: float | None = -7.25,
    demand: float | None = 100.0,
) -> CumulativeUncertainty:
    return CumulativeUncertainty(
        prefix_days=k,
        probability=p,
        issued_prefix_complete=complete,
        unavailable_reason=reason,
        demand_value=demand,
        signed_error_quantile=quantile,
        upper_turnover_value=92.75 if demand is not None and quantile is not None else None,
        safety_stock_value=0.0 if demand is not None and quantile is not None else None,
        target_value=100.0 if demand is not None and quantile is not None else None,
        units="sales_value",
        schedule_assumption_flag=True,
    )


def test_history_validation_accepts_inclusive_supported_boundaries() -> None:
    stores = (1, 1115)
    assert validate_history_selection(1, date(2013, 1, 1), date(2013, 1, 1), stores) is None
    assert validate_history_selection(1115, date(2015, 7, 3), date(2015, 7, 3), stores) is None
    assert validate_history_selection(1, date(2014, 7, 3), date(2015, 7, 3), stores) is None


@pytest.mark.parametrize(
    ("store_id", "start", "end"),
    [
        (0, date(2015, 1, 1), date(2015, 1, 1)),
        (1, date(2015, 2, 1), date(2015, 1, 1)),
        (1, date(2014, 7, 2), date(2015, 7, 3)),
        (1, date(2012, 12, 31), date(2013, 1, 1)),
        (1, date(2015, 7, 3), date(2015, 7, 4)),
    ],
)
def test_history_validation_rejects_invalid_store_reversed_oversized_and_cutoff(
    store_id: int, start: date, end: date
) -> None:
    assert validate_history_selection(store_id, start, end, (1, 1115)) is not None


def test_history_chart_keeps_zero_null_unknown_open_and_missing_date_gap() -> None:
    rows = (
        SalesHistoryRow(1, "2015-06-01", 0.0, None),
        SalesHistoryRow(1, "2015-06-03", None, 0.0),
    )

    chart = history_chart_records(rows, date(2015, 6, 1), date(2015, 6, 3))
    source = history_source_records(rows)

    assert [row["Sales"] for row in chart] == [0.0, None, None]
    assert [row["Observed row"] for row in chart] == [True, False, True]
    assert source == [
        {"Date": "2015-06-01", "Sales": 0.0, "Source Open": None},
        {"Date": "2015-06-03", "Sales": None, "Source Open": 0.0},
    ]


def test_forecast_presenters_keep_zero_null_independent_availability_and_sparse_gaps() -> None:
    points = (
        _point(1, raw=0.0, operational=None, raw_available=True, operational_available=False),
        _point(3, raw=None, operational=33.0, raw_available=False, operational_available=True),
    )

    raw_chart = forecast_chart_records(points, date(2015, 6, 19), 7, "raw")
    operational_chart = forecast_chart_records(points, date(2015, 6, 19), 7, "operational")
    table = forecast_table_records(points, 7)

    assert [row["Forecast"] for row in raw_chart[:3]] == [0.0, None, None]
    assert [row["Forecast"] for row in operational_chart[:3]] == [None, None, 33.0]
    assert [row["Horizon"] for row in table] == [1, 3]
    assert table[0]["Raw forecast"] == 0.0
    assert table[0]["Operational forecast"] is None
    assert table[0]["Raw available"] is True
    assert table[0]["Operational available"] is False
    assert forecast_display_counts(points, 7) == {
        "rows": 2,
        "raw_available": 1,
        "operational_available": 1,
    }
    assert forecast_identity(points) == [
        {"Candidate": "candidate-a", "Selection run": "selection-run-a"}
    ]
    assert all("actual" not in str(key).lower() for row in table for key in row)
    assert all("open" not in str(key).lower() for row in table for key in row)


def test_forecast_h7_is_a_display_subset_of_saved_h14() -> None:
    points = tuple(_point(horizon) for horizon in (1, 7, 8, 14))
    assert [row["Horizon"] for row in forecast_table_records(points, 7)] == [1, 7]
    assert [row["Horizon"] for row in forecast_table_records(points, 14)] == [1, 7, 8, 14]


def test_interval_segments_break_at_unavailable_and_absent_horizons() -> None:
    rows = (
        _interval(1),
        _interval(2),
        _interval(3, available=False, lower=None, upper=None, reason="unknown_schedule"),
        _interval(5),
        _interval(6, kind="operational"),
    )

    segments = interval_band_segments(rows, "raw", 14)
    table = interval_table_records(rows, "raw", 14)

    assert [[row["Horizon"] for row in segment] for segment in segments] == [[1, 2], [5]]
    assert [row["Horizon"] for row in table] == [1, 2, 3, 5]
    assert table[2]["Unavailable reason"] == "unknown_schedule"

    all_unavailable = (
        _interval(1, available=False, lower=None, upper=None, reason="no_tail"),
        _interval(2, available=False, lower=None, upper=None, reason="no_tail"),
    )
    assert interval_band_segments(all_unavailable, "raw", 14) == []


def test_interval_table_keeps_point_outside_saved_band_and_operational_identity() -> None:
    rows = (
        _interval(1, point=120.0, lower=10.0, upper=20.0),
        _interval(1, kind="operational", point=0.0, lower=0.0, upper=0.0),
    )
    raw = interval_table_records(rows, "raw", 7)
    operational = interval_table_records(rows, "operational", 7)

    assert raw[0]["Point estimate"] == 120.0
    assert (raw[0]["Lower"], raw[0]["Upper"]) == (10.0, 20.0)
    assert operational[0]["Point estimate"] == 0.0


def test_cumulative_table_preserves_negative_signed_quantile_and_nulls() -> None:
    rows = (
        _cumulative(complete=False, reason="incomplete_prefix", quantile=None, demand=None),
        _cumulative(k=14, p=0.98, complete=True, quantile=None, demand=100.0),
    )
    selected = cumulative_table_records(rows[:1], 14, 0.95)
    complete_null = cumulative_table_records(rows[1:], 14, 0.98)

    assert selected[0]["Prefix complete"] is False
    assert selected[0]["Unavailable reason"] == "incomplete_prefix"
    assert selected[0]["D_k"] is None
    assert complete_null[0]["Prefix complete"] is True
    assert complete_null[0]["Signed q"] is None

    complete = cumulative_table_records((_cumulative(),), 14, 0.95)
    assert complete[0]["Signed q"] == -7.25
    assert complete[0]["D_k"] == 100.0
    assert complete[0]["U_k"] == 92.75
