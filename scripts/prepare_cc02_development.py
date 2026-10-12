"""Describe the fixture-tested CC-02 preparation contract; real execution stays disabled."""

from rossmann_forecasting.data.cc02_preparation import cli_main

if __name__ == "__main__":
    raise SystemExit(cli_main())
