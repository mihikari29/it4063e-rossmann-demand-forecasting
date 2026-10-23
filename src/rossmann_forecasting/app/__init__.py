"""Public application contracts, loaded only when their names are requested.

Keeping submodule imports side-effect-light lets the controlled-synthetic provider reuse the
bundle verifier without importing the canonical artifact reader. Existing package-level exports
remain available through lazy attribute resolution.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORT_MODULES = {
    "DEVELOPMENT_CUTOFF": "artifacts",
    "HISTORY_PROJECTION": "artifacts",
    "read_canonical_artifact": "artifacts",
    "read_historical_sales": "artifacts",
    "ArtifactReadError": "contracts",
    "ArtifactReadiness": "contracts",
    "ArtifactSelector": "contracts",
    "ArtifactTable": "contracts",
    "ArtifactUnavailableError": "contracts",
    "ArtifactValidationLevel": "contracts",
    "ForecastQuery": "contracts",
    "HistoryQuery": "contracts",
    "InventoryComparisonQuery": "contracts",
    "ModelComparisonQuery": "contracts",
    "UnavailableReason": "contracts",
    "UnavailableResource": "contracts",
    "UncertaintyQuery": "contracts",
    "ApplicationServices": "services",
    "json_safe": "services",
}

__all__ = [
    "DEVELOPMENT_CUTOFF",
    "HISTORY_PROJECTION",
    "ArtifactReadError",
    "ArtifactReadiness",
    "ArtifactSelector",
    "ArtifactTable",
    "ArtifactUnavailableError",
    "ArtifactValidationLevel",
    "ApplicationServices",
    "ForecastQuery",
    "HistoryQuery",
    "InventoryComparisonQuery",
    "ModelComparisonQuery",
    "UncertaintyQuery",
    "UnavailableReason",
    "UnavailableResource",
    "json_safe",
    "read_canonical_artifact",
    "read_historical_sales",
]


def __getattr__(name: str) -> Any:
    """Preserve the historical package exports without importing unused app layers."""
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
