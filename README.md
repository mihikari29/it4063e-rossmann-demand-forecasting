# Retail Demand Forecasting for Inventory Optimization (FMCG)

**IT4063E – Introduction to Business Analytics · Semester 20261**

Forecast each Rossmann store's daily monetary `Sales` at **Store × Date** over a primary
**14-calendar-day horizon (H14)**, then compare inventory-value decisions under documented
synthetic operating assumptions. The business question is how expected turnover and uncertainty
inform conditional service/cost trade-offs.

Rossmann supplies observed monetary turnover, without product quantities, SKU-level sales, real
inventory or observed stockouts. Synthetic lead times, stock, costs and equivalent units support
simulation; they cannot establish actual procurement needs or historical savings. The
instructor-aligned Store-level scope is recorded in ADR-028; its additional methodological
proposals remain unaccepted.

[Proposal](docs/PROPOSAL.md) · [Project plan](docs/PROJECT_PLAN.md) ·
[Decisions](docs/DECISIONS.md) · [Progress and results](docs/PROGRESS.md) ·
[Data Dictionary](docs/DATA_DICTIONARY.md) · [Local setup](#environment-and-quick-start)

## Current state

Status as recorded on **2026-10-24**; [PROGRESS](docs/PROGRESS.md) owns detailed evidence.
Implemented components and accepted methods do not by themselves complete course delivery.

| Workstream | Verified state | Remaining boundary |
|---|---|---|
| Forecasting and application core | Phases 0–12 COMPLETE; selected Global LightGBM trial A / 180 rounds; accepted Fit B uncertainty frozen | Existing API/dashboard use localhost under ADR-024 |
| Scenario evaluation (WP1) | L1/L2/L3-F and fixture-only Milestones 1/2 REVIEWED / INTEGRATED | No real-data scenario analysis; real inputs, volume segmentation and L4 execution remain gated |
| Controlled-synthetic demonstration | A, B1, B2-A and B2-B integrated through PRs #52–#55; WP2-S22 corrections present on current `origin/main` | Milestone B INTEGRATED IMPLEMENTATION / CLOSEOUT PENDING; independent corrective review and formal closeout not recorded |
| Final evaluation and monitoring | Phase 13 M1–M3 integrated through PR #40; phase PLANNED / NOT APPROVED | Independent M3 review, source preparation, rehearsal, staging, release, M4 and later gates; final replay has not run |
| Public delivery and reporting | ADR-030 accepts the future two-URL objective | No public deployment or live public URL; Milestone C unauthorized; Phase 14 incomplete |

The protected final period **2015-07-04 through 2015-07-31 remains unreleased**. Earlier
full-source descriptive exposure is disclosed in [EDA findings](docs/EDA_FINDINGS.md); it does not
authorize new target inspection or tuning. CC-02/CC-02D readiness code is integrated, but no real
custodian preparation, development bundle, STL decomposition or published STL findings exist.
Git places the minor corrections at `a8edc487`; the older pending-integration wording in PROGRESS
and the public-demo plan is a recorded checkpoint, not evidence of independent acceptance.

## Project Requirements and Deliverables

The assignment requires all eight modules, Rossmann as the base dataset, and documented synthetic
operational/supply-chain data. Illustrative synthetic fields do not require fabricating every
example field or product-level observation.

| Assignment module | Existing capability and evidence | Remaining work / acceptance gap |
|---|---|---|
| 1. Business Understanding and Data Generation | [Proposal](docs/PROPOSAL.md), [Dictionary](docs/DATA_DICTIONARY.md), completed [Phase 9 generator](plans/completed/phase-9-synthetic-inventory.md) | Maintain assumption/provenance disclosure in final business interpretation |
| 2. Exploratory Data Analysis | Source-faithful preparation, notebooks and [descriptive findings](docs/EDA_FINDINGS.md) | Separately authorized CC-02 source/provider/STL/findings operations; no real STL evidence yet |
| 3. Data Cleaning | [Validation evidence](docs/DATA_VALIDATION.md), sparse dates and source nulls preserved | Document limitations in final report; no unsupported gap filling or anomaly correction |
| 4. Feature Engineering | Frozen 29-predictor [Feature Contract](docs/FEATURE_CONTRACT.md), exact-calendar lags and recursive history APIs | Preserve origin-time availability assumptions and approved schema |
| 5. Model Development | Three-model development comparison, accepted selection, daily/cumulative uncertainty and [inventory simulation](plans/completed/phase-10-inventory-simulation.md) | Real-data WP1 scenario comparisons and separately authorized frozen final evaluation |
| 6. Model Deployment | Shared services, local read-only FastAPI, five-screen Streamlit, offline synthetic adapters | Two accessible public URLs after content, security, hosting and explicit release approval |
| 7. Model Monitoring | Integrity checks and accepted ADR-026 descriptive final-replay design | Execute authorized replay and deliver monitoring evidence; additional drift/trigger methods need approval and implementation |
| 8. Final Report and Presentation | Versioned methodology, code, results and review history | Consolidated PDF, slides and demonstration after reviewed final evidence |

Final delivery checklist:

- [x] Source code on [GitHub](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting), with reproducible local commands.
- [x] [Data Dictionary](docs/DATA_DICTIONARY.md) covering current real, engineered and simulated fields; update for later approved outputs.
- [ ] Publicly accessible, read-only FastAPI demonstration URL — **pending**.
- [ ] Publicly accessible Streamlit dashboard URL — **pending**.
- [ ] Monitoring report or dashboard with chronological errors, availability and simulated business interpretation — **pending**.
- [ ] Final PDF report — **pending**.
- [ ] Presentation slides — **pending**.
- [ ] Final live or recorded demonstration — **pending**; accepted local UI review is narrower evidence.

## System architecture

```text
Immutable Rossmann sources -> validation/preparation -> point-in-time features
  -> Seasonal Naive / additive Holt-Winters / global LightGBM
  -> development comparison + selected recipe + daily/cumulative uncertainty
Synthetic operating scenarios -------------------------> inventory-value simulation
Pinned development artifacts -> shared Python services -> local FastAPI / Streamlit

Separate controlled-synthetic bundle -> verified demonstration services
                                    -> synthetic FastAPI / direct-service Streamlit
Frozen final protocol -> authorized sequential replay -> monitoring + final report
```

FastAPI and Streamlit reuse Python services; Streamlit calls them directly without requiring HTTP
communication with the API. Precomputed outputs suffice for demonstration. On-demand inference is
optional and is not an existing application capability. The controlled-synthetic bundle illustrates
interfaces and behavior; it is not Rossmann-derived analytical evidence or a fitted model result.

## Model comparison and scenario analysis

The accepted ladder is **Seasonal Naive → additive Holt-Winters → global recursive LightGBM**.
ADR-020's development-only selection chose `global_lightgbm_gbdt_regression_l1`, trial A at exactly
180 rounds. Comparisons retain the three approved chronological H14 origins, observed source
`Open=1` eligibility, primary MAE, supplementary RMSE/cautious MAPE/WAPE and explicit forecast
availability. Future actual Sales and Customers never enter recursive prediction. An approved
opening schedule routes operational outputs after the full raw path; Open remains outside the
predictor matrix. Operational routing requires a supplied/planned or explicitly assumed origin-known
schedule, with unknown values unresolved. Protected future actual Open cannot substitute for a plan.

Required [WP1 scenario evaluation](plans/active/wp1-scenario-forecast-evaluation.md) compares the
same candidates on identical eligible/available rows at the same origins, with segment counts,
denominators, missing predictions and failure cases. Fixture-tested L2 supports origin,
horizon/week blocks, weekday and optional Promo, StoreType, Assortment and holiday metadata views;
the current fixture provider enables Promo only. Its MAE/RMSE/WAPE and directional summaries do not
add a new MAPE contract. Competition strata, development-only volume cohorts, metadata sources and
additional methods require their applicable design/input approvals; volume segmentation remains
blocked. No real-data scenario result exists. LightGBM need not win every stratum. Synthetic
inventory stresses remain separate; cross-model inventory simulation is optional bonus work.
See the [proposal](docs/PROPOSAL.md) for proposed analytical commitments and pending decisions.

## Inventory simulation interpretation

The completed Phase 9 generator supplies reproducible synthetic lead times, starting stock,
service targets and costs. Phase 10 compares historical-mean and frozen LightGBM standing targets
under common inputs. Daily review advances a simulated order queue and lost-sales state against
targets fixed once at origin; it supplies no continuously refreshed protection-period forecast.

Daily two-sided prediction intervals and one-sided cumulative protection bounds are distinct;
daily upper endpoints cannot be summed. Stock, orders and demand use retail-equivalent monetary
value; costs and equivalent units are synthetic. The accepted development comparison found higher
simulated holding-plus-shortfall cost for the forecast policy in the reported synthetic-base and
historical-reference cases; unfavorable findings remain valid. Canonical evidence is in
[PROGRESS](docs/PROGRESS.md) and the [Phase 10 plan](plans/completed/phase-10-inventory-simulation.md).
Phase 13's accepted A-bounded scope retains two independent origin-frozen H14 episodes, with no
claim of continuous rolling 28-day inventory validation, calibrated later-review suffixes or actual
SKU procurement capability.

## Monitoring and retraining review

| Dimension | Commitment and current boundary |
|---|---|
| Data quality | Schema, duplicate Store-Date keys, nulls, missing dates, invalid values, forecast availability and unresolved operational inputs. Validation/integrity checks exist; ADR-026 selects deterministic final-replay alerts. |
| Data characteristics / drift | Descriptive feature, Sales-history, Promo and Store-segment shifts. Additional statistical drift detection/reference rules remain proposed. |
| Forecast performance | Chronological MAE, cautious MAPE, WAPE, bias where supported, forecast availability and empirical interval coverage, scored only after actuals become available. Final-replay monitoring has not run. |
| Simulated business | Stockout-rate proxy, value fill rate, completed positive-demand receipt-cycle service proxy and holding/shortfall costs, with denominators; these are simulations, never observed savings. |

ADR-026 selects daily and trailing 7/14-calendar-day descriptive summaries by origin/horizon,
plus deterministic integrity/data-quality alerts. It selects no statistical drift, error,
interval-coverage or service alarm thresholds. The [proposal](docs/PROPOSAL.md) adds a concrete
**proposed, unvalidated operational trigger policy** using development-only references, explicit
windows/support floors and persistent deterioration, with warning, unavailable-evidence and
human-review-required states. Those parameters and additional methods need a new approved decision
and implementation; ADR-028 remains proposed. Automatic retraining is unnecessary. No triggered
retraining or adaptive model/policy/interval changes are permitted in frozen Phase 13. A 28-day
replay cannot establish persistent production drift.

## API/dashboard demonstration status

Final delivery commits to **one public read-only FastAPI URL and one public Streamlit URL** under
ADR-030's narrow objective. Both are **pending**; no live public link exists to list here. ADR-030
allows a narrow exception to ADR-017's optional API-hosting direction only upon separately
authorized deployment. ADR-024 still governs current localhost operation. See the
[release contract](docs/PUBLIC_DEMO_RELEASE_CONTRACT.md) and
[active public-demo plan](plans/active/public-course-demo.md).

The canonical local app reads bounded history and pinned Rossmann-derived development artifacts.
The separate integrated synthetic API/dashboard consume an immutable controlled-synthetic bundle;
their local behavior does not prove historical accuracy, calibrated uncertainty or real inventory.
Public runtime/listener changes, exact bundle/content and rights approval, independent security
review, hosting/resource/rollback assessment and explicit owner release authorization remain gates.
Possible later source-derived public content needs separate provenance, rights and release approval.
Raw sources, protected outcomes, credentials and authorization records stay out of public bundles.

## Development integration history

<details>
<summary>Expand accepted development results and integration evidence</summary>

Phase 5 additive Holt-Winters
was integrated with the architecture/governance review by [PR #7](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/7)
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

Phase 9 is **COMPLETE** under accepted ADR-022. Its [completed plan](plans/completed/phase-9-synthetic-inventory.md)
preserves the design, implementation and review record. PR #19 was squash-merged into `main` at
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22` after external implementation and numerical review
acceptance. The canonical accepted development run is
`phase9-dev-20261007-config-validation-fix` (manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`). It produces synthetic
monetary context only; it does not fit forecasts or simulate inventory policies.

Phase 10 was implemented under ADR-023. PR #23 integrated the implementation at
`15bce83cd63a4edfeed6defb95788da90d0f36d9` and B1-B3 corrective changes integrated by PR #24 at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. The final independent external/model-assisted review
accepted the corrective implementation and numerical evidence. The [completed plan](plans/completed/phase-10-inventory-simulation.md)
records formal closeout. The accepted canonical run is `phase10-dev-20261008-validator-fix`
(manifest SHA-256 `1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`). Phases 0–10
are complete on `main` after PR #25 integration. Phase 11 is COMPLETE following PR #26's squash
merge at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; M1-M4 are accepted and M3-01, M4-01 and FR-01
are resolved. Its [completed plan](plans/completed/phase-11-application-services.md) records the
formal closeout. The protected final holdout remains unreleased.

</details>

## Environment and quick start

Python **3.12–3.14** is supported; **3.14** is the reference environment. Install pinned
[uv 0.12.23](https://docs.astral.sh/uv/getting-started/installation/) and run from the repo root:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
.\.venv\Scripts\Activate.ps1
python -m pytest
```

On macOS/Linux use `source .venv/bin/activate`. Both Python 3.12 and 3.14 passed the fixture suite
in isolated locked Windows environments. `pyproject.toml` is the hand-maintained dependency source;
`uv.lock` pins resolved packages/hashes. The optional `api` extra installs FastAPI, Uvicorn and the
HTTP test client for the local adapter and its fixture tests. The optional `dashboard` extra installs
Streamlit for the dashboard and AppTest suite. Neither extra is a core forecasting dependency.
Add `--extra acquisition` to sync only if using Kaggle API; manual acquisition needs no credentials
in this repo. See [workflow](docs/WORKFLOW.md) for lock updates, CI, branch lifecycle and contribution
authority.

<details>
<summary>Expand data-pipeline commands and detailed development evidence</summary>

## Data setup and commands

These are reproducibility references for their separately authorized scopes, not permission to
access protected data. They were not executed for this documentation task. Obtain official Kaggle
files through the [acquisition guide](docs/DATA_ACQUISITION.md), preserve them under
`data/raw/rossmann/`, then validate and prepare only within the applicable authorization:

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
and must not be reused as development inference. Source validation, preparation and default feature
generation have broader historical contact than the development forecast runners; this command
list does not authorize inspection or regeneration of protected-period data.

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

CC-02 adds a separate retrospective weekly STL diagnostic. Its reusable API accepts an
already-authorized in-memory `Store`, `Date`, `Sales` frame; it does not read the combined prepared
train artifact. A fixed-path, fixture-tested loader is implemented for an immutable development-only
bundle supplied with an external approval binding. That binding is trusted only when issued through
a separately reviewed operator process; the Python record does not prove custody or physical
separation. The dedicated command still has no filesystem input option, prints its trusted-input
contract, and fails closed:

```powershell
python scripts/run_seasonal_decomposition.py --describe-input-contract
```

The fixed diagnostic ends by 2015-07-03, uses the first three eligible Store IDs, and writes
components, status, figures, and a provenance manifest under ignored
`reports/generated/seasonal_decomposition/` when called through its API. The CC-02C preparation
code implements the Store/Date/Sales projection and immutable bundle writer, with a separate fixed
source `--execute-once` gate. The command describes the contract or fails closed by default. A
future custodian may execute it only under the externally authenticated one-use procedure, with
hash-matched source-access/preparation/custody evidence, the approved account and host, and the
approved clean execution commit. Python checks packet/evidence structure and hashes, not approving
authority. The command has no source-path override and stops after bundle preparation; it does not
load the provider or run STL:

```powershell
python scripts/prepare_cc02_development.py --describe-input-contract
```

See the [CC-02D custodian runbook](docs/CC-02D_CUSTODIAN_RUNBOOK.md) for the future GO/NO-GO
checklist and independent verification/provider/STL handoff.

No real partition or Rossmann decomposition has been created or run. A future custodian reading the
mixed source mechanically accesses protected bytes and needs a separate explicit authorization.
Provider loading, STL execution, and findings publication require later approvals. Reference IDs
may be reserved before preparation, but pending records grant no permission. The local trust claim
relies on the custodian/operator and machine owner/administrator; separate Windows identities and
ACLs are optional hardening, not a claim of strict isolation. Synthetic fixture verification is not
a Rossmann result. The components are descriptive and are not forecasting features or
model-selection evidence. See the [completed provider plan](plans/completed/cc-02b-trusted-development-provider.md),
[completed preparation plan](plans/completed/cc-02c-custodian-preparation.md), and
[EDA findings](docs/EDA_FINDINGS.md#cc-02-weekly-stl-diagnostic).

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

## Phase 9 synthetic supply-chain scenarios

After the prepared development data and frozen Phase 7/8 artifacts exist, run with a new, unused
run ID (this example can be run once):

```powershell
python scripts/generate_inventory_scenarios.py --run-id phase9-dev-20261007-example
```

The generator reads only the projected Store/Date/Sales/Open fields in the 56-day windows ending
2015-06-05 and 2015-06-19. It verifies frozen upstream identities and date boundaries before
hashing, then writes origin anchors, store parameters, a historical reference, eight synthetic
families, validation evidence and a manifest under
`data/processed/synthetic_inventory/<run_id>/`. Successful runs update the ignored `current.json`;
existing run IDs are immutable. The accepted canonical development run is
`phase9-dev-20261007-config-validation-fix` (manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`). It contains 82 catalog
rows, 2,230 origin anchors, 91,430 store-parameter rows and 1,280,020 daily-context rows. These
outputs are local artifacts and are not committed. All operational values are illustrative monetary
assumptions. This command does not create an inventory ledger, evaluate a policy, estimate realized
savings, or access the protected final holdout.

## Phase 10 - inventory simulation closeout

The [completed plan](plans/completed/phase-10-inventory-simulation.md) defines **Simulated inventory-value
policy comparison and sensitivity analysis**. It compares a historical-mean standing target with
a frozen LightGBM point-prefix plus cumulative buffer at June 5/Fit A or June 19/Fit B. Targets
are set once before evaluation outcomes, then reused for daily inventory reviews. There is no
forecast refresh or calibrated later-review suffix uncertainty; the standing target can become stale.

R=1, L=2–7 and P=L+1<=14. L means full intervening calendar demand days: an end-of-day
order is received at the start of t+L+1. L=2 means receipt before day-3 demand. Lost-sales queue
accounting uses continuous retail-equivalent monetary values, identical scenario inputs and
day-14 order suppression. Historical q used in synthetic scenarios is an uncalibrated illustrative
buffer, with `calibration_transport_valid=false`, not a synthetic service probability.

The approved cost measure is simulated holding-plus-shortfall cost; terminal stock/pipeline
exposure stays separate. The completed positive-demand receipt-cycle service rate is a
project-specific simulated CSL proxy with a policy-dependent denominator. No actual inventory,
stockouts, physical quantities, realized savings, guaranteed service or optimality is established.

Methodology and ADR-023 were approved on 2026-10-07. The implementation is in
`src/rossmann_forecasting/inventory/simulation.py`; run it with a new unused ID:

```powershell
python scripts/run_inventory_simulation.py --run-id phase10-dev-example
```

The pre-review `phase10-dev-20261007-implementation-v2` and `phase10-dev-20261008-review-fixes`
runs remain immutable historical evidence. The accepted canonical run is
`phase10-dev-20261008-validator-fix` (manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`). Final independent
external/model-assisted review returned `PHASE10_FINAL_FOCUSED_REREVIEW=ACCEPT_WITH_MINOR_CHANGES`:
B1, B2 and B3 PASS, with no blocking findings. The only minor issue was stale PR #24 metadata; it was
corrected. Review history, provenance, tests and numerical evidence are in [PROGRESS](docs/PROGRESS.md).

This simulated inventory-value policy comparison reports higher simulated holding-plus-shortfall
cost under these assumptions for the synthetic-base and historical reference cases. It does not
establish real inventory, physical demand, real stockouts, savings, universal forecast performance,
statistical superiority, optimality, calibrated synthetic service guarantees or production readiness.
Phase 10 is **COMPLETE** after closeout PR #25 merged into `main` at
`d437269b9f0cf36a842cdfd496ad50a310804768`; no final-holdout evaluation occurred. Phase 11 is
COMPLETE after PR #26 squash-merged at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; M1-M4 are
accepted, findings M3-01, M4-01 and FR-01 are resolved, and post-merge Quality #81 passed on Python
3.12 and 3.14. The [completed Phase 11 plan](plans/completed/phase-11-application-services.md)
records the formal closeout. The protected final holdout remains unreleased.

</details>

## Phase 11 local/demo API

The read-only FastAPI adapter exposes the accepted M2 services through seven GET routes. Fixture
tests need no canonical local artifacts or Kaggle credentials. For a clean checkout, install the
locked development and API extras and run the fixture suite:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dev --extra api --extra dashboard python -m pytest
```

Start the local server from the repository root:

```powershell
uv run --locked --extra dev --extra api python -m uvicorn rossmann_forecasting.app.api:app --host 127.0.0.1 --port 8000
```

In PowerShell, check process health, list supported cases, and try a bounded forecast or the
canonical reference inventory case:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/catalog
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/forecasts?store_id=1&forecast_origin=2015-06-19"
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/inventory?case_id=synthetic_base-20150605-r00--reference"
```

Portable shells can use `curl` with the same URLs. Stop Uvicorn with **Ctrl+C**.

The seven GET routes are `/health`, `/api/v1/catalog`, `/api/v1/forecasts`,
`/api/v1/uncertainty`, `/api/v1/model-comparison`, `/api/v1/inventory`, and `/api/v1/history`.
They read pinned development results or bounded historical Sales through shared services, adding
no inference or simulation. Historical access ends 2015-07-03. Error bodies use stable sanitized
JSON codes. Health `200` reports process responsiveness, not artifact integrity. Missing ignored
canonical Phase 7–10 artifacts make catalog resources unavailable and dependent requests return
sanitized `503`; fixture tests still work from a clean checkout. Canonical artifacts are not in Git.
The server binds to `127.0.0.1`; public delivery remains gated. See the
[Phase 11 handoff](plans/completed/phase-11-application-services.md#phase-11-m4-integration-handoff)
for service interfaces, artifact requirements and limitations.

## Phase 12 dashboard

The five-screen Streamlit dashboard is integrated, and Phase 12 is **COMPLETE**. It presents
bounded historical Sales, saved forecasts and uncertainty, accepted model comparisons, and
synthetic inventory comparisons through the existing services. The approved use remains local
development, analysis and live demonstration at `http://127.0.0.1:8501`. LAN, network, tunnel,
firewall, cloud and public exposure are out of scope under ADR-024 in [DECISIONS](docs/DECISIONS.md).
The [completed Phase 12 plan](plans/completed/phase-12-streamlit-dashboard.md) records the merge,
review and acceptance evidence; the [localhost deployment runbook](docs/DEPLOYMENT_LAN.md) covers
startup, local artifact requirements, security settings and recovery.

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dashboard streamlit run streamlit_app.py
```

The dashboard binds to `127.0.0.1:8501`. It does not train or infer forecasts, run inventory
simulation, access the Phase 10 ledger, or evaluate the protected final holdout. The user reported
PASS on human visual review of all five screens; this acceptance is recorded as user-attested.
Phase 12 integration and closeout evidence is in the [completed plan](plans/completed/phase-12-streamlit-dashboard.md).
ADR-030 accepts the future two-URL objective. Milestone A, B1, B2-A and B2-B are integrated.
Milestone B closeout is pending; WP2-S22 corrections are present on `origin/main`, while
independent corrective review and formal closeout are not recorded.
No public runtime, listener, bundle publication or deployment exists. ADR-024 remains effective.

### Controlled-synthetic course dashboard (local only)

The separate controlled-synthetic dashboard entrypoint is an offline, read-only view over the
verified B1 Python services; it does not use FastAPI and does not change the canonical
`streamlit_app.py` default. To run it locally, supply both process settings explicitly. The manifest
digest must come from a trusted source outside the release manifest itself:

```powershell
$env:ROSSMANN_DEMO_PROFILE = "controlled_synthetic_demo"
$env:ROSSMANN_DEMO_MANIFEST_SHA256 = "<independently supplied lowercase 64-character SHA-256>"
uv run --locked --extra dashboard streamlit run demo_streamlit_app.py
```

The entrypoint accepts no release path or dashboard pin widget, and it fails closed if configuration
or the fixed local release is unavailable or invalid. Every screen labels these values as controlled
synthetic evidence; they are not observed Rossmann performance. This local entrypoint does not grant
authority to publish the bundle, expose a public URL or deploy a service.

## Architecture and remaining work

Implemented packages: `data/` (provenance/preparation), `analysis/` (descriptive EDA),
`features/` (shared static/history contract), `forecasting/` (baselines/evaluation/runners and
development-only model selection), `inventory/` (Phase 9 origin-safe scenarios and the reviewed
Phase 10 policy simulator), and `app/` (shared services and thin adapters).
Thin command scripts expose reusable logic; notebooks are exploration/presentation.

**WP1-L3-F is fixture-only test support, not a production input path.**
`verify_trusted_scenario_fixture_snapshot` requires reviewed, project-controlled synthetic fixtures
or controlled synthetic test mutations. It cannot authenticate their origin, custody or historical
availability, and must not prepare, verify, bind or load actual Rossmann development datasets.
Output limits are checked after Arrow materialization; there is no hard peak-memory guarantee and
erroneous fixtures may exhaust memory or terminate the process. WP1-S7-01 remains
**UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE CONTRACT APPROVED** under
[ADR-029](docs/DECISIONS.md#adr-029--wp1-l3-f-restricted-trusted-fixture-contract).
L3-F is REVIEWED / INTEGRATED; hashes, receipts and synthetic bindings grant no real-source
access, L4 execution or publication authority. Real WP1 inputs and analysis remain separately gated;
passing fixture tests does not establish completion of the course deliverables.

The [roadmap](docs/PROJECT_PLAN.md) keeps Phase 0–14 IDs and their dependencies. Remaining work is:

- Authorize safe real-data WP1 inputs and frozen scenario analysis; resolve applicable
  competition/volume designs without changing accepted Phase 7 selection.
- Separately authorize CC-02D source/preparation/provider/STL/findings operations.
- Complete [Phase 13](plans/active/phase-13-sequential-final-evaluation.md) independent M3 review,
  readiness, rehearsal, staging, resources, release and later milestones before frozen final replay.
- Close public-demo Milestone B and obtain Milestone C content/security/hosting/release approvals
  before delivering the two public URLs. The local Phase 12 implementation remains COMPLETE under
  ADR-024; its [completed plan](plans/completed/phase-12-streamlit-dashboard.md) preserves PR #32,
  merge `5527e780d1a59108c041bb4ca33a32dbb3bc3aca` and Quality #103 evidence.
- Approve and implement any additional drift or retraining-review methods, then consolidate
  reviewed analytical results, monitoring, PDF, slides and demonstration in Phase 14.

These commitments authorize no source operation, holdout release, retraining or public deployment.
On-demand inference, cross-model inventory simulation and Evidently remain optional.

The [historical Phase 6 implementation handoff](docs/PROJECT_PLAN.md#phase-6-implementation-handoff-historical)
records the inputs, origins, metrics, artifacts and tests used. Phases 5–9 are integrated and formally
closed. Phase 9 implements only the approved scenario generator. Phase 10's reviewed stateful simulator
is formally closed following integration of closeout PR #25. Later phases require separate authorization.
The final holdout remains protected.

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
src/rossmann_forecasting/{data,analysis,features,forecasting,inventory,app}/
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

Earlier full-source validation/EDA included the later holdout dates. Subsequent learned references,
cohorts, tuning and calibration must use eligible development/origin history. Final evaluation is
separately gated and is not a pristine unseen-label experiment. Synthetic interface illustrations
cannot replace real analytical evidence. AI-assisted implementation/review does not establish
human authorship or course compliance; team ownership and disclosure obligations remain.

Start with the [proposal](docs/PROPOSAL.md), [roadmap](docs/PROJECT_PLAN.md),
[decisions](docs/DECISIONS.md), [progress](docs/PROGRESS.md), [agent contract](AGENTS.md),
[workflow](docs/WORKFLOW.md), [dictionary](docs/DATA_DICTIONARY.md),
[feature contract](docs/FEATURE_CONTRACT.md), and [source validation](docs/DATA_VALIDATION.md).

## Team

- Pham Le Minh Quang — 20235554
- Tran Quoc Tuan — 20235569
- Vo Ta Quang Nhat — 20225454
- Nguyen Trung Hieu — 202416689
- Nguyen Gia Minh — 202400111
