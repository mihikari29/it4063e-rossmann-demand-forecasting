"""Fixture tests for the accepted Phase 8 empirical uncertainty contract."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

import rossmann_forecasting.forecasting.uncertainty as uncertainty


def _fixture_paths(stores: int = 55) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for window_name, window in uncertainty.WINDOWS.items():
        origin = window["origin"]
        for store in range(1, stores + 1):
            for horizon in range(1, 15):
                open_value: float | None = 1.0
                if store == stores - 1:
                    open_value = 0.0
                elif store == stores:
                    open_value = None
                raw = 1000.0 + store * 2.0 + horizon
                error = float((store % 9) - 4 + ((horizon + store) % 3))
                actual = raw + error
                if open_value == 0.0:
                    actual = 8.0 if horizon == 1 else 0.0
                op = raw if open_value == 1.0 else (0.0 if open_value == 0.0 else np.nan)
                raw_residual = actual - raw
                op_residual = actual - op if np.isfinite(op) else np.nan
                raw_eligible = open_value == 1.0
                op_available = open_value is not None
                rows.append(
                    {
                        "Store": store,
                        "forecast_origin": origin,
                        "Date": origin + pd.Timedelta(days=horizon),
                        "horizon": horizon,
                        "validation_window": window_name,
                        "target_key_observed": True,
                        "actual_sales": actual,
                        "source_open": open_value,
                        "raw_forecast": raw,
                        "raw_model_forecast": raw,
                        "operational_forecast": op,
                        "raw_residual": raw_residual,
                        "operational_residual": op_residual,
                        "raw_primary_error_available": raw_eligible,
                        "operational_error_available": op_available,
                        "primary_evaluation_eligible": raw_eligible,
                        "forecast_available": True,
                        "operational_forecast_available": op_available,
                        "candidate_id": uncertainty.SELECTED_CANDIDATE_ID,
                        "model_config_identity": uncertainty.SELECTED_CANDIDATE_ID,
                        "model_configuration_sha256": "a" * 64,
                        "model_selection_run_id": uncertainty.MODEL_SELECTION_RUN_ID,
                        "source_manifest_sha256": "b" * 64,
                        "model_forecast_unclipped": raw,
                        "forecast_was_clipped": False,
                        "unavailable_reason": None,
                    }
                )
    return pd.DataFrame(rows)


def _remove_component(frame: pd.DataFrame, window: str, store: int, horizon: int) -> None:
    mask = (
        frame["validation_window"].eq(window)
        & frame["Store"].eq(store)
        & frame["horizon"].eq(horizon)
    )
    frame.loc[mask, "target_key_observed"] = False
    frame.loc[mask, ["actual_sales", "source_open", "raw_forecast", "raw_model_forecast"]] = np.nan
    frame.loc[mask, ["operational_forecast", "raw_residual", "operational_residual"]] = np.nan
    frame.loc[
        mask,
        [
            "raw_primary_error_available",
            "operational_error_available",
            "primary_evaluation_eligible",
            "forecast_available",
            "operational_forecast_available",
        ],
    ] = False


def test_exact_rank_arithmetic_and_ties_are_order_statistics() -> None:
    assert uncertainty.exact_daily_ranks(39) == (1, 39)
    assert uncertainty.exact_daily_ranks(40) == (1, 40)
    assert uncertainty.exact_upper_rank(49, "0.98") == 49
    assert uncertainty.exact_upper_rank(50, "0.98") == 50
    ties = np.asarray([5.0, 1.0, 5.0, 2.0])
    quantile, reason = uncertainty._quantile_record(ties, 3, minimum=1)
    assert quantile == 5.0
    assert reason is None
    unavailable, reason = uncertainty._quantile_record(ties, 0, minimum=1)
    assert unavailable is None
    assert reason == "quantile_rank_unavailable"


def test_prefix_errors_sum_signed_daily_components_in_horizon_order() -> None:
    frame = _fixture_paths()
    chosen = frame["validation_window"].eq("validation_1") & frame["Store"].eq(1)
    h1 = chosen & frame["horizon"].eq(1)
    h2 = chosen & frame["horizon"].eq(2)
    frame.loc[h1, "actual_sales"] = frame.loc[h1, "raw_forecast"] + 20.0
    frame.loc[h1, ["raw_residual", "operational_residual"]] = 20.0
    frame.loc[h2, "actual_sales"] = frame.loc[h2, "raw_forecast"] - 20.0
    frame.loc[h2, ["raw_residual", "operational_residual"]] = -20.0
    prefixes = uncertainty._prefix_observations(frame.loc[chosen])
    prefix = prefixes.loc[prefixes["k"].eq(2)].iloc[0]
    assert prefix["prefix_error"] == 0.0
    assert prefix["error_prefix_complete"]


def test_fit_chronology_and_assessment_labels_cannot_change_quantiles() -> None:
    original = _fixture_paths()
    baseline = uncertainty.calculate_uncertainty(original)
    changed = original.copy(deep=True)
    assessment = changed["validation_window"].eq("validation_3")
    changed.loc[assessment, "actual_sales"] += 5000.0
    changed.loc[assessment, "raw_residual"] = (
        changed.loc[assessment, "actual_sales"] - changed.loc[assessment, "raw_forecast"]
    )
    changed.loc[assessment, "operational_residual"] = (
        changed.loc[assessment, "actual_sales"] - changed.loc[assessment, "operational_forecast"]
    )
    rerun = uncertainty.calculate_uncertainty(changed)
    pdt.assert_frame_equal(baseline["daily_residual_quantiles"], rerun["daily_residual_quantiles"])
    pdt.assert_frame_equal(
        baseline["cumulative_error_quantiles"], rerun["cumulative_error_quantiles"]
    )
    a = baseline["daily_residual_quantiles"].query("fit_id == 'A'")
    assert set(a["calibration_windows"]) == {"validation_1"}
    b = baseline["daily_residual_quantiles"].query("fit_id == 'B'")
    assert set(b["calibration_windows"]) == {"validation_1+validation_2"}
    a_assessment = baseline["daily_intervals"].query("fit_id == 'A'")
    assert set(a_assessment["Date"].dt.date) == set(pd.date_range("2015-06-06", "2015-06-19").date)
    b_assessment = baseline["daily_intervals"].query("fit_id == 'B'")
    assert set(b_assessment["Date"].dt.date) == set(pd.date_range("2015-06-20", "2015-07-03").date)


def test_daily_sample_floor_partial_paths_and_support_clipping() -> None:
    frame = _fixture_paths()
    frame.loc[
        frame["validation_window"].eq("validation_1")
        & frame["horizon"].eq(2)
        & frame["Store"].between(1, 15),
        "source_open",
    ] = 0.0
    closed = (
        frame["validation_window"].eq("validation_1")
        & frame["horizon"].eq(2)
        & frame["Store"].between(1, 15)
    )
    frame.loc[closed, "actual_sales"] = 0.0
    frame.loc[closed, "operational_forecast"] = 0.0
    frame.loc[closed, "operational_residual"] = 0.0
    frame.loc[closed, "operational_error_available"] = True
    frame.loc[closed, "raw_residual"] = -frame.loc[closed, "raw_forecast"]
    frame.loc[closed, "raw_primary_error_available"] = False
    frame.loc[closed, "primary_evaluation_eligible"] = False
    result = uncertainty.calculate_uncertainty(frame)
    fit_a_h1 = (
        result["daily_residual_quantiles"]
        .query("fit_id == 'A' and horizon == 1 and tail == 'lower'")
        .iloc[0]
    )
    fit_a_h2 = (
        result["daily_residual_quantiles"]
        .query("fit_id == 'A' and horizon == 2 and tail == 'lower'")
        .iloc[0]
    )
    assert fit_a_h1["n"] == 53
    assert fit_a_h1["available"]
    assert fit_a_h2["n"] == 38
    assert not fit_a_h2["available"]
    assert fit_a_h2["unavailable_reason"] == "insufficient_calibration"

    clipped = uncertainty._interval_from_point(
        2.0, {"lower": -10.0, "upper": -5.0}, {"lower": None, "upper": None}
    )
    assert clipped["pre_support_lower"] == -8.0
    assert clipped["pre_support_upper"] == -3.0
    assert clipped["lower"] == clipped["upper"] == 0.0
    assert clipped["lower_support_clipped"] and clipped["upper_support_clipped"]
    assert clipped["width"] == 0.0
    assert not (clipped["lower"] <= clipped["point_forecast"] <= clipped["upper"])


def test_operational_open_closed_unknown_routes_and_preserves_violations() -> None:
    result = uncertainty.calculate_uncertainty(_fixture_paths())
    intervals = result["daily_intervals"].loc[
        result["daily_intervals"]["fit_id"].eq("A")
        & result["daily_intervals"]["Date"].eq(pd.Timestamp("2015-06-06"))
    ]
    closed = intervals.query("interval_kind == 'operational' and Store == 54").iloc[0]
    unknown = intervals.query("interval_kind == 'operational' and Store == 55").iloc[0]
    raw_closed = intervals.query("interval_kind == 'raw' and Store == 54").iloc[0]
    assert (closed["lower"], closed["upper"], closed["point_forecast"]) == (0.0, 0.0, 0.0)
    assert closed["closure_assumption_applied"]
    assert not unknown["available"]
    assert unknown["unavailable_reason"] == "opening_schedule_unknown"
    assert raw_closed["available"]
    assert raw_closed["actual_sales"] == 8.0
    diagnostics = result["coverage_diagnostics"].query(
        "fit_id == 'A' and role == 'chronological_assessment' "
        "and diagnostic == 'daily_interval_coverage' and population == 'operational_closed' "
        "and h_or_k == 1"
    )
    assert diagnostics.iloc[0]["closed_branch_assumption_violations"] == 1


def test_label_denominator_does_not_require_a_forecast() -> None:
    frame = _fixture_paths()
    missing_forecast = (
        frame["validation_window"].eq("validation_2")
        & frame["Store"].eq(1)
        & frame["horizon"].eq(1)
    )
    frame.loc[missing_forecast, ["raw_forecast", "operational_forecast"]] = np.nan
    frame.loc[missing_forecast, ["raw_residual", "operational_residual"]] = np.nan
    frame.loc[
        missing_forecast,
        [
            "forecast_available",
            "operational_forecast_available",
            "raw_primary_error_available",
            "operational_error_available",
            "primary_evaluation_eligible",
        ],
    ] = False
    result = uncertainty.calculate_uncertainty(frame)
    diagnostic = (
        result["coverage_diagnostics"]
        .query(
            "fit_id == 'A' and role == 'chronological_assessment' "
            "and population == 'raw_primary_open' and h_or_k == 1"
        )
        .iloc[0]
    )
    assert diagnostic["label_eligible_count"] == 53
    assert diagnostic["interval_available_eligible_count"] == 52
    assert diagnostic["usable_hit_denominator"] == 52


def test_missing_component_invalidates_only_prefixes_that_include_it() -> None:
    frame = _fixture_paths(stores=55)
    _remove_component(frame, "validation_1", store=1, horizon=5)
    paths = uncertainty.validate_development_paths(frame)
    prefixes = uncertainty._prefix_observations(
        paths.loc[paths["validation_window"].eq("validation_1")]
    )
    store = prefixes.loc[prefixes["Store"].eq(1)].set_index("k")
    assert bool(store.loc[4, "error_prefix_complete"])
    assert not bool(store.loc[5, "error_prefix_complete"])
    assert not bool(store.loc[14, "error_prefix_complete"])
    assert store.loc[5, "excluded_reason"] == "opening_schedule_unknown_or_target_key_missing"


def test_integrity_checks_reject_wrong_sign_masks_and_protected_dates() -> None:
    frame = _fixture_paths()
    bad_sign = frame.copy(deep=True)
    bad_sign.loc[0, "raw_residual"] += 1
    with pytest.raises(uncertainty.UncertaintyIntegrityError, match="residual sign"):
        uncertainty.validate_development_paths(bad_sign)
    bad_mask = frame.copy(deep=True)
    bad_mask.loc[0, "raw_primary_error_available"] = False
    with pytest.raises(uncertainty.UncertaintyIntegrityError, match="mask"):
        uncertainty.validate_development_paths(bad_mask)
    protected = frame.copy(deep=True)
    protected.loc[protected.index[-1], "Date"] = pd.Timestamp("2015-07-04")
    with pytest.raises(uncertainty.UncertaintyIntegrityError, match="cutoff"):
        uncertainty.validate_development_paths(protected)


def test_input_permutation_is_deterministic_and_does_not_mutate_input() -> None:
    frame = _fixture_paths()
    before = frame.copy(deep=True)
    baseline = uncertainty.calculate_uncertainty(frame)
    permuted = uncertainty.calculate_uncertainty(frame.sample(frac=1, random_state=701))
    for name in baseline:
        pdt.assert_frame_equal(baseline[name], permuted[name])
    pdt.assert_frame_equal(frame, before)


def _publication_lineage() -> dict[str, Any]:
    return {
        "selection_manifest_sha256": "1" * 64,
        "selected_candidate_manifest_sha256": "2" * 64,
        "selected_model_config_sha256": "3" * 64,
        "refit_recipe_file_sha256": "4" * 64,
        "refit_recipe_canonical_sha256": "5" * 64,
        "legacy_lineage_disclosure": "synthetic fixture lineage",
        "phase7_outputs": {},
        "candidate_lineage": {},
    }


def _publication_root(tmp_path: Path) -> Path:
    root = tmp_path
    lock = root / "uv.lock"
    lock.write_text("fixture lock", encoding="utf-8")
    uncertainty_source = Path(uncertainty.__file__)
    repo = uncertainty_source.parents[3]
    source = root / "src/rossmann_forecasting/forecasting/uncertainty.py"
    source.parent.mkdir(parents=True)
    shutil.copyfile(uncertainty_source, source)
    script = root / "scripts/run_forecast_uncertainty.py"
    script.parent.mkdir(parents=True)
    shutil.copyfile(repo / "scripts/run_forecast_uncertainty.py", script)
    return root


def test_publication_writes_manifest_last_and_updates_current_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _publication_root(tmp_path)
    frame = _fixture_paths()
    monkeypatch.setattr(
        uncertainty, "_verify_phase7_inputs", lambda _root: (frame, _publication_lineage())
    )
    monkeypatch.setattr(uncertainty, "_assert_ignored", lambda _root: None)
    write_order: list[str] = []
    original_writer = uncertainty._json_write

    def capture_writer(path: Path, value: dict[str, Any]) -> None:
        write_order.append(path.name)
        original_writer(path, value)

    monkeypatch.setattr(uncertainty, "_json_write", capture_writer)
    result = uncertainty.run_uncertainty(root, run_id="fixture-run")
    run_dir = root / "data/processed/uncertainty/fixture-run"
    assert result["manifest"]["status"] == "complete"
    pointer_write = next(
        i for i, name in enumerate(write_order) if name.startswith(".current.json.")
    )
    assert write_order.index("manifest.json") < pointer_write
    assert (run_dir / "manifest.json").is_file()
    assert (root / "data/processed/uncertainty/current.json").is_file()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, metadata in manifest["outputs"].items():
        assert hashlib.sha256((run_dir / name).read_bytes()).hexdigest() == metadata["sha256"]
    assert manifest["boundaries"]["holdout_open_sales_customers_opened_loaded_or_hashed"] is False
    assert manifest["external_fit_b_results_review_pending"]


def test_failed_publication_preserves_prior_run_and_current_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _publication_root(tmp_path)
    output = root / "data/processed/uncertainty"
    output.mkdir(parents=True)
    previous = output / "previous-run"
    previous.mkdir()
    (previous / "manifest.json").write_text('{"status":"complete"}\n', encoding="utf-8")
    pointer = output / "current.json"
    pointer.write_text('{"run_id":"previous-run"}\n', encoding="utf-8")
    previous_manifest = (previous / "manifest.json").read_bytes()
    previous_pointer = pointer.read_bytes()
    monkeypatch.setattr(
        uncertainty,
        "_verify_phase7_inputs",
        lambda _root: (_fixture_paths(), _publication_lineage()),
    )
    monkeypatch.setattr(uncertainty, "_assert_ignored", lambda _root: None)

    def fail_verification(_stage: Path) -> dict[str, dict[str, Any]]:
        raise uncertainty.UncertaintyIntegrityError("fixture publication failure")

    monkeypatch.setattr(uncertainty, "_verify_staged_outputs", fail_verification)
    with pytest.raises(uncertainty.UncertaintyIntegrityError, match="publication failure"):
        uncertainty.run_uncertainty(root, run_id="failed-run")
    assert (previous / "manifest.json").read_bytes() == previous_manifest
    assert pointer.read_bytes() == previous_pointer
    assert not (output / "failed-run").exists()
    assert not list(output.glob(".stage-failed-run-*"))


def test_holdout_manifest_path_is_rejected_before_any_candidate_output_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    selection_root = root / "data/processed/model_selection"
    selection_root.mkdir(parents=True)
    names = list(uncertainty.INPUT_OUTPUTS)
    outputs: dict[str, dict[str, Any]] = {}
    for name in names:
        path = selection_root / name
        if name.endswith(".parquet"):
            pd.DataFrame({"Date": [pd.Timestamp("2015-06-01")]}).to_parquet(
                path, engine="pyarrow", index=False
            )
        else:
            path.write_bytes(name.encode("utf-8"))
        outputs[name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "rows": 1 if name.endswith(".parquet") else None,
        }
    selected_names = {
        "development_residual_paths.parquet",
        "selected_development_forecasts.parquet",
        "selected_model_config.json",
        "refit_recipe.json",
    }
    selected = {name: outputs[name] for name in selected_names}
    selection_manifest = {
        "command": "rossmann-model-selection",
        "status": "selected",
        "publication_state": "complete",
        "input_integrity_status": "passed",
        "record_integrity_status": "passed",
        "selected_candidate_id": uncertainty.SELECTED_CANDIDATE_ID,
        "selection_run_id": uncertainty.MODEL_SELECTION_RUN_ID,
        "final_holdout_forecast_or_evaluation": False,
        "final_holdout_outcomes_read_or_hashed": False,
        "phase_8_started": False,
        "outputs": outputs,
        "selected_model_artifacts": selected,
    }
    (selection_root / "manifest.json").write_text(json.dumps(selection_manifest), encoding="utf-8")

    sentinel = root / "data/raw/rossmann/train.csv"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("protected data sentinel", encoding="utf-8")
    candidate_manifest = root / "data/processed/seasonal_naive/manifest.json"
    candidate_manifest.parent.mkdir(parents=True)
    candidate_manifest.write_text(
        json.dumps(
            {"outputs": {sentinel.relative_to(root).as_posix(): {"sha256": "0" * 64, "rows": 1}}}
        ),
        encoding="utf-8",
    )
    original_hash = uncertainty.sha256_file

    def guard_hash(path: Path) -> str:
        if Path(path).resolve() == sentinel.resolve():
            raise AssertionError("protected source path was hashed")
        return original_hash(path)

    monkeypatch.setattr(uncertainty, "sha256_file", guard_hash)
    monkeypatch.setattr(
        uncertainty,
        "verify_candidate_manifests",
        lambda _root: pytest.fail("candidate artifact hashing must not run for an unreviewed path"),
    )
    with pytest.raises(uncertainty.UncertaintyIntegrityError, match="unreviewed artifact path"):
        uncertainty._verify_phase7_inputs(root)
    assert sentinel.read_text(encoding="utf-8") == "protected data sentinel"
