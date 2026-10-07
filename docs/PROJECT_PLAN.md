# Project Plan

This roadmap derives from the [proposal](proposal.md) and accepted [decisions](DECISIONS.md).
[PROGRESS](PROGRESS.md) owns current implementation/review/integration state. Each phase below is
a milestone, not a requirement for a separate plan, branch, PR, or closeout ceremony.

## Execution packages and gates

Preserve Phase 0–14 IDs for auditability; do not renumber completed work. Organize the remaining
work into four manageable packages:

| Package | Milestones | Exit evidence |
|---|---|---|
| Forecast comparison | 6–7 | Recursive global candidate, comparable development results, selected-method rationale |
| Uncertainty and inventory | 8–10 | Chronological interval diagnostics, reproducible scenarios, conditional policy comparison |
| Usable demonstration | 11–13 | Shared services/API/UI, frozen protocol, one sequential final evaluation |
| Delivery | 14 | Consolidated results, reproducible demo, report and slides |

A package may share one concise execution plan, but each model/methodology approval and phase
boundary stays explicit. Phase 8 is COMPLETE following accepted results and explicit closeout.
Phase 9 design is PROPOSED / AWAITING APPROVAL; implementation has not started. Phase 10
remains PLANNED and not started, requiring separate design and authorization.
No final holdout scoring belongs to Phase 7: model/preprocessing/refit recipes, interval calibration, inventory
policy/scenarios, and monitoring thresholds must all be frozen before authorized Phase 13 replay
(ADR-015/016). Phase 5 is complete on `main` through PR #7. Phase 6 is complete on `main` through
PR #10. Phase 7 is complete on `main` through PR #13, preserving ADR-020's selected LightGBM
trial A / 180-round recipe. Phase 8 methodology is approved in ADR-021; implementation PR
[#15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) was squash-merged
into `main` at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`. PR #16 recorded independent numerical
review acceptance and Fit B freeze, and was squash-merged into `main` at
`4dd7717fed57ff3b1f14789b980772c1968f3cba`. Phase 8 is **COMPLETE** as of the explicit
2026-10-07 closeout in the [completed plan](../plans/completed/phase-8-forecast-uncertainty.md).
The frozen values apply only to the canonical artifact identities in [PROGRESS](PROGRESS.md).

## Phase 0 — Repository Foundation

**Objective:** Establish sources, scope, contribution rules, and reproducible planning.
**Dependencies:** Project intent/course requirements.
**Deliverables:** Proposal, roadmap, decisions/progress, compact agent/workflow rules.
**Acceptance / boundary:** Documents agree and distinguish planned from actual work; no speculative
model/data/application implementation is introduced merely to populate the tree.

## Phase 1 — Data Acquisition & Validation

**Objective:** Obtain and verify official immutable Rossmann inputs.
**Dependencies:** Phase 0 and authorized Kaggle access.
**Deliverables:** Acquisition/validation commands and snapshot evidence.
**Acceptance / boundary:** Source hashes, schemas, keys, coverage, missingness and warnings are
recorded; no raw mutation, unsupported correction, model or inventory work.
Full-source quality inspection is descriptive evidence, not forecasting validation.

## Phase 2 — Data Preparation & EDA

**Objective:** Preserve source meaning and document supported descriptive findings.
**Dependencies:** Phase 1 validated snapshot.
**Deliverables:** Separate joined train/test Parquet, reusable summaries, thin notebooks and EDA.
**Acceptance / boundary:** Many-to-one joins preserve rows/keys/nulls; absent dates remain absent,
valid spikes are retained, and associations are not causal effects. Historical full-source EDA
exposure is disclosed; model-facing statistics must later be recomputed from origin training data.

## Phase 3 — Feature Engineering

**Objective:** Provide forecast-origin-safe reusable predictors.
**Dependencies:** Phase 2 prepared data and approved feature definitions.
**Deliverables:** Frozen `phase-3-v1` 29-predictor schema, exact-calendar history API, audits/tests.
**Acceptance / boundary:** Shared ordered train/inference schema, complete lag/windows, no future
Customers, gap fill, target leakage, model-specific encoding or holdout-based feature selection.
[FEATURE_CONTRACT](FEATURE_CONTRACT.md) owns field semantics; later model adapters do not silently
rewrite the artifact contract.

## Phase 4 — Seasonal Naive Baseline

**Objective:** Establish the weekly, recursive 14-day benchmark.
**Dependencies:** Phase 2 history, shared keys and approved development windows.
**Deliverables:** Reusable forecasts/evaluation, coverage and MAE/RMSE/MAPE/WAPE evidence.
**Acceptance / boundary:** ADR-013 exact-date raw recursion, unavailable-history rules and
post-forecast Open routing are enforced. Evaluate observed open labels on development only;
no future actuals, fallback, holdout or final selection.

## Phase 5 — Statistical Forecasting

**Objective:** Evaluate fixed additive Holt-Winters against the benchmark.
**Dependencies:** Phase 4 and approved ADR-014.
**Deliverables:** Origin-censored fits, forecasts/diagnostics, coverage and identical-row comparison.
**Acceptance / boundary:** Fixed specification, >=28 contiguous-day minimum, complete recent
segment, clipped raw values, explicit failures/no fallback, same windows/metrics, and 99%
open-label availability guardrail. Final selection and holdout scoring are later work.

## Phase 6 — Global LightGBM

**Objective:** Implement one global recursive ML candidate.
**Dependencies:** Reviewed/closed Phase 5, Phase 3 contract, reviewed baselines and shared metrics.
**Deliverables:** Approved concise model plan, model adapter/training, 14-step recursive predictor,
fixture tests, development forecasts, reproducible configuration/manifest.
**Acceptance / boundary:** Follow the handoff below; use a finite predeclared tuning budget, fixed
seeds and chronological development evidence. Every recursive step is reproducible. No alternative
model, new feature schema, inventory input, final selection or holdout outcome access is implicit.

## Phase 7 — Walk-Forward Validation & Model Selection

**Objective:** Choose the simplest model whose additional complexity has defensible value.
**Dependencies:** Phases 4–6 and stable metrics/configurations.
**Deliverables:** Development-only paired model comparison, coverage/segment/horizon diagnostics,
selected-method and refit recipe, configuration freeze.
**Acceptance / boundary:** Use the three approved windows and identical-row comparisons while also
reporting standalone coverage. MAE is primary; include RMSE/MAPE/WAPE, compute/operational costs,
window stability and limitations. Retaining Seasonal Naive is a valid outcome. Do not force a
winner or inspect final holdout outcomes.
The 42-day late-season evidence and shared Friday origins limit annual/weekday generalization;
horizon and weekday are confounded. Any supplementary earlier origins require a precommitted
reviewed protocol used consistently for all candidates, not opportunistic window selection.

## Phase 8 — Forecast Uncertainty

**Objective:** Quantify daily and cumulative uncertainty for the selected fixed method.
**Dependencies:** Phase 7 development out-of-sample forecasts/residuals.
**Status:** COMPLETE following verified PR #15/#16 integration, accepted results review and
explicit closeout on 2026-10-07. See the [completed Phase 8 plan](../plans/completed/phase-8-forecast-uncertainty.md).
**Design:** [Phase 8 uncertainty plan](../plans/completed/phase-8-forecast-uncertainty.md),
approved in ADR-021 and integrated by PR #14. PR #15 implemented the unchanged approved protocol
from saved Phase 7 development artifacts and was merged at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`.
External numerical review accepted the canonical results; Fit B values are frozen for that exact
run, with identities in [PROGRESS](PROGRESS.md). The selected point model remains unchanged.
**Deliverables:** Horizon-specific 95% intervals, cumulative lead/protection-period quantiles,
chronological coverage diagnostics and explicit sample/availability counts.
**Acceptance / boundary:** Calibrate on earlier development residuals and assess on later origins
not used for that calibration; fitting-set coverage is diagnostic only. Selection-related
development assessment is not an independent final test. Preserve complete Store-origin residual
paths for cumulative errors, including the explicitly conditional saved-Open development replay;
never sum marginal daily upper bounds or assume independent errors silently. Pooled empirical
intervals promise neither per-store coverage nor conformal guarantees. The external implementation/
results review is accepted and Fit B values are frozen only for the identified canonical run;
PROGRESS records the hashes and observed coverage, including raw Fit B coverage below nominal 95%.
Final-holdout actual Open cannot serve as a planned schedule before issuance; operational outputs
requiring future Open remain unavailable without separately reviewed origin-known schedule
provenance or a separately approved synthetic/conditional schedule not derived from protected
actual Open. Cumulative results support origin-anchored prefixes only; no Phase 10 suffix
calibration is authorized here. No final-holdout evaluation is authorized. Phase 8 is COMPLETE
for the accepted canonical development run. Phase 9's proposed design and Phase 10's future
design require separate authorization; neither implementation is started.

## Phase 9 — Synthetic Supply-Chain / Inventory Layer

**Objective:** Provide reproducible operational scenarios absent from Rossmann.
**Status:** Design PROPOSED / AWAITING APPROVAL; implementation not started.
**Design:** [Active Phase 9 plan](../plans/active/phase-9-synthetic-inventory.md) and proposed
ADR-022. The design branch starts from PR #17's integrated Phase 8 closeout at
`f08a62aa980d0670186ed25ae1f6e5a018ff3781`; approval is required before code.
**Dependencies:** Phase 2 origin-censored development history, dictionary, ADR-016 units and
read-only Phase 7/8 lineage.
**Deliverables:** Fixed-seed scenario generator, assumptions/range/relationship checks, stress data.
The proposed contract specifies 56-day open-turnover anchors, synthetic stock/cost/lead-time
parameters, separately labelled historical references and artificial stress paths, immutable
artifacts and fixture/numerical criteria. These are future deliverables, not generated results.
**Acceptance / boundary:** Initialization uses only history at the June 5/June 19 development
origins; no protected final-holdout read, new forecast, calibration or frozen-artifact mutation.
Synthetic discount/lead-time/stock/costs stay outside the real Rossmann model feature matrix;
synthetic demand stress tests are separate from forecasting accuracy on real Sales.
No physical units, observed inventory, latent-demand correction or real-stockout inference.
Phase 9 supplies exogenous inputs and provenance to Phase 10; event order, queue, policy
comparisons and inventory KPIs are excluded. Phase 8 quantiles remain origin-prefix-only;
synthetic-regime transport and later daily-review suffix calibration are not approved here.

## Phase 10 — Inventory Simulation & Sensitivity Analysis

**Objective:** Compare simple replenishment policies under stated assumptions.
**Status:** PLANNED; not started or approved by the Phase 9 design.
**Dependencies:** Phases 8–9 and development-only forecasts.
**Deliverables:** Stateful order/receipt/stock ledger, policy/KPI comparison, sensitivity report.
**Acceptance / boundary:** Use retail-equivalent values consistently; distinguish lead-time ROP
from the daily-review order-up-to target for protection period L+R <=14. Freeze receipt/demand/
review timing, lost-sales treatment, order queue, terminal censoring and cost conventions before
comparison. Use common demand paths, starting conditions and seeds across policies. Report cycle
service, value fill rate, positive-demand stockout denominator, average inventory, simulated
holding cost and unmet-turnover proxy. Unknown/incomplete forecast paths do not become zeros.
Sensitivity varies lead time, service target, costs and starting inventory; conclusions remain
conditional, with no actual Rossmann stockout/savings or mathematical-optimality claim.

## Phase 11 — Application Services & Thin API

**Objective:** Expose the frozen analytics through reusable Python services and a small HTTP adapter.
**Dependencies:** Phases 7–10.
**Deliverables:** Forecast/uncertainty/inventory service functions, thin FastAPI request/response
adapter, input/error tests and local startup instructions.
**Acceptance / boundary:** No notebook dependency, duplicated model logic or microservice system.
Cache only with keys containing origin/configuration/scenario identity. Separate API hosting is
optional; service/API implementation does not authorize new model/policy tuning.

## Phase 12 — Streamlit Dashboard

**Objective:** Provide an understandable course demonstration.
**Dependencies:** Phase 11 shared services; it need not call FastAPI over HTTP.
**Deliverables:** Store/scenario controls, history/forecast/interval views, inventory assumptions and
alerts; one deployed Streamlit demonstration when deployment is authorized.
**Acceptance / boundary:** UI claims match supported inputs and clearly label synthetic quantities,
unknown future Open and empirical interval limitations. A 7-day view is a subset of the 14-day
path; 28-day capability requires separate design/evaluation. SHAP is optional if ordinary feature
importance and limitations suffice.

## Phase 13 — Monitoring & Sequential Final Evaluation

**Objective:** Evaluate the frozen system once and demonstrate historical monitoring.
**Dependencies:** Phases 7–12 frozen choices and explicit authorization to release holdout labels.
**Deliverables:** Auditable forecast-before-reveal ledger, final point/interval/KPI summaries,
simple drift/error/coverage alerts and protocol/environment identity.
**Acceptance / boundary:** Primary point evaluation has two non-overlapping 14-day blocks:
origin 2015-07-03 for July 4–17, then origin 2015-07-17 for July 18–31. Issue each block's
forecasts before revealing its targets; reveal observations daily. The second origin may use only
already revealed history with the precommitted refitting recipe. Configuration/calibration/policy
changes and adaptive retraining are prohibited during the final test; triggers create alerts.
Scheduled model/preprocessing refits may update fitted state only as required by that fixed
recipe, on eligible already revealed training rows; no interval recalibration or recipe selection.
For daily inventory decisions, precommit any additional operational origins/protection horizons,
issue forecasts before each day's reveal, and score only decisions with complete supported
protection-period coverage. Apply and report the same terminal censoring across policies; do not
invent future demand/covariates or count overlapping operational forecasts as extra independent
primary tests. Development replay tests the protocol before the holdout is released.
This is one sequential final evaluation, not a second unseen dataset after earlier holdout scoring.
Simple pandas summaries/plots suffice; Evidently is optional only for a demonstrated unmet need.

## Phase 14 — Final Documentation, Report & Demo

**Objective:** Deliver reproducible, evidence-based course outputs.
**Dependencies:** Reviewed preceding milestones and the frozen Phase 13 result.
**Deliverables:** Repository, dictionary, report PDF, slides, demonstration and consolidated results.
**Acceptance / boundary:** Report the recorded final evaluation; no new tuning or repeated selection
on holdout outcomes. State historical descriptive exposure, short evaluation span, simulation
assumptions and negative results honestly. Deployment is a course demonstration, not a live
Rossmann production claim.

## Phase 6 implementation handoff (historical)

Phase 6 is complete under accepted ADR-019 and was integrated into `main` by PR #10. This section
records the repository interfaces and boundary used for that implementation; the
[completed Phase 6 plan](../plans/completed/phase-6-global-lightgbm.md) records its execution and
formal closeout. Phase 7 owns later model selection and awaits separate design approval.

| Need | Source / interface |
|---|---|
| Current readiness | [PROGRESS](PROGRESS.md), Git/merged PRs and completed Phase 5 plan |
| Predictor order/roles | [FEATURE_CONTRACT](FEATURE_CONTRACT.md), [contract.py](../src/rossmann_forecasting/features/contract.py) `PREDICTOR_COLUMNS` |
| Prepared inputs | `data/interim/train.parquet`, Phase 2 manifest; [preparation.py](../src/rossmann_forecasting/data/preparation.py) |
| Static and dynamic assembly | [pipeline.py](../src/rossmann_forecasting/features/pipeline.py) `build_inference_features`; [history.py](../src/rossmann_forecasting/features/history.py) `build_origin_history_features` |
| Origins/firewall | [validation.py](../src/rossmann_forecasting/forecasting/validation.py) `APPROVED_DEVELOPMENT_WINDOWS`, `LAST_DEVELOPMENT_DATE`; ADR-013 |
| Metrics | [metrics.py](../src/rossmann_forecasting/forecasting/metrics.py) `summarize_forecast_metrics(..., forecast_column=...)` |
| Baselines | [seasonal_naive.py](../src/rossmann_forecasting/forecasting/seasonal_naive.py), [holt_winters.py](../src/rossmann_forecasting/forecasting/holt_winters.py); recompute on identical keys |
| Artifacts | Planned `data/processed/lightgbm/`; model binaries `artifacts/lightgbm/`, both ignored; manifests per WORKFLOW |
| Validation examples | [feature tests](../tests/test_feature_engineering.py), [baseline tests](../tests/test_seasonal_naive.py), [statistical tests](../tests/test_holt_winters.py), [metric tests](../tests/test_forecasting_metrics.py) |

At each origin, filter labeled fitting/history inputs through that origin (and development through
2015-07-03). Future-dated target covariates are allowed only under the declared origin-time
availability assumption. Fit labels on `training_label_eligible` / source Open=1; keep all observed
pre-origin Sales, including closed-day zeros, as history. Select exactly the frozen predictors; fit category
vocabularies/any learned preprocessing on training only and treat Store categorically.
`features_train.parquet` is a historical fitting artifact, not teacher-forced recursive validation
input. Default `features_inference.parquet` has origin July 31 and Kaggle target dates; it is not
development inference. Build each validation horizon from origin-censored actuals and earlier
predictions with the shared APIs. Missing dates/covariates cannot be manufactured from labels.

The initial recursive history uses non-negative clipped raw predictions; generate the raw path
without future Open/Customers/target labels, then apply known planned Open only to separate
operational routing. Unknown Open remains unresolved. This preserves the reviewed raw comparison
boundary; closed actual zeros versus raw recursive values can cause training/inference mismatch,
which must be reported in development horizon diagnostics. Closure-aware feedback or direct
multi-horizon forecasting is a separately reviewed extension, justified by development evidence.

The Phase 6 plan fixed the following before implementation: categorical/nullable adapter;
loss/objective and negative handling; recursive state and unavailable-path policy; future-covariate availability
assumptions; finite tuning budget/seed; chronological early stopping (inner training split or
approved origin evaluation); coverage/paired-comparison protocol and artifact manifest.
No shuffled split, full-history volume cohort, future Customers, Open_resolved routing, broad
model search or final-holdout-based decision is allowed.

The required behavioral evidence included target Sales/Open mutation invariance of raw forecasts,
origin rejection and h>1 recursion without teacher forcing, key/schema/category/null consistency,
missing-date/covariate behavior, raw/operational separation, coverage and identical-row metrics,
input non-mutation and ignored/provenance outputs. Run fixture/whole-repository checks and an
approved real-data development runner. PROGRESS and the completed execution plan record the
outcome. Phase 7 owns final selection under a separate approved design; no Phase 7 design or
implementation has started.
