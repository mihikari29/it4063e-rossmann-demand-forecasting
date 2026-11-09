"""Write an offline notice retiring the static mock; never upload or deploy."""

from __future__ import annotations

import argparse
from pathlib import Path

OFFLINE_NOTICE = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>Rossmann course demonstration instructions</title>
<style>body{font:18px system-ui;max-width:850px;margin:4rem auto;padding:1rem}</style>
<h1>Course demonstration: local Python services</h1>
<p>This static page does not execute FastAPI, LightGBM, inventory simulation or live monitoring.</p>
<p>The previous mock API tester and fixed statistical/business values have been retired.</p>
<p>Use the repository's typed FastAPI and Streamlit applications with a pinned, verified
controlled-synthetic bundle. Fixture values demonstrate interfaces and arithmetic.</p>
<p>See docs/LOCAL_DEMO_DEPLOYMENT.md for separate loopback services and HTTP verification,
and docs/MONITORING.md for reproducible descriptive synthetic monitoring.</p>
<p>External publication requires owner release and security approval. This builder does not
upload, change any existing Space or establish backend availability.</p></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new local HTML file")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(OFFLINE_NOTICE)
    print(f"Offline notice written to {args.output}; nothing uploaded.")


if __name__ == "__main__":
    main()
