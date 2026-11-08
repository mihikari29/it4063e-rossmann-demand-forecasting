---
title: Rossmann Sales Forecasting
subtitle: Simulated inventory decision support
author: IT4063E project team
date: November 8, 2026 - submission draft
aspectratio: 169
---

# Business problem

- Forecast Store x Date monetary Sales over 14 calendar days
- Compare inventory-value policies under explicit simulated operating assumptions
- Rossmann supplies no observed SKU demand or inventory

::: notes
Source: docs/PROPOSAL.md, docs/DATA_DICTIONARY.md. Explain why turnover cannot identify physical
quantities, latent demand or stockouts. This is an AI-assisted submission draft requiring team
review. The team must own the explanation; the author list does not imply exclusively manual code.
:::

# Data and information boundaries

- 1,017,209 historical rows; 1,115 Stores; 41,088 separate test-covariate rows
- Development labels stop July 3, 2015
- July 4-31 final evaluation remains gated
- Earlier descriptive holdout exposure is disclosed

::: notes
Sources: docs/DATA_VALIDATION.md, docs/EDA_FINDINGS.md, docs/DECISIONS.md ADR-015.
These counts are retained documented evidence, not rerun measurements. Distinguish full-source
historical descriptive analysis from development model selection. Never claim unseen final data.
:::

# Pipeline architecture

Source validation and sparse preparation

Origin-safe 29 predictors -> chronological forecasting -> frozen uncertainty

Synthetic contexts -> paired inventory-value simulation

Saved artifacts -> read-only API / Streamlit -> descriptive monitoring

::: notes
Sources: docs/FEATURE_CONTRACT.md, docs/DECISIONS.md and docs/LOCAL_DEMO_DEPLOYMENT.md.
This is an editable text process diagram. The dashboard calls shared Python services directly.
Monitoring joins labels after issuance; it cannot generate forecasts from target outcomes.
:::

# EDA and cleaning

- 180 Stores share a 184-day gap; absent dates remain absent
- Structural Promo2 schedule nulls remain distinguishable
- 54 open/zero-Sales rows and valid spikes are retained
- Historical lag-7 ACF indicates heterogeneous weekly structure
- Rossmann STL: BLOCKED pending authorized development input

::: notes
Sources: docs/EDA_FINDINGS.md; docs/DATA_VALIDATION.md.
The gap contains 33,120 absent Store-days. Historical ACF diagnostics on uninterrupted segments
report lag-7 correlations approximately 0.27-0.75; this is not decomposition. Validation recorded
zero errors/four warnings. Historical rows remain 1,017,209 before/after preparation, all 54
open/zero rows remain, and all 11 test Open nulls remain. These are transcribed historical findings
including the disclosed full period. Promotion associations are not causal effects. Reserve the
STL result for authorized Rossmann components/PNGs and a reviewed interpretation; none exists here.
:::

# Point-in-time features

- 29 predictors: Store/calendar, holidays/promotions and static metadata
- Exact-date lags: 1 / 7 / 14 / 28 days
- Complete rolling means and sample standard deviations
- Recursive history: origin actuals plus earlier predictions
- Customers excluded; source Open stays outside predictors

::: notes
Source: docs/FEATURE_CONTRACT.md. There are exactly 29 ordered predictors. Missing exact dates
give null. Precomputed historical lag rows can leak future actuals in recursive evaluation.
Future-known availability is an explicit assumption, not a property proved by a later snapshot.
:::

# Chronological model comparison

| Candidate | Development MAE |
|---|---:|
| Seasonal Naive | 1681.2703 |
| Additive Holt-Winters | 1281.7446 |
| Global LightGBM | 871.0612 |

MAE: turnover units; n=38,553 Open=1; 3 H14 windows; availability 100%

::: notes
Source: docs/PROGRESS.md. Origins May22, June5, June19; no shuffled split. MAE is primary, RMSE,
cautious MAPE and WAPE supplementary. The native table should remain editable after PPTX export.
These are development metrics and were not regenerated in the correction task.
The PDF preserves all supplementary scores: Seasonal Naive RMSE 2416.9677, MAPE 26.2671%,
WAPE .232748; Holt-Winters 1708.3073, 18.3669%, .177439; LightGBM 1350.9138, 11.3531%,
.120586. MAPE uses all 38,553 positive actuals; WAPE is a ratio. No final-test score exists.
:::

# Frozen LightGBM selection

- 48.1903% pooled MAE improvement over Seasonal Naive
- Fixed CPU regression L1, 15 leaves, depth 4, 180 rounds
- Weaker h2 / h9 / h10 results remain visible
- A selected recipe does not establish final holdout performance

::: notes
Sources: docs/PROGRESS.md and docs/DECISIONS.md ADR-019/020. Learning rate .05 and minimum leaf
data 200 also remain fixed. Selection heuristics followed initial results; no significance or
preregistration claim. No per-horizon replacement or final-test adaptation is introduced.
:::

# Uncertainty and availability

- Daily intervals are marginal empirical horizon-specific estimates
- Fit A: 84.39% coverage among 12,258 usable intervals
- Fit B: 91.26% among 13,437 usable intervals
- Cumulative prefix bounds are separate from daily intervals
- Sparse support and July transport limit interpretation

::: notes
Source: docs/PROGRESS.md and ADR-021/026. Fit A eligible denominator is 13,438, so availability is
91.22%; Fit B availability 100%. Fit A h2/h3/h9 are unavailable. Closure [0,0] routes inflate
pooled operational coverage. Do not sum daily interval endpoints or promise service guarantees.
:::

# Inventory simulation findings

| Synthetic base policy | Holding + shortfall cost proxy |
|---|---:|
| Historical mean | 90.787 million |
| Forecast driven | 113.929 million |

Forecast policy cost increases by 23.143 million cost-proxy units

::: notes
Source: docs/PROGRESS.md and completed Phase10 specification. Table rounds retained values.
The conditional historical replay also deteriorates. Distinguish retail-equivalent stock values
from cost-proxy units; no currency conversion, real savings or optimal-policy claim. Explain cold
start, standing targets, terminal pipeline and receipt-cycle censoring.
:::

# Decision-support interpretation

- Lower forecast MAE does not guarantee lower simulated policy cost
- Artificial cost rates and uncertainty transport influence decisions
- Short H14 episodes cannot establish long-run optimality
- Conditional historical replay also has higher simulated costs

::: notes
Sources: docs/DECISIONS.md ADR-023/025/026; plans/completed/phase-10-inventory-simulation.md.
No continuous rolling 28-day procurement is implemented. Retain the adverse result and request
approved assumption/policy investigation before recommending real operational adoption.
The conditional historical cost increase is 4,276,098.731339 cost-proxy units. The synthetic-base
increase is 23,142,547.537968. These are retained development simulation results. The final design's
two independent origin-frozen episodes remain unexecuted; they are not evidence on this slide.
:::

# API and dashboard demonstration

- Linux staging: actual FastAPI and Streamlit Python services
- HTTP/WebSocket, restart and failure checks passed
- Shared pinned synthetic bundle; model_execution=none
- Saved fixture paths do not demonstrate trained-LightGBM deployment
- Public API/dashboard URLs: PENDING; external acceptance NOT RUN

::: notes
Sources: docs/LOCAL_DEMO_DEPLOYMENT.md; WP-04 staging evidence.
See outputs/validation/wp04-staging-20261108-v1/evidence_manifest.json, linux/linux-report.json
and targeted-tests.xml. Fresh Linux Python 3.12.15/uv .12.23 setup passed with locked extras and
reused download caches. Seven routes were checked, totaling 19 expected 200, two 422 and seven 503
responses; 15 live WebSocket renders covered saved-service/monitoring/restart/error states.
The targeted fixture suite passed 362 tests, with one Windows symlink skip and one existing warning.
At 512 MiB/0.1 CPU per service, API catalog readiness was 22.49s; UI health 8.82s; peak RSS
136.08/233.23 MiB with no OOM in one sequential session. This is not a cloud concurrency guarantee.
All services were stopped. Missing bundle/wrong pin fail closed. No actual browser pixel/human
visual acceptance or public deployment occurred. The old HF Space remains static with API 404.
The course entrypoint is scripts/run_demo.py course-dashboard; Streamlit calls Python services.
:::

# Corrected monitoring

Issued forecasts -> available labels -> validated pairs -> descriptive summaries

- Rolling 7/14-day MAE/MAPE; Store, origin and horizon views
- Synthetic baseline: 36 eligible pairs; MAE 250; MAPE 3.79%
- Missing evidence stays partial/unavailable; coverage needs a roster
- PROPOSED: WAPE >1.20x reference; availability <99%; no automatic engine

::: notes
Sources: docs/MONITORING.md; WP-03 synthetic monitoring evidence.
See reports/generated/monitoring/wp03-fixture-20261108-v1/monitoring_summary.json and manifest.json;
tests/test_monitoring.py; proposal section 24.2. Predictions use Store/calendar independently of
labels. Reference June6-19 and current June20-July3 each have 42 keys, 36 eligible Open=1 pairs
and six closed labels across three synthetic Stores. MAPE is percent; WAPE is .0380113, a ratio.
The final trailing 7-day window has 21 requested/18 eligible pairs; the 14-day window has 42/36.
Missingness and all-zero denominators remain explicit. DESCRIPTIVE_ONLY is not Healthy.
PROPOSED rules also include category-frequency shift >=10 percentage points, late labels after an
approved deadline, and immediate integrity review. Pooled performance/feature/availability decisions
require >=10 observed dates, 100 Stores and 1,000 pairs per complete 14-day window/reference;
the three-Store fixture is INSUFFICIENT EVIDENCE. Two supported non-overlapping warnings prompt
human review; missing evidence breaks persistence. No numeric engine, persistence, production
monitoring or automatic retraining is implemented. Investigate quality first, then obtain separate
approval for any retraining experiment. An external expected roster is needed to detect lost keys.
:::

# Limitations and pending gates

- Monetary targets, sparse labels and synthetic operating assumptions
- Rossmann STL and genuine Store-level scenario evidence: PENDING
- Frozen final evaluation: NOT RUN; safeguards remain
- Public URLs, human review and academic ownership: PENDING
- Development-only submission scope requires instructor confirmation

::: notes
Sources: docs/PROJECT_PLAN.md, docs/SUBMISSION_READINESS.md and active plans. Explain which
implementation is tested and which evidence is absent. Independent AI review does not establish
human approval. Do not call the course project 100% complete or submission accepted.
The course announcement requires code authored by team members. This draft and prior code/test
work used AI assistance; no instructor waiver/AI-coding permission has been verified. Team review
does not establish exclusive human authorship. Confirm the roster, student IDs, actual member
contributions, policy-compliant disclosure and any required rewriting with the instructor.
:::

# Conclusions

- LightGBM leads reviewed development comparison; no final-test score
- Lower forecast error did not reduce simulated inventory cost
- Synthetic staging and monitoring demonstrate software behavior
- Submission draft for team review; scope and public acceptance pending

::: notes
Sources: docs/PROGRESS.md, reports/submission_report.md. Rehearse explaining why scientific
honesty is more useful than forcing a positive savings narrative. This editable presentation
source uses the available evidence. Confirm all claims and actual member contributions before
submission. STL figures and public URLs remain pending. Instructor acceptance of development-only
scope is separate from technical review; frozen final evaluation is neither complete nor waived.
:::
