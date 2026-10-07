# Phase 9 — Synthetic Supply-Chain / Inventory Layer Design

**Status: APPROVED / IMPLEMENTED — UNDER REVIEW (2026-10-07).** The external methodology
decision is ACCEPT. The generator, fixture suite and canonical development scenario run are
implemented on `feat/phase-9-synthetic-inventory`; this active plan records the implementation
checkpoint and pending review in
[PR #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/19). Phase 10
remains unapproved and not started.

## 1. Authority, integration and scope

The historical design branch `docs/phase-9-inventory-design` started from fetched `origin/main`
at `f08a62aa980d0670186ed25ae1f6e5a018ff3781`. GitHub reports
[PR #17](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/17) merged at that
squash commit, integrating the formal Phase 8 closeout. The base also contains implementation
PR #15 and accepted-results PR #16 at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821` and
`4dd7717fed57ff3b1f14789b980772c1968f3cba`.

The design approval synchronization
[PR #18](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/18) merged into
`main` at `97795ca5d868b512e5c2f6cae59bcec1d6ce19a4`. The implementation branch
`feat/phase-9-synthetic-inventory` starts from that commit.

Read together with [AGENTS](../../AGENTS.md), [workflow](../../docs/WORKFLOW.md),
[proposal](../../docs/PROPOSAL.md), [roadmap](../../docs/PROJECT_PLAN.md),
[decisions](../../docs/DECISIONS.md), [dictionary](../../docs/DATA_DICTIONARY.md),
[PROGRESS](../../docs/PROGRESS.md) and the
[completed Phase 8 plan](../completed/phase-8-forecast-uncertainty.md).
Accepted [ADR-022](../../docs/DECISIONS.md#adr-022--synthetic-monetary-scenario-contract)
records the approved synthetic assumptions without superseding ADR-015, ADR-016, ADR-020 or
ADR-021. Historical proposal checkpoints remain in this active plan and PROGRESS.

**Phase 9 delivers:** origin-censored initialization evidence, deterministic exogenous
operational parameters, separately labelled synthetic turnover paths, validation reports and
immutable manifests. It would neither fit a forecast nor run an inventory policy.
No protected 2015-07-04 through 2015-07-31 Sales, Open or Customers may be accessed, hashed or
used. No Phase 7/8 artifact, calibration, feature contract, model or dependency changes belong here.
The choices in this plan were accepted in the external methodology review recorded in Section 13.
The implementation state and numerical evidence are recorded in Section 14.

## 2. Value semantics and information layers

All demand proxies, stock and future replenishment values use one **retail-equivalent monetary
Sales basis**, denoted V. V is the dataset's turnover-value scale; no real currency, price per SKU,
physical unit, actual stock, uncensored demand or Rossmann stockout is inferred. Discount context
does not revalue V or convert it into units. Synthetic costs use a separate cost proxy K, with a
declared K-per-V conversion. They cannot establish realized margins or business savings.

| Layer | Authority / origin availability | Phase 9 treatment |
|---|---|---|
| Historical observed `Sales` | Unchanged Rossmann observations at Date <= origin | Only input to the initializer; Open=1 turnover anchors an illustrative scenario scale. Missing dates stay missing. |
| Historical replay outcomes | Observed development Sales after origin | Referenced as a future Phase 10 evaluation source; never loaded into Phase 9 parameter or demand generation. They are turnover proxies, not latent demand. |
| Frozen point forecasts | ADR-020 selected `global_lightgbm_gbdt_regression_l1`, trial A / 180 rounds; saved Phase 7 paths | Read-only lineage and origin/date/availability binding. No refit, recursive refresh, substitution or adjustment to match a stress scenario. |
| Frozen Phase 8 uncertainty | Canonical empirical daily/cumulative tables and approved fit chronology | Read-only references; no estimation, resampling, scaling, interpolation or new suffix bounds. |
| Synthetic operational context | Configured at scenario origin | Lead time, starting stock, conversion, costs, synthetic schedules and stress factors are assumptions. They remain outside all real Rossmann predictors. |
| Synthetic turnover path | Deterministic artificial future conditional on origin anchor and configured factors | Separate from observed Sales and point-forecast accuracy. It is an artificial simulator input, not estimated lost or latent demand. |

The implemented generator accepts only these development issuances:

| Origin (end of day) | H14 target dates | Compatible Phase 8 assessment fit |
|---|---|---|
| 2015-06-05 | 2015-06-06 through 2015-06-19 | Fit A; preserve unavailable daily h2/h3/h9 |
| 2015-06-19 | 2015-06-20 through 2015-07-03 | Fit B; reviewed frozen values |

Fit B must not be assigned retrospectively to June 5. May 22 has no approved earlier calibrated
fit and is outside this uncertainty-bound handoff. Reject any other origin or target interval;
in particular July 3 + H14 is prohibited here. This restriction does not release a final protocol.
The scenario store universe is the explicit sorted config list `1..1115` from the approved
development cohort, not a Sales-ranked or future-availability-selected cohort.

### Frozen uncertainty identity and limitations

Reference canonical run `phase8-impl-20261006-provenance-review`:

| Identity | SHA-256 |
|---|---|
| Manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| Daily quantiles | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| Cumulative quantiles | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| Canonical policy/config | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` |
| Serialized config file | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |

These identities were copied from the accepted closeout record and checked by the implementation
before binding. Original publication flags remain unchanged; the later governance freeze is
separate evidence. Fit A is the accepted historical June 5 assessment fit, not the Fit B freeze
applied to an earlier issuance.

Fit B raw-primary coverage is **12,263/13,437 = 91.26%, below nominal 95%**. Sunday h2/h9 have
only 65/64 calibration rows from 33/32 stores across two origins. Stores and origins are
dependent. Saved-source-Open operational replay is conditional on an unverified historical
availability assumption, and deterministic closures inflate pooled coverage. There is no
conformal, per-store, production or service-level guarantee. Cumulative quantiles support only
approved origin-anchored prefixes; no later daily-review suffix calibration is authorized.
The final holdout remains unreleased, and the target remains monetary Sales.
The development windows also informed Phase 7 model selection; replay results are not an
independent final test of the selected system.

## 3. Entities, keys and schema

Schema version: `phase-9-synthetic-v1`. Dates are timezone-free calendar dates
(Arrow `date32`); origin means the end of that date. Monetary values/rates/factors are float64;
Store/counts/Sales sums are int64; lead/review/protection/coverage days, replicate and horizon
are int8; flags Boolean and categories/digests UTF-8 strings. Keys/counts are never nullable;
the explicitly nullable schedule code is int8. Only declared unavailable/not-applicable fields may be null;
NaN/infinity cannot stand in for null. Parquet files use an explicit ordered Arrow schema,
zstd compression and no dataframe index. Lists live in JSON config rather than object columns.

| Entity / file | Primary key | Required fields beyond key |
|---|---|---|
| Run / `scenario_config.json` | `run_id` | `schema_version`, `generator_version`, seed 4209, origins, sorted Store list, replicates, all ranges and overrides, stream role names, H=14, initialization/schedule/value/cost conventions, immutable upstream identities and approval reference |
| Scenario / `scenario_catalog.parquet` | `scenario_id` | `family`, `mode`, `forecast_origin`, `replicate`, `horizon_days`, `schedule_mode`, `demand_basis`, `stress_spec_id`, `calibration_transport_valid` (false for synthetic stress) |
| Origin anchor / `origin_anchors.parquet` | `Store, forecast_origin` | `history_start`, `history_end`, `observed_history_start`, `observed_history_end`, `observed_rows`, `open_rows`, `closed_rows`, `closed_positive_sales_rows`, `unknown_open_rows`, `missing_calendar_days`, `open_sales_sum`, `mean_open_sales_value`, `anchor_available`, `zero_anchor`, `unavailable_reason`, `history_logical_sha256` |
| Store scenario / `store_parameters.parquet` | `scenario_id, Store` | `SupplierLeadTime`, `ReviewPeriod`, `ProtectionPeriod`, `InventoryCoverageDays`, `InitialStockOnHandValue`, `InitialOnOrderValue`, `InitialBackordersValue`, `InitialInventoryPositionValue`, `ProcurementCostRatio`, `AnnualHoldingRate`, `HoldingCostRate`, `GoodwillPenaltyRate`, `StockoutPenalty`, `AverageUnitValue`, `TrendEndChange`, `PromotionResponseSlope`, `PlannedPromoBlock`, `PlannedDiscountDepth`, `initialization_available`, `unavailable_reason` |
| Future exogenous context / `scenario_daily.parquet` | `scenario_id, Store, Date` | `horizon`, `ScenarioOpen` (nullable int8), `SyntheticPromo` (nullable Boolean), `SyntheticHolidayClosure` (nullable Boolean), `DiscountDepth`, `WeekdayFactor`, `TrendFactor`, `PromotionFactor`, `CommonShock`, `StoreDateNoise`, `NoiseFactor`, `DemandStressFactor`, `SyntheticDemandValue`, `synthetic_demand_available`, `unavailable_reason` |
| Upstream binding / `upstream_bindings.json` | `forecast_origin` entries | Selected model/recipe/manifest/file identities from Phase 7; canonical Phase 8 file and policy identities; compatible fit, dates, opening-schedule assumption, permitted L/P prefixes and p grid; `suffix_supported=false`; source paths and verification evidence |
| Validation / `validation_summary.json` | `run_id` | Checks, expected/actual counts, per-origin/family availability and zero anchors, exclusion reasons, min/max parameters/factors, arithmetic maxima, hash/determinism results, status; no service/cost/policy or forecasting metrics |
| Publication / `manifest.json` | `run_id` | Section 7 provenance and every output's byte/logical hash, schema and row count |

Nullability rules: anchor window bounds/counts/sum/digest are required (empty history has zero
counts/sum); observed history start/end are null exactly when there are no observed keys;
mean is null when the anchor is unavailable; `zero_anchor` is false unless an available
mean is zero. Store parameters are required except dependent initial stock/position, which
are null for an unavailable anchor. Initial on-order/backorders remain the declared zero
assumptions. All availability flags are required; reason is null exactly when available.
Daily synthetic context fields are required in synthetic mode except unknown `ScenarioOpen`
and unavailable `SyntheticDemandValue`. They are all null in historical-reference mode;
its demand availability is false with `historical_outcomes_not_loaded`. Keys/horizon stay
required in both modes. An unavailable anchor takes precedence over closure routing: its
synthetic demand is null even on a known-closed day, while exogenous factors remain recorded.

Catalog enums: `mode` is `historical_replay` or `synthetic_stress`; `demand_basis` is
`historical_observed_sales_reference` or `synthetic_turnover_proxy` respectively.
`schedule_mode` is `conditional_saved_source_open_reference` or `synthetic_planned_weekly_v1`;
`stress_spec_id` equals the family name. `calibration_transport_valid=true` only denotes
the permitted conditional historical population, subject to consumer identity/completeness
checks; it never means guaranteed coverage. It is always false in synthetic mode.

`scenario_id = <family>-<YYYYMMDD>-r<replicate as two digits>`; accepted replicates are 00..04
for each synthetic family and 00 only for historical replay. Catalog is the foreign-key parent
of parameters/daily context; each parameter row references its catalog origin's anchor.
`Date = forecast_origin + horizon` with horizon 1..14. Every configured store has an anchor
and every catalog-store has parameter and daily-grid rows even if initialization is unavailable.
No forward-fill, row removal or inferred zero is used to repair availability.

The future daily table contains no `Sales`, `actual_sales`, `Customers`, source `Open`,
observed future `Promo`, forecast values, residuals or quantiles. `ScenarioOpen` /
`SyntheticPromo` must never alias real feature names in a feature join. Source history
is not copied wholesale; the anchor holds only counts, sum, mean and a censored digest.
The p grid `["0.90","0.95","0.98"]` and reference p `"0.95"` are binding metadata;
Phase 9 does not choose a policy or compute inventory targets.

## 4. Origin-safe initialization

For each allowed origin o, use exactly the 56 calendar dates `[o-55, o]`. The reader projects
only `Store, Date, Sales, Open` with both range predicates and `Store in configured_stores`
at the storage boundary, before
dataframe conversion. Check o and o+14 before opening an input. Never read a full CSV/dataframe
and filter afterwards; never read feature inference, test, EDA cohorts or saved evaluation
residuals for initialization.

The implementation can follow the projected/date-filtered reader pattern in
[lightgbm_runner](../../src/rossmann_forecasting/forecasting/lightgbm_runner.py);
its existing history helper lacks Open and is not itself a suitable initializer.
Keep forecasting interfaces unchanged. The initializer's in-memory API rejects an out-of-range
date rather than silently filtering an already exposed future label.

1. Validate unique Store-Date, integer nonnegative Sales, Open in {0,1,null}, exact calendar
   dates and configured Store membership. Do not repair duplicate/invalid rows. Unknown Open
   does not become a closed or eligible open observation.
2. Count observed keys and missing calendar dates against the 56-date grid without fabricating
   Sales rows. Count Open=1/0/unknown separately. Closed-day Sales remain source truth, even
   if positive; disclose that count in validation, without overwriting or interpreting it as loss.
3. Require at least **28 observed Open=1 rows with valid Sales**. Otherwise mark
   `insufficient_open_history` (or `no_store_history`) and leave the mean and dependent
   stock/demand null. Retain the store in the coverage report. No borrowing or fallback.
4. Compute `m = integer sum(Sales where Open=1) / open_rows` in sorted date order.
   This is recent observed open-day turnover, not a latent-demand estimate. A zero sum is a
   valid `zero_anchor=true` case: m=0, initial stock=0, synthetic turnover=0 on known days.
   Do not divide by m or exclude such stores to improve a comparison.
5. Generate coverage C as specified below. `InitialStockOnHandValue = m * C`.
   C means **reference open-day-equivalent coverage**, not expected calendar days of service.
   Lead time remains calendar days. The distinction is explicit: closures affect future
   operational context, not the definition of the origin's turnover anchor.
6. Cold-start assumptions: `InitialOnOrderValue=0`, `InitialBackordersValue=0` and
   `InitialInventoryPositionValue=InitialStockOnHandValue`. They describe only initialization.
   No initial pipeline is reconstructed from Sales; no order queue is created in Phase 9.
   Phase 10 must maintain nonzero outstanding orders when its policies generate them.

Hash only the projected origin-window records, including null Open, sorted Store/Date under
Section 7's logical encoding. Record the preparation manifest's already recorded source
identities as inherited metadata; **do not recompute a full-source train file hash**, which
would read protected labels. Record the reader predicates and actual maximum date.
Missing history is an availability result; contradictory schemas/keys/values are fatal integrity
failures. Initialization and RNG inputs never depend on future Sales, Open, Customers,
forecast error, interval hits or eventual inventory performance.

## 5. Deterministic generation and parameter dependencies

All choices below are approved illustrative course assumptions; no range is estimated from
actual inventory, margins, prices or holdout performance.

### Seed and sampling algorithm

Use `sha256-counter-uniform-v1`, master seed **4209**, replicate 0..4, without a global
random state or Python `hash()`. For each draw, canonical JSON encodes the ordered array
`["phase-9-synthetic-v1",4209,replicate,origin_iso,scope,role,counter]`
(UTF-8, compact separators, no whitespace, no nonfinite numbers).
Scope is `["store",Store]` for store parameters, `["date",date_iso]` for common date
shocks, or `["store_date",Store,date_iso]` for idiosyncratic noise.
Draw roles are exactly `SupplierLeadTime`, `InventoryCoverageBuffer`, `ProcurementCostRatio`,
`AnnualHoldingRate`, `GoodwillPenaltyRate`, `AverageUnitValue`, `TrendEndChange`,
`PromotionResponseSlope`, `PlannedPromoBlock`, `PlannedDiscountDepth`, `CommonShock`
and `StoreDateNoise`. The first ten use store scope; the last two use date/store-date scope.
Counter starts at 0; only the discrete rejection rule below increments it in version 1.

Take the first 8 digest bytes as unsigned big-endian integer Z; shift right 11 bits to obtain
J and set `u=J/2^53` in [0,1). Continuous `U[a,b)` means `a+(b-a)*u`;
Bernoulli draws use `u < p` on this specified finite grid.
For a uniform discrete choice of n ordered values, accept Z only if
`Z < n*floor(2^64/n)`, then select index `Z mod n`. Otherwise increment the same role's
counter and rehash until accepted; exceeding 100 attempts fails generation.
This avoids modulo imbalance and fixes the sampling convention without a library's implicit
default RNG. Closed range checks include endpoints to accommodate configured overrides.
The role `InventoryCoverageBuffer` selects the buffer; `PlannedDiscountDepth` draws
discount and `PlannedPromoBlock` draws promotion participation.

Family/scenario IDs and policy names are **excluded** from draw keys: base and stress variants
share the same draws within origin/replicate/Store/date; deterministic overrides apply afterwards.
Neither run ID, input order, subset, worker count, timestamps nor upstream/config hashes enter
draw keys. Thus adding a scenario/store cannot perturb an existing store's draws. Different
origins/replicates have different keys. Log the exact key grammar and algorithm version.
This supplies reproducible artificial variation, not calibrated random uncertainty.

### Parameter contract

| Field | Base generation / allowed range | Dependency / meaning |
|---|---|---|
| `SupplierLeadTime` L | Uniform discrete {2,3,4,5,6,7} | Fixed over a Store-scenario's H14; stress may override to 7. No random receipt delay or queue scheduling here. |
| `ReviewPeriod` R; `ProtectionPeriod` P | R=1; P=L+1, integer 3..8 <=14 | Context for later design, not permission to use unsupported suffixes. |
| `InventoryCoverageDays` C | C=L+1+B; B uniform discrete {0,1,2,3} | Base range 3..11 open-day equivalents. Adversarial scenarios may set C=1; overall approved range 1..11. Stock is m*C. |
| `ProcurementCostRatio` c | U[0.55,0.85) K/V | `ProcurementCost(v)=c*v` for retail-equivalent v. It never changes stock or demand units. |
| `AnnualHoldingRate` a | U[0.10,0.30) per year on procurement-value proxy | `HoldingCostRate=c*a/365` K/V/calendar day; positive and <=0.85*0.30/365. No compounding/leap-year adjustment. |
| `GoodwillPenaltyRate` g | U[0.10,0.75) K/V unmet | Explicit extra illustrative penalty, not measured customer loss. |
| `StockoutPenalty` s | s=(1-c)+g, allowed [0.25,1.20] K/V unmet | One total unmet-value penalty including a hypothetical margin component; Phase 10 must not add that margin again. |
| `AverageUnitValue` | Uniform discrete {5,10,20,50} V/equivalent unit | Display-only illustrative conversion. No SKU inference, rounding or integer order constraints in Phase 9. |
| `TrendEndChange` t | U[-0.10,0.10) | At horizon h, `TrendFactor=1+t*h/14`. Stress overrides t=0.30; allowed t [-0.10,0.30]. |
| `PromotionResponseSlope` e | U[0.5,1.5) | Synthetic turnover-response coefficient; not estimated price/demand elasticity. |
| `PlannedPromoBlock` | Bernoulli p=0.40, one store-level draw | If true, synthetic promo on h4..h6; otherwise all false. Stress may replace the block. |
| `PlannedDiscountDepth` d | U[0.05,0.30) | DiscountDepth=d on synthetic promo days, otherwise exactly 0. Stress may use 0.40; allowed [0,0.40]. |
| Weekday factors | Monday..Sunday = [0.95,0.98,1.00,1.02,1.10,1.15,0.80] | Illustrative synthetic multipliers: mean 1 over seven calendar days but mean 1.033333... over default Monday–Saturday open days. Not normalized to preserve the historical anchor's mean and not fitted Sunday effects. |
| `CommonShock` z; `StoreDateNoise` v | z=U[-0.10,0.10), v=U[-0.15,0.15) | z is shared by all stores/families on a replicate-origin-date; v is Store-date-specific. `NoiseFactor=1+z+v` in [0.75,1.25]. |
| `DemandStressFactor` w | 1 base; explicit overrides in Section 6, allowed [0,2] | Same-date stress pulses are shared across stores; no IID or empirical dependence claim. |

All independent draws have distinct role keys. Dependencies are explicit: stock on turnover and
coverage; coverage on lead time; P on L/R; carrying rate on c/a; shortage penalty on c/g;
discount on synthetic promotion; common shocks across stores; adverse turnover and supply/stock
overrides jointly applied in the coupled family. No full-history Store cohort or fitted
cross-correlation is introduced.

For a synthetic known-open day, use the following ordered binary64 multiplications:

`SyntheticDemandValue = ((((m * WeekdayFactor) * TrendFactor) * (1 + e*DiscountDepth)) * NoiseFactor) * w`.

Persist every component including `PromotionFactor=1+e*DiscountDepth`. No independent
daily-residual resampling, interval-derived synthetic truth, hidden scaling or clipping is allowed.
All factors must be finite and their combined factor <=6 (the largest prescribed endpoint
product is 1.15*1.30*1.60*1.25*2=5.98).
For `ScenarioOpen=0` set synthetic turnover to 0 and retain the unrouted factors for audit.
For unknown opening status or unavailable anchor, publish null demand with an explicit reason.
Unknown never becomes zero. Closed-day zero describes an artificial closure, not latent demand.

## 6. Predeclared scenarios and schedule contract

Default synthetic schedule: Monday..Saturday open, Sunday closed, computed from Date.
It is an **invented planned schedule known by assumption at the scenario origin**, not a
reconstruction of Rossmann opening. `SyntheticHolidayClosure=false` unless overridden;
closure pulses are synthetic calendar events, not inferred source holiday meanings.
Schedules/promotions/stress paths are exogenous and identical for every later compared policy.
The config is the issue-time evidence; no saved actual Open is imported into these synthetic fields.

| Family (mode) | Overrides to shared base draws | Purpose |
|---|---|---|
| `historical_replay_reference` (historical replay), replicate 00 | Base operational parameters/stock; all future synthetic fields null, demand unavailable with `historical_outcomes_not_loaded` | Phase 10 may separately bind unchanged observed development Sales and conditional saved-source-Open forecast context. Phase 9 never fabricates these outcomes. |
| `synthetic_base` (synthetic stress) | None | Trend, weekly seasonality, artificial planned promotion, common and individual noise with base supply/stock. |
| `promo_peak` (synthetic stress) | Promo h4..h8 inclusive, d=0.40; w=1.50 on those days | Strong assumed promotion/turnover pulse; no causal price elasticity claim. |
| `demand_slump` (synthetic stress) | w=0.25 for all h | Low-volume cost/overstock stress, not a real forecast regime. |
| `trend_ramp` (synthetic stress) | t=0.30 for all stores | Common upward trend beyond the base range. |
| `long_lead_low_stock` (synthetic stress) | L=7, P=8, C=1 | Adversarial initial shortage exposure without changing the permitted calendar lead-time range. |
| `calendar_closure` (synthetic stress) | Close h8, `SyntheticHolidayClosure=true` there; w=1.50 at h10 | Exogenous Saturday closure followed by the configured Sunday closure and a Monday reopening pulse. No closure feedback into raw forecasts. |
| `coupled_peak_delay` (synthetic stress) | L=7, P=8, C=1, t=0.30; promo h4..h8 with d=0.40; w=2 at h4..h8 | Joint common turnover peak, long supply time and thin stock; explicit adverse cross-variable dependence. |
| `zero_turnover` (synthetic stress) | w=0 throughout | Degenerate denominator and no-demand fixture/scenario; initial stock still follows the same observed m and coverage. |

There are 41 scenarios per origin (1 replay + 8 synthetic families * 5 replicates), hence 82
catalog rows, 2,230 anchors, 91,430 parameter rows and 1,280,020 daily-grid rows for the default
1,115 stores. These are designed counts, **not generated results**. Unavailable anchors do not
change these counts. The five replicates illustrate assumptions; they supply no statistical
power, probability-of-stockout estimate or tuned scenario weighting.
Stress cases must be reported separately, never pooled into real Rossmann forecast scores.

Adversarial fixture inputs additionally cover unknown schedule, no/short history, missing dates,
zero anchor, duplicate keys, corrupted hashes, future rows and extreme valid parameters.
They are validation fixtures rather than automatic repairs or extra canonical scenario families.
No optimization against forecast assessment or policy performance selects these cases or ranges.

## 7. Artifact, provenance and failure contract

Implemented location: `data/processed/synthetic_inventory/<run_id>/`, entirely Git-ignored;
optional `current.json` identifies a completed run. No generated output is tracked. The four
Parquet tables and four JSON files in Section 3 form a self-contained handoff; retain upstream
references rather than copying/reformatting model or quantile tables.

Config canonical identity: SHA-256 of UTF-8 JSON with sorted object keys, compact separators,
`ensure_ascii=true` and `allow_nan=false`, excluding `config_canonical_sha256`,
`run_id` and `created_at_utc` (if present). These publication fields do not change the
semantic scenario specification.
List order is significant; configured stores/origins/roles are sorted and factors ordered by
ISO weekday. The serialized config has a separate byte hash.
For each Parquet output record byte SHA-256, logical SHA-256, byte length, row count and
ordered schema. For JSON outputs record byte hash/length and canonical JSON hash; row count/
table schema do not apply. Their semantic hash excludes only top-level current-run
`run_id`, `created_at_utc` and self-hash fields; nested frozen upstream identities are
retained. Manifest output metadata excludes the manifest itself.
Logical table encoding is a schema JSON line followed by primary-key-sorted JSON-array rows,
one newline each: dates ISO YYYY-MM-DD; integers/bools native JSON; strings unchanged; null
as JSON null; float64 values as `float.hex()` strings with negative zero normalized to zero.
Schema specifies field order, type and nullability. This avoids Parquet metadata/compression
differences being mistaken for semantic changes. Exact byte equality is required only under
the same locked writer environment; logical equality is required across supported environments.
Checksums are evidence, not proof of origin-time information availability.

Manifest records: command/arguments; run/schema/generator versions; config file/canonical hashes;
seed/key grammar; code Git SHA, clean/dirty state and source-code digest; Python/platform and
package versions; `uv.lock` hash; origin predicates and censored history logical hashes;
inherited preparation/source identities explicitly labelled not freshly byte-verified; selected
model/recipe/Phase 7 file hashes; Phase 8 run/file/policy identities and governance acceptance
reference; schedule/value/cost assumptions; exclusion counts; output metadata; validation status;
`design_approved` evidence reference and `inventory_simulation_performed=false`.
Run-specific timestamps/run IDs stay out of semantic payload hashes.
`manifest.json` cannot include its own final byte hash: record that hash in the external
pointer/review evidence after writing it. Never rewrite upstream publication flags.

Future binding reads first validate resolved allowlisted paths. For development Parquet,
inspect footer Date bounds/row counts before whole-file hashing; reject post-July-3 bounds
or missing/insufficient date statistics without loading outcome columns as a fallback.
Then verify byte identities and project forecast keys/raw point/availability/provenance
without outcome/residual columns. Pin Phase 7 identities to the canonical Phase 8 manifest's
accepted input lineage and Phase 7 handoff, rather than trusting a mutable latest pointer.
Missing statistics are an integrity failure for these frozen development exports, not a
restriction on the separately censored history reader. The generator does not call an
uncertainty calculation API.
Do not hash raw/interim full-source files for binding. A development-only upstream byte hash
can verify immutable lineage, but no later-origin outcome value influences anchors or draw keys.
Snapshot inputs before computation; repeat input identity checks before publishing.
The second history check repeats the same censored projection and logical digest, not a
full-source byte read. The saved forecast schema can be inspected in
[model_selection](../../src/rossmann_forecasting/forecasting/model_selection.py), and canonical
hash/fit restrictions in [uncertainty](../../src/rossmann_forecasting/forecasting/uncertainty.py);
do not invoke an estimator or a verifier that loads residual outcomes for this generator.

| Condition | Required behavior |
|---|---|
| Unapproved config/design, unsupported origin/horizon/Store, forbidden source or holdout request | Fail before data access/generation; no partial publication. |
| Duplicate keys, invalid schema/nonfinite/negative observed Sales, illegal Open/parameter value, broken foreign key or inconsistent arithmetic | Fatal integrity error; preserve inputs, never clip/repair/retry with another seed. |
| Missing origin history / fewer than 28 Open=1 rows | Anchor and dependent stock/demand unavailable with reason, retain all keys and counts; other parameter assumptions remain finite. |
| Known closed synthetic day with an available anchor | Demand exactly zero with closure evidence; an unavailable anchor instead leaves dependent stock/demand null. |
| Unknown schedule | Demand null; every later required prefix crossing it must remain unavailable. |
| Missing frozen file, wrong model/fit/hash, unavailable calibrated bound | Missing/mismatched required files fail publication. An unavailable bound is preserved as upstream availability, not filled or recalibrated. |
| Source changed during generation or output hash/count/schema failure | Fail staged run; do not publish manifest, replace pointer or alter earlier runs. |
| Existing run ID, non-ignored output location, path escaping intended root | Refuse overwrite/publication. |

Build in an ignored staging directory, validate and reread outputs, recheck inputs, write manifest
last, then atomically publish the new directory and replace the pointer. Failed staging must not
be treated as a handoff; retain or remove only the new task-owned staging area, never earlier
runs. A valid run may have unavailable stores; `complete_with_unavailable_inputs` is explicit
and is not evidence that all inventory scenarios can be simulated.

## 8. Implementation boundary after approval

Implemented reusable module: `src/rossmann_forecasting/inventory/scenarios.py`, with interfaces
for config validation, censored history loading, anchor computation, keyed draws, parameter/context
generation, validation and immutable publication. Entry point:
`scripts/generate_inventory_scenarios.py`; fixtures: `tests/test_inventory_scenarios.py`.
Use existing pandas/NumPy/PyArrow/standard-library dependencies and the locked environment;
no new package, feature column or forecasting adapter is needed.

Generation consumes validated config + origin-safe history + verified upstream bindings and
returns Section 3 evidence only. No forecast service receives synthetic columns, and the
29-column [feature contract](../../docs/FEATURE_CONTRACT.md) remains byte/schema unchanged.
Do not add state transition, order placement/receipt, queue, inventory target, equivalent-unit
rounding, cycle, KPI, cost-aggregation or policy-comparison functions in Phase 9.
The implementation ran the full fixture suite and canonical development scenario build; results
and exclusions are recorded in PROGRESS. Independent implementation review remains pending.

## 9. Exact Phase 10 handoff and remaining authority

Phase 9 hands over verified catalog/anchor/parameter/daily-context artifacts, config/manifest,
validation/exclusion evidence and read-only frozen forecast/uncertainty bindings. Phase 10
must use identical exogenous paths/starting stocks/replicates for every compared policy and
preserve missingness. Historical replay binds observed Sales only in its evaluation layer;
synthetic replay uses `SyntheticDemandValue` and never rewrites observed Sales.
No inventory outcome, achieved service, savings or recommended policy is delivered here.

For historical replay, preserve the Phase 8 `saved_source_open_assumed_known_at_origin`
conditional interpretation; source Open is never presented as proven origin-known information.
For a synthetic schedule or synthetic promotion/demand regime, the saved real raw point
forecast remains fixed and is a deliberately stressed input, not a forecast fitted to that
artificial world's covariates. **Phase 8 calibration does not transport automatically to
synthetic stress.** `calibration_transport_valid=false`; any Phase 10 use of frozen q as a
heuristic sensitivity input needs approval and cannot claim calibrated coverage/service.
Phase 9 does not create newly routed forecasts or bound tables for synthetic schedules.

The supported calibrated lookup requires matching model/recipe, Fit A/June 5 or Fit B/June 19,
schedule assumption, p, complete origin-anchored `h1..k` and upstream availability.
Inventory consumers are limited to L=2..7 and P=L+1=3..8. Preserve signed q and ADR-016
`D_k=sum operational point prefix; U_k=max(0,D_k+q_p); Safety=max(0,U_k-D_k);
Target=max(D_k,U_k)`. Do not sum marginal daily bounds, scale q to a store or stress multiplier,
clip negative q, or use a prefix q for `h(t+1)..h(t+P)` at a later daily review.
This handoff specifies references and restrictions only; Phase 9 implements no policy target or
inventory-state calculation.

**Phase 10 design must separately resolve:** supported review dates/forecast refresh, prefix-only
demonstration versus independently approved suffix calibration; event ordering and lead-time
receipt convention; lost-sales/no-backlog semantics; outstanding-order queue; finite-horizon
terminal receipts/censoring; cycles and KPI denominators; policy baselines/comparisons and cost
aggregation. In particular c*v is procurement cost, c*a*v/365 is daily carrying cost at a yet
unspecified stock measurement point, and s*unmet is a total penalty; Phase 10 must define its
cost objective without double-counting margin/revenue/acquisition effects.
R=1 metadata alone does not authorize rolling calibrated daily decisions.
Until that gap is approved, only supported origin-anchored decisions can be claimed calibrated.
No Phase 10 code or comparison begins under Phase 9 approval.

## 10. Fixtures, numerical acceptance and reproducibility gates

These are the implementation acceptance criteria. Results from the canonical run and local
quality gates are recorded in Section 14 and PROGRESS:

| Fixture / gate | Numerical or exact acceptance criterion |
|---|---|
| Storage-boundary censoring | Spy reader sees only Store/Date/Sales/Open with [o-55,o] and configured Store predicates; forbidden paths never opened. July-origin requests fail before any read. Appending/changing post-origin Sales/Open/Customers cannot change initializer outputs. |
| Availability threshold | Exactly 28 valid open rows succeeds; 27 fails with null mean/stock/demand. Missing dates stay missing; unknown Open excluded explicitly. Zero anchor remains valid, never a divide-by-zero. |
| Hand anchor/stock | 28 open rows with Sales=100 => m=100. L=3, B=1 => R=1, P=4, C=5, initial stock/position=500, initial on-order/backorders=0. |
| Cost arithmetic | c=0.70, a=0.20, g=0.50 => procurement for 100 V is 70 K; holding rate=0.14/365; total shortage penalty=0.80. Display conversion never changes these monetary values. |
| Hand synthetic turnover | m=100, weekday=1, trend=1, discount=0.20, e=1, noise=1, w=2 => known-open demand=240; known-closed=0; unknown=null. Unrouted factors retained. |
| Bounds and relationships | 100% available monetary quantities finite/nonnegative; signed trend/noise components follow their declared ranges. Integer L in2..7, R=1, P=L+1 <=14; C in1..11; discount zero iff no promo and positive if promo; cost formulas/ranges and combined factor<=6. No silent cap. |
| Grid and joins | Exact Section 6 counts at default config, including unavailable stores; no duplicate/foreign-key/date gaps. Smaller fixtures use exactly catalog_count*store_count*14 daily rows. |
| Common random numbers | Base vs stresses have identical unaffected draws; common date shock equal across stores; overrides occur only on declared fields/dates. No policy-dependent input. |
| Determinism | Same logical hashes on repeat, reordered history/config Store list after normalization, alternate chunk/worker order and Python 3.12/3.14. A subset's retained rows exactly match the full run's projection. Golden seed/key vectors and independently checked expected draw values are required before implementation acceptance. Changed replicate alters at least one nondegenerate draw, with no claim it must change every value. |
| Frozen identity / chronology | Wrong hash/model/fit fails. Fit B at June5 forbidden; unavailable Fit A daily tails retained. Original Phase 7/8 bytes unchanged pre/post build. No residual-calculation/model-fit call allowed. |
| Feature isolation | Original 29 ordered predictor names/dtypes unchanged; no scenario field passed to training/inference, no SyntheticPromo->promo or ScenarioOpen->Open feature substitution. |
| Failure atomicity | Inject upstream mutation, invalid output, duplicate key and existing run ID: no final run/pointer replacement and earlier run bytes unchanged. |

Arithmetic comparisons use `abs(actual-expected) <= 1e-9 * max(1,abs(expected))`;
key/schema/zero/null/integer and logical-hash checks are exact. An arithmetic tolerance does
not permit row loss, hash mismatch or nondeterministic generation. Nonfinite values fail.
Verify logical determinism across supported environments in fixture CI; do not require Parquet
byte identity across writer versions. Do not interpret approximate uniform draw histograms as
empirical Rossmann distributions or fail a small deterministic fixture for sampling imbalance.

Implementation review uses the workflow's full pytest, Ruff lint/format,
documentation link checker and git diff check, plus lock/package consistency. A real
development scenario build must meet **zero structural/integrity violations**, exact default
row counts, 100% declared range/relationship validity and identical repeat logical hashes.
Report every unavailable store and zero anchor; no invented availability/coverage/service-rate
threshold or tuned scenario performance is an acceptance criterion.
The historical design PR ran documentation/repository checks only, with no data/model build.

## 11. Alternatives, risks and proposal-stage review questions

This section records the alternatives and review questions considered before external approval.
Their disposition is in Section 13; they are no longer open Phase 9 approval blockers.

| Choice | Approved decision / alternative and consequence |
|---|---|
| Turnover scale | 56-day Open=1 mean with >=28 eligible rows. Calendar-day mean including observed closures is an alternative but answers a different scale question; physical/latent-demand correction is prohibited. |
| Initialization | m*(L+1+buffer) and empty initial pipeline. Fixed stock independent of Sales or warm-start synthetic queues are alternatives; queues would need Phase 10 timing design. Cold starts can dominate short-window outcomes and must be disclosed. |
| Costs and conversion | Explicit c/a/g synthetic proxies and display-only equivalent units. Direct retail-value costs would be simpler but obscure procurement conversion; empirical margins/unit prices are unavailable. |
| Scenario truth | Origin-history anchor and configured factors. Using point forecasts as synthetic truth risks giving a forecast-driven policy a circular advantage; using interval upper bounds as truth confuses prediction with outcome. Neither is proposed. |
| Distributions | Bounded uniform/discrete draws with specified dependencies. Lognormal/heavy-tailed or empirically fitted marginals are alternatives requiring a new design; the proposed tails are artificial, not estimated risks. |
| Dependence | Shared date shock and coupled overrides. Independent stores alone would hide common shocks; learned covariance/regional cohorts would need additional origin-safe evidence and approval. |
| Schedules | Synthetic planned weekly schedule and declared closure pulses; historical replay remains a separately labelled conditional reference. Actual future Open is not a prospectively verified schedule and protected actual Open is prohibited. |
| Lead-time stress | Fixed Store-scenario L within2..7. Variable/order-specific delays or L>7 would change protection support/event semantics; exclude them here. |
| Quantile use | Compatible historical origin prefixes only. Synthetic q use can be a later labelled heuristic sensitivity experiment; daily-review suffix calibration is a separate unapproved method. |

The external reviewer was asked to explicitly accept/revise:

1. The 56-day open-turnover anchor, 28-row threshold, open-day-equivalent coverage and empty
   initial pipeline, including handling of sparse and zero-history stores.
2. The proposed c/a/g cost basis, penalty composition (no added lost-margin term), equivalent-unit
   display convention and parameter magnitudes; these are teaching assumptions, not market estimates.
3. The seed/draw contract, five paired replicates, synthetic schedule/promotion/seasonality/trend
   factors, bounded noise and adverse joint scenarios; no outcomes tune their parameters.
4. The two development origins, Fit A/B compatibility, historical versus synthetic separation
   and exact evidence/publication/failure contracts.

These four were the **Phase 9 approval questions**; their accepted disposition and reviewer
decision are recorded in ADR-022 and Section 13. The defaults below remain approved constraints
for implementation unless a superseding decision is recorded.
Phase 10's suffix/review/event/cost-objective choices remain deliberately unresolved and require
its own design approval, without delaying a separately approved Phase 9 exogenous generator.

Risks remain: Sales can be demand-censored or price/mix-driven; no correction is inferred.
Origin anchors may not represent changing turnover, sparse Sunday evidence limits uncertainty,
short windows/cold starts bias inventory comparisons, artificial cost ranges can determine
policy ranking, deterministic stress cases are not probabilistic tail estimates, and frozen
real forecasts/uncertainty may be poorly suited to synthetic schedules/regimes.
Report conditional scenarios and sensitivity, with no physical-stock, actual-loss, optimization,
coverage, service or savings claim. No final holdout, Phase 10, application or monitoring work
is authorized by acceptance of this Phase 9 design.

## 12. Design review checkpoint — 2026-10-07

Only documentation is changed. The branch base and PR #17 integration are verified above;
frozen identities are inherited review evidence. No scenario generation, implementation,
holdout read or new artifact verification was performed. Actual local checks and the design
PR/CI evidence are recorded in [PROGRESS](../../docs/PROGRESS.md) and the PR description.
Status remains **PROPOSED / AWAITING APPROVAL**.

This is the historical proposal checkpoint. The external acceptance and current status are
recorded in the later Section 13.

## 13. External methodology approval — 2026-10-07

**Decision: ACCEPT.** The external methodology decision supplied for this synchronization accepts
the design reviewed at PR #18 head `3820c2c34749b3baa4df954afc3daa0636cff271`. This approval
record is dated 2026-10-07. The reviewer identity was not supplied with the decision.

The reviewer accepted these four methodological choices:

1. **Origin-safe initialization.** Use 56 calendar days through each scenario origin and require
   at least 28 observed Open=1 records. Do not impute or use a fallback. Preserve valid zero
   anchors. Start with no outstanding orders or backorders, and initialize retail-equivalent
   monetary stock from the origin-safe turnover anchor and reference open-day coverage.
2. **Illustrative costs.** Use c in [0.55,0.85), a in [0.10,0.30), and g in [0.10,0.75);
   HoldingCostRate=c*a/365 and StockoutPenalty=(1-c)+g. Equivalent units are display-only.
   These values are synthetic assumptions, not measured business costs or savings.
3. **Deterministic scenarios.** Keep master seed 4209 and the exact SHA-256 keyed-draw grammar,
   five paired replicates, eight synthetic families, and a separate historical reference.
   Use the specified synthetic weekly schedules/promotions, shared shocks and declared coupled
   stress. Replicates do not imply empirical likelihood or statistical power.
4. **Chronology and artifacts.** Use origins 2015-06-05 and 2015-06-19 with H14 through
   2015-07-03 and Fit A/B compatibility. Preserve the protected holdout. Use origin-safe projected
   history and immutable, provenance-bound Phase 7/8 inputs; publication fails closed on
   integrity errors without imputation or fallback.

**Weekday-factor clarification required by the reviewer:** The factor values in Section 5 and the
synthetic-demand formula are unchanged. The seven values average 1 over Monday–Sunday, but the
six default open-day values sum to 6.20 and average 1.033333... . These are illustrative synthetic
multipliers, not open-day-normalized factors preserving the historical anchor's mean. This
clarification does not change any factor or the generation formula.

At the approval checkpoint, Phase 9 state was **APPROVED / IMPLEMENTATION NOT STARTED**; this
historical decision record does not describe the current implementation state. The approval does
not start Phase 10.
Its rolling suffix calibration, simulation event timing, order queue, replenishment policies and
inventory KPI methodology remain separately unapproved. Phase 8 quantiles remain limited to
approved origin-anchored prefixes and do not transport to synthetic stress. The protected
2015-07-04 through 2015-07-31 holdout remains unreleased.

## 14. Implementation checkpoint — 2026-10-07

The fixed-seed origin-safe generator, validation and immutable publication are implemented on
`feat/phase-9-synthetic-inventory` at source commit `8dae4e43e06d815746456a1786acfc264b77093b`.
The active review state is **IMPLEMENTED / UNDER REVIEW**; this does not close Phase 9. Frozen
Phase 7 and Phase 8 identities, date boundaries, availability and permitted projection passed
before any upstream file hashing. The implementation does not refit the model, recompute Phase 8
residuals, use forecasts or uncertainty as synthetic truth, or evaluate inventory policies.

Canonical local development run `phase9-dev-20261007-canonical2` completed with manifest SHA-256
`cc148d3670c0b20c769f245488ddd7f535f4333e6b0cf759c60e544e9c6c8a82`. It records source revision
`8dae4e43e06d815746456a1786acfc264b77093b`, `worktree_modified=false`, and verifies the frozen
Phase 7/8 manifest identities. Output counts are 82 catalog rows, 2,230 origin-anchor rows,
91,430 store-parameter rows and 1,280,020 daily-context rows. Both origins include all 1,115
configured stores with available anchors; unavailable anchors, zero anchors, missing dates and
closed-positive-sales history are each zero. All output byte hashes matched after publication;
four Parquet logical hashes matched a reversed-input reproducibility check.

The validation report records zero structural failures, zero cost-arithmetic error and maximum
combined factor 4.9650810021 (below the approved ceiling 6). Holdout values were neither read nor
hashed. Historical-reference rows contain no loaded future outcomes; synthetic turnover and
operational values remain artificial retail-equivalent monetary assumptions, not observed demand,
physical inventory, realized loss, service performance or savings. Detailed ranges, checks and
hashes are in [PROGRESS](../../docs/PROGRESS.md).

Local validation passed: 218 pytest fixtures; Ruff lint and format across the repository; Markdown
link checks; `uv lock --check` with uv 0.12.23 (84 packages, unchanged); Python 3.14.5
`pip check`; and `git diff --check`. GitHub Actions run [#45](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37555928596)
passed both Python 3.12 and 3.14 jobs on head `f9c41f0`, including fixture tests, lint, format and
Markdown checks. The phase boundary remains the scenario generator only: do not begin Phase 10,
merge this PR, or mark Phase 9 complete until review and integration closeout are explicitly
handled.

### External configuration-validation review fix — 2026-10-07

PR #19's finding that nested semantic settings were not frozen is addressed at source commit
`2ec2488adf065e692141eceb8e3f979df4679f45`. Validation now compares the complete configuration
against the accepted `default_config()` contract while retaining normalized fixture subsets and
run-specific publication metadata. Regression tests cover nested settings and early failure before
history processing. No methodology, ADR-022, RNG, equations, schemas or scenario outputs changed.

A new canonical development run, `phase9-dev-20261007-config-validation-fix`, preserves all four
Parquet logical hashes, row counts and byte hashes from the unchanged `canonical2` run. Its
manifest and validation details are recorded in [PROGRESS](../../docs/PROGRESS.md). Phase 9 remains
**IMPLEMENTED / UNDER REVIEW** on PR #19; no Phase 10 work or merge is authorized by this update.
