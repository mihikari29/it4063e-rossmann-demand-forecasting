"""Synthetic tests for the approved Phase 7 selection contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import rossmann_forecasting.forecasting.model_selection as model_selection
from rossmann_forecasting.forecasting.model_selection import (
    CANDIDATE_IDS,
    CandidateEvidence,
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
    output: dict[str, pd.DataFrame] = {}
    for candidate in CANDIDATE_IDS:
        frame = combined.loc[
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
        frame["operational_forecast"] = frame[RAW_COLUMNS[candidate]]
        frame["model_forecast_unclipped"] = frame[RAW_COLUMNS[candidate]]
        output[candidate] = frame
    return output


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


_SELECTED_ARTIFACTS = (
    "selected_model_config.json",
    "refit_recipe.json",
    "selected_development_forecasts.parquet",
    "development_residual_paths.parquet",
)


def _runner_fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, CandidateEvidence]:
    evidence: dict[str, CandidateEvidence] = {}
    for candidate in CANDIDATE_IDS:
        manifest_path = root / "data" / "processed" / candidate / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"candidate_id": candidate, "fixture_only": True}
        manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode("utf-8")
        manifest_path.write_bytes(manifest_bytes)
        configuration = None
        if candidate == CANDIDATE_IDS[2]:
            configuration = {
                "selected_trial": "A",
                "selected_boosting_rounds": 180,
                "trial_parameters": dict(model_selection.TRIAL_PARAMETERS["A"]),
                "predictor_columns": list(model_selection.PREDICTOR_COLUMNS),
                "shared_parameters": dict(model_selection.LIGHTGBM_FIXED_PARAMETERS),
            }
        evidence[candidate] = CandidateEvidence(
            candidate_id=candidate,
            manifest_path=manifest_path,
            manifest=manifest,
            manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            artifact_hashes={},
            configuration=configuration,
        )

    records = _records()
    monkeypatch.setattr(model_selection, "assert_output_directory_ignored", lambda _root: None)
    monkeypatch.setattr(model_selection, "verify_candidate_manifests", lambda _root: evidence)
    monkeypatch.setattr(
        model_selection,
        "_load_saved_forecasts",
        lambda _root, _evidence: {key: value.copy(deep=True) for key, value in records.items()},
    )
    return evidence


def _synthetic_reviews_path(root: Path) -> Path:
    path = root / "synthetic-operational-review-fixture.json"
    path.write_text(json.dumps({"reviews": _reviews()}), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_manifest_has_no_current_selection(manifest: dict[str, object]) -> None:
    assert manifest["selected_candidate_id"] is None
    assert manifest["selected_model_artifacts"] == {}
    assert not set(_SELECTED_ARTIFACTS).intersection(manifest["outputs"])


def _assert_manifest_output_hashes(manifest: dict[str, object], output_dir: Path) -> None:
    outputs = manifest["outputs"]
    for name, metadata in outputs.items():
        actual_hash = hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
        assert actual_hash == metadata["sha256"]


def test_synthetic_operational_approvals_can_select_and_publish_four_coherent_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _runner_fixture(tmp_path, monkeypatch)
    original_manifests = {
        candidate: item.manifest_path.read_bytes() for candidate, item in evidence.items()
    }
    review_path = _synthetic_reviews_path(tmp_path)

    result = model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)

    output_dir = tmp_path / "data" / "processed" / "model_selection"
    manifest = _read_json(output_dir / "manifest.json")
    assert result["status"] == "selected"
    assert result["selected_candidate_id"] == CANDIDATE_IDS[2]
    assert manifest["status"] == "selected"
    assert manifest["selected_candidate_id"] == CANDIDATE_IDS[2]
    assert manifest["publication_state"] == "complete"
    assert set(manifest["selected_model_artifacts"]) == set(_SELECTED_ARTIFACTS)
    assert set(_SELECTED_ARTIFACTS).issubset(manifest["outputs"])

    decision = _read_json(output_dir / "selection_decision.json")
    recipe = _read_json(output_dir / "refit_recipe.json")
    selected_config = _read_json(output_dir / "selected_model_config.json")
    run_id = manifest["selection_run_id"]
    assert decision["selection_run_id"] == run_id
    assert recipe["selection_run_id"] == run_id
    assert selected_config["selection_run_id"] == run_id
    assert (
        selected_config["refit_recipe_sha256"]
        == manifest["selected_model_artifacts"]["refit_recipe.json"]["sha256"]
    )
    for name in _SELECTED_ARTIFACTS:
        path = output_dir / name
        assert path.is_file()
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual_hash == manifest["outputs"][name]["sha256"]
        assert actual_hash == manifest["selected_model_artifacts"][name]["sha256"]
    _assert_manifest_output_hashes(manifest, output_dir)

    for name in ("selected_development_forecasts.parquet", "development_residual_paths.parquet"):
        frame = pd.read_parquet(output_dir / name)
        assert frame["model_selection_run_id"].eq(run_id).all()
    assert {candidate: item.manifest_path.read_bytes() for candidate, item in evidence.items()} == (
        original_manifests
    )


def test_unknown_operational_review_retires_owned_selected_outputs_and_preserves_unrelated_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _runner_fixture(tmp_path, monkeypatch)
    review_path = _synthetic_reviews_path(tmp_path)
    model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)
    output_dir = tmp_path / "data" / "processed" / "model_selection"
    unrelated = output_dir / "user-note.txt"
    unrelated.write_text("leave me intact", encoding="utf-8")
    original_manifests = {
        candidate: item.manifest_path.read_bytes() for candidate, item in evidence.items()
    }

    result = model_selection.run_model_selection(root=tmp_path)

    manifest = _read_json(output_dir / "manifest.json")
    assert result["status"] == "operational_review_required"
    assert manifest["status"] == "operational_review_required"
    _assert_manifest_has_no_current_selection(manifest)
    assert all(not (output_dir / name).exists() for name in _SELECTED_ARTIFACTS)
    _assert_manifest_output_hashes(manifest, output_dir)
    assert unrelated.read_text(encoding="utf-8") == "leave me intact"
    assert {candidate: item.manifest_path.read_bytes() for candidate, item in evidence.items()} == (
        original_manifests
    )


def test_integrity_failure_retires_owned_selected_outputs_without_current_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _runner_fixture(tmp_path, monkeypatch)
    review_path = _synthetic_reviews_path(tmp_path)
    model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)
    output_dir = tmp_path / "data" / "processed" / "model_selection"
    real_verify = model_selection.verify_candidate_manifests
    calls = 0

    def fail_second_verification(root: str | Path) -> dict[str, CandidateEvidence]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise EvidenceReviewRequired("synthetic original artifact hash mismatch")
        return real_verify(root)

    monkeypatch.setattr(model_selection, "verify_candidate_manifests", fail_second_verification)
    result = model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)

    manifest = _read_json(output_dir / "manifest.json")
    assert result["status"] == "evidence_review_required"
    assert manifest["status"] == "evidence_review_required"
    _assert_manifest_has_no_current_selection(manifest)
    assert all(not (output_dir / name).exists() for name in _SELECTED_ARTIFACTS)
    _assert_manifest_output_hashes(manifest, output_dir)


def test_selected_artifact_generation_failure_publishes_failure_and_retires_old_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _runner_fixture(tmp_path, monkeypatch)
    review_path = _synthetic_reviews_path(tmp_path)
    model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)
    output_dir = tmp_path / "data" / "processed" / "model_selection"
    real_to_parquet = pd.DataFrame.to_parquet

    def fail_selected_parquet(frame: pd.DataFrame, *args: object, **kwargs: object) -> None:
        raise OSError("synthetic selected-artifact write failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail_selected_parquet)
    result = model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", real_to_parquet)

    manifest = _read_json(output_dir / "manifest.json")
    decision = _read_json(output_dir / "selection_decision.json")
    assert result["status"] == "artifact_generation_failed"
    assert manifest["status"] == "artifact_generation_failed"
    assert decision["status"] == "artifact_generation_failed"
    assert decision["artifact_publication_status"] == "failed"
    _assert_manifest_has_no_current_selection(manifest)
    assert all(not (output_dir / name).exists() for name in _SELECTED_ARTIFACTS)
    _assert_manifest_output_hashes(manifest, output_dir)


def test_unverified_selected_file_is_preserved_and_publication_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _runner_fixture(tmp_path, monkeypatch)
    review_path = _synthetic_reviews_path(tmp_path)
    model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)
    output_dir = tmp_path / "data" / "processed" / "model_selection"
    tampered_path = output_dir / _SELECTED_ARTIFACTS[0]
    tampered_path.write_bytes(tampered_path.read_bytes() + b"external edit")
    tampered_hash = hashlib.sha256(tampered_path.read_bytes()).hexdigest()

    result = model_selection.run_model_selection(root=tmp_path)

    manifest = _read_json(output_dir / "manifest.json")
    assert result["status"] == "artifact_publication_failed"
    assert manifest["status"] == "artifact_publication_failed"
    _assert_manifest_has_no_current_selection(manifest)
    assert tampered_path.is_file()
    assert hashlib.sha256(tampered_path.read_bytes()).hexdigest() == tampered_hash
    assert any(
        conflict["path"] == _SELECTED_ARTIFACTS[0]
        for conflict in manifest["publication"]["conflicts"]
    )
    _assert_manifest_output_hashes(manifest, output_dir)


def test_cannot_invalidate_manifest_leaves_prior_selection_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _runner_fixture(tmp_path, monkeypatch)
    review_path = _synthetic_reviews_path(tmp_path)
    model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)
    output_dir = tmp_path / "data" / "processed" / "model_selection"
    manifest_path = output_dir / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    original_artifacts = {
        name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
        for name in _SELECTED_ARTIFACTS
    }

    def fail_manifest_write(path: Path, _value: dict[str, object]) -> None:
        if path == manifest_path:
            raise OSError("synthetic manifest replacement failure")
        raise AssertionError("runner must stop before staging if it cannot publish its marker")

    monkeypatch.setattr(model_selection, "_write_json_atomically", fail_manifest_write)
    result = model_selection.run_model_selection(root=tmp_path)

    assert result["status"] == "artifact_publication_failed"
    assert manifest_path.read_bytes() == original_manifest
    assert {
        name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
        for name in _SELECTED_ARTIFACTS
    } == original_artifacts


def test_runner_never_invokes_candidate_fit_or_tuning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _runner_fixture(tmp_path, monkeypatch)
    review_path = _synthetic_reviews_path(tmp_path)
    commands: list[str] = []
    real_run = model_selection.subprocess.run

    def guarded_run(args: object, *positional: object, **kwargs: object) -> object:
        command = " ".join(str(item) for item in args)
        commands.append(command)
        assert not any(
            runner in command
            for runner in ("run_seasonal_naive.py", "run_holt_winters.py", "run_lightgbm.py")
        )
        return real_run(args, *positional, **kwargs)

    def forbidden_fit(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("selection runner must not fit or tune a candidate")

    monkeypatch.setattr(model_selection.subprocess, "run", guarded_run)
    monkeypatch.setattr(model_selection.lgb, "train", forbidden_fit)
    result = model_selection.run_model_selection(root=tmp_path, operational_review_path=review_path)

    output_dir = tmp_path / "data" / "processed" / "model_selection"
    recipe = _read_json(output_dir / "refit_recipe.json")
    assert result["status"] == "selected"
    assert recipe["fit_performed"] is False
    assert recipe["no_tuning_or_refit_performed"] is True
    assert all(
        not any(
            runner in command
            for runner in ("run_seasonal_naive.py", "run_holt_winters.py", "run_lightgbm.py")
        )
        for command in commands
    )


def test_residual_paths_preserve_keys_masks_signs_and_complete_partial_path_flags() -> None:
    records = _records()
    candidate = CANDIDATE_IDS[0]
    frame = records[candidate]
    selected_window = APPROVED_DEVELOPMENT_WINDOWS[0]
    frame = frame.loc[
        frame["validation_window"].eq(selected_window.name) & frame["Store"].isin([1, 2])
    ].copy()
    missing_date = selected_window.forecast_origin + pd.Timedelta(days=7)
    frame = frame.loc[~(frame["Store"].eq(1) & frame["Date"].eq(missing_date))].copy()
    closed = frame.index[frame["Store"].eq(1) & frame["horizon"].eq(1)][0]
    unknown = frame.index[frame["Store"].eq(1) & frame["horizon"].eq(4)][0]
    underforecast = frame.index[frame["Store"].eq(1) & frame["horizon"].eq(3)][0]
    frame.loc[closed, "source_open"] = 0.0
    frame.loc[closed, "operational_forecast"] = 0.0
    frame.loc[closed, "primary_evaluation_eligible"] = False
    frame.loc[unknown, "source_open"] = np.nan
    frame.loc[unknown, "operational_forecast"] = np.nan
    frame.loc[unknown, "primary_evaluation_eligible"] = False
    frame.loc[underforecast, "raw_baseline_forecast"] = (
        frame.loc[underforecast, "actual_sales"] - 10.0
    )
    frame.loc[underforecast, "operational_forecast"] = frame.loc[
        underforecast, "raw_baseline_forecast"
    ]
    frame.loc[underforecast, "model_forecast_unclipped"] = frame.loc[
        underforecast, "raw_baseline_forecast"
    ]

    output = build_selected_artifacts(candidate, frame, build_refit_recipe(candidate, {}))
    paths = output["development_residual_paths"]
    store_one = paths.loc[paths["Store"].eq(1)].sort_values("horizon")
    store_two = paths.loc[paths["Store"].eq(2)].sort_values("horizon")
    assert store_one[["Store", "forecast_origin", "horizon"]].drop_duplicates().shape[0] == 14
    assert store_one["horizon"].tolist() == list(range(1, 15))
    assert store_two["horizon"].tolist() == list(range(1, 15))

    closed_row = store_one.loc[store_one["horizon"].eq(1)].iloc[0]
    assert closed_row["raw_forecast"] > 0
    assert closed_row["operational_forecast"] == 0.0
    assert not bool(closed_row["raw_primary_error_available"])
    assert bool(closed_row["operational_error_available"])
    overforecast_row = store_one.loc[store_one["horizon"].eq(2)].iloc[0]
    underforecast_row = store_one.loc[store_one["horizon"].eq(3)].iloc[0]
    assert overforecast_row["raw_residual"] < 0
    assert underforecast_row["raw_residual"] == pytest.approx(10.0)
    assert bool(overforecast_row["primary_evaluation_eligible"])
    unknown_row = store_one.loc[store_one["horizon"].eq(4)].iloc[0]
    assert pd.isna(unknown_row["operational_forecast"])
    assert not bool(unknown_row["operational_error_available"])
    missing_row = store_one.loc[store_one["horizon"].eq(7)].iloc[0]
    assert not bool(missing_row["target_key_observed"])
    assert pd.isna(missing_row["actual_sales"])
    assert pd.isna(missing_row["raw_forecast"])
    assert not bool(missing_row["primary_evaluation_eligible"])
    assert not bool(store_one["raw_primary_path_complete"].iloc[0])
    assert not bool(store_one["operational_path_complete"].iloc[0])
    assert bool(store_two["raw_primary_path_complete"].iloc[0])
    assert bool(store_two["operational_path_complete"].iloc[0])
