"""Synthetic tests for fixture-only scenario-evaluation population alignment."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import rossmann_forecasting.forecasting.holt_winters as holt_winters
import rossmann_forecasting.forecasting.model_selection as model_selection
import rossmann_forecasting.forecasting.scenario_evaluation as scenario_evaluation
from rossmann_forecasting.forecasting.model_selection import (
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    EvidenceReviewRequired,
)
from rossmann_forecasting.forecasting.scenario_evaluation import (
    SCENARIO_POPULATION_COLUMNS,
    build_scenario_population,
)
from rossmann_forecasting.forecasting.validation import APPROVED_DEVELOPMENT_WINDOWS


def _records() -> dict[str, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    observed_targets = (
        (1, 1, 100.0, 1.0),
        (1, 5, 0.0, 1.0),
        (2, 3, 80.0, 0.0),
        (2, 14, 90.0, None),
        (3, 2, None, 1.0),
        (3, 8, 60.0, 1.0),
    )
    for window in APPROVED_DEVELOPMENT_WINDOWS:
        for store, horizon, actual, source_open in observed_targets:
            rows.append(
                {
                    "Store": store,
                    "forecast_origin": window.forecast_origin,
                    "Date": window.forecast_origin + pd.Timedelta(days=horizon),
                    "horizon": horizon,
                    "validation_window": window.name,
                    "actual_sales": actual,
                    "source_open": source_open,
                    "operational_forecast": 50_000.0 + store + horizon,
                    "model_forecast_unclipped": 60_000.0 + store + horizon,
                    "unavailable_reason": None,
                }
            )

    combined = pd.DataFrame(rows)
    records: dict[str, pd.DataFrame] = {}
    for candidate_index, candidate_id in enumerate(CANDIDATE_IDS):
        frame = combined.copy(deep=True)
        raw_column = FORECAST_COLUMNS[candidate_id]
        frame[raw_column] = [
            1_000.0 * (candidate_index + 1) + row.Store * 10 + row.horizon
            for row in frame.itertuples(index=False)
        ]
        frame["forecast_available"] = True
        frame["primary_evaluation_eligible"] = (
            frame["source_open"].eq(1) & frame["actual_sales"].notna()
        )
        records[candidate_id] = frame.loc[
            :,
            [
                "Store",
                "forecast_origin",
                "Date",
                "horizon",
                "validation_window",
                "actual_sales",
                "source_open",
                raw_column,
                "forecast_available",
                "primary_evaluation_eligible",
                "operational_forecast",
                "model_forecast_unclipped",
                "unavailable_reason",
            ],
        ].copy(deep=True)
    return records


def _row_index(
    population: pd.DataFrame,
    *,
    origin: pd.Timestamp,
    store: int,
    horizon: int,
) -> int:
    matches = population.index[
        population["forecast_origin"].eq(origin)
        & population["Store"].eq(store)
        & population["horizon"].eq(horizon)
    ]
    assert len(matches) == 1
    return int(matches[0])


def test_exact_candidate_ids_and_three_approved_windows_are_required() -> None:
    records = _records()
    population = build_scenario_population(records)

    assert population["validation_window"].drop_duplicates().tolist() == [
        window.name for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    with pytest.raises(EvidenceReviewRequired, match="Candidate IDs"):
        build_scenario_population(
            {key: value for key, value in records.items() if key != CANDIDATE_IDS[0]}
        )
    with pytest.raises(EvidenceReviewRequired, match="Candidate IDs"):
        build_scenario_population({**records, "unexpected": records[CANDIDATE_IDS[0]]})
    wrong_id = dict(records)
    wrong_id["unexpected_candidate"] = wrong_id.pop(CANDIDATE_IDS[0])
    with pytest.raises(EvidenceReviewRequired, match="Candidate IDs"):
        build_scenario_population(wrong_id)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("horizon", 0),
        ("horizon", 2),
        ("Date", pd.Timestamp("2015-07-04")),
        ("forecast_origin", pd.Timestamp("2015-05-23")),
        ("validation_window", "unapproved_window"),
    ],
)
def test_temporal_contract_is_delegated_to_phase7_validator(field: str, value: object) -> None:
    records = _records()
    records[CANDIDATE_IDS[0]].loc[0, field] = value

    with pytest.raises(EvidenceReviewRequired):
        build_scenario_population(records)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra"])
def test_candidate_target_keys_must_match_exactly(mutation: str) -> None:
    records = _records()
    candidate_id = CANDIDATE_IDS[1]
    frame = records[candidate_id]
    if mutation == "duplicate":
        records[candidate_id] = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif mutation == "missing":
        records[candidate_id] = frame.iloc[1:].copy()
    else:
        extra = frame.iloc[[0]].copy()
        extra["Store"] = 999
        records[candidate_id] = pd.concat([frame, extra], ignore_index=True)

    with pytest.raises(EvidenceReviewRequired, match="key|population|unique"):
        build_scenario_population(records)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("actual_sales", 12345.0),
        ("source_open", 0.0),
        ("horizon", 4),
        ("validation_window", "validation_2"),
    ],
)
def test_candidate_shared_labels_and_window_metadata_must_agree(field: str, value: object) -> None:
    records = _records()
    records[CANDIDATE_IDS[2]].loc[0, field] = value

    with pytest.raises(EvidenceReviewRequired):
        build_scenario_population(records)


def test_unavailable_raw_forecast_preserves_row_reason_and_other_standalone_masks() -> None:
    records = _records()
    candidate_id = CANDIDATE_IDS[1]
    raw_column = FORECAST_COLUMNS[candidate_id]
    records[candidate_id].loc[0, raw_column] = np.nan
    records[candidate_id].loc[0, "forecast_available"] = False
    records[candidate_id].loc[0, "primary_evaluation_eligible"] = False
    records[candidate_id].loc[0, "unavailable_reason"] = "fixture_fit_failure"

    population = build_scenario_population(records)
    row = _row_index(
        population,
        origin=APPROVED_DEVELOPMENT_WINDOWS[0].forecast_origin,
        store=1,
        horizon=1,
    )

    assert len(population) == 18
    assert pd.isna(population.loc[row, raw_column])
    assert not population.loc[row, f"{candidate_id}_forecast_available"]
    assert population.loc[row, f"{candidate_id}_forecast_unavailable_reason"] == (
        "fixture_fit_failure"
    )
    assert population.loc[row, "label_eligible"]
    assert population.loc[row, "seasonal_naive_standalone_eligible"]
    assert not population.loc[row, "holt_winters_additive_weekly_standalone_eligible"]
    assert population.loc[row, "global_lightgbm_gbdt_regression_l1_standalone_eligible"]
    assert not population.loc[row, "three_way_common_eligible"]


def test_standalone_mask_disagreement_with_phase7_record_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = model_selection.validate_candidate_records(_records())
    candidate_id = CANDIDATE_IDS[0]
    normalized[candidate_id].loc[0, "primary_evaluation_eligible"] = False
    monkeypatch.setattr(
        scenario_evaluation,
        "validate_candidate_records",
        lambda records_by_candidate: normalized,
    )

    with pytest.raises(EvidenceReviewRequired, match="disagrees with Phase 7 validation"):
        build_scenario_population(_records())


def test_label_only_and_standalone_masks_handle_open_zero_unknown_and_missing_sales() -> None:
    population = build_scenario_population(_records())
    origin = APPROVED_DEVELOPMENT_WINDOWS[0].forecast_origin
    open_positive = _row_index(population, origin=origin, store=1, horizon=1)
    open_zero = _row_index(population, origin=origin, store=1, horizon=5)
    closed = _row_index(population, origin=origin, store=2, horizon=3)
    unknown_open = _row_index(population, origin=origin, store=2, horizon=14)
    missing_sales = _row_index(population, origin=origin, store=3, horizon=2)

    assert population.loc[open_positive, "actual_sales"] == 100.0
    assert population.loc[open_positive, "label_eligible"]
    assert population.loc[open_zero, "actual_sales"] == 0.0
    assert population.loc[open_zero, "label_eligible"]
    assert population.loc[closed, "source_open"] == 0.0
    assert not population.loc[closed, "label_eligible"]
    assert pd.isna(population.loc[unknown_open, "source_open"])
    assert not population.loc[unknown_open, "label_eligible"]
    assert population.loc[missing_sales, "source_open"] == 1.0
    assert pd.isna(population.loc[missing_sales, "actual_sales"])
    assert not population.loc[missing_sales, "label_eligible"]

    assert (
        population.loc[open_zero, "seasonal_naive_standalone_eligible"]
        and population.loc[open_zero, "three_way_common_eligible"]
    )
    for row in (closed, unknown_open, missing_sales):
        assert not population.loc[row, "seasonal_naive_standalone_eligible"]
        assert not population.loc[row, "three_way_common_eligible"]


def test_output_uses_only_accepted_candidate_raw_forecasts_and_stable_schema() -> None:
    records = _records()
    population = build_scenario_population(records)

    assert tuple(population.columns) == SCENARIO_POPULATION_COLUMNS
    assert tuple(population.columns) == (
        "Store",
        "forecast_origin",
        "Date",
        "horizon",
        "validation_window",
        "actual_sales",
        "source_open",
        "label_eligible",
        "raw_baseline_forecast",
        "raw_statistical_forecast",
        "raw_lightgbm_forecast",
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
    for candidate_id in CANDIDATE_IDS:
        raw_column = FORECAST_COLUMNS[candidate_id]
        assert population[raw_column].min() < 50_000.0
        assert population[raw_column].max() < 60_000.0
        expected = records[candidate_id].set_index(["Store", "forecast_origin", "Date"])[raw_column]
        actual = population.set_index(["Store", "forecast_origin", "Date"])[raw_column]
        pd.testing.assert_series_equal(actual, expected.sort_index(), check_names=False)


def test_input_order_and_candidate_dictionary_order_do_not_change_output() -> None:
    records = _records()
    expected = build_scenario_population(records)
    shuffled = {
        candidate_id: frame.sample(frac=1, random_state=index + 10).reset_index(drop=True)
        for index, (candidate_id, frame) in enumerate(reversed(list(records.items())))
    }

    pd.testing.assert_frame_equal(build_scenario_population(shuffled), expected)
    pd.testing.assert_frame_equal(build_scenario_population(records), expected)


def test_builder_does_not_mutate_caller_frames() -> None:
    records = _records()
    snapshots = {candidate: frame.copy(deep=True) for candidate, frame in records.items()}

    build_scenario_population(records)

    for candidate in CANDIDATE_IDS:
        pd.testing.assert_frame_equal(records[candidate], snapshots[candidate])


def test_sparse_observed_target_population_is_preserved_without_grid_completion() -> None:
    records = _records()
    population = build_scenario_population(records)
    expected_keys = (
        records[CANDIDATE_IDS[0]][["Store", "forecast_origin", "Date"]]
        .sort_values(["Store", "forecast_origin", "Date"])
        .reset_index(drop=True)
    )
    actual_keys = population[["Store", "forecast_origin", "Date"]]

    pd.testing.assert_frame_equal(actual_keys, expected_keys)
    assert len(population) == 18
    assert len(population) < len(APPROVED_DEVELOPMENT_WINDOWS) * 3 * 14


def test_builder_has_no_file_hash_or_publication_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("fixture-only population builder attempted an external side effect")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(pd, "read_csv", forbidden)
    monkeypatch.setattr(pd, "read_parquet", forbidden)
    monkeypatch.setattr(pd.DataFrame, "to_csv", forbidden)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", forbidden)
    monkeypatch.setattr(model_selection, "sha256_file", forbidden)
    monkeypatch.setattr(model_selection, "_canonical_sha256", forbidden)
    monkeypatch.setattr(model_selection.lgb, "train", forbidden)
    monkeypatch.setattr(holt_winters.ExponentialSmoothing, "fit", forbidden)
    monkeypatch.setattr(model_selection, "_write_json", forbidden)
    monkeypatch.setattr(model_selection, "_write_json_atomically", forbidden)

    assert len(build_scenario_population(_records())) == 18
