"""Validated, copy-safe input contracts for the synthetic Phase 13 rehearsal boundary."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.features.keys import canonicalize_store_date_keys
from rossmann_forecasting.forecasting.lightgbm import FUTURE_COVARIATE_COLUMNS

STORE_ROSTER = tuple(range(1, 1116))
SUPPORTED_ORIGINS = (date(2015, 7, 3), date(2015, 7, 17))
BLOCK1_DATES = tuple(date(2015, 7, 4) + timedelta(days=lead) for lead in range(14))
BLOCK2_DATES = tuple(date(2015, 7, 18) + timedelta(days=lead) for lead in range(14))
PROTECTED_DATES = BLOCK1_DATES + BLOCK2_DATES
HORIZON = 14

TRAINING_INPUT_COLUMNS = (*FUTURE_COVARIATE_COLUMNS, "Sales", "Open", "training_label_eligible")
RECURSIVE_HISTORY_COLUMNS = ("Store", "Date", "Sales")
PLANNED_OPEN_COLUMNS = ("Store", "Date", "planned_open")
OUTCOME_PROJECTION_COLUMNS = ("Store", "Date", "Sales", "Open")
SYNTHETIC_OPEN_RULE_ID = "synthetic_mon_sat_open_sun_closed_v1"


class Phase13InputError(ValueError):
    """Raised when a Phase 13 synthetic input violates its declared contract."""


class AvailabilityAssumption(StrEnum):
    OBSERVED_THROUGH_ORIGIN = "observed_through_origin"
    RETROSPECTIVELY_ASSUMED_KNOWN = "retrospectively_assumed_known_at_origin"
    SYNTHETIC_RULE = "synthetic_deterministic_rule"


def _calendar_date(value: object, *, name: str) -> date:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            raise Phase13InputError(f"{name} must be a timezone-naive calendar date.")
        timestamp = pd.Timestamp(value)
    elif isinstance(value, date):
        timestamp = pd.Timestamp(value)
    else:
        try:
            timestamp = pd.Timestamp(value)
        except (TypeError, ValueError) as error:
            raise Phase13InputError(f"{name} must be a valid calendar date.") from error
    if pd.isna(timestamp) or timestamp.tz is not None or timestamp != timestamp.normalize():
        raise Phase13InputError(f"{name} must be a timezone-naive midnight calendar date.")
    return timestamp.date()


def _normalize_store_ids(values: object) -> tuple[int, ...]:
    try:
        stores = tuple(values)
    except TypeError as error:
        raise Phase13InputError("Store IDs must be an iterable roster allowlist.") from error
    if not stores:
        raise Phase13InputError("Store ID allowlist must not be empty.")
    if any(
        isinstance(store, (bool, np.bool_)) or not isinstance(store, (int, np.integer))
        for store in stores
    ):
        raise Phase13InputError("Store IDs must be integer members of the fixed roster.")
    normalized = tuple(int(store) for store in stores)
    if any(store not in STORE_ROSTER for store in normalized):
        raise Phase13InputError("Store IDs must belong to the fixed 1..1115 roster.")
    if normalized != tuple(sorted(set(normalized))):
        raise Phase13InputError("Store ID allowlist must be unique and ascending.")
    return normalized


def _require_provenance(provenance: SourceProvenance, *, name: str) -> SourceProvenance:
    if not isinstance(provenance, SourceProvenance):
        raise Phase13InputError(f"{name} requires typed source provenance.")
    return provenance


@dataclass(frozen=True, slots=True)
class ForecastOrigin:
    """One of the two precommitted Phase 13 forecast origins."""

    value: date

    def __post_init__(self) -> None:
        normalized = _calendar_date(self.value, name="forecast origin")
        if normalized not in SUPPORTED_ORIGINS:
            raise Phase13InputError(f"Unsupported Phase 13 forecast origin: {normalized}.")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def parse(cls, value: ForecastOrigin | date | str | pd.Timestamp) -> ForecastOrigin:
        if isinstance(value, cls):
            return value
        return cls(_calendar_date(value, name="forecast origin"))

    @property
    def target_dates(self) -> tuple[date, ...]:
        return tuple(self.value + timedelta(days=lead) for lead in range(1, HORIZON + 1))


@dataclass(frozen=True, slots=True)
class RequestedForecastGrid:
    """A complete H14 Store × Date request, independent of outcome availability."""

    origin: ForecastOrigin | date | str | pd.Timestamp
    store_ids: tuple[int, ...] = STORE_ROSTER

    def __post_init__(self) -> None:
        origin = ForecastOrigin.parse(self.origin)
        normalized = _normalize_store_ids(self.store_ids)
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "store_ids", normalized)

    @property
    def dates(self) -> tuple[date, ...]:
        return self.origin.target_dates

    @property
    def keys(self) -> tuple[tuple[int, date], ...]:
        return tuple((store, day) for store in self.store_ids for day in self.dates)

    @property
    def requested_key_count(self) -> int:
        return len(self.store_ids) * HORIZON

    @property
    def is_full_roster(self) -> bool:
        return self.store_ids == STORE_ROSTER

    @property
    def identity(self) -> str:
        return _hash_payload(
            {
                "contract": "phase13-requested-grid-v1",
                "origin": self.origin.value.isoformat(),
                "store_ids": self.store_ids,
                "dates": [day.isoformat() for day in self.dates],
            }
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [(store, pd.Timestamp(day)) for store, day in self.keys], columns=("Store", "Date")
        ).astype({"Store": "int64"})

    def validate_complete_keys(self, frame: pd.DataFrame, *, name: str = "requested keys") -> None:
        if tuple(frame.columns) != ("Store", "Date"):
            raise Phase13InputError(f"{name} must contain exactly Store and Date in that order.")
        normalized = _canonical_keys(frame, name=name, store_ids=self.store_ids)
        actual = tuple(
            (int(store), pd.Timestamp(day).date())
            for store, day in normalized[["Store", "Date"]].itertuples(index=False, name=None)
        )
        if actual != self.keys:
            raise Phase13InputError(f"{name} must equal the complete ordered H14 requested grid.")


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Required non-path source identity, version, provenance, and availability statement."""

    source_id: str
    version: str
    provenance: str
    availability_assumption: AvailabilityAssumption
    parent_identities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        source_id = self.source_id.strip() if isinstance(self.source_id, str) else ""
        version = self.version.strip() if isinstance(self.version, str) else ""
        provenance = self.provenance.strip() if isinstance(self.provenance, str) else ""
        if not source_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", source_id):
            raise Phase13InputError("Source identity must be a non-empty non-path identifier.")
        if not version or not provenance:
            raise Phase13InputError("Source version and provenance are required.")
        try:
            availability = AvailabilityAssumption(self.availability_assumption)
        except ValueError as error:
            raise Phase13InputError(
                "Source availability assumption is missing or unrecognized."
            ) from error
        parents = tuple(self.parent_identities)
        if any(not isinstance(parent, str) or not parent.strip() for parent in parents):
            raise Phase13InputError("Source parent identities must be non-empty strings.")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "availability_assumption", availability)
        object.__setattr__(self, "parent_identities", parents)


class _FrameSnapshot:
    """Private immutable-by-interface copy of one validated scalar table."""

    __slots__ = ("_frame", "_identity")

    def __init__(self, frame: pd.DataFrame, *, identity: str) -> None:
        self._frame = frame.copy(deep=True)
        self._identity = identity

    @property
    def identity(self) -> str:
        return self._identity

    def to_frame(self) -> pd.DataFrame:
        """Return an independent copy; mutating it cannot alter the sealed snapshot."""

        return self._frame.copy(deep=True)


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if pd.isna(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    raise Phase13InputError(
        f"Unsupported non-scalar value in validated input: {type(value).__name__}."
    )


def _canonical_identity(
    frame: pd.DataFrame, *, provenance: SourceProvenance, contract: str, context: dict[str, Any]
) -> str:
    payload = {
        "contract": contract,
        "context": context,
        "source": {
            "id": provenance.source_id,
            "version": provenance.version,
            "provenance": provenance.provenance,
            "availability": provenance.availability_assumption.value,
            "parents": provenance.parent_identities,
        },
        "columns": [(column, str(frame[column].dtype)) for column in frame.columns],
        "rows": [
            [_json_value(value) for value in row]
            for row in frame.itertuples(index=False, name=None)
        ],
    }
    return _hash_payload(payload)


def _exact_columns(frame: pd.DataFrame, expected: tuple[str, ...], *, name: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise Phase13InputError(f"{name} must be a pandas DataFrame.")
    if tuple(frame.columns) != expected:
        raise Phase13InputError(
            f"{name} fields/order must exactly match {expected}; got {tuple(frame.columns)}."
        )
    return frame.copy(deep=True)


def _canonical_keys(
    frame: pd.DataFrame, *, name: str, store_ids: tuple[int, ...], require_sorted: bool = True
) -> pd.DataFrame:
    try:
        keys = canonicalize_store_date_keys(frame[["Store", "Date"]], name=name)
    except (KeyError, ValueError) as error:
        raise Phase13InputError(str(error)) from error
    if not keys["Store"].isin(STORE_ROSTER).all():
        raise Phase13InputError(f"{name} contains a Store outside the fixed 1..1115 roster.")
    if not keys["Store"].isin(store_ids).all():
        raise Phase13InputError(f"{name} contains a Store outside the requested grid allowlist.")
    if require_sorted:
        ordered = keys.sort_values(["Store", "Date"], kind="stable").reset_index(drop=True)
        if not keys.reset_index(drop=True).equals(ordered):
            raise Phase13InputError(f"{name} Store × Date rows must be ordered by Store then Date.")
    return keys


def _replace_keys(frame: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy(deep=True)
    result["Store"] = keys["Store"].to_numpy(dtype=np.int64)
    result["Date"] = keys["Date"].to_numpy(dtype="datetime64[ns]")
    return result


def _sales_values(frame: pd.DataFrame, *, name: str, allow_missing: bool) -> pd.Series:
    raw = frame["Sales"]
    numeric = pd.to_numeric(raw, errors="coerce")
    malformed = raw.notna() & numeric.isna()
    values = numeric.to_numpy(dtype=np.float64, na_value=np.nan)
    invalid = malformed.any() or (~np.isfinite(values) & ~numeric.isna().to_numpy()).any()
    if invalid or (not allow_missing and numeric.isna().any()) or numeric.dropna().lt(0).any():
        qualifier = (
            "finite non-negative values"
            if allow_missing
            else "finite non-negative values without nulls"
        )
        raise Phase13InputError(f"{name} Sales must contain {qualifier}.")
    return numeric.astype("float64")


def _open_values(frame: pd.DataFrame, *, name: str) -> pd.Series:
    raw = frame["Open"]
    numeric = pd.to_numeric(raw, errors="coerce")
    malformed = raw.notna() & numeric.isna()
    if malformed.any() or not numeric.dropna().isin([0, 1]).all():
        raise Phase13InputError(f"{name} source Open must be 0, 1, or missing.")
    return numeric.astype("Int8")


class OriginCensoredTrainingInputs(_FrameSnapshot):
    """Source training rows, preserving closed-day turnover and exact eligibility metadata."""

    __slots__ = ("origin", "store_ids", "provenance")

    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        origin: ForecastOrigin | date | str | pd.Timestamp,
        store_ids: tuple[int, ...],
        provenance: SourceProvenance,
    ) -> None:
        parsed_origin = ForecastOrigin.parse(origin)
        stores = _normalize_store_ids(store_ids)
        provenance = _require_provenance(provenance, name="Training inputs")
        data = _exact_columns(frame, TRAINING_INPUT_COLUMNS, name="training inputs")
        keys = _canonical_keys(data, name="training inputs", store_ids=stores)
        if keys["Date"].gt(pd.Timestamp(parsed_origin.value)).any():
            raise Phase13InputError("Training inputs contain a row after the fit origin.")
        data = _replace_keys(data, keys)
        data["Sales"] = _sales_values(data, name="training inputs", allow_missing=True)
        data["Open"] = _open_values(data, name="training inputs")
        eligible = data["training_label_eligible"]
        if (
            eligible.isna().any()
            or not eligible.map(lambda value: isinstance(value, (bool, np.bool_))).all()
        ):
            raise Phase13InputError("training_label_eligible must be non-null Boolean metadata.")
        expected = data["Open"].eq(1).fillna(False) & data["Sales"].notna()
        if not np.array_equal(
            eligible.to_numpy(dtype=bool), expected.to_numpy(dtype=bool, na_value=False)
        ):
            raise Phase13InputError(
                "training_label_eligible must equal source Open=1 and observed Sales."
            )
        _validate_day_of_week(data, name="training inputs")
        identity = _canonical_identity(
            data,
            provenance=provenance,
            contract="phase13-origin-training-v1",
            context={"origin": parsed_origin.value.isoformat(), "store_ids": stores},
        )
        self.origin = parsed_origin
        self.store_ids = stores
        self.provenance = provenance
        super().__init__(data, identity=identity)


class RecursiveHistoryInputs(_FrameSnapshot):
    """Exact observed Store/Date/Sales history through an origin, with no gap filling."""

    __slots__ = ("origin", "store_ids", "provenance")

    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        origin: ForecastOrigin | date | str | pd.Timestamp,
        store_ids: tuple[int, ...],
        provenance: SourceProvenance,
    ) -> None:
        parsed_origin = ForecastOrigin.parse(origin)
        stores = _normalize_store_ids(store_ids)
        provenance = _require_provenance(provenance, name="Recursive history")
        data = _exact_columns(frame, RECURSIVE_HISTORY_COLUMNS, name="recursive history")
        keys = _canonical_keys(data, name="recursive history", store_ids=stores)
        if keys["Date"].gt(pd.Timestamp(parsed_origin.value)).any():
            raise Phase13InputError(
                "Recursive history contains an actual row after the fit origin."
            )
        data = _replace_keys(data, keys)
        data["Sales"] = _sales_values(data, name="recursive history", allow_missing=False)
        identity = _canonical_identity(
            data,
            provenance=provenance,
            contract="phase13-recursive-history-v1",
            context={"origin": parsed_origin.value.isoformat(), "store_ids": stores},
        )
        self.origin = parsed_origin
        self.store_ids = stores
        self.provenance = provenance
        super().__init__(data, identity=identity)


class FutureCovariates(_FrameSnapshot):
    """Origin-safe, label-free rows using the existing frozen source-column schema."""

    __slots__ = ("origin", "grid_identity", "store_ids", "provenance")

    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        grid: RequestedForecastGrid,
        provenance: SourceProvenance,
    ) -> None:
        provenance = _require_provenance(provenance, name="Future covariates")
        data = _exact_columns(frame, FUTURE_COVARIATE_COLUMNS, name="future covariates")
        keys = _canonical_keys(data, name="future covariate keys", store_ids=grid.store_ids)
        dates = keys["Date"]
        if (
            dates.le(pd.Timestamp(grid.origin.value)).any()
            or dates.gt(pd.Timestamp(grid.dates[-1])).any()
        ):
            raise Phase13InputError(
                "Future covariates must fall within this origin's H14 target dates."
            )
        expected_keys = set(grid.keys)
        actual_keys = {
            (int(store), pd.Timestamp(day).date())
            for store, day in keys.itertuples(index=False, name=None)
        }
        if not actual_keys.issubset(expected_keys):
            raise Phase13InputError(
                "Future covariates contain keys outside the requested H14 grid."
            )
        data = _replace_keys(data, keys)
        _validate_day_of_week(data, name="future covariates")
        identity = _canonical_identity(
            data,
            provenance=provenance,
            contract="phase13-future-covariates-v1",
            context={"origin": grid.origin.value.isoformat(), "grid": grid.identity},
        )
        self.origin = grid.origin
        self.grid_identity = grid.identity
        self.store_ids = grid.store_ids
        self.provenance = provenance
        super().__init__(data, identity=identity)


class SyntheticPlannedOpen(_FrameSnapshot):
    """Separate synthetic weekly schedule; `ScenarioOpen` and source `Open` are excluded."""

    __slots__ = ("origin", "grid_identity", "store_ids", "provenance", "rule_id")

    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        grid: RequestedForecastGrid,
        provenance: SourceProvenance,
        rule_id: str = SYNTHETIC_OPEN_RULE_ID,
    ) -> None:
        if rule_id != SYNTHETIC_OPEN_RULE_ID:
            raise Phase13InputError("Unknown synthetic planned-Open rule identity.")
        provenance = _require_provenance(provenance, name="Synthetic planned Open")
        if provenance.availability_assumption != AvailabilityAssumption.SYNTHETIC_RULE:
            raise Phase13InputError("Planned Open provenance must identify a synthetic rule.")
        data = _exact_columns(frame, PLANNED_OPEN_COLUMNS, name="synthetic planned Open")
        keys = _canonical_keys(data, name="planned-Open keys", store_ids=grid.store_ids)
        expected_keys = set(grid.keys)
        actual_keys = {
            (int(store), pd.Timestamp(day).date())
            for store, day in keys.itertuples(index=False, name=None)
        }
        if not actual_keys.issubset(expected_keys):
            raise Phase13InputError("Planned Open contains keys outside the requested H14 grid.")
        data = _replace_keys(data, keys)
        values = data["planned_open"]
        valid = values.isna() | values.map(lambda value: isinstance(value, (bool, np.bool_)))
        if not valid.all():
            raise Phase13InputError(
                "planned_open must be Boolean or missing; no fallback is allowed."
            )
        data["planned_open"] = pd.array(values, dtype="boolean")
        expected_open = pd.Series(pd.to_datetime(data["Date"]).dt.weekday.ne(6), index=data.index)
        planned_open = data["planned_open"]
        mismatch = planned_open.notna() & planned_open.ne(expected_open).fillna(False)
        if mismatch.any():
            raise Phase13InputError(
                "Non-null planned_open values must follow the Monday–Saturday open, "
                "Sunday closed weekly rule."
            )
        identity = _canonical_identity(
            data,
            provenance=provenance,
            contract="phase13-synthetic-planned-open-v1",
            context={
                "origin": grid.origin.value.isoformat(),
                "grid": grid.identity,
                "rule_id": rule_id,
            },
        )
        self.origin = grid.origin
        self.grid_identity = grid.identity
        self.store_ids = grid.store_ids
        self.provenance = provenance
        self.rule_id = rule_id
        super().__init__(data, identity=identity)


class ProtectedDailyOutcomeProjection(_FrameSnapshot):
    """One synthetic, explicitly authorized date projection of Sales and source Open only."""

    __slots__ = ("outcome_date", "provider_id", "authorization_token_id", "store_ids", "provenance")

    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        outcome_date: date | str | pd.Timestamp,
        provider_id: str,
        authorization_token_id: str,
        store_ids: tuple[int, ...],
        provenance: SourceProvenance,
    ) -> None:
        day = _calendar_date(outcome_date, name="outcome projection date")
        if day not in PROTECTED_DATES:
            raise Phase13InputError("Outcome projection date is outside July 4–31, 2015.")
        if (
            not isinstance(provider_id, str)
            or not provider_id.strip()
            or not isinstance(authorization_token_id, str)
            or not authorization_token_id.strip()
        ):
            raise Phase13InputError(
                "Outcome projection requires its provider and authorization identity."
            )
        stores = _normalize_store_ids(store_ids)
        provenance = _require_provenance(provenance, name="Outcome projection")
        if provenance.availability_assumption != AvailabilityAssumption.SYNTHETIC_RULE:
            raise Phase13InputError("M1 outcome projections must carry synthetic provenance.")
        data = _exact_columns(
            frame, OUTCOME_PROJECTION_COLUMNS, name="protected daily outcome projection"
        )
        keys = _canonical_keys(data, name="protected daily outcome projection", store_ids=stores)
        if len(keys) and not keys["Date"].eq(pd.Timestamp(day)).all():
            raise Phase13InputError("Outcome projection may contain only its authorized date.")
        data = _replace_keys(data, keys)
        data["Sales"] = _sales_values(data, name="outcome projection", allow_missing=True)
        data["Open"] = _open_values(data, name="outcome projection")
        identity = _canonical_identity(
            data,
            provenance=provenance,
            contract="phase13-protected-daily-outcome-v1",
            context={"date": day.isoformat(), "provider_id": provider_id},
        )
        self.outcome_date = day
        self.provider_id = provider_id
        self.authorization_token_id = authorization_token_id
        self.store_ids = stores
        self.provenance = provenance
        super().__init__(data, identity=identity)


def build_synthetic_planned_open(
    grid: RequestedForecastGrid, *, provenance: SourceProvenance
) -> SyntheticPlannedOpen:
    """Build Monday–Saturday open/Sunday closed from calendar dates alone."""

    frame = grid.to_frame()
    frame["planned_open"] = pd.array(
        [pd.Timestamp(day).weekday() != 6 for day in frame["Date"]], dtype="boolean"
    )
    return SyntheticPlannedOpen(frame, grid=grid, provenance=provenance)


def _validate_day_of_week(frame: pd.DataFrame, *, name: str) -> None:
    supplied = pd.to_numeric(frame["DayOfWeek"], errors="coerce")
    expected = pd.to_datetime(frame["Date"]).dt.weekday + 1
    if supplied.isna().any() or not supplied.eq(expected).all():
        raise Phase13InputError(f"{name} DayOfWeek conflicts with the calendar Date.")
