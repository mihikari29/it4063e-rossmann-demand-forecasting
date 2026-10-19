"""Synthetic tests for fixture-only scenario-evaluation population alignment."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import rossmann_forecasting.forecasting.holt_winters as holt_winters
import rossmann_forecasting.forecasting.model_selection as model_selection
import rossmann_forecasting.forecasting.scenario_evaluation as scenario_evaluation
from rossmann_forecasting.forecasting.metrics import summarize_forecast_metrics
from rossmann_forecasting.forecasting.model_selection import (
    BASE_COLUMNS,
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    EvidenceReviewRequired,
)
from rossmann_forecasting.forecasting.scenario_evaluation import (
    SCENARIO_POPULATION_COLUMNS,
    ScenarioEvaluationResult,
    build_scenario_population,
    serialize_scenario_fixture,
    summarize_scenario_population,
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


def _primary_fixture_rows() -> list[dict[str, object]]:
    return [
        {
            "Store": 1,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 1,
            "actual_sales": 10.0,
            "source_open": 1.0,
            "seasonal_naive": 8.0,
            "holt_winters_additive_weekly": 12.0,
            "global_lightgbm_gbdt_regression_l1": 9.0,
        },
        {
            "Store": 2,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 8,
            "actual_sales": 10.0,
            "source_open": 1.0,
            "seasonal_naive": 12.0,
            "holt_winters_additive_weekly": 8.0,
            "global_lightgbm_gbdt_regression_l1": 11.0,
        },
        {
            "Store": 3,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 14,
            "actual_sales": 0.0,
            "source_open": 1.0,
            "seasonal_naive": 0.0,
            "holt_winters_additive_weekly": 0.0,
            "global_lightgbm_gbdt_regression_l1": 0.0,
        },
        {
            "Store": 1,
            "forecast_origin": pd.Timestamp("2015-06-05"),
            "horizon": 1,
            "actual_sales": 100.0,
            "source_open": 1.0,
            "seasonal_naive": 140.0,
            "holt_winters_additive_weekly": 60.0,
            "global_lightgbm_gbdt_regression_l1": 120.0,
        },
    ]


def _population_from_rows(
    rows: list[dict[str, object]] | None = None,
    *,
    unavailable: tuple[str, int, str] | None = None,
) -> pd.DataFrame:
    fixture_rows = _primary_fixture_rows() if rows is None else rows
    shared = pd.DataFrame(
        [
            {
                "Store": row["Store"],
                "forecast_origin": row["forecast_origin"],
                "Date": row["forecast_origin"] + pd.Timedelta(days=int(row["horizon"])),
                "horizon": row["horizon"],
                "validation_window": next(
                    window.name
                    for window in APPROVED_DEVELOPMENT_WINDOWS
                    if window.forecast_origin == row["forecast_origin"]
                ),
                "actual_sales": row["actual_sales"],
                "source_open": row["source_open"],
            }
            for row in fixture_rows
        ]
    )
    records: dict[str, pd.DataFrame] = {}
    for candidate_id in CANDIDATE_IDS:
        frame = shared.copy(deep=True)
        frame[FORECAST_COLUMNS[candidate_id]] = [row[candidate_id] for row in fixture_rows]
        if unavailable is not None and unavailable[0] == candidate_id:
            frame.loc[unavailable[1], FORECAST_COLUMNS[candidate_id]] = np.nan
        frame["forecast_available"] = frame[FORECAST_COLUMNS[candidate_id]].notna()
        frame["primary_evaluation_eligible"] = (
            frame["source_open"].eq(1) & frame["actual_sales"].notna() & frame["forecast_available"]
        )
        frame["unavailable_reason"] = None
        if unavailable is not None and unavailable[0] == candidate_id:
            frame.loc[unavailable[1], "unavailable_reason"] = unavailable[2]
        records[candidate_id] = frame.loc[
            :,
            [
                *BASE_COLUMNS,
                FORECAST_COLUMNS[candidate_id],
                "forecast_available",
                "primary_evaluation_eligible",
                "unavailable_reason",
            ],
        ].copy(deep=True)
    return build_scenario_population(records)


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


def _summary_row(
    frame: pd.DataFrame,
    *,
    scope: str = "pooled",
    validation_window: str | None = None,
    dimension: str = "all",
    level_status: str = "all",
    level_value: str | None = None,
    candidate_id: str | None = None,
    reference_candidate_id: str | None = None,
) -> pd.Series:
    def equals(series: pd.Series, value: object | None) -> pd.Series:
        return series.isna() if value is None else series.eq(value)

    mask = (
        frame["scope"].eq(scope)
        & equals(frame["validation_window"], validation_window)
        & frame["dimension"].eq(dimension)
        & frame["level_status"].eq(level_status)
        & equals(frame["level_value"], level_value)
    )
    if "candidate_id" in frame:
        mask &= frame["candidate_id"].eq(candidate_id)
    if "reference_candidate_id" in frame:
        mask &= frame["reference_candidate_id"].eq(reference_candidate_id)
    matches = frame.loc[mask]
    assert len(matches) == 1
    return matches.iloc[0]


def _membership(population: pd.DataFrame) -> pd.DataFrame:
    values = {
        (1, pd.Timestamp("2015-05-22")): {
            "Promo": 0,
            "StoreType": "a",
            "Assortment": "a",
            "StateHoliday": "0",
            "SchoolHoliday": 0,
        },
        (1, pd.Timestamp("2015-06-05")): {
            "Promo": True,
            "StoreType": "a",
            "Assortment": "a",
            "StateHoliday": "x",
            "SchoolHoliday": 1,
        },
        (2, pd.Timestamp("2015-05-22")): {
            "Promo": 1,
            "StoreType": "b",
            "Assortment": "b",
            "StateHoliday": "a",
            "SchoolHoliday": 1,
        },
        (3, pd.Timestamp("2015-05-22")): {
            "Promo": None,
            "StoreType": "a",
            "Assortment": "a",
            "StateHoliday": None,
            "SchoolHoliday": 0,
        },
    }
    membership = population.loc[:, ["Store", "forecast_origin", "Date"]].copy(deep=True)
    for column in ("Promo", "StoreType", "Assortment", "StateHoliday", "SchoolHoliday"):
        membership[column] = [
            values[(int(row.Store), pd.Timestamp(row.forecast_origin))][column]
            for row in membership.itertuples(index=False)
        ]
    return membership


def _replace_metadata_identity(
    result: ScenarioEvaluationResult,
    *,
    dimension: str,
    old_status: str,
    old_value: str | None,
    new_status: str,
    new_value: str | None,
) -> ScenarioEvaluationResult:
    updated_tables: dict[str, pd.DataFrame] = {}
    support_matches = 0
    for table_name in ("support", "coverage", "metrics", "comparisons", "unavailability"):
        frame = getattr(result, table_name).copy(deep=True)
        value_matches = (
            frame["level_value"].isna() if old_value is None else frame["level_value"].eq(old_value)
        )
        mask = (
            frame["dimension"].eq(dimension) & frame["level_status"].eq(old_status) & value_matches
        )
        if table_name == "support":
            support_matches = int(mask.sum())
        frame["level_status"] = frame["level_status"].astype(object)
        frame["level_value"] = frame["level_value"].astype(object)
        frame.loc[mask, "level_status"] = new_status
        frame.loc[mask, "level_value"] = new_value
        updated_tables[table_name] = frame
    assert support_matches > 0
    return replace(result, **updated_tables)


def test_scenario_metrics_use_one_common_population_and_pool_sufficient_statistics() -> None:
    population = _population_from_rows()
    result = summarize_scenario_population(population)

    assert len(population) == 4
    assert len(population) < len(APPROVED_DEVELOPMENT_WINDOWS) * 14
    assert len(result.support) == 96
    pooled_support = _summary_row(result.support)
    assert pooled_support["observed_target_rows"] == 4
    assert pooled_support["open_label_rows"] == 4
    assert pooled_support["three_way_common_rows"] == 4
    assert result.metrics["population"].eq("three_way_common").all()

    expected = {
        CANDIDATE_IDS[0]: {
            "sum_absolute_error": 44.0,
            "sum_squared_error": 1608.0,
            "sum_signed_error": 40.0,
            "underforecast_sum": 2.0,
            "overforecast_sum": 42.0,
            "underforecast_count": 1,
            "overforecast_count": 2,
            "exact_match_count": 1,
            "mae": 11.0,
            "wape": 44.0 / 120.0,
            "mean_signed_error": 10.0,
        },
        CANDIDATE_IDS[1]: {
            "sum_absolute_error": 44.0,
            "sum_squared_error": 1608.0,
            "sum_signed_error": -40.0,
            "underforecast_sum": 42.0,
            "overforecast_sum": 2.0,
            "underforecast_count": 2,
            "overforecast_count": 1,
            "exact_match_count": 1,
            "mae": 11.0,
            "wape": 44.0 / 120.0,
            "mean_signed_error": -10.0,
        },
        CANDIDATE_IDS[2]: {
            "sum_absolute_error": 22.0,
            "sum_squared_error": 402.0,
            "sum_signed_error": 20.0,
            "underforecast_sum": 1.0,
            "overforecast_sum": 21.0,
            "underforecast_count": 1,
            "overforecast_count": 2,
            "exact_match_count": 1,
            "mae": 5.5,
            "wape": 22.0 / 120.0,
            "mean_signed_error": 5.0,
        },
    }
    for candidate_id, expected_values in expected.items():
        row = _summary_row(result.metrics, candidate_id=candidate_id)
        assert row["n"] == 4
        assert row["sum_actual"] == 120.0
        assert row["rmse"] == pytest.approx(
            np.sqrt(expected_values["sum_squared_error"] / 4), rel=1e-12, abs=1e-10
        )
        for name, value in expected_values.items():
            assert row[name] == pytest.approx(value, rel=1e-12, abs=1e-10)
        assert row["underforecast_contribution"] + row[
            "overforecast_contribution"
        ] == pytest.approx(row["mae"])
        assert (
            row["underforecast_count"] + row["overforecast_count"] + row["exact_match_count"]
            == row["n"]
        )

    lightgbm_sn = _summary_row(
        result.comparisons,
        candidate_id=CANDIDATE_IDS[2],
        reference_candidate_id=CANDIDATE_IDS[0],
    )
    lightgbm_hw = _summary_row(
        result.comparisons,
        candidate_id=CANDIDATE_IDS[2],
        reference_candidate_id=CANDIDATE_IDS[1],
    )
    hw_sn = _summary_row(
        result.comparisons,
        candidate_id=CANDIDATE_IDS[1],
        reference_candidate_id=CANDIDATE_IDS[0],
    )
    assert lightgbm_sn["relative_mae_improvement_pct"] == 50.0
    assert lightgbm_hw["relative_mae_improvement_pct"] == 50.0
    assert lightgbm_sn["absolute_mae_difference"] == -5.5
    assert hw_sn["absolute_mae_difference"] == 0.0
    assert hw_sn["relative_mae_improvement_pct"] == 0.0

    first_origin = _summary_row(
        result.metrics,
        scope="origin",
        validation_window="validation_1",
        candidate_id=CANDIDATE_IDS[0],
    )
    second_origin = _summary_row(
        result.metrics,
        scope="origin",
        validation_window="validation_2",
        candidate_id=CANDIDATE_IDS[0],
    )
    third_origin = _summary_row(
        result.metrics,
        scope="origin",
        validation_window="validation_3",
        candidate_id=CANDIDATE_IDS[0],
    )
    assert (
        first_origin["n"],
        first_origin["sum_absolute_error"],
        first_origin["sum_squared_error"],
    ) == (
        3,
        4.0,
        8.0,
    )
    assert (
        second_origin["n"],
        second_origin["sum_absolute_error"],
        second_origin["sum_squared_error"],
    ) == (
        1,
        40.0,
        1600.0,
    )
    assert third_origin["n"] == 0
    assert third_origin["mae"] is None or pd.isna(third_origin["mae"])


def test_l2_reconciles_to_phase7_metrics_on_the_same_common_rows() -> None:
    population = _population_from_rows()
    result = summarize_scenario_population(population)
    common = population.loc[population["three_way_common_eligible"]].copy()

    for candidate_id in CANDIDATE_IDS:
        source = common.loc[
            :,
            [
                "actual_sales",
                "source_open",
                FORECAST_COLUMNS[candidate_id],
                "horizon",
                "validation_window",
            ],
        ].rename(columns={FORECAST_COLUMNS[candidate_id]: "raw_baseline_forecast"})
        source["forecast_available"] = True
        source["primary_evaluation_eligible"] = True
        phase7 = summarize_forecast_metrics(source, scope="fixture")
        l2 = _summary_row(result.metrics, candidate_id=candidate_id)
        assert l2["mae"] == phase7["mae"]
        assert l2["rmse"] == pytest.approx(phase7["rmse"], rel=1e-12, abs=1e-10)
        assert l2["wape"] == pytest.approx(phase7["wape"], rel=1e-12, abs=1e-10)


def test_large_directional_cancellation_reconciles_and_serializes_signed_sum() -> None:
    origin = pd.Timestamp("2015-05-22")
    errors = [10_000.0, -10_000.0] * 500 + [10000.1 - 10_000.0]
    rows = []
    for store, error in enumerate(errors, start=1):
        prediction = 10_000.0 + error
        rows.append(
            {
                "Store": store,
                "forecast_origin": origin,
                "horizon": 1,
                "actual_sales": 10_000.0,
                "source_open": 1.0,
                **dict.fromkeys(CANDIDATE_IDS, prediction),
            }
        )

    result = summarize_scenario_population(_population_from_rows(rows))
    expected_signed_sum = math.fsum(errors)
    expected_under_sum = math.fsum(-error for error in errors if error < 0.0)
    expected_over_sum = math.fsum(error for error in errors if error > 0.0)
    for candidate_id in CANDIDATE_IDS:
        metric = _summary_row(result.metrics, candidate_id=candidate_id)
        assert metric["sum_signed_error"] == expected_signed_sum
        assert metric["underforecast_sum"] == expected_under_sum
        assert metric["overforecast_sum"] == expected_over_sum

    payload = json.loads(serialize_scenario_fixture(result))
    serialized_metric = next(
        row
        for row in payload["tables"]["metrics"]
        if row["scope"] == "pooled"
        and row["dimension"] == "all"
        and row["candidate_id"] == CANDIDATE_IDS[0]
    )
    assert serialized_metric["sum_signed_error"] == expected_signed_sum

    corrupted_metrics = result.metrics.copy(deep=True)
    mask = (
        corrupted_metrics["scope"].eq("pooled")
        & corrupted_metrics["dimension"].eq("all")
        & corrupted_metrics["candidate_id"].eq(CANDIDATE_IDS[0])
    )
    corrupted_metrics.loc[mask, "sum_signed_error"] += 0.01
    with pytest.raises(ValueError, match="signed error totals"):
        serialize_scenario_fixture(replace(result, metrics=corrupted_metrics))


def test_serializer_requires_shared_actual_denominator_in_every_stratum() -> None:
    population = _population_from_rows()
    result = summarize_scenario_population(
        population,
        scenario_membership=_membership(population),
    )
    assert serialize_scenario_fixture(result)

    corrupted_metrics = result.metrics.copy(deep=True)
    mask = (
        corrupted_metrics["scope"].eq("origin")
        & corrupted_metrics["validation_window"].eq("validation_1")
        & corrupted_metrics["dimension"].eq("Promo")
        & corrupted_metrics["level_status"].eq("known")
        & corrupted_metrics["level_value"].eq("0")
        & corrupted_metrics["candidate_id"].eq(CANDIDATE_IDS[0])
    )
    assert int(mask.sum()) == 1
    index = corrupted_metrics.index[mask][0]
    denominator = float(corrupted_metrics.loc[index, "sum_actual"]) * 2.0
    corrupted_metrics.loc[index, "sum_actual"] = denominator
    corrupted_metrics.loc[index, "wape"] = (
        corrupted_metrics.loc[index, "sum_absolute_error"] / denominator
    )
    corrupted_metrics.loc[index, "normalized_underforecast_exposure"] = (
        corrupted_metrics.loc[index, "underforecast_sum"] / denominator
    )
    corrupted_metrics.loc[index, "normalized_overforecast_exposure"] = (
        corrupted_metrics.loc[index, "overforecast_sum"] / denominator
    )
    with pytest.raises(ValueError, match="share one common-population actual Sales denominator"):
        serialize_scenario_fixture(replace(result, metrics=corrupted_metrics))


def test_unavailable_candidate_is_excluded_from_exact_common_population_with_original_reason() -> (
    None
):
    candidate_id = CANDIDATE_IDS[1]
    population = _population_from_rows(unavailable=(candidate_id, 0, "fixture_fit_failure"))
    result = summarize_scenario_population(population)
    assert serialize_scenario_fixture(result)
    support = _summary_row(result.support)
    assert support["open_label_rows"] == 4
    assert support["three_way_common_rows"] == 3
    coverage = _summary_row(result.coverage, candidate_id=candidate_id)
    assert coverage["forecast_available_rows"] == 3
    assert coverage["forecast_unavailable_rows"] == 1
    assert coverage["standalone_eligible_rows"] == 3
    assert coverage["label_eligible_unavailable_rows"] == 1
    assert coverage["standalone_excluded_from_common_rows"] == 0
    for other_candidate in (CANDIDATE_IDS[0], CANDIDATE_IDS[2]):
        peer_coverage = _summary_row(result.coverage, candidate_id=other_candidate)
        assert peer_coverage["standalone_excluded_from_common_rows"] == 1
    reason_rows = result.unavailability.loc[
        result.unavailability["scope"].eq("pooled")
        & result.unavailability["dimension"].eq("all")
        & result.unavailability["candidate_id"].eq(candidate_id)
    ]
    assert reason_rows[
        ["unavailable_reason", "observed_unavailable_rows", "open_label_unavailable_rows"]
    ].to_dict(orient="records") == [
        {
            "unavailable_reason": "fixture_fit_failure",
            "observed_unavailable_rows": 1,
            "open_label_unavailable_rows": 1,
        }
    ]
    assert result.unavailability.loc[
        result.unavailability["scope"].eq("pooled") & result.unavailability["dimension"].eq("all"),
        "candidate_id",
    ].tolist() == [candidate_id]
    assert (
        result.metrics.loc[
            result.metrics["scope"].eq("pooled") & result.metrics["dimension"].eq("all"), "n"
        ]
        .eq(3)
        .all()
    )


def test_zero_sales_row_remains_eligible_and_zero_denominators_stay_null() -> None:
    row = _primary_fixture_rows()[2]
    row["global_lightgbm_gbdt_regression_l1"] = 1.0
    population = _population_from_rows([row])
    result = summarize_scenario_population(population)
    assert serialize_scenario_fixture(result)
    for candidate_id in CANDIDATE_IDS:
        metric = _summary_row(result.metrics, candidate_id=candidate_id)
        expected_error = 1.0 if candidate_id == CANDIDATE_IDS[2] else 0.0
        assert metric["n"] == 1
        assert metric["sum_actual"] == 0.0
        assert metric["mae"] == expected_error
        assert metric["rmse"] == expected_error
        assert metric["wape"] is None or pd.isna(metric["wape"])
        assert metric["sales_ratio_unavailable_reason"] == "zero_actual_sum"
        assert metric["normalized_underforecast_exposure"] is None or pd.isna(
            metric["normalized_underforecast_exposure"]
        )
    for candidate_id, reference_id in ((CANDIDATE_IDS[2], CANDIDATE_IDS[0]),):
        comparison = _summary_row(
            result.comparisons,
            candidate_id=candidate_id,
            reference_candidate_id=reference_id,
        )
        assert comparison["absolute_mae_difference"] == 1.0
        assert comparison["relative_mae_improvement_pct"] is None or pd.isna(
            comparison["relative_mae_improvement_pct"]
        )
        assert comparison["relative_improvement_unavailable_reason"] == "zero_reference_mae"


def test_support_accounts_for_missing_sales_closed_and_unknown_open_without_grid_fill() -> None:
    rows = [
        {
            "Store": 1,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 1,
            "actual_sales": None,
            "source_open": 1.0,
            "seasonal_naive": 5.0,
            "holt_winters_additive_weekly": 5.0,
            "global_lightgbm_gbdt_regression_l1": 5.0,
        },
        {
            "Store": 2,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 2,
            "actual_sales": None,
            "source_open": 0.0,
            "seasonal_naive": 10.0,
            "holt_winters_additive_weekly": 10.0,
            "global_lightgbm_gbdt_regression_l1": 10.0,
        },
        {
            "Store": 3,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 3,
            "actual_sales": None,
            "source_open": None,
            "seasonal_naive": 0.0,
            "holt_winters_additive_weekly": 0.0,
            "global_lightgbm_gbdt_regression_l1": 0.0,
        },
        {
            "Store": 4,
            "forecast_origin": pd.Timestamp("2015-05-22"),
            "horizon": 4,
            "actual_sales": 0.0,
            "source_open": 1.0,
            "seasonal_naive": 0.0,
            "holt_winters_additive_weekly": 0.0,
            "global_lightgbm_gbdt_regression_l1": 0.0,
        },
    ]
    population = _population_from_rows(rows)
    result = summarize_scenario_population(population)
    support = _summary_row(result.support)
    assert len(population) == 4
    assert support["observed_target_rows"] == 4
    assert support["closed_rows"] == 1
    assert support["unknown_open_rows"] == 1
    assert support["open_missing_actual_rows"] == 1
    assert support["open_label_rows"] == 1
    assert support["missing_actual_rows"] == 3
    assert support["three_way_common_rows"] == 1
    assert (
        support["closed_rows"]
        + support["unknown_open_rows"]
        + support["open_missing_actual_rows"]
        + support["open_label_rows"]
        == support["observed_target_rows"]
    )
    assert serialize_scenario_fixture(result)


def test_membership_reports_known_missing_and_unrecognized_levels_per_origin() -> None:
    population = _population_from_rows()
    membership = _membership(population)
    result = summarize_scenario_population(population, scenario_membership=membership)
    assert serialize_scenario_fixture(result)

    assert result.enabled_scenarios == (
        "Promo",
        "StoreType",
        "Assortment",
        "StateHoliday",
        "SchoolHoliday",
    )
    assert len(result.support) == 180
    pooled_known = _summary_row(
        result.support,
        dimension="Promo",
        level_status="known",
        level_value="0",
    )
    assert pooled_known["observed_target_rows"] == 1
    pooled_missing = _summary_row(
        result.support,
        dimension="Promo",
        level_status="missing",
    )
    assert pooled_missing["observed_target_rows"] == 1
    pooled_unknown = _summary_row(
        result.support,
        dimension="StateHoliday",
        level_status="unrecognized",
        level_value="x",
    )
    assert pooled_unknown["observed_target_rows"] == 1
    declared_empty = _summary_row(
        result.support,
        dimension="StoreType",
        level_status="known",
        level_value="d",
    )
    assert declared_empty["observed_target_rows"] == 0
    assert declared_empty["empty_observed"]
    assert len(result.support.loc[result.support["dimension"].eq("Promo")]) == 12
    assert len(result.support.loc[result.support["scope"].eq("origin")]) == 135


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra"])
def test_membership_requires_exact_unique_observed_keys(mutation: str) -> None:
    population = _population_from_rows()
    membership = _membership(population)
    if mutation == "duplicate":
        membership = pd.concat([membership, membership.iloc[[0]]], ignore_index=True)
    elif mutation == "missing":
        membership = membership.iloc[1:].copy()
    else:
        membership = membership.copy()
        membership.loc[0, "Store"] = 999

    with pytest.raises(EvidenceReviewRequired, match="unique|exactly match"):
        summarize_scenario_population(population, scenario_membership=membership)


@pytest.mark.parametrize("bad_value", [2, 2.0, "01", " 1", "yes"])
def test_membership_rejects_invalid_binary_codes(bad_value: object) -> None:
    population = _population_from_rows()
    membership = _membership(population)
    membership.loc[0, "Promo"] = bad_value
    with pytest.raises(EvidenceReviewRequired, match="Promo metadata"):
        summarize_scenario_population(population, scenario_membership=membership)


@pytest.mark.parametrize("column", ["StoreType", "Assortment"])
def test_static_metadata_must_be_consistent_per_store(column: str) -> None:
    population = _population_from_rows()
    membership = _membership(population)
    membership.loc[1, column] = "c"
    with pytest.raises(EvidenceReviewRequired, match="static within each Store"):
        summarize_scenario_population(population, scenario_membership=membership)


def test_unrecognized_codes_on_ineligible_rows_are_still_declared() -> None:
    rows = _primary_fixture_rows()
    rows[0]["source_open"] = 0.0
    population = _population_from_rows(rows)
    membership = _membership(population)
    ineligible_row = population.index[population["Store"].eq(1)].tolist()[0]
    membership.loc[ineligible_row, "StateHoliday"] = "future-code"
    result = summarize_scenario_population(population, scenario_membership=membership)
    future = _summary_row(
        result.support,
        dimension="StateHoliday",
        level_status="unrecognized",
        level_value="future-code",
    )
    assert future["observed_target_rows"] == 1
    assert future["open_label_rows"] == 0
    assert future["no_label_eligible"]


def test_serializer_rejects_malformed_metadata_level_identities() -> None:
    population = _population_from_rows()
    membership = _membership(population)
    membership["StoreType"] = membership["StoreType"].astype(object)
    membership.loc[membership["Store"].eq(1), "StoreType"] = "future-store-type"
    result = summarize_scenario_population(population, scenario_membership=membership)
    assert serialize_scenario_fixture(result)

    malformed_identities = (
        ("StateHoliday", "x", "0"),
        ("StoreType", "future-store-type", "a"),
        ("StateHoliday", "x", None),
        ("StateHoliday", "x", ""),
    )
    for dimension, old_value, new_value in malformed_identities:
        malformed = _replace_metadata_identity(
            result,
            dimension=dimension,
            old_status="unrecognized",
            old_value=old_value,
            new_status="unrecognized",
            new_value=new_value,
        )
        with pytest.raises(ValueError, match="metadata level identity"):
            serialize_scenario_fixture(malformed)


def test_serializer_rejects_known_metadata_level_outside_fixed_domain() -> None:
    population = _population_from_rows()
    result = summarize_scenario_population(population, scenario_membership=_membership(population))
    malformed = _replace_metadata_identity(
        result,
        dimension="StoreType",
        old_status="known",
        old_value="a",
        new_status="known",
        new_value="z",
    )
    with pytest.raises(ValueError, match="metadata level identity"):
        serialize_scenario_fixture(malformed)


def test_serializer_rejects_missing_sales_count_outside_eligible_population() -> None:
    population = _population_from_rows([_primary_fixture_rows()[0]])
    result = summarize_scenario_population(population)
    assert serialize_scenario_fixture(result)

    support = result.support.copy(deep=True)
    mask = support["scope"].eq("pooled") & support["dimension"].eq("all")
    assert int(mask.sum()) == 1
    assert support.loc[mask, "observed_target_rows"].iloc[0] == 1
    assert support.loc[mask, "open_label_rows"].iloc[0] == 1
    support.loc[mask, "missing_actual_rows"] = 1
    with pytest.raises(ValueError, match="support counts are not nested consistently"):
        serialize_scenario_fixture(replace(result, support=support))


def test_serializer_rejects_reason_label_count_above_reason_total() -> None:
    records = _records()
    candidate_id = CANDIDATE_IDS[1]
    forecast_column = FORECAST_COLUMNS[candidate_id]
    for index, reason in (
        (0, "open_label_failure"),
        (2, "closed_failure"),
        (5, "open_label_failure"),
    ):
        records[candidate_id].loc[index, forecast_column] = np.nan
        records[candidate_id].loc[index, "forecast_available"] = False
        records[candidate_id].loc[index, "primary_evaluation_eligible"] = False
        records[candidate_id].loc[index, "unavailable_reason"] = reason

    population = build_scenario_population(records)
    result = summarize_scenario_population(population)
    assert serialize_scenario_fixture(result)

    unavailable = result.unavailability.copy(deep=True)
    group = unavailable["scope"].eq("pooled") & unavailable["dimension"].eq("all")
    closed_reason = (
        group
        & unavailable["candidate_id"].eq(candidate_id)
        & unavailable["unavailable_reason"].eq("closed_failure")
    )
    open_reason = (
        group
        & unavailable["candidate_id"].eq(candidate_id)
        & unavailable["unavailable_reason"].eq("open_label_failure")
    )
    assert unavailable.loc[closed_reason, "observed_unavailable_rows"].iloc[0] == 1
    assert unavailable.loc[open_reason, "observed_unavailable_rows"].iloc[0] == 2
    assert unavailable.loc[open_reason, "open_label_unavailable_rows"].iloc[0] == 2
    unavailable.loc[closed_reason, "open_label_unavailable_rows"] = 2
    unavailable.loc[open_reason, "open_label_unavailable_rows"] = 0
    assert unavailable.loc[group, "open_label_unavailable_rows"].sum() == 2
    with pytest.raises(
        ValueError, match="unavailability contains an empty or inconsistent reason row"
    ):
        serialize_scenario_fixture(replace(result, unavailability=unavailable))


def test_membership_rejects_duplicate_columns_and_invalid_stateholiday_types() -> None:
    population = _population_from_rows()
    membership = _membership(population)
    duplicate = membership.copy(deep=True)
    duplicate.columns = [*duplicate.columns[:-1], duplicate.columns[0]]
    with pytest.raises(EvidenceReviewRequired, match="duplicate columns"):
        summarize_scenario_population(population, scenario_membership=duplicate)

    for value in (True, 1, ""):
        invalid = _membership(population)
        invalid["StateHoliday"] = invalid["StateHoliday"].astype(object)
        invalid.loc[0, "StateHoliday"] = value
        with pytest.raises(EvidenceReviewRequired, match="StateHoliday"):
            summarize_scenario_population(population, scenario_membership=invalid)


def test_l2_adapter_rejects_extra_schema_and_availability_mismatches() -> None:
    population = _population_from_rows()
    extra = population.assign(unexpected=1)
    with pytest.raises(EvidenceReviewRequired, match="exact L1 population schema"):
        summarize_scenario_population(extra)

    duplicate = population.copy(deep=True)
    duplicate.columns = [*duplicate.columns[:-1], duplicate.columns[0]]
    with pytest.raises(EvidenceReviewRequired, match="duplicate columns"):
        summarize_scenario_population(duplicate)

    mismatch = population.copy(deep=True)
    mismatch.loc[0, "seasonal_naive_forecast_available"] = False
    with pytest.raises(EvidenceReviewRequired, match="available mask"):
        summarize_scenario_population(mismatch)


def test_input_row_column_order_and_caller_frames_do_not_change_fixture_bytes() -> None:
    population = _population_from_rows()
    membership = _membership(population)
    population_before = population.copy(deep=True)
    membership_before = membership.copy(deep=True)
    expected = serialize_scenario_fixture(
        summarize_scenario_population(population, scenario_membership=membership)
    )

    shuffled_population = population.sample(frac=1, random_state=41).reset_index(drop=True)
    shuffled_population = shuffled_population.loc[:, list(reversed(shuffled_population.columns))]
    shuffled_membership = membership.sample(frac=1, random_state=13).reset_index(drop=True)
    shuffled_membership = shuffled_membership.loc[:, list(reversed(shuffled_membership.columns))]
    actual = serialize_scenario_fixture(
        summarize_scenario_population(
            shuffled_population,
            scenario_membership=shuffled_membership,
        )
    )
    assert actual == expected
    pd.testing.assert_frame_equal(population, population_before)
    pd.testing.assert_frame_equal(membership, membership_before)


def test_binary_numeric_boolean_and_string_aliases_have_stable_serialization() -> None:
    population = _population_from_rows()
    canonical = _membership(population)
    aliases = canonical.copy(deep=True)
    aliases["Promo"] = aliases["Promo"].astype(object)
    aliases["SchoolHoliday"] = aliases["SchoolHoliday"].astype(object)
    aliases["StateHoliday"] = aliases["StateHoliday"].astype(object)
    aliases.loc[0, "Promo"] = "0"
    aliases.loc[0, "SchoolHoliday"] = "0"
    aliases.loc[0, "StateHoliday"] = 0.0

    canonical_bytes = serialize_scenario_fixture(
        summarize_scenario_population(population, scenario_membership=canonical)
    )
    aliases_bytes = serialize_scenario_fixture(
        summarize_scenario_population(population, scenario_membership=aliases)
    )
    assert aliases_bytes == canonical_bytes


def test_fixture_serializer_has_fixed_json_contract_and_rejects_invalid_payloads() -> None:
    result = summarize_scenario_population(_population_from_rows())
    serialized = serialize_scenario_fixture(result)
    payload = json.loads(serialized)
    assert serialized.endswith(b"\n")
    assert serialized.count(b"\n") == 1
    assert payload["schema_version"] == "wp1-l2-fixture-v1"
    assert payload["analysis_scope"] == "synthetic_fixture_only"
    assert payload["primary_population"] == "three_way_common"
    assert payload["candidate_order"] == list(CANDIDATE_IDS)
    assert payload["enabled_scenarios"] == []
    assert tuple(payload["tables"]) == (
        "comparisons",
        "coverage",
        "metrics",
        "support",
        "unavailability",
    )
    assert b"NaN" not in serialized and b"Infinity" not in serialized

    bad_metrics = result.metrics.copy(deep=True)
    bad_metrics.loc[0, "mae"] = np.inf
    invalid = ScenarioEvaluationResult(
        support=result.support,
        coverage=result.coverage,
        metrics=bad_metrics,
        comparisons=result.comparisons,
        unavailability=result.unavailability,
        enabled_scenarios=result.enabled_scenarios,
    )
    with pytest.raises(ValueError, match="finite numbers"):
        serialize_scenario_fixture(invalid)

    bad_columns = result.support.copy(deep=True)
    bad_columns["unexpected"] = 1
    invalid_schema = ScenarioEvaluationResult(
        support=bad_columns,
        coverage=result.coverage,
        metrics=result.metrics,
        comparisons=result.comparisons,
        unavailability=result.unavailability,
        enabled_scenarios=result.enabled_scenarios,
    )
    with pytest.raises(ValueError, match="fixed result schema"):
        serialize_scenario_fixture(invalid_schema)

    zero_result = summarize_scenario_population(_population_from_rows([_primary_fixture_rows()[2]]))
    negative_zero_metrics = zero_result.metrics.copy(deep=True)
    negative_zero_metrics.loc[0, "sum_signed_error"] = -0.0
    negative_zero_result = ScenarioEvaluationResult(
        support=zero_result.support,
        coverage=zero_result.coverage,
        metrics=negative_zero_metrics,
        comparisons=zero_result.comparisons,
        unavailability=zero_result.unavailability,
        enabled_scenarios=zero_result.enabled_scenarios,
    )
    negative_zero_bytes = serialize_scenario_fixture(negative_zero_result)
    assert b"-0.0" not in negative_zero_bytes


def test_l2_aggregation_and_serialization_have_no_external_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("fixture-only scenario summary attempted an external side effect")

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

    result = summarize_scenario_population(_population_from_rows())
    assert serialize_scenario_fixture(result).startswith(b"{")


def test_empty_population_emits_all_default_strata_with_null_metrics() -> None:
    population = _population_from_rows().iloc[:0].copy()
    result = summarize_scenario_population(population)
    assert len(result.support) == 96
    assert result.support["observed_target_rows"].eq(0).all()
    assert result.support["empty_observed"].all()
    assert result.coverage["forecast_available_rows"].eq(0).all()
    assert result.metrics["n"].eq(0).all()
    assert result.metrics["metrics_unavailable_reason"].eq("no_common_rows").all()
    assert result.comparisons["comparison_unavailable_reason"].eq("no_common_rows").all()
    assert result.unavailability.empty
    assert len(serialize_scenario_fixture(result)) > 0


def test_overflow_and_inconsistent_l1_masks_fail_closed() -> None:
    row = _primary_fixture_rows()[0]
    row["actual_sales"] = 0.0
    row["seasonal_naive"] = 1e200
    population = _population_from_rows([row])
    with pytest.raises(ArithmeticError, match="squared forecast error"):
        summarize_scenario_population(population)

    inconsistent = _population_from_rows()
    inconsistent.loc[0, "label_eligible"] = False
    with pytest.raises(EvidenceReviewRequired, match="label_eligible"):
        summarize_scenario_population(inconsistent)

    inconsistent = _population_from_rows()
    inconsistent.loc[0, "seasonal_naive_forecast_unavailable_reason"] = "spurious"
    with pytest.raises(EvidenceReviewRequired, match="disagrees"):
        summarize_scenario_population(inconsistent)
