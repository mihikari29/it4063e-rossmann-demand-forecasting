"""Prepare immutable Rossmann source files into ignored Parquet tables."""

from __future__ import annotations

from rossmann_forecasting.data.preparation import cli_main

if __name__ == "__main__":
    raise SystemExit(cli_main())
