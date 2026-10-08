"""Read-only access to the fixed, accepted Phase 7–10 development artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactReadError,
    ArtifactSchemaError,
    ArtifactSelector,
    ArtifactTable,
    ArtifactUnavailableError,
    CanonicalRunIdentity,
    DuplicateArtifactKeyError,
    HistoryQuery,
    InvalidArtifactRequestError,
    Phase,
    UnavailableReason,
    UnsafeArtifactPathError,
    UnsupportedArtifactSelectorError,
)
from rossmann_forecasting.data.paths import repository_root

DEVELOPMENT_CUTOFF = date(2015, 7, 3)
HISTORY_PROJECTION = ("Store", "Date", "Sales", "Open")
MAX_HISTORY_DAYS = 366
MAX_HISTORY_ROWS = 366
MAX_STORE_ID = 1115
MAX_MANIFEST_BYTES = 1_000_000
MAX_BINDINGS_BYTES = 1_000_000


@dataclass(frozen=True, slots=True)
class _ArtifactSpec:
    selector: ArtifactSelector
    phase: Phase
    filename: str
    file_format: str
    projection: tuple[str, ...]
    required_columns: tuple[str, ...]
    primary_key: tuple[str, ...]
    max_rows: int
    max_bytes: int
    development_date_filter: bool = False
    csv_header: tuple[str, ...] | None = None
    allow_null_key: bool = False


_MODEL_COMPARISON_COLUMNS = (
    "candidate_id",
    "population",
    "paired_with",
    "scope",
    "validation_window",
    "horizon",
    "week_block_start_horizon",
    "week_block_end_horizon",
    "Store",
    "metric",
    "value",
    "numerator",
    "denominator",
    "unavailable_reason",
    "paired_mae_delta",
    "paired_mae_change_fraction",
)
_DAILY_QUANTILE_COLUMNS = (
    "fit_id",
    "horizon",
    "tail",
    "tail_level",
    "error_population",
    "n",
    "distinct_stores",
    "distinct_origins",
    "observed_open_0",
    "observed_open_1",
    "observed_open_unknown",
    "candidate_rows",
    "forecast_available_count",
    "unavailable_component_reasons",
    "last_calibration_label",
    "rank_1_indexed",
    "signed_quantile",
    "available",
    "unavailable_reason",
    "policy_version",
    "selected_candidate_id",
    "calibration_windows",
)
_CUMULATIVE_QUANTILE_COLUMNS = (
    "fit_id",
    "k",
    "p",
    "error_population",
    "total_store_origin_paths",
    "complete_prefixes",
    "excluded_prefixes",
    "excluded_reason_counts",
    "distinct_stores",
    "distinct_origins",
    "last_calibration_label",
    "rank_1_indexed",
    "signed_quantile",
    "available",
    "unavailable_reason",
    "prefix_definition",
    "schedule_assumption",
    "policy_version",
    "selected_candidate_id",
    "calibration_windows",
)
_COMPARISON_SUMMARY_COLUMNS = (
    "case_id",
    "metric",
    "requested_store_count",
    "baseline_standalone_store_count",
    "forecast_standalone_store_count",
    "matched_store_count",
    "baseline_numerator",
    "baseline_denominator",
    "forecast_numerator",
    "forecast_denominator",
    "baseline_value",
    "forecast_value",
    "forecast_minus_baseline",
    "forecast_minus_baseline_relative",
    "relative_difference_null_reason",
    "null_reason",
    "interpretation",
)

_POLICY_SUMMARY_PROJECTION = (
    "case_id",
    "scenario_id",
    "Store",
    "forecast_origin",
    "family",
    "mode",
    "replicate",
    "sensitivity_variant",
    "policy_id",
    "episode_status",
    "episode_complete",
    "target_available",
    "availability_reason",
    "valid_matched_comparison",
    "demand_total",
    "fulfilled_total",
    "unmet_total",
    "SimulatedHoldingPlusShortfallCost",
    "ValueFillRate",
    "PositiveDemandStockoutRate",
    "AverageInventoryValue",
    "UnmetTurnoverValue",
    "SimulatedHoldingCost",
    "SimulatedUnmetPenalty",
    "CompletedPositiveDemandReceiptCycleServiceRate",
)
_POLICY_TARGETS_PROJECTION = (
    "case_id",
    "scenario_id",
    "Store",
    "forecast_origin",
    "family",
    "mode",
    "replicate",
    "sensitivity_variant",
    "policy_id",
    "forecast_protection_demand_value",
    "cumulative_signed_quantile",
    "upper_turnover_value",
    "safety_stock_value",
    "target_value",
    "initial_stock_value",
    "target_available",
    "availability_reason",
    "synthetic",
    "calibration_transport_valid",
    "schedule_assumption",
)

CANONICAL_RUNS: dict[Phase, CanonicalRunIdentity] = {
    Phase.PHASE7: CanonicalRunIdentity(
        phase=Phase.PHASE7,
        run_id="365f22d4c3f94722a594ab934a22c4f6",
        manifest_relative_path=Path("data/processed/model_selection/manifest.json"),
        manifest_sha256="03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc",
        run_id_field="selection_run_id",
    ),
    Phase.PHASE8: CanonicalRunIdentity(
        phase=Phase.PHASE8,
        run_id="phase8-impl-20261006-provenance-review",
        manifest_relative_path=Path(
            "data/processed/uncertainty/phase8-impl-20261006-provenance-review/manifest.json"
        ),
        manifest_sha256="63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2",
        run_id_field="run_id",
    ),
    Phase.PHASE9: CanonicalRunIdentity(
        phase=Phase.PHASE9,
        run_id="phase9-dev-20261007-config-validation-fix",
        manifest_relative_path=Path(
            "data/processed/synthetic_inventory/phase9-dev-20261007-config-validation-fix/manifest.json"
        ),
        manifest_sha256="573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761",
        run_id_field="run_id",
    ),
    Phase.PHASE10: CanonicalRunIdentity(
        phase=Phase.PHASE10,
        run_id="phase10-dev-20261008-validator-fix",
        manifest_relative_path=Path(
            "data/processed/inventory_simulation/phase10-dev-20261008-validator-fix/manifest.json"
        ),
        manifest_sha256="1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16",
        run_id_field="run_id",
    ),
}

_ARTIFACTS: dict[ArtifactSelector, _ArtifactSpec] = {
    ArtifactSelector.PHASE7_FORECASTS: _ArtifactSpec(
        selector=ArtifactSelector.PHASE7_FORECASTS,
        phase=Phase.PHASE7,
        filename="selected_development_forecasts.parquet",
        file_format="parquet",
        projection=(
            "Store",
            "forecast_origin",
            "Date",
            "horizon",
            "raw_forecast",
            "operational_forecast",
            "actual_sales",
            "source_open",
            "forecast_available",
            "operational_forecast_available",
            "primary_evaluation_eligible",
            "candidate_id",
            "model_selection_run_id",
        ),
        required_columns=(
            "Store",
            "forecast_origin",
            "Date",
            "horizon",
            "raw_forecast",
            "operational_forecast",
            "actual_sales",
            "source_open",
            "forecast_available",
            "operational_forecast_available",
            "primary_evaluation_eligible",
            "candidate_id",
            "model_selection_run_id",
        ),
        primary_key=("Store", "forecast_origin", "Date"),
        max_rows=50_000,
        max_bytes=16_000_000,
        development_date_filter=True,
    ),
    ArtifactSelector.PHASE7_MODEL_COMPARISON: _ArtifactSpec(
        selector=ArtifactSelector.PHASE7_MODEL_COMPARISON,
        phase=Phase.PHASE7,
        filename="model_comparison.csv",
        file_format="csv",
        projection=_MODEL_COMPARISON_COLUMNS,
        required_columns=_MODEL_COMPARISON_COLUMNS,
        primary_key=(
            "candidate_id",
            "population",
            "paired_with",
            "scope",
            "validation_window",
            "horizon",
            "week_block_start_horizon",
            "week_block_end_horizon",
            "Store",
            "metric",
            "unavailable_reason",
        ),
        max_rows=200_000,
        max_bytes=32_000_000,
        csv_header=_MODEL_COMPARISON_COLUMNS,
        allow_null_key=True,
    ),
    ArtifactSelector.PHASE8_DAILY_INTERVALS: _ArtifactSpec(
        selector=ArtifactSelector.PHASE8_DAILY_INTERVALS,
        phase=Phase.PHASE8,
        filename="daily_intervals.parquet",
        file_format="parquet",
        projection=(
            "fit_id",
            "Store",
            "forecast_origin",
            "Date",
            "horizon",
            "interval_kind",
            "point_forecast",
            "lower",
            "upper",
            "width",
            "available",
            "unavailable_reason",
            "actual_sales",
            "assessment_source_open",
            "selected_candidate_id",
            "model_selection_run_id",
            "units",
            "schedule_assumption_flag",
        ),
        required_columns=(
            "fit_id",
            "Store",
            "forecast_origin",
            "Date",
            "horizon",
            "interval_kind",
            "point_forecast",
            "lower",
            "upper",
            "width",
            "available",
            "unavailable_reason",
            "actual_sales",
            "assessment_source_open",
            "selected_candidate_id",
            "model_selection_run_id",
            "units",
            "schedule_assumption_flag",
        ),
        primary_key=("fit_id", "Store", "forecast_origin", "Date", "interval_kind"),
        max_rows=65_000,
        max_bytes=8_000_000,
        development_date_filter=True,
    ),
    ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY: _ArtifactSpec(
        selector=ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY,
        phase=Phase.PHASE8,
        filename="cumulative_uncertainty.parquet",
        file_format="parquet",
        projection=(
            "fit_id",
            "Store",
            "forecast_origin",
            "k",
            "p",
            "selected_candidate_id",
            "model_selection_run_id",
            "units",
            "schedule_assumption_flag",
            "issued_prefix_complete",
            "issued_prefix_unavailable_reason",
            "D_k",
            "q_p_signed",
            "U_k",
            "SafetyStock_k",
            "Target_k",
        ),
        required_columns=(
            "fit_id",
            "Store",
            "forecast_origin",
            "k",
            "p",
            "selected_candidate_id",
            "model_selection_run_id",
            "units",
            "schedule_assumption_flag",
            "issued_prefix_complete",
            "issued_prefix_unavailable_reason",
            "D_k",
            "q_p_signed",
            "U_k",
            "SafetyStock_k",
            "Target_k",
        ),
        primary_key=("fit_id", "Store", "forecast_origin", "k", "p"),
        max_rows=100_000,
        max_bytes=8_000_000,
    ),
    ArtifactSelector.PHASE8_DAILY_QUANTILES: _ArtifactSpec(
        selector=ArtifactSelector.PHASE8_DAILY_QUANTILES,
        phase=Phase.PHASE8,
        filename="daily_residual_quantiles.csv",
        file_format="csv",
        projection=_DAILY_QUANTILE_COLUMNS,
        required_columns=_DAILY_QUANTILE_COLUMNS,
        primary_key=("fit_id", "horizon", "tail"),
        max_rows=100,
        max_bytes=100_000,
        csv_header=_DAILY_QUANTILE_COLUMNS,
    ),
    ArtifactSelector.PHASE8_CUMULATIVE_QUANTILES: _ArtifactSpec(
        selector=ArtifactSelector.PHASE8_CUMULATIVE_QUANTILES,
        phase=Phase.PHASE8,
        filename="cumulative_error_quantiles.csv",
        file_format="csv",
        projection=_CUMULATIVE_QUANTILE_COLUMNS,
        required_columns=_CUMULATIVE_QUANTILE_COLUMNS,
        primary_key=("fit_id", "k", "p"),
        max_rows=100,
        max_bytes=100_000,
        csv_header=_CUMULATIVE_QUANTILE_COLUMNS,
    ),
    ArtifactSelector.PHASE9_SCENARIO_CATALOG: _ArtifactSpec(
        selector=ArtifactSelector.PHASE9_SCENARIO_CATALOG,
        phase=Phase.PHASE9,
        filename="scenario_catalog.parquet",
        file_format="parquet",
        projection=(
            "scenario_id",
            "family",
            "mode",
            "forecast_origin",
            "replicate",
            "horizon_days",
            "schedule_mode",
            "demand_basis",
            "stress_spec_id",
            "calibration_transport_valid",
        ),
        required_columns=(
            "scenario_id",
            "family",
            "mode",
            "forecast_origin",
            "replicate",
            "horizon_days",
            "schedule_mode",
            "demand_basis",
            "stress_spec_id",
            "calibration_transport_valid",
        ),
        primary_key=("scenario_id",),
        max_rows=100,
        max_bytes=100_000,
    ),
    ArtifactSelector.PHASE10_COMPARISON: _ArtifactSpec(
        selector=ArtifactSelector.PHASE10_COMPARISON,
        phase=Phase.PHASE10,
        filename="comparison_summary.csv",
        file_format="csv",
        projection=_COMPARISON_SUMMARY_COLUMNS,
        required_columns=_COMPARISON_SUMMARY_COLUMNS,
        primary_key=("case_id", "metric"),
        max_rows=2_000,
        max_bytes=1_000_000,
        csv_header=_COMPARISON_SUMMARY_COLUMNS,
    ),
    ArtifactSelector.PHASE10_POLICY_SUMMARY: _ArtifactSpec(
        selector=ArtifactSelector.PHASE10_POLICY_SUMMARY,
        phase=Phase.PHASE10,
        filename="policy_summary.parquet",
        file_format="parquet",
        projection=_POLICY_SUMMARY_PROJECTION,
        required_columns=_POLICY_SUMMARY_PROJECTION,
        primary_key=("case_id", "Store", "policy_id"),
        max_rows=400_000,
        max_bytes=64_000_000,
    ),
    ArtifactSelector.PHASE10_POLICY_TARGETS: _ArtifactSpec(
        selector=ArtifactSelector.PHASE10_POLICY_TARGETS,
        phase=Phase.PHASE10,
        filename="policy_targets.parquet",
        file_format="parquet",
        projection=_POLICY_TARGETS_PROJECTION,
        required_columns=_POLICY_TARGETS_PROJECTION,
        primary_key=("case_id", "Store", "policy_id"),
        max_rows=400_000,
        max_bytes=32_000_000,
    ),
}

_PHASE7_EXPECTED_CANDIDATE = "global_lightgbm_gbdt_regression_l1"
_UPSTREAM_BINDINGS_FILENAME = "upstream_bindings.json"
_HISTORY_RELATIVE_PATH = Path("data/interim/train.parquet")
_KEY_ARROW_TYPES: dict[ArtifactSelector, dict[str, tuple[str, ...]]] = {
    ArtifactSelector.PHASE7_FORECASTS: {
        "Store": ("int64",),
        "forecast_origin": ("timestamp[ns]",),
        "Date": ("timestamp[ns]",),
    },
    ArtifactSelector.PHASE8_DAILY_INTERVALS: {
        "Store": ("int64",),
        "forecast_origin": ("timestamp[ns]",),
        "Date": ("timestamp[ns]",),
    },
    ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY: {
        "Store": ("int64",),
        "forecast_origin": ("timestamp[ns]",),
        "k": ("int64",),
        "p": ("double",),
    },
    ArtifactSelector.PHASE9_SCENARIO_CATALOG: {
        "scenario_id": ("string", "large_string"),
    },
    ArtifactSelector.PHASE10_POLICY_SUMMARY: {
        "case_id": ("string", "large_string"),
        "Store": ("int64",),
        "policy_id": ("string", "large_string"),
    },
    ArtifactSelector.PHASE10_POLICY_TARGETS: {
        "case_id": ("string", "large_string"),
        "Store": ("int64",),
        "policy_id": ("string", "large_string"),
    },
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}.")


class _ArtifactReader:
    """Internal reader with injectable trusted identities for isolated fixtures."""

    def __init__(
        self,
        *,
        root: Path | None = None,
        expected_runs: Mapping[Phase, CanonicalRunIdentity] | None = None,
    ) -> None:
        selected_root = repository_root() if root is None else Path(root)
        try:
            self._root = selected_root.resolve(strict=True)
        except OSError:
            raise RuntimeError("Could not resolve the internal repository root.") from None
        if not self._root.is_dir():
            raise RuntimeError("Could not resolve the internal repository root.")
        self._expected_runs = dict(CANONICAL_RUNS if expected_runs is None else expected_runs)
        if set(self._expected_runs) != set(Phase):
            raise ValueError(
                "The internal reader requires one trusted identity per canonical phase."
            )
        self._verified_output_fingerprints: dict[Path, tuple[int, int, int, int]] = {}

    def read(self, selector: ArtifactSelector) -> ArtifactTable:
        """Load one registered table; arbitrary filenames and column selections are rejected."""
        if not isinstance(selector, ArtifactSelector) or selector not in _ARTIFACTS:
            raise UnsupportedArtifactSelectorError()

        spec = _ARTIFACTS[selector]
        identity = self._expected_runs[spec.phase]
        manifest = self._read_manifest(identity, selector)
        metadata = self._output_metadata(manifest, spec)
        artifact_path = self._trusted_file(
            identity.manifest_relative_path.parent / spec.filename,
            selector,
            UnavailableReason.MISSING_ARTIFACT,
        )
        self._verify_output_file(artifact_path, metadata, spec, selector)

        if spec.file_format == "csv":
            frame = self._read_csv(artifact_path, metadata, spec, selector)
        else:
            frame = self._read_parquet(artifact_path, metadata, spec, selector)
        self._assert_unique_key(frame, spec, selector)
        return ArtifactTable(
            selector=selector,
            run_id=identity.run_id,
            manifest_sha256=identity.manifest_sha256,
            output_sha256=metadata["sha256"],
            frame=frame,
        )

    def read_history_sales(self, query: HistoryQuery) -> pd.DataFrame:
        """Read one bounded Store's Sales history through the frozen development cutoff."""
        selector = ArtifactSelector.HISTORICAL_SALES
        self._validate_history_query(query)
        path = self._trusted_file(
            _HISTORY_RELATIVE_PATH,
            selector,
            UnavailableReason.MISSING_ARTIFACT,
        )
        try:
            dataset = ds.dataset(path, format="parquet")
        except Exception:
            raise ArtifactSchemaError(selector) from None

        schema = dataset.schema
        required = set(HISTORY_PROJECTION)
        if not required.issubset(schema.names):
            raise ArtifactSchemaError(selector)
        store_type = schema.field("Store").type
        date_type = schema.field("Date").type
        if not pa.types.is_integer(store_type) or not self._supported_date_type(date_type):
            raise ArtifactSchemaError(selector)
        if not (
            pa.types.is_integer(schema.field("Sales").type)
            or pa.types.is_floating(schema.field("Sales").type)
        ):
            raise ArtifactSchemaError(selector)
        if not (
            pa.types.is_integer(schema.field("Open").type)
            or pa.types.is_floating(schema.field("Open").type)
        ):
            raise ArtifactSchemaError(selector)

        lower = self._date_scalar(query.start_date, date_type)
        if pa.types.is_timestamp(date_type) or pa.types.is_date64(date_type):
            upper = self._date_scalar(query.end_date + timedelta(days=1), date_type)
            date_filter = (ds.field("Date") >= lower) & (ds.field("Date") < upper)
        else:
            upper = self._date_scalar(query.end_date, date_type)
            date_filter = (ds.field("Date") >= lower) & (ds.field("Date") <= upper)
        predicate = (ds.field("Store") == pa.scalar(query.store_id, type=store_type)) & date_filter
        try:
            table = dataset.scanner(
                columns=list(HISTORY_PROJECTION),
                filter=predicate,
                batch_size=65_536,
                use_threads=False,
            ).head(MAX_HISTORY_ROWS + 1)
        except Exception:
            raise ArtifactSchemaError(selector) from None

        if table.num_rows > MAX_HISTORY_ROWS:
            raise InvalidArtifactRequestError(selector)
        frame = table.to_pandas()
        if tuple(frame.columns) != HISTORY_PROJECTION:
            raise ArtifactSchemaError(selector)
        if frame.empty:
            return frame
        frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
        if (
            frame["Date"]
            .gt(
                pd.Timestamp(DEVELOPMENT_CUTOFF)
                + pd.Timedelta(days=1)
                - pd.Timedelta(nanoseconds=1)
            )
            .any()
        ):
            raise ArtifactIntegrityError(selector)
        if frame["Store"].ne(query.store_id).any():
            raise ArtifactIntegrityError(selector)
        if frame.duplicated(["Store", "Date"]).any():
            raise DuplicateArtifactKeyError(selector)
        return frame

    def _validate_history_query(self, query: HistoryQuery) -> None:
        selector = ArtifactSelector.HISTORICAL_SALES
        if not isinstance(query, HistoryQuery):
            raise InvalidArtifactRequestError(selector)
        if (
            isinstance(query.store_id, bool)
            or not isinstance(query.store_id, int)
            or not 1 <= query.store_id <= MAX_STORE_ID
        ):
            raise InvalidArtifactRequestError(selector)
        if (
            type(query.start_date) is not date
            or type(query.end_date) is not date
            or query.start_date > query.end_date
            or query.end_date > DEVELOPMENT_CUTOFF
            or (query.end_date - query.start_date).days + 1 > MAX_HISTORY_DAYS
        ):
            raise InvalidArtifactRequestError(selector)

    @staticmethod
    def _supported_date_type(dtype: pa.DataType) -> bool:
        return pa.types.is_date(dtype) or pa.types.is_timestamp(dtype)

    @staticmethod
    def _date_scalar(value: date, dtype: pa.DataType) -> pa.Scalar:
        if pa.types.is_timestamp(dtype) or pa.types.is_date64(dtype):
            value_for_type: date | datetime = datetime.combine(value, time.min)
        else:
            value_for_type = value
        return pa.scalar(value_for_type, type=dtype)

    def _read_manifest(
        self, identity: CanonicalRunIdentity, selector: ArtifactSelector
    ) -> dict[str, Any]:
        path = self._trusted_file(
            identity.manifest_relative_path,
            selector,
            UnavailableReason.MISSING_MANIFEST,
        )
        try:
            if path.stat().st_size > MAX_MANIFEST_BYTES:
                raise ArtifactIntegrityError(selector)
            payload = path.read_bytes()
        except ArtifactReadError:
            raise
        except OSError:
            raise ArtifactUnavailableError(selector, UnavailableReason.MISSING_MANIFEST) from None
        if hashlib.sha256(payload).hexdigest() != identity.manifest_sha256:
            raise ArtifactIntegrityError(selector)
        try:
            manifest = json.loads(payload.decode("utf-8"), parse_constant=_reject_json_constant)
        except ValueError:
            raise ArtifactIntegrityError(selector) from None
        if not isinstance(manifest, dict):
            raise ArtifactIntegrityError(selector)
        if manifest.get(identity.run_id_field) != identity.run_id:
            raise ArtifactIntegrityError(selector)
        self._validate_manifest(identity.phase, manifest, selector)
        return manifest

    def _validate_manifest(
        self, phase: Phase, manifest: dict[str, Any], selector: ArtifactSelector
    ) -> None:
        expected = self._expected_runs
        if phase is Phase.PHASE7:
            bounds = manifest.get("date_bounds")
            if (
                manifest.get("status") != "selected"
                or manifest.get("publication_state") != "complete"
                or manifest.get("selected_candidate_id") != _PHASE7_EXPECTED_CANDIDATE
                or manifest.get("final_holdout_outcomes_read_or_hashed") is not False
                or not isinstance(bounds, dict)
                or bounds.get("last_development_target") != DEVELOPMENT_CUTOFF.isoformat()
                or bounds.get("final_holdout_start") != "2015-07-04"
            ):
                raise ArtifactIntegrityError(selector)
            return

        if phase is Phase.PHASE8:
            inputs = manifest.get("inputs")
            boundaries = manifest.get("boundaries")
            phase7 = expected[Phase.PHASE7]
            if (
                manifest.get("status") != "complete_with_unavailable_strata"
                or manifest.get("selection_run_id") != phase7.run_id
                or manifest.get("selected_candidate_id") != _PHASE7_EXPECTED_CANDIDATE
                or not isinstance(inputs, dict)
                or inputs.get("selection_manifest_sha256") != phase7.manifest_sha256
                or inputs.get("selection_run_id") != phase7.run_id
                or not isinstance(boundaries, dict)
                or boundaries.get("development_cutoff_inclusive") != DEVELOPMENT_CUTOFF.isoformat()
                or boundaries.get("holdout_open_sales_customers_opened_loaded_or_hashed")
                is not False
            ):
                raise ArtifactIntegrityError(selector)
            # fit_b_quantiles_frozen is a historical manifest flag; later accepted governance
            # freezes this exact run and hashes, so that flag must not invalidate this identity.
            return

        if phase is Phase.PHASE9:
            inputs = manifest.get("inputs")
            boundaries = manifest.get("boundaries")
            phase7 = expected[Phase.PHASE7]
            phase8 = expected[Phase.PHASE8]
            if (
                manifest.get("status") != "complete"
                or not isinstance(inputs, dict)
                or inputs.get("phase7_selection_manifest_sha256") != phase7.manifest_sha256
                or inputs.get("phase8_manifest_sha256") != phase8.manifest_sha256
                or not isinstance(boundaries, dict)
                or boundaries.get("development_cutoff_inclusive") != DEVELOPMENT_CUTOFF.isoformat()
                or boundaries.get("protected_holdout_values_read_or_hashed") is not False
            ):
                raise ArtifactIntegrityError(selector)
            self._validate_phase9_bindings(manifest, selector)
            return

        inputs = manifest.get("inputs")
        boundaries = manifest.get("boundaries")
        phase7 = expected[Phase.PHASE7]
        phase8 = expected[Phase.PHASE8]
        phase9 = expected[Phase.PHASE9]
        if (
            manifest.get("status") != "complete"
            or not isinstance(inputs, dict)
            or inputs.get("phase7_run_id") != phase7.run_id
            or inputs.get("phase7_selection_manifest_sha256") != phase7.manifest_sha256
            or inputs.get("phase8_run_id") != phase8.run_id
            or inputs.get("phase8_manifest_sha256") != phase8.manifest_sha256
            or inputs.get("phase9_run_id") != phase9.run_id
            or inputs.get("phase9_manifest_sha256") != phase9.manifest_sha256
            or not isinstance(boundaries, dict)
            or boundaries.get("allowed_outcome_through") != DEVELOPMENT_CUTOFF.isoformat()
            or boundaries.get("protected_holdout_values_read_or_hashed") is not False
        ):
            raise ArtifactIntegrityError(selector)

    def _validate_phase9_bindings(
        self, manifest: dict[str, Any], selector: ArtifactSelector
    ) -> None:
        metadata = manifest.get("upstream_bindings")
        if (
            not isinstance(metadata, dict)
            or metadata.get("path") != _UPSTREAM_BINDINGS_FILENAME
            or not _is_sha256(metadata.get("sha256"))
            or not _is_sha256(metadata.get("canonical_sha256"))
        ):
            raise ArtifactIntegrityError(selector)
        path = self._trusted_file(
            self._expected_runs[Phase.PHASE9].manifest_relative_path.parent
            / _UPSTREAM_BINDINGS_FILENAME,
            selector,
            UnavailableReason.MISSING_ARTIFACT,
        )
        try:
            if path.stat().st_size > MAX_BINDINGS_BYTES:
                raise ArtifactIntegrityError(selector)
            payload = path.read_bytes()
        except ArtifactReadError:
            raise
        except OSError:
            raise ArtifactUnavailableError(selector, UnavailableReason.MISSING_ARTIFACT) from None
        if hashlib.sha256(payload).hexdigest() != metadata["sha256"]:
            raise ArtifactIntegrityError(selector)
        try:
            bindings = json.loads(payload.decode("utf-8"), parse_constant=_reject_json_constant)
        except ValueError:
            raise ArtifactIntegrityError(selector) from None
        if not isinstance(bindings, dict):
            raise ArtifactIntegrityError(selector)

        phase7 = bindings.get("phase7")
        phase8 = bindings.get("phase8")
        boundary = bindings.get("boundary_checks")
        inputs = manifest.get("inputs")
        if (
            hashlib.sha256(
                json.dumps(
                    {
                        key: value
                        for key, value in bindings.items()
                        if key not in {"canonical_sha256", "run_id", "created_at_utc"}
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
            != metadata["canonical_sha256"]
            or not isinstance(phase7, dict)
            or phase7.get("selection_manifest_sha256")
            != self._expected_runs[Phase.PHASE7].manifest_sha256
            or phase7.get("selection_run_id") != self._expected_runs[Phase.PHASE7].run_id
            or not isinstance(phase8, dict)
            or phase8.get("manifest_sha256") != self._expected_runs[Phase.PHASE8].manifest_sha256
            or phase8.get("run_id") != self._expected_runs[Phase.PHASE8].run_id
            or not isinstance(boundary, dict)
            or boundary.get("protected_holdout_values_read_or_hashed") is not False
            or not isinstance(inputs, dict)
            or inputs.get("phase7_selection_manifest_sha256")
            != self._expected_runs[Phase.PHASE7].manifest_sha256
            or inputs.get("phase8_manifest_sha256")
            != self._expected_runs[Phase.PHASE8].manifest_sha256
        ):
            raise ArtifactIntegrityError(selector)

    def _output_metadata(self, manifest: dict[str, Any], spec: _ArtifactSpec) -> dict[str, Any]:
        selector = spec.selector
        outputs = manifest.get("outputs")
        if not isinstance(outputs, dict):
            raise ArtifactIntegrityError(selector)
        metadata = outputs.get(spec.filename)
        if not isinstance(metadata, dict):
            raise ArtifactUnavailableError(selector, UnavailableReason.MISSING_ARTIFACT)
        if not _is_sha256(metadata.get("sha256")):
            raise ArtifactIntegrityError(selector)
        rows = metadata.get("rows")
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 0 or rows > spec.max_rows:
            raise ArtifactIntegrityError(selector)
        if "path" in metadata and metadata["path"] != spec.filename:
            raise ArtifactIntegrityError(selector)
        return metadata

    def _trusted_file(
        self,
        relative: Path,
        selector: ArtifactSelector,
        missing_reason: UnavailableReason,
    ) -> Path:
        relative_posix = PurePosixPath(relative.as_posix())
        if relative_posix.is_absolute() or any(
            part in {"", ".", ".."} for part in relative_posix.parts
        ):
            raise UnsafeArtifactPathError(selector)
        current = self._root
        try:
            for index, part in enumerate(relative_posix.parts):
                current = current / part
                info = current.lstat()
                if stat.S_ISLNK(info.st_mode):
                    raise UnsafeArtifactPathError(selector)
                if index < len(relative_posix.parts) - 1 and not stat.S_ISDIR(info.st_mode):
                    raise ArtifactUnavailableError(selector, missing_reason)
                if index == len(relative_posix.parts) - 1 and not stat.S_ISREG(info.st_mode):
                    raise ArtifactUnavailableError(selector, missing_reason)
            resolved = current.resolve(strict=True)
        except ArtifactReadError:
            raise
        except FileNotFoundError:
            raise ArtifactUnavailableError(selector, missing_reason) from None
        except (OSError, RuntimeError):
            raise UnsafeArtifactPathError(selector) from None
        if not resolved.is_relative_to(self._root):
            raise UnsafeArtifactPathError(selector)
        return resolved

    def _fingerprint(self, path: Path) -> tuple[int, int, int, int]:
        info = path.stat()
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)

    def _verify_output_file(
        self,
        path: Path,
        metadata: dict[str, Any],
        spec: _ArtifactSpec,
        selector: ArtifactSelector,
    ) -> None:
        try:
            before = self._fingerprint(path)
        except OSError:
            raise ArtifactUnavailableError(selector, UnavailableReason.MISSING_ARTIFACT) from None
        if before[2] > spec.max_bytes:
            raise ArtifactIntegrityError(selector)
        for size_field in ("bytes", "byte_length"):
            expected_size = metadata.get(size_field)
            if expected_size is not None and expected_size != before[2]:
                raise ArtifactIntegrityError(selector)

        cached = self._verified_output_fingerprints.get(path)
        if cached == before:
            return

        try:
            actual_hash = _sha256_file(path)
            after = self._fingerprint(path)
        except OSError:
            raise ArtifactUnavailableError(selector, UnavailableReason.MISSING_ARTIFACT) from None
        if before != after or actual_hash != metadata["sha256"]:
            raise ArtifactIntegrityError(selector)
        # Immutable local outputs are memoized per reader. Device, inode, size and nanosecond
        # mtime changes invalidate the digest and force verification again.
        self._verified_output_fingerprints[path] = after

    def _read_csv(
        self,
        path: Path,
        metadata: dict[str, Any],
        spec: _ArtifactSpec,
        selector: ArtifactSelector,
    ) -> pd.DataFrame:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader(stream), None)
        except (OSError, UnicodeDecodeError, csv.Error):
            raise ArtifactSchemaError(selector) from None
        if (
            header is None
            or len(header) != len(set(header))
            or not set(spec.required_columns).issubset(header)
            or (spec.csv_header is not None and tuple(header) != spec.csv_header)
        ):
            raise ArtifactSchemaError(selector)
        try:
            frame = pd.read_csv(
                path,
                usecols=list(spec.projection),
                nrows=metadata["rows"] + 1,
                encoding="utf-8-sig",
                keep_default_na=True,
                low_memory=False,
            )
        except Exception:
            raise ArtifactSchemaError(selector) from None
        if len(frame) != metadata["rows"]:
            raise ArtifactIntegrityError(selector)
        return frame.loc[:, list(spec.projection)]

    def _read_parquet(
        self,
        path: Path,
        metadata: dict[str, Any],
        spec: _ArtifactSpec,
        selector: ArtifactSelector,
    ) -> pd.DataFrame:
        try:
            parquet = pq.ParquetFile(path)
            schema = parquet.schema_arrow
            num_rows = parquet.metadata.num_rows
        except Exception:
            raise ArtifactSchemaError(selector) from None
        if num_rows != metadata["rows"]:
            raise ArtifactIntegrityError(selector)
        if not set(spec.required_columns).issubset(schema.names):
            raise ArtifactSchemaError(selector)

        output_schema = metadata.get("columns")
        if output_schema is None and isinstance(metadata.get("schema"), list):
            output_schema = [
                field.get("name")
                for field in metadata["schema"]
                if isinstance(field, dict) and isinstance(field.get("name"), str)
            ]
        if output_schema is not None and (
            not isinstance(output_schema, list)
            or not all(isinstance(name, str) for name in output_schema)
            or schema.names != output_schema
        ):
            raise ArtifactSchemaError(selector)
        if isinstance(metadata.get("schema"), list):
            for field in metadata["schema"]:
                if not isinstance(field, dict) or not isinstance(field.get("name"), str):
                    raise ArtifactSchemaError(selector)
                if not isinstance(field.get("type"), str):
                    raise ArtifactSchemaError(selector)
                if (
                    field["name"] not in schema.names
                    or str(schema.field(field["name"]).type) != field["type"]
                ):
                    raise ArtifactSchemaError(selector)
        for name, expected_types in _KEY_ARROW_TYPES.get(selector, {}).items():
            if name not in schema.names or str(schema.field(name).type) not in expected_types:
                raise ArtifactSchemaError(selector)

        try:
            dataset = ds.dataset(path, format="parquet")
            predicate = None
            if spec.development_date_filter:
                date_type = dataset.schema.field("Date").type
                if not self._supported_date_type(date_type):
                    raise ArtifactSchemaError(selector)
                next_day = DEVELOPMENT_CUTOFF + timedelta(days=1)
                upper = self._date_scalar(next_day, date_type)
                predicate = ds.field("Date") < upper
            table = dataset.scanner(
                columns=list(spec.projection),
                filter=predicate,
                batch_size=65_536,
                use_threads=False,
            ).head(spec.max_rows + 1)
        except ArtifactReadError:
            raise
        except Exception:
            raise ArtifactSchemaError(selector) from None
        if table.num_rows != metadata["rows"]:
            raise ArtifactIntegrityError(selector)
        try:
            frame = table.to_pandas()
        except Exception:
            raise ArtifactSchemaError(selector) from None
        if tuple(frame.columns) != spec.projection:
            raise ArtifactSchemaError(selector)
        return frame

    @staticmethod
    def _assert_unique_key(
        frame: pd.DataFrame, spec: _ArtifactSpec, selector: ArtifactSelector
    ) -> None:
        keys = list(spec.primary_key)
        if (not spec.allow_null_key and frame[keys].isna().any(axis=None)) or frame.duplicated(
            keys
        ).any():
            raise DuplicateArtifactKeyError(selector)


_DEFAULT_READER = _ArtifactReader()


def read_canonical_artifact(selector: ArtifactSelector) -> ArtifactTable:
    """Read one fixed canonical result set with integrity and schema verification."""
    return _DEFAULT_READER.read(selector)


def read_historical_sales(query: HistoryQuery) -> pd.DataFrame:
    """Read a single Store's projected Sales history through 2015-07-03."""
    return _DEFAULT_READER.read_history_sales(query)
