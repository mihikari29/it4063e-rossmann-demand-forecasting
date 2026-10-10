"""Synthetic-only Phase 13 input contracts and provider guards."""

from rossmann_forecasting.phase13.contracts import (
    AvailabilityAssumption,
    ForecastOrigin,
    FutureCovariates,
    OriginCensoredTrainingInputs,
    ProtectedDailyOutcomeProjection,
    RecursiveHistoryInputs,
    RequestedForecastGrid,
    SourceProvenance,
    SyntheticPlannedOpen,
    build_synthetic_planned_open,
)
from rossmann_forecasting.phase13.providers import (
    ISSUANCE_CAPABILITIES,
    ProviderRole,
    SourceBinding,
    SyntheticFrameStore,
    SyntheticInputProvider,
    SyntheticOutcomeAuthorization,
    SyntheticOutcomeProvider,
)

__all__ = [
    "ISSUANCE_CAPABILITIES",
    "AvailabilityAssumption",
    "ForecastOrigin",
    "FutureCovariates",
    "OriginCensoredTrainingInputs",
    "ProtectedDailyOutcomeProjection",
    "ProviderRole",
    "RecursiveHistoryInputs",
    "RequestedForecastGrid",
    "SourceBinding",
    "SourceProvenance",
    "SyntheticFrameStore",
    "SyntheticInputProvider",
    "SyntheticOutcomeAuthorization",
    "SyntheticOutcomeProvider",
    "SyntheticPlannedOpen",
    "build_synthetic_planned_open",
]
