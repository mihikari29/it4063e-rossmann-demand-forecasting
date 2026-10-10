# Phase 13 — Sequential Final Evaluation Design Proposal

**State: PROPOSED / NOT APPROVED.** This is M0 documentation for Technical Lead review.
It authorizes neither implementation nor access to the protected July 4–31 outcomes.
Phase 13 remains PLANNED / NOT AUTHORIZED; Phase 14 has not started.

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

**FACT:** The proposed base is `origin/main` `2523380f606d876c2aa0024ff1b30de2fca2393a`.
Phases 0–12 are integrated and complete; the selected point model is
`global_lightgbm_gbdt_regression_l1`, trial A at 180 rounds. ADR-015 requires a separately
authorized final protocol. ADR-020 freezes the model recipe. ADR-021 freezes the development
uncertainty method and the accepted Fit B values for the identified canonical run. ADR-022/023
freeze the synthetic assumptions and Phase 10 standing-policy simulation. ADR-024 sets the
Phase 12 demonstration boundary to localhost.

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

1. **Pre-origin history:** an allowlisted Store × Date Sales/Open projection through the
   authorized origin. Fit eligibility and recursive history use their accepted separate rules.
2. **Future covariates:** a versioned, provenance-bearing origin-known feature table without
   Sales, Customers, Open, or outcome-derived fields.
3. **Planned Open:** a separately versioned nullable operational schedule; never inferred from
   future actual Open.
4. **Sealed outcomes:** Sales/Open/Customers rows for unreleased target dates, unavailable to
   the issuance identity.
5. **Revealed outcomes:** only authorized daily projections released after a matching immutable
   issuance receipt. Block 1 outcomes may join training history for the July 17 refit only after
   the full first block has been released in order.

### Local Windows enforcement

Path allowlists, schema checks, date guards, provider spies, file hashes and an append-only
application journal enforce logical behavior and expose accidental misuse. They do **not** prove
that a process never opened a combined source file or that an administrator could not bypass a
local guard. A date filter on a Parquet scan is not physical isolation.

**Proposed minimum custody mechanism for review:** a trusted local custodian stages a bounded
pre-origin history file, separate covariate/schedule files, and sealed outcome partitions under
NTFS access control. Run issuance under a Windows identity that cannot read the sealed-outcome
directory. After verifying the published block receipt, the custodian exposes only the next
date's projection to a separate reveal/evaluation identity. The custodian records the release
sequence and hashes; after the complete first-block release, the custodian stages a new
read-only history projection through July 17 for the second fit. Keep the full source and future
partitions inaccessible to the issuance identity.

This protects against accidental reads by the forecasting process, not a hostile machine owner,
administrator, or colluding custodian. Local clock values are not trusted proof of chronology.
If separate accounts and controlled staging are not feasible, disclose that the run has a
logical, operator-enforced boundary only; do not claim physical isolation. Technical Lead
approval is required for the custody model and release operator.

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
state. Require repeatable fixture results and save/load equivalence within the frozen runtime;
do not promise bitwise identity across operating systems, compilers, or LightGBM builds.

## 6. Origin-known covariates and planned Open

Propose a versioned table keyed by Store × Date with schema version, source/version, extraction
time, availability assumption, null policy, content identity, and approved use. It contains no
outcomes.

- **Deterministic calendar:** Date and DayOfWeek are derived from the requested calendar key.
- **Static metadata:** Store type, assortment, competition and related snapshot values require
  the existing disclosed course assumption that they were known at the origin; record source
  version and distinguish snapshot values from historically verified availability.
- **Holiday/promotion schedules:** StateHoliday, SchoolHoliday, Promo, Promo2 and associated
  schedule fields require source/version and an explicit origin-known provenance decision.
  Do not infer them from protected target rows.
- **Planned Open:** a separately supplied, nullable schedule with provenance. Do not infer it
  from actual future Open, target labels, future customer counts, or later closure records.

Unknown planned Open remains unknown. It is not zero, `Open_resolved`, or a reason to overwrite
the raw forecast. Raw predictions are emitted before any operational routing. If a required
predictor row/value is absent, use only the accepted native missing-value behavior where that
feature contract permits it; otherwise mark the prediction unavailable with a reason. If
planned Open is absent, raw points may remain available while operational points, routed
intervals, cumulative operational bounds, and inventory targets that depend on it are null.
No protected actual value fills a missing covariate.

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

Do not refit quantiles, tune them, recalibrate them, use final labels before issuance, or transfer
a cumulative prefix quantile to a later-review suffix.

Preserve exact-horizon availability, signed residual quantiles, lower-bound clipping at zero,
pre-clipping endpoints/flags, point-containment behavior, valid-rank/sample-floor rules, and
explicit unsupported strata. Preserve cumulative complete-prefix assumptions and signed q. Do
not sum daily upper bounds. A July refit changes fitted state; applying June Fit B to that refit
is a transport assumption requiring explicit approval and careful labeling. Report final
empirical coverage only after authorized revelation; development coverage is not final coverage.

## 9. Controlled daily outcome revelation

After verifying a block issuance receipt, the custodian releases only the next calendar date's
Store × Date observation projection in sequence. Validate date, store keys, schema and source
identity before evaluation; append an immutable release receipt referencing the issuance hash.
Retain missing rows as missing. Actual Open is joined only after release for eligibility and
post hoc diagnostics. Sales is joined only to the matching already-issued key. Customers is not
needed for this evaluation and remains excluded.

The release journal records block, date, sequence number, issuance hash, projected schema,
source/version identity, row counts, output hash, state transition and failure status. Daily
checkpoint publication is atomic and idempotent. Reject duplicate dates with conflicting
content, out-of-order release, wrong block, changed issuance, or a failed checkpoint. The
July 17 checkpoint is the only route to Block 2 training history.

## 10. Point and uncertainty evaluation contracts

Use a left join from the fixed requested grid to revealed observations and immutable issued
forecasts. Report requested, observed, source Open=1 eligible, raw-forecast-available, interval-
available, schedule-known, and operationally available counts separately by block and overall.
Missing target rows and unavailable forecasts never become zero.

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

Proposed comparator scope: selected LightGBM is the sole final point system under test. A
previously frozen development baseline may be included only as a fixed contextual comparator
if the Technical Lead approves its exact refit/issuance protocol before Block 1. Do not add a
new final candidate or reopen model selection.

## 11. Monitoring definitions and alert strategy

Use pandas summaries against development-only references. Monitoring is descriptive and emits
alerts; it cannot alter model parameters, features, category state, quantiles, schedule,
inventory policy, or final outputs.

Proposed windows and cohorts for approval:

| Diagnostic | Window and cohort | Support/threshold proposal |
|---|---|---|
| Data availability | Every target date; fixed 1,115-store requested grid (1,115 expected keys/day), then complete 7-calendar-day and 14-calendar-day block summaries | No sampled-data floor: always report requested, observed, eligible and available counts. Compare against exact expected counts. |
| Rolling point error | Trailing 7 and 14 target-calendar-day windows, recomputed after each daily reveal; all supported stores pooled on observed Open=1 rows with available raw points. Also report each exact horizon and each block separately. | Report N every time. Derive a numeric alert floor and threshold from development-only windows matching this population/window; require Technical Lead approval. No numeric trigger is accepted here. |
| Daily interval coverage | Trailing 7 and 14 target-calendar-day windows; observed Open=1 rows with available interval, pooled across supported stores; exact horizon and block summaries remain separate. | ADR-021's 40-row daily quantile floor is an estimator rule, not an approved monitoring alert floor. Propose N<40 as “insufficient for a coverage alert” for review only. |
| Cumulative/prefix diagnostics | Exact supported origin prefix k, by block and pooled only where identities/populations match; complete Store-prefix records only. | ADR-021's 50-prefix quantile floor is an estimator rule, not an approved alert floor. Propose N<50 as “insufficient” for review only; no suffix or daily-review prefix borrowing. |
| Feature distributions | Each block's origin-known predictors, overall and by fixed StoreType/Assortment from origin-time metadata; compare the block's released scheduled covariates and issued raw-path feature summaries with that fit's origin-safe training reference. | Report missingness and descriptive pandas counts/quantiles/frequencies. Any numeric drift statistic, support floor, threshold, or alert needs a frozen development derivation and Technical Lead approval. No EDA-derived Sales tiers/cohorts. |
| Inventory/business indicators | Only if Option A is approved; exact bounded episode and policy population, with paired inputs | Report supported Phase 10 denominators and costs. Do not set a service alert threshold without an approved development-only derivation. |

For point-error and feature alerts, propose calibrating limits from the distribution of matching
7/14-day development diagnostics, using Store as the resampling unit to preserve within-store
dependence and contiguous calendar blocks to retain common-day shocks. Freeze metric, cohort,
statistic, support floor, tail probability and consecutive-window rule before release. Recursive
lag-feature distributions are expected to differ from observed-history features as predictions
replace actual lags; such shifts are descriptive until separately validated. The three development
origins and 42 days are limited evidence;
if they cannot support the approved floor/threshold, report diagnostics without a numeric alert.
Proposal §24.1's `1.2 × baseline MAE` is only an example, not an accepted threshold. Do not
claim statistically reliable drift from two final blocks or 28 days.

## 12. Inventory scope decision and alternatives

Daily inventory evaluation remains a Phase 13 scope decision; it is not silently removed.

**Option A — bounded standing-policy episodes.** Extend the accepted Phase 10 method as two
separate July H14 episodes, if Technical Lead approves. Keep the two accepted policies, paired
exogenous inputs, R=1/L=2–7/P=L+1 rules, fixed standing targets, receive/consume/order timing,
no-queue-carry boundary, H14 terminal treatment, cost/KPI definitions and caveats. Use only
approved planned Open and daily revealed monetary Sales as the turnover proxy. Extend the Phase 9
56-day origin anchor and deterministic synthetic parameter contract for July origins only under
the same approved formulas, seed/key grammar and value ranges; create new traceable contexts,
without changing/regenerating canonical June artifacts. Existing June targets/scenarios cannot
be redated. This is a new origin-context implementation decision and requires explicit approval.
The episodes are not continuous 28-day inventory operation; standing targets may become stale,
and transported Fit B buffers do not establish July or synthetic-case coverage.

**Option B — defer final-holdout inventory.** Preserve the completed Phase 10 development
simulation and its unfavorable results; make no July inventory claims. This requires an explicit
scope/acceptance adjustment because the current roadmap includes daily operational KPIs.

**Recommendation:** Prefer Option A only as the bounded two-episode demonstration, and only if
the Technical Lead explicitly accepts its July-origin context extension, schedule provenance,
and mismatch with any interpretation requiring complete rolling protection coverage. If complete
rolling coverage is mandatory, Option A does not satisfy it; choose Option B with an explicit
scope adjustment. Do not create extra forecast origins, new horizons, suffix calibrations,
operational assumptions, or actual stock claims.

## 13. Failure handling, restart, and recovery

Fail closed before publication on wrong base/recipe/hash, unsafe path, unexpected key/schema,
future-row cutoff, covariate provenance error, unsupported required input, fit exception, or
incomplete forecast grid. No baseline fallback, partial block issuance, or silent null-to-zero
conversion. Preserve native row-level unavailability only where the accepted forecaster permits
it and record reasons.

Before publication, discard staging output and permit a clean retry only after validation against
the same frozen configuration and input identities. After publication, never refit or rewrite
that issuance; resume from the verified issuance receipt and last complete daily checkpoint.
Release/evaluation failure stops the next outcome release until reconciled. Idempotent replay of
the same released-date identity returns the existing checkpoint; changed duplicate or
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

- Default-deny providers, NTFS/account boundary behavior, and no unreleased-file read/hash from
  the issuance identity; a logical filter alone is not accepted as physical isolation evidence.
- Mutation of future Sales/Open/Customers cannot change either block's raw issuance; Block 2
  can change only when the authorized revealed-through-July-17 history changes.
- Unsafe paths and dates are rejected before content hashing; fitting rejects rows after its
  cutoff; fitted-origin mismatch, warm start, recipe override, or wrong Fit B identity fails.
- Future covariate/schedule mutations affect only their authorized outputs; unknown Open never
  becomes zero; actual future Open cannot fill planned Open.
- Recursive H14 feedback, clipping, native missingness, unavailable steps, exact grid, schema,
  categories, interval signs/ranks/clipping, unsupported strata, and complete prefixes match
  accepted fixture oracles.
- Outcomes cannot alter an already issued block, frozen quantiles, thresholds, or prior daily
  metrics; daily reveals must be strictly ordered and idempotent.
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
| **M1 — Safe contract/providers** | Approved protocol → typed, default-deny pre-origin, covariate, schedule, sealed and revealed providers; exact grid/config | Synthetic provider spies, pre-hash rejection, local identity/ACL rehearsal. Requires M0 decisions. |
| **M2 — Fresh-fit issuer** | Frozen refit recipe and fixtures → serialized model/adapter plus label-free raw H14 ledger | Exact params, origin/cutoff, category state, future-mutation invariance, repeat/save-load. Requires M1. |
| **M3 — Fit B/schedule adapter** | Pinned Fit B and approved covariates/Open contract → distinct raw/operational issued outputs | Golden quantile application, no calibration call, unknown schedule and unsupported-prefix behavior. Requires M2. |
| **M4 — Immutable publication/replay state** | Issued outputs → manifest-last block publication, receipts, release journal, checkpoints | Two-block chronology, ACL/provider boundary, atomic failure, crash/restart/tamper/idempotency. Requires M3. |
| **M5 — Metrics/monitoring** | Approved populations/threshold method → post-release summaries and alerts | Missing/zero denominators, exact windows, support and threshold fixtures, no-adaptation assertion. Requires M4. |
| **M6 — Inventory adapter (conditional)** | Approved Option A contract → July episode contexts and incremental daily state | Existing Phase 10 golden event/cost/terminal oracles; paired-input checks; no changed June artifacts. Requires M4 plus explicit inventory approval. |
| **M7 — Integration/review package** | M5 and optional M6 → fixture-only implementation, provenance and operational review | Python 3.12/3.14 quality matrix, docs/dependency checks, held-out provider not mounted, Phase 7–10 preservation. Requires applicable milestones. |
| **M8 — Separate release gate** | Reviewed code/config/artifact hashes → decision record for a specific authorized release | Independent review and explicit Technical Lead authorization; M0 or this PR is insufficient. Requires M7. |

## 17. Acceptance criteria and verification matrix

| Area | Proposed acceptance evidence | Release prerequisite? |
|---|---|---|
| Phase and scope | Current plan/PR explicitly remain PROPOSED or under review until human decision; implementation and release approvals are distinct | Yes |
| Git/artifacts | Branch based on current `origin/main`; unchanged Phase 7–10 artifacts and manifests; all new outputs immutable and identified | Yes |
| Recipe/forecast | Two fresh, exact trial-A refits; 29 ordered predictors; exact fixed params, cutoffs, categories, seeds; complete H14 grid; raw/operational separation | Yes |
| Chronology/custody | Complete issue receipt precedes each block's first reveal; next-day-only staged access; two fit origins only | Yes |
| Uncertainty | Pinned Fit B applied without fitting; availability/sign/clipping/prefix behavior preserved; final empirical coverage reported after release | Yes |
| Evaluation | Fixed requested grid and separate requested/observed/eligible/available denominators; accepted metric formulas | Yes |
| Monitoring | Exact approved windows/cohorts/support/thresholds; development-only derivation; diagnostic alerts do not change frozen outputs | Yes |
| Inventory | Option A fully tested under its approved bounded assumptions, or Option B explicitly approved as a scope adjustment | Yes if Phase 13 acceptance retains inventory |
| Recovery/provenance | Failure injection, deterministic resume, journal/checkpoint and manifest verification; runtime/source identities recorded | Yes |
| Review/authorization | Full fixture/quality evidence, independent final technical review, and separate exact release approval | Yes |

Development replay uses only synthetic fixtures until an independent implementation review
authorizes any development-data rehearsal. CI remains fixture-only and must not mount protected
local artifacts. This proposal and a passing documentation check do not satisfy these gates.

## 18. Open decisions requiring Technical Lead approval

The following table tracks independent audit findings P13-01 through P13-09. **Every row is
OPEN; none is ACCEPTED by this document.**

| ID | Proposed default | Alternatives | Evidence | Main risk | TL approval? | State |
|---|---|---|---|---|---|---|
| P13-01 Protocol/release | Two fixed H14 blocks; implementation and release separately authorized | Revise before any outcome release | ADR-015; Project Plan Phase 13 | Unfrozen protocol leaks decisions | Yes | OPEN |
| P13-02 Inputs/population | 1,115-store grid; versioned origin-known covariates; separate nullable planned Open; fail closed | Narrower approved roster/source or unavailable operational outputs | ADR-019/021; `lightgbm.py`; Phase 13 origins | Actual future Open or schedule assumptions contaminate issuance | Yes | OPEN |
| P13-03 Custody/ledger | Restricted issuer identity plus custodian-controlled daily release; immutable receipt/journal | Operator-enforced logical boundary with limitation disclosed | ADR-015; local Windows boundary above; current runners lack replay ledger | Same-user/admin bypass or reveal out of order | Yes | OPEN |
| P13-04 Frozen uncertainty | Apply exact accepted Fit B tables to both fresh fits, no recalibration | Omit operational intervals/targets if incompatible, subject to acceptance revision | ADR-021; Phase 8 accepted hashes; 91.26% development raw coverage | Calibration transport overclaimed | Yes | OPEN |
| P13-05 Inventory | Option A, two bounded H14 episodes under existing assumptions, only if scope clarification accepted | Option B defer with explicit Phase 13 scope adjustment | ADR-022/023; Phase 10; Project Plan protection coverage | Stale targets, unsupported July contexts, incomplete protection | Yes | OPEN |
| P13-06 Monitoring | 7/14 calendar-day windows; all-store and fixed metadata cohorts; development-derived limits only | Descriptive reporting without numeric alerts | Proposal §24.1 examples are candidates; ADR-020 thresholds are selection rules | Invented or weakly supported alerts | Yes | OPEN |
| P13-07 Runtime/repro | Pin runtime/build/lock; exact recipe; deterministic within same environment, not across platforms | TL-selected equivalent runtime/tolerance | ADR-018/020; `lightgbm.py` and generic fit API | Non-repeatable fit or false byte-identity claim | Yes | OPEN |
| P13-08 Scores/comparator | LightGBM primary; accepted denominators; existing comparator only if frozen and preapproved | Selected model alone | ADR-013/020; `metrics.py` | Population drift or reopening selection | Yes | OPEN |
| P13-09 Status/docs | Replace stale current-boundary wording while preserving dated checkpoint history | Keep old passage explicitly labeled historical | PROGRESS top-level state conflicts with “Immediate next boundary” M1/M2 claims | Readers mistake old checkpoint for current status | No methodology approval; review requested | OPEN |

## 19. Explicit implementation and release authorization gates

1. **M0 review:** Technical Lead resolves or explicitly defers each applicable decision and
   approves a frozen Phase 13 design. This draft PR itself does not approve the design.
2. **Implementation:** A separate task authorizes M1 onward within the approved scope. No
   implementation starts from this documentation authorization alone.
3. **Implementation review:** Fixture tests, quality checks, provenance, local custody/recovery
   evidence, and independent review pass. Phase 7–10 evidence remains unchanged.
4. **Release:** A separate explicit authorization names the reviewed commit, configuration,
   approved data provider, exact block, custodian, and release procedure. Only then may any
   final-holdout outcome be released to the evaluation process.
5. **Closeout:** Only after the authorized run, independent result review, and explicit phase
   closeout may Phase 13 be called COMPLETE. Phase 14 remains outside this plan.

**Current boundary: STOP at M0. Await Technical Lead review.**
