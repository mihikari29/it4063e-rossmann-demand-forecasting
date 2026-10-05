"""Fixture-based tests for source-preserving Rossmann preparation."""

from __future__ import annotations

import pandas as pd
import pytest

from rossmann_forecasting.data.preparation import (
    SOURCE_SNAPSHOT_SHA256,
    build_prepared_tables,
    derive_test_open_resolution,
    join_store_metadata,
)


@pytest.fixture
def source_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = pd.DataFrame(
        {
            "Store": [1, 1, 2],
            "DayOfWeek": [1, 3, 2],
            "Date": ["2015-01-01", "2015-01-03", "2015-01-02"],
            "Sales": [0, 120, 90],
            "Customers": [0, 5, 4],
            "Open": [1, 1, 0],
            "Promo": [0, 1, 0],
            "StateHoliday": ["0", "0", "0"],
            "SchoolHoliday": [0, 0, 0],
        }
    )
    test = pd.DataFrame(
        {
            "Id": [1, 2],
            "Store": [1, 2],
            "DayOfWeek": [4, 5],
            "Date": ["2015-01-04", "2015-01-05"],
            "Open": [None, 1],
            "Promo": [0, 1],
            "StateHoliday": ["0", "0"],
            "SchoolHoliday": [0, 0],
        }
    )
    stores = pd.DataFrame(
        {
            "Store": [1, 2],
            "StoreType": ["a", "b"],
            "Assortment": ["a", "c"],
            "CompetitionDistance": [100.0, None],
            "CompetitionOpenSinceMonth": [None, 2.0],
            "CompetitionOpenSinceYear": [None, 2010.0],
            "Promo2": [0, 1],
            "Promo2SinceWeek": [None, 10.0],
            "Promo2SinceYear": [None, 2012.0],
            "PromoInterval": [None, "Jan,Apr,Jul,Oct"],
        }
    )
    return train, test, stores


def test_build_prepared_tables_preserves_rows_values_gaps_and_nulls(source_frames) -> None:
    train, test, stores = source_frames
    original_train = train.copy(deep=True)
    original_test = test.copy(deep=True)
    original_stores = stores.copy(deep=True)

    prepared_train, prepared_test = build_prepared_tables(train, test, stores)

    assert len(prepared_train) == len(train)
    assert len(prepared_test) == len(test)
    assert prepared_train["Date"].dtype == "datetime64[ns]"
    assert prepared_train["Date"].dt.strftime("%Y-%m-%d").tolist() == train["Date"].tolist()
    assert prepared_train[["Store", "Date"]].duplicated().sum() == 0
    assert prepared_train["Sales"].tolist() == [0, 120, 90]
    assert prepared_train["Open"].tolist() == [1, 1, 0]
    assert prepared_test["Open"].isna().tolist() == [True, False]
    assert "Sales" not in prepared_test
    assert "Customers" not in prepared_test
    assert prepared_train.columns.tolist() == list(train.columns) + list(stores.columns[1:])
    pd.testing.assert_frame_equal(train, original_train)
    pd.testing.assert_frame_equal(test, original_test)
    pd.testing.assert_frame_equal(stores, original_stores)


def test_prepared_parquet_round_trip_preserves_schema_and_missing_open(
    source_frames, tmp_path
) -> None:
    _, test, stores = source_frames
    prepared_test = join_store_metadata(test, stores, name="test")
    parquet_path = tmp_path / "test.parquet"

    prepared_test.to_parquet(parquet_path, engine="pyarrow", index=False)
    restored = pd.read_parquet(parquet_path, engine="pyarrow")

    pd.testing.assert_frame_equal(prepared_test, restored)
    assert restored["Open"].isna().tolist() == [True, False]


def test_join_rejects_duplicate_metadata_keys(source_frames) -> None:
    train, _, stores = source_frames
    duplicate = pd.concat([stores, stores.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="unique by Store"):
        join_store_metadata(train, duplicate, name="train")


def test_join_rejects_unmatched_stores(source_frames) -> None:
    train, _, stores = source_frames
    stores = stores.loc[stores["Store"].eq(1)]
    with pytest.raises(ValueError, match="no metadata row"):
        join_store_metadata(train, stores, name="train")


def test_join_rejects_duplicate_store_day_keys(source_frames) -> None:
    train, _, stores = source_frames
    duplicate = pd.concat([train, train.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate Store × Date"):
        join_store_metadata(duplicate, stores, name="train")


def test_snapshot_manifest_matches_all_phase_one_source_files() -> None:
    assert set(SOURCE_SNAPSHOT_SHA256) == {
        "train.csv",
        "test.csv",
        "store.csv",
        "sample_submission.csv",
    }
    assert all(len(value) == 64 for value in SOURCE_SNAPSHOT_SHA256.values())


def test_open_resolution_is_audited_and_leaves_source_null_unchanged() -> None:
    history = pd.DataFrame(
        {
            "Store": [622] * 35,
            "Date": pd.date_range("2015-01-01", periods=35),
            "Open": [1] * 35,
            "DayOfWeek": [1] * 35,
            "Promo": [0] * 35,
            "StateHoliday": ["0"] * 35,
            "SchoolHoliday": [0] * 35,
            "Sales": [500] * 35,
            "Customers": [10] * 35,
        }
    )
    future = pd.DataFrame(
        {
            "Store": [622],
            "Date": [pd.Timestamp("2015-08-03")],
            "Open": [None],
            "DayOfWeek": [1],
            "Promo": [0],
            "StateHoliday": ["0"],
            "SchoolHoliday": [0],
        }
    )

    resolved = derive_test_open_resolution(history, future)

    assert pd.isna(resolved.loc[0, "Open"])
    assert resolved.loc[0, "Open_resolved"] == 1
    assert resolved.loc[0, "historical_match_rows"] == 35
    assert resolved.loc[0, "Open_resolution_method"] == "historical_exact_context_consensus"
    assert bool(resolved.loc[0, "resolution_uncertain"])


def test_open_resolution_refuses_mixed_history_and_future_targets() -> None:
    history = pd.DataFrame(
        {
            "Store": [622] * 35,
            "Date": pd.date_range("2015-01-01", periods=35),
            "Open": [1] * 34 + [0],
            "DayOfWeek": [1] * 35,
            "Promo": [0] * 35,
            "StateHoliday": ["0"] * 35,
            "SchoolHoliday": [0] * 35,
        }
    )
    future = pd.DataFrame(
        {
            "Store": [622],
            "Date": [pd.Timestamp("2015-08-03")],
            "Open": [None],
            "DayOfWeek": [1],
            "Promo": [0],
            "StateHoliday": ["0"],
            "SchoolHoliday": [0],
        }
    )
    assert pd.isna(derive_test_open_resolution(history, future).loc[0, "Open_resolved"])
    with_targets = future.assign(Sales=123, Customers=4)
    with pytest.raises(ValueError, match="must not read future Sales"):
        derive_test_open_resolution(history, with_targets)


def test_open_resolution_ignores_history_after_each_forecast_date() -> None:
    history = pd.DataFrame(
        {
            "Store": [622] * 36,
            "Date": list(pd.date_range("2015-01-01", periods=35)) + [pd.Timestamp("2015-08-04")],
            "Open": [1] * 35 + [0],
            "DayOfWeek": [1] * 36,
            "Promo": [0] * 36,
            "StateHoliday": ["0"] * 36,
            "SchoolHoliday": [0] * 36,
        }
    )
    future = pd.DataFrame(
        {
            "Store": [622],
            "Date": [pd.Timestamp("2015-08-03")],
            "Open": [None],
            "DayOfWeek": [1],
            "Promo": [0],
            "StateHoliday": ["0"],
            "SchoolHoliday": [0],
        }
    )

    resolved = derive_test_open_resolution(history, future)

    assert resolved.loc[0, "Open_resolved"] == 1
    assert resolved.loc[0, "historical_match_rows"] == 35
