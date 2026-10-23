"""Offline, controlled-synthetic release candidate for a future public demo profile.

This module is deliberately independent of the canonical artifact reader, forecasting models,
calibration code, and inventory simulator. Its values are fixed fixture arithmetic only.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
RELEASE_ID = "rossmann-course-demo-synthetic-v1"
EVIDENCE_KIND = "controlled_synthetic_demo"
FIXED_SEED = 4063
BUNDLE_FILENAME = "demo_bundle.json"
MANIFEST_FILENAME = "demo_manifest.json"
MAX_BUNDLE_BYTES = 5 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024

STORE_IDS = (101, 202, 303)
FORECAST_ORIGINS = ("2015-05-22", "2015-06-05", "2015-06-19")
HORIZONS = tuple(range(1, 15))
HISTORY_START = "2015-05-09"
HISTORY_END = "2015-07-03"
DEVELOPMENT_CUTOFF = "2015-07-03"
FIT_PAIRINGS = (
    {"fit_id": "demo_fit_a", "forecast_origin": "2015-06-05"},
    {"fit_id": "demo_fit_b", "forecast_origin": "2015-06-19"},
)
CASE_IDS = (
    "synthetic_demo_reference_20150605",
    "synthetic_demo_adverse_20150605",
)
CANDIDATE_IDS = ("demo_path_a", "demo_path_b", "demo_path_c")
MODEL_METRICS = ("mae", "rmse", "mape", "wape")
INVENTORY_METRICS = (
    "SimulatedHoldingPlusShortfallCost",
    "ValueFillRate",
    "PositiveDemandStockoutRate",
    "AverageInventoryValue",
    "UnmetTurnoverValue",
    "CompletedPositiveDemandReceiptCycleServiceRate",
    "terminal_on_hand_value",
    "terminal_on_order_value",
    "TerminalStockCostValue",
    "OutstandingProcurementCommitment",
)
POLICY_IDS = ("demo_reference_policy", "demo_forecast_policy")

_HEX_256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_DISTRIBUTION_VERSION_LENGTH = 128
_DISTRIBUTION_VERSION = re.compile(
    r"(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*(?:a[0-9]+|b[0-9]+|rc[0-9]+)?"
    r"(?:\.post[0-9]+)?(?:\.dev[0-9]+)?"
    r"(?:\+[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)?\Z",
    re.ASCII | re.IGNORECASE,
)
_PROHIBITED_KEYS = frozenset(
    {
        "actual_sales",
        "source_open",
        "customers",
        "canonical_run_id",
        "canonical_manifest_sha256",
        "model_sha256",
        "authorization_record",
        "protected_sales",
        "holdout_sales",
        "input_path",
        "source_path",
    }
)


class DemoBundleError(ValueError):
    """A release candidate failed its closed schema, integrity, or safety checks."""


@dataclass(frozen=True, slots=True)
class VerificationReport:
    bundle_ready: bool
    release_id: str
    evidence_kind: str
    bundle_sha256: str
    manifest_sha256: str
    bundle_bytes: int
    manifest_bytes: int
    row_counts: dict[str, int]
    deterministic_regeneration: bool


@dataclass(frozen=True, slots=True)
class DemoConfig:
    seed: int = FIXED_SEED


DEFAULT_CONFIG = DemoConfig()


def _canonical_json(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise DemoBundleError("The release contains a non-canonical JSON value.") from exc
    return text.encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _stable_unit(seed: int, *parts: object) -> float:
    key = ":".join((str(seed), *(str(item) for item in parts))).encode("ascii")
    integer = int.from_bytes(hashlib.sha256(key).digest()[:4], "big")
    return (integer % 2001) / 1000.0 - 1.0


def _expected_query_allowlist() -> dict[str, Any]:
    return {
        "catalog": {"arguments": []},
        "sales_history": {
            "store_ids": list(STORE_IDS),
            "minimum_date": HISTORY_START,
            "maximum_date": HISTORY_END,
            "maximum_calendar_days": 56,
        },
        "forecast_issuance": {
            "store_ids": list(STORE_IDS),
            "origins": list(FORECAST_ORIGINS),
            "horizons": list(HORIZONS),
        },
        "forecast_uncertainty": {
            "store_ids": list(STORE_IDS),
            "fit_pairings": [dict(item) for item in FIT_PAIRINGS],
            "horizons": list(HORIZONS),
            "probabilities": [0.9, 0.95, 0.98],
        },
        "model_comparison": {
            "candidate_ids": list(CANDIDATE_IDS),
            "population": "synthetic_open_label_rows",
            "validation_window": "synthetic_display_panel",
            "scopes": ["pooled", "horizon", "week_block", "store"],
            "metrics": list(MODEL_METRICS),
            "maximum_rows": 500,
        },
        "inventory_comparison": {
            "case_ids": list(CASE_IDS),
            "store_ids": list(STORE_IDS),
        },
    }


def _population() -> dict[str, Any]:
    return {
        "store_ids": list(STORE_IDS),
        "forecast_origins": list(FORECAST_ORIGINS),
        "horizons": list(HORIZONS),
        "fit_pairings": [dict(item) for item in FIT_PAIRINGS],
        "history": {
            "start_date": HISTORY_START,
            "end_date": HISTORY_END,
            "maximum_calendar_days": 56,
            "sparse_dates_preserved": True,
        },
        "development_label_cutoff": DEVELOPMENT_CUTOFF,
    }


def _limitations() -> list[str]:
    return [
        "All values are controlled synthetic fixture arithmetic; no Rossmann observations "
        "are included.",
        "No model was trained, fitted, or executed to create any trajectory or comparison value.",
        "Illustrative uncertainty bands and quantiles are fixed examples, not empirical "
        "calibration.",
        "Inventory values are monetary fixture examples, not physical quantities, stockouts, "
        "or savings.",
        "No July 4 through July 31 outcome labels, source files, model artifacts, or canonical "
        "hashes are included.",
        "This offline bundle does not establish production readiness or service-level guarantees.",
    ]


def _source_declaration() -> dict[str, Any]:
    return {
        "kind": "authored_fixture_arithmetic",
        "rossmann_data_included": False,
        "source_files_included": False,
        "external_data_sources": [],
        "redistribution_rights": "not_applicable_no_rossmann_derived_content",
        "model_runs_included": False,
        "model_execution": "none",
    }


def _history_rows(config: DemoConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = date.fromisoformat(HISTORY_START)
    for store_id in STORE_IDS:
        sparse_offset = {101: 13, 202: 27, 303: 41}[store_id]
        for offset in range(56):
            current = start + timedelta(days=offset)
            if offset == sparse_offset:
                continue
            is_open: bool | None = current.weekday() != 6
            if store_id == 303 and offset == 35:
                is_open = None
            if store_id == 101 and offset == 14:
                sales: int | None = 0
            elif store_id == 202 and offset == 23:
                sales = None
            elif is_open is False:
                sales = 0
            elif is_open is None:
                sales = None
            else:
                sales = (
                    8200
                    + store_id * 17
                    + current.weekday() * 240
                    + (offset * 37) % 311
                    + round(_stable_unit(config.seed, "history", store_id, offset) * 80)
                )
            state = "null_sales" if sales is None else "zero_sales" if sales == 0 else "value"
            rows.append(
                {
                    "store_id": store_id,
                    "date": current.isoformat(),
                    "sales_value": sales,
                    "synthetic_open": is_open,
                    "observation_state": state,
                }
            )
    return rows


def _forecast_raw(
    store_id: int, origin_index: int, horizon: int, target_date: date, seed: int
) -> int:
    return max(
        100,
        8600
        + store_id * 15
        + target_date.weekday() * 225
        + origin_index * 90
        + (horizon * 41 + store_id) % 173
        + round(_stable_unit(seed, "forecast", store_id, origin_index, horizon) * 90),
    )


def _forecast_rows(config: DemoConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for store_id in STORE_IDS:
        for origin_index, origin_text in enumerate(FORECAST_ORIGINS):
            origin = date.fromisoformat(origin_text)
            for horizon in HORIZONS:
                target = origin + timedelta(days=horizon)
                is_unknown = store_id == 303 and origin_text == "2015-06-19" and horizon == 4
                is_open = None if is_unknown else target.weekday() != 6
                raw_value = _forecast_raw(store_id, origin_index, horizon, target, config.seed)
                operational = None if is_open is None else raw_value if is_open else 0
                eligibility = (
                    "unknown" if is_open is None else "known_open" if is_open else "known_closed"
                )
                rows.append(
                    {
                        "store_id": store_id,
                        "forecast_origin": origin_text,
                        "date": target.isoformat(),
                        "horizon": horizon,
                        "raw_forecast_value": raw_value,
                        "raw_forecast_available": True,
                        "synthetic_open_eligibility": eligibility,
                        "operational_forecast_value": operational,
                        "operational_forecast_available": operational is not None,
                        "trajectory_label": "fixed_arithmetic_demo_path",
                        "model_execution": "none",
                    }
                )
    return rows


def _daily_intervals(forecast: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for interval_kind in ("raw", "operational"):
        available = (
            forecast["raw_forecast_available"]
            if interval_kind == "raw"
            else forecast["operational_forecast_available"]
        )
        point = (
            forecast["raw_forecast_value"]
            if interval_kind == "raw"
            else forecast["operational_forecast_value"]
        )
        if available:
            lower = max(0.0, point * 0.85)
            upper = point * 1.15
            width = upper - lower
            reason = None
        else:
            lower = upper = width = None
            reason = "synthetic_future_eligibility_unknown"
        output.append(
            {
                "date": forecast["date"],
                "horizon": forecast["horizon"],
                "interval_kind": interval_kind,
                "point_forecast": point,
                "lower": lower,
                "upper": upper,
                "width": width,
                "available": available,
                "unavailable_reason": reason,
                "units": "synthetic_retail_equivalent_turnover_value",
                "schedule_assumption_flag": interval_kind == "operational",
                "evidence_kind": EVIDENCE_KIND,
            }
        )
    return output


def _cumulative_uncertainty(forecasts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    forecasts = sorted(forecasts, key=lambda row: row["horizon"])
    probabilities = ((0.9, 80), (0.95, 120), (0.98, 180))
    output = []
    for horizon in HORIZONS:
        prefix = forecasts[:horizon]
        complete = all(row["operational_forecast_available"] for row in prefix)
        demand = sum(row["operational_forecast_value"] for row in prefix) if complete else None
        for probability, fixed_buffer_per_day in probabilities:
            signed_error = fixed_buffer_per_day * horizon if complete else None
            upper = max(0.0, demand + signed_error) if complete else None
            output.append(
                {
                    "prefix_days": horizon,
                    "probability": probability,
                    "issued_prefix_complete": complete,
                    "unavailable_reason": (
                        None if complete else "synthetic_operational_forecast_unavailable_in_prefix"
                    ),
                    "demand_value": demand,
                    "signed_error_quantile": signed_error,
                    "upper_turnover_value": upper,
                    "safety_stock_value": upper - demand if complete else None,
                    "target_value": upper,
                    "units": "synthetic_retail_equivalent_turnover_value",
                    "schedule_assumption_flag": True,
                    "evidence_kind": EVIDENCE_KIND,
                }
            )
    return output


def _uncertainty_views(forecast_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    forecast_index = {
        (row["store_id"], row["forecast_origin"], row["horizon"]): row for row in forecast_rows
    }
    for fit in FIT_PAIRINGS:
        for store_id in STORE_IDS:
            origin = fit["forecast_origin"]
            forecasts = [forecast_index[(store_id, origin, horizon)] for horizon in HORIZONS]
            daily = [interval for row in forecasts for interval in _daily_intervals(row)]
            cumulative = _cumulative_uncertainty(forecasts)
            output.append(
                {
                    "store_id": store_id,
                    "forecast_origin": origin,
                    "fit_id": fit["fit_id"],
                    "state": "available",
                    "unavailable_reason": None,
                    "interpretation": (
                        "Fixed synthetic display bands and buffers; no fitted model or empirical "
                        "calibration."
                    ),
                    "daily_intervals": daily,
                    "cumulative_uncertainty": cumulative,
                    "evidence_kind": EVIDENCE_KIND,
                }
            )
    return output


def _candidate_prediction(
    candidate_id: str, store_id: int, origin_index: int, horizon: int, target: date
) -> int:
    base = 8400 + store_id * 16 + target.weekday() * 215 + origin_index * 83 + horizon * 29
    adjustment = {CANDIDATE_IDS[0]: -180, CANDIDATE_IDS[1]: 0, CANDIDATE_IDS[2]: 145}[candidate_id]
    return max(0, base + adjustment)


def _comparison_basis(
    history_rows: list[dict[str, Any]], forecast_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    history = {(row["store_id"], row["date"]): row for row in history_rows}
    output = []
    for forecast in forecast_rows:
        key = (forecast["store_id"], forecast["date"])
        historical = history.get(key)
        if historical is None:
            label_state = "missing_date"
            sales_value = None
        elif historical["synthetic_open"] is None:
            label_state = "unknown_synthetic_open"
            sales_value = None
        elif not historical["synthetic_open"]:
            label_state = "synthetic_closed"
            sales_value = historical["sales_value"]
        elif historical["sales_value"] is None:
            label_state = "missing_sales"
            sales_value = None
        else:
            label_state = "eligible"
            sales_value = historical["sales_value"]
        target_date = date.fromisoformat(forecast["date"])
        origin_index = FORECAST_ORIGINS.index(forecast["forecast_origin"])
        output.append(
            {
                "store_id": forecast["store_id"],
                "forecast_origin": forecast["forecast_origin"],
                "date": forecast["date"],
                "horizon": forecast["horizon"],
                "label_state": label_state,
                "metric_eligible": label_state == "eligible",
                "synthetic_sales_value": sales_value,
                "candidate_predictions": [
                    {
                        "candidate_id": candidate_id,
                        "forecast_value": _candidate_prediction(
                            candidate_id,
                            forecast["store_id"],
                            origin_index,
                            forecast["horizon"],
                            target_date,
                        ),
                    }
                    for candidate_id in CANDIDATE_IDS
                ],
                "evidence_kind": EVIDENCE_KIND,
            }
        )
    return output


def _metric_values(rows: list[dict[str, Any]], candidate_id: str) -> dict[str, tuple[float, float]]:
    eligible = [row for row in rows if row["metric_eligible"]]
    absolute_errors = []
    squared_errors = []
    percent_errors = []
    actual_sum = 0.0
    for row in eligible:
        prediction = next(
            item["forecast_value"]
            for item in row["candidate_predictions"]
            if item["candidate_id"] == candidate_id
        )
        actual = row["synthetic_sales_value"]
        error = abs(actual - prediction)
        absolute_errors.append(error)
        squared_errors.append(error * error)
        actual_sum += actual
        if actual > 0:
            percent_errors.append(error / actual * 100.0)
    count = len(eligible)
    return {
        "mae": (sum(absolute_errors), float(count)),
        "rmse": (sum(squared_errors), float(count)),
        "mape": (sum(percent_errors), float(len(percent_errors))),
        "wape": (sum(absolute_errors), actual_sum),
    }


def _metric_row_value(metric: str, numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    if metric == "rmse":
        return math.sqrt(numerator / denominator)
    return numerator / denominator if metric != "mape" else numerator / denominator


def _comparison_metric_rows(basis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specifications: list[tuple[str, int | None, int | None, int | None, int | None]] = [
        ("pooled", None, None, None, None),
        *(("horizon", horizon, None, None, None) for horizon in HORIZONS),
        ("week_block", None, 1, 7, None),
        ("week_block", None, 8, 14, None),
        *(("store", None, None, None, store_id) for store_id in STORE_IDS),
    ]
    output: list[dict[str, Any]] = []
    for candidate_id in CANDIDATE_IDS:
        for scope, horizon, block_start, block_end, store_id in specifications:
            selected = [
                row
                for row in basis_rows
                if (horizon is None or row["horizon"] == horizon)
                and (block_start is None or block_start <= row["horizon"] <= block_end)
                and (store_id is None or row["store_id"] == store_id)
            ]
            metrics = MODEL_METRICS if scope == "pooled" else ("mae",)
            values = _metric_values(selected, candidate_id)
            paired = _metric_values(selected, CANDIDATE_IDS[0])["mae"]
            paired_mae = _metric_row_value("mae", *paired)
            candidate_mae = _metric_row_value("mae", *values["mae"])
            delta = (
                candidate_mae - paired_mae
                if candidate_mae is not None and paired_mae is not None
                else None
            )
            fraction = delta / paired_mae if delta is not None and paired_mae else None
            for metric in metrics:
                numerator, denominator = values[metric]
                value = _metric_row_value(metric, numerator, denominator)
                output.append(
                    {
                        "candidate_id": candidate_id,
                        "population": "synthetic_open_label_rows",
                        "paired_with": None
                        if candidate_id == CANDIDATE_IDS[0]
                        else CANDIDATE_IDS[0],
                        "scope": scope,
                        "validation_window": "synthetic_display_panel",
                        "horizon": horizon,
                        "week_block_start_horizon": block_start,
                        "week_block_end_horizon": block_end,
                        "store_id": store_id,
                        "metric": metric,
                        "value": value,
                        "numerator": numerator,
                        "denominator": denominator,
                        "unavailable_reason": (
                            None
                            if value is not None
                            else "No eligible synthetic rows for this metric."
                        ),
                        "paired_mae_delta": delta,
                        "paired_mae_change_fraction": fraction,
                        "evidence_kind": EVIDENCE_KIND,
                    }
                )
    return output


def _policy_measurements(
    cost: int | None,
    demand: int | None,
    unmet: int | None,
    average_inventory: int | None,
    terminal_on_hand: int | None,
    terminal_on_order: int | None,
    stockout_days: int | None,
    successful_cycles: int | None,
    *,
    unavailable_reason: str | None,
) -> list[dict[str, Any]]:
    if cost is None or demand is None or unmet is None:
        return [
            {
                "metric": metric,
                "numerator": None,
                "denominator": None,
                "value": None,
                "unavailable_reason": unavailable_reason,
            }
            for metric in INVENTORY_METRICS
        ]
    fulfilled = demand - unmet
    raw = {
        "SimulatedHoldingPlusShortfallCost": (cost, 1.0, float(cost)),
        "ValueFillRate": (fulfilled, demand, fulfilled / demand if demand else None),
        "PositiveDemandStockoutRate": (
            stockout_days,
            12,
            stockout_days / 12 if stockout_days is not None else None,
        ),
        "AverageInventoryValue": (
            average_inventory * 14,
            14,
            float(average_inventory),
        ),
        "UnmetTurnoverValue": (unmet, 1.0, float(unmet)),
        "CompletedPositiveDemandReceiptCycleServiceRate": (
            successful_cycles,
            4,
            successful_cycles / 4 if successful_cycles is not None else None,
        ),
        "terminal_on_hand_value": (terminal_on_hand, 1.0, float(terminal_on_hand)),
        "terminal_on_order_value": (terminal_on_order, 1.0, float(terminal_on_order)),
        "TerminalStockCostValue": (
            terminal_on_hand * 0.7,
            1.0,
            float(terminal_on_hand * 0.7),
        ),
        "OutstandingProcurementCommitment": (
            terminal_on_order * 0.7,
            1.0,
            float(terminal_on_order * 0.7),
        ),
    }
    return [
        {
            "metric": metric,
            "numerator": raw[metric][0],
            "denominator": raw[metric][1],
            "value": raw[metric][2],
            "unavailable_reason": None if raw[metric][2] is not None else "zero_denominator",
        }
        for metric in INVENTORY_METRICS
    ]


def _policy_result(
    policy_id: str,
    cost: int | None,
    demand: int | None,
    unmet: int | None,
    target: int | None,
    measurements: list[dict[str, Any]],
    *,
    matched: bool,
    unavailable_reason: str | None = None,
) -> dict[str, Any]:
    available = unavailable_reason is None
    return {
        "policy_id": policy_id,
        "episode_status": "complete" if available else "unavailable",
        "episode_complete": available,
        "target_available": available,
        "target_unavailability_reason": unavailable_reason,
        "availability_reason": unavailable_reason,
        "valid_matched_comparison": matched and available,
        "simulated_holding_plus_shortfall_cost": cost,
        "demand_total": demand,
        "fulfilled_total": demand - unmet if demand is not None and unmet is not None else None,
        "unmet_total": unmet,
        "target_value": target,
        "synthetic": True,
        "calibration_transport_valid": False,
        "schedule_assumption": "fixed_14_day_illustrative_arithmetic_no_simulation",
        "measurements": measurements,
    }


def _inventory_aggregate_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    requested = len(STORE_IDS)
    baseline_count = sum(pair["baseline"]["episode_complete"] for pair in pairs)
    forecast_count = sum(pair["forecast"]["episode_complete"] for pair in pairs)
    matched_count = sum(pair["comparable"] for pair in pairs)
    for metric in INVENTORY_METRICS:
        values: dict[str, list[dict[str, Any]]] = {"baseline": [], "forecast": []}
        for pair in pairs:
            for side in values:
                policy = pair[side]
                measurement = next(
                    item for item in policy["measurements"] if item["metric"] == metric
                )
                if measurement["value"] is not None:
                    values[side].append(measurement)
        summaries: dict[str, tuple[float | None, float | None, float | None]] = {}
        ratio_metric = metric in {
            "ValueFillRate",
            "PositiveDemandStockoutRate",
            "CompletedPositiveDemandReceiptCycleServiceRate",
        }
        mean_metric = metric == "AverageInventoryValue"
        for side in ("baseline", "forecast"):
            numerator = sum(item["numerator"] for item in values[side])
            denominator = (
                sum(item["denominator"] for item in values[side])
                if ratio_metric or mean_metric
                else 1.0
            )
            value = numerator / denominator if denominator else None
            summaries[side] = (numerator, denominator, value)
        base_n, base_d, base_v = summaries["baseline"]
        fore_n, fore_d, fore_v = summaries["forecast"]
        matched = matched_count == requested
        difference = (
            fore_v - base_v if matched and fore_v is not None and base_v is not None else None
        )
        relative = difference / base_v if difference is not None and base_v else None
        output.append(
            {
                "metric": metric,
                "requested_store_count": requested,
                "baseline_standalone_store_count": baseline_count,
                "forecast_standalone_store_count": forecast_count,
                "matched_store_count": matched_count,
                "baseline_numerator": base_n,
                "baseline_denominator": base_d,
                "forecast_numerator": fore_n,
                "forecast_denominator": fore_d,
                "baseline_value": base_v,
                "forecast_value": fore_v,
                "forecast_minus_baseline": difference,
                "forecast_minus_baseline_relative": relative,
                "relative_difference_null_reason": (
                    "zero_baseline_denominator" if difference is not None and base_v == 0 else None
                ),
                "null_reason": None if difference is not None else "unmatched_store_coverage",
                "interpretation": (
                    "Synthetic fixture arithmetic only; unmatched Store coverage is shown and "
                    "no matched aggregate is implied."
                ),
                "evidence_kind": EVIDENCE_KIND,
            }
        )
    return output


def _inventory_views() -> list[dict[str, Any]]:
    output = []
    for case_index, case_id in enumerate(CASE_IDS):
        pairs = []
        for store_index, store_id in enumerate(STORE_IDS):
            unavailable = case_index == 1 and store_id == 303
            baseline_cost = (620 if case_index == 0 else 640) + store_index * 25
            forecast_cost = (
                None
                if unavailable
                else (590 if case_index == 0 else 690)
                + store_index * (35 if case_index == 1 else 15)
            )
            demand = 14000 + store_index * 500
            baseline_unmet = 900 + store_index * 100
            forecast_unmet = None if unavailable else baseline_unmet + (100 if case_index else -100)
            baseline_measurements = _policy_measurements(
                baseline_cost,
                demand,
                baseline_unmet,
                720 + store_index * 45,
                510 + store_index * 35,
                170 + store_index * 20,
                2 + store_index,
                3,
                unavailable_reason=None,
            )
            forecast_measurements = _policy_measurements(
                forecast_cost,
                demand if not unavailable else None,
                forecast_unmet,
                780 + store_index * 35 if not unavailable else None,
                470 + store_index * 45 if not unavailable else None,
                210 + store_index * 25 if not unavailable else None,
                3 + store_index if not unavailable else None,
                2 if not unavailable else None,
                unavailable_reason="synthetic_fixture_input_unavailable" if unavailable else None,
            )
            baseline_target = 15000 + store_index * 400
            forecast_target = None if unavailable else 15800 + store_index * 375
            comparable = not unavailable
            baseline = _policy_result(
                POLICY_IDS[0],
                baseline_cost,
                demand,
                baseline_unmet,
                baseline_target,
                baseline_measurements,
                matched=comparable,
            )
            forecast = _policy_result(
                POLICY_IDS[1],
                forecast_cost,
                demand if not unavailable else None,
                forecast_unmet,
                forecast_target,
                forecast_measurements,
                matched=comparable,
                unavailable_reason=("synthetic_fixture_input_unavailable" if unavailable else None),
            )
            pairs.append(
                {
                    "store_id": store_id,
                    "comparable": comparable,
                    "forecast_minus_baseline_cost": (
                        forecast_cost - baseline_cost if comparable else None
                    ),
                    "difference_unavailable_reason": (
                        None if comparable else "synthetic_fixture_input_unavailable"
                    ),
                    "baseline": baseline,
                    "forecast": forecast,
                    "evidence_kind": EVIDENCE_KIND,
                }
            )
        output.append(
            {
                "case_id": case_id,
                "forecast_origin": "2015-06-05",
                "store_ids": list(STORE_IDS),
                "state": "available",
                "interpretation": (
                    "Fixed illustrative monetary arithmetic; no inventory simulator, physical "
                    "units, or observed stock was used."
                ),
                "policy_pairs": pairs,
                "case_level_comparisons": _inventory_aggregate_rows(pairs),
                "evidence_kind": EVIDENCE_KIND,
            }
        )
    return output


def create_demo_bundle(config: DemoConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    """Return a fresh mutable JSON-compatible payload made only from fixed fixture arithmetic."""
    if type(config.seed) is not int or config.seed != FIXED_SEED:
        raise DemoBundleError("Only the fixed approved demonstration seed is supported.")
    history = _history_rows(config)
    forecasts = _forecast_rows(config)
    basis = _comparison_basis(history, forecasts)
    comparisons = _comparison_metric_rows(basis)
    forecast_counts = {
        "catalog": 1,
        "sales_history": len(history),
        "forecast_issuance": len(forecasts),
        "forecast_uncertainty": 0,
        "model_comparison": len(comparisons),
        "inventory_comparison": sum(len(view["policy_pairs"]) for view in _inventory_views()),
    }
    inventory_views = _inventory_views()
    forecast_counts["forecast_uncertainty"] = len(
        [row for view in _uncertainty_views(forecasts) for row in view["daily_intervals"]]
    )
    catalog = {
        "scenario_catalog_state": "available",
        "inventory_case_state": "available",
        "inventory_case_ids": list(CASE_IDS),
        "scenario_catalog": [
            {
                "scenario_id": case_id,
                "family": "synthetic_inventory_example",
                "mode": "illustrative_fixed_arithmetic",
                "forecast_origin": "2015-06-05",
                "replicate": index,
                "horizon_days": 14,
                "schedule_mode": "fixed_fixture_schedule",
                "demand_basis": "synthetic_monetary_turnover_value",
                "stress_spec_id": f"{case_id}_fixture_spec",
                "calibration_transport_valid": False,
                "evidence_kind": EVIDENCE_KIND,
            }
            for index, case_id in enumerate(CASE_IDS)
        ],
        "view_availability": {
            "catalog": "available",
            "sales_history": "available",
            "forecast_issuance": "available",
            "forecast_uncertainty": "available_with_explicit_unavailable_points",
            "model_comparison": "available",
            "inventory_comparison": "available_with_one_unavailable_store_case",
        },
        "resource_readiness": [
            {
                "view_id": view_id,
                "state": "available",
                "record_count": count,
                "unavailable_reason": None,
                "evidence_kind": EVIDENCE_KIND,
            }
            for view_id, count in forecast_counts.items()
        ],
        "health_route_semantics": "process_health_is_not_bundle_or_view_readiness",
        "evidence_kind": EVIDENCE_KIND,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": RELEASE_ID,
        "evidence_kind": EVIDENCE_KIND,
        "title": "Controlled synthetic course demonstration",
        "sales_unit": "synthetic_retail_equivalent_turnover_value",
        "inventory_cost_unit": "synthetic_cost_proxy_units",
        "source_declaration": _source_declaration(),
        "limitations": _limitations(),
        "populations": _population(),
        "query_allowlist": _expected_query_allowlist(),
        "catalog": catalog,
        "history_rows": history,
        "forecast_rows": forecasts,
        "uncertainty_views": _uncertainty_views(forecasts),
        "comparison_panel": {
            "population": "synthetic_open_label_rows",
            "validation_window": "synthetic_display_panel",
            "metric_definitions": {
                "mae": "sum absolute errors / eligible synthetic Open=1 row count",
                "rmse": "sqrt(sum squared errors / eligible synthetic Open=1 row count)",
                "mape": "mean absolute percentage error * 100 over positive synthetic Sales rows",
                "wape": "sum absolute errors / sum synthetic Sales over eligible rows",
                "development_model_selection_claim": False,
            },
            "candidate_labels": [
                {
                    "candidate_id": candidate_id,
                    "label": f"Synthetic fixed path {candidate_id[-1].upper()}",
                    "generation": "fixed arithmetic; no model fit or execution",
                    "model_execution": "none",
                    "evidence_kind": EVIDENCE_KIND,
                }
                for candidate_id in CANDIDATE_IDS
            ],
            "basis_rows": basis,
            "rows": comparisons,
            "evidence_kind": EVIDENCE_KIND,
        },
        "inventory_views": inventory_views,
    }


def _row_counts(bundle: dict[str, Any]) -> dict[str, int]:
    return {
        "history_rows": len(bundle["history_rows"]),
        "forecast_rows": len(bundle["forecast_rows"]),
        "uncertainty_views": len(bundle["uncertainty_views"]),
        "daily_interval_rows": sum(
            len(view["daily_intervals"]) for view in bundle["uncertainty_views"]
        ),
        "cumulative_uncertainty_rows": sum(
            len(view["cumulative_uncertainty"]) for view in bundle["uncertainty_views"]
        ),
        "comparison_basis_rows": len(bundle["comparison_panel"]["basis_rows"]),
        "model_comparison_rows": len(bundle["comparison_panel"]["rows"]),
        "inventory_views": len(bundle["inventory_views"]),
        "inventory_policy_pairs": sum(
            len(view["policy_pairs"]) for view in bundle["inventory_views"]
        ),
        "inventory_aggregate_rows": sum(
            len(view["case_level_comparisons"]) for view in bundle["inventory_views"]
        ),
    }


def _read_sha256(path: Path) -> str | None:
    try:
        return _sha256(path.read_bytes())
    except OSError:
        return None


def _git_revision(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    revision = result.stdout.strip()
    return (
        revision
        if _HEX_256.fullmatch(revision) or re.fullmatch(r"[0-9a-f]{40}", revision)
        else None
    )


def _dependency_versions() -> dict[str, str | None]:
    packages = ("fastapi", "numpy", "pandas", "pyarrow", "streamlit")
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _manifest(
    bundle_bytes: bytes, bundle: dict[str, Any], repository_root: Path, config: DemoConfig
) -> dict[str, Any]:
    module_path = Path(__file__).resolve()
    script_path = repository_root / "scripts" / "build_public_demo_bundle.py"
    pyproject_path = repository_root / "pyproject.toml"
    lock_path = repository_root / "uv.lock"
    config_identity = _config_identity(config)
    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": RELEASE_ID,
        "evidence_kind": EVIDENCE_KIND,
        "generator": {
            "name": "rossmann_forecasting.app.demo_bundle",
            "version": "1",
            "module_sha256": _read_sha256(module_path),
            "script_sha256": _read_sha256(script_path),
            "config_sha256": _sha256(_canonical_json(config_identity)),
            "git_revision": _git_revision(repository_root),
            "git_revision_scope": "repository_HEAD;generator_hashes_identify_current_bytes",
        },
        "environment": {
            "python_version": sys.version.split()[0],
            "pyproject_sha256": _read_sha256(pyproject_path),
            "lock_sha256": _read_sha256(lock_path),
            "installed_dependencies": _dependency_versions(),
        },
        "seed": config.seed,
        "files": {
            BUNDLE_FILENAME: {"sha256": _sha256(bundle_bytes), "byte_count": len(bundle_bytes)}
        },
        "row_counts": _row_counts(bundle),
        "supported_queries": _expected_query_allowlist(),
        "approved_origins": list(FORECAST_ORIGINS),
        "horizons": list(HORIZONS),
        "populations": _population(),
        "source_declaration": _source_declaration(),
        "limitations": _limitations(),
    }


def _config_identity(config: DemoConfig) -> dict[str, Any]:
    """Return the fixed, reviewable identity for the supported synthetic generator inputs."""
    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": RELEASE_ID,
        "seed": config.seed,
        "store_ids": list(STORE_IDS),
        "origins": list(FORECAST_ORIGINS),
        "horizons": list(HORIZONS),
        "history_bounds": [HISTORY_START, HISTORY_END],
        "fit_pairings": [dict(item) for item in FIT_PAIRINGS],
    }


def generate_release_bytes(
    repository_root: Path, config: DemoConfig = DEFAULT_CONFIG
) -> tuple[bytes, bytes]:
    """Create deterministic canonical JSON bytes for the bundle and its manifest."""
    bundle = create_demo_bundle(config)
    bundle_bytes = _canonical_json(bundle)
    if len(bundle_bytes) > MAX_BUNDLE_BYTES:
        raise DemoBundleError("The generated bundle exceeds the encoded-size limit.")
    manifest_bytes = _canonical_json(_manifest(bundle_bytes, bundle, repository_root, config))
    if len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise DemoBundleError("The generated manifest exceeds the encoded-size limit.")
    return bundle_bytes, manifest_bytes


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DemoBundleError("Duplicate JSON object keys are not allowed.")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise DemoBundleError("Non-finite JSON numbers are not allowed.")


def _decode_canonical_json(content: bytes, max_bytes: int, label: str) -> Any:
    if len(content) > max_bytes:
        raise DemoBundleError(f"The {label} exceeds the encoded-size limit.")
    try:
        text = content.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite,
        )
    except DemoBundleError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise DemoBundleError(f"The {label} is not valid UTF-8 JSON.") from exc
    if _canonical_json(value) != content:
        raise DemoBundleError(f"The {label} is not canonical JSON.")
    _validate_json_scalars(value)
    return value


def _validate_json_scalars(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise DemoBundleError("The JSON nesting depth exceeds the schema limit.")
    if value is None or type(value) in (str, bool, int):
        if isinstance(value, str) and len(value) > 2048:
            raise DemoBundleError("A text field exceeds the schema limit.")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise DemoBundleError("Non-finite JSON numbers are not allowed.")
        return
    if type(value) is list:
        for item in value:
            _validate_json_scalars(item, depth + 1)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or key in _PROHIBITED_KEYS:
                raise DemoBundleError("A prohibited or invalid schema key is present.")
            _validate_json_scalars(item, depth + 1)
        return
    raise DemoBundleError("A JSON value has an unsupported scalar type.")


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != expected:
        raise DemoBundleError(f"The {label} does not match its closed schema.")
    return value


def _validate_bundle(bundle: Any) -> dict[str, Any]:
    """Require the exact bounded payload regenerated from the reviewed fixed fixture formulas."""
    if type(bundle) is not dict:
        raise DemoBundleError("The bundle root must be a JSON object.")
    expected = create_demo_bundle()
    if _canonical_json(bundle) != _canonical_json(expected):
        raise DemoBundleError(
            "The bundle differs from the fixed deterministic fixture schema and content."
        )
    return bundle


def _validate_manifest(
    manifest: Any, bundle_bytes: bytes, bundle: dict[str, Any]
) -> dict[str, Any]:
    keys = {
        "schema_version",
        "release_id",
        "evidence_kind",
        "generator",
        "environment",
        "seed",
        "files",
        "row_counts",
        "supported_queries",
        "approved_origins",
        "horizons",
        "populations",
        "source_declaration",
        "limitations",
    }
    manifest = _keys(manifest, keys, "manifest")
    if (
        manifest["schema_version"] != SCHEMA_VERSION
        or manifest["release_id"] != RELEASE_ID
        or manifest["evidence_kind"] != EVIDENCE_KIND
    ):
        raise DemoBundleError("The manifest identity is invalid.")
    if type(manifest["seed"]) is not int or manifest["seed"] != FIXED_SEED:
        raise DemoBundleError("The manifest seed is invalid.")
    generator = _keys(
        manifest["generator"],
        {
            "name",
            "version",
            "module_sha256",
            "script_sha256",
            "config_sha256",
            "git_revision",
            "git_revision_scope",
        },
        "generator identity",
    )
    if generator["name"] != "rossmann_forecasting.app.demo_bundle" or generator["version"] != "1":
        raise DemoBundleError("The generator identity is invalid.")
    if generator["git_revision_scope"] != (
        "repository_HEAD;generator_hashes_identify_current_bytes"
    ):
        raise DemoBundleError("The Git revision scope is invalid.")
    for name in ("module_sha256", "script_sha256", "config_sha256"):
        if type(generator[name]) is not str or not _HEX_256.fullmatch(generator[name]):
            raise DemoBundleError("A required generator SHA-256 identity is malformed.")
    expected_config_sha256 = _sha256(_canonical_json(_config_identity(DEFAULT_CONFIG)))
    if generator["config_sha256"] != expected_config_sha256:
        raise DemoBundleError("The generator configuration identity is inconsistent.")
    revision = generator["git_revision"]
    if revision is not None and (
        type(revision) is not str
        or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None
    ):
        raise DemoBundleError("The Git revision identity is malformed.")
    environment = _keys(
        manifest["environment"],
        {"python_version", "pyproject_sha256", "lock_sha256", "installed_dependencies"},
        "environment identity",
    )
    if type(environment["python_version"]) is not str or not re.fullmatch(
        r"\d+\.\d+\.\d+", environment["python_version"]
    ):
        raise DemoBundleError("The Python version identity is malformed.")
    for name in ("pyproject_sha256", "lock_sha256"):
        if type(environment[name]) is not str or not _HEX_256.fullmatch(environment[name]):
            raise DemoBundleError("A dependency SHA-256 identity is malformed.")
    dependencies = _keys(
        environment["installed_dependencies"],
        {"fastapi", "numpy", "pandas", "pyarrow", "streamlit"},
        "dependency identity",
    )
    if any(
        type(value) is not str
        or len(value) > _MAX_DISTRIBUTION_VERSION_LENGTH
        or _DISTRIBUTION_VERSION.fullmatch(value) is None
        for value in dependencies.values()
    ):
        raise DemoBundleError("A required installed dependency version is malformed.")
    files = _keys(manifest["files"], {BUNDLE_FILENAME}, "manifest file map")
    file_identity = _keys(files[BUNDLE_FILENAME], {"sha256", "byte_count"}, "bundle file identity")
    if type(file_identity["sha256"]) is not str or not _HEX_256.fullmatch(file_identity["sha256"]):
        raise DemoBundleError("The bundle SHA-256 identity is malformed.")
    byte_count = file_identity["byte_count"]
    if type(byte_count) is not int or not 0 <= byte_count <= MAX_BUNDLE_BYTES:
        raise DemoBundleError("The bundle byte count must be a bounded JSON integer.")
    if file_identity["sha256"] != _sha256(bundle_bytes) or byte_count != len(bundle_bytes):
        raise DemoBundleError("The bundle bytes disagree with their manifest identity.")
    if _canonical_json(manifest["row_counts"]) != _canonical_json(_row_counts(bundle)):
        raise DemoBundleError("Manifest row counts disagree with the decoded bundle.")
    expected = {
        "supported_queries": _expected_query_allowlist(),
        "approved_origins": list(FORECAST_ORIGINS),
        "horizons": list(HORIZONS),
        "populations": _population(),
        "source_declaration": _source_declaration(),
        "limitations": _limitations(),
    }
    for name, value in expected.items():
        if _canonical_json(manifest[name]) != _canonical_json(value):
            raise DemoBundleError(f"The manifest {name} identity is invalid.")
    return manifest


def verify_release_bytes(
    bundle_bytes: bytes,
    manifest_bytes: bytes,
    *,
    expected_manifest_sha256: str | None = None,
    deterministic_regeneration: bool = False,
    repository_root: Path | None = None,
) -> VerificationReport:
    """Verify exact bounded JSON files, content relationships and optional manifest pin."""
    if type(bundle_bytes) is not bytes or type(manifest_bytes) is not bytes:
        raise DemoBundleError("Release files must be immutable byte snapshots.")
    if len(bundle_bytes) > MAX_BUNDLE_BYTES or len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise DemoBundleError("A release file exceeds its encoded-size limit.")
    bundle = _decode_canonical_json(bundle_bytes, MAX_BUNDLE_BYTES, "bundle")
    bundle = _validate_bundle(bundle)
    manifest_sha = _sha256(manifest_bytes)
    if expected_manifest_sha256 is not None:
        if (
            not _HEX_256.fullmatch(expected_manifest_sha256)
            or manifest_sha != expected_manifest_sha256
        ):
            raise DemoBundleError("The manifest does not match its out-of-band SHA-256 pin.")
    manifest = _decode_canonical_json(manifest_bytes, MAX_MANIFEST_BYTES, "manifest")
    _validate_manifest(manifest, bundle_bytes, bundle)
    regenerated = False
    if deterministic_regeneration:
        if repository_root is None:
            raise DemoBundleError("Deterministic regeneration requires a repository root.")
        expected_bundle, expected_manifest = generate_release_bytes(repository_root)
        if bundle_bytes != expected_bundle or manifest_bytes != expected_manifest:
            raise DemoBundleError("The release candidate differs from deterministic regeneration.")
        regenerated = True
    return VerificationReport(
        bundle_ready=True,
        release_id=RELEASE_ID,
        evidence_kind=EVIDENCE_KIND,
        bundle_sha256=_sha256(bundle_bytes),
        manifest_sha256=manifest_sha,
        bundle_bytes=len(bundle_bytes),
        manifest_bytes=len(manifest_bytes),
        row_counts=_row_counts(bundle),
        deterministic_regeneration=regenerated,
    )


def _is_path_alias(path: Path) -> bool:
    """Detect symbolic links and Windows reparse-point aliases without following them."""
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise DemoBundleError("A controlled path component cannot be inspected safely.") from exc

    if stat.S_ISLNK(metadata.st_mode):
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None and is_junction():
        return True
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(metadata, "st_file_attributes", 0) & reparse_attribute)


def _checkout_directory(
    path: Path,
    repository_root: Path,
    *,
    allow_missing: bool,
) -> Path:
    """Resolve a directory under the trusted checkout while rejecting aliased components."""
    try:
        root = repository_root.resolve(strict=True)
        if not root.is_dir():
            raise DemoBundleError("The trusted repository root must be a directory.")
        requested = Path(os.path.abspath(path))
        relative = requested.relative_to(root)
    except DemoBundleError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise DemoBundleError(
            "The controlled path is outside the trusted repository root."
        ) from exc
    if not relative.parts:
        raise DemoBundleError("The repository root itself is not a release directory.")

    current = root
    resolved = root
    for index, part in enumerate(relative.parts):
        current = current / part
        if _is_path_alias(current):
            raise DemoBundleError("A controlled path cannot contain a symbolic or reparse alias.")
        try:
            resolved = current.resolve(strict=True)
        except FileNotFoundError:
            if not allow_missing:
                raise DemoBundleError("The release directory is missing.") from None
            resolved = current.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise DemoBundleError("The controlled path cannot be resolved safely.") from exc
        try:
            resolved.relative_to(root)
        except ValueError:
            raise DemoBundleError(
                "The resolved path escapes the trusted repository root."
            ) from None

        is_final = index == len(relative.parts) - 1
        if current.exists():
            if is_final and not current.is_dir():
                raise DemoBundleError("The controlled release path must be a directory.")
            if not is_final and not current.is_dir():
                raise DemoBundleError("A controlled path parent must be a directory.")
    return requested if allow_missing and not requested.exists() else resolved


def _release_files(release_dir: Path) -> tuple[bytes, bytes]:
    if _is_path_alias(release_dir) or not release_dir.is_dir():
        raise DemoBundleError("The release directory must be a regular directory without aliases.")
    try:
        entries = list(os.scandir(release_dir))
    except OSError as exc:
        raise DemoBundleError("The release directory cannot be inspected.") from exc
    if {entry.name for entry in entries} != {BUNDLE_FILENAME, MANIFEST_FILENAME}:
        raise DemoBundleError("The release directory must contain exactly the two approved files.")
    paths = {entry.name: release_dir / entry.name for entry in entries}
    for name, path in paths.items():
        if _is_path_alias(path) or not path.is_file():
            raise DemoBundleError("Release files must be regular files without symbolic links.")
        limit = MAX_BUNDLE_BYTES if name == BUNDLE_FILENAME else MAX_MANIFEST_BYTES
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise DemoBundleError("A release file cannot be inspected.") from exc
        if size > limit:
            raise DemoBundleError("A release file exceeds its encoded-size limit.")
    try:
        return paths[BUNDLE_FILENAME].read_bytes(), paths[MANIFEST_FILENAME].read_bytes()
    except OSError as exc:
        raise DemoBundleError("A release file cannot be read.") from exc


def verify_release_directory(
    release_dir: Path,
    *,
    expected_manifest_sha256: str | None = None,
    deterministic_regeneration: bool = False,
    repository_root: Path | None = None,
) -> VerificationReport:
    trusted_root = (
        Path(__file__).resolve().parents[3] if repository_root is None else repository_root
    )
    safe_release_dir = _checkout_directory(release_dir, trusted_root, allow_missing=False)
    bundle_bytes, manifest_bytes = _release_files(safe_release_dir)
    return verify_release_bytes(
        bundle_bytes,
        manifest_bytes,
        expected_manifest_sha256=expected_manifest_sha256,
        deterministic_regeneration=deterministic_regeneration,
        repository_root=repository_root,
    )


def _assert_output_destination(output_dir: Path, repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise DemoBundleError("The trusted repository root cannot be resolved.") from exc
    expected = root / "artifacts" / "public_demo" / RELEASE_ID
    requested = Path(os.path.abspath(output_dir))
    if os.path.normcase(str(requested)) != os.path.normcase(str(expected)):
        raise DemoBundleError("Output must be the fixed ignored public-demo release directory.")
    _checkout_directory(expected, root, allow_missing=True)
    if expected.exists() or expected.is_symlink():
        raise DemoBundleError(
            "An existing release candidate is immutable and cannot be overwritten."
        )
    git_dir = root / ".git"
    if git_dir.exists():
        tracked = subprocess.run(
            ["git", "ls-files", "-z", "--", "artifacts/public_demo"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=5,
        ).stdout
        if tracked:
            raise DemoBundleError("The controlled release output collides with tracked files.")
        for filename in (BUNDLE_FILENAME, MANIFEST_FILENAME):
            ignored = subprocess.run(
                [
                    "git",
                    "check-ignore",
                    "-q",
                    "--no-index",
                    "--",
                    "artifacts/public_demo/" + RELEASE_ID + "/" + filename,
                ],
                cwd=root,
                check=False,
                capture_output=True,
                timeout=5,
            )
            if ignored.returncode != 0:
                raise DemoBundleError("A release output file is not ignored by Git.")
    return expected


def write_release_candidate(output_dir: Path, repository_root: Path) -> VerificationReport:
    """Atomically write a new local candidate under the fixed ignored output convention."""
    target = _assert_output_destination(output_dir, repository_root)
    bundle_bytes, manifest_bytes = generate_release_bytes(repository_root)
    verify_release_bytes(bundle_bytes, manifest_bytes)
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    parent = _checkout_directory(parent, repository_root, allow_missing=False)
    staging = Path(tempfile.mkdtemp(prefix=".public-demo-candidate-", dir=parent))
    try:
        (staging / BUNDLE_FILENAME).write_bytes(bundle_bytes)
        (staging / MANIFEST_FILENAME).write_bytes(manifest_bytes)
        report = verify_release_directory(
            staging,
            expected_manifest_sha256=_sha256(manifest_bytes),
            deterministic_regeneration=True,
            repository_root=repository_root,
        )
        os.rename(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return report
