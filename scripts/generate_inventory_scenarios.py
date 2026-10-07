"""Generate the approved Phase 9 synthetic inventory context for development origins."""

from __future__ import annotations

import argparse
from pathlib import Path

from rossmann_forecasting.inventory.scenarios import run_scenario_generation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)"
    )
    parser.add_argument("--run-id", default="phase9-dev-20261007-canonical1")
    args = parser.parse_args()
    result = run_scenario_generation(args.root, run_id=args.run_id)
    summary = result["validation_summary"]
    print(f"Phase 9 run {result['run_id']}: {summary['status']}")
    print(f"Artifacts: {result['run_directory']}")
    print(f"Manifest SHA-256: {result['manifest_sha256']}")
    for name, count in summary["actual_counts"].items():
        print(f"{name}: {count:,} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
