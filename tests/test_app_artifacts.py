"""Fixture tests for read-only canonical artifact and history readers."""

from __future__ import annotations

import csv
import hashlib
import json
import stat
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import rossmann_forecasting.app.artifacts as artifact_module
from rossmann_forecasting.app.artifacts import (
    _ARTIFACTS,
    CANONICAL_RUNS,
    HISTORY_PROJECTION,
    _ArtifactReader,
)
from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactSchemaError,
    ArtifactSelector,
    ArtifactUnavailableError,
    CanonicalRunIdentity,
    DuplicateArtifactKeyError,
    ForecastQuery,
    HistoryQuery,
    InvalidArtifactRequestError,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    Phase,
    UncertaintyQuery,
    UnsafeArtifactPathError,
    UnsupportedArtifactSelectorError,
)
from rossmann_forecasting.inventory.scenarios import CATALOG_SCHEMA
from rossmann_forecasting.inventory.simulation import (
    COMPARISON_SCHEMA,
    POLICY_SUMMARY_SCHEMA,
    POLICY_TARGET_SCHEMA,
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


_PHASE7_FIXTURE_SCHEMA = pa.schema(
    [
        pa.field("Store", pa.int64()),
        pa.field("forecast_origin", pa.timestamp("ns")),
        pa.field("Date", pa.timestamp("ns")),
        pa.field("horizon", pa.int8()),
        pa.field("raw_forecast", pa.float64()),
        pa.field("operational_forecast", pa.float64()),
        pa.field("actual_sales", pa.float64()),
        pa.field("source_open", pa.float64()),
        pa.field("forecast_available", pa.bool_()),
        pa.field("operational_forecast_available", pa.bool_()),
        pa.field("primary_evaluation_eligible", pa.bool_()),
        pa.field("candidate_id", pa.large_string()),
        pa.field("model_selection_run_id", pa.large_string()),
    ]
)
_PHASE8_DAILY_FIXTURE_SCHEMA = pa.schema(
    [
        pa.field("fit_id", pa.large_string()),
        pa.field("Store", pa.int64()),
        pa.field("forecast_origin", pa.timestamp("ns")),
        pa.field("Date", pa.timestamp("ns")),
        pa.field("horizon", pa.int64()),
        pa.field("interval_kind", pa.large_string()),
        pa.field("point_forecast", pa.float64()),
        pa.field("lower", pa.float64()),
        pa.field("upper", pa.float64()),
        pa.field("width", pa.float64()),
        pa.field("available", pa.bool_()),
        pa.field("unavailable_reason", pa.string()),
        pa.field("actual_sales", pa.float64()),
        pa.field("assessment_source_open", pa.float64()),
        pa.field("selected_candidate_id", pa.large_string()),
        pa.field("model_selection_run_id", pa.large_string()),
        pa.field("units", pa.large_string()),
        pa.field("schedule_assumption_flag", pa.bool_()),
    ]
)
_PHASE8_CUMULATIVE_FIXTURE_SCHEMA = pa.schema(
    [
        pa.field("fit_id", pa.large_string()),
        pa.field("Store", pa.int64()),
        pa.field("forecast_origin", pa.timestamp("ns")),
        pa.field("k", pa.int64()),
        pa.field("p", pa.float64()),
        pa.field("selected_candidate_id", pa.large_string()),
        pa.field("model_selection_run_id", pa.large_string()),
        pa.field("units", pa.large_string()),
        pa.field("schedule_assumption_flag", pa.bool_()),
        pa.field("issued_prefix_complete", pa.bool_()),
        pa.field("issued_prefix_unavailable_reason", pa.null()),
        pa.field("D_k", pa.float64()),
        pa.field("q_p_signed", pa.float64()),
        pa.field("U_k", pa.float64()),
        pa.field("SafetyStock_k", pa.float64()),
        pa.field("Target_k", pa.float64()),
    ]
)
_PRODUCER_FIXTURE_SCHEMAS = {
    ArtifactSelector.PHASE9_SCENARIO_CATALOG: CATALOG_SCHEMA,
    ArtifactSelector.PHASE10_COMPARISON: COMPARISON_SCHEMA,
    ArtifactSelector.PHASE10_POLICY_SUMMARY: POLICY_SUMMARY_SCHEMA,
    ArtifactSelector.PHASE10_POLICY_TARGETS: POLICY_TARGET_SCHEMA,
}
_FIXTURE_SCHEMAS = {
    ArtifactSelector.PHASE7_FORECASTS: _PHASE7_FIXTURE_SCHEMA,
    ArtifactSelector.PHASE8_DAILY_INTERVALS: _PHASE8_DAILY_FIXTURE_SCHEMA,
    ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY: _PHASE8_CUMULATIVE_FIXTURE_SCHEMA,
    **_PRODUCER_FIXTURE_SCHEMAS,
}
_DOMAIN_STRINGS = {
    "scenario_id": "fixture-scenario",
    "family": "synthetic_base",
    "mode": "synthetic",
    "schedule_mode": "planned_open",
    "demand_basis": "synthetic_turnover_value",
    "stress_spec_id": "base",
    "case_id": "fixture-case",
    "metric": "mae",
    "relative_difference_null_reason": None,
    "null_reason": None,
    "interpretation": "fixture comparison",
    "sensitivity_variant": "reference",
    "policy_id": "historical_mean_standing_target",
    "episode_status": "complete",
    "availability_reason": None,
    "common_input_identity": "fixture-input-identity",
    "fit_id": "A",
    "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
    "candidate_id": "global_lightgbm_gbdt_regression_l1",
    "model_selection_run_id": "365f22d4c3f94722a594ab934a22c4f6",
    "interval_kind": "raw",
    "units": "sales_value",
    "tail": "lower",
    "error_population": "raw_primary_source_open_1_signed_sales_error",
    "unavailable_component_reasons": "{}",
    "last_calibration_label": None,
    "unavailable_reason": None,
    "policy_version": "phase-10-adr-023-v1",
    "calibration_windows": "fixture-window",
    "excluded_reason_counts": "{}",
    "prefix_definition": "origin-anchored-prefix",
    "schedule_assumption": "saved_source_open_assumed_known_at_origin",
    "paired_with": None,
    "population": "standalone",
    "scope": "pooled",
    "validation_window": None,
    "buffer_interpretation": "reference probability",
    "upstream_identity": "fixture-upstream-identity",
    "model_id": "global_lightgbm_gbdt_regression_l1",
}
_CSV_TEST_TYPES = {
    ArtifactSelector.PHASE7_MODEL_COMPARISON: {
        **dict.fromkeys(
            (
                "candidate_id",
                "population",
                "paired_with",
                "scope",
                "validation_window",
                "metric",
                "unavailable_reason",
            ),
            "string",
        ),
        **dict.fromkeys(
            ("horizon", "week_block_start_horizon", "week_block_end_horizon", "Store"),
            "integer",
        ),
        **dict.fromkeys(
            ("value", "numerator", "denominator", "paired_mae_delta", "paired_mae_change_fraction"),
            "float",
        ),
    },
    ArtifactSelector.PHASE8_DAILY_QUANTILES: {
        **dict.fromkeys(
            (
                "fit_id",
                "tail",
                "error_population",
                "unavailable_component_reasons",
                "last_calibration_label",
                "unavailable_reason",
                "policy_version",
                "selected_candidate_id",
                "calibration_windows",
            ),
            "string",
        ),
        **dict.fromkeys(
            (
                "horizon",
                "n",
                "distinct_stores",
                "distinct_origins",
                "observed_open_0",
                "observed_open_1",
                "observed_open_unknown",
                "candidate_rows",
                "forecast_available_count",
                "rank_1_indexed",
            ),
            "integer",
        ),
        **dict.fromkeys(("tail_level", "signed_quantile"), "float"),
        "available": "boolean",
    },
    ArtifactSelector.PHASE8_CUMULATIVE_QUANTILES: {
        **dict.fromkeys(
            (
                "fit_id",
                "error_population",
                "excluded_reason_counts",
                "last_calibration_label",
                "unavailable_reason",
                "prefix_definition",
                "schedule_assumption",
                "policy_version",
                "selected_candidate_id",
                "calibration_windows",
            ),
            "string",
        ),
        **dict.fromkeys(
            (
                "k",
                "total_store_origin_paths",
                "complete_prefixes",
                "excluded_prefixes",
                "distinct_stores",
                "distinct_origins",
                "rank_1_indexed",
            ),
            "integer",
        ),
        **dict.fromkeys(("p", "signed_quantile"), "float"),
        "available": "boolean",
    },
    ArtifactSelector.PHASE10_COMPARISON: {
        **dict.fromkeys(
            (
                "case_id",
                "metric",
                "relative_difference_null_reason",
                "null_reason",
                "interpretation",
            ),
            "string",
        ),
        **dict.fromkeys(
            (
                "requested_store_count",
                "baseline_standalone_store_count",
                "forecast_standalone_store_count",
                "matched_store_count",
            ),
            "integer",
        ),
        **dict.fromkeys(
            (
                "baseline_numerator",
                "baseline_denominator",
                "forecast_numerator",
                "forecast_denominator",
                "baseline_value",
                "forecast_value",
                "forecast_minus_baseline",
                "forecast_minus_baseline_relative",
            ),
            "float",
        ),
    },
}
_CSV_TEST_VALUES = {
    "candidate_id": "global_lightgbm_gbdt_regression_l1",
    "population": "standalone",
    "paired_with": None,
    "scope": "pooled",
    "validation_window": None,
    "metric": "mae",
    "unavailable_reason": None,
    "horizon": None,
    "week_block_start_horizon": None,
    "week_block_end_horizon": None,
    "Store": None,
    "value": 12.5,
    "numerator": 12.5,
    "denominator": 1.0,
    "paired_mae_delta": None,
    "paired_mae_change_fraction": None,
    "fit_id": "A",
    "tail": "lower",
    "tail_level": 0.025,
    "error_population": "raw_primary_source_open_1_signed_sales_error",
    "n": 40,
    "distinct_stores": 10,
    "distinct_origins": 5,
    "observed_open_0": 0,
    "observed_open_1": 50,
    "observed_open_unknown": 0,
    "candidate_rows": 60,
    "forecast_available_count": 50,
    "unavailable_component_reasons": "{}",
    "last_calibration_label": "2015-06-19",
    "rank_1_indexed": 1,
    "signed_quantile": -2.5,
    "available": True,
    "policy_version": "phase-10-adr-023-v1",
    "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
    "calibration_windows": "fixture-window",
    "k": 1,
    "p": 0.95,
    "total_store_origin_paths": 60,
    "complete_prefixes": 50,
    "excluded_prefixes": 10,
    "excluded_reason_counts": "{}",
    "prefix_definition": "origin-anchored-prefix",
    "schedule_assumption": "saved_source_open_assumed_known_at_origin",
    "case_id": "fixture-case",
    "requested_store_count": 1,
    "baseline_standalone_store_count": 1,
    "forecast_standalone_store_count": 1,
    "matched_store_count": 1,
    "baseline_numerator": 10.0,
    "baseline_denominator": 1.0,
    "forecast_numerator": 9.0,
    "forecast_denominator": 1.0,
    "baseline_value": None,
    "forecast_value": 9.0,
    "forecast_minus_baseline": None,
    "forecast_minus_baseline_relative": None,
    "relative_difference_null_reason": None,
    "null_reason": None,
    "interpretation": "fixture comparison",
}


def _sample_arrow_value(field: pa.Field) -> object:
    name, dtype = field.name, field.type
    if pa.types.is_null(dtype):
        return None
    if pa.types.is_boolean(dtype):
        return True
    if pa.types.is_integer(dtype):
        return 1
    if pa.types.is_floating(dtype):
        if name in {"source_open", "assessment_source_open"}:
            return 1.0
        return 0.95 if name in {"p", "buffer_probability"} else 12.5
    if pa.types.is_date(dtype):
        return date(2015, 6, 19)
    if pa.types.is_timestamp(dtype):
        return datetime(2015, 6, 20) if name == "Date" else datetime(2015, 6, 19)
    if pa.types.is_string(dtype) or pa.types.is_large_string(dtype):
        if name not in _DOMAIN_STRINGS:
            raise AssertionError(f"Missing typed fixture value for string field {name}.")
        return _DOMAIN_STRINGS[name]
    if field.nullable:
        return None
    raise AssertionError(f"Unsupported producer fixture type for {name}: {dtype}.")


def _schema_for(selector: ArtifactSelector, columns: tuple[str, ...] | None = None) -> pa.Schema:
    schema = _FIXTURE_SCHEMAS[selector]
    return schema if columns is None else pa.schema([schema.field(name) for name in columns])


def _write_table(
    path: Path,
    selector: ArtifactSelector,
    columns: tuple[str, ...] | None = None,
    *,
    values: dict[str, object] | None = None,
    type_overrides: dict[str, pa.DataType] | None = None,
    nullable_overrides: dict[str, bool] | None = None,
    row_count: int = 1,
) -> None:
    selected = _schema_for(selector, columns)
    overrides = {} if values is None else values
    type_changes = {} if type_overrides is None else type_overrides
    nullability_changes = {} if nullable_overrides is None else nullable_overrides
    schema = pa.schema(
        [
            pa.field(
                field.name,
                type_changes.get(field.name, field.type),
                nullable=nullability_changes.get(field.name, field.nullable),
            )
            for field in selected
        ]
    )
    row = {
        field.name: overrides[field.name] if field.name in overrides else _sample_arrow_value(field)
        for field in schema
    }
    row.update(overrides)
    pq.write_table(
        pa.Table.from_pylist([row.copy() for _ in range(row_count)], schema=schema), path
    )


def _csv_value(selector: ArtifactSelector, name: str) -> object:
    if name not in _CSV_TEST_TYPES[selector]:
        raise AssertionError(f"Missing independent CSV fixture type for {name}.")
    if name not in _CSV_TEST_VALUES:
        raise AssertionError(f"Missing independent CSV fixture value for {name}.")
    if selector is ArtifactSelector.PHASE8_DAILY_QUANTILES and name == "horizon":
        return 1
    return _CSV_TEST_VALUES[name]


def _artifact_path(fixture_store: FixtureStore, selector: ArtifactSelector) -> Path:
    spec = _ARTIFACTS[selector]
    return (
        fixture_store.root
        / CANONICAL_RUNS[spec.phase].manifest_relative_path.parent
        / spec.filename
    )


def _write_csv(
    path: Path,
    selector: ArtifactSelector,
    columns: tuple[str, ...],
    *,
    values: dict[str, object] | None = None,
) -> None:
    row_values = {name: _csv_value(selector, name) for name in columns}
    if values is not None:
        row_values.update(values)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerow(["" if row_values[name] is None else row_values[name] for name in columns])


class FixtureStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.expected_runs: dict[Phase, CanonicalRunIdentity] = {}
        self.manifests: dict[Phase, dict[str, object]] = {}
        self._build()

    def _build(self) -> None:
        outputs_by_phase: dict[Phase, dict[str, dict[str, object]]] = {phase: {} for phase in Phase}
        for selector, spec in _ARTIFACTS.items():
            path = self.root / CANONICAL_RUNS[spec.phase].manifest_relative_path.parent
            path.mkdir(parents=True, exist_ok=True)
            output = path / spec.filename
            if spec.file_format == "csv":
                assert spec.csv_header is not None
                _write_csv(output, selector, spec.csv_header)
            else:
                columns = (
                    tuple(_PRODUCER_FIXTURE_SCHEMAS[selector].names)
                    if selector in _PRODUCER_FIXTURE_SCHEMAS
                    else spec.projection
                )
                _write_table(output, selector, columns)
            metadata: dict[str, object] = {
                "rows": 1,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            }
            if selector in _PRODUCER_FIXTURE_SCHEMAS:
                schema = _PRODUCER_FIXTURE_SCHEMAS[selector]
                metadata["schema"] = [
                    {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                    for field in schema
                ]
                metadata["byte_length"] = output.stat().st_size
            elif spec.file_format == "parquet":
                metadata["columns"] = list(_schema_for(selector, spec.projection).names)
            else:
                metadata["bytes"] = output.stat().st_size
            if spec.phase in {Phase.PHASE9, Phase.PHASE10}:
                metadata["path"] = spec.filename
            outputs_by_phase[spec.phase][spec.filename] = metadata

        p7 = CANONICAL_RUNS[Phase.PHASE7]
        self._write_manifest(
            Phase.PHASE7,
            {
                "selection_run_id": p7.run_id,
                "status": "selected",
                "publication_state": "complete",
                "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
                "final_holdout_outcomes_read_or_hashed": False,
                "date_bounds": {
                    "last_development_target": "2015-07-03",
                    "final_holdout_start": "2015-07-04",
                },
                "outputs": outputs_by_phase[Phase.PHASE7],
            },
        )
        p8 = CANONICAL_RUNS[Phase.PHASE8]
        self._write_manifest(
            Phase.PHASE8,
            {
                "run_id": p8.run_id,
                "status": "complete_with_unavailable_strata",
                "selection_run_id": p7.run_id,
                "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
                "fit_b_quantiles_frozen": False,
                "inputs": {
                    "selection_manifest_sha256": self.expected_runs[Phase.PHASE7].manifest_sha256,
                    "selection_run_id": p7.run_id,
                },
                "boundaries": {
                    "development_cutoff_inclusive": "2015-07-03",
                    "holdout_open_sales_customers_opened_loaded_or_hashed": False,
                },
                "outputs": outputs_by_phase[Phase.PHASE8],
            },
        )

        p9 = CANONICAL_RUNS[Phase.PHASE9]
        binding_payload: dict[str, object] = {
            "run_id": p9.run_id,
            "created_at_utc": "fixture-time",
            "phase7": {
                "selection_manifest_sha256": self.expected_runs[Phase.PHASE7].manifest_sha256,
                "selection_run_id": p7.run_id,
            },
            "phase8": {
                "manifest_sha256": self.expected_runs[Phase.PHASE8].manifest_sha256,
                "run_id": p8.run_id,
            },
            "boundary_checks": {"protected_holdout_values_read_or_hashed": False},
        }
        canonical_payload = {
            key: value
            for key, value in binding_payload.items()
            if key not in {"run_id", "created_at_utc"}
        }
        canonical_sha = hashlib.sha256(_canonical_json(canonical_payload)).hexdigest()
        binding = {**binding_payload, "canonical_sha256": canonical_sha}
        bindings_path = self.root / p9.manifest_relative_path.parent / "upstream_bindings.json"
        bindings_path.write_text(json.dumps(binding, indent=2, sort_keys=True), encoding="utf-8")
        self._write_manifest(
            Phase.PHASE9,
            {
                "run_id": p9.run_id,
                "status": "complete",
                "inputs": {
                    "phase7_selection_manifest_sha256": self.expected_runs[
                        Phase.PHASE7
                    ].manifest_sha256,
                    "phase8_manifest_sha256": self.expected_runs[Phase.PHASE8].manifest_sha256,
                },
                "boundaries": {
                    "development_cutoff_inclusive": "2015-07-03",
                    "protected_holdout_values_read_or_hashed": False,
                },
                "upstream_bindings": {
                    "path": "upstream_bindings.json",
                    "sha256": hashlib.sha256(bindings_path.read_bytes()).hexdigest(),
                    "canonical_sha256": canonical_sha,
                },
                "outputs": outputs_by_phase[Phase.PHASE9],
            },
        )

        p10 = CANONICAL_RUNS[Phase.PHASE10]
        self._write_manifest(
            Phase.PHASE10,
            {
                "run_id": p10.run_id,
                "status": "complete",
                "inputs": {
                    "phase7_run_id": p7.run_id,
                    "phase7_selection_manifest_sha256": self.expected_runs[
                        Phase.PHASE7
                    ].manifest_sha256,
                    "phase8_run_id": p8.run_id,
                    "phase8_manifest_sha256": self.expected_runs[Phase.PHASE8].manifest_sha256,
                    "phase9_run_id": p9.run_id,
                    "phase9_manifest_sha256": self.expected_runs[Phase.PHASE9].manifest_sha256,
                },
                "boundaries": {
                    "allowed_outcome_through": "2015-07-03",
                    "protected_holdout_values_read_or_hashed": False,
                },
                "outputs": outputs_by_phase[Phase.PHASE10],
            },
        )

    def _write_manifest(self, phase: Phase, manifest: dict[str, object]) -> None:
        identity = CANONICAL_RUNS[phase]
        path = self.root / identity.manifest_relative_path
        payload = _canonical_json(manifest)
        path.write_bytes(payload)
        self.manifests[phase] = manifest
        self.expected_runs[phase] = replace(
            identity,
            manifest_sha256=hashlib.sha256(payload).hexdigest(),
        )

    def reader(self) -> _ArtifactReader:
        return _ArtifactReader(root=self.root, expected_runs=self.expected_runs)

    def refresh_manifest(self, phase: Phase) -> None:
        self._write_manifest(phase, self.manifests[phase])

    def refresh_output(self, selector: ArtifactSelector) -> None:
        spec = _ARTIFACTS[selector]
        path = self.root / CANONICAL_RUNS[spec.phase].manifest_relative_path.parent / spec.filename
        metadata = self.manifests[spec.phase]["outputs"][spec.filename]
        assert isinstance(metadata, dict)
        metadata["rows"] = (
            pq.ParquetFile(path).metadata.num_rows if spec.file_format == "parquet" else 1
        )
        metadata["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        if "columns" in metadata:
            metadata["columns"] = pq.ParquetFile(path).schema_arrow.names
        if "byte_length" in metadata:
            metadata["byte_length"] = path.stat().st_size
        elif "bytes" in metadata:
            metadata["bytes"] = path.stat().st_size
        self.refresh_manifest(spec.phase)


@pytest.fixture
def fixture_store(tmp_path: Path) -> FixtureStore:
    return FixtureStore(tmp_path)


@pytest.mark.parametrize("selector", list(_ARTIFACTS))
def test_allowlisted_fixture_artifacts_load_with_trusted_identity(
    fixture_store: FixtureStore, selector: ArtifactSelector
) -> None:
    result = fixture_store.reader().read(selector)

    identity = fixture_store.expected_runs[_ARTIFACTS[selector].phase]
    assert result.selector is selector
    assert result.run_id == identity.run_id
    assert result.manifest_sha256 == identity.manifest_sha256
    assert len(result.frame) == 1
    assert tuple(result.frame.columns) == _ARTIFACTS[selector].projection


def test_rejects_wrong_trusted_manifest_hash(fixture_store: FixtureStore) -> None:
    identity = fixture_store.expected_runs[Phase.PHASE7]
    fixture_store.expected_runs[Phase.PHASE7] = replace(identity, manifest_sha256="0" * 64)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_rejects_wrong_output_hash(fixture_store: FixtureStore) -> None:
    spec = _ARTIFACTS[ArtifactSelector.PHASE7_FORECASTS]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE7].manifest_relative_path.parent
        / spec.filename
    )
    output.write_bytes(output.read_bytes() + b"changed")

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_rejects_inconsistent_phase10_upstream_lineage(fixture_store: FixtureStore) -> None:
    manifest = fixture_store.manifests[Phase.PHASE10]
    inputs = manifest["inputs"]
    assert isinstance(inputs, dict)
    inputs["phase7_run_id"] = "different-run"
    fixture_store.refresh_manifest(Phase.PHASE10)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE10_COMPARISON)


def test_missing_artifact_is_explicit_and_does_not_fall_back(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_INTERVALS
    spec = _ARTIFACTS[selector]
    expected_dir = fixture_store.root / CANONICAL_RUNS[Phase.PHASE8].manifest_relative_path.parent
    (expected_dir / spec.filename).unlink()
    alternate = fixture_store.root / "data/processed/uncertainty/other-run"
    alternate.mkdir(parents=True)
    (alternate / spec.filename).write_bytes(b"not a trusted fallback")
    (expected_dir.parent / "current.json").write_text('{"run_id":"other-run"}', encoding="utf-8")

    with pytest.raises(ArtifactUnavailableError) as error:
        fixture_store.reader().read(selector)
    assert error.value.unavailable is not None
    assert error.value.unavailable.value is None


@pytest.mark.parametrize("payload", [b"{", b'{"value":NaN}'])
def test_rejects_malformed_manifest_json(fixture_store: FixtureStore, payload: bytes) -> None:
    identity = fixture_store.expected_runs[Phase.PHASE7]
    path = fixture_store.root / identity.manifest_relative_path
    path.write_bytes(payload)
    fixture_store.expected_runs[Phase.PHASE7] = replace(
        identity, manifest_sha256=hashlib.sha256(payload).hexdigest()
    )

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_rejects_missing_required_schema_column(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    spec = _ARTIFACTS[selector]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE7].manifest_relative_path.parent
        / spec.filename
    )
    columns = tuple(name for name in spec.projection if name != "raw_forecast")
    _write_table(output, selector, columns)
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


@pytest.mark.parametrize(
    ("selector", "field", "replacement_type", "replacement_value"),
    [
        (ArtifactSelector.PHASE7_FORECASTS, "raw_forecast", pa.string(), "12.5"),
        (ArtifactSelector.PHASE8_DAILY_INTERVALS, "available", pa.string(), "True"),
    ],
)
def test_rejects_wrong_projected_parquet_types(
    fixture_store: FixtureStore,
    selector: ArtifactSelector,
    field: str,
    replacement_type: pa.DataType,
    replacement_value: object,
) -> None:
    _write_table(
        _artifact_path(fixture_store, selector),
        selector,
        values={field: replacement_value},
        type_overrides={field: replacement_type},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_rejects_nonnumeric_csv_metric_value(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE10_COMPARISON
    spec = _ARTIFACTS[selector]
    _write_csv(
        _artifact_path(fixture_store, selector),
        selector,
        spec.csv_header or (),
        values={"baseline_value": "not-a-number"},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_rejects_malformed_csv_boolean(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    spec = _ARTIFACTS[selector]
    _write_csv(
        _artifact_path(fixture_store, selector),
        selector,
        spec.csv_header or (),
        values={"available": "yes"},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_rejects_fractional_value_in_csv_integer_field(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    spec = _ARTIFACTS[selector]
    _write_csv(
        _artifact_path(fixture_store, selector),
        selector,
        spec.csv_header or (),
        values={"n": "2.5"},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


@pytest.mark.parametrize(
    ("selector", "field", "token", "expected"),
    [
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "n", "-9223372036854775808", -(2**63)),
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "n", "9223372036854775807", 2**63 - 1),
        (
            ArtifactSelector.PHASE7_MODEL_COMPARISON,
            "Store",
            "9007199254740993.0",
            9007199254740993,
        ),
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "n", "1.0", 1),
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "n", "+1", 1),
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "n", "-1", -1),
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "n", "0.00", 0),
    ],
)
def test_csv_integer_tokens_are_parsed_exactly(
    fixture_store: FixtureStore,
    selector: ArtifactSelector,
    field: str,
    token: str,
    expected: int,
) -> None:
    spec = _ARTIFACTS[selector]
    _write_csv(
        _artifact_path(fixture_store, selector),
        selector,
        spec.csv_header or (),
        values={field: token},
    )
    fixture_store.refresh_output(selector)

    result = fixture_store.reader().read(selector).frame

    assert result.loc[0, field] == expected
    assert str(result[field].dtype) == "Int64"


@pytest.mark.parametrize(
    "token",
    [
        "9223372036854775808",
        "-9223372036854775809",
        "2.0000000000000001",
        "not-an-integer",
        "1_0",
        "  ",
        "NaN",
        "Infinity",
        "1e400",
        "1e-9999999999999999",
        "9" * 129,
    ],
)
def test_csv_integer_tokens_reject_fractional_malformed_and_out_of_range_values(
    fixture_store: FixtureStore, token: str
) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    spec = _ARTIFACTS[selector]
    _write_csv(
        _artifact_path(fixture_store, selector),
        selector,
        spec.csv_header or (),
        values={"n": token},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_csv_integer_nullability_is_preserved_and_enforced(
    fixture_store: FixtureStore,
) -> None:
    optional_selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    optional_spec = _ARTIFACTS[optional_selector]
    _write_csv(
        _artifact_path(fixture_store, optional_selector),
        optional_selector,
        optional_spec.csv_header or (),
        values={"Store": None},
    )
    fixture_store.refresh_output(optional_selector)
    optional = fixture_store.reader().read(optional_selector).frame
    assert pd.isna(optional.loc[0, "Store"])
    assert str(optional["Store"].dtype) == "Int64"

    required_selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    required_spec = _ARTIFACTS[required_selector]
    _write_csv(
        _artifact_path(fixture_store, required_selector),
        required_selector,
        required_spec.csv_header or (),
        values={"n": None},
    )
    fixture_store.refresh_output(required_selector)
    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(required_selector)


@pytest.mark.parametrize(
    "token",
    ["2\x00.5", "1\x00garbage", "1\x00" + "9" * 129],
)
def test_csv_integer_reader_rejects_embedded_nul_bytes(
    fixture_store: FixtureStore, token: str
) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    spec = _ARTIFACTS[selector]
    output = _artifact_path(fixture_store, selector)
    _write_csv(output, selector, spec.csv_header or (), values={"n": token})
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError) as error:
        fixture_store.reader().read(selector)

    assert str(error.value) == "The canonical artifact does not satisfy its schema contract."
    assert error.value.__cause__ is None
    assert b"\x00" in output.read_bytes()


@pytest.mark.parametrize(
    ("selector", "field"),
    [
        (ArtifactSelector.PHASE7_MODEL_COMPARISON, "candidate_id"),
        (ArtifactSelector.PHASE8_DAILY_QUANTILES, "fit_id"),
        (ArtifactSelector.PHASE8_CUMULATIVE_QUANTILES, "fit_id"),
        (ArtifactSelector.PHASE10_COMPARISON, "case_id"),
    ],
)
def test_csv_reader_rejects_embedded_nul_in_string_field(
    fixture_store: FixtureStore, selector: ArtifactSelector, field: str
) -> None:
    spec = _ARTIFACTS[selector]
    output = _artifact_path(fixture_store, selector)
    _write_csv(output, selector, spec.csv_header or (), values={field: "nul\x00fixture"})
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_csv_reader_rejects_nul_outside_csv_fields(
    fixture_store: FixtureStore,
) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    output = _artifact_path(fixture_store, selector)
    output.write_bytes(output.read_bytes() + b"\x00")
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_csv_nul_check_preserves_valid_values_nulls_and_files(
    fixture_store: FixtureStore,
) -> None:
    comparison_fixture = FixtureStore(fixture_store.root / "valid-phase7")
    comparison_selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    comparison_spec = _ARTIFACTS[comparison_selector]
    comparison_output = _artifact_path(comparison_fixture, comparison_selector)
    _write_csv(
        comparison_output,
        comparison_selector,
        comparison_spec.csv_header or (),
        values={"candidate_id": "candidate-λ", "Store": None},
    )
    comparison_fixture.refresh_output(comparison_selector)

    quantile_fixture = FixtureStore(fixture_store.root / "valid-phase8")
    quantile_selector = ArtifactSelector.PHASE8_DAILY_QUANTILES
    quantile_spec = _ARTIFACTS[quantile_selector]
    quantile_output = _artifact_path(quantile_fixture, quantile_selector)
    _write_csv(
        quantile_output,
        quantile_selector,
        quantile_spec.csv_header or (),
        values={"fit_id": "fit-λ", "n": "1.0"},
    )
    quantile_fixture.refresh_output(quantile_selector)
    before = {
        comparison_output: comparison_output.read_bytes(),
        quantile_output: quantile_output.read_bytes(),
    }

    comparison = comparison_fixture.reader().read(comparison_selector).frame
    quantiles = quantile_fixture.reader().read(quantile_selector).frame

    assert len(comparison) == len(quantiles) == 1
    assert comparison.loc[0, "candidate_id"] == "candidate-λ"
    assert str(comparison["candidate_id"].dtype) == "string"
    assert pd.isna(comparison.loc[0, "Store"])
    assert str(comparison["Store"].dtype) == "Int64"
    assert quantiles.loc[0, "fit_id"] == "fit-λ"
    assert quantiles.loc[0, "n"] == 1
    assert str(quantiles["fit_id"].dtype) == "string"
    assert str(quantiles["n"].dtype) == "Int64"
    assert before == {
        comparison_output: comparison_output.read_bytes(),
        quantile_output: quantile_output.read_bytes(),
    }


def test_csv_values_use_nullable_semantic_dtypes(fixture_store: FixtureStore) -> None:
    daily = fixture_store.reader().read(ArtifactSelector.PHASE8_DAILY_QUANTILES).frame
    comparison = fixture_store.reader().read(ArtifactSelector.PHASE10_COMPARISON).frame

    assert str(daily["horizon"].dtype) == "Int64"
    assert str(daily["available"].dtype) == "boolean"
    assert str(daily["fit_id"].dtype) == "string"
    assert str(comparison["baseline_value"].dtype) == "Float64"


def test_rejects_null_mandatory_candidate_identifier(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    spec = _ARTIFACTS[selector]
    _write_csv(
        _artifact_path(fixture_store, selector),
        selector,
        spec.csv_header or (),
        values={"candidate_id": None},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_allows_null_model_comparison_grouping_fields(fixture_store: FixtureStore) -> None:
    result = fixture_store.reader().read(ArtifactSelector.PHASE7_MODEL_COMPARISON)

    assert pd.isna(result.frame.loc[0, "paired_with"])
    assert pd.isna(result.frame.loc[0, "Store"])
    assert result.frame.loc[0, "candidate_id"] == "global_lightgbm_gbdt_regression_l1"


def test_rejects_null_required_family_in_phase9_catalog(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    _write_table(
        _artifact_path(fixture_store, selector),
        selector,
        values={"family": None},
        nullable_overrides={"family": True},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_rejects_null_required_policy_identifier(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    _write_table(
        _artifact_path(fixture_store, selector),
        selector,
        values={"policy_id": None},
        nullable_overrides={"policy_id": True},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_required_null_rejected_and_unavailable_value_null_preserved(
    fixture_store: FixtureStore,
) -> None:
    comparison = fixture_store.reader().read(ArtifactSelector.PHASE10_COMPARISON)
    assert pd.isna(comparison.frame.loc[0, "baseline_value"])

    selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    _write_table(
        _artifact_path(fixture_store, selector),
        selector,
        values={"episode_complete": None},
        nullable_overrides={"episode_complete": True},
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_required_non_null_guard_rejects_null_values_directly() -> None:
    frame = pd.DataFrame({"family": pd.Series([pd.NA], dtype="string")})

    with pytest.raises(ArtifactSchemaError):
        _ArtifactReader._assert_required_non_null(
            frame, ArtifactSelector.PHASE9_SCENARIO_CATALOG, ("family",)
        )


def test_rejects_phase9_descriptor_nullability_mismatch(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    metadata = fixture_store.manifests[Phase.PHASE9]["outputs"]["scenario_catalog.parquet"]
    assert isinstance(metadata, dict)
    descriptors = metadata["schema"]
    assert isinstance(descriptors, list)
    descriptors[1]["nullable"] = True
    fixture_store.refresh_manifest(Phase.PHASE9)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


@pytest.mark.parametrize(
    "selector",
    [
        ArtifactSelector.PHASE9_SCENARIO_CATALOG,
        ArtifactSelector.PHASE10_COMPARISON,
        ArtifactSelector.PHASE10_POLICY_SUMMARY,
        ArtifactSelector.PHASE10_POLICY_TARGETS,
    ],
)
def test_requires_phase9_and_phase10_schema_descriptors(
    fixture_store: FixtureStore, selector: ArtifactSelector
) -> None:
    phase = _ARTIFACTS[selector].phase
    metadata = fixture_store.manifests[phase]["outputs"][_ARTIFACTS[selector].filename]
    assert isinstance(metadata, dict)
    del metadata["schema"]
    fixture_store.refresh_manifest(phase)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_rejects_unbounded_manifest_row_count_before_read(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    spec = _ARTIFACTS[selector]
    output_meta = fixture_store.manifests[Phase.PHASE7]["outputs"][spec.filename]
    assert isinstance(output_meta, dict)
    output_meta["rows"] = spec.max_rows + 1
    fixture_store.refresh_manifest(Phase.PHASE7)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(selector)


def test_rejects_duplicate_primary_keys(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    output = _artifact_path(fixture_store, selector)
    _write_table(output, selector, row_count=2)
    fixture_store.refresh_output(selector)

    with pytest.raises(DuplicateArtifactKeyError):
        fixture_store.reader().read(selector)


def test_rejects_unsupported_selectors_and_traversal(fixture_store: FixtureStore) -> None:
    reader = fixture_store.reader()
    with pytest.raises(UnsupportedArtifactSelectorError):
        reader.read("../../outside.parquet")  # type: ignore[arg-type]
    with pytest.raises(UnsafeArtifactPathError):
        reader._trusted_file(Path("../outside.parquet"), ArtifactSelector.PHASE7_FORECASTS, None)  # type: ignore[arg-type]


def test_rejects_unsafe_symlink_component(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _ARTIFACTS[ArtifactSelector.PHASE7_FORECASTS]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE7].manifest_relative_path.parent
        / spec.filename
    )
    original_lstat = Path.lstat

    def pretend_symlink(path: Path) -> object:
        if path == output:
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", pretend_symlink)

    with pytest.raises(UnsafeArtifactPathError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_null_values_are_preserved_and_fixture_files_are_unchanged(
    fixture_store: FixtureStore,
) -> None:
    files = [path for path in fixture_store.root.rglob("*") if path.is_file()]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}

    result = fixture_store.reader().read(ArtifactSelector.PHASE10_COMPARISON)

    assert pd.isna(result.frame.loc[0, "baseline_value"])
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert after == before


def test_phase8_historical_false_freeze_flag_is_accepted(fixture_store: FixtureStore) -> None:
    assert fixture_store.manifests[Phase.PHASE8]["fit_b_quantiles_frozen"] is False
    fixture_store.reader().read(ArtifactSelector.PHASE8_CUMULATIVE_QUANTILES)


def test_output_hash_cache_rechecks_when_file_identity_changes(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    original = artifact_module._sha256_file
    checked: list[Path] = []

    def counted(path: Path) -> str:
        checked.append(path)
        return original(path)

    monkeypatch.setattr(artifact_module, "_sha256_file", counted)
    reader = fixture_store.reader()
    reader.read(selector)
    reader.read(selector)
    assert len(checked) == 1

    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE9].manifest_relative_path.parent
        / "scenario_catalog.parquet"
    )
    payload = output.read_bytes()
    output.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    output.touch()
    with pytest.raises(ArtifactIntegrityError):
        reader.read(selector)
    assert len(checked) == 2


def test_history_crossing_cutoff_is_rejected_before_dataset_open(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened = False

    def unexpected_open(*args: object, **kwargs: object) -> None:
        nonlocal opened
        opened = True
        raise AssertionError("The protected history dataset must not be opened.")

    monkeypatch.setattr(artifact_module.ds, "dataset", unexpected_open)
    query = HistoryQuery(
        store_id=1,
        start_date=date(2015, 7, 3),
        end_date=date(2015, 7, 4),
    )
    with pytest.raises(InvalidArtifactRequestError):
        fixture_store.reader().read_history_sales(query)
    assert not opened


def test_history_uses_arrow_projection_and_storage_filter(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "Store": pa.array([1, 1, 1, 2], type=pa.int64()),
            "Date": pa.array(
                [
                    datetime(2015, 7, 2),
                    datetime(2015, 7, 3),
                    datetime(2015, 7, 4),
                    datetime(2015, 7, 3),
                ],
                type=pa.timestamp("ns"),
            ),
            "Sales": pa.array([100, None, 9_999_999, 200], type=pa.int64()),
            "Open": pa.array([1, None, 0, 1], type=pa.int64()),
            "Customers": pa.array([10, 11, 12_345, 20], type=pa.int64()),
        }
    )
    pq.write_table(table, source)
    original_dataset = artifact_module.ds.dataset
    observed: dict[str, object] = {}

    class RecordingDataset:
        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped
            self.schema = wrapped.schema

        def scanner(self, **kwargs: object) -> object:
            observed.update(kwargs)
            return self._wrapped.scanner(**kwargs)

    def recording_dataset(*args: object, **kwargs: object) -> RecordingDataset:
        return RecordingDataset(original_dataset(*args, **kwargs))

    monkeypatch.setattr(artifact_module.ds, "dataset", recording_dataset)
    frame = fixture_store.reader().read_history_sales(
        HistoryQuery(
            store_id=1,
            start_date=date(2015, 7, 2),
            end_date=date(2015, 7, 3),
        )
    )

    assert tuple(observed["columns"]) == HISTORY_PROJECTION
    assert observed["filter"] is not None
    assert "Date" in str(observed["filter"])
    assert "Store" in str(observed["filter"])
    assert tuple(frame.columns) == HISTORY_PROJECTION
    assert "Customers" not in frame.columns
    assert frame["Date"].max() <= pd.Timestamp("2015-07-03")
    assert len(frame) == 2
    assert pd.isna(frame.loc[frame["Date"].eq(pd.Timestamp("2015-07-03")), "Sales"]).all()


def test_history_rejects_invalid_store_and_oversized_range_before_dataset_open(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: pytest.fail("dataset opened for an invalid request"),
    )
    reader = fixture_store.reader()
    with pytest.raises(InvalidArtifactRequestError):
        reader.read_history_sales(HistoryQuery(0, date(2015, 6, 1), date(2015, 6, 2)))
    with pytest.raises(InvalidArtifactRequestError):
        reader.read_history_sales(HistoryQuery(1, date(2014, 5, 31), date(2015, 6, 1)))


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (date(1, 1, 1), date(1, 1, 1)),
        (date(2012, 12, 31), date(2012, 12, 31)),
        (date(2015, 7, 4), date(2015, 7, 4)),
    ],
)
def test_history_rejects_dates_outside_supported_bounds_before_open(
    fixture_store: FixtureStore,
    monkeypatch: pytest.MonkeyPatch,
    start: date,
    end: date,
) -> None:
    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: pytest.fail("dataset opened for an unsupported date range"),
    )

    with pytest.raises(InvalidArtifactRequestError):
        fixture_store.reader().read_history_sales(HistoryQuery(1, start, end))


def test_history_rejects_timezone_aware_query_before_open(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: pytest.fail("dataset opened for a timezone-aware query"),
    )

    with pytest.raises(InvalidArtifactRequestError):
        fixture_store.reader().read_history_sales(
            HistoryQuery(
                1,
                datetime(2015, 6, 1, tzinfo=UTC),  # type: ignore[arg-type]
                date(2015, 6, 1),
            )
        )


def test_history_rejects_timezone_aware_date_schema_sanitized(
    fixture_store: FixtureStore,
) -> None:
    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([1], type=pa.int64()),
                "Date": pa.array(
                    [datetime(2015, 6, 1, tzinfo=UTC)],
                    type=pa.timestamp("ns", tz="UTC"),
                ),
                "Sales": pa.array([100], type=pa.int64()),
                "Open": pa.array([1], type=pa.int64()),
            }
        ),
        source,
    )

    with pytest.raises(ArtifactSchemaError) as error:
        fixture_store.reader().read_history_sales(
            HistoryQuery(1, date(2015, 6, 1), date(2015, 6, 1))
        )
    assert "UTC" not in str(error.value)
    assert "timestamp" not in str(error.value)


def test_history_converts_pandas_date_errors_to_sanitized_reader_error(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([1], type=pa.int64()),
                "Date": pa.array([datetime(2015, 6, 1)], type=pa.timestamp("ns")),
                "Sales": pa.array([100], type=pa.int64()),
                "Open": pa.array([1], type=pa.int64()),
            }
        ),
        source,
    )

    def conversion_failure(*args: object, **kwargs: object) -> None:
        raise TypeError("C:\\private\\dataset\\unsafe-date")

    monkeypatch.setattr(artifact_module.pd, "to_datetime", conversion_failure)
    with pytest.raises(ArtifactSchemaError) as error:
        fixture_store.reader().read_history_sales(
            HistoryQuery(1, date(2015, 6, 1), date(2015, 6, 1))
        )
    assert "private" not in str(error.value)
    assert "unsafe-date" not in str(error.value)


def test_history_accepts_supported_lower_and_upper_date_bounds(
    fixture_store: FixtureStore,
) -> None:
    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "Store": pa.array([1, 1], type=pa.int64()),
                "Date": pa.array(
                    [datetime(2013, 1, 1), datetime(2015, 7, 3)], type=pa.timestamp("ns")
                ),
                "Sales": pa.array([100, 200], type=pa.int64()),
                "Open": pa.array([1, 1], type=pa.int64()),
            }
        ),
        source,
    )

    reader = fixture_store.reader()
    first = reader.read_history_sales(HistoryQuery(1, date(2013, 1, 1), date(2013, 1, 1)))
    last = reader.read_history_sales(HistoryQuery(1, date(2015, 7, 3), date(2015, 7, 3)))

    assert first["Date"].tolist() == [pd.Timestamp("2013-01-01")]
    assert last["Date"].tolist() == [pd.Timestamp("2015-07-03")]


def test_missing_historical_dataset_is_explicit(fixture_store: FixtureStore) -> None:
    with pytest.raises(ArtifactUnavailableError):
        fixture_store.reader().read_history_sales(
            HistoryQuery(1, date(2015, 7, 1), date(2015, 7, 3))
        )


def test_selected_forecast_pushes_arrow_predicate_and_keeps_global_row_count(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    schema = _FIXTURE_SCHEMAS[selector]
    rows = []
    for store_id, origin in ((1, datetime(2015, 6, 5)), (2, datetime(2015, 6, 19))):
        row = {field.name: _sample_arrow_value(field) for field in schema}
        row.update(
            {
                "Store": store_id,
                "forecast_origin": origin,
                "Date": origin.replace(day=origin.day + 1),
                "horizon": 1,
            }
        )
        rows.append(row)
    pq.write_table(
        pa.Table.from_pylist(rows, schema=schema), _artifact_path(fixture_store, selector)
    )
    fixture_store.refresh_output(selector)

    original_dataset = artifact_module.ds.dataset
    observed: dict[str, object] = {}

    class RecordingDataset:
        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped
            self.schema = wrapped.schema

        def scanner(self, **kwargs: object) -> object:
            observed.update(kwargs)
            return self._wrapped.scanner(**kwargs)

    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: RecordingDataset(original_dataset(*args, **kwargs)),
    )
    result = fixture_store.reader().read_forecasts(ForecastQuery(1, date(2015, 6, 5)))

    assert len(result.frame) == result.selected_rows == 1
    assert result.manifest_rows == 2
    assert result.frame.loc[0, "Store"] == 1
    assert tuple(observed["columns"]) == _ARTIFACTS[selector].projection
    assert "Store" in str(observed["filter"])
    assert "forecast_origin" in str(observed["filter"])


def test_filtered_parquet_validates_full_footer_count_before_arrow_scan(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    _write_table(_artifact_path(fixture_store, selector), selector)
    metadata = fixture_store.manifests[Phase.PHASE7]["outputs"][_ARTIFACTS[selector].filename]
    assert isinstance(metadata, dict)
    metadata["rows"] = 2
    fixture_store.refresh_manifest(Phase.PHASE7)
    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: pytest.fail("Arrow scan ran before footer validation"),
    )

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read_forecasts(ForecastQuery(1, date(2015, 6, 19)))


def test_selected_forecast_enforces_its_own_row_bound(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    schema = _FIXTURE_SCHEMAS[selector]
    origin = datetime(2015, 6, 5)
    rows = []
    for horizon in range(1, 16):
        row = {field.name: _sample_arrow_value(field) for field in schema}
        row.update(
            {
                "Store": 1,
                "forecast_origin": origin,
                "Date": origin + timedelta(days=horizon),
                "horizon": horizon,
            }
        )
        rows.append(row)
    pq.write_table(
        pa.Table.from_pylist(rows, schema=schema), _artifact_path(fixture_store, selector)
    )
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read_forecasts(ForecastQuery(1, date(2015, 6, 5)))


def test_model_comparison_filters_stream_without_full_pandas_materialization(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    spec = _ARTIFACTS[selector]
    path = _artifact_path(fixture_store, selector)
    rows = []
    for metric in ("mae", "rmse"):
        row = {name: _csv_value(selector, name) for name in spec.projection}
        row["metric"] = metric
        rows.append(["" if row[name] is None else row[name] for name in spec.projection])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(spec.csv_header)
        writer.writerows(rows)
    metadata = fixture_store.manifests[Phase.PHASE7]["outputs"][spec.filename]
    assert isinstance(metadata, dict)
    metadata["rows"] = 2
    metadata["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata["bytes"] = path.stat().st_size
    fixture_store.refresh_manifest(Phase.PHASE7)
    monkeypatch.setattr(
        artifact_module.pd,
        "read_csv",
        lambda *args, **kwargs: pytest.fail("filtered CSV was materialized through pandas"),
    )
    reader = fixture_store.reader()
    query = ModelComparisonQuery(candidate_id="global_lightgbm_gbdt_regression_l1", limit=2)

    result = reader.read_model_comparison(query)
    assert result.selected_rows == result.manifest_rows == 2
    assert result.frame["metric"].tolist() == ["mae", "rmse"]
    assert str(result.frame["Store"].dtype) == "Int64"
    with pytest.raises(InvalidArtifactRequestError):
        reader.read_model_comparison(
            ModelComparisonQuery(candidate_id="global_lightgbm_gbdt_regression_l1", limit=1)
        )


def test_model_comparison_query_is_validated_before_manifest_read(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = fixture_store.reader()
    monkeypatch.setattr(
        reader,
        "_read_manifest",
        lambda *args, **kwargs: pytest.fail("manifest opened for an unbounded query"),
    )

    with pytest.raises(InvalidArtifactRequestError):
        reader.read_model_comparison(ModelComparisonQuery())


def test_uncertainty_views_push_fit_store_and_origin_predicates(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selectors = (
        ArtifactSelector.PHASE8_DAILY_INTERVALS,
        ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY,
    )
    for selector in selectors:
        schema = _FIXTURE_SCHEMAS[selector]
        row = {field.name: _sample_arrow_value(field) for field in schema}
        row.update(
            {
                "fit_id": "B",
                "Store": 1,
                "forecast_origin": datetime(2015, 6, 19),
            }
        )
        pq.write_table(
            pa.Table.from_pylist([row], schema=schema), _artifact_path(fixture_store, selector)
        )
        fixture_store.refresh_output(selector)
    original_dataset = artifact_module.ds.dataset
    scans: list[dict[str, object]] = []

    class RecordingDataset:
        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped
            self.schema = wrapped.schema

        def scanner(self, **kwargs: object) -> object:
            scans.append(kwargs)
            return self._wrapped.scanner(**kwargs)

    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: RecordingDataset(original_dataset(*args, **kwargs)),
    )
    reader = fixture_store.reader()
    query = UncertaintyQuery(1, date(2015, 6, 19), "B")
    daily = reader.read_daily_intervals(query)
    cumulative = reader.read_cumulative_uncertainty(query)

    assert daily.selected_rows == cumulative.selected_rows == 1
    assert len(scans) == 2
    for scan, selector in zip(scans, selectors, strict=True):
        assert tuple(scan["columns"]) == _ARTIFACTS[selector].projection
        assert "fit_id" in str(scan["filter"])
        assert "Store" in str(scan["filter"])
        assert "forecast_origin" in str(scan["filter"])


def test_uncertainty_fit_origin_pair_is_validated_before_manifest_read(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = fixture_store.reader()
    monkeypatch.setattr(
        reader,
        "_read_manifest",
        lambda *args, **kwargs: pytest.fail("manifest opened for a mismatched fit/origin"),
    )

    with pytest.raises(InvalidArtifactRequestError):
        reader.read_daily_intervals(UncertaintyQuery(1, date(2015, 6, 19), "A"))


def test_inventory_selector_pushes_case_and_store_predicate(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = ArtifactSelector.PHASE10_POLICY_SUMMARY
    schema = POLICY_SUMMARY_SCHEMA
    rows = []
    for case_id, store_id in (("fixture-case", 1), ("other-case", 2)):
        row = {field.name: _sample_arrow_value(field) for field in schema}
        row.update({"case_id": case_id, "Store": store_id})
        rows.append(row)
    pq.write_table(
        pa.Table.from_pylist(rows, schema=schema), _artifact_path(fixture_store, selector)
    )
    fixture_store.refresh_output(selector)
    original_dataset = artifact_module.ds.dataset
    observed: dict[str, object] = {}

    class RecordingDataset:
        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped
            self.schema = wrapped.schema

        def scanner(self, **kwargs: object) -> object:
            observed.update(kwargs)
            return self._wrapped.scanner(**kwargs)

    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: RecordingDataset(original_dataset(*args, **kwargs)),
    )
    result = fixture_store.reader().read_inventory_artifact(
        selector, InventoryComparisonQuery("fixture-case", store_id=1)
    )

    assert len(result.frame) == result.selected_rows == 1
    assert result.manifest_rows == 2
    assert result.frame.loc[0, "case_id"] == "fixture-case"
    assert result.frame.loc[0, "Store"] == 1
    assert "case_id" in str(observed["filter"])
    assert "Store" in str(observed["filter"])
