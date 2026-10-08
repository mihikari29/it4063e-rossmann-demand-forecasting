# Architecture and Methodology Decision Log

Only durable decisions supported by the authoritative proposal or explicitly approved phase design
belong here. Changes require a new or superseding decision record rather than a silent rewrite.
Explicitly labelled proposed ADRs record reviewable changes and have no authority until accepted.

## ADR-001 — Forecast Granularity

**Status:** Accepted

**Decision:** Forecast at the Store × Date level.

**Reason:** Rossmann provides daily observations for stores, and this is the finest demand granularity supported by the selected data.

**Consequences:** Data keys, features, forecasts, metrics, and dashboard views must preserve store-day granularity.

## ADR-002 — Forecast Target

**Status:** Accepted

**Decision:** Use Rossmann `Sales` as the store-level monetary demand signal.

**Reason:** `Sales` is the available historical outcome associated with store demand, but it represents turnover rather than physical quantity.

**Consequences:** Forecasts and core inventory calculations use monetary-value units and must not be described as product-unit demand.

## ADR-003 — No SKU-Level Forecasting

**Status:** Accepted

**Decision:** Do not claim SKU-level forecasting or production SKU replenishment capability from the Rossmann dataset.

**Reason:** The dataset contains neither product identifiers nor physical quantities sold.

**Consequences:** Equivalent units may appear only as explicitly simulated illustrations based on a synthetic average unit value.

## ADR-004 — Primary Forecast Horizon

**Status:** Accepted

**Decision:** Use 14 days as the primary forecast horizon for model comparison and evaluation.

**Reason:** The proposal defines two weeks as the standard planning horizon while allowing optional 7-day and 28-day dashboard views.

**Consequences:** Validation windows and primary comparisons must produce 14 forecast steps and should report performance by horizon.

## ADR-005 — Synthetic Operational Layer

**Status:** Accepted

**Decision:** Simulate supply-chain and inventory fields absent from Rossmann and keep them explicitly separated from real data.

**Reason:** Lead time, inventory position, unit value, and cost inputs are required for decision support but are unavailable in the source dataset.

**Consequences:** Generation rules, assumptions, dependencies, ranges, and fixed seeds must be documented. Business conclusions remain conditional on those assumptions.

## ADR-006 — Forecasting Baseline

**Status:** Accepted

**Decision:** Use Seasonal Naive with a seven-day lag as the required primary baseline.

**Reason:** Daily store sales exhibit weekly seasonality, and advanced models must demonstrate value over a transparent benchmark.

**Consequences:** Every candidate model must be evaluated against the same baseline using the same time-ordered windows and metrics.

## ADR-007 — Main Machine-Learning Strategy

**Status:** Accepted

**Decision:** Use one global LightGBM model across stores as the primary machine-learning candidate rather than 1,115 independent machine-learning models.

**Reason:** A global model can share information across stores and use store, calendar, promotion, competition, lag, and rolling features efficiently.

**Consequences:** Store identity and store characteristics become model inputs. LightGBM must still earn final selection through validation.

## ADR-008 — Validation Strategy

**Status:** Accepted

**Clarification (2026-10-05):** ADR-015 defines the current final-evaluation release and discloses
earlier full-source descriptive exposure; "untouched" below means excluded from selection,
not a claim that the labels were never inspected.

**Decision:** Use rolling-origin / walk-forward validation and keep the latest 28 labeled days as a final untouched holdout during feature and model selection.

**Reason:** Time-ordered evaluation represents forecasting conditions and prevents future information from contaminating model selection.

**Consequences:** Random shuffling is prohibited. At least three 14-day validation windows are planned, primary metrics use `Open = 1`, and the final holdout is evaluated only after the methodology is locked.

## ADR-009 — Spark Is Optional

**Status:** Accepted

**Decision:** Keep Spark off the critical path; PySpark may be used only as an optional ETL demonstration.

**Reason:** The dataset is manageable on personal computers and does not require distributed processing for the proposed workflow.

**Consequences:** Core deliverables must not depend on Spark infrastructure or an optional PySpark experiment.

## ADR-010 - Python Environment and Packaging

**Status:** Accepted

**Supersession note (2026-10-05):** ADR-018 replaces the single-minor Python restriction and
deferred-lock policy. The original rationale below is retained as historical evidence.

**Decision:** Use Python 3.14 and `pyproject.toml` as the supported development baseline and single
hand-maintained source for package metadata, dependencies, command entry points, pytest, and Ruff.
Keep acquisition and development tools in optional extras.

**Reason:** The available Python 3.14.5 environment supports the current stable Phase 1 packages.
A standard `src/` package and one configuration file keep reusable logic importable and avoid
duplicated dependency lists.

**Consequences:** Contributors create a repository-local virtual environment and install the
appropriate extras. Later-phase dependencies are added only when needed. Deployment-specific lock
or constraints files may be generated later instead of manually duplicating requirements.

## ADR-011 - Official, Immutable Raw Data

**Status:** Accepted

**Decision:** Acquire Rossmann files only from the official Kaggle competition into the ignored
`data/raw/rossmann/` directory. Acquisition is atomic and refuses overwrite; validation is
read-only and checks file hashes.

**Reason:** A single authoritative source and immutable local files make provenance reproducible
without committing restricted data or credentials.

**Consequences:** Each contributor must obtain authorized competition access. A source refresh
requires explicitly moving the existing raw directory aside and rerunning acquisition and
validation. Derived data must be written elsewhere in a later phase.

## ADR-012 - Phase 3 Point-in-Time Feature Contract

**Status:** Accepted for Phase 3 implementation; contract version `phase-3-v1`.

**Decision:** Use one ordered 29-predictor schema for historical training and inference. Preserve
`Store` unchanged as both a key and later categorical model input; keep Date key-only and Sales as
label/history source. Dynamic target-history features use exact calendar dates, complete trailing
windows, and origin-censored actual history with optional earlier recursive predictions. Missing
exact history stays null. Competition opening status/age use month-level semantics, and invalid or
missing metadata is not imputed. Open-resolution candidates remain audit-only. The latest 28
labeled days are protected by a holdout firewall.

**Reason:** This preserves source precision and sparse coverage while making target-history
availability explicit for recursive forecasting; it also prevents train/inference schema drift and
future actuals from leaking through precomputed historical rows.

**Consequences:** The detailed, versioned field manifest and output roles are defined in
[`FEATURE_CONTRACT.md`](FEATURE_CONTRACT.md). Phase 3 adds no model-specific encoding, scaling,
same-weekday features, imputation, or forecasting model. Any later contract change must be reviewed,
regenerated, and must not be selected using final-holdout outcomes.

## ADR-013 - Phase 4 Seasonal Naive Evaluation Contract

**Status:** Accepted by explicit user approval on 2026-10-05.

**Lifecycle note:** Phase 4 has since been reviewed, merged and closed; PROGRESS owns current
state. The final paragraph below records the original review/closeout requirement.

**Decision:** Implement the weekly Seasonal Naive baseline on exactly three non-overlapping,
chronological 14-day development windows: `validation_1` (origin 2015-05-22, targets 2015-05-23
through 2015-06-05), `validation_2` (origin 2015-06-05, targets 2015-06-06 through 2015-06-19),
and `validation_3` (origin 2015-06-19, targets 2015-06-20 through 2015-07-03). For each Store and
origin, forecast the exact same-Store calendar date seven days earlier. Horizons 1–7 use actual
Sales only through the origin; horizons 8–14 recursively use the already generated raw forecast
from seven days earlier. Teacher forcing is prohibited. Missing exact weekly history remains
unavailable/null, with no prior-row fallback, interpolation, imputation, or zero fill. For each
Store with at least one observed target key in a window, construct internal forecast states for all
14 calendar horizons, but emit/evaluate only source-observed Store × Date target keys; internal
states have no target labels and may feed later recursive horizons.

Keep pure `raw_baseline_forecast` separate from post-forecast `operational_forecast`: known source
`Open == 0` routes operational output to zero only after raw generation; `Open == 1` retains the raw
forecast; unknown Open remains unresolved and is not treated as closed. `Open_resolved` is not
source truth. Attach actual Sales, source Open, and the validation label only after raw forecast
generation. Primary metrics use observed source `Open == 1` targets with actual Sales and an
available raw forecast. MAE is primary; RMSE, MAPE, and WAPE are secondary under the approved
metric contract. MAPE excludes zero-actual eligible rows only from MAPE (no epsilon) and reports
the excluded count and coverage. WAPE is unavailable/null with a reason when the actual denominator
is zero. Report availability coverage with explicit numerators and denominators. The final holdout,
2015-07-04 through 2015-07-31, is not forecast or evaluated during Phase 4.

**Reason:** The fixed weekly rule is a transparent benchmark for the approved 14-day horizon. Exact
calendar lookup and origin-censored recursion preserve time-series integrity and sparse source
coverage; separating raw predictions, operational routing, and labels prevents leakage and keeps
model quality distinct from the closed-store business rule.

**Consequences:** Results are development-only and are reported by validation window, pooled over
eligible observations, and by horizon. Missing raw forecasts remain visible in output and coverage
summaries rather than silently changing the metric population. No validation window, missing-history
rule, metric, or routing rule may be changed based on final-holdout outcomes. Phase 4 remains under
review until its implementation and results are externally reviewed and explicitly closed.

## ADR-014 - Phase 5 Holt-Winters Statistical Forecasting Contract

**Status:** Accepted by explicit user approval on 2026-10-05.

**Packaging clarification (2026-10-05):** ADR-018 supersedes only this record's Python-version
restriction. The model, dependency bound, 14-day development evaluation and failure policy remain
unchanged. The reviewed public API also honors requested horizons 1–14; Phase 5 uses 14, and
length validation/per-fit diagnostics use the requested horizon (see PROGRESS review-fix record).

**Decision:** Evaluate one univariate statsmodels Holt-Winters / `ExponentialSmoothing` model per
Store and forecast origin, using `trend="add"`, `damped_trend=False`, `seasonal="add"`,
`seasonal_periods=7`, `initialization_method="estimated"`, `use_boxcox=False`, and optimized
smoothing parameters. Use no exogenous inputs and do not tune model structure using validation
results. The runtime dependency is bounded to `statsmodels>=0.15,<0.16`; retain the repository's
Python `>=3.14,<3.15` requirement.

Fit on the regular daily series from the most recent contiguous observed Store × Date Sales segment
ending at the origin. Include observed closed-day Sales, including zeros. Do not remove closed days,
fill gaps, interpolate, compress to business days, or use Open as a regressor. Require at least 28
consecutive daily observations and use the entire eligible contiguous segment. An absent origin key,
insufficient history, model construction/fit/forecast exception, a forecast other than 14 finite
numeric values, or other unusable model output makes that Store-origin unavailable. No fallback to
Seasonal Naive, Holt, or Simple Exponential Smoothing is permitted; record sanitized failure
categories and capture warning/convergence diagnostics without hiding them.

Retain direct `model_forecast_unclipped` values and define
`raw_statistical_forecast = max(0, model_forecast_unclipped)`. Record clipping flags and aggregate
clipping count/rate/minimum diagnostics. After raw generation, route source `Open == 0` to an
operational zero, `Open == 1` to the raw statistical forecast, and unknown Open to null. Never use
target Sales or Open to generate raw forecasts; attach labels/routing fields only afterward.

Use exactly the Phase 4 development windows and Phase 4 primary metric, open-label eligibility,
MAPE/WAPE zero handling, and pooled/horizon aggregation contract. Report standalone Holt-Winters
coverage and metrics. Recompute Seasonal Naive through the reviewed Phase 4 implementation and
compare models only on identical primary-evaluation rows where both raw forecasts are available.
Report paired counts, metrics, MAE difference and relative MAE change, and lower-MAE candidate by
window, pooled, and horizon.

Before comparative interpretation, require at least 99% Holt-Winters forecast availability among
open-label targets in every development window. If any window is below 99%, retain auditable
forecasts, coverage, and fit diagnostics, flag coverage review, report affected fits, and suppress
claims that either candidate is superior or inferior. This is a precommitted coverage-quality
guardrail, not a selection hyperparameter.

The final holdout remains 2015-07-04 through 2015-07-31 and is not forecast or evaluated in Phase 5.
Phase 5 evaluates a fixed candidate but does not select the final project model; Phase 7 remains
responsible for model-ladder selection after LightGBM exists.

**Reason:** The proposal requires level, trend, and weekly seasonality. This fixed additive
candidate is transparent and can accommodate zero observations without a multiplicative seasonal
form. Contiguous-history rules preserve actual calendar spacing and prevent implicit gap filling.
Explicit failure handling keeps coverage visible and avoids conflating the statistical candidate
with Model 0. Identical-row pairing and the availability guardrail keep the baseline comparison
auditable.

**Consequences:** Phase 5 results are development-only and must report fit/warning/failure and
clipping diagnostics alongside standalone and paired metrics. Do not change model structure from
validation performance, add automatic fallback, access holdout outcomes, or mark Phase 5 complete
until external review and explicit closeout.

## ADR-015 — Final Evaluation Release and Historical Exposure

**Status:** Accepted for the user-authorized repository architecture review, 2026-10-05.

**Clarifies:** ADR-008/012–014; replaces the roadmap's Phase 7 holdout-scoring deliverable.

**Decision:** Phase 7 selects the model using development only. Freeze model/preprocessing specifications,
refit recipe, interval calibration, inventory policies/scenarios and monitoring thresholds before
the explicitly authorized Phase 13 final evaluation. Its primary point protocol has two 14-day
blocks: July 3 origin forecasts July 4–17, then July 17 origin forecasts July 18–31. Each block is
issued before revealing its labels daily. The second origin may consume already revealed actuals
under the frozen recipe. Scheduled model/preprocessing refitting may relearn fitted state only
when precommitted, on eligible already revealed training rows; specifications/hyperparameters
cannot change and interval calibration stays frozen. It may not retune or recalibrate from final
outcomes. Monitoring triggers are alerts, not automatic changes to the final-test model.
Phase 14 reports the frozen outputs. Any extra daily
operational forecast origins/protection horizons and common terminal censoring must be precommitted
in the replay plan; overlapping forecasts are not extra independent primary test observations.

**Evidence and reason:** The old roadmap scored the holdout in Phase 7 before uncertainty and
inventory design, then described a new sequential reveal in Phase 13. That could leak evaluation
feedback into later policy/calibration decisions. Also, Phase 1 quality checks and Phase 2 EDA
summarized full historical labels, including July 4–31, before the Phase 3 firewall. Preserve that
evidence: this is not a pristine never-inspected dataset. No holdout forecasting metrics or model
comparison have been produced; future learned statistics/cohorts must use origin training or
development data, never the full-period EDA tiers/representatives.

**Consequences:** Existing model windows/results remain intact. Development runners retain the
July 3 read filter; no evaluation is authorized by this review. Later final reporting discloses
descriptive exposure and the short holdout span; a replay is one final evaluation, not an
independent second test. Supplementary development origins require an approved common protocol.

## ADR-016 — Inventory Proxy Values and Cumulative Uncertainty

**Status:** Accepted for the user-authorized repository architecture review, 2026-10-05.

**Clarifies:** ADR-002/005 and proposal uncertainty/inventory scope.

**Decision:** Interpret simulated demand, stock, outstanding orders, ROP and replenishment on a
retail-equivalent monetary basis matching Sales turnover. Procurement cost requires an explicit
synthetic conversion; no quantity, actual stockout, unconstrained demand or Rossmann savings can
be inferred. Use common scenario paths/seeds/starting stocks for policy comparison. The default
simulation models lost sales, maintains an outstanding-order queue, and does not reset OnOrder to
zero merely because Rossmann has no such source field.

For daily review R=1 and lead time L=2–7, use protection P=L+R within the 14-day supported horizon.
Lead-time ROP is a separate continuous-review illustration; the simulator orders toward a
protection-period target. For complete out-of-sample Store-origin residual paths, form cumulative
error E_k = sum(e_h, h=1..k), then U_k = max(0, D_k + q_p(E_k)), where p is the cycle-service target.
Safety stock is max(0, U_k-D_k); ROP or order-up-to target is max(D_k,U_k), not necessarily U_k when
the empirical quantile is negative. Never sum marginal daily 95% upper bounds or assume independent
daily errors silently. Daily intervals and cumulative service bounds have distinct calibration
populations/levels. Calibrate on earlier development residuals and assess later origins; pooled
empirical coverage is not a guarantee for each store or a conformal claim.

**Reason:** Common monetary units alone do not equate sales revenue with procurement-cost inventory.
Marginal intervals do not establish cumulative lead-time risk, and static stock subtraction is not
a stateful replenishment simulator.

**Consequences:** Phase 10 must freeze event order, receipt/order lead convention, availability and
terminal-censoring rules before running comparisons. Dictionary definitions distinguish cycle
service from monetary fill rate, positive-demand stockout rate, daily holding-cost rate and cost
per unmet monetary unit. Results demonstrate a conditional heuristic/tradeoff, not proven optimal
inventory or verified real-business improvement. Unknown/incomplete operational paths remain
unavailable; synthetic DiscountDepth is scenario context, never a measured Rossmann predictor.

## ADR-017 — Proportionate Application and Forecast Extension Scope

**Status:** Accepted for the user-authorized repository architecture review, 2026-10-05.

**Clarifies:** ADR-004/007/012 and the planned application/monitoring scope.

**Decision:** Retain the three-model ladder and recursive global LightGBM first. Its initial raw
recursive state uses clipped raw predictions without future Open or outcome labels; operational
Open routing follows the full raw path. This preserves comparison/feature boundaries and does not
change reviewed baselines. Report the mismatch between closed actual history and raw recursive
history; closure-aware feedback/direct multi-horizon methods need a separately approved design
and development evidence. Optional SARIMA, extra features or broad model searches are not required.

Use a shared Python application service layer, a thin local/demo FastAPI adapter, and Streamlit
calling the same services directly. One deployed Streamlit demonstration suffices for the planned
application deployment; independent API hosting is optional. Evidently, SHAP, Docker and Spark
remain optional only for a concrete need. Simple drift/error/coverage summaries and alerts meet
the historical monitoring objective. A 7-day view is a subset of 14 days; 28-day support is a
separately designed/evaluated extension, not an existing promise.

**Reason:** Separate hosting, HTTP coupling and monitoring infrastructure add little to a five-person
course demonstration. Raw recursion makes the information boundary explicit without changing
accepted model results. Demonstrated baseline value or honest negative findings are legitimate
analytics outcomes; model/business improvement is a hypothesis, not a completion prerequisite.

**Consequences:** Keep Phase IDs for traceability but group future work packages; do not require
separate docs-only branches for design and closeout. Application and synthetic modules are created
only when implemented. The original course announcement is not in this repository; the thin API
retains the existing API objective without asserting an unverified requirement for two cloud
deployments. Deployment details can be settled in the application plan.

## ADR-018 — Portable Locked Environment and Quality CI

**Status:** Accepted and implemented in this user-authorized repository review, 2026-10-05.

**Supersedes:** ADR-010 single-minor Python/deferred-lock policy and only ADR-014's Python clause.

**Decision:** Support Python >=3.12,<3.15 with 3.14 as reference; use py312-compatible syntax/Ruff.
Keep pyproject.toml as the single hand-maintained dependency source and generate one universal
uv.lock (uv 0.12.23). Make NumPy explicit because the package imports it directly. Preserve reviewed
numerical versions in the lock; adding LightGBM remains Phase 6 work. CI runs locked dev-only
fixture tests, dependency consistency, Ruff and Markdown links on Python 3.12 and 3.14, requiring
no Kaggle credentials/data or holdout outcomes.

**Evidence and reason:** The old single-minor bound reflected the available machine, not a model
requirement. Three parenthesis-free exception tuples were the only 3.12 syntax incompatibilities;
adding parentheses preserves behavior. Isolated locked environments passed the complete fixture
suite on both 3.12.15 and 3.14.5, retaining the reviewed numerical package versions; current
validation counts are in PROGRESS.
Unbounded transitive installs and missing CI weakened reproducibility before the ML phase.
See [uv locking](https://docs.astral.sh/uv/concepts/projects/sync/) and
[GitHub integration](https://docs.astral.sh/uv/guides/integration/github/).

**Consequences:** Lock updates are deliberate and validated; no parallel maintained requirements
file. Future artifact manifests include code revision and environment/lock hash. Existing manifests
and results remain historical evidence, not regenerated merely for this documentation review.
The workflow defines a quality check, but remote execution awaits publication. Main protection is
recommended; GitHub reported main unprotected during this review, and no settings were changed.

## ADR-019 — Global Recursive LightGBM Phase 6 Contract

**Status:** Accepted after external methodology review, 2026-10-06.

**Decision:** Phase 6 will evaluate one global CPU GBDT LightGBM model for untransformed Store ×
Date monetary Sales, trained with regression_l1 and exactly the frozen Phase 3 29-predictor
contract. Fit labels are restricted to training_label_eligible/source Open=1, while all observed
pre-origin Sales (including closed-day zeros) remain available only for lag/rolling history.
Forecast recursively for 14 days using finite predictions clipped at zero for raw output and
feedback; non-finite predictions are unavailable. Keep future Open out of raw prediction/state and
apply operational Open routing only after the raw path. Learn categorical vocabularies from
eligible fitting data only; preserve the specified native numeric missing behavior and explicit
unavailability reasons.

Tune only the four predeclared configurations at the 2015-04-24 inner origin using recursive
open-label MAE and the 99% coverage requirement; freeze the chosen configuration/round count before
the three approved outer development windows. Recompute Seasonal Naive and additive Holt-Winters
and compare on identical eligible rows. Do not fall back to a baseline for unavailable forecasts.
Treat future holiday, school-holiday, promotion-plan, Promo2 schedule, competition, and Store
metadata as known at the origin for this course replay only; this is an explicit
operational/evaluation assumption, not historically verified Rossmann information availability.
Preserve the mismatch between actual closed-day zeros in historical state and raw recursive
feedback; do not add closure-aware feedback or direct multi-horizon modeling in Phase 6.

**Reason:** This adds the intended global feature-based candidate to the approved model ladder
while retaining origin-censored temporal evaluation, the existing forecast contract, and the
baseline-comparison boundary.

**Consequences:** The detailed specification, fixed configurations, windows, diagnostics, tests,
failure policy, and artifacts are in the [completed Phase 6 plan](../plans/completed/phase-6-global-lightgbm.md).
Acceptance authorizes Phase 6 implementation only after PR #9 integrates the design into main. It
does not authorize Phase 7 model selection, final-holdout access, or any final-holdout forecast or
evaluation.

## ADR-020 — Development-Only Model Selection and Frozen Refit Policy

**Status:** Accepted after external Phase 7 methodology review, 2026-10-06. Approval was
synchronized for PR #12 reviewed head `1c15ab0b6ee94f3ecccb8f04c84da97d58bbb225`. PR #12 was the
required design-integration gate at methodology approval and later merged into `main` at
`64dbf2359c34cc06d81ee4fc1640ad7225db3973` before Phase 7 implementation began.

**Decision:** Compare exactly Seasonal Naive, additive Holt-Winters and the frozen global LightGBM
on the three approved chronological H14 development windows. Use primary MAE on identical three-way
eligible/available open-label rows, while reporting standalone, pairwise and common coverage and
supplementary RMSE/MAPE/WAPE, window, horizon-block and individual-horizon diagnostics. Require at
least 99% open-label coverage in every window for each standalone candidate and the three-way common
population, and pass all key, label, mask, configuration and original-manifest integrity checks;
otherwise stop selection and suppress superiority claims.

Apply the fixed simplicity ladder SN → HW → LightGBM. Promote from the current incumbent only when
pooled MAE improves by at least 5%, MAE is lower in at least two of three windows, no window has
more than 10% regression, and neither pooled horizon block (1–7, 8–14) has more than 10% regression.
Exact ties, smaller gains, fewer window wins or a failed regression gate retain the simpler
incumbent. A failed HW promotion does not prevent comparing LightGBM to SN. Keep unavailable values
null and apply each reviewed failure policy; no fallback or model mixing. Report every individual
horizon, including unfavorable and sparse Sunday results; no per-horizon veto is added.

These numeric thresholds and the simplicity preference were proposed after Phase 4–6 results had
been observed. They are transparent project decision heuristics, not preregistered thresholds,
statistical significance tests or estimates. Three late-season windows, repeated Friday origins,
shared stores and correlated Store × Date errors do not establish independent out-of-sample
confirmation, universal horizon/Store dominance or year-round generalization.

For the existing offline CPU course demonstration, qualitative operational assessment is accepted;
a new performance benchmark is not a precondition to selection. This does not establish API
latency, throughput, production reliability, comparative end-to-end runtime, measured memory needs
or operational savings. Any later implementation must record versioned operational inputs and
their evidence; this acceptance does not extend to unexamined deployment environments.

Accept the cached development evidence lineage within this scope: verify original manifest hashes,
target keys, labels, masks, model/configuration identities and stop on any mismatch. Preserve old
source/version metadata; do not rewrite manifests or claim historical runs were regenerated from
current `main`. SN/HW legacy provenance and the recorded modified LightGBM worktree remain disclosed.

Freeze only the reviewed recipes, not fitted model state: SN exact d−7 lookup then prior raw
recursive values; Holt-Winters additive trend and weekly seasonality 7 on each store's latest
contiguous history of at least 28 days; LightGBM trial A at exactly 180 rounds with its reviewed
Phase 6 predictors, shared parameters, fit-only categories and recursive feedback. Use only
information available through each authorized origin. Phase 8 receives selected identity/config,
out-of-sample records, residual definitions, masks, complete/partial paths, missingness and
provenance; Phase 8 owns uncertainty intervals.

The Phase 7 development firewall continues through 2015-07-03. This ADR does not authorize any
2015-07-04–31 target access or final forecast/evaluation. Final release remains subject to ADR-015's
separately authorized frozen sequential Phase 13 protocol. Methodology approval itself did not
select a model. At that approval checkpoint, Phase 7 implementation could begin only after design
PR #12 merged into `main`; it later did, and the subsequent implementation and selection results
are maintained in [PROGRESS](PROGRESS.md).

**Reason:** A pooled MAE lead alone does not account for practical gain, consistency, coverage,
horizon tradeoffs, complexity or artifact lineage. A fixed simple-first rule makes those project
choices reproducible without overstating the evidence.

**Consequences:** Full thresholds, descriptive evidence, candidate recipes, implementation checks,
artifacts and Phase 8 handoff are in the [completed Phase 7 plan](../plans/completed/phase-7-model-selection.md).
At methodology approval, the Phase 7 plan was approved, its runner was not implemented, and no
model had been selected. PR #12 was the implementation integration boundary and merged before
implementation began. Later implementation and selection results are maintained in
[PROGRESS](PROGRESS.md); Phase 8 and final-holdout release remain separate future work.

## ADR-021 — Chronological Empirical Forecast Uncertainty and Conditional Operational Replay

**Status:** Accepted after external Phase 8 methodology review, 2026-10-06.

**Clarifies:** ADR-015–017, ADR-019–020; [completed Phase 8 plan](../plans/completed/phase-8-forecast-uncertainty.md).

**Context:** ADR-020 selected `global_lightgbm_gbdt_regression_l1`, trial A at exactly 180
boosting rounds with the approved ordered 29 predictors. Three selected development origins
provide sparse and dependent residual evidence. Saved historical Open supports reproducing
operational routing only under a conditional course-replay assumption; it does not prove that a
schedule was available at any forecast origin. ADR-015 protects July 4–31 outcomes for a
separately authorized sequential Phase 13 evaluation.

**Decision:** Keep the selected point model and its recipe unchanged. Approve only the following
development uncertainty protocol:

- Daily residuals are signed `actual_sales - raw_forecast` on the observed Open=1 primary-eligible
  population. Partial paths contribute eligible individual observations. Pool Store-origin rows
  equally within each exact horizon h=1..14; do not borrow across horizons, stores, or candidate
  models, and do not replace this population with the 32-store raw-complete H14 subset.
- For sorted residuals `e_(1)..e_(n)`, use 1-indexed ranks
  `floor((n+1)/40)` and `ceil(39*(n+1)/40)` for the nominal two-sided 95% tails. Retain ties,
  use no interpolation or rank clamping, require n>=40 and both ranks in 1..n, and leave
  unsupported horizons unavailable with explicit reasons. The 40-row floor is a pragmatic rule,
  not a reliability guarantee. Fit B h2/h9 contain 65/64 rows but only 33/32 distinct stores,
  so their Sunday estimates remain fragile. Add signed quantiles to the saved clipped nonnegative point;
  clip each bound independently at zero, preserve pre-clipping values/flags, reject nonfinite or
  inverted bounds, and do not force the point inside the interval. Fit A h2/h3/h9 remain
  unavailable; Fit B Sunday support remains fragile and must be disclosed. These are nominal
  marginal horizon-specific intervals, not conformal, simultaneous, per-store, or guaranteed
  95% coverage.
- Use only the approved chronological fits: Fit A calibrates validation_1 and assesses
  validation_2, with calibration labels through 2015-06-05 at that issuance; Fit B calibrates
  validation_1+validation_2 and assesses validation_3, with labels through 2015-06-19. Calibration
  labels must be available by the assessment origin; the assessment's own labels are excluded.
  No other origins/windows or automatic protocol changes are allowed. Later-origin evidence is
  descriptive because all windows participated in point-model selection.
- For each Store-origin and exact prefix k=1..14, construct signed cumulative operational error
  `E_k=sum(actual_sales_h-operational_forecast_h)` only from complete valid components h=1..k.
  Missing later components do not invalidate a shorter prefix; missing components are never filled
  with zero. Pool complete prefixes at the same k, preserving paths and within-path dependence.
  For p={0.90,0.95,0.98}, use the 1-indexed upper rank `ceil((n+1)*p)`, no interpolation or rank
  clamping, and require at least 50 complete prefixes and a valid rank; otherwise the stratum is
  unavailable. Retain signed q, including negative values. Under ADR-016, use
  `D_k=sum(operational_forecast_h)`, `U_k=max(0,D_k+q_p(E_k))`,
  `SafetyStock_k=max(0,U_k-D_k)`, and `Target_k=max(D_k,U_k)`. These terminal cumulative
  monetary bounds are not realized inventory cycle-service probabilities. Never sum marginal
  daily upper endpoints or assume independent daily errors.
- Permit `saved_source_open_assumed_known_at_origin` only to reproduce existing DEVELOPMENT
  operational forecasts as a **conditional historical course replay**. This assumption is not
  evidence of origin-time schedule availability; label operational calibration and assessment
  accordingly. A closed-day `[0,0]` route is valid only for an explicitly known or approved
  assumed closure and describes turnover, not latent demand. Keep Open=1, Open=0, and pooled
  operational diagnostics separate and disclose deterministic-closure inflation. A development
  replay does not authorize final-holdout operational replay.
- For Phase 13, never read, hash, load, or substitute final-holdout actual Open as planned schedule
  before the corresponding forecast issuance. Do not expose protected July 4–31 Open, Sales, or
  Customers early. Operational issuance requires separately reviewed origin-known schedule
  provenance or a separately approved synthetic/conditional schedule that is not derived from
  protected future actual Open. Without an authorized schedule, operational forecasts, routed
  intervals, and prefixes requiring future Open remain unavailable. Join actual Open only after
  issuance and the separately authorized sequential outcome reveal. Raw forecasts and raw
  interval calibration must not use future actual Open as predictors.
- Approve origin-anchored complete prefixes only for the Phase 10 handoff. Preserve ADR-016's
  R=1, L=2..7, and P=3..8 context. A later daily-review suffix is a different error population;
  q_P for an origin prefix cannot be reused as its calibrated bound. Phase 10 must obtain a
  separately reviewed suffix method or restrict its demonstration to supported origin-anchored
  decisions.
- Keep the limitations prominent: only three Friday development origins; shared stores/common-date
  shocks and serial dependence; weekday/horizon confounding; sparse Sunday Open=1 evidence; weak
  h10 point performance; only 96 complete raw-primary H14 paths from 32 stores repeated across
  three origins; 3,345 operational paths depend on the conditional saved-Open interpretation;
  historical counts are not independent temporal replications; development windows were involved
  in point-model selection; and original candidate/selection provenance limitations remain.
  Make no significance, confidence, bootstrap, conformal, or guaranteed-coverage claims and invent
  no empirical coverage results.

The approved calibration policy does not freeze any fitted quantile values. Fit B tables,
diagnostics, hashes, and availability must receive external implementation/results review before
their values are frozen. Do not automatically change the predeclared protocol in response to
diagnostics or refit on validation_3 merely to increase sample size. Do not mix models, use other
windows, or conduct final evaluation under this ADR.

**Reason:** These fixed empirical estimators preserve the accepted point-model and chronology
boundaries, expose sparse strata instead of hiding them with fallback, and retain cumulative
within-path dependence while keeping the opening-schedule assumption and holdout firewall explicit.

**Consequences:** The full estimator, diagnostics, artifacts, fixture criteria, operational
failure behavior, and Phase 10 handoff are specified in the completed plan. Acceptance authorizes
implementing and evaluating only this protocol after PR #14 integrates into `main`; this approval
sync does not implement an uncertainty runner, calculate intervals or quantile tables, or freeze
fitted values. External review of implementation results is required before fitted-table freeze.
No final-holdout outcome access or Phase 13 evaluation is authorized; ADR-015 still requires a
separate frozen sequential protocol. Phase 9/10 implementation remains outside this decision.

## ADR-022 — Synthetic Monetary Scenario Contract

**Status:** ACCEPTED after external methodology review, 2026-10-07.

**Extends:** ADR-016 with explicit synthetic initialization, conversion/cost and stress
assumptions. ADR-015/016/020/021 remain unchanged. Full approved schema, deterministic algorithm,
artifacts, fixtures and acceptance criteria:
[completed Phase 9 plan](../plans/completed/phase-9-synthetic-inventory.md).
The design is based on PR #17's merged Phase 8 closeout at
`f08a62aa980d0670186ed25ae1f6e5a018ff3781`.

**Accepted decision — four approved methodological choices:**

1. **Origin-safe initialization and value semantics.** Use the 56 calendar days through origin
   with at least 28 observed Open=1 records. Do not impute or fall back; preserve valid zero
   anchors. Initialize stock from the origin-safe observed turnover anchor times synthetic
   reference open-day coverage. Begin with an empty outstanding-order pipeline. Stock and
   demand remain retail-equivalent monetary proxies, not physical units or observed Rossmann
   inventory; Sales does not identify latent demand or real stockouts.
2. **Illustrative synthetic costs.** Use procurement ratio c in [0.55,0.85), annual holding
   rate a in [0.10,0.30), and goodwill rate g in [0.10,0.75). Set
   HoldingCostRate=c*a/365 and StockoutPenalty=(1-c)+g. Equivalent units are display-only.
   These are not measured business costs, margins or savings.
3. **Deterministic scenario contract.** Use master seed 4209 and the exact SHA-256 keyed-draw
   grammar; five paired replicates; eight synthetic families and a separate historical
   reference. Use the specified synthetic weekly schedules/promotions, shared shocks and
   declared coupled stress. Replicates imply no empirical likelihood or statistical power.
   Synthetic paths remain separate from observed Sales, frozen point forecasts and frozen
   Phase 8 estimates.
4. **Development chronology and artifact integrity.** Use origins 2015-06-05 and 2015-06-19,
   H14 ending by 2015-07-03, with Fit A/B compatibility. Use origin-safe projected history;
   preserve the protected holdout; verify frozen Phase 7/8 bindings; publish immutable artifacts;
   fail closed on integrity violations. Preserve unavailable inputs without repair/fallback.

**Weekday-factor clarification accepted by the reviewer:** The approved values remain Monday–
Sunday [0.95, 0.98, 1.00, 1.02, 1.10, 1.15, 0.80], and the approved generation formula is
unchanged. These factors average 1 over seven calendar days, while the default Monday–Saturday
open-day mean is 6.20/6 = 1.033333…. They are illustrative synthetic multipliers, not
open-day-normalized factors that preserve the historical anchor's mean. This clarification
changes neither the factor values nor the formula.

**Reason:** Rossmann supplies turnover, not supply/stock/cost records. Explicit synthetic
assumptions make a reproducible course demonstration possible while preventing fabricated
operations from becoming observations, predictors or guaranteed inventory recommendations.
Bounded paired stresses expose shared-shock and cold-start risks without tuning to later outcomes.

**Alternatives considered:** Open-day versus calendar-day turnover initialization; empty versus
synthetic warm-start pipeline; direct retail-value costs versus explicit procurement conversion;
independent versus shared/coupled stress; empirical/heavy-tailed versus bounded illustrative
draws; synthetic versus conditional historical schedules. The active plan records their
tradeoffs. Rolling-review/suffix calibration and simulation conventions require a separate
Phase 10 design and are not decided by this ADR.

**Consequences:** The Phase 9 design is approved; implementation is NOT STARTED by this
synchronization. Future implementation must follow this design and report fixture and
development-only evidence separately. This ADR does not start Phase 10 or approve rolling suffix
calibration, simulation event timing, an order queue, replenishment policies or inventory KPIs.
Preserve Phase 8's origin-anchored prefix-only use and conditional historical replay. Calibration
does not transport to synthetic stress. Fit B raw-primary coverage remains below nominal 95%;
sparse Sunday support and store/origin dependence remain. No conformal, per-store, production or
service-level guarantee is introduced. The protected holdout remains unreleased.

## ADR-023 — Origin-Frozen Daily Inventory Policy Simulation and Finite-Window Accounting

**Status:** ACCEPTED after explicit human methodology approval, 2026-10-07.

**Review evidence:** Initial technical methodology review ACCEPT; fresh independent methodology
review `INDEPENDENT_PHASE10_DESIGN_REVIEW=ACCEPT`. No blocking findings or required methodology
changes. Human approval is recorded in the Phase 10 plan and PROGRESS; this is not a claim of
GitHub-native reviewer approval.

**Lifecycle note:** At the 2026-10-07 approval synchronization, implementation had not started.
Implementation was subsequently reviewed and integrated through PR #23 at
`15bce83cd63a4edfeed6defb95788da90d0f36d9` and corrective PR #24 at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. The final independent external/model-assisted technical
review accepted the corrective implementation; formal Phase 10 closeout is recorded in the completed
Phase 10 plan. This lifecycle note does not change the accepted methodology or authorize holdout
access.

**Scope extension:** ADR-016/021/022's Phase 10 handoff only. Accepted Phases 0–9 methodology,
selected LightGBM recipe and Phase 8 fitted tables remain unchanged. Full proposal:
[completed Phase 10 plan](../plans/completed/phase-10-inventory-simulation.md).

**Context:** Phase 9 is COMPLETE and supplies exogenous monetary scenarios, not inventory policies.
Phase 8 supplies cumulative uncertainty for approved origin-anchored prefixes only; it provides
no calibrated later-review suffix. A daily forecast-refresh simulator would exceed that handoff.
Technical and independent methodology reviews supported the proposal; at the approval checkpoint,
explicit human approval authorized implementation only as a separate next task.

**Accepted decision:** Use separate H14 development episodes at end-of-day June 5/Fit A and
June 19/Fit B, ending by July 3. Set exactly two standing targets once at origin: baseline
`S=m*sum(origin-known open indicators over h1..P)` from the Phase 9 turnover anchor, and selected
LightGBM `D_P=sum(operational points)`, `U_P=max(0,D_P+q_(p,P))`,
`Safety=max(0,U_P-D_P)`, `S=max(D_P,U_P)`. Preserve signed q. Reference p=0.95;
additional sensitivity p is 0.90/0.98 only. Later daily reviews execute that unchanged target;
no forecast refresh, suffix generation, quantile scaling, rolling uncertainty, recalibration or fit.
The target can become stale; standing inventory decisions claim no later-review calibration.

Use R=1, L integer 2–7 and P=L+1=3–8 <=14. L counts full intervening calendar demand days:
EOD-t orders arrive at BO-day t+L+1 (L=2 => receipt before day-3 demand). At origin verify
identities/schedule and freeze targets before loading outcomes, then initialize stock/empty
pipeline and order. Days 1–13 receive, reveal consumption, fulfil, record lost sales, charge ending-
stock holding/shortfall costs, calculate position and order. Day 14 processes outcomes/state/costs
but suppresses the final order review. Maintain an explicit simulated order queue; no backlog.
`IP=ending on-hand+outstanding before new order`, `Q=max(0,S-IP)` in continuous monetary V.

Require exact model/recipe/origin/fit/P/p, complete operational prefix, compatible schedule and
finite inputs. Unavailable targets remain null with reasons, never zero/baseline/point-only or
another stratum. Historical replay preserves the accepted conditional saved-source-Open assumption
and unchanged development Sales, not realized inventory truth. Synthetic schedules route the
unchanged raw points; frozen historical q is only an illustrative uncalibrated stress-test buffer,
with `calibration_transport_valid=false`. No nominal synthetic coverage/service claim.

Share demand, starting stocks, lead time, schedule, costs, family, replicate, variant and upstream
identity between policies. Use Phase 9 `h=c*a/365`, `b=(1-c)+g` and primary
**simulated holding-plus-shortfall cost** `sum(h*ending_stock+b*unmet)` over H14. Do not add
procurement expenditure/lost margin again, subtract Sales or call it profit. Report c*terminal
stock and c*outstanding orders as separate exposure diagnostics, outside the objective.

Freeze value fill/positive-demand stockout denominators, ending-stock inventory mean and additive
cost/unmet fields. The cycle output is **completed positive-demand receipt-cycle service rate**,
a project-specific simulated CSL proxy: no-unmet positive-demand cycles / completed positive-demand
cycles bounded by two observed positive receipt dates. Report policy-dependent denominators,
zero-demand cycles and censored intervals; zero denominators give null. Pool ratios from totals.
Missing consumption stops dependent state; incomplete tracks are not complete comparison evidence.
Closed synthetic days consume zero when available; receipts/reviews/carrying continue.

Retain all orders placed through day 13, including those due after T=origin+14; due-on-T receipts
precede consumption. No cancellation, refund, acceleration, extension or salvage. Apply identical
terminal treatment, report inventory/pipeline/late orders/commitments and do not call exposure
savings. Use all Phase 9 scenarios at p=0.95 plus nine one-factor-at-a-time synthetic_base overlays
for L, p, a, g and starting coverage; do not modify/regenerate Phase 9 or infer replicate likelihood.

Future outputs are ignored immutable, schema/key/null/hash-validated runs with pinned Phase 7/8/9
lineage, staged reread, input recheck, manifest-last and atomic publication. Fail closed and preserve
earlier runs/pointer. No protected outcomes may be read or hashed; ADR-015 release remains separate.

**Reason:** A simple standing-target comparison preserves daily inventory mechanics without
inventing forecast availability or calibrated suffix uncertainty. Explicit valuation, chronology,
finite-window exposure and denominators make a defensible course demonstration possible.

**Alternatives and limitations:** Supported-origin-only ordering would provide a narrower mechanics
demonstration; rolling issuance/suffix calibration would need separate evidence and approval.
The proposed standing target may be stale. Two origins, dependent Stores, cold starts, H14
truncation, artificial costs, uncalibrated stress transport and endogenous cycles limit inference.
This is policy simulation/comparison, not industrial optimization or proof of superiority.

**Consequences:** Implementation followed this accepted ADR and completed plan; the corrective
implementation and external/model-assisted technical review were integrated through PR #23 and PR #24.
The accepted canonical development run and formal closeout are recorded in the completed Phase 10 plan
and PROGRESS. At approval, implementation had not started; that historical checkpoint is preserved
above. Phase 9 remains COMPLETE. Phase 11 remains NOT STARTED / NOT AUTHORIZED. No
final holdout evaluation or access was part of Phase 10 or this closeout.
