"""Origin-safe weekly Seasonal Naive forecasts for sparse Store × Date targets."""

from __future__ import annotations

from numbers import Integral

import numpy as np
import pandas as pd

from rossmann_forecasting.features.calendar import normalize_dates
from rossmann_forecasting.features.keys import canonicalize_store_date_keys

MAX_FORECAST_HORIZON = 14
FORECAST_RECORD_COLUMNS = (
    "Store",
    "forecast_origin",
    "Date",
    "horizon",
    "raw_baseline_forecast",
)


def _calendar_date(value: object, *, name: str) -> pd.Timestamp:
    """Parse one date-only value through the shared Phase 3 date contract."""

    return pd.Timestamp(normalize_dates(pd.Series([value]), name=name).iloc[0])


def _validated_horizon(horizon: int) -> int:
    if isinstance(horizon, bool) or not isinstance(horizon, Integral):
        raise ValueError("horizon must be an integer from 1 through 14.")
    value = int(horizon)
    if not 1 <= value <= MAX_FORECAST_HORIZON:
        raise ValueError("horizon must be an integer from 1 through 14.")
    return value


def forecast_seasonal_naive(
    target_keys: pd.DataFrame,
    *,
    actual_history_through_origin: pd.DataFrame,
    forecast_origin: str | pd.Timestamp,
    horizon: int = MAX_FORECAST_HORIZON,
) -> pd.DataFrame:
    """Forecast observed target keys using exact weekly lookup and recursive state.

    ``target_keys`` must contain only ``Store`` and ``Date``. It defines which forecasts are
    emitted, not which internal states are generated: for every Store represented there, the
    function computes every calendar horizon from 1 through ``horizon``. This lets a forecast at
    h=8 use its internal h=1 state even if the h=1 Store × Date label row is absent.

    Actual history is canonicalized and must be explicitly censored at ``forecast_origin``.
    Target dates must be date-only and fall within horizons 1..``horizon``. No target labels,
    ``Open``, ``Customers``, or post-origin actuals are read by this function.
    """

    if set(target_keys.columns) != {"Store", "Date"} or len(target_keys.columns) != 2:
        raise ValueError("target_keys must contain exactly Store and Date, with no label fields.")
    required_history = {"Store", "Date", "Sales"}
    missing = required_history.difference(actual_history_through_origin.columns)
    if missing:
        raise ValueError(f"actual_history_through_origin is missing columns: {sorted(missing)}.")
    if target_keys.empty:
        raise ValueError("target_keys must contain at least one observed Store × Date key.")

    max_horizon = _validated_horizon(horizon)
    origin = _calendar_date(forecast_origin, name="forecast_origin")
    targets = canonicalize_store_date_keys(target_keys, name="target_keys")[
        ["Store", "Date"]
    ].reset_index(drop=True)
    history = canonicalize_store_date_keys(
        actual_history_through_origin[["Store", "Date", "Sales"]],
        name="actual_history_through_origin",
    )

    if history["Date"].gt(origin).any():
        latest = history.loc[history["Date"].gt(origin), "Date"].max()
        raise ValueError(
            "actual_history_through_origin contains a date after forecast_origin "
            f"({latest.date()} > {origin.date()})."
        )

    target_horizons = (targets["Date"] - origin).dt.days
    if target_horizons.le(0).any():
        raise ValueError("All target dates must be strictly after forecast_origin.")
    if target_horizons.gt(max_horizon).any():
        raise ValueError(f"All target dates must fall within horizons 1..{max_horizon}.")

    sales = pd.to_numeric(history["Sales"], errors="coerce")
    if sales.isna().any() or not np.isfinite(sales.to_numpy(dtype=np.float64)).all():
        raise ValueError("Actual-history Sales values must be finite and non-missing.")
    if sales.lt(0).any():
        raise ValueError("Actual-history Sales values must be non-negative.")

    actual_values = {
        (int(store), pd.Timestamp(date)): float(value)
        for store, date, value in zip(history["Store"], history["Date"], sales, strict=True)
    }
    stores = targets["Store"].drop_duplicates().tolist()
    forecast_states: dict[tuple[int, pd.Timestamp], float | None] = {}

    for store_value in stores:
        store = int(store_value)
        for step in range(1, max_horizon + 1):
            target_date = origin + pd.Timedelta(days=step)
            weekly_source_date = target_date - pd.Timedelta(days=7)
            if weekly_source_date <= origin:
                value = actual_values.get((store, weekly_source_date))
            else:
                value = forecast_states.get((store, weekly_source_date))
            forecast_states[(store, target_date)] = value

    raw_values = [
        forecast_states[(int(store), pd.Timestamp(date))]
        for store, date in zip(targets["Store"], targets["Date"], strict=True)
    ]
    result = targets.copy()
    result.insert(1, "forecast_origin", pd.Series([origin] * len(result), dtype="datetime64[ns]"))
    result["horizon"] = target_horizons.astype("int8")
    result["raw_baseline_forecast"] = np.asarray(
        [np.nan if value is None else value for value in raw_values], dtype=np.float64
    )
    result = result.loc[:, FORECAST_RECORD_COLUMNS]
    if result.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise AssertionError("Forecast output contains duplicate composite keys.")
    return result
