# Retail Demand Forecasting for Inventory Optimization (FMCG)

Store-level Business Analytics and inventory-value decision support using the Rossmann Store
Sales dataset. This is the group project for **IT4063E - Introduction to Business Analytics**.

The planned system forecasts monetary `Sales` at the **Store x Date** level with a primary
14-day horizon. It does not claim SKU-level or physical-unit forecasting. Any later equivalent
units and supply-chain fields will be explicitly simulated.

## Current Status

Phase 1 - Data Acquisition & Validation, Phase 2 - Data Preparation & EDA, Phase 3 - Feature
Engineering, and Phase 4 - Seasonal Naive Baseline are COMPLETE. Phase 3 was merged in PR #3 and
Phase 4 in PR #5. Phase 5 - Exponential Smoothing / Holt-Winters - is implemented and under
external review on `feat/holt-winters`; it evaluates the fixed statistical candidate against the
Seasonal Naive baseline on development windows only. Development results are recorded in
[`docs/PROGRESS.md`](docs/PROGRESS.md), and the final holdout remains untouched. Raw Rossmann data
remain immutable; prepared tables, feature Parquet files, EDA exports, and forecast outputs are
reproducible and ignored local outputs.

## Environment

Python 3.14 is the supported development baseline. From PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,acquisition]"
```

On macOS or Linux, activate with `source .venv/bin/activate`. The `acquisition` extra installs the
Kaggle client. The `dev` extra includes pytest, Ruff, and the Jupyter kernel/client needed to execute
the included notebooks. PyArrow and Matplotlib support the Phase 2 Parquet and figure outputs.

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

## Prepare Data and Generate EDA

After the official Phase 1 source files are present, run from the repository root:

```powershell
python scripts/prepare_data.py
python scripts/run_eda.py
```

Preparation verifies the four documented source hashes, retains source rows and nulls, joins store
metadata many-to-one, and writes separate train and test Parquet tables under `data/interim/`.
EDA uses labelled historical train Sales and test covariates only, writing summaries and figures to
`reports/eda/`. These outputs are ignored and can be regenerated. The numbered notebooks provide a
thin presentation layer over the same reusable package functions.

## Build Phase 3 Features

After Phase 2 preparation, build the frozen shared train/inference schema with:

```powershell
python scripts/build_features.py
```

The command verifies raw-source and Phase 2 input hashes, writes ignored
`data/processed/features_train.parquet`, `features_inference.parquet`, and
`feature_manifest.json`, and records development-only coverage plus mechanical final-holdout
checks. See the [Feature Contract](docs/FEATURE_CONTRACT.md) for field roles, dtypes, null rules,
and the origin-censored recursive-history interface. This step trains no models and computes no
forecast metrics.

## Run the Phase 4 Development Baseline

After Phase 2 preparation, run the approved Seasonal Naive development backtest with:

```powershell
python scripts/run_seasonal_naive.py
```

The runner verifies raw and Phase 2 provenance, filters historical inputs through 2015-07-03
before evaluation, and evaluates only the three approved 14-day windows. Forecast records and
window, pooled, horizon, and coverage summaries are written under the ignored
`data/processed/seasonal_naive/` directory. It does not forecast or evaluate the final holdout.
See the [completed Phase 4 plan](plans/completed/phase-4-seasonal-naive.md) for the approved
methodology and [`docs/PROGRESS.md`](docs/PROGRESS.md) for recorded results.

## Run the Phase 5 Statistical Development Evaluation

After Phase 2 preparation, run the approved additive Holt-Winters evaluation with:

```powershell
python scripts/run_holt_winters.py
```

The runner verifies source provenance, filters historical inputs through 2015-07-03 before model
or evaluation code can access labels, and evaluates the same three 14-day development windows as
Phase 4. It recomputes Seasonal Naive for an identical-row paired comparison and writes forecasts,
fit diagnostics, coverage, clipping, metrics, and a manifest under the ignored
`data/processed/holt_winters/` directory. It does not evaluate or forecast the final holdout, and
these Phase 5 results do not select the final project model. See [`docs/PROGRESS.md`](docs/PROGRESS.md)
for the recorded development results.

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
- [Phase 3 feature contract](docs/FEATURE_CONTRACT.md)
- [Phase 2 EDA findings](docs/EDA_FINDINGS.md)

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
|-- plans/
|   |-- active/
|   `-- completed/
|-- scripts/
|-- src/rossmann_forecasting/{analysis,data,features,forecasting}/
|-- notebooks/
|-- tests/
`-- pyproject.toml
```

Raw data, generated validation reports, credentials, virtual environments, and caches are ignored.
