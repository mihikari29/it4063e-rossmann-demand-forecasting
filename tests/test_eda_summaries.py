"""Small fixtures for deterministic, descriptive Rossmann EDA helpers."""

from __future__ import annotations

import pandas as pd

from rossmann_forecasting.analysis.eda import _summary, select_representative_stores


def _fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2015-01-01", periods=84, freq="D")
    metadata = {
        1: ("a", "a", 0, 100.0),
        2: ("b", "b", 1, 200.0),
        3: ("c", "c", 0, 300.0),
        4: ("d", "a", 1, 400.0),
    }
    rows = []
    for store, (store_type, assortment, promo2, competition) in metadata.items():
        for index, date in enumerate(dates):
            opened = int(date.dayofweek != 6)
            sales = 0 if (store == 2 and index == 7) or not opened else store * 100 + index
            rows.append(
                {
                    "Store": store,
                    "Date": date,
                    "Sales": sales,
                    "Customers": 0 if not opened else store * 2,
                    "Open": opened,
                    "Promo": int(index % 2 == 0),
                    "StateHoliday": "0",
                    "SchoolHoliday": int(index % 14 < 3),
                    "DayOfWeek": int(date.isoweekday()),
                    "StoreType": store_type,
                    "Assortment": assortment,
                    "Promo2": promo2,
                    "CompetitionDistance": competition,
                    "CompetitionOpenSinceMonth": None,
                    "CompetitionOpenSinceYear": None,
                    "Promo2SinceWeek": None,
                    "Promo2SinceYear": None,
                    "PromoInterval": None,
                }
            )
    train = pd.DataFrame(rows)
    test = pd.DataFrame(
        {
            "Store": [1],
            "Date": [pd.Timestamp("2015-03-26")],
            "Open": [None],
            "Promo": [0],
            "DayOfWeek": [4],
            "StateHoliday": ["0"],
            "SchoolHoliday": [0],
        }
    )
    return train, test


def test_representative_selection_is_deterministic_and_covers_metadata() -> None:
    train, _ = _fixture()
    before = train.copy(deep=True)
    first = select_representative_stores(train)
    second = select_representative_stores(train)

    pd.testing.assert_frame_equal(first, second)
    assert set(first["StoreType"]) == set(train["StoreType"])
    assert set(first["Assortment"]) == set(train["Assortment"])
    assert set(first["Promo2"]) == set(train["Promo2"])
    assert first["selection_reasons"].str.len().gt(0).all()
    pd.testing.assert_frame_equal(train, before)


def test_summary_uses_open_day_denominators_and_keeps_test_unlabelled() -> None:
    train, test = _fixture()
    summary, tables = _summary(train, test)

    assert summary["train"]["rows"] == len(train)
    assert summary["train"]["open_rows"] == int(train["Open"].eq(1).sum())
    assert summary["train"]["open_zero_rows"]["rows"] == 1
    assert summary["test"]["missing_open_rows"] == 1
    assert len(summary["weekday_open_sales"]) == 7
    assert len(tables["store_open_zero_context.csv"]) == 1
    assert "Sales" not in test
    assert "Customers" not in test
