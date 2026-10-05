"""Date-derived calendar predictors with a source-weekday consistency check."""

from __future__ import annotations

import pandas as pd


def normalize_dates(values: pd.Series, *, name: str = "Date") -> pd.Series:
    """Parse date values and require date-only midnight timestamps."""

    dates = pd.to_datetime(values, errors="raise")
    if dates.isna().any():
        raise ValueError(f"{name} contains missing dates.")
    if not dates.eq(dates.dt.normalize()).all():
        raise ValueError(f"{name} must contain calendar dates without a time component.")
    return dates.astype("datetime64[ns]")


def build_calendar_features(rows: pd.DataFrame) -> pd.DataFrame:
    """Build calendar predictors and assert source DayOfWeek agrees with ISO weekday."""

    if "Date" not in rows:
        raise ValueError("Calendar features require Date.")
    dates = normalize_dates(rows["Date"])
    iso_weekday = dates.dt.isocalendar().day.astype("int8")

    if "DayOfWeek" in rows:
        source_weekday = pd.to_numeric(rows["DayOfWeek"], errors="coerce")
        invalid = (
            source_weekday.isna() | ~source_weekday.between(1, 7) | source_weekday.mod(1).ne(0)
        )
        mismatch = invalid | source_weekday.ne(iso_weekday)
        if mismatch.any():
            sample = pd.DataFrame(
                {
                    "Date": dates.loc[mismatch].astype(str),
                    "source_DayOfWeek": source_weekday.loc[mismatch],
                    "derived_iso_weekday": iso_weekday.loc[mismatch],
                }
            ).head(5)
            raise ValueError(
                "Source DayOfWeek disagrees with ISO weekday derived from Date: "
                f"{sample.to_dict('records')}"
            )

    iso_calendar = dates.dt.isocalendar()
    return pd.DataFrame(
        {
            "day_of_week": iso_weekday,
            "week_of_year": iso_calendar.week.astype("int8"),
            "month": dates.dt.month.astype("int8"),
            "quarter": dates.dt.quarter.astype("int8"),
            "year": dates.dt.year.astype("int16"),
            "is_weekend": iso_weekday.ge(6).astype(bool),
            "is_month_start": dates.dt.is_month_start.astype(bool),
            "is_month_end": dates.dt.is_month_end.astype(bool),
        },
        index=rows.index,
    )
