"""Shared assembly of static predictors and role-specific train/inference artifacts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.features.calendar import build_calendar_features, normalize_dates
from rossmann_forecasting.features.competition import build_competition_features
from rossmann_forecasting.features.contract import (
    PREDICTOR_COLUMNS,
    PREDICTOR_DTYPES,
    STATIC_PREDICTOR_COLUMNS,
)
from rossmann_forecasting.features.history import (
    build_historical_history_features,
    build_origin_history_features,
)
from rossmann_forecasting.features.promotion import build_promotion_features

_STORE_FIELDS = ("StoreType", "Assortment", "CompetitionDistance")
_OPEN_RESOLUTION_FIELDS = (
    "Open_resolved",
    "Open_resolution_method",
    "historical_match_rows",
    "historical_open_rate",
    "resolution_uncertain",
)


def _validate_store_ids(rows: pd.DataFrame) -> pd.Series:
    if "Store" not in rows:
        raise ValueError("Feature rows must include Store.")
    values = pd.to_numeric(rows["Store"], errors="coerce")
    if values.isna().any() or values.mod(1).ne(0).any():
        raise ValueError("Store must be a non-missing integer identity.")
    if values.lt(1).any() or values.gt(np.iinfo(np.int64).max).any():
        raise ValueError("Store is outside the supported positive int64 identity range.")
    return values.astype("int64")


def _static_store_value(rows: pd.DataFrame, column: str) -> pd.Series:
    if column not in rows:
        raise ValueError(f"Static predictor source {column} is missing.")
    values = rows[column]
    numeric = pd.to_numeric(values, errors="coerce")
    malformed = values.notna() & numeric.isna()
    if malformed.any() or numeric.lt(0).any():
        raise ValueError(f"{column} contains invalid negative or non-numeric values.")
    return numeric.astype("float64")


def _cast_predictors(frame: pd.DataFrame) -> pd.DataFrame:
    if tuple(frame.columns) != PREDICTOR_COLUMNS:
        raise AssertionError(
            f"Predictor column order differs from contract: {tuple(frame.columns)}"
        )
    result = frame.copy()
    for column, dtype in PREDICTOR_DTYPES.items():
        result[column] = result[column].astype(dtype)
    return result


def build_static_predictors(rows: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Build Store identity, calendar, holiday/promotion, store, and competition predictors."""

    if rows[["Store", "Date"]].isna().any(axis=None):
        raise ValueError("Feature rows contain missing Store × Date keys.")
    if rows.duplicated(["Store", "Date"]).any():
        raise ValueError("Feature rows contain duplicate Store × Date keys.")

    store = _validate_store_ids(rows)
    calendar = build_calendar_features(rows)
    promotion, promotion_findings = build_promotion_features(rows)
    competition, competition_findings = build_competition_features(rows)

    for field in ("StoreType", "Assortment"):
        if field not in rows or rows[field].isna().any():
            raise ValueError(f"{field} must be present and non-missing for every feature row.")
    store_features = pd.DataFrame(
        {
            "Store": store,
            "store_type": rows["StoreType"].astype("string"),
            "assortment": rows["Assortment"].astype("string"),
            "competition_distance": _static_store_value(rows, "CompetitionDistance"),
        },
        index=rows.index,
    )
    static = pd.concat(
        [
            store_features[["Store"]],
            calendar,
            promotion,
            store_features[["store_type", "assortment", "competition_distance"]],
            competition,
        ],
        axis=1,
    )
    static = static.loc[:, STATIC_PREDICTOR_COLUMNS]
    static = static.astype(
        {column: PREDICTOR_DTYPES[column] for column in STATIC_PREDICTOR_COLUMNS}
    )
    return static, promotion_findings + competition_findings


def _assemble_predictors(
    rows: pd.DataFrame,
    *,
    history_features: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    static, findings = build_static_predictors(rows)
    if not static.index.equals(history_features.index):
        raise ValueError("Static and dynamic feature rows do not align by input index.")
    features = pd.concat([static, history_features], axis=1)
    features = features.loc[:, PREDICTOR_COLUMNS]
    return _cast_predictors(features), findings


def build_training_features(train: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Build one-step historical train features with labels and eligibility sidecars."""

    required = {"Sales", "Open", "Store", "Date"}
    if not required.issubset(train.columns):
        raise ValueError(
            f"Training rows are missing required fields: {sorted(required - set(train))}"
        )
    if not pd.api.types.is_numeric_dtype(train["Sales"]):
        raise ValueError("Training Sales labels must be numeric.")
    sales = pd.to_numeric(train["Sales"], errors="coerce")
    if sales.isna().any() or not np.isfinite(sales).all() or sales.lt(0).any():
        raise ValueError("Training Sales labels must be finite and non-negative.")

    history_features = build_historical_history_features(train, train)
    predictors, findings = _assemble_predictors(train, history_features=history_features)
    output = predictors.copy()
    output["Date"] = normalize_dates(train["Date"])
    output["Sales"] = train["Sales"].to_numpy(copy=True)
    output["Open"] = train["Open"].to_numpy(copy=True)
    eligible = train["Open"].eq(1) & train["Sales"].notna()
    output["training_label_eligible"] = eligible.to_numpy(dtype=bool)
    output["primary_evaluation_eligible"] = eligible.to_numpy(dtype=bool)
    output["row_role"] = pd.Series("train", index=output.index, dtype="string")
    sidecars = [
        "Date",
        "Sales",
        "Open",
        "training_label_eligible",
        "primary_evaluation_eligible",
        "row_role",
    ]
    return output.loc[:, [*PREDICTOR_COLUMNS, *sidecars]], findings


def _append_open_resolution(
    output: pd.DataFrame,
    target_rows: pd.DataFrame,
    open_resolution: pd.DataFrame | None,
) -> pd.DataFrame:
    if open_resolution is None:
        return output
    required = {"Store", "Date", *_OPEN_RESOLUTION_FIELDS}
    missing = sorted(required.difference(open_resolution.columns))
    if missing:
        raise ValueError(f"Open resolution audit is missing columns: {missing}")
    keys = ["Store", "Date"]
    if open_resolution.duplicated(keys).any():
        raise ValueError("Open resolution audit contains duplicate Store × Date keys.")
    left_keys = target_rows[keys].reset_index(drop=True)
    right = open_resolution[[*keys, *_OPEN_RESOLUTION_FIELDS]]
    merged = left_keys.merge(right, on=keys, how="left", validate="one_to_one", sort=False)
    if not left_keys.equals(merged[keys]):
        raise AssertionError("Open resolution join changed inference key order.")
    if merged["Open_resolution_method"].isna().any():
        raise ValueError("Open resolution audit does not cover every inference Store × Date key.")
    result = output.copy()
    for column in _OPEN_RESOLUTION_FIELDS:
        result[column] = merged[column].array
    return result


def build_inference_features(
    inference_rows: pd.DataFrame,
    *,
    actual_history_through_origin: pd.DataFrame,
    forecast_origin: str | pd.Timestamp,
    prior_recursive_predictions: pd.DataFrame | None = None,
    open_resolution: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Build inference predictors, rejecting any Sales/Customers-derived source inputs."""

    forbidden = [
        column
        for column in inference_rows.columns
        if "sales" in column.casefold() or "customer" in column.casefold()
    ]
    if forbidden:
        raise ValueError(
            f"Inference rows contain forbidden Sales/Customers-derived fields: {forbidden}"
        )
    history_features = build_origin_history_features(
        inference_rows,
        actual_history_through_origin=actual_history_through_origin,
        forecast_origin=forecast_origin,
        prior_recursive_predictions=prior_recursive_predictions,
    )
    predictors, findings = _assemble_predictors(inference_rows, history_features=history_features)
    output = predictors.copy()
    output["Date"] = normalize_dates(inference_rows["Date"])
    if "Open" in inference_rows:
        output["Open"] = inference_rows["Open"].to_numpy(copy=True)
    if "Id" in inference_rows:
        output["Id"] = inference_rows["Id"].to_numpy(copy=True)
    output = _append_open_resolution(output, inference_rows, open_resolution)
    output["row_role"] = pd.Series("inference", index=output.index, dtype="string")
    audit_columns = [
        column
        for column in ("Open", "Id", *_OPEN_RESOLUTION_FIELDS, "row_role")
        if column in output
    ]
    return output.loc[:, [*PREDICTOR_COLUMNS, "Date", *audit_columns]], findings


def build_feature_tables(
    train: pd.DataFrame,
    inference_rows: pd.DataFrame,
    *,
    open_resolution: pd.DataFrame | None = None,
    forecast_origin: str | pd.Timestamp | None = None,
    prior_recursive_predictions: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Build separate train/inference artifacts using a shared predictor contract."""

    train_features, train_findings = build_training_features(train)
    origin = (
        normalize_dates(train["Date"], name="Training Date").max()
        if forecast_origin is None
        else normalize_dates(pd.Series([forecast_origin]), name="forecast_origin").iloc[0]
    )
    actual_history = train.loc[
        normalize_dates(train["Date"]).le(origin), ["Store", "Date", "Sales"]
    ]
    inference_features, inference_findings = build_inference_features(
        inference_rows,
        actual_history_through_origin=actual_history,
        forecast_origin=origin,
        prior_recursive_predictions=prior_recursive_predictions,
        open_resolution=open_resolution,
    )
    if (
        tuple(column for column in train_features if column in PREDICTOR_COLUMNS)
        != PREDICTOR_COLUMNS
    ):
        raise AssertionError("Training predictor schema does not match the feature contract.")
    if (
        tuple(column for column in inference_features if column in PREDICTOR_COLUMNS)
        != PREDICTOR_COLUMNS
    ):
        raise AssertionError("Inference predictor schema does not match the feature contract.")
    for column in PREDICTOR_COLUMNS:
        if train_features[column].dtype != inference_features[column].dtype:
            raise AssertionError(f"Train/inference dtype mismatch for predictor {column}.")
    return train_features, inference_features, train_findings + inference_findings
