"""Global LightGBM fitting, its categorical adapter, and raw recursive forecasting."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd

from rossmann_forecasting.features.contract import (
    PREDICTOR_COLUMNS,
    predictor_schema,
)
from rossmann_forecasting.features.history import OriginHistoryFeatureCache
from rossmann_forecasting.features.keys import canonicalize_store_date_keys
from rossmann_forecasting.features.pipeline import build_inference_features

MODEL_NAME = "global_lightgbm_gbdt_regression_l1"
FORECAST_COLUMN = "raw_lightgbm_forecast"
CATEGORICAL_COLUMNS = ("Store", "state_holiday", "store_type", "assortment")
REQUIRED_CATEGORICAL_COLUMNS = CATEGORICAL_COLUMNS
REQUIRED_BINARY_COLUMNS = ("school_holiday", "promo", "promo2")
REQUIRED_PREDICTOR_COLUMNS = REQUIRED_CATEGORICAL_COLUMNS + REQUIRED_BINARY_COLUMNS
SOURCE_REQUIRED_COLUMNS = {
    "Store": "Store",
    "state_holiday": "StateHoliday",
    "store_type": "StoreType",
    "assortment": "Assortment",
    "school_holiday": "SchoolHoliday",
    "promo": "Promo",
    "promo2": "Promo2",
}
FUTURE_COVARIATE_COLUMNS = (
    "Store",
    "DayOfWeek",
    "Date",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
    "StoreType",
    "Assortment",
    "CompetitionDistance",
    "CompetitionOpenSinceMonth",
    "CompetitionOpenSinceYear",
    "Promo2",
    "Promo2SinceWeek",
    "Promo2SinceYear",
    "PromoInterval",
)
FIXED_PARAMETERS: dict[str, Any] = {
    "boosting_type": "gbdt",
    "objective": "regression_l1",
    "metric": "l1",
    "device_type": "cpu",
    "num_threads": 4,
    "deterministic": True,
    "force_col_wise": True,
    "feature_fraction": 1.0,
    "bagging_fraction": 1.0,
    "bagging_freq": 0,
    "lambda_l2": 1.0,
    "max_bin": 63,
    "zero_as_missing": False,
    "verbosity": -1,
    "seed": 42,
    "data_random_seed": 42,
    "feature_fraction_seed": 42,
    "bagging_seed": 42,
}


class InvalidFeatureSchema(ValueError):
    """Raised when source predictors do not match the frozen Phase 3 contract."""


class CategoricalAdapterIncompatibility(ValueError):
    """Raised when categorical or numeric model conversion cannot follow the design."""


@dataclass(frozen=True)
class PreparedTrainingData:
    """Eligible fitting matrix and the fit-only category vocabularies."""

    features: pd.DataFrame
    labels: np.ndarray
    category_vocabularies: dict[str, tuple[Any, ...]]
    eligible_row_count: int
    origin: pd.Timestamp


@dataclass(frozen=True)
class AdaptedPredictionData:
    """Model-ready copied matrix plus row-level category diagnostics."""

    features: pd.DataFrame
    unseen_store: np.ndarray
    unseen_category_counts: dict[str, int]


@dataclass
class FittedLightGBM:
    """One booster and the categorical vocabularies learned at its fit origin."""

    booster: Any | None
    category_vocabularies: dict[str, tuple[Any, ...]]
    fit_row_count: int
    forecast_origin: pd.Timestamp
    model_parameters: dict[str, Any]
    failure_reason: str | None = None

    @property
    def category_vocabulary_hashes(self) -> dict[str, str]:
        return vocabulary_hashes(self.category_vocabularies)

    def predict_features(self, features: pd.DataFrame) -> tuple[np.ndarray, AdaptedPredictionData]:
        """Predict from a copy-converted feature matrix, preserving caller data."""

        try:
            adapted = adapt_prediction_features(features, self.category_vocabularies)
        except (CategoricalAdapterIncompatibility, InvalidFeatureSchema):
            raise
        except Exception as error:
            raise CategoricalAdapterIncompatibility(
                "Prediction feature adaptation failed."
            ) from error
        if self.booster is None:
            raise RuntimeError(self.failure_reason or "LightGBM booster is unavailable.")
        predictions = self.booster.predict(
            adapted.features,
            num_threads=int(self.model_parameters.get("num_threads", 4)),
        )
        return np.asarray(predictions, dtype=np.float64), adapted


def validate_predictor_frame(features: pd.DataFrame, *, check_dtypes: bool = True) -> None:
    """Require the exact names, order, and (when requested) Phase 3 dtypes."""

    if tuple(features.columns) != PREDICTOR_COLUMNS:
        raise InvalidFeatureSchema(
            "Predictor names/order differ from phase-3-v1: "
            f"expected {PREDICTOR_COLUMNS}, got {tuple(features.columns)}."
        )
    if check_dtypes:
        expected = predictor_schema()
        actual = {name: str(features[name].dtype) for name in PREDICTOR_COLUMNS}
        mismatches = {
            name: (expected[name], actual[name])
            for name in PREDICTOR_COLUMNS
            if not pd.api.types.is_dtype_equal(
                features[name].dtype,
                pd.api.types.pandas_dtype(expected[name]),
            )
        }
        if mismatches:
            raise InvalidFeatureSchema(f"Predictor dtypes differ from phase-3-v1: {mismatches}.")


def _required_values_missing(features: pd.DataFrame) -> pd.DataFrame:
    return features.loc[:, REQUIRED_PREDICTOR_COLUMNS].isna()


def _category_values(series: pd.Series, column: str) -> tuple[Any, ...]:
    values = series.dropna().unique().tolist()
    try:
        return tuple(sorted(values))
    except TypeError as error:
        raise CategoricalAdapterIncompatibility(
            f"{column} category values are not mutually comparable."
        ) from error


def prepare_training_data(
    training_rows: pd.DataFrame, *, forecast_origin: str | pd.Timestamp
) -> PreparedTrainingData:
    """Censor a fit at origin and learn categories from eligible labels only."""

    required = {*PREDICTOR_COLUMNS, "Date", "Sales", "Open", "training_label_eligible"}
    missing = required.difference(training_rows.columns)
    if missing:
        raise InvalidFeatureSchema(f"Training rows are missing fields: {sorted(missing)}.")
    data = training_rows.copy()
    origin = pd.Timestamp(forecast_origin).normalize()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise")
    if data["Date"].dt.normalize().ne(data["Date"]).any():
        raise InvalidFeatureSchema("Training dates must be midnight calendar dates.")
    if data["Date"].gt(origin).any():
        raise InvalidFeatureSchema("Training rows contain labels or features after the fit origin.")
    predictor_data = data.loc[:, PREDICTOR_COLUMNS]
    validate_predictor_frame(predictor_data)
    labels = pd.to_numeric(data["Sales"], errors="coerce")
    open_values = pd.to_numeric(data["Open"], errors="coerce")
    if labels.isna().any() or not np.isfinite(labels.to_numpy(dtype=np.float64)).all():
        raise InvalidFeatureSchema("Origin-censored Sales labels must be finite numeric values.")
    if labels.lt(0).any() or not open_values.dropna().isin([0, 1]).all():
        raise InvalidFeatureSchema("Training Sales/Open values violate the source label contract.")
    eligible = data["training_label_eligible"].astype("boolean")
    if eligible.isna().any():
        raise InvalidFeatureSchema("training_label_eligible cannot be null.")
    expected_eligible = open_values.eq(1) & labels.notna()
    if not eligible.astype(bool).equals(expected_eligible.astype(bool)):
        raise InvalidFeatureSchema(
            "training_label_eligible must equal observed source Open=1 with observed Sales."
        )
    fitting_features = predictor_data.loc[eligible.astype(bool)].copy()
    fitting_labels = labels.loc[eligible.astype(bool)].to_numpy(dtype=np.float64)
    missing_required = _required_values_missing(fitting_features)
    if missing_required.any().any():
        columns = missing_required.columns[missing_required.any()].tolist()
        raise InvalidFeatureSchema(
            f"Eligible training predictors contain required nulls: {columns}."
        )
    vocabularies = {
        column: _category_values(fitting_features[column], column) for column in CATEGORICAL_COLUMNS
    }
    return PreparedTrainingData(
        features=fitting_features.reset_index(drop=True),
        labels=fitting_labels,
        category_vocabularies=vocabularies,
        eligible_row_count=len(fitting_features),
        origin=origin,
    )


def _numeric_copy(series: pd.Series, column: str) -> np.ndarray:
    converted = pd.to_numeric(series, errors="coerce")
    invalid = series.notna() & converted.isna()
    if invalid.any():
        raise CategoricalAdapterIncompatibility(
            f"Numeric predictor {column} has non-numeric values."
        )
    return converted.to_numpy(dtype=np.float64, na_value=np.nan, copy=True)


def adapt_prediction_features(
    features: pd.DataFrame,
    category_vocabularies: dict[str, tuple[Any, ...]],
) -> AdaptedPredictionData:
    """Convert model inputs on copies using an origin's ordered categorical vocabularies."""

    validate_predictor_frame(features)
    if tuple(category_vocabularies) != CATEGORICAL_COLUMNS:
        raise CategoricalAdapterIncompatibility(
            "Category vocabulary fields/order differ from the Phase 6 adapter contract."
        )
    result = pd.DataFrame(index=features.index)
    unseen_store = np.zeros(len(features), dtype=bool)
    unseen_counts: dict[str, int] = {}
    for column in CATEGORICAL_COLUMNS:
        vocabulary = category_vocabularies[column]
        values = features[column].copy()
        if column == "Store":
            numeric = pd.to_numeric(values, errors="coerce")
            malformed = values.notna() & numeric.isna()
            if malformed.any() or numeric.dropna().mod(1).ne(0).any():
                raise CategoricalAdapterIncompatibility("Store must contain integer category IDs.")
            source = numeric.astype("Int64")
            known = source.isin(vocabulary) | source.isna()
            unseen_store = (~known).to_numpy(dtype=bool)
            category_values = pd.Series(source.astype(object), index=values.index)
            category_values.loc[unseen_store] = np.nan
            category_values.loc[source.isna()] = np.nan
        else:
            category_values = pd.Series(
                values.astype(pd.StringDtype(storage="python")).astype(object),
                index=values.index,
            )
            unseen = values.notna() & ~values.isin(vocabulary)
            unseen_counts[column] = int(unseen.sum())
            category_values.loc[unseen] = np.nan
        dtype = pd.CategoricalDtype(categories=list(vocabulary), ordered=False)
        try:
            result[column] = pd.Series(category_values, index=features.index).astype(dtype)
        except (TypeError, ValueError) as error:
            raise CategoricalAdapterIncompatibility(
                f"LightGBM categorical conversion failed for {column}."
            ) from error
    for column in PREDICTOR_COLUMNS:
        if column in CATEGORICAL_COLUMNS:
            continue
        result[column] = _numeric_copy(features[column], column)
    return AdaptedPredictionData(result.loc[:, PREDICTOR_COLUMNS], unseen_store, unseen_counts)


def vocabulary_hashes(vocabularies: dict[str, tuple[Any, ...]]) -> dict[str, str]:
    """Hash ordered category values without exposing them in the run manifest."""

    hashes: dict[str, str] = {}
    for column in CATEGORICAL_COLUMNS:
        payload = json.dumps(
            list(vocabularies[column]), ensure_ascii=False, separators=(",", ":"), default=str
        ).encode("utf-8")
        hashes[column] = hashlib.sha256(payload).hexdigest()
    return hashes


def make_lightgbm_dataset(prepared: PreparedTrainingData) -> lgb.Dataset:
    """Create the single eligible-label training dataset for a fit origin."""

    if prepared.eligible_row_count == 0:
        raise ValueError("No eligible fitting labels are available.")
    adapted = adapt_prediction_features(prepared.features, prepared.category_vocabularies)
    if adapted.unseen_store.any():
        raise AssertionError("A training Store cannot be outside its own fit vocabulary.")
    return lgb.Dataset(
        adapted.features,
        label=prepared.labels,
        feature_name=list(PREDICTOR_COLUMNS),
        categorical_feature=list(CATEGORICAL_COLUMNS),
        params={"max_bin": 63, "zero_as_missing": False, "feature_pre_filter": False},
        free_raw_data=False,
    )


def lightgbm_parameters(trial_parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the exact approved shared parameters plus one frozen trial recipe."""

    return {**FIXED_PARAMETERS, **(trial_parameters or {})}


def fit_lightgbm(
    prepared: PreparedTrainingData,
    *,
    num_boost_round: int,
    trial_parameters: dict[str, Any] | None = None,
    dataset: lgb.Dataset | None = None,
    init_model: lgb.Booster | None = None,
) -> FittedLightGBM:
    """Fit or continue one global CPU booster, reporting failures without fallback."""

    parameters = lightgbm_parameters(trial_parameters)
    if prepared.eligible_row_count == 0:
        return FittedLightGBM(
            None,
            prepared.category_vocabularies,
            0,
            prepared.origin,
            parameters,
            "no_eligible_training_rows",
        )
    try:
        fit_set = dataset if dataset is not None else make_lightgbm_dataset(prepared)
        booster = lgb.train(
            parameters,
            fit_set,
            num_boost_round=num_boost_round,
            init_model=init_model,
            keep_training_booster=True,
        )
    except Exception:
        return FittedLightGBM(
            None,
            prepared.category_vocabularies,
            prepared.eligible_row_count,
            prepared.origin,
            parameters,
            "model_fit_failure",
        )
    return FittedLightGBM(
        booster,
        prepared.category_vocabularies,
        prepared.eligible_row_count,
        prepared.origin,
        parameters,
    )


def _valid_future_covariates(covariates: pd.DataFrame) -> pd.DataFrame:
    missing = set(FUTURE_COVARIATE_COLUMNS).difference(covariates.columns)
    if missing:
        raise InvalidFeatureSchema(f"Future covariates are missing fields: {sorted(missing)}.")
    forbidden = [
        column
        for column in covariates.columns
        if column.casefold() in {"sales", "customers", "open", "open_resolved"}
        or "customer" in column.casefold()
        or "sales" in column.casefold()
    ]
    if forbidden:
        raise InvalidFeatureSchema(
            f"Future covariates contain forbidden outcome fields: {forbidden}."
        )
    keys = canonicalize_store_date_keys(
        covariates.loc[:, ["Store", "Date"]], name="future covariate keys"
    )
    if keys.duplicated(["Store", "Date"]).any():
        raise InvalidFeatureSchema("Future covariates contain duplicate Store × Date keys.")
    data = covariates.copy()
    data["Store"] = keys["Store"].to_numpy()
    data["Date"] = keys["Date"].to_numpy()
    return data


def _source_missing_reason(row: pd.Series) -> str | None:
    for predictor, source in SOURCE_REQUIRED_COLUMNS.items():
        if source not in row.index or pd.isna(row[source]):
            return f"missing_required_covariate:{predictor}"
    return None


def recursive_lightgbm_forecasts(
    requested_target_keys: pd.DataFrame,
    *,
    future_covariates: pd.DataFrame,
    actual_history_through_origin: pd.DataFrame,
    forecast_origin: str | pd.Timestamp,
    model: FittedLightGBM,
    forecast_horizon: int = 14,
) -> pd.DataFrame:
    """Build label-free recursive raw paths from actuals through origin and prior predictions."""

    origin = pd.Timestamp(forecast_origin).normalize()
    if not 1 <= forecast_horizon <= 14:
        raise ValueError("forecast_horizon must be between 1 and 14.")
    requested = canonicalize_store_date_keys(requested_target_keys, name="requested target keys")
    if requested.empty or requested.duplicated(["Store", "Date"]).any():
        raise InvalidFeatureSchema("Requested target keys must be non-empty and unique.")
    target_leads = (requested["Date"] - origin).dt.days
    if target_leads.lt(1).any() or target_leads.gt(forecast_horizon).any():
        raise InvalidFeatureSchema("Requested target keys fall outside the forecast horizon.")
    covariates = _valid_future_covariates(future_covariates)
    covariates = covariates.loc[
        covariates["Date"].gt(origin)
        & covariates["Date"].le(origin + pd.Timedelta(days=forecast_horizon))
    ].copy()
    actual = canonicalize_store_date_keys(
        actual_history_through_origin, name="actual_history_through_origin"
    )
    if "Sales" not in actual_history_through_origin:
        raise InvalidFeatureSchema("Actual recursive history is missing Sales.")
    actual = actual.assign(
        Sales=pd.to_numeric(actual_history_through_origin["Sales"], errors="coerce").to_numpy()
    )
    if actual["Date"].gt(origin).any():
        raise InvalidFeatureSchema("Actual history contains Sales after forecast_origin.")
    sales = pd.to_numeric(actual["Sales"], errors="coerce")
    sales_values = sales.to_numpy(dtype=np.float64)
    if sales.isna().any() or not np.isfinite(sales_values).all() or sales.lt(0).any():
        raise InvalidFeatureSchema("Actual history Sales must be finite and non-negative.")
    actual = actual.loc[:, ["Store", "Date", "Sales"]].copy()
    stores = sorted(requested["Store"].unique().tolist())
    requested_set = set(map(tuple, requested[["Store", "Date"]].itertuples(index=False, name=None)))
    covariates = covariates.loc[covariates["Store"].isin(stores)].copy()
    covariate_index = {
        (int(row.Store), row.Date): position
        for position, row in enumerate(covariates.itertuples(index=False))
    }
    covariate_rows = covariates.reset_index(drop=True)
    path_rows: list[dict[str, Any]] = []
    history_cache = OriginHistoryFeatureCache(actual, origin)

    for horizon in range(1, forecast_horizon + 1):
        target_date = origin + pd.Timedelta(days=horizon)
        date_keys = [(store, target_date) for store in stores]
        existing_positions = [covariate_index[key] for key in date_keys if key in covariate_index]
        existing_stores = {
            int(covariate_rows.at[position, "Store"]): position for position in existing_positions
        }
        current_rows = covariate_rows.iloc[existing_positions].copy().reset_index(drop=True)
        valid_positions: list[int] = []
        step_reasons: dict[int, str] = {}
        unseen_category_columns: dict[str, np.ndarray] = {}
        adapted: AdaptedPredictionData | None = None
        prediction_values: np.ndarray | None = None
        prediction_row_by_store: dict[int, int] = {}

        if model.booster is not None and model.failure_reason is None and not current_rows.empty:
            for store, position in existing_stores.items():
                reason = _source_missing_reason(covariate_rows.iloc[position])
                if reason is not None:
                    step_reasons[store] = reason
                else:
                    valid_positions.append(position)
            usable_covariates = covariate_rows.iloc[valid_positions].copy().reset_index(drop=True)
            usable_stores = usable_covariates["Store"].astype("int64").tolist()
            prediction_row_by_store = {
                store: row_position for row_position, store in enumerate(usable_stores)
            }
            if not usable_covariates.empty:
                try:
                    feature_rows, _ = build_inference_features(
                        usable_covariates.loc[:, FUTURE_COVARIATE_COLUMNS],
                        actual_history_through_origin=actual,
                        forecast_origin=origin,
                        history_cache=history_cache,
                    )
                    if tuple(feature_rows.loc[:, PREDICTOR_COLUMNS].columns) != PREDICTOR_COLUMNS:
                        raise InvalidFeatureSchema(
                            "Recursive predictor order differs from contract."
                        )
                except CategoricalAdapterIncompatibility:
                    for store in usable_stores:
                        step_reasons[store] = "categorical_adapter_incompatibility"
                except InvalidFeatureSchema:
                    for store in usable_stores:
                        step_reasons[store] = "invalid_feature_schema"
                except Exception:
                    for store in usable_stores:
                        step_reasons[store] = "recursive_state_construction_failure"
                else:
                    try:
                        predictions, adapted = model.predict_features(
                            feature_rows.loc[:, PREDICTOR_COLUMNS]
                        )
                        if len(predictions) != len(usable_covariates):
                            raise CategoricalAdapterIncompatibility(
                                "LightGBM prediction length differs from the feature rows."
                            )
                    except CategoricalAdapterIncompatibility:
                        for store in usable_stores:
                            step_reasons[store] = "categorical_adapter_incompatibility"
                    except InvalidFeatureSchema:
                        for store in usable_stores:
                            step_reasons[store] = "invalid_feature_schema"
                    except Exception:
                        for store in usable_stores:
                            step_reasons[store] = "model_fit_failure"
                    else:
                        unseen_category_columns = {
                            column: np.asarray(
                                feature_rows[column].notna()
                                & ~feature_rows[column].isin(model.category_vocabularies[column])
                            )
                            for column in ("state_holiday", "store_type", "assortment")
                        }
                        for row_idx, is_unseen_store in enumerate(adapted.unseen_store):
                            if is_unseen_store:
                                step_reasons[usable_stores[row_idx]] = "unseen_store_category"
                        prediction_values = predictions

        new_recursive_predictions: list[dict[str, Any]] = []
        for store in stores:
            key = (store, target_date)
            position = covariate_index.get(key)
            reason: str | None = None
            unclipped: float | None = None
            raw: float | None = None
            clipped: bool | None = None
            if position is None:
                reason = (
                    "missing_target_key"
                    if key in requested_set
                    else ("missing_future_covariate_row")
                )
            elif model.failure_reason is not None:
                reason = model.failure_reason
            elif model.booster is None:
                reason = "model_fit_failure"
            else:
                reason = step_reasons.get(store)
                if reason is None and prediction_values is not None:
                    if store in prediction_row_by_store:
                        row_idx = prediction_row_by_store[store]
                        output = float(prediction_values[row_idx])
                        if np.isfinite(output):
                            unclipped = output
                            raw = max(0.0, output)
                            clipped = output < 0.0
                            new_recursive_predictions.append(
                                {
                                    "Store": store,
                                    "Date": target_date,
                                    "PredictedSales": raw,
                                }
                            )
                        else:
                            reason = "non_finite_prediction"
                if reason is None and prediction_values is None:
                    reason = "recursive_state_construction_failure"
            row: dict[str, Any] = {
                "Store": store,
                "forecast_origin": origin,
                "Date": target_date,
                "horizon": horizon,
                "model": MODEL_NAME,
                "model_forecast_unclipped": unclipped,
                FORECAST_COLUMN: raw,
                "recursive_state_value": raw,
                "forecast_was_clipped": clipped,
                "forecast_available": raw is not None,
                "unavailable_reason": reason,
            }
            for column in ("state_holiday", "store_type", "assortment"):
                unseen = unseen_category_columns.get(column)
                row[f"unseen_{column}"] = bool(
                    unseen is not None
                    and store in prediction_row_by_store
                    and unseen[prediction_row_by_store[store]]
                )
            path_rows.append(row)

        if new_recursive_predictions:
            history_cache.append_predictions(pd.DataFrame(new_recursive_predictions))

    path = pd.DataFrame(path_rows)
    if path.duplicated(["Store", "forecast_origin", "Date"]).any():
        raise AssertionError("Recursive LightGBM path contains duplicate keys.")
    return path


def select_requested_raw_forecasts(
    path: pd.DataFrame, requested_target_keys: pd.DataFrame
) -> pd.DataFrame:
    """Project full internal paths onto precommitted target keys without synthesizing keys."""

    requested = canonicalize_store_date_keys(requested_target_keys, name="requested target keys")
    forecasts = path.copy()
    forecasts["Date"] = pd.to_datetime(forecasts["Date"], errors="raise").dt.normalize()
    selected = requested.merge(
        forecasts,
        on=["Store", "Date"],
        how="left",
        validate="one_to_one",
        indicator=True,
        sort=False,
    )
    missing_path = selected["_merge"].eq("left_only")
    selected.loc[missing_path, "unavailable_reason"] = "missing_target_key"
    selected.loc[missing_path, "forecast_available"] = False
    selected.loc[missing_path, "horizon"] = (
        selected.loc[missing_path, "Date"] - selected.loc[missing_path, "forecast_origin"]
    ).dt.days
    selected = selected.drop(columns="_merge")
    selected["horizon"] = pd.to_numeric(selected["horizon"], errors="coerce").astype("int8")
    return selected
