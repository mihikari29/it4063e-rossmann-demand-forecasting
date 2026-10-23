"""Pinned, offline access to the fixed controlled-synthetic demonstration release."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from rossmann_forecasting.app.demo_bundle import (
    BUNDLE_FILENAME,
    EVIDENCE_KIND,
    MANIFEST_FILENAME,
    MAX_BUNDLE_BYTES,
    MAX_MANIFEST_BYTES,
    RELEASE_ID,
    SCHEMA_VERSION,
    DemoBundleError,
    verify_release_directory,
)

_MANIFEST_PIN = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_VERIFIED_PROVIDER_TOKEN = object()


class DemoProfile(StrEnum):
    """Explicit profile selector; this provider has no implicit canonical fallback."""

    CONTROLLED_SYNTHETIC = "controlled_synthetic_demo"


class DemoErrorCode(StrEnum):
    """Stable, sanitized codes for a future HTTP adapter."""

    PROFILE = "demo_profile_invalid"
    UNAVAILABLE = "demo_release_unavailable"
    INTEGRITY = "demo_release_invalid"
    REQUEST = "demo_request_invalid"


class DemoProviderError(RuntimeError):
    """A release cannot safely provide synthetic application results."""

    def __init__(self, code: DemoErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


class DemoReleaseUnavailableError(DemoProviderError):
    """The fixed synthetic release files are missing."""

    def __init__(self) -> None:
        super().__init__(
            DemoErrorCode.UNAVAILABLE, "The synthetic demonstration release is unavailable."
        )


class DemoReleaseIntegrityError(DemoProviderError):
    """The fixed synthetic release did not pass pinned validation."""

    def __init__(self) -> None:
        super().__init__(DemoErrorCode.INTEGRITY, "The synthetic demonstration release is invalid.")


class DemoInvalidRequestError(ValueError):
    """A synthetic query is outside the release's closed allowlist."""

    code = DemoErrorCode.REQUEST
    message = "The synthetic demonstration request is invalid or outside the supported range."

    def __init__(self) -> None:
        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class SyntheticProvenance:
    """Machine-readable synthetic identity, deliberately separate from canonical run identity."""

    release_id: str
    evidence_kind: str
    bundle_sha256: str
    manifest_sha256: str
    schema_version: str
    source_kind: str
    view_id: str
    selected_rows: int


def _freeze(value: Any) -> Any:
    """Recursively detach parsed JSON from mutable containers."""
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


def _read_bounded(path: Path, limit: int) -> bytes:
    try:
        with path.open("rb") as source:
            content = source.read(limit + 1)
    except OSError:
        raise DemoReleaseIntegrityError() from None
    if len(content) > limit:
        raise DemoReleaseIntegrityError()
    return content


@dataclass(frozen=True, slots=True, init=False)
class DemoProvider:
    """One verified in-memory snapshot and bounded indexes over its fixed release."""

    profile: DemoProfile
    release_id: str
    evidence_kind: str
    schema_version: str
    source_kind: str
    bundle_sha256: str
    manifest_sha256: str
    limitations: tuple[str, ...]
    _bundle: Mapping[str, Any]
    _query_allowlist: Mapping[str, Any]
    _history_by_store: Mapping[int, tuple[Mapping[str, Any], ...]]
    _forecasts_by_query: Mapping[tuple[int, str], tuple[Mapping[str, Any], ...]]
    _uncertainty_by_query: Mapping[tuple[int, str, str], Mapping[str, Any]]
    _comparison_rows: tuple[Mapping[str, Any], ...]
    _inventory_by_case: Mapping[str, Mapping[str, Any]]

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise TypeError("Construct a verified provider with DemoProvider.open().")

    @classmethod
    def _from_verified(cls, *, _token: object, **values: Any) -> DemoProvider:
        if (
            _token is not _VERIFIED_PROVIDER_TOKEN
            or values.keys() != cls.__dataclass_fields__.keys()
        ):
            raise TypeError("Construct a verified provider with DemoProvider.open().")
        provider = object.__new__(cls)
        for name, value in values.items():
            object.__setattr__(provider, name, value)
        return provider

    @classmethod
    def open(
        cls,
        *,
        profile: DemoProfile,
        expected_manifest_sha256: str,
        repository_root: Path | None = None,
    ) -> DemoProvider:
        """Verify the fixed two-file release with a mandatory out-of-band pin."""
        if profile is not DemoProfile.CONTROLLED_SYNTHETIC:
            raise DemoProviderError(
                DemoErrorCode.PROFILE, "An explicit supported synthetic profile is required."
            )
        if (
            type(expected_manifest_sha256) is not str
            or _MANIFEST_PIN.fullmatch(expected_manifest_sha256) is None
        ):
            raise DemoReleaseIntegrityError()

        try:
            root = (
                Path(__file__).resolve().parents[3]
                if repository_root is None
                else repository_root.resolve(strict=True)
            )
        except (OSError, RuntimeError, AttributeError):
            raise DemoReleaseUnavailableError() from None
        release_dir = root / "artifacts" / "public_demo" / RELEASE_ID
        if not release_dir.is_dir():
            raise DemoReleaseUnavailableError()
        if (
            not (release_dir / BUNDLE_FILENAME).is_file()
            or not (release_dir / MANIFEST_FILENAME).is_file()
        ):
            raise DemoReleaseUnavailableError()

        try:
            report = verify_release_directory(
                release_dir,
                expected_manifest_sha256=expected_manifest_sha256,
                repository_root=root,
            )
        except (DemoBundleError, OSError, ValueError):
            raise DemoReleaseIntegrityError() from None

        # The validator returns identities rather than decoded data. Snapshot the two fixed files
        # once here, then require those exact bytes to match the validator's report before parsing.
        bundle_bytes = _read_bounded(release_dir / BUNDLE_FILENAME, MAX_BUNDLE_BYTES)
        manifest_bytes = _read_bounded(release_dir / MANIFEST_FILENAME, MAX_MANIFEST_BYTES)
        if (
            hashlib.sha256(bundle_bytes).hexdigest() != report.bundle_sha256
            or hashlib.sha256(manifest_bytes).hexdigest() != report.manifest_sha256
            or report.manifest_sha256 != expected_manifest_sha256
            or not report.bundle_ready
            or report.release_id != RELEASE_ID
            or report.evidence_kind != EVIDENCE_KIND
        ):
            raise DemoReleaseIntegrityError()
        try:
            decoded = json.loads(bundle_bytes.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            raise DemoReleaseIntegrityError() from None
        bundle = _freeze(decoded)
        if (
            bundle["schema_version"] != SCHEMA_VERSION
            or bundle["release_id"] != RELEASE_ID
            or bundle["evidence_kind"] != EVIDENCE_KIND
        ):
            raise DemoReleaseIntegrityError()

        history: dict[int, list[Mapping[str, Any]]] = {}
        for row in bundle["history_rows"]:
            history.setdefault(row["store_id"], []).append(row)
        history_index = MappingProxyType(
            {
                store_id: tuple(sorted(rows, key=lambda row: row["date"]))
                for store_id, rows in history.items()
            }
        )

        forecasts: dict[tuple[int, str], list[Mapping[str, Any]]] = {}
        for row in bundle["forecast_rows"]:
            key = (row["store_id"], row["forecast_origin"])
            forecasts.setdefault(key, []).append(row)
        forecast_index = MappingProxyType(
            {
                key: tuple(sorted(rows, key=lambda row: row["horizon"]))
                for key, rows in forecasts.items()
            }
        )

        uncertainty_index = MappingProxyType(
            {
                (view["store_id"], view["forecast_origin"], view["fit_id"]): view
                for view in bundle["uncertainty_views"]
            }
        )
        inventory_index = MappingProxyType(
            {view["case_id"]: view for view in bundle["inventory_views"]}
        )
        return cls._from_verified(
            _token=_VERIFIED_PROVIDER_TOKEN,
            profile=profile,
            release_id=RELEASE_ID,
            evidence_kind=EVIDENCE_KIND,
            schema_version=SCHEMA_VERSION,
            source_kind=bundle["source_declaration"]["kind"],
            bundle_sha256=report.bundle_sha256,
            manifest_sha256=report.manifest_sha256,
            limitations=tuple(bundle["limitations"]),
            _bundle=bundle,
            _query_allowlist=bundle["query_allowlist"],
            _history_by_store=history_index,
            _forecasts_by_query=forecast_index,
            _uncertainty_by_query=uncertainty_index,
            _comparison_rows=tuple(bundle["comparison_panel"]["rows"]),
            _inventory_by_case=inventory_index,
        )

    def provenance(self, view_id: str, selected_rows: int) -> SyntheticProvenance:
        """Create truthful response provenance without canonical phase or run assertions."""
        return SyntheticProvenance(
            release_id=self.release_id,
            evidence_kind=self.evidence_kind,
            bundle_sha256=self.bundle_sha256,
            manifest_sha256=self.manifest_sha256,
            schema_version=self.schema_version,
            source_kind=self.source_kind,
            view_id=view_id,
            selected_rows=selected_rows,
        )

    @property
    def bundle(self) -> Mapping[str, Any]:
        """Read-only access for the service layer to already frozen fixed catalog metadata."""
        return self._bundle

    @property
    def query_allowlist(self) -> Mapping[str, Any]:
        return self._query_allowlist

    @property
    def history_by_store(self) -> Mapping[int, tuple[Mapping[str, Any], ...]]:
        return self._history_by_store

    @property
    def forecasts_by_query(self) -> Mapping[tuple[int, str], tuple[Mapping[str, Any], ...]]:
        return self._forecasts_by_query

    @property
    def uncertainty_by_query(self) -> Mapping[tuple[int, str, str], Mapping[str, Any]]:
        return self._uncertainty_by_query

    @property
    def comparison_rows(self) -> tuple[Mapping[str, Any], ...]:
        return self._comparison_rows

    @property
    def inventory_by_case(self) -> Mapping[str, Mapping[str, Any]]:
        return self._inventory_by_case
