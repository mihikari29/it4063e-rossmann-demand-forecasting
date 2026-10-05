"""Origin-safe additive Holt-Winters forecasts for Store × Date Sales."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from numbers import Integral

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from rossmann_forecasting.features.calendar import normalize_dates
from rossmann_forecasting.features.keys import canonicalize_store_date_keys

STATISTICAL_MODEL = "holt_winters_additive_weekly"
MINIMUM_HISTORY_DAYS = 28
FORECAST_HORIZON = 14
FORECAST_COLUMN = "raw_statistical_forecast"


@dataclass(frozen=True)
class HoltWintersForecastResult:
    """Observed-key forecasts plus label-free internal paths and fit diagnostics."""

    forecasts: pd.DataFrame
    internal_forecasts: pd.DataFrame
    diagnostics: pd.DataFrame


def _calendar_date(value: object, *, name: str) -> pd.Timestamp:
    return pd.Timestamp(normalize_dates(pd.Series([value]), name=name).iloc[0])


def _validated_horizon(horizon: int) -> int:
    if isinstance(horizon, bool) or not isinstance(horizon, Integral):
        raise ValueError("horizon must be an integer from 1 through 14.")
    result = int(horizon)
    if not 1 <= result <= FORECAST_HORIZON:
        raise ValueError("horizon must be an integer from 1 through 14.")
    return result


def _validated_inputs(
    target_keys: pd.DataFrame,
    actual_history_through_origin: pd.DataFrame,
    forecast_origin: str | pd.Timestamp,
    horizon: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, int]:
    if set(target_keys.columns) != {"Store", "Date"}:
        raise ValueError("target_keys must contain exactly Store and Date.")
    if set(actual_history_through_origin.columns) != {"Store", "Date", "Sales"}:
        raise ValueError("actual history must contain exactly Store, Date, and Sales.")
    origin = _calendar_date(forecast_origin, name="forecast_origin")
    steps = _validated_horizon(horizon)
    targets = canonicalize_store_date_keys(target_keys, name="forecast target keys")
    history = canonicalize_store_date_keys(
        actual_history_through_origin, name="actual history through origin"
    )
    if targets.empty:
        raise ValueError("At least one observed target key is required.")
    if history["Date"].gt(origin).any():
        latest = history.loc[history["Date"].gt(origin), "Date"].max()
        raise ValueError(
            "Actual history contains a row after forecast_origin "
            f"({latest.date()} > {origin.date()})."
        )
    if (targets["Date"] <= origin).any() or (targets["Date"] - origin).dt.days.gt(steps).any():
        raise ValueError("Every target key must be a future calendar date within horizons 1..14.")
    return targets, history, origin, steps


def _history_index(history: pd.DataFrame) -> dict[int, dict[pd.Timestamp, float | None]]:
    sales = pd.to_numeric(history["Sales"], errors="coerce")
    result: dict[int, dict[pd.Timestamp, float | None]] = {}
    for store, date, value in zip(history["Store"], history["Date"], sales, strict=True):
        numeric: float | None
        if pd.isna(value) or not np.isfinite(float(value)) or float(value) < 0:
            numeric = None
        else:
            numeric = float(value)
        result.setdefault(int(store), {})[pd.Timestamp(date)] = numeric
    return result


def _recent_contiguous_segment(
    observations: dict[pd.Timestamp, float | None], origin: pd.Timestamp
) -> tuple[list[float], pd.Timestamp | None, str | None]:
    if origin not in observations:
        return [], None, "missing_origin_row"
    if observations[origin] is None:
        return [], None, "unusable_origin_sales"

    reverse_values: list[float] = []
    current = origin
    stop_reason: str | None = None
    while current in observations:
        value = observations[current]
        if value is None:
            stop_reason = "unusable_sales_break"
            break
        reverse_values.append(value)
        current -= pd.Timedelta(days=1)
    else:
        stop_reason = "missing_calendar_date"
    return list(reversed(reverse_values)), current + pd.Timedelta(days=1), stop_reason


def _optimizer_status(fitted: object) -> tuple[bool | None, str | int | float | None]:
    retvals = getattr(fitted, "mle_retvals", None)
    if not isinstance(retvals, dict):
        return None, None
    success = retvals.get("success")
    converged = bool(success) if isinstance(success, (bool, np.bool_)) else None
    warnflag = retvals.get("warnflag")
    if isinstance(warnflag, (bool, np.bool_, int, np.integer)):
        warnflag_value: str | int | float | None = int(warnflag)
    elif isinstance(warnflag, (float, np.floating)) and np.isfinite(warnflag):
        warnflag_value = float(warnflag)
    elif warnflag is None:
        warnflag_value = None
    else:
        warnflag_value = type(warnflag).__name__
    return converged, warnflag_value


def forecast_holt_winters(
    target_keys: pd.DataFrame,
    *,
    actual_history_through_origin: pd.DataFrame,
    forecast_origin: str | pd.Timestamp,
    horizon: int = FORECAST_HORIZON,
) -> HoltWintersForecastResult:
    """Fit fixed additive Holt-Winters once per target Store and forecast h=1..14.

    The inputs are deliberately narrow: targets contain only Store/Date and history only
    Store/Date/Sales. A Store with fewer than 28 contiguous observations ending at the origin,
    or any construction/fit/forecast/output failure, remains unavailable without fallback.
    """

    targets, history, origin, steps = _validated_inputs(
        target_keys, actual_history_through_origin, forecast_origin, horizon
    )
    history_by_store = _history_index(history)
    target_stores = sorted(int(value) for value in targets["Store"].unique())
    path_records: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for store in target_stores:
        observations = history_by_store.get(store, {})
        values, segment_start, stop_reason = _recent_contiguous_segment(observations, origin)
        history_rows = len(values)
        eligible = history_rows >= MINIMUM_HISTORY_DAYS
        failure_reason: str | None = None
        if not eligible:
            failure_reason = (
                stop_reason
                if history_rows == 0
                and stop_reason in {"missing_origin_row", "unusable_origin_sales"}
                else "insufficient_contiguous_history"
            )

        full_forecast: np.ndarray | None = None
        warning_names: set[str] = set()
        warning_count = 0
        optimizer_converged: bool | None = None
        optimizer_warnflag: str | int | float | None = None
        failure_stage: str | None = None
        if eligible:
            daily_sales = pd.Series(
                values,
                index=pd.date_range(end=origin, periods=history_rows, freq="D"),
                name="Sales",
                dtype="float64",
            )
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                try:
                    model = ExponentialSmoothing(
                        daily_sales,
                        trend="add",
                        damped_trend=False,
                        seasonal="add",
                        seasonal_periods=7,
                        initialization_method="estimated",
                        use_boxcox=False,
                    )
                except Exception as exc:  # sanitized; no exception text in outputs
                    failure_reason = f"model_construction:{type(exc).__name__}"
                    failure_stage = "model_construction"
                    model = None
                fitted = None
                if model is not None:
                    try:
                        fitted = model.fit(optimized=True)
                    except Exception as exc:
                        failure_reason = f"model_fit:{type(exc).__name__}"
                        failure_stage = "model_fit"
                if fitted is not None:
                    optimizer_converged, optimizer_warnflag = _optimizer_status(fitted)
                    try:
                        forecast_values = fitted.forecast(FORECAST_HORIZON)
                    except Exception as exc:
                        failure_reason = f"forecast:{type(exc).__name__}"
                        failure_stage = "forecast"
                    else:
                        try:
                            numeric_forecast = np.asarray(
                                forecast_values, dtype=np.float64
                            ).reshape(-1)
                        except TypeError, ValueError:
                            failure_reason = "non_numeric_forecast"
                            failure_stage = "forecast_output"
                        else:
                            if numeric_forecast.size != FORECAST_HORIZON:
                                failure_reason = "invalid_forecast_length"
                                failure_stage = "forecast_output"
                            elif not np.isfinite(numeric_forecast).all():
                                failure_reason = "non_finite_forecast"
                                failure_stage = "forecast_output"
                            else:
                                full_forecast = numeric_forecast
                warning_names = {item.category.__name__ for item in caught}
                warning_count = len(caught)

        model_success = full_forecast is not None
        if not model_success and failure_reason is None:
            failure_reason = "unusable_model_output"
            failure_stage = "forecast_output"

        diagnostic = {
            "Store": store,
            "forecast_origin": origin,
            "statistical_model": STATISTICAL_MODEL,
            "contiguous_history_start": segment_start,
            "contiguous_history_end": origin if history_rows else pd.NaT,
            "contiguous_history_rows": history_rows,
            "history_stop_reason": stop_reason,
            "training_history_start": segment_start if eligible else pd.NaT,
            "training_history_end": origin if eligible else pd.NaT,
            "training_history_rows": history_rows if eligible else 0,
            "model_fit_success": model_success,
            "fit_failure_reason": failure_reason,
            "failure_stage": failure_stage,
            "warning_count": warning_count,
            "warning_categories": "|".join(sorted(warning_names)) if warning_names else None,
            "optimizer_converged": optimizer_converged,
            "optimizer_warnflag": optimizer_warnflag,
            "forecast_was_clipped_count": (
                int(np.count_nonzero(full_forecast < 0)) if model_success else 0
            ),
            "minimum_unclipped_forecast": (float(np.min(full_forecast)) if model_success else None),
        }
        diagnostics.append(diagnostic)

        for step in range(1, FORECAST_HORIZON + 1):
            unclipped = float(full_forecast[step - 1]) if model_success else None
            clipped = max(0.0, unclipped) if unclipped is not None else None
            path_records.append(
                {
                    "Store": store,
                    "forecast_origin": origin,
                    "Date": origin + pd.Timedelta(days=step),
                    "horizon": step,
                    "statistical_model": STATISTICAL_MODEL,
                    "model_fit_success": model_success,
                    "fit_failure_reason": failure_reason,
                    "model_forecast_unclipped": unclipped,
                    FORECAST_COLUMN: clipped,
                    "forecast_was_clipped": (unclipped < 0) if unclipped is not None else None,
                    "forecast_available": unclipped is not None,
                    "training_history_start": diagnostic["training_history_start"],
                    "training_history_end": diagnostic["training_history_end"],
                    "training_history_rows": diagnostic["training_history_rows"],
                }
            )

    internal = pd.DataFrame(path_records)
    target_steps = targets.assign(
        forecast_origin=origin,
        horizon=(targets["Date"] - origin).dt.days.astype("int8"),
    )
    observed = target_steps.merge(
        internal,
        on=["Store", "forecast_origin", "Date", "horizon"],
        how="left",
        validate="one_to_one",
        sort=False,
    )
    if observed.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise AssertionError("Holt-Winters forecasts contain duplicate composite keys.")
    expected_keys = set(map(tuple, targets[["Store", "Date"]].itertuples(index=False, name=None)))
    emitted_keys = set(map(tuple, observed[["Store", "Date"]].itertuples(index=False, name=None)))
    if expected_keys != emitted_keys:
        raise AssertionError("Holt-Winters emitted keys differ from observed target keys.")
    return HoltWintersForecastResult(
        forecasts=observed.reset_index(drop=True),
        internal_forecasts=internal.reset_index(drop=True),
        diagnostics=pd.DataFrame(diagnostics).reset_index(drop=True),
    )
