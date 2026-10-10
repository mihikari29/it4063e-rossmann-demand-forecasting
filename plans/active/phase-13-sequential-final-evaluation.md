# Phase 13 — Sequential Final Evaluation Design Proposal

**State: PROPOSED / NOT APPROVED.** This is M0.1 documentation for Technical Lead and owner
review. Every material choice remains pending approval. It authorizes neither implementation nor
access to protected July 4–31 outcomes. Phase 13 remains PLANNED / NOT AUTHORIZED; Phase 14 has
not started.

## 1. Objective, scope, and non-goals

Propose one reproducible, leakage-controlled final evaluation of the accepted Rossmann
Store × Date monetary Sales forecast, with two non-overlapping H14 blocks issued before
their outcomes are revealed. Propose lightweight historical monitoring and resolve whether
the inventory deliverable can be evaluated within those same bounded episodes.

This plan does not implement the protocol, inspect final outcomes, select another model,
change accepted features/metrics/calibration/policies, add forecast origins or horizons,
generate final forecasts, or authorize a final-data release. No ADR is added: this proposal
contains unresolved choices and does not supersede accepted ADRs.

## 2. Current accepted evidence and dependencies

**FACT:** PR #34 merged the initial M0 design into `main` at
`4f2f9dc407109efea8401ff3b19894e104ad764e`, verified as the current `origin/main` base for this
review. PR #34 did not approve the methodology. Phases 0–12 are integrated and complete; the
selected point model is
`global_lightgbm_gbdt_regression_l1`, trial A at 180 rounds. ADR-015 requires a separately
authorized final protocol. ADR-020 freezes the model recipe. ADR-021 freezes the development
uncertainty method and the accepted Fit B values for the identified canonical run. ADR-022/023
freeze the synthetic assumptions and Phase 10 standing-policy simulation. ADR-024 sets the
Phase 12 demonstration boundary to localhost.

This M0.1 revision incorporates the independent Sol 6.1 methodology review of P13-01 through P13-09.
It remains an approval proposal: all material methodology choices below are PENDING APPROVAL.
There is no pending code integration dependency. The origin-parameterized training and recursive
functions can represent authorized July 3 and July 17 fits when given safe inputs; no such fit has
been run. The current development runner rejects reads after July 3 and is not the final replay
entry point. The active interfaces and evidence are in
[PROGRESS](../../docs/PROGRESS.md), [DECISIONS](../../docs/DECISIONS.md), and the completed
[Phase 7](../completed/phase-7-model-selection.md),
[Phase 8](../completed/phase-8-forecast-uncertainty.md),
[Phase 9](../completed/phase-9-synthetic-inventory.md),
[Phase 10](../completed/phase-10-inventory-simulation.md), and
[Phase 12](../completed/phase-12-streamlit-dashboard.md) plans.

**Code contract:** reuse `prepare_training_data` and `recursive_lightgbm_forecasts` in
[`forecasting/lightgbm.py`](../../src/rossmann_forecasting/forecasting/lightgbm.py#L176)
(lines 176 and 404); `build_refit_recipe` in
[`forecasting/model_selection.py`](../../src/rossmann_forecasting/forecasting/model_selection.py#L1059)
(line 1059); `summarize_forecast_metrics` in
[`forecasting/metrics.py`](../../src/rossmann_forecasting/forecasting/metrics.py#L78)
(line 78); and existing interval arithmetic `_interval_from_point` in
[`forecasting/uncertainty.py`](../../src/rossmann_forecasting/forecasting/uncertainty.py#L955)
(line 955), through a new tested adapter. The runner's Parquet reader and `run` method remain
development-only (`lightgbm_runner.py`, lines 93 and 417); `calculate_uncertainty` re-estimates
quantiles (`uncertainty.py`, line 1517); `simulate_case` requires a complete episode path and
June origins (`inventory/simulation.py`, line 634). Keep those restrictions; do not route Phase 13
through them unchanged.

**Important limitations:** Phase 8 Fit B raw-primary empirical coverage was 12,263/13,437
(91.26%), below nominal 95%; sparse Sunday support remains fragile. This is development
evidence and is not a final coverage promise. Phase 10's accepted forecast-policy simulated
holding-plus-shortfall cost was higher than baseline in both recorded populations; preserve
the unfavorable result. Earlier full-source descriptive EDA included the protected period,
as disclosed in [EDA findings](../../docs/EDA_FINDINGS.md). Do not call the holdout pristine
or reuse full-period EDA tiers/cohorts for modeling or monitoring.

## 3. Proposed architecture and trust boundaries

**RECOMMENDATION:** A small local replay coordinator around existing `src/` functions, with
separate issue, reveal-one-day, and evaluate operations. Persist immutable issued forecasts,
an append-only day-release journal, and checkpoint identities. Keep application/API/dashboard
services out of the replay path.

The input contract distinguishes:

1. **Historical training predictor sources and labels:** an origin-safe provider view with the
   exact accepted predictors, source `Sales` labels, source `Open`, and eligibility fields. The
   provider filters dates before labels reach fit code; eligible fit labels are observed
   source-Open=1 Sales through the fit origin. It never includes Customers or Customers-derived
   fields.
2. **Recursive history:** a separate `Store`/`Date`/`Sales` view of observed actuals through the
   fit origin, including observed closed-day zeros. Feature recursion appends only earlier raw
   predictions from the same issuance. Sparse dates remain absent; no missing date becomes zero.
3. **Future covariates:** a separately versioned, provenance-bearing origin-known exogenous
   feature-source view used to assemble the existing `phase-3-v1` ordered 29-predictor schema.
   Dynamic Sales-lag/window predictors are rebuilt from recursive history. This view contains no
   target labels, Customers, actual future Open, or future outcome-derived values.
4. **Optional planned Open:** a separately versioned nullable operational schedule, if supplied
   under an approved availability assumption. It is never inferred from future actual Open.
5. **Unreleased outcomes:** protected target projections are unavailable to issuance and general
   preparation. For a newly staged outcome partition, the default sequence is: complete and persist
   that block's issuance; persist the next chronological date's `release_intent`; separately
   authorize mechanical staging; then create/read only that date's projection. The staging read is
   protected-data access, but it is not analytical outcome revelation. Any mechanical reads or
   partitions from earlier custody work must have documented authorization and provenance; such
   historical reads are not day-level analytical releases and authorize no new access. For a
   pre-existing partition, verify authorization/provenance records without opening its projection;
   after the matching per-day intent and analytical release, access only that date's projection.
6. **Released outcomes:** a separate provider view exposing only the date projection authorized
   for analytical release after a matching immutable issuance and persisted release intent, and,
   for new projections, separate staging authorization. Evaluation uses released Sales and source
   Open; Customers remains excluded. Block 1's released rows can enter the July 17 training-label
   and recursive-history views only after the ordered release through July 17 is complete. This
   requires no access to Block 2 outcomes.

At the July 17 origin, the training and recursive-history views may therefore include actual
Block 1 Sales/Open rows already revealed in order, while their date guard remains `Date <=
2015-07-17`; Block 2 outcome projections remain inaccessible. Each provider has its own explicit
path, schema, field, and date allowlist.

### Local custody and provider enforcement

Path allowlists, schema checks, date guards, provider spies, hashes of authorized inputs/issued
outputs, and an append-only application journal enforce logical behavior and expose accidental
misuse. Never hash sealed or unreleased outcome contents. These controls do **not** prove that a
process never opened a combined source file or that an administrator could not bypass a local
guard. A date filter on a Parquet scan is not physical isolation.

**Recommended A2 — independently staged inputs with provider-scoped access:** give each input
view its own staged projection and provider. Default-deny every unlisted provider, file, path,
field, and date; reject unsafe paths and dates before content access; keep issued outputs immutable;
and record durable, chronological release-intent, release, and evaluation-checkpoint events. A
trusted operator controls staging and day release and is part of the trust assumption. This is a
logical/operator-enforced boundary; it does not claim protection from that operator, a hostile
machine owner, or an administrator. Separate Windows accounts and NTFS ACLs are not mandatory
under A2.

**Optional A1 — stronger local isolation:** separate Windows identities, restrictive NTFS ACLs,
and custodian-controlled staged projections may further constrain accidental reads. A1 is an
optional hardening arrangement, not the minimum architecture.

Analytical release and mechanical staging are distinct actions. For a new outcome projection,
complete the block issuance, persist the date-specific `release_intent`, separately authorize
mechanical staging, and create/read only that date's projection. **Mechanical staging** reads
protected source content to partition, copy, or filter it; that is protected-data access, but not
analytical revelation. Then separately authorize **analytical release** of only that date's
projection to the evaluation provider, evaluate and checkpoint it, and only then advance to the
next date. If a projection already exists from earlier custody work, verify its documented staging
authorization and provenance from records without opening its contents; the same per-day intent and
analytical-release sequence still applies. Record earlier mechanical reads separately from analytical
releases. This task performs no protected-data staging, extraction, access, or hash.

Under A2, an operator-enforced boundary is the stated evidence limit; it does not establish strict
physical isolation from the trusted operator, machine owner, or administrator, and local clock
values alone do not prove chronology. The chosen custody model and trusted-operator assumption
remain subject to Technical Lead/owner approval.

## 4. Exact two-origin evaluation chronology

| Block | Fit origin | Complete issuance target dates | Allowed history at fit | Revelation gate |
|---|---|---|---|---|
| 1 | 2015-07-03 | 2015-07-04–2015-07-17, H1–H14 | Through 2015-07-03 | Publish and verify every requested forecast before the first block outcome is exposed; then release one target date at a time in order. |
| 2 | 2015-07-17 | 2015-07-18–2015-07-31, H1–H14 | Through 2015-07-17, including Block 1 outcomes already released | Publish and verify every requested forecast before exposing any Block 2 outcome; then release one target date at a time in order. |

There are 1,115 supported stores under the existing roster contract (`Store` 1–1,115),
subject to preflight verification. The requested grid is 15,610 Store × Date keys per block
and 31,220 across both blocks. Requested keys are not a claim that each outcome is present or
eligible. Do not shrink the grid based on unrevealed outcomes.

Before Block 1 issuance, the issuance process must not access, hash, load, derive from, or score
any July 4–31 target outcome, including actual Open. Before Block 2 issuance, it must not access,
hash, load, derive from, or score July 18–31 outcomes. No actual future Sales, Open, Customers,
or outcome-derived field enters either issuance. Block 2's permitted first-block history is
available only after the authorized daily releases complete through July 17.

## 5. Frozen model/refit recipe and reproducibility

Reuse the exact accepted trial A recipe: global CPU GBDT, 180 requested rounds, the frozen 29
predictors, and these existing parameter dictionaries:

```python
trial_a = {
    "learning_rate": 0.05,
    "num_leaves": 15,
    "max_depth": 4,
    "min_data_in_leaf": 200,
}
shared = {
    "boosting_type": "gbdt",
    "objective": "regression_l1",
    "metric": "l1",
    "device_type": "cpu",
    "num_threads": 4,
    "deterministic": True,
    "force_col_wise": True,
    "feature_fraction": 1.0,
    "bagging_fraction": 1.0,
    "bagging_freq": 0,
    "lambda_l2": 1.0,
    "max_bin": 63,
    "zero_as_missing": False,
    "verbosity": -1,
    "seed": 42,
    "data_random_seed": 42,
    "feature_fraction_seed": 42,
    "bagging_seed": 42,
}
dataset = {"max_bin": 63, "zero_as_missing": False, "feature_pre_filter": False}
```

Also preserve `free_raw_data=False` for dataset creation and the reviewed ordered predictor
schema. These are copied for review from the approved implementation, not new parameter choices.
Source of truth:
[ADR-020](../../docs/DECISIONS.md#adr-020--development-only-model-selection-and-frozen-refit-policy),
[Phase 6 implementation](../completed/phase-6-global-lightgbm.md),
[`lightgbm_evaluation.py`](../../src/rossmann_forecasting/forecasting/lightgbm_evaluation.py#L70), and
[`lightgbm.py`](../../src/rossmann_forecasting/forecasting/lightgbm.py).

At each origin, fit a new model using eligible observed source Open=1 training rows through
that origin; retain observed pre-origin closed-day zeros in lag history. Relearn categorical
vocabularies only from eligible fitting rows under the accepted adapter. No warm start,
early-stop-driven recipe change, tuning, feature selection change, continuation model, or
fallback. Block 2 is a scheduled fresh refit, not model selection from Block 1 results.
Validate recipe construction against the accepted refit recipe and fail on any parameter,
schema, cutoff, category, or origin mismatch. Assert the fitted model origin equals the
issuance origin; the current recursive API does not make that assertion itself.

Record requested rounds and actual tree count. Persist the booster and all prediction adapter
state. Recommend the locked Windows x64 / Python 3.14 reference environment from ADR-018, using
the repository `uv.lock` and pinned uv version; record the LightGBM native build and environment
identity. Require exact equality for frozen recipe/configuration, ordered feature schema,
categories, input/output identities, requested keys, and pinned Fit B table identities. For
same-input booster save/load prediction comparison, propose `rtol=1e-12` and `atol=1e-9`.
Those tolerances are a proposal, not an accepted prior result. Do not claim bitwise identity
across operating systems, compilers, or LightGBM builds.

## 6. Origin-known covariates and planned Open

Propose a versioned table keyed by Store × Date with schema version, source/version, extraction
time, availability assumption, null policy, content identity, and approved use. Keep the exact
existing ordered 29-predictor `phase-3-v1` model schema; this proposal adds no predictor or derived
feature. The exogenous covariate table supplies origin-known sources only; dynamic Sales history
predictors are rebuilt from the separate recursive-history view. It contains no target labels or
future outcome-derived fields.

- **Deterministic calendar:** Date and DayOfWeek are derived from the requested calendar key.
- **Static metadata:** Store type, assortment, competition and related snapshot values require
  the existing disclosed course assumption that they were known at the origin; record source
  version and distinguish snapshot values from historically verified availability.
- **Holiday/promotion schedules:** StateHoliday, SchoolHoliday, Promo, Promo2 and associated
  schedule fields require source/version and an explicit origin-known provenance decision.
  Retrospective schedule covariates from the historical source may be proposed only under an
  explicitly approved conditional assumption that they were known at the origin; a stored value
  does not prove that availability. Do not derive them from Sales, Customers, or target outcomes.
- **Planned Open:** a separately supplied, nullable schedule with provenance. Do not infer it
  from actual future Open, target labels, future customer counts, or later closure records.

Future actual `Open` is never a planned schedule or a predictor. Unknown planned Open remains
unknown. It is not zero, `Open_resolved`, or a reason to overwrite the raw forecast. Raw
predictions are emitted before any operational routing. If a required
predictor row/value is absent, use only the accepted native missing-value behavior where that
feature contract permits it; otherwise mark the prediction unavailable with a reason. If
planned Open is absent, raw points may remain available while operational points, routed
intervals, cumulative operational bounds, and inventory targets that depend on it are null.
No protected actual value fills a missing covariate. This proposal authorizes no future-data
extraction, including retrospective promotion/holiday covariate extraction.

## 7. Forecast issuance and immutable persistence

For each block, validate configuration and allowlisted input identities, construct origin-censored
training/features, fit fresh, generate all 14 recursive calendar steps for the fixed requested
grid, apply approved schedule routing separately, and validate keys/schema/availability. Issue
raw and operational records as distinct fields and outputs.

Publication is a commit point. Write to a unique staging location; reread and validate every
output, recompute allowed output hashes, write the manifest last, then atomically publish an
immutable issuance directory and receipt. Only a verified receipt unlocks the first day-release
request. If a complete block cannot be issued, stop before release. A published block is never
rewritten after outcomes become available.

## 8. Frozen Fit B uncertainty application

**PROPOSED DEFAULT — Technical Lead approval required:** apply the already accepted frozen Fit B
daily residual quantiles and cumulative-prefix quantiles unchanged to both blocks, subject to
matching selected-model, feature, fit, horizon/prefix, and source identities. Pin these accepted
identities recorded in [PROGRESS](../../docs/PROGRESS.md):

| Fit B identity | SHA-256 / value |
|---|---|
| Phase 8 run | `phase8-impl-20261006-provenance-review` |
| Manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| Daily residual quantiles | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| Cumulative error quantiles | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` |
| `calibration_config.json` file | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |

The accepted Fit B governance record supersedes the manifest's publication-time
`fit_b_quantiles_frozen=false` field for these exact identities. Preserve that historical manifest;
do not regenerate or rewrite it.

**A. Fit B calibration evidence (historical observations).** ADR-021's daily calibration residuals
are signed `actual_sales_h - raw_forecast_h` on its accepted observed-Open=1 population. Partial
paths contribute eligible individual observations, pooled equally across Store-origin rows at each
exact horizon; do not borrow across horizons, stores, or candidate models or substitute the
raw-complete H14 subset. For each exact horizon, sort those historical signed residuals and use
1-indexed ranks `floor((n+1)/40)` and `ceil(39*(n+1)/40)`, requiring `n >= 40` and both ranks in
`1..n`. Use no interpolation or rank clamping, and do not borrow across horizons. For each
Store-origin's complete historical cumulative operational prefix `k`, define the signed calibration
error as `E_k^cal = sum_{h=1..k}(actual_sales_h^cal - operational_forecast_h^cal)`, using only
complete valid components. Missing later components do not invalidate a shorter prefix, and missing
components are never filled with zero. Pool complete calibration prefixes at the same exact `k`,
preserving paths and within-path dependence. For `p ∈ {0.90, 0.95, 0.98}`, Fit B's saved signed
`q_{k,p}` uses the 1-indexed upper rank `ceil((n+1)*p)`, with at least 50 complete calibration
prefixes and a valid rank; use no interpolation or rank clamping. These `n >= 40` and `n >= 50`
floors apply to historical calibration evidence for each exact horizon or prefix. Unsupported
calibration strata remain unavailable with their saved reasons. Fit B's calibration actuals are
not July outcomes; the frozen identities above and exact saved entries remain authoritative.

**B. Final issuance.** For daily bounds, use the issued raw point forecasts with the exact frozen
Fit B daily entries `q_low,h` and `q_high,h`. For cumulative bounds, use only the issued
operational forecasts with the exact frozen Fit B cumulative entry `q_{k,p}`, subject to the
saved identities, matching fit/horizon/prefix/source conditions, and frozen availability/reason
fields. For a daily issued raw point `yhat_h`, emit endpoints `max(0, yhat_h + q_low,h)` and
`max(0, yhat_h + q_high,h)`, retaining signed quantiles, pre-clipping endpoints/flags, availability,
and the accepted unsupported reason. For a complete cumulative operational prefix `k`, use
`D_k = sum_{h=1..k} operational_forecast_h`,
`U_k = max(0, D_k + q_{k,p})`,
`SafetyStock_k = max(0, U_k - D_k)`, and `Target_k = max(D_k, U_k)`.
No July actual Sales, July residual, or newly fitted quantile is needed or used to issue these
uncertainty bounds. Do not refit, tune, or recalibrate quantiles, transfer a cumulative prefix
quantile to a later-review suffix, sum daily upper bounds, or force a point inside its daily
interval.

**C. Final evaluation after authorized chronological revelation.** Only after the matching July
date has been authorized and revealed through the ordered procedure in Section 9 may its actual
Sales enter post-issuance evaluation. Define the signed July error
`e_h^eval = actual_sales_h^July - issued_operational_forecast_h`; for a complete valid revealed
prefix, define
`E_k^eval = sum_{h=1..k} e_h^eval`. Use these revealed errors to assess cumulative error and the
empirical coverage of the already-issued bounds under the accepted evaluation population and
denominators. They do not change the issuance, frozen quantiles, or bounds. Incomplete or
unsupported prefixes retain their prescribed unavailable status. Never use July outcomes before
their authorized chronological revelation.

June Fit B was calibrated on a different fit state and development period; applying it to either
July fresh fit is an explicit transport assumption. Transport validity and July coverage are
unknown, so do not present transferred intervals/buffers as reliable, nominally calibrated, or
guaranteed. If an exact table identity, horizon/prefix, sample-floor, fit, or schedule condition
is unsupported, preserve the accepted unavailable reason. Keep raw forecasts/intervals distinct
from planned-Open-routed operational forecasts/intervals and cumulative outputs.

Preserve exact-horizon/prefix availability, signed residual quantiles, pre-clipping endpoints and
flags, point-containment behavior, valid-rank/sample-floor rules, and explicit unsupported
reasons. Report final empirical coverage only after authorized revelation; development coverage
is not final coverage.

## 9. Controlled daily outcome revelation

After the complete block issuance receipt is verified and persisted, durably flush an immutable
`release_intent` for the next chronological date, naming the block, sequence, issuance receipt/hash,
provider, and expected projection identity **before any process accesses that date's protected
outcome content**. The event records intended access, not proof that content was mechanically read
or analytically released. If the date projection must be newly created, a separate authorization
for mechanical staging is required after the intent and before the source read; stage only that
date's projection. This mechanical read is protected-data access, but is not analytical outcome
revelation. If a projection already exists from earlier custody work, verify its documented staging
authorization and provenance from records without opening the projection; an earlier mechanical
read is still not an analytical release and does not authorize current evaluation access. Then
separately authorize analytical release of only that date's projection to the evaluation provider,
and only then access its contents. Validate date, store keys, schema, source identity, and projection
provenance before evaluation; append an immutable release receipt referencing the intent and
issuance hash. Evaluate and checkpoint that date before advancing chronologically.
Retain missing rows as missing. Actual Open is joined only after release for eligibility and
post hoc diagnostics. Sales is joined only to the matching already-issued key. Customers is not
needed for this evaluation and remains excluded.

The release journal records intent and completion as distinct state transitions, plus block,
date, sequence number, issuance hash, projected schema, source/version identity, row counts,
output hash, evaluation checkpoint, and failure status. Daily checkpoint publication is atomic
and idempotent. Reject duplicate dates with conflicting
content, out-of-order release, wrong block, changed issuance, or a failed checkpoint. The
July 17 checkpoint is the only route to Block 2 training history.

## 10. Point and uncertainty evaluation contracts

The fixed requested grid contains 15,610 Store × Date keys per block and 31,220 across both
blocks. Account for that grid separately from observed labels and metric records. Report, by block
and overall: (1) requested keys; (2) observed outcome rows; (3) observed source-Open=1 rows;
(4) issued raw-forecast-available keys on the requested grid and the subset matching observed
targets; and (5) evaluation-eligible observed source-Open=1 rows with an available raw forecast.
Also report interval-, schedule-, and operational-availability counts with their own denominators.
Missing target rows and unavailable forecasts never become zero.

`metrics.summarize_forecast_metrics` expects observed target records with the accepted metric
fields. Its `observed_target_rows` is `len(records)`; it is not the number of requested grid keys.
Pass observed outcome records joined to immutable forecasts, and report the requested-grid count
separately. Do not pad observed records with synthetic missing-label rows to make the requested
and observed counts agree.

- **Primary:** MAE on observed source Open=1 keys with available issued raw forecasts.
- **Secondary:** RMSE, MAPE and WAPE on that same clearly reported population, plus exact-horizon
  and calendar-block diagnostics. MAPE excludes only actual zero values and reports the
  nonzero denominator; it uses no epsilon. WAPE is null if the observed-sales sum is zero.
- **Intervals:** report marginal daily hit rate/coverage and width on observed Open=1 keys with
  available issued intervals; report the eligible-label and issued-interval denominators
  independently. Cumulative prefix outputs are evaluated only on complete valid prefixes and
  remain dependent, origin-anchored errors, not simultaneous or service guarantees.
- **Operational diagnostics:** keep actual Open=0, Open=1 and unknown populations separate.
  Do not let closure-routed zeros inflate the primary raw-forecast metric. Pool ratios from
  numerators/denominators, never by unweighted averaging of subgroup ratios.

Proposed comparator scope: accepted selected LightGBM is the sole primary final point system.
The frozen Seasonal Naive algorithm may be reported as a contextual comparator under a separately
precommitted issuance protocol. Report standalone populations and an exact common-row comparison
as separate results; the common rows are those observed source-Open=1 targets for which both
issued raw forecasts are available. Do not rank/select a winner, reopen model selection, add a
candidate, or use Holt-Winters as a final comparator.

## 11. Monitoring definitions and alert strategy

Use descriptive pandas summaries. Proposed windows are one calendar day, trailing 7 calendar
days, and trailing 14 calendar days, recomputed after each authorized daily release. Startup
windows are explicitly partial until they contain 7 or 14 released calendar days; record the
nominal window length, actual day count, and partial-window flag. No bootstrap, statistical
control limit, numeric drift threshold, or numeric MAE, interval-coverage, or service alarm is
proposed.

For each window, report its exact population and numerator/denominator: requested keys; observed
outcome rows; source-Open=1 observed labels; raw forecasts available on requested keys and on
observed targets; point-evaluation-eligible rows; available issued intervals and interval-eligible
labels; and schedule/operational availability. Point errors use the accepted observed source-
Open=1 plus available-raw-forecast population. Daily interval coverage uses observed source-Open=1
labels with an available issued interval and reports interval-available and eligible-label counts
separately. Feature summaries describe only the origin-known covariates and issued raw-path
predictors against that fit's origin-safe training reference; use counts, missingness, and
descriptive frequencies/quantiles, without Sales-derived cohorts or a numeric drift statistic.

Every released record retains its block origin and forecast horizon. A 7/14-day window that spans
the July 17 boundary is labeled as a multi-origin window and keeps origin/horizon breakdowns;
do not imply one common horizon or origin across both blocks. Recursive lag-feature differences
as forecasts replace actual history remain descriptive.

Alerts are limited to deterministic integrity and data-quality contract violations, such as a
changed identity/hash, duplicate or missing requested key, invalid schema/value, blocked-path
attempt, out-of-order event, or incomplete required provider response. An unavailable prediction
or unknown planned Open remains an explicit status with its reason. ADR-021's 40-row daily and
50-prefix cumulative floors define calibration estimators only; they do not establish monitoring
reliability or justify a monitoring alert. Under recommended Option B, there are no new July
inventory KPIs or service alerts. Do not claim statistically reliable drift from two final blocks
or 28 days.

## 12. Inventory scope decision and alternatives

**Option B — defer final-holdout inventory (TECHNICAL LEAD RECOMMENDATION / OWNER APPROVAL
PENDING).** This is a recommendation only; Option B is NOT ACCEPTED and does not yet change
scope. If later approved, do not run a new July inventory simulation or make July inventory
claims. Preserve the completed Phase 10 development simulation, its canonical artifacts, and its unfavorable
forecast-policy cost results unchanged. This does not erase the accepted development evidence or
claim that inventory value is physical stock, actual service, or savings.

If the owner approves Option B, the following normative requirements need an explicit acceptance
adjustment before implementation; they remain unchanged in this review:

- `PROPOSAL.md` §24's sequential-monitoring step that updates simulated inventory KPIs each day
  and §24.1's business/service alert examples would not describe the July replay.
- `PROPOSAL.md` §26 Monitoring's business-monitoring/alert criteria need to say whether the
  completed Phase 10 development evidence suffices and that no July inventory/service alert is
  produced. The broader Phase 10 development simulation and sensitivity work in §§17.1 and 19
  remain completed evidence; any claim that they require a July holdout simulation must be
  explicitly rejected or revised.
- `PROPOSAL.md` §26 Business's service/cost comparison criterion should identify the completed
  Phase 10 development comparison as its evidence and state that Option B supplies no July
  inventory comparison; adjust it only if that criterion is currently interpreted as requiring
  final-holdout inventory results.
- `PROJECT_PLAN.md` Phase 13 deliverables' “KPI summaries” and its acceptance paragraph requiring
  additional operational origins, supported protection coverage, and common terminal censoring
  need to exclude July inventory KPIs under Option B and point to the retained Phase 10 evidence.
  Phase 14 reporting would then state that no July inventory result exists.

**Option A — rejected alternative under the current recommendation; final owner choice pending.**
It would extend the accepted Phase 10 method to two separate July H14 episodes under its existing
policies, paired exogenous inputs, R=1/L=2–7/P=L+1 rules, standing targets, event timing,
no-queue-carry boundary, terminal treatment, cost/KPI definitions and caveats. It would use only
approved planned Open and daily revealed monetary Sales as the turnover proxy. It also requires a
new Phase 9 56-day July-origin context under the same approved formulas, seed/key grammar, and
value ranges, with new traceable identities; June targets/scenarios cannot be redated or
regenerated. This is a new origin-context design and needs explicit approval. The episodes are not
continuous 28-day inventory operation; standing targets may become stale, and transported Fit B
buffers do not establish July or synthetic-case coverage. Choosing A would require reopening the
inventory recommendation and exact acceptance implications above; this proposal does not
authorize that implementation.

## 13. Failure handling, restart, and recovery

Fail closed before publication on wrong base/recipe/hash, unsafe path, unexpected key/schema,
future-row cutoff, covariate provenance error, unsupported required input, fit exception, or
incomplete forecast grid. No baseline fallback, partial block issuance, or silent null-to-zero
conversion. Preserve native row-level unavailability only where the accepted forecaster permits
it and record reasons.

Before publication, discard staging output and permit a clean retry only after validation against
the same frozen configuration and input identities. After publication, never refit or rewrite
that issuance; resume from the verified issuance receipt and last complete daily checkpoint.
If a crash occurs after a `release_intent` is durably persisted but before evaluation and its
checkpoint complete, treat that date as potentially accessed; the intent cannot be silently
rolled back and does not prove whether content was mechanically read or analytically revealed.
Block all later dates. On restart, reconcile the same block/date/sequence, issuance, provider, any
separate staging authorization, and projection identity/provenance with the trusted operator. For
an existing partition, verify its documented prior staging authorization and provenance from
records without opening its contents. Resume evaluation idempotently only from that exact authorized
projection and intent, after the per-day intent and separate analytical-release authorization; if
its identity or exposure state cannot be established, mark the run incomplete and require a new
explicit recovery decision before any further release. Never infer that access did not occur merely
because no checkpoint exists.

Release/evaluation failure stops the next outcome release until reconciled. Idempotent replay of
the same authorized date identity returns the existing checkpoint; changed duplicate or
out-of-order data aborts. Mark incomplete runs explicitly and do not calculate complete-block
metrics from them.

## 14. Required provenance and manifests

The issue manifest binds protocol/configuration hash; code commit and clean/modified state;
model name and selected Phase 7 lineage; the accepted selection run
`365f22d4c3f94722a594ab934a22c4f6`, selection manifest
`03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc`, selected configuration
`de53a477b4bed768a9fbaa459e7f347be28c05063f5c5e379c0dfbb40d21960b`, and refit recipe
`9ef3ee340ac57f14394857203ca3de5445ebae70972ec541a51947f38a49f799`; all parameter dictionaries,
requested/actual rounds and fit origin;
29-feature schema/order/dtypes/hash; category values/order/hash; allowed training-row identity,
date cutoff and eligible counts; covariate/schedule schema, provenance, version and hashes;
Fit B run/table/config identities; requested grid identity; booster and adapter hashes; seed;
Python, LightGBM native build, numpy/pandas/pyarrow, OS/architecture, CPU/thread settings,
uv version and lock hash; output schemas/hashes; and publication receipt.

The day journal binds each ordered reveal projection and checkpoint to the immutable issuance.
The final assessment manifest binds all released projections, issued ledgers, evaluation code,
metric definitions/populations, monitoring outputs, inventory outputs if approved, and report
hashes. Never hash sealed unreleased outcome contents from the issuance identity. Inherit
previously accepted full-source snapshot identifiers as recorded metadata; do not rehash the
full source as a preflight shortcut.

## 15. Leakage prevention and adversarial tests

Before release, fixtures must demonstrate:

- A2 independently staged, provider-scoped views; default-deny file/path/field/date guards;
  reject unsafe paths/dates before content access; and prove synthetic fixtures cannot access an
  unprovided projection. A1 NTFS/account isolation is optional hardening, not the mandatory test
  architecture. Do not claim physical isolation from a logical provider guard.
- Mutating unreleased Sales/Open/Customers cannot change the raw issuance for its block. Block 2
  may respond only to authorized Block 1 actuals released through July 17; Block 2 outcomes cannot
  affect its own issuance.
- Unsafe paths and dates are rejected before content hashing; fitting rejects rows after its
  cutoff; fitted-origin mismatch, warm start, recipe override, or wrong Fit B identity fails.
- Future covariate/schedule mutations affect only their authorized outputs; unknown Open never
  becomes zero; actual future Open cannot fill planned Open.
- Recursive H14 feedback, clipping, native missingness, unavailable steps, exact grid, schema,
  categories, interval signs/ranks/clipping, unsupported strata, and complete prefixes match
  accepted fixture oracles.
- Outcomes cannot alter an already issued block, frozen quantiles, thresholds, or prior daily
  metrics; daily reveals must be strictly ordered and idempotent.
- A durable release-intent event precedes every provider access; crash injection between intent,
  provider access, analytical release, evaluation, and checkpoint follows the unresolved-intent
  recovery rule and blocks the next date.
- Crash/tamper/restart at each publication, journal and checkpoint boundary retains prior
  immutable outputs and either resumes identically or fails closed.
- Point and interval denominators, missing keys, zero-sales MAPE, zero-denominator WAPE,
  operational closure separation, pooled ratios, and inventory event/terminal balances are
  verified with synthetic fixtures only.

## 16. Proposed M1–M8 implementation milestones

These are reviewable tasks for a later, separately authorized Luna 6 implementation assignment.
They are not authorized by this M0 proposal.

| Milestone | Inputs → output | Tests and dependency gate |
|---|---|---|
| **M1 — Synthetic contract/providers** | After M0 approval, implement only typed contracts and default-deny provider behavior against synthetic fixtures; no real source, local data provider, protected path, staging, ACL, or outcome access | Synthetic-only provider spies, path/date rejection before fixture access, exact grid/config checks. Requires M0 decisions and M1's own milestone approval. |
| **M2 — Fresh-fit issuer** | Frozen refit recipe and fixtures → serialized model/adapter plus label-free raw H14 ledger | Exact params, origin/cutoff, category state, future-mutation invariance, repeat/save-load. Requires M1. |
| **M3 — Fit B/schedule adapter** | Pinned Fit B and approved covariates/Open contract → distinct raw/operational issued outputs | Golden quantile application, no calibration call, unknown schedule and unsupported-prefix behavior. Requires M2. |
| **M4 — Immutable publication/replay state** | Issued outputs → manifest-last block publication, receipts, durable release-intent/release journal, checkpoints | Two-block chronology, A2 provider boundary (A1 optional), atomic failure, crash/restart/tamper/idempotency. Requires M3. |
| **M5 — Metrics/monitoring** | Approved populations/windows → post-release descriptive summaries and deterministic integrity/data-quality alerts | Missing/zero denominators, daily/partial 7/14-day windows, origin/horizon boundary labels, no numeric statistical alert or adaptation. Requires M4. |
| **M6 — Inventory adapter (conditional)** | Option A only if explicitly selected and approved → July episode contexts and incremental daily state | Under recommended Option B this milestone is conditionally INAPPLICABLE, not cancelled; if the owner chooses A, reopen its design and approve scope first. No June artifacts change. |
| **M7 — Integration/review package** | M5 and M6 only if applicable → fixture-only implementation, provenance and operational review | Locked Windows/Python 3.14 reference plus supported Python 3.12/3.14 quality checks as approved; docs checks; protected provider not mounted; Phase 7–10 preservation. Requires applicable milestones. |
| **M8 — Separate release gate** | Reviewed code/config/artifact hashes → decision record for a specific authorized release | Independent review plus explicit Technical Lead/owner authorization; any protected-source staging has its own prior authorization; M0 or this PR is insufficient. Requires M7. |

## 17. Acceptance criteria and verification matrix

| Area | Proposed acceptance evidence | Release prerequisite? |
|---|---|---|
| Phase and scope | Current plan/PR explicitly remain PROPOSED / NOT APPROVED; all methodology choices remain pending; implementation, protected-data staging, analytical release, and closeout approvals are distinct | Yes |
| Git/artifacts | Branch based on current `origin/main`; unchanged Phase 7–10 artifacts and manifests; all new outputs immutable and identified | Yes |
| Recipe/forecast | Two fresh, exact trial-A refits; 29 ordered predictors; exact fixed params, cutoffs, categories, seeds; complete H14 grid; raw/operational separation | Yes |
| Chronology/custody | Two fit origins only; immutable block issuance; A2 provider-scoped default-deny boundary or explicitly approved alternative; durable release intent precedes access; chronological daily release | Yes |
| Uncertainty | Exact pinned Fit B identities/formulas applied without fitting; availability/sign/clipping/prefix behavior preserved; June-to-July transport limitation disclosed; final coverage only after authorized release | Yes |
| Evaluation | Fixed 31,220-key request grid reported separately from observed targets; observed/Open=1/forecast-available/evaluation-eligible counts and accepted formulas retained | Yes |
| Monitoring | Daily and descriptive trailing 7/14-day windows; partial startup windows and origin/horizon labels; exact populations/denominators; deterministic integrity/data-quality alerts only | Yes |
| Inventory | Option B only after explicit owner approval and acceptance adjustment, with M6 conditionally inapplicable; or Option A after separately approved design/scope | Yes if Phase 13 acceptance retains inventory |
| Recovery/provenance | Failure injection, unresolved-intent stop/reconciliation, idempotent resume, journal/checkpoint and manifest verification; locked Windows/Python 3.14 identity and proposed save/load tolerances recorded | Yes |
| Review/authorization | Full fixture/quality evidence, independent final technical review, and separate exact release approval | Yes |

Development replay uses only synthetic fixtures until an independent implementation review
authorizes any development-data rehearsal. CI remains fixture-only and must not mount protected
local artifacts. This proposal and a passing documentation check do not satisfy these gates.

## 18. Open decisions requiring Technical Lead and owner review

The following table tracks independent audit findings P13-01 through P13-09. **Every material
choice is PENDING APPROVAL; none is ACCEPTED by this document.**

| ID | Recommended choice | Approval status | Remaining input needed | Exact acceptance implications |
|---|---|---|---|---|
| P13-01 Protocol/release | Keep the two fixed H14 blocks and separate design, implementation, protected-data staging, analytical-release, and closeout gates. | PENDING APPROVAL | Technical Lead/owner approval of the frozen chronology and the distinct future gates. | No implementation starts until M0 is approved; no target content is staged or released under this plan. A later release must name its exact reviewed code/configuration, provider, block, and operator. |
| P13-02 Inputs/population | Fixed 1,115-store requested grid; separate origin-safe providers; unchanged 29 predictors; optional nullable planned Open; fail closed. | PENDING APPROVAL | Approve roster, each field/source availability assumption, and whether a planned-Open provider exists. | No predictor/schema change or future-data extraction; unknown planned Open leaves dependent operational outputs unavailable. Narrowing the roster or changing predictors needs a separately approved scope/design revision. |
| P13-03 Custody/ledger | Recommend A2 independently staged input views, provider-scoped default-deny path/date/field guards, immutable issuance, chronological journal, and a trusted operator; keep A1 Windows identities/NTFS ACLs optional. | PENDING APPROVAL | Accept A2's logical/operator-enforced limit and trusted-operator assumption, or choose optional A1. Separately authorize any later mechanical staging that reads protected source content. | A2 does not promise isolation from the operator/admin. Mechanical staging authorization is distinct from analytical release. No staging or protected-data access occurs in this task. |
| P13-04 Frozen uncertainty | Preserve exact frozen Fit B identities and ADR-021 estimators; no refit/recalibration; disclose transport to July fresh fits. | PENDING APPROVAL | Approve or reject applying the June-calibrated tables to both July fresh fits. | If transport is rejected or an exact identity/stratum is unsupported, affected intervals, operational bounds, and dependent outputs remain unavailable; changing that result scope requires an explicit acceptance adjustment. |
| P13-05 Inventory | Recommend Option B, no July inventory simulation; preserve Phase 10 evidence/results. Keep Option A as the rejected alternative pending the final owner choice. | TECHNICAL LEAD RECOMMENDATION / OWNER APPROVAL PENDING | Owner's explicit choice between B and reopening A for design. | If B is approved, explicitly adjust the Proposal §24/§26 July monitoring and business expectations and Phase 13 KPI/additional-origin/protection/terminal-censoring requirements listed in §12; do not edit them before approval. M6 is then conditionally INAPPLICABLE, not already cancelled. If A is chosen, approve its new July-origin context and exact scope before implementation. |
| P13-06 Monitoring | Daily plus descriptive trailing 7/14-day windows, exact populations/denominators, partial startup flags, origin/horizon labeling, deterministic integrity/data-quality alerts only. | PENDING APPROVAL | Approve descriptive populations/windows and the boundary-crossing presentation; confirm no statistical alert thresholds. | No numeric MAE, drift, interval-coverage, or service alarms; ADR-021 calibration floors are not monitoring reliability. If accepted, adjust Proposal §26 Monitoring and Phase 13 alert deliverables if they are read to require statistical drift or business thresholds. |
| P13-07 Runtime/repro | Recommend locked Windows/Python 3.14; compare frozen identities exactly; propose prediction save/load `rtol=1e-12`, `atol=1e-9`. | PENDING APPROVAL | Approve the environment reference and proposed tolerance. | Tolerances are proposals, not accepted results; reproducibility claims are bounded to the pinned environment/build and do not promise cross-platform bitwise equality. |
| P13-08 Scores/comparator | LightGBM sole primary system; frozen Seasonal Naive contextual comparator; separate exact common-row comparison; no renewed selection or Holt-Winters final comparator. | PENDING APPROVAL | Approve exact Seasonal Naive issuance and common-row reporting protocol. | Report standalone and common-row populations separately under ADR-013 metrics; do not select a new winner or present this as renewed model selection. |
| P13-09 Status/docs | Record PR #34's verified merge at `4f2f9dc407109efea8401ff3b19894e104ad764e`; keep this revision PROPOSED / NOT APPROVED and Phase 13 PLANNED / NOT AUTHORIZED. | PENDING TECHNICAL LEAD REVIEW | Review the M0.1 corrections and resolve/defer P13-01–P13-08. | No accepted ADR, implementation status, or completion claim follows from this documentation review; preserve earlier dated checkpoints as historical records. |

## 19. Explicit implementation and release authorization gates

1. **M0 review:** Technical Lead/owner resolves or explicitly defers each applicable choice and
   approves a frozen Phase 13 design. This draft PR itself does not approve the design.
2. **Implementation:** A separate task authorizes M1 onward within the approved scope. M1 is
   limited to synthetic fixtures. No implementation starts from this documentation authorization
   alone.
3. **Protected-source staging:** For newly created outcome projections, issue and persist the whole
   block first; then persist that date's `release_intent`; then obtain separate explicit
   authorization before mechanically reading protected source content to create/access only that
   date's projection. Existing partitions from earlier custody work require documented prior
   authorization and provenance before use. Document any earlier mechanical reads as protected-data
   access, separate from analytical outcome revelation; they do not authorize new staging or
   evaluation access. No staging, source read, or release is authorized or performed by this task.
4. **Implementation review:** Fixture tests, quality checks, provenance, A2 custody/recovery
   evidence (or an approved alternative), and independent review pass. Phase 7–10 evidence remains
   unchanged.
5. **Analytical release:** A separate explicit authorization names the reviewed commit,
   configuration, approved provider, exact block/date, trusted operator, and release procedure.
   For each date, the verified complete-block issuance and durable `release_intent` precede any
   source/projection access; newly staged projections also require the separate staging authorization
   in Gate 3. Release only that date to evaluation, then finish its checkpoint before advancing.
6. **Closeout:** Only after the authorized run, independent result review, acceptance of remaining
   scope adjustments, and explicit phase closeout may Phase 13 be called COMPLETE. Phase 14 remains
   outside this plan.

**Current boundary: STOP at M0.1 pending Technical Lead and owner approval.**
