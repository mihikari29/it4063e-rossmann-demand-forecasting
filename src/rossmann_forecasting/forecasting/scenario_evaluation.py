"""Fixture-only population alignment for approved Phase 7 forecast candidates."""

from __future__ import annotations

import pandas as pd

from rossmann_forecasting.forecasting.model_selection import (
    BASE_COLUMNS,
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    KEY_COLUMNS,
    EvidenceReviewRequired,
    validate_candidate_records,
)

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
