"""Synthetic M4-A contracts. No native fitting, source reads or canonical artifacts."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import stat
import subprocess
import sys
import time
import tracemalloc
from dataclasses import replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import test_phase13_adapters as golden
from pandas.testing import assert_frame_equal

import rossmann_forecasting.phase13.publication as publication
from rossmann_forecasting.forecasting.lightgbm import CATEGORICAL_COLUMNS, FIXED_PARAMETERS
from rossmann_forecasting.forecasting.lightgbm_evaluation import TRIAL_PARAMETERS
from rossmann_forecasting.phase13.adapters import Phase13M3Adapter
from rossmann_forecasting.phase13.contracts import (
    SUPPORTED_ORIGINS,
    AvailabilityAssumption,
    SourceProvenance,
)
from rossmann_forecasting.phase13.issuer import TrainingRowCounts, _identity
from rossmann_forecasting.phase13.publication import (
    IncompletePublicationError,
    Phase13PublicationError,
    PublicationConflictError,
    PublicationMetadata,
    SyntheticModelState,
    TrustedSyntheticParents,
    load_issued_view,
    prepare_publication,
    publish_publication,
    verify_publication,
)

REPOSITORY = Path(__file__).absolute().parents[1]
ORIGIN = SUPPORTED_ORIGINS[0]


def _sha(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _fixture(origin=ORIGIN, stores=(1, 2), *, scenario="normal"):
    """Hand-calculated points plus a clearly artificial text-state handoff; never fitted."""
    unavailable = {(stores[0], 1)} if scenario == "unavailable" else set()
    if scenario in ("fit_failure", "no_eligible"):
        unavailable = {(store, h) for store in stores for h in range(1, 15)}
    with patch.object(golden, "STORES", stores):
        raw = golden._raw_issuance(origin, unavailable=unavailable)
        schedule = golden._planned_open(
            origin,
            unknown={(stores[0], 3)} if scenario == "unknown_schedule" else set(),
            omit={(stores[0], 3)} if scenario == "missing_schedule" else set(),
        )
        anchors = golden._anchor_collection(
            origin,
            means={store: 0.0 if scenario == "zero_anchor" else 100.0 for store in stores},
            missing={stores[0]} if scenario == "missing_anchor" else set(),
        )
    category_map = {
        "Store": stores,
        "state_holiday": ("0",),
        "store_type": ("a",),
        "assortment": ("a",),
    }
    categories = tuple((column, category_map[column]) for column in CATEGORICAL_COLUMNS)
    if scenario == "no_eligible":
        categories = tuple((column, ()) for column in CATEGORICAL_COLUMNS)
    category_hashes = {
        column: _sha(json.dumps(list(values), separators=(",", ":")))
        for column, values in categories
    }
    booster_bytes = (
        None
        if scenario in ("fit_failure", "no_eligible")
        else b"Synthetic fixture text; NOT a native LightGBM model.\n"
    )
    failure_reason = "model_fit_failure" if booster_bytes is None else None
    if scenario == "no_eligible":
        failure_reason = "no_eligible_training_rows"
    fit_rows = 0 if scenario == "no_eligible" else len(stores)
    tree_count = None if booster_bytes is None else 180
    # Independent expression of the accepted M2 identity inputs, including order.
    model_id = _identity(
        {
            "model": raw.model_name,
            "origin": origin.isoformat(),
            "recipe_identity": raw.recipe_identity,
            "feature_schema_identity": raw.feature_schema_identity,
            "category_vocabulary_hashes": category_hashes,
            "booster_sha256": None if booster_bytes is None else sha256(booster_bytes).hexdigest(),
            "failure_reason": failure_reason,
        }
    )
    fit_id = _identity(
        {
            "model_identity": model_id,
            "input_identities": raw.input_identities,
            "fit_row_count": fit_rows,
            "actual_tree_count": tree_count,
        }
    )
    frame = raw.to_frame()
    frame["model_identity"], frame["fit_identity"] = model_id, fit_id
    if booster_bytes is None:
        frame["unavailable_reason"] = failure_reason
    raw = replace(
        raw,
        model_identity=model_id,
        fit_identity=fit_id,
        actual_tree_count=tree_count,
        training_counts=TrainingRowCounts(
            len(stores),
            len(stores),
            0,
            len(stores) if scenario == "no_eligible" else 0,
            fit_rows,
            fit_rows,
        ),
        category_vocabulary_hashes=tuple(category_hashes.items()),
        _records=frame,
    )
    state = SyntheticModelState(
        origin=origin,
        booster_bytes=booster_bytes,
        category_vocabularies=categories,
        fit_row_count=fit_rows,
        model_identity=model_id,
        fit_identity=fit_id,
        recipe_identity=raw.recipe_identity,
        feature_schema_identity=raw.feature_schema_identity,
        model_parameters=tuple(sorted({**FIXED_PARAMETERS, **TRIAL_PARAMETERS["A"]}.items())),
        failure_reason=failure_reason,
        actual_tree_count=tree_count,
    )
    quantiles = golden._fixture(
        raw,
        daily_unsupported={2} if scenario == "unsupported_quantile" else set(),
        cumulative_unsupported={(3, 0.95)} if scenario == "unsupported_quantile" else set(),
    )
    issued = Phase13M3Adapter().issue(raw, schedule, quantiles)
    targets = issued.build_standing_targets(anchors)
    parents = TrustedSyntheticParents(raw, schedule, quantiles, anchors, state)
    environment = {
        "python": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "cpu": "fixture-CPU-metadata",
        "lightgbm_build": "synthetic-text-handoff-no-native-model-provenance",
        "num_threads": "4",
        "uv": "0.12.23",
        **{
            name: importlib.metadata.version(name)
            for name in ("lightgbm", "numpy", "pandas", "pyarrow")
        },
    }
    provenance = SourceProvenance(
        "phase13.synthetic.publication",
        "fixture-v1",
        "Handcrafted synthetic fixture definitions.",
        AvailabilityAssumption.SYNTHETIC_RULE,
    )
    metadata = PublicationMetadata(
        fixture_id="synthetic://phase13/m4a-handcrafted-v1",
        protocol_sha256=_sha("synthetic-protocol"),
        configuration_sha256=_sha("synthetic-config"),
        code_revision="ded614c24fcb6766e578480ba314a10a3e7f223e",
        code_worktree_dirty=True,
        lock_sha256=sha256((REPOSITORY / "uv.lock").read_bytes()).hexdigest(),
        command=("pytest", "synthetic-M4-A-fixture"),
        environment=tuple(sorted(environment.items())),
        input_provenance=tuple(
            (role, provenance) for role in ("training", "recursive_history", "future_covariates")
        ),
        phase7_lineage=(
            ("selection_run_id", "synthetic-lineage-reference"),
            ("selection_manifest_sha256", _sha("synthetic-selection")),
            ("configuration_sha256", _sha("synthetic-selected-configuration")),
        ),
    )
    return parents, issued, targets, metadata


def _prepare(fixture):
    parents, issued, targets, metadata = fixture
    return prepare_publication(parents=parents, issuance=issued, targets=targets, metadata=metadata)


def _verify(root, prepared, parents):
    return verify_publication(
        fixture_root=root, expected_binding=prepared.binding, trusted_parents=parents
    )


@pytest.fixture(autouse=True)
def no_native_or_outcome_operations(monkeypatch):
    import rossmann_forecasting.forecasting.lightgbm as model
    import rossmann_forecasting.forecasting.uncertainty as uncertainty
    import rossmann_forecasting.inventory.simulation as inventory
    import rossmann_forecasting.phase13.adapters as adapters
    import rossmann_forecasting.phase13.issuer as issuer
    from rossmann_forecasting.phase13.providers import SyntheticOutcomeProvider

    def forbidden(*_args, **_kwargs):
        pytest.fail("M4-A called a forbidden native/source/outcome/evaluation operation")

    for module, names in (
        (model, ("fit_lightgbm", "recursive_lightgbm_forecasts", "make_lightgbm_dataset")),
        (issuer, ("fit_lightgbm", "recursive_lightgbm_forecasts", "make_lightgbm_dataset")),
        (uncertainty, ("calculate_uncertainty", "_build_quantile_tables")),
        (adapters, ("load_canonical_fit_b_quantiles",)),
        (inventory, ("run_inventory_simulation",)),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(SyntheticOutcomeProvider, "read_day", forbidden)


@pytest.fixture(scope="module")
def normal_fixture():
    return _fixture()


@pytest.fixture(scope="module")
def prepared(normal_fixture):
    return _prepare(normal_fixture)


@pytest.mark.parametrize("origin", SUPPORTED_ORIGINS)
@pytest.mark.parametrize(
    "scenario",
    (
        "normal",
        "unavailable",
        "fit_failure",
        "no_eligible",
        "unknown_schedule",
        "missing_schedule",
        "unsupported_quantile",
        "zero_anchor",
        "missing_anchor",
    ),
)
def test_both_origins_round_trip_scientific_outputs(tmp_path, origin, scenario):
    fixture = _fixture(origin, scenario=scenario)
    parents, issued, targets, _ = fixture
    prepared = _prepare(fixture)
    receipt = publish_publication(prepared, fixture_root=tmp_path)
    view = load_issued_view(_verify(tmp_path, prepared, parents))
    assert_frame_equal(view.to_frame(), issued.to_frame(), check_exact=True)
    assert_frame_equal(view.prefixes_to_frame(), issued.prefixes_to_frame(), check_exact=True)
    assert_frame_equal(view.targets_to_frame(), targets.to_frame(), check_exact=True)
    assert len(view.to_frame()) == 28
    assert len(view.prefixes_to_frame()) == 84
    assert len(view.targets_to_frame()) == 72
    assert receipt.scope == "synthetic_selected_model_issuance"
    assert receipt.release_eligible is False
    payload = json.loads((tmp_path / "receipts" / origin.isoformat() / "receipt.json").read_bytes())
    for name in (
        "release_eligible",
        "comparator_complete",
        "inventory_initial_state_complete",
        "protected_access_authorized",
    ):
        assert payload[name] is False
    if scenario in ("fit_failure", "no_eligible"):
        assert not (tmp_path / "issuances" / origin.isoformat() / "booster.txt").exists()
        assert not view.to_frame()["forecast_available"].any()
        assert view.to_frame()["raw_forecast"].isna().all()
    # Defensive copies cannot modify the verified snapshot.
    frame = view.to_frame()
    frame.loc[0, "raw_forecast"] = 99999.0
    assert_frame_equal(view.to_frame(), issued.to_frame(), check_exact=True)


def test_hand_calculated_routing_quantile_and_targets(normal_fixture, tmp_path):
    parents, issued, targets, _ = normal_fixture
    prepared = _prepare(normal_fixture)
    publish_publication(prepared, fixture_root=tmp_path)
    view = load_issued_view(_verify(tmp_path, prepared, parents))
    frame = view.to_frame()
    saturday = frame.loc[frame["Store"].eq(1) & frame["horizon"].eq(1)].iloc[0]
    sunday = frame.loc[frame["Store"].eq(1) & frame["horizon"].eq(2)].iloc[0]
    assert saturday.raw_forecast == 10.0
    assert saturday.raw_interval_lower == saturday.raw_interval_upper == 0.0
    assert sunday.raw_forecast == 120.0 and sunday.operational_forecast == 0.0
    selected = view.targets_to_frame().query(
        "Store == 1 and lead_time == 2 and buffer_probability == 0.95"
    )
    assert sorted(selected.target_value.tolist()) == [146.0, 200.0]
    assert_frame_equal(frame, issued.to_frame())
    assert_frame_equal(view.targets_to_frame(), targets.to_frame())


def test_equivalent_preparations_have_identical_bytes_and_idempotent_publication(tmp_path):
    first, second = _fixture(), _fixture()
    a, b = _prepare(first), _prepare(second)
    assert a == b
    receipt = publish_publication(a, fixture_root=tmp_path / "a")
    root = tmp_path / "a"
    before = {
        p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }
    assert publish_publication(b, fixture_root=root) == receipt
    after = {
        p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }
    assert after == before
    assert publish_publication(b, fixture_root=tmp_path / "b") == receipt
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == {
        p.relative_to(tmp_path / "b"): p.read_bytes()
        for p in (tmp_path / "b").rglob("*")
        if p.is_file()
    }


def test_unordered_parent_evidence_and_metadata_have_canonical_publication_order():
    parents, issued, targets, metadata = _fixture()
    quantiles = publication.SyntheticFitBQuantileFixture(
        parents.quantiles.daily_to_frame().iloc[::-1],
        parents.quantiles.cumulative_to_frame().iloc[::-1],
        fixture_id=parents.quantiles.fixture_id,
        transport=parents.quantiles.transport,
    )
    anchors = publication.SyntheticHistoricalMeanAnchorCollection(
        origin=parents.anchors.origin,
        store_ids=parents.anchors.store_ids,
        anchors=parents.anchors.anchors[::-1],
    )
    equivalent = replace(
        parents,
        quantiles=quantiles,
        anchors=anchors,
        model_state=replace(
            parents.model_state, model_parameters=parents.model_state.model_parameters[::-1]
        ),
    )
    reordered_metadata = replace(
        metadata,
        environment=metadata.environment[::-1],
        input_provenance=metadata.input_provenance[::-1],
        phase7_lineage=metadata.phase7_lineage[::-1],
    )
    assert _prepare((parents, issued, targets, metadata)) == _prepare(
        (equivalent, issued, targets, reordered_metadata)
    )


def test_conflicting_duplicate_preserves_original(normal_fixture, prepared, tmp_path):
    publish_publication(prepared, fixture_root=tmp_path)
    parents, issued, targets, metadata = normal_fixture
    different = prepare_publication(
        parents=parents,
        issuance=issued,
        targets=targets,
        metadata=replace(metadata, configuration_sha256=_sha("other")),
    )
    with pytest.raises(PublicationConflictError):
        publish_publication(different, fixture_root=tmp_path)
    assert _verify(tmp_path, prepared, parents).binding == prepared.binding


def test_conflicting_fit_status_is_a_conflict_without_changing_prior_publication(
    prepared, tmp_path
):
    failure_fixture = _fixture(scenario="fit_failure")
    failed = _prepare(failure_fixture)
    publish_publication(failed, fixture_root=tmp_path)
    with pytest.raises(PublicationConflictError):
        publish_publication(prepared, fixture_root=tmp_path)
    assert _verify(tmp_path, failed, failure_fixture[0]).binding == failed.binding


@pytest.mark.parametrize(
    "mutation",
    (
        "model_missing",
        "model_bytes",
        "model_origin",
        "model_id",
        "fit_id",
        "schema",
        "recipe",
        "categories",
        "parameters",
        "rounds",
        "fit_rows",
        "missing_booster",
        "schedule",
        "quantiles",
        "anchors",
    ),
)
def test_wrong_parents_and_sidecars_fail_before_writes(normal_fixture, tmp_path, mutation):
    parents, issued, targets, metadata = normal_fixture
    state = parents.model_state
    changes = {
        "model_bytes": {"booster_bytes": b"unrelated fixture text"},
        "model_origin": {"origin": SUPPORTED_ORIGINS[1]},
        "model_id": {"model_identity": "0" * 64},
        "fit_id": {"fit_identity": "0" * 64},
        "schema": {"feature_schema_identity": "0" * 64},
        "recipe": {"recipe_identity": "0" * 64},
        "categories": {"category_vocabularies": ()},
        "parameters": {"model_parameters": ()},
        "rounds": {"requested_boost_rounds": 179},
        "fit_rows": {"fit_row_count": 999},
        "missing_booster": {"booster_bytes": None},
    }
    if mutation == "model_missing":
        parents = replace(parents, model_state=None)
    elif mutation in changes:
        parents = replace(parents, model_state=replace(state, **changes[mutation]))
    elif mutation == "schedule":
        parents = replace(parents, planned_open=golden._planned_open(unknown={(1, 1)}))
    elif mutation == "quantiles":
        parents = replace(
            parents, quantiles=golden._fixture(parents.raw_issuance, daily_unsupported={1})
        )
    else:
        parents = replace(parents, anchors=golden._anchor_collection(means={1: 101.0, 2: 100.0}))
    root = tmp_path / "must-not-exist"
    with pytest.raises(Phase13PublicationError):
        payload = prepare_publication(
            parents=parents, issuance=issued, targets=targets, metadata=metadata
        )
        publish_publication(payload, fixture_root=root)
    assert not root.exists()


@pytest.mark.parametrize(
    "kind",
    ("missing", "duplicate", "reordered", "extra", "unknown_column", "numeric_boolean", "array"),
)
def test_raw_parent_grid_types_and_schema_rejected(normal_fixture, kind):
    parents, issued, targets, metadata = normal_fixture
    frame = parents.raw_issuance.to_frame()
    if kind == "missing":
        frame = frame.iloc[:-1]
    elif kind == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif kind == "reordered":
        frame = frame.iloc[::-1]
    elif kind == "extra":
        extra = frame.iloc[[0]].copy()
        extra["Date"] += pd.Timedelta(days=14)
        frame = pd.concat([frame, extra], ignore_index=True)
    elif kind == "unknown_column":
        frame["unexpected"] = 1
    else:
        frame["forecast_was_clipped"] = frame["forecast_was_clipped"].astype(object)
        frame.at[0, "forecast_was_clipped"] = 0 if kind == "numeric_boolean" else np.array(False)
    with pytest.raises((Phase13PublicationError, golden.Phase13IssuanceError)):
        raw = replace(parents.raw_issuance, _records=frame)
        prepare_publication(
            parents=replace(parents, raw_issuance=raw),
            issuance=issued,
            targets=targets,
            metadata=metadata,
        )


@pytest.mark.parametrize("table", ("records", "prefixes", "targets"))
@pytest.mark.parametrize("mutation", ("value", "row_order", "column", "dtype", "array"))
def test_supplied_snapshots_cannot_assert_own_integrity(table, mutation):
    parents, issued, targets, metadata = _fixture()
    frame = (
        issued.to_frame()
        if table == "records"
        else issued.prefixes_to_frame()
        if table == "prefixes"
        else targets.to_frame()
    )
    column = (
        "raw_forecast"
        if table == "records"
        else "operational_cumulative_forecast"
        if table == "prefixes"
        else "target_value"
    )
    if mutation == "value":
        frame.loc[0, column] += 1
    elif mutation == "row_order":
        frame = frame.iloc[::-1]
    elif mutation == "column":
        frame["unexpected"] = 0
    elif mutation == "dtype":
        frame["Store"] = frame["Store"].astype("float64")
    else:
        frame[column] = frame[column].astype(object)
        frame.at[0, column] = np.array(1.0)
    target_object = targets if table == "targets" else issued
    attribute = "_prefixes" if table == "prefixes" else "_records"
    object.__setattr__(target_object, attribute, frame)
    with pytest.raises(Phase13PublicationError):
        prepare_publication(parents=parents, issuance=issued, targets=targets, metadata=metadata)


def test_m4_boundary_distinguishes_boolean_integer_without_changing_m3():
    parents, issued, targets, metadata = _fixture()
    frame = issued.to_frame()
    frame["forecast_was_clipped"] = frame["forecast_was_clipped"].astype(object)
    frame.at[0, "forecast_was_clipped"] = 0
    object.__setattr__(issued, "_records", frame)
    with pytest.raises(Phase13PublicationError):
        prepare_publication(parents=parents, issuance=issued, targets=targets, metadata=metadata)


def test_table_codec_preserves_exact_scalars_types_dates_and_nulls():
    frame = pd.DataFrame(
        {
            "int64": pd.Series([2**63 - 1, -(2**63)], dtype="int64"),
            "float64": pd.Series([np.nextafter(1.0, 2.0), -0.0], dtype="float64"),
            "Boolean": pd.Series([True, pd.NA], dtype="boolean"),
            "date_ns": pd.Series([pd.Timestamp("2015-07-03"), pd.NaT], dtype="datetime64[ns]"),
            "date_us": pd.Series([pd.Timestamp("2015-07-03"), pd.NaT], dtype="datetime64[us]"),
            "object": pd.Series([date(2015, 7, 3), ("parent", "other")], dtype="object"),
            "missing": pd.Series([None, pd.NA], dtype="object"),
            "numeric_missing": pd.Series([np.nan, False], dtype="object"),
            "string": pd.Series(["value", pd.NA], dtype=pd.StringDtype(storage="python")),
        }
    )
    encoded = publication._table_bytes(frame)
    restored = publication._table_from_bytes(encoded)
    assert_frame_equal(restored, frame, check_exact=True)
    assert np.signbit(restored.loc[1, "float64"])
    assert publication._table_bytes(restored) == encoded


@pytest.mark.parametrize(
    "value", (np.array(np.nan), np.array(False), float("inf"), 1j, [1], {"x": 1})
)
def test_unsupported_or_nonfinite_table_cells_raise_typed_errors(value):
    frame = pd.DataFrame({"diagnostic": pd.Series([None], dtype="object")})
    frame.at[0, "diagnostic"] = value
    with pytest.raises(Phase13PublicationError):
        publication._table_bytes(frame)


@pytest.mark.parametrize(
    "content", (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b"\xff", b'{"x": 1}', b"{}\n")
)
def test_strict_json_rejects_noncanonical_or_ambiguous_content(content):
    with pytest.raises((Phase13PublicationError, ValueError, UnicodeError)):
        publication._decode(content, 100)


@pytest.mark.parametrize(
    "name",
    (
        "raw_records.json",
        "planned_open.json",
        "daily_quantiles.json",
        "cumulative_quantiles.json",
        "anchors.json",
        "issued_records.json",
        "issued_prefixes.json",
        "standing_targets.json",
        "adapter_state.json",
        "booster.txt",
        "metadata.json",
        "manifest.json",
        "receipt.json",
    ),
)
@pytest.mark.parametrize("mutation", ("changed", "truncated", "missing"))
def test_tampered_or_missing_files_never_load(normal_fixture, prepared, tmp_path, name, mutation):
    publish_publication(prepared, fixture_root=tmp_path)
    directory = "receipts" if name == "receipt.json" else "issuances"
    path = tmp_path / directory / ORIGIN.isoformat() / name
    if mutation == "missing":
        path.unlink()
    else:
        content = path.read_bytes()
        path.write_bytes(content[:-1] if mutation == "truncated" else b"X" + content[1:])
    before = path.read_bytes() if path.exists() else None
    with pytest.raises(Phase13PublicationError):
        _verify(tmp_path, prepared, normal_fixture[0])
    assert (path.read_bytes() if path.exists() else None) == before


def test_extra_files_and_wrong_external_bindings_fail(normal_fixture, prepared, tmp_path):
    publish_publication(prepared, fixture_root=tmp_path)
    extra = tmp_path / "issuances" / ORIGIN.isoformat() / "extra.json"
    extra.write_bytes(b"{}")
    with pytest.raises(Phase13PublicationError):
        _verify(tmp_path, prepared, normal_fixture[0])
    extra.unlink()
    for field in ("publication_id", "grid_identity", "manifest_sha256", "receipt_sha256"):
        with pytest.raises(Phase13PublicationError):
            verify_publication(
                fixture_root=tmp_path,
                trusted_parents=normal_fixture[0],
                expected_binding=replace(prepared.binding, **{field: "0" * 64}),
            )
    # Correct file pins cannot replace the authoritative parents.
    wrong_parents = _fixture(scenario="zero_anchor")[0]
    with pytest.raises(Phase13PublicationError):
        _verify(tmp_path, prepared, wrong_parents)


@pytest.mark.parametrize(
    "name,column",
    (
        ("issued_records.json", "raw_forecast"),
        ("issued_prefixes.json", "operational_cumulative_forecast"),
        ("standing_targets.json", "target_value"),
        ("raw_records.json", "raw_forecast"),
        ("issued_records.json", "forecast_was_clipped"),
    ),
)
def test_self_rehashed_tampering_still_requires_authoritative_parents(
    normal_fixture, prepared, tmp_path, name, column
):
    publish_publication(prepared, fixture_root=tmp_path)
    issue = tmp_path / "issuances" / ORIGIN.isoformat()
    table = json.loads((issue / name).read_bytes())
    index = table["columns"].index(column)
    table["rows"][0][index] = 0 if column == "forecast_was_clipped" else 99999.0
    content = publication._canonical(table)
    (issue / name).write_bytes(content)
    manifest = json.loads((issue / "manifest.json").read_bytes())
    manifest["files"][name].update(bytes=len(content), sha256=sha256(content).hexdigest())
    manifest.pop("publication_id")
    publication_id = publication._domain_hash(publication.VERSION + ":publication", manifest)
    manifest["publication_id"] = publication_id
    manifest_bytes = publication._canonical(manifest)
    (issue / "manifest.json").write_bytes(manifest_bytes)
    receipt_path = tmp_path / "receipts" / ORIGIN.isoformat() / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt.pop("receipt_id")
    receipt.update(
        publication_id=publication_id, manifest_sha256=sha256(manifest_bytes).hexdigest()
    )
    receipt["receipt_id"] = publication._domain_hash(publication.VERSION + ":receipt", receipt)
    receipt_bytes = publication._canonical(receipt)
    receipt_path.write_bytes(receipt_bytes)
    # Even supplying the new self-consistent pins does not validate changed results.
    binding = replace(
        prepared.binding,
        publication_id=publication_id,
        manifest_sha256=sha256(manifest_bytes).hexdigest(),
        receipt_sha256=sha256(receipt_bytes).hexdigest(),
    )
    with pytest.raises(Phase13PublicationError):
        verify_publication(
            fixture_root=tmp_path, expected_binding=binding, trusted_parents=normal_fixture[0]
        )


def test_independent_origins_coexist_without_claiming_block1_release(tmp_path):
    bindings = []
    for origin in SUPPORTED_ORIGINS:
        fixture = _fixture(origin)
        prepared = _prepare(fixture)
        publish_publication(prepared, fixture_root=tmp_path)
        verified = _verify(tmp_path, prepared, fixture[0])
        assert verified.receipt.release_eligible is False
        bindings.append(verified.binding)
    assert bindings[0].publication_id != bindings[1].publication_id
    assert {p.name for p in (tmp_path / "issuances").iterdir()} == {
        origin.isoformat() for origin in SUPPORTED_ORIGINS
    }


def test_all_publication_file_opens_stay_in_explicit_fixture_root(
    normal_fixture, prepared, tmp_path, monkeypatch
):
    original = Path.open
    calls = []

    def guarded(path, *args, **kwargs):
        assert path.absolute().is_relative_to(tmp_path), "Publication opened a nonfixture path"
        calls.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    publish_publication(prepared, fixture_root=tmp_path)
    _verify(tmp_path, prepared, normal_fixture[0])
    assert calls


def test_alias_in_existing_payload_rejected_before_any_read(
    normal_fixture, prepared, tmp_path, monkeypatch
):
    publish_publication(prepared, fixture_root=tmp_path)
    target = tmp_path / "issuances" / ORIGIN.isoformat() / "raw_records.json"
    original = Path.lstat

    def alias(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == target:
            from types import SimpleNamespace

            return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
        return info

    monkeypatch.setattr(Path, "lstat", alias)
    monkeypatch.setattr(publication, "_read", lambda *_: pytest.fail("read before alias rejection"))
    for operation in (
        lambda: publish_publication(prepared, fixture_root=tmp_path),
        lambda: _verify(tmp_path, prepared, normal_fixture[0]),
    ):
        with pytest.raises(Phase13PublicationError):
            operation()


@pytest.mark.parametrize("orphan", ("issue", "receipt"))
def test_orphan_pair_is_preserved_and_never_automatically_completed(
    normal_fixture, prepared, tmp_path, orphan
):
    path = tmp_path / ("issuances" if orphan == "issue" else "receipts") / ORIGIN.isoformat()
    path.mkdir(parents=True)
    marker = path / "keep.txt"
    marker.write_bytes(b"incomplete historical state")
    for operation in (
        lambda: publish_publication(prepared, fixture_root=tmp_path),
        lambda: _verify(tmp_path, prepared, normal_fixture[0]),
    ):
        with pytest.raises(IncompletePublicationError):
            operation()
    assert marker.read_bytes() == b"incomplete historical state"


@pytest.mark.parametrize("root_kind", ("relative", "traversal", "checkout", "temporary_base"))
def test_unsafe_roots_rejected_before_writes(prepared, tmp_path, root_kind):
    roots = {
        "relative": Path("relative-fixture"),
        "traversal": tmp_path / ".." / "unsafe",
        "checkout": REPOSITORY / "data" / "processed" / "fixture-denied",
        "temporary_base": Path(publication.tempfile.gettempdir()),
    }
    with pytest.raises(Phase13PublicationError):
        publish_publication(prepared, fixture_root=roots[root_kind])


def test_reparse_is_rejected_before_any_content_read(prepared, tmp_path, monkeypatch):
    target = tmp_path / "issuances"
    target.mkdir()
    original = Path.lstat

    def alias(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == target:
            from types import SimpleNamespace

            return SimpleNamespace(
                st_mode=info.st_mode, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT
            )
        return info

    monkeypatch.setattr(Path, "lstat", alias)
    monkeypatch.setattr(publication, "_read", lambda *_: pytest.fail("read before alias rejection"))
    with pytest.raises(Phase13PublicationError):
        publish_publication(prepared, fixture_root=tmp_path)


def test_real_symlink_rejected_when_host_permits(prepared, tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    try:
        (root / "issuances").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        error_code = getattr(error, "winerror", error.errno)
        pytest.skip(f"Host cannot create directory symlinks: {error_code}")
    with pytest.raises(Phase13PublicationError):
        publish_publication(prepared, fixture_root=root)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize(
    "boundary",
    (
        "VALIDATED",
        "STAGING",
        "written:raw_records.json",
        "fsynced:raw_records.json",
        "STAGED_VERIFIED",
        "written:manifest.json",
        "fsynced:manifest.json",
        "MANIFEST_SEALED",
        "DIRECTORY_PUBLISHED",
        "written:receipt.json",
        "fsynced:receipt.json",
        "RECEIPT_STAGED",
        "RECEIPT_PUBLISHED",
        "VERIFIED",
    ),
)
def test_failure_injection_never_rolls_back_final_or_returns_success(
    normal_fixture, prepared, tmp_path, monkeypatch, boundary
):
    old = tmp_path / ".staging" / "m4a-old"
    old.mkdir(parents=True)
    (old / "keep.txt").write_bytes(b"old staging is inert")

    def interrupt(name):
        if name == boundary:
            raise OSError("simulated interruption")

    monkeypatch.setattr(publication, "_transition", interrupt)
    with pytest.raises(Phase13PublicationError):
        publish_publication(prepared, fixture_root=tmp_path)
    issue = tmp_path / "issuances" / ORIGIN.isoformat()
    receipt = tmp_path / "receipts" / ORIGIN.isoformat()
    assert (old / "keep.txt").read_bytes() == b"old staging is inert"
    stages = set(old.parent.iterdir())
    assert old in stages
    assert len(stages) == (1 if boundary == "VALIDATED" else 2)
    if boundary in ("RECEIPT_PUBLISHED", "VERIFIED"):
        assert _verify(tmp_path, prepared, normal_fixture[0]).receipt.release_eligible is False
    elif issue.exists():
        assert not receipt.exists()
        with pytest.raises(IncompletePublicationError):
            _verify(tmp_path, prepared, normal_fixture[0])
        assert (issue / "manifest.json").read_bytes() == prepared._manifest
    else:
        assert not receipt.exists()


@pytest.mark.parametrize("which", ("write", "fsync", "issue_rename", "receipt_rename"))
def test_syscall_failures_preserve_final_state(prepared, tmp_path, monkeypatch, which):
    if which in ("write", "fsync"):
        module, attribute = (
            (publication, "_write") if which == "write" else (publication.os, "fsync")
        )

        def fail(*_args, **_kwargs):
            raise OSError("simulated filesystem failure")

        monkeypatch.setattr(module, attribute, fail)
    else:
        original = publication._rename_final_directory

        def fail_at(stage, destination):
            if destination.parent.name == ("issuances" if which == "issue_rename" else "receipts"):
                raise OSError("simulated rename failure")
            return original(stage, destination)

        monkeypatch.setattr(publication, "_rename_final_directory", fail_at)
    with pytest.raises(Phase13PublicationError):
        publish_publication(prepared, fixture_root=tmp_path)
    assert not (tmp_path / "receipts" / ORIGIN.isoformat()).exists()
    if which == "receipt_rename":
        assert (tmp_path / "issuances" / ORIGIN.isoformat() / "manifest.json").exists()


@pytest.mark.parametrize("with_marker", (False, True))
def test_late_destination_collision_never_overwrites(prepared, tmp_path, monkeypatch, with_marker):
    def collide(name):
        if name == "MANIFEST_SEALED":
            destination = tmp_path / "issuances" / ORIGIN.isoformat()
            destination.mkdir()
            if with_marker:
                (destination / "unrelated.txt").write_bytes(b"unrelated existing directory")

    monkeypatch.setattr(publication, "_transition", collide)
    with pytest.raises(Phase13PublicationError):
        publish_publication(prepared, fixture_root=tmp_path)
    destination = tmp_path / "issuances" / ORIGIN.isoformat()
    if with_marker:
        assert [p.name for p in destination.iterdir()] == ["unrelated.txt"]
        assert (destination / "unrelated.txt").read_bytes() == b"unrelated existing directory"
    else:
        assert list(destination.iterdir()) == []
    assert not (tmp_path / "receipts" / ORIGIN.isoformat()).exists()


def test_uncertain_current_staging_content_is_preserved(prepared, tmp_path, monkeypatch):
    markers = []

    def interfere(name):
        if name == "STAGING":
            stage = next((tmp_path / ".staging").iterdir())
            marker = stage / "unrelated-user-file.txt"
            marker.write_bytes(b"preserve unexpected content")
            markers.append(marker)
            raise OSError("simulated interruption with uncertain ownership")

    monkeypatch.setattr(publication, "_transition", interfere)
    with pytest.raises(IncompletePublicationError, match="retained for explicit reconciliation"):
        publish_publication(prepared, fixture_root=tmp_path)
    assert len(markers) == 1 and markers[0].read_bytes() == b"preserve unexpected content"
    assert not (tmp_path / "issuances" / ORIGIN.isoformat()).exists()


@pytest.mark.parametrize(
    "boundary", ("STAGED_VERIFIED", "DIRECTORY_PUBLISHED", "RECEIPT_PUBLISHED")
)
def test_subprocess_interruption_and_fresh_process_restart(
    normal_fixture, prepared, tmp_path, boundary
):
    root = tmp_path / "child"
    script = """
import os,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import test_phase13_publication as fixture
import rossmann_forecasting.phase13.publication as p
parents, issued, targets, metadata = fixture._fixture()
prepared = fixture._prepare((parents, issued, targets, metadata))
root = Path(sys.argv[2])
if sys.argv[3] == 'publish':
    def interrupt(name):
        if name == sys.argv[4]: os._exit(73)
    p._transition = interrupt
    p.publish_publication(prepared, fixture_root=root)
else:
    try:
        verified = p.verify_publication(
            fixture_root=root, expected_binding=prepared.binding, trusted_parents=parents)
        assert p.load_issued_view(verified).receipt.release_eligible is False
    except p.IncompletePublicationError:
        sys.exit(74)
"""
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    arguments = [str(REPOSITORY / "tests"), str(root)]
    child = subprocess.run(
        [sys.executable, "-B", "-c", script, *arguments, "publish", boundary],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert child.returncode == 73, child.stderr
    restarted = subprocess.run(
        [sys.executable, "-B", "-c", script, *arguments, "verify", boundary],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert restarted.returncode == (0 if boundary == "RECEIPT_PUBLISHED" else 74), restarted.stderr
    assert list((root / ".staging").iterdir())  # staging is inert across restarts
    if boundary == "RECEIPT_PUBLISHED":
        assert _verify(root, prepared, normal_fixture[0]).receipt.release_eligible is False
    else:
        with pytest.raises(IncompletePublicationError):
            _verify(root, prepared, normal_fixture[0])


def test_bounds_and_unverified_objects_fail(normal_fixture, prepared, tmp_path, monkeypatch):
    with pytest.raises(Phase13PublicationError):
        load_issued_view(prepared)
    forged = publication.VerifiedPublication(
        prepared.binding, publication._receipt(prepared), b"{}", b"{}", b"{}"
    )
    with pytest.raises(Phase13PublicationError):
        load_issued_view(forged)
    with pytest.raises(Phase13PublicationError):
        publish_publication(replace(prepared), fixture_root=tmp_path)
    monkeypatch.setattr(publication, "MAX_TABLE_BYTES", 1)
    with pytest.raises(Phase13PublicationError):
        _prepare(normal_fixture)


def test_file_growth_during_read_is_detected(prepared, tmp_path, monkeypatch):
    publish_publication(prepared, fixture_root=tmp_path)
    target = tmp_path / "issuances" / ORIGIN.isoformat() / "raw_records.json"
    identity = target.stat().st_ino
    original = publication.os.fstat
    calls = []

    def changed(descriptor):
        info = original(descriptor)
        if info.st_ino == identity:
            calls.append(info)
            if len(calls) == 2:
                with target.open("ab") as output:
                    output.write(b" ")
                return original(descriptor)
        return info

    monkeypatch.setattr(publication.os, "fstat", changed)
    with pytest.raises(Phase13PublicationError, match="changed while reading"):
        publication._read(target)


def test_replaced_staging_directory_is_never_removed(prepared, tmp_path, monkeypatch):
    displaced = tmp_path / "displaced-owned-stage"
    replacements = []

    def replace_stage(name):
        if name == "STAGING":
            stage = next((tmp_path / ".staging").iterdir())
            stage.rename(displaced)
            (stage / "issue").mkdir(parents=True)
            marker = stage / "issue" / "metadata.json"
            marker.write_bytes(b"replacement directory, plausible publication filename")
            replacements.append(marker)
            raise OSError("publication failed after staging replacement")

    monkeypatch.setattr(publication, "_transition", replace_stage)
    with pytest.raises(Phase13PublicationError) as failure:
        publish_publication(prepared, fixture_root=tmp_path)
    assert replacements[0].read_bytes() == b"replacement directory, plausible publication filename"
    assert (displaced / "issue").is_dir()
    assert not (tmp_path / "receipts" / ORIGIN.isoformat()).exists()
    assert not (tmp_path / "issuances" / ORIGIN.isoformat()).exists()
    assert isinstance(failure.value, IncompletePublicationError)
    assert "reconcil" in str(failure.value)


def test_failed_staging_is_inert_across_repeated_attempts(
    normal_fixture, prepared, tmp_path, monkeypatch
):
    def fail(name):
        if name == "STAGED_VERIFIED":
            raise OSError("before final publication")

    with monkeypatch.context() as injection:
        injection.setattr(publication, "_transition", fail)
        for _ in range(2):
            with pytest.raises(IncompletePublicationError, match="reconcil"):
                publish_publication(prepared, fixture_root=tmp_path)
    stages = list((tmp_path / ".staging").iterdir())
    assert len(stages) == 2
    retained = {p: p.read_bytes() for stage in stages for p in stage.rglob("*") if p.is_file()}
    assert retained
    assert not (tmp_path / "receipts" / ORIGIN.isoformat()).exists()
    receipt = publish_publication(prepared, fixture_root=tmp_path)
    assert publish_publication(prepared, fixture_root=tmp_path) == receipt
    assert _verify(tmp_path, prepared, normal_fixture[0]).receipt == receipt
    assert all(path.read_bytes() == content for path, content in retained.items())


def test_staging_audit_error_preserves_incomplete_final_state(prepared, tmp_path, monkeypatch):
    stages = []
    original = Path.lstat

    def unavailable(path, *args, **kwargs):
        if stages and path == stages[0]:
            raise OSError("staging identity audit unavailable")
        return original(path, *args, **kwargs)

    def fail_after_final_rename(name):
        if name == "DIRECTORY_PUBLISHED":
            stages.extend((tmp_path / ".staging").iterdir())
            raise OSError("interrupted immediately after final rename")

    with monkeypatch.context() as injection:
        injection.setattr(publication, "_transition", fail_after_final_rename)
        injection.setattr(Path, "lstat", unavailable)
        with pytest.raises(IncompletePublicationError, match="reconciliation"):
            publish_publication(prepared, fixture_root=tmp_path)
    assert len(stages) == 1 and stages[0].is_dir()
    issue = tmp_path / "issuances" / ORIGIN.isoformat()
    assert (issue / "manifest.json").read_bytes() == prepared._manifest
    assert not (tmp_path / "receipts" / ORIGIN.isoformat()).exists()
    with pytest.raises(IncompletePublicationError):
        publish_publication(prepared, fixture_root=tmp_path)


@pytest.mark.parametrize("operation", ("prepare", "verify"))
@pytest.mark.parametrize(
    "mutation",
    (
        "canonical_classification",
        "missing_classification",
        "anchor_not_synthetic",
        "anchor_numeric_synthetic",
        "anchor_availability_assumption",
        "anchor_empty_version",
        "anchor_empty_parent_identity",
    ),
)
def test_mutated_synthetic_provenance_cannot_be_repackaged(tmp_path, operation, mutation):
    fixture = _fixture()
    parents = fixture[0]
    prepared = _prepare(fixture)
    if operation == "verify":
        publish_publication(prepared, fixture_root=tmp_path)
    if mutation.endswith("classification"):
        object.__setattr__(
            parents.quantiles,
            "content_classification",
            "canonical_fit_b_content" if mutation == "canonical_classification" else "",
        )
    else:
        # Check every nested entry, including the last rather than only the first.
        anchor = parents.anchors.anchors[-1]
        if mutation in ("anchor_not_synthetic", "anchor_numeric_synthetic"):
            object.__setattr__(
                anchor, "synthetic_only", False if mutation == "anchor_not_synthetic" else 1
            )
        else:
            attribute, value = {
                "anchor_availability_assumption": (
                    "availability_assumption",
                    AvailabilityAssumption.OBSERVED_THROUGH_ORIGIN,
                ),
                "anchor_empty_version": ("version", ""),
                "anchor_empty_parent_identity": ("parent_identities", ("",)),
            }[mutation]
            object.__setattr__(anchor.provenance, attribute, value)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(Phase13PublicationError):
        if operation == "prepare":
            payload = _prepare(fixture)
            publish_publication(payload, fixture_root=tmp_path)
            _verify(tmp_path, payload, parents)
        else:
            _verify(tmp_path, prepared, parents)
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    if operation == "prepare":
        assert list(tmp_path.iterdir()) == []


def test_serialization_uses_validated_parent_snapshots(monkeypatch):
    fixture = _fixture()
    expected = _prepare(fixture)
    original = publication._assemble

    def mutate_caller_then_assemble(*args):
        object.__setattr__(
            fixture[0].quantiles, "content_classification", "canonical_fit_b_content"
        )
        object.__setattr__(fixture[0].anchors.anchors[0], "synthetic_only", False)
        return original(*args)

    monkeypatch.setattr(publication, "_assemble", mutate_caller_then_assemble)
    assert _prepare(fixture) == expected


@pytest.mark.parametrize("replacement", ("hardlink", "regular"))
def test_opened_replacement_is_rejected_before_canary_read(
    normal_fixture, prepared, tmp_path, monkeypatch, replacement
):
    publish_publication(prepared, fixture_root=tmp_path)
    target = tmp_path / "issuances" / ORIGIN.isoformat() / "raw_records.json"
    canary = tmp_path / "canary.json"
    canary.write_bytes(b"PRIVATE CANARY BYTES MUST NOT BE READ")
    original = Path.open
    reads, opened = [], []

    class ObservedReader:
        def __init__(self, source):
            self.source = source

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.source.__exit__(*args)

        def fileno(self):
            return self.source.fileno()

        def read(self, *args):
            reads.append("replacement read attempted")
            return self.source.read(*args)

    def substitute(path, *args, **kwargs):
        if path == target and args == ("rb",) and not opened:
            target.rename(tmp_path / "admitted-original.json")
            if replacement == "hardlink":
                os.link(canary, target)
                assert target.stat().st_nlink == 2
            else:
                with original(target, "wb") as output:
                    output.write(b"PRIVATE CANARY BYTES MUST NOT BE READ")
            source = original(path, *args, **kwargs)
            opened.append(source)
            return ObservedReader(source)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", substitute)
    with pytest.raises(Phase13PublicationError):
        _verify(tmp_path, prepared, normal_fixture[0])
    assert len(opened) == 1 and opened[0].closed
    assert reads == []
    assert canary.read_bytes() == b"PRIVATE CANARY BYTES MUST NOT BE READ"


@pytest.mark.parametrize("alias", ("hardlink", "symlink"))
def test_static_payload_alias_is_rejected_before_read(
    normal_fixture, prepared, tmp_path, monkeypatch, alias
):
    publish_publication(prepared, fixture_root=tmp_path)
    target = tmp_path / "issuances" / ORIGIN.isoformat() / "raw_records.json"
    outside = tmp_path / "outside.json"
    target.rename(outside)
    if alias == "hardlink":
        os.link(outside, target)
    else:
        try:
            target.symlink_to(outside)
        except OSError as error:
            pytest.skip(
                f"Host cannot create file symlinks: {getattr(error, 'winerror', error.errno)}"
            )
    monkeypatch.setattr(publication, "_read", lambda *_: pytest.fail("alias content read"))
    with pytest.raises(Phase13PublicationError):
        _verify(tmp_path, prepared, normal_fixture[0])


@pytest.mark.parametrize(
    "attribute,value",
    (
        ("st_ino", 0),
        ("st_dev", None),
        ("st_mode", stat.S_IFDIR),
        ("st_nlink", 2),
        ("st_file_attributes", stat.FILE_ATTRIBUTE_REPARSE_POINT),
    ),
)
def test_opened_descriptor_requires_supported_unaliased_identity(
    prepared, tmp_path, monkeypatch, attribute, value
):
    from types import SimpleNamespace

    publish_publication(prepared, fixture_root=tmp_path)
    target = tmp_path / "issuances" / ORIGIN.isoformat() / "raw_records.json"
    original = publication.os.fstat
    original_read = publication._read
    identity = target.stat().st_ino

    def unsupported(descriptor):
        info = original(descriptor)
        if info.st_ino == identity:
            body = {
                name: getattr(info, name)
                for name in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")
            }
            return SimpleNamespace(**{**body, attribute: value})
        return info

    monkeypatch.setattr(publication.os, "fstat", unsupported)
    with pytest.raises(Phase13PublicationError):
        original_read(target)


@pytest.mark.parametrize("fail_flush", (False, True))
def test_linux_directory_sync_orders_flush_and_close(tmp_path, monkeypatch, fail_flush):
    from types import SimpleNamespace

    events = []

    def opened(path, flags):
        events.append(("open", path, flags))
        return 42

    def flushed(descriptor):
        events.append(("fsync", descriptor))
        if fail_flush:
            raise OSError("directory flush failure")

    def closed(descriptor):
        events.append(("close", descriptor))

    monkeypatch.setattr(
        publication,
        "os",
        SimpleNamespace(
            name="posix",
            O_RDONLY=0,
            O_DIRECTORY=1,
            open=opened,
            fsync=flushed,
            close=closed,
        ),
    )
    if fail_flush:
        with pytest.raises(OSError):
            publication._sync_directory(tmp_path)
    else:
        publication._sync_directory(tmp_path)
    assert events == [("open", tmp_path, 1), ("fsync", 42), ("close", 42)]


@pytest.mark.parametrize("stores", ((1, 2), tuple(range(1, 17))))
def test_small_medium_resource_measurements(stores, tmp_path):
    fixture = _fixture(stores=stores)

    def measure(function):
        tracemalloc.start()
        started = time.perf_counter()
        result = function()
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return result, round(elapsed, 6), peak

    _, reconstruction_seconds, reconstruction_peak = measure(
        lambda: publication._authoritative(fixture[0])
    )
    prepared, prepare_seconds, prepare_peak = measure(lambda: _prepare(fixture))
    _, publish_seconds, publish_peak = measure(
        lambda: publish_publication(prepared, fixture_root=tmp_path)
    )
    verified, verify_seconds, verify_peak = measure(lambda: _verify(tmp_path, prepared, fixture[0]))
    assert len(load_issued_view(verified).to_frame()) == 14 * len(stores)
    serialized = sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file())
    print(
        "M4A_RESOURCE "
        + json.dumps(
            {
                "stores": len(stores),
                "reconstruction_seconds": reconstruction_seconds,
                "prepare_seconds": prepare_seconds,
                "publish_seconds": publish_seconds,
                "verify_seconds": verify_seconds,
                "python_peak_bytes": {
                    "reconstruction": reconstruction_peak,
                    "prepare": prepare_peak,
                    "publish": publish_peak,
                    "verify": verify_peak,
                },
                "serialized_bytes": serialized,
                "full_roster_feasibility_established": False,
            },
            sort_keys=True,
        )
    )
