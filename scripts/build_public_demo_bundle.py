"""Build or verify the offline controlled-synthetic public-demo release candidate."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from rossmann_forecasting.app.demo_bundle import (  # noqa: E402
    RELEASE_ID,
    DemoBundleError,
    VerificationReport,
    verify_release_directory,
    write_release_candidate,
)


def _fixed_release_path(value: str, option: str) -> Path:
    requested = Path(os.path.abspath(value))
    expected = REPOSITORY_ROOT / "artifacts" / "public_demo" / RELEASE_ID
    if os.path.normcase(str(requested)) != os.path.normcase(str(expected)):
        raise argparse.ArgumentTypeError(f"{option} must be artifacts/public_demo/{RELEASE_ID}")
    return expected


def _report_dict(report: VerificationReport) -> dict[str, object]:
    return {
        "bundle_ready": report.bundle_ready,
        "release_id": report.release_id,
        "evidence_kind": report.evidence_kind,
        "bundle_sha256": report.bundle_sha256,
        "manifest_sha256": report.manifest_sha256,
        "bundle_bytes": report.bundle_bytes,
        "manifest_bytes": report.manifest_bytes,
        "row_counts": report.row_counts,
        "deterministic_regeneration": report.deterministic_regeneration,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="write one new offline release candidate")
    build.add_argument(
        "--output-dir", required=True, type=lambda v: _fixed_release_path(v, "--output-dir")
    )
    verify = commands.add_parser("verify", help="verify the exact two-file release candidate")
    verify.add_argument(
        "--release-dir", required=True, type=lambda v: _fixed_release_path(v, "--release-dir")
    )
    verify.add_argument("--expected-manifest-sha256")
    verify.add_argument(
        "--regenerate", action="store_true", help="compare against deterministic regeneration"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            report = write_release_candidate(args.output_dir, REPOSITORY_ROOT)
        else:
            report = verify_release_directory(
                args.release_dir,
                expected_manifest_sha256=args.expected_manifest_sha256,
                deterministic_regeneration=args.regenerate,
                repository_root=REPOSITORY_ROOT,
            )
    except (DemoBundleError, OSError, ValueError) as exc:
        parser.exit(2, f"release candidate rejected: {exc}\n")
    print(json.dumps(_report_dict(report), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
