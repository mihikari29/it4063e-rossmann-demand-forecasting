# Architecture and Methodology Decision Log

Only durable decisions supported by the authoritative proposal or explicitly approved phase design
belong here. Changes require a new or superseding decision record rather than a silent rewrite.

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
