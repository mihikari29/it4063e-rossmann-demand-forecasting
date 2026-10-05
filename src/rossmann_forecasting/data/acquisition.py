"""Safe acquisition of the official Rossmann Store Sales competition files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

from rossmann_forecasting.data.paths import resolve_data_dir

COMPETITION_SLUG = "rossmann-store-sales"
EXPECTED_SOURCE_FILES = (
    "train.csv",
    "test.csv",
    "store.csv",
    "sample_submission.csv",
)


class AcquisitionError(RuntimeError):
    """Raised when official data cannot be acquired safely."""


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return a SHA-256 digest without modifying the file."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def kaggle_cli_path() -> str | None:
    """Return the Kaggle executable path when it is available."""

    executable = shutil.which("kaggle")
    if executable:
        return executable

    scripts_dir = Path(sys.executable).parent
    for name in ("kaggle.exe", "kaggle"):
        candidate = scripts_dir / name
        if candidate.is_file():
            return str(candidate)
    return None


def kaggle_auth_configured() -> bool:
    """Check for Kaggle authentication without exposing credential values."""

    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True

    configured_dir = os.environ.get("KAGGLE_CONFIG_DIR")
    config_path = (
        Path(configured_dir).expanduser() / "kaggle.json"
        if configured_dir
        else Path.home() / ".kaggle" / "kaggle.json"
    )
    if not config_path.is_file():
        return False

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(payload.get("username") and payload.get("key"))


def acquisition_readiness(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Return a credential-safe summary of local acquisition readiness."""

    target = resolve_data_dir(data_dir)
    return {
        "data_dir": str(target),
        "files_present": {name: (target / name).is_file() for name in EXPECTED_SOURCE_FILES},
        "kaggle_cli_available": kaggle_cli_path() is not None,
        "kaggle_auth_configured": kaggle_auth_configured(),
    }


def _extract_expected_files(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        members_by_name = {Path(name).name: name for name in bundle.namelist()}
        missing = [name for name in EXPECTED_SOURCE_FILES if name not in members_by_name]
        if missing:
            raise AcquisitionError(
                "The Kaggle archive is missing expected files: " + ", ".join(missing)
            )

        destination.mkdir(parents=True, exist_ok=False)
        for name in EXPECTED_SOURCE_FILES:
            source_member = members_by_name[name]
            target = destination / name
            with bundle.open(source_member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            if target.stat().st_size == 0:
                raise AcquisitionError(f"Extracted file is empty: {name}")


def acquire_official_data(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Download and atomically place the official competition files.

    Existing raw files are never overwritten. The target directory must not exist,
    which prevents mixing files from different downloads.
    """

    target = resolve_data_dir(data_dir)
    if target.exists():
        raise AcquisitionError(
            f"Raw target already exists and will not be modified: {target}. "
            "Move it aside explicitly before acquiring a new source version."
        )

    executable = kaggle_cli_path()
    if executable is None:
        raise AcquisitionError(
            "Kaggle CLI is unavailable. Install the acquisition extra and retry."
        )
    if not kaggle_auth_configured():
        raise AcquisitionError(
            "Kaggle authentication is unavailable. Configure credentials outside the repository."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".{target.name}.staging-{uuid.uuid4().hex}"

    try:
        with tempfile.TemporaryDirectory(prefix="rossmann-kaggle-") as temporary:
            download_dir = Path(temporary)
            result = subprocess.run(
                [
                    executable,
                    "competitions",
                    "download",
                    "-c",
                    COMPETITION_SLUG,
                    "-p",
                    str(download_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                output = f"{result.stdout}\n{result.stderr}".lower()
                if "403" in output or "forbidden" in output:
                    reason = (
                        "Kaggle returned HTTP 403 Forbidden. Confirm that the account has accepted "
                        "the competition rules and that its API credential is current."
                    )
                elif "401" in output or "unauthorized" in output:
                    reason = "Kaggle rejected the configured API credential."
                else:
                    reason = "Verify credentials, competition access, and network connectivity."
                raise AcquisitionError(
                    f"Kaggle download failed (exit code {result.returncode}). {reason}"
                )

            archives = sorted(download_dir.glob("*.zip"))
            if len(archives) != 1:
                raise AcquisitionError(
                    f"Expected one downloaded ZIP archive, found {len(archives)}."
                )
            _extract_expected_files(archives[0], staging)

        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return {
        "competition": COMPETITION_SLUG,
        "data_dir": str(target),
        "files": {
            name: {
                "bytes": (target / name).stat().st_size,
                "sha256": sha256_file(target / name),
            }
            for name in EXPECTED_SOURCE_FILES
        },
    }


def cli_main(argv: list[str] | None = None) -> int:
    """Run the acquisition command."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        help="Raw-data destination; relative paths resolve from the repository root.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = acquire_official_data(args.data_dir)
    except AcquisitionError as error:
        print(f"Acquisition failed: {error}")
        return 1

    print(f"Acquired official Rossmann files in {manifest['data_dir']}")
    for name, metadata in manifest["files"].items():
        print(f"- {name}: {metadata['bytes']} bytes, sha256={metadata['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
