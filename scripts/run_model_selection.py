"""Run Phase 7 selection aggregation over the verified cached development forecasts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rossmann_forecasting.data.paths import repository_root
from rossmann_forecasting.forecasting.model_selection import run_model_selection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare the three approved candidates using saved development forecasts only."
    )
    parser.add_argument(
        "--operational-review",
        type=Path,
        help="Versioned JSON containing candidate-level offline operational review decisions.",
    )
    args = parser.parse_args(argv)
    result = run_model_selection(
        root=repository_root(),
        operational_review_path=args.operational_review,
    )
    decision = result["decision"]
    summary = {
        "output_directory": result["output_directory"],
        "status": result["status"],
        "selected_candidate_id": result["selected_candidate_id"],
        "comparison_rows": result["comparison_rows"],
        "coverage_status": decision.get("coverage_status"),
        "numeric_ladder": decision.get("numeric_ladder"),
        "operational_ladder": decision.get("operational_ladder"),
        "manifest": result["manifest"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return (
        0 if result["status"] not in {"evidence_review_required", "coverage_review_required"} else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
