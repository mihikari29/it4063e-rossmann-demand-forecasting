"""Stage a compact, checksummed local package; no publication or protected-data reads."""

import argparse
from pathlib import Path

from rossmann_forecasting.submission_package import stage_submission_package

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "report", "presentation", "rendered", "monitoring", "notebook"):
        parser.add_argument(f"--{name}-dir", required=True, type=Path)
    args = parser.parse_args()
    result = stage_submission_package(
        Path(__file__).resolve().parents[1],
        args.output_dir,
        report=args.report_dir,
        presentation=args.presentation_dir,
        rendered=args.rendered_dir,
        monitoring=args.monitoring_dir,
        notebook=args.notebook_dir,
    )
    print(f"Staged {len(result['entries'])} verified files; overall submission remains BLOCKED.")
