"""Synthetic-only Phase 13 frozen uncertainty, schedule, and target adapters.

This module accepts only in-memory M2 issuances, typed synthetic planned schedules,
independently generated synthetic quantile fixtures, and synthetic mean anchors. It does
not load or inspect Phase 8/9 artifacts or any Rossmann source.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.forecasting.lightgbm import MODEL_NAME
from rossmann_forecasting.forecasting.model_selection import CANDIDATE_IDS
from rossmann_forecasting.phase13.contracts import (
    HORIZON,
    SUPPORTED_ORIGINS,
    SYNTHETIC_OPEN_RULE_ID,
    AvailabilityAssumption,
    ForecastOrigin,
    RequestedForecastGrid,
    SourceProvenance,
    SyntheticPlannedOpen,
)
from rossmann_forecasting.phase13.issuer import (
    NUM_BOOST_ROUND,
    RawForecastIssuance,
    _frozen_recipe,
    _identity,
    _schema_identity,
)

FIT_B_ID = "fit_b"
FIT_B_RUN_ID = "phase8-impl-20261006-provenance-review"
DAILY_ERROR_POPULATION = "raw_primary_source_open_1_signed_sales_error"
CUMULATIVE_ERROR_POPULATION = "complete_operational_signed_sales_prefix_error"
PREFIX_DEFINITION = "exact_h1_through_k_complete_origin_anchored_path"
HISTORICAL_SCHEDULE_ASSUMPTION = "saved_source_open_assumed_known_at_origin"
UNCERTAINTY_POLICY_VERSION = "phase-8-uncertainty-v1"
CALIBRATION_WINDOWS = "validation_1+validation_2"
DAILY_TAILS = {"lower": 0.025, "upper": 0.975}
CUMULATIVE_LEVELS = (0.90, 0.95, 0.98)
LEAD_TIMES = tuple(range(2, 8))
REVIEW_PERIOD = 1
POLICY_IDS = (
    "historical_mean_standing_target",
    "lightgbm_buffer_standing_target",
)
SYNTHETIC_TARGET_SEMANTICS = "synthetic_turnover_inventory_value_proxy"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DAILY_COLUMNS = (
    "fit_id",
    "horizon",
    "tail",
    "tail_level",
    "error_population",
    "n",
    "rank_1_indexed",
    "signed_quantile",
    "available",
    "unavailable_reason",
    "policy_version",
    "selected_candidate_id",
    "calibration_windows",
)
_CUMULATIVE_COLUMNS = (
    "fit_id",
    "k",
    "p",
    "error_population",
    "n",
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
TARGET_COLUMNS = (
    "Store",
    "forecast_origin",
    "model_identity",
    "model_fit_identity",
    "fresh_model_fit_identity",
    "calibration_fit_identity",
    "calibration_run_id",
    "calibration_manifest_sha256",
    "calibration_daily_table_sha256",
    "calibration_cumulative_table_sha256",
    "calibration_policy_config_sha256",
    "calibration_config_sha256",
    "daily_fixture_sha256",
    "cumulative_fixture_sha256",
    "quantile_fixture_identity",
    "transport_status",
    "calibration_transport_valid",
    "schedule_identity",
    "schedule_rule_id",
    "schedule_source_id",
    "schedule_version",
    "schedule_provenance",
    "schedule_availability_assumption",
    "anchor_collection_identity",
    "anchor_identity",
    "anchor_store_id",
    "anchor_origin",
    "anchor_source_id",
    "anchor_version",
    "anchor_provenance",
    "anchor_availability_assumption",
    "anchor_parent_identities",
    "anchor_available",
    "anchor_unavailable_reason",
    "mean_open_sales_value",
    "anchor_semantics",
    "open_days_in_protection_period",
    "lead_time",
    "review_period",
    "protection_period",
    "buffer_probability",
    "cumulative_signed_quantile",
    "quantile_available",
    "quantile_unavailable_reason",
    "forecast_protection_demand_value",
    "upper_turnover_value",
    "safety_stock_value",
    "input_semantics",
    "issuance_identity",
    "policy_id",
    "target_value",
    "target_available",
    "availability_reason",
    "buffer_interpretation",
)
_RAW_REQUIRED_COLUMNS = {
    "requested_key",
    "Store",
    "Date",
    "forecast_origin",
    "horizon",
    "model",
    "raw_forecast",
    "unclipped_forecast",
    "recursive_state_value",
    "forecast_was_clipped",
    "forecast_available",
    "unavailable_reason",
    "model_identity",
    "fit_identity",
    "recipe_identity",
    "feature_schema_identity",
    "requested_grid_identity",
    "training_input_identity",
    "recursive_history_identity",
    "future_covariate_identity",
}
_FORBIDDEN_INPUT_NAMES = {
    "sales",
    "customers",
    "open",
    "open_resolved",
    "actual_sales",
    "actual_open",
    "scenarioopen",
    "syntheticdemandvalue",
    "residual",
    "residuals",
}


class Phase13AdapterError(ValueError):
    """Raised when synthetic M3 adapter inputs violate the frozen contracts."""


@dataclass(frozen=True, slots=True)
class FitBCanonicalMetadata:
    """Pinned historical identities from accepted documentation, without file access."""

    calibration_fit_id: str
    run_id: str
    manifest_sha256: str
    daily_table_sha256: str
    cumulative_table_sha256: str
    policy_config_sha256: str
    calibration_config_sha256: str


FROZEN_FIT_B_METADATA = FitBCanonicalMetadata(
    calibration_fit_id=FIT_B_ID,
    run_id=FIT_B_RUN_ID,
    manifest_sha256="63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2",
    daily_table_sha256="5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8",
    cumulative_table_sha256="1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff",
    policy_config_sha256="49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93",
    calibration_config_sha256="afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08",
)


@dataclass(frozen=True, slots=True)
class FitBTransportMetadata:
    """Declared compatibility profile for the unvalidated June-to-July transport."""

    selected_model_id: str
    recipe_identity: str
    feature_schema_identity: str
    daily_error_population: str = DAILY_ERROR_POPULATION
    cumulative_error_population: str = CUMULATIVE_ERROR_POPULATION
    prefix_definition: str = PREFIX_DEFINITION
    historical_schedule_assumption: str = HISTORICAL_SCHEDULE_ASSUMPTION
    application_schedule_rule_id: str = SYNTHETIC_OPEN_RULE_ID
    transport_status: str = "unvalidated_june_fit_b_to_july_assumption"


@dataclass(frozen=True, slots=True, init=False)
class SyntheticFitBQuantileFixture:
    """Defensive, hash-checked synthetic rows shaped like frozen Fit B tables.

    Fixture hashes identify only these independently generated test rows. The pinned
    historical hashes in calibration_metadata are governance metadata and are never
    compared with or represented by the synthetic content hashes.
    """

    fixture_id: str
    calibration_metadata: FitBCanonicalMetadata
    transport: FitBTransportMetadata
    daily_fixture_sha256: str
    cumulative_fixture_sha256: str
    fixture_identity: str
    content_classification: str
    _daily: pd.DataFrame
    _cumulative: pd.DataFrame

    def __init__(
        self,
        daily: pd.DataFrame,
        cumulative: pd.DataFrame,
        *,
        fixture_id: str,
        transport: FitBTransportMetadata,
        calibration_metadata: FitBCanonicalMetadata = FROZEN_FIT_B_METADATA,
        expected_daily_fixture_sha256: str | None = None,
        expected_cumulative_fixture_sha256: str | None = None,
    ) -> None:
        if not isinstance(fixture_id, str) or not fixture_id.startswith("synthetic://phase13/"):
            raise Phase13AdapterError("Quantile content must use a synthetic fixture identity.")
        if calibration_metadata != FROZEN_FIT_B_METADATA:
            raise Phase13AdapterError("Pinned historical Fit B metadata identity mismatch.")
        if not isinstance(transport, FitBTransportMetadata):
            raise Phase13AdapterError("Fit B transport metadata must be typed.")
        daily_copy = _validated_daily_table(daily)
        cumulative_copy = _validated_cumulative_table(cumulative)
        daily_hash = _table_sha256(daily_copy, _DAILY_COLUMNS, ("horizon", "tail"))
        cumulative_hash = _table_sha256(cumulative_copy, _CUMULATIVE_COLUMNS, ("k", "p"))
        if (
            expected_daily_fixture_sha256 is not None
            and expected_daily_fixture_sha256 != daily_hash
        ):
            raise Phase13AdapterError("Synthetic daily fixture SHA-256 does not match content.")
        if (
            expected_cumulative_fixture_sha256 is not None
            and expected_cumulative_fixture_sha256 != cumulative_hash
        ):
            raise Phase13AdapterError(
                "Synthetic cumulative fixture SHA-256 does not match content."
            )
        fixture_identity = _digest(
            {
                "fixture_id": fixture_id,
                "content_classification": "synthetic_fixture_content_only",
                "daily_fixture_sha256": daily_hash,
                "cumulative_fixture_sha256": cumulative_hash,
            }
        )
        object.__setattr__(self, "fixture_id", fixture_id)
        object.__setattr__(self, "calibration_metadata", calibration_metadata)
        object.__setattr__(self, "transport", transport)
        object.__setattr__(self, "daily_fixture_sha256", daily_hash)
        object.__setattr__(self, "cumulative_fixture_sha256", cumulative_hash)
        object.__setattr__(self, "fixture_identity", fixture_identity)
        object.__setattr__(self, "content_classification", "synthetic_fixture_content_only")
        object.__setattr__(self, "_daily", daily_copy)
        object.__setattr__(self, "_cumulative", cumulative_copy)

    def daily_to_frame(self) -> pd.DataFrame:
        """Return an independent copy of the synthetic daily table."""

        return self._daily.copy(deep=True)

    def cumulative_to_frame(self) -> pd.DataFrame:
        """Return an independent copy of the synthetic cumulative table."""

        return self._cumulative.copy(deep=True)


@dataclass(frozen=True, slots=True)
class SyntheticHistoricalMeanAnchor:
    """One synthetic mean anchor bound to a single Store and Phase 13 origin."""

    store_id: int
    forecast_origin: date
    identity: str
    provenance: SourceProvenance
    available: bool
    mean_open_sales_value: float | None
    unavailable_reason: str | None = None
    semantics: str = SYNTHETIC_TARGET_SEMANTICS
    synthetic_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity.startswith(
            "synthetic://phase13/"
        ):
            raise Phase13AdapterError("Target anchor must have a synthetic fixture identity.")
        try:
            grid = RequestedForecastGrid(self.forecast_origin, (self.store_id,))
        except (TypeError, ValueError) as exc:
            raise Phase13AdapterError("Target anchor Store/origin binding is invalid.") from exc
        if not isinstance(self.provenance, SourceProvenance):
            raise Phase13AdapterError("Target anchor requires typed source provenance.")
        if self.provenance.availability_assumption != AvailabilityAssumption.SYNTHETIC_RULE:
            raise Phase13AdapterError("Target anchor provenance must identify synthetic input.")
        if not isinstance(self.available, (bool, np.bool_)):
            raise Phase13AdapterError("Target anchor availability must be explicit Boolean.")
        if self.synthetic_only is not True:
            raise Phase13AdapterError("Target construction accepts synthetic anchors only.")
        if self.semantics != SYNTHETIC_TARGET_SEMANTICS:
            raise Phase13AdapterError("Target anchor turnover semantics are incompatible.")
        object.__setattr__(self, "store_id", grid.store_ids[0])
        object.__setattr__(self, "forecast_origin", grid.origin.value)
        object.__setattr__(self, "available", bool(self.available))
        if self.available:
            value = _finite_number(self.mean_open_sales_value, "mean_open_sales_value")
            if value < 0 or self.unavailable_reason is not None:
                raise Phase13AdapterError("Available synthetic anchor has invalid value/reason.")
            object.__setattr__(self, "mean_open_sales_value", value)
        elif self.mean_open_sales_value is not None or not _nonempty_reason(
            self.unavailable_reason
        ):
            raise Phase13AdapterError("Unavailable synthetic anchor requires only a reason.")


@dataclass(frozen=True, slots=True, init=False)
class SyntheticHistoricalMeanAnchorCollection:
    """Origin-bound anchors for an exact requested Store universe; missing keys stay missing."""

    origin: date
    store_ids: tuple[int, ...]
    anchors: tuple[SyntheticHistoricalMeanAnchor, ...]
    identity: str

    def __init__(
        self,
        *,
        origin: date,
        store_ids: tuple[int, ...],
        anchors: tuple[SyntheticHistoricalMeanAnchor, ...],
    ) -> None:
        try:
            grid = RequestedForecastGrid(origin, tuple(store_ids))
            anchor_values = tuple(anchors)
        except (TypeError, ValueError) as exc:
            raise Phase13AdapterError(
                "Target anchor collection origin/universe is invalid."
            ) from exc
        if any(not isinstance(anchor, SyntheticHistoricalMeanAnchor) for anchor in anchor_values):
            raise Phase13AdapterError("Target anchor collection contains an untyped anchor.")
        keys = [(anchor.store_id, anchor.forecast_origin) for anchor in anchor_values]
        if len(keys) != len(set(keys)):
            raise Phase13AdapterError(
                "Target anchor collection contains duplicate Store/origin keys."
            )
        if any(anchor.forecast_origin != grid.origin.value for anchor in anchor_values):
            raise Phase13AdapterError("Target anchor collection contains a cross-origin anchor.")
        if any(anchor.store_id not in grid.store_ids for anchor in anchor_values):
            raise Phase13AdapterError("Target anchor Store is outside the requested universe.")
        if len({anchor.identity for anchor in anchor_values}) != len(anchor_values):
            raise Phase13AdapterError(
                "Target anchor identities must be unique within the collection."
            )
        payload = {
            "contract": "phase13-synthetic-mean-anchor-collection-v1",
            "origin": grid.origin.value.isoformat(),
            "store_ids": grid.store_ids,
            "anchors": [
                {
                    "store_id": anchor.store_id,
                    "origin": anchor.forecast_origin.isoformat(),
                    "identity": anchor.identity,
                    "available": anchor.available,
                    "mean_open_sales_value": anchor.mean_open_sales_value,
                    "unavailable_reason": anchor.unavailable_reason,
                    "semantics": anchor.semantics,
                    "provenance": {
                        "source_id": anchor.provenance.source_id,
                        "version": anchor.provenance.version,
                        "provenance": anchor.provenance.provenance,
                        "availability_assumption": (
                            anchor.provenance.availability_assumption.value
                        ),
                        "parent_identities": anchor.provenance.parent_identities,
                    },
                }
                for anchor in sorted(anchor_values, key=lambda row: row.store_id)
            ],
        }
        object.__setattr__(self, "origin", grid.origin.value)
        object.__setattr__(self, "store_ids", grid.store_ids)
        object.__setattr__(self, "anchors", anchor_values)
        object.__setattr__(self, "identity", _digest(payload))

    def for_store(self, store_id: int) -> SyntheticHistoricalMeanAnchor | None:
        """Return the exact origin-bound anchor, or None when that Store key is absent."""

        return next((anchor for anchor in self.anchors if anchor.store_id == store_id), None)


@dataclass(frozen=True, slots=True, init=False)
class Phase13M3Issuance:
    """Immutable in-memory M3 result for one exact July-origin H14 block."""

    origin: date
    raw_issuance_identity: str
    issuance_identity: str
    grid_identity: str
    model_identity: str
    fresh_model_fit_identity: str
    recipe_identity: str
    feature_schema_identity: str
    input_identities: tuple[tuple[str, str], ...]
    schedule_identity: str
    schedule_rule_id: str
    quantile_fixture_identity: str
    daily_fixture_sha256: str
    cumulative_fixture_sha256: str
    calibration_metadata: FitBCanonicalMetadata
    transport_status: str
    _records: pd.DataFrame
    _prefixes: pd.DataFrame

    def __init__(
        self,
        *,
        origin: date,
        raw_issuance_identity: str,
        issuance_identity: str,
        grid_identity: str,
        model_identity: str,
        fresh_model_fit_identity: str,
        recipe_identity: str,
        feature_schema_identity: str,
        input_identities: tuple[tuple[str, str], ...],
        schedule_identity: str,
        schedule_rule_id: str,
        quantile_fixture_identity: str,
        daily_fixture_sha256: str,
        cumulative_fixture_sha256: str,
        calibration_metadata: FitBCanonicalMetadata,
        transport_status: str,
        records: pd.DataFrame,
        prefixes: pd.DataFrame,
    ) -> None:
        if not isinstance(records, pd.DataFrame) or not isinstance(prefixes, pd.DataFrame):
            raise Phase13AdapterError("M3 results require table outputs.")
        _reject_forbidden_columns(records, "M3 records")
        _reject_forbidden_columns(prefixes, "M3 prefixes")
        _validate_m3_result_snapshot(
            origin=origin,
            raw_issuance_identity=raw_issuance_identity,
            issuance_identity=issuance_identity,
            grid_identity=grid_identity,
            model_identity=model_identity,
            fresh_model_fit_identity=fresh_model_fit_identity,
            recipe_identity=recipe_identity,
            feature_schema_identity=feature_schema_identity,
            input_identities=tuple(input_identities),
            schedule_identity=schedule_identity,
            schedule_rule_id=schedule_rule_id,
            quantile_fixture_identity=quantile_fixture_identity,
            daily_fixture_sha256=daily_fixture_sha256,
            cumulative_fixture_sha256=cumulative_fixture_sha256,
            calibration_metadata=calibration_metadata,
            transport_status=transport_status,
            records=records,
            prefixes=prefixes,
        )
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "raw_issuance_identity", raw_issuance_identity)
        object.__setattr__(self, "issuance_identity", issuance_identity)
        object.__setattr__(self, "grid_identity", grid_identity)
        object.__setattr__(self, "model_identity", model_identity)
        object.__setattr__(self, "fresh_model_fit_identity", fresh_model_fit_identity)
        object.__setattr__(self, "recipe_identity", recipe_identity)
        object.__setattr__(self, "feature_schema_identity", feature_schema_identity)
        object.__setattr__(self, "input_identities", tuple(input_identities))
        object.__setattr__(self, "schedule_identity", schedule_identity)
        object.__setattr__(self, "schedule_rule_id", schedule_rule_id)
        object.__setattr__(self, "quantile_fixture_identity", quantile_fixture_identity)
        object.__setattr__(self, "daily_fixture_sha256", daily_fixture_sha256)
        object.__setattr__(self, "cumulative_fixture_sha256", cumulative_fixture_sha256)
        object.__setattr__(self, "calibration_metadata", calibration_metadata)
        object.__setattr__(self, "transport_status", transport_status)
        object.__setattr__(self, "_records", records.copy(deep=True).reset_index(drop=True))
        object.__setattr__(self, "_prefixes", prefixes.copy(deep=True).reset_index(drop=True))

    def to_frame(self) -> pd.DataFrame:
        """Return a copy containing the original M2 raw records plus M3 projections."""

        return self._records.copy(deep=True)

    def operational_forecasts_to_frame(self) -> pd.DataFrame:
        """Return origin-safe operational point forecasts with unchanged raw diagnostics."""

        columns = [
            "requested_key",
            "Store",
            "Date",
            "forecast_origin",
            "horizon",
            "raw_forecast",
            "forecast_available",
            "unavailable_reason",
            "model_identity",
            "fit_identity",
            "recipe_identity",
            "feature_schema_identity",
            "requested_grid_identity",
            "training_input_identity",
            "recursive_history_identity",
            "future_covariate_identity",
            "planned_open",
            "planned_open_known",
            "planned_open_rule_id",
            "schedule_identity",
            "schedule_source_id",
            "schedule_version",
            "schedule_provenance",
            "schedule_availability_assumption",
            "operational_forecast",
            "operational_forecast_available",
            "operational_unavailable_reason",
            "closure_routing_applied",
        ]
        return self._records.loc[:, columns].copy(deep=True)

    def daily_intervals_to_frame(self) -> pd.DataFrame:
        """Return raw and separately routed operational interval diagnostics."""

        columns = [
            "requested_key",
            "Store",
            "Date",
            "forecast_origin",
            "horizon",
            "raw_forecast",
            "forecast_available",
            "unavailable_reason",
            "planned_open",
            "planned_open_known",
            "planned_open_rule_id",
            "schedule_identity",
            "schedule_source_id",
            "schedule_version",
            "schedule_provenance",
            "schedule_availability_assumption",
            "q_low_signed",
            "q_high_signed",
            "raw_interval_pre_lower",
            "raw_interval_pre_upper",
            "raw_interval_lower_clipped",
            "raw_interval_upper_clipped",
            "raw_interval_lower",
            "raw_interval_upper",
            "raw_interval_width",
            "raw_interval_available",
            "raw_interval_unavailable_reason",
            "operational_interval_lower",
            "operational_interval_upper",
            "operational_interval_width",
            "operational_interval_available",
            "operational_interval_unavailable_reason",
            "operational_interval_closure_routed",
            "daily_lower_n",
            "daily_lower_rank_1_indexed",
            "daily_lower_available",
            "daily_lower_unavailable_reason",
            "daily_upper_n",
            "daily_upper_rank_1_indexed",
            "daily_upper_available",
            "daily_upper_unavailable_reason",
            "calibration_fit_identity",
            "calibration_run_id",
            "manifest_sha256",
            "daily_table_sha256",
            "cumulative_table_sha256",
            "policy_config_sha256",
            "calibration_config_sha256",
            "daily_fixture_sha256",
            "fresh_model_fit_identity",
            "quantile_fixture_identity",
            "transport_status",
        ]
        return self._records.loc[:, columns].copy(deep=True)

    def prefixes_to_frame(self) -> pd.DataFrame:
        """Return exact origin-anchored operational prefixes for k=1..14 and each p."""

        return self._prefixes.copy(deep=True)

    def build_standing_targets(
        self, anchors: SyntheticHistoricalMeanAnchorCollection
    ) -> OriginFrozenStandingTargets:
        """Build both Phase 10 target policies from origin- and Store-bound anchors."""

        return build_origin_frozen_targets(self, anchors)


@dataclass(frozen=True, slots=True, init=False)
class OriginFrozenStandingTargets:
    """Defensive snapshot of paired origin-frozen synthetic inventory targets."""

    origin: date
    store_ids: tuple[int, ...]
    issuance_identity: str
    anchor_collection_identity: str
    _records: pd.DataFrame

    def __init__(
        self,
        *,
        origin: date,
        store_ids: tuple[int, ...],
        issuance_identity: str,
        anchor_collection_identity: str,
        records: pd.DataFrame,
    ) -> None:
        if not isinstance(records, pd.DataFrame):
            raise Phase13AdapterError("Standing targets require a table output.")
        try:
            grid = RequestedForecastGrid(origin, tuple(store_ids))
        except (TypeError, ValueError) as exc:
            raise Phase13AdapterError("Standing target origin/store universe is invalid.") from exc
        if not _is_sha256(issuance_identity):
            raise Phase13AdapterError("Standing target issuance identity must be SHA-256.")
        if not _is_sha256(anchor_collection_identity):
            raise Phase13AdapterError("Standing target anchor collection identity must be SHA-256.")
        _reject_forbidden_columns(records, "standing targets")
        snapshot = _validate_standing_target_snapshot(
            records,
            origin=grid.origin.value,
            store_ids=grid.store_ids,
            issuance_identity=issuance_identity,
            anchor_collection_identity=anchor_collection_identity,
        )
        object.__setattr__(self, "origin", grid.origin.value)
        object.__setattr__(self, "store_ids", grid.store_ids)
        object.__setattr__(self, "issuance_identity", issuance_identity)
        object.__setattr__(self, "anchor_collection_identity", anchor_collection_identity)
        object.__setattr__(self, "_records", snapshot)

    def to_frame(self) -> pd.DataFrame:
        """Return an independent copy of the frozen target rows."""

        return self._records.copy(deep=True)


class Phase13M3Adapter:
    """Apply synthetic planned-Open routing and synthetic Fit B table lookups."""

    def issue(
        self,
        raw_issuance: RawForecastIssuance,
        planned_open: SyntheticPlannedOpen,
        quantiles: SyntheticFitBQuantileFixture,
    ) -> Phase13M3Issuance:
        raw_frame, grid = _validate_raw_issuance(raw_issuance)
        schedule = _validate_schedule(planned_open, grid)
        _validate_transport(raw_issuance, planned_open, quantiles)
        daily_lookup = _daily_lookup(quantiles)
        cumulative_lookup = _cumulative_lookup(quantiles)

        records = raw_frame.copy(deep=True).merge(
            schedule.loc[:, ["Store", "Date", "planned_open"]],
            on=["Store", "Date"],
            how="left",
            validate="one_to_one",
            sort=False,
        )
        records["planned_open"] = pd.array(records["planned_open"], dtype="boolean")
        records["planned_open_known"] = records["planned_open"].notna()
        records["planned_open_rule_id"] = planned_open.rule_id
        records["schedule_identity"] = planned_open.identity
        records["schedule_source_id"] = planned_open.provenance.source_id
        records["schedule_version"] = planned_open.provenance.version
        records["schedule_provenance"] = planned_open.provenance.provenance
        records["schedule_availability_assumption"] = (
            planned_open.provenance.availability_assumption.value
        )

        operational_values: list[float | None] = []
        operational_available: list[bool] = []
        operational_reasons: list[str | None] = []
        closure_routed: list[bool] = []
        raw_lower: list[float | None] = []
        raw_upper: list[float | None] = []
        raw_pre_lower: list[float | None] = []
        raw_pre_upper: list[float | None] = []
        raw_lower_clipped: list[bool | None] = []
        raw_upper_clipped: list[bool | None] = []
        raw_width: list[float | None] = []
        raw_interval_available: list[bool] = []
        raw_interval_reasons: list[str | None] = []
        op_lower: list[float | None] = []
        op_upper: list[float | None] = []
        op_width: list[float | None] = []
        op_interval_available: list[bool] = []
        op_interval_reasons: list[str | None] = []
        op_interval_closure_routed: list[bool] = []
        q_low_values: list[float | None] = []
        q_high_values: list[float | None] = []
        daily_lower_n: list[int] = []
        daily_upper_n: list[int] = []
        daily_lower_rank: list[int] = []
        daily_upper_rank: list[int] = []
        daily_lower_available: list[bool] = []
        daily_upper_available: list[bool] = []
        daily_lower_reason: list[str | None] = []
        daily_upper_reason: list[str | None] = []

        for row in records.itertuples(index=False):
            horizon = int(row.horizon)
            opening = row.planned_open
            raw_ok = bool(row.forecast_available)
            if pd.isna(opening):
                operational_values.append(None)
                operational_available.append(False)
                operational_reasons.append("planned_open_unknown")
                closure_routed.append(False)
            elif not bool(opening):
                operational_values.append(0.0)
                operational_available.append(True)
                operational_reasons.append(None)
                closure_routed.append(True)
            elif raw_ok:
                operational_values.append(float(row.raw_forecast))
                operational_available.append(True)
                operational_reasons.append(None)
                closure_routed.append(False)
            else:
                operational_values.append(None)
                operational_available.append(False)
                operational_reasons.append(f"raw_forecast_unavailable:{row.unavailable_reason}")
                closure_routed.append(False)

            low = daily_lookup[(horizon, "lower")]
            high = daily_lookup[(horizon, "upper")]
            q_low_values.append(low["signed_quantile"])
            q_high_values.append(high["signed_quantile"])
            daily_lower_n.append(low["n"])
            daily_upper_n.append(high["n"])
            daily_lower_rank.append(low["rank_1_indexed"])
            daily_upper_rank.append(high["rank_1_indexed"])
            daily_lower_available.append(low["available"])
            daily_upper_available.append(high["available"])
            daily_lower_reason.append(low["unavailable_reason"])
            daily_upper_reason.append(high["unavailable_reason"])
            interval = _raw_interval(
                row.raw_forecast if raw_ok else None,
                raw_reason=row.unavailable_reason if not raw_ok else None,
                lower=low,
                upper=high,
            )
            raw_pre_lower.append(interval["pre_lower"])
            raw_pre_upper.append(interval["pre_upper"])
            raw_lower_clipped.append(interval["lower_clipped"])
            raw_upper_clipped.append(interval["upper_clipped"])
            raw_lower.append(interval["lower"])
            raw_upper.append(interval["upper"])
            raw_width.append(interval["width"])
            raw_interval_available.append(interval["available"])
            raw_interval_reasons.append(interval["reason"])

            if pd.isna(opening):
                op_lower.append(None)
                op_upper.append(None)
                op_width.append(None)
                op_interval_available.append(False)
                op_interval_reasons.append("planned_open_unknown")
                op_interval_closure_routed.append(False)
            elif not bool(opening):
                op_lower.append(0.0)
                op_upper.append(0.0)
                op_width.append(0.0)
                op_interval_available.append(True)
                op_interval_reasons.append(None)
                op_interval_closure_routed.append(True)
            elif interval["available"]:
                op_lower.append(interval["lower"])
                op_upper.append(interval["upper"])
                op_width.append(interval["width"])
                op_interval_available.append(True)
                op_interval_reasons.append(None)
                op_interval_closure_routed.append(False)
            else:
                op_lower.append(None)
                op_upper.append(None)
                op_width.append(None)
                op_interval_available.append(False)
                op_interval_reasons.append(f"raw_interval_unavailable:{interval['reason']}")
                op_interval_closure_routed.append(False)

        records["operational_forecast"] = operational_values
        records["operational_forecast_available"] = pd.array(operational_available, dtype="boolean")
        records["operational_unavailable_reason"] = operational_reasons
        records["closure_routing_applied"] = pd.array(closure_routed, dtype="boolean")
        records["q_low_signed"] = q_low_values
        records["q_high_signed"] = q_high_values
        records["raw_interval_pre_lower"] = raw_pre_lower
        records["raw_interval_pre_upper"] = raw_pre_upper
        records["raw_interval_lower_clipped"] = pd.array(raw_lower_clipped, dtype="boolean")
        records["raw_interval_upper_clipped"] = pd.array(raw_upper_clipped, dtype="boolean")
        records["raw_interval_lower"] = raw_lower
        records["raw_interval_upper"] = raw_upper
        records["raw_interval_width"] = raw_width
        records["raw_interval_available"] = pd.array(raw_interval_available, dtype="boolean")
        records["raw_interval_unavailable_reason"] = raw_interval_reasons
        records["operational_interval_lower"] = op_lower
        records["operational_interval_upper"] = op_upper
        records["operational_interval_width"] = op_width
        records["operational_interval_available"] = pd.array(op_interval_available, dtype="boolean")
        records["operational_interval_unavailable_reason"] = op_interval_reasons
        records["operational_interval_closure_routed"] = pd.array(
            op_interval_closure_routed, dtype="boolean"
        )
        records["daily_lower_n"] = daily_lower_n
        records["daily_lower_rank_1_indexed"] = daily_lower_rank
        records["daily_lower_available"] = pd.array(daily_lower_available, dtype="boolean")
        records["daily_lower_unavailable_reason"] = daily_lower_reason
        records["daily_upper_n"] = daily_upper_n
        records["daily_upper_rank_1_indexed"] = daily_upper_rank
        records["daily_upper_available"] = pd.array(daily_upper_available, dtype="boolean")
        records["daily_upper_unavailable_reason"] = daily_upper_reason
        _add_calibration_metadata(records, quantiles)
        prefixes = _build_prefixes(records, cumulative_lookup, quantiles)

        raw_identity = _raw_issuance_identity(raw_issuance, raw_frame)
        issuance_identity = _digest(
            {
                "raw_issuance_identity": raw_identity,
                "schedule_identity": planned_open.identity,
                "quantile_fixture_identity": quantiles.fixture_identity,
                "origin": raw_issuance.origin.isoformat(),
                "contract": "phase13-m3-synthetic-adapter-v1",
            }
        )
        records["raw_issuance_identity"] = raw_identity
        records["m3_issuance_identity"] = issuance_identity
        records["quantile_fixture_identity"] = quantiles.fixture_identity
        records["daily_fixture_sha256"] = quantiles.daily_fixture_sha256
        records["cumulative_fixture_sha256"] = quantiles.cumulative_fixture_sha256
        records["fresh_model_fit_identity"] = raw_issuance.fit_identity
        records["transport_status"] = quantiles.transport.transport_status
        return Phase13M3Issuance(
            origin=raw_issuance.origin,
            raw_issuance_identity=raw_identity,
            issuance_identity=issuance_identity,
            grid_identity=raw_issuance.grid_identity,
            model_identity=raw_issuance.model_identity,
            fresh_model_fit_identity=raw_issuance.fit_identity,
            recipe_identity=raw_issuance.recipe_identity,
            feature_schema_identity=raw_issuance.feature_schema_identity,
            input_identities=raw_issuance.input_identities,
            schedule_identity=planned_open.identity,
            schedule_rule_id=planned_open.rule_id,
            quantile_fixture_identity=quantiles.fixture_identity,
            daily_fixture_sha256=quantiles.daily_fixture_sha256,
            cumulative_fixture_sha256=quantiles.cumulative_fixture_sha256,
            calibration_metadata=quantiles.calibration_metadata,
            transport_status=quantiles.transport.transport_status,
            records=records,
            prefixes=prefixes,
        )


def load_canonical_fit_b_quantiles(*_args: object, **_kwargs: object) -> None:
    """Fail closed: canonical Phase 8 artifact loading is not authorized or implemented."""

    raise Phase13AdapterError(
        "Canonical Fit B artifact loading requires separate authorization and hash verification."
    )


def build_origin_frozen_targets(
    issuance: Phase13M3Issuance,
    anchors: SyntheticHistoricalMeanAnchorCollection,
) -> OriginFrozenStandingTargets:
    """Build the paired Phase 10 standing targets from origin-only synthetic inputs."""

    if not isinstance(issuance, Phase13M3Issuance):
        raise Phase13AdapterError("Standing targets require a validated M3 issuance.")
    if not isinstance(anchors, SyntheticHistoricalMeanAnchorCollection):
        raise Phase13AdapterError("Standing targets require a typed synthetic anchor collection.")
    if anchors.origin != issuance.origin:
        raise Phase13AdapterError("Target anchor collection origin differs from M3 issuance.")
    forecasts = issuance.to_frame()
    prefixes = issuance.prefixes_to_frame()
    requested_stores = tuple(sorted(int(store) for store in forecasts["Store"].unique()))
    if anchors.store_ids != requested_stores:
        raise Phase13AdapterError("Target anchor Store universe differs from M3 issuance.")
    rows: list[dict[str, Any]] = []
    for store, block in forecasts.groupby("Store", sort=True):
        anchor = anchors.for_store(int(store))
        anchor_available = anchor is not None and anchor.available
        block = block.sort_values("horizon", kind="mergesort")
        if tuple(block["horizon"].astype(int)) != tuple(range(1, HORIZON + 1)):
            raise Phase13AdapterError("Standing-target input is not one complete H14 grid.")
        prefix_rows = prefixes.loc[prefixes["Store"].eq(store)]
        for lead_time in LEAD_TIMES:
            protection = lead_time + REVIEW_PERIOD
            prefix = block.iloc[:protection]
            schedule_values = prefix["planned_open"].tolist()
            schedule_known = all(not pd.isna(value) for value in schedule_values)
            open_days = (
                sum(int(bool(value)) for value in schedule_values) if schedule_known else None
            )
            baseline_available = schedule_known and anchor_available
            baseline_value = (
                float(anchor.mean_open_sales_value) * int(open_days)
                if baseline_available and anchor is not None
                else None
            )
            if not schedule_known:
                baseline_reason = "unknown_schedule_in_protection_prefix"
            elif anchor is None:
                baseline_reason = "anchor_missing"
            elif not anchor.available:
                baseline_reason = anchor.unavailable_reason
            else:
                baseline_reason = None
            operational_available = (
                bool(prefix["operational_forecast_available"].astype(bool).all()) and schedule_known
            )
            demand = (
                float(sum(float(value) for value in prefix["operational_forecast"]))
                if operational_available
                else None
            )
            if not schedule_known:
                point_reason = "unknown_schedule_in_protection_prefix"
            elif operational_available:
                point_reason = None
            else:
                unavailable = prefix.loc[
                    ~prefix["operational_forecast_available"].astype(bool)
                ].iloc[0]
                point_reason = (
                    "operational_point_unavailable_at_h"
                    f"{int(unavailable['horizon'])}:"
                    f"{unavailable['operational_unavailable_reason']}"
                )
            for probability in CUMULATIVE_LEVELS:
                q_row = prefix_rows.loc[
                    prefix_rows["k"].eq(protection) & prefix_rows["p"].eq(probability)
                ]
                if len(q_row) != 1:
                    raise Phase13AdapterError(
                        "Standing target lacks its exact cumulative prefix/probability row."
                    )
                q_record = q_row.iloc[0]
                q = q_record["cumulative_signed_quantile"]
                q_available = bool(q_record["quantile_available"])
                forecast_available = operational_available and q_available
                forecast_reason = (
                    point_reason
                    if not operational_available
                    else q_record["quantile_unavailable_reason"]
                    if not q_available
                    else None
                )
                upper = max(0.0, float(demand) + float(q)) if forecast_available else None
                safety = max(0.0, float(upper) - float(demand)) if forecast_available else None
                forecast_target = max(float(demand), float(upper)) if forecast_available else None
                common = {
                    "Store": int(store),
                    "forecast_origin": issuance.origin,
                    "model_identity": issuance.model_identity,
                    "model_fit_identity": issuance.fresh_model_fit_identity,
                    "fresh_model_fit_identity": issuance.fresh_model_fit_identity,
                    "calibration_fit_identity": FIT_B_ID,
                    "calibration_run_id": FROZEN_FIT_B_METADATA.run_id,
                    "calibration_manifest_sha256": FROZEN_FIT_B_METADATA.manifest_sha256,
                    "calibration_daily_table_sha256": (FROZEN_FIT_B_METADATA.daily_table_sha256),
                    "calibration_cumulative_table_sha256": (
                        FROZEN_FIT_B_METADATA.cumulative_table_sha256
                    ),
                    "calibration_policy_config_sha256": (
                        FROZEN_FIT_B_METADATA.policy_config_sha256
                    ),
                    "calibration_config_sha256": (FROZEN_FIT_B_METADATA.calibration_config_sha256),
                    "daily_fixture_sha256": issuance.daily_fixture_sha256,
                    "cumulative_fixture_sha256": issuance.cumulative_fixture_sha256,
                    "quantile_fixture_identity": issuance.quantile_fixture_identity,
                    "transport_status": issuance.transport_status,
                    "calibration_transport_valid": False,
                    "schedule_identity": issuance.schedule_identity,
                    "schedule_rule_id": issuance.schedule_rule_id,
                    "schedule_source_id": prefix.iloc[0]["schedule_source_id"],
                    "schedule_version": prefix.iloc[0]["schedule_version"],
                    "schedule_provenance": prefix.iloc[0]["schedule_provenance"],
                    "schedule_availability_assumption": (
                        prefix.iloc[0]["schedule_availability_assumption"]
                    ),
                    "anchor_collection_identity": anchors.identity,
                    "anchor_identity": anchor.identity if anchor is not None else None,
                    "anchor_store_id": int(store),
                    "anchor_origin": issuance.origin,
                    "anchor_source_id": anchor.provenance.source_id if anchor else None,
                    "anchor_version": anchor.provenance.version if anchor else None,
                    "anchor_provenance": anchor.provenance.provenance if anchor else None,
                    "anchor_availability_assumption": (
                        anchor.provenance.availability_assumption.value if anchor else None
                    ),
                    "anchor_parent_identities": (
                        anchor.provenance.parent_identities if anchor else None
                    ),
                    "anchor_available": bool(anchor_available),
                    "anchor_unavailable_reason": (
                        anchor.unavailable_reason if anchor is not None else "anchor_missing"
                    ),
                    "mean_open_sales_value": (
                        anchor.mean_open_sales_value if anchor is not None else None
                    ),
                    "anchor_semantics": (
                        anchor.semantics if anchor is not None else SYNTHETIC_TARGET_SEMANTICS
                    ),
                    "open_days_in_protection_period": open_days,
                    "lead_time": lead_time,
                    "review_period": REVIEW_PERIOD,
                    "protection_period": protection,
                    "buffer_probability": probability,
                    "cumulative_signed_quantile": q,
                    "quantile_available": q_available,
                    "quantile_unavailable_reason": q_record["quantile_unavailable_reason"],
                    "forecast_protection_demand_value": demand,
                    "upper_turnover_value": upper,
                    "safety_stock_value": safety,
                    "input_semantics": SYNTHETIC_TARGET_SEMANTICS,
                    "issuance_identity": issuance.issuance_identity,
                }
                rows.append(
                    {
                        **common,
                        "policy_id": POLICY_IDS[0],
                        "target_value": baseline_value,
                        "target_available": bool(baseline_available),
                        "availability_reason": baseline_reason,
                        "buffer_interpretation": "synthetic_open_day_historical_mean_anchor",
                    }
                )
                rows.append(
                    {
                        **common,
                        "policy_id": POLICY_IDS[1],
                        "target_value": forecast_target,
                        "target_available": bool(forecast_available),
                        "availability_reason": forecast_reason,
                        "buffer_interpretation": "uncalibrated_synthetic_fit_b_transport",
                    }
                )
    records = pd.DataFrame.from_records(rows, columns=TARGET_COLUMNS)
    return OriginFrozenStandingTargets(
        origin=issuance.origin,
        store_ids=anchors.store_ids,
        issuance_identity=issuance.issuance_identity,
        anchor_collection_identity=anchors.identity,
        records=records,
    )


def _validate_standing_target_snapshot(
    records: pd.DataFrame,
    *,
    origin: date,
    store_ids: tuple[int, ...],
    issuance_identity: str,
    anchor_collection_identity: str,
) -> pd.DataFrame:
    data = _exact_table(records, TARGET_COLUMNS, "origin-frozen standing targets")
    _reject_forbidden_columns(data, "standing targets")
    if data.empty:
        raise Phase13AdapterError("Standing target snapshot must not be empty.")
    try:
        stores = pd.to_numeric(data["Store"], errors="raise").to_numpy(dtype=np.float64)
        anchor_stores = pd.to_numeric(data["anchor_store_id"], errors="raise").to_numpy(
            dtype=np.float64
        )
        origins = pd.to_datetime(data["forecast_origin"], errors="raise")
        anchor_origins = pd.to_datetime(data["anchor_origin"], errors="raise")
    except (TypeError, ValueError, OverflowError) as exc:
        raise Phase13AdapterError("Standing target keys or origins are malformed.") from exc
    if (
        not np.isfinite(stores).all()
        or not np.equal(stores, np.floor(stores)).all()
        or not np.isfinite(anchor_stores).all()
        or not np.equal(anchor_stores, np.floor(anchor_stores)).all()
        or (stores <= 0).any()
        or (anchor_stores <= 0).any()
    ):
        raise Phase13AdapterError("Standing target Store keys must be positive integers.")
    if origins.dt.tz is not None or anchor_origins.dt.tz is not None:
        raise Phase13AdapterError("Standing target origins must be timezone-naive dates.")
    if (
        not origins.eq(origins.dt.normalize()).all()
        or not anchor_origins.eq(anchor_origins.dt.normalize()).all()
    ):
        raise Phase13AdapterError("Standing target origins must be normalized calendar dates.")
    expected_stores = np.asarray(store_ids, dtype=np.int64)
    if not np.isin(stores.astype(np.int64), expected_stores).all():
        raise Phase13AdapterError("Standing target rows contain a Store outside the requested set.")

    key_values: list[tuple[int, date, int, int, int, float, str]] = []
    for row in data.itertuples(index=False):
        store = _integer(row.Store, "target Store", minimum=1)
        lead_time = _integer(row.lead_time, "target lead time", minimum=2)
        review_period = _integer(row.review_period, "target review period", minimum=0)
        protection = _integer(row.protection_period, "target protection period", minimum=1)
        probability = _finite_number(row.buffer_probability, "target buffer probability")
        if lead_time not in LEAD_TIMES or review_period != REVIEW_PERIOD:
            raise Phase13AdapterError("Standing target lead/review contract is incompatible.")
        if protection != lead_time + REVIEW_PERIOD:
            raise Phase13AdapterError("Standing target protection period is incompatible.")
        if probability not in CUMULATIVE_LEVELS or row.policy_id not in POLICY_IDS:
            raise Phase13AdapterError("Standing target probability or policy is unsupported.")
        key_values.append(
            (
                store,
                pd.Timestamp(row.forecast_origin).date(),
                lead_time,
                review_period,
                protection,
                probability,
                str(row.policy_id),
            )
        )
    if len(key_values) != len(set(key_values)):
        raise Phase13AdapterError("Standing target snapshot contains duplicate exact keys.")
    expected_keys = {
        (store, origin, lead, REVIEW_PERIOD, lead + REVIEW_PERIOD, probability, policy)
        for store in store_ids
        for lead in LEAD_TIMES
        for probability in CUMULATIVE_LEVELS
        for policy in POLICY_IDS
    }
    if set(key_values) != expected_keys:
        raise Phase13AdapterError("Standing target snapshot is partial or has unexpected keys.")

    if (
        not origins.eq(pd.Timestamp(origin)).all()
        or not anchor_origins.eq(pd.Timestamp(origin)).all()
    ):
        raise Phase13AdapterError("Standing target row origins disagree with snapshot origin.")
    if (
        not data["issuance_identity"].eq(issuance_identity).all()
        or not data["anchor_collection_identity"].eq(anchor_collection_identity).all()
    ):
        raise Phase13AdapterError("Standing target row identity disagrees with snapshot identity.")
    if not np.array_equal(stores.astype(np.int64), anchor_stores.astype(np.int64)):
        raise Phase13AdapterError("Standing target anchor Store binding is inconsistent.")
    for column in (
        "model_identity",
        "fresh_model_fit_identity",
        "schedule_identity",
        "quantile_fixture_identity",
        "daily_fixture_sha256",
        "cumulative_fixture_sha256",
    ):
        if data[column].isna().any() or data[column].nunique(dropna=False) != 1:
            raise Phase13AdapterError(f"Standing target {column} is missing or inconsistent.")
    for column in (
        "model_identity",
        "fresh_model_fit_identity",
        "schedule_identity",
        "quantile_fixture_identity",
        "daily_fixture_sha256",
        "cumulative_fixture_sha256",
    ):
        if not _is_sha256(data[column].iloc[0]):
            raise Phase13AdapterError(f"Standing target {column} must be SHA-256.")
    if not data["model_fit_identity"].eq(data["fresh_model_fit_identity"]).all():
        raise Phase13AdapterError("Standing target model-fit identities disagree.")
    if (
        not data["calibration_transport_valid"]
        .map(lambda value: isinstance(value, (bool, np.bool_)) and not bool(value))
        .all()
    ):
        raise Phase13AdapterError("Standing targets must retain unvalidated Fit B transport.")
    if (
        not data["anchor_semantics"].eq(SYNTHETIC_TARGET_SEMANTICS).all()
        or not data["input_semantics"].eq(SYNTHETIC_TARGET_SEMANTICS).all()
    ):
        raise Phase13AdapterError("Standing target synthetic turnover semantics changed.")

    for column in ("target_available", "anchor_available", "quantile_available"):
        if (
            data[column].isna().any()
            or not data[column].map(lambda value: isinstance(value, (bool, np.bool_))).all()
        ):
            raise Phase13AdapterError(f"Standing target {column} must be explicit Boolean.")
    for row in data.itertuples(index=False):
        available = bool(row.target_available)
        reason = None if _is_missing_scalar(row.availability_reason) else row.availability_reason
        if available:
            if reason is not None:
                raise Phase13AdapterError("Available standing targets cannot carry a reason.")
            if _finite_number(row.target_value, "available target value") < 0:
                raise Phase13AdapterError("Available target value cannot be negative.")
        elif not _is_missing_scalar(row.target_value) or not _nonempty_reason(reason):
            raise Phase13AdapterError(
                "Unavailable standing targets require null value and a nonempty reason."
            )

    anchor_group_columns = (
        "anchor_identity",
        "anchor_available",
        "anchor_unavailable_reason",
        "mean_open_sales_value",
        "anchor_source_id",
        "anchor_version",
        "anchor_provenance",
        "anchor_availability_assumption",
        "anchor_parent_identities",
    )
    anchor_identities_by_store: dict[int, str] = {}
    for store, group in data.groupby("Store", sort=True):
        for column in anchor_group_columns:
            if group[column].nunique(dropna=False) != 1:
                raise Phase13AdapterError(
                    f"Standing target Store {int(store)} has inconsistent anchor {column}."
                )
        anchor_available = bool(group["anchor_available"].iloc[0])
        anchor_identity = group["anchor_identity"].iloc[0]
        anchor_reason = group["anchor_unavailable_reason"].iloc[0]
        mean_value = group["mean_open_sales_value"].iloc[0]
        provenance_values = [group[column].iloc[0] for column in anchor_group_columns[4:]]
        identity_missing = _is_missing_scalar(anchor_identity)
        if anchor_available:
            if (
                not isinstance(anchor_identity, str)
                or not anchor_identity.startswith("synthetic://phase13/")
                or _finite_number(mean_value, "Store mean anchor") < 0
                or not _is_missing_scalar(anchor_reason)
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in provenance_values[:3]
                )
                or provenance_values[3] != AvailabilityAssumption.SYNTHETIC_RULE.value
            ):
                raise Phase13AdapterError("Available Store mean anchor snapshot is invalid.")
        else:
            if not _is_missing_scalar(mean_value) or not _nonempty_reason(anchor_reason):
                raise Phase13AdapterError("Unavailable Store mean anchor snapshot is invalid.")
            if identity_missing:
                if anchor_reason != "anchor_missing" or any(
                    not _is_missing_scalar(value) for value in provenance_values
                ):
                    raise Phase13AdapterError(
                        "Missing Store anchor must remain explicitly missing."
                    )
            elif (
                not isinstance(anchor_identity, str)
                or not anchor_identity.startswith("synthetic://phase13/")
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in provenance_values[:3]
                )
                or provenance_values[3] != AvailabilityAssumption.SYNTHETIC_RULE.value
            ):
                raise Phase13AdapterError("Unavailable Store anchor provenance is invalid.")
        if not identity_missing:
            anchor_identities_by_store[int(store)] = anchor_identity
    if len(set(anchor_identities_by_store.values())) != len(anchor_identities_by_store):
        raise Phase13AdapterError("Standing target anchor identity is reused across Stores.")

    data["Store"] = stores.astype("int64")
    data["anchor_store_id"] = anchor_stores.astype("int64")
    data["forecast_origin"] = origins.dt.date
    data["anchor_origin"] = anchor_origins.dt.date
    data["lead_time"] = pd.to_numeric(data["lead_time"]).astype("int64")
    data["review_period"] = pd.to_numeric(data["review_period"]).astype("int64")
    data["protection_period"] = pd.to_numeric(data["protection_period"]).astype("int64")
    data["buffer_probability"] = pd.to_numeric(data["buffer_probability"]).astype("float64")
    return data.reset_index(drop=True).copy(deep=True)


def _validate_m3_result_snapshot(
    *,
    origin: date,
    raw_issuance_identity: str,
    issuance_identity: str,
    grid_identity: str,
    model_identity: str,
    fresh_model_fit_identity: str,
    recipe_identity: str,
    feature_schema_identity: str,
    input_identities: tuple[tuple[str, str], ...],
    schedule_identity: str,
    schedule_rule_id: str,
    quantile_fixture_identity: str,
    daily_fixture_sha256: str,
    cumulative_fixture_sha256: str,
    calibration_metadata: FitBCanonicalMetadata,
    transport_status: str,
    records: pd.DataFrame,
    prefixes: pd.DataFrame,
) -> None:
    if origin not in SUPPORTED_ORIGINS:
        raise Phase13AdapterError("M3 result has an unsupported July origin.")
    if calibration_metadata != FROZEN_FIT_B_METADATA:
        raise Phase13AdapterError("M3 result lost the pinned Fit B metadata identity.")
    if schedule_rule_id != SYNTHETIC_OPEN_RULE_ID:
        raise Phase13AdapterError("M3 result has an incompatible planned-Open rule.")
    if transport_status != "unvalidated_june_fit_b_to_july_assumption":
        raise Phase13AdapterError("M3 result cannot claim validated Fit B transport.")
    if any(
        not _is_sha256(value)
        for value in (
            raw_issuance_identity,
            issuance_identity,
            grid_identity,
            model_identity,
            fresh_model_fit_identity,
            recipe_identity,
            feature_schema_identity,
            schedule_identity,
            quantile_fixture_identity,
            daily_fixture_sha256,
            cumulative_fixture_sha256,
            *[value for _, value in input_identities],
        )
    ):
        raise Phase13AdapterError("M3 result contains a malformed provenance identity.")
    if model_identity == fresh_model_fit_identity:
        raise Phase13AdapterError("M3 model and fresh-fit identities must remain distinct.")
    identity_map = dict(input_identities)
    if (
        len(identity_map) != len(input_identities)
        or set(identity_map)
        != {"requested_grid", "training", "recursive_history", "future_covariates"}
        or identity_map["requested_grid"] != grid_identity
    ):
        raise Phase13AdapterError("M3 result input provenance identities are incompatible.")
    required_records = _RAW_REQUIRED_COLUMNS | {
        "planned_open",
        "planned_open_known",
        "planned_open_rule_id",
        "schedule_identity",
        "schedule_source_id",
        "schedule_version",
        "schedule_provenance",
        "schedule_availability_assumption",
        "operational_forecast",
        "operational_forecast_available",
        "operational_unavailable_reason",
        "closure_routing_applied",
        "raw_interval_available",
        "operational_interval_available",
        "calibration_fit_identity",
        "calibration_run_id",
        "daily_fixture_sha256",
        "cumulative_fixture_sha256",
        "quantile_fixture_identity",
        "fresh_model_fit_identity",
        "transport_status",
        "raw_issuance_identity",
        "m3_issuance_identity",
    }
    if required_records - set(records.columns):
        raise Phase13AdapterError("M3 result records omit required routed/provenance fields.")
    if records.empty or records.duplicated(["Store", "Date"]).any():
        raise Phase13AdapterError("M3 result records are empty or have duplicate keys.")
    stores = tuple(sorted(pd.to_numeric(records["Store"], errors="raise").astype(int).unique()))
    grid = RequestedForecastGrid(ForecastOrigin(origin), stores)
    if grid.identity != grid_identity or len(records) != grid.requested_key_count:
        raise Phase13AdapterError("M3 result grid identity or row count is incompatible.")
    actual_keys = tuple(
        (int(store), pd.Timestamp(day).normalize())
        for store, day in records[["Store", "Date"]].itertuples(index=False, name=None)
    )
    expected_keys = tuple(
        (int(store), pd.Timestamp(day).normalize())
        for store, day in grid.to_frame()[["Store", "Date"]].itertuples(index=False, name=None)
    )
    if actual_keys != expected_keys:
        raise Phase13AdapterError("M3 result changed the exact Store/Date ordering.")
    identity_columns = {
        "model": MODEL_NAME,
        "model_identity": model_identity,
        "fit_identity": fresh_model_fit_identity,
        "fresh_model_fit_identity": fresh_model_fit_identity,
        "recipe_identity": recipe_identity,
        "feature_schema_identity": feature_schema_identity,
        "requested_grid_identity": grid_identity,
        "training_input_identity": identity_map["training"],
        "recursive_history_identity": identity_map["recursive_history"],
        "future_covariate_identity": identity_map["future_covariates"],
        "planned_open_rule_id": schedule_rule_id,
        "schedule_identity": schedule_identity,
        "calibration_fit_identity": FIT_B_ID,
        "calibration_run_id": calibration_metadata.run_id,
        "daily_fixture_sha256": daily_fixture_sha256,
        "cumulative_fixture_sha256": cumulative_fixture_sha256,
        "quantile_fixture_identity": quantile_fixture_identity,
        "transport_status": transport_status,
        "raw_issuance_identity": raw_issuance_identity,
        "m3_issuance_identity": issuance_identity,
    }
    for column, expected in identity_columns.items():
        if not records[column].eq(expected).all():
            raise Phase13AdapterError(f"M3 result row identity mismatch: {column}.")

    required_prefixes = {
        "Store",
        "forecast_origin",
        "model_identity",
        "model_fit_identity",
        "calibration_fit_identity",
        "schedule_identity",
        "schedule_rule_id",
        "k",
        "p",
        "complete_operational_prefix",
        "operational_cumulative_forecast",
        "cumulative_signed_quantile",
        "quantile_available",
        "available",
        "unavailable_reason",
    }
    if required_prefixes - set(prefixes.columns):
        raise Phase13AdapterError("M3 prefix table omits required uncertainty fields.")
    if prefixes.duplicated(["Store", "forecast_origin", "k", "p"]).any():
        raise Phase13AdapterError("M3 prefix table contains duplicate exact keys.")
    expected_prefix_keys = {
        (store, origin, k, p)
        for store in stores
        for k in range(1, HORIZON + 1)
        for p in CUMULATIVE_LEVELS
    }
    actual_prefix_keys = {
        (
            int(row.Store),
            pd.Timestamp(row.forecast_origin).date(),
            int(row.k),
            float(row.p),
        )
        for row in prefixes.itertuples(index=False)
    }
    if actual_prefix_keys != expected_prefix_keys:
        raise Phase13AdapterError("M3 prefix table omitted or added a frozen k/p stratum.")


def _validate_raw_issuance(
    issuance: RawForecastIssuance,
) -> tuple[pd.DataFrame, RequestedForecastGrid]:
    if not isinstance(issuance, RawForecastIssuance):
        raise Phase13AdapterError("M3 requires the typed M2 RawForecastIssuance contract.")
    if issuance.origin not in SUPPORTED_ORIGINS:
        raise Phase13AdapterError("M2 issuance origin is not one of the two July blocks.")
    if issuance.model_name != CANDIDATE_IDS[2] or issuance.model_name != MODEL_NAME:
        raise Phase13AdapterError("M2 model identity is incompatible with the selected model.")
    if issuance.requested_boost_rounds != NUM_BOOST_ROUND or issuance.actual_tree_count not in (
        None,
        NUM_BOOST_ROUND,
    ):
        raise Phase13AdapterError("M2 model recipe round count is incompatible.")
    if issuance.recipe_identity != _identity(_frozen_recipe()):
        raise Phase13AdapterError("M2 frozen recipe identity is incompatible.")
    if issuance.feature_schema_identity != _schema_identity():
        raise Phase13AdapterError("M2 ordered feature schema identity is incompatible.")
    if (
        not _is_sha256(issuance.model_identity)
        or not _is_sha256(issuance.fit_identity)
        or issuance.model_identity == issuance.fit_identity
    ):
        raise Phase13AdapterError("M2 model and fresh fit identities are invalid.")
    try:
        identity_pairs = tuple(issuance.input_identities)
        identity_map = dict(identity_pairs)
    except (TypeError, ValueError) as exc:
        raise Phase13AdapterError("M2 input provenance identities are malformed.") from exc
    expected_roles = {
        "requested_grid",
        "training",
        "recursive_history",
        "future_covariates",
    }
    if len(identity_map) != len(identity_pairs) or set(identity_map) != expected_roles:
        raise Phase13AdapterError("M2 input provenance identities are incomplete or duplicated.")
    if any(not _is_sha256(value) for value in identity_map.values()):
        raise Phase13AdapterError("M2 input provenance identity is malformed.")
    if identity_map["requested_grid"] != issuance.grid_identity:
        raise Phase13AdapterError("M2 requested-grid provenance does not match its identity.")

    records = issuance.to_frame()
    if not isinstance(records, pd.DataFrame):
        raise Phase13AdapterError("M2 raw issuance did not return a defensive table.")
    _reject_forbidden_columns(records, "raw issuance")
    missing = _RAW_REQUIRED_COLUMNS - set(records.columns)
    if missing:
        raise Phase13AdapterError(f"M2 raw records are missing required fields: {sorted(missing)}.")
    if records.empty or records[["Store", "Date"]].isna().any().any():
        raise Phase13AdapterError("M2 raw issuance has an empty or incomplete requested grid.")
    if records.duplicated(["Store", "Date"]).any():
        raise Phase13AdapterError("M2 raw issuance contains duplicate Store/Date keys.")
    try:
        store_values = pd.to_numeric(records["Store"], errors="raise").to_numpy(dtype=np.float64)
        dates = pd.to_datetime(records["Date"], errors="raise")
        origins = pd.to_datetime(records["forecast_origin"], errors="raise")
        horizon_values = pd.to_numeric(records["horizon"], errors="raise").to_numpy(
            dtype=np.float64
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise Phase13AdapterError("M2 raw issuance keys or horizons are malformed.") from exc
    if (
        not np.isfinite(store_values).all()
        or not np.equal(store_values, np.floor(store_values)).all()
        or np.any(store_values <= 0)
        or not np.isfinite(horizon_values).all()
        or not np.equal(horizon_values, np.floor(horizon_values)).all()
    ):
        raise Phase13AdapterError("M2 Store and horizon keys must be finite integers.")
    stores = tuple(sorted(set(int(value) for value in store_values)))
    horizons = pd.Series(horizon_values.astype("int64"), index=records.index)
    if dates.dt.tz is not None or origins.dt.tz is not None:
        raise Phase13AdapterError("M2 raw issuance dates must be timezone-naive calendar dates.")
    if not dates.eq(dates.dt.normalize()).all() or not origins.eq(origins.dt.normalize()).all():
        raise Phase13AdapterError("M2 raw issuance dates must be normalized calendar dates.")
    grid = RequestedForecastGrid(ForecastOrigin(issuance.origin), stores)
    if (
        grid.identity != issuance.grid_identity
        or issuance.requested_key_count != grid.requested_key_count
    ):
        raise Phase13AdapterError(
            "M2 issuance grid identity or requested-key count is incompatible."
        )
    expected_keys = grid.to_frame()
    actual_keys = tuple(
        (int(store), pd.Timestamp(day))
        for store, day in records[["Store", "Date"]].itertuples(index=False, name=None)
    )
    expected_tuple = tuple(
        (int(store), pd.Timestamp(day))
        for store, day in expected_keys[["Store", "Date"]].itertuples(index=False, name=None)
    )
    if actual_keys != expected_tuple:
        raise Phase13AdapterError(
            "M2 raw issuance does not preserve the complete ordered H14 grid."
        )
    if not dates.eq(pd.to_datetime(expected_keys["Date"])).all():
        raise Phase13AdapterError("M2 raw issuance dates differ from the exact origin H14 block.")
    expected_horizons = pd.Series(
        [lead for _store in stores for lead in range(1, HORIZON + 1)],
        index=records.index,
    )
    if (
        not horizons.eq(expected_horizons).all()
        or not origins.eq(pd.Timestamp(issuance.origin)).all()
    ):
        raise Phase13AdapterError("M2 origin and horizon fields do not match the requested block.")
    expected_requested_keys = [
        f"{int(store)}:{pd.Timestamp(day).date().isoformat()}" for store, day in actual_keys
    ]
    if records["requested_key"].tolist() != expected_requested_keys:
        raise Phase13AdapterError("M2 requested-key identities do not match the exact grid.")
    if (
        bool(records["forecast_available"].isna().any())
        or not records["forecast_available"]
        .map(lambda value: isinstance(value, (bool, np.bool_)))
        .all()
    ):
        raise Phase13AdapterError("M2 raw forecast availability must be explicit Boolean.")
    available = records["forecast_available"].astype(bool)
    numeric = ("raw_forecast", "unclipped_forecast", "recursive_state_value")
    for column in numeric:
        values = pd.to_numeric(records[column], errors="coerce")
        if (
            values.loc[available].isna().any()
            or not np.isfinite(values.loc[available].to_numpy(dtype=np.float64)).all()
        ):
            raise Phase13AdapterError("Available M2 raw forecasts must have finite diagnostics.")
        if values.loc[~available].notna().any():
            raise Phase13AdapterError("Unavailable M2 raw forecasts cannot carry numeric values.")
    raw_values = pd.to_numeric(records.loc[available, "raw_forecast"], errors="raise")
    if raw_values.lt(0).any():
        raise Phase13AdapterError("M2 raw point forecasts cannot be negative.")
    reasons = records["unavailable_reason"]
    if (
        reasons.loc[available].notna().any()
        or reasons.loc[~available].map(lambda value: not _nonempty_reason(value)).any()
    ):
        raise Phase13AdapterError("M2 availability and unavailable reasons are inconsistent.")
    clipped = records["forecast_was_clipped"]
    if (
        clipped.loc[available].isna().any()
        or clipped.loc[~available].notna().any()
        or not clipped.loc[available].map(lambda value: isinstance(value, (bool, np.bool_))).all()
    ):
        raise Phase13AdapterError("M2 clipping diagnostics are inconsistent with availability.")
    expected_row_identities = {
        "model": issuance.model_name,
        "model_identity": issuance.model_identity,
        "fit_identity": issuance.fit_identity,
        "recipe_identity": issuance.recipe_identity,
        "feature_schema_identity": issuance.feature_schema_identity,
        "requested_grid_identity": issuance.grid_identity,
        "training_input_identity": identity_map["training"],
        "recursive_history_identity": identity_map["recursive_history"],
        "future_covariate_identity": identity_map["future_covariates"],
    }
    for column, expected in expected_row_identities.items():
        if not records[column].eq(expected).all():
            raise Phase13AdapterError(
                f"M2 row {column} provenance does not match issuance metadata."
            )
    available_count = int(available.sum())
    if (
        issuance.available_row_count != available_count
        or issuance.unavailable_row_count != len(records) - available_count
        or not issuance.all_requested_keys_accounted
        or issuance.complete_path_available != bool(available.all())
    ):
        raise Phase13AdapterError("M2 issuance availability counts do not reconcile.")
    if available_count and issuance.actual_tree_count != NUM_BOOST_ROUND:
        raise Phase13AdapterError("Available M2 points require the exact fitted tree count.")
    records["Store"] = store_values.astype("int64")
    records["Date"] = dates.dt.normalize()
    records["forecast_origin"] = origins.dt.normalize()
    records["horizon"] = horizons.astype("int64")
    return records.reset_index(drop=True), grid


def _validate_schedule(
    planned_open: SyntheticPlannedOpen, grid: RequestedForecastGrid
) -> pd.DataFrame:
    if not isinstance(planned_open, SyntheticPlannedOpen):
        raise Phase13AdapterError("M3 requires M1's typed synthetic planned-Open contract.")
    if (
        planned_open.origin != grid.origin
        or planned_open.grid_identity != grid.identity
        or planned_open.store_ids != grid.store_ids
        or planned_open.rule_id != SYNTHETIC_OPEN_RULE_ID
        or planned_open.provenance.availability_assumption.value != "synthetic_deterministic_rule"
        or not _is_sha256(planned_open.identity)
    ):
        raise Phase13AdapterError("Planned-Open grid, rule, or provenance is incompatible.")
    frame = planned_open.to_frame()
    _reject_forbidden_columns(frame, "planned-Open schedule")
    if tuple(frame.columns) != ("Store", "Date", "planned_open"):
        raise Phase13AdapterError("Planned-Open schedule schema changed.")
    if frame.duplicated(["Store", "Date"]).any():
        raise Phase13AdapterError("Planned-Open schedule has duplicate keys.")
    return frame


def _validate_transport(
    raw: RawForecastIssuance,
    schedule: SyntheticPlannedOpen,
    fixture: SyntheticFitBQuantileFixture,
) -> None:
    if not isinstance(fixture, SyntheticFitBQuantileFixture):
        raise Phase13AdapterError("M3 accepts synthetic Fit B quantile fixtures only.")
    if fixture.content_classification != "synthetic_fixture_content_only":
        raise Phase13AdapterError("Quantile fixture content cannot claim canonical authenticity.")
    if fixture.calibration_metadata != FROZEN_FIT_B_METADATA:
        raise Phase13AdapterError("Historical Fit B metadata identity mismatch.")
    if raw.fit_identity == fixture.calibration_metadata.calibration_fit_id:
        raise Phase13AdapterError("Fresh July fit identity must remain distinct from Fit B.")
    transport = fixture.transport
    expected = {
        "selected_model_id": raw.model_name,
        "recipe_identity": raw.recipe_identity,
        "feature_schema_identity": raw.feature_schema_identity,
        "daily_error_population": DAILY_ERROR_POPULATION,
        "cumulative_error_population": CUMULATIVE_ERROR_POPULATION,
        "prefix_definition": PREFIX_DEFINITION,
        "historical_schedule_assumption": HISTORICAL_SCHEDULE_ASSUMPTION,
        "application_schedule_rule_id": schedule.rule_id,
        "transport_status": "unvalidated_june_fit_b_to_july_assumption",
    }
    for field, value in expected.items():
        if getattr(transport, field) != value:
            raise Phase13AdapterError(f"Fit B transport compatibility mismatch: {field}.")


def _validated_daily_table(frame: pd.DataFrame) -> pd.DataFrame:
    data = _exact_table(frame, _DAILY_COLUMNS, "daily Fit B fixture")
    _require_unique(data, ("fit_id", "horizon", "tail"), "daily Fit B fixture")
    expected_keys = {(horizon, tail) for horizon in range(1, HORIZON + 1) for tail in DAILY_TAILS}
    actual_keys: set[tuple[int, str]] = set()
    for index, row in data.iterrows():
        if row["fit_id"] != FIT_B_ID:
            raise Phase13AdapterError("Daily fixture contains a non-Fit-B identity.")
        horizon = _integer(row["horizon"], "daily horizon", minimum=1)
        tail = row["tail"]
        if horizon > HORIZON or tail not in DAILY_TAILS:
            raise Phase13AdapterError("Daily fixture has an unsupported exact key.")
        actual_keys.add((horizon, tail))
        if _finite_number(row["tail_level"], "daily tail level") != DAILY_TAILS[tail]:
            raise Phase13AdapterError("Daily fixture tail probability is incompatible.")
        if row["error_population"] != DAILY_ERROR_POPULATION:
            raise Phase13AdapterError("Daily fixture error population is incompatible.")
        if (
            row["policy_version"] != UNCERTAINTY_POLICY_VERSION
            or row["selected_candidate_id"] != CANDIDATE_IDS[2]
            or row["calibration_windows"] != CALIBRATION_WINDOWS
        ):
            raise Phase13AdapterError("Daily fixture compatibility metadata is incompatible.")
        n = _integer(row["n"], "daily calibration count", minimum=0)
        rank = _integer(row["rank_1_indexed"], "daily quantile rank", minimum=0)
        expected_rank = (n + 1) // 40 if tail == "lower" else (39 * (n + 1) + 39) // 40
        if rank != expected_rank:
            raise Phase13AdapterError("Daily fixture saved rank differs from the frozen rank.")
        _validate_quantile_row(row, n=n, rank=rank, minimum=40)
        data.at[index, "horizon"] = horizon
        data.at[index, "tail_level"] = DAILY_TAILS[tail]
        data.at[index, "n"] = n
        data.at[index, "rank_1_indexed"] = rank
    if actual_keys != expected_keys:
        raise Phase13AdapterError("Daily fixture must contain exact horizons 1..14 and two tails.")
    by_horizon = data.set_index(["horizon", "tail"])
    for horizon in range(1, HORIZON + 1):
        lower = by_horizon.loc[(horizon, "lower")]
        upper = by_horizon.loc[(horizon, "upper")]
        if int(lower["n"]) != int(upper["n"]):
            raise Phase13AdapterError(
                "Daily lower and upper tails must share the same calibration sample count."
            )
        if (
            bool(lower["available"])
            and bool(upper["available"])
            and float(lower["signed_quantile"]) > float(upper["signed_quantile"])
        ):
            raise Phase13AdapterError("Daily signed quantile tails are inverted.")
    data["horizon"] = data["horizon"].astype("int64")
    data["n"] = data["n"].astype("int64")
    data["rank_1_indexed"] = data["rank_1_indexed"].astype("int64")
    return data.reset_index(drop=True)


def _validated_cumulative_table(frame: pd.DataFrame) -> pd.DataFrame:
    data = _exact_table(frame, _CUMULATIVE_COLUMNS, "cumulative Fit B fixture")
    _require_unique(data, ("fit_id", "k", "p"), "cumulative Fit B fixture")
    expected_keys = {(k, p) for k in range(1, HORIZON + 1) for p in CUMULATIVE_LEVELS}
    actual_keys: set[tuple[int, float]] = set()
    for index, row in data.iterrows():
        if row["fit_id"] != FIT_B_ID:
            raise Phase13AdapterError("Cumulative fixture contains a non-Fit-B identity.")
        k = _integer(row["k"], "cumulative prefix", minimum=1)
        p = _finite_number(row["p"], "cumulative probability")
        if k > HORIZON or p not in CUMULATIVE_LEVELS:
            raise Phase13AdapterError("Cumulative fixture has an unsupported exact key.")
        actual_keys.add((k, p))
        if (
            row["error_population"] != CUMULATIVE_ERROR_POPULATION
            or row["prefix_definition"] != PREFIX_DEFINITION
            or row["schedule_assumption"] != HISTORICAL_SCHEDULE_ASSUMPTION
        ):
            raise Phase13AdapterError(
                "Cumulative fixture population or prefix metadata is incompatible."
            )
        if (
            row["policy_version"] != UNCERTAINTY_POLICY_VERSION
            or row["selected_candidate_id"] != CANDIDATE_IDS[2]
            or row["calibration_windows"] != CALIBRATION_WINDOWS
        ):
            raise Phase13AdapterError("Cumulative fixture compatibility metadata is incompatible.")
        n = _integer(row["n"], "complete calibration-prefix count", minimum=0)
        rank = _integer(row["rank_1_indexed"], "cumulative quantile rank", minimum=0)
        expected_rank = _ceil_fraction((n + 1) * Fraction(str(p)))
        if rank != expected_rank:
            raise Phase13AdapterError("Cumulative fixture saved rank differs from the frozen rank.")
        _validate_quantile_row(row, n=n, rank=rank, minimum=50)
        data.at[index, "k"] = k
        data.at[index, "p"] = p
        data.at[index, "n"] = n
        data.at[index, "rank_1_indexed"] = rank
    if actual_keys != expected_keys:
        raise Phase13AdapterError(
            "Cumulative fixture must contain exact prefixes 1..14 and p in {0.90, 0.95, 0.98}."
        )
    by_prefix = data.groupby("k", sort=True)["n"].nunique()
    if not by_prefix.eq(1).all():
        raise Phase13AdapterError(
            "Cumulative probabilities at each prefix must share the same complete-sample count."
        )
    data["k"] = data["k"].astype("int64")
    data["n"] = data["n"].astype("int64")
    data["rank_1_indexed"] = data["rank_1_indexed"].astype("int64")
    return data.reset_index(drop=True)


def _validate_quantile_row(row: pd.Series, *, n: int, rank: int, minimum: int) -> None:
    available = row["available"]
    if not isinstance(available, (bool, np.bool_)):
        raise Phase13AdapterError("Quantile availability must be explicit Boolean.")
    value = row["signed_quantile"]
    reason = None if pd.isna(row["unavailable_reason"]) else row["unavailable_reason"]
    valid_rank = 1 <= rank <= n
    if n < minimum:
        expected_available = False
        expected_reason = "insufficient_calibration"
    elif not valid_rank:
        expected_available = False
        expected_reason = "quantile_rank_unavailable"
    elif _is_finite_scalar(value):
        expected_available = True
        expected_reason = None
    else:
        expected_available = False
        expected_reason = "nonfinite_quantile"
    if bool(available) != expected_available or reason != expected_reason:
        raise Phase13AdapterError(
            "Quantile availability and unsupported reason semantics disagree."
        )
    if expected_available:
        _finite_number(value, "signed quantile")
    elif not pd.isna(value):
        raise Phase13AdapterError("Unavailable quantiles must retain a null signed value.")
    elif not _nonempty_reason(reason):
        raise Phase13AdapterError("Unavailable quantiles require a saved reason.")


def _exact_table(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise Phase13AdapterError(f"{name} must be a pandas DataFrame fixture.")
    _reject_forbidden_columns(frame, name)
    if tuple(frame.columns) != columns:
        raise Phase13AdapterError(f"{name} columns do not match its typed schema.")
    return frame.copy(deep=True)


def _require_unique(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    if frame.duplicated(list(columns)).any():
        raise Phase13AdapterError(f"{name} contains duplicate exact keys.")


def _daily_lookup(
    fixture: SyntheticFitBQuantileFixture,
) -> dict[tuple[int, str], dict[str, Any]]:
    return {
        (int(row.horizon), str(row.tail)): {
            "n": int(row.n),
            "rank_1_indexed": int(row.rank_1_indexed),
            "signed_quantile": _optional_float(row.signed_quantile),
            "available": bool(row.available),
            "unavailable_reason": row.unavailable_reason,
        }
        for row in fixture.daily_to_frame().itertuples(index=False)
    }


def _cumulative_lookup(
    fixture: SyntheticFitBQuantileFixture,
) -> dict[tuple[int, float], dict[str, Any]]:
    return {
        (int(row.k), float(row.p)): {
            "n": int(row.n),
            "rank_1_indexed": int(row.rank_1_indexed),
            "signed_quantile": _optional_float(row.signed_quantile),
            "available": bool(row.available),
            "unavailable_reason": row.unavailable_reason,
        }
        for row in fixture.cumulative_to_frame().itertuples(index=False)
    }


def _raw_interval(
    point: Any,
    *,
    raw_reason: Any,
    lower: dict[str, Any],
    upper: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "pre_lower": None,
        "pre_upper": None,
        "lower_clipped": None,
        "upper_clipped": None,
        "lower": None,
        "upper": None,
        "width": None,
        "available": False,
        "reason": None,
    }
    if point is None or not _is_finite_scalar(point):
        result["reason"] = f"raw_forecast_unavailable:{raw_reason}"
        return result
    if not lower["available"]:
        result["reason"] = f"daily_lower_quantile_unavailable:{lower['unavailable_reason']}"
        return result
    if not upper["available"]:
        result["reason"] = f"daily_upper_quantile_unavailable:{upper['unavailable_reason']}"
        return result
    yhat = _finite_number(point, "raw point forecast")
    q_low = _finite_number(lower["signed_quantile"], "daily lower signed quantile")
    q_high = _finite_number(upper["signed_quantile"], "daily upper signed quantile")
    pre_lower = yhat + q_low
    pre_upper = yhat + q_high
    if not math.isfinite(pre_lower) or not math.isfinite(pre_upper) or pre_lower > pre_upper:
        raise Phase13AdapterError("Raw daily interval endpoints are nonfinite or inverted.")
    clipped_lower = pre_lower < 0.0
    clipped_upper = pre_upper < 0.0
    final_lower = max(0.0, pre_lower)
    final_upper = max(0.0, pre_upper)
    width = final_upper - final_lower
    if not math.isfinite(width) or width < 0.0:
        raise Phase13AdapterError("Raw daily interval width is invalid.")
    result.update(
        {
            "pre_lower": pre_lower,
            "pre_upper": pre_upper,
            "lower_clipped": clipped_lower,
            "upper_clipped": clipped_upper,
            "lower": final_lower,
            "upper": final_upper,
            "width": width,
            "available": True,
        }
    )
    return result


def _add_calibration_metadata(records: pd.DataFrame, fixture: SyntheticFitBQuantileFixture) -> None:
    metadata = fixture.calibration_metadata
    records["calibration_fit_identity"] = metadata.calibration_fit_id
    records["calibration_run_id"] = metadata.run_id
    records["manifest_sha256"] = metadata.manifest_sha256
    records["daily_table_sha256"] = metadata.daily_table_sha256
    records["cumulative_table_sha256"] = metadata.cumulative_table_sha256
    records["policy_config_sha256"] = metadata.policy_config_sha256
    records["calibration_config_sha256"] = metadata.calibration_config_sha256


def _build_prefixes(
    records: pd.DataFrame,
    lookup: dict[tuple[int, float], dict[str, Any]],
    fixture: SyntheticFitBQuantileFixture,
) -> pd.DataFrame:
    output: list[dict[str, Any]] = []
    for store, block in records.groupby("Store", sort=True):
        block = block.sort_values("horizon", kind="mergesort")
        for k in range(1, HORIZON + 1):
            prefix = block.iloc[:k]
            schedule_known = bool(prefix["planned_open_known"].astype(bool).all())
            points_known = bool(prefix["operational_forecast_available"].astype(bool).all())
            components_available = schedule_known and points_known
            demand = (
                float(sum(float(value) for value in prefix["operational_forecast"]))
                if components_available
                else None
            )
            if not schedule_known:
                component_reason = "planned_open_unknown"
            elif not points_known:
                missing = prefix.loc[~prefix["operational_forecast_available"].astype(bool)].iloc[0]
                component_reason = (
                    f"operational_forecast_unavailable_at_h{int(missing['horizon'])}:"
                    f"{missing['operational_unavailable_reason']}"
                )
            else:
                component_reason = None
            for p in CUMULATIVE_LEVELS:
                quantile = lookup[(k, p)]
                q = quantile["signed_quantile"]
                available = components_available and quantile["available"]
                reason = (
                    component_reason
                    if not components_available
                    else quantile["unavailable_reason"]
                    if not quantile["available"]
                    else None
                )
                upper = max(0.0, float(demand) + float(q)) if available else None
                safety = max(0.0, float(upper) - float(demand)) if available else None
                target = max(float(demand), float(upper)) if available else None
                output.append(
                    {
                        "Store": int(store),
                        "forecast_origin": pd.Timestamp(block.iloc[0]["forecast_origin"]).date(),
                        "model_identity": block.iloc[0]["model_identity"],
                        "model_fit_identity": block.iloc[0]["fit_identity"],
                        "calibration_fit_identity": FIT_B_ID,
                        "calibration_run_id": fixture.calibration_metadata.run_id,
                        "calibration_manifest_sha256": (
                            fixture.calibration_metadata.manifest_sha256
                        ),
                        "calibration_daily_table_sha256": (
                            fixture.calibration_metadata.daily_table_sha256
                        ),
                        "calibration_cumulative_table_sha256": (
                            fixture.calibration_metadata.cumulative_table_sha256
                        ),
                        "calibration_policy_config_sha256": (
                            fixture.calibration_metadata.policy_config_sha256
                        ),
                        "calibration_config_sha256": (
                            fixture.calibration_metadata.calibration_config_sha256
                        ),
                        "quantile_fixture_identity": fixture.fixture_identity,
                        "cumulative_fixture_sha256": fixture.cumulative_fixture_sha256,
                        "schedule_identity": block.iloc[0]["schedule_identity"],
                        "schedule_rule_id": block.iloc[0]["planned_open_rule_id"],
                        "schedule_source_id": block.iloc[0]["schedule_source_id"],
                        "schedule_version": block.iloc[0]["schedule_version"],
                        "schedule_provenance": block.iloc[0]["schedule_provenance"],
                        "schedule_availability_assumption": (
                            block.iloc[0]["schedule_availability_assumption"]
                        ),
                        "k": k,
                        "p": p,
                        "complete_operational_prefix": bool(components_available),
                        "operational_prefix_unavailable_reason": component_reason,
                        "operational_cumulative_forecast": demand,
                        "cumulative_signed_quantile": q,
                        "quantile_available": bool(quantile["available"]),
                        "quantile_unavailable_reason": quantile["unavailable_reason"],
                        "cumulative_quantile_n": quantile["n"],
                        "cumulative_quantile_rank_1_indexed": quantile["rank_1_indexed"],
                        "upper_turnover": upper,
                        "safety_stock": safety,
                        "target": target,
                        "available": bool(available),
                        "unavailable_reason": reason,
                        "transport_status": fixture.transport.transport_status,
                    }
                )
    result = pd.DataFrame.from_records(output)
    if result.duplicated(["Store", "forecast_origin", "k", "p"]).any():
        raise Phase13AdapterError("Cumulative prefix output contains duplicate exact keys.")
    return result


def _table_sha256(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
    sort_columns: tuple[str, ...],
) -> str:
    data = frame.loc[:, columns].sort_values(list(sort_columns), kind="mergesort")
    return hashlib.sha256(_canonical_json_bytes(data.to_dict(orient="records"))).hexdigest()


def _raw_issuance_identity(issuance: RawForecastIssuance, records: pd.DataFrame) -> str:
    return _digest(
        {
            "origin": issuance.origin.isoformat(),
            "grid_identity": issuance.grid_identity,
            "recipe_identity": issuance.recipe_identity,
            "feature_schema_identity": issuance.feature_schema_identity,
            "model_identity": issuance.model_identity,
            "fit_identity": issuance.fit_identity,
            "input_identities": issuance.input_identities,
            "records_sha256": hashlib.sha256(
                _canonical_json_bytes(records.to_dict(orient="records"))
            ).hexdigest(),
        }
    )


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _normalize_json(value),
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json(item) for item in value]
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        stamp = pd.Timestamp(value)
        return stamp.date().isoformat() if stamp == stamp.normalize() else stamp.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.str_, str)):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _reject_forbidden_columns(frame: pd.DataFrame, name: str) -> None:
    forbidden = sorted(
        str(column)
        for column in frame.columns
        if str(column).casefold() in _FORBIDDEN_INPUT_NAMES
        or str(column).casefold().startswith("actual_")
        or "customer" in str(column).casefold()
    )
    if forbidden:
        raise Phase13AdapterError(f"{name} contains forbidden outcome fields: {forbidden}.")


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise Phase13AdapterError(f"{name} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise Phase13AdapterError(f"{name} must be a finite number.") from exc
    if not math.isfinite(number):
        raise Phase13AdapterError(f"{name} must be a finite number.")
    return number


def _optional_float(value: Any) -> float | None:
    return None if pd.isna(value) else _finite_number(value, "signed quantile")


def _integer(value: Any, name: str, *, minimum: int) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise Phase13AdapterError(f"{name} must be an integer.")
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise Phase13AdapterError(f"{name} must be an integer.") from exc
    if not math.isfinite(numeric) or not numeric.is_integer() or numeric < minimum:
        raise Phase13AdapterError(f"{name} must be an integer >= {minimum}.")
    return int(numeric)


def _is_finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _is_missing_scalar(value: Any) -> bool:
    """Return whether a single scalar is null without accepting array-shaped values."""

    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return isinstance(result, (bool, np.bool_)) and bool(result)


def _nonempty_reason(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _ceil_fraction(value: Fraction) -> int:
    return (value.numerator + value.denominator - 1) // value.denominator


__all__ = [
    "CUMULATIVE_LEVELS",
    "FIT_B_ID",
    "FIT_B_RUN_ID",
    "FROZEN_FIT_B_METADATA",
    "FitBCanonicalMetadata",
    "FitBTransportMetadata",
    "OriginFrozenStandingTargets",
    "Phase13AdapterError",
    "Phase13M3Adapter",
    "Phase13M3Issuance",
    "SyntheticFitBQuantileFixture",
    "SyntheticHistoricalMeanAnchor",
    "SyntheticHistoricalMeanAnchorCollection",
    "build_origin_frozen_targets",
    "load_canonical_fit_b_quantiles",
]
