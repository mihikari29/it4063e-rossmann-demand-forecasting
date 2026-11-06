"""Export the reviewed Markdown source to an editable 15-slide PPTX."""

import argparse
from pathlib import Path

from rossmann_forecasting.presentation import write_presentation

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(write_presentation(args.output_dir, Path(__file__).resolve().parents[1]))
