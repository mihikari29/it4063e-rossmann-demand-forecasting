"""Descriptive, development-only monitoring of immutable issued forecasts and delayed labels.

No source reader, prediction generation, statistical alarm or retraining is provided here.
Callers must separately establish input authorization and authenticate issuance custody.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics

DEVELOPMENT_END = date(2015, 7, 3)
KINDS = {"retrospective_development_forecast", "controlled_synthetic_fixture"}
FEATURES = {"DayOfWeek", "Promo", "SchoolHoliday"}
FORECAST_FIELDS = {
    "Store",
    "forecast_origin",
    "target_date",
    "horizon",
    "prediction",
    "issued_on",
    "training_through",
    "model_id",
    "evidence_kind",
    "issuance_id",
    "issuance_sha256",
    "features",
    "features_available_on",
}
LABEL_FIELDS = {"Store", "target_date", "available_on", "actual_sales", "source_open"}


def _day(value: Any, field: str) -> date:
    if type(value) is not str:
        raise ValueError(f"{field} must be an ISO calendar date.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be an ISO calendar date.") from None
    if parsed.isoformat() != value or parsed > DEVELOPMENT_END:
        raise ValueError(f"{field} must be canonical and end by 2015-07-03.")
    return parsed


def _number(value: Any, field: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{field} must be finite and nonnegative.")
    return float(value)


def _store(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 1115:
        raise ValueError("Store must be an integer in 1..1115.")
    return value


def _identity(value: Any, field: str) -> str:
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value) is None:
        raise ValueError(f"Invalid {field}.")
    return value


def pair_forecasts(
    forecasts: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
    *,
    as_of: str,
) -> pd.DataFrame:
    """Validate issuance separately, then left-join labels available by the as-of day.

    Future labels supplied by the caller are rejected rather than silently filtered. A missing
    label is absence of evidence, never zero. Repeated Store/target labels are rejected even if
    their values agree. Overlapping origins can share one subsequently available label.
    """
    cutoff = _day(as_of, "as_of")
    if not forecasts:
        raise ValueError("At least one issued forecast is required.")
    rows: list[dict[str, Any]] = []
    keys: set[tuple[int, date, int]] = set()
    receipts: dict[str, tuple[Any, ...]] = {}
    identities: set[tuple[str, str]] = set()
    for record in forecasts:
        if set(record) != FORECAST_FIELDS:
            raise ValueError("Unexpected or missing issuance fields; labels cannot enter issuance.")
        store = _store(record["Store"])
        origin = _day(record["forecast_origin"], "forecast_origin")
        target = _day(record["target_date"], "target_date")
        issued = _day(record["issued_on"], "issued_on")
        trained = _day(record["training_through"], "training_through")
        feature_day = _day(record["features_available_on"], "features_available_on")
        horizon = record["horizon"]
        if type(horizon) is not int or not 1 <= horizon <= 14:
            raise ValueError("horizon must be an integer in 1..14.")
        if target != origin + timedelta(days=horizon):
            raise ValueError("target_date must equal forecast_origin + horizon calendar days.")
        if issued != origin or trained > origin or feature_day > origin or issued > cutoff:
            raise ValueError("Issuance, training and feature availability must be origin-safe.")
        model = _identity(record["model_id"], "model_id")
        kind = record["evidence_kind"]
        if kind not in KINDS:
            raise ValueError("Unsupported evidence_kind.")
        if kind == "controlled_synthetic_fixture" and not model.startswith("synthetic_"):
            raise ValueError("Synthetic fixtures require an explicitly synthetic model_id.")
        issuance = _identity(record["issuance_id"], "issuance_id")
        pin = record["issuance_sha256"]
        if type(pin) is not str or re.fullmatch(r"[0-9a-f]{64}", pin) is None:
            raise ValueError("issuance_sha256 must be a lowercase SHA-256.")
        receipt = (origin, issued, trained, model, kind, pin)
        if issuance in receipts and receipts[issuance] != receipt:
            raise ValueError("An issuance_id has inconsistent provenance.")
        receipts[issuance] = receipt
        identities.add((model, kind))
        key = (store, origin, horizon)
        if key in keys:
            raise ValueError("Duplicate forecast key.")
        keys.add(key)
        features = record["features"]
        if not isinstance(features, Mapping) or not set(features) <= FEATURES:
            raise ValueError("Only declared origin-known calendar/planned features are supported.")
        feature_values = {}
        for name, value in features.items():
            feature_values[name] = _number(value, name, nullable=True)
            allowed = range(1, 8) if name == "DayOfWeek" else (0, 1)
            if value is not None and (type(value) is not int or value not in allowed):
                raise ValueError(f"Invalid {name} category.")
        rows.append(
            {
                **{name: record[name] for name in FORECAST_FIELDS - {"features"}},
                "Store": store,
                "forecast_origin": origin,
                "target_date": target,
                "prediction": _number(record["prediction"], "prediction", nullable=True),
                **{f"feature_{name}": feature_values.get(name) for name in sorted(FEATURES)},
            }
        )
    if len(identities) != 1:
        raise ValueError("Monitor exactly one model and evidence kind at a time.")

    target_keys = {(row["Store"], row["target_date"]) for row in rows}
    observed: dict[tuple[int, date], dict[str, Any]] = {}
    for label in labels:
        if set(label) != LABEL_FIELDS:
            raise ValueError("Unexpected or missing label fields.")
        store = _store(label["Store"])
        target = _day(label["target_date"], "label target_date")
        available = _day(label["available_on"], "available_on")
        if not target <= available <= cutoff:
            raise ValueError("Labels must become available after their target and by as_of.")
        key = (store, target)
        if key not in target_keys or key in observed:
            raise ValueError("Duplicate or unmatched label key.")
        source_open = label["source_open"]
        if source_open is not None and (type(source_open) is not int or source_open not in (0, 1)):
            raise ValueError("source_open must be 0, 1, or null.")
        observed[key] = {
            "actual_sales": _number(label["actual_sales"], "actual_sales", nullable=True),
            "source_open": source_open,
            "label_available_on": available.isoformat(),
        }
    for row in rows:
        row.update(
            observed.get(
                (row["Store"], row["target_date"]),
                {
                    "actual_sales": None,
                    "source_open": None,
                    "label_available_on": None,
                },
            )
        )
    frame = pd.DataFrame(rows).sort_values(["forecast_origin", "Store", "horizon"])
    frame["forecast_available"] = frame["prediction"].notna()
    frame["validation_window"] = frame["forecast_origin"].map(date.isoformat)
    frame["primary_evaluation_eligible"] = (
        frame["source_open"].eq(1) & frame["actual_sales"].notna() & frame["forecast_available"]
    )
    frame.attrs["as_of"] = cutoff.isoformat()
    return frame.reset_index(drop=True)


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    observed = frame.loc[frame["actual_sales"].notna()]
    result = summarize_forecast_metrics(observed, scope="monitoring", forecast_column="prediction")
    result["requested_forecast_keys"] = len(frame)
    result["requested_forecast_available_rows"] = int(frame["forecast_available"].sum())
    result["missing_actual_rows"] = int(frame["actual_sales"].isna().sum())
    result["closed_label_rows"] = int(
        (frame["source_open"].eq(0) & frame["actual_sales"].notna()).sum()
    )
    result["closed_positive_sales_rows"] = int(
        (frame["source_open"].eq(0) & frame["actual_sales"].gt(0)).sum()
    )
    result["unknown_open_rows"] = int(frame["source_open"].isna().sum())
    return result


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "pooled": _metrics(frame),
        "by_store": [
            {"Store": int(key), **_metrics(group)}
            for key, group in frame.groupby("Store", sort=True)
        ],
        "by_origin": [
            {"forecast_origin": key.isoformat(), **_metrics(group)}
            for key, group in frame.groupby("forecast_origin", sort=True)
        ],
        "by_horizon": [
            {**_metrics(group), "horizon": int(key)}
            for key, group in frame.groupby("horizon", sort=True)
        ],
    }


def _features(reference: pd.DataFrame, current: pd.DataFrame) -> list[dict[str, Any]]:
    summaries = []
    for name in sorted(FEATURES):
        column = f"feature_{name}"
        populations = {}
        for scope, frame in (("reference", reference), ("current", current)):
            values = frame[column].dropna().astype(float)
            populations[scope] = {
                "rows": len(frame),
                "available": len(values),
                "missing": int(frame[column].isna().sum()),
                "q25": float(values.quantile(0.25)) if len(values) else None,
                "median": float(values.median()) if len(values) else None,
                "q75": float(values.quantile(0.75)) if len(values) else None,
                "distinct_values": int(values.nunique()),
                "frequencies": {
                    str(int(key)): int(count) / len(values)
                    for key, count in values.value_counts().sort_index().items()
                },
            }
        ref, cur = populations["reference"], populations["current"]
        supported = ref["available"] >= 2 and cur["available"] >= 2
        summaries.append(
            {
                "feature": name,
                **populations,
                "state": "DESCRIPTIVE_ONLY" if supported else "INSUFFICIENT_SAMPLE",
                "reference_constant": ref["distinct_values"] == 1 if ref["available"] else None,
                "median_difference": cur["median"] - ref["median"] if supported else None,
                "test": "quartiles_and_category_frequencies_no_significance_test",
            }
        )
    return summaries


def build_monitoring_summary(
    forecasts: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
    *,
    as_of: str,
    reference_start: str,
    reference_end: str,
    current_start: str,
    current_end: str,
    generated_at: str,
) -> dict[str, Any]:
    """Build one shared payload using calendar windows, never open-day counts."""
    frame = pair_forecasts(forecasts, labels, as_of=as_of)
    try:
        timestamp = datetime.fromisoformat(generated_at)
    except (ValueError, TypeError):
        raise ValueError("generated_at must be an ISO timestamp with timezone.") from None
    if timestamp.tzinfo is None:
        raise ValueError("generated_at must be an ISO timestamp with timezone.")
    rs, re_, cs, ce = [
        _day(value, "window")
        for value in (reference_start, reference_end, current_start, current_end)
    ]
    cutoff = _day(as_of, "as_of")
    if not rs <= re_ < cs <= ce <= cutoff:
        raise ValueError("Reference must precede current without overlap; windows end by as_of.")
    reference = frame.loc[frame["target_date"].between(rs, re_)]
    current = frame.loc[frame["target_date"].between(cs, ce)]
    windows = []
    for end in pd.date_range(cs, ce):
        end_day = end.date()
        for days in (1, 7, 14):
            nominal_start = end_day - timedelta(days=days - 1)
            effective_start = max(cs, nominal_start)
            selected = current.loc[current["target_date"].between(effective_start, end_day)]
            windows.append(
                {
                    "start": effective_start.isoformat(),
                    "end": end_day.isoformat(),
                    "nominal_days": days,
                    "calendar_days": (end_day - effective_start).days + 1,
                    "partial": effective_start != nominal_start,
                    "observed_label_dates": int(
                        selected.loc[selected["actual_sales"].notna(), "target_date"].nunique()
                    ),
                    "multi_origin": selected["forecast_origin"].nunique() > 1,
                    **_summary(selected),
                }
            )
    metrics = _metrics(current)
    status = (
        "UNAVAILABLE"
        if not metrics["eligible_rows"]
        else "PARTIAL_EVIDENCE"
        if metrics["missing_actual_rows"]
        or metrics["requested_forecast_available_rows"] != metrics["requested_forecast_keys"]
        or metrics["open_label_rows"] != metrics["eligible_rows"]
        or metrics["unknown_open_rows"]
        else "DESCRIPTIVE_ONLY"
    )
    return {
        "schema_version": "1.0.0",
        "status": status,
        "generated_at": generated_at,
        "as_of": as_of,
        "evidence_kind": frame["evidence_kind"].iloc[0],
        "model_id": frame["model_id"].iloc[0],
        "reference_window": {"start": reference_start, "end": reference_end},
        "current_window": {"start": current_start, "end": current_end},
        "reference": _summary(reference),
        "current": _summary(current),
        "windows": windows,
        "feature_comparison": _features(reference, current),
        "issuances": [
            {
                "issuance_id": key,
                "sha256": group["issuance_sha256"].iloc[0],
                "forecast_origin": group["forecast_origin"].iloc[0].isoformat(),
            }
            for key, group in frame.groupby("issuance_id", sort=True)
        ],
        "human_review": "Inspect data quality, coverage and descriptive differences; separate "
        "approval is required for retraining or promotion.",
        "limitations": [
            "Retrospective development or synthetic evidence; no post-deployment observations.",
            "Hashes establish consistency, not issuance authenticity, custody or data permission.",
            "No statistical alarm, persistence trigger, automatic retraining or health claim.",
            "Origin-known calendar/planned feature availability is a caller-declared assumption.",
            "MAPE excludes zero actuals; WAPE is a ratio; primary errors use observed Open=1.",
        ],
    }


def synthetic_monitoring_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Author predictions from calendar/store, independently of subsequent labels."""
    forecasts = []
    for origin in (date(2015, 6, 5), date(2015, 6, 19)):
        issued = []
        for store in (101, 202, 303):
            for horizon in range(1, 15):
                target = origin + timedelta(days=horizon)
                issued.append(
                    {
                        "Store": store,
                        "forecast_origin": origin.isoformat(),
                        "target_date": target.isoformat(),
                        "horizon": horizon,
                        "prediction": float(6000 + store + 50 * target.weekday()),
                        "issued_on": origin.isoformat(),
                        "training_through": origin.isoformat(),
                        "features_available_on": origin.isoformat(),
                        "model_id": "synthetic_calendar_fixture",
                        "evidence_kind": "controlled_synthetic_fixture",
                        "issuance_id": f"synthetic_{origin:%Y%m%d}",
                        "features": {"DayOfWeek": target.isoweekday(), "Promo": int(horizon <= 5)},
                    }
                )
        pin = hashlib.sha256(json.dumps(issued, sort_keys=True).encode()).hexdigest()
        forecasts.extend({**row, "issuance_sha256": pin} for row in issued)
    labels = []
    for row in forecasts:
        target = date.fromisoformat(row["target_date"])
        # Label mechanism is independent of the prediction field and may disagree with it.
        actual = float(6200 + row["Store"] + 70 * target.weekday())
        labels.append(
            {
                "Store": row["Store"],
                "target_date": target.isoformat(),
                "available_on": target.isoformat(),
                "source_open": int(target.weekday() < 6),
                "actual_sales": actual if target.weekday() < 6 else 0.0,
            }
        )
    return forecasts, labels
