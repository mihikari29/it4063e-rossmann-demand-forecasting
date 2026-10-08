# Data Dictionary

Real-field observations below were measured from the official Kaggle Rossmann Store Sales snapshot
validated on 2026-10-05. Category codes are recorded as observed without inventing unsupported
business meanings. Phase 3 engineered predictors are implemented separately from source fields and
documented in Section B and the [Feature Contract](FEATURE_CONTRACT.md). Phase 2 diagnostic
derivations remain audit-only and are not model inputs. Synthetic variables remain simulated and
are not Rossmann operational data.

## A. Real Rossmann Variables

Availability describes the backtest/application contract, not evidence of when Rossmann released
each field historically. `store.csv` is one static snapshot; treating its metadata as available
at earlier origins is an explicit assumption. Calendar, promotion, and opening schedules are
future-known only when supplied or planned at the origin. The original source facts below remain
unchanged; source `Open` determines evaluation eligibility, not proven historical schedule knowledge.

| Name | Source file(s) | Meaning / unit | Observed type | Observed values or range | Missingness | Forecast-time availability and notes |
|---|---|---|---|---|---|---|
| `Id` | `test.csv`, `sample_submission.csv` | Competition row identifier | `int64` | 1–41,088; unique in both files | 0 | Supplied for future rows; test and submission identifier sets match |
| `Store` | `train.csv`, `test.csv`, `store.csv` | Store identifier | `int64` | 1–1,115; 1,115 train/metadata stores and 856 test stores | 0 | Primary unit key with `Date`; supplied for future rows |
| `DayOfWeek` | `train.csv`, `test.csv` | Source-provided weekday code | `int64` | 1–7 | 0 | Supplied for future rows; code meanings are not inferred here |
| `Date` | `train.csv`, `test.csv` | Calendar day | parsed date from source string | Train: 2013-01-01–2015-07-31; test: 2015-08-01–2015-09-17 | 0 | Primary unit key with `Store`; future-known |
| `Sales` | `train.csv` | Daily store sales turnover; monetary value | `int64` | 0–41,551 | 0 | Historical target only; affected by price/mix and potentially unmet demand; not physical units or uncensored latent demand |
| `Customers` | `train.csv` | Customers observed for a store-day | `int64` | 0–7,388 | 0 | Historical observation only; future actual values must not be production features |
| `Open` | `train.csv`, `test.csv` | Store-open indicator | train `int64`; test `float64` because of nulls | {0, 1} when present | Train: 0; test: 11 (0.026772%) | Preserve source truth; operational routing requires a supplied/planned schedule assumed known at origin. Unknown remains unknown. Separate uncertain candidates in `test_open_resolution.parquet` are audit-only, not known future status or raw-forecast inputs |
| `Promo` | `train.csv`, `test.csv` | Store-promotion indicator | `int64` | {0, 1} | 0 | Future-known when the promotion is planned |
| `StateHoliday` | `train.csv`, `test.csv` | State-holiday code | string | Train: {0, a, b, c}; test: {0, a} | 0 | Future-known calendar field; category meanings are not inferred from values alone |
| `SchoolHoliday` | `train.csv`, `test.csv` | School-holiday indicator | `int64` | {0, 1} | 0 | Future-known calendar field |
| `StoreType` | `store.csv` | Store type code | string | {a, b, c, d} | 0 | Static store attribute; category meanings are not inferred from values alone |
| `Assortment` | `store.csv` | Assortment code | string | {a, b, c} | 0 | Static store attribute; category meanings are not inferred from values alone |
| `CompetitionDistance` | `store.csv` | Source competition-distance measure; source unit not asserted here | `float64` | 20–75,860 when present | 3 (0.269058%) | Static metadata; missing-value handling is deferred |
| `CompetitionOpenSinceMonth` | `store.csv` | Calendar month competition began operating | `float64` because of nulls | 1–12 when present | 354 (31.748879%) | Static metadata; month/year are jointly missing for all 354 rows |
| `CompetitionOpenSinceYear` | `store.csv` | Calendar year competition began operating | `float64` because of nulls | 1900–2015 when present | 354 (31.748879%) | Static metadata; the source does not establish the missingness cause |
| `Promo2` | `store.csv` | Continuing-promotion participation indicator | `int64` | {0, 1} | 0 | Static, schedule-related metadata |
| `Promo2SinceWeek` | `store.csv` | Calendar week Promo2 participation began | `float64` because of nulls | 1–50 when present | 544 (48.789238%) | Missing exactly for all `Promo2 = 0` stores; structurally absent for non-participants |
| `Promo2SinceYear` | `store.csv` | Calendar year Promo2 participation began | `float64` because of nulls | 2009–2015 when present | 544 (48.789238%) | Missing exactly for all `Promo2 = 0` stores; structurally absent for non-participants |
| `PromoInterval` | `store.csv` | Months when Promo2 is active | string with nulls | `Jan,Apr,Jul,Oct`; `Feb,May,Aug,Nov`; `Mar,Jun,Sept,Dec` | 544 (48.789238%) | Missing exactly for all `Promo2 = 0` stores; schedule is future-known when present |

## B. Derived / Engineered Features

Phase 3 now implements a frozen 29-predictor schema, `phase-3-v1`. It includes unchanged `Store`
as both a key and a categorical-source predictor; calendar, holiday, promotion, store, and
competition features; exact-date Sales lags; and complete calendar-window Sales statistics. `Date`
is key-only. The detailed per-feature source, derivation, dtype, availability, null, leakage, and
train/inference rules are in the [Phase 3 Feature Contract](FEATURE_CONTRACT.md).

Dynamic features use exact same-Store Sales dates at d-1/d-7/d-14/d-28 and exact prior calendar
windows d-n through d-1 for n=7/14/28. Windows require every exact date and use sample standard
deviation (`ddof=1`); current-target Sales, absent dates, partial windows, and gap filling are
prohibited. Historical training rows use only Sales strictly before their target. Recursive
inference requires actual history censored at the declared origin and accepts optional earlier
predictions. No model-specific encoding, scaling, same-weekday features, or imputation is included.

Competition opening status and age use month-level arithmetic, not an asserted day: known
pre-opening is False/0, opening month is True/0, later age is completed calendar-month offsets,
and paired missing source metadata stays null/null. Promo2 nonparticipants are inactive; valid
participant schedules use the Monday of the ISO start week, recurring interval months, and target
Date. Incomplete/invalid schedules stay null and are audited. Availability/null diagnostics are
audit-only, not predictors.

Phase 3 feature diagnostics use development rows only. Its holdout audits are mechanical: schema,
keys, dtypes, determinism, and non-mutation; no holdout forecast metrics or feature selection were
performed. Earlier source validation and full-source EDA included descriptive holdout information,
as disclosed in [EDA findings](EDA_FINDINGS.md). Later model/interval/policy selection cannot use
holdout outcomes or reuse full-history Sales-based EDA cohorts. The final replay protocol is
defined in the [proposal](PROPOSAL.md) and [decision log](DECISIONS.md).

## C. Phase 2 Diagnostic Derivations

These audit-only fields are stored separately from the source-faithful prepared `test.parquet`.
They are not forecast features, and a candidate status is not guaranteed ground truth.

| Name | Source | Meaning | Rule | Availability / caution |
|---|---|---|---|---|
| `Open_resolved` | Prepared test `Open`; historical train `Open`; exact known covariates | Source Open when known; otherwise a candidate status when supported | For the same Store and exact `DayOfWeek`, `Promo`, `StateHoliday`, and `SchoolHoliday`, require at least 30 prior historical rows and unanimous observed `Open`; otherwise leave missing | Candidate is marked uncertain and kept in separate `test_open_resolution.parquet`; no future Sales or Customers are used |
| `Open_resolution_method` | Same as above | Distinguishes source status, unanimous historical context, and unresolved status | Deterministic label emitted by the audited rule | Phase 3 keeps this candidate audit-only; it never overwrites source Open or establishes eligibility/evaluation truth |
| `historical_match_rows` | Historical train `Open` and known covariates | Number of earlier matching historical records with known Open | Count exact-context prior rows | Evidence size, not a probability guarantee |
| `historical_open_rate` | Historical train `Open` and known covariates | Historical fraction with Open=1 in the matching context | Mean of known matching Open statuses | Descriptive evidence only |
| `resolution_uncertain` | Derived audit metadata | Flags a candidate or unresolved missing source status as uncertain | `True` for missing source statuses; `False` when the source status was present | Does not alter source `Open` |

## D. Synthetic Operational Variables

These are **synthetic or simulated fields, never Rossmann observations**. Phase 9's origin-safe
scenario inputs are implemented and formally complete. Phase 10's stateful simulation and corrective
review are accepted; formal completion takes effect when this closeout PR is integrated, as recorded in
the completed plan. Phase 9 generation uses its documented fixed seed; Phase 10 makes no random draws.
Monetary demand, stock, orders, and recommendations share a retail-equivalent turnover-value basis;
they are not procurement-cost inventory. Costs below are scenario proxies. Initial demand-dependent
inputs use only history available at the
simulation origin, and compared policies share inputs, demand paths, seeds, and starting stocks.
The [completed Phase 9 plan](../plans/completed/phase-9-synthetic-inventory.md) records the accepted
design and completed scenario generator. Section D.1 summarizes the accepted illustrative
assumptions. ADR-016's monetary basis remains in force; these assumptions are not observed Rossmann
operating data or measured business costs. Phase 9 does not implement the inventory simulator.

| Name | Category | Source | Meaning | Unit | Known Range | Generation / Derivation Rule | Availability at Forecast Time | Notes |
|---|---|---|---|---|---|---|---|---|
| `SupplierLeadTime` | Supply-chain input | Synthetic / simulated | Store-specific replenishment lead time | Calendar days | Integer 2–7 | Fixed-seed scenario assumption | Yes, as simulated input | Approved Phase 10: L full intervening demand days; EOD-t order received BO-day t+L+1 |
| `ReviewPeriod` | Policy input | Simulated policy | Time between replenishment reviews | Calendar days | 1 for initial simulator | Daily-review policy | Yes | Not a fitted Rossmann parameter |
| `ProtectionPeriod` | Policy derivation | Simulated policy | Lead time plus review period | Calendar days | 3–8; must be $\le14$ | `SupplierLeadTime + ReviewPeriod` | Yes | Distinct from lead time alone |
| `StockOnHandValue` | Inventory state | Synthetic / simulated | Available simulated stock | Retail-equivalent value | $\ge 0$ | Origin-safe recent Sales times initial coverage; then evolve with receipts and fulfilled proxy demand | Yes, as current simulated state | Not procurement cost or physical units |
| `OnOrderValue` | Inventory state | Synthetic / simulated | Outstanding scheduled receipts | Retail-equivalent value | $\ge 0$ | Sum outstanding order queue; remove orders on receipt | Yes, as current simulated state | Cannot be assumed zero throughout replay |
| `BackordersValue` | Inventory state | Simulated policy | Unfulfilled value carried forward | Retail-equivalent value | 0 in initial lost-sales policy | Record unmet value as lost sales instead of backlog | Yes | Alternative backorder policy requires reviewed design |
| `InventoryPositionValue` | Inventory derivation | Simulated state | Stock plus orders less backorders | Retail-equivalent value | $\ge 0$ under initial policy | `StockOnHandValue + OnOrderValue - BackordersValue` | Yes | Timing consistent with event order |
| `ServiceLevelTarget` | Policy input | Synthetic / simulated | Target probability of no shortfall over a protection period | Probability | 0.90–0.98; 0.95 base | Scenario's one-sided cumulative-residual quantile level | Yes | Approved Phase 10 uses p as nominal buffer parameter, not achieved cycle service/value fill or calibrated synthetic probability |
| `HoldingCostRate` | Cost input | Synthetic / simulated | Daily inventory carrying-cost proxy | Cost per inventory-value unit per day | Approved illustrative range in D.1 | Synthetic annual-rate conversion in D.1 | Yes | Approved Phase 10 applies to ending on-hand stock, including closed days |
| `StockoutPenalty` | Cost input | Synthetic / simulated | Cost proxy for unmet sales value | Cost per unmet-value unit | Approved illustrative [0.25, 1.20] | Approved total penalty in D.1 | Yes | Not actual Rossmann loss or margin |
| `AverageUnitValue` | Conversion input | Synthetic / simulated | Value used to illustrate equivalent units | Retail-equivalent value per equivalent unit | Approved illustrative {5,10,20,50} | Store-level display assumption | Yes | Display only; no real products or SKUs |
| `DiscountDepth` | Stress-scenario input | Synthetic / simulated | Simulated promotion intensity | Proportion | $0 \le x < 1$ | Zero when `Promo = 0`; positive when `Promo = 1` in the scenario | Yes, in synthetic scenarios only | Never a measured Rossmann predictor or reason to modify historical Sales |
| `InventoryCoverageDays` | Inventory-policy input | Synthetic / simulated | Initial stock coverage assumption | Reference open-day equivalents in approved design | Approved 1–11 | Multiply origin-safe recent open-day average Sales | Yes | Not calendar service duration; illustrative scenario input |

### D.1 Approved Phase 9 design contract

The [completed plan](../plans/completed/phase-9-synthetic-inventory.md) records the complete schema,
seed/draw grammar, scenarios, artifact hashes, failure rules and planned tests. These accepted
values are illustrative assumptions, not Rossmann facts:

- Origins are 2015-06-05 and 2015-06-19 only, with H14 ending by 2015-07-03.
  The anchor is the mean of observed Open=1 Sales in [origin-55, origin], requiring 28 valid
  open rows. Sparse/absent dates are not filled; zero turnover is valid.
- Base coverage is L+1+B, B uniform discrete {0,1,2,3}, giving 3–11 reference open-day
  equivalents; adverse thin-stock cases use 1. Initial stock is anchor*coverage. Initial
  on-order/backorders are zero only at cold start; Phase 10 owns later queue/state evolution.
- `ProcurementCostRatio` c is synthetic cost value per retail-equivalent value,
  uniform [0.55,0.85); `AnnualHoldingRate` a is [0.10,0.30).
  `HoldingCostRate=c*a/365` per calendar day. `GoodwillPenaltyRate` g is [0.10,0.75);
  `StockoutPenalty=(1-c)+g` includes the hypothetical margin component once.
  Cost proxies neither revalue stock nor establish actual margin or savings.
- `ScenarioOpen`, `SyntheticPromo`, discount, trend, weekly seasonality, common shocks,
  individual noise and `SyntheticDemandValue` are artificial context/path fields, never
  LightGBM predictors or observed Sales. Synthetic promotion response is not estimated
  price elasticity; synthetic closure implies zero turnover only for an available path.
- The approved weekday multipliers average 1 over seven calendar days and 1.033333... over the
  default Monday–Saturday open days. They are not normalized to preserve the historical anchor's
  mean; this clarification does not alter their values or the generation formula.
- Historical observed Sales, frozen point forecasts, frozen Phase 8 uncertainty and fully
  synthetic operational values remain separate. The Phase 8 Fit A/B chronology and
  origin-anchored prefix restriction persist. No calibrated synthetic-stress transport,
  later daily-review suffix method or protected holdout access is authorized.

Phase 9 implements no policy, event order, queue, inventory KPI or cost aggregation under this
approved design. Phase 10 implements those rules under the approved methodology; corrective implementation
and final external review are accepted. Its formal closeout and corrected development run are recorded
in the completed plan and [PROGRESS](PROGRESS.md).

## E. Approved Phase 10 Inventory Decision and Evaluation Outputs

These definitions distinguish simulated policy outputs from Rossmann observations. Phase 10's reviewed
implementation is formally complete when the closeout PR is integrated. Exact emitted column names and
grains are listed in the completed plan and canonical run manifest. `ReorderPointValue` and
`EquivalentUnits` are illustrative concepts, not emitted fields or physical quantities. Operational forecasts require known
source/planned Open; an unresolved required forecast makes the target unavailable rather than
silently supplying zero.

The [approved Phase 10 plan](../plans/completed/phase-10-inventory-simulation.md) and accepted ADR-023
define the refinements below. The implementation and corrected canonical development run are accepted;
the formal closeout is recorded in the completed plan.
They retain Phase 9's accepted monetary inputs and Phase 8's origin-prefix definitions. V denotes
retail-equivalent turnover value; K denotes synthetic cost-proxy units. Each H14 episode uses June
5/Fit A or June 19/Fit B, with targets fixed before evaluation outcomes are loaded.

| Output | Definition / unit | Interpretation |
|---|---|---|
| `LeadTimeDemandValue` / `ProtectionDemandValue` | Sum operational forecasts through $L$ / $P$; retail-equivalent value | Forecast sales proxy, not latent physical demand |
| `CumulativeUpperValue` | $\max(0,D_P+q_p(E_P))$, using complete out-of-sample cumulative residual paths; $p=ServiceLevelTarget$ | Frozen Phase 8 origin-prefix quantile; never sum daily bounds; synthetic use is uncalibrated transport |
| `SafetyStockValue` | $\max(0,U_P-D_P)$ for the simulator; retail-equivalent value | Non-negative simulated protection buffer |
| `ReorderPointValue` | $\max(D_L,U_L)$; retail-equivalent value | Continuous-review illustration, not the daily-review order-up-to target |
| `OrderUpToValue` | $\max(D_P,U_P)$; retail-equivalent value | Approved origin-frozen standing target from h1..P; reused at daily reviews without rolling calibration |
| `ReplenishmentValue` | $\max(0,OrderUpToValue-InventoryPositionValue)$ | Simulated value order; arrival date enters the queue |
| `EquivalentUnits` | $\lceil ReplenishmentValue/AverageUnitValue\rceil$ | Illustrative equivalent units, never real SKU quantity |
| `UnmetValue` / `EstimatedLostSales` | Positive proxy demand that cannot be fulfilled from simulated available stock; retail-equivalent value | Not observed Rossmann lost sales; lost-sales default carries no backlog |
| `StockoutRate` | Positive-demand days with unmet value / positive-demand days | Explicit denominator; unavailable when zero |
| `CompletedPositiveDemandReceiptCycleServiceRate` | Completed positive-demand receipt cycles with zero unmet value / completed positive-demand receipt cycles | Approved label: completed positive-demand receipt-cycle service rate; project-specific simulated CSL proxy, policy-dependent denominator, not guaranteed industry-standard CSL; zero denominator => null |
| `ValueFillRate` | $1-\sum UnmetValue/\sum DemandValue$ | Fraction of proxy value fulfilled; unavailable with zero demand denominator |
| `AverageInventoryValue` / `EstimatedHoldingCost` | Fixed daily stock measurement; mean stock / sum daily rate times stock | State event order and measurement convention; conditional cost proxy |

### E.1 Approved Phase 10 accounting and denominator definitions

- Baseline target is m times the number of origin-known open days in h1..P; forecast target uses
  the unchanged signed cumulative q at exact fit/P/p. R=1, L=2–7, P=L+1=3–8. L counts full
  intervening calendar demand days: EOD-t order arrives BO-day t+L+1. Origin review precedes
  outcomes, later reviews use the same standing target, and day-14 ordering is suppressed.
- Receipt-cycle boundaries are two observed positive receipt dates a_i<a_(i+1), with demand
  measured over [a_i,a_(i+1)-1]. Both boundaries must occur by T. Only positive-demand completed
  cycles enter the service-rate denominator; report zero-demand cycles and initial/terminal
  censored intervals separately. The denominator depends on the policy.
- Record `fulfilled_total`, `demand_total`, `positive_demand_stockout_days`, `positive_demand_days`,
  `ending_inventory_sum`, `calendar_days`, `zero_unmet_positive_demand_cycles` and
  `completed_positive_demand_cycles`. Fill=fulfilled/demand; stockout=positive-demand stockout
  days/positive-demand days; average inventory=ending-stock sum/14 for complete episodes.
  Zero service denominators give null. Pool ratios from totals, not Store percentages.
- `HoldingCost_t=HoldingCostRate*ending_on_hand_value` K and
  `UnmetPenalty_t=StockoutPenalty*unmet_value` K, using the unchanged c*a/365 and (1-c)+g rates.
  `SimulatedHoldingPlusShortfallCost` sums these over 14 days; no procurement expenditure,
  duplicate margin or revenue subtraction. `TerminalStockCostValue=c*I_T` and
  `OutstandingProcurementCommitment=c*O_T` are separate exposure diagnostics, not profit/savings
  or objective components. Retain due-after-T orders without cancellation, refund or salvage.
- Synthetic q use is an uncalibrated illustrative buffer: `calibration_transport_valid=false`.
  No nominal synthetic coverage/service claim. Unknown inputs remain null; missing demand stops
  dependent state evolution and prevents a complete-episode score. Known synthetic closures
  consume zero only for available demand; stock, receipts, reviews and holding costs continue.

Phase 9 fixes scenario ranges, seed, and generation rules; approved Phase 10 fixes event order, cycle
boundaries, forecast-refresh cadence, supported review dates, terminal-state handling, policy
comparisons, and KPI denominators. Both must be locked before the authorized
final replay. Historical Sales is held unchanged across policies; synthetic stress paths remain
separate, and results cannot establish actual Rossmann savings or stockout rates.

## Validation Notes

The real-variable observations are tied to the validated 2026-10-05 source hashes recorded in
[Data Acquisition](DATA_ACQUISITION.md) and [Data Validation](DATA_VALIDATION.md). Derived features
in Section B are Phase 3 outputs, not source variables. Synthetic variables remain proposed
simulation inputs and must never be presented as observed Rossmann data.
