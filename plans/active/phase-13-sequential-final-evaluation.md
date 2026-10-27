# Sequential Final Evaluation Protocol

**Method selected; fixture milestones M1–M3 integrated; Phase 13 PLANNED / NOT APPROVED.**
Independent Sol 6.1 review of M3 uncertainty/schedule/target adapters and all later milestones
remain open. No final replay, real-source access, protected staging or analytical release is authorized.

## Objective and dependencies

Evaluate the frozen Store × Date monetary Sales system in two issue-before-reveal H14 blocks.
Retain the selected LightGBM trial A/180-round recipe, 29 predictors, exact frozen June Fit B
uncertainty, Seasonal Naive contextual comparator and two independent standing-target inventory
episodes. [Decisions](../../docs/DECISIONS.md) owns the accepted method; the
[roadmap](../../docs/PROJECT_PLAN.md) owns remaining deliverables and
[results](../../docs/PROGRESS.md) owns existing evidence. No new winner, policy or model is selected.

Reuse the origin-parameterized training/recursive APIs in `forecasting/lightgbm.py`, the frozen
refit recipe in `forecasting/model_selection.py`, shared metrics, and the implemented `phase13/`
contracts/providers/issuer/adapters. Development runners still stop at July 3; the uncertainty
estimator recalibrates and the batch simulator restricts June origins, so none is an unchanged
final-replay entrypoint. Missing publication/journal/monitoring/incremental inventory work remains gated.

Fit B daily development coverage was 91.26%, below nominal 95%; recorded inventory cost differences
were unfavorable. Earlier full-source descriptive exposure is disclosed in
[EDA findings](../../docs/EDA_FINDINGS.md). Do not treat the holdout as pristine or reuse full-period
cohorts. Separate source/preparation/custody provenance, named operator, resources and review are
execution prerequisites. Integration and tests are not independent acceptance or phase completion.

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
4. **Synthetic planned Open:** a separately versioned operational schedule generated from the
   selected Monday–Saturday-open / Sunday-closed rule and calendar keys. This is a conditional
   planning assumption, not observed operation, and is never inferred from future actual Open.
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

**Selected A2 — independently staged inputs with provider-scoped access:** give each input
view its own staged projection and provider. Default-deny every unlisted provider, file, path,
field, and date; reject unsafe paths and dates before content access; keep issued outputs immutable;
and record durable, chronological release-intent, release, and evaluation-checkpoint events. A
trusted operator controls staging and day release and is part of the trust assumption. A2 is a
logical/operator-enforced boundary and does not provide strict physical isolation from that
operator, a hostile machine owner, or an administrator. Separate Windows accounts and NTFS ACLs
are optional hardening under A2. Design and operation still require explicit separate
authorizations for mechanical staging and analytical release.

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
[model-selection contract](../../docs/DECISIONS.md#adr-020--development-only-model-selection-and-frozen-refit-policy),
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
state. Use the selected locked Windows x64 / Python 3.14 reference environment from portable locked-environment policy, using
the repository `uv.lock` and pinned uv version; record the LightGBM native build and environment
identity. Require exact equality for frozen recipe/configuration, ordered feature schema,
categories, input/output identities, requested keys, and pinned Fit B table identities. For
same-environment booster save/load prediction comparison, require `rtol=1e-12` and `atol=1e-9`.
If fixture verification fails, stop for a new reviewed tolerance decision; never loosen these
tolerances after protected results are observed. Record full environment, native build, and runtime
identity. Do not claim bitwise identity across operating systems, compilers, or LightGBM builds.

## 6. Origin-known covariates and planned Open

Use separately versioned tables keyed by Store × Date with schema version, source/version,
extraction time, availability assumption, null policy, content identity, and approved use. Keep the exact
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
  Retrospective schedule covariates from the historical source use an explicitly documented
  conditional assumed-known-at-origin availability assumption; a stored value does not prove
  historical availability. Do not derive them from Sales, Customers, or target outcomes. The source
  identity, provenance, safe acquisition, and authorized preparation remain preflight requirements.
- **Planned Open:** a separately versioned schedule generated from the selected weekly planning
  rule and calendar keys, with its rule identity and conditional-assumption provenance. Do not infer
  it from actual future Open, target labels, future customer counts, or later closure records.

Keep these schedule concepts distinct. Deterministic Date/weekday values come from the calendar.
Static Store metadata and conditional future covariates require their own source/version and
origin-availability assumptions. Use the selected Monday–Saturday-open/Sunday-closed pattern as a
conditional synthetic planning schedule for scenario and observed-Sales-reference simulations; it
is not observed or historically proven Rossmann operation. `ScenarioOpen` remains the Phase 9
scenario schedule, and planned operational Open is a distinct schedule field for routing issued raw
forecasts. Observed source `Open` is available only after the matching date is authorizedly
revealed, for eligibility, diagnostics, and schedule-mismatch reporting. It never fills planned
Open. A planned closure never overwrites positive observed Sales or synthetic demand.

Future actual `Open` is never a planned schedule or a predictor. Unknown planned Open remains
unknown. It is not zero, `Open_resolved`, or a reason to overwrite the raw forecast. Raw
predictions are emitted before any operational routing. If a required
predictor row/value is absent, use only the accepted native missing-value behavior where that
feature contract permits it; otherwise mark the prediction unavailable with a reason. If
planned Open is absent, raw points may remain available while operational points, routed
intervals, cumulative operational bounds, and inventory targets that depend on it are null.
No protected actual value fills a missing covariate. This method selection authorizes no future-data
extraction, including retrospective promotion/holiday covariate extraction. If required covariates
exist only in a combined source containing protected Sales/Open, a separately reviewed safe
preparation and custody procedure is required before any access to that source. Column projection
alone does not establish physical isolation. Fail closed if input provenance cannot be established.

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

**SELECTED METHOD — UNVALIDATED transport assumption:** apply the already accepted frozen Fit B
daily residual quantiles and cumulative-prefix quantiles unchanged to both July blocks, subject to
the exact-identity and transport-compatibility requirements below. Pin the accepted identities in `phase13/adapters.py` and the immutable runtime bindings.
The June calibration source, each July fresh fit and each origin-safe input/schedule retain distinct
identities; equality of their names is not the transport requirement.

The accepted Fit B governance record supersedes the manifest's publication-time
`fit_b_quantiles_frozen=false` field for these exact identities. Preserve that historical manifest;
do not regenerate or rewrite it.

**Identity and transport compatibility.** Require exact equality to the pinned frozen Fit B daily
and cumulative quantile-table identities and hashes, and to the accepted calibration policy/config
identity, including the `calibration_config.json` hash. Each July fit must use the accepted selected
model recipe and ordered feature contract. Apply only the exact matching horizon or cumulative
prefix and probability-level entry. Preserve the saved signed values, rank definitions and sample
floors, availability/reason semantics, and clipping rules verbatim; a July fit does not create or
replace a calibration identity.

Record distinct identities and complete provenance for (1) the historical June Fit B calibration
source and calibration fit/run, (2) each July fresh model fit at origin 2015-07-03 or 2015-07-17,
and (3) that origin's origin-safe forecast-input and schedule sources. Complete provenance is
required for both the historical calibration side and, if separately authorized for use, the July
application side, including its fresh fit and input/schedule sources. Do not require literal equality
between the June calibration fit-run ID and a July fresh-fit ID, or between the historical
calibration source identity and a newly authorized July source identity. Instead, verify that the
separately identified July fit, inputs, and schedule satisfy the selected recipe, feature,
availability, schedule-compatibility, and other conditions of the approved transport contract.

If an exact identity or required compatibility condition fails, or either side's provenance is
incomplete, preserve the applicable unavailable status and saved reason semantics; do not silently
substitute another table, source, horizon, or model. This check establishes conformance to the
declared UNVALIDATED transport contract only. It is not evidence that June quantiles transport
statistically to July or that empirical coverage will be achieved.

**A. Fit B calibration evidence (historical observations).** Under the
[accepted uncertainty method](../../docs/DECISIONS.md#adr-021--chronological-empirical-forecast-uncertainty-and-conditional-operational-replay), daily calibration residuals
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
saved identities and the identity-and-transport-compatibility requirements above, and frozen
availability/reason fields. For a daily issued raw point `yhat_h`, emit endpoints
`max(0, yhat_h + q_low,h)` and `max(0, yhat_h + q_high,h)`, retaining signed quantiles,
pre-clipping endpoints/flags, availability, and the accepted unsupported reason. For a complete
cumulative operational prefix `k`, use
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
guaranteed. If the exact frozen table or calibration policy/configuration identity, selected recipe
or feature contract, horizon/prefix/probability, sample floor, availability/reason semantics,
provenance, or required schedule compatibility is unsupported, preserve the applicable unavailable
status and saved reason semantics. Keep raw forecasts/intervals distinct from planned-Open-routed
operational forecasts/intervals and cumulative outputs.

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

Selected score/comparator protocol: accepted selected LightGBM is the primary final point system.
Include the existing frozen Seasonal Naive as a contextual comparator with immutable H14 issuance
before outcome revelation. Report standalone populations and an exact common-row comparison as
separate results; the common rows are those observed source-Open=1 targets for which both issued raw
forecasts are available. Do not rank/select a winner, reopen model selection, add a candidate, or
use Holt-Winters as a final comparator.

## 11. Monitoring definitions and alert strategy

Use the selected descriptive daily, trailing 7-calendar-day, and trailing 14-calendar-day summaries,
recomputed after each authorized daily release and stratified by block origin and forecast horizon.
Startup windows are explicitly partial until they contain 7 or 14 released calendar days; record
nominal length, actual day count, and partial-window flag. No bootstrap, statistical control limit,
or numeric drift, performance, interval-coverage, or service alarm threshold is selected.

For each window, report its exact population and numerator/denominator: requested keys; observed outcome rows; source-Open=1 observed labels; raw forecasts available on requested keys and observed targets; point-evaluation-eligible rows; available issued intervals and interval-eligible labels; and schedule/operational availability. Point errors use the accepted observed source-Open=1 plus available-raw-forecast population. Daily interval coverage uses observed source-Open=1 labels with an available issued interval and reports interval-available and eligible-label counts separately. Feature summaries describe only origin-known covariates and issued raw-path predictors against that fit's origin-safe training reference; use counts, missingness, and descriptive frequencies/quantiles without Sales-derived cohorts or a numeric drift statistic.

Every released record retains its block origin and forecast horizon. A 7/14-day window spanning July 17 is labeled multi-origin and keeps origin/horizon breakdowns. Recursive lag-feature differences as forecasts replace actual history remain descriptive.

Show descriptive feature-distribution shifts and post-release forecast errors and interval coverage
with their populations and denominators. Feature summaries use origin-safe references without
Sales-derived cohorts. Precommit deterministic integrity and data-quality alerts only, such as
changed identities, duplicate/missing keys, invalid schema/value, blocked-path attempt, out-of-order
event, or incomplete provider response. Alert definitions remain independent of final outcomes.
An unavailable prediction or unknown planned Open remains explicit with its reason. The
[uncertainty method's](../../docs/DECISIONS.md#adr-021--chronological-empirical-forecast-uncertainty-and-conditional-operational-replay)
40-row daily and 50-prefix cumulative floors define calibration estimators only; they do not
establish monitoring reliability. Under the owner-approved A-bounded inventory scope, update
inventory state and descriptive KPIs after each authorized daily release; label episode-to-date
values partial through H14. Rolling 7/14-day inventory summaries retain block origin, episode reset,
released-day count, and partial-window status; do not present the reset episodes as continuous
inventory. Receipt-cycle service uses its accepted completed-cycle denominator and triggers no
alert. Do not claim statistically reliable drift from two forecast blocks or 28 days.

## 12. Inventory scope decision and alternatives

### Owner approval — scope only

**Owner decision, 2026-10-10: Option A-bounded inventory scope APPROVED — SCOPE ONLY.** The [approved inventory scope](../../docs/DECISIONS.md#adr-025--phase-13-a-bounded-inventory-evaluation-scope) specifies two independent H14 origin-frozen standing-target episodes at the July 3 and July 17 origins, the full precommitted scenario/sensitivity panel subject to its resource-feasibility gate, daily chronological simulated state/KPI evaluation under Phase 10 mechanics, and the accepted limitation that later reviews have no fresh calibrated protection-period forecast. The owner also explicitly accepts that these episodes do not demonstrate continuous rolling 28-day inventory validation. The Technical Lead selected the remaining P13 methods under the [final-evaluation methodology](../../docs/DECISIONS.md#adr-026--phase-13-selected-sequential-evaluation-methodology). Method selection is not implementation approval; source/preparation provenance, operator, resource, implementation, rehearsal, staging, and analytical-release preconditions remain open.

### Approved bounded episodes

| Block | Inventory/model origin | Target and reveal dates | History allowed at origin |
|---|---|---|---|
| 1 | 2015-07-03 | July 4–17, H1–H14 | Through July 3 |
| 2 | 2015-07-17 | July 18–31, H1–H14 | Through July 17, including Block 1 outcomes only after authorized chronological releases |

These are the existing two primary forecast origins; no additional forecast origin or primary forecast test is introduced. Each block is a separate cold-start inventory episode. No inventory, order queue, or target carries between episodes. Report both terminal states and outstanding commitments; the episode reset is an evaluation boundary, not a claim that real stock or orders were canceled.

Retain the accepted Phase 10 policies, historical_mean_standing_target and lightgbm_buffer_standing_target, R=1, L in 2..7, P=L+1 in 3..8, p=.95 reference, accepted paired exogenous inputs, order/receipt timing, lost-sales state, KPI definitions and limitations. Preserve the exact one-factor overlays `buffer_090`, `buffer_098`, `lead_2`, `lead_7`, `holding_010`, `holding_030`, `goodwill_010`, `goodwill_075`, and `coverage_1`. Freeze each policy target at its block origin for all 14 days. The selected method prohibits warm starts, daily target refresh, suffix calibration, new quantile estimation, policy selection, and outcome-driven adaptation.

Preserve the accepted Phase 10 target equations, with `m` the Phase 9 open-day turnover anchor, `z_h` the origin-known open indicator, `operational_point_h` the issued operational LightGBM point forecast, and `q_(p,P)` the exact saved signed Fit B cumulative-error quantile for prefix `P` and level `p`:

```text
S_base = m * sum(z_h for h=1..P)
D_P = sum(operational_point_h for h=1..P)
U_P = max(0, D_P + frozen_q_(p,P))
SafetyStock_P = max(0, U_P - D_P)
S_forecast = D_P + SafetyStock_P = max(D_P, U_P)
```

Use the saved quantile only when its identity, exact prefix, level, availability conditions, 50-prefix floor and valid rank are supported; otherwise that forecast-driven target is unavailable with its recorded reason and no fallback. The issuance uses only the frozen saved `q_(p,P)` and issued operational forecasts. Historical calibration observations determine Fit B's signed cumulative-error evidence; July Sales can enter evaluation of cumulative error and empirical coverage only after authorized chronological revelation. July outcomes and newly fitted quantiles are never inputs to uncertainty-bound issuance.

The explicit coverage limitation is:

- The H14 standing target is fixed at its block origin; later daily reviews execute that same target.
- No new rolling forecast or daily-review suffix calibration is performed.
- Not every later review has complete forecast-supported protection-period coverage.
- The episodes do not demonstrate continuous calibrated 28-day inventory operation.

The simulation evaluates the precommitted standing policy's daily state transitions and paired H14 outcomes. It cannot describe each later order as a newly forecast, calibrated protection-period recommendation. The [inventory scope decision](../../docs/DECISIONS.md#adr-025--phase-13-a-bounded-inventory-evaluation-scope) accepts this exception; the [final-evaluation methodology](../../docs/DECISIONS.md#adr-026--phase-13-selected-sequential-evaluation-methodology) defines execution. Method selection does not satisfy implementation or data-access gates.

### July contexts, schedules and uncertainty

Use new origin-specific 56-calendar-day Phase 9 contexts under the accepted anchor and generator contracts:

- July 3 origin: May 9–July 3.
- July 17 origin: May 23–July 17, with released Block 1 observations available only after July 17.

Require at least 28 valid observed Open=1 history rows. Keep missing dates absent, preserve zero anchors and unavailable stores, retain seed 4209, accepted SHA-256 key grammar, ranges, scenario families, common shocks and sensitivity overlays. Create new July context identities; do not redated-copy or regenerate accepted June canonical artifacts.

For each block, finish and verify its complete raw H14 forecast issue, apply only exact saved Fit B entries whose identities and availability conditions match, create the origin-safe inventory context, freeze both policy targets, and persist starting inventory and origin orders before accessing any outcome for that block. Keep historical Fit B calibration-fit identity distinct from fresh July model-fit origin. Retain signed q, clipping, sample floors, unsupported reasons and calibration/issuance identity separation. July actuals do not create or change forecasts, quantiles or targets. June Fit B transport to July fresh fits and schedules is selected as an explicitly UNVALIDATED assumption; neither July nor synthetic service coverage is guaranteed.

Keep deterministic calendar inputs, authorized conditional future covariates, static Store metadata assumptions, synthetic ScenarioOpen, the selected synthetic Monday–Saturday-open/Sunday-closed planning schedule, and post-release observed Open as distinct fields and providers (Section 6). The selected weekly schedule is a synthetic assumption, not historical proof, and applies to scenario and observed-Sales-reference simulations. Never derive planned Open from protected actual Open. After release report schedule mismatches. Do not route away, replace with zero, or otherwise alter observed positive Sales because planned Open says closed. Source identity, provenance, safe acquisition, and authorized preparation remain preflight requirements; if needed covariates exist only in a combined source containing protected Sales/Open, separately review a safe preparation/custody procedure before any source access.

For the observed-Sales-reference case, consume only each authorized day's unchanged Sales turnover as demand proxy. Actual Open is joined only after release for evaluation eligibility and diagnostics. For synthetic cases, precommit exogenous parameters and generate each daily demand value independently of either policy; expose the same date's value to both policy states only when that simulated day is released. The target builder and order-decision function receive no future synthetic demand values.

### Paired daily simulation and outcomes

Initialize both policies with the same origin-safe stock, zero on-order pipeline and zero backorders. Share schedule, lead time, c/a/g costs, family, replicate, variant and exogenous demand path. Keep separate policy inventory states and order queues after their decisions diverge.

For each released date, follow the [accepted inventory event order](../../docs/DECISIONS.md#adr-023--origin-frozen-daily-inventory-policy-simulation-and-finite-window-accounting): receive due orders once at BO; apply that day's demand; calculate fulfilled and unmet monetary turnover; charge holding and shortfall costs; update stock and outstanding orders; calculate inventory position; then, on days 1–13, replenish toward the unchanged origin target. An EOD order placed on day t arrives at BO-day t+L+1. Lost sales create no backlog. Day 14 processes due receipts and demand but suppresses the final order. Checkpoint both policy states atomically after the day's transitions.

Report holding cost, shortfall penalty, total simulated holding-plus-shortfall cost, value fill, positive-demand stockout-day rate, completed positive-demand receipt-cycle service proxy, average ending stock, unmet turnover, terminal stock, terminal pipeline, and late orders. Preserve accepted KPI denominators, null zero-denominator ratios, and right-censoring of the final receipt cycle. Apply common H14 terminal accounting to both policies; include terminal stock cost and outstanding procurement commitment as exposures outside the primary objective. No numeric service threshold, actual-stock claim, realized-savings claim, or causal-effect claim is authorized.

Missing target components leave that policy target unavailable without fallback. Missing daily consumption stops dependent state evolution; retain the valid prefix and exclude incomplete tracks from full-H14 metrics and matched comparisons. If one paired state cannot be checkpointed, publish neither state transition as complete for that date and stop to reconcile.

### Precommitted scenario panel and resource gate

Retain the accepted Phase 10 panel: observed-Sales reference, all eight synthetic families and five paired replicates, plus all nine accepted one-factor sensitivity overlays. The precommitted catalog contains 172 cases, 383,560 requested policy tracks, and 5,753,400 origin-plus-daily ledger records (15 records per track: origin plus 14 days). These are planned requested volumes, not evidence of available or complete tracks. Report requested, available, complete, unavailable and matched track counts separately; preserve configured stores and all unavailability reasons.

Use bounded-memory case/store partitions, deterministic key ordering, atomic paired daily checkpoints and partitioned immutable outputs. Record worker/chunk limits, peak memory, runtime, output volume and resource use during separately authorized rehearsal. Before full-panel execution, review measurements against declared execution-host budgets. If infeasible, stop and seek an explicit scope/resource decision; never sample stores or cases based on runtime or results. Do not regenerate Phase 9 or modify June artifacts.

### Alternative A-full

A-full would add precommitted operational origins and protection horizons to refresh daily recommendations. It is not recommended or included in this proposal's implementation scope. It requires a separately approved rolling-policy and calibration design, origin-safe covariate/schedule rules at each added origin, and supported uncertainty for each decision. Frozen origin-prefix q values cannot be borrowed as calibrated later-review suffix bounds. July-only outcomes also cannot fully assess protection horizons extending beyond July 31. Extra overlapping forecasts remain dependent operational decisions, not additional independent primary tests.

The source, operator, resource, rehearsal, staging and release preconditions below remain open.
Keep adverse development evidence in the [results summary](../../docs/PROGRESS.md), without
presupposing favorable July performance.

## 13. Failure handling, restart, and recovery

Fail closed before publication on wrong base/recipe/hash, unsafe path, unexpected key/schema, future-row cutoff, covariate provenance error, unsupported required input, fit exception, or incomplete forecast grid. No baseline fallback, partial block issue, or silent null-to-zero conversion. Preserve native row-level unavailability only where the accepted forecaster permits it and record reasons.

Before publication, discard staging output and permit a clean retry only after validation against the same frozen configuration and input identities. After publication, never refit or rewrite that issue; resume from verified issue receipt and last complete daily checkpoint. If a crash occurs after a durable release_intent but before evaluation/checkpoint completes, treat the date as potentially accessed; the intent cannot be silently rolled back and does not prove whether content was mechanically read or analytically revealed. Block later dates. On restart, reconcile the same block/date/sequence, issue, provider, separate staging authorization, and projection identity/provenance with the trusted operator. For an existing partition, verify documented staging authorization and provenance from records without opening its contents. Resume only from that authorized projection and intent after per-day intent and separate analytical-release authorization; if identity or exposure state is uncertain, mark the run incomplete and require an explicit recovery decision. Never infer that access did not occur merely because no checkpoint exists.

Release/evaluation failure stops the next release until reconciled. Idempotent replay of the same authorized date identity returns its existing checkpoint; changed duplicate or out-of-order data aborts. Mark incomplete runs explicitly and do not calculate complete-block metrics from them.

The inventory checkpoint is one atomic unit per case/store/date and contains both policies' stock, full outstanding-order queues (IDs, amounts, placement and due dates), frozen target identities, receipts, running demand/fulfilment/unmet/cost totals, receipt-cycle sufficient statistics, and availability/recovery status. Policy queues remain distinct after orders diverge. Commit neither policy's new state unless both ledgers and the common exogenous-date identity validate. After a crash, reconcile the authorized release intent and demand projection, then resume the same date idempotently or mark the paired case incomplete; do not recreate received orders/receipts. For synthetic cases, the day-specific demand projection is deterministically regenerated or loaded by its fixed key only after that simulated date is released. It is shared across policies and never passed to target construction.

## 14. Required provenance and manifests

The issue manifest binds protocol/configuration hash; code commit and clean/modified state; model name and Phase 7 lineage; accepted selection run, selection manifest, selected configuration and refit recipe identities recorded above; all parameter dictionaries, requested/actual rounds and fit origin; 29-feature schema/order/dtypes/hash; category values/order/hash; allowed training-row identity, cutoff and eligible counts; covariate/schedule schema, provenance, version and hashes; Fit B run/table/config identities; requested grid; booster and adapter hashes; seed; Python, LightGBM build, numpy/pandas/pyarrow, OS/architecture, CPU/thread settings, uv version and lock hash; output schemas/hashes; and publication receipt.

The day journal binds each ordered reveal projection and checkpoint to immutable issuance. The final assessment manifest binds all released projections, issued ledgers, evaluation code, metric definitions/populations, monitoring outputs, inventory outputs and report hashes. Never hash sealed unreleased outcome contents for issuance identity. Inherit accepted full-source snapshot identifiers as recorded metadata; do not rehash the full source as a preflight shortcut.

For inventory, also bind each new July context and 56-day anchor identity; generator version, seed/key grammar and parameters; separate ScenarioOpen and planned-Open provenance/assumption; future-covariate identities; scenario/case/replicate/variant; initial stock and zero-pipeline convention; distinct July model-fit origin and frozen historical Fit B calibration-fit/table identity; both target inputs/outputs and availability reasons; paired common exogenous-demand projection identity; partition ordering and requested/available/complete/matched/unavailable counts; worker/chunk settings; peak-memory/runtime/output measurements; and checkpoint/recovery receipts. July identities never replace June canonical identities. Inventory outputs are partitioned by stable case/store keys and published atomically with manifests last.

## 15. Leakage prevention and adversarial tests

Before release, fixtures must demonstrate:

- A2 independently staged, provider-scoped views; default-deny file/path/field/date guards; reject unsafe paths/dates before content access; and prove synthetic fixtures cannot access an unprovided projection. A1 NTFS/account isolation remains optional. Do not claim physical isolation from a logical provider guard.
- Mutating unreleased Sales/Open/Customers cannot change raw issuance for its block. Block 2 may use only authorized Block 1 actuals released through July 17; Block 2 outcomes cannot affect its issue.
- Unsafe paths/dates are rejected before content hashing; fitting rejects rows after cutoff; fitted-origin mismatch, warm start, recipe override, or wrong Fit B identity fails.
- Future covariate/schedule mutations affect only authorized outputs; unknown Open never becomes zero; actual future Open cannot fill planned Open; observed positive Sales is never rewritten by planned closure.
- M1 synthetic fixtures enforce fixed role-to-column schemas and reject unsafe projections before invoking a reader; reject forged Block 1 projection collections; bind Block 2 to a provider-created in-memory handoff containing exactly 14 chronological authorized Block 1 dates and the matching provider, Store roster, covariate grid/identity, and provenance; and reject any handoff that would include Block 2 outcomes. Handoff and returned frames are copy-safe. Every non-null synthetic planned-Open value follows Monday–Saturday open/Sunday closed; nullable unknowns and missing grid rows remain valid. These are logical synthetic controls, not physical isolation.
- Recursive H14 feedback, clipping, native missingness, unavailable steps, exact grid/schema/categories, interval signs/ranks/clipping, unsupported strata and complete prefixes match accepted fixture oracles.
- Outcomes cannot alter an issued block, frozen quantiles, thresholds, targets or prior daily metrics. Daily reveals are strictly ordered and idempotent.
- Durable release-intent precedes every provider access; crash injection between intent, provider access, analytical release, evaluation and checkpoint follows unresolved-intent recovery and blocks the next date.
- Crash/tamper/restart at publication, journal and paired-inventory checkpoint boundaries retains prior immutable outputs and either resumes identically or fails closed.
- Point/interval denominators, missing keys, zero-sales MAPE, zero-denominator WAPE, closure routing, pooled ratios, and inventory event/terminal balances use synthetic fixtures.
- Anchor fixtures verify exact 56-day bounds, 28 eligible Open=1 rows, integer-Sales mean arithmetic, zero anchor, missing dates and unavailability. Target fixtures verify baseline and forecast equations, signed q, exact frozen Fit B identities, and unavailable strata without fallback.
- Future-demand mutation cannot alter either frozen target, an earlier released state/order, or the other policy's shared exogenous path. Synthetic demand comes from a policy-independent date-keyed source and is invisible to target/order functions until release.
- One-day transitions reproduce existing batch simulation ledger/summaries exactly on an accepted June development fixture, including due-date order, queue, costs and day-14 boundary. This fixture does not extend that function's July contract.
- All scenarios/replicates/overlays and both policies retain requested rows and explicit available, complete, incomplete, unavailable and matched counts. Ordering/logical identities persist across bounded partitions and repeat fixture runs.
- KPI zero denominators remain null; pooled ratios use summed statistics; due-on-T and after-T orders, terminal exposure and right-censored cycles match golden fixtures.
- Atomic paired checkpoints survive crash/retry/tamper without duplicate orders/receipts; recovery and unauthorized-provider spies pass. No quantile fitting API is called and no origin-prefix q is borrowed as a later-review suffix bound.
- Resource-gate fixtures enforce worker/chunk limits and deterministic partition identity; authorized development rehearsal records peak memory, runtime and output size before full-panel execution.

## 16. Proposed M1–M8 implementation milestones

These milestones remain separately gated. M1–M3 are integrated; independent M3
review and all later milestones remain open. This plan does not authorize real-data operations,
source staging, rehearsal, or analytical release.

| Milestone | Inputs → output | Tests and dependency gate |
|---|---|---|
| **M1 — Synthetic contract/providers** | Integrated: typed contracts and default-deny providers against synthetic fixtures only. Fixed role-to-field schemas are checked before reads; Block 2 requires an in-memory Block 1 handoff registered by the synthetic outcome provider and bound to the exact covariate identity/provenance; non-null planned Open is checked against the weekly rule. | Synthetic-only spies reject unexpected fields without reads; forged Block 1 collections fail; exact chronological 14-day handoff, provider/store/grid identity, provenance and copy safety are checked; contradictory schedule values fail while unknowns and missing keys remain allowed. No real source, local data provider, protected path, staging, ACL, or real outcome access. |
| **M2 — Fresh-fit issuer** | Integrated: frozen refit recipe and fixtures → serialized model/adapter plus label-free H14 ledgers for the two existing origins. | Exact params, fit origin/cutoff, categories, future-mutation invariance, repeat/save-load, and overlapping training/history Sales consistency. No extra origin. Requires M1. |
| **M3 — Fit B/schedule/target adapter** | Integrated: synthetic Fit B-shaped fixtures and typed planned-Open schedule → distinct raw/operational uncertainty views and frozen paired H14 targets. | Exact signed quantile ranks/sample floors; calibration/model fit identity separation; no fitting, interpolation, borrowing or fallback; closure/unknown schedule routing; exact Phase 10 targets; both origins. Requires M2. |
| **M4 — Immutable publication/replay state** | Issued blocks and safe inventory inputs → manifest-last publication, receipt, release journal and paired daily checkpoints. | Two-block chronology, A2 boundary (A1 optional), paired atomicity, crash/restart/tamper/idempotency. Requires M3. |
| **M5 — Metrics/forecast monitoring** | Approved populations/windows → post-release forecast/uncertainty summaries and deterministic integrity/data-quality alerts. | Missing/zero denominators; daily/partial 7/14-day windows; origin/horizon labels; no numeric statistical alert or adaptation. Requires M4. |
| **M6 — Bounded inventory evaluation** | Accepted June fixtures and synthetic Phase 9 contracts → July-origin context schema, paired targets, incremental state, full panel, inventory KPIs and terminal accounting. | Section 15 oracles; counts by status; deterministic bounded partitions; resource gate passed or stop for scope review. No July context generation, real-data simulation or protected provider during fixture implementation. Requires M0 and separate M6 authorization. |
| **M7 — Integration and independent review** | M1–M6 → fixture-only integrated package, provenance, resource report and review evidence. | Locked Windows/Python 3.14 reference and supported Python 3.12/3.14 checks as approved; docs checks; Phase 7–10 unchanged; full panel volume and declared resource gate. Requires applicable approvals. |
| **M8 — Development rehearsal and release gates** | Reviewed code/config/resource evidence → specific development-rehearsal decision, then separate protected-release decision. | Rehearsal has separate written authorization and origin-safe development inputs. Release names commit, configuration, provider, block/date and operator; staging has its own authorization. M0 or this plan is insufficient. Requires M7. |

## 17. Acceptance criteria and verification matrix

| Area | Proposed acceptance evidence | Release prerequisite? |
|---|---|---|
| Phase and scope | Approved [inventory scope](../../docs/DECISIONS.md#adr-025--phase-13-a-bounded-inventory-evaluation-scope) and [evaluation method](../../docs/DECISIONS.md#adr-026--phase-13-selected-sequential-evaluation-methodology); implementation, rehearsal, staging, analytical release and closeout remain distinct | Yes |
| Git/artifacts | Branch based on verified origin/main; Phase 7–10 artifacts/manifests unchanged; new outputs immutable and identified | Yes |
| Recipe/forecast | Two exact trial-A fits; ordered 29 predictors; fixed params, cutoffs, categories, seeds; complete H14 grids; raw/operational separation | Yes |
| Chronology/custody | Two forecast origins; immutable block issue before outcome access; A2 provider boundary or approved alternative; durable per-day intent; chronological release | Yes |
| Uncertainty | Exact Fit B identities/formulas, signed values, floors, clipping and reasons; calibration/model origins distinct; no new fit or suffix borrowing; transport disclosed | Yes |
| Forecast evaluation | 31,220 requested primary point keys separate from observed labels, Open=1, forecast-available and eligible rows | Yes |
| Monitoring | Daily and descriptive 7/14-day windows; partial counts and origin/horizon/reset labels; exact populations; deterministic integrity/data-quality alerts only | Yes |
| Inventory method | Two independent H14 episodes; both standing-target policies; fixed targets; R=1/L=2..7/P=L+1; common inputs; no queue carry; common terminal accounting; limitation explicit | Yes |
| Inventory volume | Full 172-case panel requested: 383,560 policy tracks and 5,753,400 origin-plus-daily records; requested/available/complete/incomplete/unavailable/matched counts reconcile; no silent sample | Yes |
| Inventory outcomes | [Inventory methodology](../../docs/DECISIONS.md#adr-023--origin-frozen-daily-inventory-policy-simulation-and-finite-window-accounting): event order, lost sales, queue, costs, KPI denominators, day-14 suppression, terminal exposure and right-censored cycles match fixtures | Yes |
| Schedules/contexts | New origin-safe 56-day contexts; 28-open-row threshold; deterministic/synthetic/conditional/planned/observed schedules distinct; no future actual Open routing; positive Sales preserved | Yes |
| Performance | Stable bounded-memory partitions; measured peak memory/runtime/output fit declared host budget; otherwise stop for explicit scope/resource review | Yes before full-panel rehearsal |
| Recovery/provenance | Synthetic failure injection; unresolved-intent recovery; atomic paired checkpoint; idempotent resume; manifests/output identities | Yes |
| Rehearsal/review | Separately authorized development rehearsal; origin-safe inputs; fixture/quality evidence; independent technical review before release | Yes |

Remaining implementation begins with synthetic fixtures only under its separate authorization. A full development-data rehearsal requires its own written authorization after implementation review and before any holdout release decision; it uses origin-safe development inputs and cannot rewrite canonical artifacts. CI remains fixture-only and must not mount protected local artifacts. This proposal and a passing documentation check do not satisfy these gates.

## Implementation and release gates

1. **Pending independent review:** Sol 6.1 must assess the integrated M3 uncertainty/schedule
   routing, paired targets, fixture evidence and boundaries before dependent milestones.
2. **Source/preparation preflight:** Establish approved identities, availability assumptions,
   safe preparation and custody before any real-source read/hash. Verify existing partition
   provenance from records without opening its contents. A projection or binding grants no access.
3. **Remaining fixture milestones:** Separately authorize immutable publication/replay state,
   metrics/monitoring, incremental paired inventory and integration/recovery review. M1–M3 grant
   no canonical artifact loading, real provider, durable publication or M4 authority.
4. **Resource and development rehearsal:** Measure and approve full-panel memory/runtime/output
   budgets and separately authorize origin-safe development rehearsal. Preserve canonical artifacts.
5. **Mechanical staging:** For each new date projection, persist complete block issuance and its
   date-specific release intent first, then obtain staging authorization before source access.
   Existing projections require documented prior authorization; previous reads authorize no new access.
6. **Analytical release:** Separate authorization names reviewed code/configuration, provider,
   block/date, trusted operator and procedure. Reveal only that date, complete paired checkpoints,
   then advance. Mechanical staging is protected access, distinct from analytical revelation.
7. **Closure:** Only the authorized run, independent review, accepted scope adjustments and
   explicit closeout can complete Phase 13. Final reporting remains a separate deliverable.

The final period remains **UNRELEASED**. Stop before any unauthorized milestone or real-data operation.
