---
title: Rossmann Sales Forecasting
subtitle: Simulated inventory decision support
author: IT4063E project team
date: November 6, 2026 - submission draft
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
- Promotion associations do not establish causal effects

::: notes
Source: docs/EDA_FINDINGS.md. The gap contains 33,120 absent Store-days. These are historical
descriptive findings including the disclosed full period. Real weekly STL execution remains
pending safe inputs and permission; no synthetic STL result is presented as Rossmann evidence.
:::

# Point-in-time features

- Calendar, planned promotions and static Store metadata
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

38,553 common observed Open=1 labels; three H14 windows; 100% availability

::: notes
Source: docs/PROGRESS.md. Origins May22, June5, June19; no shuffled split. MAE is primary, RMSE,
cautious MAPE and WAPE supplementary. The native table should remain editable after PPTX export.
These are development metrics and were not regenerated in the correction task.
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
- Final design retains two independent origin-frozen episodes

::: notes
Sources: docs/DECISIONS.md ADR-023/025/026; plans/completed/phase-10-inventory-simulation.md.
No continuous rolling 28-day procurement is implemented. Retain the adverse result and request
approved assumption/policy investigation before recommending real operational adoption.
:::

# API and dashboard demonstration

- Actual local HTTP API and separate Streamlit dashboard
- Shared immutable bundle and explicit synthetic provenance
- Health reports liveness; catalog reports bundle/view readiness
- Public API/dashboard release remains pending

::: notes
Source: docs/LOCAL_DEMO_DEPLOYMENT.md. Demonstrate only authorized local fixtures using
scripts/run_demo.py api and dashboard. API 127.0.0.1:8000, UI 127.0.0.1:8501 while running.
Store/origin/case/interval controls use real Python services. The historical HF Space is static,
not FastAPI evidence. Do not show illustrative fixtures as genuine LightGBM inference.
:::

# Corrected monitoring

Issued forecasts -> available labels -> validated pairs -> descriptive summaries

- Daily and trailing 7 / 14 calendar days
- Store, origin and horizon strata; coverage and zero-denominator rules
- Declared origin-known feature quartiles and frequencies
- No numeric alarm, fake KS test or automatic retraining

::: notes
Source: docs/MONITORING.md and notebooks/03_model_monitoring.ipynb. The fixture predictor uses
Store/calendar independently of labels. JSON/HTML/chart/notebook share calculation logic and
status semantics. No new real production observations exist. Broader numeric thresholds and
persistence require separate design approval and a development rehearsal.
:::

# Limitations and pending gates

- Monetary targets, sparse Sundays and dependent Stores/date shocks
- Unvalidated uncertainty transport and synthetic operating assumptions
- Real scenario / STL / protected final evidence pending
- Exact-content security and owner public-release approval pending
- Human review, AI disclosure and academic ownership required

::: notes
Sources: docs/PROJECT_PLAN.md, docs/SUBMISSION_READINESS.md and active plans. Explain which
implementation is tested and which evidence is absent. Independent AI review does not establish
human approval. Do not call the course project 100% complete or submission accepted.
:::

# Conclusions

- Frozen LightGBM leads the accepted development comparison
- Inventory simulation provides an adverse business finding
- Corrected interfaces preserve provenance and unavailable evidence
- Final conclusions require the remaining authorized evaluation and team review

::: notes
Sources: docs/PROGRESS.md, reports/submission_report.md. Rehearse explaining why scientific
honesty is more useful than forcing a positive savings narrative. This editable presentation
source is complete for the available evidence; a PPTX is not claimed unless actually exported
and inspected. Questions about final results must be answered as pending, never estimated.
:::
