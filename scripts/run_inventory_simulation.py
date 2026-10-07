"""Run the approved development-only Phase 10 inventory-value simulation."""

from __future__ import annotations

import argparse
from pathlib import Path

from rossmann_forecasting.inventory.simulation import run_inventory_simulation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)"
    )
    parser.add_argument("--run-id", required=True, help="new immutable run identifier")
    args = parser.parse_args()
    result = run_inventory_simulation(
        args.root,
        run_id=args.run_id,
        command=f"python scripts/run_inventory_simulation.py --run-id {args.run_id}",
    )
    summary = result["validation_summary"]
    print(f"Phase 10 run {result['run_id']}: {summary['status']}")
    print(f"Artifacts: {result['run_directory']}")
    print(f"Manifest SHA-256: {result['manifest_sha256']}")
    for name, count in summary["actual_counts"].items():
        print(f"{name}: {count:,}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(f"Phase 10 simulation failed: {error}") from error
