"""Independent synthetic v1 inputs; no original dataset or saved forecast is used."""

from __future__ import annotations

import builtins
import copy
import hashlib
import io
import json
import os
import subprocess
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import rossmann_forecasting.data.acquisition as acquisition
import rossmann_forecasting.data.cc02_custodian_execution as custodian
import rossmann_forecasting.data.cc02_development as cc02
import rossmann_forecasting.data.cc02_preparation as preparation
import rossmann_forecasting.data.wp1_inputs as inputs
import rossmann_forecasting.forecasting.holt_winters as holt_winters
import rossmann_forecasting.forecasting.model_selection as phase7
import rossmann_forecasting.forecasting.scenario_evaluation as scenarios
import rossmann_forecasting.phase13.issuer as issuer
import rossmann_forecasting.phase13.providers as providers
from rossmann_forecasting.data.wp1_inputs import (
    ScenarioInputBinding,
    ScenarioInputError,
    validate_scenario_input_binding,
    verify_trusted_scenario_fixture_snapshot,
)

_CANDIDATES = (
    "seasonal_naive",
    "holt_winters_additive_weekly",
    "global_lightgbm_gbdt_regression_l1",
)
_RAW = ("raw_baseline_forecast", "raw_statistical_forecast", "raw_lightgbm_forecast")
_KEYS = ["Store", "forecast_origin", "Date"]
_WINDOWS = [
    {
        "name": "validation_1",
        "forecast_origin": "2015-05-22",
        "target_start": "2015-05-23",
        "target_end": "2015-06-05",
    },
    {
        "name": "validation_2",
        "forecast_origin": "2015-06-05",
        "target_start": "2015-06-06",
        "target_end": "2015-06-19",
    },
    {
        "name": "validation_3",
        "forecast_origin": "2015-06-19",
        "target_start": "2015-06-20",
        "target_end": "2015-07-03",
    },
]
_KEY_TEXT = (
    "1\t2015-05-22\t2015-05-23\n1\t2015-05-22\t2015-05-27\n"
    "1\t2015-06-05\t2015-06-06\n1\t2015-06-05\t2015-06-10\n"
    "1\t2015-06-19\t2015-06-20\n1\t2015-06-19\t2015-06-24\n"
    "2\t2015-05-22\t2015-05-25\n2\t2015-05-22\t2015-06-05\n"
    "2\t2015-06-05\t2015-06-08\n2\t2015-06-05\t2015-06-19\n"
    "2\t2015-06-19\t2015-06-22\n2\t2015-06-19\t2015-07-03\n"
    "3\t2015-05-22\t2015-05-24\n3\t2015-05-22\t2015-05-30\n"
    "3\t2015-06-05\t2015-06-07\n3\t2015-06-05\t2015-06-13\n"
    "3\t2015-06-19\t2015-06-21\n3\t2015-06-19\t2015-06-27\n"
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _envelope(payloads: dict[str, bytes], manifest: dict) -> tuple[dict[str, bytes], bytes]:
    manifest["files"] = {
        name: {"bytes": len(content), "sha256": _sha(content)} for name, content in payloads.items()
    }
    manifest["payload_sha256"] = _sha(_json(manifest["files"]))
    return _reseal({**payloads, "manifest.json": b""}, manifest)


def _reseal(files: dict[str, bytes], manifest: dict) -> tuple[dict[str, bytes], bytes]:
    result = {**files, "manifest.json": _json(manifest)}
    receipt = {
        **manifest["preparation"],
        **{
            field: manifest[field]
            for field in (
                "schema_version",
                "purpose",
                "bundle_id",
                "source_lineage_references",
                "payload_sha256",
            )
        },
        "manifest_sha256": _sha(result["manifest.json"]),
    }
    return result, _json(receipt)


@dataclass
class Fixture:
    frames: dict[str, pd.DataFrame]
    archives: dict[str, bytes]
    manifest: dict

    def snapshot(self, *, row_group_size: int | None = None) -> tuple[dict[str, bytes], bytes]:
        payloads = dict(self.archives)
        schemas = {}
        for name, frame in self.frames.items():
            table = pa.Table.from_pandas(frame, preserve_index=False)
            stream = pa.BufferOutputStream()
            pq.write_table(table, stream, row_group_size=row_group_size)
            payloads[name] = stream.getvalue().to_pybytes()
            schemas[name] = [
                {"name": field.name, "type": str(field.type)} for field in table.schema
            ]
        self.manifest["field_schemas"] = schemas
        return _envelope(payloads, self.manifest)


def _fixture(*, metadata: bool = True) -> Fixture:
    # Roster is explicitly declared, never derived from any candidate or the L1 builder.
    rows = [line.split("\t") for line in _KEY_TEXT.splitlines()]
    roster = pd.DataFrame(rows, columns=_KEYS)
    roster["Store"] = roster["Store"].astype("int64")
    for field in ("forecast_origin", "Date"):
        roster[field] = pd.to_datetime(roster[field]).astype("datetime64[ns]")
    frames = {"M/observed_keys.parquet": roster}
    for index, candidate in enumerate(_CANDIDATES):
        candidate_rows = []
        for window in _WINDOWS:
            # Sparse observations, closed/unknown Open, zero/missing Sales, one unavailable path.
            for store, horizon, actual, source_open in (
                (1, 1, 100.0, 1.0),
                (1, 5, 0.0, 1.0),
                (2, 3, 80.0, 0.0),
                (2, 14, 90.0, None),
                (3, 2, None, 1.0),
                (3, 8, 60.0, 1.0),
            ):
                origin = pd.Timestamp(window["forecast_origin"])
                available = not (index == 1 and store == 3 and horizon == 8)
                candidate_rows.append(
                    {
                        "Store": store,
                        "forecast_origin": origin,
                        "Date": origin + pd.Timedelta(days=horizon),
                        "horizon": horizon,
                        "validation_window": window["name"],
                        "actual_sales": actual,
                        "source_open": source_open,
                        _RAW[index]: 10.0 + index if available else None,
                        "forecast_available": available,
                        "primary_evaluation_eligible": source_open == 1
                        and actual is not None
                        and available,
                    }
                )
        frame = pd.DataFrame(candidate_rows)
        if index == 1:
            frame["unavailable_reason"] = [
                None if value else "synthetic_fit_failure" for value in frame["forecast_available"]
            ]
        frames[f"M/{candidate}.parquet"] = frame
    enabled = list(inputs.METADATA_FIELDS) if metadata else []
    if metadata:
        membership = roster.copy(deep=True)
        membership["Promo"] = [0.0, 1.0, None] * 6
        membership["StoreType"] = membership["Store"].map({1: "a", 2: None, 3: "future-type"})
        membership["Assortment"] = membership["Store"].map({1: "a", 2: "b", 3: "c"})
        membership["StateHoliday"] = ["0", "a", "future-holiday"] * 6
        membership["SchoolHoliday"] = [0.0, None, 1.0] * 6
        frames["C/membership.parquet"] = membership
    configuration = _json({"fixture_only": True, "archived_reference": "Z:/inert/config"})
    archives = {"M/lightgbm_configuration.json": configuration}
    for candidate in _CANDIDATES:
        original = {
            "candidate_id": candidate,
            "development_only_through": "2015-07-03",
            "final_holdout_forecast_or_evaluation": False,
            "original_path": "../../inert/no-follow",
            "legacy_field": {"preserved": True},
        }
        if candidate == _CANDIDATES[2]:
            original["configuration_sha256"] = _sha(configuration)
        archives[f"M/original_manifests/{candidate}.json"] = _json(original)
    manifest = {
        "schema_version": 1,
        "purpose": "wp1_scenario_fixture_inputs",
        "input_kind": "synthetic_fixture",
        "bundle_id": "fixture-wp1-v1",
        "development_cutoff": "2015-07-03",
        "h_enabled": False,
        "candidates": {
            candidate: {
                "raw_column": _RAW[i],
                "original_evidence_reference": f"fixture:original:{candidate}",
                "original_reason_fields": ["unavailable_reason"] if i == 1 else [],
                "legacy_provenance_limitations": [
                    "Synthetic archival declaration; authenticity unknown."
                ],
            }
            for i, candidate in enumerate(_CANDIDATES)
        },
        "metadata_fields": enabled,
        "windows": copy.deepcopy(_WINDOWS),
        "population": {
            "row_count": 18,
            "store_count": 3,
            "date_count": 18,
            "origin_count": 3,
            "date_min": "2015-05-23",
            "date_max": "2015-07-03",
        },
        "observed_key_sha256": _sha(_KEY_TEXT.encode("ascii")),
        "source_lineage_references": ["fixture:daily-source", "fixture:store-source"],
        "observed_key_lineage_reference": "fixture:independently-declared-roster",
        "preparation": {
            "execution_id": "fixture-execution-01",
            "reference": "fixture:preparation",
            "code_revision": "a" * 40,
            "lock_sha256": "b" * 64,
            "environment_references": ["fixture:python314-locked"],
            "custodian_label": "untrusted synthetic label",
            "authorization_reference": "fixture:untrusted-label-not-approval",
        },
        "availability_claims": {
            field: {
                "original_source_identity": "fixture:store-source"
                if field in {"StoreType", "Assortment"}
                else "fixture:daily-source",
                "level": "observed_retrospective",
                "assumption_or_evidence_reference": "fixture:claim",
                "permitted_interpretation": "retrospective_conditional_grouping",
            }
            for field in enabled
        },
    }
    return Fixture(frames, archives, manifest)


def _binding(result: inputs.ScenarioInputVerification) -> ScenarioInputBinding:
    names = {field.name for field in fields(ScenarioInputBinding)} - {"reference", "permitted_uses"}
    return ScenarioInputBinding(
        reference="external:untrusted-label",
        permitted_uses=("synthetic_fixture_verification",),
        **{name: getattr(result, name) for name in names},
    )


def test_valid_snapshot_sparse_labels_reasons_hashes_and_public_compatibility() -> None:
    fixture = _fixture()
    files, receipt = fixture.snapshot()
    result = verify_trusted_scenario_fixture_snapshot(files, receipt)
    assert (result.row_count, result.store_count, result.date_count, result.origin_count) == (
        18,
        3,
        18,
        3,
    )
    assert result.manifest_sha256 == _sha(files["manifest.json"])
    assert result.payload_sha256 == _sha(_json(fixture.manifest["files"]))
    assert result.observed_key_sha256 == _sha(_KEY_TEXT.encode("ascii"))
    assert _sha(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert result.candidate_ids == phase7.CANDIDATE_IDS == _CANDIDATES
    assert result.candidates[0].configuration_sha256 is None
    assert result.candidates[1].original_reason_fields == ("unavailable_reason",)
    assert result.candidates[1].unavailable_reason_counts == (("synthetic_fit_failure", 3),)
    assert result.candidates[2].configuration_sha256 == _sha(files["M/lightgbm_configuration.json"])
    assert all(claim.status == "unverified_declaration" for claim in result.availability_claims)
    assert not any(field.name in {"approved", "authorized"} for field in fields(result))
    records = {candidate: fixture.frames[f"M/{candidate}.parquet"] for candidate in _CANDIDATES}
    population = scenarios.build_scenario_population(records)
    assert len(population) == 18 and population["label_eligible"].sum() == 9
    assert population["three_way_common_eligible"].sum() == 6
    # L2 runs explicitly here for compatibility; the verifier never calls it.
    summary = scenarios.summarize_scenario_population(
        population, scenario_membership=fixture.frames["C/membership.parquet"]
    )
    assert summary.enabled_scenarios == inputs.METADATA_FIELDS
    assert scenarios.serialize_scenario_fixture(summary)
    validate_scenario_input_binding(_binding(result), result)


def test_no_metadata_inventory_and_immutable_results() -> None:
    fixture = _fixture(metadata=False)
    files, receipt = fixture.snapshot()
    assert len(files) == 9
    result = verify_trusted_scenario_fixture_snapshot(files, receipt)
    assert result.enabled_scenario_dimensions == () and result.availability_claims == ()
    with pytest.raises(FrozenInstanceError):
        result.row_count = 0
    with pytest.raises(FrozenInstanceError):
        result.candidates[0].candidate_id = "other"


@pytest.mark.parametrize("mode", ["absent", "fit_reason", "precedence"])
def test_optional_original_reasons_and_fallback(mode: str) -> None:
    fixture = _fixture()
    candidate = _CANDIDATES[1]
    frame = fixture.frames[f"M/{candidate}.parquet"]
    if mode == "absent":
        frame.drop(columns="unavailable_reason", inplace=True)
        fixture.manifest["candidates"][candidate]["original_reason_fields"] = []
        expected = "not_recorded_in_original_forecast_artifact"
    else:
        frame["fit_failure_reason"] = "secondary_reason"
        if mode == "fit_reason":
            frame["unavailable_reason"] = None
        fixture.manifest["candidates"][candidate]["original_reason_fields"] += [
            "fit_failure_reason"
        ]
        expected = "secondary_reason" if mode == "fit_reason" else "synthetic_fit_failure"
    result = verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())
    assert result.candidates[1].unavailable_reason_counts == ((expected, 3),)


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate",
        "missing",
        "shared_omission",
        "wrong_raw",
        "invalid_available",
        "invalid_eligible",
        "invalid_mask_type",
        "conflicting_sales",
        "conflicting_open",
        "unapproved_origin",
        "protected_date",
        "timezone",
        "nonmidnight",
        "horizon",
        "window",
        "negative_raw",
        "invalid_reason",
        "extra_column",
        "wrong_store_type",
    ],
)
def test_invalid_candidate_evidence(mode: str) -> None:
    fixture = _fixture()
    path = f"M/{_CANDIDATES[0]}.parquet"
    frame = fixture.frames[path]
    if mode == "duplicate":
        fixture.frames[path] = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif mode == "missing":
        fixture.frames[path] = frame.iloc[1:]
    elif mode == "shared_omission":
        for candidate in _CANDIDATES:
            name = f"M/{candidate}.parquet"
            fixture.frames[name] = fixture.frames[name].iloc[1:]
    elif mode == "wrong_raw":
        frame.rename(columns={_RAW[0]: "operational_forecast"}, inplace=True)
    elif mode == "invalid_available":
        frame.loc[0, "forecast_available"] = False
    elif mode == "invalid_eligible":
        frame.loc[0, "primary_evaluation_eligible"] = False
    elif mode == "invalid_mask_type":
        frame["forecast_available"] = 2
    elif mode == "conflicting_sales":
        frame.loc[0, "actual_sales"] = 101.0
    elif mode == "conflicting_open":
        frame.loc[2, "source_open"] = 1.0
        frame.loc[2, "primary_evaluation_eligible"] = True
    elif mode == "unapproved_origin":
        frame.loc[0, "forecast_origin"] = pd.Timestamp("2015-05-21")
    elif mode == "protected_date":
        frame.loc[0, "Date"] = pd.Timestamp("2015-07-04")
    elif mode == "timezone":
        frame["Date"] = frame["Date"].dt.tz_localize("UTC")
    elif mode == "nonmidnight":
        frame.loc[0, "Date"] += pd.Timedelta(hours=1)
    elif mode == "horizon":
        frame.loc[0, "horizon"] = 15
    elif mode == "window":
        frame.loc[0, "validation_window"] = "other"
    elif mode == "negative_raw":
        frame.loc[0, _RAW[0]] = -1.0
    elif mode == "invalid_reason":
        frame.loc[0, _RAW[0]] = float("nan")
        frame.loc[0, "forecast_available"] = False
        frame.loc[0, "primary_evaluation_eligible"] = False
        frame["unavailable_reason"] = ""
        fixture.manifest["candidates"][_CANDIDATES[0]]["original_reason_fields"] = [
            "unavailable_reason"
        ]
    elif mode == "extra_column":
        frame["Customers"] = 100
    else:
        frame["Store"] = frame["Store"].astype("float64")
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())


@pytest.mark.parametrize("candidate", _CANDIDATES)
@pytest.mark.parametrize("horizon", [65537, -65535, 32769, 0, 15])
def test_original_candidate_horizon_range_is_checked_before_integer_narrowing(
    candidate: str, horizon: int
) -> None:
    fixture = _fixture()
    name = f"M/{candidate}.parquet"
    fixture.frames[name].loc[0, "horizon"] = horizon
    before = {path: frame.copy(deep=True) for path, frame in fixture.frames.items()}
    files, receipt = fixture.snapshot()

    # The fixture helper reseals the complete synthetic inventory, manifest, and receipt.
    manifest = json.loads(files["manifest.json"])
    assert manifest["files"][name]["sha256"] == _sha(files[name])
    assert manifest["payload_sha256"] == _sha(_json(manifest["files"]))
    assert json.loads(receipt)["manifest_sha256"] == _sha(files["manifest.json"])
    with pytest.raises(ScenarioInputError, match="Original candidate horizons"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)

    for path, frame in fixture.frames.items():
        pd.testing.assert_frame_equal(frame, before[path])


@pytest.mark.parametrize("horizon", [1, 14])
def test_original_candidate_horizon_valid_range_boundaries_are_accepted(horizon: int) -> None:
    fixture = _fixture()
    frame = fixture.frames[f"M/{_CANDIDATES[0]}.parquet"]
    row = frame.loc[frame["horizon"].eq(horizon)].iloc[0]
    assert (row["Date"] - row["forecast_origin"]).days == horizon

    result = verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())

    assert result.row_count == 18


def test_nullable_original_candidate_horizon_is_rejected_before_pandas_conversion() -> None:
    fixture = _fixture()
    frame = fixture.frames[f"M/{_CANDIDATES[0]}.parquet"]
    frame["horizon"] = pd.array(frame["horizon"], dtype="Int64")
    frame.loc[0, "horizon"] = pd.NA
    files, receipt = fixture.snapshot()
    assert json.loads(files["manifest.json"])["field_schemas"][f"M/{_CANDIDATES[0]}.parquet"][
        3
    ] == {"name": "horizon", "type": "int64"}

    with pytest.raises(ScenarioInputError, match="Original candidate horizons"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


def test_noninteger_original_candidate_horizon_physical_type_is_rejected() -> None:
    fixture = _fixture()
    name = f"M/{_CANDIDATES[0]}.parquet"
    fixture.frames[name]["horizon"] = fixture.frames[name]["horizon"].astype("float64")
    files, receipt = fixture.snapshot()

    with pytest.raises(ScenarioInputError, match="Unsupported Parquet physical type"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


def test_in_range_original_candidate_horizon_must_still_match_its_target_date() -> None:
    fixture = _fixture()
    fixture.frames[f"M/{_CANDIDATES[0]}.parquet"].loc[0, "horizon"] = 2

    with pytest.raises(ScenarioInputError, match="Candidate population failed accepted Phase 7/L1"):
        verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate",
        "unsorted",
        "extra",
        "missing",
        "protected",
        "origin",
        "timezone",
        "nonmidnight",
        "column",
        "store",
    ],
)
def test_independent_roster_integrity(mode: str) -> None:
    fixture = _fixture()
    name = "M/observed_keys.parquet"
    frame = fixture.frames[name]
    if mode in {"duplicate", "extra"}:
        extra = frame.iloc[[0]].copy()
        if mode == "extra":
            extra["Store"] = 4
        fixture.frames[name] = pd.concat([frame, extra], ignore_index=True)
    elif mode == "unsorted":
        fixture.frames[name] = frame.iloc[::-1]
    elif mode == "missing":
        fixture.frames[name] = frame.iloc[1:]
    elif mode == "protected":
        frame.loc[0, "Date"] = pd.Timestamp("2015-07-04")
    elif mode == "origin":
        frame.loc[0, "forecast_origin"] = pd.Timestamp("2015-05-21")
    elif mode == "timezone":
        frame["forecast_origin"] = frame["forecast_origin"].dt.tz_localize("UTC")
    elif mode == "nonmidnight":
        frame.loc[0, "forecast_origin"] += pd.Timedelta(minutes=1)
    elif mode == "column":
        frame["Sales"] = 1.0
    else:
        frame.loc[0, "Store"] = 0
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate",
        "missing_ineligible",
        "extra",
        "binary",
        "static",
        "static_null",
        "extra_field",
        "empty_text",
        "holiday_numeric",
    ],
)
def test_metadata_integrity_including_ineligible_rows(mode: str) -> None:
    fixture = _fixture()
    name = "C/membership.parquet"
    frame = fixture.frames[name]
    if mode == "duplicate":
        fixture.frames[name] = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif mode == "missing_ineligible":
        fixture.frames[name] = frame.loc[~((frame["Store"] == 2) & (frame.index == 6))]
    elif mode == "extra":
        frame.loc[0, "Store"] = 999
    elif mode == "binary":
        frame.loc[0, "Promo"] = 2.0
    elif mode == "static":
        frame.loc[0, "StoreType"] = "b"
    elif mode == "static_null":
        frame.loc[0, "Assortment"] = None
    elif mode == "extra_field":
        frame["Open"] = 1
    elif mode == "empty_text":
        frame.loc[0, "StateHoliday"] = ""
    else:
        frame["StateHoliday"] = 1
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())


@pytest.mark.parametrize(
    "level", ["observed_retrospective", "assumed_known_at_origin", "documented_known_at_origin"]
)
def test_availability_levels_remain_unverified(level: str) -> None:
    fixture = _fixture()
    fixture.manifest["availability_claims"]["Promo"]["level"] = level
    result = verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())
    assert result.availability_claims[0].level == level
    assert result.availability_claims[0].status == "unverified_declaration"
    assert "unverified declarations" in " ".join(result.limitations)


@pytest.mark.parametrize(
    "mode", ["claim", "source", "evidence", "interpretation", "missing", "extra"]
)
def test_invalid_availability_claims(mode: str) -> None:
    fixture = _fixture()
    claim = fixture.manifest["availability_claims"]["Promo"]
    if mode == "claim":
        claim["level"] = "verified_origin_known"
    elif mode == "source":
        claim["original_source_identity"] = "unknown"
    elif mode == "evidence":
        claim["assumption_or_evidence_reference"] = ""
    elif mode == "interpretation":
        claim["permitted_interpretation"] = "causal_business_savings"
    elif mode == "missing":
        del fixture.manifest["availability_claims"]["Promo"]
    else:
        claim["approved"] = True
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())


@pytest.mark.parametrize(
    "mode",
    [
        "schema",
        "purpose",
        "kind",
        "h_enabled",
        "cutoff",
        "origin",
        "bundle",
        "candidate",
        "raw",
        "reason",
        "counts",
        "date",
        "key_hash",
        "payload_hash",
        "hash_grammar",
        "bytes",
        "schema_declaration",
        "lineage",
        "preparation",
        "extra",
    ],
)
def test_strict_manifest_semantics(mode: str) -> None:
    fixture = _fixture()
    files, _ = fixture.snapshot()
    m = fixture.manifest
    if mode == "schema":
        m["schema_version"] = True
    elif mode == "purpose":
        m["purpose"] = "cc02_development_only_sales"
    elif mode == "kind":
        m["input_kind"] = "real_evidence"
    elif mode == "h_enabled":
        m["h_enabled"] = True
    elif mode == "cutoff":
        m["development_cutoff"] = "2015-07-31"
    elif mode == "origin":
        m["windows"][0]["forecast_origin"] = "2015-07-03"
    elif mode == "bundle":
        m["bundle_id"] = "../alias"
    elif mode == "candidate":
        del m["candidates"][_CANDIDATES[2]]
    elif mode == "raw":
        m["candidates"][_CANDIDATES[0]]["raw_column"] = _RAW[1]
    elif mode == "reason":
        m["candidates"][_CANDIDATES[0]]["original_reason_fields"] = ["unknown"]
    elif mode == "counts":
        m["population"]["store_count"] = 4
    elif mode == "date":
        m["population"]["date_max"] = "2015-07-31"
    elif mode == "key_hash":
        m["observed_key_sha256"] = "0" * 64
    elif mode == "payload_hash":
        m["payload_sha256"] = "0" * 64
    elif mode == "hash_grammar":
        m["files"]["M/observed_keys.parquet"]["sha256"] = "A" * 64
    elif mode == "bytes":
        m["files"]["M/observed_keys.parquet"]["bytes"] += 1
    elif mode == "schema_declaration":
        m["field_schemas"]["M/observed_keys.parquet"][0]["type"] = "double"
    elif mode == "lineage":
        m["source_lineage_references"] = []
    elif mode == "preparation":
        m["preparation"]["lock_sha256"] = "not-a-hash"
    else:
        m["authorized"] = True
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(*_reseal(files, m))


@pytest.mark.parametrize(
    "name",
    [
        "../manifest.json",
        "/absolute.json",
        "C:/absolute.json",
        "M\\observed_keys.parquet",
        "M/../manifest.json",
        "extra.json",
        "M/unknown.parquet",
        "M/Observed_keys.parquet",
    ],
)
def test_exact_logical_inventory_rejects_paths_and_unexpected_files(name: str) -> None:
    fixture = _fixture(metadata=False)
    files, receipt = fixture.snapshot()
    files[name] = b"{}"
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "corruption",
        "conflicting_manifest_inventory",
        "optional_membership_present",
        "required_membership_absent",
    ],
)
def test_inventory_and_hash_mismatches(mode: str) -> None:
    fixture = _fixture(metadata=mode != "optional_membership_present")
    files, receipt = fixture.snapshot()
    if mode == "missing":
        del files[f"M/original_manifests/{_CANDIDATES[0]}.json"]
    elif mode == "corruption":
        files["M/lightgbm_configuration.json"] = b"{}"
    elif mode == "conflicting_manifest_inventory":
        del fixture.manifest["files"]["M/observed_keys.parquet"]
        files, receipt = _reseal(files, fixture.manifest)
    elif mode == "required_membership_absent":
        del files["C/membership.parquet"]
    else:
        files["C/membership.parquet"] = b"extra"
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize("target", ["manifest", "receipt", "archive", "configuration"])
@pytest.mark.parametrize(
    "bad",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'{"x":1e999}',
        b"\xff",
        b"[]",
    ],
)
def test_strict_json_all_supplied_json(target: str, bad: bytes) -> None:
    fixture = _fixture()
    if target in {"archive", "configuration"}:
        path = (
            f"M/original_manifests/{_CANDIDATES[0]}.json"
            if target == "archive"
            else "M/lightgbm_configuration.json"
        )
        fixture.archives[path] = bad
    files, receipt = fixture.snapshot()
    if target == "manifest":
        files["manifest.json"] = bad
    elif target == "receipt":
        receipt = bad
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize(
    "field",
    [
        "execution_id",
        "bundle_id",
        "purpose",
        "code_revision",
        "lock_sha256",
        "source_lineage_references",
        "manifest_sha256",
        "payload_sha256",
        "environment_references",
        "custodian_label",
        "reference",
        "authorization_reference",
        "unexpected",
    ],
)
def test_receipt_identity_mismatches(field: str) -> None:
    files, receipt = _fixture().snapshot()
    value = json.loads(receipt)
    value[field] = "mismatched-label"
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, _json(value))


@pytest.mark.parametrize(
    "field", [field.name for field in fields(ScenarioInputBinding) if field.name != "reference"]
)
def test_binding_identity_and_use_mismatches(field: str) -> None:
    result = verify_trusted_scenario_fixture_snapshot(*_fixture().snapshot())
    binding = _binding(result)
    value = ("real_l4_execution",) if field == "permitted_uses" else "mismatch"
    with pytest.raises(ScenarioInputError):
        validate_scenario_input_binding(replace(binding, **{field: value}), result)


def test_missing_binding_empty_reference_duplicate_or_empty_uses() -> None:
    result = verify_trusted_scenario_fixture_snapshot(*_fixture().snapshot())
    binding = _binding(result)
    for invalid in (
        None,
        replace(binding, reference=""),
        replace(binding, permitted_uses=()),
        replace(binding, permitted_uses=(inputs.PERMITTED_USES[0],) * 2),
    ):
        with pytest.raises(ScenarioInputError):
            validate_scenario_input_binding(invalid, result)


@pytest.mark.parametrize("target", ["manifest", "receipt", "parquet", "archive", "total", "files"])
def test_byte_limits_precede_any_json_or_parquet_decode(
    target: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    files, receipt = _fixture().snapshot()

    def forbidden(*args, **kwargs):
        pytest.fail("Input-size checks must precede parsing")

    if target == "manifest":
        monkeypatch.setattr(inputs, "MAX_MANIFEST_BYTES", len(files["manifest.json"]) - 1)
    elif target == "receipt":
        monkeypatch.setattr(inputs, "MAX_RECEIPT_BYTES", len(receipt) - 1)
    elif target == "parquet":
        monkeypatch.setattr(inputs, "MAX_PARQUET_BYTES", 1)
    elif target == "archive":
        monkeypatch.setattr(inputs, "MAX_ARCHIVE_BYTES", 1)
    elif target == "total":
        monkeypatch.setattr(
            inputs, "MAX_TOTAL_BYTES", sum(map(len, files.values())) + len(receipt) - 1
        )
    else:
        files["M/extra.parquet"] = b"extra"
    monkeypatch.setattr(inputs, "_json", forbidden)
    monkeypatch.setattr(pq, "ParquetFile", forbidden)
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize(
    "limit",
    [
        "MAX_ROWS",
        "MAX_COLUMNS",
        "MAX_ROW_GROUPS",
        "MAX_FOOTER_BYTES",
        "MAX_DECODED_BYTES",
        "MAX_TOTAL_DECODED_BYTES",
    ],
)
def test_footer_metadata_and_size_estimates_precede_materializing_any_table(
    limit: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # These prechecks exercise bounded footer estimates, not decoder allocation enforcement.
    fixture = _fixture()
    files, receipt = fixture.snapshot(row_group_size=1)
    if limit == "MAX_ROWS":
        for field in ("row_count", "store_count", "date_count", "origin_count"):
            fixture.manifest["population"][field] = 1
        files, receipt = _reseal(files, fixture.manifest)

    def forbidden(*args, **kwargs):
        pytest.fail("All Parquet metadata limits must precede table decoding")

    monkeypatch.setattr(pq.ParquetFile, "read", forbidden)
    monkeypatch.setattr(inputs, limit, 1)
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize(
    "mode", ["footer", "malformed", "string", "json_depth", "json_nodes", "json_text"]
)
def test_malformed_parquet_and_decoded_text_json_limits(mode: str) -> None:
    fixture = _fixture()
    if mode == "string":
        fixture.frames["C/membership.parquet"].loc[0, "StateHoliday"] = "x" * (
            inputs.MAX_TEXT_LENGTH + 1
        )
    elif mode.startswith("json"):
        value = "x"
        if mode == "json_depth":
            for _ in range(inputs.MAX_JSON_DEPTH + 1):
                value = [value]
        elif mode == "json_nodes":
            value = [0] * (inputs.MAX_JSON_NODES + 1)
        else:
            value = "x" * (inputs.MAX_TEXT_LENGTH + 1)
        fixture.archives[f"M/original_manifests/{_CANDIDATES[0]}.json"] = _json({"x": value})
    files, receipt = fixture.snapshot()
    if mode in {"footer", "malformed"}:
        payloads = {name: value for name, value in files.items() if name != "manifest.json"}
        payloads["M/observed_keys.parquet"] = (
            b"PAR1" + b"\xff" * 4 + b"PAR1" if mode == "footer" else b"PAR1xx\x02\0\0\0PAR1"
        )
        files, receipt = _envelope(payloads, fixture.manifest)
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


def test_input_ordering_date_units_and_no_caller_mutation() -> None:
    fixture = _fixture()
    originals = {name: frame.copy(deep=True) for name, frame in fixture.frames.items()}
    files, receipt = fixture.snapshot()
    copy_of_files = dict(files)
    first = verify_trusted_scenario_fixture_snapshot(files, receipt)
    second = verify_trusted_scenario_fixture_snapshot(dict(reversed(list(files.items()))), receipt)
    assert first == second and files == copy_of_files
    for name, frame in fixture.frames.items():
        pd.testing.assert_frame_equal(frame, originals[name])
    for name in fixture.frames.keys() - {"M/observed_keys.parquet"}:
        fixture.frames[name] = fixture.frames[name].sample(frac=1, random_state=11)
        for column in ("forecast_origin", "Date"):
            fixture.frames[name][column] = fixture.frames[name][column].astype("datetime64[us]")
    shuffled = verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())
    assert shuffled.observed_key_sha256 == first.observed_key_sha256
    assert shuffled.row_count == first.row_count


def test_requires_immutable_bytes_and_duplicate_mapping_items() -> None:
    files, receipt = _fixture().snapshot()
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(files, bytearray(receipt))
    mutable = dict(files)
    mutable["manifest.json"] = bytearray(files["manifest.json"])
    with pytest.raises(ScenarioInputError):
        verify_trusted_scenario_fixture_snapshot(mutable, receipt)

    class DuplicateMapping(Mapping):
        def __len__(self):
            return len(files)

        def __getitem__(self, key):
            return files[key]

        def __iter__(self):
            return iter(files)

        def items(self):
            return [*files.items(), ("manifest.json", files["manifest.json"])]

    with pytest.raises(ScenarioInputError, match="Duplicate"):
        verify_trusted_scenario_fixture_snapshot(DuplicateMapping(), receipt)


@pytest.mark.parametrize("invalid", ["valid", "inventory", "candidate", "receipt", "binding"])
def test_no_external_io_execution_aggregation_or_authorization(
    invalid: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    if invalid == "candidate":
        fixture.frames[f"M/{_CANDIDATES[0]}.parquet"].loc[0, "forecast_available"] = False
    files, receipt = fixture.snapshot()
    if invalid == "inventory":
        files["../forbidden.parquet"] = b"no"
        del files["M/lightgbm_configuration.json"]  # stay within count limit
    elif invalid == "receipt":
        receipt = b"{}"

    def forbidden(*args, **kwargs):
        pytest.fail("External operation or aggregation attempted")

    calls = []
    original_validator = inputs.validate_candidate_records
    original_builder = inputs.build_scenario_population

    def validator(records):
        calls.append("phase7")
        return original_validator(records)

    def builder(records):
        calls.append("l1")
        return original_builder(records)

    monkeypatch.setattr(inputs, "validate_candidate_records", validator)
    monkeypatch.setattr(inputs, "build_scenario_population", builder)
    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(io, "open", forbidden)
    for name in (
        "open",
        "read_bytes",
        "write_bytes",
        "read_text",
        "write_text",
        "resolve",
        "glob",
        "rglob",
    ):
        monkeypatch.setattr(Path, name, forbidden)
    for name in ("open", "listdir", "scandir", "getenv"):
        monkeypatch.setattr(os, name, forbidden)
    monkeypatch.setattr(pd, "read_parquet", forbidden)
    monkeypatch.setattr(pq, "read_table", forbidden)
    monkeypatch.setattr(pa, "OSFile", forbidden)
    monkeypatch.setattr(pa, "memory_map", forbidden)
    monkeypatch.setattr(acquisition, "sha256_file", forbidden)
    monkeypatch.setattr(acquisition, "acquire_official_data", forbidden)
    monkeypatch.setattr(acquisition, "acquisition_readiness", forbidden)
    monkeypatch.setattr(phase7, "verify_candidate_manifests", forbidden)
    monkeypatch.setattr(phase7, "_load_saved_forecasts", forbidden)
    monkeypatch.setattr(phase7, "run_model_selection", forbidden)
    monkeypatch.setattr(scenarios, "summarize_scenario_population", forbidden)
    monkeypatch.setattr(scenarios, "serialize_scenario_fixture", forbidden)
    monkeypatch.setattr(cc02, "load_approved_development_sales", forbidden)
    monkeypatch.setattr(cc02, "decompose_approved_development_sales", forbidden)
    monkeypatch.setattr(preparation, "_prepare_partition_from_bytes", forbidden)
    monkeypatch.setattr(custodian, "run_fixed_source_preparation_once", forbidden)
    monkeypatch.setattr(issuer.Phase13FreshFitIssuer, "issue", forbidden)
    monkeypatch.setattr(providers.SyntheticInputProvider, "read_training_inputs", forbidden)
    monkeypatch.setattr(providers.SyntheticOutcomeProvider, "read_day", forbidden)
    monkeypatch.setattr(phase7.lgb, "train", forbidden)
    monkeypatch.setattr(holt_winters.ExponentialSmoothing, "fit", forbidden)
    if invalid in {"inventory", "receipt", "candidate"}:
        with pytest.raises(ScenarioInputError):
            verify_trusted_scenario_fixture_snapshot(files, receipt)
        assert calls == (["phase7"] if invalid == "candidate" else [])
    else:
        result = verify_trusted_scenario_fixture_snapshot(files, receipt)
        if invalid == "binding":
            with pytest.raises(ScenarioInputError):
                validate_scenario_input_binding(None, result)
        else:
            validate_scenario_input_binding(_binding(result), result)
        assert calls == ["phase7", "l1"]


def test_protected_labels_never_reach_phase7_or_l1(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _fixture()
    fixture.frames[f"M/{_CANDIDATES[0]}.parquet"].loc[0, "Date"] = pd.Timestamp("2015-07-04")
    files, receipt = fixture.snapshot()

    def forbidden(*args, **kwargs):
        pytest.fail("Protected-date labels reached an evaluation layer")

    monkeypatch.setattr(inputs, "validate_candidate_records", forbidden)
    monkeypatch.setattr(inputs, "build_scenario_population", forbidden)
    with pytest.raises(ScenarioInputError, match="unapproved/protected"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize(
    "mode", ["candidate", "command", "cutoff", "holdout", "configuration_hash"]
)
def test_archival_identity_mismatch(mode: str) -> None:
    fixture = _fixture()
    name = f"M/original_manifests/{_CANDIDATES[2]}.json"
    original = json.loads(fixture.archives[name])
    field, value = {
        "candidate": ("candidate_id", "other"),
        "command": ("command", "rossmann-seasonal-naive"),
        "cutoff": ("development_only_through", "2015-07-31"),
        "holdout": ("final_holdout_forecast_or_evaluation", True),
        "configuration_hash": ("configuration_sha256", "0" * 64),
    }[mode]
    original[field] = value
    fixture.archives[name] = _json(original)
    with pytest.raises(ScenarioInputError, match="Original"):
        verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())


def test_correct_length_but_wrong_payload_hash() -> None:
    fixture = _fixture()
    files, receipt = fixture.snapshot()
    name = "M/lightgbm_configuration.json"
    files[name] = files[name].replace(b"inert", b"fake") + b" "  # identical length
    assert len(files[name]) == fixture.manifest["files"][name]["bytes"]
    with pytest.raises(ScenarioInputError, match="SHA-256"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


def test_aggregate_footer_estimate_precedes_all_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files, receipt = _fixture().snapshot()
    sizes = []
    for name, content in files.items():
        if name.endswith(".parquet"):
            metadata = pq.ParquetFile(pa.BufferReader(content)).metadata
            sizes.append(
                sum(metadata.row_group(i).total_byte_size for i in range(metadata.num_row_groups))
            )
    monkeypatch.setattr(inputs, "MAX_TOTAL_DECODED_BYTES", sum(sizes) - 1)

    def forbidden(*args, **kwargs):
        pytest.fail("Aggregate metadata budget must precede decoding")

    monkeypatch.setattr(pq.ParquetFile, "read", forbidden)
    with pytest.raises(ScenarioInputError, match="Total decoded"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


def test_parquet_external_column_paths_rejected_before_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    files, _ = fixture.snapshot()
    name = "M/observed_keys.parquet"
    original = pq.ParquetFile(pa.BufferReader(files[name]))
    metadata = original.metadata
    metadata.set_file_path("../untrusted-external.parquet")
    stream = io.BytesIO()
    pq.write_metadata(original.schema_arrow, stream, metadata_collector=[metadata])
    payloads = {name: value for name, value in files.items() if name != "manifest.json"}
    payloads[name] = stream.getvalue()
    files, receipt = _envelope(payloads, fixture.manifest)

    def forbidden(*args, **kwargs):
        pytest.fail("External column reference reached a table reader")

    monkeypatch.setattr(pq.ParquetFile, "read", forbidden)
    with pytest.raises(ScenarioInputError, match="External Parquet"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


def test_generic_decoder_api_is_absent() -> None:
    assert not hasattr(inputs, "verify_scenario_bundle_snapshot")
    assert callable(inputs.verify_trusted_scenario_fixture_snapshot)


@pytest.mark.parametrize("metadata", [False, True])
def test_success_always_carries_immutable_fixture_trust_and_memory_limitations(
    metadata: bool,
) -> None:
    result = verify_trusted_scenario_fixture_snapshot(*_fixture(metadata=metadata).snapshot())
    assert isinstance(result.limitations, tuple)
    limitations = " ".join(result.limitations)
    for required in (
        "Fixture-only conformance",
        "Origin and custody are unauthenticated",
        "Historical availability remains unverified",
        "Real observed-roster independence/completeness is unverified",
        "No permission to access real sources",
        "No hard peak-memory guarantee",
        "after materialization",
        "Python, Arrow, pandas and native temporaries",
        "exhaust memory or terminate the process",
        "No approval to execute L4",
        "UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE CONTRACT APPROVED",
    ):
        assert required in limitations
    assert not {field.name for field in fields(result)} & {
        "trusted",
        "authorized",
        "approved",
        "production_safe",
    }
    with pytest.raises(FrozenInstanceError):
        result.limitations = ()


_NONFIXTURE_USES = (
    "real_rossmann_preparation",
    "production_development_data_loading",
    "actual_forecast_evaluation_execution",
    "phase13_protected_evaluation",
    "real_source_custody",
    "approval_issuance",
    "public_release",
    "publication",
)


@pytest.mark.parametrize("purpose", _NONFIXTURE_USES)
def test_nonfixture_manifest_purpose_is_rejected_before_decode(
    purpose: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture()
    files, _ = fixture.snapshot()
    fixture.manifest["purpose"] = purpose
    files, receipt = _reseal(files, fixture.manifest)

    def forbidden(*args, **kwargs):
        pytest.fail("A nonfixture purpose reached the Parquet decoder")

    monkeypatch.setattr(pq, "ParquetFile", forbidden)
    with pytest.raises(ScenarioInputError, match="synthetic fixture purpose"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)


@pytest.mark.parametrize("use", _NONFIXTURE_USES)
def test_binding_never_permits_real_operations_even_with_matching_fabricated_purpose(
    use: str,
) -> None:
    result = verify_trusted_scenario_fixture_snapshot(*_fixture(metadata=False).snapshot())
    binding = _binding(result)
    for uses in ((use,), ("synthetic_fixture_verification", use)):
        with pytest.raises(ScenarioInputError, match="permitted uses"):
            validate_scenario_input_binding(replace(binding, permitted_uses=uses), result)
    # Equality of two caller-fabricated records must not admit a real-data purpose.
    with pytest.raises(ScenarioInputError, match="synthetic fixture bindings"):
        validate_scenario_input_binding(replace(binding, purpose=use), replace(result, purpose=use))


@pytest.mark.parametrize("use", inputs.PERMITTED_USES)
def test_synthetic_binding_consistency_never_authenticates_fabricated_provenance(
    use: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture()
    fixture.manifest["preparation"].update(
        custodian_label="fabricated trusted custodian",
        authorization_reference="fabricated:owner-approved-real-data",
        reference="fabricated:real-source-custody",
    )
    # Neither a tempting reference nor an environment assertion proves synthetic origin.
    monkeypatch.setenv("WP1_INPUT_TRUSTED", "true")
    result = verify_trusted_scenario_fixture_snapshot(*fixture.snapshot())
    binding = replace(
        _binding(result), reference="fabricated:production-approval", permitted_uses=(use,)
    )
    assert validate_scenario_input_binding(binding, result) is None
    assert result.preparation_reference == "fabricated:real-source-custody"
    assert "unauthenticated" in " ".join(result.limitations)
    assert "No permission to access real sources" in " ".join(result.limitations)
    assert "No approval to execute L4" in " ".join(result.limitations)


def test_fixture_decoder_has_no_tracked_production_or_other_test_callers() -> None:
    root = Path(__file__).resolve().parents[1]
    # Query tracked code/config only; do not walk ignored data or artifact directories.
    tracked = (
        subprocess.run(
            ["git", "ls-files", "-z", "--", "*.py", "*.toml"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .split("\0")
    )
    allowed = {
        "src/rossmann_forecasting/data/wp1_inputs.py",
        "tests/test_wp1_inputs.py",
    }
    for name in filter(None, tracked):
        if name not in allowed:
            content = (root / name).read_text(encoding="utf-8")
            assert not any(
                marker in content
                for marker in (
                    "wp1_inputs",
                    "verify_scenario_bundle_snapshot",
                    "verify_trusted_scenario_fixture_snapshot",
                )
            ), f"Fixture decoder escaped into tracked code/config: {name}"


def _zero_fixture_row_group_total(content: bytes) -> bytes:
    """Mutate only this test generator's single-row-group compact-Thrift total.

    This exact marker replacement is not a general format parser or a security control.
    Column/page bytes stay untouched; the reader sees a forged zero row-group estimate.
    """
    metadata = pq.ParquetFile(pa.BufferReader(content)).metadata
    assert metadata.num_row_groups == 1
    value = metadata.row_group(0).total_byte_size * 2  # positive compact-Thrift i64 zigzag
    encoded = bytearray()
    while value > 127:
        encoded.append((value & 127) | 128)
        value >>= 7
    encoded.append(value)
    footer_start = len(content) - 8 - int.from_bytes(content[-8:-4], "little")
    footer = content[footer_start:-8]
    # RowGroup field 2 (i64 total_byte_size) followed by field 3 (i64 num_rows).
    marker = b"\x16" + bytes(encoded) + b"\x16"
    assert footer.count(marker) == 1
    footer = footer.replace(marker, b"\x16\x00\x16", 1)
    return content[:footer_start] + footer + len(footer).to_bytes(4, "little") + b"PAR1"


@pytest.mark.parametrize("case", ["honest_dictionary_expansion", "forged_low_footer"])
def test_controlled_memory_expansion_rejects_output_after_allocation(
    case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Bounded reconstructions of S7's two mechanisms, not allocation-prevention tests.
    # At most 20,000 rows and about 34 MiB of logical Arrow output; no hostile fuzzing.
    fixture = _fixture(metadata=False)
    name = f"M/{_CANDIDATES[2]}.parquet"  # first table in deterministic decode order
    count, width = (20_000, 1024) if case == "honest_dictionary_expansion" else (1024, 32_768)
    frame = fixture.frames[name].iloc[[0] * count].reset_index(drop=True)
    frame["Store"] = range(1, count + 1)
    frame["horizon"] = frame["horizon"].astype("int8")
    frame["unavailable_reason"] = "x" * width
    fixture.manifest["candidates"][_CANDIDATES[2]]["original_reason_fields"] = [
        "unavailable_reason"
    ]
    table = pa.Table.from_pandas(frame, preserve_index=False)
    schema = pa.schema(
        [
            pa.field(
                field.name, pa.string() if pa.types.is_large_string(field.type) else field.type
            )
            for field in table.schema
        ]
    )
    table = table.cast(schema)
    stream = pa.BufferOutputStream()
    pq.write_table(
        table,
        stream,
        use_dictionary=True,
        compression="snappy" if case == "honest_dictionary_expansion" else "zstd",
    )
    content = stream.getvalue().to_pybytes()
    del table, frame
    if case == "forged_low_footer":
        content = _zero_fixture_row_group_total(content)
    parquet = pq.ParquetFile(pa.BufferReader(content))
    footer_estimate = parquet.metadata.row_group(0).total_byte_size
    assert len(content) < 256 * 1024 < inputs.MAX_PARQUET_BYTES
    assert 0 <= footer_estimate < inputs.MAX_DECODED_BYTES
    if case == "forged_low_footer":
        assert footer_estimate == 0
    files, _ = fixture.snapshot()
    payloads = {key: value for key, value in files.items() if key != "manifest.json"}
    payloads[name] = content
    fixture.manifest["field_schemas"][name] = [
        {"name": field.name, "type": str(field.type)} for field in parquet.schema_arrow
    ]
    files, receipt = _envelope(payloads, fixture.manifest)
    materialized = []
    original_read = pq.ParquetFile.read

    def record_materialization(reader, *args, **kwargs):
        decoded = original_read(reader, *args, **kwargs)
        materialized.append(decoded.nbytes)
        return decoded

    def forbidden(*args, **kwargs):
        pytest.fail("Oversized output reached string conversion or scientific validation")

    monkeypatch.setattr(pq.ParquetFile, "read", record_materialization)
    monkeypatch.setattr(inputs.pc, "utf8_length", forbidden)
    monkeypatch.setattr(inputs, "validate_candidate_records", forbidden)
    monkeypatch.setattr(inputs, "build_scenario_population", forbidden)
    with pytest.raises(ScenarioInputError, match="Decoded Arrow byte limit exceeded"):
        verify_trusted_scenario_fixture_snapshot(files, receipt)
    assert len(materialized) == 1
    # This explicitly proves allocation already happened before rejection.
    assert inputs.MAX_DECODED_BYTES < materialized[0] <= 36 * 1024 * 1024
