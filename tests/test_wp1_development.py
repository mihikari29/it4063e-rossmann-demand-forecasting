from __future__ import annotations

import builtins
import csv
import io
import json
import socket
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from rossmann_forecasting.data import wp1_development as development
from rossmann_forecasting.data.wp1_preparation import (
    SOURCE_COLUMNS,
    WP1PreparationError,
    build_promo_membership,
    prepare_candidate_records,
    prepare_target_observations,
)
from rossmann_forecasting.forecasting import (
    holt_winters,
    lightgbm,
    lightgbm_evaluation,
    model_selection,
    scenario_evaluation,
    seasonal_naive,
)
from rossmann_forecasting.forecasting.model_selection import CANDIDATE_IDS, FORECAST_COLUMNS
from rossmann_forecasting.forecasting.validation import APPROVED_DEVELOPMENT_WINDOWS


def _source_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    cases = [(1, 1, 0, 1, 0), (1, 14, 20, 0, 1), (2, 1, None, 1, None), (2, 14, 30, None, 0)]
    for window_index, window in enumerate(APPROVED_DEVELOPMENT_WINDOWS):
        for case_index, (store, horizon, sales, source_open, promo) in enumerate(cases):
            if window_index == 1 and store == 2 and horizon == 14:
                continue
            target = (window.forecast_origin + pd.Timedelta(days=horizon)).date().isoformat()
            rows.append(
                [
                    str(store),
                    str(pd.Timestamp(target).isoweekday()),
                    target,
                    "" if sales is None else str(sales + window_index + case_index),
                    "synthetic-only-unused",
                    "" if source_open is None else str(source_open),
                    "" if promo is None else str(promo),
                    "0",
                    "0",
                ]
            )
    return rows


def _independent_reference_rows() -> list[list[str]]:
    """Hand-constructed source oracle, separate from the preparer's fixture-row helper."""

    rows: list[list[str]] = []
    for index, window in enumerate(APPROVED_DEVELOPMENT_WINDOWS):
        expected = [
            (1, 1, index, 1, 0),
            (1, 14, 21 + index, 0, 1),
            (2, 1, None, 1, None),
        ]
        if index != 1:
            expected.append((2, 14, 33 + index, None, 0))
        for store, horizon, sales, source_open, promo in expected:
            target = (window.forecast_origin + pd.Timedelta(days=horizon)).date().isoformat()
            rows.append(
                [
                    str(store),
                    str(pd.Timestamp(target).isoweekday()),
                    target,
                    "" if sales is None else str(sales),
                    "independent-reference-only",
                    "" if source_open is None else str(source_open),
                    "" if promo is None else str(promo),
                    "0",
                    "0",
                ]
            )
    return rows


def _csv_bytes(rows: list[list[str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(SOURCE_COLUMNS)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _reference_bytes(*extra_rows: list[str]) -> bytes:
    return _csv_bytes([*_independent_reference_rows(), *extra_rows])


def _candidate_frames(source_rows: list[list[str]]) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for candidate_index, candidate in enumerate(CANDIDATE_IDS):
        records = []
        for row in source_rows:
            store = int(row[0])
            target = pd.Timestamp(row[2])
            window = next(
                item
                for item in APPROVED_DEVELOPMENT_WINDOWS
                if item.target_start <= target <= item.target_end
            )
            horizon = (target - window.forecast_origin).days
            sales = None if row[3] == "" else float(row[3])
            source_open = None if row[5] == "" else float(row[5])
            available = not (
                candidate == CANDIDATE_IDS[1]
                and store == 1
                and horizon == 14
                and window.name == "validation_3"
            )
            record = {
                "Store": store,
                "forecast_origin": window.forecast_origin,
                "Date": target,
                "horizon": horizon,
                "validation_window": window.name,
                "actual_sales": sales,
                "source_open": source_open,
                FORECAST_COLUMNS[candidate]: float(80 + candidate_index + horizon)
                if available
                else None,
                "forecast_available": available,
                "primary_evaluation_eligible": available and source_open == 1 and sales is not None,
            }
            if candidate == CANDIDATE_IDS[1]:
                record["fit_failure_reason"] = None if available else "synthetic_fit_failure"
            records.append(record)
        frames[candidate] = pd.DataFrame(records)
    return frames


def _snapshot() -> tuple[development.WP1FixtureSnapshot, list[list[str]], dict[str, pd.DataFrame]]:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    return development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates), rows, candidates


def _verified_fixture_binding(
    snapshot: development.WP1FixtureSnapshot,
    reference: bytes | None = None,
) -> tuple[bytes, development.WP1FixtureVerification, development.WP1FixtureBinding]:
    source_reference = _reference_bytes() if reference is None else reference
    verification = development.verify_wp1_fixture_snapshot(snapshot, source_reference)
    binding = development.WP1FixtureBinding(
        schema_version=development.SCHEMA_VERSION,
        purpose=development.PURPOSE,
        preparation_manifest_sha256=verification.preparation_manifest_sha256,
        payload_inventory_sha256=verification.payload_inventory_sha256,
        preparation_receipt_sha256=verification.preparation_receipt_sha256,
        verification_identity_sha256=verification.identity_sha256,
        candidate_identities=verification.candidate_identities,
        development_cutoff=development.DEVELOPMENT_CUTOFF,
        approved_windows=tuple(
            (
                window.name,
                window.forecast_origin.date().isoformat(),
                window.target_start.date().isoformat(),
                window.target_end.date().isoformat(),
            )
            for window in APPROVED_DEVELOPMENT_WINDOWS
        ),
        enabled_dimensions=("Promo",),
        h_segmentation_enabled=False,
        external_fixture_use_reference="reviewed-fixture-test:WP1-S16",
    )
    return source_reference, verification, binding


def _load_bound_fixture(
    snapshot: development.WP1FixtureSnapshot,
    reference: bytes | None = None,
) -> development.WP1BoundFixtureData:
    source_reference, verification, binding = _verified_fixture_binding(snapshot, reference)
    return development.load_wp1_fixture_provider(
        snapshot,
        source_reference,
        verification,
        binding,
        fixture_use_context=development.FIXTURE_USE_CONTEXT,
    )


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def _reseal(
    snapshot: development.WP1FixtureSnapshot,
    *,
    payload_change: tuple[str, bytes] | None = None,
    manifest_change: Any = None,
) -> development.WP1FixtureSnapshot:
    payloads = dict(snapshot.payloads)
    if payload_change is not None:
        payloads[payload_change[0]] = payload_change[1]
    manifest = json.loads(snapshot.preparation_manifest)
    if manifest_change is not None:
        manifest_change(manifest)
    manifest["prepared_payloads"] = {
        name: {"byte_count": len(content), "sha256": development._sha256(content)}
        for name, content in sorted(payloads.items())
    }
    manifest_bytes = _canonical(manifest)
    receipt = {
        "schema_version": development.SCHEMA_VERSION,
        "purpose": development.PURPOSE,
        "receipt_type": "synthetic_fixture_preparation_consistency",
        "preparation_manifest_sha256": development._sha256(manifest_bytes),
        "payload_inventory_sha256": development._sha256(_canonical(manifest["prepared_payloads"])),
        "authorization_granted": False,
        "limitations": list(development._SECURITY_LIMITATIONS),
    }
    return development.WP1FixtureSnapshot(
        payloads=tuple(sorted(payloads.items())),
        preparation_manifest=manifest_bytes,
        preparation_receipt=_canonical(receipt),
    )


def _replace_table_rows(content: bytes, rows: list[dict[str, Any]]) -> bytes:
    table = json.loads(content)
    table["rows"] = rows
    return _canonical(table)


def test_valid_snapshot_uses_independent_source_roster_and_keeps_three_candidates() -> None:
    snapshot, rows, _ = _snapshot()
    verified = development.verify_wp1_fixture_snapshot(
        snapshot, _csv_bytes(list(reversed(_independent_reference_rows())))
    )
    assert verified.observed_target_rows == len(rows)
    assert verified.candidate_row_counts == tuple(
        (candidate, len(rows)) for candidate in CANDIDATE_IDS
    )
    assert verified.enabled_dimensions == ("Promo",)
    assert json.loads(snapshot.preparation_manifest)["h_segmentation_enabled"] is False
    assert len(verified.source_reference_identity_sha256) == 64
    assert len(verified.source_derived_roster_sha256) == 64
    assert verified.limitations == development._SECURITY_LIMITATIONS


def test_all_candidates_sharing_an_omitted_source_target_still_fail() -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    for candidate in CANDIDATE_IDS:
        candidates[candidate] = candidates[candidate].iloc[1:].reset_index(drop=True)
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    with pytest.raises(development.WP1FixtureEvidenceError, match="population"):
        development.verify_wp1_fixture_snapshot(snapshot, _reference_bytes())


def test_candidate_target_absent_from_source_fails_even_when_all_models_agree() -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    window = APPROVED_DEVELOPMENT_WINDOWS[0]
    extra = {
        "Store": 999,
        "forecast_origin": window.forecast_origin,
        "Date": window.target_start,
        "horizon": 1,
        "validation_window": window.name,
        "actual_sales": 10.0,
        "source_open": 1.0,
        "forecast_available": True,
        "primary_evaluation_eligible": True,
    }
    for candidate in CANDIDATE_IDS:
        candidates[candidate] = pd.concat(
            [candidates[candidate], pd.DataFrame([{**extra, FORECAST_COLUMNS[candidate]: 12.0}])],
            ignore_index=True,
        )
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    with pytest.raises(development.WP1FixtureEvidenceError, match="absent from independent source"):
        development.verify_wp1_fixture_snapshot(snapshot, _reference_bytes())


@pytest.mark.parametrize(("field", "new_value"), [("actual_sales", 777.0), ("source_open", 0.0)])
def test_candidate_source_labels_must_match_independent_sales_and_open(
    field: str, new_value: float
) -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    target_key = (
        candidates[CANDIDATE_IDS[0]].loc[0, "Store"],
        candidates[CANDIDATE_IDS[0]].loc[0, "Date"],
    )
    for candidate in CANDIDATE_IDS:
        frame = candidates[candidate]
        match = frame["Store"].eq(target_key[0]) & frame["Date"].eq(target_key[1])
        frame.loc[match, field] = new_value
        if field == "source_open":
            frame.loc[match, "primary_evaluation_eligible"] = (
                frame.loc[match, "actual_sales"].notna()
                & frame.loc[match, "forecast_available"]
                & (new_value == 1)
            )
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    with pytest.raises(development.WP1FixtureEvidenceError, match="independent source"):
        development.verify_wp1_fixture_snapshot(snapshot, _reference_bytes())


def test_exact_integer_sales_comparison_precedes_phase7_float_normalization() -> None:
    rows = _source_rows()
    exact_source_sales = 2**53
    rows[0][3] = str(exact_source_sales)
    candidates = _candidate_frames(rows)
    for candidate in CANDIDATE_IDS:
        candidates[candidate]["actual_sales"] = candidates[candidate]["actual_sales"].astype(object)
        candidates[candidate].loc[0, "actual_sales"] = exact_source_sales + 1

    # Phase 7's accepted numeric normalizer maps these adjacent large integers to the same
    # float64 value. The fixture payload must preserve the original integer for source checking.
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    reference_rows = _independent_reference_rows()
    reference_rows[0][3] = str(exact_source_sales)
    with pytest.raises(development.WP1FixtureEvidenceError, match="Sales label differs"):
        development.verify_wp1_fixture_snapshot(snapshot, _csv_bytes(reference_rows))


def _large_integer_sales_case(
    candidate_sales: int,
) -> tuple[list[list[str]], dict[str, pd.DataFrame], list[list[str]]]:
    source_rows = _source_rows()
    reference_rows = _independent_reference_rows()
    source_value = 2**53
    source_rows[0][3] = str(source_value)
    reference_rows[0][3] = str(source_value)
    candidates = _candidate_frames(source_rows)
    for frame in candidates.values():
        frame["actual_sales"] = pd.Series(frame["actual_sales"].tolist(), dtype="object")
        frame.at[0, "actual_sales"] = candidate_sales
    return source_rows, candidates, reference_rows


@pytest.mark.parametrize("candidate_sales", [2**53, 2**53 + 1])
@pytest.mark.parametrize("prepare_first", [False, True])
def test_snapshot_preserves_large_sales_from_raw_and_prepared_candidates(
    candidate_sales: int, prepare_first: bool
) -> None:
    source_rows, candidates, reference_rows = _large_integer_sales_case(candidate_sales)
    candidate_input = prepare_candidate_records(candidates) if prepare_first else candidates

    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(source_rows), candidate_input)
    candidate_payload = json.loads(
        dict(snapshot.payloads)[development.CANDIDATE_NAMES[CANDIDATE_IDS[0]]]
    )
    assert candidate_payload["rows"][0]["actual_sales"] == candidate_sales
    if candidate_sales == 2**53:
        assert development.verify_wp1_fixture_snapshot(
            snapshot, _csv_bytes(reference_rows)
        ).observed_target_rows == len(source_rows)
    else:
        with pytest.raises(development.WP1FixtureEvidenceError, match="Sales label differs"):
            development.verify_wp1_fixture_snapshot(snapshot, _csv_bytes(reference_rows))


def test_exact_integer_and_float_sales_equivalence_has_no_tolerance() -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    for frame in candidates.values():
        frame["actual_sales"] = pd.Series(frame["actual_sales"].tolist(), dtype="object")
        frame.at[1, "actual_sales"] = 21.0

    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    assert development.verify_wp1_fixture_snapshot(
        snapshot, _reference_bytes()
    ).observed_target_rows == len(rows)


@pytest.mark.parametrize("candidate", CANDIDATE_IDS)
@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("Store", 1.5),
        ("Store", Decimal("1.0000000000000001")),
        ("source_open", Decimal("1.0000000000000001")),
        ("source_open", "1.0000000000000001"),
    ],
)
def test_snapshot_creation_rejects_original_store_and_open_before_coercion(
    candidate: str, field: str, bad_value: object
) -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    frame = candidates[candidate]
    frame[field] = pd.Series(frame[field].tolist(), dtype="object")
    frame.at[0, field] = bad_value

    with pytest.raises(development.WP1FixtureEvidenceError, match="preparation failed"):
        development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)


@pytest.mark.parametrize(
    "authorization_flag",
    ["operational_permission", "real_source_access", "l4_execution", "publication"],
)
@pytest.mark.parametrize("substitute", [0, 1, "false", None])
def test_resealed_manifest_rejects_non_boolean_authorization_flags(
    authorization_flag: str, substitute: object
) -> None:
    snapshot, _rows, _candidates = _snapshot()

    def set_substitute(manifest: dict[str, Any]) -> None:
        manifest["authorization_limitations"][authorization_flag] = substitute

    changed = _reseal(snapshot, manifest_change=set_substitute)
    with pytest.raises(development.WP1FixtureEvidenceError, match="Boolean"):
        development.verify_wp1_fixture_snapshot(changed, _reference_bytes())


@pytest.mark.parametrize("horizon", [65537, -65535])
def test_original_horizon_overflow_is_rejected_before_narrowing(horizon: int) -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    candidates[CANDIDATE_IDS[0]].loc[0, "horizon"] = horizon
    with pytest.raises(development.WP1FixtureEvidenceError, match="preparation failed"):
        development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)


@pytest.mark.parametrize("horizon", [1, 14])
def test_horizon_boundaries_pass_preparation_and_phase7_validation(horizon: int) -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    candidates = prepare_candidate_records(candidates)
    assert any(candidates[CANDIDATE_IDS[0]]["horizon"].eq(horizon))
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), _candidate_frames(rows))
    assert development.verify_wp1_fixture_snapshot(
        snapshot, _reference_bytes()
    ).observed_target_rows == len(rows)


def test_protected_canary_values_do_not_enter_snapshot_or_errors() -> None:
    rows = _source_rows()
    rows.append(
        [
            "PRIVATE_STORE",
            "bad",
            "2015-07-04",
            "PROTECTED_CANARY_SENTINEL",
            "x",
            "9",
            "8",
            "x",
            "x",
            "extra",
        ]
    )
    candidates = _candidate_frames(_source_rows())
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    protected = [
        "PRIVATE_STORE",
        "bad",
        "2015-07-04",
        "PROTECTED_CANARY_SENTINEL",
        "x",
        "9",
        "8",
        "x",
        "x",
        "extra",
    ]
    development.verify_wp1_fixture_snapshot(
        snapshot, _csv_bytes(list(reversed([*_independent_reference_rows(), protected])))
    )
    all_bytes = (
        snapshot.preparation_manifest
        + snapshot.preparation_receipt
        + b"".join(content for _, content in snapshot.payloads)
    )
    assert b"PROTECTED_CANARY_SENTINEL" not in all_bytes
    assert b"PRIVATE_STORE" not in all_bytes
    assert "PROTECTED_CANARY_SENTINEL" not in repr(snapshot)

    invalid_target = _source_rows()
    invalid_target[0][3] = "TARGET_PRIVATE_SENTINEL"
    with pytest.raises(WP1PreparationError) as caught:
        prepare_target_observations(_csv_bytes(invalid_target))
    assert "TARGET_PRIVATE_SENTINEL" not in str(caught.value)


def test_duplicate_source_keys_and_sparse_null_zero_labels_are_preserved() -> None:
    rows = _source_rows()
    with pytest.raises(WP1PreparationError, match="duplicate"):
        prepare_target_observations(_csv_bytes([*rows, rows[0]]))
    observations = prepare_target_observations(_csv_bytes(rows))
    assert len(observations) == 11
    assert observations["Sales"].eq(0).any()
    assert observations["Sales"].isna().any()
    assert observations["Open"].isna().any()
    assert not observations.duplicated(["Store", "Date"]).any()


def test_open_one_zero_sales_remains_label_eligible_and_raw_candidate_values_are_used() -> None:
    rows = _source_rows()
    observations = prepare_target_observations(_csv_bytes(rows))
    candidates = prepare_candidate_records(_candidate_frames(rows))
    population = scenario_evaluation.build_scenario_population(candidates)
    zero_key = observations.loc[observations["Sales"].eq(0), ["Store", "Date"]].iloc[0]
    matched = population[
        population["Store"].eq(zero_key["Store"]) & population["Date"].eq(zero_key["Date"])
    ]
    assert len(matched) == 1
    assert matched.iloc[0]["label_eligible"]
    for candidate in CANDIDATE_IDS:
        assert (
            matched.iloc[0][FORECAST_COLUMNS[candidate]]
            == candidates[candidate]
            .loc[
                candidates[candidate]["Store"].eq(zero_key["Store"])
                & candidates[candidate]["Date"].eq(zero_key["Date"]),
                "raw_model_forecast",
            ]
            .iloc[0]
        )


def test_availability_masks_and_original_reason_fields_are_integrity_checked() -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    candidate = CANDIDATE_IDS[1]
    unavailable = candidates[candidate]["fit_failure_reason"].notna()
    assert unavailable.any()
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    assert development.verify_wp1_fixture_snapshot(
        snapshot, _reference_bytes()
    ).observed_target_rows == len(rows)

    broken = _candidate_frames(rows)
    broken[CANDIDATE_IDS[0]].loc[0, "forecast_available"] = False
    broken[CANDIDATE_IDS[0]].loc[0, "primary_evaluation_eligible"] = False
    with pytest.raises(development.WP1FixtureEvidenceError, match="preparation failed"):
        development.create_wp1_fixture_snapshot(_csv_bytes(rows), broken)
    broken = _candidate_frames(rows)
    broken[candidate].loc[unavailable, "fit_failure_reason"] = ""
    with pytest.raises(development.WP1FixtureEvidenceError, match="preparation failed"):
        development.create_wp1_fixture_snapshot(_csv_bytes(rows), broken)


def test_promo_zero_one_null_are_rows_and_a_missing_membership_key_fails() -> None:
    snapshot, rows, _ = _snapshot()
    verified = development.verify_wp1_fixture_snapshot(snapshot, _reference_bytes())
    assert verified.enabled_dimensions == ("Promo",)
    promo_table = json.loads(dict(snapshot.payloads)[development.PROMO_NAME])
    assert {row["Promo"] for row in promo_table["rows"]} >= {0, 1, None}

    changed_rows = promo_table["rows"][:-1]
    mutated = _reseal(
        snapshot,
        payload_change=(
            development.PROMO_NAME,
            _replace_table_rows(dict(snapshot.payloads)[development.PROMO_NAME], changed_rows),
        ),
    )
    with pytest.raises(development.WP1FixtureEvidenceError, match="Promo membership"):
        development.verify_wp1_fixture_snapshot(mutated, _reference_bytes())

    invalid_rows = _source_rows()
    invalid_rows[0][6] = "2"
    with pytest.raises(WP1PreparationError, match="Promo"):
        prepare_target_observations(_csv_bytes(invalid_rows))


@pytest.mark.parametrize("part", ["manifest", "payload", "receipt"])
def test_changed_manifest_payload_or_receipt_identity_fails(part: str) -> None:
    snapshot, rows, _ = _snapshot()
    if part == "manifest":
        changed = replace(snapshot, preparation_manifest=snapshot.preparation_manifest + b" ")
    elif part == "receipt":
        changed = replace(snapshot, preparation_receipt=snapshot.preparation_receipt + b" ")
    else:
        payloads = list(snapshot.payloads)
        name, content = payloads[0]
        payloads[0] = (name, content + b" ")
        changed = replace(snapshot, payloads=tuple(payloads))
    with pytest.raises(development.WP1FixtureEvidenceError):
        development.verify_wp1_fixture_snapshot(changed, _reference_bytes())


@pytest.mark.parametrize("mutation", ["schema", "count", "unsupported", "purpose", "h_enabled"])
def test_manifest_schema_counts_and_declarations_are_strict(mutation: str) -> None:
    snapshot, rows, _ = _snapshot()

    def change(manifest: dict[str, Any]) -> None:
        if mutation == "schema":
            manifest["schemas"]["source_observations"].remove("Promo")
        elif mutation == "count":
            manifest["populations"]["source_observations"]["rows"] += 1
        elif mutation == "unsupported":
            manifest["unexpected"] = "no"
        elif mutation == "h_enabled":
            manifest["h_segmentation_enabled"] = True
        else:
            manifest["purpose"] = "real_input"

    changed = _reseal(snapshot, manifest_change=change)
    with pytest.raises(development.WP1FixtureEvidenceError):
        development.verify_wp1_fixture_snapshot(changed, _reference_bytes())


def test_duplicate_json_keys_and_noncanonical_json_fail_closed() -> None:
    snapshot, rows, _ = _snapshot()
    duplicate_manifest = snapshot.preparation_manifest.replace(
        b'"purpose":"wp1_synthetic_fixture_milestone_1"',
        b'"purpose":"wp1_synthetic_fixture_milestone_1","purpose":"other"',
    )
    with pytest.raises(development.WP1FixtureEvidenceError, match="duplicate"):
        development.verify_wp1_fixture_snapshot(
            replace(snapshot, preparation_manifest=duplicate_manifest), _reference_bytes()
        )
    with pytest.raises(development.WP1FixtureEvidenceError, match="canonical"):
        development.verify_wp1_fixture_snapshot(
            replace(snapshot, preparation_manifest=snapshot.preparation_manifest + b"\n"),
            _reference_bytes(),
        )


def test_payload_values_and_missing_membership_are_checked_after_valid_resealing() -> None:
    snapshot, rows, _ = _snapshot()
    source_content = dict(snapshot.payloads)[development.OBSERVATIONS_NAME]
    source_table = json.loads(source_content)
    source_table["rows"][0]["Promo"] = 9
    changed = _reseal(
        snapshot, payload_change=(development.OBSERVATIONS_NAME, _canonical(source_table))
    )
    with pytest.raises(development.WP1FixtureEvidenceError, match="Promo"):
        development.verify_wp1_fixture_snapshot(changed, _reference_bytes())


def test_reordered_valid_inputs_produce_identical_snapshot_bytes() -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    first = development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    reversed_candidates = {
        candidate: candidates[candidate]
        .iloc[::-1]
        .loc[:, list(reversed(candidates[candidate].columns))]
        .copy()
        for candidate in reversed(CANDIDATE_IDS)
    }
    second = development.create_wp1_fixture_snapshot(
        _csv_bytes(list(reversed(rows))), reversed_candidates
    )
    assert first == second


def test_snapshot_creation_does_not_mutate_caller_frames() -> None:
    rows = _source_rows()
    candidates = _candidate_frames(rows)
    before = {candidate: frame.copy(deep=True) for candidate, frame in candidates.items()}
    development.create_wp1_fixture_snapshot(_csv_bytes(rows), candidates)
    for candidate in CANDIDATE_IDS:
        pd.testing.assert_frame_equal(candidates[candidate], before[candidate])


def test_preparation_and_verification_do_not_use_filesystem_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("fixture contract attempted external I/O")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    rows = _source_rows()
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), _candidate_frames(rows))
    development.verify_wp1_fixture_snapshot(
        snapshot, _csv_bytes(list(reversed(_independent_reference_rows())))
    )


def test_verification_never_calls_fit_selection_l2_aggregation_or_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("fixture verification called a later-stage interface")

    monkeypatch.setattr(model_selection, "run_model_selection", forbidden)
    monkeypatch.setattr(seasonal_naive, "forecast_seasonal_naive", forbidden)
    monkeypatch.setattr(holt_winters, "forecast_holt_winters", forbidden)
    monkeypatch.setattr(lightgbm, "fit_lightgbm", forbidden)
    monkeypatch.setattr(lightgbm, "recursive_lightgbm_forecasts", forbidden)
    monkeypatch.setattr(lightgbm_evaluation, "tune_global_lightgbm", forbidden)
    monkeypatch.setattr(scenario_evaluation, "summarize_scenario_population", forbidden)
    monkeypatch.setattr(scenario_evaluation, "serialize_scenario_fixture", forbidden)
    rows = _source_rows()
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(rows), _candidate_frames(rows))
    development.verify_wp1_fixture_snapshot(snapshot, _reference_bytes())


def test_synthetic_outputs_remain_compatible_with_phase7_l1_and_l2() -> None:
    rows = _source_rows()
    observations = prepare_target_observations(_csv_bytes(rows))
    candidates = prepare_candidate_records(_candidate_frames(rows))
    membership = build_promo_membership(observations)
    population = scenario_evaluation.build_scenario_population(candidates)
    assert len(population) == len(observations)
    summary = scenario_evaluation.summarize_scenario_population(
        population, scenario_membership=membership
    )
    assert summary.enabled_scenarios == ("Promo",)
    assert set(summary.metrics["candidate_id"]) == set(CANDIDATE_IDS)


def test_protected_canary_is_absent_from_outputs_and_fixture_errors() -> None:
    rows = _source_rows()
    rows.append(
        [
            "NEVER_EMIT_STORE",
            "bad",
            "2015-07-31",
            "NEVER_EMIT_PROTECTED_SALES",
            "x",
            "7",
            "8",
            "x",
            "x",
        ]
    )
    snapshot = development.create_wp1_fixture_snapshot(
        _csv_bytes(rows), _candidate_frames(_source_rows())
    )
    try:
        verified = development.verify_wp1_fixture_snapshot(snapshot, _reference_bytes(rows[-1]))
    except Exception as exc:  # pragma: no cover - assertion keeps error text under review
        assert "NEVER_EMIT_PROTECTED_SALES" not in str(exc)
        raise
    all_bytes = (
        snapshot.preparation_manifest
        + snapshot.preparation_receipt
        + b"".join(content for _, content in snapshot.payloads)
    )
    assert b"NEVER_EMIT_STORE" not in all_bytes
    assert b"NEVER_EMIT_PROTECTED_SALES" not in all_bytes
    assert verified.observed_target_rows == len(_source_rows())


def test_fixture_provider_completes_external_c_to_v_to_b_handoff() -> None:
    snapshot, source_rows, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    fixture = development.load_wp1_fixture_provider(
        snapshot,
        reference,
        verification,
        binding,
        fixture_use_context=development.FIXTURE_USE_CONTEXT,
    )

    manifest_inventory = json.loads(snapshot.preparation_manifest)["prepared_payloads"]
    assert verification.candidate_identities == tuple(
        (
            candidate,
            FORECAST_COLUMNS[candidate],
            manifest_inventory[development.CANDIDATE_NAMES[candidate]]["sha256"],
        )
        for candidate in CANDIDATE_IDS
    )
    assert fixture.provenance.source_kind == "controlled_project_synthetic_fixture"
    assert (
        fixture.provenance.external_fixture_use_reference == binding.external_fixture_use_reference
    )
    assert fixture.provenance.verification_identity_sha256 == verification.identity_sha256
    assert fixture.provenance.enabled_dimensions == ("Promo",)
    assert fixture.provenance.h_segmentation_enabled is False
    assert fixture.provenance.observed_target_rows == len(source_rows)
    assert set(fixture.candidate_records) == set(CANDIDATE_IDS)
    assert all(len(frame) == len(source_rows) for frame in fixture.candidate_records.values())
    assert len(fixture.promo_membership) == len(source_rows)
    assert fixture.provenance.limitations == development._SECURITY_LIMITATIONS


@pytest.mark.parametrize(
    "binding_change",
    [
        {"schema_version": 2},
        {"purpose": "real_wp1_input"},
        {"candidate_identities": ()},
        {"development_cutoff": "2015-07-31"},
        {"approved_windows": ()},
        {"enabled_dimensions": ("Promo", "H")},
        {"h_segmentation_enabled": True},
        {"preparation_manifest_sha256": "f" * 64},
        {"payload_inventory_sha256": "f" * 64},
        {"preparation_receipt_sha256": "f" * 64},
        {"verification_identity_sha256": "f" * 64},
    ],
)
def test_fixture_provider_rejects_mismatched_external_binding(
    binding_change: dict[str, Any],
) -> None:
    snapshot, _, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    changed_binding = replace(binding, **binding_change)
    with pytest.raises(development.WP1FixtureProviderError, match="binding"):
        development.load_wp1_fixture_provider(
            snapshot,
            reference,
            verification,
            changed_binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )


def test_fixture_provider_requires_verification_binding_and_exact_context() -> None:
    snapshot, _, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    with pytest.raises(development.WP1FixtureProviderError, match="verification"):
        development.load_wp1_fixture_provider(
            snapshot,
            reference,
            None,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )
    with pytest.raises(development.WP1FixtureProviderError, match="binding"):
        development.load_wp1_fixture_provider(
            snapshot,
            reference,
            verification,
            None,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )
    with pytest.raises(development.WP1FixtureProviderError, match="context"):
        development.load_wp1_fixture_provider(snapshot, reference, verification, binding)
    with pytest.raises(development.WP1FixtureProviderError, match="context"):
        development.load_wp1_fixture_provider(
            snapshot,
            reference,
            verification,
            binding,
            fixture_use_context="cc02_real_input_authorization",
        )


def test_fixture_provider_rejects_mismatched_reference_and_stale_verification() -> None:
    snapshot, _, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    changed_reference_rows = _independent_reference_rows()
    changed_reference_rows[0][3] = "999"
    with pytest.raises(development.WP1FixtureProviderError, match="failed verification"):
        development.load_wp1_fixture_provider(
            snapshot,
            _csv_bytes(changed_reference_rows),
            verification,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )

    changed_verification = replace(verification, source_derived_roster_sha256="f" * 64)
    with pytest.raises(development.WP1FixtureProviderError, match="verification"):
        development.load_wp1_fixture_provider(
            snapshot,
            reference,
            changed_verification,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )


@pytest.mark.parametrize("tamper", ["manifest", "payload", "receipt", "missing", "extra"])
def test_fixture_provider_reverifies_snapshot_and_exact_logical_inventory(tamper: str) -> None:
    snapshot, _, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    if tamper == "manifest":
        changed = replace(snapshot, preparation_manifest=snapshot.preparation_manifest + b" ")
    elif tamper == "receipt":
        changed = replace(snapshot, preparation_receipt=snapshot.preparation_receipt + b" ")
    else:
        payloads = list(snapshot.payloads)
        if tamper == "payload":
            name, content = payloads[0]
            payloads[0] = (name, content + b" ")
        elif tamper == "missing":
            payloads.pop()
        else:
            payloads.append(("candidates/unexpected.json", b"{}"))
        changed = replace(snapshot, payloads=tuple(payloads))
    with pytest.raises(development.WP1FixtureEvidenceError):
        development.load_wp1_fixture_provider(
            changed,
            reference,
            verification,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [("Store", 1.0), ("source_open", 0.5), ("horizon", 65537)],
)
def test_fixture_provider_rejects_invalid_original_candidate_values(
    field: str, replacement: int | float
) -> None:
    snapshot, _, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    candidate = CANDIDATE_IDS[0]
    payload_name = development.CANDIDATE_NAMES[candidate]
    rows = json.loads(dict(snapshot.payloads)[payload_name])["rows"]
    rows[0][field] = replacement
    changed = _reseal(
        snapshot,
        payload_change=(
            payload_name,
            _canonical(
                {
                    "columns": json.loads(dict(snapshot.payloads)[payload_name])["columns"],
                    "rows": rows,
                }
            ),
        ),
    )
    with pytest.raises(development.WP1FixtureProviderError, match="failed verification"):
        development.load_wp1_fixture_provider(
            changed,
            reference,
            verification,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )


def test_fixture_provider_enforces_predecode_size_and_population_limits() -> None:
    snapshot, _, _ = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    oversized = replace(
        snapshot,
        preparation_manifest=b" " * (development._MAX_PROVIDER_MANIFEST_BYTES + 1),
    )
    with pytest.raises(development.WP1FixtureProviderError, match="size limit"):
        development.load_wp1_fixture_provider(
            oversized,
            reference,
            verification,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )

    manifest = json.loads(snapshot.preparation_manifest)
    manifest["populations"]["source_observations"]["rows"] = development._MAX_PROVIDER_ROWS + 1
    oversized_population = replace(
        snapshot,
        preparation_manifest=_canonical(manifest),
    )
    with pytest.raises(development.WP1FixtureProviderError, match="row limit"):
        development.load_wp1_fixture_provider(
            oversized_population,
            reference,
            verification,
            binding,
            fixture_use_context=development.FIXTURE_USE_CONTEXT,
        )


def test_fixture_provider_reuses_immutable_snapshot_and_returns_copy_safe_frames() -> None:
    snapshot, _, input_candidates = _snapshot()
    reference, verification, binding = _verified_fixture_binding(snapshot)
    original = development.load_wp1_fixture_provider(
        snapshot,
        reference,
        verification,
        binding,
        fixture_use_context=development.FIXTURE_USE_CONTEXT,
    )
    input_candidates[CANDIDATE_IDS[0]].loc[:, "actual_sales"] = 999999
    first_copy = original.candidate_records
    candidate = CANDIDATE_IDS[0]
    first_copy[candidate].loc[:, "actual_sales"] = 888888
    first_copy[candidate].loc[:, FORECAST_COLUMNS[candidate]] = 0
    first_promo = original.promo_membership
    first_promo.loc[:, "Promo"] = 0

    repeated = development.load_wp1_fixture_provider(
        snapshot,
        reference,
        verification,
        binding,
        fixture_use_context=development.FIXTURE_USE_CONTEXT,
    )
    assert not repeated.candidate_records[candidate]["actual_sales"].eq(888888).any()
    assert not repeated.candidate_records[candidate][FORECAST_COLUMNS[candidate]].eq(0).all()
    assert repeated.promo_membership["Promo"].isna().any()


def test_fixture_provider_preserves_sales_integer_precision_and_promo_null_roster() -> None:
    source_rows = _source_rows()
    reference_rows = _independent_reference_rows()
    large_sales = 2**53 + 1
    target = (APPROVED_DEVELOPMENT_WINDOWS[0].forecast_origin + pd.Timedelta(days=1)).date()
    for row in source_rows:
        if int(row[0]) == 1 and row[2] == target.isoformat():
            row[3] = str(large_sales)
    for row in reference_rows:
        if int(row[0]) == 1 and row[2] == target.isoformat():
            row[3] = str(large_sales)
    candidates = _candidate_frames(source_rows)
    for frame in candidates.values():
        frame["actual_sales"] = pd.Series(
            [
                large_sales
                if int(record.Store) == 1 and pd.Timestamp(record.Date).date() == target
                else record.actual_sales
                for record in frame.itertuples(index=False)
            ],
            dtype="object",
        )
    snapshot = development.create_wp1_fixture_snapshot(_csv_bytes(source_rows), candidates)
    fixture = _load_bound_fixture(snapshot, _csv_bytes(reference_rows))
    candidate = CANDIDATE_IDS[0]
    found = fixture.candidate_records[candidate].loc[
        fixture.candidate_records[candidate]["Date"].eq(pd.Timestamp(target)), "actual_sales"
    ]
    assert found.iloc[0] == large_sales
    assert isinstance(found.iloc[0], int)
    membership = fixture.promo_membership
    assert membership["Promo"].isna().any()
    sparse_missing_key = (
        2,
        APPROVED_DEVELOPMENT_WINDOWS[1].forecast_origin,
        APPROVED_DEVELOPMENT_WINDOWS[1].target_end,
    )
    assert not (
        membership["Store"].eq(sparse_missing_key[0])
        & membership["forecast_origin"].eq(sparse_missing_key[1])
        & membership["Date"].eq(sparse_missing_key[2])
    ).any()


def test_fixture_provider_has_no_io_or_analysis_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("fixture provider attempted I/O or analysis")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    for module, name in (
        (seasonal_naive, "forecast_seasonal_naive"),
        (holt_winters, "forecast_holt_winters"),
        (lightgbm, "fit_lightgbm"),
        (lightgbm, "recursive_lightgbm_forecasts"),
        (lightgbm_evaluation, "tune_global_lightgbm"),
        (scenario_evaluation, "build_scenario_population"),
        (scenario_evaluation, "summarize_scenario_population"),
        (scenario_evaluation, "serialize_scenario_fixture"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    snapshot, _, _ = _snapshot()
    _load_bound_fixture(snapshot)


def test_fixture_provider_outputs_work_with_existing_synthetic_l1_l2_interfaces() -> None:
    snapshot, _, _ = _snapshot()
    fixture = _load_bound_fixture(snapshot)
    population = scenario_evaluation.build_scenario_population(fixture.candidate_records)
    summary = scenario_evaluation.summarize_scenario_population(
        population, scenario_membership=fixture.promo_membership
    )
    assert len(population) == fixture.provenance.observed_target_rows
    assert summary.enabled_scenarios == ("Promo",)
    assert set(summary.metrics["candidate_id"]) == set(CANDIDATE_IDS)
