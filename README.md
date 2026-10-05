# Retail Demand Forecasting for Inventory Optimization (FMCG)

Store-level Business Analytics and inventory-value decision support using the Rossmann Store
Sales dataset. This is the group project for **IT4063E - Introduction to Business Analytics**.

The planned system forecasts monetary `Sales` at the **Store x Date** level with a primary
14-day horizon. It does not claim SKU-level or physical-unit forecasting. Any later equivalent
units and supply-chain fields will be explicitly simulated.

## Current Status

Phase 1 - Data Acquisition & Validation is complete. The official Kaggle files were obtained by
manual web download, validated without modifying raw data, and documented from measured evidence.
Phase 2 - Data Preparation & EDA is next but has not begun.

## Environment

Python 3.14 is the supported development baseline. From PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,acquisition]"
```

On macOS or Linux, activate with `source .venv/bin/activate`. The `acquisition` extra installs the
Kaggle client; the `dev` extra installs pytest and Ruff.

## Acquire and Validate Data

Download the official competition archive manually from Kaggle, extract the four expected CSVs to
`data/raw/rossmann/`, and run:

```powershell
python scripts/validate_data.py --report reports/validation/rossmann.json
```

The optional Kaggle API acquisition command remains available as `python scripts/acquire_data.py`
after credentials and competition access are configured outside the repository. It refuses to
overwrite an existing raw directory. The validator is read-only, prints a concise result, writes an
optional ignored JSON report, and exits nonzero on hard failures.

See [data acquisition](docs/DATA_ACQUISITION.md) and
[data validation](docs/DATA_VALIDATION.md) for the reproducible workflow and verified findings.

## Quality Checks

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Documentation

- [Authoritative proposal](docs/proposal.md)
- [Project roadmap](docs/PROJECT_PLAN.md)
- [Current progress](docs/PROGRESS.md)
- [Development workflow](docs/WORKFLOW.md)
- [Decision log](docs/DECISIONS.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)

## Team

- Pham Le Minh Quang - 20235554
- Tran Quoc Tuan - 20235569
- Vo Ta Quang Nhat - 20225454
- Nguyen Trung Hieu - 202416689
- Nguyen Gia Minh - 202400111

## Repository Structure

```text
.
|-- data/README.md
|-- docs/
|-- plans/completed/
|-- scripts/
|-- src/rossmann_forecasting/data/
|-- tests/
`-- pyproject.toml
```

Raw data, generated validation reports, credentials, virtual environments, and caches are ignored.
