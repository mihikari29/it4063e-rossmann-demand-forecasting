"""Approved development windows and post-forecast evaluation-record assembly."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from rossmann_forecasting.features.calendar import normalize_dates
from rossmann_forecasting.features.keys import canonicalize_store_date_keys
from rossmann_forecasting.forecasting.seasonal_naive import forecast_seasonal_naive

FINAL_HOLDOUT_START = pd.Timestamp("2015-07-04")
LAST_DEVELOPMENT_DATE = pd.Timestamp("2015-07-03")


@dataclass(frozen=True)
class ValidationWindow:
    """One fixed, chronological 14-day development forecast window."""

    name: str
    forecast_origin: pd.Timestamp
    target_start: pd.Timestamp
    target_end: pd.Timestamp


APPROVED_DEVELOPMENT_WINDOWS = (
    ValidationWindow(
        name="validation_1",
        forecast_origin=pd.Timestamp("2015-05-22"),
        target_start=pd.Timestamp("2015-05-23"),
        target_end=pd.Timestamp("2015-06-05"),
    ),
    ValidationWindow(
        name="validation_2",
        forecast_origin=pd.Timestamp("2015-06-05"),
        target_start=pd.Timestamp("2015-06-06"),
        target_end=pd.Timestamp("2015-06-19"),
    ),
    ValidationWindow(
        name="validation_3",
        forecast_origin=pd.Timestamp("2015-06-19"),
        target_start=pd.Timestamp("2015-06-20"),
        target_end=pd.Timestamp("2015-07-03"),
    ),
)

EVALUATION_RECORD_COLUMNS = (
    "Store",
    "forecast_origin",
    "Date",
    "horizon",
    "raw_baseline_forecast",
    "operational_forecast",
    "actual_sales",
    "source_open",
    "forecast_available",
    "operational_forecast_available",
    "primary_evaluation_eligible",
    "validation_window",
)


def validate_development_windows(
    windows: tuple[ValidationWindow, ...] = APPROVED_DEVELOPMENT_WINDOWS,
) -> None:
    """Check exact 14-day, ordered, non-overlapping windows before the holdout."""

    if not windows:
        raise ValueError("At least one development validation window is required.")
    names = [window.name for window in windows]
    if len(set(names)) != len(names):
        raise ValueError("Validation window names must be unique.")

    previous_end: pd.Timestamp | None = None
    for window in windows:
        dates = (window.forecast_origin, window.target_start, window.target_end)
        normalized = [
            pd.Timestamp(normalize_dates(pd.Series([date]), name="validation window date").iloc[0])
            for date in dates
        ]
        origin, start, end = normalized
        if start != origin + pd.Timedelta(days=1):
            raise ValueError(f"{window.name} must begin the day after its forecast origin.")
        if end < start or (end - start).days != 13:
            raise ValueError(f"{window.name} must contain exactly 14 calendar target dates.")
        if end >= FINAL_HOLDOUT_START:
            raise ValueError(f"{window.name} must end before the final holdout.")
        if previous_end is not None and start <= previous_end:
            raise ValueError(
                "Validation target windows must be chronologically ordered and disjoint."
            )
        previous_end = end


def _validated_development_history(historical: pd.DataFrame) -> pd.DataFrame:
    required = {"Store", "Date", "Sales", "Open"}
    missing = required.difference(historical.columns)
    if missing:
        raise ValueError(f"Historical development data are missing columns: {sorted(missing)}.")
    data = canonicalize_store_date_keys(historical, name="historical development data")
    if data["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        latest = data.loc[data["Date"].gt(LAST_DEVELOPMENT_DATE), "Date"].max()
        raise ValueError(
            "Development evaluator received a row after 2015-07-03; final-holdout rows "
            f"must be filtered before evaluation ({latest.date()})."
        )
    return data


def _validate_source_labels(labels: pd.DataFrame) -> pd.DataFrame:
    result = labels[["Store", "Date", "Sales", "Open"]].copy()
    actual_sales = pd.to_numeric(result["Sales"], errors="coerce")
    invalid_sales = result["Sales"].notna() & actual_sales.isna()
    invalid_sales |= actual_sales.notna() & (
        ~np.isfinite(actual_sales.to_numpy(dtype=np.float64, na_value=np.nan)) | actual_sales.lt(0)
    )
    if invalid_sales.any():
        raise ValueError("Historical target Sales labels must be finite and non-negative.")
    open_values = pd.to_numeric(result["Open"], errors="coerce")
    invalid_open = result["Open"].notna() & open_values.isna()
    invalid_open |= open_values.notna() & ~open_values.isin([0, 1])
    if invalid_open.any():
        raise ValueError("Historical source Open values must be 0, 1, or missing.")
    result["Sales"] = actual_sales.astype("float64")
    result["Open"] = open_values.astype("float64")
    return result


def assemble_evaluation_records(
    raw_forecasts: pd.DataFrame,
    target_labels: pd.DataFrame,
    *,
    validation_window: str,
) -> pd.DataFrame:
    """Attach target Sales/Open only after label-free raw forecasts are complete."""

    required_forecasts = {
        "Store",
        "forecast_origin",
        "Date",
        "horizon",
        "raw_baseline_forecast",
    }
    missing_forecasts = required_forecasts.difference(raw_forecasts.columns)
    if missing_forecasts:
        raise ValueError(f"Raw forecasts are missing columns: {sorted(missing_forecasts)}.")
    if not {"Store", "Date", "Sales", "Open"}.issubset(target_labels.columns):
        raise ValueError("target_labels must contain Store, Date, Sales, and Open.")

    forecasts = raw_forecasts.copy()
    forecasts = canonicalize_store_date_keys(forecasts, name="raw forecast records")
    forecasts["forecast_origin"] = normalize_dates(
        forecasts["forecast_origin"], name="raw forecast forecast_origin"
    )
    if forecasts["forecast_origin"].nunique() != 1:
        raise ValueError("One evaluation window must contain exactly one forecast origin.")
    forecast_horizon = pd.to_numeric(forecasts["horizon"], errors="coerce")
    invalid_horizon = forecast_horizon.isna() | forecast_horizon.mod(1).ne(0)
    if invalid_horizon.any():
        raise ValueError("Raw forecast horizons must be integer calendar leads from 1 through 14.")
    forecast_horizon = forecast_horizon.astype("int16")
    expected_horizon = (forecasts["Date"] - forecasts["forecast_origin"]).dt.days
    if (
        forecast_horizon.lt(1).any()
        or forecast_horizon.gt(14).any()
        or forecast_horizon.ne(expected_horizon).any()
    ):
        raise ValueError("Raw forecast horizon must equal Date minus forecast_origin in 1..14.")
    forecasts["horizon"] = forecast_horizon.astype("int8")
    raw_forecast_values = pd.to_numeric(forecasts["raw_baseline_forecast"], errors="coerce")
    invalid_raw_forecasts = forecasts["raw_baseline_forecast"].notna() & raw_forecast_values.isna()
    invalid_raw_forecasts |= raw_forecast_values.notna() & (
        ~np.isfinite(raw_forecast_values.to_numpy(dtype=np.float64, na_value=np.nan))
        | raw_forecast_values.lt(0)
    )
    if invalid_raw_forecasts.any():
        raise ValueError("Available raw forecast values must be finite and non-negative.")
    forecasts["raw_baseline_forecast"] = raw_forecast_values.astype("float64")
    keys = target_labels[["Store", "Date"]].copy()
    canonical_keys = canonicalize_store_date_keys(keys, name="evaluation target labels")
    label_frame = pd.concat(
        [
            canonical_keys[["Store", "Date"]].reset_index(drop=True),
            target_labels[["Sales", "Open"]].reset_index(drop=True),
        ],
        axis=1,
    )
    labels = _validate_source_labels(label_frame)
    if forecasts.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise ValueError("Raw forecast composite keys are not unique.")
    forecast_keys = set(map(tuple, forecasts[["Store", "Date"]].itertuples(index=False, name=None)))
    label_keys = set(map(tuple, labels[["Store", "Date"]].itertuples(index=False, name=None)))
    if forecast_keys != label_keys or len(forecasts) != len(labels):
        raise ValueError("Raw forecast keys must exactly match observed target label keys.")

    merged = forecasts.merge(
        labels.rename(columns={"Sales": "actual_sales", "Open": "source_open"}),
        on=["Store", "Date"],
        how="left",
        validate="one_to_one",
        sort=False,
    )
    raw = pd.to_numeric(merged["raw_baseline_forecast"], errors="coerce")
    source_open = merged["source_open"]
    operational = np.full(len(merged), np.nan, dtype=np.float64)
    closed = source_open.eq(0).to_numpy()
    open_rows = source_open.eq(1).to_numpy()
    operational[closed] = 0.0
    operational[open_rows] = raw.loc[open_rows].to_numpy(dtype=np.float64, na_value=np.nan)

    merged["raw_baseline_forecast"] = raw.astype("float64")
    merged["operational_forecast"] = operational
    merged["forecast_available"] = raw.notna().to_numpy(dtype=bool)
    merged["operational_forecast_available"] = np.isfinite(operational)
    merged["primary_evaluation_eligible"] = (
        source_open.eq(1) & merged["actual_sales"].notna() & raw.notna()
    ).to_numpy(dtype=bool)
    merged["validation_window"] = validation_window
    result = merged.loc[:, EVALUATION_RECORD_COLUMNS].reset_index(drop=True)
    if result.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise AssertionError("Evaluation records contain duplicate composite keys.")
    return result


def build_window_evaluation_records(
    historical_development: pd.DataFrame,
    window: ValidationWindow,
) -> pd.DataFrame:
    """Generate a window's raw forecasts first, then attach observed target labels."""

    validate_development_windows((window,))
    data = _validated_development_history(historical_development)
    target_mask = data["Date"].between(window.target_start, window.target_end)
    target_keys = data.loc[target_mask, ["Store", "Date"]].copy()
    if target_keys.empty:
        raise ValueError(f"No observed target rows exist for {window.name}.")

    actual_history = data.loc[
        data["Date"].le(window.forecast_origin), ["Store", "Date", "Sales"]
    ].copy()
    raw_forecasts = forecast_seasonal_naive(
        target_keys,
        actual_history_through_origin=actual_history,
        forecast_origin=window.forecast_origin,
        horizon=14,
    )

    # Label/routing fields are selected only after raw forecast generation has returned.
    target_labels = data.loc[target_mask, ["Store", "Date", "Sales", "Open"]].copy()
    return assemble_evaluation_records(
        raw_forecasts,
        target_labels,
        validation_window=window.name,
    )


def build_development_evaluation_records(
    historical_development: pd.DataFrame,
) -> pd.DataFrame:
    """Evaluate exactly the approved development windows, without holdout rows."""

    validate_development_windows()
    data = _validated_development_history(historical_development)
    outputs = [
        build_window_evaluation_records(data, window) for window in APPROVED_DEVELOPMENT_WINDOWS
    ]
    result = pd.concat(outputs, ignore_index=True)
    if result["Date"].gt(LAST_DEVELOPMENT_DATE).any():
        raise AssertionError("Development evaluation emitted a final-holdout target.")
    if result.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise AssertionError("Development evaluation contains duplicate forecast keys.")
    return result
