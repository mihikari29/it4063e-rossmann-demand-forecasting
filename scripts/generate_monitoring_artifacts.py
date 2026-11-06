"""Generate descriptive synthetic monitoring; no source reads or deployment."""

from __future__ import annotations

import argparse
from pathlib import Path

from rossmann_forecasting.monitoring_report import write_synthetic_monitoring_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="new local directory")
    args = parser.parse_args()
    write_synthetic_monitoring_report(args.output_dir, Path(__file__).resolve().parents[1])
    print(f"Synthetic report written to {args.output_dir}; no production observations.")


if __name__ == "__main__":
    main()
