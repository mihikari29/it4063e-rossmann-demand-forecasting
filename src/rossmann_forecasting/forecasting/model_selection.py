"""Integrity-checked Phase 7 development-only model comparison and selection."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow
import statsmodels

from rossmann_forecasting.data.acquisition import sha256_file
from rossmann_forecasting.data.preparation import SOURCE_SNAPSHOT_SHA256
from rossmann_forecasting.features.contract import (
    FEATURE_CONTRACT_VERSION,
    PREDICTOR_COLUMNS,
    predictor_schema,
)
from rossmann_forecasting.forecasting.holt_winters import FORECAST_COLUMN as HW_FORECAST_COLUMN
from rossmann_forecasting.forecasting.lightgbm import (
    FIXED_PARAMETERS as LIGHTGBM_FIXED_PARAMETERS,
)
from rossmann_forecasting.forecasting.lightgbm import (
    FORECAST_COLUMN as LIGHTGBM_FORECAST_COLUMN,
)
from rossmann_forecasting.forecasting.lightgbm import (
    MODEL_NAME as LIGHTGBM_MODEL_NAME,
)
from rossmann_forecasting.forecasting.lightgbm_evaluation import TRIAL_PARAMETERS
from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    FINAL_HOLDOUT_START,
    LAST_DEVELOPMENT_DATE,
)

CANDIDATE_IDS = (
    "seasonal_naive",
    "holt_winters_additive_weekly",
    "global_lightgbm_gbdt_regression_l1",
)
FORECAST_COLUMNS = {
    CANDIDATE_IDS[0]: "raw_baseline_forecast",
    CANDIDATE_IDS[1]: HW_FORECAST_COLUMN,
    CANDIDATE_IDS[2]: LIGHTGBM_FORECAST_COLUMN,
}
MODEL_SELECTION_POLICY_VERSION = "phase-7-adr-020-v1"
OPERATIONAL_REVIEW_SCHEMA_VERSION = "phase-7-operational-review-v1"
OPERATIONAL_SCOPE = "offline_cpu_course_demonstration"
COVERAGE_THRESHOLD = 0.99
PROMOTION_THRESHOLD = 0.05
REGRESSION_CAP = 0.10
KEY_COLUMNS = ("Store", "forecast_origin", "Date")
BASE_COLUMNS = (
    "Store",
    "forecast_origin",
    "Date",
    "horizon",
    "validation_window",
    "actual_sales",
    "source_open",
)
_WINDOWS = {
    window.name: {
        "origin": window.forecast_origin,
        "start": window.target_start,
        "end": window.target_end,
    }
    for window in APPROVED_DEVELOPMENT_WINDOWS
}
_SN_FOLDER = "seasonal_naive"
_HW_FOLDER = "holt_winters"
_LGBM_FOLDER = "lightgbm"
_FOLDERS = {
    CANDIDATE_IDS[0]: _SN_FOLDER,
    CANDIDATE_IDS[1]: _HW_FOLDER,
    CANDIDATE_IDS[2]: _LGBM_FOLDER,
}
_COMMANDS = {
    CANDIDATE_IDS[0]: "rossmann-seasonal-naive",
    CANDIDATE_IDS[1]: "rossmann-holt-winters",
    CANDIDATE_IDS[2]: "rossmann-lightgbm",
}
POLICY_CONFIGURATION = {
    "candidate_order": list(CANDIDATE_IDS),
    "coverage_threshold_per_window": COVERAGE_THRESHOLD,
    "primary_population": (
        "observed Open=1 and observed Sales; identical candidate availability for numeric selection"
    ),
    "pooled_mae_improvement_fraction": PROMOTION_THRESHOLD,
    "minimum_strict_window_wins": 2,
    "window_regression_cap_fraction": REGRESSION_CAP,
    "pooled_week_blocks": [[1, 7], [8, 14]],
    "tie_behavior": "retain simpler incumbent",
    "per_horizon_veto": False,
    "model_mixing": False,
}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


class EvidenceReviewRequired(ValueError):
    """Raised when cached evidence cannot safely support model selection."""


@dataclass(frozen=True)
class CandidateEvidence:
    candidate_id: str
    manifest_path: Path
    manifest: dict[str, Any]
    manifest_sha256: str
    artifact_hashes: dict[str, str]
    configuration: dict[str, Any] | None


def _equal_with_nulls(left: pd.Series, right: pd.Series) -> pd.Series:
    return left.eq(right) | (left.isna() & right.isna())


def _boolean_mask(values: pd.Series, *, name: str) -> pd.Series:
    if values.isna().any() or not values.isin([True, False, 0, 1]).all():
        raise EvidenceReviewRequired(f"{name} mask must contain only explicit booleans.")
    return values.astype(bool)


def _normalise_candidate_frame(candidate_id: str, frame: pd.DataFrame) -> pd.DataFrame:
    if candidate_id not in CANDIDATE_IDS:
        raise EvidenceReviewRequired(f"Unexpected candidate ID: {candidate_id}.")
    raw_column = FORECAST_COLUMNS[candidate_id]
    required = set(BASE_COLUMNS) | {
        raw_column,
        "forecast_available",
        "primary_evaluation_eligible",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise EvidenceReviewRequired(
            f"{candidate_id} forecast records are missing required fields: {sorted(missing)}."
        )

    result = frame.copy(deep=True)
    for column in ("Store",):
        values = pd.to_numeric(result[column], errors="coerce")
        if values.isna().any() or values.mod(1).ne(0).any() or values.le(0).any():
            raise EvidenceReviewRequired(f"{candidate_id} has invalid {column} keys.")
        result[column] = values.astype("int64")
    for column in ("forecast_origin", "Date"):
        values = pd.to_datetime(result[column], errors="coerce")
        if values.isna().any() or values.dt.normalize().ne(values).any():
            raise EvidenceReviewRequired(
                f"{candidate_id} has invalid or non-midnight {column} values."
            )
        result[column] = values.dt.normalize()
    if result.duplicated(list(KEY_COLUMNS)).any():
        raise EvidenceReviewRequired(f"{candidate_id} forecast keys are not unique.")

    horizon = pd.to_numeric(result["horizon"], errors="coerce")
    if horizon.isna().any() or horizon.mod(1).ne(0).any():
        raise EvidenceReviewRequired(f"{candidate_id} forecast horizons must be integer days.")
    horizon = horizon.astype("int16")
    if horizon.lt(1).any() or horizon.gt(14).any():
        raise EvidenceReviewRequired(f"{candidate_id} forecast horizons must be within 1..14.")
    expected_horizon = (result["Date"] - result["forecast_origin"]).dt.days
    if horizon.ne(expected_horizon).any():
        raise EvidenceReviewRequired(f"{candidate_id} horizon disagrees with its origin and Date.")
    result["horizon"] = horizon.astype("int8")

    windows = result["validation_window"].astype("string")
    for name, metadata in _WINDOWS.items():
        mask = windows.eq(name)
        if mask.any():
            if result.loc[mask, "forecast_origin"].ne(metadata["origin"]).any():
                raise EvidenceReviewRequired(f"{candidate_id} has an unexpected origin for {name}.")
            if not result.loc[mask, "Date"].between(metadata["start"], metadata["end"]).all():
                raise EvidenceReviewRequired(f"{candidate_id} has an unexpected date for {name}.")
    if windows.isna().any() or not windows.isin(_WINDOWS).all():
        raise EvidenceReviewRequired(f"{candidate_id} contains an unapproved validation window.")
    if result["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        raise EvidenceReviewRequired(f"{candidate_id} includes rows after 2015-07-03.")
    result["validation_window"] = windows.astype(str)

    actual = pd.to_numeric(result["actual_sales"], errors="coerce")
    invalid_actual = result["actual_sales"].notna() & actual.isna()
    invalid_actual |= actual.notna() & (
        ~np.isfinite(actual.to_numpy(dtype=np.float64, na_value=np.nan)) | actual.lt(0)
    )
    if invalid_actual.any():
        raise EvidenceReviewRequired(f"{candidate_id} contains invalid observed Sales labels.")
    source_open = pd.to_numeric(result["source_open"], errors="coerce")
    invalid_open = result["source_open"].notna() & source_open.isna()
    invalid_open |= source_open.notna() & ~source_open.isin([0, 1])
    if invalid_open.any():
        raise EvidenceReviewRequired(f"{candidate_id} source Open must be 0, 1, or missing.")
    raw = pd.to_numeric(result[raw_column], errors="coerce")
    invalid_raw = result[raw_column].notna() & raw.isna()
    invalid_raw |= raw.notna() & (
        ~np.isfinite(raw.to_numpy(dtype=np.float64, na_value=np.nan)) | raw.lt(0)
    )
    if invalid_raw.any():
        raise EvidenceReviewRequired(
            f"{candidate_id} available raw forecasts must be finite and non-negative."
        )
    available = _boolean_mask(result["forecast_available"], name=f"{candidate_id} available")
    eligible = _boolean_mask(result["primary_evaluation_eligible"], name=f"{candidate_id} eligible")
    if not available.reset_index(drop=True).equals(raw.notna().reset_index(drop=True)):
        raise EvidenceReviewRequired(f"{candidate_id} available mask disagrees with raw forecasts.")
    expected_eligible = source_open.eq(1) & actual.notna() & raw.notna()
    if not eligible.reset_index(drop=True).equals(expected_eligible.reset_index(drop=True)):
        raise EvidenceReviewRequired(
            f"{candidate_id} eligible mask disagrees with labels/Open/raw availability."
        )

    result["actual_sales"] = actual.astype("float64")
    result["source_open"] = source_open.astype("float64")
    result["raw_model_forecast"] = raw.astype("float64")
    result["forecast_available"] = available.to_numpy(dtype=bool)
    result["primary_evaluation_eligible"] = eligible.to_numpy(dtype=bool)
    unavailable_reason = pd.Series(None, index=result.index, dtype="object")
    for reason_column in ("unavailable_reason", "fit_failure_reason"):
        if reason_column in result:
            reason_values = result[reason_column].astype("object")
            unavailable_reason = unavailable_reason.where(unavailable_reason.notna(), reason_values)
    unavailable_reason = unavailable_reason.where(
        unavailable_reason.notna(), "not_recorded_in_original_forecast_artifact"
    )
    result["forecast_unavailable_reason"] = unavailable_reason.where(raw.isna(), None)
    result["candidate_id"] = candidate_id
    return result.sort_values(list(KEY_COLUMNS), kind="mergesort").reset_index(drop=True)


def validate_candidate_records(
    records_by_candidate: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Validate exact candidate/window/key/label/mask identity using outer joins."""

    if set(records_by_candidate) != set(CANDIDATE_IDS) or len(records_by_candidate) != 3:
        raise EvidenceReviewRequired(
            f"Candidate IDs must be exactly {list(CANDIDATE_IDS)} in the approved population."
        )
    normalized = {
        candidate: _normalise_candidate_frame(candidate, records_by_candidate[candidate])
        for candidate in CANDIDATE_IDS
    }
    joined = normalized[CANDIDATE_IDS[0]][list(KEY_COLUMNS)].copy()
    for candidate in CANDIDATE_IDS[1:]:
        keys = normalized[candidate][list(KEY_COLUMNS)]
        joined = joined.merge(
            keys,
            on=list(KEY_COLUMNS),
            how="outer",
            validate="one_to_one",
            indicator=f"_merge_{candidate}",
        )
        if not joined[f"_merge_{candidate}"].eq("both").all():
            raise EvidenceReviewRequired(
                "Candidate target key populations differ in an outer join."
            )
        joined = joined.drop(columns=f"_merge_{candidate}")
    reference = normalized[CANDIDATE_IDS[0]].set_index(list(KEY_COLUMNS))
    for candidate in CANDIDATE_IDS[1:]:
        compared = normalized[candidate].set_index(list(KEY_COLUMNS)).reindex(reference.index)
        for column in ("horizon", "validation_window", "actual_sales", "source_open"):
            if not _equal_with_nulls(reference[column], compared[column]).all():
                raise EvidenceReviewRequired(
                    f"Candidates disagree on shared target {column} labels or window metadata."
                )
    return normalized


def _metric_scopes(
    frame: pd.DataFrame,
) -> list[tuple[str, str | None, int | None, int | None, int | None, pd.DataFrame]]:
    scopes: list[tuple[str, str | None, int | None, int | None, int | None, pd.DataFrame]] = [
        ("pooled", None, None, None, None, frame)
    ]
    scopes.extend(
        (
            "validation_window",
            window.name,
            None,
            None,
            None,
            frame.loc[frame["validation_window"].eq(window.name)],
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    )
    scopes.extend(
        ("horizon", None, step, None, None, frame.loc[frame["horizon"].eq(step)])
        for step in range(1, 15)
    )
    scopes.extend(
        (
            "week_block",
            None,
            None,
            first,
            last,
            frame.loc[frame["horizon"].between(first, last)],
        )
        for first, last in ((1, 7), (8, 14))
    )
    scopes.extend(
        ("store", None, None, None, None, group)
        for _, group in frame.groupby("Store", sort=True, observed=True)
    )
    return scopes


def _metric_rows(
    frame: pd.DataFrame,
    *,
    candidate_id: str,
    population: str,
    paired_with: str | None,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    prepared = frame.drop(columns=FORECAST_COLUMNS[candidate_id]).rename(
        columns={"raw_model_forecast": "raw_baseline_forecast"}
    )
    for scope, window, horizon, first_step, last_step, subset in _metric_scopes(prepared):
        metric_scope = "pooled_development" if scope == "pooled" else scope
        summary = summarize_forecast_metrics(
            subset,
            scope=metric_scope,
            validation_window=window,
            horizon=horizon,
            forecast_column="raw_baseline_forecast",
        )
        data = subset
        eligible = data["primary_evaluation_eligible"].astype(bool)
        actual = data.loc[eligible, "actual_sales"].to_numpy(dtype=np.float64)
        forecast = data.loc[eligible, "raw_baseline_forecast"].to_numpy(dtype=np.float64)
        absolute_sum = float(np.abs(actual - forecast).sum()) if eligible.any() else None
        squared_sum = float(np.square(actual - forecast).sum()) if eligible.any() else None
        positive = actual > 0
        percentage_sum = (
            float((np.abs(actual[positive] - forecast[positive]) / actual[positive]).sum())
            if positive.any()
            else None
        )
        metric_values: dict[str, tuple[Any, Any, Any, str | None]] = {
            "mae": (
                summary["mae"],
                absolute_sum,
                summary["eligible_rows"],
                summary["metrics_unavailable_reason"],
            ),
            "rmse": (
                summary["rmse"],
                squared_sum,
                summary["eligible_rows"],
                summary["metrics_unavailable_reason"],
            ),
            "mape": (
                summary["mape"],
                percentage_sum,
                summary["mape_rows"],
                summary["mape_unavailable_reason"],
            ),
            "wape": (
                summary["wape"],
                absolute_sum,
                summary["wape_actual_denominator"],
                summary["wape_unavailable_reason"],
            ),
            "eligible_rows": (
                summary["eligible_rows"],
                summary["eligible_rows"],
                summary["observed_target_rows"],
                None,
            ),
            "observed_target_rows": (
                summary["observed_target_rows"],
                summary["observed_target_rows"],
                None,
                None,
            ),
            "forecast_available_rows": (
                summary["forecast_available_rows"],
                summary["forecast_available_rows"],
                summary["forecast_available_denominator_rows"],
                None,
            ),
            "raw_forecast_coverage_rate": (
                summary["raw_forecast_coverage_rate"],
                summary["forecast_available_rows"],
                summary["forecast_available_denominator_rows"],
                summary["raw_forecast_coverage_unavailable_reason"],
            ),
            "open_label_rows": (
                summary["open_label_rows"],
                summary["open_label_rows"],
                summary["open_label_coverage_denominator_rows"],
                None,
            ),
            "open_label_forecast_available_rows": (
                summary["open_label_forecast_available_rows"],
                summary["open_label_forecast_available_rows"],
                summary["open_label_rows"],
                None,
            ),
            "open_label_forecast_coverage_rate": (
                summary["open_label_forecast_coverage_rate"],
                summary["open_label_forecast_available_rows"],
                summary["open_label_coverage_denominator_rows"],
                summary["open_label_coverage_unavailable_reason"],
            ),
            "mape_rows": (
                summary["mape_rows"],
                summary["mape_rows"],
                summary["eligible_rows"],
                summary["mape_unavailable_reason"] if not summary["mape_rows"] else None,
            ),
            "zero_actual_rows_excluded_from_mape": (
                summary["zero_actual_rows_excluded_from_mape"],
                summary["zero_actual_rows_excluded_from_mape"],
                summary["eligible_rows"],
                None,
            ),
            "wape_actual_denominator": (
                summary["wape_actual_denominator"],
                summary["wape_actual_denominator"],
                None,
                summary["wape_unavailable_reason"] if summary["wape"] is None else None,
            ),
        }
        for metric, (value, numerator, denominator, reason) in metric_values.items():
            output.append(
                {
                    "candidate_id": candidate_id,
                    "population": population,
                    "paired_with": paired_with,
                    "scope": scope,
                    "validation_window": window,
                    "horizon": horizon,
                    "week_block_start_horizon": first_step,
                    "week_block_end_horizon": last_step,
                    "Store": int(data["Store"].iloc[0]) if scope == "store" and len(data) else None,
                    "metric": metric,
                    "value": value,
                    "numerator": numerator,
                    "denominator": denominator,
                    "unavailable_reason": reason,
                    "paired_mae_delta": None,
                    "paired_mae_change_fraction": None,
                }
            )
        if "forecast_unavailable_reason" in data:
            unavailable = data.loc[
                data["raw_baseline_forecast"].isna(), "forecast_unavailable_reason"
            ]
            counts = unavailable.fillna("not_recorded_in_original_forecast_artifact").value_counts(
                sort=True, dropna=False
            )
            for unavailable_reason, count in counts.items():
                output.append(
                    {
                        "candidate_id": candidate_id,
                        "population": population,
                        "paired_with": paired_with,
                        "scope": scope,
                        "validation_window": window,
                        "horizon": horizon,
                        "week_block_start_horizon": first_step,
                        "week_block_end_horizon": last_step,
                        "Store": int(data["Store"].iloc[0])
                        if scope == "store" and len(data)
                        else None,
                        "metric": "forecast_unavailable_reason",
                        "value": int(count),
                        "numerator": int(count),
                        "denominator": len(data),
                        "unavailable_reason": str(unavailable_reason),
                        "paired_mae_delta": None,
                        "paired_mae_change_fraction": None,
                    }
                )
    return output


def _comparison_metrics(records: dict[str, pd.DataFrame]) -> pd.DataFrame:
    output: list[dict[str, Any]] = []
    populations: list[tuple[str, tuple[str, ...]]] = [
        ("standalone", (candidate,)) for candidate in CANDIDATE_IDS
    ]
    populations.extend(
        ("pairwise", pair)
        for pair in (
            (CANDIDATE_IDS[0], CANDIDATE_IDS[1]),
            (CANDIDATE_IDS[0], CANDIDATE_IDS[2]),
            (CANDIDATE_IDS[1], CANDIDATE_IDS[2]),
        )
    )
    populations.append(("three_way_common", CANDIDATE_IDS))
    for population, members in populations:
        available = pd.Series(True, index=records[members[0]].index)
        for candidate in members:
            available &= records[candidate]["raw_model_forecast"].notna()
        masked_frames: dict[str, pd.DataFrame] = {}
        for candidate in members:
            frame = records[candidate].copy(deep=True)
            if len(frame) != len(available):
                raise AssertionError("Validated candidate rows lost aligned sorted order.")
            if population != "standalone":
                peer_unavailable = ~available & frame["raw_model_forecast"].notna()
                frame.loc[~available, "raw_model_forecast"] = np.nan
                frame.loc[peer_unavailable, "forecast_unavailable_reason"] = (
                    "excluded_from_common_comparison_due_to_peer_unavailability"
                )
                frame["forecast_available"] = frame["raw_model_forecast"].notna()
                frame["primary_evaluation_eligible"] = (
                    frame["source_open"].eq(1)
                    & frame["actual_sales"].notna()
                    & frame["raw_model_forecast"].notna()
                )
            masked_frames[candidate] = frame
        for candidate in members:
            references = [item for item in members if item != candidate]
            ref = references[0] if references else None
            if population == "three_way_common":
                ref = None if candidate == CANDIDATE_IDS[0] else CANDIDATE_IDS[0]
            output.extend(
                _metric_rows(
                    masked_frames[candidate],
                    candidate_id=candidate,
                    population=population,
                    paired_with=ref,
                )
            )
    result = pd.DataFrame(output)
    group_fields = [
        "population",
        "scope",
        "validation_window",
        "horizon",
        "week_block_start_horizon",
        "week_block_end_horizon",
        "Store",
    ]
    mae_rows = result.loc[result["metric"].eq("mae")]

    def _scope_key(row: pd.Series) -> tuple[Any, ...]:
        return tuple(None if pd.isna(row[field]) else row[field] for field in group_fields)

    mae_lookup = {
        (*_scope_key(row), row["candidate_id"]): row["value"] for _, row in mae_rows.iterrows()
    }
    for index, row in mae_rows.iterrows():
        reference = row["paired_with"]
        if pd.isna(reference) or pd.isna(row["value"]):
            continue
        reference_mae = mae_lookup.get((*_scope_key(row), reference))
        if reference_mae is None or pd.isna(reference_mae):
            continue
        candidate_mae = float(row["value"])
        reference_mae = float(reference_mae)
        result.at[index, "paired_mae_delta"] = candidate_mae - reference_mae
        if reference_mae != 0:
            result.at[index, "paired_mae_change_fraction"] = candidate_mae / reference_mae - 1.0
    order = {candidate: index for index, candidate in enumerate(CANDIDATE_IDS)}
    result["_candidate_order"] = result["candidate_id"].map(order)
    result = result.sort_values(
        [
            "population",
            "_candidate_order",
            "scope",
            "validation_window",
            "horizon",
            "Store",
            "metric",
        ],
        kind="mergesort",
        na_position="first",
    ).drop(columns="_candidate_order")
    return result.reset_index(drop=True)


def _summary_lookup(
    metrics: pd.DataFrame,
    population: str,
    candidate: str,
    scope: str,
    *,
    window: str | None = None,
    horizon: int | None = None,
    metric: str = "mae",
) -> float | None:
    mask = (
        metrics["population"].eq(population)
        & metrics["candidate_id"].eq(candidate)
        & metrics["scope"].eq(scope)
        & metrics["metric"].eq(metric)
    )
    if window is not None:
        mask &= metrics["validation_window"].eq(window)
    if horizon is not None:
        mask &= metrics["horizon"].eq(horizon)
    if scope in {"pooled", "week_block"}:
        mask &= metrics["validation_window"].isna()
    if scope == "pooled":
        mask &= metrics["horizon"].isna() & metrics["week_block_start_horizon"].isna()
    rows = metrics.loc[mask, "value"]
    return None if rows.empty or pd.isna(rows.iloc[0]) else float(rows.iloc[0])


def _coverage_audit(metrics: pd.DataFrame) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    passed = True
    targets = [("standalone", candidate) for candidate in CANDIDATE_IDS]
    targets.append(("three_way_common", CANDIDATE_IDS[0]))
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        for population, candidate in targets:
            matches = metrics.loc[
                metrics["population"].eq(population)
                & metrics["candidate_id"].eq(candidate)
                & metrics["scope"].eq("validation_window")
                & metrics["validation_window"].eq(window.name)
                & metrics["metric"].eq("open_label_forecast_coverage_rate")
            ]
            row = matches.iloc[0] if len(matches) == 1 else None
            rate = None if row is None or pd.isna(row["value"]) else float(row["value"])
            denominator = (
                0 if row is None or pd.isna(row["denominator"]) else int(row["denominator"])
            )
            this_passes = rate is not None and denominator > 0 and rate >= COVERAGE_THRESHOLD
            passed &= this_passes
            rows.append(
                {
                    "population": population,
                    "candidate_id": candidate,
                    "validation_window": window.name,
                    "coverage_rate": rate,
                    "threshold": COVERAGE_THRESHOLD,
                    "denominator": denominator,
                    "passed": bool(this_passes),
                }
            )
    return rows, bool(passed)


def _candidate_gate(metrics: pd.DataFrame, candidate: str, incumbent: str) -> dict[str, Any]:
    incumbent_mae = _summary_lookup(metrics, "three_way_common", incumbent, "pooled")
    candidate_mae = _summary_lookup(metrics, "three_way_common", candidate, "pooled")
    window_results: list[dict[str, Any]] = []
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        base_mae = _summary_lookup(
            metrics, "three_way_common", incumbent, "validation_window", window=window.name
        )
        candidate_window_mae = _summary_lookup(
            metrics, "three_way_common", candidate, "validation_window", window=window.name
        )
        window_results.append(
            {
                "validation_window": window.name,
                "incumbent_mae": base_mae,
                "candidate_mae": candidate_window_mae,
                "strict_win": base_mae is not None
                and candidate_window_mae is not None
                and candidate_window_mae < base_mae,
                "regression_fraction": _regression_fraction(candidate_window_mae, base_mae),
                "within_10_percent_cap": _within_regression_cap(candidate_window_mae, base_mae),
            }
        )
    block_results = []
    for first, last in ((1, 7), (8, 14)):
        candidate_block = _week_mae(metrics, incumbent, candidate, first, last)
        block_results.append(
            {
                "week_block": f"h{first}-{last}",
                "incumbent_mae": candidate_block[0],
                "candidate_mae": candidate_block[1],
                "regression_fraction": _regression_fraction(candidate_block[1], candidate_block[0]),
                "within_10_percent_cap": _within_regression_cap(
                    candidate_block[1], candidate_block[0]
                ),
            }
        )
    improvement = (
        (incumbent_mae - candidate_mae) / incumbent_mae
        if incumbent_mae is not None and candidate_mae is not None and incumbent_mae > 0
        else None
    )
    enough_windows = sum(bool(item["strict_win"]) for item in window_results) >= 2
    window_caps = all(bool(item["within_10_percent_cap"]) for item in window_results)
    block_caps = all(bool(item["within_10_percent_cap"]) for item in block_results)
    pooled_pass = improvement is not None and improvement >= PROMOTION_THRESHOLD
    zero_or_tied = incumbent_mae == 0 or (
        incumbent_mae is not None and candidate_mae == incumbent_mae
    )
    numeric_pass = bool(pooled_pass and enough_windows and window_caps and block_caps)
    return {
        "candidate_id": candidate,
        "incumbent_before": incumbent,
        "incumbent_after_numeric_gates": candidate if numeric_pass else incumbent,
        "incumbent_mae": incumbent_mae,
        "candidate_mae": candidate_mae,
        "pooled_mae_improvement_fraction": improvement,
        "pooled_improvement_at_least_5_percent": bool(pooled_pass),
        "strict_window_wins": int(sum(bool(item["strict_win"]) for item in window_results)),
        "at_least_two_window_wins": bool(enough_windows),
        "window_regression_cap_passed": bool(window_caps),
        "week_block_regression_cap_passed": bool(block_caps),
        "window_results": window_results,
        "week_block_results": block_results,
        "tie_or_zero_incumbent": bool(zero_or_tied),
        "numeric_gates_passed": numeric_pass,
        "promotes": numeric_pass,
    }


def _numeric_ladder(metrics: pd.DataFrame) -> list[dict[str, Any]]:
    incumbent = CANDIDATE_IDS[0]
    output: list[dict[str, Any]] = []
    for candidate in CANDIDATE_IDS[1:]:
        gate = _candidate_gate(metrics, candidate, incumbent)
        output.append(gate)
        numeric_pass = gate["numeric_gates_passed"]
        if numeric_pass:
            incumbent = candidate
    return output


def _week_mae(
    metrics: pd.DataFrame, incumbent: str, candidate: str, first: int, last: int
) -> tuple[float | None, float | None]:
    def _value(candidate_id: str) -> float | None:
        mask = (
            metrics["population"].eq("three_way_common")
            & metrics["candidate_id"].eq(candidate_id)
            & metrics["scope"].eq("horizon")
            & metrics["horizon"].between(first, last)
            & metrics["metric"].eq("mae")
        )
        # Compute pooled block MAE directly from the row-level common forecast errors below.
        subset = metrics.loc[mask]
        if subset.empty:
            return None
        # Per-horizon MAEs cannot be averaged. The metric table's pooled block row carries
        # the row-pooled result under its explicit block bounds.
        block = metrics.loc[
            metrics["population"].eq("three_way_common")
            & metrics["candidate_id"].eq(candidate_id)
            & metrics["scope"].eq("week_block")
            & metrics["week_block_start_horizon"].eq(first)
            & metrics["metric"].eq("mae")
        ]
        return (
            None
            if block.empty or pd.isna(block.iloc[0]["value"])
            else float(block.iloc[0]["value"])
        )

    return _value(incumbent), _value(candidate)


def _horizon_change(
    metrics: pd.DataFrame, candidate: str, baseline: str, horizon: int
) -> float | None:
    candidate_mae = _summary_lookup(
        metrics, "three_way_common", candidate, "horizon", horizon=horizon
    )
    baseline_mae = _summary_lookup(
        metrics, "three_way_common", baseline, "horizon", horizon=horizon
    )
    if candidate_mae is None or baseline_mae in (None, 0):
        return None
    return candidate_mae / baseline_mae - 1.0


def _regression_fraction(candidate: float | None, incumbent: float | None) -> float | None:
    if candidate is None or incumbent is None:
        return None
    if incumbent == 0:
        return 0.0 if candidate == 0 else math.inf
    return candidate / incumbent - 1.0


def _within_regression_cap(candidate: float | None, incumbent: float | None) -> bool:
    if candidate is None or incumbent is None:
        return False
    if incumbent == 0:
        return candidate == 0
    return candidate <= incumbent * (1.0 + REGRESSION_CAP)


def _normalise_reviews(
    operational_reviews: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if operational_reviews is None:
        return {
            candidate: {
                "candidate_id": candidate,
                "policy_version": OPERATIONAL_REVIEW_SCHEMA_VERSION,
                "decision": "unknown",
                "reviewer_or_approval_reference": None,
                "rationale": (
                    "No candidate-specific operational decision was provided or found "
                    "in the reviewed record."
                ),
                "scope_of_acceptance": OPERATIONAL_SCOPE,
                "evidence_references": [],
            }
            for candidate in CANDIDATE_IDS
        }
    if set(operational_reviews) != set(CANDIDATE_IDS):
        raise EvidenceReviewRequired(
            "Operational review must contain exactly the three candidate IDs."
        )
    result: dict[str, dict[str, Any]] = {}
    required = {
        "candidate_id",
        "policy_version",
        "decision",
        "reviewer_or_approval_reference",
        "rationale",
        "scope_of_acceptance",
        "evidence_references",
    }
    for candidate in CANDIDATE_IDS:
        review = dict(operational_reviews[candidate])
        if required.difference(review):
            raise EvidenceReviewRequired(
                f"{candidate} operational review is missing required fields."
            )
        if review["candidate_id"] != candidate:
            raise EvidenceReviewRequired(
                f"Operational review candidate ID mismatch for {candidate}."
            )
        if review["decision"] not in {"approved", "rejected", "unknown"}:
            raise EvidenceReviewRequired(f"Invalid operational decision for {candidate}.")
        for field in ("policy_version", "rationale", "scope_of_acceptance"):
            if not isinstance(review[field], str) or not review[field].strip():
                raise EvidenceReviewRequired(
                    f"Operational review {field} must be non-empty for {candidate}."
                )
        if review["scope_of_acceptance"] != OPERATIONAL_SCOPE:
            raise EvidenceReviewRequired(
                f"{candidate} acceptance scope must be exactly {OPERATIONAL_SCOPE}."
            )
        if (
            review["decision"] in {"approved", "rejected"}
            and not review["reviewer_or_approval_reference"]
        ):
            raise EvidenceReviewRequired(
                f"{candidate} operational decision needs an approval reference."
            )
        if not isinstance(review["evidence_references"], list) or any(
            not isinstance(item, str) or not item.strip() for item in review["evidence_references"]
        ):
            raise EvidenceReviewRequired(f"{candidate} evidence_references must be a string list.")
        result[candidate] = review
    return result


def _operational_ladder(
    metrics: pd.DataFrame,
    reviews: dict[str, dict[str, Any]],
    coverage_passed: bool,
) -> tuple[list[dict[str, Any]], str, str | None]:
    operations: list[dict[str, Any]] = []
    if not coverage_passed:
        return operations, "coverage_review_required", None
    base_decision = reviews[CANDIDATE_IDS[0]]["decision"]
    if base_decision != "approved":
        operations.append(
            {
                "candidate_id": CANDIDATE_IDS[0],
                "outcome": "operational_review_required",
                "reason": "Seasonal Naive must be operationally approved to initialize the ladder.",
            }
        )
        return operations, "operational_review_required", None
    incumbent = CANDIDATE_IDS[0]
    for candidate in CANDIDATE_IDS[1:]:
        gate = _candidate_gate(metrics, candidate, incumbent)
        if not gate["numeric_gates_passed"]:
            operations.append(
                {
                    "candidate_id": candidate,
                    "outcome": "numeric_gates_failed",
                    "incumbent": incumbent,
                    "gate": gate,
                }
            )
            continue
        decision = reviews[candidate]["decision"]
        if decision == "approved":
            incumbent = candidate
            outcome = "approved_promoted"
        elif decision == "rejected":
            outcome = "rejected_retained_incumbent"
        else:
            operations.append(
                {
                    "candidate_id": candidate,
                    "outcome": "operational_review_required",
                    "incumbent": incumbent,
                    "reason": (
                        "Numeric gates passed but candidate-level operational "
                        "acceptance is unknown."
                    ),
                    "gate": gate,
                }
            )
            return operations, "operational_review_required", None
        operations.append(
            {"candidate_id": candidate, "outcome": outcome, "incumbent": incumbent, "gate": gate}
        )
    return operations, "selected", incumbent


def evaluate_model_selection(
    records_by_candidate: dict[str, pd.DataFrame],
    *,
    operational_reviews: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate, summarize and apply the approved fixed-ladder policy without fitting models."""

    records = validate_candidate_records(records_by_candidate)
    reviews = _normalise_reviews(operational_reviews)
    comparison = _comparison_metrics(records)
    coverage, coverage_passed = _coverage_audit(comparison)
    numeric = _numeric_ladder(comparison)
    operations, status, selected = _operational_ladder(comparison, reviews, coverage_passed)
    decision: dict[str, Any] = {
        "policy_version": MODEL_SELECTION_POLICY_VERSION,
        "policy_configuration": POLICY_CONFIGURATION,
        "policy_configuration_sha256": _canonical_sha256(POLICY_CONFIGURATION),
        "operational_review_schema_version": OPERATIONAL_REVIEW_SCHEMA_VERSION,
        "candidate_order": list(CANDIDATE_IDS),
        "approved_windows": [
            {
                "name": window.name,
                "forecast_origin": window.forecast_origin.date().isoformat(),
                "target_start": window.target_start.date().isoformat(),
                "target_end": window.target_end.date().isoformat(),
                "calendar_days": 14,
            }
            for window in APPROVED_DEVELOPMENT_WINDOWS
        ],
        "primary_population": (
            "Observed Open=1, observed Sales, and raw forecasts available for all three candidates."
        ),
        "coverage_threshold": COVERAGE_THRESHOLD,
        "coverage_status": "passed" if coverage_passed else "failed",
        "coverage_audit": coverage,
        "numeric_ladder": numeric,
        "operational_review": reviews,
        "operational_scope_disclosure": {
            "accepted_scope": OPERATIONAL_SCOPE,
            "qualitative_assessment_only": True,
            "production_latency_established": False,
            "production_reliability_established": False,
            "memory_sla_established": False,
            "end_to_end_runtime_advantage_measured": False,
            "real_business_savings_established": False,
            "benchmark_run": False,
        },
        "operational_review_summary": [
            {
                **reviews[candidate],
                "numeric_promotion_gate_passed": next(
                    (
                        gate["numeric_gates_passed"]
                        for gate in numeric
                        if gate["candidate_id"] == candidate
                    ),
                    candidate == CANDIDATE_IDS[0],
                ),
                "selection_requires_review": (
                    candidate == CANDIDATE_IDS[0]
                    or any(
                        gate["candidate_id"] == candidate and gate["numeric_gates_passed"]
                        for gate in numeric
                    )
                ),
            }
            for candidate in CANDIDATE_IDS
        ],
        "operational_ladder": operations,
        "horizon_watchlist": [
            {
                "horizon": step,
                "weekday_interpretation": "Sunday" if step in (2, 9) else "Monday",
                "three_way_common_mae": {
                    candidate: _summary_lookup(
                        comparison, "three_way_common", candidate, "horizon", horizon=step
                    )
                    for candidate in CANDIDATE_IDS
                },
                "change_fraction_vs_seasonal_naive": {
                    candidate: _horizon_change(comparison, candidate, CANDIDATE_IDS[0], step)
                    for candidate in CANDIDATE_IDS[1:]
                },
                "per_horizon_veto_applied": False,
            }
            for step in (2, 9, 10)
        ],
        "record_integrity_status": "passed",
        "status": status,
        "final_holdout_accessed": False,
        "development_target_ceiling": LAST_DEVELOPMENT_DATE.date().isoformat(),
        "final_holdout_start": FINAL_HOLDOUT_START.date().isoformat(),
        "phase_8_started": False,
    }
    if selected is not None:
        decision["selected_candidate_id"] = selected
        decision["selected_model_identity"] = selected
    return {
        "model_comparison": comparison,
        "decision": decision,
        "selected_artifacts": None,
        "normalized_records": records,
    }


_HW_CONFIGURATION = {
    "damped_trend": False,
    "fallback": None,
    "forecast_horizon_days": 14,
    "history_calendar": "observed daily rows including closed-day Sales; no gap filling",
    "initialization_method": "estimated",
    "minimum_contiguous_history_days": 28,
    "open_label_coverage_guardrail": 0.99,
    "optimized": True,
    "seasonal": "add",
    "seasonal_periods": 7,
    "trend": "add",
    "use_boxcox": False,
}


def build_refit_recipe(
    candidate_id: str,
    configuration: dict[str, Any] | None,
    *,
    provenance_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize the exact approved method recipe; this function never fits a model."""

    configuration = dict(configuration or {})
    common = {
        "candidate_id": candidate_id,
        "policy_version": MODEL_SELECTION_POLICY_VERSION,
        "recipe_only_no_fitted_model": True,
        "fit_performed": False,
        "forecast_horizon_days": 14,
        "raw_forecast_before_open_routing": True,
        "open_routing": (
            "planned/source Open=0 routes to zero; Open=1 routes raw; unknown stays null."
        ),
        "authorized_fit_or_history_boundary": (
            "origin inclusive; never read target outcomes before raw paths exist."
        ),
        "authorization_boundary": (
            "July 3 and July 17 Phase 13 origins require separate ADR-015 authorization."
        ),
        "configuration": configuration,
        "provenance_identity": dict(provenance_identity or {}),
        "future_origins_authorized": False,
        "future_origins_requiring_ADR_015": ["2015-07-03", "2015-07-17"],
    }
    if candidate_id == CANDIDATE_IDS[0]:
        return {
            **common,
            "algorithm": "exact_same_store_calendar_d_minus_7",
            "seasonal_lag_days": 7,
            "recursive_horizons": list(range(8, 15)),
            "history_includes_closed_day_sales": True,
            "missing_exact_history_or_prior_raw_prediction": "unavailable; no fallback",
        }
    if candidate_id == CANDIDATE_IDS[1]:
        if configuration and configuration != _HW_CONFIGURATION:
            raise EvidenceReviewRequired(
                "Holt-Winters configuration differs from the reviewed recipe."
            )
        return {
            **common,
            "algorithm": "holt_winters_additive_weekly",
            "configuration": dict(_HW_CONFIGURATION),
            "trend": "additive",
            "seasonality": "additive",
            "seasonal_periods": 7,
            "damped_trend": False,
            "initialization_method": "estimated",
            "history_segment": "latest contiguous per-store observed daily Sales through origin",
            "minimum_contiguous_history_days": 28,
            "gap_filling": False,
            "negative_forecasts": (
                "clip finite negative values to zero; preserve unclipped value and flag"
            ),
            "fit_or_invalid_output_failure": "store-origin path unavailable; no fallback",
        }
    if candidate_id == CANDIDATE_IDS[2]:
        trial_a = dict(TRIAL_PARAMETERS["A"])
        if configuration:
            if (
                configuration.get("selected_trial") != "A"
                or configuration.get("selected_boosting_rounds") != 180
            ):
                raise EvidenceReviewRequired(
                    "LightGBM must use frozen trial A and exactly 180 rounds."
                )
            if configuration.get("trial_parameters") != trial_a:
                raise EvidenceReviewRequired(
                    "LightGBM trial parameters differ from frozen trial A."
                )
            if configuration.get("predictor_columns") != list(PREDICTOR_COLUMNS):
                raise EvidenceReviewRequired("LightGBM predictor order differs from phase-3-v1.")
            if configuration.get("shared_parameters") != LIGHTGBM_FIXED_PARAMETERS:
                raise EvidenceReviewRequired(
                    "LightGBM shared parameters differ from the reviewed configuration."
                )
        return {
            **common,
            "algorithm": LIGHTGBM_MODEL_NAME,
            "selected_trial": "A",
            "selected_boosting_rounds": 180,
            "trial_parameters": trial_a,
            "shared_parameters": dict(LIGHTGBM_FIXED_PARAMETERS),
            "dataset_parameters": {
                "max_bin": 63,
                "zero_as_missing": False,
                "feature_pre_filter": False,
            },
            "predictor_contract_identity": {
                "version": FEATURE_CONTRACT_VERSION,
                "ordered_columns": list(PREDICTOR_COLUMNS),
                "schema": predictor_schema(),
            },
            "training_labels": "observed Sales and source Open=1 through each origin only",
            "category_vocabulary_policy": (
                "ordered vocabularies learned from eligible fit rows only"
            ),
            "history_policy": (
                "origin-censored actuals plus this run's earlier clipped raw predictions"
            ),
            "recursive_feedback": "prior clipped raw forecast; no teacher forcing or fallback",
            "future_covariate_assumption": configuration.get(
                "future_covariate_availability_assumption",
                (
                    "origin-known calendar, promotion, holiday and static metadata "
                    "assumptions remain explicit."
                ),
            ),
            "no_tuning_or_refit_performed": True,
        }
    raise EvidenceReviewRequired(f"Cannot construct an unapproved refit recipe for {candidate_id}.")


def _routed_forecast(source_open: pd.Series, raw: pd.Series) -> pd.Series:
    routed = pd.Series(np.nan, index=source_open.index, dtype="float64")
    closed = source_open.eq(0)
    open_rows = source_open.eq(1)
    routed.loc[closed] = 0.0
    routed.loc[open_rows] = raw.loc[open_rows]
    return routed


def build_selected_artifacts(
    candidate_id: str,
    records: pd.DataFrame,
    recipe: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Build selected development rows and 14-calendar-day residual paths without fitting."""

    if recipe.get("candidate_id") != candidate_id or recipe.get("fit_performed") is not False:
        raise EvidenceReviewRequired(
            "Selected artifacts require a matching serialized no-fit recipe."
        )
    normalized = _normalise_candidate_frame(candidate_id, records)
    raw = normalized["raw_model_forecast"].astype("float64")
    operational = (
        pd.to_numeric(normalized["operational_forecast"], errors="coerce")
        if "operational_forecast" in normalized
        else _routed_forecast(normalized["source_open"], raw)
    )
    expected_routing = _routed_forecast(normalized["source_open"], raw)
    if not _equal_with_nulls(operational, expected_routing).all():
        raise EvidenceReviewRequired(
            "Saved operational forecasts disagree with source Open routing."
        )
    normalized["operational_forecast"] = operational
    normalized["raw_forecast"] = raw
    normalized["operational_forecast_available"] = operational.notna().to_numpy(dtype=bool)
    if "model_forecast_unclipped" not in normalized:
        normalized["model_forecast_unclipped"] = raw
    else:
        unclipped = pd.to_numeric(normalized["model_forecast_unclipped"], errors="coerce")
        invalid_unclipped = normalized["model_forecast_unclipped"].notna() & unclipped.isna()
        if invalid_unclipped.any():
            raise EvidenceReviewRequired(
                "Unclipped forecast diagnostics contain non-numeric values."
            )
        if (
            unclipped.notna().any()
            and not np.isfinite(unclipped.dropna().to_numpy(dtype=float)).all()
        ):
            raise EvidenceReviewRequired(
                "Unclipped forecast diagnostics contain non-finite values."
            )
        normalized["model_forecast_unclipped"] = unclipped
    normalized["raw_residual"] = normalized["actual_sales"] - normalized["raw_forecast"]
    normalized["operational_residual"] = (
        normalized["actual_sales"] - normalized["operational_forecast"]
    )
    normalized["raw_primary_error_available"] = (
        normalized["source_open"].eq(1)
        & normalized["actual_sales"].notna()
        & normalized["raw_forecast"].notna()
    )
    normalized["operational_error_available"] = (
        normalized["actual_sales"].notna() & normalized["operational_forecast"].notna()
    )
    if "unavailable_reason" not in normalized:
        normalized["unavailable_reason"] = normalized["forecast_unavailable_reason"]
    else:
        normalized["unavailable_reason"] = normalized["unavailable_reason"].where(
            normalized["unavailable_reason"].notna(),
            normalized["forecast_unavailable_reason"],
        )
    normalized["model_config_identity"] = candidate_id
    normalized["model_configuration_sha256"] = hashlib.sha256(
        json.dumps(recipe, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    source_identity = recipe.get("provenance_identity", {})
    normalized["source_manifest_sha256"] = source_identity.get("source_manifest_sha256")
    selected = normalized.sort_values(list(KEY_COLUMNS), kind="mergesort").reset_index(drop=True)

    path_rows: list[pd.DataFrame] = []
    for (store, origin), observed in selected.groupby(["Store", "forecast_origin"], sort=True):
        grid = pd.DataFrame(
            {
                "Store": int(store),
                "forecast_origin": origin,
                "Date": pd.date_range(origin + pd.Timedelta(days=1), periods=14, freq="D"),
            }
        )
        grid = grid.merge(
            observed, on=list(KEY_COLUMNS), how="left", validate="one_to_one", indicator=True
        )
        grid["horizon"] = (grid["Date"] - grid["forecast_origin"]).dt.days.astype("int8")
        grid["target_key_observed"] = grid["_merge"].eq("both")
        grid = grid.drop(columns="_merge")
        grid["validation_window"] = grid["validation_window"].fillna(
            observed["validation_window"].iloc[0]
        )
        grid["unavailable_reason"] = grid["unavailable_reason"].where(
            grid["target_key_observed"], "target_key_not_observed"
        )
        grid["raw_residual"] = grid["actual_sales"] - grid["raw_forecast"]
        grid["operational_residual"] = grid["actual_sales"] - grid["operational_forecast"]
        grid["raw_primary_error_available"] = (
            grid["target_key_observed"]
            & grid["source_open"].eq(1)
            & grid["actual_sales"].notna()
            & grid["raw_forecast"].notna()
        )
        grid["operational_error_available"] = (
            grid["target_key_observed"]
            & grid["actual_sales"].notna()
            & grid["operational_forecast"].notna()
        )
        grid["forecast_available"] = grid["raw_forecast"].notna().to_numpy(dtype=bool)
        grid["operational_forecast_available"] = (
            grid["operational_forecast"].notna().to_numpy(dtype=bool)
        )
        grid["primary_evaluation_eligible"] = grid["raw_primary_error_available"].to_numpy(
            dtype=bool
        )
        grid["raw_primary_path_complete"] = bool(grid["raw_primary_error_available"].all())
        grid["operational_path_complete"] = bool(grid["operational_error_available"].all())
        grid["raw_primary_missing_horizons"] = int((~grid["raw_primary_error_available"]).sum())
        grid["operational_missing_horizons"] = int((~grid["operational_error_available"]).sum())
        path_rows.append(grid)
    residuals = pd.concat(path_rows, ignore_index=True) if path_rows else pd.DataFrame()
    residuals = residuals.sort_values(list(KEY_COLUMNS), kind="mergesort").reset_index(drop=True)
    return {"selected_development_forecasts": selected, "development_residual_paths": residuals}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, str, bytes)) else False:
        return None
    return value


def _artifact_entries(candidate_id: str, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_entries = (
        manifest.get("outputs")
        if isinstance(manifest.get("outputs"), dict)
        else manifest.get("artifacts")
    )
    if not isinstance(raw_entries, dict) or not raw_entries:
        raise EvidenceReviewRequired(
            f"{candidate_id} original manifest has no output artifact metadata."
        )
    result: dict[str, dict[str, Any]] = {}
    for key, item in raw_entries.items():
        if not isinstance(item, dict) or not isinstance(item.get("sha256"), str):
            raise EvidenceReviewRequired(
                f"{candidate_id} artifact metadata is malformed for {key}."
            )
        path_value = item.get("path", key)
        result[str(path_value)] = dict(item)
    return result


def _candidate_manifest_path(root: Path, candidate_id: str) -> Path:
    standard = root / "data" / "processed" / _FOLDERS[candidate_id] / "manifest.json"
    if standard.is_file():
        return standard
    fixture = root / "data" / "processed" / candidate_id / "manifest.json"
    return fixture


def verify_candidate_manifests(root: str | Path) -> dict[str, CandidateEvidence]:
    """Verify cached manifest artifacts and candidate/source/config identities without fitting."""

    repository = Path(root).resolve()
    evidence: dict[str, CandidateEvidence] = {}
    shared_raw: dict[str, str] | None = None
    shared_train: str | None = None
    for candidate in CANDIDATE_IDS:
        manifest_path = _candidate_manifest_path(repository, candidate)
        if not manifest_path.is_file():
            raise EvidenceReviewRequired(f"Required original manifest is missing: {manifest_path}.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise EvidenceReviewRequired(
                f"Cannot read original {candidate} manifest: {error}."
            ) from error
        if not isinstance(manifest, dict):
            raise EvidenceReviewRequired(f"Original {candidate} manifest must be a JSON object.")
        if manifest.get("candidate_id") not in (None, candidate):
            raise EvidenceReviewRequired(f"Original manifest identity mismatch for {candidate}.")
        if manifest.get("command") not in (None, _COMMANDS[candidate]):
            raise EvidenceReviewRequired(
                f"Original command/model identity mismatch for {candidate}."
            )
        if manifest.get("development_only_through") != LAST_DEVELOPMENT_DATE.date().isoformat():
            raise EvidenceReviewRequired(
                f"Original {candidate} manifest has a different development cutoff."
            )
        if manifest.get("final_holdout_forecast_or_evaluation") is not False:
            raise EvidenceReviewRequired(
                f"Original {candidate} manifest does not certify development-only output."
            )

        entries = _artifact_entries(candidate, manifest)
        expected_forecast_name = "development_forecasts.parquet"
        matching_forecast = [
            (path, item)
            for path, item in entries.items()
            if Path(path).name == expected_forecast_name
        ]
        if len(matching_forecast) != 1:
            raise EvidenceReviewRequired(
                f"{candidate} manifest must identify exactly one development forecast artifact."
            )
        artifact_hashes: dict[str, str] = {}
        for relative, metadata in entries.items():
            artifact_path = (repository / Path(relative)).resolve()
            if not artifact_path.is_relative_to(repository):
                raise EvidenceReviewRequired(
                    f"{candidate} manifest artifact escapes the repository: {relative}."
                )
            if not artifact_path.is_file():
                raise EvidenceReviewRequired(
                    f"{candidate} manifest artifact is missing: {relative}."
                )
            actual_hash = sha256_file(artifact_path)
            if actual_hash != metadata["sha256"]:
                raise EvidenceReviewRequired(f"{candidate} artifact hash mismatch: {relative}.")
            artifact_hashes[relative] = actual_hash
        forecast_path, forecast_meta = matching_forecast[0]
        if forecast_meta.get("rows") is not None and int(forecast_meta["rows"]) <= 0:
            raise EvidenceReviewRequired(f"{candidate} saved development forecasts are empty.")

        if candidate == CANDIDATE_IDS[0]:
            if (
                manifest.get("methodology")
                != "exact same-Store calendar d-7; recursive horizons 8-14; no teacher forcing"
            ):
                raise EvidenceReviewRequired(
                    "Seasonal Naive methodology identity differs from the reviewed recipe."
                )
        elif candidate == CANDIDATE_IDS[1]:
            if (
                manifest.get("statistical_model")
                != "Additive Holt-Winters, additive trend, undamped, weekly additive seasonality"
            ):
                raise EvidenceReviewRequired(
                    "Holt-Winters model identity differs from the reviewed recipe."
                )
            if manifest.get("configuration") != _HW_CONFIGURATION:
                raise EvidenceReviewRequired(
                    "Holt-Winters manifest configuration differs from the reviewed recipe."
                )
        else:
            if (
                manifest.get("selected_trial") != "A"
                or manifest.get("selected_boosting_rounds") != 180
            ):
                raise EvidenceReviewRequired(
                    "LightGBM manifest is not frozen trial A with 180 rounds."
                )
            if manifest.get("selected_trial_parameters") != TRIAL_PARAMETERS["A"]:
                raise EvidenceReviewRequired(
                    "LightGBM selected trial parameters differ from trial A."
                )
            contract = manifest.get("predictor_contract_identity", {})
            if contract.get("version") != FEATURE_CONTRACT_VERSION or contract.get(
                "ordered_columns"
            ) != list(PREDICTOR_COLUMNS):
                raise EvidenceReviewRequired("LightGBM predictor contract differs from phase-3-v1.")

        provenance = manifest.get("input_provenance")
        if candidate in CANDIDATE_IDS[:2]:
            if not isinstance(provenance, dict):
                raise EvidenceReviewRequired(f"{candidate} legacy source provenance is missing.")
            raw_hashes = provenance.get("raw_source_sha256")
            train_hash = provenance.get("phase2_train_sha256")
        else:
            snapshots = manifest.get("input_snapshot_identifiers")
            if not isinstance(snapshots, dict):
                raise EvidenceReviewRequired("LightGBM source snapshot identity is missing.")
            raw_hashes = snapshots.get("phase2_source_snapshot_sha256")
            train_hash = snapshots.get("phase2_train_snapshot_sha256")
        if not isinstance(raw_hashes, dict) or not isinstance(train_hash, str):
            raise EvidenceReviewRequired(f"{candidate} Phase 2 source identity is incomplete.")
        if raw_hashes != SOURCE_SNAPSHOT_SHA256:
            raise EvidenceReviewRequired(
                f"{candidate} raw source hash identity is not the reviewed snapshot."
            )
        if shared_raw is None:
            shared_raw = raw_hashes
            shared_train = train_hash
        elif raw_hashes != shared_raw or train_hash != shared_train:
            raise EvidenceReviewRequired(
                "Candidate manifests disagree on reviewed Phase 2 source snapshots."
            )

        config: dict[str, Any] | None = None
        if candidate == CANDIDATE_IDS[2]:
            config_path = repository / "data" / "processed" / _LGBM_FOLDER / "configuration.json"
            if not config_path.is_file():
                raise EvidenceReviewRequired("Reviewed LightGBM configuration.json is missing.")
            config_hash = sha256_file(config_path)
            if manifest.get("configuration_sha256") != config_hash:
                raise EvidenceReviewRequired(
                    "LightGBM configuration hash differs from its original manifest."
                )
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise EvidenceReviewRequired(
                    f"Cannot read checked LightGBM configuration: {error}."
                ) from error
            # Check the persisted object against the reviewed settings before recipe serialization.
            build_refit_recipe(candidate, config)
        evidence[candidate] = CandidateEvidence(
            candidate_id=candidate,
            manifest_path=manifest_path,
            manifest=manifest,
            manifest_sha256=sha256_file(manifest_path),
            artifact_hashes=artifact_hashes,
            configuration=config,
        )
    return evidence


def _load_saved_forecasts(
    root: Path, evidence: dict[str, CandidateEvidence]
) -> dict[str, pd.DataFrame]:
    records: dict[str, pd.DataFrame] = {}
    for candidate in CANDIDATE_IDS:
        item = evidence[candidate]
        entries = _artifact_entries(candidate, item.manifest)
        forecast_relative = next(
            path for path in entries if Path(path).name == "development_forecasts.parquet"
        )
        forecast_metadata = entries[forecast_relative]
        forecast_path = (root / forecast_relative).resolve()
        frame = pd.read_parquet(forecast_path)
        expected_rows = forecast_metadata.get("rows")
        if expected_rows is not None and int(expected_rows) != len(frame):
            raise EvidenceReviewRequired(
                f"{candidate} saved forecast row count differs from its original manifest."
            )
        if frame["Date"].max() > LAST_DEVELOPMENT_DATE:
            raise EvidenceReviewRequired(f"{candidate} saved forecasts extend beyond 2015-07-03.")
        records[candidate] = frame
    return records


def _read_operational_reviews(path: str | Path | None) -> dict[str, dict[str, Any]] | None:
    if path is None:
        return None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceReviewRequired(f"Cannot read operational review input: {error}.") from error
    if not isinstance(value, dict):
        raise EvidenceReviewRequired("Operational review input must be a JSON object.")
    reviews = value.get("reviews", value)
    if not isinstance(reviews, dict):
        raise EvidenceReviewRequired("Operational review 'reviews' field must be an object.")
    return reviews


def _git_revision(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=False, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _git_worktree_modified(root: Path) -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, check=False, capture_output=True, text=True
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def _source_code_hash(root: Path) -> str:
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "src/rossmann_forecasting/forecasting",
            "scripts/run_model_selection.py",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    paths = set(line for line in tracked.stdout.splitlines() if line)
    forecasting_dir = root / "src" / "rossmann_forecasting" / "forecasting"
    if forecasting_dir.is_dir():
        paths.update(
            path.relative_to(root).as_posix()
            for path in forecasting_dir.glob("*.py")
            if path.is_file()
        )
    script_path = root / "scripts" / "run_model_selection.py"
    if script_path.is_file():
        paths.add(script_path.relative_to(root).as_posix())
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = root / Path(relative)
        if path.is_file():
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def assert_output_directory_ignored(root: str | Path) -> None:
    repository = Path(root).resolve()
    candidate = repository / "data" / "processed" / "model_selection" / "model_comparison.csv"
    relative = candidate.relative_to(repository).as_posix()
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvidenceReviewRequired(
            f"Refusing to write generated output outside Git ignore: {relative}."
        )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(_json_safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _empty_comparison() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
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
        ]
    )


def _base_decision(
    status: str, reason: str, review_inputs: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "policy_version": MODEL_SELECTION_POLICY_VERSION,
        "policy_configuration": POLICY_CONFIGURATION,
        "policy_configuration_sha256": _canonical_sha256(POLICY_CONFIGURATION),
        "candidate_order": list(CANDIDATE_IDS),
        "status": status,
        "status_reason": reason,
        "artifact_integrity_status": "failed",
        "record_integrity_status": "not_checked",
        "operational_review": _normalise_reviews(None),
        "operational_scope_disclosure": {
            "accepted_scope": OPERATIONAL_SCOPE,
            "qualitative_assessment_only": True,
            "production_latency_established": False,
            "production_reliability_established": False,
            "memory_sla_established": False,
            "end_to_end_runtime_advantage_measured": False,
            "real_business_savings_established": False,
            "benchmark_run": False,
        },
        "operational_review_input": review_inputs,
        "selected_candidate_id": None,
        "final_holdout_accessed": False,
        "development_target_ceiling": LAST_DEVELOPMENT_DATE.date().isoformat(),
        "phase_8_started": False,
    }


def run_model_selection(
    *,
    root: str | Path,
    operational_review_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run selection over saved development forecasts only and write ignored audit artifacts."""

    repository = Path(root).resolve()
    assert_output_directory_ignored(repository)
    output_dir = repository / "data" / "processed" / "model_selection"
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = output_dir / "model_comparison.csv"
    decision_path = output_dir / "selection_decision.json"
    manifest_path = output_dir / "manifest.json"
    review_input: dict[str, Any] | None = None
    evidence: dict[str, CandidateEvidence] = {}
    comparison = _empty_comparison()
    selected_files: dict[str, Path] = {}
    input_evidence_summary: dict[str, Any] = {}
    artifact_integrity_status = "not_checked"
    record_integrity_status = "not_checked"
    try:
        reviews = _read_operational_reviews(operational_review_path)
        if operational_review_path is not None:
            review_input = {
                "path": str(Path(operational_review_path).resolve()),
                "sha256": sha256_file(Path(operational_review_path)),
            }
        artifact_integrity_status = "checking"
        evidence = verify_candidate_manifests(repository)
        artifact_integrity_status = "passed"
        record_integrity_status = "checking"
        records = _load_saved_forecasts(repository, evidence)
        result = evaluate_model_selection(records, operational_reviews=reviews)
        comparison = result["model_comparison"]
        decision = result["decision"]
        record_integrity_status = "passed"
        decision["artifact_integrity_status"] = artifact_integrity_status
        decision["record_integrity_status"] = record_integrity_status
        input_evidence_summary = {
            "forecast_rows_by_candidate": {
                candidate: int(len(result["normalized_records"][candidate]))
                for candidate in CANDIDATE_IDS
            },
            "common_eligible_rows": int(
                _summary_lookup(
                    comparison,
                    "three_way_common",
                    CANDIDATE_IDS[0],
                    "pooled",
                    metric="eligible_rows",
                )
                or 0
            ),
            "forecast_target_min": min(
                frame["Date"].min() for frame in result["normalized_records"].values()
            )
            .date()
            .isoformat(),
            "forecast_target_max": max(
                frame["Date"].max() for frame in result["normalized_records"].values()
            )
            .date()
            .isoformat(),
        }
        if decision["status"] == "selected":
            selected = decision["selected_candidate_id"]
            selected_manifest = evidence[selected].manifest
            selected_configuration = evidence[selected].configuration
            if selected == CANDIDATE_IDS[0]:
                selected_configuration = {
                    "methodology": selected_manifest.get("methodology"),
                    "target": selected_manifest.get("target"),
                }
            recipe = build_refit_recipe(
                selected,
                selected_configuration,
                provenance_identity={
                    "source_manifest_sha256": evidence[selected].manifest_sha256,
                    "source_manifest_code_revision": selected_manifest.get("code_revision"),
                    "source_manifest_worktree_modified": selected_manifest.get(
                        "code_worktree_modified"
                    ),
                    "source_manifest_working_tree_sha256": selected_manifest.get(
                        "working_tree_source_sha256"
                    ),
                    "configuration_sha256": selected_manifest.get("configuration_sha256"),
                },
            )
            selected_artifacts = build_selected_artifacts(
                selected, result["normalized_records"][selected], recipe
            )
            config_path = output_dir / "selected_model_config.json"
            recipe_path = output_dir / "refit_recipe.json"
            forecasts_path = output_dir / "selected_development_forecasts.parquet"
            residuals_path = output_dir / "development_residual_paths.parquet"
            recipe_sha256 = hashlib.sha256(
                json.dumps(recipe, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                    "utf-8"
                )
            ).hexdigest()
            _write_json(
                config_path,
                {
                    "candidate_id": selected,
                    "algorithm": recipe.get("algorithm"),
                    "configuration": recipe["configuration"],
                    "source_identity": recipe["provenance_identity"],
                    "refit_recipe_sha256": recipe_sha256,
                    "fit_performed": False,
                },
            )
            _write_json(recipe_path, recipe)
            selected_artifacts["selected_development_forecasts"].to_parquet(
                forecasts_path, engine="pyarrow", index=False, compression="zstd"
            )
            selected_artifacts["development_residual_paths"].to_parquet(
                residuals_path, engine="pyarrow", index=False, compression="zstd"
            )
            selected_files = {
                path.name: path
                for path in (config_path, recipe_path, forecasts_path, residuals_path)
            }
        decision["operational_review_input"] = review_input
        decision["source_manifest_sha256"] = {
            candidate: evidence[candidate].manifest_sha256 for candidate in CANDIDATE_IDS
        }
        decision["source_artifact_sha256"] = {
            candidate: evidence[candidate].artifact_hashes for candidate in CANDIDATE_IDS
        }
    except (EvidenceReviewRequired, OSError, ValueError, KeyError, TypeError) as error:
        decision = _base_decision("evidence_review_required", str(error), review_input)
        decision["artifact_integrity_status"] = (
            "failed" if artifact_integrity_status == "checking" else artifact_integrity_status
        )
        decision["record_integrity_status"] = (
            "failed" if record_integrity_status == "checking" else record_integrity_status
        )
        decision["evidence_review_required_reason"] = str(error)
        selected_files = {}

    comparison.to_csv(comparison_path, index=False, float_format="%.17g", na_rep="")
    _write_json(decision_path, decision)
    outputs = {
        comparison_path.name: {"sha256": sha256_file(comparison_path), "rows": len(comparison)},
        decision_path.name: {"sha256": sha256_file(decision_path), "rows": None},
    }
    for name, path in selected_files.items():
        rows = None
        if path.suffix == ".parquet":
            rows = int(pd.read_parquet(path, columns=["Store"]).shape[0])
        outputs[name] = {"sha256": sha256_file(path), "rows": rows}
    input_manifests = {
        candidate: {
            "path": evidence[candidate].manifest_path.relative_to(repository).as_posix(),
            "sha256": evidence[candidate].manifest_sha256,
            "original_artifacts": evidence[candidate].artifact_hashes,
            "original_artifact_metadata": evidence[candidate].manifest.get(
                "outputs", evidence[candidate].manifest.get("artifacts")
            ),
            "original_identity_metadata": {
                key: evidence[candidate].manifest.get(key)
                for key in (
                    "command",
                    "code_revision",
                    "code_worktree_modified",
                    "working_tree_source_sha256",
                    "configuration_sha256",
                    "selected_trial",
                    "selected_boosting_rounds",
                    "selected_trial_parameters",
                    "predictor_contract_identity",
                    "input_provenance",
                    "input_snapshot_identifiers",
                    "censored_input_sha256",
                )
            },
        }
        for candidate in evidence
    }
    lock_path = repository / "uv.lock"
    manifest = {
        "command": "rossmann-model-selection",
        "policy_version": MODEL_SELECTION_POLICY_VERSION,
        "candidate_order": list(CANDIDATE_IDS),
        "configuration": POLICY_CONFIGURATION,
        "configuration_sha256": _canonical_sha256(POLICY_CONFIGURATION),
        "status": decision["status"],
        "input_integrity_status": decision.get("artifact_integrity_status", "failed"),
        "record_integrity_status": decision.get("record_integrity_status", "not_checked"),
        "selected_candidate_id": decision.get("selected_candidate_id"),
        "input_manifests": input_manifests,
        "input_evidence_summary": input_evidence_summary,
        "operational_review_input": review_input,
        "date_bounds": {
            "first_development_target": min(
                window.target_start for window in APPROVED_DEVELOPMENT_WINDOWS
            )
            .date()
            .isoformat(),
            "last_development_target": LAST_DEVELOPMENT_DATE.date().isoformat(),
            "final_holdout_start": FINAL_HOLDOUT_START.date().isoformat(),
        },
        "final_holdout_forecast_or_evaluation": False,
        "final_holdout_outcomes_read_or_hashed": False,
        "phase_8_started": False,
        "legacy_lineage_disclosure": (
            "SN/HW manifests have legacy provenance limits; LightGBM preserves the original "
            "dirty-worktree provenance. No old manifest was rewritten or treated as generated "
            "from the current revision."
        ),
        "operational_scope_disclosure": {
            "accepted_scope": OPERATIONAL_SCOPE,
            "qualitative_assessment_only": True,
            "production_latency_established": False,
            "production_reliability_established": False,
            "memory_sla_established": False,
            "end_to_end_runtime_advantage_measured": False,
            "real_business_savings_established": False,
            "benchmark_run": False,
        },
        "execution": {
            "code_revision": _git_revision(repository),
            "code_worktree_modified": _git_worktree_modified(repository),
            "current_source_sha256": _source_code_hash(repository),
            "python_version": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "statsmodels_version": statsmodels.__version__,
            "lightgbm_version": lgb.__version__,
            "pyarrow_version": pyarrow.__version__,
            "project_package_version": importlib.metadata.version("rossmann-demand-forecasting"),
            "uv_lock_sha256": sha256_file(lock_path) if lock_path.is_file() else None,
            "seed": "not applicable; aggregation only, no fit or stochastic operation",
        },
        "outputs": outputs,
    }
    _write_json(manifest_path, manifest)
    return {
        "output_directory": output_dir.relative_to(repository).as_posix(),
        "status": decision["status"],
        "selected_candidate_id": decision.get("selected_candidate_id"),
        "comparison_rows": len(comparison),
        "manifest": manifest_path.relative_to(repository).as_posix(),
        "decision": decision,
    }
