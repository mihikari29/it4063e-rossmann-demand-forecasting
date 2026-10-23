"""Focused offline integrity and semantic tests for the synthetic public-demo bundle."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import socket
import subprocess
import sys
from datetime import date
from pathlib import Path
from shutil import copyfile

import pytest

from rossmann_forecasting.app import demo_bundle as demo


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _release_bytes() -> tuple[bytes, bytes]:
    return demo.generate_release_bytes(Path.cwd())


@pytest.fixture(scope="module")
def _release_payload() -> tuple[bytes, bytes]:
    return _release_bytes()


def _decode(content: bytes) -> object:
    return json.loads(content)


def _reseal(bundle: dict, manifest_bytes: bytes) -> tuple[bytes, bytes]:
    bundle_bytes = _canonical(bundle)
    manifest = _decode(manifest_bytes)
    manifest["files"][demo.BUNDLE_FILENAME] = {
        "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "byte_count": len(bundle_bytes),
    }
    return bundle_bytes, _canonical(manifest)


def _reseal_manifest(manifest: dict) -> bytes:
    return _canonical(manifest)


def _create_cli_repository(root: Path) -> None:
    """Create a minimal isolated checkout for actual CLI path-boundary tests."""
    source_root = Path(__file__).resolve().parents[1]
    for relative in (
        ".gitignore",
        "pyproject.toml",
        "uv.lock",
        "scripts/build_public_demo_bundle.py",
        "src/rossmann_forecasting/__init__.py",
        "src/rossmann_forecasting/app/demo_bundle.py",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source_root / relative, destination)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)


def _add_manifest_inputs(root: Path) -> None:
    """Supply the required tracked build identities to a temporary repository fixture."""
    source_root = Path(__file__).resolve().parents[1]
    for relative in ("pyproject.toml", "uv.lock", "scripts/build_public_demo_bundle.py"):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source_root / relative, destination)


def _make_junction(link: Path, target: Path) -> None:
    """Create a disposable Windows directory junction without changing machine settings."""
    if os.name != "nt":
        pytest.skip("Windows directory junctions are only available on Windows.")
    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not create a controlled Windows junction: {result.stderr.strip()}")
    assert link.is_junction()


def test_release_bytes_are_deterministic_and_manifest_records_code_environment() -> None:
    root = Path.cwd()
    first = demo.generate_release_bytes(root)
    second = demo.generate_release_bytes(root)

    assert first == second
    report = demo.verify_release_bytes(
        *first,
        deterministic_regeneration=True,
        repository_root=root,
    )
    manifest = _decode(first[1])
    assert report.bundle_ready is True
    assert report.release_id == "rossmann-course-demo-synthetic-v1"
    assert report.evidence_kind == "controlled_synthetic_demo"
    assert manifest["seed"] == 4063
    assert manifest["generator"]["module_sha256"]
    assert manifest["environment"]["lock_sha256"]
    assert manifest["files"][demo.BUNDLE_FILENAME]["sha256"] == report.bundle_sha256
    assert report.manifest_sha256 == hashlib.sha256(first[1]).hexdigest()


def test_fixed_schema_population_and_representative_history_forecast_pairs() -> None:
    bundle = demo.create_demo_bundle()

    assert bundle["schema_version"] == "1.0.0"
    assert bundle["release_id"] == "rossmann-course-demo-synthetic-v1"
    assert bundle["evidence_kind"] == "controlled_synthetic_demo"
    assert bundle["populations"]["store_ids"] == [101, 202, 303]
    assert bundle["populations"]["forecast_origins"] == [
        "2015-05-22",
        "2015-06-05",
        "2015-06-19",
    ]
    assert bundle["populations"]["horizons"] == list(range(1, 15))
    assert len(bundle["history_rows"]) == 165
    assert len(bundle["forecast_rows"]) == 3 * 3 * 14
    history = {(row["store_id"], row["date"]): row for row in bundle["history_rows"]}
    assert any((row["store_id"], row["date"]) in history for row in bundle["forecast_rows"])
    assert all(
        date.fromisoformat(row["date"]) <= date(2015, 7, 3) for row in bundle["history_rows"]
    )
    assert all(
        date.fromisoformat(row["date"]) <= date(2015, 7, 3) for row in bundle["forecast_rows"]
    )
    assert bundle["query_allowlist"] == demo._expected_query_allowlist()


def test_catalog_is_populated_and_query_allowlist_keeps_readiness_health_separate() -> None:
    catalog = demo.create_demo_bundle()["catalog"]
    assert catalog["scenario_catalog_state"] == "available"
    assert catalog["inventory_case_state"] == "available"
    assert len(catalog["scenario_catalog"]) == 2
    assert {item["view_id"] for item in catalog["resource_readiness"]} == {
        "catalog",
        "sales_history",
        "forecast_issuance",
        "forecast_uncertainty",
        "model_comparison",
        "inventory_comparison",
    }
    assert catalog["health_route_semantics"] == ("process_health_is_not_bundle_or_view_readiness")
    queries = demo.create_demo_bundle()["query_allowlist"]
    assert queries["sales_history"] == {
        "store_ids": [101, 202, 303],
        "minimum_date": "2015-05-09",
        "maximum_date": "2015-07-03",
        "maximum_calendar_days": 56,
    }
    assert queries["forecast_issuance"]["origins"] == [
        "2015-05-22",
        "2015-06-05",
        "2015-06-19",
    ]
    assert queries["forecast_uncertainty"]["fit_pairings"] == [
        {"fit_id": "demo_fit_a", "forecast_origin": "2015-06-05"},
        {"fit_id": "demo_fit_b", "forecast_origin": "2015-06-19"},
    ]
    assert queries["inventory_comparison"]["case_ids"] == [
        "synthetic_demo_reference_20150605",
        "synthetic_demo_adverse_20150605",
    ]


def test_history_arithmetic_sparse_zero_and_null_semantics_are_explicit() -> None:
    bundle = demo.create_demo_bundle()
    rows = {(row["store_id"], row["date"]): row for row in bundle["history_rows"]}
    first = rows[(101, "2015-05-09")]
    digest = hashlib.sha256(b"4063:history:101:0").digest()
    stable = (int.from_bytes(digest[:4], "big") % 2001) / 1000.0 - 1.0
    expected = 8200 + 101 * 17 + 5 * 240 + round(stable * 80)
    assert first["sales_value"] == expected
    assert rows[(101, "2015-05-23")]["observation_state"] == "zero_sales"
    assert rows[(202, "2015-06-01")]["sales_value"] is None
    assert (101, "2015-05-22") not in rows  # sparse date, not a zero row
    assert rows[(303, "2015-06-13")]["synthetic_open"] is None


def test_forecast_raw_and_operational_paths_keep_eligibility_separate() -> None:
    bundle = demo.create_demo_bundle()
    rows = {
        (row["store_id"], row["forecast_origin"], row["horizon"]): row
        for row in bundle["forecast_rows"]
    }
    closed = rows[(101, "2015-05-22", 2)]  # Sunday
    unknown = rows[(303, "2015-06-19", 4)]
    assert closed["raw_forecast_available"] is True
    assert closed["raw_forecast_value"] > 0
    assert closed["synthetic_open_eligibility"] == "known_closed"
    assert closed["operational_forecast_value"] == 0
    assert closed["operational_forecast_available"] is True
    assert unknown["raw_forecast_available"] is True
    assert unknown["synthetic_open_eligibility"] == "unknown"
    assert unknown["operational_forecast_value"] is None
    assert unknown["operational_forecast_available"] is False


def test_uncertainty_pairings_keep_unavailable_points_and_prefixes_null() -> None:
    bundle = demo.create_demo_bundle()
    assert {(item["fit_id"], item["forecast_origin"]) for item in bundle["uncertainty_views"]} == {
        ("demo_fit_a", "2015-06-05"),
        ("demo_fit_b", "2015-06-19"),
    }
    view = next(
        item
        for item in bundle["uncertainty_views"]
        if item["store_id"] == 303 and item["fit_id"] == "demo_fit_b"
    )
    operational_h4 = next(
        item
        for item in view["daily_intervals"]
        if item["horizon"] == 4 and item["interval_kind"] == "operational"
    )
    assert operational_h4["available"] is False
    assert operational_h4["point_forecast"] is None
    assert operational_h4["lower"] is None
    assert all(
        item["issued_prefix_complete"] is False
        for item in view["cumulative_uncertainty"]
        if item["prefix_days"] >= 4
    )
    assert all(
        item["target_value"] is None
        for item in view["cumulative_uncertainty"]
        if item["prefix_days"] >= 4
    )


def test_comparison_metrics_follow_mae_rmse_cautious_mape_and_wape_definitions() -> None:
    panel = demo.create_demo_bundle()["comparison_panel"]
    eligible = [row for row in panel["basis_rows"] if row["metric_eligible"]]
    assert eligible
    candidate = "demo_path_b"
    absolute_errors = []
    squared_errors = []
    percent_errors = []
    sales_sum = 0
    for row in eligible:
        prediction = next(
            item["forecast_value"]
            for item in row["candidate_predictions"]
            if item["candidate_id"] == candidate
        )
        actual = row["synthetic_sales_value"]
        error = abs(actual - prediction)
        absolute_errors.append(error)
        squared_errors.append(error * error)
        sales_sum += actual
        if actual > 0:
            percent_errors.append(error / actual * 100.0)
    output = [
        row
        for row in panel["rows"]
        if row["candidate_id"] == candidate and row["scope"] == "pooled"
    ]
    by_metric = {row["metric"]: row for row in output}
    assert by_metric["mae"]["value"] == pytest.approx(sum(absolute_errors) / len(eligible))
    assert by_metric["rmse"]["value"] == pytest.approx((sum(squared_errors) / len(eligible)) ** 0.5)
    assert by_metric["mape"]["value"] == pytest.approx(sum(percent_errors) / len(percent_errors))
    assert by_metric["wape"]["value"] == pytest.approx(sum(absolute_errors) / sales_sum)
    assert panel["metric_definitions"]["development_model_selection_claim"] is False
    assert all("global_lightgbm" not in row["candidate_id"] for row in output)


def test_inventory_contains_adverse_result_and_explicit_unavailable_case() -> None:
    bundle = demo.create_demo_bundle()
    reference, adverse = bundle["inventory_views"]
    assert len(reference["case_level_comparisons"]) == 10
    assert all(pair["comparable"] for pair in reference["policy_pairs"])
    positive = [
        pair["forecast_minus_baseline_cost"]
        for pair in adverse["policy_pairs"]
        if pair["forecast_minus_baseline_cost"] is not None
    ]
    assert any(value > 0 for value in positive)
    missing = next(pair for pair in adverse["policy_pairs"] if pair["store_id"] == 303)
    assert missing["comparable"] is False
    assert missing["forecast_minus_baseline_cost"] is None
    assert missing["forecast"]["target_available"] is False
    assert missing["forecast"]["simulated_holding_plus_shortfall_cost"] is None
    assert missing["forecast"]["calibration_transport_valid"] is False


def test_manifest_and_bundle_have_exactly_approved_content_files(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _add_manifest_inputs(root)
    target = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    report = demo.write_release_candidate(target, root)
    assert sorted(item.name for item in target.iterdir()) == [
        demo.BUNDLE_FILENAME,
        demo.MANIFEST_FILENAME,
    ]
    verified = demo.verify_release_directory(
        target,
        expected_manifest_sha256=report.manifest_sha256,
        deterministic_regeneration=True,
        repository_root=root,
    )
    assert verified == report
    with pytest.raises(demo.DemoBundleError, match="cannot be overwritten"):
        demo.write_release_candidate(target, root)


def test_output_destination_is_fixed_and_refuses_tracked_collisions(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    wrong = root / "outputs" / demo.RELEASE_ID
    with pytest.raises(demo.DemoBundleError, match="fixed ignored"):
        demo.write_release_candidate(wrong, root)

    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    tracked = root / "artifacts" / "public_demo" / "tracked.txt"
    tracked.parent.mkdir(parents=True)
    tracked.write_text("tracked", encoding="utf-8")
    subprocess.run(["git", "add", "artifacts/public_demo/tracked.txt"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
    )
    target = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    with pytest.raises(demo.DemoBundleError, match="collides with tracked"):
        demo.write_release_candidate(target, root)


def test_output_path_rejects_parent_traversal_and_absolute_escape(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    for escaped in (
        root / "artifacts" / ".." / "outside" / demo.RELEASE_ID,
        tmp_path / "outside" / demo.RELEASE_ID,
    ):
        with pytest.raises(demo.DemoBundleError):
            demo.write_release_candidate(escaped, root)
    assert not (tmp_path / "outside").exists()
    assert not (root / "artifacts").exists()
    assert not target.exists()


def test_output_path_rejects_symlink_ancestor(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    try:
        (root / "artifacts").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Could not create a controlled directory symlink: {exc}")
    with pytest.raises(demo.DemoBundleError, match="alias|unsafe|contained"):
        demo.write_release_candidate(
            root / "artifacts" / "public_demo" / demo.RELEASE_ID,
            root,
        )
    assert not (outside / "public_demo").exists()


def test_output_path_rejects_junction_as_artifacts_ancestor(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    _make_junction(root / "artifacts", outside)
    with pytest.raises(demo.DemoBundleError, match="alias|unsafe|contained"):
        demo.write_release_candidate(
            root / "artifacts" / "public_demo" / demo.RELEASE_ID,
            root,
        )
    assert not (outside / "public_demo").exists()


def test_output_path_rejects_junction_below_allowed_root(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    (root / "artifacts").mkdir(parents=True)
    _make_junction(root / "artifacts" / "public_demo", outside)
    with pytest.raises(demo.DemoBundleError, match="alias|unsafe|contained"):
        demo.write_release_candidate(
            root / "artifacts" / "public_demo" / demo.RELEASE_ID,
            root,
        )
    assert not (outside / demo.RELEASE_ID).exists()


def test_output_path_rejects_junction_as_release_destination(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    target = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    outside = tmp_path / "outside-release"
    target.parent.mkdir(parents=True)
    _make_junction(target, outside)
    with pytest.raises(demo.DemoBundleError, match="alias|unsafe|contained"):
        demo.write_release_candidate(target, root)
    assert list(outside.iterdir()) == []


def test_directory_verifier_rejects_junction_release_alias(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _add_manifest_inputs(root)
    release = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    demo.write_release_candidate(release, root)
    alias = root / "release-alias"
    _make_junction(alias, release)
    with pytest.raises(demo.DemoBundleError, match="alias|unsafe|contained"):
        demo.verify_release_directory(alias, repository_root=root)


def test_directory_verifier_rejects_junction_ancestor(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    actual_root = tmp_path / "actual-repo"
    actual_root.mkdir()
    _add_manifest_inputs(actual_root)
    release = actual_root / "artifacts" / "public_demo" / demo.RELEASE_ID
    bundle_bytes, manifest_bytes = demo.generate_release_bytes(actual_root)
    release.mkdir(parents=True)
    (release / demo.BUNDLE_FILENAME).write_bytes(bundle_bytes)
    (release / demo.MANIFEST_FILENAME).write_bytes(manifest_bytes)
    _make_junction(root / "artifacts", actual_root / "artifacts")
    with pytest.raises(demo.DemoBundleError, match="alias|unsafe|contained"):
        demo.verify_release_directory(
            root / "artifacts" / "public_demo" / demo.RELEASE_ID,
            repository_root=root,
        )


def test_actual_build_cli_rejects_artifacts_junction_before_writing(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    outside = tmp_path / "outside"
    root.mkdir()
    _create_cli_repository(root)
    _make_junction(root / "artifacts", outside)
    destination = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_public_demo_bundle.py"),
            "build",
            "--output-dir",
            str(destination),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "alias" in completed.stderr.lower() or "unsafe" in completed.stderr.lower()
    assert not (outside / "public_demo").exists()


@pytest.mark.parametrize("failure_point", ["write", "rename"])
def test_builder_failure_cleans_staging_directory(
    tmp_path: Path, monkeypatch, failure_point: str
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _add_manifest_inputs(root)
    target = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    if failure_point == "write":
        original_write_bytes = Path.write_bytes

        def fail_manifest_write(path: Path, content: bytes) -> int:
            if path.name == demo.MANIFEST_FILENAME:
                raise OSError("controlled manifest write failure")
            return original_write_bytes(path, content)

        monkeypatch.setattr(Path, "write_bytes", fail_manifest_write)
    else:
        monkeypatch.setattr(
            demo.os,
            "rename",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                OSError("controlled final rename failure")
            ),
        )
    with pytest.raises(OSError, match="controlled"):
        demo.write_release_candidate(target, root)
    assert not target.exists()
    assert not list(target.parent.glob(".public-demo-candidate-*"))


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["generator"].__setitem__("config_sha256", "0" * 64),
            "configuration",
        ),
        (lambda value: value["generator"].__setitem__("script_sha256", None), "SHA-256"),
        (
            lambda value: value["environment"].__setitem__("pyproject_sha256", None),
            "SHA-256",
        ),
        (lambda value: value["environment"].__setitem__("lock_sha256", None), "SHA-256"),
        (
            lambda value: value["generator"].__setitem__("module_sha256", "invalid"),
            "hash identity|SHA-256",
        ),
        (
            lambda value: value["generator"].__setitem__("module_sha256", "a" * 63),
            "hash identity|SHA-256",
        ),
        (
            lambda value: value["environment"]["installed_dependencies"].__setitem__("numpy", ""),
            "version",
        ),
        (
            lambda value: value["environment"]["installed_dependencies"].__setitem__("numpy", 2),
            "version",
        ),
        (
            lambda value: value["generator"].__setitem__("git_revision", "a" * 45),
            "revision",
        ),
        (
            lambda value: value["generator"].__setitem__("git_revision", "z" * 40),
            "revision",
        ),
        (
            lambda value: value["generator"].__setitem__("git_revision", "a" * 39),
            "revision",
        ),
        (
            lambda value: value["generator"].__setitem__("git_revision", 1),
            "revision",
        ),
    ],
    ids=[
        "wrong-config-digest",
        "null-script-hash",
        "null-project-hash",
        "null-lock-hash",
        "malformed-module-hash",
        "short-module-hash",
        "empty-dependency-version",
        "non-string-dependency-version",
        "45-character-revision",
        "non-hex-revision",
        "39-character-revision",
        "non-string-revision",
    ],
)
def test_plain_verifier_rejects_inconsistent_manifest_provenance(mutate, message: str) -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    manifest = _decode(manifest_bytes)
    mutate(manifest)
    with pytest.raises(demo.DemoBundleError, match=message):
        demo.verify_release_bytes(bundle_bytes, _reseal_manifest(manifest))


_REQUIRED_DEMO_DEPENDENCIES = ("fastapi", "numpy", "pandas", "pyarrow", "streamlit")
_MALFORMED_DEPENDENCY_VERSIONS = [
    pytest.param("1+.", id="empty-local-segment"),
    pytest.param("1a1b1", id="repeated-pre-release"),
    pytest.param("1+\u0130", id="unicode-casefold-latin-capital-i"),
    pytest.param("1+\u0131", id="unicode-casefold-dotless-i"),
    pytest.param("1+\u017f", id="unicode-casefold-long-s"),
    pytest.param("1+\u212a", id="unicode-casefold-kelvin-sign"),
    pytest.param("1.0.po\u017ft1", id="unicode-casefold-post-release-keyword"),
    pytest.param("1.\u0661", id="unicode-arabic-indic-release-digit"),
    pytest.param("1.0+\u00e9", id="unicode-local-letter"),
    pytest.param("1.0+ab\u0301", id="unicode-combining-mark"),
    pytest.param("\u00a01.0", id="unicode-nonbreaking-space"),
    pytest.param("1.0.p\u043est1", id="unicode-cyrillic-keyword-lookalike"),
    pytest.param("1.0+", id="empty-local-version"),
    pytest.param("1.0+abc.", id="trailing-local-separator"),
    pytest.param("1.0+..abc", id="empty-local-segment-middle"),
    pytest.param("1.0rc1rc2", id="repeated-pre-release-clause"),
    pytest.param("", id="empty"),
    pytest.param(" ", id="whitespace"),
    pytest.param("1.0.", id="trailing-release-separator"),
    pytest.param("1.0_", id="trailing-underscore"),
    pytest.param("1" * (demo._MAX_DISTRIBUTION_VERSION_LENGTH + 1), id="overlong"),
    pytest.param(True, id="boolean"),
    pytest.param(1, id="integer"),
    pytest.param(1.0, id="float"),
    pytest.param(None, id="null"),
    pytest.param([], id="array"),
    pytest.param({}, id="object"),
]
_SUPPORTED_DEPENDENCY_VERSIONS = (
    "1",
    "1.2",
    "1.2.3",
    "1.2a1",
    "1.2b2",
    "1.2rc1",
    "1.2.post1",
    "1.2.dev1",
    "1.2+abc.1",
    "2!1.0",
)


@pytest.mark.parametrize("dependency", _REQUIRED_DEMO_DEPENDENCIES)
@pytest.mark.parametrize("version", _MALFORMED_DEPENDENCY_VERSIONS)
def test_plain_verifier_rejects_malformed_dependency_version_with_matching_pin(
    _release_payload: tuple[bytes, bytes], dependency: str, version: object
) -> None:
    bundle_bytes, manifest_bytes = _release_payload
    manifest = _decode(manifest_bytes)
    manifest["environment"]["installed_dependencies"][dependency] = version
    resealed_manifest = _reseal_manifest(manifest)
    manifest_pin = hashlib.sha256(resealed_manifest).hexdigest()

    with pytest.raises(demo.DemoBundleError, match="dependency version"):
        demo.verify_release_bytes(
            bundle_bytes,
            resealed_manifest,
            expected_manifest_sha256=manifest_pin,
        )


@pytest.mark.parametrize("dependency", _REQUIRED_DEMO_DEPENDENCIES)
@pytest.mark.parametrize("version", _SUPPORTED_DEPENDENCY_VERSIONS)
def test_plain_verifier_accepts_supported_dependency_version_with_matching_pin(
    _release_payload: tuple[bytes, bytes], dependency: str, version: str
) -> None:
    bundle_bytes, manifest_bytes = _release_payload
    manifest = _decode(manifest_bytes)
    manifest["environment"]["installed_dependencies"][dependency] = version
    resealed_manifest = _reseal_manifest(manifest)
    manifest_pin = hashlib.sha256(resealed_manifest).hexdigest()

    report = demo.verify_release_bytes(
        bundle_bytes,
        resealed_manifest,
        expected_manifest_sha256=manifest_pin,
    )

    assert report.bundle_ready is True


def test_portable_valid_dependency_version_requires_exact_match_for_regeneration(
    _release_payload: tuple[bytes, bytes],
) -> None:
    bundle_bytes, manifest_bytes = _release_payload
    manifest = _decode(manifest_bytes)
    portable_version = "999999.123+course.1"
    assert portable_version != manifest["environment"]["installed_dependencies"]["numpy"]
    manifest["environment"]["installed_dependencies"]["numpy"] = portable_version
    resealed_manifest = _reseal_manifest(manifest)
    manifest_pin = hashlib.sha256(resealed_manifest).hexdigest()

    report = demo.verify_release_bytes(
        bundle_bytes,
        resealed_manifest,
        expected_manifest_sha256=manifest_pin,
    )
    assert report.bundle_ready is True

    with pytest.raises(demo.DemoBundleError, match="differs from deterministic regeneration"):
        demo.verify_release_bytes(
            bundle_bytes,
            resealed_manifest,
            expected_manifest_sha256=manifest_pin,
            deterministic_regeneration=True,
            repository_root=Path.cwd(),
        )


def test_actual_cli_rejects_unicode_casefolding_dependency_version_with_matching_pin(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkout"
    root.mkdir()
    _create_cli_repository(root)
    release = root / "artifacts" / "public_demo" / demo.RELEASE_ID
    demo.write_release_candidate(release, root)

    manifest_path = release / demo.MANIFEST_FILENAME
    manifest = _decode(manifest_path.read_bytes())
    manifest["environment"]["installed_dependencies"]["numpy"] = "1+\u212a"
    resealed_manifest = _reseal_manifest(manifest)
    manifest_pin = hashlib.sha256(resealed_manifest).hexdigest()
    manifest_path.write_bytes(resealed_manifest)

    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_public_demo_bundle.py"),
            "verify",
            "--release-dir",
            str(release),
            "--expected-manifest-sha256",
            manifest_pin,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "dependency version" in completed.stderr.lower()
    assert "bundle_ready" not in completed.stdout


@pytest.mark.parametrize(
    "byte_count",
    [326074.0, True, "326074", None, -1, 326075],
    ids=["float", "boolean", "string", "null", "negative", "wrong-integer"],
)
def test_plain_verifier_rejects_non_integer_or_incorrect_manifest_byte_count(
    byte_count,
) -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    manifest = _decode(manifest_bytes)
    manifest["files"][demo.BUNDLE_FILENAME]["byte_count"] = byte_count
    with pytest.raises(
        demo.DemoBundleError,
        match="byte count|file identity|bytes disagree",
    ):
        demo.verify_release_bytes(bundle_bytes, _reseal_manifest(manifest))


def test_plain_verifier_accepts_valid_manifest_provenance_and_integer_byte_count() -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    report = demo.verify_release_bytes(bundle_bytes, manifest_bytes)
    assert report.bundle_ready is True
    assert _decode(manifest_bytes)["files"][demo.BUNDLE_FILENAME]["byte_count"] == len(bundle_bytes)


def test_bundle_mutation_without_matching_hash_is_rejected() -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    with pytest.raises(demo.DemoBundleError):
        demo.verify_release_bytes(bundle_bytes + b" ", manifest_bytes)


def test_manifest_mutation_is_rejected_by_owner_supplied_hash_pin() -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    pin = hashlib.sha256(manifest_bytes).hexdigest()
    changed = manifest_bytes + b" "
    with pytest.raises(demo.DemoBundleError, match="out-of-band SHA-256 pin"):
        demo.verify_release_bytes(
            bundle_bytes,
            changed,
            expected_manifest_sha256=pin,
        )


def test_duplicate_json_keys_are_rejected_even_if_payload_hash_is_resealed() -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    duplicate = bundle_bytes.replace(
        b'"release_id":"rossmann-course-demo-synthetic-v1"',
        b'"release_id":"rossmann-course-demo-synthetic-v1","release_id":"rossmann-course-demo-synthetic-v1"',
        1,
    )
    manifest = _decode(manifest_bytes)
    manifest["files"][demo.BUNDLE_FILENAME] = {
        "sha256": hashlib.sha256(duplicate).hexdigest(),
        "byte_count": len(duplicate),
    }
    with pytest.raises(demo.DemoBundleError, match="Duplicate JSON"):
        demo.verify_release_bytes(duplicate, _canonical(manifest))


@pytest.mark.parametrize(
    "field,value", [("evidence_kind", "rossmann_observed"), ("schema_version", "2.0.0")]
)
def test_wrong_evidence_or_schema_identity_is_rejected(field: str, value: str) -> None:
    _, manifest_bytes = _release_bytes()
    bundle = copy.deepcopy(demo.create_demo_bundle())
    bundle[field] = value
    with pytest.raises(demo.DemoBundleError, match="fixed deterministic fixture"):
        demo.verify_release_bytes(*_reseal(bundle, manifest_bytes))


def test_unauthorized_extra_fields_and_source_references_are_rejected() -> None:
    _, manifest_bytes = _release_bytes()
    extra = copy.deepcopy(demo.create_demo_bundle())
    extra["catalog"]["source_path"] = "data/processed/model_selection"
    with pytest.raises(demo.DemoBundleError):
        demo.verify_release_bytes(*_reseal(extra, manifest_bytes))

    changed_query = copy.deepcopy(demo.create_demo_bundle())
    changed_query["query_allowlist"]["sales_history"]["store_ids"].append(404)
    with pytest.raises(demo.DemoBundleError, match="fixed deterministic fixture"):
        demo.verify_release_bytes(*_reseal(changed_query, manifest_bytes))

    bad_execution = copy.deepcopy(demo.create_demo_bundle())
    bad_execution["forecast_rows"][0]["model_execution"] = "canonical_training_run"
    with pytest.raises(demo.DemoBundleError, match="fixed deterministic fixture"):
        demo.verify_release_bytes(*_reseal(bad_execution, manifest_bytes))


def test_nonfinite_numbers_and_protected_dates_are_rejected() -> None:
    bundle_bytes, manifest_bytes = _release_bytes()
    with pytest.raises(demo.DemoBundleError):
        demo.verify_release_bytes(
            bundle_bytes.replace(b'"sales_value":0', b'"sales_value":NaN', 1), manifest_bytes
        )

    bundle = copy.deepcopy(demo.create_demo_bundle())
    bundle["history_rows"][0]["date"] = "2015-07-04"
    with pytest.raises(demo.DemoBundleError, match="fixed deterministic fixture"):
        demo.verify_release_bytes(*_reseal(bundle, manifest_bytes))


@pytest.mark.parametrize("oversized_file", ["bundle", "manifest"], ids=["bundle", "manifest"])
def test_encoded_size_limits_apply_before_json_decoding(oversized_file: str) -> None:
    bundle_bytes = b"x" * (demo.MAX_BUNDLE_BYTES + 1) if oversized_file == "bundle" else b"{}"
    manifest_bytes = b"x" * (demo.MAX_MANIFEST_BYTES + 1) if oversized_file == "manifest" else b"{}"
    with pytest.raises(demo.DemoBundleError, match="encoded-size limit"):
        demo.verify_release_bytes(bundle_bytes, manifest_bytes)


def test_no_canonical_read_training_simulation_or_network_dependencies() -> None:
    source_path = Path(demo.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    banned = (
        "rossmann_forecasting.app.artifacts",
        "rossmann_forecasting.forecasting",
        "rossmann_forecasting.inventory.simulation",
        "socket",
        "urllib",
        "requests",
        "httpx",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".") for name in imported for prefix in banned
    )
    assert not hasattr(demo, "_ArtifactReader")
    assert not hasattr(demo, "simulate_inventory")


def test_offline_generation_has_no_socket_or_publication_side_effect(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _add_manifest_inputs(root)
    target = root / "artifacts" / "public_demo" / demo.RELEASE_ID

    def forbidden_socket(*args, **kwargs):
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    report = demo.write_release_candidate(target, root)
    assert report.bundle_bytes < demo.MAX_BUNDLE_BYTES
    assert sorted(path.name for path in target.iterdir()) == [
        demo.BUNDLE_FILENAME,
        demo.MANIFEST_FILENAME,
    ]
    assert not (root / "render.yaml").exists()
    assert not (root / "streamlit_demo.py").exists()
