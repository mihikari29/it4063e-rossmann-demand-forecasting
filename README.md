# Retail Demand Forecasting for Inventory Optimization (FMCG)

IT4063E Business Analytics project: forecast Rossmann monetary `Sales` at **Store × Date** for
14 days, then demonstrate inventory-value decisions under explicit simulated assumptions.
It provides no SKU forecasts, physical demand, real inventory data or verified Rossmann savings.

## Current state

`main` contains completed Phases 0–6. Phase 5 additive Holt-Winters was integrated with the
architecture/governance review by [PR #7](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/7)
at squash-merge commit `76707a03b7d10dbaa79d3ef26b39e31994431d70`; its formal closeout preserves
the development-only results and does not evaluate the final holdout. Phase 6's approved global
LightGBM candidate was reviewed and merged by
[PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10) at
`dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its [formal closeout plan](plans/completed/phase-6-global-lightgbm.md)
preserves the development-only results and confirms no final-holdout evaluation.
[PROGRESS](docs/PROGRESS.md) records development results. Phase 7 methodology is approved in ADR-020;
implementation awaits integration of design PR #12. No final project model has been selected.

## Environment and quick start

Python **3.12–3.14** is supported; **3.14** is the reference environment. Install pinned
[uv 0.12.23](https://docs.astral.sh/uv/getting-started/installation/) and run from the repo root:

```powershell
uv sync --locked --extra dev --python 3.14
.\.venv\Scripts\Activate.ps1
python -m pytest
```

On macOS/Linux use `source .venv/bin/activate`. Both Python 3.12 and 3.14 passed the fixture suite
in isolated locked Windows environments. `pyproject.toml` is the hand-maintained dependency source;
`uv.lock` pins resolved packages/hashes. Add `--extra acquisition` to sync only if using Kaggle API;
manual acquisition needs no credentials in this repo. See [workflow](docs/WORKFLOW.md) for lock
updates, CI, branch lifecycle and contribution authority.

## Data setup and commands

Obtain official Kaggle files through the [acquisition guide](docs/DATA_ACQUISITION.md), preserve
them under `data/raw/rossmann/`, then validate and prepare:

```powershell
python scripts/validate_data.py --report reports/validation/rossmann.json
python scripts/prepare_data.py
python scripts/build_features.py
python scripts/run_seasonal_naive.py
python scripts/run_holt_winters.py
python scripts/run_lightgbm.py
```

Preparation retains source rows/nulls, asserts many-to-one metadata joins, and writes separate
train/test Parquet. Feature artifacts use the frozen 29-predictor
[contract](docs/FEATURE_CONTRACT.md). Historical feature rows are for fitting through an origin;
validation-target lags must be rebuilt recursively. Default Kaggle inference uses origin July 31
and must not be reused as development inference.

Forecast runners apply the 2015-07-03 label ceiling at read time and use the three approved
14-day windows. Phase 6's LightGBM runner saves ignored artifacts under `data/processed/lightgbm/`
and serialized models under `artifacts/lightgbm/`; it recomputes both reviewed baselines on paired
development rows. These commands do not forecast or score the final holdout or select the final
project model.

`python scripts/run_eda.py` and the two notebooks reproduce the historical **full-source**
descriptive audit, not a development-model gate. That earlier audit included July 4–31 labels;
[EDA findings](docs/EDA_FINDINGS.md) disclose the exposure. Any new source-wide inspection needs an
explicit audit scope; model cohorts/statistics must be recomputed from origin training data.
The current modeling firewall still excludes July 4–31 from selection, tuning and calibration.

## Architecture and remaining work

Implemented packages: `data/` (provenance/preparation), `analysis/` (descriptive EDA),
`features/` (shared static/history contract), and `forecasting/` (baselines/evaluation/runners).
Thin command scripts expose reusable logic; notebooks are exploration/presentation.

The [roadmap](docs/PROJECT_PLAN.md) keeps Phase 0–14 IDs and groups remaining milestones:

- Phases 6–7: Phase 6 global recursive LightGBM candidate is complete; Phase 7 owns later
  development-only model selection under the approved ADR-020 policy. Implementation awaits
  integration of design PR #12.
- Phases 8–10: out-of-sample uncertainty, separate synthetic scenarios and stateful inventory.
- Phases 11–13: shared Python services, thin FastAPI adapter, Streamlit and one frozen sequential
  final evaluation. Streamlit calls the same services directly; separate API hosting and Evidently
  are optional.
- Phase 14: recorded results, report, slides and demonstration.

Later inventory/app modules are created when their work is approved; there is no speculative
service framework. The [historical Phase 6 implementation handoff](docs/PROJECT_PLAN.md#phase-6-implementation-handoff-historical)
records the inputs, origins, metrics, artifacts and tests used. Phases 5 and 6 are integrated and
formally closed; Phase 7's design is approved but remains unintegrated and unimplemented.

## Quality and repository layout

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/check_docs.py
git diff --check
```

The [CI workflow](.github/workflows/quality.yml) runs locked fixture checks for Python 3.12/3.14
on pull requests and pushes to `main`, without Rossmann data or secrets. Verify the live checks for
the current pull request before merging.
Local Markdown checks cover relative files/directories and common heading anchors, not external
website availability.

```text
data/README.md       local immutable/derived artifact conventions
docs/               business intent, contracts, decisions and evidence
plans/active/       current scoped plans awaiting their completion boundary
plans/completed/    preserved historical execution records
scripts/            pipeline entry points and repository checks
src/rossmann_forecasting/{data,analysis,features,forecasting}/
notebooks/          thin descriptive presentation
tests/              constructed-fixture behavioral tests
pyproject.toml      package/tool configuration
uv.lock             generated environment lock
.github/workflows/  fixture quality CI
```

Raw/derived datasets, reports, credentials and model binaries remain ignored. See
[data layout](data/README.md). Final holdout release requires an explicitly authorized protocol
after model/interval/policy choices are frozen; it is never a tuning resource.

## Limitations and documentation

Sales turnover reflects prices/promotions and may not reveal unconstrained demand. Inventory
values, costs, equivalent units, stockouts and policy benefits are simulated. Three late-season
windows do not establish year-round robustness; pooled empirical intervals do not guarantee each
store's service level. Fair negative results or retaining the baseline are valid project outcomes.

Start with the [proposal](docs/proposal.md), [roadmap](docs/PROJECT_PLAN.md),
[decisions](docs/DECISIONS.md), [progress](docs/PROGRESS.md), [agent contract](AGENTS.md),
[workflow](docs/WORKFLOW.md), [dictionary](docs/DATA_DICTIONARY.md),
[feature contract](docs/FEATURE_CONTRACT.md), and [source validation](docs/DATA_VALIDATION.md).

## Team

- Pham Le Minh Quang — 20235554
- Tran Quoc Tuan — 20235569
- Vo Ta Quang Nhat — 20225454
- Nguyen Trung Hieu — 202416689
- Nguyen Gia Minh — 202400111
