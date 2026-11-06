"""Prepare an allowlisted synthetic-only cloud candidate; never upload or deploy."""

import argparse
from pathlib import Path

from rossmann_forecasting.deployment_candidate import prepare_deployment_candidate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = prepare_deployment_candidate(args.output_dir, Path(__file__).resolve().parents[1])
    print(f"Prepared {len(result['output_sha256'])} files; no deployment or public listener.")
