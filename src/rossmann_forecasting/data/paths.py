"""Portable project data-path resolution."""

from __future__ import annotations

from pathlib import Path


def repository_root() -> Path:
    """Return the repository root based on this installed source tree."""

    candidate = Path(__file__).resolve().parents[3]
    if not (candidate / "pyproject.toml").is_file():
        raise RuntimeError("Could not locate the repository root from the package source tree.")
    return candidate


def default_raw_data_dir() -> Path:
    """Return the default local directory for immutable Rossmann source files."""

    return repository_root() / "data" / "raw" / "rossmann"


def resolve_data_dir(data_dir: str | Path | None = None) -> Path:
    """Resolve an explicit data directory or the repository-relative default.

    Relative overrides are interpreted from the repository root so commands behave
    consistently regardless of the caller's current working directory.
    """

    if data_dir is None:
        return default_raw_data_dir()

    path = Path(data_dir).expanduser()
    if not path.is_absolute():
        path = repository_root() / path
    return path.resolve(strict=False)
