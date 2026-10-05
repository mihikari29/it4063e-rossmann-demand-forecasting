"""Canonical, non-mutating Store × Date key validation for feature construction."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

from rossmann_forecasting.features.calendar import normalize_dates

_INT64_MAX = np.iinfo(np.int64).max
_MAX_SAFE_FLOAT_INTEGER = 2**53


def _store_id_as_int64(value: object) -> int:
    """Convert one safe, positive integer identifier to int64 without truncation."""

    if isinstance(value, (bool, np.bool_)):
        raise ValueError

    if isinstance(value, (int, np.integer)):
        identifier = int(value)
    elif isinstance(value, (float, np.floating)):
        if (
            not np.isfinite(value)
            or value != np.trunc(value)
            or abs(value) > _MAX_SAFE_FLOAT_INTEGER
        ):
            raise ValueError
        identifier = int(value)
    elif isinstance(value, (str, Decimal)):
        try:
            number = value if isinstance(value, Decimal) else Decimal(value.strip())
        except InvalidOperation, ValueError:
            raise ValueError from None
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError
        if number < 1 or number > _INT64_MAX:
            raise ValueError
        identifier = int(number)
    else:
        raise ValueError

    if identifier < 1 or identifier > _INT64_MAX:
        raise ValueError
    return identifier


def canonicalize_store_date_keys(frame: pd.DataFrame, *, name: str) -> pd.DataFrame:
    """Return a copy with validated int64 Store and datetime64[ns] Date keys.

    Store values must be positive, exact integers and safely coercible to int64. Dates must
    parse as midnight calendar dates. Duplicate detection runs after both key columns have been
    canonicalized, so equivalent input representations cannot evade the uniqueness check.
    """

    missing = {"Store", "Date"}.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} requires Store and Date columns; missing {sorted(missing)}.")

    canonical = frame.copy()
    store_values = []
    for value in canonical["Store"].array:
        try:
            store_values.append(_store_id_as_int64(value))
        except ValueError:
            raise ValueError(
                f"{name} Store keys must be non-missing, positive, exact integer identifiers "
                "that can be safely represented as int64."
            ) from None
    canonical["Store"] = np.asarray(store_values, dtype=np.int64)

    dates = normalize_dates(canonical["Date"], name=f"{name} Date")
    canonical["Date"] = dates.to_numpy(dtype="datetime64[ns]")

    if canonical.duplicated(["Store", "Date"]).any():
        duplicates = canonical.loc[
            canonical.duplicated(["Store", "Date"], keep=False), ["Store", "Date"]
        ].head(5)
        raise ValueError(
            f"{name} contains duplicate Store × Date keys after canonicalization: "
            f"{duplicates.to_dict('records')}"
        )
    return canonical
