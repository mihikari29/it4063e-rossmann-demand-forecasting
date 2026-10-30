"""Immutable, synthetic-only M4-A publication; no outcome or release capability.

The trusted caller supplies in-memory parents and an independent expected binding.
Hashes establish content integrity, not custody, historical availability or human
authorization. Files are fsynced and directories published without replacement.
Two directory renames are not a transaction; Windows power-loss durability is not
claimed. An unreceipted final directory is retained for explicit reconciliation.
Staging directories, including empty successful stages, are retained inert: portable
pathname-based recursive cleanup cannot bind deletion to the invocation's ownership.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tempfile
from dataclasses import dataclass, field, fields, replace
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.data.cc02_preparation import (
    PreparationError,
    _assert_no_aliases,
    _rename_final_directory,
)
from rossmann_forecasting.features.contract import PREDICTOR_COLUMNS, predictor_schema
from rossmann_forecasting.forecasting.lightgbm import (
    CATEGORICAL_COLUMNS,
    FIXED_PARAMETERS,
    FittedLightGBM,
    vocabulary_hashes,
)
from rossmann_forecasting.forecasting.lightgbm_evaluation import TRIAL_PARAMETERS
from rossmann_forecasting.phase13.adapters import (
    OriginFrozenStandingTargets,
    Phase13M3Adapter,
    Phase13M3Issuance,
    SyntheticFitBQuantileFixture,
    SyntheticHistoricalMeanAnchor,
    SyntheticHistoricalMeanAnchorCollection,
)
from rossmann_forecasting.phase13.contracts import (
    ForecastOrigin,
    RequestedForecastGrid,
    SourceProvenance,
    SyntheticPlannedOpen,
)
from rossmann_forecasting.phase13.issuer import (
    NUM_BOOST_ROUND,
    RawForecastIssuance,
    _frozen_recipe,
    _identity,
    _model_and_fit_identities,
    _schema_identity,
)

SCOPE = "synthetic_selected_model_issuance"
VERSION = "phase13-m4a-v1"
MAX_MANIFEST_BYTES = 256 * 1024
MAX_METADATA_BYTES = 1024 * 1024
MAX_TABLE_BYTES = 64 * 1024 * 1024
MAX_MODEL_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
_REPOSITORY = Path(__file__).absolute().parents[3]
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_RAW_COLUMNS = frozenset(
    "requested_key Store Date forecast_origin horizon model raw_forecast unclipped_forecast "
    "recursive_state_value forecast_was_clipped forecast_available unavailable_reason "
    "unseen_store_category unseen_state_holiday unseen_store_type unseen_assortment "
    "model_identity fit_identity recipe_identity feature_schema_identity requested_grid_identity "
    "training_input_identity recursive_history_identity future_covariate_identity".split()
)
_TABLE_NAMES = (
    "raw_records.json",
    "planned_open.json",
    "daily_quantiles.json",
    "cumulative_quantiles.json",
    "issued_records.json",
    "issued_prefixes.json",
    "standing_targets.json",
)
_PAYLOAD_NAMES = frozenset((*_TABLE_NAMES, "metadata.json", "anchors.json", "adapter_state.json"))
_ENVIRONMENT_KEYS = frozenset(
    "python lightgbm lightgbm_build numpy pandas pyarrow os architecture cpu num_threads uv".split()
)
_PREPARED_TOKEN = object()
_VERIFIED_TOKEN = object()


class Phase13PublicationError(ValueError):
    """Invalid synthetic publication, unsafe path, or failed publication I/O."""


class PublicationConflictError(Phase13PublicationError):
    """An immutable origin already has different content."""


class IncompletePublicationError(Phase13PublicationError):
    """An incomplete publication requires explicit operator reconciliation."""


def _boundary(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Phase13PublicationError:
            raise
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            OverflowError,
            OSError,
            RecursionError,
        ):
            raise Phase13PublicationError(
                "Synthetic publication validation or I/O failed; no release is authorized."
            ) from None

    return checked


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Phase13PublicationError(message)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _domain_hash(domain: str, body: Any) -> str:
    return _sha(domain.encode("ascii") + b"\0" + _canonical(body))


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate JSON field.")
        result[key] = value
    return result


def _reject_constant(_value):
    raise Phase13PublicationError("Nonfinite JSON number.")


def _json_tree(value: Any, depth: int = 0) -> None:
    _require(depth <= 32, "JSON nesting exceeds the fixture contract.")
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float:
        _require(math.isfinite(value), "Nonfinite JSON number.")
        return
    _require(type(value) in (dict, list), "Unsupported JSON value.")
    for item in value.values() if isinstance(value, dict) else value:
        _json_tree(item, depth + 1)


def _decode(content: bytes, limit: int) -> Any:
    _require(type(content) is bytes and len(content) <= limit, "Encoded-size limit exceeded.")
    value = json.loads(
        content.decode("utf-8", errors="strict"),
        object_pairs_hook=_no_duplicates,
        parse_constant=_reject_constant,
    )
    _json_tree(value)
    _require(_canonical(value) == content, "JSON is not canonical.")
    return value


def _scalar(value: Any) -> Any:
    """A deliberately narrow scalar codec; never coerce arrays, Booleans or keys."""
    if value is None:
        return None
    if value is pd.NA or value is pd.NaT:
        return {"kind": "missing", "value": "pd.NA" if value is pd.NA else "pd.NaT"}
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        _require(-(2**63) <= int(value) < 2**63, "Integer outside int64.")
        return int(value)
    if isinstance(value, (float, np.floating)):
        _require(
            not isinstance(value, np.floating) or value.dtype.itemsize <= 8,
            "Floating-point type exceeds the float64 publication contract.",
        )
        number = float(value)
        if math.isnan(number):
            return {"kind": "missing", "value": "nan"}
        _require(math.isfinite(number), "Nonfinite table value.")
        return number
    if isinstance(value, (str, np.str_)):
        return str(value)
    if isinstance(value, pd.Timestamp):
        _require(value.tz is None, "Timezone-aware table value.")
        return {"kind": "timestamp", "value": value.isoformat()}
    if type(value) is date:
        return {"kind": "date", "value": value.isoformat()}
    if type(value) is tuple:
        _require(all(type(item) is str for item in value), "Unsupported tuple cell.")
        return {"kind": "tuple", "value": list(value)}
    raise Phase13PublicationError("Unsupported nonscalar or table cell type.")


def _unscalar(value: Any) -> Any:
    if type(value) is not dict:
        _require(value is None or type(value) in (str, bool, int, float), "Invalid cell.")
        return value
    _require(set(value) == {"kind", "value"}, "Unknown tagged-cell field.")
    kind, item = value["kind"], value["value"]
    if kind == "missing":
        _require(item in ("pd.NA", "pd.NaT", "nan"), "Unknown missing sentinel.")
        return {"pd.NA": pd.NA, "pd.NaT": pd.NaT, "nan": float("nan")}[item]
    if kind == "timestamp":
        return pd.Timestamp(item)
    if kind == "date":
        return date.fromisoformat(item)
    if kind == "tuple":
        _require(type(item) is list and all(type(x) is str for x in item), "Invalid tuple.")
        return tuple(item)
    raise Phase13PublicationError("Unknown tagged-cell kind.")


def _dtype(dtype: Any) -> dict[str, str]:
    name = str(dtype)
    if isinstance(dtype, pd.StringDtype):
        return {
            "name": "string",
            "storage": dtype.storage,
            "missing": "pd.NA" if dtype.na_value is pd.NA else "nan",
        }
    _require(
        name in {"object", "bool", "boolean", "float64", "float32"}
        or re.fullmatch(r"[uU]?[iI]nt(?:8|16|32|64)", name) is not None
        or name in {f"datetime64[{unit}]" for unit in ("s", "ms", "us", "ns")},
        "Unsupported table dtype.",
    )
    return {"name": name}


def _table_bytes(frame: pd.DataFrame) -> bytes:
    _require(isinstance(frame, pd.DataFrame), "Expected a table.")
    columns = list(frame.columns)
    _require(
        all(type(c) is str for c in columns) and len(set(columns)) == len(columns),
        "Invalid table columns.",
    )
    body = {
        "schema_version": VERSION + ":table",
        "columns": columns,
        "dtypes": [_dtype(dtype) for dtype in frame.dtypes],
        "rows": [
            [_scalar(cell) for cell in row] for row in frame.itertuples(index=False, name=None)
        ],
    }
    content = _canonical(body)
    _require(len(content) <= MAX_TABLE_BYTES, "Table exceeds fixture byte limit.")
    return content


def _table_from_bytes(content: bytes) -> pd.DataFrame:
    body = _decode(content, MAX_TABLE_BYTES)
    _require(set(body) == {"schema_version", "columns", "dtypes", "rows"}, "Table schema mismatch.")
    _require(body["schema_version"] == VERSION + ":table", "Unknown table version.")
    columns, dtypes, rows = body["columns"], body["dtypes"], body["rows"]
    _require(len(columns) == len(dtypes), "Invalid dtype count.")
    _require(all(len(row) == len(columns) for row in rows), "Invalid table row length.")
    result = {}
    for index, (column, descriptor) in enumerate(zip(columns, dtypes, strict=True)):
        if descriptor.get("name") == "string":
            _require(set(descriptor) == {"name", "storage", "missing"}, "String dtype mismatch.")
            _require(descriptor["missing"] in ("pd.NA", "nan"), "String null mismatch.")
            dtype = pd.StringDtype(
                storage=descriptor["storage"],
                na_value=pd.NA if descriptor["missing"] == "pd.NA" else np.nan,
            )
        else:
            _require(set(descriptor) == {"name"}, "Unknown dtype field.")
            dtype = pd.api.types.pandas_dtype(descriptor["name"])
        _require(_dtype(dtype) == descriptor, "Unsupported dtype descriptor.")
        result[column] = pd.Series([_unscalar(row[index]) for row in rows], dtype=dtype)
    frame = pd.DataFrame(result, columns=columns)
    _require(_table_bytes(frame) == content, "Table decode changed types or values.")
    return frame


def _plain(value: Any) -> Any:
    """Metadata serialization uses only explicitly supported, non-path data values."""
    if hasattr(value, "__dataclass_fields__"):
        return {
            f.name: _plain(getattr(value, f.name))
            for f in fields(value)
            if not f.name.startswith("_")
        }
    if type(value) is dict:
        _require(all(type(k) is str for k in value), "Metadata keys must be strings.")
        return {k: _plain(v) for k, v in value.items()}
    if type(value) in (list, tuple):
        return [_plain(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return str(value)
    _require(value is None or type(value) in (bool, int, float), "Unsupported metadata scalar.")
    if type(value) is float:
        _require(math.isfinite(value), "Nonfinite metadata.")
    return value


@dataclass(frozen=True, slots=True)
class SyntheticModelState:
    """Trusted fixture handoff, not proof that bytes came from a real trained booster."""

    origin: date
    booster_bytes: bytes | None
    category_vocabularies: tuple[tuple[str, tuple[Any, ...]], ...]
    fit_row_count: int
    model_identity: str
    fit_identity: str
    recipe_identity: str
    feature_schema_identity: str
    model_parameters: tuple[tuple[str, Any], ...]
    failure_reason: str | None = None
    requested_boost_rounds: int = NUM_BOOST_ROUND
    actual_tree_count: int | None = NUM_BOOST_ROUND
    ordered_predictors: tuple[str, ...] = PREDICTOR_COLUMNS


@dataclass(frozen=True, slots=True)
class TrustedSyntheticParents:
    raw_issuance: RawForecastIssuance
    planned_open: SyntheticPlannedOpen
    quantiles: SyntheticFitBQuantileFixture
    anchors: SyntheticHistoricalMeanAnchorCollection
    model_state: SyntheticModelState


@dataclass(frozen=True, slots=True)
class PublicationMetadata:
    fixture_id: str
    protocol_sha256: str
    configuration_sha256: str
    code_revision: str
    code_worktree_dirty: bool
    lock_sha256: str
    command: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    input_provenance: tuple[tuple[str, SourceProvenance], ...]
    phase7_lineage: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class PublicationBinding:
    origin: date
    grid_identity: str
    publication_id: str
    manifest_sha256: str
    receipt_sha256: str


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    origin: date
    publication_id: str
    manifest_sha256: str
    receipt_id: str
    receipt_sha256: str
    scope: str = SCOPE
    release_eligible: bool = False


@dataclass(frozen=True, slots=True)
class PreparedPublication:
    """Immutable bytes sealed after authoritative synthetic-parent validation."""

    binding: PublicationBinding
    _files: tuple[tuple[str, bytes], ...]
    _manifest: bytes
    _receipt: bytes
    _token: object = field(default=None, init=False, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class VerifiedPublication:
    binding: PublicationBinding
    receipt: PublicationReceipt
    _issued_records: bytes
    _issued_prefixes: bytes
    _standing_targets: bytes
    _token: object = field(default=None, init=False, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class VerifiedIssuedView:
    """Copy-safe label-free view, with no provider, daily release or evaluation method."""

    receipt: PublicationReceipt
    _records: bytes
    _prefixes: bytes
    _targets: bytes

    @_boundary
    def to_frame(self) -> pd.DataFrame:
        return _table_from_bytes(self._records)

    @_boundary
    def prefixes_to_frame(self) -> pd.DataFrame:
        return _table_from_bytes(self._prefixes)

    @_boundary
    def targets_to_frame(self) -> pd.DataFrame:
        return _table_from_bytes(self._targets)


@dataclass(frozen=True)
class _BoosterTextSnapshot:
    text: str

    def model_to_string(self) -> str:
        return self.text


def _model_document(parents: TrustedSyntheticParents) -> dict[str, Any]:
    raw, state = parents.raw_issuance, parents.model_state
    _require(isinstance(state, SyntheticModelState), "Missing typed synthetic model-state handoff.")
    _require(
        type(state.origin) is date and state.origin == raw.origin,
        "Model-state origin mismatch.",
    )
    recipe = _frozen_recipe()
    _require(
        state.recipe_identity == raw.recipe_identity == _identity(recipe)
        and state.feature_schema_identity == raw.feature_schema_identity == _schema_identity()
        and state.ordered_predictors == PREDICTOR_COLUMNS,
        "Model-state recipe or feature schema mismatch.",
    )
    parameters = dict(state.model_parameters)
    _require(
        len(parameters) == len(state.model_parameters)
        and _canonical(parameters) == _canonical({**FIXED_PARAMETERS, **TRIAL_PARAMETERS["A"]}),
        "Model-state parameters differ from frozen Trial A.",
    )
    _require(
        type(state.fit_row_count) is int
        and state.fit_row_count >= 0
        and state.fit_row_count == raw.training_counts.fitted_eligible_rows
        and type(state.requested_boost_rounds) is int
        and state.requested_boost_rounds == raw.requested_boost_rounds == NUM_BOOST_ROUND,
        "Model-state row/round counts mismatch.",
    )
    counts = raw.training_counts
    _require(
        all(
            type(getattr(counts, f.name)) is int and getattr(counts, f.name) >= 0
            for f in fields(counts)
        )
        and counts.input_rows
        == counts.valid_observed_label_rows + counts.missing_label_excluded_rows
        and counts.fitted_eligible_rows == counts.eligible_source_open_rows
        and counts.fitted_eligible_rows + counts.observed_closed_history_rows
        <= counts.valid_observed_label_rows,
        "Training row counts do not reconcile.",
    )
    _require(
        type(state.category_vocabularies) is tuple
        and tuple(k for k, _ in state.category_vocabularies) == CATEGORICAL_COLUMNS,
        "Category vocabulary schema/order mismatch.",
    )
    vocabularies = {}
    for column, values in state.category_vocabularies:
        _require(type(values) is tuple, "Category values must be immutable tuples.")
        kind = int if column == "Store" else str
        _require(all(type(v) is kind for v in values), "Category scalar type mismatch.")
        _require(values == tuple(sorted(set(values))), "Category values must be unique and sorted.")
        vocabularies[column] = values
    _require(
        set(vocabularies["Store"]).issubset(parents.anchors.store_ids),
        "Model category vocabulary exceeds the declared synthetic Store subset.",
    )
    category_hashes = vocabulary_hashes(vocabularies)
    _require(
        tuple(category_hashes.items()) == raw.category_vocabulary_hashes,
        "Category vocabulary hashes mismatch.",
    )
    if state.booster_bytes is None:
        _require(
            state.actual_tree_count is None
            and raw.actual_tree_count is None
            and state.failure_reason in ("model_fit_failure", "no_eligible_training_rows")
            and raw.available_row_count == 0
            and (state.fit_row_count == 0) == (state.failure_reason == "no_eligible_training_rows")
            and raw.to_frame()["unavailable_reason"]
            .isin((state.failure_reason, "missing_target_key"))
            .all(),
            "Missing booster requires an explicit unavailable fit.",
        )
        booster = None
    else:
        _require(
            type(state.booster_bytes) is bytes
            and 0 < len(state.booster_bytes) <= MAX_MODEL_BYTES
            and state.failure_reason is None
            and type(state.actual_tree_count) is int
            and state.actual_tree_count == raw.actual_tree_count == NUM_BOOST_ROUND
            and state.fit_row_count > 0,
            "Invalid available model-state handoff.",
        )
        booster = _BoosterTextSnapshot(state.booster_bytes.decode("utf-8", errors="strict"))
    fitted = FittedLightGBM(
        booster=booster,
        category_vocabularies=vocabularies,
        fit_row_count=state.fit_row_count,
        forecast_origin=pd.Timestamp(state.origin),
        model_parameters=parameters,
        failure_reason=state.failure_reason,
    )
    # The accepted M2 identity routine only reads the already supplied text snapshot.
    # It neither loads a native booster nor performs fitting/prediction.
    model_id, fit_id = _model_and_fit_identities(
        fitted,
        recipe_identity=state.recipe_identity,
        schema_identity=state.feature_schema_identity,
        origin=ForecastOrigin(state.origin),
        input_identities=raw.input_identities,
        category_hashes=category_hashes,
        actual_tree_count=state.actual_tree_count,
    )
    _require(
        state.model_identity == raw.model_identity == model_id
        and state.fit_identity == raw.fit_identity == fit_id,
        "Model-state bytes or fresh-fit identity mismatch.",
    )
    document = _plain(
        {f.name: getattr(state, f.name) for f in fields(state) if f.name != "booster_bytes"}
    )
    document.update(
        schema_version=VERSION + ":model",
        content_classification="trusted_synthetic_fixture_handoff",
        booster_sha256=None if state.booster_bytes is None else _sha(state.booster_bytes),
        category_vocabulary_hashes=category_hashes,
        recipe=recipe,
        feature_schema=predictor_schema(),
        real_trained_booster_provenance_proven=False,
    )
    document["model_parameters"] = _plain(tuple(sorted(parameters.items())))
    return document


def _validate_metadata(metadata: PublicationMetadata) -> None:
    _require(isinstance(metadata, PublicationMetadata), "Publication requires typed metadata.")
    _require(
        type(metadata.fixture_id) is str
        and re.fullmatch(r"synthetic://phase13/[a-zA-Z0-9._-]+", metadata.fixture_id) is not None,
        "Publication must declare a synthetic fixture identity.",
    )
    for digest in (metadata.protocol_sha256, metadata.configuration_sha256, metadata.lock_sha256):
        _require(
            type(digest) is str and _SHA256.fullmatch(digest) is not None, "Invalid metadata hash."
        )
    _require(
        re.fullmatch(r"[0-9a-f]{40}", metadata.code_revision) is not None
        and type(metadata.code_worktree_dirty) is bool,
        "Invalid code identity.",
    )
    _require(
        type(metadata.command) is tuple
        and bool(metadata.command)
        and all(type(x) is str and bool(x.strip()) for x in metadata.command),
        "Missing command/configuration provenance.",
    )
    environment = dict(metadata.environment)
    _require(
        len(environment) == len(metadata.environment)
        and set(environment) == _ENVIRONMENT_KEYS
        and all(type(x) is str and bool(x.strip()) for x in environment.values())
        and environment["num_threads"] == "4"
        and environment["uv"] == "0.12.23",
        "Incomplete environment/lock provenance.",
    )
    provenance = dict(metadata.input_provenance)
    _require(
        len(provenance) == len(metadata.input_provenance)
        and set(provenance) == {"training", "recursive_history", "future_covariates"}
        and all(isinstance(x, SourceProvenance) for x in provenance.values()),
        "Incomplete typed input provenance.",
    )
    lineage = dict(metadata.phase7_lineage)
    _require(
        len(lineage) == len(metadata.phase7_lineage)
        and set(lineage)
        == {"selection_run_id", "selection_manifest_sha256", "configuration_sha256"}
        and type(lineage["selection_run_id"]) is str
        and bool(lineage["selection_run_id"])
        and all(_SHA256.fullmatch(lineage[k]) is not None for k in lineage if k.endswith("sha256")),
        "Incomplete selection lineage.",
    )


def _authoritative(
    parents: TrustedSyntheticParents,
) -> tuple[
    Phase13M3Issuance,
    OriginFrozenStandingTargets,
    dict[str, Any],
    TrustedSyntheticParents,
]:
    _require(isinstance(parents, TrustedSyntheticParents), "Missing trusted synthetic parents.")
    raw, schedule, quantiles, anchors = (
        parents.raw_issuance,
        parents.planned_open,
        parents.quantiles,
        parents.anchors,
    )
    _require(
        isinstance(raw, RawForecastIssuance)
        and isinstance(schedule, SyntheticPlannedOpen)
        and isinstance(quantiles, SyntheticFitBQuantileFixture)
        and isinstance(anchors, SyntheticHistoricalMeanAnchorCollection),
        "Publication requires all authoritative typed parents.",
    )
    raw_frame = raw.to_frame()
    _require(set(raw_frame.columns) == _RAW_COLUMNS, "Unknown/missing raw record field.")
    # Encode before M3: reject nonscalars and preserve bool/int distinctions even
    # where pandas equality would consider an object Boolean equal to an integer.
    _table_bytes(raw_frame)
    for column in (
        "forecast_available",
        "forecast_was_clipped",
        "unseen_store_category",
        "unseen_state_holiday",
        "unseen_store_type",
        "unseen_assortment",
    ):
        for value in raw_frame[column]:
            encoded = _scalar(value)
            _require(
                type(encoded) is bool or encoded is None or type(encoded) is dict,
                "Boolean diagnostic contains a numeric value.",
            )
    model_document = _model_document(parents)
    # Rebuild parent objects whose public attributes can be reassigned, checking
    # the declared identity against their freshly validated content.
    grid = RequestedForecastGrid(raw.origin, anchors.store_ids)
    clean_schedule = SyntheticPlannedOpen(
        schedule.to_frame(),
        grid=grid,
        provenance=replace(schedule.provenance),
        rule_id=schedule.rule_id,
    )
    _require(clean_schedule.identity == schedule.identity, "Schedule parent content changed.")
    _require(
        quantiles.content_classification == "synthetic_fixture_content_only",
        "Quantile content must retain its synthetic fixture classification.",
    )
    clean_quantiles = SyntheticFitBQuantileFixture(
        quantiles.daily_to_frame(),
        quantiles.cumulative_to_frame(),
        fixture_id=quantiles.fixture_id,
        transport=replace(quantiles.transport),
        calibration_metadata=replace(quantiles.calibration_metadata),
        expected_daily_fixture_sha256=quantiles.daily_fixture_sha256,
        expected_cumulative_fixture_sha256=quantiles.cumulative_fixture_sha256,
    )
    _require(
        _canonical(_plain(clean_quantiles)) == _canonical(_plain(quantiles)),
        "Quantile parent metadata or identity changed.",
    )
    _require(
        all(isinstance(anchor, SyntheticHistoricalMeanAnchor) for anchor in anchors.anchors),
        "Anchor collection requires typed synthetic entries.",
    )
    clean_anchors = SyntheticHistoricalMeanAnchorCollection(
        origin=anchors.origin,
        store_ids=anchors.store_ids,
        anchors=tuple(
            replace(anchor, provenance=replace(anchor.provenance)) for anchor in anchors.anchors
        ),
    )
    _require(
        _canonical(_plain(clean_anchors)) == _canonical(_plain(anchors)),
        "Anchor parent content or provenance changed.",
    )
    issued = Phase13M3Adapter().issue(raw, clean_schedule, clean_quantiles)
    _require(grid.identity == issued.grid_identity, "Store universe mismatch.")
    targets = issued.build_standing_targets(clean_anchors)
    _require(
        len(issued.to_frame()) == 14 * len(grid.store_ids)
        and len(issued.prefixes_to_frame()) == 42 * len(grid.store_ids)
        and len(targets.to_frame()) == 36 * len(grid.store_ids),
        "Incomplete issuance/prefix/paired-target grid.",
    )
    clean_parents = replace(
        parents, planned_open=clean_schedule, quantiles=clean_quantiles, anchors=clean_anchors
    )
    return issued, targets, model_document, clean_parents


def _assemble(
    parents: TrustedSyntheticParents,
    issued: Phase13M3Issuance,
    targets: OriginFrozenStandingTargets,
    model_document: dict[str, Any],
    metadata: PublicationMetadata,
) -> PreparedPublication:
    _validate_metadata(metadata)
    tables = dict(
        zip(
            _TABLE_NAMES,
            (
                parents.raw_issuance.to_frame(),
                parents.planned_open.to_frame(),
                parents.quantiles.daily_to_frame(),
                parents.quantiles.cumulative_to_frame(),
                issued.to_frame(),
                issued.prefixes_to_frame(),
                targets.to_frame(),
            ),
            strict=True,
        )
    )
    # These evidence collections have unordered semantic keys upstream. Canonical
    # publication order must not depend on their caller-supplied row/pair order.
    # Requested raw/M3 grids, by contrast, must already have the exact H14 order.
    for name, keys in (
        ("daily_quantiles.json", ["horizon", "tail"]),
        ("cumulative_quantiles.json", ["k", "p"]),
    ):
        tables[name] = tables[name].sort_values(keys, kind="stable").reset_index(drop=True)
    files = {name: _table_bytes(frame) for name, frame in tables.items()}
    run_document = _plain(metadata)
    for name in ("environment", "input_provenance", "phase7_lineage"):
        run_document[name].sort(key=lambda pair: pair[0])
    document = {
        "schema_version": VERSION + ":metadata",
        "scope": SCOPE,
        "release_eligible": False,
        "run": run_document,
        "raw": _plain(parents.raw_issuance),
        "schedule": _plain(parents.planned_open.provenance),
        "schedule_rule_id": parents.planned_open.rule_id,
        "quantiles": _plain(parents.quantiles),
        "issuance": _plain(issued),
        "targets": _plain(targets),
    }
    files["metadata.json"] = _canonical(document)
    anchor_document = _plain(parents.anchors)
    anchor_document["anchors"].sort(key=lambda anchor: anchor["store_id"])
    files["anchors.json"] = _canonical(anchor_document)
    files["adapter_state.json"] = _canonical(model_document)
    if parents.model_state.booster_bytes is not None:
        files["booster.txt"] = parents.model_state.booster_bytes
    for name in ("metadata.json", "anchors.json", "adapter_state.json"):
        _require(len(files[name]) <= MAX_METADATA_BYTES, "Metadata exceeds fixture byte limit.")
    _require(sum(map(len, files.values())) <= MAX_TOTAL_BYTES, "Publication exceeds fixture limit.")
    inventory = {}
    for name, content in sorted(files.items()):
        entry = {"bytes": len(content), "sha256": _sha(content)}
        if name in tables:
            frame = tables[name]
            entry.update(
                rows=len(frame),
                columns=list(frame.columns),
                dtypes=[_dtype(d) for d in frame.dtypes],
            )
        inventory[name] = entry
    body = {
        "schema_version": VERSION + ":manifest",
        "scope": SCOPE,
        "release_eligible": False,
        "origin": issued.origin.isoformat(),
        "grid_identity": issued.grid_identity,
        "store_ids": list(parents.anchors.store_ids),
        "issuance_identity": issued.issuance_identity,
        "files": inventory,
        "receipt_contract": VERSION + ":receipt",
        "availability": {
            "raw_available": parents.raw_issuance.available_row_count,
            "raw_unavailable": parents.raw_issuance.unavailable_row_count,
            "complete_path_available": parents.raw_issuance.complete_path_available,
            "operational_available": int(issued.to_frame()["operational_forecast_available"].sum()),
            "targets_available": int(targets.to_frame()["target_available"].sum()),
        },
    }
    publication_id = _domain_hash(VERSION + ":publication", body)
    manifest = _canonical({**body, "publication_id": publication_id})
    _require(len(manifest) <= MAX_MANIFEST_BYTES, "Manifest exceeds fixture byte limit.")
    receipt_body = {
        "schema_version": VERSION + ":receipt",
        "scope": SCOPE,
        "release_eligible": False,
        "origin": issued.origin.isoformat(),
        "grid_identity": issued.grid_identity,
        "publication_id": publication_id,
        "manifest_sha256": _sha(manifest),
        "comparator_complete": False,
        "inventory_initial_state_complete": False,
        "protected_access_authorized": False,
    }
    receipt = _canonical(
        {**receipt_body, "receipt_id": _domain_hash(VERSION + ":receipt", receipt_body)}
    )
    binding = PublicationBinding(
        issued.origin, issued.grid_identity, publication_id, _sha(manifest), _sha(receipt)
    )
    prepared = PreparedPublication(binding, tuple(sorted(files.items())), manifest, receipt)
    object.__setattr__(prepared, "_token", _PREPARED_TOKEN)
    return prepared


@_boundary
def prepare_publication(
    *,
    parents: TrustedSyntheticParents,
    issuance: Phase13M3Issuance,
    targets: OriginFrozenStandingTargets,
    metadata: PublicationMetadata,
) -> PreparedPublication:
    """Revalidate against authoritative parents and freeze bytes without filesystem I/O."""
    _require(
        isinstance(issuance, Phase13M3Issuance)
        and isinstance(targets, OriginFrozenStandingTargets),
        "Expected typed M3 issuance and targets.",
    )
    authoritative, authoritative_targets, model, clean_parents = _authoritative(parents)
    _require(
        _canonical(_plain(issuance)) == _canonical(_plain(authoritative)), "M3 metadata mismatch."
    )
    _require(
        _canonical(_plain(targets)) == _canonical(_plain(authoritative_targets)),
        "Target metadata mismatch.",
    )
    for actual, expected in (
        (issuance.to_frame(), authoritative.to_frame()),
        (issuance.prefixes_to_frame(), authoritative.prefixes_to_frame()),
        (targets.to_frame(), authoritative_targets.to_frame()),
    ):
        _require(
            _table_bytes(actual) == _table_bytes(expected), "Snapshot differs from typed parents."
        )
    return _assemble(clean_parents, authoritative, authoritative_targets, model, metadata)


def _fixture_root(value: Path) -> Path:
    root = Path(value)
    _require(
        root.is_absolute() and ".." not in root.parts and not str(root).startswith("\\\\"),
        "Fixture root must be an absolute local path without traversal.",
    )
    _assert_no_aliases(root)
    root = root.absolute()
    temporary = Path(tempfile.gettempdir()).absolute()
    _require(
        root != temporary
        and root.is_relative_to(temporary)
        and not root.is_relative_to(_REPOSITORY)
        and not _REPOSITORY.is_relative_to(root),
        "Fixture root must be a dedicated temporary directory outside the checkout.",
    )
    _require(
        root.parent.is_dir(), "The dedicated fixture root requires an existing temporary parent."
    )
    for name in ("issuances", "receipts", ".staging"):
        _assert_no_aliases(root / name)
    return root


def _paths(root: Path, origin: date) -> tuple[Path, Path]:
    _require(type(origin) is date, "Binding origin must be a calendar date.")
    name = ForecastOrigin(origin).value.isoformat()
    issue, receipt = root / "issuances" / name, root / "receipts" / name
    _assert_no_aliases(issue)
    _assert_no_aliases(receipt)
    return issue, receipt


def _validate_binding(binding: PublicationBinding) -> None:
    _require(isinstance(binding, PublicationBinding), "An independent typed binding is required.")
    ForecastOrigin(binding.origin)
    for descriptor in fields(binding):
        if descriptor.name != "origin":
            value = getattr(binding, descriptor.name)
            _require(
                type(value) is str and _SHA256.fullmatch(value) is not None,
                "Invalid binding identity.",
            )


def _limit(name: str) -> int:
    if name == "booster.txt":
        return MAX_MODEL_BYTES
    if name in _TABLE_NAMES:
        return MAX_TABLE_BYTES
    if name in ("manifest.json", "receipt.json"):
        return MAX_MANIFEST_BYTES
    return MAX_METADATA_BYTES


def _file_signature(info: os.stat_result) -> tuple[int, ...]:
    """Fail closed unless this filesystem exposes an unaliased regular-file identity."""
    _require(
        stat.S_ISREG(info.st_mode)
        and info.st_nlink == 1
        and not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT,
        "Expected an unaliased regular file.",
    )
    _require(
        type(info.st_dev) is int
        and info.st_dev >= 0
        and type(info.st_ino) is int
        and info.st_ino > 0,
        "Reliable filesystem identity is unavailable.",
    )
    return (
        info.st_dev,
        info.st_ino,
        stat.S_IFMT(info.st_mode),
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
    )


def _regular(path: Path) -> os.stat_result:
    _assert_no_aliases(path)
    info = path.lstat()
    _file_signature(info)
    _require(info.st_size <= _limit(path.name), "File exceeds fixture byte limit.")
    return info


def _directory(path: Path, names: set[str]) -> None:
    _assert_no_aliases(path)
    _require(path.is_dir(), "Missing publication directory.")
    entries = list(path.iterdir())
    _require({p.name for p in entries} == names, "Missing or extra publication files.")
    total = 0
    for entry in entries:
        total += _regular(entry).st_size
    _require(total <= MAX_TOTAL_BYTES, "Directory exceeds fixture byte limit.")


def _read(path: Path) -> bytes:
    before = _regular(path)
    with path.open("rb") as source:
        opened = os.fstat(source.fileno())
        _require(
            _file_signature(before) == _file_signature(opened) == _file_signature(_regular(path)),
            "Opened file identity changed before reading.",
        )
        # The admitted file size is already bounded. Reading the entire cap can
        # allocate 64 MiB even for a tiny fixture on buffered Windows streams.
        content = source.read(before.st_size + 1)
        after = os.fstat(source.fileno())

    _require(
        _file_signature(before) == _file_signature(after) == _file_signature(_regular(path)),
        "File changed while reading.",
    )
    _require(len(content) == before.st_size, "Truncated or oversized file.")
    return content


def _transition(_name: str) -> None:
    """Private failure-injection seam; no public callback or recovery capability."""


def _write(path: Path, content: bytes) -> None:
    _assert_no_aliases(path)
    with path.open("xb") as output:
        _require(output.write(content) == len(content), "Short write.")
        _transition("written:" + path.name)
        output.flush()
        os.fsync(output.fileno())
        _transition("fsynced:" + path.name)


def _sync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _verify_files(directory: Path, prepared: PreparedPublication, *, sealed: bool) -> None:
    expected = dict(prepared._files)
    if sealed:
        expected["manifest.json"] = prepared._manifest
    _directory(directory, set(expected))
    for name, content in expected.items():
        found = _read(directory / name)
        _require(found == content, "Publication content differs from validated payload.")
        if name.endswith(".json"):
            _decode(found, _limit(name))


def _receipt(prepared: PreparedPublication) -> PublicationReceipt:
    body = _decode(prepared._receipt, MAX_MANIFEST_BYTES)
    return PublicationReceipt(
        prepared.binding.origin,
        prepared.binding.publication_id,
        prepared.binding.manifest_sha256,
        body["receipt_id"],
        prepared.binding.receipt_sha256,
    )


def _check_prepared(prepared: PreparedPublication) -> None:
    _require(
        isinstance(prepared, PreparedPublication), "Expected a validated prepared publication."
    )
    _require(
        prepared._token is _PREPARED_TOKEN, "Payload was not prepared through typed validation."
    )
    _validate_binding(prepared.binding)
    files = dict(prepared._files)
    _require(len(files) == len(prepared._files), "Duplicate payload name.")
    _require(
        set(files) in (_PAYLOAD_NAMES, _PAYLOAD_NAMES | {"booster.txt"}),
        "Payload file set mismatch.",
    )
    manifest = _decode(prepared._manifest, MAX_MANIFEST_BYTES)
    receipt = _decode(prepared._receipt, MAX_MANIFEST_BYTES)
    publication_id = manifest.pop("publication_id")
    _require(
        publication_id
        == prepared.binding.publication_id
        == _domain_hash(VERSION + ":publication", manifest)
        and _sha(prepared._manifest) == prepared.binding.manifest_sha256
        and _sha(prepared._receipt) == prepared.binding.receipt_sha256,
        "Prepared publication binding mismatch.",
    )
    receipt_id = receipt.pop("receipt_id")
    _require(
        receipt_id == _domain_hash(VERSION + ":receipt", receipt), "Receipt identity mismatch."
    )
    _require(
        receipt["publication_id"] == publication_id
        and receipt["manifest_sha256"] == prepared.binding.manifest_sha256
        and receipt["grid_identity"] == manifest["grid_identity"] == prepared.binding.grid_identity
        and receipt["origin"] == manifest["origin"] == prepared.binding.origin.isoformat()
        and manifest["scope"] == receipt["scope"] == SCOPE
        and manifest["release_eligible"] is False
        and receipt["release_eligible"] is False,
        "Prepared receipt scope/binding mismatch.",
    )
    _require(set(manifest["files"]) == set(files), "Manifest inventory mismatch.")
    for name, content in files.items():
        _require(type(content) is bytes and len(content) <= _limit(name), "Invalid payload bytes.")
        entry = manifest["files"][name]
        _require(
            entry["bytes"] == len(content) and entry["sha256"] == _sha(content),
            "Payload hash mismatch.",
        )
        if name.endswith(".json"):
            _decode(content, _limit(name))
    _require(sum(map(len, files.values())) <= MAX_TOTAL_BYTES, "Payload exceeds fixture limit.")


def _verify_pair(issue: Path, receipt: Path, prepared: PreparedPublication) -> VerifiedPublication:
    _directory(receipt, {"receipt.json"})  # Check both trees for aliases before any content reads.
    _directory(issue, set(dict(prepared._files)) | {"manifest.json"})
    _verify_files(issue, prepared, sealed=True)
    _require(_read(receipt / "receipt.json") == prepared._receipt, "Receipt content mismatch.")
    files = dict(prepared._files)
    verified = VerifiedPublication(
        prepared.binding,
        _receipt(prepared),
        files["issued_records.json"],
        files["issued_prefixes.json"],
        files["standing_targets.json"],
    )
    object.__setattr__(verified, "_token", _VERIFIED_TOKEN)
    return verified


def _stage_identity(stage: Path) -> tuple[int, int]:
    _assert_no_aliases(stage)
    info = stage.lstat()
    _require(
        stat.S_ISDIR(info.st_mode)
        and type(info.st_dev) is int
        and info.st_dev >= 0
        and type(info.st_ino) is int
        and info.st_ino > 0,
        "Reliable staging directory identity is unavailable.",
    )
    return info.st_dev, info.st_ino


def _retain_stage(stage: Path, owned_identity: tuple[int, int]) -> None:
    """Audit ownership, never delete through a pathname that another process can replace.

    Even a matching identity does not bind a later rmtree/rmdir to that directory.
    All stages stay inert for explicit reconciliation; a displaced original is
    neither searched for nor removed, and final directories are never cleaned up.
    """
    try:
        _require(_stage_identity(stage) == owned_identity, "Staging identity changed.")
    except (OSError, Phase13PublicationError, PreparationError) as error:
        raise IncompletePublicationError(
            "Staging ownership changed or is uncertain; "
            "preserve all paths for explicit reconciliation."
        ) from error


@_boundary
def publish_publication(prepared: PreparedPublication, *, fixture_root: Path) -> PublicationReceipt:
    """No-replace publication. Incomplete final state is retained, never repaired."""
    _check_prepared(prepared)
    root = _fixture_root(fixture_root)
    issue, receipt = _paths(root, prepared.binding.origin)
    if issue.exists() or receipt.exists():
        if not issue.exists() or not receipt.exists():
            raise IncompletePublicationError(
                "Issuance/receipt pair is incomplete; reconcile explicitly."
            )
        _directory(receipt, {"receipt.json"})
        existing_names = {entry.name for entry in issue.iterdir()}
        allowed_names = _PAYLOAD_NAMES | {"manifest.json"}
        _require(
            existing_names in (allowed_names, allowed_names | {"booster.txt"}),
            "Missing or extra existing publication files.",
        )
        _directory(issue, existing_names)
        existing = _read(issue / "manifest.json")
        if existing != prepared._manifest:
            raise PublicationConflictError("Origin already has a different immutable publication.")
        return _verify_pair(issue, receipt, prepared).receipt
    for directory in (root, root / "issuances", root / "receipts", root / ".staging"):
        _assert_no_aliases(directory)
        directory.mkdir(parents=True, exist_ok=True)
        _assert_no_aliases(directory)
        _sync_directory(directory.parent)
    _transition("VALIDATED")
    stage = Path(tempfile.mkdtemp(prefix="m4a-", dir=root / ".staging"))
    try:
        owned_identity = _stage_identity(stage)
    except (OSError, Phase13PublicationError, PreparationError) as error:
        raise IncompletePublicationError(
            "Staging ownership could not be recorded; retain it for explicit reconciliation."
        ) from error
    try:
        staged_issue, staged_receipt = stage / "issue", stage / "receipt"
        staged_issue.mkdir()
        _transition("STAGING")
        _retain_stage(stage, owned_identity)
        for name, content in prepared._files:
            _write(staged_issue / name, content)
        _verify_files(staged_issue, prepared, sealed=False)
        _transition("STAGED_VERIFIED")
        _write(staged_issue / "manifest.json", prepared._manifest)
        _verify_files(staged_issue, prepared, sealed=True)
        _sync_directory(staged_issue)
        _sync_directory(stage)
        _transition("MANIFEST_SEALED")
        _retain_stage(stage, owned_identity)
        _assert_no_aliases(issue)
        _rename_final_directory(staged_issue, issue)
        _sync_directory(issue.parent)
        _sync_directory(stage)
        _transition("DIRECTORY_PUBLISHED")
        _verify_files(issue, prepared, sealed=True)
        staged_receipt.mkdir()
        _write(staged_receipt / "receipt.json", prepared._receipt)
        _require(
            _read(staged_receipt / "receipt.json") == prepared._receipt, "Receipt reread failed."
        )
        _sync_directory(staged_receipt)
        _sync_directory(stage)
        _transition("RECEIPT_STAGED")
        _retain_stage(stage, owned_identity)
        _assert_no_aliases(receipt)
        _rename_final_directory(staged_receipt, receipt)
        _sync_directory(receipt.parent)
        _sync_directory(stage)
        _transition("RECEIPT_PUBLISHED")
        verified = _verify_pair(issue, receipt, prepared)
        _transition("VERIFIED")
    except (OSError, Phase13PublicationError, PreparationError) as error:
        _retain_stage(stage, owned_identity)
        raise IncompletePublicationError(
            "Publication interrupted; staging and any final directories "
            "retained for explicit reconciliation."
        ) from error
    _retain_stage(stage, owned_identity)
    return verified.receipt


def _metadata_from_document(document: Any) -> PublicationMetadata:
    run = document["run"]
    _require(
        set(run) == {f.name for f in fields(PublicationMetadata)}, "Unknown run metadata fields."
    )
    provenance = []
    for role, source in run["input_provenance"]:
        _require(
            set(source) == {f.name for f in fields(SourceProvenance)}, "Unknown provenance fields."
        )
        source = {**source, "parent_identities": tuple(source["parent_identities"])}
        provenance.append((role, SourceProvenance(**source)))
    return PublicationMetadata(
        **{
            **run,
            "command": tuple(run["command"]),
            "environment": tuple(tuple(x) for x in run["environment"]),
            "input_provenance": tuple(provenance),
            "phase7_lineage": tuple(tuple(x) for x in run["phase7_lineage"]),
        }
    )


@_boundary
def verify_publication(
    *,
    fixture_root: Path,
    expected_binding: PublicationBinding,
    trusted_parents: TrustedSyntheticParents,
) -> VerifiedPublication:
    """Verify disk bytes against an independent binding AND authoritative typed parents."""
    _validate_binding(expected_binding)
    root = _fixture_root(fixture_root)
    issue, receipt = _paths(root, expected_binding.origin)
    if not issue.exists() or not receipt.exists():
        raise IncompletePublicationError("Issuance/receipt pair is incomplete; no trusted load.")
    # Check all entries/aliases before opening even the manifest. Booster absence
    # is explicit in the trusted sidecar, never guessed from missing disk files.
    _require(isinstance(trusted_parents, TrustedSyntheticParents), "Missing typed parents.")
    _require(isinstance(trusted_parents.model_state, SyntheticModelState), "Missing model sidecar.")
    names = set(_PAYLOAD_NAMES) | {"manifest.json"}
    if trusted_parents.model_state.booster_bytes is not None:
        names.add("booster.txt")
    _directory(issue, names)
    _directory(receipt, {"receipt.json"})
    manifest = _read(issue / "manifest.json")
    receipt_bytes = _read(receipt / "receipt.json")
    _require(
        _sha(manifest) == expected_binding.manifest_sha256
        and _sha(receipt_bytes) == expected_binding.receipt_sha256,
        "Independent manifest/receipt pin mismatch.",
    )
    metadata = _metadata_from_document(_decode(_read(issue / "metadata.json"), MAX_METADATA_BYTES))
    issued, targets, model, clean_parents = _authoritative(trusted_parents)
    prepared = _assemble(clean_parents, issued, targets, model, metadata)
    _require(
        prepared.binding == expected_binding, "Publication differs from trusted parent bindings."
    )
    _check_prepared(prepared)
    return _verify_pair(issue, receipt, prepared)


@_boundary
def load_issued_view(verified_publication: VerifiedPublication) -> VerifiedIssuedView:
    """Load a defensive snapshot; never reopen disk or acquire an outcome capability."""
    _require(
        isinstance(verified_publication, VerifiedPublication),
        "Verification is required before load.",
    )
    _require(
        verified_publication._token is _VERIFIED_TOKEN, "Verification is required before load."
    )
    _require(
        verified_publication.receipt.release_eligible is False
        and verified_publication.receipt.scope == SCOPE,
        "Invalid verified receipt scope.",
    )
    return VerifiedIssuedView(
        verified_publication.receipt,
        verified_publication._issued_records,
        verified_publication._issued_prefixes,
        verified_publication._standing_targets,
    )
