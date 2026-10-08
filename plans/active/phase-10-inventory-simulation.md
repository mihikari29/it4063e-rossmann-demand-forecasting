# Phase 10 — Inventory Simulation & Sensitivity Analysis

**Status: REVIEWED - awaiting corrective PR integration / closeout. NOT COMPLETE.**

Human methodology approval was given on 2026-10-07, accepting
[ADR-023](../../docs/DECISIONS.md#adr-023--origin-frozen-daily-inventory-policy-simulation-and-finite-window-accounting).
The initial technical review and a fresh independent methodology review both returned ACCEPT; the
independent verdict was `INDEPENDENT_PHASE10_DESIGN_REVIEW=ACCEPT`, with no blocking findings or
required changes. That approval authorized implementation as a separate task. The implementation,
canonical run and final review are recorded in Sections 19-22. Phase 9 remains COMPLETE. Phase 10 is
REVIEWED, with PR #24 integration and formal closeout pending; it is NOT COMPLETE. Phase 11 is
NOT STARTED / NOT AUTHORIZED. The protected final holdout remains unreleased. PR #23 was merged into
`main` before external implementation review resolution; the corrective follow-up is in
[PR #24](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/24). The final
focused external review accepted the corrected implementation and numerical evidence; the minor stale
PR metadata finding has been corrected. This plan remains active through authorized integration and
explicit closeout.

## 1. Authority, base and execution boundary

Design history: `docs/phase-10-inventory-simulation-design` was created directly from fetched
`origin/main` at `8234ab2170b7c76b00623c0f4e11a82dd8f2d4b2` on 2026-10-07. This is the PR #21
Phase 9 closeout commit, not the stale local `main` checkpoint. The starting worktree was clean.
[PROGRESS](../../docs/PROGRESS.md) confirms completed Phases 0–9, selected LightGBM, reviewed
Phase 8 uncertainty and completed Phase 9 scenario inputs. At that design-proposal checkpoint,
Phase 10 methodology approval was still pending; the later approval is recorded in Section 18.

Read with the [proposal](../../docs/PROPOSAL.md), [decisions](../../docs/DECISIONS.md),
[roadmap](../../docs/PROJECT_PLAN.md), [dictionary](../../docs/DATA_DICTIONARY.md),
[README](../../README.md), [AGENTS](../../AGENTS.md), [workflow](../../docs/WORKFLOW.md),
[artifact conventions](../../data/README.md), completed
[Phase 7](../completed/phase-7-model-selection.md),
[Phase 8](../completed/phase-8-forecast-uncertainty.md) and
[Phase 9](../completed/phase-9-synthetic-inventory.md) plans. The reviewed interfaces are
`forecasting/model_selection.py`, `forecasting/uncertainty.py`, `inventory/scenarios.py` and their
existing fixture tests. ADR-015/016/020/021/022 and the selected model remain unchanged.

The original design-proposal task was limited to documentation, existing checks and its review PR.
The subsequent approval and implementation task authorized source, fixtures, a thin CLI, result
documentation, one corrected canonical development run, commit, push and an implementation PR, but
not merge. Phase 11 remains outside that authorization. No protected 2015-07-04 through 2015-07-31
Sales, Open or Customers may be read, inspected, hashed, summarized or evaluated. This methodology
refinement needs no change to `docs/PROPOSAL.md`.

## 2. Objective, units and episode

Answer: under explicitly simulated monetary inventory and supply-chain assumptions, how does a
forecast-driven replenishment policy change service/cost indicators relative to a transparent
baseline? A negative finding is valid. Presentation phrase:
**Simulated inventory-value policy comparison and sensitivity analysis.**

Simulation grain is Store × scenario × sensitivity_variant × origin × policy × calendar date.
Each independent episode has H=14 calendar days; state does not carry between origins.
Use the Phase 9 configured Store universe, not a performance-selected subset.

- V is retail-equivalent monetary turnover value on the Rossmann Sales scale: demand, stock,
  outstanding orders, receipts, position, targets and replenishment.
- K is a synthetic cost-proxy unit; holding and shortage rates convert V into K.
- Sales is observed turnover, not physical/SKU demand or identified latent demand. Stock,
  shortages and costs are simulated, not observed Rossmann operations or realized savings.

Only end-of-day origins 2015-06-05 (Fit A; June 6–19) and 2015-06-19 (Fit B; June 20–July 3)
are permitted. Fit B cannot be assigned retrospectively to June 5. Reject other origins before
opening inputs. Phase 10 never releases the final holdout or changes the Phase 13 protocol.

## 3. Review, lead time and receipt convention

Daily review R=1; SupplierLeadTime L is an integer in {2,3,4,5,6,7}.
ProtectionPeriod P=L+R=L+1 is in {3,...,8} and must be <=14.

**SupplierLeadTime L means the number of full intervening calendar demand days between an
end-of-day order and its receipt. An order placed at END OF DAY t arrives at START OF DAY
t+L+1.** With L=2, days 1 and 2 pass after the origin review; receipt precedes day-3 demand.
This convention resolves Phase 9's undecided receipt timing without changing its L draws.
The next daily review's order arrives on day L+2, giving the original h1..L+1 protection prefix.

At origin o, before loading evaluation outcomes:

1. Verify upstream identities and chronology.
2. Construct the declared origin-known or explicitly assumed-known schedule view.
3. Calculate and freeze both policy targets.
4. Initialize Phase 9 stock and an empty order pipeline; backorders are zero.
5. Review inventory and place any required positive order.

Do not replay origin-day demand. For h=1..13, date t=o+h:

1. Receive all due orders at the start of the day and remove them exactly once from the queue.
2. Reveal/apply only that day's allowed demand proxy.
3. Fulfil demand from available stock.
4. Record unmet turnover as lost sales.
5. Calculate ending stock and daily holding/shortfall costs.
6. Calculate inventory position.
7. Review against the unchanged standing target.
8. Place a positive order if required, with its exact due date.
9. Record the ledger and verify state balances.

At h=14, process receipts, consumption, fulfilment, unmet value, ending stock, costs and inventory
position, but suppress the final order review with `terminal_boundary`. No day-14 order is placed.
Targets never consume evaluation outcomes; daily orders use state after already revealed demand.

## 4. State transitions and order queue

With I=on-hand V, O=outstanding V, R_t=receipt V (distinct from review cadence R), d=demand proxy,
F=fulfilled V, M=unmet V, IP=inventory position V, Q=order V and S=frozen target V:

```text
A_t = I_(t-1) + R_t
F_t = min(A_t, d_t)
M_t = d_t - F_t
I_t = A_t - F_t
O_t^- = O_(t-1) - R_t
IP_t = I_t + O_t^-
Q_t = max(0, S - IP_t)          # permitted reviews only
O_t = O_t^- + Q_t
```

At origin, IP_0=I_0, Q_0=max(0,S-IP_0), O_0=Q_0. On day 14, Q=0 because review is suppressed,
not because a new forecast recommendation was calculated. Each queued order has an identifier,
placement date, due date and V amount. OnOrder is the queue sum, never reset to zero after review.

Lost sales only: unmet V is recorded and discarded; no backlog or later catch-up demand.
Finite nonnegative consumption and receipts imply nonnegative stock. Orders are continuous V:
no rounding, MOQ, capacity constraint, fixed-order charge or cancellation. AverageUnitValue is
display-only; equivalent-unit illustrations cannot alter the monetary simulation.

## 5. Exactly two standing-target policies

Policy IDs are `historical_mean_standing_target` and `lightgbm_buffer_standing_target`.
Let z_h be the binary opening schedule known/assumed at origin, and m the Phase 9 origin-safe
mean open-day turnover anchor. Initial stock and every exogenous input are identical across policies.

**Baseline:** for the original prefix h1..P, `S_base=m*sum(z_h)`.
This mean-based comparator has no safety buffer and uses the same schedule/time boundary.
Freeze S_base for the entire H14 episode; no later moving-average update.

**Forecast-driven:** for the same original prefix:

```text
D_P = sum(operational LightGBM point forecasts over h1..P)
U_P = max(0, D_P + q_(p,P))
SafetyStock_P = max(0, U_P - D_P)
S_fcst = D_P + SafetyStock_P = max(D_P, U_P)
```

Reference p=0.95; additional sensitivity p is only 0.90 or 0.98. Preserve signed q, including
negative q. A negative q cannot lower S below D_P. Do not sum marginal daily upper bounds.
At every permitted later review use `Q=max(0,S-IP)` with the SAME S.

This is an **origin-frozen standing/base-stock target policy**, not rolling calibrated inventory
control. Targets may become stale during H14. There is no forecast refresh, suffix generation,
rolling uncertainty, quantile scaling, recalibration or refitting. ADR-023 accepts the Phase 10
standing-rule execution on frozen targets; Phase 8 approval alone did not authorize these inventory
decisions.
Policy differences combine point forecasting and buffering; they do not isolate LightGBM's effect.

## 6. Availability, chronology and synthetic buffer transport

Target construction may receive only anchors, effective L/P/p, schedule indicators, frozen point
values, signed cumulative quantiles/availability and safe provenance. It must not receive realized
Sales/SyntheticDemandValue, assessment totals/hits, residual outcomes or future stress realizations.

Require the selected `global_lightgbm_gbdt_regression_l1`, frozen trial A/180-round/29-predictor
recipe; matching origin/fit; complete operational h1..P; finite q at exact fit/P/p; compatible
schedule; and finite nonnegative operational points. Phase 8 supports **origin-anchored prefixes
only**. Later reviews execute a standing target; q is never relabelled a suffix bound.

If a required input is unavailable, keep target null with a reason. Do not replace it with zero,
baseline, point-only target, another p, fit or horizon. Retain requested keys and availability;
that policy track is unavailable, not a zero-order fallback. Available standalone tracks may be
reported, but paired comparisons require complete available tracks for both policies.
Fit A's unavailable marginal daily tails do not invalidate an independently available cumulative
prefix. Historical D/U/Safety/Target must agree with saved issuance-only Phase 8 fields; assessment
`actual_total`, errors and hits are excluded from target construction.

Historical replay uses `saved_source_open_assumed_known_at_origin` only as the accepted conditional
development assumption, not proven schedule availability. Synthetic scenarios route the unchanged
frozen raw point prefix with Phase 9 ScenarioOpen; no synthetic feature enters LightGBM recursion.
ADR-023 accepts frozen historical q only as an illustrative stress-test buffer. Every synthetic
case retains `calibration_transport_valid=false` and `buffer_interpretation=uncalibrated_synthetic_heuristic`.
No nominal p coverage or achieved synthetic service probability is claimed. Do not rescale q for
Store size, stress, discount or starting stock.

Pin the accepted run identities inherited from PROGRESS, not mutable current pointers:

| Stage | Canonical run / expected manifest SHA-256 |
|---|---|
| Phase 7 | `365f22d4c3f94722a594ab934a22c4f6` / `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` |
| Phase 8 | `phase8-impl-20261006-provenance-review` / `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| Phase 9 | `phase9-dev-20261007-config-validation-fix` / `573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761` |

These are inherited governance references, not newly verified data hashes in this documentation PR.
Future implementation checks every bound file/config/recipe identity. Fit B's later governance
freeze does not rewrite original publication-time pending-review flags; Fit A retains its accepted
historical June 5 role and is not the Fit B freeze applied to an earlier origin.

## 7. Demand layers, closure and missingness

Keep hand-worked mechanics verification, synthetic stress comparison and historical-reference
conditional replay separate. Historical replay loads unchanged observed DEVELOPMENT Sales from
verified Phase 7 residual paths only in the evaluator, after targets are fixed. No raw/interim,
Kaggle test or feature-inference outcome read is needed. Historical reference is not realized
inventory ground truth. Missing source keys/labels are not zeros. A closed-day positive Sales label
is retained as an assumption violation and excludes the affected episode from valid conditional
comparison; never overwrite it to force a closure zero.

Synthetic replay consumes published SyntheticDemandValue and its origin-known synthetic schedule.
Neither realized future demand nor demand-stress factors may enter target construction. Known
synthetic closures have zero applicable demand when the upstream demand is available; unavailable
anchors/demand remain unavailable even on a closure. Unknown required schedule makes the target
unavailable. Unknown later applicability or missing demand stops dependent state evolution; retain
valid earlier ledger rows, null later dependent states and mark the episode incomplete.

Assume receiving and administrative reviews can occur seven days a week, including closed days.
Stock remains held; receipts, permitted reviews and holding costs continue on closed days.
No protected future actual Open is used. Source Open remains routing/evaluation context, not a
predictor or proof of prospective availability.

## 8. Cost accounting

Use Phase 9's c=ProcurementCostRatio, a=AnnualHoldingRate and g=GoodwillPenaltyRate:
`h=c*a/365` K/V/calendar day; `b=(1-c)+g` K/V unmet.
At ending on-hand stock, `HoldingCost_t=h*I_t`; `UnmetPenalty_t=b*M_t`.

Primary episode `C_window=sum(HoldingCost_t+UnmetPenalty_t)` over all 14 days is named
**simulated holding-plus-shortfall cost**. It is not profit or complete lifecycle cost. Do not
charge procurement value as an additional objective component, subtract Sales revenue or add
lost margin again; b already contains the hypothetical margin component once. No carrying charge
on pipeline value is assumed.

Report `TerminalStockCostValue=c*I_T` and `OutstandingProcurementCommitment=c*O_T` separately as
synthetic exposure diagnostics, excluded from C_window. Inventory itself remains on the V basis.

## 9. KPI numerators, denominators and receipt cycles

Full-episode metrics require 14 valid state/consumption days. Origin rows are excluded from daily
costs and inventory means. Record the following sufficient statistics in policy summaries:

| Metric | Numerator / denominator or additive field |
|---|---|
| ValueFillRate | `fulfilled_total` / `demand_total`; zero denominator => null |
| PositiveDemandStockoutRate | `positive_demand_stockout_days` / `positive_demand_days`; zero denominator => null |
| AverageInventoryValue | `ending_inventory_sum` / `calendar_days` (exactly 14 for a complete episode) |
| UnmetTurnoverValue | `unmet_total=sum(M_t)` V |
| SimulatedHoldingCost | `holding_cost_total=sum(h*I_t)` K |
| SimulatedUnmetPenalty | `unmet_penalty_total=sum(b*M_t)` K |
| SimulatedHoldingPlusShortfallCost | `holding_cost_total+unmet_penalty_total` K |
| Terminal inventory / pipeline | `terminal_on_hand_value`, `terminal_on_order_value` V |

Use the exact presentation label **completed positive-demand receipt-cycle service rate**,
with output field `CompletedPositiveDemandReceiptCycleServiceRate`. This is a simulated CSL proxy /
project-specific receipt-cycle measure, not an unconditional industry-standard guaranteed CSL.

For distinct observed positive receipt dates a_i<a_(i+1), a completed cycle covers
`[a_i,a_(i+1)-1]`; both receipt boundaries must occur by T. Only cycles with positive total demand
enter `completed_positive_demand_cycles`. Numerator `zero_unmet_positive_demand_cycles` counts
those with sum(M)=0. Their ratio is null when the denominator is zero. Also record
`completed_cycles_total`, `zero_demand_completed_cycles`, `initial_left_censored_intervals` and
`terminal_right_censored_intervals`. Cold-start days before the first receipt and the unfinished
final cycle are censored for this metric, but remain in daily service/cost measures. No receipts
means no completed cycles; the observed episode is reported as a censored interval, not a success.
The cycle denominator is policy-dependent; this proxy is secondary to value fill/shortfall metrics.

Closed days enter inventory/cost accounting but not positive-demand day denominators. A zero-demand
episode has null fill, stockout and positive-demand cycle rates; inventory and costs remain valid.
Incomplete episodes have null full-H14 metrics; any partial-prefix diagnostics must be explicitly
labelled and excluded from complete comparisons. Pooled ratios use summed numerators/denominators,
not averages of Store percentages. Pooled inventory divides summed stock by valid calendar days.

## 10. Terminal treatment and common inputs

T=o+14. Orders placed through day 13 remain valid. Receive due-on-T orders before day-14 demand;
orders due after T remain outstanding. Do not cancel, refund, accelerate, extend the simulation,
invent future consumption or assign salvage. Charge day-14 holding cost on ending inventory.
Report terminal I/O, late-order count/value and procurement commitment for both policies.
Computed due dates after July 3 are schedule metadata, not protected outcome access.

Use identical terminal treatment. Terminal exposure is not savings; finite-window costs do not
include later carrying costs or the complete economic consequences of committed orders.

Within a case both policies share exact demand path, initial stock/pipeline, L, schedule, c/a/g,
family, replicate, sensitivity variant and upstream model/scenario identity. Only decisions differ.
No new random draw is made by the simulator. Publish standalone availability and matched-store
counts; compare complete tracks on the same case/Store population with forecast-minus-baseline
differences. Relative cost differences are null when baseline cost is zero. Do not select a winning
policy or service parameter from these results for a later holdout protocol without authorization.

## 11. Compact sensitivity overlays

Reference: every existing Phase 9 scenario at p=0.95 (82 scenarios; all configured Stores).
Additional variants apply only to synthetic_base at both origins and all five paired replicates:

| Variant IDs | Change | Retain |
|---|---|---|
| `lead_2`, `lead_7` | L=2 or 7; recalculate P and due dates | Demand, starting stock and costs |
| `buffer_090`, `buffer_098` | p=0.90 or 0.98 | All other exogenous inputs; baseline target unchanged |
| `holding_010`, `holding_030` | a=0.10 or 0.30; h=c*a/365 | c/g and physical state/order decisions |
| `goodwill_010`, `goodwill_075` | g=0.10 or 0.75; b=(1-c)+g | c/a and physical state/order decisions |
| `coverage_1` | C=1; initial stock=m*C for both policies | Demand, lead time and costs |

These are nine one-factor-at-a-time additions, not a factorial grid. Validate immutable original
Phase 9 tables first; store separately validated effective parameters as Phase 10 overlays.
Do not modify/regenerate Phase 9 or change its strict generator config. Use its eight existing
families for demand and coupled stress. No new demand draw, fitted stress distribution or family.
Keep origin/family/replicate/variant results separate; report cost, fill, stockout, inventory and
terminal differences. Five replicate ranges are descriptive, not confidence intervals or empirical
probability weights. Cost-only variants must leave state/order trajectories exactly unchanged.

## 12. Implemented software interfaces

The implementation is in `src/rossmann_forecasting/inventory/simulation.py`; existing
`scenarios.py` is unchanged. Split policy/metric modules only if implementation review demonstrates
a need.
Use existing pandas, NumPy, PyArrow and standard library; no new dependency is expected.

| Public interface | Responsibility |
|---|---|
| `default_simulation_config()` | Approved policies, timing, overlays, KPI and artifact specification |
| `verify_simulation_inputs(...)` | Safe Phase 9/7/8 verification, projected views and identity snapshot |
| `build_policy_targets(...)` | Origin-only targets without evaluation outcomes or realized stress |
| `simulate_case(...)` | One case/policy; sequential daily outcomes, queue and ledger |
| `summarize_simulation(...)` | Episode metrics, cycle/censoring counts and matched comparison |
| `validate_simulation_outputs(...)` | Schemas, keys, balances, cost/denominator arithmetic and population |
| `run_inventory_simulation(...)` | Verify, compute, stage, validate and publish an immutable run |

Use small immutable config/target/order records, not an optimizer framework. Reuse public
`scenarios.verify_frozen_bindings`, `validate_scenario_tables` and `logical_table_sha256`
where appropriate, without invoking a generator, estimator, forecaster or verifier that loads
evaluation outcomes into target construction. The implemented thin CLI is
`python scripts/run_inventory_simulation.py --run-id <unused-id>` (optional repository root).
It calls the package logic in `src/rossmann_forecasting/inventory/simulation.py`.
Phase 9's `scenarios.py` and dependencies/lock are unchanged.

## 13. Implemented artifacts and publication

Ignored immutable root: `data/processed/inventory_simulation/<run_id>/`. The pre-review canonical
run `phase10-dev-20261007-implementation-v2` remains immutable historical evidence; the current
canonical review-fix run and its manifest are recorded in [PROGRESS](../../docs/PROGRESS.md).
`case_id=<scenario_id>--<variant_id>`; the reference variant is `reference`. Retain explicit origin,
mode, family, replicate and variant columns. The seven required files below were published and
validated. All 383,560 requested tracks are complete; no track is unavailable or excluded.

| File | Primary key / grain | Important fields |
|---|---|---|
| `simulation_config.json` | One run config | Policy IDs/version, timing/domain, p grid, overlays, cost/KPI/censoring rules, approval and pinned upstream identities |
| `policy_targets.parquet` | `(case_id, Store, policy_id)` | origin, L/R/P/p, m/open-day count or D/q/U/Safety/S, issuance date, standing-rule scope, availability/reason, fit/schedule/buffer interpretation and model identity |
| `simulation_ledger.parquet` | `(case_id, Store, policy_id, Date)` | origin review h0 plus h1..14; starting/available/ending stock, receipts, demand/F/M, pipeline before/after, IP, target, order ID/value/due date, review status, costs, state availability/reason |
| `policy_summary.parquet` | `(case_id, Store, policy_id)` | complete/partial/unavailable status, Section 9 sufficient statistics, cycles/censoring, terminal exposures, late orders, common-input identity and exclusion reason |
| `comparison_summary.csv` | `(case_id, metric)` | requested/standalone/matched Store counts, paired numerator/denominator or additive values, forecast-minus-baseline difference, null reason and interpretation |
| `validation_summary.json` | One run | counts, structural/invariant errors, exclusions, date boundaries, upstream checks and logical reproducibility |
| `manifest.json` | One publication | command/config, environment/code/lock, provenance, output inventory and boundary flags |

Ledger placement/due-date fields reconstruct the queue; no separate orders file is required.
Reference counts: 182,860 policy tracks/target/summary rows and 2,742,900 ledger rows. Including all
nine sensitivity additions: 383,560 tracks/target/summary rows and 5,753,400 ledger rows. The run
contains 172 cases and 1,720 comparison rows; all counts match the approved design.

Use ordered explicit Arrow schemas: date32 calendar dates; integer keys/counts; float64 V/K/rates;
Boolean availability; UTF-8 IDs/reasons. Keys and flags are nonnullable; dependent unavailable
values are null, never NaN/infinity or silently zero. Reject duplicate keys/schema/foreign-key
violations. Preserve input objects and original upstream publication metadata.

For tables record byte SHA-256/length, logical SHA-256, row count, key and ordered schema. Reuse
Phase 9's primary-key-sorted schema-plus-row logical encoding (ISO dates, float.hex(), explicit
nulls). JSON has separate byte and canonical hashes; semantic config identity excludes its own
hash and current-run ID/timestamp, while nested frozen upstream identities remain included.
Simulator seed is not_applicable; record inherited scenario seed 4209 and its draw grammar.

Manifest records command/arguments, policy/config, approval evidence, code revision/source digest/
dirty state, Python/platform/packages, uv.lock identity, all input/output identities, availability,
assumptions and no-holdout/no-refit/no-recalibration flags. Expected input manifests are in Section 6;
preserve legacy/modified-worktree lineage disclosures. No retroactive regeneration claim.

Resolve allowlisted paths and preflight development Parquet footer date bounds/row counts before
whole-file hashing; reject post-cutoff or insufficient statistics without loading protected
columns as a fallback. Project only necessary fields; separate safe issuance views from evaluation
outcomes. Do not hash full raw/interim train files or access feature inference/test/EDA data.

The implementation stages each ignored run, rereads and validates schemas, balances, counts and
hashes, and rechecks every upstream identity before publication. It writes the manifest last and
publishes atomically, then updates ignored `current.json` only after complete success. Existing run
IDs are immutable. Fatal integrity/chronology/publication failure publishes no consumable run and
preserves previous directories/pointer; expected unavailable episodes may yield
`complete_with_unavailable_inputs` with explicit coverage counts.

## 14. Fixture tests

| Behavior | Required evidence |
|---|---|
| No look-ahead | Future outcome mutation leaves earlier orders unchanged; all outcome mutations leave targets unchanged |
| Information separation | Target builder excludes outcome/residual/hit and realized-demand/stress columns |
| Determinism/order invariance | Repeats, input/case/Store/policy permutations, chunks and retained subsets preserve logical results |
| Receipt timing | Origin L=2 receipt precedes day-3 demand; never day 1/2; receipt removes an order once |
| Queue/position | Outstanding orders contribute to IP and survive reviews; all same-day due orders are received |
| Lost sales/nonnegative stock | F=min(A,d), M=d-F, no backlog/catch-up; demand beyond stock leaves I=0 |
| Order-up-to | IP below/equal/above S gives exact positive/zero Q; continuous values are not rounded |
| Target arithmetic | D=80,q=-20 => U=60,S=80; D=80,q=30 => U=110,S=110; signed q retained |
| Baseline arithmetic | m=100 and two open days in the original P prefix => S=200 |
| Domain | L integer 2..7, R=1, P=L+1; reject inconsistent P, P>14 and unsupported origin/fit/p |
| Availability | Missing prefix/q/schedule yields null target without fallback; unavailable daily tails alone do not block cumulative use |
| Common inputs | Both policies receive identical exogenous path/stock/lead/cost/schedule/replicate/variant/lineage |
| Zero demand | Null service ratios on zero denominators; inventory, queue and costs remain valid |
| Closed/unknown days | Known synthetic zero, receipts/reviews/carrying continue; unknown stays unavailable; historical contradictions preserved |
| Terminal | Due-on-T received; due-after-T retained; no day-14 order/cancel/refund/salvage or future outcome read |
| Costs | h=ca/365 and b=(1-c)+g applied once at ending stock/unmet; exposure excluded from C_window |
| KPI denominators | Exact sufficient statistics, zero => null, pooling from totals rather than Store percentages |
| Receipt cycles | Positive receipt boundaries, positive-demand denominator, zero-demand counts and initial/final censoring |
| Non-mutation | Frames/tables/config unchanged; no source or frozen artifact write |
| Sensitivity | Cost-only overlays change costs but not stock/order trajectory; only declared overlay inputs change |
| Firewall | Unsupported origin/July-4 target rejected before data read/hash; protected-path reader/hash spies never fire |
| Frozen integrity | Wrong/mutated Phase 7/8/9 hash/model/fit/run/config or inconsistent availability fails closed |
| Publication | Existing ID, staged failure, upstream mutation and pointer failure preserve prior runs/pointer |

Hand-worked fixture: S=100, initial I=50, L=2. Origin Q=50. Day 1 d=40 => I=10,
outstanding before new order=50, IP=60, Q=40. Day 2 d=30 => F=10, M=20, I=0,
outstanding before new order=90, IP=90, Q=10. Day 3 receives origin Q=50 BEFORE demand.
For c=0.70,a=0.20,g=0.50, h=0.14/365 and b=0.80; day-2 unmet penalty is 16 K.

## 15. Development numerical validation and acceptance

Under the accepted Phase 10 methodology, run the canonical development reference and sensitivity
panel from verified saved inputs, with no fit/calibration or scenario regeneration.
Require zero structural/integrity violations, exact designed grids and every availability reason.
Independently reconstruct queues, costs, denominators and matched populations from the ledger:

```text
I_T = I_0 + sum(receipts) - sum(fulfilled)
O_T = sum(orders, including origin order) - sum(receipts)
sum(demand) = sum(fulfilled) + sum(unmet)
```

Verify daily balances, nonnegative states/costs and terminal orders, not only aggregate identities.
Arithmetic tolerance is `abs(actual-expected)<=1e-9*max(1,abs(expected))`. Schemas, dates, keys,
nulls and hashes are exact; tolerance permits no repair or row loss. Detailed canonical counts,
results, hashes, and validation evidence are maintained in [PROGRESS](../../docs/PROGRESS.md).

**IMPLEMENTED / UNDER REVIEW:** methodology was approved before code. Review findings, fixes,
regression tests, canonical evidence, and remaining review state are recorded in PROGRESS; that file
is the authoritative numerical-results record. Improvement over baseline is not a passage criterion.

**COMPLETE:** independent implementation and numerical review accepted; findings resolved;
authorized merge verified; explicit closeout and frozen configuration/result identities recorded;
plan archived. Tests or a successful run alone do not close the phase. Phase 11 requires separate
authorization; Phase 13 release remains governed by ADR-015.

## 16. Critical limitations

The static target can become stale; origin cumulative turnover coverage does not imply later
suffix coverage or absence of within-cycle shortage. Synthetic q transport is uncalibrated.
Two Friday inventory origins and shared Stores provide little temporal replication; five artificial
replicates do not create statistical power. Cold starts, H14 truncation, endogenous receipt cycles,
illustrative costs and unpriced later carrying costs can influence rankings. The development
windows informed point-model selection; this is not an independent final test. Phase 8's accepted
raw Fit B coverage remains below nominal 95%; sparse Sundays and dependent errors remain disclosed
in PROGRESS, not recomputed or repaired here.

The overall project title may retain Inventory Optimization, but Phase 10 proves no mathematical
optimality. Prohibit claims of actual Rossmann stockouts, real inventory, SKU/physical quantities,
realized savings, guaranteed service, calibrated synthetic uncertainty, statistical superiority,
production readiness or optimal replenishment. p is a nominal buffer parameter, not the achieved
receipt-cycle proxy or value fill rate. Report adverse comparisons and terminal exposure honestly.

Human approval accepts the standing-target daily execution, uncalibrated synthetic buffer use,
explicit receipt/cost/KPI/terminal definitions and nine sensitivity overlays recorded here. It
does not change accepted Phase 0–9 methods or authorize holdout access.

## 17. Documentation proposal execution and historical handoff

The original documentation task recorded the active plan and proposed ADR, aligned current-state
documentation and artifact conventions, ran existing workflow checks, inspected the diff and
opened a review PR. Its no-merge and awaiting-approval statements describe that historical
pre-approval checkpoint; human approval and later integration are recorded below and in PROGRESS.
No simulation results are claimed.

## 18. Methodology approval checkpoint — 2026-10-07

**Decision at this checkpoint: APPROVED; IMPLEMENTATION NOT STARTED.** Human approval accepted
this Phase 10 methodology and ADR-023 on 2026-10-07. The initial technical methodology review and fresh
independent methodology review returned ACCEPT. The independent review recorded
`INDEPENDENT_PHASE10_DESIGN_REVIEW=ACCEPT`, no blocking findings and no required methodology
changes. This is model-assisted methodology review evidence plus explicit human approval; it does
not claim a GitHub-native reviewer approval.

At that approval checkpoint, Phase 10 implementation was authorized as the next separate task and
required to follow Sections 2–15 without changing accepted upstream recipes or scenario artifacts.
The approval commit and PR integration did not implement Phase 10. Phase 9 remains COMPLETE;
Phase 11 remains NOT STARTED and unauthorized. The protected final holdout remains protected under
ADR-015.

## 19. Initial implementation checkpoint — 2026-10-07

Phase 10 was implemented on `feat/phase-10-inventory-simulation`; PR #23 was merged into `main`
before the external implementation review was resolved. The first canonical attempt was superseded
after a Pandas `Series.mode` metadata collision; the corrected v2 run is retained as immutable
pre-review evidence. Detailed original and current canonical results are maintained in
[PROGRESS](../../docs/PROGRESS.md), which is the authoritative numerical-results source.

## 20. External implementation review fixes — 2026-10-08 (initial corrective checkpoint)

The external implementation review returned **REQUEST CHANGES** after PR #23 merged, with blockers
B1–B3: Phase 9 schema and date rejection ordering before byte hashing, missing-demand dependent-state
and incomplete-prefix validation, and terminal receipt-cycle right censoring. The fixes preserve
ADR-023 and add regression coverage. The source/test commit passed 48 focused tests and the full
suite passed 278 tests. Ruff lint/format, documentation validation, `uv lock --check`, `uv pip check`,
and `git diff --check` passed.

The corrected canonical run `phase10-dev-20261008-review-fixes` completed from pinned Phase 7/8/9
inputs without holdout access, refit, recalibration, or Phase 9 regeneration. Its results are retained
as the prior review-fix checkpoint; the subsequent focused re-review and validator correction are in
Section 21. Detailed numerical results remain in [PROGRESS](../../docs/PROGRESS.md).

## 21. Focused re-review validator correction — 2026-10-08

Focused re-review #1 returned REQUEST CHANGES: B1 pre-hash firewall, B3 terminal censoring, and B2
simulation semantics passed; the only remaining blocker was incomplete-track validator coverage. The
validator correction preserves simulation outputs and ADR-023 while checking origin invariants,
static metadata/rate consistency throughout incomplete tracks, and empty receipt IDs after the first
missing-demand boundary. New regression fixtures cover each reported mutation and a valid L=2 prefix
that receives an order before demand becomes missing. Source commit
`5504d855fd60b8a038a4d6574e35b579ed0f439d` passed 50 focused Phase 10 tests and 280 full-suite tests;
the required quality checks passed. A new canonical run,
`phase10-dev-20261008-validator-fix`, is current and logically matches the previous review-fix run in
targets, ledger, policy summary, and comparison. Its manifest, validation fields, hash comparisons,
censor reconstruction, and preserved numerical results are recorded in [PROGRESS](../../docs/PROGRESS.md).
The prior runs remain immutable. At this validator-correction checkpoint, Phase 10 was
**IMPLEMENTED / UNDER REVIEW**, pending the final focused external re-review. The current accepted
review and governance status are recorded in Section 22. Phase 11 remains
**NOT STARTED / NOT AUTHORIZED**.

## 22. Final focused external re-review and current governance status - 2026-10-08

The final focused external re-review of PR #24 returned
`PHASE10_FINAL_FOCUSED_REREVIEW=ACCEPT_WITH_MINOR_CHANGES`. Review chronology: initial
`PHASE10_IMPLEMENTATION_REVIEW=REQUEST_CHANGES`; focused re-review #1
`PHASE10_FOCUSED_REREVIEW=REQUEST_CHANGES`; final focused re-review
`PHASE10_FINAL_FOCUSED_REREVIEW=ACCEPT_WITH_MINOR_CHANGES`. B1, B2 and B3 pass, with no blocking
findings. The sole minor finding was stale PR body evidence; the PR description is refreshed to the
accepted canonical run and validation results. ADR-023, simulation methodology, numerical evidence,
and immutable run history remain unchanged.

Accepted canonical run: `phase10-dev-20261008-validator-fix`; manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`. The run's source revision is
`5504d855fd60b8a038a4d6574e35b579ed0f439d` and source digest is
`a4c1ec83d4211c45d75afe4db9845b359ddb41f88f04f3611a0c3cda872096db`. Focused tests: 50 passed;
full suite: 280 passed. GitHub Quality run [#64 / 37718032966](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37718032966)
passed on Python 3.12 and 3.14. Detailed comparison, sensitivity and right-censor results remain in
PROGRESS and are unchanged.

**Phase 10 - REVIEWED.** Corrected implementation and numerical evidence are accepted; PR #24
integration and formal closeout remain pending. **NOT COMPLETE.** Phase 11 is **NOT STARTED / NOT
AUTHORIZED**. The protected holdout remains unreleased; no holdout outcomes were accessed for this
metadata/governance update. No simulation rerun or canonical artifact change was made. The plan
remains active until authorized PR integration and explicit closeout.
