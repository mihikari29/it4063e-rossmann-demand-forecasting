"""Synthetic-only, fresh-fit H14 raw forecast issuance for Phase 13 M2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.features.contract import (
    FEATURE_CONTRACT_VERSION,
    PREDICTOR_COLUMNS,
    predictor_schema,
)
from rossmann_forecasting.features.pipeline import build_training_features
from rossmann_forecasting.forecasting.lightgbm import (
    CATEGORICAL_COLUMNS,
    FIXED_PARAMETERS,
    FORECAST_COLUMN,
    FittedLightGBM,
    fit_lightgbm,
    make_lightgbm_dataset,
    prepare_training_data,
    recursive_lightgbm_forecasts,
    select_requested_raw_forecasts,
    vocabulary_hashes,
)
from rossmann_forecasting.forecasting.lightgbm_evaluation import TRIAL_PARAMETERS
from rossmann_forecasting.forecasting.model_selection import CANDIDATE_IDS, build_refit_recipe
from rossmann_forecasting.phase13.contracts import (
    ForecastOrigin,
    FutureCovariates,
    OriginCensoredTrainingInputs,
    RecursiveHistoryInputs,
    RequestedForecastGrid,
)
from rossmann_forecasting.phase13.providers import SyntheticInputProvider

NUM_BOOST_ROUND = 180
SAVE_LOAD_RTOL = 1e-12
SAVE_LOAD_ATOL = 1e-9


class Phase13IssuanceError(ValueError):
    """Raised when a synthetic Phase 13 issuance contract does not hold."""


class ModelOriginMismatchError(Phase13IssuanceError):
    """Raised before prediction when a fresh fit belongs to a different origin."""


@dataclass(frozen=True, slots=True)
class TrainingRowCounts:
    """Auditable counts for label validity, history, and eligible model fitting."""

    input_rows: int
    valid_observed_label_rows: int
    missing_label_excluded_rows: int
    observed_closed_history_rows: int
    eligible_source_open_rows: int
    fitted_eligible_rows: int


@dataclass(frozen=True, slots=True)
class RawForecastIssuance:
    """Label-free in-memory H14 result; this is not a durable publication record."""

    origin: date
    grid_identity: str
    recipe_identity: str
    feature_schema_identity: str
    fit_identity: str
    model_identity: str
    model_name: str
    requested_key_count: int
    available_row_count: int
    unavailable_row_count: int
    all_requested_keys_accounted: bool
    complete_path_available: bool
    requested_boost_rounds: int
    actual_tree_count: int | None
    training_counts: TrainingRowCounts
    input_identities: tuple[tuple[str, str], ...]
    category_vocabulary_hashes: tuple[tuple[str, str], ...]
    _records: pd.DataFrame

    def __post_init__(self) -> None:
        records = self._records.copy(deep=True)
        forbidden = [
            column
            for column in records.columns
            if column.casefold() in {"sales", "open", "customers", "open_resolved"}
            or "customer" in column.casefold()
            or column.casefold().startswith("actual_")
        ]
        if forbidden:
            raise Phase13IssuanceError(
                f"Raw issuance records contain forbidden outcome fields: {forbidden}."
            )
        required = {
            "requested_key",
            "Store",
            "Date",
            "forecast_origin",
            "horizon",
            "model_identity",
            "raw_forecast",
            "unclipped_forecast",
            "forecast_was_clipped",
            "recursive_state_value",
            "forecast_available",
            "unavailable_reason",
            "unseen_store_category",
            "unseen_state_holiday",
            "unseen_store_type",
            "unseen_assortment",
            "training_input_identity",
            "recursive_history_identity",
            "future_covariate_identity",
            "fit_identity",
        }
        missing = required.difference(records.columns)
        if missing:
            raise Phase13IssuanceError(
                f"Raw issuance records are missing fields: {sorted(missing)}."
            )
        if records.duplicated(["Store", "Date"]).any():
            raise Phase13IssuanceError("Raw issuance records contain duplicate requested keys.")
        records.reset_index(drop=True, inplace=True)
        object.__setattr__(self, "_records", records)

    def to_frame(self) -> pd.DataFrame:
        """Return an independent, label-free copy of the in-memory records."""

        return self._records.copy(deep=True)


def _identity(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _schema_identity() -> str:
    return _identity(
        {
            "version": FEATURE_CONTRACT_VERSION,
            "ordered_columns": PREDICTOR_COLUMNS,
            "schema": predictor_schema(),
        }
    )


def _frozen_recipe() -> dict[str, Any]:
    trial_parameters = dict(TRIAL_PARAMETERS["A"])
    configuration = {
        "selected_trial": "A",
        "selected_boosting_rounds": NUM_BOOST_ROUND,
        "trial_parameters": trial_parameters,
        "predictor_columns": list(PREDICTOR_COLUMNS),
        "shared_parameters": dict(FIXED_PARAMETERS),
    }
    recipe = build_refit_recipe(CANDIDATE_IDS[2], configuration)
    expected_trial = {
        "learning_rate": 0.05,
        "num_leaves": 15,
        "max_depth": 4,
        "min_data_in_leaf": 200,
    }
    if (
        trial_parameters != expected_trial
        or recipe.get("selected_trial") != "A"
        or recipe.get("selected_boosting_rounds") != NUM_BOOST_ROUND
        or recipe.get("trial_parameters") != expected_trial
        or recipe.get("shared_parameters") != FIXED_PARAMETERS
        or recipe.get("dataset_parameters")
        != {"max_bin": 63, "zero_as_missing": False, "feature_pre_filter": False}
        or tuple(recipe.get("predictor_contract_identity", {}).get("ordered_columns", ()))
        != PREDICTOR_COLUMNS
    ):
        raise Phase13IssuanceError("Frozen Phase 7 LightGBM Trial A recipe identity changed.")
    return recipe


def _validate_inputs(
    grid: RequestedForecastGrid,
    training_input: OriginCensoredTrainingInputs,
    recursive_history: RecursiveHistoryInputs,
    future_covariates: FutureCovariates,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, TrainingRowCounts]:
    origin = grid.origin
    if (
        training_input.origin != origin
        or recursive_history.origin != origin
        or future_covariates.origin != origin
        or future_covariates.grid_identity != grid.identity
        or training_input.store_ids != grid.store_ids
        or recursive_history.store_ids != grid.store_ids
        or future_covariates.store_ids != grid.store_ids
    ):
        raise Phase13IssuanceError("Provider input origins or Store grids do not match issuance.")

    training = training_input.to_frame()
    history = recursive_history.to_frame()
    covariates = future_covariates.to_frame()
    if pd.to_datetime(training["Date"], errors="raise").gt(pd.Timestamp(origin.value)).any():
        raise Phase13IssuanceError("Training labels or observed Open exceed the fit origin.")
    if pd.to_datetime(history["Date"], errors="raise").gt(pd.Timestamp(origin.value)).any():
        raise Phase13IssuanceError("Recursive actual history exceeds the fit origin.")
    if not set(covariates.columns).isdisjoint({"Sales", "Open", "Customers", "Open_resolved"}):
        raise Phase13IssuanceError("Future covariates include a forbidden outcome or Open field.")

    labels = pd.to_numeric(training["Sales"], errors="coerce")
    malformed_labels = training["Sales"].notna() & labels.isna()
    label_values = labels.to_numpy(dtype=np.float64, na_value=np.nan)
    if malformed_labels.any() or (~np.isfinite(label_values) & ~labels.isna().to_numpy()).any():
        raise Phase13IssuanceError("Training labels must be finite or genuinely missing.")
    if labels.dropna().lt(0).any():
        raise Phase13IssuanceError("Training labels cannot be negative.")

    open_values = pd.to_numeric(training["Open"], errors="coerce")
    malformed_open = training["Open"].notna() & open_values.isna()
    if malformed_open.any() or not open_values.dropna().isin([0, 1]).all():
        raise Phase13IssuanceError("Observed training Open must be 0, 1, or missing.")
    eligible = training["training_label_eligible"].astype("boolean")
    expected_eligible = open_values.eq(1).fillna(False) & labels.notna()
    if eligible.isna().any() or not np.array_equal(
        eligible.to_numpy(dtype=bool), expected_eligible.to_numpy(dtype=bool)
    ):
        raise Phase13IssuanceError(
            "Eligible training rows must equal observed source Open=1 with valid Sales."
        )

    valid_mask = labels.notna()
    valid_rows = training.loc[valid_mask].copy()
    valid_rows["Sales"] = labels.loc[valid_mask].to_numpy(dtype=np.float64)
    # Nullable source Open remains missing; a float array lets the approved builder test `== 1`.
    valid_rows["Open"] = open_values.loc[valid_mask].to_numpy(dtype=np.float64, na_value=np.nan)
    closed = open_values.eq(0).fillna(False)
    counts = TrainingRowCounts(
        input_rows=len(training),
        valid_observed_label_rows=int(valid_mask.sum()),
        missing_label_excluded_rows=int((~valid_mask).sum()),
        observed_closed_history_rows=int((valid_mask & closed).sum()),
        eligible_source_open_rows=int(expected_eligible.sum()),
        fitted_eligible_rows=0,
    )
    return valid_rows, history, covariates, counts


def _model_and_fit_identities(
    fitted: FittedLightGBM,
    *,
    recipe_identity: str,
    schema_identity: str,
    origin: ForecastOrigin,
    input_identities: tuple[tuple[str, str], ...],
    category_hashes: dict[str, str],
    actual_tree_count: int | None,
) -> tuple[str, str]:
    booster_hash = None
    if fitted.booster is not None:
        booster_hash = hashlib.sha256(fitted.booster.model_to_string().encode("utf-8")).hexdigest()
    model_identity = _identity(
        {
            "model": CANDIDATE_IDS[2],
            "origin": origin.value.isoformat(),
            "recipe_identity": recipe_identity,
            "feature_schema_identity": schema_identity,
            "category_vocabulary_hashes": category_hashes,
            "booster_sha256": booster_hash,
            "failure_reason": fitted.failure_reason,
        }
    )
    fit_identity = _identity(
        {
            "model_identity": model_identity,
            "input_identities": input_identities,
            "fit_row_count": fitted.fit_row_count,
            "actual_tree_count": actual_tree_count,
        }
    )
    return model_identity, fit_identity


def _records(
    selected: pd.DataFrame,
    *,
    grid: RequestedForecastGrid,
    model_identity: str,
    fit_identity: str,
    recipe_identity: str,
    schema_identity: str,
    input_identities: tuple[tuple[str, str], ...],
) -> pd.DataFrame:
    identity_map = dict(input_identities)
    result = selected.loc[
        :,
        [
            "Store",
            "Date",
            "forecast_origin",
            "horizon",
            "model",
            "model_forecast_unclipped",
            FORECAST_COLUMN,
            "recursive_state_value",
            "forecast_was_clipped",
            "forecast_available",
            "unavailable_reason",
            "unseen_state_holiday",
            "unseen_store_type",
            "unseen_assortment",
        ],
    ].copy()
    result.insert(
        0,
        "requested_key",
        [
            f"{int(store)}:{pd.Timestamp(day).date().isoformat()}"
            for store, day in result[["Store", "Date"]].itertuples(index=False, name=None)
        ],
    )
    result.rename(
        columns={
            "model_forecast_unclipped": "unclipped_forecast",
            FORECAST_COLUMN: "raw_forecast",
        },
        inplace=True,
    )
    result["unseen_store_category"] = result["unavailable_reason"].eq("unseen_store_category")
    result["model_identity"] = model_identity
    result["fit_identity"] = fit_identity
    result["recipe_identity"] = recipe_identity
    result["feature_schema_identity"] = schema_identity
    result["requested_grid_identity"] = grid.identity
    result["training_input_identity"] = identity_map["training"]
    result["recursive_history_identity"] = identity_map["recursive_history"]
    result["future_covariate_identity"] = identity_map["future_covariates"]

    available = result["forecast_available"].astype("boolean")
    if available.isna().any():
        raise Phase13IssuanceError(
            "Forecast availability must be explicit for every requested key."
        )
    available = available.astype(bool)
    numeric_columns = ["raw_forecast", "unclipped_forecast", "recursive_state_value"]
    if result.loc[available, numeric_columns].isna().any().any():
        raise Phase13IssuanceError("Available forecasts must have all three numeric values.")
    if result.loc[~available, numeric_columns].notna().any().any():
        raise Phase13IssuanceError("Unavailable forecasts cannot carry invented numeric values.")
    raw_values = pd.to_numeric(result.loc[available, "raw_forecast"], errors="coerce")
    if not np.isfinite(raw_values.to_numpy(dtype=np.float64)).all() or raw_values.lt(0).any():
        raise Phase13IssuanceError("Available raw forecasts must be finite and non-negative.")
    if result.loc[available, "unavailable_reason"].notna().any():
        raise Phase13IssuanceError("Available forecasts cannot carry an unavailable reason.")
    if result.loc[~available, "unavailable_reason"].isna().any():
        raise Phase13IssuanceError("Unavailable forecasts require an explicit reason.")
    result["forecast_available"] = available
    clipped = result["forecast_was_clipped"].astype("boolean")
    if clipped.loc[available].isna().any():
        raise Phase13IssuanceError("Available forecasts require an explicit clipping flag.")
    if clipped.loc[~available].notna().any():
        raise Phase13IssuanceError("Unavailable forecasts cannot claim a clipping result.")
    result["forecast_was_clipped"] = clipped
    for column in (
        "unseen_store_category",
        "unseen_state_holiday",
        "unseen_store_type",
        "unseen_assortment",
    ):
        result[column] = result[column].astype("boolean")
        if result[column].isna().any():
            raise Phase13IssuanceError(f"{column} must be explicit for every requested key.")
        result[column] = result[column].astype(bool)

    result["Store"] = pd.to_numeric(result["Store"], errors="raise").astype("int64")
    result["Date"] = pd.to_datetime(result["Date"], errors="raise").dt.normalize()
    requested = grid.to_frame()
    grid.validate_complete_keys(result.loc[:, ["Store", "Date"]], name="raw issuance keys")
    actual_keys = tuple(
        (int(store), pd.Timestamp(day).normalize())
        for store, day in result[["Store", "Date"]].itertuples(index=False, name=None)
    )
    expected_keys = tuple(
        (int(store), pd.Timestamp(day).normalize())
        for store, day in requested[["Store", "Date"]].itertuples(index=False, name=None)
    )
    if actual_keys != expected_keys:
        raise Phase13IssuanceError("Raw issuance changed the requested Store × Date order.")
    expected_dates = tuple(pd.Timestamp(day) for day in grid.dates)
    if set(pd.to_datetime(result["Date"])) != set(expected_dates):
        raise Phase13IssuanceError("Raw issuance did not preserve exactly the H14 dates.")
    return result


class Phase13FreshFitIssuer:
    """Fit frozen LightGBM Trial A and issue one synthetic-only Phase 13 H14 raw path."""

    def issue(self, provider: SyntheticInputProvider) -> RawForecastIssuance:
        if not isinstance(provider, SyntheticInputProvider):
            raise Phase13IssuanceError(
                "M2 issuance accepts only the typed synthetic Phase 13 input provider."
            )
        grid = provider.grid
        if not isinstance(grid, RequestedForecastGrid):
            raise Phase13IssuanceError("Synthetic provider is not bound to a typed H14 grid.")
        origin = grid.origin
        training_input = provider.read_training_inputs(origin=origin)
        recursive_history = provider.read_recursive_history_inputs(origin=origin)
        future_covariates = provider.read_future_covariates(origin=origin)
        if not (
            isinstance(training_input, OriginCensoredTrainingInputs)
            and isinstance(recursive_history, RecursiveHistoryInputs)
            and isinstance(future_covariates, FutureCovariates)
        ):
            raise Phase13IssuanceError("Synthetic provider returned an untyped issuance input.")

        valid_training_rows, history, covariates, counts = _validate_inputs(
            grid, training_input, recursive_history, future_covariates
        )
        training_features, _ = build_training_features(valid_training_rows)
        prepared = prepare_training_data(training_features, forecast_origin=origin.value)
        counts = TrainingRowCounts(
            input_rows=counts.input_rows,
            valid_observed_label_rows=counts.valid_observed_label_rows,
            missing_label_excluded_rows=counts.missing_label_excluded_rows,
            observed_closed_history_rows=counts.observed_closed_history_rows,
            eligible_source_open_rows=counts.eligible_source_open_rows,
            fitted_eligible_rows=prepared.eligible_row_count,
        )
        if prepared.origin != pd.Timestamp(origin.value):
            raise Phase13IssuanceError("Prepared training origin differs from the issuer origin.")
        if prepared.eligible_row_count != counts.eligible_source_open_rows:
            raise Phase13IssuanceError("Fitted eligible-row count differs from the input contract.")

        recipe = _frozen_recipe()
        recipe_identity = _identity(recipe)
        schema_identity = _schema_identity()
        dataset = make_lightgbm_dataset(prepared) if prepared.eligible_row_count > 0 else None
        fitted = fit_lightgbm(
            prepared,
            num_boost_round=NUM_BOOST_ROUND,
            trial_parameters=dict(TRIAL_PARAMETERS["A"]),
            dataset=dataset,
            init_model=None,
        )
        expected_parameters = {**FIXED_PARAMETERS, **TRIAL_PARAMETERS["A"]}
        if fitted.model_parameters != expected_parameters:
            raise Phase13IssuanceError("Fitted LightGBM parameters differ from frozen Trial A.")
        if fitted.fit_row_count != prepared.eligible_row_count:
            raise Phase13IssuanceError("Fitted row count differs from eligible prepared labels.")
        fitted_origin = pd.Timestamp(fitted.forecast_origin)
        if fitted_origin.tz is not None or fitted_origin != fitted_origin.normalize():
            raise ModelOriginMismatchError("Fitted model origin is not a midnight calendar date.")
        if fitted_origin != pd.Timestamp(origin.value):
            raise ModelOriginMismatchError(
                f"Fitted model origin {fitted_origin.date()} differs from issuer origin "
                f"{origin.value}."
            )

        actual_tree_count: int | None = None
        if fitted.booster is not None and fitted.failure_reason is None:
            iterations = int(fitted.booster.current_iteration())
            actual_tree_count = int(fitted.booster.num_trees())
            if iterations != NUM_BOOST_ROUND or actual_tree_count != NUM_BOOST_ROUND:
                raise Phase13IssuanceError(
                    "Fitted booster tree count differs from the frozen 180-round recipe."
                )
        if tuple(fitted.category_vocabularies) != CATEGORICAL_COLUMNS:
            raise Phase13IssuanceError("Fit category vocabulary schema differs from Phase 6.")
        eligible_features = training_features.loc[
            training_features["training_label_eligible"].astype(bool)
        ]
        expected_vocabularies = {
            column: tuple(sorted(eligible_features[column].dropna().unique().tolist()))
            for column in CATEGORICAL_COLUMNS
        }
        if prepared.category_vocabularies != expected_vocabularies:
            raise Phase13IssuanceError(
                "Fit category vocabulary does not match eligible origin training rows."
            )
        if prepared.category_vocabularies != fitted.category_vocabularies:
            raise Phase13IssuanceError("Fit category adapter state changed after fitting.")
        category_hash_map = vocabulary_hashes(fitted.category_vocabularies)
        input_identities = (
            ("requested_grid", grid.identity),
            ("training", training_input.identity),
            ("recursive_history", recursive_history.identity),
            ("future_covariates", future_covariates.identity),
        )
        model_identity, fit_identity = _model_and_fit_identities(
            fitted,
            recipe_identity=recipe_identity,
            schema_identity=schema_identity,
            origin=origin,
            input_identities=input_identities,
            category_hashes=category_hash_map,
            actual_tree_count=actual_tree_count,
        )

        # Guard the origin explicitly; the existing recursive API does not check model identity.
        if pd.Timestamp(fitted.forecast_origin) != pd.Timestamp(origin.value):
            raise ModelOriginMismatchError("Fitted model origin differs from raw issuance origin.")
        recursive_path = recursive_lightgbm_forecasts(
            grid.to_frame(),
            future_covariates=covariates,
            actual_history_through_origin=history,
            forecast_origin=origin.value,
            model=fitted,
            forecast_horizon=14,
        )
        selected = select_requested_raw_forecasts(recursive_path, grid.to_frame())
        records = _records(
            selected,
            grid=grid,
            model_identity=model_identity,
            fit_identity=fit_identity,
            recipe_identity=recipe_identity,
            schema_identity=schema_identity,
            input_identities=input_identities,
        )
        available_count = int(records["forecast_available"].sum())
        unavailable_count = len(records) - available_count
        accounted = len(records) == grid.requested_key_count
        complete = accounted and available_count == grid.requested_key_count
        if not accounted:
            raise Phase13IssuanceError("Raw issuance failed to account for every requested key.")
        return RawForecastIssuance(
            origin=origin.value,
            grid_identity=grid.identity,
            recipe_identity=recipe_identity,
            feature_schema_identity=schema_identity,
            fit_identity=fit_identity,
            model_identity=model_identity,
            model_name=CANDIDATE_IDS[2],
            requested_key_count=grid.requested_key_count,
            available_row_count=available_count,
            unavailable_row_count=unavailable_count,
            all_requested_keys_accounted=accounted,
            complete_path_available=complete,
            requested_boost_rounds=NUM_BOOST_ROUND,
            actual_tree_count=actual_tree_count,
            training_counts=counts,
            input_identities=input_identities,
            category_vocabulary_hashes=tuple(category_hash_map.items()),
            _records=records,
        )


__all__ = [
    "NUM_BOOST_ROUND",
    "SAVE_LOAD_ATOL",
    "SAVE_LOAD_RTOL",
    "ModelOriginMismatchError",
    "Phase13FreshFitIssuer",
    "Phase13IssuanceError",
    "RawForecastIssuance",
    "TrainingRowCounts",
]
