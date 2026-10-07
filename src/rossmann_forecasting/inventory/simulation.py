"""Approved Phase 10 origin-frozen inventory-value simulation.

Targets are constructed from a deliberately narrow safe-input projection. Realized
historical and synthetic demand is loaded only after every target has been frozen.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import tempfile
import uuid
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from rossmann_forecasting.inventory import scenarios

POLICY_VERSION = "phase-10-adr-023-v1"
SCHEMA_VERSION = "phase-10-inventory-simulation-v1"
HORIZON_DAYS = 14
REVIEW_PERIOD = 1
ALLOWED_LEAD_TIMES = (2, 3, 4, 5, 6, 7)
REFERENCE_P = 0.95
ALLOWED_P = (0.90, 0.95, 0.98)
POLICY_IDS = ("historical_mean_standing_target", "lightgbm_buffer_standing_target")
REFERENCE_VARIANT = "reference"
PHASE7_RUN_ID = "365f22d4c3f94722a594ab934a22c4f6"
PHASE7_MANIFEST_SHA256 = "03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc"
PHASE8_CUMULATIVE_SHA256 = "1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff"
PHASE8_RUN_ID = "phase8-impl-20261006-provenance-review"
PHASE8_MANIFEST_SHA256 = "63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2"
PHASE9_RUN_ID = "phase9-dev-20261007-config-validation-fix"
PHASE9_MANIFEST_SHA256 = "573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761"
PHASE7_SAFE_COLUMNS = (
    "Store",
    "forecast_origin",
    "Date",
    "horizon",
    "raw_forecast",
    "forecast_available",
    "source_open",
)
TARGET_INPUT_COLUMNS = (
    "case_id",
    "scenario_id",
    "Store",
    "forecast_origin",
    "family",
    "mode",
    "replicate",
    "sensitivity_variant",
    "SupplierLeadTime",
    "ReviewPeriod",
    "ProtectionPeriod",
    "buffer_probability",
    "mean_open_sales_value",
    "anchor_available",
    "initial_stock_value",
    "ProcurementCostRatio",
    "AnnualHoldingRate",
    "GoodwillPenaltyRate",
    "horizon",
    "schedule_open",
    "raw_point_forecast",
    "forecast_available",
    "cumulative_signed_quantile",
    "quantile_available",
    "quantile_unavailable_reason",
    "fit_id",
    "model_id",
    "upstream_identity",
    "synthetic",
    "schedule_assumption",
)
FORBIDDEN_TARGET_COLUMNS = frozenset(
    {
        "Sales",
        "actual_sales",
        "SyntheticDemandValue",
        "synthetic_demand_value",
        "future_stress",
        "DemandStressFactor",
        "raw_residual",
        "operational_residual",
        "residual",
        "actual_total",
        "assessment_actual_total",
        "interval_hit",
        "hit",
        "fulfilled_value",
        "unmet_value",
        "future_realized_demand",
    }
)


class SimulationIntegrityError(ValueError):
    """Raised when approved simulation inputs or outputs violate ADR-023."""


def _field(name: str, dtype: pa.DataType, nullable: bool = False) -> pa.Field:
    return pa.field(name, dtype, nullable=nullable)


POLICY_TARGET_SCHEMA = pa.schema(
    [
        _field("case_id", pa.string()),
        _field("scenario_id", pa.string()),
        _field("Store", pa.int64()),
        _field("forecast_origin", pa.date32()),
        _field("family", pa.string()),
        _field("mode", pa.string()),
        _field("replicate", pa.int8()),
        _field("sensitivity_variant", pa.string()),
        _field("policy_id", pa.string()),
        _field("SupplierLeadTime", pa.int8()),
        _field("ReviewPeriod", pa.int8()),
        _field("ProtectionPeriod", pa.int8()),
        _field("buffer_probability", pa.float64(), True),
        _field("mean_open_sales_value", pa.float64(), True),
        _field("open_days_in_protection_period", pa.int8(), True),
        _field("forecast_protection_demand_value", pa.float64(), True),
        _field("cumulative_signed_quantile", pa.float64(), True),
        _field("upper_turnover_value", pa.float64(), True),
        _field("safety_stock_value", pa.float64(), True),
        _field("target_value", pa.float64(), True),
        _field("initial_stock_value", pa.float64(), True),
        _field("ProcurementCostRatio", pa.float64()),
        _field("AnnualHoldingRate", pa.float64()),
        _field("GoodwillPenaltyRate", pa.float64()),
        _field("fit_id", pa.string()),
        _field("model_id", pa.string()),
        _field("upstream_identity", pa.string()),
        _field("synthetic", pa.bool_()),
        _field("calibration_transport_valid", pa.bool_()),
        _field("buffer_interpretation", pa.string()),
        _field("schedule_assumption", pa.string()),
        _field("target_available", pa.bool_()),
        _field("availability_reason", pa.string(), True),
    ]
)

SIMULATION_LEDGER_SCHEMA = pa.schema(
    [
        _field("case_id", pa.string()),
        _field("scenario_id", pa.string()),
        _field("Store", pa.int64()),
        _field("policy_id", pa.string()),
        _field("Date", pa.date32()),
        _field("forecast_origin", pa.date32()),
        _field("family", pa.string()),
        _field("mode", pa.string()),
        _field("replicate", pa.int8()),
        _field("sensitivity_variant", pa.string()),
        _field("horizon", pa.int8()),
        _field("SupplierLeadTime", pa.int8()),
        _field("ProtectionPeriod", pa.int8()),
        _field("ProcurementCostRatio", pa.float64()),
        _field("AnnualHoldingRate", pa.float64()),
        _field("GoodwillPenaltyRate", pa.float64()),
        _field("HoldingCostRate", pa.float64()),
        _field("UnmetPenaltyRate", pa.float64()),
        _field("target_value", pa.float64(), True),
        _field("target_available", pa.bool_()),
        _field("ScenarioOpen", pa.int8(), True),
        _field("source_open", pa.int8(), True),
        _field("starting_inventory_value", pa.float64(), True),
        _field("receipts_today_value", pa.float64(), True),
        _field("available_stock_value", pa.float64(), True),
        _field("demand_value", pa.float64(), True),
        _field("fulfilled_value", pa.float64(), True),
        _field("unmet_value", pa.float64(), True),
        _field("ending_inventory_value", pa.float64(), True),
        _field("pipeline_before_receipt_value", pa.float64(), True),
        _field("pipeline_after_receipt_value", pa.float64(), True),
        _field("pipeline_after_review_value", pa.float64(), True),
        _field("inventory_position_value", pa.float64(), True),
        _field("order_value", pa.float64(), True),
        _field("order_id", pa.string(), True),
        _field("order_due_date", pa.date32(), True),
        _field("received_order_ids", pa.string()),
        _field("holding_cost", pa.float64(), True),
        _field("unmet_penalty", pa.float64(), True),
        _field("review_status", pa.string()),
        _field("state_available", pa.bool_()),
        _field("state_unavailable_reason", pa.string(), True),
        _field("historical_open_assumption_violation", pa.bool_()),
    ]
)

POLICY_SUMMARY_SCHEMA = pa.schema(
    [
        _field("case_id", pa.string()),
        _field("scenario_id", pa.string()),
        _field("Store", pa.int64()),
        _field("forecast_origin", pa.date32()),
        _field("family", pa.string()),
        _field("mode", pa.string()),
        _field("replicate", pa.int8()),
        _field("sensitivity_variant", pa.string()),
        _field("policy_id", pa.string()),
        _field("episode_status", pa.string()),
        _field("episode_complete", pa.bool_()),
        _field("target_available", pa.bool_()),
        _field("availability_reason", pa.string(), True),
        _field("valid_matched_comparison", pa.bool_()),
        _field("historical_open_assumption_violation", pa.bool_()),
        _field("calendar_days", pa.int8()),
        _field("demand_total", pa.float64(), True),
        _field("fulfilled_total", pa.float64(), True),
        _field("unmet_total", pa.float64(), True),
        _field("positive_demand_days", pa.int8(), True),
        _field("positive_demand_stockout_days", pa.int8(), True),
        _field("ending_inventory_sum", pa.float64(), True),
        _field("holding_cost_total", pa.float64(), True),
        _field("unmet_penalty_total", pa.float64(), True),
        _field("SimulatedHoldingPlusShortfallCost", pa.float64(), True),
        _field("ValueFillRate", pa.float64(), True),
        _field("PositiveDemandStockoutRate", pa.float64(), True),
        _field("AverageInventoryValue", pa.float64(), True),
        _field("UnmetTurnoverValue", pa.float64(), True),
        _field("SimulatedHoldingCost", pa.float64(), True),
        _field("SimulatedUnmetPenalty", pa.float64(), True),
        _field("CompletedPositiveDemandReceiptCycleServiceRate", pa.float64(), True),
        _field("completed_cycles_total", pa.int8(), True),
        _field("completed_positive_demand_cycles", pa.int8(), True),
        _field("zero_unmet_positive_demand_cycles", pa.int8(), True),
        _field("zero_demand_completed_cycles", pa.int8(), True),
        _field("initial_left_censored_intervals", pa.int8(), True),
        _field("terminal_right_censored_intervals", pa.int8(), True),
        _field("terminal_on_hand_value", pa.float64(), True),
        _field("terminal_on_order_value", pa.float64(), True),
        _field("TerminalStockCostValue", pa.float64(), True),
        _field("OutstandingProcurementCommitment", pa.float64(), True),
        _field("late_order_count", pa.int8(), True),
        _field("late_order_value", pa.float64(), True),
        _field("common_input_identity", pa.string()),
    ]
)

COMPARISON_COLUMNS = (
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
COMPARISON_SCHEMA = pa.schema(
    [
        _field("case_id", pa.string()),
        _field("metric", pa.string()),
        _field("requested_store_count", pa.int64()),
        _field("baseline_standalone_store_count", pa.int64()),
        _field("forecast_standalone_store_count", pa.int64()),
        _field("matched_store_count", pa.int64()),
        _field("baseline_numerator", pa.float64(), True),
        _field("baseline_denominator", pa.float64(), True),
        _field("forecast_numerator", pa.float64(), True),
        _field("forecast_denominator", pa.float64(), True),
        _field("baseline_value", pa.float64(), True),
        _field("forecast_value", pa.float64(), True),
        _field("forecast_minus_baseline", pa.float64(), True),
        _field("forecast_minus_baseline_relative", pa.float64(), True),
        _field("relative_difference_null_reason", pa.string(), True),
        _field("null_reason", pa.string(), True),
        _field("interpretation", pa.string()),
    ]
)


@dataclass(frozen=True)
class SimulationConfig:
    horizon_days: int = HORIZON_DAYS
    review_period: int = REVIEW_PERIOD
    allowed_origins: tuple[date, ...] = scenarios.ALLOWED_ORIGINS
    lead_times: tuple[int, ...] = ALLOWED_LEAD_TIMES
    reference_probability: float = REFERENCE_P
    sensitivity_probabilities: tuple[float, ...] = (0.90, 0.98)
    policy_ids: tuple[str, ...] = POLICY_IDS
    terminal_review_suppressed: bool = True


def default_simulation_config() -> dict[str, Any]:
    """Return the fixed ADR-023 execution contract; callers cannot tune its domain."""
    config = SimulationConfig()
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "decision": "ADR-023",
        "horizon_days": config.horizon_days,
        "review_period": config.review_period,
        "allowed_origins": [value.isoformat() for value in config.allowed_origins],
        "lead_times": list(config.lead_times),
        "protection_period_rule": "P=L+R; L full intervening demand days; EOD t -> BO-day t+L+1",
        "reference_probability": config.reference_probability,
        "sensitivity_probabilities": list(config.sensitivity_probabilities),
        "policy_ids": list(config.policy_ids),
        "sensitivity_variants": {
            "lead_2": {"SupplierLeadTime": 2},
            "lead_7": {"SupplierLeadTime": 7},
            "buffer_090": {"buffer_probability": 0.90},
            "buffer_098": {"buffer_probability": 0.98},
            "holding_010": {"AnnualHoldingRate": 0.10},
            "holding_030": {"AnnualHoldingRate": 0.30},
            "goodwill_010": {"GoodwillPenaltyRate": 0.10},
            "goodwill_075": {"GoodwillPenaltyRate": 0.75},
            "coverage_1": {"InventoryCoverageDays": 1},
        },
        "cost_rules": {
            "holding_cost_rate": "ProcurementCostRatio * AnnualHoldingRate / 365",
            "unmet_penalty_rate": "(1 - ProcurementCostRatio) + GoodwillPenaltyRate",
            "pipeline_carrying_cost": False,
            "procurement_expenditure_in_primary_objective": False,
        },
        "terminal_rule": (
            "receive due-on-T; suppress review; retain after-T orders; no later simulation"
        ),
        "simulation_seed": "not_applicable",
        "inherited_phase9_seed": 4209,
    }


def _validate_origin(origin: date | str) -> date:
    value = pd.Timestamp(origin).date()
    if value not in scenarios.ALLOWED_ORIGINS:
        raise SimulationIntegrityError(
            "Unsupported origin rejected before opening any outcome-bearing artifact."
        )
    if value + timedelta(days=HORIZON_DAYS) > scenarios.DEVELOPMENT_CUTOFF:
        raise SimulationIntegrityError("H14 target crosses the development cutoff.")
    return value


def _number(value: Any, name: str, *, nonnegative: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise SimulationIntegrityError(f"{name} must be numeric.") from error
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise SimulationIntegrityError(f"{name} must be finite and nonnegative when required.")
    return result


def _close(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= 1e-9 * max(1.0, abs(expected))


def _is_null(value: Any) -> bool:
    return value is None or bool(pd.isna(value))


def _ensure_allowed_target_columns(frame: pd.DataFrame) -> None:
    columns = set(frame.columns)
    forbidden = sorted(columns & FORBIDDEN_TARGET_COLUMNS)
    extra = sorted(columns - set(TARGET_INPUT_COLUMNS))
    missing = sorted(set(TARGET_INPUT_COLUMNS) - columns)
    if forbidden:
        raise SimulationIntegrityError(
            f"Target construction rejects realized/outcome columns: {forbidden}."
        )
    if extra or missing:
        raise SimulationIntegrityError(
            f"Target input schema mismatch; extra={extra}, missing={missing}."
        )


def build_policy_targets(target_inputs: pd.DataFrame) -> pa.Table:
    """Freeze both targets from the explicit safe-input projection only.

    The exact column allowlist prevents realized Sales, synthetic demand, residuals,
    stress outcomes and assessment labels from entering target construction.
    """
    if not isinstance(target_inputs, pd.DataFrame):
        raise TypeError("target_inputs must be a pandas DataFrame with the safe input schema.")
    _ensure_allowed_target_columns(target_inputs)
    source = target_inputs.copy(deep=True)
    if source.empty:
        return pa.Table.from_pylist([], schema=POLICY_TARGET_SCHEMA)
    grouping = ["case_id", "Store"]
    if source.duplicated(grouping + ["horizon"]).any():
        raise SimulationIntegrityError("Target input has duplicate case/Store/horizon keys.")
    rows: list[dict[str, Any]] = []
    for _, block in source.sort_values(grouping + ["horizon"], kind="mergesort").groupby(
        grouping, sort=True
    ):
        first = block.iloc[0]
        origin = _validate_origin(first.forecast_origin)
        lead = int(first.SupplierLeadTime)
        review = int(first.ReviewPeriod)
        protection = int(first.ProtectionPeriod)
        if lead not in ALLOWED_LEAD_TIMES or review != REVIEW_PERIOD or protection != lead + review:
            raise SimulationIntegrityError("Invalid L/R/P target domain.")
        if protection > HORIZON_DAYS:
            raise SimulationIntegrityError("Protection period exceeds H14.")
        if set(block["horizon"].astype(int)) != set(range(1, protection + 1)):
            raise SimulationIntegrityError("Target prefix must contain exactly h1 through hP.")
        for column in TARGET_INPUT_COLUMNS:
            if column in {"horizon", "schedule_open", "raw_point_forecast", "forecast_available"}:
                continue
            if block[column].nunique(dropna=False) != 1:
                raise SimulationIntegrityError(f"Target input {column} changes within its prefix.")
        p = float(first.buffer_probability)
        if p not in ALLOWED_P:
            raise SimulationIntegrityError("Only p in {0.90, 0.95, 0.98} is permitted.")
        schedule = block.sort_values("horizon", kind="mergesort")["schedule_open"].tolist()
        prefix_schedule_known = all(value in (0, 1, 0.0, 1.0) for value in schedule)
        open_days = int(sum(int(value) for value in schedule)) if prefix_schedule_known else None
        mean_value = None
        if bool(first.anchor_available) and not pd.isna(first.mean_open_sales_value):
            mean_value = _number(
                first.mean_open_sales_value, "mean_open_sales_value", nonnegative=True
            )
        initial = (
            None
            if pd.isna(first.initial_stock_value)
            else _number(first.initial_stock_value, "initial_stock_value", nonnegative=True)
        )
        base_available = prefix_schedule_known and mean_value is not None
        base_target = mean_value * int(open_days) if base_available else None
        point_values: list[float] = []
        points_available = True
        for day in block.sort_values("horizon", kind="mergesort").itertuples(index=False):
            opening = day.schedule_open
            if opening not in (0, 1, 0.0, 1.0):
                points_available = False
                break
            if int(opening) == 0:
                point_values.append(0.0)
            elif not bool(day.forecast_available) or pd.isna(day.raw_point_forecast):
                points_available = False
                break
            else:
                point_values.append(
                    _number(day.raw_point_forecast, "raw_point_forecast", nonnegative=True)
                )
        q = (
            None
            if pd.isna(first.cumulative_signed_quantile)
            else _number(first.cumulative_signed_quantile, "cumulative_signed_quantile")
        )
        q_available = bool(first.quantile_available) and q is not None
        fit_id = str(first.fit_id)
        expected_fit = scenarios.FIT_BY_ORIGIN[origin]
        if fit_id != expected_fit:
            raise SimulationIntegrityError("Origin and Phase 8 fit identity are incompatible.")
        if str(first.model_id) != "global_lightgbm_gbdt_regression_l1":
            raise SimulationIntegrityError(
                "Target inputs use an unapproved Phase 7 model identity."
            )
        forecast_available = points_available and q_available and prefix_schedule_known
        demand_sum = float(sum(point_values)) if points_available else None
        upper = max(0.0, demand_sum + q) if forecast_available else None
        safety = max(0.0, upper - demand_sum) if forecast_available else None
        forecast_target = max(demand_sum, upper) if forecast_available else None
        synthetic = bool(first.synthetic)
        base_reason = (
            None
            if base_available
            else (
                "unknown_schedule_in_protection_prefix"
                if not prefix_schedule_known
                else "anchor_unavailable"
            )
        )
        forecast_reason = None
        if not forecast_available:
            if not prefix_schedule_known:
                forecast_reason = "unknown_schedule_in_protection_prefix"
            elif not points_available:
                forecast_reason = "operational_point_prefix_unavailable"
            elif not q_available:
                forecast_reason = str(
                    first.quantile_unavailable_reason or "cumulative_quantile_unavailable"
                )
            else:
                forecast_reason = "forecast_target_unavailable"
        common = {
            "case_id": str(first.case_id),
            "scenario_id": str(first.scenario_id),
            "Store": int(first.Store),
            "forecast_origin": origin,
            "family": str(first.family),
            "mode": str(first["mode"]),
            "replicate": int(first.replicate),
            "sensitivity_variant": str(first.sensitivity_variant),
            "SupplierLeadTime": lead,
            "ReviewPeriod": review,
            "ProtectionPeriod": protection,
            "buffer_probability": p,
            "mean_open_sales_value": mean_value,
            "open_days_in_protection_period": open_days,
            "initial_stock_value": initial,
            "ProcurementCostRatio": _number(
                first.ProcurementCostRatio, "ProcurementCostRatio", nonnegative=True
            ),
            "AnnualHoldingRate": _number(
                first.AnnualHoldingRate, "AnnualHoldingRate", nonnegative=True
            ),
            "GoodwillPenaltyRate": _number(
                first.GoodwillPenaltyRate, "GoodwillPenaltyRate", nonnegative=True
            ),
            "fit_id": fit_id,
            "model_id": str(first.model_id),
            "upstream_identity": str(first.upstream_identity),
            "synthetic": synthetic,
            "schedule_assumption": str(first.schedule_assumption),
        }
        rows.append(
            {
                **common,
                "policy_id": POLICY_IDS[0],
                "forecast_protection_demand_value": None,
                "cumulative_signed_quantile": None,
                "upper_turnover_value": None,
                "safety_stock_value": None,
                "target_value": base_target,
                "calibration_transport_valid": not synthetic,
                "buffer_interpretation": "historical_mean_open_day_target",
                "target_available": bool(base_available),
                "availability_reason": base_reason,
            }
        )
        rows.append(
            {
                **common,
                "policy_id": POLICY_IDS[1],
                "forecast_protection_demand_value": demand_sum,
                "cumulative_signed_quantile": q,
                "upper_turnover_value": upper,
                "safety_stock_value": safety,
                "target_value": forecast_target,
                "calibration_transport_valid": not synthetic,
                "buffer_interpretation": (
                    "uncalibrated_synthetic_heuristic"
                    if synthetic
                    else "historical_conditional_cumulative_buffer"
                ),
                "target_available": bool(forecast_available),
                "availability_reason": forecast_reason,
            }
        )
    table = pa.Table.from_pylist(rows, schema=POLICY_TARGET_SCHEMA)
    _assert_unique(table, ("case_id", "Store", "policy_id"), "policy targets")
    return table


def _assert_unique(table: pa.Table, keys: Sequence[str], name: str) -> None:
    if table.num_rows == 0:
        return
    frame = table.select(list(keys)).to_pandas()
    if frame.duplicated(list(keys)).any():
        raise SimulationIntegrityError(f"{name} contains duplicate keys {tuple(keys)}.")


def _origin_record(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "case_id": target["case_id"],
        "scenario_id": target["scenario_id"],
        "Store": int(target["Store"]),
        "policy_id": target["policy_id"],
        "Date": target["forecast_origin"],
        "forecast_origin": target["forecast_origin"],
        "family": target["family"],
        "mode": target["mode"],
        "replicate": int(target["replicate"]),
        "sensitivity_variant": target["sensitivity_variant"],
        "horizon": 0,
        "SupplierLeadTime": int(target["SupplierLeadTime"]),
        "ProtectionPeriod": int(target["ProtectionPeriod"]),
        "ProcurementCostRatio": float(target["ProcurementCostRatio"]),
        "AnnualHoldingRate": float(target["AnnualHoldingRate"]),
        "GoodwillPenaltyRate": float(target["GoodwillPenaltyRate"]),
        "HoldingCostRate": float(target["ProcurementCostRatio"])
        * float(target["AnnualHoldingRate"])
        / 365.0,
        "UnmetPenaltyRate": (1.0 - float(target["ProcurementCostRatio"]))
        + float(target["GoodwillPenaltyRate"]),
        "target_value": target["target_value"],
        "target_available": bool(target["target_available"]),
        "ScenarioOpen": None,
        "source_open": None,
        "starting_inventory_value": target["initial_stock_value"],
        "receipts_today_value": 0.0,
        "available_stock_value": target["initial_stock_value"],
        "demand_value": None,
        "fulfilled_value": None,
        "unmet_value": None,
        "ending_inventory_value": target["initial_stock_value"],
        "pipeline_before_receipt_value": 0.0,
        "pipeline_after_receipt_value": 0.0,
        "pipeline_after_review_value": None,
        "inventory_position_value": None,
        "order_value": None,
        "order_id": None,
        "order_due_date": None,
        "received_order_ids": "",
        "holding_cost": 0.0,
        "unmet_penalty": 0.0,
        "review_status": "origin_review_unavailable",
        "state_available": False,
        "state_unavailable_reason": None,
        "historical_open_assumption_violation": False,
    }


def simulate_case(
    target: Mapping[str, Any],
    demand_path: Sequence[Mapping[str, Any]],
    *,
    common_input_identity: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Simulate one policy on a frozen target and a subsequently revealed demand path."""
    if target.get("policy_id") not in POLICY_IDS:
        raise SimulationIntegrityError("Unknown policy ID.")
    origin = _validate_origin(target["forecast_origin"])
    lead = int(target["SupplierLeadTime"])
    protection = int(target["ProtectionPeriod"])
    if lead not in ALLOWED_LEAD_TIMES or protection != lead + 1:
        raise SimulationIntegrityError("Invalid lead/protection period in simulation target.")
    if len(demand_path) != HORIZON_DAYS:
        raise SimulationIntegrityError("Simulation demand path must contain h1..h14.")
    ordered_path = sorted((dict(item) for item in demand_path), key=lambda row: int(row["horizon"]))
    if [int(row["horizon"]) for row in ordered_path] != list(range(1, HORIZON_DAYS + 1)):
        raise SimulationIntegrityError("Simulation demand path must be exactly h1..h14.")
    c = _number(target["ProcurementCostRatio"], "ProcurementCostRatio", nonnegative=True)
    annual = _number(target["AnnualHoldingRate"], "AnnualHoldingRate", nonnegative=True)
    goodwill = _number(target["GoodwillPenaltyRate"], "GoodwillPenaltyRate", nonnegative=True)
    holding_rate = c * annual / 365.0
    unmet_rate = (1.0 - c) + goodwill
    rows = [_origin_record(target)]
    initial = target.get("initial_stock_value")
    if initial is None or pd.isna(initial):
        return _unavailable_case(target, rows, "initialization_unavailable", common_input_identity)
    initial_stock = _number(initial, "initial_stock_value", nonnegative=True)
    if not bool(target["target_available"]):
        return _unavailable_case(
            target,
            rows,
            str(target.get("availability_reason") or "policy_target_unavailable"),
            common_input_identity,
        )
    standing_target = _number(target["target_value"], "target_value", nonnegative=True)
    stock = initial_stock
    queue: list[dict[str, Any]] = []
    all_orders: list[dict[str, Any]] = []
    origin_q = max(0.0, standing_target - stock)
    origin_id = None
    origin_due = None
    if origin_q > 0:
        origin_id = f"{target['case_id']}:{target['Store']}:{target['policy_id']}:h0"
        origin_due = origin + timedelta(days=lead + 1)
        order = {
            "order_id": origin_id,
            "placement_date": origin,
            "due_date": origin_due,
            "value": origin_q,
        }
        queue.append(order)
        all_orders.append(order)
    rows[0].update(
        {
            "review_status": "origin_review",
            "state_available": True,
            "state_unavailable_reason": None,
            "inventory_position_value": stock,
            "order_value": origin_q,
            "order_id": origin_id,
            "order_due_date": origin_due,
            "pipeline_after_review_value": sum(item["value"] for item in queue),
        }
    )
    broken_reason: str | None = None
    for day in ordered_path:
        horizon = int(day["horizon"])
        current = origin + timedelta(days=horizon)
        ledger = {
            **_origin_record(target),
            "Date": current,
            "horizon": horizon,
            "ScenarioOpen": day.get("ScenarioOpen"),
            "source_open": day.get("source_open"),
            "starting_inventory_value": stock,
            "receipts_today_value": 0.0,
            "available_stock_value": stock,
            "review_status": "state_unavailable",
            "state_available": False,
            "state_unavailable_reason": None,
        }
        if broken_reason is not None:
            for field in (
                "starting_inventory_value",
                "receipts_today_value",
                "available_stock_value",
                "demand_value",
                "fulfilled_value",
                "unmet_value",
                "ending_inventory_value",
                "pipeline_before_receipt_value",
                "pipeline_after_receipt_value",
                "pipeline_after_review_value",
                "inventory_position_value",
                "order_value",
                "order_id",
                "order_due_date",
                "holding_cost",
                "unmet_penalty",
            ):
                ledger[field] = None
            ledger["received_order_ids"] = ""
            ledger["review_status"] = "state_unavailable_after_missing_demand"
            ledger["state_unavailable_reason"] = broken_reason
            rows.append(ledger)
            continue
        before = sum(item["value"] for item in queue)
        due = [item for item in queue if item["due_date"] == current]
        overdue = [item for item in queue if item["due_date"] < current]
        if overdue:
            raise SimulationIntegrityError(
                "An outstanding order passed its due date without receipt."
            )
        receipt = sum(item["value"] for item in due)
        queue = [item for item in queue if item not in due]
        after_receipt = sum(item["value"] for item in queue)
        source_demand = day.get("demand_value")
        demand_available = bool(day.get("demand_available")) and source_demand is not None
        if not demand_available or pd.isna(source_demand):
            broken_reason = str(day.get("unavailable_reason") or "demand_unavailable")
            ledger.update(
                {
                    "starting_inventory_value": stock,
                    "receipts_today_value": receipt,
                    "available_stock_value": stock + receipt,
                    "received_order_ids": ",".join(item["order_id"] for item in due),
                    "pipeline_before_receipt_value": before,
                    "pipeline_after_receipt_value": after_receipt,
                    "pipeline_after_review_value": None,
                    "review_status": "demand_unavailable",
                    "state_unavailable_reason": broken_reason,
                }
            )
            rows.append(ledger)
            continue
        demand = _number(source_demand, "demand_value", nonnegative=True)
        available_stock = stock + receipt
        fulfilled = min(available_stock, demand)
        unmet = demand - fulfilled
        ending = available_stock - fulfilled
        position = ending + after_receipt
        order_value = max(0.0, standing_target - position) if horizon < HORIZON_DAYS else 0.0
        new_order = None
        if order_value > 0:
            order_id = f"{target['case_id']}:{target['Store']}:{target['policy_id']}:h{horizon}"
            due_date = current + timedelta(days=lead + 1)
            new_order = {
                "order_id": order_id,
                "placement_date": current,
                "due_date": due_date,
                "value": order_value,
            }
            queue.append(new_order)
            all_orders.append(new_order)
        pipeline_after = sum(item["value"] for item in queue)
        holding_cost = holding_rate * ending
        unmet_penalty = unmet_rate * unmet
        assumption_violation = bool(day.get("historical_open_assumption_violation", False))
        ledger.update(
            {
                "starting_inventory_value": stock,
                "receipts_today_value": receipt,
                "available_stock_value": available_stock,
                "demand_value": demand,
                "fulfilled_value": fulfilled,
                "unmet_value": unmet,
                "ending_inventory_value": ending,
                "pipeline_before_receipt_value": before,
                "pipeline_after_receipt_value": after_receipt,
                "pipeline_after_review_value": pipeline_after,
                "inventory_position_value": position,
                "order_value": order_value,
                "order_id": new_order["order_id"] if new_order else None,
                "order_due_date": new_order["due_date"] if new_order else None,
                "received_order_ids": ",".join(item["order_id"] for item in due),
                "holding_cost": holding_cost,
                "unmet_penalty": unmet_penalty,
                "review_status": "terminal_boundary" if horizon == HORIZON_DAYS else "reviewed",
                "state_available": True,
                "state_unavailable_reason": None,
                "historical_open_assumption_violation": assumption_violation,
            }
        )
        if not _close(available_stock, stock + receipt):
            raise SimulationIntegrityError("Daily available-stock balance failed.")
        if not _close(demand, fulfilled + unmet) or not _close(ending, available_stock - fulfilled):
            raise SimulationIntegrityError("Daily lost-sales/inventory balance failed.")
        if ending < 0 or pipeline_after < 0 or holding_cost < 0 or unmet_penalty < 0:
            raise SimulationIntegrityError("Negative inventory, pipeline or cost state.")
        if horizon == HORIZON_DAYS and (order_value != 0 or new_order is not None):
            raise SimulationIntegrityError("The terminal day must suppress ordering.")
        rows.append(ledger)
        stock = ending
    summary = summarize_simulation(
        target, rows, all_orders, common_input_identity=common_input_identity
    )
    return rows, summary


def _unavailable_case(
    target: Mapping[str, Any], rows: list[dict[str, Any]], reason: str, identity: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows[0]["review_status"] = "origin_review_unavailable"
    rows[0]["state_available"] = False
    rows[0]["state_unavailable_reason"] = reason
    for horizon in range(1, HORIZON_DAYS + 1):
        current = target["forecast_origin"] + timedelta(days=horizon)
        row = dict(rows[0])
        row.update(
            {
                "Date": current,
                "horizon": horizon,
                "ScenarioOpen": None,
                "source_open": None,
                "starting_inventory_value": None,
                "receipts_today_value": None,
                "available_stock_value": None,
                "demand_value": None,
                "fulfilled_value": None,
                "unmet_value": None,
                "ending_inventory_value": None,
                "pipeline_before_receipt_value": None,
                "pipeline_after_receipt_value": None,
                "pipeline_after_review_value": None,
                "inventory_position_value": None,
                "order_value": None,
                "order_id": None,
                "order_due_date": None,
                "received_order_ids": "",
                "holding_cost": None,
                "unmet_penalty": None,
                "review_status": "track_unavailable",
                "state_available": False,
                "state_unavailable_reason": reason,
                "historical_open_assumption_violation": False,
            }
        )
        rows.append(row)
    base = {name: None for name in POLICY_SUMMARY_SCHEMA.names}
    base.update(
        {
            "case_id": target["case_id"],
            "scenario_id": target["scenario_id"],
            "Store": int(target["Store"]),
            "forecast_origin": target["forecast_origin"],
            "family": target["family"],
            "mode": target["mode"],
            "replicate": int(target["replicate"]),
            "sensitivity_variant": target["sensitivity_variant"],
            "policy_id": target["policy_id"],
            "episode_status": reason,
            "episode_complete": False,
            "target_available": bool(target["target_available"]),
            "availability_reason": reason,
            "valid_matched_comparison": False,
            "historical_open_assumption_violation": False,
            "calendar_days": 0,
            "common_input_identity": identity,
        }
    )
    return rows, base


def summarize_simulation(
    target: Mapping[str, Any],
    ledger: Sequence[Mapping[str, Any]],
    orders: Sequence[Mapping[str, Any]],
    *,
    common_input_identity: str,
) -> dict[str, Any]:
    """Compute sufficient statistics first, then the approved episode ratios."""
    days = [row for row in ledger if int(row["horizon"]) > 0]
    valid = [row for row in days if bool(row["state_available"])]
    complete = len(valid) == HORIZON_DAYS
    assumption_violation = any(bool(row["historical_open_assumption_violation"]) for row in valid)
    if not complete:
        first_unavailable = next((row for row in days if not bool(row["state_available"])), {})
        reason = str(first_unavailable.get("state_unavailable_reason") or "incomplete_episode")
        _, summary = _unavailable_case(target, [dict(ledger[0])], reason, common_input_identity)
        summary["episode_status"] = "incomplete_episode"
        summary["target_available"] = bool(target["target_available"])
        summary["availability_reason"] = reason
        summary["historical_open_assumption_violation"] = assumption_violation
        summary["valid_matched_comparison"] = False
        return summary
    demand = sum(float(row["demand_value"]) for row in valid)
    fulfilled = sum(float(row["fulfilled_value"]) for row in valid)
    unmet = sum(float(row["unmet_value"]) for row in valid)
    positive_days = [row for row in valid if float(row["demand_value"]) > 0]
    stockout_days = sum(float(row["unmet_value"]) > 0 for row in positive_days)
    inventory_sum = sum(float(row["ending_inventory_value"]) for row in valid)
    holding = sum(float(row["holding_cost"]) for row in valid)
    penalty = sum(float(row["unmet_penalty"]) for row in valid)
    receipts_by_date: dict[date, float] = {}
    for row in valid:
        receipt_value = float(row["receipts_today_value"])
        if receipt_value > 0:
            receipts_by_date[row["Date"]] = receipts_by_date.get(row["Date"], 0.0) + receipt_value
    receipt_dates = sorted(receipts_by_date)
    positive_cycles = 0
    zero_unmet_cycles = 0
    zero_demand_cycles = 0
    for left, right in zip(receipt_dates, receipt_dates[1:], strict=False):
        cycle = [row for row in valid if left <= row["Date"] < right]
        cycle_demand = sum(float(row["demand_value"]) for row in cycle)
        if cycle_demand > 0:
            positive_cycles += 1
            if sum(float(row["unmet_value"]) for row in cycle) == 0:
                zero_unmet_cycles += 1
        else:
            zero_demand_cycles += 1
    first_day = target["forecast_origin"] + timedelta(days=1)
    last_day = target["forecast_origin"] + timedelta(days=HORIZON_DAYS)
    initial_left = int(not receipt_dates or receipt_dates[0] > first_day)
    terminal_right = int(not receipt_dates or receipt_dates[-1] < last_day)
    terminal = valid[-1]
    on_hand = float(terminal["ending_inventory_value"])
    on_order = float(terminal["pipeline_after_review_value"])
    c = float(target["ProcurementCostRatio"])
    late = [order for order in orders if order["due_date"] > last_day]
    ratio_fill = fulfilled / demand if demand > 0 else None
    stockout_rate = stockout_days / len(positive_days) if positive_days else None
    cycle_rate = zero_unmet_cycles / positive_cycles if positive_cycles else None
    result = {
        "case_id": target["case_id"],
        "scenario_id": target["scenario_id"],
        "Store": int(target["Store"]),
        "forecast_origin": target["forecast_origin"],
        "family": target["family"],
        "mode": target["mode"],
        "replicate": int(target["replicate"]),
        "sensitivity_variant": target["sensitivity_variant"],
        "policy_id": target["policy_id"],
        "episode_status": "complete",
        "episode_complete": True,
        "target_available": True,
        "availability_reason": None,
        "valid_matched_comparison": not assumption_violation,
        "historical_open_assumption_violation": assumption_violation,
        "calendar_days": HORIZON_DAYS,
        "demand_total": demand,
        "fulfilled_total": fulfilled,
        "unmet_total": unmet,
        "positive_demand_days": len(positive_days),
        "positive_demand_stockout_days": stockout_days,
        "ending_inventory_sum": inventory_sum,
        "holding_cost_total": holding,
        "unmet_penalty_total": penalty,
        "SimulatedHoldingPlusShortfallCost": holding + penalty,
        "ValueFillRate": ratio_fill,
        "PositiveDemandStockoutRate": stockout_rate,
        "AverageInventoryValue": inventory_sum / HORIZON_DAYS,
        "UnmetTurnoverValue": unmet,
        "SimulatedHoldingCost": holding,
        "SimulatedUnmetPenalty": penalty,
        "CompletedPositiveDemandReceiptCycleServiceRate": cycle_rate,
        "completed_cycles_total": max(0, len(receipt_dates) - 1),
        "completed_positive_demand_cycles": positive_cycles,
        "zero_unmet_positive_demand_cycles": zero_unmet_cycles,
        "zero_demand_completed_cycles": zero_demand_cycles,
        "initial_left_censored_intervals": initial_left,
        "terminal_right_censored_intervals": terminal_right,
        "terminal_on_hand_value": on_hand,
        "terminal_on_order_value": on_order,
        "TerminalStockCostValue": c * on_hand,
        "OutstandingProcurementCommitment": c * on_order,
        "late_order_count": len(late),
        "late_order_value": sum(float(order["value"]) for order in late),
        "common_input_identity": common_input_identity,
    }
    return result


def validate_simulation_outputs(
    policy_targets: pa.Table,
    simulation_ledger: pa.Table,
    policy_summary: pa.Table,
    comparison_summary: pd.DataFrame | pa.Table,
) -> dict[str, Any]:
    """Validate explicit schemas, keys, foreign keys, state balances and paired inputs."""
    expected = (
        (policy_targets, POLICY_TARGET_SCHEMA, ("case_id", "Store", "policy_id"), "targets"),
        (
            simulation_ledger,
            SIMULATION_LEDGER_SCHEMA,
            ("case_id", "Store", "policy_id", "Date"),
            "ledger",
        ),
        (policy_summary, POLICY_SUMMARY_SCHEMA, ("case_id", "Store", "policy_id"), "summary"),
    )
    for table, schema, keys, name in expected:
        if not table.schema.remove_metadata().equals(schema, check_metadata=False):
            raise SimulationIntegrityError(
                f"{name} schema differs from the approved ordered schema."
            )
        _assert_unique(table, keys, name)
    targets = policy_targets.to_pandas()
    summaries = policy_summary.to_pandas()
    if set(targets["policy_id"].unique()) - set(POLICY_IDS):
        raise SimulationIntegrityError("Output contains an unapproved policy ID.")
    for row in targets.to_dict(orient="records"):
        if bool(row["target_available"]) != _is_null(row["availability_reason"]):
            raise SimulationIntegrityError("Target availability flag and reason disagree.")
        if not _is_null(row["target_value"]) and not math.isfinite(float(row["target_value"])):
            raise SimulationIntegrityError("Target values must be finite or null.")
        if bool(row["synthetic"]) and row["calibration_transport_valid"]:
            raise SimulationIntegrityError(
                "Synthetic quantile transport cannot be called calibrated."
            )
        if row["policy_id"] == POLICY_IDS[0] and bool(row["target_available"]):
            expected_target = float(row["mean_open_sales_value"]) * int(
                row["open_days_in_protection_period"]
            )
            if not _close(float(row["target_value"]), expected_target):
                raise SimulationIntegrityError("Baseline target arithmetic failed validation.")
        if row["policy_id"] == POLICY_IDS[1] and bool(row["target_available"]):
            demand = float(row["forecast_protection_demand_value"])
            quantile = float(row["cumulative_signed_quantile"])
            upper = max(0.0, demand + quantile)
            safety = max(0.0, upper - demand)
            if (
                not _close(float(row["upper_turnover_value"]), upper)
                or not _close(float(row["safety_stock_value"]), safety)
                or not _close(float(row["target_value"]), max(demand, upper))
            ):
                raise SimulationIntegrityError("Forecast target arithmetic failed validation.")
    target_keys = set(
        map(tuple, targets[["case_id", "Store", "policy_id"]].itertuples(index=False, name=None))
    )
    summary_keys = set(
        map(tuple, summaries[["case_id", "Store", "policy_id"]].itertuples(index=False, name=None))
    )
    if target_keys != summary_keys:
        raise SimulationIntegrityError("Policy summary foreign keys do not match target tracks.")
    for row in summaries.to_dict(orient="records"):
        if not bool(row["episode_complete"]):
            if not _is_null(row["SimulatedHoldingPlusShortfallCost"]):
                raise SimulationIntegrityError(
                    "Incomplete episodes must not have full-window metrics."
                )
            continue
        if int(row["calendar_days"]) != HORIZON_DAYS:
            raise SimulationIntegrityError("Complete episode does not have exactly 14 days.")
        if not _close(
            float(row["SimulatedHoldingPlusShortfallCost"]),
            float(row["holding_cost_total"]) + float(row["unmet_penalty_total"]),
        ):
            raise SimulationIntegrityError("Primary simulated cost arithmetic failed.")
        expected_fill = (
            float(row["fulfilled_total"]) / float(row["demand_total"])
            if float(row["demand_total"]) > 0
            else None
        )
        if (expected_fill is None) != _is_null(row["ValueFillRate"]) or (
            expected_fill is not None and not _close(float(row["ValueFillRate"]), expected_fill)
        ):
            raise SimulationIntegrityError("Value fill-rate denominator/arithmetic failed.")
    ledger = simulation_ledger.to_pandas()
    if not set(
        map(
            tuple,
            ledger[["case_id", "Store", "policy_id"]]
            .drop_duplicates()
            .itertuples(index=False, name=None),
        )
    ).issubset(target_keys):
        raise SimulationIntegrityError("Ledger contains a track without a policy target.")
    for key, block in ledger.groupby(["case_id", "Store", "policy_id"], sort=False):
        ordered = block.sort_values("horizon", kind="mergesort")
        if ordered["horizon"].astype(int).tolist() != list(range(15)):
            raise SimulationIntegrityError(f"Ledger track {key} does not contain origin plus H14.")
        valid = ordered[ordered["state_available"]]
        for row in valid.itertuples(index=False):
            if int(row.horizon) == 0:
                continue
            if not _close(
                float(row.demand_value), float(row.fulfilled_value) + float(row.unmet_value)
            ):
                raise SimulationIntegrityError(f"Demand balance failed for {key}.")
            if not _close(
                float(row.available_stock_value),
                float(row.starting_inventory_value) + float(row.receipts_today_value),
            ):
                raise SimulationIntegrityError(f"Receipt balance failed for {key}.")
            if not _close(
                float(row.ending_inventory_value),
                float(row.available_stock_value) - float(row.fulfilled_value),
            ):
                raise SimulationIntegrityError(f"Inventory balance failed for {key}.")
            holding_rate = float(row.ProcurementCostRatio) * float(row.AnnualHoldingRate) / 365.0
            unmet_rate = (1.0 - float(row.ProcurementCostRatio)) + float(row.GoodwillPenaltyRate)
            if not _close(float(row.HoldingCostRate), holding_rate):
                raise SimulationIntegrityError(f"Holding-rate arithmetic failed for {key}.")
            if not _close(float(row.UnmetPenaltyRate), unmet_rate):
                raise SimulationIntegrityError(f"Unmet-rate arithmetic failed for {key}.")
            if not _close(
                float(row.holding_cost), holding_rate * float(row.ending_inventory_value)
            ):
                raise SimulationIntegrityError(f"Holding cost failed for {key}.")
            if not _close(float(row.unmet_penalty), unmet_rate * float(row.unmet_value)):
                raise SimulationIntegrityError(f"Unmet penalty failed for {key}.")
            if row.horizon == HORIZON_DAYS and row.order_value != 0:
                raise SimulationIntegrityError(f"Terminal boundary ordered for {key}.")
        if len(valid) == HORIZON_DAYS + 1:
            daily = valid[valid["horizon"] > 0]
            if not _close(
                float(daily["ending_inventory_value"].iloc[-1]),
                float(daily["starting_inventory_value"].iloc[0])
                + float(daily["receipts_today_value"].sum())
                - float(daily["fulfilled_value"].sum()),
            ):
                raise SimulationIntegrityError(f"Terminal inventory identity failed for {key}.")
            if not _close(
                float(daily["pipeline_after_review_value"].iloc[-1]),
                float(ordered["order_value"].fillna(0).sum() - daily["receipts_today_value"].sum()),
            ):
                raise SimulationIntegrityError(f"Terminal pipeline identity failed for {key}.")
    paired = summaries.pivot_table(
        index=["case_id", "Store"],
        columns="policy_id",
        values="common_input_identity",
        aggfunc="first",
    )
    if (
        set(paired.columns) != set(POLICY_IDS)
        or paired.isna().any().any()
        or (paired[POLICY_IDS[0]] != paired[POLICY_IDS[1]]).any()
    ):
        raise SimulationIntegrityError("Paired policies do not share the same exogenous identity.")
    comparison_frame = (
        comparison_summary.to_pandas()
        if isinstance(comparison_summary, pa.Table)
        else comparison_summary
    )
    if len(comparison_frame) and comparison_frame.duplicated(["case_id", "metric"]).any():
        raise SimulationIntegrityError("Comparison summary contains duplicate keys.")
    return {
        "target_tracks": int(policy_targets.num_rows),
        "ledger_rows": int(simulation_ledger.num_rows),
        "summary_tracks": int(policy_summary.num_rows),
        "duplicate_keys": 0,
        "invalid_foreign_keys": 0,
        "daily_and_terminal_balances": "passed",
        "paired_exogenous_identity": "passed",
        "protected_outcome_dates": 0,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SimulationIntegrityError(f"Cannot read required JSON artifact: {path}.") from error
    if not isinstance(value, dict):
        raise SimulationIntegrityError(f"Expected a JSON object: {path}.")
    return value


def _repo_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise SimulationIntegrityError(
            f"Frozen upstream path is missing or escapes repository: {relative}."
        )
    return path


def _preflight_phase9_parquet(path: Path, name: str) -> dict[str, Any]:
    """Read only Parquet footer metadata and reject dates after the dev cutoff."""
    try:
        parquet = pq.ParquetFile(path)
    except (OSError, pa.ArrowException) as error:
        raise SimulationIntegrityError(
            f"Cannot inspect Phase 9 Parquet metadata: {name}."
        ) from error
    metadata = parquet.metadata
    if metadata is None or metadata.num_rows <= 0:
        raise SimulationIntegrityError(f"Phase 9 Parquet lacks auditable row metadata: {name}.")
    schema = parquet.schema_arrow
    date_fields = [field.name for field in schema if pa.types.is_date(field.type)]
    bounds: dict[str, dict[str, str]] = {}
    for field_name in date_fields:
        index = schema.names.index(field_name)
        low: date | None = None
        high: date | None = None
        for group_index in range(metadata.num_row_groups):
            stats = metadata.row_group(group_index).column(index).statistics
            if stats is None or stats.min is None or stats.max is None:
                raise SimulationIntegrityError(f"Phase 9 date statistics are insufficient: {name}.")
            group_low = pd.Timestamp(stats.min).date()
            group_high = pd.Timestamp(stats.max).date()
            low = group_low if low is None else min(low, group_low)
            high = group_high if high is None else max(high, group_high)
        if low is None or high is None:
            raise SimulationIntegrityError(f"Phase 9 date bounds are absent: {name}.")
        if field_name == "Date" and high > scenarios.DEVELOPMENT_CUTOFF:
            raise SimulationIntegrityError(f"Phase 9 daily metadata crosses July 3: {name}.")
        if field_name == "forecast_origin" and (
            low not in scenarios.ALLOWED_ORIGINS or high not in scenarios.ALLOWED_ORIGINS
        ):
            raise SimulationIntegrityError(
                f"Phase 9 origin metadata contains an unsupported origin: {name}."
            )
        bounds[field_name] = {"minimum": low.isoformat(), "maximum": high.isoformat()}
    return {
        "rows": int(metadata.num_rows),
        "columns": schema.names,
        "date_bounds": bounds,
        "schema": scenarios._schema_descriptor(schema),
    }


def verify_simulation_inputs(
    root: str | Path | None = None, *, origin: date | str | None = None
) -> dict[str, Any]:
    """Verify the pinned development inputs; reject a bad origin before any artifact read."""
    if origin is not None:
        _validate_origin(origin)
    repository = Path(root or Path.cwd()).resolve()
    upstream = scenarios.verify_frozen_bindings(repository)
    snapshot = upstream["identity_snapshot"]
    if snapshot.get("phase7_selection_manifest_sha256") != PHASE7_MANIFEST_SHA256:
        raise SimulationIntegrityError("Phase 7 selection manifest differs from ADR-023 pin.")
    if snapshot.get("phase8_manifest_sha256") != PHASE8_MANIFEST_SHA256:
        raise SimulationIntegrityError("Phase 8 manifest differs from ADR-023 pin.")
    p9_dir = repository / "data/processed/synthetic_inventory" / PHASE9_RUN_ID
    manifest_path = p9_dir / "manifest.json"
    config_path = p9_dir / "scenario_config.json"
    binding_path = p9_dir / "upstream_bindings.json"
    manifest = _read_json(manifest_path)
    if manifest.get("run_id") != PHASE9_RUN_ID or manifest.get("status") not in {
        "complete",
        "complete_with_unavailable_inputs",
    }:
        raise SimulationIntegrityError("Phase 9 run identity/status differs from the approved pin.")
    manifest_hash = _sha256_file(manifest_path)
    if manifest_hash != PHASE9_MANIFEST_SHA256:
        raise SimulationIntegrityError("Phase 9 manifest SHA-256 differs from ADR-023 pin.")
    outputs = manifest.get("outputs")
    expected_outputs = {
        "scenario_config.json",
        "upstream_bindings.json",
        "validation_summary.json",
        *scenarios.TABLE_SCHEMAS.keys(),
    }
    if not isinstance(outputs, dict) or set(outputs) != expected_outputs:
        raise SimulationIntegrityError("Phase 9 manifest output inventory is unexpected.")
    phase9_footer: dict[str, Any] = {}
    for filename in scenarios.TABLE_SCHEMAS:
        file_path = p9_dir / filename
        phase9_footer[filename] = _preflight_phase9_parquet(file_path, filename)
    phase9_files: dict[str, dict[str, Any]] = {}
    for filename, metadata in outputs.items():
        file_path = p9_dir / filename
        expected_path = metadata.get("path", filename)
        if expected_path != filename:
            raise SimulationIntegrityError(f"Phase 9 manifest path changed for {filename}.")
        byte_hash = _sha256_file(file_path)
        if byte_hash != metadata.get("sha256") or file_path.stat().st_size != metadata.get(
            "byte_length"
        ):
            raise SimulationIntegrityError(f"Phase 9 artifact identity mismatch: {filename}.")
        phase9_files[filename] = {
            "path": str(file_path.relative_to(repository).as_posix()),
            "sha256": byte_hash,
            "byte_length": file_path.stat().st_size,
            "rows": metadata.get("rows"),
        }
    config = _read_json(config_path)
    if config.get("run_id") != PHASE9_RUN_ID or config.get("config_canonical_sha256") != outputs[
        "scenario_config.json"
    ].get("canonical_json_sha256"):
        raise SimulationIntegrityError("Phase 9 config identity differs from its manifest.")
    if scenarios._semantic_json_sha256(config) != config.get("config_canonical_sha256"):
        raise SimulationIntegrityError("Phase 9 canonical config hash does not validate.")
    if config.get("forecast_origins") != [item.isoformat() for item in scenarios.ALLOWED_ORIGINS]:
        raise SimulationIntegrityError("Phase 9 origins differ from the approved Phase 10 grid.")
    if len(config.get("stores", [])) != 1115 or config.get("replicates") != [0, 1, 2, 3, 4]:
        raise SimulationIntegrityError("Phase 9 configured Store/replicate universe is unexpected.")
    bindings = _read_json(binding_path)
    phase7 = bindings.get("phase7", {})
    phase8 = bindings.get("phase8", {})
    if (
        phase7.get("selection_manifest_sha256") != PHASE7_MANIFEST_SHA256
        or phase7.get("selection_run_id") != PHASE7_RUN_ID
        or phase8.get("manifest_sha256") != PHASE8_MANIFEST_SHA256
        or bindings.get("canonical_sha256")
        != outputs["upstream_bindings.json"].get("canonical_json_sha256")
    ):
        raise SimulationIntegrityError("Phase 9 upstream binding does not match Phase 7/8 pins.")
    validation = _read_json(p9_dir / "validation_summary.json")
    if validation.get("checks", {}).get("protected_holdout_values_read_or_hashed") is not False:
        raise SimulationIntegrityError("Phase 9 validation does not certify the holdout boundary.")
    return {
        "repository": repository,
        "phase7_8_bindings": upstream,
        "phase9_dir": p9_dir,
        "phase9_manifest": manifest,
        "phase9_manifest_sha256": manifest_hash,
        "phase9_config": config,
        "phase9_upstream_bindings": bindings,
        "phase9_footer_metadata": phase9_footer,
        "phase9_files": phase9_files,
        "identity_snapshot": snapshot,
        "protected_holdout_values_read_or_hashed": False,
    }


def _read_phase7_safe_points(inputs: Mapping[str, Any]) -> pd.DataFrame:
    root = Path(inputs["repository"])
    relative = "data/processed/model_selection/selected_development_forecasts.parquet"
    path = _repo_file(root, relative)
    parquet = pq.ParquetFile(path)
    schema = parquet.schema_arrow
    if not set(PHASE7_SAFE_COLUMNS).issubset(schema.names):
        raise SimulationIntegrityError("Phase 7 selected forecast lacks safe target columns.")
    # This projection deliberately excludes actual_sales, residuals and customers.
    table = pq.read_table(
        path,
        columns=list(PHASE7_SAFE_COLUMNS),
        filters=[("forecast_origin", "in", [datetime(2015, 6, 5), datetime(2015, 6, 19)])],
    )
    frame = table.to_pandas()
    frame["forecast_origin"] = pd.to_datetime(frame["forecast_origin"], errors="raise").dt.date
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise").dt.date
    frame["Store"] = frame["Store"].astype("int64")
    frame["horizon"] = frame["horizon"].astype("int64")
    frame = frame.loc[
        frame["forecast_origin"].isin(scenarios.ALLOWED_ORIGINS)
        & frame["Date"].map(lambda value: value <= scenarios.DEVELOPMENT_CUTOFF)
    ].copy()
    if frame.duplicated(["Store", "forecast_origin", "horizon"]).any():
        raise SimulationIntegrityError("Phase 7 safe projection has duplicate point keys.")
    forbidden = FORBIDDEN_TARGET_COLUMNS | {"actual_sales", "raw_residual", "operational_residual"}
    if forbidden.intersection(frame.columns):
        raise SimulationIntegrityError("Phase 7 safe point projection included outcomes.")
    return frame


def _read_phase8_quantiles(inputs: Mapping[str, Any]) -> pd.DataFrame:
    root = Path(inputs["repository"])
    relative = f"data/processed/uncertainty/{PHASE8_RUN_ID}/cumulative_error_quantiles.csv"
    path = _repo_file(root, relative)
    expected_hash = inputs["phase7_8_bindings"]["identity_snapshot"]["phase8_output_hashes"].get(
        "cumulative_error_quantiles.csv"
    )
    if expected_hash != PHASE8_CUMULATIVE_SHA256 or _sha256_file(path) != expected_hash:
        raise SimulationIntegrityError(
            "Phase 8 cumulative quantile file hash differs from manifest."
        )
    frame = pd.read_csv(path)
    required = {
        "fit_id",
        "k",
        "p",
        "signed_quantile",
        "available",
        "unavailable_reason",
        "prefix_definition",
        "schedule_assumption",
        "selected_candidate_id",
    }
    if not required.issubset(frame.columns):
        raise SimulationIntegrityError("Phase 8 cumulative quantile schema is incomplete.")
    if not frame["prefix_definition"].eq("exact_h1_through_k_complete_origin_anchored_path").all():
        raise SimulationIntegrityError("Phase 8 cumulative prefix definition changed.")
    if not frame["selected_candidate_id"].eq("global_lightgbm_gbdt_regression_l1").all():
        raise SimulationIntegrityError("Phase 8 quantiles use an unexpected model.")
    if not frame["schedule_assumption"].eq("saved_source_open_assumed_known_at_origin").all():
        raise SimulationIntegrityError("Phase 8 quantile schedule assumption changed.")
    frame["p_key"] = frame["p"].round(2)
    return frame


def _check_phase9_tables_after_target_freeze(inputs: Mapping[str, Any]) -> dict[str, pa.Table]:
    """Validate Phase 9 contents after target freeze, when demand values may be loaded."""
    directory = Path(inputs["phase9_dir"])
    tables = {
        filename: pq.read_table(directory / filename, columns=schema.names)
        for filename, schema in scenarios.TABLE_SCHEMAS.items()
    }
    for filename, table in tables.items():
        expected_schema = scenarios.TABLE_SCHEMAS[filename]
        if not table.schema.remove_metadata().equals(expected_schema, check_metadata=False):
            raise SimulationIntegrityError(f"Phase 9 table schema changed: {filename}.")
        expected_hash = inputs["phase9_manifest"]["outputs"][filename].get("logical_sha256")
        actual_hash = scenarios.logical_table_sha256(table, scenarios.TABLE_KEYS[filename])
        if expected_hash != actual_hash:
            raise SimulationIntegrityError(f"Phase 9 logical content identity changed: {filename}.")
    try:
        scenarios.validate_scenario_tables(tables, inputs["phase9_config"])
    except scenarios.ScenarioIntegrityError as error:
        raise SimulationIntegrityError(
            "Phase 9 scenario bundle failed its accepted validator."
        ) from error
    return tables


def _safe_schedule_projection(
    inputs: Mapping[str, Any],
) -> tuple[dict[str, dict[int, int | None]], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load Phase 9 openings and Phase 7 saved points without realized outcomes."""
    p9_daily = Path(inputs["phase9_dir"]) / "scenario_daily.parquet"
    schedule_table = pq.read_table(
        p9_daily,
        columns=["scenario_id", "Store", "horizon", "ScenarioOpen"],
        filters=[("horizon", "<=", max(ALLOWED_LEAD_TIMES) + 1)],
    )
    schedule_frame = schedule_table.to_pandas()
    schedule_by_case: dict[str, dict[int, int | None]] = {}
    for (scenario_id, store), block in schedule_frame.groupby(["scenario_id", "Store"], sort=False):
        schedule_by_case[f"{scenario_id}\0{int(store)}"] = {
            int(row.horizon): None if pd.isna(row.ScenarioOpen) else int(row.ScenarioOpen)
            for row in block.itertuples(index=False)
        }
    points = _read_phase7_safe_points(inputs)
    quantiles = _read_phase8_quantiles(inputs)
    # The selected Phase 7 table is a frozen issuance artifact. This projection is
    # deliberately the only source for the conditional historical Open assumption.
    historical_schedule = points[["Store", "forecast_origin", "horizon", "source_open"]].copy()
    return schedule_by_case, points, quantiles, historical_schedule


def _quantile_row(
    quantiles: pd.DataFrame, fit_id: str, prefix: int, probability: float
) -> dict[str, Any]:
    rows = quantiles.loc[
        quantiles["fit_id"].eq(fit_id)
        & quantiles["k"].astype(int).eq(prefix)
        & quantiles["p_key"].eq(round(probability, 2))
    ]
    if len(rows) != 1:
        raise SimulationIntegrityError("Phase 8 cumulative quantile key is missing or duplicated.")
    row = rows.iloc[0]
    available = bool(row["available"])
    q = None if pd.isna(row["signed_quantile"]) else float(row["signed_quantile"])
    if available and (q is None or not math.isfinite(q)):
        raise SimulationIntegrityError("Available Phase 8 quantile is not finite.")
    return {
        "value": q,
        "available": available,
        "reason": None if pd.isna(row["unavailable_reason"]) else str(row["unavailable_reason"]),
    }


def _case_variants(
    scenario: Mapping[str, Any], parameter: Mapping[str, Any], anchor: Mapping[str, Any]
) -> list[dict[str, Any]]:
    variants = [{"id": REFERENCE_VARIANT}]
    if scenario["family"] != "synthetic_base" or scenario["mode"] != "synthetic_stress":
        return variants
    additions = (
        ("lead_2", {"SupplierLeadTime": 2}),
        ("lead_7", {"SupplierLeadTime": 7}),
        ("buffer_090", {"buffer_probability": 0.90}),
        ("buffer_098", {"buffer_probability": 0.98}),
        ("holding_010", {"AnnualHoldingRate": 0.10}),
        ("holding_030", {"AnnualHoldingRate": 0.30}),
        ("goodwill_010", {"GoodwillPenaltyRate": 0.10}),
        ("goodwill_075", {"GoodwillPenaltyRate": 0.75}),
        ("coverage_1", {"InventoryCoverageDays": 1}),
    )
    variants.extend({"id": name, **change} for name, change in additions)
    return sorted(variants, key=lambda item: item["id"])


def _build_case_target_inputs(
    scenario: Mapping[str, Any],
    variant: Mapping[str, Any],
    parameter: Mapping[str, Any],
    anchor: Mapping[str, Any],
    *,
    schedule_by_case: Mapping[str, Mapping[int, int | None]],
    point_by_key: Mapping[tuple[int, date, int], Mapping[str, Any]],
    quantiles: pd.DataFrame,
    upstream_identity: str,
) -> list[dict[str, Any]]:
    origin = scenario["forecast_origin"]
    store = int(parameter["Store"])
    lead = int(variant.get("SupplierLeadTime", parameter["SupplierLeadTime"]))
    protection = lead + REVIEW_PERIOD
    probability = float(variant.get("buffer_probability", REFERENCE_P))
    fit_id = scenarios.FIT_BY_ORIGIN[origin]
    qrow = _quantile_row(quantiles, fit_id, protection, probability)
    case_id = f"{scenario['scenario_id']}--{variant['id']}"
    is_synthetic = scenario["mode"] == "synthetic_stress"
    safe_schedule = schedule_by_case.get(f"{scenario['scenario_id']}\0{store}", {})
    anchor_available = bool(anchor["anchor_available"])
    mean_value = anchor["mean_open_sales_value"]
    if variant.get("InventoryCoverageDays") == 1:
        initial_stock = None if not anchor_available else float(mean_value)
    else:
        initial_stock = parameter["InitialStockOnHandValue"]
    annual = float(variant.get("AnnualHoldingRate", parameter["AnnualHoldingRate"]))
    goodwill = float(variant.get("GoodwillPenaltyRate", parameter["GoodwillPenaltyRate"]))
    rows: list[dict[str, Any]] = []
    for horizon in range(1, protection + 1):
        point = point_by_key.get((store, origin, horizon))
        if is_synthetic:
            schedule_open = safe_schedule.get(horizon)
        else:
            raw_open = None if point is None else point.get("source_open")
            schedule_open = None if raw_open is None or pd.isna(raw_open) else int(raw_open)
        rows.append(
            {
                "case_id": case_id,
                "scenario_id": str(scenario["scenario_id"]),
                "Store": store,
                "forecast_origin": origin,
                "family": str(scenario["family"]),
                "mode": str(scenario["mode"]),
                "replicate": int(scenario["replicate"]),
                "sensitivity_variant": str(variant["id"]),
                "SupplierLeadTime": lead,
                "ReviewPeriod": REVIEW_PERIOD,
                "ProtectionPeriod": protection,
                "buffer_probability": probability,
                "mean_open_sales_value": mean_value,
                "anchor_available": anchor_available,
                "initial_stock_value": initial_stock,
                "ProcurementCostRatio": float(parameter["ProcurementCostRatio"]),
                "AnnualHoldingRate": annual,
                "GoodwillPenaltyRate": goodwill,
                "horizon": horizon,
                "schedule_open": schedule_open,
                "raw_point_forecast": None if point is None else point["raw_forecast"],
                "forecast_available": False if point is None else bool(point["forecast_available"]),
                "cumulative_signed_quantile": qrow["value"],
                "quantile_available": qrow["available"],
                "quantile_unavailable_reason": qrow["reason"],
                "fit_id": fit_id,
                "model_id": "global_lightgbm_gbdt_regression_l1",
                "upstream_identity": upstream_identity,
                "synthetic": is_synthetic,
                "schedule_assumption": (
                    "phase9_scenario_open_known_at_origin"
                    if is_synthetic
                    else "saved_source_open_assumed_known_at_origin"
                ),
            }
        )
    return rows


def _build_targets_to_file(inputs: Mapping[str, Any], stage: Path) -> tuple[int, dict[str, Any]]:
    schedule_by_case, points, quantiles, _ = _safe_schedule_projection(inputs)
    point_by_key: dict[tuple[int, date, int], dict[str, Any]] = {}
    for row in points.itertuples(index=False):
        raw = None if pd.isna(row.raw_forecast) else float(row.raw_forecast)
        source_open = None if pd.isna(row.source_open) else float(row.source_open)
        point_by_key[(int(row.Store), row.forecast_origin, int(row.horizon))] = {
            "raw_forecast": raw,
            "forecast_available": bool(row.forecast_available),
            "source_open": source_open,
        }
    phase9_dir = Path(inputs["phase9_dir"])
    catalog = pq.read_table(phase9_dir / "scenario_catalog.parquet").to_pylist()
    parameters = pq.read_table(phase9_dir / "store_parameters.parquet").to_pylist()
    anchors = pq.read_table(phase9_dir / "origin_anchors.parquet").to_pylist()
    parameters_by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in parameters:
        parameters_by_scenario.setdefault(row["scenario_id"], []).append(row)
    anchor_by_key = {(int(row["Store"]), row["forecast_origin"]): row for row in anchors}
    upstream_identity = hashlib.sha256(
        _canonical_json(
            {
                "phase7": PHASE7_MANIFEST_SHA256,
                "phase8": PHASE8_MANIFEST_SHA256,
                "phase9": PHASE9_MANIFEST_SHA256,
                "model": "global_lightgbm_gbdt_regression_l1",
            }
        )
    ).hexdigest()
    destination = stage / "policy_targets.parquet"
    writer = pq.ParquetWriter(destination, POLICY_TARGET_SCHEMA, compression="zstd")
    requested_pairs = 0
    reference_pairs = 0
    case_counts: Counter[str] = Counter()
    try:
        for scenario in sorted(catalog, key=lambda row: row["scenario_id"]):
            variants = _case_variants(scenario, {}, {})
            for variant in variants:
                buffered: list[dict[str, Any]] = []
                for parameter in parameters_by_scenario[scenario["scenario_id"]]:
                    store = int(parameter["Store"])
                    anchor = anchor_by_key[(store, scenario["forecast_origin"])]
                    buffered.extend(
                        _build_case_target_inputs(
                            scenario,
                            variant,
                            parameter,
                            anchor,
                            schedule_by_case=schedule_by_case,
                            point_by_key=point_by_key,
                            quantiles=quantiles,
                            upstream_identity=upstream_identity,
                        )
                    )
                    requested_pairs += 1
                    case_counts[f"{scenario['scenario_id']}--{variant['id']}"] += 1
                    if variant["id"] == REFERENCE_VARIANT:
                        reference_pairs += 1
                batch = build_policy_targets(pd.DataFrame.from_records(buffered))
                writer.write_table(batch, row_group_size=65_536)
    finally:
        writer.close()
    actual_tracks = pq.ParquetFile(destination).metadata.num_rows
    if actual_tracks != requested_pairs * len(POLICY_IDS):
        raise SimulationIntegrityError(
            "Target grid row count differs from requested case/Store grid."
        )
    expected_pairs = 191_780
    if (
        len(parameters) != 91_430
        or reference_pairs != 91_430
        or requested_pairs != expected_pairs
        or actual_tracks != 383_560
        or reference_pairs * len(POLICY_IDS) != 182_860
    ):
        raise SimulationIntegrityError(
            f"Approved requested grid mismatch: expected 191780 pairs/383560 tracks, "
            f"got {requested_pairs}/{actual_tracks}."
        )
    return actual_tracks, {
        "scenario_store_pairs": requested_pairs,
        "reference_scenario_store_pairs": reference_pairs,
        "reference_policy_tracks": reference_pairs * len(POLICY_IDS),
        "policy_tracks": actual_tracks,
        "case_count": len(case_counts),
        "case_store_counts": dict(sorted(case_counts.items())),
        "upstream_identity": upstream_identity,
    }


def _load_historical_outcomes(
    inputs: Mapping[str, Any],
) -> dict[tuple[int, date, int], dict[str, Any]]:
    """Load development Sales only after policy_targets.parquet has been frozen."""
    root = Path(inputs["repository"])
    relative = "data/processed/model_selection/development_residual_paths.parquet"
    path = _repo_file(root, relative)
    metadata = scenarios._verify_development_parquet_metadata(path, expected_rows=46_830)
    if date.fromisoformat(metadata["maximum_date"]) > scenarios.DEVELOPMENT_CUTOFF:
        raise SimulationIntegrityError("Historical outcome Parquet crosses the development cutoff.")
    dataset = ds.dataset(path, format="parquet")
    required = [
        "Store",
        "forecast_origin",
        "Date",
        "target_key_observed",
        "actual_sales",
        "source_open",
    ]
    if not set(required).issubset(dataset.schema.names):
        raise SimulationIntegrityError(
            "Phase 7 residual paths lack the historical replay projection."
        )
    origin_values = [datetime(2015, 6, 5), datetime(2015, 6, 19)]
    origin_field = dataset.schema.field("forecast_origin")
    date_field = dataset.schema.field("Date")
    predicate = ds.field("forecast_origin").isin(
        [pa.scalar(value, type=origin_field.type) for value in origin_values]
    ) & (ds.field("Date") <= pa.scalar(datetime(2015, 7, 3), type=date_field.type))
    table = dataset.to_table(columns=required, filter=predicate, use_threads=False)
    frame = table.to_pandas()
    frame["forecast_origin"] = pd.to_datetime(frame["forecast_origin"], errors="raise").dt.date
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise").dt.date
    if not frame["Date"].map(lambda value: value <= scenarios.DEVELOPMENT_CUTOFF).all():
        raise SimulationIntegrityError("Projected historical outcomes cross July 3, 2015.")
    result: dict[tuple[int, date, int], dict[str, Any]] = {}
    for row in frame.itertuples(index=False):
        key = (int(row.Store), row.forecast_origin, int((row.Date - row.forecast_origin).days))
        if key[2] not in range(1, HORIZON_DAYS + 1):
            continue
        if key in result:
            raise SimulationIntegrityError("Historical outcome projection has duplicate keys.")
        sales = None if pd.isna(row.actual_sales) else float(row.actual_sales)
        source_open = None if pd.isna(row.source_open) else int(row.source_open)
        observed = bool(row.target_key_observed)
        result[key] = {
            "sales": sales if observed else None,
            "source_open": source_open,
            "target_key_observed": observed,
        }
    return result


def _read_synthetic_path(
    inputs: Mapping[str, Any], scenario_id: str
) -> dict[int, list[dict[str, Any]]]:
    """Read one Phase 9 realized path after targets have been written and frozen."""
    path = Path(inputs["phase9_dir"]) / "scenario_daily.parquet"
    required = [
        "scenario_id",
        "Store",
        "Date",
        "horizon",
        "ScenarioOpen",
        "SyntheticDemandValue",
        "synthetic_demand_available",
        "unavailable_reason",
    ]
    table = pq.read_table(path, columns=required, filters=[("scenario_id", "=", scenario_id)])
    frame = table.to_pandas()
    if frame.empty or not frame["scenario_id"].eq(scenario_id).all():
        raise SimulationIntegrityError(f"Synthetic demand path is missing for {scenario_id}.")
    result: dict[int, list[dict[str, Any]]] = {}
    for store, block in frame.groupby("Store", sort=True):
        block = block.sort_values("horizon", kind="mergesort")
        if block["horizon"].astype(int).tolist() != list(range(1, HORIZON_DAYS + 1)):
            raise SimulationIntegrityError(
                f"Synthetic path has incomplete H14 grid: {scenario_id}."
            )
        days: list[dict[str, Any]] = []
        for row in block.itertuples(index=False):
            opening = None if pd.isna(row.ScenarioOpen) else int(row.ScenarioOpen)
            value = None if pd.isna(row.SyntheticDemandValue) else float(row.SyntheticDemandValue)
            available = bool(row.synthetic_demand_available) and value is not None
            if available and opening == 0:
                value = 0.0
            days.append(
                {
                    "horizon": int(row.horizon),
                    "ScenarioOpen": opening,
                    "source_open": None,
                    "demand_value": value,
                    "demand_available": available,
                    "unavailable_reason": row.unavailable_reason,
                    "historical_open_assumption_violation": False,
                }
            )
        result[int(store)] = days
    if len(result) != 1115:
        raise SimulationIntegrityError(f"Synthetic scenario Store coverage changed: {scenario_id}.")
    return result


def _historical_path(
    store: int, origin: date, outcomes: Mapping[tuple[int, date, int], Mapping[str, Any]]
) -> list[dict[str, Any]]:
    days = []
    for horizon in range(1, HORIZON_DAYS + 1):
        item = outcomes.get((store, origin, horizon))
        if item is None or not bool(item["target_key_observed"]):
            days.append(
                {
                    "horizon": horizon,
                    "ScenarioOpen": None,
                    "source_open": None if item is None else item["source_open"],
                    "demand_value": None,
                    "demand_available": False,
                    "unavailable_reason": "target_key_not_observed",
                    "historical_open_assumption_violation": False,
                }
            )
            continue
        sales = item["sales"]
        opening = item["source_open"]
        available = sales is not None
        violation = bool(available and opening == 0 and sales > 0)
        days.append(
            {
                "horizon": horizon,
                "ScenarioOpen": None,
                "source_open": opening,
                "demand_value": sales,
                "demand_available": available,
                "unavailable_reason": None if available else "sales_label_unavailable",
                "historical_open_assumption_violation": violation,
            }
        )
    return days


def _stable_value(value: Any) -> Any:
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, (float, np.floating)):
        return float(value).hex()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, Mapping):
        return {str(key): _stable_value(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    return value


def _common_input_identity(
    target: Mapping[str, Any], demand_path: Sequence[Mapping[str, Any]]
) -> str:
    payload = {
        "case_id": target["case_id"],
        "scenario_id": target["scenario_id"],
        "Store": int(target["Store"]),
        "origin": target["forecast_origin"],
        "family": target["family"],
        "mode": target["mode"],
        "replicate": int(target["replicate"]),
        "variant": target["sensitivity_variant"],
        "initial_stock": target["initial_stock_value"],
        "lead": int(target["SupplierLeadTime"]),
        "review": int(target["ReviewPeriod"]),
        "protection": int(target["ProtectionPeriod"]),
        "c": target["ProcurementCostRatio"],
        "a": target["AnnualHoldingRate"],
        "g": target["GoodwillPenaltyRate"],
        "demand_path": [
            {
                "horizon": item["horizon"],
                "schedule": item.get("ScenarioOpen"),
                "source_open": item.get("source_open"),
                "demand": item.get("demand_value"),
                "available": item.get("demand_available"),
            }
            for item in demand_path
        ],
        "upstream_identity": target["upstream_identity"],
    }
    return hashlib.sha256(_canonical_json(_stable_value(payload))).hexdigest()


def _physical_trajectory(rows: Sequence[Mapping[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    fields = (
        "horizon",
        "ScenarioOpen",
        "source_open",
        "starting_inventory_value",
        "receipts_today_value",
        "available_stock_value",
        "demand_value",
        "fulfilled_value",
        "unmet_value",
        "ending_inventory_value",
        "pipeline_before_receipt_value",
        "pipeline_after_receipt_value",
        "pipeline_after_review_value",
        "inventory_position_value",
        "order_value",
        "order_due_date",
        "received_order_ids",
        "state_available",
        "state_unavailable_reason",
    )
    return tuple(tuple(_stable_value(row.get(field)) for field in fields) for row in rows)


def _comparison_rows(case_id: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        return []
    requested = int(frame["Store"].nunique())
    baseline = frame.loc[frame["policy_id"].eq(POLICY_IDS[0])].set_index("Store")
    forecast = frame.loc[frame["policy_id"].eq(POLICY_IDS[1])].set_index("Store")
    common = baseline.index.intersection(forecast.index)
    b = baseline.loc[common]
    f = forecast.loc[common]
    matched_mask = (
        b["episode_complete"].astype(bool)
        & f["episode_complete"].astype(bool)
        & b["valid_matched_comparison"].astype(bool)
        & f["valid_matched_comparison"].astype(bool)
    )
    matched_b = b.loc[matched_mask]
    matched_f = f.loc[matched_mask]
    matched_count = int(len(matched_b))
    baseline_standalone = int(b["episode_complete"].sum())
    forecast_standalone = int(f["episode_complete"].sum())

    def total(frame_part: pd.DataFrame, column: str) -> float:
        values = pd.to_numeric(frame_part[column], errors="coerce").dropna()
        return float(values.sum())

    specs = [
        (
            "SimulatedHoldingPlusShortfallCost",
            "SimulatedHoldingPlusShortfallCost",
            "additive",
            "lower simulated holding-plus-shortfall cost under these assumptions is favorable",
        ),
        (
            "ValueFillRate",
            "fulfilled_total",
            "fill",
            "pooled fulfilled turnover divided by pooled demand",
        ),
        (
            "PositiveDemandStockoutRate",
            "positive_demand_stockout_days",
            "stockout",
            "pooled positive-demand stockout days divided by pooled positive-demand days",
        ),
        (
            "AverageInventoryValue",
            "ending_inventory_sum",
            "inventory",
            "pooled ending inventory divided by valid calendar days",
        ),
        ("UnmetTurnoverValue", "unmet_total", "additive", "pooled unmet turnover value"),
        (
            "CompletedPositiveDemandReceiptCycleServiceRate",
            "zero_unmet_positive_demand_cycles",
            "cycle",
            "project-specific simulated positive-demand receipt-cycle proxy",
        ),
        (
            "terminal_on_hand_value",
            "terminal_on_hand_value",
            "additive",
            "terminal stock exposure; not savings",
        ),
        (
            "terminal_on_order_value",
            "terminal_on_order_value",
            "additive",
            "terminal pipeline exposure",
        ),
        (
            "TerminalStockCostValue",
            "TerminalStockCostValue",
            "additive",
            "terminal stock cost exposure",
        ),
        (
            "OutstandingProcurementCommitment",
            "OutstandingProcurementCommitment",
            "additive",
            "terminal procurement commitment; excluded from the primary objective",
        ),
    ]
    output: list[dict[str, Any]] = []
    for metric, column, kind, interpretation in specs:
        row: dict[str, Any] = {
            "case_id": case_id,
            "metric": metric,
            "requested_store_count": requested,
            "baseline_standalone_store_count": baseline_standalone,
            "forecast_standalone_store_count": forecast_standalone,
            "matched_store_count": matched_count,
            "baseline_numerator": None,
            "baseline_denominator": None,
            "forecast_numerator": None,
            "forecast_denominator": None,
            "baseline_value": None,
            "forecast_value": None,
            "forecast_minus_baseline": None,
            "forecast_minus_baseline_relative": None,
            "relative_difference_null_reason": (
                "not_applicable"
                if metric != "SimulatedHoldingPlusShortfallCost"
                else "no_complete_matched_stores"
            ),
            "null_reason": None,
            "interpretation": interpretation,
        }
        if matched_count == 0:
            row["null_reason"] = "no_complete_matched_stores"
            output.append(row)
            continue
        b_num = total(matched_b, column)
        f_num = total(matched_f, column)
        if kind == "fill":
            b_den, f_den = total(matched_b, "demand_total"), total(matched_f, "demand_total")
        elif kind == "stockout":
            b_den = total(matched_b, "positive_demand_days")
            f_den = total(matched_f, "positive_demand_days")
        elif kind == "inventory":
            b_den = total(matched_b, "calendar_days")
            f_den = total(matched_f, "calendar_days")
        elif kind == "cycle":
            b_den = total(matched_b, "completed_positive_demand_cycles")
            f_den = total(matched_f, "completed_positive_demand_cycles")
        else:
            b_den = f_den = None
        row["baseline_numerator"] = b_num
        row["forecast_numerator"] = f_num
        row["baseline_denominator"] = b_den
        row["forecast_denominator"] = f_den
        if kind in {"fill", "stockout", "inventory", "cycle"}:
            if b_den == 0 or f_den == 0:
                row["null_reason"] = "zero_denominator"
            else:
                row["baseline_value"] = b_num / b_den
                row["forecast_value"] = f_num / f_den
                row["forecast_minus_baseline"] = row["forecast_value"] - row["baseline_value"]
        else:
            row["baseline_value"] = b_num
            row["forecast_value"] = f_num
            row["forecast_minus_baseline"] = f_num - b_num
        if metric == "SimulatedHoldingPlusShortfallCost":
            if row["baseline_value"] == 0:
                row["relative_difference_null_reason"] = "zero_baseline_cost"
            else:
                row["forecast_minus_baseline_relative"] = (
                    row["forecast_minus_baseline"] / row["baseline_value"]
                )
                row["relative_difference_null_reason"] = None
        output.append(row)
    return output


def _assert_git_ignored(root: Path, path: str) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SimulationIntegrityError(f"Refusing to publish non-ignored Phase 10 path: {path}.")


def _source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/rossmann_forecasting/inventory/simulation.py",
        "src/rossmann_forecasting/inventory/scenarios.py",
        "src/rossmann_forecasting/forecasting/model_selection.py",
        "src/rossmann_forecasting/forecasting/uncertainty.py",
        "scripts/run_inventory_simulation.py",
        "pyproject.toml",
        "uv.lock",
    ):
        path = root / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _package_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for package in ("numpy", "pandas", "pyarrow"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = None
    return result


def _parquet_metadata(path: Path, schema: pa.Schema, keys: Sequence[str]) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    if not parquet.schema_arrow.remove_metadata().equals(schema, check_metadata=False):
        raise SimulationIntegrityError(f"Staged Parquet schema changed: {path.name}.")
    logical = scenarios._logical_sha256_parquet(path, schema, keys)
    return {
        "path": path.name,
        "rows": int(parquet.metadata.num_rows),
        "schema": scenarios._schema_descriptor(schema),
        "key": list(keys),
        "sha256": _sha256_file(path),
        "byte_length": path.stat().st_size,
        "logical_sha256": logical,
    }


def _json_metadata(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    return {
        "path": path.name,
        "sha256": _sha256_file(path),
        "byte_length": path.stat().st_size,
        "canonical_json_sha256": hashlib.sha256(_canonical_json(value)).hexdigest(),
    }


def _csv_metadata(path: Path) -> dict[str, Any]:
    frame = pd.read_csv(path)
    if tuple(frame.columns) != COMPARISON_COLUMNS:
        raise SimulationIntegrityError("Comparison CSV ordered columns differ from its contract.")
    arrays = [
        pa.array(frame[field.name].tolist(), type=field.type, from_pandas=True)
        for field in COMPARISON_SCHEMA
    ]
    table = pa.Table.from_arrays(arrays, schema=COMPARISON_SCHEMA)
    logical = scenarios.logical_table_sha256(table, ("case_id", "metric"))
    return {
        "path": path.name,
        "rows": int(len(frame)),
        "schema": scenarios._schema_descriptor(table.schema),
        "key": ["case_id", "metric"],
        "sha256": _sha256_file(path),
        "byte_length": path.stat().st_size,
        "logical_sha256": logical,
    }


def _atomic_publish(
    stage: Path, final_dir: Path, output_root: Path, pointer: Mapping[str, Any]
) -> None:
    if final_dir.exists():
        raise FileExistsError(f"Phase 10 run ID already exists: {final_dir}.")
    pointer_tmp = output_root / f".current-{os.getpid()}-{uuid.uuid4().hex}.tmp"
    current_path = output_root / "current.json"
    try:
        _write_json(pointer_tmp, pointer)
        os.replace(stage, final_dir)
        try:
            os.replace(pointer_tmp, current_path)
        except Exception:
            shutil.rmtree(final_dir, ignore_errors=True)
            raise
    finally:
        pointer_tmp.unlink(missing_ok=True)


def _target_record_map(path: Path) -> dict[tuple[str, int, str], dict[str, Any]]:
    result: dict[tuple[str, int, str], dict[str, Any]] = {}
    for batch in pq.ParquetFile(path).iter_batches(batch_size=65_536):
        for row in batch.to_pylist():
            key = (row["case_id"], int(row["Store"]), row["policy_id"])
            if key in result:
                raise SimulationIntegrityError("Target artifact contains a duplicate track key.")
            result[key] = row
    return result


def _target_pairs(path: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    pending: list[dict[str, Any]] = []
    last_key: tuple[str, int] | None = None
    for batch in pq.ParquetFile(path).iter_batches(batch_size=65_536):
        for row in batch.to_pylist():
            key = (row["case_id"], int(row["Store"]))
            if last_key is not None and key != last_key:
                if len(pending) != 2 or [item["policy_id"] for item in pending] != list(POLICY_IDS):
                    raise SimulationIntegrityError(
                        "Target artifact does not contain a complete policy pair."
                    )
                yield pending[0], pending[1]
                pending = []
            pending.append(row)
            last_key = key
    if pending:
        if len(pending) != 2 or [item["policy_id"] for item in pending] != list(POLICY_IDS):
            raise SimulationIntegrityError("Final target artifact pair is incomplete.")
        yield pending[0], pending[1]


def _trajectory_signature(rows: Sequence[Mapping[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        tuple(
            _stable_value(row.get(field))
            for field in (
                "Date",
                "receipts_today_value",
                "demand_value",
                "fulfilled_value",
                "unmet_value",
                "ending_inventory_value",
                "pipeline_before_receipt_value",
                "pipeline_after_receipt_value",
                "pipeline_after_review_value",
                "inventory_position_value",
                "order_value",
                "order_due_date",
            )
        )
        for row in rows
    )


def _validate_target_stream(path: Path, expected_tracks: int) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    if not parquet.schema_arrow.remove_metadata().equals(
        POLICY_TARGET_SCHEMA, check_metadata=False
    ):
        raise SimulationIntegrityError("Emitted target schema differs from its explicit contract.")
    tracks = reference_tracks = 0
    variants: Counter[str] = Counter()
    seen: set[tuple[str, int, str]] = set()
    pair: list[dict[str, Any]] = []
    pair_key: tuple[str, int] | None = None

    def validate_pair(records: list[dict[str, Any]]) -> None:
        nonlocal tracks, reference_tracks
        if not records:
            return
        if len(records) != 2 or [row["policy_id"] for row in records] != list(POLICY_IDS):
            raise SimulationIntegrityError("Target artifact has an incomplete policy pair.")
        baseline, forecast = records
        shared = (
            "case_id",
            "scenario_id",
            "Store",
            "forecast_origin",
            "family",
            "mode",
            "replicate",
            "sensitivity_variant",
            "SupplierLeadTime",
            "ReviewPeriod",
            "ProtectionPeriod",
            "buffer_probability",
            "mean_open_sales_value",
            "initial_stock_value",
            "ProcurementCostRatio",
            "AnnualHoldingRate",
            "GoodwillPenaltyRate",
            "fit_id",
            "model_id",
            "upstream_identity",
            "synthetic",
            "calibration_transport_valid",
            "schedule_assumption",
        )
        if any(baseline[field] != forecast[field] for field in shared):
            raise SimulationIntegrityError("Paired policy targets have different exogenous inputs.")
        _validate_origin(baseline["forecast_origin"])
        lead = int(baseline["SupplierLeadTime"])
        if lead not in ALLOWED_LEAD_TIMES or int(baseline["ReviewPeriod"]) != 1:
            raise SimulationIntegrityError("Target artifact contains an unsupported L/R domain.")
        if int(baseline["ProtectionPeriod"]) != lead + 1 or lead + 1 > HORIZON_DAYS:
            raise SimulationIntegrityError("Target artifact contains an invalid protection period.")
        if float(baseline["buffer_probability"]) not in ALLOWED_P:
            raise SimulationIntegrityError("Target artifact contains an unsupported p value.")
        for record in records:
            tracks += 1
            variants[str(record["sensitivity_variant"])] += 1
            key = (record["case_id"], int(record["Store"]), record["policy_id"])
            if key in seen:
                raise SimulationIntegrityError("Target artifact contains a duplicate primary key.")
            seen.add(key)
            if record["case_id"] != f"{record['scenario_id']}--{record['sensitivity_variant']}":
                raise SimulationIntegrityError(
                    "Target case_id differs from scenario/variant identity."
                )
            if bool(record["target_available"]) != (record["availability_reason"] is None):
                raise SimulationIntegrityError("Target availability flag and reason disagree.")
            for field in (
                "mean_open_sales_value",
                "forecast_protection_demand_value",
                "cumulative_signed_quantile",
                "upper_turnover_value",
                "safety_stock_value",
                "target_value",
                "initial_stock_value",
                "ProcurementCostRatio",
                "AnnualHoldingRate",
                "GoodwillPenaltyRate",
            ):
                value = record[field]
                if value is not None and not math.isfinite(float(value)):
                    raise SimulationIntegrityError(f"Target value {field} is non-finite.")
            if record["target_value"] is not None and record["target_value"] < 0:
                raise SimulationIntegrityError("Target value cannot be negative.")
            if bool(record["synthetic"]):
                if record["calibration_transport_valid"] is not False:
                    raise SimulationIntegrityError(
                        "Synthetic transport cannot be marked calibrated."
                    )
                if (
                    record["policy_id"] == POLICY_IDS[1]
                    and record["buffer_interpretation"] != "uncalibrated_synthetic_heuristic"
                ):
                    raise SimulationIntegrityError("Synthetic buffer interpretation is mislabeled.")
            if record["policy_id"] == POLICY_IDS[0]:
                if record["target_available"]:
                    expected_target = float(record["mean_open_sales_value"]) * int(
                        record["open_days_in_protection_period"]
                    )
                    if not _close(float(record["target_value"]), expected_target):
                        raise SimulationIntegrityError(
                            "Baseline standing-target arithmetic failed."
                        )
                elif record["target_value"] is not None:
                    raise SimulationIntegrityError("Unavailable baseline target must be null.")
            elif record["target_available"]:
                demand = float(record["forecast_protection_demand_value"])
                quantile = float(record["cumulative_signed_quantile"])
                upper = max(0.0, demand + quantile)
                safety = max(0.0, upper - demand)
                if (
                    not _close(float(record["upper_turnover_value"]), upper)
                    or not _close(float(record["safety_stock_value"]), safety)
                    or not _close(float(record["target_value"]), max(demand, upper))
                ):
                    raise SimulationIntegrityError("Forecast buffered-target arithmetic failed.")
            elif record["target_value"] is not None:
                raise SimulationIntegrityError("Unavailable forecast target must be null.")
            if record["sensitivity_variant"] == REFERENCE_VARIANT:
                reference_tracks += 1

    for batch in parquet.iter_batches(batch_size=65_536):
        for row in batch.to_pylist():
            key = (row["case_id"], int(row["Store"]))
            if pair_key is not None and key != pair_key:
                validate_pair(pair)
                pair = []
            pair_key = key
            pair.append(row)
    validate_pair(pair)
    if tracks != expected_tracks:
        raise SimulationIntegrityError(
            "Target artifact track counts differ from approved grid counts."
        )
    if expected_tracks == 383_560:
        expected_variants = {REFERENCE_VARIANT: 182_860}
        expected_variants.update(
            {
                variant: 22_300
                for variant in (
                    "lead_2",
                    "lead_7",
                    "buffer_090",
                    "buffer_098",
                    "holding_010",
                    "holding_030",
                    "goodwill_010",
                    "goodwill_075",
                    "coverage_1",
                )
            }
        )
        if dict(variants) != expected_variants or reference_tracks != 182_860:
            raise SimulationIntegrityError(
                "Target artifact sensitivity variants/counts differ from contract."
            )
    return {
        "tracks": tracks,
        "reference_tracks": reference_tracks,
        "variant_track_counts": dict(sorted(variants.items())),
        "target_arithmetic": "passed",
        "paired_exogenous_inputs": "passed",
    }


def _validate_ledger_stream(
    path: Path,
    expected_tracks: int,
    expected_rows: int,
    *,
    summary_path: Path | None = None,
    target_path: Path | None = None,
) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    if not parquet.schema_arrow.remove_metadata().equals(
        SIMULATION_LEDGER_SCHEMA, check_metadata=False
    ):
        raise SimulationIntegrityError("Emitted ledger schema differs from the explicit contract.")
    current_key: tuple[str, int, str] | None = None
    current: list[dict[str, Any]] = []
    tracks = rows = complete = unavailable = protected = reference_tracks = 0
    summary_rows = (
        (
            record
            for batch in pq.ParquetFile(summary_path).iter_batches(batch_size=8192)
            for record in batch.to_pylist()
        )
        if summary_path is not None
        else None
    )
    target_keys = (
        (
            (row["case_id"], int(row["Store"]), row["policy_id"])
            for batch in pq.ParquetFile(target_path).iter_batches(batch_size=8192)
            for row in batch.to_pylist()
        )
        if target_path is not None
        else None
    )

    def validate_track(track: list[dict[str, Any]]) -> None:
        nonlocal tracks, complete, unavailable, protected, reference_tracks
        if not track:
            return
        tracks += 1
        ordered = sorted(track, key=lambda row: int(row["horizon"]))
        if [int(row["horizon"]) for row in ordered] != list(range(15)):
            raise SimulationIntegrityError("Emitted ledger track does not contain origin plus H14.")
        key = (ordered[0]["case_id"], int(ordered[0]["Store"]), ordered[0]["policy_id"])
        if target_keys is not None:
            try:
                target_key = next(target_keys)
            except StopIteration as error:
                raise SimulationIntegrityError(
                    "Ledger contains a track without a policy target foreign key."
                ) from error
            if target_key != key:
                raise SimulationIntegrityError(
                    f"Ledger track {key} does not match target foreign key {target_key}."
                )
        lead = int(ordered[0]["SupplierLeadTime"])
        if ordered[0]["sensitivity_variant"] == REFERENCE_VARIANT:
            reference_tracks += 1
        if any(row["Date"] > scenarios.DEVELOPMENT_CUTOFF for row in ordered):
            protected += 1
            raise SimulationIntegrityError("Emitted ledger contains a post-development date.")
        summary = next(summary_rows) if summary_rows is not None else None
        if summary is not None:
            summary_key = (summary["case_id"], int(summary["Store"]), summary["policy_id"])
            if summary_key != key:
                raise SimulationIntegrityError(
                    "Policy summary row order/keys differ from the ledger."
                )
        if not all(bool(row["state_available"]) for row in ordered):
            unavailable += 1
            if summary is not None:
                if summary["episode_complete"] or summary["episode_status"] == "complete":
                    raise SimulationIntegrityError(
                        f"Unavailable ledger has a complete summary for {key}."
                    )
                for field in (
                    "demand_total",
                    "fulfilled_total",
                    "unmet_total",
                    "holding_cost_total",
                    "unmet_penalty_total",
                    "SimulatedHoldingPlusShortfallCost",
                    "ValueFillRate",
                    "PositiveDemandStockoutRate",
                    "AverageInventoryValue",
                    "CompletedPositiveDemandReceiptCycleServiceRate",
                ):
                    if not _is_null(summary[field]):
                        raise SimulationIntegrityError(
                            f"Unavailable summary metric {field} is not null."
                        )
            return
        complete += 1
        queue: dict[str, tuple[date, float]] = {}
        total_orders = total_receipts = total_fulfilled = total_demand = total_unmet = 0.0
        total_holding = total_unmet_penalty = inventory_sum = 0.0
        positive_days = stockout_days = 0
        placed_orders: list[tuple[date, float]] = []
        initial_stock = float(ordered[0]["starting_inventory_value"])
        if not _close(float(ordered[0]["inventory_position_value"]), initial_stock):
            raise SimulationIntegrityError(f"Origin inventory position failed for {key}.")
        for row in ordered:
            horizon = int(row["horizon"])
            current_date = row["Date"]
            before = sum(value for _, value in queue.values())
            if not _close(float(row["pipeline_before_receipt_value"]), before):
                raise SimulationIntegrityError(
                    f"Pipeline-before-receipt identity failed for {key}."
                )
            due_ids = row["received_order_ids"].split(",") if row["received_order_ids"] else []
            receipt_total = 0.0
            for order_id in due_ids:
                if order_id not in queue or queue[order_id][0] != current_date:
                    raise SimulationIntegrityError(
                        f"Queue order received zero/multiple times for {key}."
                    )
                due_date, value = queue.pop(order_id)
                if due_date != current_date:
                    raise SimulationIntegrityError(f"Order due date differs from ledger for {key}.")
                receipt_total += value
            if not _close(float(row["receipts_today_value"]), receipt_total):
                raise SimulationIntegrityError(f"Receipt identity failed for {key}.")
            after_receipt = sum(value for _, value in queue.values())
            if any(due_date < current_date for due_date, _ in queue.values()):
                raise SimulationIntegrityError(f"An order passed its due date for {key}.")
            if not _close(float(row["pipeline_after_receipt_value"]), after_receipt):
                raise SimulationIntegrityError(f"Pipeline-after-receipt identity failed for {key}.")
            if horizon > 0:
                demand = float(row["demand_value"])
                fulfilled = float(row["fulfilled_value"])
                unmet = float(row["unmet_value"])
                if not _close(demand, fulfilled + unmet):
                    raise SimulationIntegrityError(f"Demand balance failed for {key}.")
                if not _close(
                    float(row["available_stock_value"]),
                    float(row["starting_inventory_value"]) + receipt_total,
                ):
                    raise SimulationIntegrityError(f"Available-stock balance failed for {key}.")
                if not _close(
                    float(row["ending_inventory_value"]),
                    float(row["available_stock_value"]) - fulfilled,
                ):
                    raise SimulationIntegrityError(f"Ending-inventory balance failed for {key}.")
                if not _close(
                    float(row["inventory_position_value"]),
                    float(row["ending_inventory_value"]) + after_receipt,
                ):
                    raise SimulationIntegrityError(f"Inventory-position balance failed for {key}.")
                c = float(row["ProcurementCostRatio"])
                annual = float(row["AnnualHoldingRate"])
                goodwill = float(row["GoodwillPenaltyRate"])
                holding_rate = c * annual / 365.0
                unmet_rate = (1.0 - c) + goodwill
                if not _close(float(row["HoldingCostRate"]), holding_rate):
                    raise SimulationIntegrityError(f"Holding-rate arithmetic failed for {key}.")
                if not _close(float(row["UnmetPenaltyRate"]), unmet_rate):
                    raise SimulationIntegrityError(
                        f"Unmet-penalty-rate arithmetic failed for {key}."
                    )
                if not _close(
                    float(row["holding_cost"]), holding_rate * float(row["ending_inventory_value"])
                ):
                    raise SimulationIntegrityError(
                        f"Daily holding-cost arithmetic failed for {key}."
                    )
                if not _close(float(row["unmet_penalty"]), unmet_rate * unmet):
                    raise SimulationIntegrityError(
                        f"Daily unmet-penalty arithmetic failed for {key}."
                    )
                total_fulfilled += fulfilled
                total_unmet += unmet
                total_demand += demand
                total_receipts += receipt_total
                total_holding += float(row["holding_cost"])
                total_unmet_penalty += float(row["unmet_penalty"])
                inventory_sum += float(row["ending_inventory_value"])
                if demand > 0:
                    positive_days += 1
                    stockout_days += int(unmet > 0)
            order_value = float(row["order_value"] or 0.0)
            if horizon == HORIZON_DAYS and order_value != 0:
                raise SimulationIntegrityError(f"Terminal day order found for {key}.")
            order_id = row["order_id"]
            if order_value > 0:
                expected_due = current_date + timedelta(days=lead + 1)
                if order_id is None or row["order_due_date"] != expected_due:
                    raise SimulationIntegrityError(f"Order placement/due date failed for {key}.")
                if order_id in queue:
                    raise SimulationIntegrityError(f"Duplicate order ID in ledger for {key}.")
                queue[order_id] = (expected_due, order_value)
                total_orders += order_value
                placed_orders.append((expected_due, order_value))
            after_review = sum(value for _, value in queue.values())
            if not _close(float(row["pipeline_after_review_value"]), after_review):
                raise SimulationIntegrityError(f"Pipeline-after-review identity failed for {key}.")
        terminal = ordered[-1]
        if not _close(
            float(terminal["ending_inventory_value"]),
            initial_stock + total_receipts - total_fulfilled,
        ):
            raise SimulationIntegrityError(f"Terminal inventory identity failed for {key}.")
        if not _close(
            float(terminal["pipeline_after_review_value"]), total_orders - total_receipts
        ):
            raise SimulationIntegrityError(f"Terminal outstanding-order identity failed for {key}.")
        if not _close(total_demand, total_fulfilled + total_unmet):
            raise SimulationIntegrityError(f"Episode demand conservation failed for {key}.")
        if summary is not None:
            receipt_dates = sorted(
                {
                    row["Date"]
                    for row in ordered
                    if int(row["horizon"]) > 0 and float(row["receipts_today_value"]) > 0
                }
            )
            completed_positive = zero_unmet_positive = zero_demand_cycles = 0
            for left, right in zip(receipt_dates, receipt_dates[1:], strict=False):
                cycle_rows = [row for row in ordered if left <= row["Date"] < right]
                cycle_demand = sum(float(row["demand_value"]) for row in cycle_rows)
                cycle_unmet = sum(float(row["unmet_value"]) for row in cycle_rows)
                if cycle_demand > 0:
                    completed_positive += 1
                    zero_unmet_positive += int(cycle_unmet == 0)
                else:
                    zero_demand_cycles += 1
            first_day = ordered[0]["forecast_origin"] + timedelta(days=1)
            last_day = ordered[0]["forecast_origin"] + timedelta(days=HORIZON_DAYS)
            initial_left = int(not receipt_dates or receipt_dates[0] > first_day)
            terminal_right = int(not receipt_dates or receipt_dates[-1] < last_day)
            terminal = ordered[-1]
            terminal_stock = float(terminal["ending_inventory_value"])
            terminal_pipeline = float(terminal["pipeline_after_review_value"])
            c = float(terminal["ProcurementCostRatio"])
            late_orders = [item for item in placed_orders if item[0] > last_day]

            def check_metric(name: str, expected_value: float | int | None) -> None:
                actual = summary[name]
                if expected_value is None:
                    if not _is_null(actual):
                        raise SimulationIntegrityError(
                            f"Summary metric {name} should be null for {key}."
                        )
                elif _is_null(actual) or not _close(float(actual), float(expected_value)):
                    raise SimulationIntegrityError(
                        f"Summary metric {name} differs from the ledger for {key}."
                    )

            if summary["episode_complete"] is not True or summary["episode_status"] != "complete":
                raise SimulationIntegrityError(
                    f"Complete ledger has an incomplete summary for {key}."
                )
            if summary["calendar_days"] != HORIZON_DAYS:
                raise SimulationIntegrityError(f"Summary calendar denominator differs for {key}.")
            for name, value in (
                ("demand_total", total_demand),
                ("fulfilled_total", total_fulfilled),
                ("unmet_total", total_unmet),
                ("positive_demand_days", positive_days),
                ("positive_demand_stockout_days", stockout_days),
                ("ending_inventory_sum", inventory_sum),
                ("holding_cost_total", total_holding),
                ("unmet_penalty_total", total_unmet_penalty),
                ("SimulatedHoldingPlusShortfallCost", total_holding + total_unmet_penalty),
                ("ValueFillRate", total_fulfilled / total_demand if total_demand > 0 else None),
                (
                    "PositiveDemandStockoutRate",
                    stockout_days / positive_days if positive_days else None,
                ),
                ("AverageInventoryValue", inventory_sum / HORIZON_DAYS),
                ("UnmetTurnoverValue", total_unmet),
                ("SimulatedHoldingCost", total_holding),
                ("SimulatedUnmetPenalty", total_unmet_penalty),
                (
                    "CompletedPositiveDemandReceiptCycleServiceRate",
                    zero_unmet_positive / completed_positive if completed_positive else None,
                ),
                ("terminal_on_hand_value", terminal_stock),
                ("terminal_on_order_value", terminal_pipeline),
                ("TerminalStockCostValue", c * terminal_stock),
                ("OutstandingProcurementCommitment", c * terminal_pipeline),
                ("late_order_count", len(late_orders)),
                ("late_order_value", sum(value for _, value in late_orders)),
            ):
                check_metric(name, value)
            for name, value in (
                ("completed_cycles_total", max(0, len(receipt_dates) - 1)),
                ("completed_positive_demand_cycles", completed_positive),
                ("zero_unmet_positive_demand_cycles", zero_unmet_positive),
                ("zero_demand_completed_cycles", zero_demand_cycles),
                ("initial_left_censored_intervals", initial_left),
                ("terminal_right_censored_intervals", terminal_right),
            ):
                if summary[name] != value:
                    raise SimulationIntegrityError(
                        f"Summary count {name} differs from ledger for {key}."
                    )

    for batch in parquet.iter_batches(batch_size=65_536):
        records = batch.to_pylist()
        rows += len(records)
        for row in records:
            key = (row["case_id"], int(row["Store"]), row["policy_id"])
            if current_key is not None and key != current_key:
                validate_track(current)
                current = []
            current_key = key
            current.append(row)
    validate_track(current)
    if summary_rows is not None:
        try:
            next(summary_rows)
        except StopIteration:
            pass
        else:
            raise SimulationIntegrityError("Policy summary has rows not represented in the ledger.")
    if target_keys is not None:
        try:
            next(target_keys)
        except StopIteration:
            pass
        else:
            raise SimulationIntegrityError("Policy targets contain tracks absent from the ledger.")
    if (
        tracks != expected_tracks
        or rows != expected_rows
        or (expected_tracks == 383_560 and reference_tracks != 182_860)
    ):
        raise SimulationIntegrityError(
            f"Emitted ledger grid mismatch: tracks={tracks}, rows={rows}, "
            f"reference_tracks={reference_tracks}."
        )
    return {
        "tracks": tracks,
        "rows": rows,
        "reference_tracks": reference_tracks,
        "reference_rows": reference_tracks * 15,
        "complete_tracks": complete,
        "unavailable_or_incomplete_tracks": unavailable,
        "invalid_foreign_keys": 0,
        "post_cutoff_date_rows": protected,
        "queue_identity": "passed",
        "daily_and_terminal_balances": "passed",
    }


def _target_source_metadata(inputs: Mapping[str, Any]) -> dict[str, Any]:
    config = inputs["phase9_config"]
    return {
        "scenario_families": list(config["scenario_families"]),
        "origins": list(config["forecast_origins"]),
        "store_count": len(config["stores"]),
        "replicates": list(config["replicates"]),
        "phase7_manifest_sha256": PHASE7_MANIFEST_SHA256,
        "phase8_manifest_sha256": PHASE8_MANIFEST_SHA256,
        "phase9_manifest_sha256": PHASE9_MANIFEST_SHA256,
    }


def run_inventory_simulation(
    root: str | Path | None = None,
    *,
    run_id: str = "phase10-dev-20261007-implementation",
    command: str = "python scripts/run_inventory_simulation.py",
) -> dict[str, Any]:
    """Verify, freeze, simulate, validate and immutably publish one development run."""
    repository = Path(root or Path.cwd()).resolve()
    if not run_id or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in run_id
    ):
        raise SimulationIntegrityError(
            "run_id may contain only ASCII letters, digits, hyphens and underscores."
        )
    output_root = repository / "data/processed/inventory_simulation"
    final_dir = output_root / run_id
    if final_dir.exists():
        raise FileExistsError(f"Phase 10 run ID already exists: {final_dir}.")
    _assert_git_ignored(repository, "data/processed/inventory_simulation")
    _assert_git_ignored(repository, f"data/processed/inventory_simulation/{run_id}")

    # No target or outcome-bearing read starts until unsupported origins are rejected.
    initial_inputs = verify_simulation_inputs(repository)
    output_root.mkdir(parents=True, exist_ok=True)
    if final_dir.exists():
        raise FileExistsError(f"Phase 10 run ID already exists: {final_dir}.")
    stage = Path(tempfile.mkdtemp(prefix=f".phase10-stage-{run_id}-", dir=output_root))
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    config = default_simulation_config()
    config.update(
        {
            "run_id": run_id,
            "created_at_utc": created_at,
            "approval_reference": "ADR-023 accepted; human approval 2026-10-07",
            "inputs": _target_source_metadata(initial_inputs),
            "assumptions": [
                "Sales is retail-equivalent monetary turnover, not physical demand.",
                "Historical replay is conditional on saved source Open assumed known at origin.",
                "Synthetic q transport is uncalibrated and heuristic.",
                "Phase 9 seed 4209 is inherited; Phase 10 makes no random draw.",
            ],
            "boundaries": {
                "allowed_outcome_through": scenarios.DEVELOPMENT_CUTOFF.isoformat(),
                "protected_holdout_values_read_or_hashed": False,
                "raw_train_file_hashed": False,
                "phase9_regenerated": False,
                "model_refit": False,
                "uncertainty_recalibrated": False,
            },
        }
    )
    config["config_canonical_sha256"] = hashlib.sha256(
        _canonical_json(
            {
                key: value
                for key, value in config.items()
                if key not in {"run_id", "created_at_utc", "config_canonical_sha256"}
            }
        )
    ).hexdigest()
    try:
        _write_json(stage / "simulation_config.json", config)
        target_tracks, target_grid = _build_targets_to_file(initial_inputs, stage)
        if target_tracks != 383_560:
            raise SimulationIntegrityError(
                "Policy target output differs from the approved requested grid."
            )

        # All policy targets are now durably frozen in the staging run. Only now may
        # realized synthetic or historical demand values be materialized.
        phase9_tables = _check_phase9_tables_after_target_freeze(initial_inputs)
        del phase9_tables
        historical_outcomes = _load_historical_outcomes(initial_inputs)

        targets_path = stage / "policy_targets.parquet"
        target_parquet = pq.ParquetFile(targets_path)
        if not target_parquet.schema_arrow.remove_metadata().equals(
            POLICY_TARGET_SCHEMA, check_metadata=False
        ):
            raise SimulationIntegrityError(
                "Frozen target artifact schema differs from its contract."
            )
        if target_parquet.metadata.num_rows != 383_560:
            raise SimulationIntegrityError(
                "Frozen target count differs from approved grid expectation."
            )
        # PyArrow keeps the file handle open on Windows; it must be released before
        # the staged directory can be atomically renamed into its immutable run path.
        target_parquet.close()
        target_validation = _validate_target_stream(targets_path, expected_tracks=383_560)

        scenario_rows = pq.read_table(
            Path(initial_inputs["phase9_dir"]) / "scenario_catalog.parquet"
        ).to_pylist()
        scenario_by_id = {row["scenario_id"]: row for row in scenario_rows}
        ledger_path = stage / "simulation_ledger.parquet"
        summary_path = stage / "policy_summary.parquet"
        ledger_writer = pq.ParquetWriter(ledger_path, SIMULATION_LEDGER_SCHEMA, compression="zstd")
        summary_writer = pq.ParquetWriter(summary_path, POLICY_SUMMARY_SCHEMA, compression="zstd")
        ledger_buffer: list[dict[str, Any]] = []
        summary_buffer: list[dict[str, Any]] = []
        current_case: str | None = None
        current_case_summaries: list[dict[str, Any]] = []
        comparison_rows: list[dict[str, Any]] = []
        current_scenario: str | None = None
        synthetic_paths: dict[int, list[dict[str, Any]]] = {}
        requested_tracks = 0
        reference_tracks = 0
        exclusion_reasons: Counter[str] = Counter()
        status_counts: Counter[str] = Counter()
        headline: dict[tuple[str, str, str], dict[str, float]] = {}
        reference_signatures: dict[tuple[str, int, str], tuple[tuple[Any, ...], ...]] = {}
        cost_overlay_signatures: list[
            tuple[tuple[str, int, str], str, tuple[tuple[Any, ...], ...]]
        ] = []
        try:
            for baseline_target, forecast_target in _target_pairs(targets_path):
                case_id = str(baseline_target["case_id"])
                scenario_id = str(baseline_target["scenario_id"])
                if current_case is not None and case_id != current_case:
                    comparison_rows.extend(_comparison_rows(current_case, current_case_summaries))
                    current_case_summaries.clear()
                current_case = case_id
                if scenario_id != current_scenario:
                    current_scenario = scenario_id
                    scenario = scenario_by_id[scenario_id]
                    synthetic_paths = (
                        _read_synthetic_path(initial_inputs, scenario_id)
                        if scenario["mode"] == "synthetic_stress"
                        else {}
                    )
                scenario = scenario_by_id[scenario_id]
                store = int(baseline_target["Store"])
                origin = baseline_target["forecast_origin"]
                demand_path = (
                    synthetic_paths[store]
                    if scenario["mode"] == "synthetic_stress"
                    else _historical_path(store, origin, historical_outcomes)
                )
                left_exogenous = tuple(
                    baseline_target[name]
                    for name in (
                        "initial_stock_value",
                        "SupplierLeadTime",
                        "ProtectionPeriod",
                        "ProcurementCostRatio",
                        "AnnualHoldingRate",
                        "GoodwillPenaltyRate",
                    )
                )
                right_exogenous = tuple(
                    forecast_target[name]
                    for name in (
                        "initial_stock_value",
                        "SupplierLeadTime",
                        "ProtectionPeriod",
                        "ProcurementCostRatio",
                        "AnnualHoldingRate",
                        "GoodwillPenaltyRate",
                    )
                )
                if left_exogenous != right_exogenous:
                    raise SimulationIntegrityError(
                        "Paired target policies have unequal exogenous inputs."
                    )
                common_identity = _common_input_identity(baseline_target, demand_path)
                pair_results: list[dict[str, Any]] = []
                for target in (baseline_target, forecast_target):
                    track, summary = simulate_case(
                        target, demand_path, common_input_identity=common_identity
                    )
                    ledger_buffer.extend(track)
                    summary_buffer.append(summary)
                    current_case_summaries.append(summary)
                    pair_results.append(summary)
                    status_counts[str(summary["episode_status"])] += 1
                    if not summary["episode_complete"]:
                        reason = str(summary["availability_reason"] or "unavailable")
                        exclusion_reasons[reason] += 1
                    requested_tracks += 1
                    signature = _trajectory_signature(track)
                    physical_key = (scenario_id, store, str(target["policy_id"]))
                    variant = str(target["sensitivity_variant"])
                    if variant == REFERENCE_VARIANT and scenario["family"] == "synthetic_base":
                        reference_signatures[physical_key] = signature
                    elif variant in {"holding_010", "holding_030", "goodwill_010", "goodwill_075"}:
                        cost_overlay_signatures.append((physical_key, variant, signature))
                if (
                    pair_results[0]["common_input_identity"]
                    != pair_results[1]["common_input_identity"]
                ):
                    raise SimulationIntegrityError(
                        "Paired tracks do not retain a common input identity."
                    )
                if baseline_target["sensitivity_variant"] == REFERENCE_VARIANT:
                    reference_tracks += len(POLICY_IDS)
                if all(
                    item["episode_complete"] and item["valid_matched_comparison"]
                    for item in pair_results
                ):
                    headline_key = (
                        str(scenario["mode"]),
                        str(scenario["family"]),
                        str(baseline_target["sensitivity_variant"]),
                    )
                    totals = headline.setdefault(
                        headline_key,
                        {
                            "matched_store_tracks": 0.0,
                            "baseline_cost": 0.0,
                            "forecast_cost": 0.0,
                            "baseline_demand": 0.0,
                            "forecast_demand": 0.0,
                            "baseline_fulfilled": 0.0,
                            "forecast_fulfilled": 0.0,
                            "baseline_unmet": 0.0,
                            "forecast_unmet": 0.0,
                            "baseline_terminal_stock": 0.0,
                            "forecast_terminal_stock": 0.0,
                            "baseline_terminal_pipeline": 0.0,
                            "forecast_terminal_pipeline": 0.0,
                            "baseline_terminal_stock_cost": 0.0,
                            "forecast_terminal_stock_cost": 0.0,
                            "baseline_commitment": 0.0,
                            "forecast_commitment": 0.0,
                        },
                    )
                    totals["matched_store_tracks"] += 1
                    for label, summary in zip(("baseline", "forecast"), pair_results, strict=True):
                        totals[f"{label}_cost"] += float(
                            summary["SimulatedHoldingPlusShortfallCost"]
                        )
                        totals[f"{label}_demand"] += float(summary["demand_total"])
                        totals[f"{label}_fulfilled"] += float(summary["fulfilled_total"])
                        totals[f"{label}_unmet"] += float(summary["unmet_total"])
                        totals[f"{label}_terminal_stock"] += float(
                            summary["terminal_on_hand_value"]
                        )
                        totals[f"{label}_terminal_pipeline"] += float(
                            summary["terminal_on_order_value"]
                        )
                        totals[f"{label}_terminal_stock_cost"] += float(
                            summary["TerminalStockCostValue"]
                        )
                        totals[f"{label}_commitment"] += float(
                            summary["OutstandingProcurementCommitment"]
                        )
                if len(ledger_buffer) >= 60_000:
                    ledger_writer.write_table(
                        pa.Table.from_pylist(ledger_buffer, schema=SIMULATION_LEDGER_SCHEMA),
                        row_group_size=65_536,
                    )
                    ledger_buffer.clear()
                if len(summary_buffer) >= 20_000:
                    summary_writer.write_table(
                        pa.Table.from_pylist(summary_buffer, schema=POLICY_SUMMARY_SCHEMA),
                        row_group_size=65_536,
                    )
                    summary_buffer.clear()
            if current_case is not None:
                comparison_rows.extend(_comparison_rows(current_case, current_case_summaries))
            if ledger_buffer:
                ledger_writer.write_table(
                    pa.Table.from_pylist(ledger_buffer, schema=SIMULATION_LEDGER_SCHEMA),
                    row_group_size=65_536,
                )
            if summary_buffer:
                summary_writer.write_table(
                    pa.Table.from_pylist(summary_buffer, schema=POLICY_SUMMARY_SCHEMA),
                    row_group_size=65_536,
                )
        finally:
            ledger_writer.close()
            summary_writer.close()

        if requested_tracks != 383_560:
            raise SimulationIntegrityError(f"Simulation track count mismatch: {requested_tracks}.")
        if reference_tracks != 182_860:
            raise SimulationIntegrityError(f"Reference track count mismatch: {reference_tracks}.")
        for key, variant, signature in cost_overlay_signatures:
            reference = reference_signatures.get(key)
            if reference is None or reference != signature:
                raise SimulationIntegrityError(
                    f"Cost-only sensitivity changed the physical trajectory: {key}/{variant}."
                )
        comparison_rows.sort(key=lambda row: (row["case_id"], row["metric"]))
        comparison = pd.DataFrame.from_records(comparison_rows, columns=COMPARISON_COLUMNS)
        if len(comparison) != 1_720:
            raise SimulationIntegrityError(
                f"Comparison grid mismatch: expected 1720 rows, got {len(comparison)}."
            )
        if comparison.duplicated(["case_id", "metric"]).any():
            raise SimulationIntegrityError("Comparison summary contains duplicate keys.")
        comparison_path = stage / "comparison_summary.csv"
        comparison.to_csv(
            comparison_path,
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )

        # Independently reread the emitted ledger and reconstruct its queue and balances.
        ledger_validation = _validate_ledger_stream(
            ledger_path,
            expected_tracks=383_560,
            expected_rows=5_753_400,
            summary_path=summary_path,
            target_path=targets_path,
        )
        target_metadata = _parquet_metadata(
            targets_path, POLICY_TARGET_SCHEMA, ("case_id", "Store", "policy_id")
        )
        ledger_metadata = _parquet_metadata(
            ledger_path,
            SIMULATION_LEDGER_SCHEMA,
            ("case_id", "Store", "policy_id", "Date"),
        )
        summary_metadata = _parquet_metadata(
            summary_path, POLICY_SUMMARY_SCHEMA, ("case_id", "Store", "policy_id")
        )
        if summary_metadata["rows"] != 383_560 or target_metadata["rows"] != 383_560:
            raise SimulationIntegrityError(
                "Target/summary artifact row counts differ from approved counts."
            )
        comparison_metadata = _csv_metadata(comparison_path)
        policy_summary_table = pq.read_table(summary_path)
        if not policy_summary_table.schema.remove_metadata().equals(
            POLICY_SUMMARY_SCHEMA, check_metadata=False
        ):
            raise SimulationIntegrityError("Staged policy summary schema changed.")
        summary_frame = policy_summary_table.to_pandas()
        if summary_frame.duplicated(["case_id", "Store", "policy_id"]).any():
            raise SimulationIntegrityError("Staged policy summary has duplicate keys.")
        if set(summary_frame["case_id"]) != set(comparison["case_id"]):
            raise SimulationIntegrityError("Comparison summary omitted a requested case.")
        headline_rows = []
        for key, values in sorted(headline.items()):
            mode, family, variant = key
            headline_rows.append(
                {
                    "mode": mode,
                    "family": family,
                    "sensitivity_variant": variant,
                    **values,
                    "forecast_minus_baseline_cost": values["forecast_cost"]
                    - values["baseline_cost"],
                    "baseline_value_fill_rate": (
                        values["baseline_fulfilled"] / values["baseline_demand"]
                        if values["baseline_demand"] > 0
                        else None
                    ),
                    "forecast_value_fill_rate": (
                        values["forecast_fulfilled"] / values["forecast_demand"]
                        if values["forecast_demand"] > 0
                        else None
                    ),
                }
            )
        exclusion_counts = dict(sorted(exclusion_reasons.items()))
        unavailable_tracks = sum(
            count for status, count in status_counts.items() if status != "complete"
        )
        validation = {
            "run_id": run_id,
            "created_at_utc": created_at,
            "status": "complete_with_unavailable_inputs" if unavailable_tracks else "complete",
            "policy_version": POLICY_VERSION,
            "decision": "ADR-023",
            "expected_counts": {
                "reference_policy_tracks": 182_860,
                "reference_ledger_rows": 2_742_900,
                "all_variant_policy_tracks": 383_560,
                "all_variant_ledger_rows": 5_753_400,
                "scenario_store_pairs_including_overlays": 191_780,
                "case_count": 172,
            },
            "actual_counts": {
                "policy_target_rows": target_metadata["rows"],
                "policy_summary_rows": summary_metadata["rows"],
                "ledger_tracks": ledger_validation["tracks"],
                "ledger_rows": ledger_validation["rows"],
                "reference_policy_tracks": reference_tracks,
                "reference_ledger_rows": reference_tracks * 15,
                "comparison_rows": comparison_metadata["rows"],
                "cases": int(summary_frame["case_id"].nunique()),
            },
            "availability": {
                "episode_status_counts": dict(sorted(status_counts.items())),
                "unavailable_or_incomplete_tracks": unavailable_tracks,
                "exclusion_reasons": exclusion_counts,
                "matched_case_store_pairs": int(
                    summary_frame.groupby(["case_id", "Store"])["valid_matched_comparison"]
                    .all()
                    .sum()
                ),
                "historical_open_assumption_violation_tracks": int(
                    summary_frame["historical_open_assumption_violation"].fillna(False).sum()
                ),
            },
            "checks": {
                "pinned_phase7_phase8_phase9_identities": "passed",
                "unsupported_origins_rejected_before_artifact_reads": "passed",
                "target_input_outcome_allowlist": "passed",
                "targets_frozen_before_synthetic_or_historical_outcomes_loaded": "passed",
                "phase9_schema_keys_and_logical_hashes": "passed",
                "daily_queue_inventory_demand_and_cost_invariants": "passed",
                "paired_exogenous_input_identity": "passed",
                "cost_only_overlay_trajectory_identity": "passed",
                "sensitivity_grid_exactly_nine_ofat_variants": "passed",
                "protected_outcome_dates_read_or_hashed": False,
                "raw_train_file_hashed": False,
                "model_refit": False,
                "phase9_regenerated": False,
                "holdout_access": False,
                "terminal_exposure_in_primary_objective": False,
                "terminal_day_order_suppressed": True,
            },
            "ledger_validation": ledger_validation,
            "target_validation": target_validation,
            "target_grid": target_grid,
            "headline_comparisons": headline_rows,
            "limitations": [
                "Historical replay is conditional on saved source Open being known at each origin.",
                "Synthetic uncertainty transport remains explicitly uncalibrated.",
                "Finite-window terminal stock and commitments exclude later lifecycle costs.",
                "Simulated monetary outcomes are not actual inventory, physical demand or savings.",
            ],
        }
        _write_json(stage / "validation_summary.json", validation)

        output_metadata = {
            "simulation_config.json": _json_metadata(stage / "simulation_config.json"),
            "policy_targets.parquet": target_metadata,
            "simulation_ledger.parquet": ledger_metadata,
            "policy_summary.parquet": summary_metadata,
            "comparison_summary.csv": comparison_metadata,
            "validation_summary.json": _json_metadata(stage / "validation_summary.json"),
        }

        # Final identity snapshot check catches upstream changes during the run.
        final_inputs = verify_simulation_inputs(repository)
        if _canonical_json(final_inputs["identity_snapshot"]) != _canonical_json(
            initial_inputs["identity_snapshot"]
        ):
            raise SimulationIntegrityError("Frozen upstream identities changed before publication.")

        worktree = _git(repository, "status", "--porcelain")
        manifest = {
            "run_id": run_id,
            "created_at_utc": created_at,
            "schema_version": SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "decision": "ADR-023",
            "status": validation["status"],
            "command": command,
            "arguments": {"run_id": run_id},
            "code_provenance": {
                "git_revision": _git(repository, "rev-parse", "HEAD"),
                "branch": _git(repository, "branch", "--show-current"),
                "worktree_clean": not bool(worktree),
                "worktree_status_porcelain": worktree,
                "source_sha256": _source_digest(repository),
            },
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "packages": _package_versions(),
                "uv_lock_sha256": _sha256_file(repository / "uv.lock"),
            },
            "seed": {"simulator": "not_applicable", "inherited_phase9": 4209},
            "inputs": {
                "phase7_selection_manifest_sha256": PHASE7_MANIFEST_SHA256,
                "phase7_run_id": PHASE7_RUN_ID,
                "phase8_manifest_sha256": PHASE8_MANIFEST_SHA256,
                "phase8_run_id": PHASE8_RUN_ID,
                "phase8_cumulative_error_quantiles_sha256": PHASE8_CUMULATIVE_SHA256,
                "phase9_manifest_sha256": PHASE9_MANIFEST_SHA256,
                "phase9_run_id": PHASE9_RUN_ID,
                "phase9_files": initial_inputs["phase9_files"],
                "phase7_8_identity_snapshot_sha256": hashlib.sha256(
                    _canonical_json(initial_inputs["identity_snapshot"])
                ).hexdigest(),
            },
            "assumptions": config["assumptions"],
            "boundaries": config["boundaries"],
            "outputs": output_metadata,
            "validation": {
                "path": "validation_summary.json",
                "status": validation["status"],
                "protected_outcome_dates_read_or_hashed": 0,
            },
        }
        _write_json(stage / "manifest.json", manifest)
        for name, metadata in output_metadata.items():
            path = stage / name
            if (
                _sha256_file(path) != metadata["sha256"]
                or path.stat().st_size != metadata["byte_length"]
            ):
                raise SimulationIntegrityError(
                    f"Staged output identity changed before publication: {name}."
                )
        manifest_sha = _sha256_file(stage / "manifest.json")
        pointer = {
            "run_id": run_id,
            "manifest_path": f"{run_id}/manifest.json",
            "manifest_sha256": manifest_sha,
            "status": validation["status"],
        }
        _atomic_publish(stage, final_dir, output_root, pointer)
        return {
            "run_id": run_id,
            "run_directory": str(final_dir),
            "manifest_sha256": manifest_sha,
            "validation_summary": validation,
            "output_metadata": output_metadata,
        }
    except Exception:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        raise
