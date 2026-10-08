"""Fixture tests for read-only canonical artifact and history readers."""

from __future__ import annotations

import csv
import hashlib
import json
import stat
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import rossmann_forecasting.app.artifacts as artifact_module
from rossmann_forecasting.app.artifacts import (
    _ARTIFACTS,
    CANONICAL_RUNS,
    HISTORY_PROJECTION,
    _ArtifactReader,
)
from rossmann_forecasting.app.contracts import (
    ArtifactIntegrityError,
    ArtifactSchemaError,
    ArtifactSelector,
    ArtifactUnavailableError,
    CanonicalRunIdentity,
    DuplicateArtifactKeyError,
    HistoryQuery,
    InvalidArtifactRequestError,
    Phase,
    UnsafeArtifactPathError,
    UnsupportedArtifactSelectorError,
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _sample_value(name: str, selector: ArtifactSelector) -> object:
    if name in {"Store", "horizon", "k", "replicate", "n", "distinct_stores", "distinct_origins"}:
        return 1
    if name == "p":
        return 0.95
    if name == "Date":
        return datetime(2015, 6, 20)
    if name == "forecast_origin":
        return (
            datetime(2015, 6, 19)
            if selector
            in {
                ArtifactSelector.PHASE7_FORECASTS,
                ArtifactSelector.PHASE8_DAILY_INTERVALS,
                ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY,
            }
            else date(2015, 6, 19)
        )
    if name == "fit_id":
        return "A"
    if name == "candidate_id":
        return "global_lightgbm_gbdt_regression_l1"
    if name == "selected_candidate_id":
        return "global_lightgbm_gbdt_regression_l1"
    if name == "model_selection_run_id":
        return "365f22d4c3f94722a594ab934a22c4f6"
    if name == "scenario_id":
        return "fixture-scenario"
    if name == "case_id":
        return "fixture-case"
    if name == "policy_id":
        return "forecast"
    if name == "interval_kind":
        return "raw"
    if name == "tail":
        return "lower"
    if name in {
        "available",
        "forecast_available",
        "operational_forecast_available",
        "primary_evaluation_eligible",
        "schedule_assumption_flag",
        "issued_prefix_complete",
        "calibration_transport_valid",
        "synthetic",
    }:
        return name != "available" or selector in {
            ArtifactSelector.PHASE8_DAILY_INTERVALS,
            ArtifactSelector.PHASE8_CUMULATIVE_UNCERTAINTY,
        }
    if name in {
        "actual_sales",
        "assessment_source_open",
        "unavailable_reason",
        "issued_prefix_unavailable_reason",
        "baseline_value",
        "forecast_value",
    }:
        return None
    if name in {
        "Store",
        "raw_forecast",
        "operational_forecast",
        "point_forecast",
        "lower",
        "upper",
        "width",
        "D_k",
        "q_p_signed",
        "U_k",
        "SafetyStock_k",
        "Target_k",
        "tail_level",
        "signed_quantile",
        "forecast_protection_demand_value",
        "cumulative_signed_quantile",
        "upper_turnover_value",
        "safety_stock_value",
        "target_value",
        "initial_stock_value",
        "baseline_numerator",
        "baseline_denominator",
        "forecast_numerator",
        "forecast_denominator",
        "forecast_minus_baseline",
        "forecast_minus_baseline_relative",
        "value",
        "numerator",
        "denominator",
        "paired_mae_delta",
        "paired_mae_change_fraction",
    }:
        return 12.5
    if name in {"Store"}:
        return 1
    if name == "population":
        return "standalone"
    if name == "scope":
        return "pooled"
    if name == "metric":
        return "mae"
    if name == "unavailable_reason":
        return "fixture_unavailable"
    if name == "paired_with":
        return None
    if name == "availability_reason":
        return None
    if name == "forecast_origin":
        return date(2015, 6, 19)
    return "fixture"


def _write_table(path: Path, selector: ArtifactSelector, columns: tuple[str, ...]) -> None:
    arrays = {}
    for name in columns:
        value = _sample_value(name, selector)
        if name in {"Date", "forecast_origin"} and isinstance(value, datetime):
            arrays[name] = pa.array([value], type=pa.timestamp("ns"))
        else:
            arrays[name] = pa.array([value])
    pq.write_table(pa.table(arrays), path)


def _write_csv(path: Path, selector: ArtifactSelector, columns: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerow(
            ["" if (value := _sample_value(name, selector)) is None else value for name in columns]
        )


class FixtureStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.expected_runs: dict[Phase, CanonicalRunIdentity] = {}
        self.manifests: dict[Phase, dict[str, object]] = {}
        self._build()

    def _build(self) -> None:
        outputs_by_phase: dict[Phase, dict[str, dict[str, object]]] = {phase: {} for phase in Phase}
        for selector, spec in _ARTIFACTS.items():
            path = self.root / CANONICAL_RUNS[spec.phase].manifest_relative_path.parent
            path.mkdir(parents=True, exist_ok=True)
            output = path / spec.filename
            if spec.file_format == "csv":
                assert spec.csv_header is not None
                _write_csv(output, selector, spec.csv_header)
            else:
                _write_table(output, selector, spec.projection)
            metadata: dict[str, object] = {
                "rows": 1,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            }
            if spec.file_format == "parquet":
                metadata["columns"] = list(spec.projection)
            else:
                metadata["bytes"] = output.stat().st_size
            if spec.phase in {Phase.PHASE9, Phase.PHASE10}:
                metadata["path"] = spec.filename
            outputs_by_phase[spec.phase][spec.filename] = metadata

        p7 = CANONICAL_RUNS[Phase.PHASE7]
        self._write_manifest(
            Phase.PHASE7,
            {
                "selection_run_id": p7.run_id,
                "status": "selected",
                "publication_state": "complete",
                "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
                "final_holdout_outcomes_read_or_hashed": False,
                "date_bounds": {
                    "last_development_target": "2015-07-03",
                    "final_holdout_start": "2015-07-04",
                },
                "outputs": outputs_by_phase[Phase.PHASE7],
            },
        )
        p8 = CANONICAL_RUNS[Phase.PHASE8]
        self._write_manifest(
            Phase.PHASE8,
            {
                "run_id": p8.run_id,
                "status": "complete_with_unavailable_strata",
                "selection_run_id": p7.run_id,
                "selected_candidate_id": "global_lightgbm_gbdt_regression_l1",
                "fit_b_quantiles_frozen": False,
                "inputs": {
                    "selection_manifest_sha256": self.expected_runs[Phase.PHASE7].manifest_sha256,
                    "selection_run_id": p7.run_id,
                },
                "boundaries": {
                    "development_cutoff_inclusive": "2015-07-03",
                    "holdout_open_sales_customers_opened_loaded_or_hashed": False,
                },
                "outputs": outputs_by_phase[Phase.PHASE8],
            },
        )

        p9 = CANONICAL_RUNS[Phase.PHASE9]
        binding_payload: dict[str, object] = {
            "run_id": p9.run_id,
            "created_at_utc": "fixture-time",
            "phase7": {
                "selection_manifest_sha256": self.expected_runs[Phase.PHASE7].manifest_sha256,
                "selection_run_id": p7.run_id,
            },
            "phase8": {
                "manifest_sha256": self.expected_runs[Phase.PHASE8].manifest_sha256,
                "run_id": p8.run_id,
            },
            "boundary_checks": {"protected_holdout_values_read_or_hashed": False},
        }
        canonical_payload = {
            key: value
            for key, value in binding_payload.items()
            if key not in {"run_id", "created_at_utc"}
        }
        canonical_sha = hashlib.sha256(_canonical_json(canonical_payload)).hexdigest()
        binding = {**binding_payload, "canonical_sha256": canonical_sha}
        bindings_path = self.root / p9.manifest_relative_path.parent / "upstream_bindings.json"
        bindings_path.write_text(json.dumps(binding, indent=2, sort_keys=True), encoding="utf-8")
        self._write_manifest(
            Phase.PHASE9,
            {
                "run_id": p9.run_id,
                "status": "complete",
                "inputs": {
                    "phase7_selection_manifest_sha256": self.expected_runs[
                        Phase.PHASE7
                    ].manifest_sha256,
                    "phase8_manifest_sha256": self.expected_runs[Phase.PHASE8].manifest_sha256,
                },
                "boundaries": {
                    "development_cutoff_inclusive": "2015-07-03",
                    "protected_holdout_values_read_or_hashed": False,
                },
                "upstream_bindings": {
                    "path": "upstream_bindings.json",
                    "sha256": hashlib.sha256(bindings_path.read_bytes()).hexdigest(),
                    "canonical_sha256": canonical_sha,
                },
                "outputs": outputs_by_phase[Phase.PHASE9],
            },
        )

        p10 = CANONICAL_RUNS[Phase.PHASE10]
        self._write_manifest(
            Phase.PHASE10,
            {
                "run_id": p10.run_id,
                "status": "complete",
                "inputs": {
                    "phase7_run_id": p7.run_id,
                    "phase7_selection_manifest_sha256": self.expected_runs[
                        Phase.PHASE7
                    ].manifest_sha256,
                    "phase8_run_id": p8.run_id,
                    "phase8_manifest_sha256": self.expected_runs[Phase.PHASE8].manifest_sha256,
                    "phase9_run_id": p9.run_id,
                    "phase9_manifest_sha256": self.expected_runs[Phase.PHASE9].manifest_sha256,
                },
                "boundaries": {
                    "allowed_outcome_through": "2015-07-03",
                    "protected_holdout_values_read_or_hashed": False,
                },
                "outputs": outputs_by_phase[Phase.PHASE10],
            },
        )

    def _write_manifest(self, phase: Phase, manifest: dict[str, object]) -> None:
        identity = CANONICAL_RUNS[phase]
        path = self.root / identity.manifest_relative_path
        payload = _canonical_json(manifest)
        path.write_bytes(payload)
        self.manifests[phase] = manifest
        self.expected_runs[phase] = replace(
            identity,
            manifest_sha256=hashlib.sha256(payload).hexdigest(),
        )

    def reader(self) -> _ArtifactReader:
        return _ArtifactReader(root=self.root, expected_runs=self.expected_runs)

    def refresh_manifest(self, phase: Phase) -> None:
        self._write_manifest(phase, self.manifests[phase])

    def refresh_output(self, selector: ArtifactSelector) -> None:
        spec = _ARTIFACTS[selector]
        path = self.root / CANONICAL_RUNS[spec.phase].manifest_relative_path.parent / spec.filename
        metadata = self.manifests[spec.phase]["outputs"][spec.filename]
        assert isinstance(metadata, dict)
        metadata["rows"] = (
            pq.ParquetFile(path).metadata.num_rows if spec.file_format == "parquet" else 1
        )
        metadata["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        if spec.file_format == "parquet":
            metadata["columns"] = pq.ParquetFile(path).schema_arrow.names
        else:
            metadata["bytes"] = path.stat().st_size
        self.refresh_manifest(spec.phase)


@pytest.fixture
def fixture_store(tmp_path: Path) -> FixtureStore:
    return FixtureStore(tmp_path)


@pytest.mark.parametrize("selector", list(_ARTIFACTS))
def test_allowlisted_fixture_artifacts_load_with_trusted_identity(
    fixture_store: FixtureStore, selector: ArtifactSelector
) -> None:
    result = fixture_store.reader().read(selector)

    identity = fixture_store.expected_runs[_ARTIFACTS[selector].phase]
    assert result.selector is selector
    assert result.run_id == identity.run_id
    assert result.manifest_sha256 == identity.manifest_sha256
    assert len(result.frame) == 1
    assert tuple(result.frame.columns) == _ARTIFACTS[selector].projection


def test_rejects_wrong_trusted_manifest_hash(fixture_store: FixtureStore) -> None:
    identity = fixture_store.expected_runs[Phase.PHASE7]
    fixture_store.expected_runs[Phase.PHASE7] = replace(identity, manifest_sha256="0" * 64)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_rejects_wrong_output_hash(fixture_store: FixtureStore) -> None:
    spec = _ARTIFACTS[ArtifactSelector.PHASE7_FORECASTS]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE7].manifest_relative_path.parent
        / spec.filename
    )
    output.write_bytes(output.read_bytes() + b"changed")

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_rejects_inconsistent_phase10_upstream_lineage(fixture_store: FixtureStore) -> None:
    manifest = fixture_store.manifests[Phase.PHASE10]
    inputs = manifest["inputs"]
    assert isinstance(inputs, dict)
    inputs["phase7_run_id"] = "different-run"
    fixture_store.refresh_manifest(Phase.PHASE10)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE10_COMPARISON)


def test_missing_artifact_is_explicit_and_does_not_fall_back(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE8_DAILY_INTERVALS
    spec = _ARTIFACTS[selector]
    expected_dir = fixture_store.root / CANONICAL_RUNS[Phase.PHASE8].manifest_relative_path.parent
    (expected_dir / spec.filename).unlink()
    alternate = fixture_store.root / "data/processed/uncertainty/other-run"
    alternate.mkdir(parents=True)
    (alternate / spec.filename).write_bytes(b"not a trusted fallback")
    (expected_dir.parent / "current.json").write_text('{"run_id":"other-run"}', encoding="utf-8")

    with pytest.raises(ArtifactUnavailableError) as error:
        fixture_store.reader().read(selector)
    assert error.value.unavailable is not None
    assert error.value.unavailable.value is None


@pytest.mark.parametrize("payload", [b"{", b'{"value":NaN}'])
def test_rejects_malformed_manifest_json(fixture_store: FixtureStore, payload: bytes) -> None:
    identity = fixture_store.expected_runs[Phase.PHASE7]
    path = fixture_store.root / identity.manifest_relative_path
    path.write_bytes(payload)
    fixture_store.expected_runs[Phase.PHASE7] = replace(
        identity, manifest_sha256=hashlib.sha256(payload).hexdigest()
    )

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_rejects_missing_required_schema_column(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_FORECASTS
    spec = _ARTIFACTS[selector]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE7].manifest_relative_path.parent
        / spec.filename
    )
    columns = tuple(name for name in spec.projection if name != "raw_forecast")
    _write_table(output, selector, columns)
    fixture_store.refresh_output(selector)

    with pytest.raises(ArtifactSchemaError):
        fixture_store.reader().read(selector)


def test_rejects_unbounded_manifest_row_count_before_read(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE7_MODEL_COMPARISON
    spec = _ARTIFACTS[selector]
    output_meta = fixture_store.manifests[Phase.PHASE7]["outputs"][spec.filename]
    assert isinstance(output_meta, dict)
    output_meta["rows"] = spec.max_rows + 1
    fixture_store.refresh_manifest(Phase.PHASE7)

    with pytest.raises(ArtifactIntegrityError):
        fixture_store.reader().read(selector)


def test_rejects_duplicate_primary_keys(fixture_store: FixtureStore) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    spec = _ARTIFACTS[selector]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE9].manifest_relative_path.parent
        / spec.filename
    )
    arrays = {
        name: pa.array([_sample_value(name, selector), _sample_value(name, selector)])
        for name in spec.projection
    }
    pq.write_table(pa.table(arrays), output)
    fixture_store.refresh_output(selector)

    with pytest.raises(DuplicateArtifactKeyError):
        fixture_store.reader().read(selector)


def test_rejects_unsupported_selectors_and_traversal(fixture_store: FixtureStore) -> None:
    reader = fixture_store.reader()
    with pytest.raises(UnsupportedArtifactSelectorError):
        reader.read("../../outside.parquet")  # type: ignore[arg-type]
    with pytest.raises(UnsafeArtifactPathError):
        reader._trusted_file(Path("../outside.parquet"), ArtifactSelector.PHASE7_FORECASTS, None)  # type: ignore[arg-type]


def test_rejects_unsafe_symlink_component(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _ARTIFACTS[ArtifactSelector.PHASE7_FORECASTS]
    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE7].manifest_relative_path.parent
        / spec.filename
    )
    original_lstat = Path.lstat

    def pretend_symlink(path: Path) -> object:
        if path == output:
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", pretend_symlink)

    with pytest.raises(UnsafeArtifactPathError):
        fixture_store.reader().read(ArtifactSelector.PHASE7_FORECASTS)


def test_null_values_are_preserved_and_fixture_files_are_unchanged(
    fixture_store: FixtureStore,
) -> None:
    files = [path for path in fixture_store.root.rglob("*") if path.is_file()]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}

    result = fixture_store.reader().read(ArtifactSelector.PHASE10_COMPARISON)

    assert pd.isna(result.frame.loc[0, "baseline_value"])
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert after == before


def test_phase8_historical_false_freeze_flag_is_accepted(fixture_store: FixtureStore) -> None:
    assert fixture_store.manifests[Phase.PHASE8]["fit_b_quantiles_frozen"] is False
    fixture_store.reader().read(ArtifactSelector.PHASE8_CUMULATIVE_QUANTILES)


def test_output_hash_cache_rechecks_when_file_identity_changes(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = ArtifactSelector.PHASE9_SCENARIO_CATALOG
    original = artifact_module._sha256_file
    checked: list[Path] = []

    def counted(path: Path) -> str:
        checked.append(path)
        return original(path)

    monkeypatch.setattr(artifact_module, "_sha256_file", counted)
    reader = fixture_store.reader()
    reader.read(selector)
    reader.read(selector)
    assert len(checked) == 1

    output = (
        fixture_store.root
        / CANONICAL_RUNS[Phase.PHASE9].manifest_relative_path.parent
        / "scenario_catalog.parquet"
    )
    output.write_bytes(output.read_bytes() + b"x")
    with pytest.raises(ArtifactIntegrityError):
        reader.read(selector)
    assert len(checked) == 2


def test_history_crossing_cutoff_is_rejected_before_dataset_open(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened = False

    def unexpected_open(*args: object, **kwargs: object) -> None:
        nonlocal opened
        opened = True
        raise AssertionError("The protected history dataset must not be opened.")

    monkeypatch.setattr(artifact_module.ds, "dataset", unexpected_open)
    query = HistoryQuery(
        store_id=1,
        start_date=date(2015, 7, 3),
        end_date=date(2015, 7, 4),
    )
    with pytest.raises(InvalidArtifactRequestError):
        fixture_store.reader().read_history_sales(query)
    assert not opened


def test_history_uses_arrow_projection_and_storage_filter(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = fixture_store.root / "data/interim/train.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "Store": pa.array([1, 1, 1, 2], type=pa.int64()),
            "Date": pa.array(
                [
                    datetime(2015, 7, 2),
                    datetime(2015, 7, 3),
                    datetime(2015, 7, 4),
                    datetime(2015, 7, 3),
                ],
                type=pa.timestamp("ns"),
            ),
            "Sales": pa.array([100, None, 9_999_999, 200], type=pa.int64()),
            "Open": pa.array([1, None, 0, 1], type=pa.int64()),
            "Customers": pa.array([10, 11, 12_345, 20], type=pa.int64()),
        }
    )
    pq.write_table(table, source)
    original_dataset = artifact_module.ds.dataset
    observed: dict[str, object] = {}

    class RecordingDataset:
        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped
            self.schema = wrapped.schema

        def scanner(self, **kwargs: object) -> object:
            observed.update(kwargs)
            return self._wrapped.scanner(**kwargs)

    def recording_dataset(*args: object, **kwargs: object) -> RecordingDataset:
        return RecordingDataset(original_dataset(*args, **kwargs))

    monkeypatch.setattr(artifact_module.ds, "dataset", recording_dataset)
    frame = fixture_store.reader().read_history_sales(
        HistoryQuery(
            store_id=1,
            start_date=date(2015, 7, 2),
            end_date=date(2015, 7, 3),
        )
    )

    assert tuple(observed["columns"]) == HISTORY_PROJECTION
    assert observed["filter"] is not None
    assert "Date" in str(observed["filter"])
    assert "Store" in str(observed["filter"])
    assert tuple(frame.columns) == HISTORY_PROJECTION
    assert "Customers" not in frame.columns
    assert frame["Date"].max() <= pd.Timestamp("2015-07-03")
    assert len(frame) == 2
    assert pd.isna(frame.loc[frame["Date"].eq(pd.Timestamp("2015-07-03")), "Sales"]).all()


def test_history_rejects_invalid_store_and_oversized_range_before_dataset_open(
    fixture_store: FixtureStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        artifact_module.ds,
        "dataset",
        lambda *args, **kwargs: pytest.fail("dataset opened for an invalid request"),
    )
    reader = fixture_store.reader()
    with pytest.raises(InvalidArtifactRequestError):
        reader.read_history_sales(HistoryQuery(0, date(2015, 6, 1), date(2015, 6, 2)))
    with pytest.raises(InvalidArtifactRequestError):
        reader.read_history_sales(HistoryQuery(1, date(2014, 5, 31), date(2015, 6, 1)))


def test_missing_historical_dataset_is_explicit(fixture_store: FixtureStore) -> None:
    with pytest.raises(ArtifactUnavailableError):
        fixture_store.reader().read_history_sales(
            HistoryQuery(1, date(2015, 7, 1), date(2015, 7, 3))
        )
