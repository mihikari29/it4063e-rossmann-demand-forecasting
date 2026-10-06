"""Create a development-only Phase 8 uncertainty package from saved Phase 7 outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from rossmann_forecasting.forecasting.uncertainty import run_uncertainty


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)"
    )
    parser.add_argument("--run-id", help="optional unique run ID for reproducible fixture runs")
    args = parser.parse_args()
    result = run_uncertainty(args.root, run_id=args.run_id)
    print(f"Phase 8 run {result['run_id']}: {result['manifest']['status']}")
    print(f"Artifacts: {result['run_directory']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
