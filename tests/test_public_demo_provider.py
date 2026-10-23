"""Fixture-only pinned loading tests for the controlled-synthetic demo provider."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from rossmann_forecasting.app import demo_bundle
from rossmann_forecasting.app.demo_provider import (
    DemoErrorCode,
    DemoProfile,
    DemoProvider,
    DemoProviderError,
    DemoReleaseIntegrityError,
    DemoReleaseUnavailableError,
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


@pytest.fixture(scope="module")
def release_bytes() -> tuple[bytes, bytes]:
    """Generate one controlled-synthetic fixture with the checked-in Milestone A builder."""
    return demo_bundle.generate_release_bytes(Path.cwd())


def _write_release(root: Path, release_bytes: tuple[bytes, bytes]) -> tuple[Path, str]:
    bundle_bytes, manifest_bytes = release_bytes
    release_dir = root / "artifacts" / "public_demo" / demo_bundle.RELEASE_ID
    release_dir.mkdir(parents=True)
    (release_dir / demo_bundle.BUNDLE_FILENAME).write_bytes(bundle_bytes)
    (release_dir / demo_bundle.MANIFEST_FILENAME).write_bytes(manifest_bytes)
    # Derive the pin from the actual manifest bytes, independently of the verifier report.
    return release_dir, hashlib.sha256(manifest_bytes).hexdigest()


def _new_repo(tmp_path: Path, release_bytes: tuple[bytes, bytes]) -> tuple[Path, Path, str]:
    root = tmp_path / "synthetic-fixture-repository"
    root.mkdir(parents=True)
    release_dir, pin = _write_release(root, release_bytes)
    return root, release_dir, pin


def _reseal_manifest(manifest: dict[str, object]) -> bytes:
    return _canonical(manifest)


def test_provider_requires_explicit_supported_profile_and_manifest_pin(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    root, _, pin = _new_repo(tmp_path, release_bytes)

    with pytest.raises(DemoProviderError) as profile_error:
        DemoProvider.open(
            profile="controlled_synthetic_demo",  # type: ignore[arg-type]
            expected_manifest_sha256=pin,
            repository_root=root,
        )
    assert profile_error.value.code is DemoErrorCode.PROFILE
    with pytest.raises(DemoReleaseIntegrityError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256="not-a-pin",
            repository_root=root,
        )


def test_provider_cannot_be_constructed_without_the_verified_factory() -> None:
    with pytest.raises(TypeError, match="DemoProvider.open"):
        DemoProvider()


def test_successful_load_uses_the_independent_pin_and_freezes_the_snapshot(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    root, _, pin = _new_repo(tmp_path, release_bytes)
    provider = DemoProvider.open(
        profile=DemoProfile.CONTROLLED_SYNTHETIC,
        expected_manifest_sha256=pin,
        repository_root=root,
    )

    assert provider.profile is DemoProfile.CONTROLLED_SYNTHETIC
    assert provider.release_id == "rossmann-course-demo-synthetic-v1"
    assert provider.evidence_kind == "controlled_synthetic_demo"
    assert provider.manifest_sha256 == pin
    assert provider.bundle_sha256 == hashlib.sha256(release_bytes[0]).hexdigest()
    assert len(provider.history_by_store) == 3
    assert len(provider.forecasts_by_query) == 9
    assert len(provider.uncertainty_by_query) == 6
    assert len(provider.comparison_rows) == 69
    assert len(provider.inventory_by_case) == 2
    assert isinstance(provider.bundle["history_rows"], tuple)
    with pytest.raises(TypeError):
        provider.bundle["release_id"] = "canonical"  # type: ignore[index]
    with pytest.raises(TypeError):
        provider.bundle["source_declaration"]["kind"] = "canonical"  # type: ignore[index]


def test_missing_release_or_either_file_is_unavailable(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    root = tmp_path / "empty-repository"
    root.mkdir()
    pin = hashlib.sha256(release_bytes[1]).hexdigest()
    with pytest.raises(DemoReleaseUnavailableError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=root,
        )

    _, release_dir, pin = _new_repo(tmp_path / "partial", release_bytes)
    (release_dir / demo_bundle.BUNDLE_FILENAME).unlink()
    with pytest.raises(DemoReleaseUnavailableError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=release_dir.parents[2],
        )

    _, release_dir, pin = _new_repo(tmp_path / "manifest-missing", release_bytes)
    (release_dir / demo_bundle.MANIFEST_FILENAME).unlink()
    with pytest.raises(DemoReleaseUnavailableError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=release_dir.parents[2],
        )


def test_wrong_pin_and_changed_bundle_bytes_fail_closed(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    root, release_dir, pin = _new_repo(tmp_path, release_bytes)
    with pytest.raises(DemoReleaseIntegrityError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256="0" * 64,
            repository_root=root,
        )

    bundle_path = release_dir / demo_bundle.BUNDLE_FILENAME
    original = bundle_path.read_bytes()
    bundle_path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    with pytest.raises(DemoReleaseIntegrityError) as error:
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=root,
        )
    assert str(release_dir) not in str(error.value)


def test_resealed_invalid_manifest_metadata_is_still_rejected(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    root, release_dir, _ = _new_repo(tmp_path, release_bytes)
    manifest_path = release_dir / demo_bundle.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_bytes())
    manifest["evidence_kind"] = "observed_rossmann"
    changed = _reseal_manifest(manifest)
    manifest_path.write_bytes(changed)
    changed_pin = hashlib.sha256(changed).hexdigest()

    with pytest.raises(DemoReleaseIntegrityError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=changed_pin,
            repository_root=root,
        )


def test_resealed_unsupported_bundle_evidence_kind_is_rejected(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    root, release_dir, _ = _new_repo(tmp_path, release_bytes)
    bundle_path = release_dir / demo_bundle.BUNDLE_FILENAME
    manifest_path = release_dir / demo_bundle.MANIFEST_FILENAME
    bundle = json.loads(bundle_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    bundle["evidence_kind"] = "observed_rossmann"
    bundle_bytes = _canonical(bundle)
    manifest["files"][demo_bundle.BUNDLE_FILENAME] = {
        "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "byte_count": len(bundle_bytes),
    }
    manifest_bytes = _reseal_manifest(manifest)
    bundle_path.write_bytes(bundle_bytes)
    manifest_path.write_bytes(manifest_bytes)

    with pytest.raises(DemoReleaseIntegrityError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            repository_root=root,
        )


def test_extra_release_file_is_rejected(tmp_path: Path, release_bytes: tuple[bytes, bytes]) -> None:
    root, release_dir, pin = _new_repo(tmp_path, release_bytes)
    (release_dir / "extra.json").write_text("{}", encoding="utf-8")

    with pytest.raises(DemoReleaseIntegrityError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=root,
        )


def test_release_directory_junction_is_rejected(
    tmp_path: Path, release_bytes: tuple[bytes, bytes]
) -> None:
    if os.name != "nt":
        pytest.skip("Windows directory junctions are only available on Windows.")
    target_root, target, pin = _new_repo(tmp_path / "target", release_bytes)
    _ = target_root
    alias_root = tmp_path / "alias-repository"
    junction = alias_root / "artifacts" / "public_demo" / demo_bundle.RELEASE_ID
    junction.parent.mkdir(parents=True)
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("Could not create a disposable Windows directory junction.")
    assert junction.is_junction()

    with pytest.raises(DemoReleaseIntegrityError):
        DemoProvider.open(
            profile=DemoProfile.CONTROLLED_SYNTHETIC,
            expected_manifest_sha256=pin,
            repository_root=alias_root,
        )


def test_importing_synthetic_provider_does_not_import_canonical_reader() -> None:
    code = (
        "import sys; import rossmann_forecasting.app.demo_provider; "
        "import rossmann_forecasting.app.demo_services; "
        "assert 'rossmann_forecasting.app.artifacts' not in sys.modules; "
        "assert 'rossmann_forecasting.app.services' not in sys.modules; "
        "assert not any(name.startswith('rossmann_forecasting.forecasting') "
        "for name in sys.modules); "
        "assert not any(name.startswith('rossmann_forecasting.inventory') "
        "for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", code], cwd=Path.cwd(), check=True)
