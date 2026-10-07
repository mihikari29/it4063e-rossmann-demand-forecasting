"""Origin-safe deterministic synthetic inventory scenarios.

This module creates exogenous retail-equivalent monetary context for later simulation.
It does not estimate latent demand, fit a model, or run an inventory policy.
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
from collections.abc import Iterable, Iterator, Mapping
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

SCHEMA_VERSION = "phase-9-synthetic-v1"
GENERATOR_VERSION = "phase-9-generator-v1"
MASTER_SEED = 4209
HORIZON_DAYS = 14
HISTORY_DAYS = 56
MIN_OPEN_HISTORY = 28
DEVELOPMENT_CUTOFF = date(2015, 7, 3)
ALLOWED_ORIGINS = (date(2015, 6, 5), date(2015, 6, 19))
HISTORY_COLUMNS = ("Store", "Date", "Sales", "Open")
DRAW_ROLES = (
    "SupplierLeadTime",
    "InventoryCoverageBuffer",
    "ProcurementCostRatio",
    "AnnualHoldingRate",
    "GoodwillPenaltyRate",
    "AverageUnitValue",
    "TrendEndChange",
    "PromotionResponseSlope",
    "PlannedPromoBlock",
    "PlannedDiscountDepth",
    "CommonShock",
    "StoreDateNoise",
)
WEEKDAY_FACTORS = (0.95, 0.98, 1.00, 1.02, 1.10, 1.15, 0.80)
P_GRID = ("0.90", "0.95", "0.98")
REFERENCE_P = "0.95"
FIT_BY_ORIGIN = {
    date(2015, 6, 5): "A",
    date(2015, 6, 19): "B",
}
SCENARIO_FAMILIES = (
    "synthetic_base",
    "promo_peak",
    "demand_slump",
    "trend_ramp",
    "long_lead_low_stock",
    "calendar_closure",
    "coupled_peak_delay",
    "zero_turnover",
)
HISTORICAL_FAMILY = "historical_replay_reference"


class ScenarioIntegrityError(ValueError):
    """Raised when an input, scenario or artifact violates the approved contract."""


def _field(name: str, dtype: pa.DataType, nullable: bool = False) -> pa.Field:
    return pa.field(name, dtype, nullable=nullable)


CATALOG_SCHEMA = pa.schema(
    [
        _field("scenario_id", pa.string()),
        _field("family", pa.string()),
        _field("mode", pa.string()),
        _field("forecast_origin", pa.date32()),
        _field("replicate", pa.int8()),
        _field("horizon_days", pa.int8()),
        _field("schedule_mode", pa.string()),
        _field("demand_basis", pa.string()),
        _field("stress_spec_id", pa.string()),
        _field("calibration_transport_valid", pa.bool_()),
    ]
)
ANCHOR_SCHEMA = pa.schema(
    [
        _field("Store", pa.int64()),
        _field("forecast_origin", pa.date32()),
        _field("history_start", pa.date32()),
        _field("history_end", pa.date32()),
        _field("observed_history_start", pa.date32(), True),
        _field("observed_history_end", pa.date32(), True),
        _field("observed_rows", pa.int64()),
        _field("open_rows", pa.int64()),
        _field("closed_rows", pa.int64()),
        _field("closed_positive_sales_rows", pa.int64()),
        _field("unknown_open_rows", pa.int64()),
        _field("missing_calendar_days", pa.int64()),
        _field("open_sales_sum", pa.int64()),
        _field("mean_open_sales_value", pa.float64(), True),
        _field("anchor_available", pa.bool_()),
        _field("zero_anchor", pa.bool_()),
        _field("unavailable_reason", pa.string(), True),
        _field("history_logical_sha256", pa.string()),
    ]
)
PARAMETER_SCHEMA = pa.schema(
    [
        _field("scenario_id", pa.string()),
        _field("Store", pa.int64()),
        _field("SupplierLeadTime", pa.int8()),
        _field("ReviewPeriod", pa.int8()),
        _field("ProtectionPeriod", pa.int8()),
        _field("InventoryCoverageDays", pa.int8()),
        _field("InitialStockOnHandValue", pa.float64(), True),
        _field("InitialOnOrderValue", pa.float64()),
        _field("InitialBackordersValue", pa.float64()),
        _field("InitialInventoryPositionValue", pa.float64(), True),
        _field("ProcurementCostRatio", pa.float64()),
        _field("AnnualHoldingRate", pa.float64()),
        _field("HoldingCostRate", pa.float64()),
        _field("GoodwillPenaltyRate", pa.float64()),
        _field("StockoutPenalty", pa.float64()),
        _field("AverageUnitValue", pa.float64()),
        _field("TrendEndChange", pa.float64()),
        _field("PromotionResponseSlope", pa.float64()),
        _field("PlannedPromoBlock", pa.bool_()),
        _field("PlannedDiscountDepth", pa.float64()),
        _field("initialization_available", pa.bool_()),
        _field("unavailable_reason", pa.string(), True),
    ]
)
DAILY_SCHEMA = pa.schema(
    [
        _field("scenario_id", pa.string()),
        _field("Store", pa.int64()),
        _field("Date", pa.date32()),
        _field("horizon", pa.int8()),
        _field("ScenarioOpen", pa.int8(), True),
        _field("SyntheticPromo", pa.bool_(), True),
        _field("SyntheticHolidayClosure", pa.bool_(), True),
        _field("DiscountDepth", pa.float64(), True),
        _field("WeekdayFactor", pa.float64(), True),
        _field("TrendFactor", pa.float64(), True),
        _field("PromotionFactor", pa.float64(), True),
        _field("CommonShock", pa.float64(), True),
        _field("StoreDateNoise", pa.float64(), True),
        _field("NoiseFactor", pa.float64(), True),
        _field("DemandStressFactor", pa.float64(), True),
        _field("SyntheticDemandValue", pa.float64(), True),
        _field("synthetic_demand_available", pa.bool_()),
        _field("unavailable_reason", pa.string(), True),
    ]
)

TABLE_SCHEMAS = {
    "scenario_catalog.parquet": CATALOG_SCHEMA,
    "origin_anchors.parquet": ANCHOR_SCHEMA,
    "store_parameters.parquet": PARAMETER_SCHEMA,
    "scenario_daily.parquet": DAILY_SCHEMA,
}
TABLE_KEYS = {
    "scenario_catalog.parquet": ("scenario_id",),
    "origin_anchors.parquet": ("Store", "forecast_origin"),
    "store_parameters.parquet": ("scenario_id", "Store"),
    "scenario_daily.parquet": ("scenario_id", "Store", "Date"),
}

HISTORY_LOGICAL_SCHEMA = {
    "fields": [
        {"name": "Store", "type": "int64", "nullable": False},
        {"name": "Date", "type": "date32", "nullable": False},
        {"name": "Sales", "type": "int64", "nullable": False},
        {"name": "Open", "type": "int8", "nullable": True},
    ],
    "schema_version": SCHEMA_VERSION,
}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iso(value: date | datetime | pd.Timestamp) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def _as_date(value: date | datetime | pd.Timestamp | str) -> date:
    if isinstance(value, str):
        parsed = pd.Timestamp(value)
        if parsed.tz is not None or parsed != parsed.normalize():
            raise ScenarioIntegrityError(f"Date must be a timezone-free calendar date: {value!r}.")
        return parsed.date()
    if isinstance(value, pd.Timestamp):
        if value.tz is not None or value != value.normalize():
            raise ScenarioIntegrityError(f"Date must be a timezone-free calendar date: {value!r}.")
        return value.date()
    if isinstance(value, datetime):
        if value.tzinfo is not None or value.time() != datetime.min.time():
            raise ScenarioIntegrityError(f"Date must be a timezone-free calendar date: {value!r}.")
        return value.date()
    return value


def _schema_descriptor(schema: pa.Schema) -> list[dict[str, Any]]:
    return [
        {"name": item.name, "type": str(item.type), "nullable": item.nullable} for item in schema
    ]


def _normalize_logical_value(value: Any, field: pa.Field) -> Any:
    if value is None:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if pa.types.is_floating(field.type):
        number = float(value)
        if not math.isfinite(number):
            raise ScenarioIntegrityError(f"Non-finite value in {field.name}.")
        return (0.0 if number == 0.0 else number).hex()
    if pa.types.is_date(field.type):
        return _iso(value)
    if pa.types.is_boolean(field.type):
        return bool(value)
    if pa.types.is_integer(field.type):
        return int(value)
    if pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
        return str(value)
    raise ScenarioIntegrityError(f"Unsupported logical-hash type: {field.type}.")


def _schema_line(schema: pa.Schema) -> bytes:
    payload = {"fields": _schema_descriptor(schema), "schema_version": SCHEMA_VERSION}
    return _canonical_json_bytes(payload) + b"\n"


def logical_table_sha256(table: pa.Table, key_columns: Iterable[str]) -> str:
    """Hash a key-sorted logical table independent of Parquet encoding and row input order."""
    schema = table.schema.remove_metadata()
    order = pc.sort_indices(table, sort_keys=[(name, "ascending") for name in key_columns])
    sorted_table = table.take(order)
    digest = hashlib.sha256(_schema_line(schema))
    fields = list(schema)
    for row in sorted_table.to_pylist():
        values = [_normalize_logical_value(row[field.name], field) for field in fields]
        digest.update(_canonical_json_bytes(values) + b"\n")
    return digest.hexdigest()


def _history_hash(records: list[tuple[int, date, int, int | None]]) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(HISTORY_LOGICAL_SCHEMA) + b"\n")
    for store, day, sales, open_value in sorted(records, key=lambda row: (row[0], row[1])):
        digest.update(_canonical_json_bytes([store, day.isoformat(), sales, open_value]) + b"\n")
    return digest.hexdigest()


def default_config(
    *, stores: Iterable[int] | None = None, upstream_bindings: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return the approved scenario configuration, optionally with a fixture store subset."""
    store_ids = sorted(set(stores if stores is not None else range(1, 1116)))
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "run_id": None,
        "created_at_utc": None,
        "master_seed": MASTER_SEED,
        "forecast_origins": [_iso(item) for item in ALLOWED_ORIGINS],
        "stores": store_ids,
        "replicates": [0, 1, 2, 3, 4],
        "horizon_days": HORIZON_DAYS,
        "history_days": HISTORY_DAYS,
        "minimum_open_history_rows": MIN_OPEN_HISTORY,
        "draw_algorithm": "sha256-counter-uniform-v1",
        "draw_roles": list(DRAW_ROLES),
        "value_basis": "retail_equivalent_monetary_sales_turnover",
        "initialization": {
            "history_window": "[origin-55, origin] inclusive",
            "anchor": "mean of observed Open=1 Sales with integer sum and 28-row minimum",
            "coverage": "SupplierLeadTime + ReviewPeriod + discrete buffer",
            "initial_on_order_value": 0,
            "initial_backorders_value": 0,
            "missing_dates": "preserve; never impute",
            "zero_anchor": "valid; preserve",
        },
        "parameter_ranges": {
            "SupplierLeadTime": [2, 7],
            "ReviewPeriod": [1, 1],
            "ProtectionPeriod": [3, 8],
            "InventoryCoverageBuffer": [0, 3],
            "InventoryCoverageDays": [1, 11],
            "ProcurementCostRatio": [0.55, 0.85],
            "AnnualHoldingRate": [0.10, 0.30],
            "GoodwillPenaltyRate": [0.10, 0.75],
            "AverageUnitValue": [5, 50],
            "TrendEndChange": [-0.10, 0.30],
            "PromotionResponseSlope": [0.5, 1.5],
            "PlannedDiscountDepth": [0.0, 0.40],
            "CommonShock": [-0.10, 0.10],
            "StoreDateNoise": [-0.15, 0.15],
            "DemandStressFactor": [0.0, 2.0],
            "combined_factor_maximum": 6.0,
        },
        "discrete_values": {
            "SupplierLeadTime": [2, 3, 4, 5, 6, 7],
            "InventoryCoverageBuffer": [0, 1, 2, 3],
            "AverageUnitValue": [5, 10, 20, 50],
        },
        "weekday_factors_monday_to_sunday": list(WEEKDAY_FACTORS),
        "weekday_factor_note": (
            "Mean 1 over seven days; mean 1.033333... over the default Monday-Saturday open days; "
            "illustrative and not normalized to preserve the historical anchor."
        ),
        "promotion_block": {"base_horizons": [4, 5, 6], "probability": 0.40},
        "scenario_families": list(SCENARIO_FAMILIES),
        "scenario_overrides": {
            "promo_peak": {"promo_horizons": [4, 5, 6, 7, 8], "discount": 0.40, "stress": 1.50},
            "demand_slump": {"stress": 0.25},
            "trend_ramp": {"trend_end_change": 0.30},
            "long_lead_low_stock": {"lead_time": 7, "protection_period": 8, "coverage": 1},
            "calendar_closure": {"closure_horizon": 8, "reopening_horizon": 10, "stress": 1.50},
            "coupled_peak_delay": {
                "lead_time": 7,
                "protection_period": 8,
                "coverage": 1,
                "trend_end_change": 0.30,
                "promo_horizons": [4, 5, 6, 7, 8],
                "discount": 0.40,
                "stress": 2.0,
            },
            "zero_turnover": {"stress": 0.0},
        },
        "common_random_numbers": (
            "Scenario family and policy names are excluded from keys; deterministic overrides "
            "are applied after shared draws."
        ),
        "cost_conventions": {
            "procurement_cost": "ProcurementCostRatio * retail_equivalent_value",
            "holding_cost_rate": "ProcurementCostRatio * AnnualHoldingRate / 365",
            "stockout_penalty": "(1 - ProcurementCostRatio) + GoodwillPenaltyRate",
            "equivalent_units": "display only; no rounding or quantity constraints",
        },
        "schedule_conventions": {
            "synthetic_default": "Monday-Saturday open, Sunday closed",
            "historical_reference": "saved source Open assumed known at origin, conditional only",
            "unknown_open": "preserve as unavailable",
        },
        "uncertainty_reference": {
            "canonical_run_id": "phase8-impl-20261006-provenance-review",
            "p_grid": list(P_GRID),
            "reference_p": REFERENCE_P,
            "suffix_supported": False,
        },
        "approval_reference": "ADR-022; Phase 9 design external ACCEPT 2026-10-07",
        "upstream_bindings": dict(upstream_bindings or {}),
        "config_canonical_sha256": None,
    }


def _validate_config(config: Mapping[str, Any], *, canonical_run: bool = False) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ScenarioIntegrityError("Unsupported scenario schema version.")
    if config.get("generator_version") != GENERATOR_VERSION:
        raise ScenarioIntegrityError("Unsupported generator version.")
    if config.get("master_seed") != MASTER_SEED:
        raise ScenarioIntegrityError("Master seed must be 4209.")
    if config.get("draw_algorithm") != "sha256-counter-uniform-v1":
        raise ScenarioIntegrityError("The approved SHA-256 counter draw algorithm is required.")
    if config.get("draw_roles") != list(DRAW_ROLES):
        raise ScenarioIntegrityError("Draw role names or order differ from ADR-022.")
    if config.get("horizon_days") != HORIZON_DAYS or config.get("history_days") != HISTORY_DAYS:
        raise ScenarioIntegrityError("Phase 9 requires H14 and exactly 56 calendar history days.")
    if config.get("minimum_open_history_rows") != MIN_OPEN_HISTORY:
        raise ScenarioIntegrityError("The Open=1 history threshold must be exactly 28 rows.")
    origins = tuple(_as_date(value) for value in config.get("forecast_origins", []))
    if origins != ALLOWED_ORIGINS:
        raise ScenarioIntegrityError("Only the June 5 and June 19 development origins are allowed.")
    if any((origin + timedelta(days=HORIZON_DAYS)) > DEVELOPMENT_CUTOFF for origin in origins):
        raise ScenarioIntegrityError("An H14 target extends beyond 2015-07-03.")
    stores = config.get("stores")
    if (
        not isinstance(stores, list)
        or not stores
        or any(type(store) is not int or store < 1 for store in stores)
        or stores != sorted(set(stores))
    ):
        raise ScenarioIntegrityError("Configured Stores must be sorted unique positive integers.")
    replicates = config.get("replicates")
    if replicates != [0, 1, 2, 3, 4]:
        raise ScenarioIntegrityError("Exactly five paired replicates 0..4 are required.")
    if config.get("weekday_factors_monday_to_sunday") != list(WEEKDAY_FACTORS):
        raise ScenarioIntegrityError("Approved weekday factors cannot be normalized or changed.")
    if config.get("scenario_families") != list(SCENARIO_FAMILIES):
        raise ScenarioIntegrityError("The approved eight synthetic scenario families are required.")
    if canonical_run and stores != list(range(1, 1116)):
        raise ScenarioIntegrityError(
            "Canonical development run requires configured Stores 1..1115."
        )


def keyed_digest(
    replicate: int,
    forecast_origin: date | str,
    scope: list[Any],
    role: str,
    counter: int = 0,
) -> bytes:
    """Return the exact version-1 SHA-256 digest for an approved draw key."""
    origin = _iso(_as_date(forecast_origin))
    if role not in DRAW_ROLES or not 0 <= replicate <= 4 or counter < 0:
        raise ScenarioIntegrityError("Invalid SHA-256 draw key component.")
    key = [SCHEMA_VERSION, MASTER_SEED, replicate, origin, scope, role, counter]
    return hashlib.sha256(_canonical_json_bytes(key)).digest()


def keyed_uniform(
    replicate: int,
    forecast_origin: date | str,
    scope: list[Any],
    role: str,
    *,
    low: float = 0.0,
    high: float = 1.0,
) -> float:
    if not math.isfinite(low) or not math.isfinite(high) or high < low:
        raise ScenarioIntegrityError("Invalid continuous draw interval.")
    digest = keyed_digest(replicate, forecast_origin, scope, role, 0)
    z = int.from_bytes(digest[:8], "big", signed=False)
    u = (z >> 11) / (2**53)
    return low + (high - low) * u


def keyed_discrete(
    replicate: int,
    forecast_origin: date | str,
    scope: list[Any],
    role: str,
    values: Iterable[int],
) -> int:
    choices = tuple(values)
    if not choices:
        raise ScenarioIntegrityError("A discrete draw requires at least one ordered value.")
    limit = 2**64 - (2**64 % len(choices))
    for counter in range(100):
        digest = keyed_digest(replicate, forecast_origin, scope, role, counter)
        z = int.from_bytes(digest[:8], "big", signed=False)
        if z < limit:
            return int(choices[z % len(choices)])
    raise ScenarioIntegrityError("Discrete SHA-256 rejection sampling exceeded 100 attempts.")


def validate_history_frame(
    history: pd.DataFrame, *, origin: date | str, stores: Iterable[int]
) -> pd.DataFrame:
    """Validate an already-projected origin window without filtering exposed future rows."""
    scenario_origin = _as_date(origin)
    if scenario_origin not in ALLOWED_ORIGINS:
        raise ScenarioIntegrityError("History was requested for an unapproved origin.")
    if tuple(history.columns) != HISTORY_COLUMNS:
        raise ScenarioIntegrityError(
            "History projection must contain exactly "
            f"{HISTORY_COLUMNS}; got {tuple(history.columns)}."
        )
    store_set = set(stores)
    frame = history.copy(deep=True)
    if frame.empty:
        return pd.DataFrame(
            {
                "Store": pd.Series(dtype="int64"),
                "Date": pd.Series(dtype="object"),
                "Sales": pd.Series(dtype="int64"),
                "Open": pd.Series(dtype="object"),
            }
        )
    store_values = pd.to_numeric(frame["Store"], errors="raise")
    if store_values.isna().any() or (store_values % 1 != 0).any():
        raise ScenarioIntegrityError("Store identifiers must be positive exact integers.")
    if (store_values <= 0).any() or (~store_values.isin(store_set)).any():
        raise ScenarioIntegrityError("History contains a Store outside the configured universe.")
    try:
        date_values = pd.to_datetime(frame["Date"], errors="raise")
    except (TypeError, ValueError) as error:
        raise ScenarioIntegrityError("History Date values are invalid.") from error
    if (
        getattr(date_values.dt, "tz", None) is not None
        or date_values.ne(date_values.dt.normalize()).any()
    ):
        raise ScenarioIntegrityError("History Date values must be timezone-free calendar dates.")
    start = scenario_origin - timedelta(days=HISTORY_DAYS - 1)
    if (
        date_values.lt(pd.Timestamp(start)).any()
        or date_values.gt(pd.Timestamp(scenario_origin)).any()
    ):
        raise ScenarioIntegrityError(
            "In-memory history contains rows outside the exact origin window."
        )
    sales = pd.to_numeric(frame["Sales"], errors="raise")
    if sales.isna().any() or (~np.isfinite(sales.to_numpy(dtype="float64"))).any():
        raise ScenarioIntegrityError("Observed Sales must be present and finite.")
    if (sales < 0).any() or (sales % 1 != 0).any():
        raise ScenarioIntegrityError("Observed Sales must be nonnegative exact integers.")
    open_values = frame["Open"]
    legal_open = open_values.isna() | open_values.isin((0, 1))
    if not legal_open.all():
        raise ScenarioIntegrityError("Open must contain only 0, 1 or null.")
    normalized = pd.DataFrame(
        {
            "Store": store_values.astype("int64"),
            "Date": date_values.dt.date,
            "Sales": sales.astype("int64"),
        }
    )
    normalized["Open"] = pd.Series(
        [None if pd.isna(value) else int(value) for value in open_values],
        index=normalized.index,
        dtype="object",
    )
    if normalized.duplicated(["Store", "Date"]).any():
        raise ScenarioIntegrityError("History contains duplicate Store-Date keys.")
    return normalized.sort_values(["Store", "Date"], kind="mergesort").reset_index(drop=True)


def read_censored_history(
    train_path: str | Path, *, origin: date | str, stores: Iterable[int]
) -> pd.DataFrame:
    """Push Store and exact 56-day Date predicates into Arrow before materializing rows."""
    scenario_origin = _as_date(origin)
    if scenario_origin not in ALLOWED_ORIGINS:
        raise ScenarioIntegrityError("Unsupported origin; refusing to open history input.")
    if scenario_origin + timedelta(days=HORIZON_DAYS) > DEVELOPMENT_CUTOFF:
        raise ScenarioIntegrityError("Forecast target exceeds the development cutoff.")
    store_ids = sorted(set(int(store) for store in stores))
    if not store_ids or any(store < 1 for store in store_ids):
        raise ScenarioIntegrityError("At least one positive configured Store is required.")
    path = Path(train_path)
    dataset = ds.dataset(path, format="parquet")
    missing = set(HISTORY_COLUMNS).difference(dataset.schema.names)
    if missing:
        raise ScenarioIntegrityError(
            f"Prepared history is missing projected columns: {sorted(missing)}."
        )
    date_type = dataset.schema.field("Date").type
    start = scenario_origin - timedelta(days=HISTORY_DAYS - 1)
    start_scalar = pa.scalar(datetime.combine(start, datetime.min.time()), type=date_type)
    end_scalar = pa.scalar(datetime.combine(scenario_origin, datetime.min.time()), type=date_type)
    predicate = (
        (ds.field("Date") >= start_scalar)
        & (ds.field("Date") <= end_scalar)
        & ds.field("Store").isin(store_ids)
    )
    table = dataset.to_table(columns=list(HISTORY_COLUMNS), filter=predicate, use_threads=False)
    result = table.to_pandas()
    return validate_history_frame(result, origin=scenario_origin, stores=store_ids)


def compute_origin_anchors(
    history: pd.DataFrame, *, origin: date | str, stores: Iterable[int]
) -> pa.Table:
    """Create one complete 56-day anchor evidence row for each configured Store."""
    scenario_origin = _as_date(origin)
    store_ids = sorted(set(stores))
    frame = validate_history_frame(history, origin=scenario_origin, stores=store_ids)
    start = scenario_origin - timedelta(days=HISTORY_DAYS - 1)
    rows: list[dict[str, Any]] = []
    groups = {int(store): group for store, group in frame.groupby("Store", sort=False)}
    for store in store_ids:
        group = groups.get(store)
        if group is None:
            group = frame.iloc[0:0]
        records = [
            (int(item.Store), item.Date, int(item.Sales), item.Open)
            for item in group.itertuples(index=False)
        ]
        observed = len(records)
        opens = group.loc[group["Open"].eq(1)]
        closed = group.loc[group["Open"].eq(0)]
        unknown = group.loc[group["Open"].isna()]
        open_rows = int(len(opens))
        sales_sum = int(opens["Sales"].sum()) if open_rows else 0
        available = open_rows >= MIN_OPEN_HISTORY
        mean_value = float(sales_sum / open_rows) if available else None
        reason = (
            None
            if available
            else ("no_store_history" if observed == 0 else "insufficient_open_history")
        )
        rows.append(
            {
                "Store": store,
                "forecast_origin": scenario_origin,
                "history_start": start,
                "history_end": scenario_origin,
                "observed_history_start": min((item[1] for item in records), default=None),
                "observed_history_end": max((item[1] for item in records), default=None),
                "observed_rows": observed,
                "open_rows": open_rows,
                "closed_rows": int(len(closed)),
                "closed_positive_sales_rows": int((closed["Sales"] > 0).sum()),
                "unknown_open_rows": int(len(unknown)),
                "missing_calendar_days": HISTORY_DAYS - observed,
                "open_sales_sum": sales_sum,
                "mean_open_sales_value": mean_value,
                "anchor_available": available,
                "zero_anchor": bool(available and mean_value == 0.0),
                "unavailable_reason": reason,
                "history_logical_sha256": _history_hash(records),
            }
        )
    return pa.Table.from_pylist(rows, schema=ANCHOR_SCHEMA)


def _catalog_rows(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    origins = tuple(_as_date(value) for value in config["forecast_origins"])
    rows: list[dict[str, Any]] = []
    for origin in origins:
        rows.append(
            {
                "scenario_id": f"{HISTORICAL_FAMILY}-{origin:%Y%m%d}-r00",
                "family": HISTORICAL_FAMILY,
                "mode": "historical_replay",
                "forecast_origin": origin,
                "replicate": 0,
                "horizon_days": HORIZON_DAYS,
                "schedule_mode": "conditional_saved_source_open_reference",
                "demand_basis": "historical_observed_sales_reference",
                "stress_spec_id": HISTORICAL_FAMILY,
                "calibration_transport_valid": True,
            }
        )
        for family in SCENARIO_FAMILIES:
            for replicate in config["replicates"]:
                rows.append(
                    {
                        "scenario_id": f"{family}-{origin:%Y%m%d}-r{replicate:02d}",
                        "family": family,
                        "mode": "synthetic_stress",
                        "forecast_origin": origin,
                        "replicate": replicate,
                        "horizon_days": HORIZON_DAYS,
                        "schedule_mode": "synthetic_planned_weekly_v1",
                        "demand_basis": "synthetic_turnover_proxy",
                        "stress_spec_id": family,
                        "calibration_transport_valid": False,
                    }
                )
    return sorted(rows, key=lambda row: row["scenario_id"])


def create_scenario_catalog(config: Mapping[str, Any]) -> pa.Table:
    _validate_config(config)
    return pa.Table.from_pylist(_catalog_rows(config), schema=CATALOG_SCHEMA)


def _draw_cache(
    config: Mapping[str, Any],
) -> tuple[dict[tuple[Any, ...], dict[str, Any]], dict[tuple[Any, ...], float]]:
    parameters: dict[tuple[Any, ...], dict[str, Any]] = {}
    shocks: dict[tuple[Any, ...], float] = {}
    for origin_value in config["forecast_origins"]:
        origin = _as_date(origin_value)
        future_dates = [origin + timedelta(days=h) for h in range(1, HORIZON_DAYS + 1)]
        for replicate in config["replicates"]:
            for day in future_dates:
                shocks[(origin, replicate, day)] = keyed_uniform(
                    replicate,
                    origin,
                    ["date", day.isoformat()],
                    "CommonShock",
                    low=-0.10,
                    high=0.10,
                )
            for store in config["stores"]:
                scope = ["store", store]
                lead = keyed_discrete(replicate, origin, scope, "SupplierLeadTime", range(2, 8))
                buffer = keyed_discrete(
                    replicate, origin, scope, "InventoryCoverageBuffer", range(0, 4)
                )
                parameters[(origin, replicate, store)] = {
                    "SupplierLeadTime": lead,
                    "InventoryCoverageBuffer": buffer,
                    "ProcurementCostRatio": keyed_uniform(
                        replicate, origin, scope, "ProcurementCostRatio", low=0.55, high=0.85
                    ),
                    "AnnualHoldingRate": keyed_uniform(
                        replicate, origin, scope, "AnnualHoldingRate", low=0.10, high=0.30
                    ),
                    "GoodwillPenaltyRate": keyed_uniform(
                        replicate, origin, scope, "GoodwillPenaltyRate", low=0.10, high=0.75
                    ),
                    "AverageUnitValue": keyed_discrete(
                        replicate, origin, scope, "AverageUnitValue", (5, 10, 20, 50)
                    ),
                    "TrendEndChange": keyed_uniform(
                        replicate, origin, scope, "TrendEndChange", low=-0.10, high=0.10
                    ),
                    "PromotionResponseSlope": keyed_uniform(
                        replicate, origin, scope, "PromotionResponseSlope", low=0.5, high=1.5
                    ),
                    "PlannedPromoBlock": keyed_uniform(
                        replicate, origin, scope, "PlannedPromoBlock"
                    )
                    < 0.40,
                    "PlannedDiscountDepth": keyed_uniform(
                        replicate, origin, scope, "PlannedDiscountDepth", low=0.05, high=0.30
                    ),
                }
                for day in future_dates:
                    shocks[(origin, replicate, store, day)] = keyed_uniform(
                        replicate,
                        origin,
                        ["store_date", store, day.isoformat()],
                        "StoreDateNoise",
                        low=-0.15,
                        high=0.15,
                    )
    return parameters, shocks


def synthetic_demand_value(
    mean_open_sales: float | None,
    scenario_open: int | None,
    *,
    weekday_factor: float,
    trend_factor: float,
    promotion_factor: float,
    noise_factor: float,
    demand_stress_factor: float,
    anchor_available: bool = True,
    unavailable_reason: str | None = None,
) -> tuple[float | None, str | None]:
    """Apply the approved ordered multiplications while preserving closure and unknowns."""
    if not anchor_available or mean_open_sales is None:
        return None, unavailable_reason or "insufficient_open_history"
    if scenario_open is None:
        return None, "unknown_scenario_open"
    if scenario_open not in (0, 1):
        raise ScenarioIntegrityError("ScenarioOpen must be 0, 1 or null.")
    if scenario_open == 0:
        return 0.0, None
    value = (
        (((mean_open_sales * weekday_factor) * trend_factor) * promotion_factor) * noise_factor
    ) * demand_stress_factor
    if not math.isfinite(value) or value < 0:
        raise ScenarioIntegrityError("Synthetic demand must be finite and nonnegative.")
    return float(value), None


def initial_stock_on_hand_value(mean_open_sales: float | None, coverage_days: int) -> float | None:
    if mean_open_sales is None:
        return None
    if not math.isfinite(mean_open_sales) or mean_open_sales < 0 or coverage_days < 1:
        raise ScenarioIntegrityError("Initial stock inputs must be finite and nonnegative.")
    return float(mean_open_sales * coverage_days)


def holding_cost_rate(procurement_ratio: float, annual_holding_rate: float) -> float:
    return procurement_ratio * annual_holding_rate / 365


def stockout_penalty(procurement_ratio: float, goodwill_penalty_rate: float) -> float:
    return (1.0 - procurement_ratio) + goodwill_penalty_rate


def _anchor_lookup(anchor_table: pa.Table) -> dict[tuple[int, date], dict[str, Any]]:
    return {(int(row["Store"]), row["forecast_origin"]): row for row in anchor_table.to_pylist()}


def _scenario_parameter_rows(
    scenario: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    anchor_by_key: Mapping[tuple[int, date], Mapping[str, Any]],
    random_parameters: Mapping[tuple[Any, ...], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    family = scenario["family"]
    origin = scenario["forecast_origin"]
    replicate = int(scenario["replicate"])
    random_replicate = 0 if family == HISTORICAL_FAMILY else replicate
    rows: list[dict[str, Any]] = []
    for store in config["stores"]:
        base = random_parameters[(origin, random_replicate, store)]
        lead = (
            7
            if family in {"long_lead_low_stock", "coupled_peak_delay"}
            else base["SupplierLeadTime"]
        )
        review = 1
        protection = lead + review
        coverage = (
            1
            if family in {"long_lead_low_stock", "coupled_peak_delay"}
            else lead + review + base["InventoryCoverageBuffer"]
        )
        anchor = anchor_by_key[(store, origin)]
        available = bool(anchor["anchor_available"])
        mean_value = anchor["mean_open_sales_value"]
        initial_stock = initial_stock_on_hand_value(mean_value, coverage) if available else None
        procurement_ratio = float(base["ProcurementCostRatio"])
        annual_rate = float(base["AnnualHoldingRate"])
        goodwill_rate = float(base["GoodwillPenaltyRate"])
        end_change = (
            0.30 if family in {"trend_ramp", "coupled_peak_delay"} else base["TrendEndChange"]
        )
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "Store": store,
                "SupplierLeadTime": lead,
                "ReviewPeriod": review,
                "ProtectionPeriod": protection,
                "InventoryCoverageDays": coverage,
                "InitialStockOnHandValue": initial_stock,
                "InitialOnOrderValue": 0.0,
                "InitialBackordersValue": 0.0,
                "InitialInventoryPositionValue": initial_stock,
                "ProcurementCostRatio": procurement_ratio,
                "AnnualHoldingRate": annual_rate,
                "HoldingCostRate": holding_cost_rate(procurement_ratio, annual_rate),
                "GoodwillPenaltyRate": goodwill_rate,
                "StockoutPenalty": stockout_penalty(procurement_ratio, goodwill_rate),
                "AverageUnitValue": float(base["AverageUnitValue"]),
                "TrendEndChange": float(end_change),
                "PromotionResponseSlope": float(base["PromotionResponseSlope"]),
                "PlannedPromoBlock": bool(base["PlannedPromoBlock"]),
                "PlannedDiscountDepth": float(base["PlannedDiscountDepth"]),
                "initialization_available": available,
                "unavailable_reason": anchor["unavailable_reason"],
            }
        )
    return rows


def _scenario_daily_rows(
    scenario: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    anchor_by_key: Mapping[tuple[int, date], Mapping[str, Any]],
    parameter_by_key: Mapping[tuple[str, int], Mapping[str, Any]],
    random_shocks: Mapping[tuple[Any, ...], float],
) -> list[dict[str, Any]]:
    family = scenario["family"]
    origin = scenario["forecast_origin"]
    replicate = int(scenario["replicate"])
    random_replicate = 0 if family == HISTORICAL_FAMILY else replicate
    rows: list[dict[str, Any]] = []
    for store in config["stores"]:
        anchor = anchor_by_key[(store, origin)]
        parameters = parameter_by_key[(scenario["scenario_id"], store)]
        for horizon in range(1, HORIZON_DAYS + 1):
            day = origin + timedelta(days=horizon)
            if family == HISTORICAL_FAMILY:
                rows.append(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "Store": store,
                        "Date": day,
                        "horizon": horizon,
                        "ScenarioOpen": None,
                        "SyntheticPromo": None,
                        "SyntheticHolidayClosure": None,
                        "DiscountDepth": None,
                        "WeekdayFactor": None,
                        "TrendFactor": None,
                        "PromotionFactor": None,
                        "CommonShock": None,
                        "StoreDateNoise": None,
                        "NoiseFactor": None,
                        "DemandStressFactor": None,
                        "SyntheticDemandValue": None,
                        "synthetic_demand_available": False,
                        "unavailable_reason": "historical_outcomes_not_loaded",
                    }
                )
                continue

            holiday_closure = family == "calendar_closure" and horizon == 8
            scenario_open = int(day.weekday() < 6 and not holiday_closure)
            if family in {"promo_peak", "coupled_peak_delay"}:
                synthetic_promo = horizon in (4, 5, 6, 7, 8)
                discount = 0.40 if synthetic_promo else 0.0
            else:
                synthetic_promo = bool(parameters["PlannedPromoBlock"] and horizon in (4, 5, 6))
                discount = float(parameters["PlannedDiscountDepth"]) if synthetic_promo else 0.0
            if family == "demand_slump":
                stress = 0.25
            elif family == "promo_peak":
                stress = 1.50 if horizon in (4, 5, 6, 7, 8) else 1.0
            elif family == "calendar_closure":
                stress = 1.50 if horizon == 10 else 1.0
            elif family == "coupled_peak_delay":
                stress = 2.0 if horizon in (4, 5, 6, 7, 8) else 1.0
            elif family == "zero_turnover":
                stress = 0.0
            else:
                stress = 1.0

            weekday = WEEKDAY_FACTORS[day.weekday()]
            trend = 1.0 + float(parameters["TrendEndChange"]) * horizon / HORIZON_DAYS
            promotion = 1.0 + float(parameters["PromotionResponseSlope"]) * discount
            common = float(random_shocks[(origin, random_replicate, day)])
            store_noise = float(random_shocks[(origin, random_replicate, store, day)])
            noise_factor = 1.0 + common + store_noise
            combined = (((weekday * trend) * promotion) * noise_factor) * stress
            if any(
                not math.isfinite(item)
                for item in (weekday, trend, promotion, common, store_noise, noise_factor, stress)
            ):
                raise ScenarioIntegrityError("Scenario factors must be finite.")
            if combined > 6.0 + 1e-12:
                raise ScenarioIntegrityError("Combined synthetic demand factor exceeds 6.0.")
            demand, reason = synthetic_demand_value(
                anchor["mean_open_sales_value"],
                scenario_open,
                weekday_factor=weekday,
                trend_factor=trend,
                promotion_factor=promotion,
                noise_factor=noise_factor,
                demand_stress_factor=stress,
                anchor_available=bool(anchor["anchor_available"]),
                unavailable_reason=anchor["unavailable_reason"],
            )
            rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "Store": store,
                    "Date": day,
                    "horizon": horizon,
                    "ScenarioOpen": scenario_open,
                    "SyntheticPromo": synthetic_promo,
                    "SyntheticHolidayClosure": holiday_closure,
                    "DiscountDepth": discount,
                    "WeekdayFactor": weekday,
                    "TrendFactor": trend,
                    "PromotionFactor": promotion,
                    "CommonShock": common,
                    "StoreDateNoise": store_noise,
                    "NoiseFactor": noise_factor,
                    "DemandStressFactor": stress,
                    "SyntheticDemandValue": demand,
                    "synthetic_demand_available": demand is not None,
                    "unavailable_reason": reason,
                }
            )
    return rows


def _concat_tables(tables: list[pa.Table], schema: pa.Schema) -> pa.Table:
    return pa.concat_tables(tables) if tables else pa.Table.from_pylist([], schema=schema)


def _assert_sorted_unique_keys(table: pa.Table, key_columns: Iterable[str], name: str) -> None:
    previous: tuple[Any, ...] | None = None
    keys = table.select(list(key_columns))
    for batch in keys.to_batches(max_chunksize=65_536):
        for row in batch.to_pylist():
            current = tuple(row.values())
            if previous is not None and current <= previous:
                reason = "duplicate" if current == previous else "not sorted by primary key"
                raise ScenarioIntegrityError(f"{name} contains a {reason} key: {current}.")
            previous = current


def _build_generation_core(
    config: Mapping[str, Any], histories: Mapping[date | str, pd.DataFrame]
) -> tuple[pa.Table, pa.Table, pa.Table, Any]:
    _validate_config(config)
    normalized_histories: dict[date, pd.DataFrame] = {}
    anchor_tables: list[pa.Table] = []
    for origin_value in config["forecast_origins"]:
        origin = _as_date(origin_value)
        matches = [value for key, value in histories.items() if _as_date(key) == origin]
        if len(matches) != 1:
            raise ScenarioIntegrityError(
                f"Exactly one censored history frame is required for {origin}."
            )
        normalized = validate_history_frame(matches[0], origin=origin, stores=config["stores"])
        normalized_histories[origin] = normalized
        anchor_tables.append(
            compute_origin_anchors(normalized, origin=origin, stores=config["stores"])
        )
    anchors = _concat_tables(anchor_tables, ANCHOR_SCHEMA)
    if anchors.num_rows:
        anchors = anchors.take(
            pc.sort_indices(
                anchors, sort_keys=[("Store", "ascending"), ("forecast_origin", "ascending")]
            )
        )
    catalog_rows = _catalog_rows(config)
    catalog = pa.Table.from_pylist(catalog_rows, schema=CATALOG_SCHEMA)
    anchor_by_key = _anchor_lookup(anchors)
    random_parameters, random_shocks = _draw_cache(config)
    parameter_rows: list[dict[str, Any]] = []
    for scenario in catalog_rows:
        parameter_rows.extend(
            _scenario_parameter_rows(
                scenario,
                config=config,
                anchor_by_key=anchor_by_key,
                random_parameters=random_parameters,
            )
        )
    parameters = pa.Table.from_pylist(parameter_rows, schema=PARAMETER_SCHEMA)
    if parameters.num_rows:
        parameters = parameters.take(
            pc.sort_indices(
                parameters, sort_keys=[("scenario_id", "ascending"), ("Store", "ascending")]
            )
        )
    parameter_by_key = {
        (row["scenario_id"], int(row["Store"])): row for row in parameters.to_pylist()
    }

    def daily_batches() -> Iterator[pa.Table]:
        for scenario in catalog_rows:
            rows = _scenario_daily_rows(
                scenario,
                config=config,
                anchor_by_key=anchor_by_key,
                parameter_by_key=parameter_by_key,
                random_shocks=random_shocks,
            )
            yield pa.Table.from_pylist(rows, schema=DAILY_SCHEMA)

    return catalog, anchors, parameters, daily_batches


def generate_scenario_tables(
    config: Mapping[str, Any], histories: Mapping[date | str, pd.DataFrame]
) -> dict[str, pa.Table]:
    """Generate all logical tables in memory; intended for fixtures and small cohorts."""
    catalog, anchors, parameters, daily_batches = _build_generation_core(config, histories)
    daily = _concat_tables(list(daily_batches()), DAILY_SCHEMA)
    return {
        "scenario_catalog.parquet": catalog,
        "origin_anchors.parquet": anchors,
        "store_parameters.parquet": parameters,
        "scenario_daily.parquet": daily,
    }


def validate_scenario_tables(
    tables: Mapping[str, pa.Table], config: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate schema, keys, availability, factor ranges and approved arithmetic."""
    _validate_config(config)
    if set(tables) != set(TABLE_SCHEMAS):
        raise ScenarioIntegrityError("Scenario bundle has an unexpected table inventory.")
    for name, expected_schema in TABLE_SCHEMAS.items():
        table = tables[name]
        if not table.schema.remove_metadata().equals(expected_schema, check_metadata=False):
            raise ScenarioIntegrityError(f"{name} schema differs from its approved ordered schema.")

    expected_catalog_count = len(config["forecast_origins"]) * (
        1 + len(config["scenario_families"]) * len(config["replicates"])
    )
    expected_counts = {
        "scenario_catalog.parquet": expected_catalog_count,
        "origin_anchors.parquet": len(config["forecast_origins"]) * len(config["stores"]),
        "store_parameters.parquet": expected_catalog_count * len(config["stores"]),
        "scenario_daily.parquet": expected_catalog_count * len(config["stores"]) * HORIZON_DAYS,
    }
    for name, expected in expected_counts.items():
        if tables[name].num_rows != expected:
            raise ScenarioIntegrityError(
                f"{name} row count mismatch: expected {expected}, got {tables[name].num_rows}."
            )
        _assert_sorted_unique_keys(tables[name], TABLE_KEYS[name], name)

    catalog = tables["scenario_catalog.parquet"].to_pylist()
    anchors = tables["origin_anchors.parquet"].to_pylist()
    parameters = tables["store_parameters.parquet"].to_pylist()
    daily = (
        row
        for batch in tables["scenario_daily.parquet"].to_batches(max_chunksize=65_536)
        for row in batch.to_pylist()
    )
    catalog_by_id = {row["scenario_id"]: row for row in catalog}
    anchors_by_key = {(int(row["Store"]), row["forecast_origin"]): row for row in anchors}
    parameter_by_key = {(row["scenario_id"], int(row["Store"])): row for row in parameters}
    configured_stores = set(config["stores"])
    if catalog != _catalog_rows(config):
        raise ScenarioIntegrityError(
            "Scenario catalog differs from the approved family/origin grid."
        )
    for row in catalog:
        origin = row["forecast_origin"]
        if row["mode"] == "synthetic_stress" and row["calibration_transport_valid"]:
            raise ScenarioIntegrityError("Synthetic stress cannot transport Phase 8 calibration.")
        if row["mode"] == "historical_replay" and not row["calibration_transport_valid"]:
            raise ScenarioIntegrityError(
                "The historical reference must retain conditional validity."
            )
        if origin + timedelta(days=HORIZON_DAYS) > DEVELOPMENT_CUTOFF:
            raise ScenarioIntegrityError("Scenario target extends beyond July 3, 2015.")
        if row["horizon_days"] != HORIZON_DAYS or row["stress_spec_id"] != row["family"]:
            raise ScenarioIntegrityError(
                "Scenario catalog horizon or stress identity is inconsistent."
            )
    for row in anchors:
        if row["open_rows"] >= MIN_OPEN_HISTORY:
            if not row["anchor_available"] or row["mean_open_sales_value"] is None:
                raise ScenarioIntegrityError("A 28-row anchor was incorrectly marked unavailable.")
            expected_mean = row["open_sales_sum"] / row["open_rows"]
            if not math.isclose(
                row["mean_open_sales_value"], expected_mean, rel_tol=1e-12, abs_tol=1e-12
            ):
                raise ScenarioIntegrityError("Open-sales anchor arithmetic is inconsistent.")
            if row["zero_anchor"] != (expected_mean == 0):
                raise ScenarioIntegrityError(
                    "zero_anchor does not match the valid open-sales mean."
                )
        elif row["anchor_available"] or row["mean_open_sales_value"] is not None:
            raise ScenarioIntegrityError("An anchor below 28 valid open rows must be unavailable.")
        if row["zero_anchor"] and (
            not row["anchor_available"] or row["mean_open_sales_value"] != 0
        ):
            raise ScenarioIntegrityError("zero_anchor is true without an available zero mean.")
        if row["anchor_available"] and row["unavailable_reason"] is not None:
            raise ScenarioIntegrityError("Available anchor has an unavailable reason.")
        if not row["anchor_available"]:
            expected_reason = (
                "no_store_history" if row["observed_rows"] == 0 else "insufficient_open_history"
            )
            if row["unavailable_reason"] != expected_reason:
                raise ScenarioIntegrityError(
                    "Unavailable anchor reason does not match its history."
                )
        if row["observed_rows"] == 0:
            if row["observed_history_start"] is not None or row["observed_history_end"] is not None:
                raise ScenarioIntegrityError("Empty history must have null observed bounds.")
        elif row["observed_history_start"] is None or row["observed_history_end"] is None:
            raise ScenarioIntegrityError("Observed history is missing its date bounds.")
        if (
            not isinstance(row["history_logical_sha256"], str)
            or len(row["history_logical_sha256"]) != 64
        ):
            raise ScenarioIntegrityError("Origin anchor history digest is malformed.")
        if row["observed_rows"] + row["missing_calendar_days"] != HISTORY_DAYS:
            raise ScenarioIntegrityError("Anchor observed/missing date counts do not sum to 56.")
        if row["open_rows"] + row["closed_rows"] + row["unknown_open_rows"] != row["observed_rows"]:
            raise ScenarioIntegrityError("Anchor Open-status counts do not sum to observed rows.")

    for row in parameters:
        scenario = catalog_by_id.get(row["scenario_id"])
        if scenario is None or row["Store"] not in configured_stores:
            raise ScenarioIntegrityError(
                "Store parameters have an invalid catalog/store reference."
            )
        anchor = anchors_by_key[(int(row["Store"]), scenario["forecast_origin"])]
        available = bool(anchor["anchor_available"])
        if row["initialization_available"] != available:
            raise ScenarioIntegrityError("Store parameter availability differs from its anchor.")
        if not available:
            if (
                row["InitialStockOnHandValue"] is not None
                or row["InitialInventoryPositionValue"] is not None
            ):
                raise ScenarioIntegrityError(
                    "Unavailable anchor has fabricated initial stock/position."
                )
            if row["unavailable_reason"] != anchor["unavailable_reason"]:
                raise ScenarioIntegrityError(
                    "Unavailable store parameter reason differs from anchor."
                )
        else:
            expected_stock = anchor["mean_open_sales_value"] * row["InventoryCoverageDays"]
            if not math.isclose(
                row["InitialStockOnHandValue"], expected_stock, rel_tol=1e-12, abs_tol=1e-9
            ):
                raise ScenarioIntegrityError("Initial stock does not equal anchor times coverage.")
            if row["InitialInventoryPositionValue"] != row["InitialStockOnHandValue"]:
                raise ScenarioIntegrityError(
                    "Cold-start inventory position differs from initial stock."
                )
            if row["unavailable_reason"] is not None:
                raise ScenarioIntegrityError("Available store parameter has an unavailable reason.")
        if row["InitialOnOrderValue"] != 0 or row["InitialBackordersValue"] != 0:
            raise ScenarioIntegrityError("Initial order pipeline/backorders must start at zero.")
        if not 2 <= row["SupplierLeadTime"] <= 7 or row["ReviewPeriod"] != 1:
            raise ScenarioIntegrityError("Lead-time/review values are outside approved ranges.")
        if row["ProtectionPeriod"] != row["SupplierLeadTime"] + row["ReviewPeriod"]:
            raise ScenarioIntegrityError(
                "Protection period must equal lead time plus review period."
            )
        if not 1 <= row["InventoryCoverageDays"] <= 11:
            raise ScenarioIntegrityError("Inventory coverage is outside the approved 1..11 range.")
        c = row["ProcurementCostRatio"]
        a = row["AnnualHoldingRate"]
        g = row["GoodwillPenaltyRate"]
        if not 0.55 <= c < 0.85 or not 0.10 <= a < 0.30 or not 0.10 <= g < 0.75:
            raise ScenarioIntegrityError("Synthetic cost assumptions are outside approved ranges.")
        if not math.isclose(row["HoldingCostRate"], c * a / 365, rel_tol=1e-12, abs_tol=1e-15):
            raise ScenarioIntegrityError("HoldingCostRate arithmetic is inconsistent.")
        if not math.isclose(row["StockoutPenalty"], (1 - c) + g, rel_tol=1e-12, abs_tol=1e-15):
            raise ScenarioIntegrityError("StockoutPenalty arithmetic is inconsistent.")
        if row["AverageUnitValue"] not in (5, 10, 20, 50):
            raise ScenarioIntegrityError("AverageUnitValue is outside its discrete choices.")
        if not -0.10 <= row["TrendEndChange"] <= 0.30:
            raise ScenarioIntegrityError("TrendEndChange is outside the approved range.")
        if not 0.5 <= row["PromotionResponseSlope"] < 1.5:
            raise ScenarioIntegrityError("PromotionResponseSlope is outside the approved range.")
        if not 0 <= row["PlannedDiscountDepth"] <= 0.40:
            raise ScenarioIntegrityError("PlannedDiscountDepth is outside the approved range.")
        if scenario["family"] in {"long_lead_low_stock", "coupled_peak_delay"} and (
            row["SupplierLeadTime"] != 7
            or row["ProtectionPeriod"] != 8
            or row["InventoryCoverageDays"] != 1
        ):
            raise ScenarioIntegrityError("Long-lead/thin-stock override is incomplete.")
        if (
            scenario["family"] in {"trend_ramp", "coupled_peak_delay"}
            and row["TrendEndChange"] != 0.30
        ):
            raise ScenarioIntegrityError("Trend-ramp override is missing.")
        if row["TrendEndChange"] == 0.30 and scenario["family"] not in {
            "trend_ramp",
            "coupled_peak_delay",
        }:
            raise ScenarioIntegrityError("Trend stress override appears outside declared families.")

    for row in daily:
        scenario = catalog_by_id.get(row["scenario_id"])
        if scenario is None or row["Store"] not in configured_stores:
            raise ScenarioIntegrityError("Daily context has an invalid catalog/store reference.")
        origin = scenario["forecast_origin"]
        horizon = row["horizon"]
        if not 1 <= horizon <= HORIZON_DAYS or row["Date"] != origin + timedelta(days=horizon):
            raise ScenarioIntegrityError("Daily context date does not equal origin plus horizon.")
        if row["Date"] > DEVELOPMENT_CUTOFF:
            raise ScenarioIntegrityError(
                "Daily context crosses the protected final-holdout boundary."
            )
        if scenario["mode"] == "historical_replay":
            if any(row[name] is not None for name in DAILY_SCHEMA.names[4:16]):
                raise ScenarioIntegrityError(
                    "Historical reference contains synthetic context values."
                )
            if (
                row["synthetic_demand_available"]
                or row["unavailable_reason"] != "historical_outcomes_not_loaded"
            ):
                raise ScenarioIntegrityError("Historical reference must not fabricate outcomes.")
            continue
        anchor = anchors_by_key[(int(row["Store"]), origin)]
        parameter = parameter_by_key[(row["scenario_id"], int(row["Store"]))]
        values = [row[name] for name in DAILY_SCHEMA.names[7:16] if name != "SyntheticDemandValue"]
        if any(value is None or not math.isfinite(float(value)) for value in values):
            raise ScenarioIntegrityError("Synthetic exogenous factors must be finite and present.")
        if row["ScenarioOpen"] not in (0, 1, None):
            raise ScenarioIntegrityError("ScenarioOpen must be 0, 1 or null.")
        expected_weekday = WEEKDAY_FACTORS[row["Date"].weekday()]
        if row["WeekdayFactor"] != expected_weekday:
            raise ScenarioIntegrityError("Synthetic weekday factors were changed or normalized.")
        family = scenario["family"]
        expected_holiday = family == "calendar_closure" and horizon == 8
        expected_open = int(row["Date"].weekday() < 6 and not expected_holiday)
        if (
            row["SyntheticHolidayClosure"] != expected_holiday
            or row["ScenarioOpen"] != expected_open
        ):
            raise ScenarioIntegrityError(
                "Synthetic weekly or holiday opening schedule is inconsistent."
            )
        if not 0.75 <= row["NoiseFactor"] < 1.25:
            raise ScenarioIntegrityError("NoiseFactor is outside its approved range.")
        if not -0.10 <= row["CommonShock"] < 0.10 or not -0.15 <= row["StoreDateNoise"] < 0.15:
            raise ScenarioIntegrityError(
                "Common or store-date noise is outside its approved range."
            )
        if not math.isclose(
            row["NoiseFactor"],
            1.0 + row["CommonShock"] + row["StoreDateNoise"],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ScenarioIntegrityError("NoiseFactor arithmetic is inconsistent.")
        if not 0 <= row["DemandStressFactor"] <= 2:
            raise ScenarioIntegrityError("DemandStressFactor is outside its approved range.")
        if family in {"promo_peak", "coupled_peak_delay"}:
            expected_promo = horizon in (4, 5, 6, 7, 8)
            expected_discount = 0.40 if expected_promo else 0.0
        else:
            expected_promo = bool(parameter["PlannedPromoBlock"] and horizon in (4, 5, 6))
            expected_discount = parameter["PlannedDiscountDepth"] if expected_promo else 0.0
        if row["SyntheticPromo"] != expected_promo or row["DiscountDepth"] != expected_discount:
            raise ScenarioIntegrityError(
                "Synthetic promotion schedule/depth differs from its contract."
            )
        if row["SyntheticPromo"] != (row["DiscountDepth"] > 0):
            raise ScenarioIntegrityError("Promo and discount-depth relationship is inconsistent.")
        expected_promotion = 1 + parameter["PromotionResponseSlope"] * row["DiscountDepth"]
        if not math.isclose(
            row["PromotionFactor"], expected_promotion, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise ScenarioIntegrityError("PromotionFactor arithmetic is inconsistent.")
        expected_trend = 1 + parameter["TrendEndChange"] * horizon / HORIZON_DAYS
        if not math.isclose(row["TrendFactor"], expected_trend, rel_tol=1e-12, abs_tol=1e-12):
            raise ScenarioIntegrityError("TrendFactor arithmetic is inconsistent.")
        if family == "demand_slump":
            expected_stress = 0.25
        elif family == "promo_peak":
            expected_stress = 1.50 if horizon in (4, 5, 6, 7, 8) else 1.0
        elif family == "calendar_closure":
            expected_stress = 1.50 if horizon == 10 else 1.0
        elif family == "coupled_peak_delay":
            expected_stress = 2.0 if horizon in (4, 5, 6, 7, 8) else 1.0
        elif family == "zero_turnover":
            expected_stress = 0.0
        else:
            expected_stress = 1.0
        if row["DemandStressFactor"] != expected_stress:
            raise ScenarioIntegrityError("Demand-stress override differs from its declared family.")
        combined_factor = (
            ((row["WeekdayFactor"] * row["TrendFactor"]) * row["PromotionFactor"])
            * row["NoiseFactor"]
        ) * row["DemandStressFactor"]
        if combined_factor > 6.0:
            raise ScenarioIntegrityError("Combined synthetic demand factor exceeds 6.0.")
        if row["synthetic_demand_available"] != (row["SyntheticDemandValue"] is not None):
            raise ScenarioIntegrityError("Synthetic demand value and availability flag disagree.")
        if not anchor["anchor_available"]:
            if row["SyntheticDemandValue"] is not None or row["synthetic_demand_available"]:
                raise ScenarioIntegrityError(
                    "Unavailable anchor was converted to synthetic zero demand."
                )
            if row["unavailable_reason"] != anchor["unavailable_reason"]:
                raise ScenarioIntegrityError("Unavailable demand reason differs from its anchor.")
        elif row["ScenarioOpen"] == 0:
            if (
                row["SyntheticDemandValue"] != 0
                or not row["synthetic_demand_available"]
                or row["unavailable_reason"] is not None
            ):
                raise ScenarioIntegrityError(
                    "Known closure must route to available synthetic zero."
                )
        elif row["ScenarioOpen"] is None:
            if row["SyntheticDemandValue"] is not None or row["synthetic_demand_available"]:
                raise ScenarioIntegrityError("Unknown schedule must remain unavailable.")
            if row["unavailable_reason"] != "unknown_scenario_open":
                raise ScenarioIntegrityError("Unknown schedule requires its explicit reason.")
        else:
            if row["SyntheticDemandValue"] is None or not row["synthetic_demand_available"]:
                raise ScenarioIntegrityError(
                    "Known-open available path must have synthetic demand."
                )
            if row["unavailable_reason"] is not None:
                raise ScenarioIntegrityError(
                    "Available synthetic demand has an unavailable reason."
                )
            expected, _ = synthetic_demand_value(
                anchor["mean_open_sales_value"],
                1,
                weekday_factor=row["WeekdayFactor"],
                trend_factor=row["TrendFactor"],
                promotion_factor=row["PromotionFactor"],
                noise_factor=row["NoiseFactor"],
                demand_stress_factor=row["DemandStressFactor"],
            )
            if not math.isclose(row["SyntheticDemandValue"], expected, rel_tol=1e-12, abs_tol=1e-9):
                raise ScenarioIntegrityError(
                    "Synthetic turnover does not match the approved formula."
                )
            if parameter["initialization_available"] is False:
                raise ScenarioIntegrityError(
                    "A synthetic daily path references unavailable initialization."
                )
    return {
        "status": "passed",
        "expected_counts": expected_counts,
        "actual_counts": {name: table.num_rows for name, table in tables.items()},
        "structural_failures": [],
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ScenarioIntegrityError(
            f"Cannot read required JSON identity {path}: {error}."
        ) from error
    if not isinstance(value, dict):
        raise ScenarioIntegrityError(f"Expected a JSON object at {path}.")
    return value


def _statistic_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def _verify_development_parquet_metadata(
    path: Path, *, expected_rows: int | None = None, allow_origin_horizon: bool = False
) -> dict[str, Any]:
    """Check row counts and footer date bounds before any frozen-file byte hash."""
    try:
        parquet = pq.ParquetFile(path)
    except (OSError, pa.ArrowException) as error:
        raise ScenarioIntegrityError(
            f"Cannot inspect development Parquet metadata: {path}."
        ) from error
    metadata = parquet.metadata
    if metadata is None or metadata.num_rows <= 0:
        raise ScenarioIntegrityError(f"Development Parquet has no row metadata: {path}.")
    if expected_rows is not None and metadata.num_rows != expected_rows:
        raise ScenarioIntegrityError(
            f"Development Parquet row count differs from its manifest: {path}."
        )
    schema = parquet.schema_arrow
    names = schema.names
    min_date: date | None = None
    max_date: date | None = None
    if "Date" in names:
        date_index = names.index("Date")
        for group_index in range(metadata.num_row_groups):
            statistics = metadata.row_group(group_index).column(date_index).statistics
            if statistics is None or statistics.min is None or statistics.max is None:
                raise ScenarioIntegrityError(f"Development Parquet lacks Date statistics: {path}.")
            group_min = _statistic_date(statistics.min)
            group_max = _statistic_date(statistics.max)
            min_date = group_min if min_date is None else min(min_date, group_min)
            max_date = group_max if max_date is None else max(max_date, group_max)
    elif allow_origin_horizon and {"forecast_origin", "k"}.issubset(names):
        origin_index = names.index("forecast_origin")
        horizon_index = names.index("k")
        for group_index in range(metadata.num_row_groups):
            group = metadata.row_group(group_index)
            origin_stats = group.column(origin_index).statistics
            horizon_stats = group.column(horizon_index).statistics
            if (
                origin_stats is None
                or horizon_stats is None
                or origin_stats.min is None
                or origin_stats.max is None
                or horizon_stats.max is None
            ):
                raise ScenarioIntegrityError(
                    f"Development Parquet lacks origin/horizon boundary statistics: {path}."
                )
            group_min = _statistic_date(origin_stats.min)
            group_max = _statistic_date(origin_stats.max) + timedelta(days=int(horizon_stats.max))
            min_date = group_min if min_date is None else min(min_date, group_min)
            max_date = group_max if max_date is None else max(max_date, group_max)
    else:
        raise ScenarioIntegrityError(f"Development Parquet has no auditable Date boundary: {path}.")
    if min_date is None or max_date is None or max_date > DEVELOPMENT_CUTOFF:
        raise ScenarioIntegrityError(
            f"Development Parquet metadata crosses the 2015-07-03 boundary: {path}."
        )
    return {
        "rows": int(metadata.num_rows),
        "minimum_date": min_date.isoformat(),
        "maximum_date": max_date.isoformat(),
        "columns": names,
    }


def _assert_repo_path(root: Path, relative: str) -> Path:
    path = (root / Path(relative)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ScenarioIntegrityError(f"Frozen upstream path escapes repository: {relative}.")
    if not path.is_file():
        raise ScenarioIntegrityError(f"Frozen upstream artifact is missing: {relative}.")
    return path


def _preflight_phase7_parquets(root: Path) -> dict[str, dict[str, Any]]:
    """Inspect all allowlisted Phase 7 Parquet footers before hashing any frozen file."""
    from rossmann_forecasting.forecasting.uncertainty import (
        CANDIDATE_OUTPUT_PATHS,
        INPUT_OUTPUTS,
    )

    metadata: dict[str, dict[str, Any]] = {}
    candidate_files: list[tuple[Path, int | None]] = []
    folders = {
        "seasonal_naive": "seasonal_naive",
        "holt_winters_additive_weekly": "holt_winters",
        "global_lightgbm_gbdt_regression_l1": "lightgbm",
    }
    for candidate_id, candidate_paths in CANDIDATE_OUTPUT_PATHS.items():
        candidate_manifest = _read_json_object(
            root / "data" / "processed" / folders[candidate_id] / "manifest.json"
        )
        entries = candidate_manifest.get("outputs")
        if not isinstance(entries, dict) or not entries:
            entries = candidate_manifest.get("artifacts")
        if not isinstance(entries, dict):
            raise ScenarioIntegrityError(
                f"Candidate artifact metadata is malformed: {candidate_id}."
            )
        metadata_by_path = {
            item.get("path", key): item for key, item in entries.items() if isinstance(item, dict)
        }
        for relative in candidate_paths:
            if Path(relative).suffix == ".parquet":
                item = metadata_by_path.get(relative)
                if not isinstance(item, dict) or not isinstance(item.get("rows"), int):
                    raise ScenarioIntegrityError(
                        f"Candidate Parquet row metadata is missing: {relative}."
                    )
                candidate_files.append((_assert_repo_path(root, relative), item["rows"]))
    for name in INPUT_OUTPUTS:
        if name.endswith(".parquet"):
            candidate_files.append(
                (_assert_repo_path(root, f"data/processed/model_selection/{name}"), None)
            )
    selection_manifest = _read_json_object(root / "data/processed/model_selection/manifest.json")
    outputs = selection_manifest.get("outputs")
    if not isinstance(outputs, dict):
        raise ScenarioIntegrityError("Phase 7 selection manifest output metadata is malformed.")
    for name in ("development_residual_paths.parquet", "selected_development_forecasts.parquet"):
        item = outputs.get(name)
        if not isinstance(item, dict) or not isinstance(item.get("rows"), int):
            raise ScenarioIntegrityError(f"Phase 7 manifest omits Parquet row metadata for {name}.")
        candidate_files.append(
            (_assert_repo_path(root, f"data/processed/model_selection/{name}"), item["rows"])
        )

    # Deduplicate while retaining exact manifest-declared row counts for selection outputs.
    seen: set[Path] = set()
    for path, expected_rows in candidate_files:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        metadata[resolved.relative_to(root.resolve()).as_posix()] = (
            _verify_development_parquet_metadata(resolved, expected_rows=expected_rows)
        )
    return metadata


def _preflight_phase8_parquets(
    root: Path, run_dir: Path, manifest: Mapping[str, Any]
) -> dict[str, Any]:
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        raise ScenarioIntegrityError("Phase 8 manifest output metadata is malformed.")
    result: dict[str, Any] = {}
    for name, item in outputs.items():
        if not name.endswith(".parquet"):
            continue
        if not isinstance(item, dict) or not isinstance(item.get("rows"), int):
            raise ScenarioIntegrityError(f"Phase 8 output metadata is malformed for {name}.")
        path = (run_dir / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ScenarioIntegrityError(f"Phase 8 output path is missing or unsafe: {name}.")
        result[name] = _verify_development_parquet_metadata(
            path,
            expected_rows=item["rows"],
            allow_origin_horizon=(name == "cumulative_uncertainty.parquet"),
        )
    return result


def validate_phase8_fit_chronology(fits: Any) -> None:
    expected_fits = [
        {
            "fit_id": "A",
            "assessment_window": "validation_2",
            "assessment_origin": "2015-06-05",
            "assessment_targets_after_origin": True,
            "assessment_target_dates": {"first_date": "2015-06-06", "last_date": "2015-06-19"},
            "calibration_windows": ["validation_1"],
            "calibration_labels_through": "2015-06-05",
            "calibration_date_ranges": [
                {"first_date": "2015-05-23", "last_date": "2015-06-05", "window": "validation_1"}
            ],
        },
        {
            "fit_id": "B",
            "assessment_window": "validation_3",
            "assessment_origin": "2015-06-19",
            "assessment_targets_after_origin": True,
            "assessment_target_dates": {"first_date": "2015-06-20", "last_date": "2015-07-03"},
            "calibration_windows": ["validation_1", "validation_2"],
            "calibration_labels_through": "2015-06-19",
            "calibration_date_ranges": [
                {"first_date": "2015-05-23", "last_date": "2015-06-05", "window": "validation_1"},
                {"first_date": "2015-06-06", "last_date": "2015-06-19", "window": "validation_2"},
            ],
        },
    ]
    if fits != expected_fits:
        raise ScenarioIntegrityError(
            "Phase 8 Fit A/Fit B chronology differs from approved origins."
        )


def _validate_phase8_config(config: Mapping[str, Any]) -> None:
    if config.get("selection_run_id") != "365f22d4c3f94722a594ab934a22c4f6":
        raise ScenarioIntegrityError("Phase 8 config references the wrong Phase 7 selection run.")
    if config.get("selected_candidate_id") != "global_lightgbm_gbdt_regression_l1":
        raise ScenarioIntegrityError("Phase 8 config references a different selected model.")
    if config.get("policy_version") != "phase-8-uncertainty-v1":
        raise ScenarioIntegrityError("Phase 8 uncertainty policy identity differs from ADR-021.")
    if (
        config.get("config_canonical_sha256")
        != "49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93"
    ):
        raise ScenarioIntegrityError(
            "Phase 8 canonical policy/config identity differs from accepted ADR-022."
        )
    canonical_payload = {
        key: value
        for key, value in config.items()
        if key not in {"config_canonical_sha256", "config_hash_excludes_self_field"}
    }
    if _canonical_sha256(canonical_payload) != config["config_canonical_sha256"]:
        raise ScenarioIntegrityError(
            "Phase 8 config canonical identity does not match its contents."
        )
    if config.get("p_grid", config.get("cumulative_error", {}).get("levels")) is None:
        # The accepted grid is repeated in the cumulative policy section.
        raise ScenarioIntegrityError("Phase 8 p grid is missing.")
    if config.get("cumulative_error", {}).get("levels") != list(P_GRID):
        raise ScenarioIntegrityError("Phase 8 p grid differs from the approved scenario binding.")
    if (
        config.get("schedule_assumption", {}).get("identifier")
        != "saved_source_open_assumed_known_at_origin"
    ):
        raise ScenarioIntegrityError("Phase 8 historical Open assumption identity differs.")
    if config.get("schedule_assumption", {}).get("externally_verified") is not False:
        raise ScenarioIntegrityError("Saved source Open must remain a conditional assumption.")
    if config.get("boundaries", {}).get("development_cutoff_inclusive") != "2015-07-03":
        raise ScenarioIntegrityError(
            "Phase 8 cutoff does not match the Phase 9 development boundary."
        )
    if (
        config.get("boundaries", {}).get("holdout_open_sales_customers_read_loaded_or_hashed")
        is not False
    ):
        raise ScenarioIntegrityError(
            "Phase 8 config does not certify the protected holdout boundary."
        )
    validate_phase8_fit_chronology(config.get("fits"))


def validate_phase7_selection_identity(manifest: Mapping[str, Any]) -> None:
    expected = {
        "command": "rossmann-model-selection",
        "status": "selected",
        "publication_state": "complete",
        "input_integrity_status": "passed",
        "record_integrity_status": "passed",
        "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
        "selection_run_id": "365f22d4c3f94722a594ab934a22c4f6",
        "final_holdout_forecast_or_evaluation": False,
        "final_holdout_outcomes_read_or_hashed": False,
        "phase_8_started": False,
        "policy_version": "phase-7-adr-020-v1",
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise ScenarioIntegrityError(f"Phase 7 selection identity differs for {field}.")


def validate_phase8_manifest_identity(manifest: Mapping[str, Any]) -> None:
    expected = {
        "run_id": "phase8-impl-20261006-provenance-review",
        "policy_version": "phase-8-uncertainty-v1",
        "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
        "selection_run_id": "365f22d4c3f94722a594ab934a22c4f6",
        "fit_b_quantiles_frozen": False,
        "external_fit_b_results_review_pending": True,
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise ScenarioIntegrityError(f"Phase 8 publication identity differs for {field}.")


def _read_safe_phase7_forecasts(path: Path, stores: list[int]) -> dict[str, Any]:
    """Project only forecast keys, raw point values, availability and provenance."""
    columns = [
        "Store",
        "forecast_origin",
        "Date",
        "horizon",
        "raw_forecast",
        "operational_forecast",
        "forecast_available",
        "operational_forecast_available",
        "candidate_id",
        "model_config_identity",
        "model_configuration_sha256",
        "model_selection_run_id",
        "source_manifest_sha256",
    ]
    dataset = ds.dataset(path, format="parquet")
    missing = set(columns).difference(dataset.schema.names)
    if missing:
        raise ScenarioIntegrityError(
            f"Selected Phase 7 forecasts lack safe binding columns: {sorted(missing)}."
        )
    origin_values = [datetime.combine(origin, datetime.min.time()) for origin in ALLOWED_ORIGINS]
    date_type = dataset.schema.field("Date").type
    predicate = ds.field("forecast_origin").isin(origin_values) & (
        ds.field("Date")
        <= pa.scalar(datetime.combine(DEVELOPMENT_CUTOFF, datetime.min.time()), type=date_type)
    )
    table = dataset.to_table(columns=columns, filter=predicate, use_threads=False)
    frame = table.to_pandas()
    forbidden = {"actual_sales", "source_open", "raw_residual", "operational_residual", "Customers"}
    if forbidden.intersection(frame.columns):
        raise ScenarioIntegrityError(
            "Safe forecast projection unexpectedly included outcomes/residuals."
        )
    frame["forecast_origin"] = pd.to_datetime(frame["forecast_origin"], errors="raise").dt.date
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise").dt.date
    frame["Store"] = pd.to_numeric(frame["Store"], errors="raise").astype("int64")
    frame["horizon"] = pd.to_numeric(frame["horizon"], errors="raise").astype("int64")
    if frame.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise ScenarioIntegrityError("Safe Phase 7 forecast projection contains duplicate keys.")
    expected_keys = {
        (store, origin, origin + timedelta(days=horizon))
        for origin in ALLOWED_ORIGINS
        for store in stores
        for horizon in range(1, HORIZON_DAYS + 1)
    }
    actual_keys = set(zip(frame["Store"], frame["forecast_origin"], frame["Date"], strict=True))
    if actual_keys != expected_keys:
        raise ScenarioIntegrityError(
            "Phase 7 selected forecasts do not cover the exact two H14 grids."
        )
    if not frame["Date"].map(lambda value: value <= DEVELOPMENT_CUTOFF).all():
        raise ScenarioIntegrityError(
            "Safe Phase 7 forecast projection crossed the development cutoff."
        )
    if any(
        row.Date != row.forecast_origin + timedelta(days=int(row.horizon))
        for row in frame.itertuples(index=False)
    ):
        raise ScenarioIntegrityError(
            "Phase 7 forecast dates disagree with origin and horizon keys."
        )
    if (
        frame["forecast_available"].isna().any()
        or frame["operational_forecast_available"].isna().any()
    ):
        raise ScenarioIntegrityError("Phase 7 availability flags must be present.")
    available_raw = frame.loc[frame["forecast_available"].astype(bool), "raw_forecast"]
    if available_raw.isna().any() or not np.isfinite(available_raw.to_numpy(dtype="float64")).all():
        raise ScenarioIntegrityError("Available raw forecast points must be finite.")
    if (available_raw < 0).any():
        raise ScenarioIntegrityError("Saved clipped raw forecast points must be nonnegative.")
    rows_by_origin = {
        origin.isoformat(): int(frame["forecast_origin"].eq(origin).sum())
        for origin in ALLOWED_ORIGINS
    }
    provenance = {}
    for column in (
        "candidate_id",
        "model_config_identity",
        "model_configuration_sha256",
        "model_selection_run_id",
        "source_manifest_sha256",
    ):
        values = frame[column].dropna().unique().tolist()
        if len(values) != 1 or frame[column].isna().any():
            raise ScenarioIntegrityError(f"Phase 7 forecast provenance is inconsistent: {column}.")
        provenance[column] = values[0]
    return {
        "rows": int(len(frame)),
        "rows_by_origin": rows_by_origin,
        "origins": [origin.isoformat() for origin in ALLOWED_ORIGINS],
        "projected_columns": columns,
        "provenance": provenance,
        "outcome_and_residual_columns_loaded": False,
    }


def verify_frozen_bindings(root: str | Path) -> dict[str, Any]:
    """Bind immutable development-only Phase 7/8 artifacts without reading outcomes."""
    from rossmann_forecasting.data.preparation import SOURCE_SNAPSHOT_SHA256
    from rossmann_forecasting.forecasting.model_selection import (
        verify_candidate_manifests,
    )
    from rossmann_forecasting.forecasting.uncertainty import (
        INPUT_OUTPUTS,
        MODEL_SELECTION_RUN_ID,
        OUTPUT_FILENAMES,
        SELECTED_CANDIDATE_ID,
    )

    repository = Path(root).resolve()
    phase7_dir = repository / "data/processed/model_selection"
    phase8_run_id = "phase8-impl-20261006-provenance-review"
    phase8_dir = repository / "data/processed/uncertainty" / phase8_run_id
    phase7_manifest_path = phase7_dir / "manifest.json"
    phase8_manifest_path = phase8_dir / "manifest.json"
    if not phase7_manifest_path.is_file() or not phase8_manifest_path.is_file():
        raise ScenarioIntegrityError("Canonical Phase 7/8 development manifests are required.")
    phase7_manifest = _read_json_object(phase7_manifest_path)
    phase8_manifest = _read_json_object(phase8_manifest_path)
    phase8_config_path = phase8_dir / "calibration_config.json"
    phase8_config = _read_json_object(phase8_config_path)

    # All footer Date-boundary and row-count checks precede every whole-file hash below.
    phase7_footer = _preflight_phase7_parquets(repository)
    phase8_footer = _preflight_phase8_parquets(repository, phase8_dir, phase8_manifest)

    validate_phase7_selection_identity(phase7_manifest)
    phase7_outputs = phase7_manifest.get("outputs")
    selected_artifacts = phase7_manifest.get("selected_model_artifacts")
    if not isinstance(phase7_outputs, dict) or set(phase7_outputs) != set(INPUT_OUTPUTS):
        raise ScenarioIntegrityError(
            "Phase 7 selection output allowlist differs from ADR-021 lineage."
        )
    expected_selected_names = {
        "development_residual_paths.parquet",
        "selected_development_forecasts.parquet",
        "selected_model_config.json",
        "refit_recipe.json",
    }
    if (
        not isinstance(selected_artifacts, dict)
        or set(selected_artifacts) != expected_selected_names
    ):
        raise ScenarioIntegrityError("Phase 7 selected artifact set is incomplete or unexpected.")

    from rossmann_forecasting.forecasting.uncertainty import CANDIDATE_OUTPUT_PATHS

    folders = {
        "seasonal_naive": "seasonal_naive",
        "holt_winters_additive_weekly": "holt_winters",
        "global_lightgbm_gbdt_regression_l1": "lightgbm",
    }
    candidate_manifest_paths = {
        candidate: repository / "data" / "processed" / folder / "manifest.json"
        for candidate, folder in folders.items()
    }
    candidate_manifests = {
        candidate: _read_json_object(path) for candidate, path in candidate_manifest_paths.items()
    }
    for candidate, manifest in candidate_manifests.items():
        if manifest.get("development_only_through") != DEVELOPMENT_CUTOFF.isoformat():
            raise ScenarioIntegrityError(f"{candidate} manifest has the wrong development cutoff.")
        if manifest.get("final_holdout_forecast_or_evaluation") is not False:
            raise ScenarioIntegrityError(
                f"{candidate} manifest does not certify development-only outputs."
            )
        if manifest.get("candidate_id") not in (None, candidate):
            raise ScenarioIntegrityError(f"Candidate manifest identity mismatch for {candidate}.")
        raw_entries = manifest.get("outputs") or manifest.get("artifacts")
        if not isinstance(raw_entries, dict):
            raise ScenarioIntegrityError(
                f"Candidate manifest has no output inventory: {candidate}."
            )
        declared = {
            Path(item.get("path", key)).as_posix()
            for key, item in raw_entries.items()
            if isinstance(item, dict)
        }
        if declared != CANDIDATE_OUTPUT_PATHS[candidate]:
            raise ScenarioIntegrityError(
                f"Candidate output paths differ from reviewed allowlist: {candidate}."
            )
    candidate_evidence = verify_candidate_manifests(repository)

    phase7_file_hashes: dict[str, dict[str, Any]] = {}
    for name in INPUT_OUTPUTS:
        item = phase7_outputs.get(name)
        if not isinstance(item, dict) or not isinstance(item.get("sha256"), str):
            raise ScenarioIntegrityError(f"Phase 7 manifest hash is missing for {name}.")
        path = _assert_repo_path(repository, f"data/processed/model_selection/{name}")
        actual = _sha256_file(path)
        if actual != item["sha256"]:
            raise ScenarioIntegrityError(f"Phase 7 output hash mismatch for {name}.")
        if (
            name.endswith(".parquet")
            and item.get("rows") != phase7_footer[f"data/processed/model_selection/{name}"]["rows"]
        ):
            raise ScenarioIntegrityError(f"Phase 7 output row count mismatch for {name}.")
        phase7_file_hashes[name] = {
            "path": path.relative_to(repository).as_posix(),
            "sha256": actual,
            "rows": item.get("rows"),
        }
    selection_manifest_hash = _sha256_file(phase7_manifest_path)
    for name in expected_selected_names:
        selected_item = selected_artifacts.get(name)
        output_item = phase7_outputs.get(name)
        if (
            not isinstance(selected_item, dict)
            or not isinstance(output_item, dict)
            or selected_item.get("sha256") != output_item.get("sha256")
        ):
            raise ScenarioIntegrityError(f"Phase 7 selected artifact identity differs for {name}.")

    recorded_manifests = phase7_manifest.get("input_manifests")
    if not isinstance(recorded_manifests, dict) or set(recorded_manifests) != set(
        candidate_evidence
    ):
        raise ScenarioIntegrityError("Phase 7 candidate manifest lineage is malformed.")
    candidate_lineage: dict[str, Any] = {}
    for candidate, evidence in candidate_evidence.items():
        recorded = recorded_manifests.get(candidate)
        if not isinstance(recorded, dict) or recorded.get("sha256") != evidence.manifest_sha256:
            raise ScenarioIntegrityError(f"Phase 7 candidate manifest hash mismatch: {candidate}.")
        candidate_lineage[candidate] = {
            "manifest_path": evidence.manifest_path.relative_to(repository).as_posix(),
            "manifest_sha256": evidence.manifest_sha256,
            "artifact_hashes": dict(sorted(evidence.artifact_hashes.items())),
        }

    config_path = phase7_dir / "selected_model_config.json"
    recipe_path = phase7_dir / "refit_recipe.json"
    decision_path = phase7_dir / "selection_decision.json"
    model_config = _read_json_object(config_path)
    recipe = _read_json_object(recipe_path)
    decision = _read_json_object(decision_path)
    config_hash = phase7_file_hashes["selected_model_config.json"]["sha256"]
    recipe_file_hash = phase7_file_hashes["refit_recipe.json"]["sha256"]
    source_identity = model_config.get("source_identity")
    if not isinstance(source_identity, dict):
        raise ScenarioIntegrityError("Selected Phase 7 model source identity is missing.")
    if (
        model_config.get("candidate_id") != SELECTED_CANDIDATE_ID
        or model_config.get("selection_run_id") != MODEL_SELECTION_RUN_ID
        or model_config.get("fit_performed") is not False
        or model_config.get("refit_recipe_sha256") != recipe_file_hash
        or recipe.get("candidate_id") != SELECTED_CANDIDATE_ID
        or recipe.get("selection_run_id") != MODEL_SELECTION_RUN_ID
        or recipe.get("fit_performed") is not False
        or recipe.get("recipe_only_no_fitted_model") is not True
        or model_config.get("configuration") != recipe.get("configuration")
        or recipe.get("provenance_identity") != source_identity
    ):
        raise ScenarioIntegrityError(
            "Phase 7 selected-model config and refit recipe identities disagree."
        )
    if (
        decision.get("status") != "selected"
        or decision.get("selected_candidate_id") != SELECTED_CANDIDATE_ID
        or decision.get("selected_model_identity") != SELECTED_CANDIDATE_ID
        or decision.get("selection_run_id") != MODEL_SELECTION_RUN_ID
        or decision.get("final_holdout_accessed") is not False
    ):
        raise ScenarioIntegrityError("Phase 7 selection decision does not match accepted identity.")
    lightgbm_evidence = candidate_evidence[SELECTED_CANDIDATE_ID]
    if source_identity.get("source_manifest_sha256") != lightgbm_evidence.manifest_sha256:
        raise ScenarioIntegrityError(
            "Selected model points to a different LightGBM candidate manifest."
        )
    if source_identity.get("configuration_sha256") != lightgbm_evidence.manifest.get(
        "configuration_sha256"
    ):
        raise ScenarioIntegrityError("Selected model points to a different LightGBM configuration.")
    recipe_canonical_hash = _canonical_sha256(recipe)
    forecast_projection = _read_safe_phase7_forecasts(
        phase7_dir / "selected_development_forecasts.parquet", list(range(1, 1116))
    )
    expected_forecast_provenance = {
        "candidate_id": SELECTED_CANDIDATE_ID,
        "model_config_identity": SELECTED_CANDIDATE_ID,
        "model_configuration_sha256": recipe_canonical_hash,
        "model_selection_run_id": MODEL_SELECTION_RUN_ID,
        "source_manifest_sha256": lightgbm_evidence.manifest_sha256,
    }
    for field, expected in expected_forecast_provenance.items():
        if forecast_projection["provenance"].get(field) != expected:
            raise ScenarioIntegrityError(f"Phase 7 safe forecast provenance mismatch for {field}.")

    # The Phase 8 Parquets are date-checked above. Hashes below bind only the frozen dev run.
    phase8_expected = {
        "manifest": "63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2",
        "daily_residual_quantiles.csv": (
            "5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8"
        ),
        "cumulative_error_quantiles.csv": (
            "1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff"
        ),
        "calibration_config.json": (
            "afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08"
        ),
        "config_canonical_sha256": (
            "49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93"
        ),
    }
    if _sha256_file(phase8_manifest_path) != phase8_expected["manifest"]:
        raise ScenarioIntegrityError(
            "Canonical Phase 8 manifest hash differs from accepted evidence."
        )
    validate_phase8_manifest_identity(phase8_manifest)
    if set(phase8_manifest.get("outputs", {})) != set(OUTPUT_FILENAMES):
        raise ScenarioIntegrityError("Canonical Phase 8 output inventory differs from ADR-021.")
    configuration = phase8_manifest.get("configuration")
    if (
        not isinstance(configuration, dict)
        or configuration.get("path") != "calibration_config.json"
    ):
        raise ScenarioIntegrityError("Canonical Phase 8 configuration reference is malformed.")
    phase8_output_hashes: dict[str, Any] = {}
    for name, item in phase8_manifest["outputs"].items():
        path = (phase8_dir / name).resolve()
        if not path.is_relative_to(repository) or not path.is_file():
            raise ScenarioIntegrityError(f"Canonical Phase 8 output is missing or unsafe: {name}.")
        actual_hash = _sha256_file(path)
        if actual_hash != item.get("sha256"):
            raise ScenarioIntegrityError(f"Canonical Phase 8 output hash mismatch: {name}.")
        phase8_output_hashes[name] = {
            "path": path.relative_to(repository).as_posix(),
            "sha256": actual_hash,
            "rows": item.get("rows"),
        }
    if (
        phase8_output_hashes["calibration_config.json"]["sha256"]
        != phase8_expected["calibration_config.json"]
    ):
        raise ScenarioIntegrityError(
            "Canonical Phase 8 config file hash differs from accepted evidence."
        )
    if (
        phase8_output_hashes["daily_residual_quantiles.csv"]["sha256"]
        != phase8_expected["daily_residual_quantiles.csv"]
        or phase8_output_hashes["cumulative_error_quantiles.csv"]["sha256"]
        != phase8_expected["cumulative_error_quantiles.csv"]
    ):
        raise ScenarioIntegrityError(
            "Frozen Phase 8 quantile file hashes differ from accepted evidence."
        )
    if configuration.get("sha256") != phase8_expected["calibration_config.json"]:
        raise ScenarioIntegrityError("Phase 8 manifest config identity is inconsistent.")
    _validate_phase8_config(phase8_config)

    phase8_inputs = phase8_manifest.get("inputs")
    if not isinstance(phase8_inputs, dict):
        raise ScenarioIntegrityError("Phase 8 manifest omits Phase 7 input lineage.")
    if phase8_inputs.get("selection_manifest_sha256") != selection_manifest_hash:
        raise ScenarioIntegrityError(
            "Phase 8 is not bound to the current Phase 7 selection manifest."
        )
    if phase8_inputs.get("selected_candidate_manifest_sha256") != lightgbm_evidence.manifest_sha256:
        raise ScenarioIntegrityError("Phase 8 selected candidate lineage differs from Phase 7.")
    p8_phase7_outputs = phase8_inputs.get("phase7_outputs")
    if not isinstance(p8_phase7_outputs, dict):
        raise ScenarioIntegrityError("Phase 8 manifest does not list Phase 7 output identities.")
    for name, identity in phase7_file_hashes.items():
        if p8_phase7_outputs.get(name, {}).get("sha256") != identity["sha256"]:
            raise ScenarioIntegrityError(f"Phase 8 lineage does not match Phase 7 artifact {name}.")
    selected_lineage = phase8_config.get("selected_lineage", {})
    if (
        selected_lineage.get("selection_manifest_sha256") != selection_manifest_hash
        or selected_lineage.get("selected_candidate_manifest_sha256")
        != lightgbm_evidence.manifest_sha256
        or phase8_config.get("selected_model_configuration_file_sha256") != config_hash
        or phase8_config.get("refit_recipe_file_sha256") != recipe_file_hash
        or phase8_config.get("refit_recipe_canonical_sha256") != recipe_canonical_hash
    ):
        raise ScenarioIntegrityError(
            "Phase 8 config lineage does not bind the verified Phase 7 files."
        )

    prep_manifest_path = repository / "data/interim/preparation_manifest.json"
    prep_manifest = _read_json_object(prep_manifest_path)
    source_hashes = prep_manifest.get("source_sha256")
    from rossmann_forecasting.features.contract import FEATURE_CONTRACT_VERSION, PREDICTOR_COLUMNS

    if source_hashes != SOURCE_SNAPSHOT_SHA256:
        raise ScenarioIntegrityError(
            "Inherited preparation source identities differ from the accepted snapshot."
        )
    train_snapshot_hash = prep_manifest.get("outputs", {}).get("train.parquet", {}).get("sha256")
    if not isinstance(train_snapshot_hash, str) or not train_snapshot_hash:
        raise ScenarioIntegrityError(
            "Preparation manifest omits the inherited train snapshot identity."
        )
    for candidate, manifest in candidate_manifests.items():
        provenance = manifest.get("input_provenance")
        snapshots = manifest.get("input_snapshot_identifiers")
        if candidate in {"seasonal_naive", "holt_winters_additive_weekly"}:
            raw = provenance.get("raw_source_sha256") if isinstance(provenance, dict) else None
            train_hash = (
                provenance.get("phase2_train_sha256") if isinstance(provenance, dict) else None
            )
        else:
            raw = (
                snapshots.get("phase2_source_snapshot_sha256")
                if isinstance(snapshots, dict)
                else None
            )
            train_hash = (
                snapshots.get("phase2_train_snapshot_sha256")
                if isinstance(snapshots, dict)
                else None
            )
        if raw != source_hashes or train_hash != train_snapshot_hash:
            raise ScenarioIntegrityError(
                f"{candidate} source snapshot lineage differs from preparation."
            )
    lgbm_manifest = candidate_manifests[SELECTED_CANDIDATE_ID]
    if (
        lgbm_manifest.get("selected_trial") != "A"
        or lgbm_manifest.get("selected_boosting_rounds") != 180
        or lgbm_manifest.get("predictor_contract_identity", {}).get("version")
        != FEATURE_CONTRACT_VERSION
        or lgbm_manifest.get("predictor_contract_identity", {}).get("ordered_columns")
        != list(PREDICTOR_COLUMNS)
    ):
        raise ScenarioIntegrityError(
            "Frozen LightGBM recipe or 29-column predictor contract changed."
        )

    phase8_identity = {
        "run_id": phase8_run_id,
        "manifest_path": phase8_manifest_path.relative_to(repository).as_posix(),
        "manifest_sha256": phase8_expected["manifest"],
        "outputs": phase8_output_hashes,
        "config_canonical_sha256": phase8_expected["config_canonical_sha256"],
        "schedule_assumption": "saved_source_open_assumed_known_at_origin",
        "fits": [
            {
                "forecast_origin": origin.isoformat(),
                "fit_id": FIT_BY_ORIGIN[origin],
                "target_start": (origin + timedelta(days=1)).isoformat(),
                "target_end": (origin + timedelta(days=HORIZON_DAYS)).isoformat(),
            }
            for origin in ALLOWED_ORIGINS
        ],
        "permitted_lead_time_days": [2, 7],
        "permitted_protection_period_days": [3, 8],
        "p_grid": list(P_GRID),
        "reference_p": REFERENCE_P,
        "suffix_supported": False,
    }
    source_identity = {
        "source_sha256": source_hashes,
        "phase2_train_snapshot_sha256": train_snapshot_hash,
        "verification": ("inherited from preparation manifest; full train file not rehashed"),
    }
    bindings = {
        "schema_version": SCHEMA_VERSION,
        "phase7": {
            "selection_manifest_path": phase7_manifest_path.relative_to(repository).as_posix(),
            "selection_manifest_sha256": selection_manifest_hash,
            "selection_run_id": MODEL_SELECTION_RUN_ID,
            "selected_candidate_id": SELECTED_CANDIDATE_ID,
            "selected_candidate_manifest_sha256": lightgbm_evidence.manifest_sha256,
            "selected_model_config_sha256": config_hash,
            "refit_recipe_file_sha256": recipe_file_hash,
            "refit_recipe_canonical_sha256": recipe_canonical_hash,
            "outputs": phase7_file_hashes,
            "candidate_lineage": candidate_lineage,
            "safe_forecast_projection": forecast_projection,
            "selection_policy_version": phase7_manifest.get("policy_version"),
        },
        "phase8": phase8_identity,
        "source_provenance": source_identity,
        "history_reader": {
            "path": "data/interim/train.parquet",
            "projected_columns": list(HISTORY_COLUMNS),
            "date_predicates": "origin-55 <= Date <= origin",
            "store_predicate": "Store in configured sorted Store list",
            "post_origin_rows_materialized": False,
            "full_train_file_rehashed": False,
        },
        "boundary_checks": {
            "phase7_parquet_footer_max_dates": {
                path: value["maximum_date"] for path, value in sorted(phase7_footer.items())
            },
            "phase8_parquet_footer_bounds": phase8_footer,
            "protected_holdout_values_read_or_hashed": False,
            "phase8_residuals_recomputed": False,
            "point_model_refit": False,
        },
    }
    return {
        "bindings": bindings,
        "identity_snapshot": {
            "phase7_selection_manifest_sha256": selection_manifest_hash,
            "phase7_output_hashes": {
                name: item["sha256"] for name, item in phase7_file_hashes.items()
            },
            "phase7_candidate_manifest_hashes": {
                name: item["manifest_sha256"] for name, item in candidate_lineage.items()
            },
            "phase8_manifest_sha256": phase8_expected["manifest"],
            "phase8_output_hashes": {
                name: item["sha256"] for name, item in phase8_output_hashes.items()
            },
            "source_provenance": source_identity,
            "forecast_projection": forecast_projection,
        },
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _seal_json(value: dict[str, Any], *, field_name: str) -> None:
    value[field_name] = None
    payload = {
        key: item
        for key, item in value.items()
        if key not in {field_name, "run_id", "created_at_utc"}
    }
    value[field_name] = _canonical_sha256(payload)


def _semantic_json_sha256(value: Mapping[str, Any]) -> str:
    payload = {
        key: item
        for key, item in value.items()
        if key not in {"run_id", "created_at_utc", "config_canonical_sha256", "canonical_sha256"}
    }
    return _canonical_sha256(payload)


def _write_parquet_table(path: Path, table: pa.Table) -> None:
    with pq.ParquetWriter(path, table.schema.remove_metadata(), compression="zstd") as writer:
        writer.write_table(table.replace_schema_metadata(None))


def _write_parquet_batches(path: Path, batches: Iterable[pa.Table], schema: pa.Schema) -> int:
    count = 0
    with pq.ParquetWriter(path, schema, compression="zstd") as writer:
        for table in batches:
            if not table.schema.remove_metadata().equals(schema, check_metadata=False):
                raise ScenarioIntegrityError("Generated Parquet batch has an unexpected schema.")
            writer.write_table(table.replace_schema_metadata(None))
            count += table.num_rows
    return count


def _logical_sha256_parquet(path: Path, schema: pa.Schema, key_columns: Iterable[str]) -> str:
    parquet = pq.ParquetFile(path)
    actual_schema = parquet.schema_arrow.remove_metadata()
    if not actual_schema.equals(schema, check_metadata=False):
        raise ScenarioIntegrityError(
            f"Reread Parquet schema differs from the approved schema: {path.name}."
        )
    digest = hashlib.sha256(_schema_line(schema))
    fields = list(schema)
    previous: tuple[Any, ...] | None = None
    for batch in parquet.iter_batches(batch_size=65_536, columns=schema.names):
        for row in batch.to_pylist():
            key = tuple(row[name] for name in key_columns)
            if previous is not None and key <= previous:
                kind = "duplicate" if key == previous else "unsorted"
                raise ScenarioIntegrityError(f"Reread Parquet contains {kind} primary keys: {key}.")
            previous = key
            values = [_normalize_logical_value(row[field.name], field) for field in fields]
            digest.update(_canonical_json_bytes(values) + b"\n")
    return digest.hexdigest()


def _logical_sha256_batches(
    batches: Iterable[pa.Table], schema: pa.Schema, key_columns: Iterable[str]
) -> str:
    digest = hashlib.sha256(_schema_line(schema))
    fields = list(schema)
    previous: tuple[Any, ...] | None = None
    for table in batches:
        for batch in table.to_batches(max_chunksize=65_536):
            for row in batch.to_pylist():
                key = tuple(row[name] for name in key_columns)
                if previous is not None and key <= previous:
                    raise ScenarioIntegrityError("Repeat generation is not sorted by primary key.")
                previous = key
                values = [_normalize_logical_value(row[field.name], field) for field in fields]
                digest.update(_canonical_json_bytes(values) + b"\n")
    return digest.hexdigest()


def _table_output_metadata(
    path: Path, schema: pa.Schema, key_columns: Iterable[str]
) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    logical_hash = _logical_sha256_parquet(path, schema, key_columns)
    return {
        "path": path.name,
        "sha256": _sha256_file(path),
        "logical_sha256": logical_hash,
        "byte_length": path.stat().st_size,
        "rows": int(parquet.metadata.num_rows),
        "schema": _schema_descriptor(schema),
    }


def _json_output_metadata(path: Path, semantic_hash: str) -> dict[str, Any]:
    value = _read_json_object(path)
    canonical_hash = _semantic_json_sha256(value)
    if canonical_hash != semantic_hash:
        raise ScenarioIntegrityError(
            f"JSON semantic hash changed during serialization: {path.name}."
        )
    return {
        "path": path.name,
        "sha256": _sha256_file(path),
        "canonical_json_sha256": canonical_hash,
        "byte_length": path.stat().st_size,
    }


def _range_for_column(table: pa.Table, name: str) -> dict[str, float | None]:
    array = table[name].combine_chunks()
    valid = pc.drop_null(array)
    if len(valid) == 0:
        return {"minimum": None, "maximum": None}
    result = pc.min_max(valid).as_py()
    return {"minimum": float(result["min"]), "maximum": float(result["max"])}


def _build_validation_summary(
    *,
    run_id: str,
    created_at_utc: str,
    config: Mapping[str, Any],
    tables: Mapping[str, pa.Table],
    validation: Mapping[str, Any],
    output_metadata: Mapping[str, Mapping[str, Any]],
    repeat_hashes: Mapping[str, str],
) -> dict[str, Any]:
    catalog = tables["scenario_catalog.parquet"].to_pylist()
    anchors = tables["origin_anchors.parquet"].to_pylist()
    parameters = tables["store_parameters.parquet"].to_pylist()
    daily = tables["scenario_daily.parquet"]
    anchor_by_origin: dict[date, list[dict[str, Any]]] = {}
    for row in anchors:
        anchor_by_origin.setdefault(row["forecast_origin"], []).append(row)
    availability_by_origin: list[dict[str, Any]] = []
    for origin in ALLOWED_ORIGINS:
        rows = anchor_by_origin[origin]
        unavailable_reasons: dict[str, int] = {}
        for row in rows:
            if row["unavailable_reason"] is not None:
                key = row["unavailable_reason"]
                unavailable_reasons[key] = unavailable_reasons.get(key, 0) + 1
        availability_by_origin.append(
            {
                "forecast_origin": origin.isoformat(),
                "stores": len(rows),
                "available_anchors": sum(bool(row["anchor_available"]) for row in rows),
                "unavailable_anchors": sum(not bool(row["anchor_available"]) for row in rows),
                "zero_anchors": sum(bool(row["zero_anchor"]) for row in rows),
                "unavailable_reasons": dict(sorted(unavailable_reasons.items())),
                "closed_positive_sales_rows": sum(
                    row["closed_positive_sales_rows"] for row in rows
                ),
                "missing_calendar_days": sum(row["missing_calendar_days"] for row in rows),
            }
        )

    params_by_scenario: dict[str, dict[str, int]] = {}
    for row in parameters:
        counts = params_by_scenario.setdefault(
            row["scenario_id"], {"available": 0, "unavailable": 0}
        )
        counts["available" if row["initialization_available"] else "unavailable"] += 1
    family_availability: list[dict[str, Any]] = []
    for scenario in catalog:
        counts = params_by_scenario[scenario["scenario_id"]]
        family_availability.append(
            {
                "scenario_id": scenario["scenario_id"],
                "family": scenario["family"],
                "forecast_origin": scenario["forecast_origin"].isoformat(),
                "replicate": int(scenario["replicate"]),
                "available_store_initializations": counts["available"],
                "unavailable_store_initializations": counts["unavailable"],
            }
        )

    parameter_ranges = {
        name: _range_for_column(tables["store_parameters.parquet"], name)
        for name in (
            "SupplierLeadTime",
            "ReviewPeriod",
            "ProtectionPeriod",
            "InventoryCoverageDays",
            "InitialStockOnHandValue",
            "ProcurementCostRatio",
            "AnnualHoldingRate",
            "HoldingCostRate",
            "GoodwillPenaltyRate",
            "StockoutPenalty",
            "AverageUnitValue",
            "TrendEndChange",
            "PromotionResponseSlope",
            "PlannedDiscountDepth",
        )
    }
    daily_ranges = {
        name: _range_for_column(daily, name)
        for name in (
            "DiscountDepth",
            "WeekdayFactor",
            "TrendFactor",
            "PromotionFactor",
            "CommonShock",
            "StoreDateNoise",
            "NoiseFactor",
            "DemandStressFactor",
            "SyntheticDemandValue",
        )
    }
    c = np.asarray(
        tables["store_parameters.parquet"]["ProcurementCostRatio"].to_numpy(), dtype="float64"
    )
    a = np.asarray(
        tables["store_parameters.parquet"]["AnnualHoldingRate"].to_numpy(), dtype="float64"
    )
    g = np.asarray(
        tables["store_parameters.parquet"]["GoodwillPenaltyRate"].to_numpy(), dtype="float64"
    )
    holding = np.asarray(
        tables["store_parameters.parquet"]["HoldingCostRate"].to_numpy(), dtype="float64"
    )
    penalty = np.asarray(
        tables["store_parameters.parquet"]["StockoutPenalty"].to_numpy(), dtype="float64"
    )
    valid_factors = pc.is_valid(daily["WeekdayFactor"])
    factors = {
        name: np.asarray(pc.filter(daily[name], valid_factors).to_numpy(), dtype="float64")
        for name in (
            "WeekdayFactor",
            "TrendFactor",
            "PromotionFactor",
            "NoiseFactor",
            "DemandStressFactor",
        )
    }
    combined = (
        factors["WeekdayFactor"]
        * factors["TrendFactor"]
        * factors["PromotionFactor"]
        * factors["NoiseFactor"]
        * factors["DemandStressFactor"]
    )
    expected_counts = {
        "scenario_catalog.parquet": 82
        if len(config["stores"]) == 1115
        else tables["scenario_catalog.parquet"].num_rows,
        "origin_anchors.parquet": 2230
        if len(config["stores"]) == 1115
        else tables["origin_anchors.parquet"].num_rows,
        "store_parameters.parquet": 91430
        if len(config["stores"]) == 1115
        else tables["store_parameters.parquet"].num_rows,
        "scenario_daily.parquet": 1280020
        if len(config["stores"]) == 1115
        else tables["scenario_daily.parquet"].num_rows,
    }
    actual_counts = {name: table.num_rows for name, table in tables.items()}
    unavailable = sum(item["unavailable_anchors"] for item in availability_by_origin)
    summary = {
        "run_id": run_id,
        "created_at_utc": created_at_utc,
        "schema_version": SCHEMA_VERSION,
        "status": "complete_with_unavailable_inputs" if unavailable else "complete",
        "checks": {
            "schema_and_primary_keys": "passed",
            "origin_and_horizon_boundary": "passed",
            "anchor_threshold_and_missingness": "passed",
            "parameter_ranges_and_cost_arithmetic": "passed",
            "scenario_overrides_and_common_random_numbers": "passed",
            "synthetic_demand_formula_and_factor_ceiling": "passed",
            "frozen_phase7_phase8_identity": "passed",
            "input_snapshot_rechecked_before_publication": "passed",
            "output_reread_and_logical_hash": "passed",
            "protected_holdout_values_read_or_hashed": False,
            "inventory_simulation_performed": False,
        },
        "expected_counts": expected_counts,
        "actual_counts": actual_counts,
        "availability_by_origin": availability_by_origin,
        "availability_by_scenario": family_availability,
        "parameter_ranges": parameter_ranges,
        "daily_factor_ranges": daily_ranges,
        "arithmetic_maxima": {
            "holding_cost_rate_abs_error": float(np.max(np.abs(holding - c * a / 365)))
            if len(c)
            else 0.0,
            "stockout_penalty_abs_error": float(np.max(np.abs(penalty - ((1 - c) + g))))
            if len(c)
            else 0.0,
            "combined_factor_maximum": float(np.max(combined)) if len(combined) else 0.0,
        },
        "logical_reproducibility": {
            "row_order_reversal": "passed",
            "logical_hashes_match": {
                name: repeat_hashes[name] == output_metadata[name]["logical_sha256"]
                for name in TABLE_SCHEMAS
            },
        },
        "logical_sha256": {name: output_metadata[name]["logical_sha256"] for name in TABLE_SCHEMAS},
        "exclusion_counts": {
            reason: sum(1 for row in anchors if row["unavailable_reason"] == reason)
            for reason in ("no_store_history", "insufficient_open_history")
        },
        "structural_failures": validation["structural_failures"],
    }
    return summary


def _git_value(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _source_code_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/rossmann_forecasting/inventory/scenarios.py",
        "scripts/generate_inventory_scenarios.py",
    ):
        path = root / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _package_versions() -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for package in ("numpy", "pandas", "pyarrow"):
        try:
            values[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            values[package] = None
    return values


def _assert_ignored(root: Path, relative_paths: Iterable[str]) -> None:
    for relative in relative_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", relative],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ScenarioIntegrityError(
                f"Refusing to publish non-ignored Phase 9 path: {relative}."
            )


def _atomic_publish(
    stage: Path, final_dir: Path, output_root: Path, pointer: Mapping[str, Any]
) -> None:
    if final_dir.exists():
        raise FileExistsError(f"Phase 9 run ID already exists: {final_dir}.")
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


def run_scenario_generation(
    root: str | Path | None = None, *, run_id: str = "phase9-dev-20261007-canonical1"
) -> dict[str, Any]:
    """Generate, validate and immutably publish the canonical Phase 9 dev-only bundle."""
    repository = Path(root or Path.cwd()).resolve()
    if not run_id or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for char in run_id
    ):
        raise ScenarioIntegrityError(
            "run_id may contain only ASCII letters, digits, hyphens and underscores."
        )
    output_root = repository / "data/processed/synthetic_inventory"
    final_dir = output_root / run_id
    _assert_ignored(
        repository,
        ["data/processed/synthetic_inventory", f"data/processed/synthetic_inventory/{run_id}"],
    )
    if final_dir.exists():
        raise FileExistsError(f"Phase 9 run ID already exists: {final_dir}.")

    initial_bindings = verify_frozen_bindings(repository)
    config = default_config(upstream_bindings=initial_bindings["bindings"])
    _validate_config(config, canonical_run=True)
    created_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    config["run_id"] = run_id
    config["created_at_utc"] = created_at_utc
    _seal_json(config, field_name="config_canonical_sha256")

    history_path = repository / "data/interim/train.parquet"
    histories = {
        origin: read_censored_history(history_path, origin=origin, stores=config["stores"])
        for origin in ALLOWED_ORIGINS
    }
    expected_anchor_digests = {
        origin: compute_origin_anchors(history, origin=origin, stores=config["stores"])[
            "history_logical_sha256"
        ].to_pylist()
        for origin, history in histories.items()
    }

    output_root.mkdir(parents=True, exist_ok=True)
    if final_dir.exists():
        raise FileExistsError(f"Phase 9 run ID already exists: {final_dir}.")
    stage = Path(tempfile.mkdtemp(prefix=f".phase9-stage-{run_id}-", dir=output_root))
    try:
        upstream = dict(initial_bindings["bindings"])
        upstream.update(
            {"run_id": run_id, "created_at_utc": created_at_utc, "canonical_sha256": None}
        )
        _seal_json(upstream, field_name="canonical_sha256")
        _write_json(stage / "scenario_config.json", config)
        _write_json(stage / "upstream_bindings.json", upstream)

        catalog, anchors, parameters, daily_batches = _build_generation_core(config, histories)
        _write_parquet_table(stage / "scenario_catalog.parquet", catalog)
        _write_parquet_table(stage / "origin_anchors.parquet", anchors)
        _write_parquet_table(stage / "store_parameters.parquet", parameters)
        daily_rows = _write_parquet_batches(
            stage / "scenario_daily.parquet", daily_batches(), DAILY_SCHEMA
        )
        if daily_rows != len(catalog.to_pylist()) * len(config["stores"]) * HORIZON_DAYS:
            raise ScenarioIntegrityError(
                "Generated daily-context row count differs from the designed grid."
            )

        tables = {
            name: pq.read_table(stage / name, columns=schema.names)
            for name, schema in TABLE_SCHEMAS.items()
        }
        validation = validate_scenario_tables(tables, config)
        parquet_metadata = {
            name: _table_output_metadata(stage / name, schema, TABLE_KEYS[name])
            for name, schema in TABLE_SCHEMAS.items()
        }

        repeat_histories = {
            origin: history.iloc[::-1].reset_index(drop=True)
            for origin, history in histories.items()
        }
        repeated_catalog, repeated_anchors, repeated_parameters, repeated_daily_batches = (
            _build_generation_core(config, repeat_histories)
        )
        repeat_hashes = {
            "scenario_catalog.parquet": logical_table_sha256(
                repeated_catalog, TABLE_KEYS["scenario_catalog.parquet"]
            ),
            "origin_anchors.parquet": logical_table_sha256(
                repeated_anchors, TABLE_KEYS["origin_anchors.parquet"]
            ),
            "store_parameters.parquet": logical_table_sha256(
                repeated_parameters, TABLE_KEYS["store_parameters.parquet"]
            ),
            "scenario_daily.parquet": _logical_sha256_batches(
                repeated_daily_batches(), DAILY_SCHEMA, TABLE_KEYS["scenario_daily.parquet"]
            ),
        }
        for name, expected in repeat_hashes.items():
            if expected != parquet_metadata[name]["logical_sha256"]:
                raise ScenarioIntegrityError(f"Repeated logical generation differs for {name}.")

        # Recheck frozen identities and the same censored history projection before publish.
        final_bindings = verify_frozen_bindings(repository)
        if _canonical_sha256(final_bindings["identity_snapshot"]) != _canonical_sha256(
            initial_bindings["identity_snapshot"]
        ):
            raise ScenarioIntegrityError("Frozen Phase 7/8 inputs changed during generation.")
        rechecked_history = {
            origin: read_censored_history(history_path, origin=origin, stores=config["stores"])
            for origin in ALLOWED_ORIGINS
        }
        for origin in ALLOWED_ORIGINS:
            digest = compute_origin_anchors(
                rechecked_history[origin], origin=origin, stores=config["stores"]
            )["history_logical_sha256"].to_pylist()
            if digest != expected_anchor_digests[origin]:
                raise ScenarioIntegrityError("Censored history changed during scenario generation.")

        summary = _build_validation_summary(
            run_id=run_id,
            created_at_utc=created_at_utc,
            config=config,
            tables=tables,
            validation=validation,
            output_metadata=parquet_metadata,
            repeat_hashes=repeat_hashes,
        )
        _seal_json(summary, field_name="canonical_sha256")
        _write_json(stage / "validation_summary.json", summary)
        json_values = {
            "scenario_config.json": config,
            "upstream_bindings.json": upstream,
            "validation_summary.json": summary,
        }
        output_metadata: dict[str, Any] = dict(parquet_metadata)
        for name, value in json_values.items():
            self_hash = (
                "config_canonical_sha256" if name == "scenario_config.json" else "canonical_sha256"
            )
            output_metadata[name] = _json_output_metadata(stage / name, value[self_hash])

        git_status = _git_value(repository, "status", "--porcelain")
        manifest = {
            "command": "python scripts/generate_inventory_scenarios.py",
            "arguments": {
                "run_id": run_id,
                "origins": [item.isoformat() for item in ALLOWED_ORIGINS],
            },
            "run_id": run_id,
            "created_at_utc": created_at_utc,
            "schema_version": SCHEMA_VERSION,
            "generator_version": GENERATOR_VERSION,
            "status": summary["status"],
            "seed": MASTER_SEED,
            "draw_algorithm": "sha256-counter-uniform-v1",
            "config": {
                "path": "scenario_config.json",
                "sha256": output_metadata["scenario_config.json"]["sha256"],
                "canonical_sha256": config["config_canonical_sha256"],
            },
            "source_provenance": {
                "phase2_source_identities": upstream["source_provenance"]["source_sha256"],
                "phase2_train_snapshot_sha256": upstream["source_provenance"][
                    "phase2_train_snapshot_sha256"
                ],
                "phase2_identity_status": (
                    "inherited from preparation manifest; full train file not rehashed"
                ),
                "history_source_path": "data/interim/train.parquet",
                "history_projection": list(HISTORY_COLUMNS),
                "history_window_predicate": "origin-55 <= Date <= origin and configured Store set",
                "history_logical_sha256_by_origin": {
                    origin.isoformat(): expected_anchor_digests[origin]
                    for origin in ALLOWED_ORIGINS
                },
                "history_rechecked_before_publication": True,
            },
            "upstream_bindings": {
                "path": "upstream_bindings.json",
                "sha256": output_metadata["upstream_bindings.json"]["sha256"],
                "canonical_sha256": upstream["canonical_sha256"],
            },
            "code_provenance": {
                "git_revision": _git_value(repository, "rev-parse", "HEAD"),
                "worktree_modified": bool(git_status),
                "source_files": [
                    "src/rossmann_forecasting/inventory/scenarios.py",
                    "scripts/generate_inventory_scenarios.py",
                ],
                "source_sha256": _source_code_digest(repository),
                "uv_lock_sha256": _sha256_file(repository / "uv.lock"),
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "packages": _package_versions(),
            },
            "inputs": {
                "identity_snapshot_sha256": _canonical_sha256(final_bindings["identity_snapshot"]),
                "phase7_selection_manifest_sha256": upstream["phase7"]["selection_manifest_sha256"],
                "phase8_manifest_sha256": upstream["phase8"]["manifest_sha256"],
            },
            "outputs": output_metadata,
            "validation": {
                "path": "validation_summary.json",
                "status": summary["status"],
                "structural_failures": summary["structural_failures"],
            },
            "boundaries": {
                "development_cutoff_inclusive": DEVELOPMENT_CUTOFF.isoformat(),
                "protected_holdout": "2015-07-04 through 2015-07-31",
                "protected_holdout_values_read_or_hashed": False,
                "full_train_parquet_rehashed": False,
                "phase8_residuals_recomputed": False,
                "model_refit_or_tuning": False,
                "inventory_simulation_performed": False,
                "forecast_or_uncertainty_used_as_synthetic_truth": False,
            },
        }
        expected_stage_files = set(output_metadata)
        if {path.name for path in stage.iterdir()} != expected_stage_files:
            raise ScenarioIntegrityError(
                "Staging output inventory contains unexpected or missing files."
            )
        _write_json(stage / "manifest.json", manifest)
        reread_manifest = _read_json_object(stage / "manifest.json")
        if reread_manifest.get("outputs") != output_metadata:
            raise ScenarioIntegrityError(
                "Staged manifest output identities differ from reread artifacts."
            )
        manifest_sha = _sha256_file(stage / "manifest.json")
        pointer = {
            "run_id": run_id,
            "manifest_path": f"{run_id}/manifest.json",
            "manifest_sha256": manifest_sha,
            "status": summary["status"],
        }
        _atomic_publish(stage, final_dir, output_root, pointer)
        return {
            "run_id": run_id,
            "run_directory": final_dir,
            "manifest": manifest,
            "manifest_sha256": manifest_sha,
            "validation_summary": summary,
        }
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
