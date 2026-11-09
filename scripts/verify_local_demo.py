"""Verify a genuine loopback API using bounded HTTP requests."""

import argparse
import json

import httpx

from rossmann_forecasting.app.demo_probe import probe_local_api


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    with httpx.Client(trust_env=False, follow_redirects=False) as client:
        result = probe_local_api(client)
    print(json.dumps(result, indent=2))
    return 0 if result["bundle_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
