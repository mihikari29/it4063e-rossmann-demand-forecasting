"""Tests for null-safe dashboard-only display conversions."""

from __future__ import annotations

from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactSchemaError,
    ArtifactSelector,
)
from rossmann_forecasting.app.dashboard_presenters import (
    catalog_provenance_records,
    display_scalar,
    error_notice,
    resource_status_records,
)
from rossmann_forecasting.app.services import (
    ApplicationCatalog,
    ArtifactProvenance,
    ResourceStatus,
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


def test_artifact_error_notices_are_fixed_distinct_and_path_free() -> None:
    integrity = error_notice(ArtifactIntegrityError(ArtifactSelector.PHASE9_SCENARIO_CATALOG))
    schema = error_notice(ArtifactSchemaError(ArtifactSelector.PHASE9_SCENARIO_CATALOG))
    unexpected = error_notice(RuntimeError("C:\\private\\root\\manifest.json"))

    assert integrity.code == "artifact_integrity_error"
    assert schema.code == "artifact_schema_error"
    assert integrity.message != schema.message
    assert integrity.selector == "phase9_scenario_catalog"
    assert unexpected.code == "internal_error"
    assert "C:\\private" not in unexpected.message
