"""Exact-date Sales lags and complete calendar-window statistics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from rossmann_forecasting.features.calendar import normalize_dates
from rossmann_forecasting.features.contract import DYNAMIC_PREDICTOR_COLUMNS
from rossmann_forecasting.features.keys import canonicalize_store_date_keys

_DAY_NS = 86_400_000_000_000
_LAGS = (1, 7, 14, 28)
_WINDOWS = (7, 14, 28)


@dataclass
class _StoreHistory:
    """Lookup and prefix statistics for one store's observed/predicted dates."""

    days: np.ndarray
    day_positions: dict[int, int]
    prefix_sum: np.ndarray
    prefix_square_sum: np.ndarray
    values: np.ndarray


def _day_numbers(values: pd.Series, *, name: str) -> np.ndarray:
    dates = normalize_dates(values, name=name)
    return dates.astype("int64").to_numpy() // _DAY_NS


def _store_histories(history: pd.DataFrame, *, sales_column: str) -> dict[int, _StoreHistory]:
    if sales_column not in history:
        raise ValueError(f"Sales history is missing {sales_column}.")
    canonical_history = canonicalize_store_date_keys(history, name="Sales history")
    sales = pd.to_numeric(canonical_history[sales_column], errors="coerce")
    invalid = sales.isna() | ~np.isfinite(sales) | sales.lt(0)
    if invalid.any():
        raise ValueError(f"{sales_column} history must contain finite, non-negative values.")

    prepared = canonical_history[["Store", "Date"]].copy()
    prepared["_day"] = _day_numbers(prepared["Date"], name="Sales history Date")
    prepared["_sales"] = sales.to_numpy(dtype=np.float64)
    result: dict[int, _StoreHistory] = {}
    for store, group in prepared.groupby("Store", sort=False, observed=True):
        ordered = group.sort_values("_day", kind="stable")
        days = ordered["_day"].to_numpy(dtype=np.int64)
        values = ordered["_sales"].to_numpy(dtype=np.float64)
        day_positions = {int(day): position for position, day in enumerate(days)}
        prefix_sum = np.concatenate(([0.0], np.cumsum(values, dtype=np.float64)))
        prefix_square_sum = np.concatenate(([0.0], np.cumsum(values * values, dtype=np.float64)))
        result[int(store)] = _StoreHistory(
            days=days,
            day_positions=day_positions,
            prefix_sum=prefix_sum,
            prefix_square_sum=prefix_square_sum,
            values=values,
        )
    return result


def _calculate_history_features(
    target_rows: pd.DataFrame,
    history: pd.DataFrame | None,
    *,
    sales_column: str,
    prepared_histories: dict[int, _StoreHistory] | None = None,
) -> pd.DataFrame:
    canonical_targets = canonicalize_store_date_keys(target_rows, name="Target rows")
    if prepared_histories is None:
        if history is None:
            raise ValueError("Sales history or prepared store histories are required.")
        histories = _store_histories(history, sales_column=sales_column)
    else:
        histories = prepared_histories
    target_days = _day_numbers(canonical_targets["Date"], name="Target Date")
    store_values = canonical_targets["Store"].to_numpy(dtype=np.int64)
    matrix = np.full(
        (len(canonical_targets), len(DYNAMIC_PREDICTOR_COLUMNS)), np.nan, dtype=np.float64
    )

    for row_position, (store, target_day) in enumerate(zip(store_values, target_days, strict=True)):
        store_history = histories.get(int(store))
        if store_history is None:
            continue
        positions = store_history.day_positions
        for lag_position, lag_days in enumerate(_LAGS):
            history_position = positions.get(int(target_day) - lag_days)
            if history_position is not None:
                matrix[row_position, lag_position] = store_history.values[history_position]

        for window_position, window_days in enumerate(_WINDOWS):
            first_position = positions.get(int(target_day) - window_days)
            last_position = positions.get(int(target_day) - 1)
            observed_days = (
                store_history.days[first_position : last_position + 1]
                if first_position is not None and last_position is not None
                else np.array([], dtype=np.int64)
            )
            # Exact endpoint lookups plus consecutive observed calendar days prove full coverage.
            if (
                first_position is None
                or last_position is None
                or len(observed_days) != window_days
                or (np.diff(observed_days) != 1).any()
            ):
                continue
            total = (
                store_history.prefix_sum[last_position + 1]
                - store_history.prefix_sum[first_position]
            )
            square_total = (
                store_history.prefix_square_sum[last_position + 1]
                - store_history.prefix_square_sum[first_position]
            )
            mean = total / window_days
            variance = max(0.0, (square_total - total * total / window_days) / (window_days - 1))
            matrix[row_position, 4 + window_position] = mean
            matrix[row_position, 7 + window_position] = np.sqrt(variance)

    return pd.DataFrame(matrix, columns=DYNAMIC_PREDICTOR_COLUMNS, index=canonical_targets.index)


class OriginHistoryFeatureCache:
    """Reuse an origin-censored history index as recursive predictions arrive."""

    def __init__(
        self, actual_history_through_origin: pd.DataFrame, forecast_origin: str | pd.Timestamp
    ):
        actual = canonicalize_store_date_keys(
            actual_history_through_origin, name="actual_history_through_origin"
        )
        if "Sales" not in actual:
            raise ValueError("actual_history_through_origin must contain Sales.")
        self.forecast_origin = normalize_dates(
            pd.Series([forecast_origin]), name="forecast_origin"
        ).iloc[0]
        if actual["Date"].gt(self.forecast_origin).any():
            latest = actual["Date"].max()
            raise ValueError(
                "actual_history_through_origin contains actual Sales after forecast_origin "
                f"({latest.date()} > {self.forecast_origin.date()})."
            )
        actual = actual.loc[:, ["Store", "Date", "Sales"]]
        self._histories = _store_histories(actual, sales_column="Sales")
        self._origin_day = int(
            _day_numbers(pd.Series([self.forecast_origin]), name="forecast_origin")[0]
        )

    def features(self, target_rows: pd.DataFrame) -> pd.DataFrame:
        """Calculate predictors using actuals plus predictions already appended to the cache."""

        canonical_targets = canonicalize_store_date_keys(target_rows, name="Target rows")
        if canonical_targets["Date"].le(self.forecast_origin).any():
            raise ValueError("Inference target dates must be strictly after forecast_origin.")
        return _calculate_history_features(
            target_rows,
            None,
            sales_column="Sales",
            prepared_histories=self._histories,
        )

    def append_predictions(self, predictions: pd.DataFrame) -> None:
        """Append one completed recursive horizon; omitted stores remain missing for that date."""

        required = {"Store", "Date", "PredictedSales"}
        missing = sorted(required.difference(predictions.columns))
        if missing:
            raise ValueError(f"Recursive predictions are missing columns: {missing}")
        canonical = canonicalize_store_date_keys(
            predictions[["Store", "Date"]], name="recursive predictions"
        )
        if canonical["Date"].le(self.forecast_origin).any():
            raise ValueError("Recursive predictions must be strictly after forecast_origin.")
        values = pd.to_numeric(predictions["PredictedSales"], errors="coerce")
        value_array = values.to_numpy(dtype=np.float64)
        if values.isna().any() or not np.isfinite(value_array).all() or values.lt(0).any():
            raise ValueError("Recursive predictions must be finite and non-negative.")

        day_numbers = _day_numbers(canonical["Date"], name="recursive prediction Date")
        stores = canonical["Store"].to_numpy(dtype=np.int64)
        for store, day_number, value in zip(stores, day_numbers, value_array, strict=True):
            store_history = self._histories.get(int(store))
            if store_history is None:
                store_history = _StoreHistory(
                    days=np.array([], dtype=np.int64),
                    day_positions={},
                    prefix_sum=np.array([0.0]),
                    prefix_square_sum=np.array([0.0]),
                    values=np.array([], dtype=np.float64),
                )
                self._histories[int(store)] = store_history
            if int(day_number) in store_history.day_positions:
                raise ValueError("Recursive prediction overlaps an existing Store × Date value.")
            if len(store_history.days) and int(day_number) <= int(store_history.days[-1]):
                raise ValueError("Recursive predictions must be appended in date order per store.")
            next_position = len(store_history.values)
            store_history.days = np.append(store_history.days, day_number)
            store_history.values = np.append(store_history.values, value)
            store_history.day_positions[int(day_number)] = next_position
            store_history.prefix_sum = np.append(
                store_history.prefix_sum, store_history.prefix_sum[-1] + value
            )
            store_history.prefix_square_sum = np.append(
                store_history.prefix_square_sum,
                store_history.prefix_square_sum[-1] + value * value,
            )


def build_historical_history_features(
    target_rows: pd.DataFrame, sales_history: pd.DataFrame
) -> pd.DataFrame:
    """Build one-step historical features using only exact Sales dates before each target.

    The supplied history can contain later historical rows: every lookup is for an exact date
    strictly before its target date, so later values cannot satisfy a lag/window lookup.
    These rows are not substitutes for origin-censored recursive inference features.
    """

    return _calculate_history_features(target_rows, sales_history, sales_column="Sales")


def build_origin_history_features(
    target_rows: pd.DataFrame,
    *,
    actual_history_through_origin: pd.DataFrame,
    forecast_origin: str | pd.Timestamp,
    prior_recursive_predictions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build dynamic history features from origin-censored actuals and prior predictions.

    Actual rows after ``forecast_origin`` are rejected rather than silently ignored. The optional
    prediction frame must contain Store, Date, and PredictedSales; for each target row, only prior
    predictions with the same Store and an exact date before that target can be used. Every supplied
    prediction must precede at least one requested target for its Store.
    """

    canonical_targets = canonicalize_store_date_keys(target_rows, name="Target rows")
    actual = canonicalize_store_date_keys(
        actual_history_through_origin, name="actual_history_through_origin"
    )
    if "Sales" not in actual:
        raise ValueError("actual_history_through_origin must contain Sales.")
    origin = normalize_dates(pd.Series([forecast_origin]), name="forecast_origin").iloc[0]
    actual_dates = actual["Date"]
    target_dates = canonical_targets["Date"]
    if target_dates.le(origin).any():
        raise ValueError("Inference target dates must be strictly after forecast_origin.")

    actual = actual[["Store", "Date", "Sales"]].copy()
    if prior_recursive_predictions is None or prior_recursive_predictions.empty:
        if actual_dates.gt(origin).any():
            latest = actual_dates.max()
            raise ValueError(
                "actual_history_through_origin contains actual Sales after forecast_origin "
                f"({latest.date()} > {origin.date()}). Pass origin-censored actual history."
            )
        return _calculate_history_features(target_rows, actual, sales_column="Sales")

    required = {"Store", "Date", "PredictedSales"}
    missing = sorted(required.difference(prior_recursive_predictions.columns))
    if missing:
        raise ValueError(f"prior_recursive_predictions is missing columns: {missing}")
    predictions = canonicalize_store_date_keys(
        prior_recursive_predictions[["Store", "Date", "PredictedSales"]],
        name="prior_recursive_predictions",
    )
    prediction_dates = predictions["Date"]
    overlap = actual[["Store", "Date"]].merge(
        predictions[["Store", "Date"]], on=["Store", "Date"], how="inner"
    )
    if not overlap.empty:
        raise ValueError(
            "Actual history and recursive predictions contain overlapping Store × Date keys."
        )

    if actual_dates.gt(origin).any():
        latest = actual_dates.max()
        raise ValueError(
            "actual_history_through_origin contains actual Sales after forecast_origin "
            f"({latest.date()} > {origin.date()}). Pass origin-censored actual history."
        )
    if prediction_dates.le(origin).any():
        raise ValueError("Recursive predictions must be strictly after forecast_origin.")
    target_keys = canonical_targets[["Store", "Date"]].copy()
    latest_target_by_store = target_keys.groupby("Store", sort=False)["Date"].max()
    prediction_latest_targets = predictions[["Store"]].merge(
        latest_target_by_store.rename("latest_target_date"),
        left_on="Store",
        right_index=True,
        how="left",
        validate="many_to_one",
    )
    latest_target_dates = prediction_latest_targets["latest_target_date"].to_numpy()
    if (
        prediction_latest_targets["latest_target_date"].isna().any()
        or (prediction_dates.to_numpy() >= latest_target_dates).any()
    ):
        raise ValueError(
            "Each recursive prediction must be strictly before a requested target date "
            "for the same Store."
        )
    predicted_sales = pd.to_numeric(predictions["PredictedSales"], errors="coerce")
    if predicted_sales.isna().any() or not np.isfinite(predicted_sales).all():
        raise ValueError("Prior recursive predictions must be finite numeric values.")
    predictions["PredictedSales"] = predicted_sales.to_numpy(dtype=np.float64)

    prediction_history = predictions.rename(columns={"PredictedSales": "Sales"})
    combined = pd.concat([actual, prediction_history], ignore_index=True)
    return _calculate_history_features(target_rows, combined, sales_column="Sales")
