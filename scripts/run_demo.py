"""Launch one of two separate controlled-synthetic services on loopback only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=("api", "dashboard", "course-dashboard"))
    args = parser.parse_args()
    if args.component == "api":
        import uvicorn

        uvicorn.run(
            "rossmann_forecasting.app.demo_runtime:create_app",
            factory=True,
            host="127.0.0.1",
            port=8000,
            access_log=False,
        )
    else:
        root = Path(__file__).resolve().parents[1]
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(
                    root
                    / (
                        "course_demo_app.py"
                        if args.component == "course-dashboard"
                        else "demo_streamlit_app.py"
                    )
                ),
                "--server.address=127.0.0.1",
                "--server.port=8501",
                "--server.headless=true",
                "--server.enableStaticServing=false",
                "--server.enableCORS=true",
                "--server.enableXsrfProtection=true",
                "--browser.gatherUsageStats=false",
            ],
            cwd=root,
            check=True,
        )


if __name__ == "__main__":
    main()
