"""Fixture-only population alignment for approved Phase 7 forecast candidates."""

from __future__ import annotations

import json
import math
import numbers
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.forecasting.model_selection import (
    BASE_COLUMNS,
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    KEY_COLUMNS,
    EvidenceReviewRequired,
    validate_candidate_records,
)
from rossmann_forecasting.forecasting.validation import APPROVED_DEVELOPMENT_WINDOWS

_CANDIDATE_MASK_COLUMNS = {
    candidate_id: {
        "available": f"{candidate_id}_forecast_available",
        "reason": f"{candidate_id}_forecast_unavailable_reason",
        "standalone": f"{candidate_id}_standalone_eligible",
    }
    for candidate_id in CANDIDATE_IDS
}

SCENARIO_POPULATION_COLUMNS = (
    *BASE_COLUMNS,
    "label_eligible",
    *FORECAST_COLUMNS.values(),
    "seasonal_naive_forecast_available",
    "seasonal_naive_forecast_unavailable_reason",
    "seasonal_naive_standalone_eligible",
    "holt_winters_additive_weekly_forecast_available",
    "holt_winters_additive_weekly_forecast_unavailable_reason",
    "holt_winters_additive_weekly_standalone_eligible",
    "global_lightgbm_gbdt_regression_l1_forecast_available",
    "global_lightgbm_gbdt_regression_l1_forecast_unavailable_reason",
    "global_lightgbm_gbdt_regression_l1_standalone_eligible",
    "three_way_common_eligible",
)

_SCENARIO_METADATA_COLUMNS = (
    "Promo",
    "StoreType",
    "Assortment",
    "StateHoliday",
    "SchoolHoliday",
)
_METADATA_LEVELS = {
    "Promo": ("0", "1"),
    "StoreType": ("a", "b", "c", "d"),
    "Assortment": ("a", "b", "c"),
    "StateHoliday": ("0", "a", "b", "c"),
    "SchoolHoliday": ("0", "1"),
}
_GROUP_COLUMNS = (
    "scope",
    "validation_window",
    "forecast_origin",
    "dimension",
    "level_status",
    "level_value",
)
_SUPPORT_COLUMNS = (
    *_GROUP_COLUMNS,
    "observed_target_rows",
    "open_label_rows",
    "three_way_common_rows",
    "closed_rows",
    "unknown_open_rows",
    "open_missing_actual_rows",
    "missing_actual_rows",
    "observed_store_count",
    "observed_date_count",
    "observed_origin_count",
    "common_store_count",
    "common_date_count",
    "common_origin_count",
    "label_coverage_rate",
    "label_coverage_unavailable_reason",
    "common_label_coverage_rate",
    "common_label_coverage_unavailable_reason",
    "missing_metadata_rows",
    "unrecognized_metadata_rows",
    "empty_observed",
    "no_label_eligible",
    "no_common_rows",
    "single_common_store",
    "single_common_date",
    "single_common_origin",
)
_COVERAGE_COLUMNS = (
    *_GROUP_COLUMNS,
    "candidate_id",
    "observed_target_rows",
    "open_label_rows",
    "forecast_available_rows",
    "forecast_unavailable_rows",
    "standalone_eligible_rows",
    "label_eligible_unavailable_rows",
    "standalone_excluded_from_common_rows",
    "standalone_store_count",
    "standalone_date_count",
    "standalone_origin_count",
    "raw_forecast_coverage_rate",
    "raw_forecast_coverage_unavailable_reason",
    "open_label_forecast_coverage_rate",
    "open_label_forecast_coverage_unavailable_reason",
    "common_open_label_coverage_rate",
    "common_open_label_coverage_unavailable_reason",
)
_METRICS_COLUMNS = (
    *_GROUP_COLUMNS,
    "candidate_id",
    "population",
    "n",
    "sum_actual",
    "sum_absolute_error",
    "sum_squared_error",
    "sum_signed_error",
    "underforecast_sum",
    "overforecast_sum",
    "underforecast_count",
    "overforecast_count",
    "exact_match_count",
    "mae",
    "rmse",
    "wape",
    "mean_signed_error",
    "underforecast_contribution",
    "overforecast_contribution",
    "underforecast_rate",
    "overforecast_rate",
    "normalized_underforecast_exposure",
    "normalized_overforecast_exposure",
    "sales_unit",
    "squared_error_unit",
    "ratio_unit",
    "rate_unit",
    "metrics_unavailable_reason",
    "sales_ratio_unavailable_reason",
)
_COMPARISON_PAIRS = (
    (CANDIDATE_IDS[2], CANDIDATE_IDS[0]),
    (CANDIDATE_IDS[2], CANDIDATE_IDS[1]),
    (CANDIDATE_IDS[1], CANDIDATE_IDS[0]),
)
_COMPARISON_COLUMNS = (
    *_GROUP_COLUMNS,
    "population",
    "candidate_id",
    "reference_candidate_id",
    "n",
    "candidate_mae",
    "reference_mae",
    "absolute_mae_difference",
    "relative_mae_improvement_pct",
    "sales_unit",
    "relative_improvement_unit",
    "comparison_unavailable_reason",
    "relative_improvement_unavailable_reason",
)
_UNAVAILABILITY_COLUMNS = (
    *_GROUP_COLUMNS,
    "candidate_id",
    "unavailable_reason",
    "observed_unavailable_rows",
    "open_label_unavailable_rows",
)
_CORE_DIMENSIONS = ("all", "horizon", "horizon_block", "iso_weekday")
_SALES_UNIT = "monetary_sales_turnover"
_SQUARED_SALES_UNIT = "monetary_sales_turnover_squared"


@dataclass(frozen=True)
class ScenarioEvaluationResult:
    """Deterministic in-memory summaries for a synthetic scenario fixture."""

    support: pd.DataFrame
    coverage: pd.DataFrame
    metrics: pd.DataFrame
    comparisons: pd.DataFrame
    unavailability: pd.DataFrame
    enabled_scenarios: tuple[str, ...]


def build_scenario_population(
    records_by_candidate: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Align in-memory candidate records on observed keys and derive eligibility masks.

    The returned frame retains every observed target key after Phase 7 validation. It contains
    label-only eligibility, each candidate's raw forecast availability and standalone eligibility,
    and exact three-way common eligibility. No target grid, forecast, metric, or scenario field is
    synthesized.
    """

    normalized = validate_candidate_records(records_by_candidate)
    reference = normalized[CANDIDATE_IDS[0]]
    result = reference.loc[:, BASE_COLUMNS].copy(deep=True)
    label_eligible = result["source_open"].eq(1) & result["actual_sales"].notna()
    result["label_eligible"] = label_eligible.to_numpy(dtype=bool)

    reference_keys = pd.MultiIndex.from_frame(reference.loc[:, list(KEY_COLUMNS)])
    common_eligible = label_eligible.reset_index(drop=True).copy()

    for candidate_id in CANDIDATE_IDS:
        candidate = normalized[candidate_id].set_index(list(KEY_COLUMNS), drop=False)
        aligned = candidate.reindex(reference_keys)
        raw_column = FORECAST_COLUMNS[candidate_id]
        raw = aligned["raw_model_forecast"].to_numpy(dtype="float64", na_value=float("nan"))
        available = aligned["forecast_available"].to_numpy(dtype=bool)
        accepted_eligible = aligned["primary_evaluation_eligible"].to_numpy(dtype=bool)
        standalone_eligible = label_eligible & pd.Series(available, dtype=bool)

        if not standalone_eligible.reset_index(drop=True).equals(
            pd.Series(accepted_eligible, dtype=bool)
        ):
            raise EvidenceReviewRequired(
                f"{candidate_id} derived standalone eligibility disagrees with Phase 7 validation."
            )

        mask_columns = _CANDIDATE_MASK_COLUMNS[candidate_id]
        result[raw_column] = raw
        result[mask_columns["available"]] = available
        result[mask_columns["reason"]] = aligned["forecast_unavailable_reason"].to_numpy(
            dtype=object
        )
        result[mask_columns["standalone"]] = standalone_eligible.to_numpy(dtype=bool)
        common_eligible &= standalone_eligible.reset_index(drop=True)

    result["three_way_common_eligible"] = common_eligible.to_numpy(dtype=bool)
    return result.loc[:, SCENARIO_POPULATION_COLUMNS].reset_index(drop=True)


def _canonicalize_keys(frame: pd.DataFrame, *, source: str) -> pd.DataFrame:
    missing = set(KEY_COLUMNS).difference(frame.columns)
    if missing:
        raise EvidenceReviewRequired(
            f"{source} is missing canonical key columns: {sorted(missing)}."
        )
    keys = frame.loc[:, list(KEY_COLUMNS)].copy(deep=True)
    store = pd.to_numeric(keys["Store"], errors="coerce")
    if store.isna().any() or not np.isfinite(store.to_numpy(dtype=np.float64)).all():
        raise EvidenceReviewRequired(f"{source} has invalid Store keys.")
    if store.mod(1).ne(0).any() or store.le(0).any():
        raise EvidenceReviewRequired(f"{source} has invalid Store keys.")
    if store.gt(np.iinfo(np.int64).max).any():
        raise EvidenceReviewRequired(f"{source} has out-of-range Store keys.")
    keys["Store"] = store.astype("int64")

    dates: list[pd.Timestamp] = []
    for column in ("forecast_origin", "Date"):
        dates.clear()
        for value in keys[column].tolist():
            try:
                parsed = pd.Timestamp(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise EvidenceReviewRequired(f"{source} has invalid {column} keys.") from exc
            if pd.isna(parsed) or parsed.tz is not None or parsed.normalize() != parsed:
                raise EvidenceReviewRequired(f"{source} has invalid {column} keys.")
            dates.append(parsed)
        keys[column] = pd.Series(dates, index=keys.index, dtype="datetime64[ns]")
    return keys


def _scalar_equal(left: Any, right: Any) -> bool:
    left_missing = pd.isna(left)
    right_missing = pd.isna(right)
    if bool(left_missing) or bool(right_missing):
        return bool(left_missing) and bool(right_missing)
    try:
        comparison = left == right
    except (TypeError, ValueError):
        return False
    return bool(comparison) if not pd.isna(comparison) else False


def _validated_population(population: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(population, pd.DataFrame):
        raise EvidenceReviewRequired("Scenario aggregation requires an L1 population DataFrame.")
    if population.columns.duplicated().any():
        raise EvidenceReviewRequired("L1 population contains duplicate columns.")
    if len(population.columns) != len(SCENARIO_POPULATION_COLUMNS) or set(
        population.columns
    ) != set(SCENARIO_POPULATION_COLUMNS):
        raise EvidenceReviewRequired("Input columns do not match the exact L1 population schema.")

    supplied = population.loc[:, list(SCENARIO_POPULATION_COLUMNS)].copy(deep=True)
    normalized_keys = _canonicalize_keys(supplied, source="L1 population")
    supplied.loc[:, list(KEY_COLUMNS)] = normalized_keys.to_numpy()

    records_by_candidate: dict[str, pd.DataFrame] = {}
    for candidate_id in CANDIDATE_IDS:
        mask_columns = _CANDIDATE_MASK_COLUMNS[candidate_id]
        record = supplied.loc[:, list(BASE_COLUMNS)].copy(deep=True)
        record[FORECAST_COLUMNS[candidate_id]] = supplied[FORECAST_COLUMNS[candidate_id]].copy()
        record["forecast_available"] = supplied[mask_columns["available"]].copy()
        record["primary_evaluation_eligible"] = supplied[mask_columns["standalone"]].copy()
        record["unavailable_reason"] = supplied[mask_columns["reason"]].copy()
        records_by_candidate[candidate_id] = record

    regenerated = build_scenario_population(records_by_candidate)
    supplied_indexed = supplied.set_index(list(KEY_COLUMNS)).sort_index(kind="mergesort")
    regenerated_indexed = regenerated.set_index(list(KEY_COLUMNS)).sort_index(kind="mergesort")
    if not supplied_indexed.index.equals(regenerated_indexed.index):
        raise EvidenceReviewRequired("Input L1 keys do not match the regenerated canonical keys.")

    audited_columns = (
        "label_eligible",
        *(name["available"] for name in _CANDIDATE_MASK_COLUMNS.values()),
        *(name["reason"] for name in _CANDIDATE_MASK_COLUMNS.values()),
        *(name["standalone"] for name in _CANDIDATE_MASK_COLUMNS.values()),
        "three_way_common_eligible",
    )
    for column in audited_columns:
        left = supplied_indexed[column].tolist()
        right = regenerated_indexed[column].tolist()
        if any(not _scalar_equal(a, b) for a, b in zip(left, right, strict=True)):
            raise EvidenceReviewRequired(
                f"Supplied L1 field {column} disagrees with the regenerated population."
            )

    for candidate_id in CANDIDATE_IDS:
        mask_columns = _CANDIDATE_MASK_COLUMNS[candidate_id]
        for available, reason in zip(
            regenerated[mask_columns["available"]],
            regenerated[mask_columns["reason"]],
            strict=True,
        ):
            if available:
                if not pd.isna(reason):
                    raise EvidenceReviewRequired(
                        f"{candidate_id} available forecasts must not have unavailable reasons."
                    )
            elif not isinstance(reason, str) or not reason:
                raise EvidenceReviewRequired(
                    f"{candidate_id} unavailable forecasts require an original reason string."
                )
    return regenerated


def _normalize_metadata_value(column: str, value: Any) -> tuple[str, str | None]:
    if _is_null_scalar(value):
        return "missing", None
    if column in {"Promo", "SchoolHoliday"}:
        if isinstance(value, (bool, np.bool_)):
            normalized = "1" if value else "0"
        elif isinstance(value, numbers.Real) and not isinstance(value, bool):
            numeric = float(value)
            if not math.isfinite(numeric) or numeric not in (0.0, 1.0):
                raise EvidenceReviewRequired(f"{column} metadata must be 0, 1, or missing.")
            normalized = str(int(numeric))
        elif isinstance(value, str) and value in {"0", "1"}:
            normalized = value
        else:
            raise EvidenceReviewRequired(f"{column} metadata must be 0, 1, or missing.")
        return "known", normalized

    if (
        column == "StateHoliday"
        and isinstance(value, numbers.Real)
        and not isinstance(value, (bool, np.bool_))
    ):
        numeric = float(value)
        if numeric == 0.0 and math.isfinite(numeric):
            return "known", "0"
        raise EvidenceReviewRequired("StateHoliday numeric metadata accepts only 0.")
    if not isinstance(value, str) or not value:
        raise EvidenceReviewRequired(f"{column} metadata must be nonempty text or missing.")
    if value in _METADATA_LEVELS[column]:
        return "known", value
    return "unrecognized", value


def _validated_membership(
    population: pd.DataFrame,
    scenario_membership: pd.DataFrame | None,
) -> tuple[tuple[str, ...], dict[str, list[tuple[str, str | None]]]]:
    if scenario_membership is None:
        return (), {}
    if not isinstance(scenario_membership, pd.DataFrame):
        raise EvidenceReviewRequired("Scenario membership must be an in-memory DataFrame.")
    if scenario_membership.columns.duplicated().any():
        raise EvidenceReviewRequired("Scenario membership contains duplicate columns.")
    columns = list(scenario_membership.columns)
    enabled = tuple(column for column in _SCENARIO_METADATA_COLUMNS if column in columns)
    expected_columns = set(KEY_COLUMNS).union(enabled)
    if len(columns) != len(expected_columns) or set(columns) != expected_columns:
        raise EvidenceReviewRequired(
            "Scenario membership must contain exactly canonical keys and approved metadata columns."
        )

    membership = scenario_membership.loc[:, [*KEY_COLUMNS, *enabled]].copy(deep=True)
    membership.loc[:, list(KEY_COLUMNS)] = _canonicalize_keys(
        membership, source="Scenario membership"
    ).to_numpy()
    if membership.duplicated(list(KEY_COLUMNS)).any():
        raise EvidenceReviewRequired("Scenario membership keys must be unique.")

    population_index = pd.MultiIndex.from_frame(population.loc[:, list(KEY_COLUMNS)])
    membership_index = pd.MultiIndex.from_frame(membership.loc[:, list(KEY_COLUMNS)])
    population_keys = set(population_index.tolist())
    membership_keys = set(membership_index.tolist())
    if population_keys != membership_keys or len(population_index) != len(membership_index):
        raise EvidenceReviewRequired(
            "Scenario membership keys must exactly match the observed L1 population keys."
        )

    aligned = membership.set_index(list(KEY_COLUMNS)).reindex(population_index)
    normalized: dict[str, list[tuple[str, str | None]]] = {}
    for column in enabled:
        values = [_normalize_metadata_value(column, value) for value in aligned[column].tolist()]
        normalized[column] = values

    store_values = population["Store"].tolist()
    for column in ("StoreType", "Assortment"):
        if column not in normalized:
            continue
        by_store: dict[int, tuple[str, str | None]] = {}
        for store, value in zip(store_values, normalized[column], strict=True):
            previous = by_store.setdefault(int(store), value)
            if previous != value:
                raise EvidenceReviewRequired(f"{column} metadata must be static within each Store.")
    return enabled, normalized


def _group_specs(
    population: pd.DataFrame,
    enabled: tuple[str, ...],
    metadata: dict[str, list[tuple[str, str | None]]],
) -> list[tuple[dict[str, Any], np.ndarray]]:
    row_count = len(population)
    all_rows = np.ones(row_count, dtype=bool)
    weekdays = population["Date"].dt.dayofweek.to_numpy(dtype=np.int8) + 1
    horizons = population["horizon"].to_numpy(dtype=np.int16)
    windows: list[tuple[str, pd.Timestamp | None, str, np.ndarray]] = [
        ("pooled", None, "pooled", all_rows)
    ]
    windows.extend(
        (
            "origin",
            window.forecast_origin,
            window.name,
            population["validation_window"].eq(window.name).to_numpy(dtype=bool),
        )
        for window in APPROVED_DEVELOPMENT_WINDOWS
    )

    specs: list[tuple[dict[str, Any], np.ndarray]] = []
    for scope, origin, window_name, scope_mask in windows:
        for dimension in _CORE_DIMENSIONS:
            if dimension == "all":
                levels = [("all", None, all_rows)]
            elif dimension == "horizon":
                levels = [("known", f"H{step}", horizons == step) for step in range(1, 15)]
            elif dimension == "horizon_block":
                levels = [
                    ("known", "H1-H7", (horizons >= 1) & (horizons <= 7)),
                    ("known", "H8-H14", (horizons >= 8) & (horizons <= 14)),
                ]
            else:
                levels = [("known", str(day), weekdays == day) for day in range(1, 8)]
            for level_status, level_value, level_mask in levels:
                specs.append(
                    (
                        {
                            "scope": scope,
                            "validation_window": window_name if scope == "origin" else None,
                            "forecast_origin": origin,
                            "dimension": dimension,
                            "level_status": level_status,
                            "level_value": level_value,
                        },
                        scope_mask & level_mask,
                    )
                )

        for column in enabled:
            statuses = metadata[column]
            discovered = sorted(
                {value for status, value in statuses if status == "unrecognized"},
                key=lambda value: value if value is not None else "",
            )
            levels = [
                ("known", value, np.fromiter((item == ("known", value) for item in statuses), bool))
                for value in _METADATA_LEVELS[column]
            ]
            levels.append(
                (
                    "missing",
                    None,
                    np.fromiter((item[0] == "missing" for item in statuses), bool),
                )
            )
            levels.extend(
                (
                    "unrecognized",
                    value,
                    np.fromiter((item == ("unrecognized", value) for item in statuses), bool),
                )
                for value in discovered
            )
            for level_status, level_value, level_mask in levels:
                specs.append(
                    (
                        {
                            "scope": scope,
                            "validation_window": window_name if scope == "origin" else None,
                            "forecast_origin": origin,
                            "dimension": column,
                            "level_status": level_status,
                            "level_value": level_value,
                        },
                        scope_mask & level_mask,
                    )
                )
    return specs


def _finite_fsum(values: list[float], *, name: str) -> float:
    try:
        result = math.fsum(values)
    except (OverflowError, ValueError) as exc:
        raise ArithmeticError(f"Non-finite {name} arithmetic in scenario summary.") from exc
    if not math.isfinite(result):
        raise ArithmeticError(f"Non-finite {name} arithmetic in scenario summary.")
    return 0.0 if result == 0.0 else result


def _finite_float(value: float, *, name: str) -> float:
    if not math.isfinite(value):
        raise ArithmeticError(f"Non-finite {name} arithmetic in scenario summary.")
    return 0.0 if value == 0.0 else float(value)


def _assert_close(left: float, right: float, *, name: str) -> None:
    if not math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-10):
        raise ArithmeticError(f"Scenario sufficient-statistic reconciliation failed for {name}.")


def _signed_totals_reconcile(signed_sum: float, over_sum: float, under_sum: float) -> bool:
    if not all(math.isfinite(value) for value in (signed_sum, over_sum, under_sum)):
        return False
    directional_sum = math.fsum((over_sum, -under_sum))
    # Each rounded sum contributes at most half an ULP; scale this bound to the
    # component totals so cancellation does not make valid directional sums fail.
    rounding_bound = math.fsum(
        math.ulp(value) / 2.0 for value in (signed_sum, over_sum, under_sum, directional_sum)
    )
    rounding_bound = max(rounding_bound, math.ulp(0.0))
    return abs(signed_sum - directional_sum) <= rounding_bound


def _count_unique(frame: pd.DataFrame, column: str) -> int:
    return int(frame[column].nunique(dropna=True))


def _support_row(
    population: pd.DataFrame,
    rows: np.ndarray,
    group: dict[str, Any],
    enabled: tuple[str, ...],
    metadata: dict[str, list[tuple[str, str | None]]],
) -> dict[str, Any]:
    selected = population.loc[rows]
    observed = len(selected)
    label = selected["label_eligible"].to_numpy(dtype=bool)
    common = selected["three_way_common_eligible"].to_numpy(dtype=bool)
    source_open = selected["source_open"].to_numpy(dtype=np.float64, na_value=np.nan)
    actual = selected["actual_sales"].to_numpy(dtype=np.float64, na_value=np.nan)
    closed_rows = int(np.equal(source_open, 0.0).sum())
    unknown_open_rows = int(np.isnan(source_open).sum())
    open_missing_actual_rows = int((np.equal(source_open, 1.0) & np.isnan(actual)).sum())
    missing_actual_rows = int(np.isnan(actual).sum())
    label_rows = int(label.sum())
    common_rows = int(common.sum())
    if observed != closed_rows + unknown_open_rows + open_missing_actual_rows + label_rows:
        raise ArithmeticError("Observed target accounting identity failed in scenario support.")

    common_frame = selected.loc[common]
    label_rate = label_rows / observed if observed else None
    common_rate = common_rows / label_rows if label_rows else None
    metadata_missing: int | None = None
    metadata_unrecognized: int | None = None
    dimension = group["dimension"]
    if dimension in enabled:
        states = np.asarray(metadata[dimension], dtype=object)[rows]
        metadata_missing = int(sum(status == "missing" for status, _ in states))
        metadata_unrecognized = int(sum(status == "unrecognized" for status, _ in states))

    return {
        **group,
        "observed_target_rows": observed,
        "open_label_rows": label_rows,
        "three_way_common_rows": common_rows,
        "closed_rows": closed_rows,
        "unknown_open_rows": unknown_open_rows,
        "open_missing_actual_rows": open_missing_actual_rows,
        "missing_actual_rows": missing_actual_rows,
        "observed_store_count": _count_unique(selected, "Store"),
        "observed_date_count": _count_unique(selected, "Date"),
        "observed_origin_count": _count_unique(selected, "forecast_origin"),
        "common_store_count": _count_unique(common_frame, "Store"),
        "common_date_count": _count_unique(common_frame, "Date"),
        "common_origin_count": _count_unique(common_frame, "forecast_origin"),
        "label_coverage_rate": label_rate,
        "label_coverage_unavailable_reason": None if observed else "no_observed_target_rows",
        "common_label_coverage_rate": common_rate,
        "common_label_coverage_unavailable_reason": (
            None if label_rows else "no_label_eligible_rows"
        ),
        "missing_metadata_rows": metadata_missing,
        "unrecognized_metadata_rows": metadata_unrecognized,
        "empty_observed": observed == 0,
        "no_label_eligible": label_rows == 0,
        "no_common_rows": common_rows == 0,
        "single_common_store": _count_unique(common_frame, "Store") == 1,
        "single_common_date": _count_unique(common_frame, "Date") == 1,
        "single_common_origin": _count_unique(common_frame, "forecast_origin") == 1,
    }


def _coverage_row(
    population: pd.DataFrame,
    rows: np.ndarray,
    group: dict[str, Any],
    candidate_id: str,
) -> dict[str, Any]:
    selected = population.loc[rows]
    available_column = _CANDIDATE_MASK_COLUMNS[candidate_id]["available"]
    standalone_column = _CANDIDATE_MASK_COLUMNS[candidate_id]["standalone"]
    available = selected[available_column].to_numpy(dtype=bool)
    standalone = selected[standalone_column].to_numpy(dtype=bool)
    label = selected["label_eligible"].to_numpy(dtype=bool)
    common = selected["three_way_common_eligible"].to_numpy(dtype=bool)
    observed = len(selected)
    label_rows = int(label.sum())
    available_rows = int(available.sum())
    standalone_rows = int(standalone.sum())
    common_rows = int(common.sum())
    rate_reason = None if observed else "no_observed_target_rows"
    label_reason = None if label_rows else "no_label_eligible_rows"
    return {
        **group,
        "candidate_id": candidate_id,
        "observed_target_rows": observed,
        "open_label_rows": label_rows,
        "forecast_available_rows": available_rows,
        "forecast_unavailable_rows": observed - available_rows,
        "standalone_eligible_rows": standalone_rows,
        "label_eligible_unavailable_rows": label_rows - standalone_rows,
        "standalone_excluded_from_common_rows": standalone_rows - common_rows,
        "standalone_store_count": _count_unique(selected.loc[standalone], "Store"),
        "standalone_date_count": _count_unique(selected.loc[standalone], "Date"),
        "standalone_origin_count": _count_unique(selected.loc[standalone], "forecast_origin"),
        "raw_forecast_coverage_rate": available_rows / observed if observed else None,
        "raw_forecast_coverage_unavailable_reason": rate_reason,
        "open_label_forecast_coverage_rate": (standalone_rows / label_rows if label_rows else None),
        "open_label_forecast_coverage_unavailable_reason": label_reason,
        "common_open_label_coverage_rate": common_rows / label_rows if label_rows else None,
        "common_open_label_coverage_unavailable_reason": label_reason,
    }


def _metric_row(
    population: pd.DataFrame,
    rows: np.ndarray,
    group: dict[str, Any],
    candidate_id: str,
) -> dict[str, Any]:
    selected = population.loc[rows]
    common = selected["three_way_common_eligible"].to_numpy(dtype=bool)
    common_rows = selected.loc[common]
    actual = common_rows["actual_sales"].to_numpy(dtype=np.float64)
    forecast = common_rows[FORECAST_COLUMNS[candidate_id]].to_numpy(dtype=np.float64)
    errors = [
        float(predicted) - float(observed)
        for observed, predicted in zip(actual, forecast, strict=True)
    ]
    if any(not math.isfinite(error) for error in errors):
        raise ArithmeticError("Non-finite signed forecast error in scenario summary.")

    absolute = [abs(error) for error in errors]
    squared = [error * error for error in errors]
    if any(not math.isfinite(value) for value in squared):
        raise ArithmeticError("Non-finite squared forecast error in scenario summary.")
    under = [max(-error, 0.0) for error in errors]
    over = [max(error, 0.0) for error in errors]
    actual_sum = _finite_fsum([float(value) for value in actual], name="actual Sales sum")
    absolute_sum = _finite_fsum(absolute, name="absolute error sum")
    squared_sum = _finite_fsum(squared, name="squared error sum")
    signed_sum = _finite_fsum(errors, name="signed error sum")
    under_sum = _finite_fsum(under, name="underforecast sum")
    over_sum = _finite_fsum(over, name="overforecast sum")
    under_count = sum(error < 0.0 for error in errors)
    over_count = sum(error > 0.0 for error in errors)
    exact_count = sum(error == 0.0 for error in errors)
    count = len(errors)

    if count != under_count + over_count + exact_count:
        raise ArithmeticError("Forecast direction count reconciliation failed.")
    _assert_close(absolute_sum, under_sum + over_sum, name="absolute error")
    if not _signed_totals_reconcile(signed_sum, over_sum, under_sum):
        raise ArithmeticError(
            "Scenario sufficient-statistic reconciliation failed for signed error."
        )

    if count:
        mae = _finite_float(absolute_sum / count, name="MAE")
        rmse = _finite_float(math.sqrt(squared_sum / count), name="RMSE")
        mean_signed = _finite_float(signed_sum / count, name="mean signed error")
        under_contribution = _finite_float(under_sum / count, name="underforecast contribution")
        over_contribution = _finite_float(over_sum / count, name="overforecast contribution")
        under_rate = _finite_float(under_count / count, name="underforecast rate")
        over_rate = _finite_float(over_count / count, name="overforecast rate")
        _assert_close(mae, under_contribution + over_contribution, name="MAE direction")
        if actual_sum > 0.0:
            wape = _finite_float(absolute_sum / actual_sum, name="WAPE")
            normalized_under = _finite_float(under_sum / actual_sum, name="underforecast exposure")
            normalized_over = _finite_float(over_sum / actual_sum, name="overforecast exposure")
            _assert_close(wape, normalized_under + normalized_over, name="WAPE direction")
            ratio_reason = None
        else:
            wape = None
            normalized_under = None
            normalized_over = None
            ratio_reason = "zero_actual_sum"
        metrics_reason = None
    else:
        mae = rmse = mean_signed = None
        under_contribution = over_contribution = None
        under_rate = over_rate = None
        wape = normalized_under = normalized_over = None
        metrics_reason = "no_common_rows"
        ratio_reason = "no_common_rows"

    return {
        **group,
        "candidate_id": candidate_id,
        "population": "three_way_common",
        "n": count,
        "sum_actual": actual_sum,
        "sum_absolute_error": absolute_sum,
        "sum_squared_error": squared_sum,
        "sum_signed_error": signed_sum,
        "underforecast_sum": under_sum,
        "overforecast_sum": over_sum,
        "underforecast_count": under_count,
        "overforecast_count": over_count,
        "exact_match_count": exact_count,
        "mae": mae,
        "rmse": rmse,
        "wape": wape,
        "mean_signed_error": mean_signed,
        "underforecast_contribution": under_contribution,
        "overforecast_contribution": over_contribution,
        "underforecast_rate": under_rate,
        "overforecast_rate": over_rate,
        "normalized_underforecast_exposure": normalized_under,
        "normalized_overforecast_exposure": normalized_over,
        "sales_unit": _SALES_UNIT,
        "squared_error_unit": _SQUARED_SALES_UNIT,
        "ratio_unit": "unitless_ratio",
        "rate_unit": "unit_interval",
        "metrics_unavailable_reason": metrics_reason,
        "sales_ratio_unavailable_reason": ratio_reason,
    }


def _group_key(group: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(group[column] for column in _GROUP_COLUMNS)


def summarize_scenario_population(
    population: pd.DataFrame,
    *,
    scenario_membership: pd.DataFrame | None = None,
) -> ScenarioEvaluationResult:
    """Summarize an accepted L1 population using synthetic in-memory scenarios only."""

    canonical = _validated_population(population)
    enabled, metadata = _validated_membership(canonical, scenario_membership)
    specs = _group_specs(canonical, enabled, metadata)

    support_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    unavailability_rows: list[dict[str, Any]] = []
    metrics_by_group_candidate: dict[tuple[Any, ...], dict[str, Any]] = {}

    for group, row_mask in specs:
        support_rows.append(_support_row(canonical, row_mask, group, enabled, metadata))
        for candidate_id in CANDIDATE_IDS:
            coverage_rows.append(_coverage_row(canonical, row_mask, group, candidate_id))
            metric = _metric_row(canonical, row_mask, group, candidate_id)
            metric_rows.append(metric)
            metrics_by_group_candidate[(*_group_key(group), candidate_id)] = metric

            selected = canonical.loc[row_mask]
            unavailable_column = _CANDIDATE_MASK_COLUMNS[candidate_id]["available"]
            unavailable_reason_column = _CANDIDATE_MASK_COLUMNS[candidate_id]["reason"]
            unavailable = ~selected[unavailable_column].to_numpy(dtype=bool)
            if unavailable.any():
                reasons = selected.loc[unavailable, unavailable_reason_column].tolist()
                for reason in sorted(set(reasons)):
                    reason_mask = np.asarray([value == reason for value in reasons], dtype=bool)
                    unavailable_rows = selected.loc[unavailable].iloc[reason_mask]
                    open_label_unavailable = int(unavailable_rows["label_eligible"].sum())
                    unavailability_rows.append(
                        {
                            **group,
                            "candidate_id": candidate_id,
                            "unavailable_reason": reason,
                            "observed_unavailable_rows": len(unavailable_rows),
                            "open_label_unavailable_rows": open_label_unavailable,
                        }
                    )

        group_identity = _group_key(group)
        for candidate_id, reference_candidate_id in _COMPARISON_PAIRS:
            candidate = metrics_by_group_candidate[(*group_identity, candidate_id)]
            reference = metrics_by_group_candidate[(*group_identity, reference_candidate_id)]
            count = int(candidate["n"])
            candidate_mae = candidate["mae"]
            reference_mae = reference["mae"]
            if count == 0:
                absolute_difference = None
                relative_improvement = None
                comparison_reason = "no_common_rows"
                relative_reason = "no_common_rows"
            else:
                absolute_difference = _finite_float(
                    float(candidate_mae) - float(reference_mae),
                    name="absolute MAE difference",
                )
                comparison_reason = None
                if float(reference_mae) == 0.0:
                    relative_improvement = None
                    relative_reason = "zero_reference_mae"
                else:
                    relative_improvement = _finite_float(
                        100.0
                        * (float(reference_mae) - float(candidate_mae))
                        / float(reference_mae),
                        name="relative MAE improvement",
                    )
                    relative_reason = None
            comparison_rows.append(
                {
                    **group,
                    "population": "three_way_common",
                    "candidate_id": candidate_id,
                    "reference_candidate_id": reference_candidate_id,
                    "n": count,
                    "candidate_mae": candidate_mae,
                    "reference_mae": reference_mae,
                    "absolute_mae_difference": absolute_difference,
                    "relative_mae_improvement_pct": relative_improvement,
                    "sales_unit": _SALES_UNIT,
                    "relative_improvement_unit": "percent",
                    "comparison_unavailable_reason": comparison_reason,
                    "relative_improvement_unavailable_reason": relative_reason,
                }
            )

    support_table = pd.DataFrame(support_rows, columns=_SUPPORT_COLUMNS)
    for column in ("missing_metadata_rows", "unrecognized_metadata_rows"):
        support_table[column] = support_table[column].astype("Int64")
    result = ScenarioEvaluationResult(
        support=support_table,
        coverage=pd.DataFrame(coverage_rows, columns=_COVERAGE_COLUMNS),
        metrics=pd.DataFrame(metric_rows, columns=_METRICS_COLUMNS),
        comparisons=pd.DataFrame(comparison_rows, columns=_COMPARISON_COLUMNS),
        unavailability=pd.DataFrame(unavailability_rows, columns=_UNAVAILABILITY_COLUMNS),
        enabled_scenarios=enabled,
    )
    _validate_scenario_result(result)
    return result


_TABLE_SCHEMAS = {
    "support": _SUPPORT_COLUMNS,
    "coverage": _COVERAGE_COLUMNS,
    "metrics": _METRICS_COLUMNS,
    "comparisons": _COMPARISON_COLUMNS,
    "unavailability": _UNAVAILABILITY_COLUMNS,
}
_INTEGER_COLUMNS = {
    "observed_target_rows",
    "open_label_rows",
    "three_way_common_rows",
    "closed_rows",
    "unknown_open_rows",
    "open_missing_actual_rows",
    "missing_actual_rows",
    "observed_store_count",
    "observed_date_count",
    "observed_origin_count",
    "common_store_count",
    "common_date_count",
    "common_origin_count",
    "missing_metadata_rows",
    "unrecognized_metadata_rows",
    "forecast_available_rows",
    "forecast_unavailable_rows",
    "standalone_eligible_rows",
    "label_eligible_unavailable_rows",
    "standalone_excluded_from_common_rows",
    "standalone_store_count",
    "standalone_date_count",
    "standalone_origin_count",
    "n",
    "underforecast_count",
    "overforecast_count",
    "exact_match_count",
    "observed_unavailable_rows",
    "open_label_unavailable_rows",
}
_FLOAT_COLUMNS = {
    "label_coverage_rate",
    "common_label_coverage_rate",
    "raw_forecast_coverage_rate",
    "open_label_forecast_coverage_rate",
    "common_open_label_coverage_rate",
    "sum_actual",
    "sum_absolute_error",
    "sum_squared_error",
    "sum_signed_error",
    "underforecast_sum",
    "overforecast_sum",
    "mae",
    "rmse",
    "wape",
    "mean_signed_error",
    "underforecast_contribution",
    "overforecast_contribution",
    "underforecast_rate",
    "overforecast_rate",
    "normalized_underforecast_exposure",
    "normalized_overforecast_exposure",
    "candidate_mae",
    "reference_mae",
    "absolute_mae_difference",
    "relative_mae_improvement_pct",
}
_BOOLEAN_COLUMNS = {
    "empty_observed",
    "no_label_eligible",
    "no_common_rows",
    "single_common_store",
    "single_common_date",
    "single_common_origin",
}
_NULLABLE_COLUMNS = {
    "support": {
        "validation_window",
        "forecast_origin",
        "level_value",
        "label_coverage_rate",
        "label_coverage_unavailable_reason",
        "common_label_coverage_rate",
        "common_label_coverage_unavailable_reason",
        "missing_metadata_rows",
        "unrecognized_metadata_rows",
    },
    "coverage": {
        "validation_window",
        "forecast_origin",
        "level_value",
        "raw_forecast_coverage_rate",
        "raw_forecast_coverage_unavailable_reason",
        "open_label_forecast_coverage_rate",
        "open_label_forecast_coverage_unavailable_reason",
        "common_open_label_coverage_rate",
        "common_open_label_coverage_unavailable_reason",
    },
    "metrics": {
        "validation_window",
        "forecast_origin",
        "level_value",
        "mae",
        "rmse",
        "wape",
        "mean_signed_error",
        "underforecast_contribution",
        "overforecast_contribution",
        "underforecast_rate",
        "overforecast_rate",
        "normalized_underforecast_exposure",
        "normalized_overforecast_exposure",
        "metrics_unavailable_reason",
        "sales_ratio_unavailable_reason",
    },
    "comparisons": {
        "validation_window",
        "forecast_origin",
        "level_value",
        "candidate_mae",
        "reference_mae",
        "absolute_mae_difference",
        "relative_mae_improvement_pct",
        "comparison_unavailable_reason",
        "relative_improvement_unavailable_reason",
    },
    "unavailability": {"validation_window", "forecast_origin", "level_value"},
}


def _is_null_scalar(value: Any) -> bool:
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(missing) if isinstance(missing, (bool, np.bool_)) else False


def _json_scalar(table: str, column: str, value: Any) -> Any:
    if _is_null_scalar(value):
        if column not in _NULLABLE_COLUMNS[table]:
            raise ValueError(f"Unexpected null in {table}.{column}.")
        return None
    if column in _INTEGER_COLUMNS:
        if not isinstance(value, numbers.Integral) or isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{table}.{column} must contain JSON integers.")
        integer = int(value)
        if integer < 0:
            raise ValueError(f"{table}.{column} must be non-negative.")
        return integer
    if column in _FLOAT_COLUMNS:
        if not isinstance(value, numbers.Real) or isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{table}.{column} must contain finite numbers.")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{table}.{column} must contain finite numbers.")
        return 0.0 if number == 0.0 else number
    if column in _BOOLEAN_COLUMNS:
        if not isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{table}.{column} must contain JSON booleans.")
        return bool(value)
    if column == "forecast_origin":
        if not isinstance(value, (pd.Timestamp, np.datetime64)):
            raise ValueError("forecast_origin must contain ISO dates.")
        timestamp = pd.Timestamp(value)
        if timestamp.tz is not None or timestamp.normalize() != timestamp:
            raise ValueError("forecast_origin must contain timezone-naive calendar dates.")
        return timestamp.date().isoformat()
    if not isinstance(value, str):
        raise ValueError(f"{table}.{column} must contain strings.")
    if column.endswith("reason") and not value:
        raise ValueError(f"{table}.{column} reason strings must not be empty.")
    return value


def _table_records(table: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame) or frame.columns.duplicated().any():
        raise ValueError(f"{table} must be a DataFrame with unique columns.")
    if tuple(frame.columns) != _TABLE_SCHEMAS[table]:
        raise ValueError(f"{table} columns do not match the fixed result schema.")
    records: list[dict[str, Any]] = []
    for source in frame.to_dict(orient="records"):
        records.append(
            {
                column: _json_scalar(table, column, source[column])
                for column in _TABLE_SCHEMAS[table]
            }
        )
    return records


def _group_identity(record: dict[str, Any]) -> tuple[Any, ...]:
    origin = record["forecast_origin"]
    if origin is not None:
        origin = pd.Timestamp(origin)
    return (
        record["scope"],
        record["validation_window"],
        origin,
        record["dimension"],
        record["level_status"],
        record["level_value"],
    )


def _expected_group_identities(
    enabled: tuple[str, ...],
    unrecognized: dict[str, set[str]],
) -> set[tuple[Any, ...]]:
    scopes: list[tuple[str, str | None, pd.Timestamp | None]] = [("pooled", None, None)]
    scopes.extend(
        ("origin", window.name, window.forecast_origin) for window in APPROVED_DEVELOPMENT_WINDOWS
    )
    expected: set[tuple[Any, ...]] = set()
    for scope, window_name, origin in scopes:
        dimensions: list[tuple[str, list[tuple[str, str | None]]]] = [
            ("all", [("all", None)]),
            ("horizon", [("known", f"H{step}") for step in range(1, 15)]),
            (
                "horizon_block",
                [("known", "H1-H7"), ("known", "H8-H14")],
            ),
            ("iso_weekday", [("known", str(day)) for day in range(1, 8)]),
        ]
        for column in enabled:
            dimensions.append(
                (
                    column,
                    [("known", value) for value in _METADATA_LEVELS[column]]
                    + [("missing", None)]
                    + [("unrecognized", value) for value in sorted(unrecognized[column])],
                )
            )
        for dimension, levels in dimensions:
            expected.update(
                (
                    scope,
                    window_name,
                    origin,
                    dimension,
                    status,
                    value,
                )
                for status, value in levels
            )
    return expected


def _close_values(left: float, right: float, *, field: str) -> None:
    if not math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-10):
        raise ValueError(f"Scenario result is inconsistent at {field}.")


def _ratio_value(numerator: float, denominator: float) -> float:
    return _finite_float(numerator / denominator, name="serialized ratio")


def _canonical_group_sort_key(
    identity: tuple[Any, ...], enabled: tuple[str, ...]
) -> tuple[Any, ...]:
    scope, window_name, origin, dimension, status, value = identity
    if scope == "pooled":
        scope_rank = 0
    else:
        scope_rank = 1 + next(
            index
            for index, window in enumerate(APPROVED_DEVELOPMENT_WINDOWS)
            if window.name == window_name
        )
    dimension_order = (*_CORE_DIMENSIONS, *enabled)
    dimension_rank = dimension_order.index(dimension)
    if status in {"all", "known"}:
        status_rank = 0
    elif status == "missing":
        status_rank = 1
    else:
        status_rank = 2
    if status == "known":
        if dimension == "horizon":
            level_rank: Any = int(str(value)[1:])
        elif dimension == "horizon_block":
            level_rank = 0 if value == "H1-H7" else 1
        elif dimension == "iso_weekday":
            level_rank = int(str(value))
        elif dimension in enabled:
            level_rank = _METADATA_LEVELS[dimension].index(value)
        else:
            level_rank = 0
    else:
        level_rank = value or ""
    return (
        scope_rank,
        dimension_rank,
        status_rank,
        level_rank,
        str(origin or ""),
    )


def _validate_scenario_result(result: ScenarioEvaluationResult) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(result, ScenarioEvaluationResult):
        raise ValueError("Serializer requires a ScenarioEvaluationResult.")
    if not isinstance(result.enabled_scenarios, tuple):
        raise ValueError("enabled_scenarios must be an ordered tuple.")
    if tuple(
        column for column in _SCENARIO_METADATA_COLUMNS if column in result.enabled_scenarios
    ) != (result.enabled_scenarios) or len(set(result.enabled_scenarios)) != len(
        result.enabled_scenarios
    ):
        raise ValueError("enabled_scenarios must be an ordered subset of approved dimensions.")

    tables = {name: _table_records(name, getattr(result, name)) for name in _TABLE_SCHEMAS}
    support = tables["support"]
    if not support:
        raise ValueError("Scenario support must include all declared strata.")
    groups = [_group_identity(row) for row in support]
    if len(set(groups)) != len(groups):
        raise ValueError("support contains duplicate reporting strata.")

    for row in support:
        dimension = row["dimension"]
        if dimension not in result.enabled_scenarios:
            continue
        status = row["level_status"]
        value = row["level_value"]
        known_levels = _METADATA_LEVELS[dimension]
        if status == "known":
            valid_identity = value in known_levels
        elif status == "missing":
            valid_identity = value is None
        elif status == "unrecognized":
            valid_identity = isinstance(value, str) and bool(value) and value not in known_levels
        else:
            valid_identity = False
        if not valid_identity:
            raise ValueError(f"{dimension} metadata level identity is inconsistent.")

    unrecognized = {
        column: {
            row["level_value"]
            for row in support
            if row["dimension"] == column and row["level_status"] == "unrecognized"
        }
        for column in result.enabled_scenarios
    }
    expected_groups = _expected_group_identities(result.enabled_scenarios, unrecognized)
    if set(groups) != expected_groups:
        raise ValueError("support does not contain the complete fixed stratum schema.")
    support_by_group = dict(zip(groups, support, strict=True))

    for identity, row in support_by_group.items():
        observed = row["observed_target_rows"]
        label = row["open_label_rows"]
        common = row["three_way_common_rows"]
        closed = row["closed_rows"]
        unknown_open = row["unknown_open_rows"]
        open_missing = row["open_missing_actual_rows"]
        missing_actual = row["missing_actual_rows"]
        if observed != closed + unknown_open + open_missing + label:
            raise ValueError("support violates the observed target accounting identity.")
        if (
            missing_actual < open_missing
            or missing_actual > observed - label
            or common > label
            or label > observed
        ):
            raise ValueError("support counts are not nested consistently.")
        if row["empty_observed"] is not (observed == 0):
            raise ValueError("support empty_observed flag is inconsistent.")
        if row["no_label_eligible"] is not (label == 0):
            raise ValueError("support no_label_eligible flag is inconsistent.")
        if row["no_common_rows"] is not (common == 0):
            raise ValueError("support no_common_rows flag is inconsistent.")
        for count_name, maximum in (
            ("observed_store_count", observed),
            ("observed_date_count", observed),
            ("observed_origin_count", observed),
            ("common_store_count", common),
            ("common_date_count", common),
            ("common_origin_count", common),
        ):
            if row[count_name] > maximum:
                raise ValueError(f"support {count_name} exceeds its population count.")
        if row["single_common_store"] is not (row["common_store_count"] == 1):
            raise ValueError("support single_common_store flag is inconsistent.")
        if row["single_common_date"] is not (row["common_date_count"] == 1):
            raise ValueError("support single_common_date flag is inconsistent.")
        if row["single_common_origin"] is not (row["common_origin_count"] == 1):
            raise ValueError("support single_common_origin flag is inconsistent.")
        if observed:
            _close_values(row["label_coverage_rate"], label / observed, field="label coverage")
            if row["label_coverage_unavailable_reason"] is not None:
                raise ValueError("label coverage has an unexpected unavailable reason.")
        elif (
            row["label_coverage_rate"] is not None
            or row["label_coverage_unavailable_reason"] != "no_observed_target_rows"
        ):
            raise ValueError("empty support label coverage must be explicitly unavailable.")
        if label:
            _close_values(
                row["common_label_coverage_rate"], common / label, field="common label coverage"
            )
            if row["common_label_coverage_unavailable_reason"] is not None:
                raise ValueError("common label coverage has an unexpected unavailable reason.")
        elif (
            row["common_label_coverage_rate"] is not None
            or row["common_label_coverage_unavailable_reason"] != "no_label_eligible_rows"
        ):
            raise ValueError("support without labels must have an explicit coverage reason.")
        if identity[3] in result.enabled_scenarios:
            if row["missing_metadata_rows"] is None or row["unrecognized_metadata_rows"] is None:
                raise ValueError("metadata support requires missing/unrecognized counts.")
            expected_missing = observed if identity[4] == "missing" else 0
            expected_unrecognized = observed if identity[4] == "unrecognized" else 0
            if (
                row["missing_metadata_rows"] != expected_missing
                or row["unrecognized_metadata_rows"] != expected_unrecognized
            ):
                raise ValueError("metadata support counts disagree with the active stratum.")
        elif (
            row["missing_metadata_rows"] is not None
            or row["unrecognized_metadata_rows"] is not None
        ):
            raise ValueError("non-metadata support must not carry metadata counts.")

    expected_candidate_keys = {
        (group, candidate_id) for group in expected_groups for candidate_id in CANDIDATE_IDS
    }
    coverage = tables["coverage"]
    metrics = tables["metrics"]
    coverage_keys = [(_group_identity(row), row["candidate_id"]) for row in coverage]
    metric_keys = [(_group_identity(row), row["candidate_id"]) for row in metrics]
    if (
        len(set(coverage_keys)) != len(coverage_keys)
        or set(coverage_keys) != expected_candidate_keys
    ):
        raise ValueError("coverage must contain one row per stratum and candidate.")
    if len(set(metric_keys)) != len(metric_keys) or set(metric_keys) != expected_candidate_keys:
        raise ValueError("metrics must contain one row per stratum and candidate.")
    coverage_by_key = dict(zip(coverage_keys, coverage, strict=True))
    metrics_by_key = dict(zip(metric_keys, metrics, strict=True))

    for key, row in coverage_by_key.items():
        support_row = support_by_group[key[0]]
        observed = support_row["observed_target_rows"]
        label = support_row["open_label_rows"]
        common = support_row["three_way_common_rows"]
        available = row["forecast_available_rows"]
        standalone = row["standalone_eligible_rows"]
        if (
            row["observed_target_rows"] != observed
            or row["open_label_rows"] != label
            or row["forecast_unavailable_rows"] + available != observed
            or row["label_eligible_unavailable_rows"] + standalone != label
            or row["standalone_excluded_from_common_rows"] != standalone - common
        ):
            raise ValueError("coverage counts disagree with support or eligibility masks.")
        if standalone > available or common > standalone:
            raise ValueError("coverage population counts are not nested consistently.")
        for name in (
            "standalone_store_count",
            "standalone_date_count",
            "standalone_origin_count",
        ):
            if row[name] > standalone:
                raise ValueError(f"coverage {name} exceeds its standalone population.")
        for name, numerator, denominator, reason_name, unavailable_reason in (
            (
                "raw_forecast_coverage_rate",
                available,
                observed,
                "raw_forecast_coverage_unavailable_reason",
                "no_observed_target_rows",
            ),
            (
                "open_label_forecast_coverage_rate",
                standalone,
                label,
                "open_label_forecast_coverage_unavailable_reason",
                "no_label_eligible_rows",
            ),
            (
                "common_open_label_coverage_rate",
                common,
                label,
                "common_open_label_coverage_unavailable_reason",
                "no_label_eligible_rows",
            ),
        ):
            if denominator:
                _close_values(row[name], numerator / denominator, field=name)
                if row[reason_name] is not None:
                    raise ValueError(f"{name} has an unexpected unavailable reason.")
            elif row[name] is not None or row[reason_name] != unavailable_reason:
                raise ValueError(f"{name} must explain its zero denominator.")

    for key, row in metrics_by_key.items():
        support_row = support_by_group[key[0]]
        count = support_row["three_way_common_rows"]
        if row["population"] != "three_way_common" or row["n"] != count:
            raise ValueError("metrics must use the exact three-way common population.")
        if row["sales_unit"] != _SALES_UNIT or row["squared_error_unit"] != _SQUARED_SALES_UNIT:
            raise ValueError("metrics units do not match monetary Sales turnover.")
        if row["ratio_unit"] != "unitless_ratio" or row["rate_unit"] != "unit_interval":
            raise ValueError("metrics ratio/rate units are invalid.")
        if (
            row["n"]
            != row["underforecast_count"] + row["overforecast_count"] + row["exact_match_count"]
        ):
            raise ValueError("metric direction counts do not reconcile.")
        if (
            min(
                row["sum_actual"],
                row["sum_absolute_error"],
                row["sum_squared_error"],
                row["underforecast_sum"],
                row["overforecast_sum"],
            )
            < 0
        ):
            raise ValueError("metric additive totals must be non-negative.")
        _close_values(
            row["sum_absolute_error"],
            row["underforecast_sum"] + row["overforecast_sum"],
            field="absolute error totals",
        )
        if not _signed_totals_reconcile(
            row["sum_signed_error"], row["overforecast_sum"], row["underforecast_sum"]
        ):
            raise ValueError("Scenario result is inconsistent at signed error totals.")
        if count == 0:
            totals = (
                row["sum_actual"],
                row["sum_absolute_error"],
                row["sum_squared_error"],
                row["sum_signed_error"],
                row["underforecast_sum"],
                row["overforecast_sum"],
            )
            if any(value != 0.0 for value in totals):
                raise ValueError("empty common metrics must have zero additive totals.")
            if any(
                row[name] is not None
                for name in (
                    "mae",
                    "rmse",
                    "wape",
                    "mean_signed_error",
                    "underforecast_contribution",
                    "overforecast_contribution",
                    "underforecast_rate",
                    "overforecast_rate",
                    "normalized_underforecast_exposure",
                    "normalized_overforecast_exposure",
                )
            ):
                raise ValueError("empty common metrics must be null, not zero-filled.")
            if row["metrics_unavailable_reason"] != "no_common_rows":
                raise ValueError("empty common metrics require no_common_rows.")
            if row["sales_ratio_unavailable_reason"] != "no_common_rows":
                raise ValueError("empty common ratios require no_common_rows.")
            continue

        if row["metrics_unavailable_reason"] is not None:
            raise ValueError("nonempty common metrics have an unexpected unavailable reason.")
        _close_values(row["mae"], row["sum_absolute_error"] / count, field="MAE")
        _close_values(row["rmse"], math.sqrt(row["sum_squared_error"] / count), field="RMSE")
        _close_values(
            row["mean_signed_error"], row["sum_signed_error"] / count, field="mean signed error"
        )
        _close_values(
            row["underforecast_contribution"],
            row["underforecast_sum"] / count,
            field="under contribution",
        )
        _close_values(
            row["overforecast_contribution"],
            row["overforecast_sum"] / count,
            field="over contribution",
        )
        _close_values(
            row["underforecast_rate"], row["underforecast_count"] / count, field="under rate"
        )
        _close_values(
            row["overforecast_rate"], row["overforecast_count"] / count, field="over rate"
        )
        _close_values(
            row["mae"],
            row["underforecast_contribution"] + row["overforecast_contribution"],
            field="directional MAE",
        )
        if row["sum_actual"] == 0.0:
            if (
                any(
                    row[name] is not None
                    for name in (
                        "wape",
                        "normalized_underforecast_exposure",
                        "normalized_overforecast_exposure",
                    )
                )
                or row["sales_ratio_unavailable_reason"] != "zero_actual_sum"
            ):
                raise ValueError("zero actual sum ratios must remain null with a reason.")
        else:
            if row["sales_ratio_unavailable_reason"] is not None:
                raise ValueError("defined Sales ratios have an unexpected unavailable reason.")
            _close_values(row["wape"], row["sum_absolute_error"] / row["sum_actual"], field="WAPE")
            _close_values(
                row["normalized_underforecast_exposure"],
                row["underforecast_sum"] / row["sum_actual"],
                field="normalized underforecast exposure",
            )
            _close_values(
                row["normalized_overforecast_exposure"],
                row["overforecast_sum"] / row["sum_actual"],
                field="normalized overforecast exposure",
            )
            _close_values(
                row["wape"],
                row["normalized_underforecast_exposure"] + row["normalized_overforecast_exposure"],
                field="directional WAPE",
            )

    for group in expected_groups:
        actual_denominators = {
            metrics_by_key[(group, candidate_id)]["sum_actual"] for candidate_id in CANDIDATE_IDS
        }
        if len(actual_denominators) != 1:
            raise ValueError("metrics must share one common-population actual Sales denominator.")

    expected_comparison_keys = {
        (group, candidate_id, reference_id)
        for group in expected_groups
        for candidate_id, reference_id in _COMPARISON_PAIRS
    }
    comparisons = tables["comparisons"]
    comparison_keys = [
        (_group_identity(row), row["candidate_id"], row["reference_candidate_id"])
        for row in comparisons
    ]
    if (
        len(set(comparison_keys)) != len(comparison_keys)
        or set(comparison_keys) != expected_comparison_keys
    ):
        raise ValueError("comparisons must contain the three fixed pairs for every stratum.")
    for row in comparisons:
        group = _group_identity(row)
        candidate = metrics_by_key[(group, row["candidate_id"])]
        reference = metrics_by_key[(group, row["reference_candidate_id"])]
        count = candidate["n"]
        if (
            row["population"] != "three_way_common"
            or row["n"] != count
            or row["sales_unit"] != _SALES_UNIT
            or row["relative_improvement_unit"] != "percent"
        ):
            raise ValueError("comparison identity or units are invalid.")
        if not _scalar_equal(row["candidate_mae"], candidate["mae"]) or not _scalar_equal(
            row["reference_mae"], reference["mae"]
        ):
            raise ValueError("comparison MAEs disagree with common-population metrics.")
        if count == 0:
            if (
                row["absolute_mae_difference"] is not None
                or row["relative_mae_improvement_pct"] is not None
                or row["comparison_unavailable_reason"] != "no_common_rows"
                or row["relative_improvement_unavailable_reason"] != "no_common_rows"
            ):
                raise ValueError("empty comparisons require explicit unavailable reasons.")
        else:
            difference = candidate["mae"] - reference["mae"]
            _close_values(
                row["absolute_mae_difference"], difference, field="absolute MAE difference"
            )
            if row["comparison_unavailable_reason"] is not None:
                raise ValueError("defined comparison has an unexpected unavailable reason.")
            if reference["mae"] == 0.0:
                if (
                    row["relative_mae_improvement_pct"] is not None
                    or row["relative_improvement_unavailable_reason"] != "zero_reference_mae"
                ):
                    raise ValueError(
                        "zero reference MAE must leave relative improvement undefined."
                    )
            else:
                expected = 100.0 * (reference["mae"] - candidate["mae"]) / reference["mae"]
                _close_values(
                    row["relative_mae_improvement_pct"], expected, field="relative MAE improvement"
                )
                if row["relative_improvement_unavailable_reason"] is not None:
                    raise ValueError("defined relative improvement has an unexpected reason.")

    unavailable = tables["unavailability"]
    unavailable_keys = [
        (_group_identity(row), row["candidate_id"], row["unavailable_reason"])
        for row in unavailable
    ]
    if len(set(unavailable_keys)) != len(unavailable_keys):
        raise ValueError("unavailability contains duplicate group/reason rows.")
    for row in unavailable:
        group = _group_identity(row)
        support_row = support_by_group.get(group)
        coverage_row = coverage_by_key.get((group, row["candidate_id"]))
        if (
            support_row is None
            or coverage_row is None
            or support_row["observed_target_rows"] == 0
            or row["observed_unavailable_rows"] == 0
            or row["observed_unavailable_rows"] > coverage_row["forecast_unavailable_rows"]
            or row["open_label_unavailable_rows"] > row["observed_unavailable_rows"]
            or row["open_label_unavailable_rows"] > support_row["open_label_rows"]
        ):
            raise ValueError("unavailability contains an empty or inconsistent reason row.")
        if not row["unavailable_reason"]:
            raise ValueError("unavailability reason strings must not be empty.")

    unavailable_totals: dict[tuple[tuple[Any, ...], str], tuple[int, int]] = {}
    for row in unavailable:
        key = (_group_identity(row), row["candidate_id"])
        previous = unavailable_totals.get(key, (0, 0))
        unavailable_totals[key] = (
            previous[0] + row["observed_unavailable_rows"],
            previous[1] + row["open_label_unavailable_rows"],
        )
    for key, row in coverage_by_key.items():
        unavailable_count, open_unavailable_count = unavailable_totals.get(key, (0, 0))
        if (
            unavailable_count != row["forecast_unavailable_rows"]
            or open_unavailable_count != row["label_eligible_unavailable_rows"]
        ):
            raise ValueError("unavailability reason totals do not reconcile to coverage.")

    return tables


def serialize_scenario_fixture(result: ScenarioEvaluationResult) -> bytes:
    """Serialize a validated synthetic fixture summary as deterministic JSON bytes."""

    tables = _validate_scenario_result(result)
    serialized_tables: dict[str, list[dict[str, Any]]] = {}
    for table_name, records in tables.items():

        def sort_key(row: dict[str, Any], table_name: str = table_name) -> tuple[Any, ...]:
            group_key = _canonical_group_sort_key(_group_identity(row), result.enabled_scenarios)
            if table_name in {"coverage", "metrics"}:
                suffix: tuple[Any, ...] = (CANDIDATE_IDS.index(row["candidate_id"]),)
            elif table_name == "comparisons":
                suffix = (
                    _COMPARISON_PAIRS.index((row["candidate_id"], row["reference_candidate_id"])),
                )
            elif table_name == "unavailability":
                suffix = (CANDIDATE_IDS.index(row["candidate_id"]), row["unavailable_reason"])
            else:
                suffix = ()
            return (*group_key, *suffix)

        serialized_tables[table_name] = sorted(records, key=sort_key)

    payload = {
        "schema_version": "wp1-l2-fixture-v1",
        "analysis_scope": "synthetic_fixture_only",
        "primary_population": "three_way_common",
        "candidate_order": list(CANDIDATE_IDS),
        "enabled_scenarios": list(result.enabled_scenarios),
        "tables": serialized_tables,
    }
    document = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return (document + "\n").encode("utf-8")
