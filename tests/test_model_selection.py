"""Synthetic tests for the approved Phase 7 selection contract."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.forecasting.model_selection import (
    CANDIDATE_IDS,
    EvidenceReviewRequired,
    build_refit_recipe,
    build_selected_artifacts,
    evaluate_model_selection,
    validate_candidate_records,
    verify_candidate_manifests,
)
from rossmann_forecasting.forecasting.validation import APPROVED_DEVELOPMENT_WINDOWS

RAW_COLUMNS = {
    "seasonal_naive": "raw_baseline_forecast",
    "holt_winters_additive_weekly": "raw_statistical_forecast",
    "global_lightgbm_gbdt_regression_l1": "raw_lightgbm_forecast",
}


def _records(*, stores_per_window: tuple[int, int, int] = (2, 2, 2)) -> dict[str, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for window_index, window in enumerate(APPROVED_DEVELOPMENT_WINDOWS):
        for store in range(1, stores_per_window[window_index] + 1):
            for horizon in range(1, 15):
                actual = 1000.0 + store * 20.0 + horizon
                rows.append(
                    {
                        "Store": store,
                        "forecast_origin": window.forecast_origin,
                        "Date": window.forecast_origin + pd.Timedelta(days=horizon),
                        "horizon": horizon,
                        "validation_window": window.name,
                        "actual_sales": actual,
                        "source_open": 1.0,
                        "raw_baseline_forecast": actual + 100.0,
                        "raw_statistical_forecast": actual + 95.0,
                        "raw_lightgbm_forecast": actual + 90.0,
                        "forecast_available": True,
                        "primary_evaluation_eligible": True,
                        "operational_forecast": actual + 100.0,
                        "model_forecast_unclipped": actual + 100.0,
                        "unavailable_reason": None,
                        "forecast_was_clipped": False,
                    }
                )
    combined = pd.DataFrame(rows)
    return {
        candidate: combined.loc[
            :,
            [
                "Store",
                "forecast_origin",
                "Date",
                "horizon",
                "validation_window",
                "actual_sales",
                "source_open",
                RAW_COLUMNS[candidate],
                "forecast_available",
                "primary_evaluation_eligible",
                "operational_forecast",
                "model_forecast_unclipped",
                "unavailable_reason",
                "forecast_was_clipped",
            ],
        ].copy()
        for candidate in CANDIDATE_IDS
    }


def _reviews(decision: str = "approved") -> dict[str, dict[str, object]]:
    return {
        candidate: {
            "candidate_id": candidate,
            "policy_version": "offline-review-v1",
            "decision": decision,
            "reviewer_or_approval_reference": "review-123",
            "rationale": "Synthetic fixture decision.",
            "scope_of_acceptance": "offline_cpu_course_demonstration",
            "evidence_references": ["fixture:evidence"],
        }
        for candidate in CANDIDATE_IDS
    }


def _set_errors(
    records: dict[str, pd.DataFrame],
    candidate: str,
    values: dict[str, float] | float,
) -> None:
    column = RAW_COLUMNS[candidate]
    for name, frame in records.items():
        if name != candidate:
            continue
        if isinstance(values, dict):
            errors = frame["validation_window"].map(values).astype(float)
        else:
            errors = pd.Series(float(values), index=frame.index)
        frame[column] = frame["actual_sales"] + errors
        frame["model_forecast_unclipped"] = frame[column]
        if "forecast_available" in frame:
            frame["forecast_available"] = frame[column].notna()
        frame["primary_evaluation_eligible"] = (
            frame["source_open"].eq(1) & frame["actual_sales"].notna() & frame[column].notna()
        )


def _set_horizon_errors(
    records: dict[str, pd.DataFrame], candidate: str, errors: pd.Series
) -> None:
    frame = records[candidate]
    frame[RAW_COLUMNS[candidate]] = frame["actual_sales"] + errors.to_numpy(dtype=float)
    frame["model_forecast_unclipped"] = frame[RAW_COLUMNS[candidate]]
    frame["forecast_available"] = frame[RAW_COLUMNS[candidate]].notna()
    frame["primary_evaluation_eligible"] = (
        frame["source_open"].eq(1)
        & frame["actual_sales"].notna()
        & frame[RAW_COLUMNS[candidate]].notna()
    )


def _review_status(result: dict[str, object], candidate: str) -> str:
    return str(result["decision"]["operational_review"][candidate]["decision"])


def test_exact_candidate_population_and_chronological_windows_are_enforced() -> None:
    records = _records()
    validate_candidate_records(records)

    with pytest.raises(EvidenceReviewRequired, match="Candidate IDs"):
        validate_candidate_records({**records, "extra": records[CANDIDATE_IDS[0]]})

    changed = {key: frame.copy() for key, frame in records.items()}
    changed[CANDIDATE_IDS[0]].loc[0, "forecast_origin"] += pd.Timedelta(days=1)
    with pytest.raises(EvidenceReviewRequired, match="window|horizon"):
        validate_candidate_records(changed)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra"])
def test_missing_extra_and_duplicate_keys_stop_selection(mutation: str) -> None:
    records = _records()
    candidate = CANDIDATE_IDS[1]
    if mutation == "missing":
        records[candidate] = records[candidate].iloc[1:].copy()
    elif mutation == "duplicate":
        records[candidate] = pd.concat(
            [records[candidate], records[candidate].iloc[[0]]], ignore_index=True
        )
    else:
        extra = records[candidate].iloc[[0]].copy()
        extra["Store"] = 999
        records[candidate] = pd.concat([records[candidate], extra], ignore_index=True)
    with pytest.raises(EvidenceReviewRequired, match="key|unique|population"):
        validate_candidate_records(records)


@pytest.mark.parametrize("label", ["actual_sales", "source_open", "horizon", "validation_window"])
def test_shared_label_and_window_metadata_must_match(label: str) -> None:
    records = _records()
    records[CANDIDATE_IDS[2]].loc[0, label] = (
        88
        if label == "actual_sales"
        else (0 if label == "source_open" else (88 if label == "horizon" else "validation_2"))
    )
    with pytest.raises(EvidenceReviewRequired, match="disagree|window|horizon|origin"):
        validate_candidate_records(records)


def test_standalone_and_three_way_coverage_keep_correct_denominators() -> None:
    records = _records()
    for candidate_index, candidate in enumerate(CANDIDATE_IDS):
        frame = records[candidate]
        index = frame.index[(frame["validation_window"] == "validation_1")][candidate_index]
        frame.loc[index, RAW_COLUMNS[candidate]] = np.nan
        frame.loc[index, "forecast_available"] = False
        frame.loc[index, "primary_evaluation_eligible"] = False
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    comparison = result["model_comparison"]
    v1 = comparison.loc[
        comparison["population"].eq("standalone")
        & comparison["scope"].eq("validation_window")
        & comparison["candidate_id"].eq(CANDIDATE_IDS[0])
        & comparison["metric"].eq("open_label_forecast_coverage_rate")
    ].iloc[0]
    common = comparison.loc[
        comparison["population"].eq("three_way_common")
        & comparison["scope"].eq("validation_window")
        & comparison["candidate_id"].eq(CANDIDATE_IDS[0])
        & comparison["metric"].eq("open_label_forecast_coverage_rate")
    ].iloc[0]
    assert v1["denominator"] == 28
    assert v1["numerator"] == 27
    assert common["denominator"] == 28
    assert common["numerator"] == 25


def test_99_percent_coverage_boundary_passes_and_below_boundary_stops() -> None:
    records = _records(stores_per_window=(100, 100, 100))
    for candidate in CANDIDATE_IDS:
        frame = records[candidate]
        indexes = frame.index[frame["validation_window"].eq("validation_1")][:14]
        frame.loc[indexes, RAW_COLUMNS[candidate]] = np.nan
        frame.loc[indexes, "forecast_available"] = False
        frame.loc[indexes, "primary_evaluation_eligible"] = False
    passed = evaluate_model_selection(records)
    assert passed["decision"]["coverage_status"] == "passed"
    assert passed["decision"]["status"] == "operational_review_required"

    candidate = CANDIDATE_IDS[0]
    frame = records[candidate]
    second = frame.index[frame["validation_window"].eq("validation_1")][14]
    frame.loc[second, RAW_COLUMNS[candidate]] = np.nan
    frame.loc[second, "forecast_available"] = False
    frame.loc[second, "primary_evaluation_eligible"] = False
    failed = evaluate_model_selection(records)
    assert failed["decision"]["coverage_status"] == "failed"
    assert failed["decision"]["status"] == "coverage_review_required"
    assert "selected_candidate_id" not in failed["decision"]


def test_invalid_available_and_eligible_masks_are_rejected() -> None:
    records = _records()
    records[CANDIDATE_IDS[0]].loc[0, "primary_evaluation_eligible"] = False
    with pytest.raises(EvidenceReviewRequired, match="mask"):
        validate_candidate_records(records)
    records = _records()
    records[CANDIDATE_IDS[0]].loc[0, RAW_COLUMNS[CANDIDATE_IDS[0]]] = -1.0
    with pytest.raises(EvidenceReviewRequired, match="non-negative|finite"):
        validate_candidate_records(records)


def test_final_holdout_date_is_rejected_before_any_selection_population_is_built() -> None:
    records = _records()
    frame = records[CANDIDATE_IDS[0]]
    row = frame.index[-1]
    frame.loc[row, "Date"] = pd.Timestamp("2015-07-04")
    frame.loc[row, "horizon"] = 15
    with pytest.raises(EvidenceReviewRequired, match="1..14|unexpected date|after 2015-07-03"):
        validate_candidate_records(records)


def test_pooled_mae_is_row_pooled_not_average_of_window_maes() -> None:
    records = _records(stores_per_window=(1, 2, 3))
    _set_errors(
        records, CANDIDATE_IDS[0], {"validation_1": 10, "validation_2": 20, "validation_3": 30}
    )
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    pooled = (
        result["model_comparison"]
        .loc[
            result["model_comparison"]["population"].eq("standalone")
            & result["model_comparison"]["candidate_id"].eq(CANDIDATE_IDS[0])
            & result["model_comparison"]["scope"].eq("pooled")
            & result["model_comparison"]["metric"].eq("mae")
        ]
        .iloc[0]
    )
    assert pooled["value"] == pytest.approx((14 * 10 + 28 * 20 + 42 * 30) / 84)
    assert pooled["value"] != pytest.approx((10 + 20 + 30) / 3)


def test_pairwise_and_three_way_populations_are_exactly_common_available_rows() -> None:
    records = _records()
    target = records[CANDIDATE_IDS[0]].index[0]
    records[CANDIDATE_IDS[2]].loc[target, RAW_COLUMNS[CANDIDATE_IDS[2]]] = np.nan
    records[CANDIDATE_IDS[2]].loc[target, "forecast_available"] = False
    records[CANDIDATE_IDS[2]].loc[target, "primary_evaluation_eligible"] = False
    result = evaluate_model_selection(records)
    metrics = result["model_comparison"]
    pair_rows = metrics.loc[
        metrics["population"].eq("pairwise")
        & metrics["scope"].eq("pooled")
        & metrics["candidate_id"].eq(CANDIDATE_IDS[0])
        & metrics["paired_with"].eq(CANDIDATE_IDS[1])
        & metrics["metric"].eq("eligible_rows")
    ].iloc[0]
    three_rows = metrics.loc[
        metrics["population"].eq("three_way_common")
        & metrics["scope"].eq("pooled")
        & metrics["candidate_id"].eq(CANDIDATE_IDS[0])
        & metrics["metric"].eq("eligible_rows")
    ].iloc[0]
    assert pair_rows["value"] == 84
    assert three_rows["value"] == 83
    pair_delta = metrics.loc[
        metrics["population"].eq("pairwise")
        & metrics["scope"].eq("validation_window")
        & metrics["validation_window"].eq("validation_1")
        & metrics["candidate_id"].eq(CANDIDATE_IDS[0])
        & metrics["paired_with"].eq(CANDIDATE_IDS[1])
        & metrics["metric"].eq("mae")
    ].iloc[0]
    assert pair_delta["paired_mae_delta"] == pytest.approx(5.0)
    excluded = metrics.loc[
        metrics["population"].eq("pairwise")
        & metrics["candidate_id"].eq(CANDIDATE_IDS[0])
        & metrics["paired_with"].eq(CANDIDATE_IDS[2])
        & metrics["scope"].eq("pooled")
        & metrics["metric"].eq("forecast_unavailable_reason")
    ]
    assert excluded.iloc[0]["value"] == 1
    assert excluded.iloc[0]["unavailable_reason"] == (
        "excluded_from_common_comparison_due_to_peer_unavailability"
    )


def test_promotion_threshold_is_at_least_five_percent_with_full_precision() -> None:
    records = _records()
    _set_errors(records, CANDIDATE_IDS[1], 95.0)
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    hw = result["decision"]["numeric_ladder"][0]
    assert hw["pooled_mae_improvement_fraction"] == pytest.approx(0.05)
    assert hw["promotes"] is True

    records = _records()
    _set_errors(records, CANDIDATE_IDS[1], 95.000001)
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    assert result["decision"]["numeric_ladder"][0]["promotes"] is False


def test_window_wins_are_strict_and_window_and_week_block_caps_are_inclusive() -> None:
    records = _records()
    _set_errors(
        records,
        CANDIDATE_IDS[1],
        {"validation_1": 90.0, "validation_2": 90.0, "validation_3": 110.0},
    )
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    gate = result["decision"]["numeric_ladder"][0]
    assert gate["strict_window_wins"] == 2
    assert gate["window_regression_cap_passed"] is True
    assert gate["week_block_regression_cap_passed"] is True

    records = _records()
    _set_errors(records, CANDIDATE_IDS[1], 111.0)
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    gate = result["decision"]["numeric_ladder"][0]
    assert gate["window_regression_cap_passed"] is False

    records = _records()
    _set_horizon_errors(
        records,
        CANDIDATE_IDS[1],
        pd.Series(
            [75.0 if horizon <= 7 else 110.0 for horizon in records[CANDIDATE_IDS[1]]["horizon"]]
        ),
    )
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    gate = result["decision"]["numeric_ladder"][0]
    assert gate["week_block_regression_cap_passed"] is True
    assert gate["numeric_gates_passed"] is True

    records = _records()
    _set_horizon_errors(
        records,
        CANDIDATE_IDS[1],
        pd.Series(
            [75.0 if horizon <= 7 else 110.0001 for horizon in records[CANDIDATE_IDS[1]]["horizon"]]
        ),
    )
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    gate = result["decision"]["numeric_ladder"][0]
    assert gate["week_block_regression_cap_passed"] is False
    assert gate["numeric_gates_passed"] is False


def test_failed_holt_winters_still_compares_lightgbm_directly_to_seasonal_naive() -> None:
    records = _records()
    _set_errors(records, CANDIDATE_IDS[1], 120.0)
    _set_errors(records, CANDIDATE_IDS[2], 90.0)
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    ladder = result["decision"]["numeric_ladder"]
    assert ladder[0]["incumbent_before"] == CANDIDATE_IDS[0]
    assert ladder[0]["promotes"] is False
    assert ladder[1]["candidate_id"] == CANDIDATE_IDS[2]
    assert ladder[1]["incumbent_before"] == CANDIDATE_IDS[0]
    assert ladder[1]["promotes"] is True


def test_ties_retain_simpler_candidate_and_zero_mae_cannot_be_improved() -> None:
    records = _records()
    _set_errors(records, CANDIDATE_IDS[1], 100.0)
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    assert result["decision"]["numeric_ladder"][0]["promotes"] is False
    assert result["decision"]["numeric_ladder"][0]["tie_or_zero_incumbent"] is True

    records = _records()
    _set_errors(records, CANDIDATE_IDS[0], 0.0)
    _set_errors(records, CANDIDATE_IDS[1], 0.0)
    result = evaluate_model_selection(records, operational_reviews=_reviews())
    assert result["decision"]["numeric_ladder"][0]["promotes"] is False


def test_rejected_candidate_retains_incumbent_while_unknown_blocks_promotion() -> None:
    records = _records()
    reviews = _reviews()
    reviews[CANDIDATE_IDS[0]]["decision"] = "approved"
    reviews[CANDIDATE_IDS[1]]["decision"] = "rejected"
    reviews[CANDIDATE_IDS[2]]["decision"] = "unknown"
    result = evaluate_model_selection(records, operational_reviews=reviews)
    assert result["decision"]["status"] == "operational_review_required"
    assert _review_status(result, CANDIDATE_IDS[1]) == "rejected"
    assert result["decision"]["operational_ladder"][0]["outcome"] == "rejected_retained_incumbent"
    assert (
        result["decision"]["operational_ladder"][1]["gate"]["incumbent_before"] == CANDIDATE_IDS[0]
    )
    assert "selected_candidate_id" not in result["decision"]
    assert result["selected_artifacts"] is None


def test_default_operational_reviews_are_unknown_and_never_emit_selection() -> None:
    result = evaluate_model_selection(_records())
    assert all(_review_status(result, candidate) == "unknown" for candidate in CANDIDATE_IDS)
    assert result["decision"]["status"] == "operational_review_required"
    assert "selected_candidate_id" not in result["decision"]
    assert result["selected_artifacts"] is None


def test_input_order_is_deterministic_and_frames_are_not_mutated() -> None:
    records = _records()
    before = {candidate: frame.copy(deep=True) for candidate, frame in records.items()}
    first = evaluate_model_selection(records)
    shuffled = {
        candidate: frame.sample(frac=1, random_state=index).reset_index(drop=True)
        for index, (candidate, frame) in enumerate(records.items())
    }
    second = evaluate_model_selection(shuffled)
    pd.testing.assert_frame_equal(first["model_comparison"], second["model_comparison"])
    for candidate in CANDIDATE_IDS:
        pd.testing.assert_frame_equal(records[candidate], before[candidate])


def test_manifest_hash_mismatch_is_an_evidence_review_failure(tmp_path: Path) -> None:
    for candidate in CANDIDATE_IDS:
        folder = tmp_path / "data" / "processed" / candidate
        folder.mkdir(parents=True)
        artifact = folder / "development_forecasts.parquet"
        artifact.write_bytes(b"forecast evidence")
        manifest = {
            "candidate_id": candidate,
            "final_holdout_forecast_or_evaluation": False,
            "development_only_through": "2015-07-03",
            "artifacts": {
                artifact.relative_to(tmp_path).as_posix(): {
                    "sha256": "0" * 64,
                    "rows": 1,
                }
            },
        }
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvidenceReviewRequired, match="hash"):
        verify_candidate_manifests(tmp_path)


def test_missing_candidate_artifact_provenance_fails_closed(tmp_path: Path) -> None:
    for candidate in CANDIDATE_IDS:
        folder = tmp_path / "data" / "processed" / candidate
        folder.mkdir(parents=True)
        (folder / "manifest.json").write_text(
            json.dumps({"candidate_id": candidate}), encoding="utf-8"
        )
    with pytest.raises(EvidenceReviewRequired, match="artifact|development|identity|manifest"):
        verify_candidate_manifests(tmp_path)


def test_raw_operational_forecasts_and_signed_residual_paths_remain_distinct() -> None:
    records = _records()
    candidate = CANDIDATE_IDS[0]
    frame = records[candidate]
    frame.loc[0, "source_open"] = 0.0
    frame.loc[0, "operational_forecast"] = 0.0
    frame.loc[0, "primary_evaluation_eligible"] = False
    output = build_selected_artifacts(candidate, frame, build_refit_recipe(candidate, {}))
    forecasts = output["selected_development_forecasts"]
    residuals = output["development_residual_paths"]
    closed = forecasts.iloc[0]
    assert closed["raw_forecast"] != 0.0
    assert closed["operational_forecast"] == 0.0
    assert "raw_primary_path_complete" in residuals
    assert "operational_path_complete" in residuals
    row = residuals.iloc[0]
    assert row["raw_residual"] == pytest.approx(row["actual_sales"] - row["raw_forecast"])
    assert row["operational_residual"] == pytest.approx(
        row["actual_sales"] - row["operational_forecast"]
    )


def test_absent_source_day_is_explicit_and_partial_paths_are_not_zero_filled() -> None:
    records = _records()
    candidate = CANDIDATE_IDS[0]
    frame = records[candidate].loc[records[candidate]["Store"].eq(1)].copy()
    missing_date = frame["Date"].min() + pd.Timedelta(days=4)
    frame = frame.loc[frame["Date"].ne(missing_date)].copy()
    output = build_selected_artifacts(candidate, frame, build_refit_recipe(candidate, {}))
    paths = output["development_residual_paths"]
    missing = paths.loc[paths["Date"].eq(missing_date)]
    assert len(missing) == 1
    assert not bool(missing.iloc[0]["target_key_observed"])
    assert pd.isna(missing.iloc[0]["actual_sales"])
    assert pd.isna(missing.iloc[0]["raw_forecast"])
    assert missing.iloc[0]["unavailable_reason"] == "target_key_not_observed"
    assert not bool(missing.iloc[0]["raw_primary_path_complete"])


def test_refit_recipes_freeze_each_approved_method_without_fitting_or_tuning() -> None:
    recipes = {candidate: build_refit_recipe(candidate, {}) for candidate in CANDIDATE_IDS}
    assert recipes[CANDIDATE_IDS[0]]["seasonal_lag_days"] == 7
    assert recipes[CANDIDATE_IDS[0]]["recursive_horizons"] == [8, 9, 10, 11, 12, 13, 14]
    assert recipes[CANDIDATE_IDS[1]]["seasonal_periods"] == 7
    assert recipes[CANDIDATE_IDS[1]]["minimum_contiguous_history_days"] == 28
    lightgbm = recipes[CANDIDATE_IDS[2]]
    assert lightgbm["selected_trial"] == "A"
    assert lightgbm["selected_boosting_rounds"] == 180
    assert len(lightgbm["predictor_contract_identity"]["ordered_columns"]) == 29
    assert lightgbm["fit_performed"] is False
    assert "July 3" in lightgbm["authorization_boundary"]
    with pytest.raises(EvidenceReviewRequired, match="Holt-Winters configuration"):
        build_refit_recipe(CANDIDATE_IDS[1], {"seasonal_periods": 5})
    with pytest.raises(EvidenceReviewRequired, match="trial A"):
        build_refit_recipe(
            CANDIDATE_IDS[2],
            {"selected_trial": "B", "selected_boosting_rounds": 180},
        )


def test_output_directory_is_git_ignored() -> None:
    from rossmann_forecasting.forecasting.model_selection import assert_output_directory_ignored

    assert_output_directory_ignored(Path(__file__).resolve().parents[1])
