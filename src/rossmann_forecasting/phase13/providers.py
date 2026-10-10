"""Default-deny providers backed only by injected synthetic in-memory frames."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

import pandas as pd

from rossmann_forecasting.phase13.contracts import (
    BLOCK1_DATES,
    FUTURE_COVARIATE_COLUMNS,
    OUTCOME_PROJECTION_COLUMNS,
    PROTECTED_DATES,
    RECURSIVE_HISTORY_COLUMNS,
    TRAINING_INPUT_COLUMNS,
    AvailabilityAssumption,
    ForecastOrigin,
    FutureCovariates,
    OriginCensoredTrainingInputs,
    Phase13InputError,
    ProtectedDailyOutcomeProjection,
    RecursiveHistoryInputs,
    RequestedForecastGrid,
    SourceProvenance,
    SyntheticPlannedOpen,
    _normalize_store_ids,
    build_synthetic_planned_open,
)


class ProviderRole(StrEnum):
    TRAINING = "training"
    RECURSIVE_HISTORY = "recursive_history"
    FUTURE_COVARIATES = "future_covariates"
    PLANNED_OPEN = "planned_open"
    PROTECTED_OUTCOME = "protected_outcome"


ISSUANCE_CAPABILITIES = frozenset(
    {
        ProviderRole.TRAINING,
        ProviderRole.RECURSIVE_HISTORY,
        ProviderRole.FUTURE_COVARIATES,
        ProviderRole.PLANNED_OPEN,
    }
)
OUTCOME_CAPABILITIES = frozenset({ProviderRole.PROTECTED_OUTCOME})
_MEMORY_REFERENCE = re.compile(r"memory://phase13/[a-z0-9][a-z0-9._-]*\Z")
_DEVELOPMENT_CUTOFF = date(2015, 7, 3)
_JULY17_ORIGIN = date(2015, 7, 17)


def _role(value: ProviderRole | str) -> ProviderRole:
    try:
        return ProviderRole(value)
    except (TypeError, ValueError) as error:
        raise Phase13InputError(f"Unknown Phase 13 provider role: {value!r}.") from error


def _capability_set(values: Iterable[ProviderRole | str]) -> frozenset[ProviderRole]:
    try:
        return frozenset(_role(value) for value in values)
    except TypeError as error:
        raise Phase13InputError(
            "Provider capabilities must be an explicit iterable of roles."
        ) from error


def _memory_reference(value: object) -> str:
    if not isinstance(value, str) or not _MEMORY_REFERENCE.fullmatch(value):
        raise Phase13InputError("Only recognized memory://phase13 fixture references are allowed.")
    if ".." in value:
        raise Phase13InputError(
            "Path-like traversal is not allowed in a synthetic source reference."
        )
    return value


@dataclass(frozen=True, slots=True)
class SourceBinding:
    """One role-scoped synthetic memory reference and its provenance."""

    role: ProviderRole
    reference: str
    provenance: SourceProvenance

    def __post_init__(self) -> None:
        normalized_role = _role(self.role)
        reference = _memory_reference(self.reference)
        if not isinstance(self.provenance, SourceProvenance):
            raise Phase13InputError("Every provider source requires typed provenance.")
        object.__setattr__(self, "role", normalized_role)
        object.__setattr__(self, "reference", reference)


class _SyntheticReader(Protocol):
    def read_memory(self, reference: str) -> pd.DataFrame: ...


class SyntheticFrameStore:
    """In-memory fixture reader; it has no filesystem or network access methods."""

    def __init__(self, frames: Mapping[str, pd.DataFrame]) -> None:
        sealed: dict[str, pd.DataFrame] = {}
        for raw_reference, frame in frames.items():
            reference = _memory_reference(raw_reference)
            if reference in sealed:
                raise Phase13InputError(f"Duplicate synthetic memory reference: {reference}.")
            if not isinstance(frame, pd.DataFrame):
                raise Phase13InputError("SyntheticFrameStore accepts only in-memory DataFrames.")
            sealed[reference] = frame.copy(deep=True)
        self._frames = sealed
        self._read_calls: list[str] = []

    @property
    def read_calls(self) -> tuple[str, ...]:
        return tuple(self._read_calls)

    def read_memory(self, reference: str) -> pd.DataFrame:
        safe_reference = _memory_reference(reference)
        if safe_reference not in self._frames:
            raise Phase13InputError(f"Unknown synthetic fixture reference: {safe_reference}.")
        self._read_calls.append(safe_reference)
        return self._frames[safe_reference].copy(deep=True)


def _guarded_synthetic_read(
    reader: _SyntheticReader,
    binding: SourceBinding,
    *,
    requested_role: ProviderRole | str,
    capabilities: Iterable[ProviderRole | str],
    requested_fields: Sequence[str],
    expected_fields: Sequence[str],
) -> pd.DataFrame:
    """Validate role, capability, path, and fields before invoking the injected reader."""

    role = _role(requested_role)
    allowed = _capability_set(capabilities)
    if role not in allowed or role != binding.role:
        raise Phase13InputError(f"Provider lacks the required {role.value!r} capability.")
    reference = _memory_reference(binding.reference)
    if tuple(requested_fields) != tuple(expected_fields):
        raise Phase13InputError(f"Requested fields do not match the {role.value} source contract.")
    frame = reader.read_memory(reference)
    if not isinstance(frame, pd.DataFrame) or tuple(frame.columns) != tuple(expected_fields):
        raise Phase13InputError(f"{role.value} source fields/order violate the declared contract.")
    return frame.copy(deep=True)


@dataclass(frozen=True, slots=True)
class SyntheticOutcomeAuthorization:
    """Date-bound synthetic fixture token; it is not a real-data release authorization."""

    provider_id: str
    outcome_date: date
    token_id: str
    synthetic_fixture_only: bool = True

    def __post_init__(self) -> None:
        parsed_date = _provider_date(self.outcome_date)
        if (
            not isinstance(self.provider_id, str)
            or not self.provider_id.strip()
            or not isinstance(self.token_id, str)
            or not self.token_id.strip()
        ):
            raise Phase13InputError(
                "Synthetic outcome authorization requires provider and token IDs."
            )
        if self.synthetic_fixture_only is not True:
            raise Phase13InputError("Only synthetic fixture authorizations are accepted in M1.")
        if parsed_date not in PROTECTED_DATES:
            raise Phase13InputError(
                "Synthetic outcome authorization date is outside July 4–31, 2015."
            )
        object.__setattr__(self, "outcome_date", parsed_date)


class SyntheticInputProvider:
    """Issuance-facing provider with no outcome capability or generic field projection API."""

    def __init__(
        self,
        *,
        grid: RequestedForecastGrid,
        reader: _SyntheticReader,
        sources: Iterable[SourceBinding],
        capabilities: Iterable[ProviderRole | str],
        planned_open_provenance: SourceProvenance,
        prior_block1_covariates: FutureCovariates | None = None,
        prior_block1_outcomes: Iterable[ProtectedDailyOutcomeProjection] = (),
    ) -> None:
        self.grid = grid
        self._reader = reader
        self.capabilities = _capability_set(capabilities)
        if not self.capabilities.issubset(ISSUANCE_CAPABILITIES):
            raise Phase13InputError(
                "Issuance providers cannot receive protected-outcome capability."
            )
        if not isinstance(planned_open_provenance, SourceProvenance):
            raise Phase13InputError("Planned Open requires explicit synthetic rule provenance.")
        if planned_open_provenance.availability_assumption != AvailabilityAssumption.SYNTHETIC_RULE:
            raise Phase13InputError("Planned Open provenance must identify a synthetic rule.")
        bindings: dict[ProviderRole, SourceBinding] = {}
        for binding in sources:
            if not isinstance(binding, SourceBinding):
                raise Phase13InputError(
                    "Issuance provider sources must be typed SourceBinding values."
                )
            if binding.role == ProviderRole.PROTECTED_OUTCOME:
                raise Phase13InputError(
                    "Protected outcomes cannot be bound to an issuance provider."
                )
            if binding.role in bindings:
                raise Phase13InputError(f"Duplicate issuance source role: {binding.role.value}.")
            if binding.role not in self.capabilities:
                raise Phase13InputError(f"Source role {binding.role.value} is not allowlisted.")
            bindings[binding.role] = binding
        required_sources = {
            ProviderRole.TRAINING,
            ProviderRole.RECURSIVE_HISTORY,
            ProviderRole.FUTURE_COVARIATES,
        }
        if set(bindings) != required_sources:
            raise Phase13InputError(
                "Issuance provider requires exactly training, history, and covariate sources."
            )
        if not required_sources.issubset(self.capabilities):
            raise Phase13InputError(
                "Issuance provider must explicitly allow its three source roles."
            )
        if ProviderRole.PLANNED_OPEN not in self.capabilities:
            raise Phase13InputError(
                "Issuance provider must explicitly allow the synthetic planned-Open rule."
            )
        self._bindings = bindings
        self._planned_open_provenance = planned_open_provenance
        self._prior_covariates = prior_block1_covariates
        self._prior_outcomes = tuple(prior_block1_outcomes)
        self._validate_prior_release_inputs()

    def _validate_origin(self, origin: ForecastOrigin | date | str | pd.Timestamp | None) -> None:
        parsed = self.grid.origin if origin is None else ForecastOrigin.parse(origin)
        if parsed != self.grid.origin:
            raise Phase13InputError("Provider request origin does not match its bound H14 grid.")

    def _read(
        self,
        role: ProviderRole,
        *,
        requested_fields: Sequence[str],
    ) -> pd.DataFrame:
        binding = self._bindings.get(role)
        if binding is None:
            raise Phase13InputError(f"Provider has no source binding for {role.value}.")
        return _guarded_synthetic_read(
            self._reader,
            binding,
            requested_role=role,
            capabilities=self.capabilities,
            requested_fields=requested_fields,
            expected_fields=requested_fields,
        )

    def read_training_inputs(
        self, *, origin: ForecastOrigin | date | str | pd.Timestamp | None = None
    ) -> OriginCensoredTrainingInputs:
        self._validate_origin(origin)
        binding = self._bindings[ProviderRole.TRAINING]
        base = self._read(ProviderRole.TRAINING, requested_fields=TRAINING_INPUT_COLUMNS)
        baseline = OriginCensoredTrainingInputs(
            base,
            origin=_DEVELOPMENT_CUTOFF,
            store_ids=self.grid.store_ids,
            provenance=binding.provenance,
        )
        if self.grid.origin.value == _DEVELOPMENT_CUTOFF:
            return baseline
        covariates = self._prior_covariates.to_frame() if self._prior_covariates else None
        if covariates is None:
            raise Phase13InputError("July 17 training requires prior issued Block 1 covariates.")
        released = pd.concat(
            [projection.to_frame() for projection in self._prior_outcomes], ignore_index=True
        )
        if released.empty:
            prior_training = pd.DataFrame(columns=TRAINING_INPUT_COLUMNS)
        else:
            joined = released.merge(
                covariates,
                on=["Store", "Date"],
                how="left",
                validate="one_to_one",
                indicator=True,
                sort=False,
            )
            if joined["_merge"].ne("both").any():
                raise Phase13InputError(
                    "Released Block 1 outcomes lack matching issued covariates."
                )
            prior_training = joined.loc[:, FUTURE_COVARIATE_COLUMNS].copy()
            prior_training["Sales"] = joined["Sales"].to_numpy(copy=True)
            prior_training["Open"] = joined["Open"].to_numpy(copy=True)
            prior_training["training_label_eligible"] = (
                pd.to_numeric(prior_training["Open"], errors="coerce").eq(1)
                & pd.to_numeric(prior_training["Sales"], errors="coerce").notna()
            ).to_numpy(dtype=bool)
            prior_training = prior_training.loc[:, TRAINING_INPUT_COLUMNS]
        combined = pd.concat([baseline.to_frame(), prior_training], ignore_index=True)
        combined = combined.sort_values(["Store", "Date"], kind="stable").reset_index(drop=True)
        provenance = SourceProvenance(
            source_id=f"training-origin-{self.grid.origin.value.isoformat()}",
            version="phase13-synthetic-input-v1",
            provenance=(
                "Synthetic base history plus only Block 1 outcomes released through the origin."
            ),
            availability_assumption=AvailabilityAssumption.OBSERVED_THROUGH_ORIGIN,
            parent_identities=(
                baseline.identity,
                self._prior_covariates.identity,
                *(projection.identity for projection in self._prior_outcomes),
            ),
        )
        return OriginCensoredTrainingInputs(
            combined,
            origin=self.grid.origin,
            store_ids=self.grid.store_ids,
            provenance=provenance,
        )

    def read_recursive_history_inputs(
        self, *, origin: ForecastOrigin | date | str | pd.Timestamp | None = None
    ) -> RecursiveHistoryInputs:
        self._validate_origin(origin)
        binding = self._bindings[ProviderRole.RECURSIVE_HISTORY]
        base = self._read(
            ProviderRole.RECURSIVE_HISTORY, requested_fields=RECURSIVE_HISTORY_COLUMNS
        )
        baseline = RecursiveHistoryInputs(
            base,
            origin=_DEVELOPMENT_CUTOFF,
            store_ids=self.grid.store_ids,
            provenance=binding.provenance,
        )
        if self.grid.origin.value == _DEVELOPMENT_CUTOFF:
            return baseline
        released = pd.concat(
            [
                projection.to_frame().loc[:, list(RECURSIVE_HISTORY_COLUMNS)]
                for projection in self._prior_outcomes
            ],
            ignore_index=True,
        )
        combined = pd.concat([baseline.to_frame(), released], ignore_index=True)
        combined = combined.sort_values(["Store", "Date"], kind="stable").reset_index(drop=True)
        provenance = SourceProvenance(
            source_id=f"history-origin-{self.grid.origin.value.isoformat()}",
            version="phase13-synthetic-history-v1",
            provenance=(
                "Synthetic observed history through the origin; "
                "Block 1 rows are separately released."
            ),
            availability_assumption=AvailabilityAssumption.OBSERVED_THROUGH_ORIGIN,
            parent_identities=(
                baseline.identity,
                *(projection.identity for projection in self._prior_outcomes),
            ),
        )
        return RecursiveHistoryInputs(
            combined,
            origin=self.grid.origin,
            store_ids=self.grid.store_ids,
            provenance=provenance,
        )

    def read_future_covariates(
        self, *, origin: ForecastOrigin | date | str | pd.Timestamp | None = None
    ) -> FutureCovariates:
        self._validate_origin(origin)
        binding = self._bindings[ProviderRole.FUTURE_COVARIATES]
        frame = self._read(
            ProviderRole.FUTURE_COVARIATES,
            requested_fields=FUTURE_COVARIATE_COLUMNS,
        )
        return FutureCovariates(frame, grid=self.grid, provenance=binding.provenance)

    def read_planned_open(
        self, *, origin: ForecastOrigin | date | str | pd.Timestamp | None = None
    ) -> SyntheticPlannedOpen:
        self._validate_origin(origin)
        if ProviderRole.PLANNED_OPEN not in self.capabilities:
            raise Phase13InputError("Provider lacks the synthetic planned-Open capability.")
        return build_synthetic_planned_open(self.grid, provenance=self._planned_open_provenance)

    def _validate_prior_release_inputs(self) -> None:
        if self.grid.origin.value == _DEVELOPMENT_CUTOFF:
            if self._prior_covariates is not None or self._prior_outcomes:
                raise Phase13InputError(
                    "Block 1 issuance cannot receive later outcomes or prior-block inputs."
                )
            return
        if self.grid.origin.value != _JULY17_ORIGIN:
            raise Phase13InputError("Unsupported issuance origin.")
        if self._prior_covariates is None:
            raise Phase13InputError("Block 2 requires separately issued Block 1 covariates.")
        expected_grid = RequestedForecastGrid(_DEVELOPMENT_CUTOFF, self.grid.store_ids)
        if (
            self._prior_covariates.origin.value != _DEVELOPMENT_CUTOFF
            or self._prior_covariates.grid_identity != expected_grid.identity
            or self._prior_covariates.store_ids != self.grid.store_ids
        ):
            raise Phase13InputError(
                "Block 2 prior covariates must be the matching Block 1 grid input."
            )
        dates = tuple(projection.outcome_date for projection in self._prior_outcomes)
        if dates != BLOCK1_DATES:
            raise Phase13InputError(
                "Block 2 requires all 14 Block 1 dates in authorized chronological order."
            )
        if any(projection.store_ids != self.grid.store_ids for projection in self._prior_outcomes):
            raise Phase13InputError(
                "Released Block 1 outcomes do not match the requested Store allowlist."
            )
        provider_ids = {projection.provider_id for projection in self._prior_outcomes}
        if len(provider_ids) != 1:
            raise Phase13InputError(
                "Block 1 released outcomes must share one synthetic provider identity."
            )


class SyntheticOutcomeProvider:
    """Separate date-at-a-time synthetic outcome reader gated by a matching token allowlist."""

    def __init__(
        self,
        *,
        reader: _SyntheticReader,
        provider_id: str,
        store_ids: tuple[int, ...],
        date_sources: Mapping[date | str, SourceBinding],
        authorization_allowlist: Mapping[date | str, str],
        expected_dates: Sequence[date | str] = PROTECTED_DATES,
    ) -> None:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise Phase13InputError("Synthetic outcome provider requires a provider identity.")
        stores = _normalize_store_ids(store_ids)
        parsed_dates = tuple(_provider_date(value) for value in expected_dates)
        if not parsed_dates or parsed_dates != tuple(sorted(set(parsed_dates))):
            raise Phase13InputError(
                "Outcome provider dates must be non-empty, unique, and chronological."
            )
        if any(day not in PROTECTED_DATES for day in parsed_dates):
            raise Phase13InputError(
                "Outcome provider date allowlist must stay within July 4–31, 2015."
            )
        sources = {_provider_date(day): binding for day, binding in date_sources.items()}
        tokens = {_provider_date(day): token for day, token in authorization_allowlist.items()}
        if (
            len(sources) != len(date_sources)
            or len(tokens) != len(authorization_allowlist)
            or set(sources) != set(parsed_dates)
            or set(tokens) != set(parsed_dates)
        ):
            raise Phase13InputError(
                "Every allowed outcome date requires one source and one token allowlist entry."
            )
        if any(binding.role != ProviderRole.PROTECTED_OUTCOME for binding in sources.values()):
            raise Phase13InputError(
                "Outcome projections require protected_outcome source bindings."
            )
        if any(not isinstance(token, str) or not token.strip() for token in tokens.values()):
            raise Phase13InputError(
                "Outcome authorization token allowlist contains an empty token."
            )
        self._reader = reader
        self.provider_id = provider_id
        self.store_ids = stores
        self.expected_dates = parsed_dates
        self._sources = sources
        self._tokens = tokens
        self._next_index = 0
        self._released: list[ProtectedDailyOutcomeProjection] = []

    @property
    def released_projections(self) -> tuple[ProtectedDailyOutcomeProjection, ...]:
        return tuple(self._released)

    def read_day(
        self,
        day: date | str | pd.Timestamp,
        authorization: SyntheticOutcomeAuthorization | None,
    ) -> ProtectedDailyOutcomeProjection:
        requested_day = _provider_date(day)
        if self._next_index >= len(self.expected_dates):
            raise Phase13InputError(
                "No unreleased synthetic outcome date remains in this provider."
            )
        expected_day = self.expected_dates[self._next_index]
        if requested_day != expected_day:
            raise Phase13InputError(
                "Synthetic outcome dates must be requested in allowlisted order."
            )
        if not isinstance(authorization, SyntheticOutcomeAuthorization):
            raise Phase13InputError(
                "Matching synthetic release authorization is required before access."
            )
        if (
            authorization.provider_id != self.provider_id
            or authorization.outcome_date != requested_day
            or authorization.token_id != self._tokens[requested_day]
            or authorization.synthetic_fixture_only is not True
        ):
            raise Phase13InputError(
                "Synthetic release authorization does not match provider/date/token allowlist."
            )
        binding = self._sources[requested_day]
        frame = _guarded_synthetic_read(
            self._reader,
            binding,
            requested_role=ProviderRole.PROTECTED_OUTCOME,
            capabilities=OUTCOME_CAPABILITIES,
            requested_fields=OUTCOME_PROJECTION_COLUMNS,
            expected_fields=OUTCOME_PROJECTION_COLUMNS,
        )
        provenance = SourceProvenance(
            source_id=f"{binding.provenance.source_id}-{requested_day.isoformat()}",
            version=binding.provenance.version,
            provenance=binding.provenance.provenance,
            availability_assumption=AvailabilityAssumption.SYNTHETIC_RULE,
            parent_identities=(binding.provenance.source_id, authorization.token_id),
        )
        projection = ProtectedDailyOutcomeProjection(
            frame,
            outcome_date=requested_day,
            provider_id=self.provider_id,
            authorization_token_id=authorization.token_id,
            store_ids=self.store_ids,
            provenance=provenance,
        )
        self._released.append(projection)
        self._next_index += 1
        return projection

    def released_history_through(
        self, origin: ForecastOrigin | date | str | pd.Timestamp
    ) -> RecursiveHistoryInputs:
        parsed_origin = ForecastOrigin.parse(origin)
        allowed = tuple(day for day in BLOCK1_DATES if day <= parsed_origin.value)
        released_by_date = {item.outcome_date: item for item in self._released}
        if any(day not in released_by_date for day in allowed):
            raise Phase13InputError(
                "Requested origin includes Block 1 dates that are not released."
            )
        frames = [
            released_by_date[day].to_frame().loc[:, list(RECURSIVE_HISTORY_COLUMNS)]
            for day in allowed
        ]
        frame = (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame(columns=RECURSIVE_HISTORY_COLUMNS)
        )
        provenance = SourceProvenance(
            source_id=f"released-outcomes-through-{parsed_origin.value.isoformat()}",
            version="phase13-synthetic-release-v1",
            provenance=(
                "Only synthetic outcome projections returned after matching per-date tokens."
            ),
            availability_assumption=AvailabilityAssumption.OBSERVED_THROUGH_ORIGIN,
            parent_identities=tuple(released_by_date[day].identity for day in allowed),
        )
        return RecursiveHistoryInputs(
            frame,
            origin=parsed_origin,
            store_ids=self.store_ids,
            provenance=provenance,
        )


def _provider_date(value: date | str | pd.Timestamp) -> date:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise Phase13InputError("Provider date must be a valid calendar date.") from error
    if pd.isna(timestamp) or timestamp.tz is not None or timestamp != timestamp.normalize():
        raise Phase13InputError("Provider date must be a timezone-naive midnight date.")
    return timestamp.date()
