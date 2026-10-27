# Rossmann Sales Forecasting and Inventory Decision Support

**IT4063E — Introduction to Business Analytics — Semester 20261**

Forecast daily monetary `Sales` for each Rossmann store over **14 calendar days**, then
compare inventory-value policies under explicit synthetic operating assumptions. This university
project combines descriptive, predictive and prescriptive analytics in a reproducible Python workflow.

[Proposal](docs/PROPOSAL.md) · [Results and status](docs/PROGRESS.md) ·
[Remaining deliverables](docs/PROJECT_PLAN.md) — [Data Dictionary](docs/DATA_DICTIONARY.md)

## Business problem and objectives

How much store turnover should be expected over the next two weeks, and how do forecast-based
inventory policies affect simulated service and cost? The project explores sales patterns,
compares three forecasting methods, quantifies uncertainty, and presents conditional business
trade-offs through a read-only API and dashboard.

## Dataset and scope

Rossmann Store Sales supplies daily store observations and static metadata for 1,115 stores.
The target is **Store × Date monetary turnover**, without SKU identifiers, physical quantities,
observed inventory or stockouts. Lead times, starting stock, costs and equivalent units are
synthetic assumptions. Simulation results cannot establish actual Rossmann savings.

Development labels stop at **2015-07-03**. The final period **2015-07-04–2015-07-31** remains
protected and unevaluated. Earlier full-source descriptive exposure is disclosed in
[EDA findings](docs/EDA_FINDINGS.md). Access to mixed sources containing protected outcomes
requires its own authorization, including for preparation or hashing.

## Methodology and models

| Component | Accepted approach |
|---|---|
| Preparation and EDA | Source-faithful joins, sparse dates/nulls retained, descriptive associations |
| Features | [29 ordered predictors](docs/FEATURE_CONTRACT.md), exact-calendar lags and complete rolling windows |
| Seasonal Naive | Exact seven-day lookup, then recursive raw predictions |
| Holt-Winters | Per-store additive trend and weekly seasonality on contiguous origin-censored history |
| Global LightGBM | Recursive regression L1; selected trial A at 180 rounds; fit-only categories |
| Evaluation | Three chronological H14 windows; primary MAE on observed open labels, paired rows and explicit coverage |
| Uncertainty | Chronological empirical daily intervals and separate cumulative prefix bounds |
| Inventory | Two origin-frozen monetary standing-target policies with paired scenario/sensitivity comparisons |

The [methodology decisions](docs/DECISIONS.md) explain the rationale and constraints. Raw paths
are generated before opening-schedule routing. Future actual Sales, Customers and Open cannot
enter raw predictions. Missing dates and unknown opening status remain explicit.

## System architecture

```text
Authorized Rossmann inputs → preparation → features → development forecasts
                                                   → comparison → uncertainty
Synthetic operating scenarios + frozen forecasts   → inventory simulation
Verified immutable results → Python services → FastAPI / Streamlit
Controlled synthetic bundle → separate provider → synthetic API / Streamlit
```

Streamlit calls Python services directly. The applications display precomputed evidence and do
not train models or run simulations on request. The synthetic profile has explicit configuration
and never falls back to canonical Rossmann artifacts.

## Results and limitations

On 38,553 common eligible development rows, pooled MAE was **1,681.27** for Seasonal Naive,
**1,281.74** for Holt-Winters and **871.06** for LightGBM. LightGBM was selected under the
accepted coverage and stability rules; its h2, h9 and h10 results were weaker than Seasonal Naive.

Frozen Fit B daily interval coverage was **91.26%**, below nominal 95%. The forecast inventory
policy produced **higher simulated holding-plus-shortfall costs** than the baseline in the
synthetic-base and historical reference cases. These findings and their denominators are retained
in [results](docs/PROGRESS.md). Three late-season Friday origins, sparse Sundays, correlated
errors and synthetic operating assumptions limit generalization. No final-period results or
production/service guarantees are available.

## Installation and quick start

Python **3.12–3.14** is supported, with **3.14** as reference. From the repository root, use
[uv](https://docs.astral.sh/uv/getting-started/installation/) **0.12.23**:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dev --extra api --extra dashboard python -m pytest
```

Fixtures run without Rossmann files or credentials. An optional integration test uses existing
canonical artifacts when present; use a clean checkout without ignored artifacts for a strictly
fixture-only full-suite run. `pyproject.toml` defines dependencies and `uv.lock` pins resolution.
Add the `acquisition` extra only for authorized Kaggle API use.

[Acquisition](docs/DATA_ACQUISITION.md), [pipeline commands](data/README.md), and
[contribution checks](docs/WORKFLOW.md) provide the detailed instructions. Source-wide preparation,
EDA and default feature generation contact protected-period data and require their applicable
access approval. They are separate from the fixture quick start.

## API and dashboard usage

For the canonical local applications:

```powershell
uv run --locked --extra api python -m uvicorn rossmann_forecasting.app.api:app --host 127.0.0.1 --port 8000
uv run --locked --extra dashboard streamlit run streamlit_app.py
```

Run each in its own terminal; stop with **Ctrl+C**. The dashboard binds to
`http://127.0.0.1:8501`. The API exposes seven GET routes:

| Route | Purpose |
|---|---|
| `/health` | Process liveness |
| `/api/v1/catalog` | Supported resources and availability |
| `/api/v1/history` | Bounded historical Sales through July 3 |
| `/api/v1/forecasts` | Saved raw and operational forecasts |
| `/api/v1/uncertainty` | Daily intervals and cumulative bounds |
| `/api/v1/model-comparison` | Development model metrics |
| `/api/v1/inventory` | Saved simulated policy comparisons |

For example, request
`http://127.0.0.1:8000/api/v1/forecasts?store_id=1&forecast_origin=2015-06-19`.
Canonical artifacts are ignored and unavailable in a fresh checkout; dependent routes return
sanitized `503` responses while health remains available. See the
[local application guide](docs/LOCAL_APPLICATION.md) for requirements and recovery.

The separate `demo_streamlit_app.py` requires both `ROSSMANN_DEMO_PROFILE=controlled_synthetic_demo`
and an independently supplied `ROSSMANN_DEMO_MANIFEST_SHA256` pin. Its controlled synthetic
examples demonstrate interface behavior only. See the [demo plan](plans/active/public-course-demo.md)
and [release contract](docs/PUBLIC_DEMO_RELEASE_CONTRACT.md).

## Repository structure

| Path | Contents |
|---|---|
| `src/rossmann_forecasting/` | Reusable data, analysis, features, forecasting, inventory and application code |
| `scripts/` | Thin supported command entrypoints and documentation checker |
| `tests/` | Contract fixtures, API tests and Streamlit AppTests |
| `notebooks/` | Preparation diagnostics and descriptive EDA presentation |
| `docs/` | Proposal, decisions, definitions, results and operating guides |
| `plans/active/` | Remaining scoped work and approval gates |
| `plans/completed/` | Retained methodological specifications |
| `configs/` | Versioned operational review input |
| `data/`, `artifacts/`, `reports/` | Local ignored sources and generated outputs; see [layout](data/README.md) |

## Current status and remaining deliverables

The development analytics and local application core (Phases 0–12) are complete. Fixture-only
scenario support and the synthetic API/dashboard are integrated. Independent corrective review
and synthetic-demo closeout remain pending. Phase 13 input, issuance and uncertainty/target
fixtures are integrated, but final evaluation remains **PLANNED / NOT APPROVED**.

Remaining course work includes authorized real-data scenario analysis, supplementary STL
findings, the frozen final replay and monitoring, public API/dashboard release, and the final
PDF report, slides and demonstration. Public URLs are a gated future delivery objective;
**no public deployment exists**. Current applications stay on localhost. The
[roadmap](docs/PROJECT_PLAN.md) lists dependencies and approvals. Team ownership review and
course-required AI-assistance disclosure remain part of delivery.
