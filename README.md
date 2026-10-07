# Retail Demand Forecasting for Inventory Optimization (FMCG)

IT4063E Business Analytics project: forecast Rossmann monetary `Sales` at **Store × Date** for
14 days, then demonstrate inventory-value decisions under explicit simulated assumptions.
It provides no SKU forecasts, physical demand, real inventory data or verified Rossmann savings.

## Current state

`main` contains completed Phases 0–8. Phase 5 additive Holt-Winters was integrated with the
architecture/governance review by [PR #7](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/7)
at squash-merge commit `76707a03b7d10dbaa79d3ef26b39e31994431d70`; its formal closeout preserves
the development-only results and does not evaluate the final holdout. Phase 6's approved global
LightGBM candidate was reviewed and merged by
[PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10) at
`dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its [formal closeout plan](plans/completed/phase-6-global-lightgbm.md)
preserves the development-only results and confirms no final-holdout evaluation.
[PROGRESS](docs/PROGRESS.md) records development results. Phase 7 is **COMPLETE** after
[PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged into
`main` at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`; its
[completed plan](plans/completed/phase-7-model-selection.md) preserves the approval and selection
history. The development selection under ADR-020 chose Global LightGBM
(`global_lightgbm_gbdt_regression_l1`), frozen trial A at 180 rounds, for the offline CPU course
demonstration using development evidence.
Phase 8's ADR-021 implementation was squash-merged by
[PR #15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) into `main` at
`c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`. The external results review ACCEPTED the canonical
development run, and its Fit B fitted quantile values are **FROZEN** for that exact run. PR #16
recorded the accepted review and was squash-merged at
`4dd7717fed57ff3b1f14789b980772c1968f3cba`. Phase 8 is **COMPLETE**; the
[completed plan](plans/completed/phase-8-forecast-uncertainty.md) records the explicit closeout.
The selected candidate remains `global_lightgbm_gbdt_regression_l1`. Fit A daily tails at h2, h3
and h9 remain unavailable under the approved sample floor. Fit B raw-primary daily assessment
coverage is 12,263/13,437 (91.26%), below nominal 95%. Operational assessment is a conditional
historical replay assuming saved source Open was known at origin; closure routing inflates pooled
coverage. Sparse Sunday h2/h9 evidence and dependence across stores/origins remain limitations.
These empirical tables provide no conformal, per-store, production or service-level guarantee.
Cumulative uncertainty supports approved origin-anchored prefixes only; no later daily-review
suffix calibration is authorized. The final holdout, 2015-07-04 through 2015-07-31, remains
protected and unreleased. Forecast Sales is monetary turnover, not SKU-level physical demand.

Phase 9 has a [synthetic inventory design](plans/active/phase-9-synthetic-inventory.md)
**PROPOSED / AWAITING APPROVAL**, based on PR #17's integrated Phase 8 closeout.
It specifies origin-safe initialization, deterministic monetary scenarios and synthetic cost
assumptions; no generator or inventory simulation is implemented. Proposed ADR-022 requires
external methodology acceptance before implementation. Synthetic context stays outside the
real forecast feature matrix. Phase 10 remains PLANNED and not started; its daily-review
suffix method and simulation timing require a separate approved design.

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

After the approved Phase 4–6 development forecast artifacts exist, run model selection separately:

```powershell
python scripts/run_model_selection.py --operational-review configs/phase-7-operational-review-v1.json
```

The Phase 7 runner validates and aggregates those cached forecasts; it does not call the model
runners, rerun tuning, or fit candidates. Candidate-level offline operational reviews can be
provided with `--operational-review path/to/review.json`. The versioned review input in this
command approves Seasonal Naive and LightGBM and leaves Holt-Winters `unknown`, within the
`offline_cpu_course_demonstration` scope. The current development-only decision selects LightGBM
under ADR-020 and is integrated by PR #13. Without an operational review or with
unresolved required decisions, the runner writes the comparison and an
`operational_review_required` decision without selected-model artifacts. Outputs are staged and
hashed before publication; prior selected outputs are retired only when their hashes match the
runner manifest. The selected output is a frozen recipe and development evidence, not a fitted
future model or final-holdout result.

`python scripts/run_eda.py` and the two notebooks reproduce the historical **full-source**
descriptive audit, not a development-model gate. That earlier audit included July 4–31 labels;
[EDA findings](docs/EDA_FINDINGS.md) disclose the exposure. Any new source-wide inspection needs an
explicit audit scope; model cohorts/statistics must be recomputed from origin training data.
The current modeling firewall still excludes July 4–31 from selection, tuning and calibration.

## Phase 8 development-only uncertainty

With verified Phase 7 outputs in `data/processed/model_selection/`, run:

```powershell
python scripts/run_forecast_uncertainty.py
```

The command verifies the saved Phase 7 hashes and selected-model identity, then calculates the
approved Fit A/Fit B uncertainty protocol without refitting or tuning the point model. After
calculation, it rechecks the allowlisted Phase 7 manifests and artifacts against their original
hashes before publishing an immutable run under `data/processed/uncertainty/<run_id>/` and updating
the ignored `current.json` pointer. Read `manifest.json` and `coverage_diagnostics.csv` with the
tables. Sparse strata remain explicitly unavailable. The accepted and frozen Fit B values are
bound to canonical run `phase8-impl-20261006-provenance-review`; its unchanged manifest records the
publication-time pre-review freeze state. Operational results are a conditional historical replay
assuming saved source Open was known at each development origin. The closed `[0,0]` route raises
Fit B pooled coverage to 92.48% versus 91.26% on Open=1, so pooled coverage is closure-inflated.
Fit B h2/h9 calibration has 65/64 rows from only 33/32 distinct stores. No conformal or production
guarantee is implied. This command does not access the protected final holdout, evaluate a
production model, or authorize Phases 9–13.

## Architecture and remaining work

Implemented packages: `data/` (provenance/preparation), `analysis/` (descriptive EDA),
`features/` (shared static/history contract), and `forecasting/` (baselines/evaluation/runners and
development-only model selection).
Thin command scripts expose reusable logic; notebooks are exploration/presentation.

The [roadmap](docs/PROJECT_PLAN.md) keeps Phase 0–14 IDs and groups remaining milestones:

- Phases 6–7: complete; ADR-020's development-only decision selected the frozen LightGBM method
  for the offline CPU course demonstration.
- Phase 8: **COMPLETE** after PR #15/#16 integration, independent results acceptance and explicit
  closeout. Fit B values are frozen for the canonical run; cumulative tables support approved
  origin-anchored prefixes only. Phases 9–10 remain planned and have not started.
- Phases 11–13: shared Python services, thin FastAPI adapter, Streamlit and one frozen sequential
  final evaluation. Streamlit calls the same services directly; separate API hosting and Evidently
  are optional.
- Phase 14: recorded results, report, slides and demonstration.

Later inventory/app modules are created when their work is approved; there is no speculative
service framework. The [historical Phase 6 implementation handoff](docs/PROJECT_PLAN.md#phase-6-implementation-handoff-historical)
records the inputs, origins, metrics, artifacts and tests used. Phases 5–8 are integrated and
formally closed. Phase 8 methodology remains as approved in ADR-021; its implementation/results
review is accepted and Fit B is frozen for the identified development run. Phase 9 and later work
requires separate design and authorization. The final holdout remains protected.

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
