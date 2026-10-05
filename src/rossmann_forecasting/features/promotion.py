"""Future-known holiday and promotion predictors."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from rossmann_forecasting.features.calendar import normalize_dates

_MONTHS = {
    name: number
    for number, name in enumerate(
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
        start=1,
    )
}
_MONTHS["Sept"] = 9
_DAY_NS = 86_400_000_000_000


def _required_binary(rows: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(rows[column], errors="coerce")
    invalid = values.isna() | ~values.isin([0, 1])
    if invalid.any():
        raise ValueError(f"{column} must be present and encoded as 0 or 1.")
    return values.astype(bool)


def _single_store_metadata(rows: pd.DataFrame, fields: tuple[str, ...]) -> pd.DataFrame:
    metadata = rows[["Store", *fields]].drop_duplicates()
    if metadata["Store"].duplicated().any():
        stores = metadata.loc[metadata["Store"].duplicated(), "Store"].head(5).tolist()
        raise ValueError(f"Store-static promotion metadata changes within a store: {stores}")
    return metadata


def _interval_months(value: Any) -> set[int]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("PromoInterval is missing or empty.")
    tokens = [part.strip() for part in value.split(",")]
    try:
        months = {_MONTHS[token] for token in tokens}
    except KeyError as error:
        raise ValueError(
            f"PromoInterval contains an unrecognized month: {error.args[0]}"
        ) from error
    if not months or len(months) != len(tokens):
        raise ValueError("PromoInterval must contain unique month abbreviations.")
    return months


def build_promotion_features(
    rows: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Return future-known promotion/holiday features and schedule audit findings.

    Invalid or incomplete Promo2 participant schedules deliberately produce a nullable active
    indicator and an audit finding. Promo2 nonparticipants are False; their structural schedule
    nulls are not errors.
    """

    required = {
        "Store",
        "Date",
        "Promo",
        "StateHoliday",
        "SchoolHoliday",
        "Promo2",
        "Promo2SinceWeek",
        "Promo2SinceYear",
        "PromoInterval",
    }
    missing = sorted(required.difference(rows.columns))
    if missing:
        raise ValueError(f"Promotion features are missing required columns: {missing}")

    dates = normalize_dates(rows["Date"])
    promo = _required_binary(rows, "Promo")
    school_holiday = _required_binary(rows, "SchoolHoliday")
    promo2 = _required_binary(rows, "Promo2")
    state_holiday = rows["StateHoliday"].astype(pd.StringDtype(storage="python"))
    active = pd.Series(pd.NA, index=rows.index, dtype="boolean")
    active.loc[~promo2] = False
    findings: list[dict[str, Any]] = []

    fields = ("Promo2", "Promo2SinceWeek", "Promo2SinceYear", "PromoInterval")
    metadata = _single_store_metadata(rows, fields)
    for item in metadata.itertuples(index=False, name=None):
        store = item[0]
        store_promo2, raw_week, raw_year, interval = item[1:]
        if int(store_promo2) == 0:
            continue

        reason = None
        if pd.isna(raw_week) or pd.isna(raw_year) or pd.isna(interval):
            reason = "Promo2 participant has incomplete schedule metadata."
        else:
            try:
                week_number = float(raw_week)
                year_number = float(raw_year)
                if (
                    not week_number.is_integer()
                    or not year_number.is_integer()
                    or not 1 <= week_number <= 53
                    or not 1900 <= year_number <= 2100
                ):
                    raise ValueError("Promo2SinceWeek/Year is outside the validated integer range.")
                start = date.fromisocalendar(int(year_number), int(week_number), 1)
                months = _interval_months(interval)
            except (OverflowError, TypeError, ValueError) as error:
                reason = str(error)

        store_mask = rows["Store"].eq(store)
        if reason is not None:
            findings.append(
                {
                    "feature": "is_promo2_active",
                    "Store": int(store),
                    "reason": reason,
                    "affected_rows": int(store_mask.sum()),
                }
            )
            continue

        store_dates = dates.loc[store_mask]
        active.loc[store_mask] = (
            store_dates.ge(pd.Timestamp(start)) & store_dates.dt.month.isin(months)
        ).to_numpy()

    output = pd.DataFrame(
        {
            "state_holiday": state_holiday,
            "school_holiday": school_holiday.astype(bool),
            "promo": promo.astype(bool),
            "promo2": promo2.astype(bool),
            "is_promo2_active": active,
        },
        index=rows.index,
    )
    return output, findings
