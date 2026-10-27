# Architecture and Methodology Decisions

These records explain accepted choices, rationale and boundaries. Stable decision headings support
existing references; prose uses descriptive links. Proposed work has no authority until accepted.
Method changes require an explicit superseding decision. Current implementation and results live
in [Progress](PROGRESS.md), rather than approval histories or build logs here.

## ADR-001 — Forecast Granularity

**Accepted.** Forecast at Store × Date, the finest supported granularity. Preserve store-day
keys in features, forecasts, metrics and application views.

## ADR-002 — Forecast Target

**Accepted.** Use `Sales` as daily monetary turnover. It is a demand proxy affected by price,
mix and potentially unmet demand, without identifying unconstrained physical demand.

## ADR-003 — No SKU-Level Forecasting

**Accepted.** Rossmann has neither SKU identifiers nor quantities. Do not claim SKU forecasts
or procurement. Equivalent units may be displayed only under a declared synthetic unit-value assumption.

## ADR-004 — Primary Forecast Horizon

**Accepted.** Compare models over 14 calendar days. A seven-day view is a subset; 28-step
forecasting needs a separate reviewed design. A 28-day final period does not imply 28-step support.

## ADR-005 — Synthetic Operational Layer

**Accepted.** Keep simulated supply-chain/stock/cost inputs separate from observed data.
Document ranges, dependencies and seeds; business conclusions are conditional on these assumptions.

## ADR-006 — Forecasting Baseline

**Accepted.** Use weekly Seasonal Naive as the transparent baseline. Advanced candidates must
justify complexity on identical chronological windows and eligible rows.

## ADR-007 — Main Machine-Learning Strategy

**Accepted.** Use one global LightGBM across stores to share information and avoid 1,115
separate ML models. The later development-selection decision fixes the chosen recipe.

## ADR-008 — Validation Strategy

**Accepted; clarified by the final-release decision below.** Use walk-forward evaluation,
never shuffled splits. Reserve July 4–31 for final forecasting evaluation, excluding it from
selection. Earlier full-source descriptive exposure means the labels are not pristine unseen data.

## ADR-009 — Spark Is Optional

**Accepted.** Spark is optional. The dataset is manageable locally; distributed ETL must not
block course delivery or add dependencies without a concrete implemented need.

## ADR-010 - Python Environment and Packaging

**Accepted, with environment policy superseded by the portable-lock decision below.**
Use a standard `src/` package and `pyproject.toml` as the only hand-maintained source for metadata,
dependencies, entrypoints and quality configuration. Generate `uv.lock`; do not duplicate requirements.

## ADR-011 - Official, Immutable Raw Data

**Accepted.** Acquire official Kaggle inputs atomically into ignored `data/raw/rossmann/`;
refuse overwrite, validate read-only and retain immutable source identities. Contributors need
authorized competition access. Source refresh and any mixed-source read/hash require their own scope.

## ADR-012 - Phase 3 Point-in-Time Feature Contract

**Accepted; version `phase-3-v1`.** The [feature contract](FEATURE_CONTRACT.md) fixes 29 ordered
predictors and shared train/inference dtypes. Store remains an unchanged key and categorical input;
Date is key-only; Sales is label/history; Customers and Open-derived audit fields are excluded.
Use exact-calendar lags, complete trailing windows and actuals censored at origin plus earlier
predictions from that same run. Missing dates stay missing. Competition age uses month precision;
invalid/missing metadata is not imputed. Learned categories are fit-only adapter state.

## ADR-013 - Phase 4 Seasonal Naive Evaluation Contract

**Accepted.** Use exactly these development windows:

| Window | Origin | Target dates |
|---|---|---|
| `validation_1` | 2015-05-22 | 2015-05-23–2015-06-05 |
| `validation_2` | 2015-06-05 | 2015-06-06–2015-06-19 |
| `validation_3` | 2015-06-19 | 2015-06-20–2015-07-03 |

Seasonal Naive uses exact same-Store d−7 actuals at h1–7 and earlier raw predictions at h8–14.
Missing exact history is unavailable, without prior-row substitution, interpolation or zero fill.
Build internal states for all 14 horizons for stores with observed targets; emit/evaluate only
source-observed target keys. Attach Sales/Open labels after raw generation. Known Open=0 routes
operational output to zero, Open=1 retains raw, unknown stays unresolved; `Open_resolved` is audit-only.

Primary metrics use available raw forecasts on observed Open=1 rows with Sales. MAE is primary;
RMSE, cautious MAPE and WAPE supplement it. MAPE alone excludes zero actuals, without epsilon,
and reports exclusions/coverage. Zero-total WAPE is unavailable with a reason. Report window,
pooled-row and horizon metrics plus explicit availability numerators/denominators. No teacher forcing.
The implementation in [validation](../src/rossmann_forecasting/forecasting/validation.py) and
[metrics](../src/rossmann_forecasting/forecasting/metrics.py) owns the executable contract.

## ADR-014 - Phase 5 Holt-Winters Statistical Forecasting Contract

**Accepted.** Fit one statsmodels `ExponentialSmoothing` per Store/origin with additive trend,
undamped additive weekly seasonality (`seasonal_periods=7`), estimated initialization,
`use_boxcox=False` and optimized smoothing parameters. Use `statsmodels>=0.15,<0.16`.
The current Python range is defined by the portable-lock decision below.

Use the entire most recent contiguous observed daily Sales segment ending at origin, requiring
at least 28 days and retaining observed closed-day zeros. Do not compress dates or fill gaps.
Missing origin, short history, model/forecast exceptions, wrong-length or nonfinite output makes
the fit unavailable, without fallback. Public horizons are 1–14; development requests 14.
Retain unclipped values and diagnostics, clip raw at zero, then apply separate Open routing.

Use the shared windows/metrics, report standalone coverage and compare Seasonal Naive on identical
eligible available rows. Require at least 99% open-label availability in every window before
superiority/inferiority interpretation; otherwise flag review and suppress those claims. Record
warning, convergence, clipping and failure counts. The structure is fixed, without validation tuning.

## ADR-015 — Final Evaluation Release and Historical Exposure

**Accepted.** Development label reads filter Date ≤ 2015-07-03 before modeling/evaluation;
every fit/history input also stops at its origin. Protect July 4–31 from tuning, feature/cohort
selection, learned preprocessing, calibration and policy/monitoring decisions.

After a separately approved frozen protocol, final evaluation may issue two H14 blocks at July 3
and July 17, persist each complete issuance before revealing its outcomes chronologically, and
use only already released history for the scheduled second refit. Freeze the recipe, uncertainty,
policies/scenarios and monitoring rules; never adapt them to final performance. Phase 14 reports
that sole replay, without a second selection/test. Mixed-source preparation, mechanical staging
and analytical release have distinct approval gates.

Earlier source quality checks and EDA included the eventual holdout; disclose this exposure and
never reuse full-history EDA cohorts as development inputs. No final forecasting metrics have
been produced. The [active protocol](../plans/active/phase-13-sequential-final-evaluation.md)
defines the remaining requirements.

## ADR-016 — Inventory Proxy Values and Cumulative Uncertainty

**Accepted.** Simulated demand, stock, orders and targets use retail-equivalent monetary value
matching turnover. Procurement cost needs an explicit synthetic conversion. Use lost sales, an
outstanding-order queue and common inputs/starting stocks for policy comparison. On-order is
zero only at initialization, not throughout replay.

For R=1 and L=2–7, protection P=L+R lies in 3–8 within H14. On complete origin prefixes use
`E_k=sum(actual-operational_forecast)`, `D_k=sum(operational_forecast)`,
`U_k=max(0,D_k+q_p(E_k))`, `SafetyStock_k=max(0,U_k-D_k)` and `Target_k=max(D_k,U_k)`.
Keep signed q; never sum marginal daily upper endpoints or assume independent errors.
Daily intervals and cumulative bounds have different populations/levels. Incomplete operational
paths remain unavailable; costs/service are conditional proxies, not savings or guaranteed service.

## ADR-017 — Proportionate Application and Forecast Extension Scope

**Accepted, with future delivery scope narrowly extended by the public-demo objective below.**
Keep the three-model ladder and raw recursive feedback: clip finite raw predictions at zero,
complete the raw path, then route operational values with supplied/planned Open. Closed historical
actuals versus raw recursive states remain a disclosed mismatch. Closure-aware feedback, direct
multi-horizon forecasting, extra predictors and models require a separate reviewed design.

Use shared Python services, a thin FastAPI adapter and Streamlit calling services directly.
The original single-dashboard delivery sufficiency is extended only by the later gated two-URL
objective. On-demand inference, HTTP coupling, SHAP, Evidently, Docker and Spark remain optional.

## ADR-018 — Portable Locked Environment and Quality CI

**Accepted.** Support Python >=3.12,<3.15 with 3.14 as reference and py312-compatible syntax.
Use uv 0.12.23, generated universal `uv.lock`, explicit direct dependencies and optional acquisition,
API/dashboard and development extras. CI checks locked fixtures, package consistency, Ruff and local
Markdown links on Python 3.12 and 3.14 without Rossmann data. Lock changes are deliberate and tested;
new manifests record code/environment/lock identity. Historical manifests remain immutable.

This replaces the former single-minor/deferred-lock restriction. Repository protections are a
recommendation, without a claim that hosting settings are enabled; settings changes need authorization.

## ADR-019 — Global Recursive LightGBM Phase 6 Contract

**Accepted.** Train one global CPU GBDT for untransformed monetary Sales using regression L1 and
the 29-predictor schema. Fit labels require source Open=1; all observed pre-origin Sales, including
closed zeros, remain in recursive history. Learn category vocabularies only from fit rows; preserve
native numeric missingness and explicit unseen-category diagnostics. Future Customers/Open are excluded.

Use the fixed four inner-origin trials, coverage gates, ten-round recursive checkpoints and finite
stopping budget in the [LightGBM specification](../plans/completed/phase-6-global-lightgbm.md).
Outer development windows share the approved raw/routing/metric/failure contracts. No fallback,
future actual recursion, inventory input or final-period outcome may influence training/selection.

## ADR-020 — Development-Only Model Selection and Frozen Refit Policy

**Accepted; selection completed.** Compare exactly Seasonal Naive, additive Holt-Winters and
global LightGBM on identical three-way common open-label rows, alongside standalone/pairwise
coverage and supplementary metrics. Require 99% coverage in every window for each candidate and
the common population, with exact key/label/mask/configuration/original-artifact integrity.

Use the simplicity ladder SN → HW → LightGBM. Promotion requires ≥5% pooled MAE improvement,
MAE wins in ≥2/3 windows, no window regression >10% and no pooled h1–7/h8–14 regression >10%.
Ties or failed gates retain the incumbent; failed HW promotion still allows LightGBM versus SN.
These project heuristics were chosen after initial results, not preregistered significance tests.
Report unfavorable individual horizons without adding a later veto. The offline CPU operational
assessment does not prove production latency, throughput or resource needs.

Selected LightGBM uses trial A at exactly 180 rounds, reviewed shared parameters and fit-only
categories. Freeze recipes rather than fitted future state. Preserve original cached provenance,
including legacy SN/HW manifests and the historical modified LightGBM worktree; do not rewrite
manifests or claim current-code regeneration. [Results](PROGRESS.md) records selection evidence.

## ADR-021 — Chronological Empirical Forecast Uncertainty and Conditional Operational Replay

**Accepted; reviewed Fit B fitted values frozen.** Keep the point recipe unchanged. Fit A
calibrates validation_1 and assesses validation_2; Fit B calibrates validation_1+2 and assesses
validation_3. Calibration labels stop at issuance; own-window/later labels are excluded. Do not
refit quantiles on validation_3 to increase support.

Daily signed residuals `actual_sales-raw_forecast` use eligible observed Open=1 individual rows,
including partial paths, pooled equally by exact h1–14. For sorted n residuals use 1-indexed ranks
`floor((n+1)/40)` and `ceil(39*(n+1)/40)`, n≥40 and valid ranks. Retain ties, without interpolation,
clamping, borrowing or fallback. Add signed tails to the nonnegative raw point and independently
clip endpoints at zero; retain pre-clipping values/flags, reject nonfinite/inverted bounds and do
not force the point inside. These nominal 95% intervals are marginal, without conformal,
simultaneous, per-store or guaranteed coverage.

Cumulative operational errors require every valid component h1..k; missing later components do
not invalidate a shorter prefix. Sum in ascending horizon order and pool complete prefixes at
exact k. For p={.90,.95,.98}, use upper rank `ceil((n+1)*p)`, n≥50 and valid rank. Keep signed q
and the monetary formulas above. Never substitute summed daily endpoints or a later-review suffix.

Development operational routing permits `saved_source_open_assumed_known_at_origin` only as a
conditional historical replay, without evidence of historical schedule availability. Known closure
routes to [0,0], unknown stays unavailable. Report Open=1/0/pooled results and closure inflation.
For final issuance actual future Open/Sales/Customers cannot be read/hashed as schedule inputs;
separately approved origin-known or synthetic schedule provenance is required.

Three Friday origins, repeated stores/common shocks, sparse Sunday tails, weak h10 and selection
on all development windows limit inference. Fit A h2/h3/h9 remain unavailable; Fit B h2/h9 have
65/64 rows from 33/32 distinct stores. No significance, confidence, bootstrap or service guarantee
is inferred. Full estimator and diagnostics: [uncertainty specification](../plans/completed/phase-8-forecast-uncertainty.md).

## ADR-022 — Synthetic Monetary Scenario Contract

**Accepted.** Initialize from 56 calendar days through origin, requiring 28 valid observed
Open=1 rows. Retain sparse dates/valid zero anchors, leave unavailable anchors/stock/demand null
without fallback, and start with an empty pipeline. Stock=m×coverage on a retail-equivalent value basis.

Use illustrative c∈[.55,.85), annual a∈[.10,.30), goodwill g∈[.10,.75), holding rate=c*a/365 and
shortfall penalty=(1-c)+g exactly once. Equivalent units are display-only. Use seed 4209, the exact
SHA-256 keyed draws, five paired replicates, eight synthetic families and a historical reference
at June 5 and June 19. Weekly factors Monday–Sunday [.95,.98,1,1.02,1.10,1.15,.80] average one
per calendar week, but 1.033333… per default open day; do not renormalize the formula.

Synthetic stresses remain separate from observed Sales, forecasts and uncertainty. Verify frozen
upstream bindings, preserve immutable publication and unavailable states, and never access protected
outcomes. The [scenario specification](../plans/completed/phase-9-synthetic-inventory.md) fixes
schemas, draw grammar, factors and overrides. Cold starts and artificial distributions limit inference.

## ADR-023 — Origin-Frozen Daily Inventory Policy Simulation and Finite-Window Accounting

**Accepted.** Use independent June 5/Fit A and June 19/Fit B H14 episodes. Freeze exactly two
targets before outcomes: baseline `S=m*sum(planned_open_h,h=1..P)` and forecast
`D_P=sum(operational_points)`, `U_P=max(0,D_P+q_(p,P))`, `S=max(D_P,U_P)`.
Use p=.95 plus .90/.98 sensitivities. Later daily reviews reuse S; there is no forecast refresh,
suffix calibration, uncertainty scaling or refit. The target may become stale.

R=1, integer L=2–7, P=L+1. End-of-day t orders arrive before demand at day t+L+1. At origin
verify/freeze, initialize and order. Days 1–13 receive, reveal consumption, fulfil, record lost
sales, charge costs, calculate position and order; day 14 suppresses new review/orders.
`IP=ending_stock+outstanding_before_new_order`; `Q=max(0,S-IP)`. No backlog or SKU rounding.
Require exact identities/complete prefixes/schedule and finite inputs; unavailability never becomes
a zero, baseline or point-only substitute. Synthetic schedule routing leaves raw points unchanged;
historical q on synthetic stress is explicitly uncalibrated (`calibration_transport_valid=false`).

Primary cost is `sum(h*ending_stock+b*unmet)`. Do not add procurement/lost margin again or call it
profit. Report terminal c×stock and c×pipeline exposure separately. Value fill, positive-demand
stockout rate and completed positive-demand receipt-cycle service have explicit denominators;
cycle service counts complete cycles between two observed positive receipts, with zero-demand and
censored intervals reported. Pool ratios from totals; zero denominator is null. Missing consumption
stops dependent state; incomplete tracks cannot support paired complete comparisons.

Retain all orders placed through day 13 even when due after T; on-T receipts precede consumption.
No cancellation, refund, acceleration, extension or salvage. Compare common inputs/starts and the
full scenario panel plus nine one-factor synthetic-base overlays. The
[inventory specification](../plans/completed/phase-10-inventory-simulation.md) fixes the detailed
accounting. Short episodes, cold starts, endogenous cycles and artificial costs preclude optimality,
actual inventory, savings or service guarantees.

## ADR-024 - Phase 12 Localhost-Only Demonstration Boundary

**Accepted; current runtime boundary.** The dashboard remains at `http://127.0.0.1:8501` with
`server.address="127.0.0.1"`, static serving off, CORS and XSRF protection on. LAN/network-profile,
firewall, forwarding, tunnels and hosting changes require separate authorization. Local acceptance
included automated checks, browser/security/performance checks, user-attested human visual review
and independent review. Automated UI interaction cannot substitute for human visual acceptance.
The later public-demo objective does not itself change this runtime boundary.

## ADR-025 — Phase 13 A-bounded Inventory Evaluation Scope

**Accepted for scope only.** Final inventory evaluation comprises independent H14 episodes at
July 3 and July 17 using the same two origin-frozen policies and finite-window event/terminal
accounting. Retain the full scenario/sensitivity panel subject to measured resource feasibility
and explicit approval. Exceeding budget requires a scope/resource decision, without silent sampling.

This accepts the exception that later daily reviews have no fresh calibrated protection forecast;
unsupported protection coverage cannot be scored as evidence. It is not continuous rolling 28-day
operation. Preserve adverse development results; scope does not select a policy or promise savings.
Method, inputs, schedules, transport, custody, implementation, rehearsal, staging and analytical
release retain separate approvals.

## ADR-026 — Phase 13 Selected Sequential Evaluation Methodology

**Accepted for method selection only.** The [active final-evaluation protocol](../plans/active/phase-13-sequential-final-evaluation.md)
selects these applications of the existing contracts, without authorizing execution:

1. Issue and persist two full H14 blocks before any matching outcomes are revealed. Release dates
   in order with durable intent/checkpoints. The July 17 fresh fit uses only already released history.
2. Use the 1,115-store grid, exact predictors and separately versioned origin-safe covariates.
   Retrospective assumed-known availability remains an assumption. Planned Open is synthetic
   Monday–Saturday open/Sunday closed; keep actual Open and ScenarioOpen distinct. Preserve positive
   actual Sales even when the planned schedule says closed and report mismatches after release.
3. Use logical/operator-enforced custody: separately staged provider views, default-deny paths,
   dates/fields, immutable issuance and append-only journals. Separate Windows identities/ACLs are
   optional. The trusted operator/owner/admin can bypass local checks; no strict isolation claim.
   New partitions require persisted issuance/intent before separately authorized mechanical staging;
   existing partitions require documented authorization/provenance. Analytical release is separate.
4. Apply exact frozen June Fit B unchanged to July fresh fits as **UNVALIDATED transport**. Preserve
   ranks, floors, signed values, clipping, prefix semantics and unavailable reasons. No recalibration.
5. Keep two independent origin-frozen inventory episodes and the approved measured resource gate.
6. Monitor descriptive daily/trailing 7/14-calendar-day views by origin/horizon, including feature
   shifts and post-release errors/coverage. Precommit deterministic integrity/data-quality alerts
   only, without numeric drift/performance/coverage/service alarms or adaptive retraining.
7. Use locked Windows x64/Python 3.14 and exact recipe/configuration/feature/category identities.
   Same-environment booster save/load comparisons use `rtol=1e-12`, `atol=1e-9`; fixture failure
   needs a reviewed tolerance decision before protected results. Measure/approve full-panel resources.
8. Final LightGBM has frozen Seasonal Naive as contextual comparator on standalone/common rows.
   Do not reselect, add candidates or use Holt-Winters as a final comparator.

Real source identity, safe preparation/custody, named operator, partition provenance, resources,
remaining implementation, rehearsal, staging and each analytical release remain pending gates.
A projection/manifest/binding is not access permission. Phase 13 remains PLANNED / NOT APPROVED.

## ADR-027 — CC-02 Development-Only Weekly STL Diagnostic

**Accepted; fixture implementation reviewed/integrated.** Use robust weekly STL (period 7)
on uninterrupted finite daily Sales segments ending by July 3. Require 56 days, choose latest end
then latest start, retain latest 112 rows and analyze first three eligible Store IDs ascending.
Zeros stay; gaps/nonfinite/missing observations split segments without smoothing/interpolation.
Report per-Store availability, component reconstruction and retrospective descriptive figures.

The in-memory API requires authorized Store/Date/Sales. The fixed provider verifies one immutable
development-only bundle against an external binding; it does not authenticate issuer/custody.
The [custodian runbook](CC-02D_CUSTODIAN_RUNBOOK.md) controls future mixed-source preparation:
separately effective source/preparation authorization before any read/hash, independent verification,
external exact-hash binding, then separately approved provider loading, STL and publication.
Reserved pending references grant no permission; immutable manifests are not edited to activate them.
The one-use preparation CLI is default-deny and has no source override; STL CLI stays fail-closed.
No real bundle or Rossmann STL results exist. Trust is operator-enforced, without administrator-proof
isolation. This diagnostic is outside features, selection, inventory and final evaluation.

## ADR-028 — Instructor Feedback Alignment and Public Demonstration

**PROPOSED; broader methods await owner acceptance.** Instructor guidance accepts Store × Date
monetary H14 scope, requests public API/dashboard demonstrations, Store-level comparisons of the
three existing methods, monitoring across data quality/characteristics/performance and supported
simulated business indicators, plus human retraining-review conditions. Precomputed forecasts suffice;
on-demand inference and cross-model inventory simulation are optional.

Proposed scenario definitions, eligible populations, support/comparison/interpretation rules and
broader monitoring triggers require separate accepted designs and development-only evidence.
Automatic retraining is optional, with no adaptive final replay. Instructor preference authorizes
neither hosting purchases nor data/release operations. The later narrow public-demo objective
accepts only its stated delivery direction; the remaining proposal is not accepted wholesale.

## ADR-029 — WP1-L3-F Restricted Trusted-Fixture Contract

**Accepted restricted fixture contract; implementation reviewed/integrated.**
`verify_trusted_scenario_fixture_snapshot` may decode only reviewed project-controlled synthetic
fixture bytes and controlled test mutations. Synthetic origin is a caller precondition that the
verifier cannot authenticate. Hashes, receipts, custody labels and matching bindings prove
consistency, without trust, availability, real-source access or analysis authority.

Byte/JSON/footer/schema/output thresholds remain, but Arrow output is checked after materialization.
Python/native temporaries have no hard peak-memory budget. Malformed fixtures can exhaust memory
or terminate the process. The original untrusted-decoder memory requirement remains unresolved;
the owner accepted residual risk only for restricted fixture testing. Eventual output rejection
is not allocation prevention. No real/untrusted decoder or production ingestion use is approved.

Keep `validate_scenario_input_binding`, exact scientific/key/roster/metadata checks and explicit
limitations. The generic verifier name was removed without alias. A later isolated worker needs a
separate process/security design; a custom Parquet parser was rejected as disproportionate.
Real preparation/verification/binding, volume segmentation, scenario execution and final release
remain separately gated; independent Sol 6.1 review requirements remain in the active plan.

## ADR-030 — Narrow Public Course-Demonstration Objective and Synthetic-First Milestone A

**Accepted narrow future objective.** Provide separately reachable public read-only FastAPI and
Streamlit URLs after release approval, sharing an immutable explicitly approved bundle through a
typed provider. Streamlit uses direct Python services. Start with controlled synthetic content;
a public profile is explicit and never falls back to canonical local artifacts. Render is a
candidate for assessment, without a selected host/service or purchase authority.

The bundle/provider/API/dashboard are integrated; [current status](PROGRESS.md) records pending
corrective review and closeout. [Milestone C](../plans/active/public-course-demo.md) still requires
exact-content/rights/provenance, independent implementation/security review, resource/rollback and
specific owner approval for hosting, audience and window. No public listener, bundle publication,
source-derived release, deployment or URL is authorized by this objective. Current localhost rules
remain effective. Synthetic content proves interfaces/arithmetic, not Rossmann history, accuracy,
calibrated uncertainty, physical quantities, stockouts, savings, service or production readiness.
