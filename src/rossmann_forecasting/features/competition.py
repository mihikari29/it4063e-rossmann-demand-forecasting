"""Competition opening status and month-granular age predictors."""

from __future__ import annotations

from typing import Any

import pandas as pd

from rossmann_forecasting.features.calendar import normalize_dates


def _numeric_metadata(rows: pd.DataFrame, column: str) -> pd.Series:
    parsed = pd.to_numeric(rows[column], errors="coerce")
    malformed = rows[column].notna() & parsed.isna()
    if malformed.any():
        raise ValueError(f"{column} contains non-numeric metadata values.")
    fractional = parsed.notna() & parsed.mod(1).ne(0)
    if fractional.any():
        raise ValueError(f"{column} must contain integer-valued metadata when present.")
    return parsed


def build_competition_features(
    rows: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Build nullable opened-status and completed calendar-month age.

    Competition metadata is month/year resolution only. A helper first-of-month date is not
    materialized; this function compares integer calendar-month offsets directly.
    """

    required = {"Store", "Date", "CompetitionOpenSinceMonth", "CompetitionOpenSinceYear"}
    missing = sorted(required.difference(rows.columns))
    if missing:
        raise ValueError(f"Competition features are missing required columns: {missing}")

    dates = normalize_dates(rows["Date"])
    month = _numeric_metadata(rows, "CompetitionOpenSinceMonth")
    year = _numeric_metadata(rows, "CompetitionOpenSinceYear")
    metadata = rows[["Store"]].copy()
    metadata["month"] = month
    metadata["year"] = year
    metadata = metadata.drop_duplicates()
    if metadata["Store"].duplicated().any():
        stores = metadata.loc[metadata["Store"].duplicated(), "Store"].head(5).tolist()
        raise ValueError(f"Competition opening metadata changes within a store: {stores}")

    partial = month.isna() ^ year.isna()
    if partial.any():
        stores = rows.loc[partial, "Store"].drop_duplicates().head(10).tolist()
        raise ValueError(
            f"Competition opening month/year is partially missing for stores: {stores}"
        )

    invalid_month = month.notna() & ~month.between(1, 12)
    invalid_year = year.notna() & ~year.between(1900, 2100)
    if invalid_month.any() or invalid_year.any():
        bad = rows.loc[
            invalid_month | invalid_year,
            ["Store", "CompetitionOpenSinceMonth", "CompetitionOpenSinceYear"],
        ]
        raise ValueError(
            "Competition opening month/year is outside Phase 1 validation ranges: "
            f"{bad.drop_duplicates().head(10).to_dict('records')}"
        )

    known = month.notna() & year.notna()
    target_month_index = dates.dt.year.astype("int64") * 12 + dates.dt.month.astype("int64")
    opening_month_index = year.fillna(0).astype("int64") * 12 + month.fillna(0).astype("int64")
    offset = target_month_index - opening_month_index
    opened = pd.Series(pd.NA, index=rows.index, dtype="boolean")
    age = pd.Series(pd.NA, index=rows.index, dtype="Int16")
    opened.loc[known] = offset.loc[known].ge(0).to_numpy()
    age.loc[known] = offset.loc[known].clip(lower=0).astype("int16").to_numpy()

    missing_stores = rows.loc[~known, "Store"].drop_duplicates().astype(int).tolist()
    findings = []
    if missing_stores:
        findings.append(
            {
                "feature": "competition_opening_metadata",
                "reason": (
                    "Competition opening month/year is jointly missing; preserved as unknown."
                ),
                "affected_stores": len(missing_stores),
                "affected_rows": int((~known).sum()),
            }
        )

    return (
        pd.DataFrame(
            {"competition_has_opened": opened, "competition_age_months": age},
            index=rows.index,
        ),
        findings,
    )
