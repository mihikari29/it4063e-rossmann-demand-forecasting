# Project Proposal

## Retail Demand Forecasting for Inventory Optimization (FMCG)

### Store-Level Business Analytics and Inventory Decision Support with Rossmann Sales

**Course:** IT4063E – Introduction to Business Analytics  
**Semester:** 20261 · **Class:** 175884 · **Instructor:** Dr. Bui Quoc Trung

**Team:** Pham Le Minh Quang (20235554), Tran Quoc Tuan (20235569), Vo Ta Quang Nhat (20225454),
Nguyen Trung Hieu (202416689), Nguyen Gia Minh (202400111).

## 1. Business problem and scope

> How much store-level sales turnover is expected over the next 14 days, and how do forecast-based
> inventory-value policies compare under explicit simulated operating assumptions?

Forecast **Store × Date monetary Sales** for 1,115 Rossmann stores. Sales is turnover, without
identifying physical quantities, latent unconstrained demand, actual inventory or stockouts.
Prices, mix and unmet demand may affect it. The instructor accepts this granularity and primary
H14 horizon; inventing SKU identifiers would add no observations. Synthetic operational variables
supplement the real forecasting core and support conditional decisions, without proving savings.

At origin $t$, predict $\hat y_{t+1},\hat y_{t+2},...,\hat y_{t+14}$ for store $s$.
A seven-day view is a subset of H14. A 28-step extension requires separate design/evaluation;
the 28-day final period does not imply that forecasting capability.

This proposal defines intended course delivery. [Progress](PROGRESS.md) owns demonstrated results
and [the roadmap](PROJECT_PLAN.md) owns remaining dependencies. Local development analytics and
applications are complete; real scenario analysis, supplementary STL findings, final replay/
monitoring, public release, PDF and slides remain incomplete. This proposal grants no new source,
method, execution or release approval.

## 2. Objectives and analytical questions

Build a reproducible descriptive → predictive → prescriptive workflow that:

- Explains trends, weekly/annual seasonality, promotions, holidays, Store characteristics,
  competition, variability, anomalies and supported associations, without causal claims.
- Compares Seasonal Naive, additive Holt-Winters and global recursive LightGBM fairly over the
  same chronological origins, observed eligible targets and supported Store-level scenarios.
- Forecasts monetary Sales over H14 and assesses daily and cumulative uncertainty separately.
- Translates supported forecasts into simulated targets/replenishment and paired service/cost/
  sensitivity comparisons, retaining deterioration or no benefit.
- Provides shared services, read-only FastAPI and Streamlit, then two public demonstration URLs
  only after exact-content/rights/security/resource and owner-release approvals.
- Delivers monitoring and human retraining-review conditions, reproducible source/dictionary,
  a PDF report, slides and demonstration with human ownership and required AI-assistance disclosure.

The accepted LightGBM selection remains fixed. Scenario analysis asks where and why it differs
from simpler methods, without restarting selection or requiring every stratum to favor LightGBM.
A matched cross-model inventory simulation is optional bonus work.

### 2.3. Assignment requirement traceability

| Course module | Implemented foundation | Remaining acceptance |
|---|---|---|
| Business understanding/data generation | Monetary Store-level problem, deterministic synthetic scenarios and dictionary | Disclose assumptions and conditional interpretation in final delivery |
| EDA | Descriptive findings, notebooks and bounded weekly STL implementation | Authorized real STL input/execution and reviewed findings |
| Data cleaning | Validation, checked joins, sparse dates/nulls/valid spikes preserved | Retain source limitations in final reporting |
| Feature engineering | Fixed 29-predictor point-in-time contract | Preserve schema and origin-time information |
| Model development | Three-model comparison, selection, frozen uncertainty and inventory development evidence | Real scenario comparison and authorized final evaluation |
| Deployment | Shared services, local API/five-screen dashboard, separate synthetic adapters | Two reachable approved public URLs after release gates |
| Monitoring | Validation/availability/KPI building blocks and selected descriptive replay design | Working report/dashboard, final results and approved human trigger policy |
| Report/presentation | Reviewed development evidence | PDF, slides, demonstration, reproducibility and ownership/AI disclosure |

Fixtures and design/implementation approval cannot substitute for empirical results or delivered artifacts.

## 5. Dataset and preparation

Use official Kaggle `train.csv` (Sales history), `test.csv` (future covariates without Sales or
Customers), `store.csv` (static metadata), and `sample_submission.csv`. Join metadata many-to-one
on Store, retaining sparse Store-Date keys, source values/nulls, valid spikes and open/zero Sales.
An absent date is not zero; correct/remove anomalies only with evidence of source error.
[Acquisition](DATA_ACQUISITION.md), [validation](DATA_VALIDATION.md) and the
[Data Dictionary](DATA_DICTIONARY.md) define the source and observed limitations.

Calendar/holidays derive from Date; promotion and opening schedules require supplied or explicitly
assumed origin-known plans. A static Store snapshot is not a history of information availability.
Competition opening uses month/year precision, without inventing a day. Future Customers and
Customers-derived features are prohibited. Source Open defines eligibility/routing, never a raw
predictor; uncertain Open-resolution candidates remain audit-only. Unknown Open stays unknown.

## 6. Synthetic operational extension

The [scenario specification](../plans/completed/phase-9-synthetic-inventory.md) and
[dictionary](DATA_DICTIONARY.md#d-synthetic-operational-variables) own exact schemas, ranges and draws.

| Input | Implemented synthetic assumption |
|---|---|
| Lead/review/protection | Store-specific integer L=2–7 calendar days; R=1; P=L+1=3–8 within H14 |
| Turnover anchor | Mean observed Open=1 Sales in the 56 calendar days through origin, ≥28 valid open rows; no gap fill/fallback, zero anchor valid |
| Stock/coverage | Anchor × (L+1+B), B∈{0,1,2,3}; base 3–11 open-day equivalents, thin-stock stress 1 |
| Pipeline/backorders | Zero only at cold start; order queue evolves during simulation |
| Nominal buffer | p=.95 reference, .90/.98 sensitivities; not achieved cycle service or fill |
| Costs | c∈[.55,.85), annual a∈[.10,.30), goodwill g∈[.10,.75); holding=c*a/365, shortfall=(1-c)+g once |
| Equivalent units | Display-only AverageUnitValue∈{5,10,20,50}, without SKU mapping |
| Discount/promotion | Zero without synthetic promotion; typical [.05,.30), specified stress .40; never a Rossmann predictor |

Use seed 4209, exact keyed SHA-256 draws, five paired replicates, eight synthetic families and a
historical reference at June 5/June 19 origins. The conceptual additive path combines base, trend,
weekly seasonality, promotion/holiday and noise; the implementation uses the exact ordered
multiplicative factors and coupled stresses in the specification. Weekly factors average one over
seven calendar days but 1.033333… over default Monday–Saturday open days; do not renormalize them.

Common draws, paths, starts and seeds pair policies. Validate ranges, dependencies, distributions,
availability, counts and deterministic arithmetic. Unavailable anchors keep stock/demand null,
including on closures. Designed replicates do not estimate scenario probabilities or statistical
power. Synthetic paths never replace historical labels or retrain forecasts/uncertainty.
Weather/perishability are optional unimplemented extensions. Public-demo fixtures have a separate
seed/content contract and are not this generator's analytical output.

## 9. Leakage prevention and EDA

No shuffled forecasting split. Every fit/history input stops at origin; development labels stop
at July 3 before reaching modeling/evaluation. Recursive lags use actuals through origin plus
earlier predictions from that run, never precomputed future-target historical rows. A projection,
receipt or hash grants no mixed-source access: preparation/custody approval precedes any read/hash.

EDA describes trends, seasonality, autocorrelation/decomposition, promotions and promotion×Store-type
associations, holidays, StoreType/Assortment, competition, Promo2, volume/variability and anomalies.
Report sparse subgroup support and avoid causal effects. Earlier full-source validation/EDA included
eventual holdout dates, as disclosed in [findings](EDA_FINDINGS.md). Recompute modeling/monitoring
cohorts from eligible origin/development history; never reuse full-source EDA volume tiers.
Supplementary robust weekly STL is retrospective, without smoothing/gap interpolation or use as
predictors; real execution/publication needs the [custodian procedure](CC-02D_CUSTODIAN_RUNBOOK.md).

## 11. Features

The [Feature Contract](FEATURE_CONTRACT.md) fixes 29 ordered predictors: categorical Store identity;
calendar fields; holidays/promotions/Promo2 schedule; StoreType/Assortment/competition; exact Sales
lags 1/7/14/28; complete 7/14/28-day means and sample standard deviations (`ddof=1`). Date is key-only.
Competition age is completed calendar-month offset bounded at zero; paired missing metadata stays
null. Promo2 nonparticipants are inactive; invalid/incomplete schedules stay null.

Fit-only category vocabularies belong in the model adapter, without changing artifact dtypes.
Target-day Sales, future Customers, Open/audit predictors, imputation and same-weekday statistics
are excluded. Scaling is used only where needed; extra features need separate approved scope.

## 12. Models and multi-step strategy

| Model | Accepted behavior |
|---|---|
| Seasonal Naive | Exact d−7 same-Store actuals at h1–7, earlier raw predictions at h8–14; missing exact history stays unavailable |
| Additive Holt-Winters | Univariate additive trend/weekly seasonality, latest contiguous daily segment ending at origin, ≥28 days including observed closed zeros, no fallback |
| Global LightGBM | CPU regression L1 on eligible Open=1 labels, fit-only categories/native numeric missingness, all observed pre-origin Sales in lag history, four finite original inner trials |

LightGBM predicts the next day, appends its finite nonnegative clipped raw value, rebuilds lags/
windows and repeats through H14. Complete the raw path before separate planned-Open routing;
unknown Open never changes raw feedback. Retain unclipped/clipping/failure/category diagnostics.
The mismatch between observed closed-day history and raw recursive values remains a limitation.
Closure-aware feedback, direct/horizon-feature/hybrid approaches, SARIMA and extra models require
separate origin-safe development designs, without motivation from protected outcomes.

Simple-first development selection chose LightGBM trial A at exactly 180 rounds. Preserve its
recipe, selection thresholds and unfavorable individual horizons in [decisions](DECISIONS.md)
and [results](PROGRESS.md); universal Store/horizon superiority is not required.

## 14. Validation strategy

| Origin | H14 target dates |
|---|---|
| 2015-05-22 | May 23–June 5 |
| 2015-06-05 | June 6–19 |
| 2015-06-19 | June 20–July 3 |

Use expanding origin-safe training and these three chronological windows. Their 42 late-season
days and shared Friday origins confound weekday/horizon and cannot establish year-round accuracy.
Supplementary origins need a precommitted common protocol, without opportunistic selection.

### 14.1. Final holdout

Protect July 4–31 from feature/preprocessing/model/calibration/policy/scenario/monitoring selection.
Earlier descriptive exposure prevents a pristine unseen-label claim. The sole
[final protocol](../plans/active/phase-13-sequential-final-evaluation.md) issues complete H14 blocks
at July 3 and July 17 before revealing matching outcomes date by date. Persist issuance, release
in order and checkpoint before advancing. The scheduled second fresh fit uses only already released
history through July 17 under the frozen recipe. No outcome-driven recipe, quantile, target,
policy or alarm adaptation is permitted. Source preparation, mechanical staging and analytical
release require distinct approvals. Final LightGBM has Seasonal Naive as contextual comparator,
without new selection or Holt-Winters final comparison. Exact June Fit B transport to July remains
explicitly UNVALIDATED, without a July/synthetic guarantee.

## 15. Metrics and Store-level scenarios

MAE is primary in turnover units; RMSE emphasizes large errors. MAPE alone excludes zero actuals,
without epsilon, reporting exclusions/coverage. WAPE is summed absolute error / summed actual Sales,
unavailable with reason for zero denominator. Pool rows/sufficient statistics, not window ratios.
Primary raw metrics use observed Open=1/Sales with available forecasts. Closed operational zeros
cannot inflate primary scores. Report standalone and paired coverage alongside window/pooled/horizon metrics.

Scenario comparisons use the same three frozen candidates, origins and sparse observed roster,
primary three-way common eligible/available rows, standalone/pairwise/common counts, missing reasons,
Store/date/origin support, exact denominators and unavailable results. Interpret errors and failures,
without causal/significance claims, fallback pooling or invented support. Preserve frozen daily/
cumulative meanings in separately approved segment interval assessment, without recalibration.

| Dimension | Foundation and pending scope |
|---|---|
| StoreType/Assortment | Known/missing/unrecognized categories; real metadata preparation/provider approval pending |
| Promotion | Retrospective keyed Promo; fixture bridge enables Promo only, without historic availability proof |
| Weekday/holidays | ISO weekday strata; combined weekday/weekend requires approved aggregation; no invented code meanings |
| Competition | Distance/opening bins require accepted definitions, source access and snapshot/month-precision assumptions |
| High/low volume | BLOCKED pending eligible origin-training/development-only definitions and inputs; no full-source EDA tiers |
| Origin/horizon | Three windows, individual h1–14 and h1–7/h8–14, including unfavorable/sparse horizons |

Freeze membership/strata/support/unavailability/interpretation before real analysis. Existing L2
emits MAE/RMSE/WAPE and directional errors; scenario MAPE needs separate approval or a clearly
labeled link to existing development diagnostics. Interactions, new origins and inference need
separate scope. Real preparation, verification/binding and analysis remain gated in the
[scenario plan](../plans/active/wp1-scenario-forecast-evaluation.md). Fixture consistency cannot
authenticate custody or contain peak decoder memory. Cross-model inventory simulation is optional.

# 16. Forecast Uncertainty

Forecast uncertainty will be estimated using **out-of-sample residuals** obtained from walk-forward validation.

For forecast horizon $h$:

$$
e_{t,h}
=
y_{t+h}-\hat y_{t+h}
$$

From the empirical residual distribution, the following quantiles will be obtained:

$$
q_{\alpha/2,h},
\qquad
q_{1-\alpha/2,h}
$$

The prediction interval will then be constructed as:

$$
PI_{t+h}
=
[
\hat y_{t+h}+q_{\alpha/2,h},
\hat y_{t+h}+q_{1-\alpha/2,h}
]
$$

The nominal daily interval level is:

$$
95\%\ prediction\ interval
$$

For this daily two-sided interval, $\alpha=0.05$ is the total non-coverage probability;
each tail has probability $\alpha/2=0.025$.

Empirical coverage will also be evaluated:

$$
Coverage=
\frac{\#\{y_t\in PI_t\}}
N
$$

This ensures that forecast uncertainty is not merely visualized on the dashboard but also quantitatively evaluated.
The accepted development assessment is below nominal coverage; its exact counts, sparse Sunday
support and unavailable Fit A horizons remain disclosed in [PROGRESS](PROGRESS.md). No fitted
tables or historical numerical results are changed by this proposal revision.

Completed Phase 8 assigned distinct chronological development residual roles in uncertainty contract:
Fit A calibrates validation_1 and assesses validation_2; Fit B calibrates validation_1+validation_2
and assesses validation_3. The reviewed canonical Fit B fitted values are frozen for their exact
artifact identities in [PROGRESS](PROGRESS.md). Coverage on the quantile-calibration sample is a
diagnostic, not independent reliability evidence. Report sample counts, interval width, and
coverage by horizon and supported segments; pooled empirical quantiles do not guarantee coverage
for every store. Apply $\max(0,endpoint)$ to both interval endpoints, retain their ordering, and
evaluate coverage and width using the intervals as actually emitted.
The selected-model/development reuse and correlated Store-day errors limit inferential claims;
final replay assesses the frozen interval recipe without recalibration from its outcomes.

Inventory protection requires a quantile of **cumulative residual paths**, not a sum of daily
upper bounds. For a supported protection period $P$, use complete out-of-sample Store-origin paths:

$$
E_P=\sum_{h=1}^{P}(y_{t+h}-\hat y^{op}_{t+h}),\qquad
U_P=\max(0,D_P+q_p(E_P))
$$

Here, $\hat y^{op}$ is the operational forecast under the declared known-opening schedule,
$D_P=\sum_{h=1}^{P}\hat y^{op}_{t+h}$, and $p$ is the one-sided cycle-service target
(for example, $p=0.95$), distinct from the daily interval's tail probability $\alpha$.
Preserve dependence within each residual path, report calibration counts and assumptions, and
define a reviewed low-sample policy. A daily two-sided 95% interval is not automatically a 95%
cumulative service bound. Do not assume independent daily errors or guaranteed service.

---

# 17. Inventory Decision Framework

Let the supplier lead time be:

$$
L
$$

The operational forecast value during lead time is:

$$
D_L=
\sum_{h=1}^{L}\hat y^{op}_{t+h}
$$

Let $U_L$ denote the cumulative sales-proxy bound at the chosen one-sided cycle-service target,
calibrated from lead-time residual paths as described in Section 16.

Then:

$$
\boxed{
SafetyStock_L=
\max(0,U_L-D_L)
}
$$

and:

$$
\boxed{
ReorderPoint=
D_L+SafetyStock_L
}
$$

or equivalently:

$$
ROP=\max(D_L,U_L)
$$

This reorder-point illustration describes a continuous-review threshold. It is distinct from the
initial simulator's daily-review order-up-to policy. With lead time $L=2,\ldots,7$ days and review
period $R=1$ day, use protection period $P=L+R\le14$, forecast value $D_P$, and cumulative bound
$U_P$. Define $SafetyStock_P=\max(0,U_P-D_P)$ and order-up-to target
$S_P=D_P+SafetyStock_P=\max(D_P,U_P)$. Completed Phase 10 fixed event timing and terminal
accounting in inventory simulation contract: an end-of-day order at t arrives before demand at t+L+1; receipts precede
consumption, unmet value is lost, costs use ending stock, and the final day suppresses new ordering.
Targets are frozen once at origin, the outstanding-order queue evolves, and due-after-window
orders remain separate terminal exposures without cancellation or salvage.

For Phase 13, the owner has approved the A-bounded inventory scope and its explicit
acceptance limitation under bounded inventory scope: inventory evaluation uses two independent origin-frozen H14
episodes at the same July 3 and July 17 origins as the primary forecast evaluation. Each episode
executes the accepted Phase 10 standing-target policies from targets frozen at its origin.
Subsequent daily reviews advance simulated inventory state against those same targets; they are not
new forecast-based recommendations or freshly calibrated protection-period decisions. This is the
accepted Phase 13 scope with no new rolling operational forecast origin or daily suffix
recalibration. It is the explicit exception to the earlier requirement for complete fresh protection-period
coverage at every daily review. Do not score or imply unsupported later-review protection coverage.
The two episodes do not demonstrate continuous rolling 28-day inventory operation. A-full rolling
inventory capability remains unapproved and would require a separate origin-safe forecasting and
uncertainty design. Preserve Phase 10 event and paired-policy mechanics and common finite-window
terminal accounting; the full precommitted scenario/sensitivity panel remains subject to its
resource-feasibility gate.

---

## 17.1. Inventory Position

Within the simulated retail-equivalent-value model:

$$
InventoryPosition
=
StockOnHandValue
+
OnOrderValue
-
BackordersValue
$$

The initial simulator uses lost sales, not backorders: `BackordersValue = 0`, unmet value is
recorded, and outstanding orders remain in a queue until their scheduled arrival. `OnOrderValue`
is the sum of that queue; it is not reset to zero because real Rossmann order data are unavailable.
Approximating position by stock on hand is valid only for a clearly labeled static example with
no outstanding orders, not for the evolving simulation.

---

## 17.2. Recommended Replenishment

$$
\boxed{
ReplenishmentValue
=
\max(0,S_P-InventoryPosition)
}
$$

The equivalent inventory quantity is:

$$
\boxed{
EquivalentUnits=
\left\lceil
\frac{ReplenishmentValue}
{AverageUnitValue}
\right\rceil
}
$$

This daily-review order-up-to heuristic produces a simulated value recommendation, not an actual
SKU order or an optimized procurement quantity. If any required operational forecast in the
protection period is unresolved, keep the recommendation unavailable rather than treating the
unknown opening status or demand as zero.

---

# 18. Business Evaluation

The forecasting model will not be evaluated solely using MAE or RMSE.

The team will conduct an **inventory simulation**.

The business KPIs include:

$$
StockoutRate
$$

$$
CycleServiceLevel
$$

$$
ValueFillRate
$$

$$
AverageInventoryValue
$$

$$
EstimatedHoldingCost
$$

$$
EstimatedLostSales
$$

The project will compare:

### Baseline Inventory Policy

For example, replenishment based on a historical moving average.

with:

### Forecast-Driven Policy

Forecast + uncertainty + safety stock + reorder rule.

Hold the historical Sales proxy unchanged across policies; do not modify it to manufacture an
inventory benefit or interpret it as unconstrained latent demand. All policies use common scenario
inputs, seeds, starting stocks, and arrival timing. Stress-scenario comparisons are reported
separately from the historical-proxy replay.

Define simulated KPIs before comparison:

- **Stockout rate:** days with unmet value / days with positive proxy demand; zero denominator is unavailable.
- **Completed positive-demand receipt-cycle service rate:** completed positive-demand cycles
  with no unmet value / completed positive-demand cycles bounded by two observed positive receipt
  dates. This is a project-specific simulated cycle-service proxy with policy-dependent
  denominators; report zero-demand and initial/terminal censored intervals, and keep the nominal
  scenario target distinct.
- **Value fill rate:** $1-\sum UnmetValue/\sum DemandValue$; report denominator and handle zero explicitly.
- **Average inventory and holding cost:** use the fixed daily measurement point and `HoldingCostRate` per inventory-value unit per day.
- **Estimated lost sales:** unmet retail-equivalent value, not observed Rossmann lost revenue; the penalty multiplier converts it to a simulated cost proxy.

The primary business question is:

> Under the stated scenarios, how do forecast-based policies change simulated service and cost trade-offs?

---

# 19. Inventory Sensitivity Analysis

Because the supply-chain variables are synthetic, the business conclusions must be tested under multiple scenarios.

| Scenario | Cycle-service target | Lead Time |
|---|---:|---:|
| Low protection | 90% | 2–3 days |
| Base | 95% | 4–5 days |
| High protection | 98% | 6–7 days |

This compact table illustrates the planning intuition; it does not redefine the accepted scenario
panel. Implemented Phase 10 uses all Phase 9 families at p=0.95 plus nine one-factor-at-a-time
synthetic-base overlays for lead time, service parameter, annual holding rate, goodwill penalty
and initial coverage. Keep those accepted cases and common policy inputs unchanged; report actual
unfavorable development results through [PROGRESS](PROGRESS.md).

The hypothesized trade-off is:

$$
ServiceLevelTarget\uparrow
\Rightarrow
SafetyStock\uparrow
\Rightarrow
HoldingCost\uparrow
$$

while:

$$
StockoutRisk\downarrow
$$

The system demonstrates conditional service/cost trade-offs. A service-level target is not a
guarantee of achieved service, and retaining the baseline is an acceptable result if another
policy does not improve the trade-off.

---

## 20. Technology and application architecture

Use Python, pandas/NumPy, CSV/Parquet/PyArrow, matplotlib, statsmodels, LightGBM, shared Python
services, FastAPI and Streamlit, with `pyproject.toml` and generated `uv.lock`.
Plotly/scikit-learn, SHAP, Evidently, Spark/PySpark and Docker remain optional only for a supported
approved need. Distributed processing is unnecessary on the critical path.

```text
Immutable source → validation/preparation → EDA + point-in-time features
 → Seasonal Naive / Holt-Winters / LightGBM → comparison/selection → uncertainty
Synthetic operating scenarios + frozen forecasts → inventory-value engine
Verified evidence → Python services → Streamlit + thin FastAPI
Frozen final replay → monitoring → final report/presentation
Separate controlled synthetic bundle → explicit provider → synthetic API + direct-service dashboard
```

The five completed screens are Overview & Evidence, Historical Sales, Forecast Explorer, Model
Comparison and Inventory Comparison. They select bounded saved Store/origin/Fit/case evidence,
without request-time training, inference, simulation or unrestricted scenario editing. Potential
stock/lead-time/service/unit-value editing, feature explanations/SHAP and business-alert controls
are design concepts, without an implementation claim. Daily intervals, cumulative bounds, ROP,
position, replenishment and equivalent units must retain their distinct semantics/availability.

Final delivery requires two public read-only URLs, using precomputed outputs if appropriate.
Current runtime stays localhost; no public deployment or live URL exists. The separate synthetic
profile labels authored fixture arithmetic on every view and never falls back to canonical inputs.
Health, bundle readiness and analytical-view availability remain separate facts. The
[release plan](../plans/active/public-course-demo.md) requires corrective review/closeout,
exact-content/rights/provenance and independent security review, a trusted manifest pin, resource/
rollback assessment, specific hosting/audience/window owner approval and external release/shutdown checks.

# 23. Model Monitoring

The final monitoring report or dashboard must distinguish four dimensions. Existing validation,
forecast-availability and simulated-KPI components provide building blocks; they do not constitute
a completed monitoring report. Phase 13's selected monitoring design in selected final-evaluation method is narrower than
the broader instructor-feedback proposals in broader instructor-feedback proposal. Its monitoring implementation and final
replay evidence remain pending.

## 23.1. Data Quality Monitoring

Record schema/type consistency, duplicate Store-Date and issuance keys, missing/invalid values,
missing calendar dates, coverage changes, and missing or inconsistent operational inputs. Preserve
absent dates, nulls and observed zeros as different states. Distinguish expected source sparsity
from a failed declared input contract. Report forecast availability and unresolved planned Open,
schedule provenance or protection-period inputs with counts, reasons and affected Store/origin/
horizon. Unavailable operational values remain unavailable rather than zero.

Existing validators and integrity/availability checks support these diagnostics. selected final-evaluation method selects
precommitted deterministic integrity/data-quality alerts for the future replay; the exact rule
catalog and output still require the relevant implementation/review gates.

## 23.2. Data Characteristics and Drift Monitoring

Describe selected supported distributions: Promo frequency, calendar/holiday categories, StoreType
and Assortment mix, and missingness and quantiles of origin-safe lagged/rolling Sales histories.
Compare with a versioned eligible development reference, retaining segment sizes and static-snapshot
availability assumptions. Sales-history summaries use only observations already available through
the relevant origin; they do not create new target-derived cohorts or feed revealed within-block
actuals back into a previously issued forecast.

Descriptive frequency/quantile shifts fit selected final-evaluation method. Numeric distribution-shift alerts, new tests,
competition/volume cohorts or learned drift methods require a separate approved methodology.
A changed mix can reflect eligibility or missing data rather than a changing business process.

## 23.3. Forecast Performance Monitoring

Join immutable issued forecasts to actual observations **only after the corresponding authorized
reveal**. Report MAE, cautious MAPE, WAPE, forecast availability and empirical daily interval
coverage, with RMSE as supporting evidence. Preserve observed Open=1 eligibility, the accepted
MAPE zero exclusions, WAPE denominator, missing-prediction accounting and separate raw/operational
views. Distinguish forecast availability from interval coverage; neither missing actuals nor
unavailable intervals count as successful predictions.

The descriptive time-indexed summaries include:

$$
MAE_t
$$

$$
WAPE_t
$$

$$
IntervalCoverage_t
$$

Descriptive delayed errors/coverage are selected under the selected final-evaluation method. A future bias summary can use a
predeclared signed-error definition (for example forecast minus actual, with positive values
meaning overforecast), accompanied by under/overforecast counts and eligible denominators. Its
monitoring definition, numerical performance alarms and retraining-review decisions remain
extensions requiring approval; existing WP1 directional-error outputs are not a monitoring service.
Daily marginal intervals and cumulative inventory-protection bounds retain their distinct
populations and meanings; neither establishes realized cycle-service probability.

## 23.4. Simulated Business Monitoring

Summarize the supported positive-demand stockout-rate proxy, value fill rate, completed
positive-demand receipt-cycle service-rate proxy, ending-stock inventory, replenishment activity,
holding-cost and shortfall-cost proxies. Retain Phase 10 event timing, ratio numerators/denominators,
unavailable states and terminal exposures. Label each Phase 13 episode, reset, partial window and
censored cycle; do not pool episode boundaries into invented continuous operations.

These indicators are conditional monetary simulations, not observed Rossmann stockouts, service
or savings. Approved KPI definitions and development simulation exist; final replay summaries
remain pending. Numeric business-service alerts are not selected by the selected final-evaluation method and need separate
approval. Synthetic demonstration fixture ratios are interface evidence, not replay measurements.

---

# 24. Pseudo-Production Monitoring

Because the Rossmann dataset is historical and the team does not have access to a live Rossmann sales feed, the project will **not assume access to real production data**.

Instead, the final holdout period will be revealed sequentially:

$$
Day_1
\rightarrow
Day_2
\rightarrow
...
\rightarrow
Day_n
$$

At each scheduled origin, issue the complete raw and operational forecast paths. On each day
within its block:

1. retrieve the stored forecast for that target, issued before its actual value was available;
2. the actual observation is subsequently revealed;
3. the rolling forecasting error is updated;
4. feature distributions are compared with the training reference;
5. prediction-interval coverage is updated;
6. simulated inventory KPIs are updated;
7. precommitted deterministic integrity/data-quality conditions generate alerts.

Use the two fixed 14-day origins and daily reveal protocol from Section 14.1. Forecasts at the
start of a block cannot use observations later revealed within that block; once a target becomes
observable, monitoring joins its actual value to the stored forecast with matching origin/horizon.
No adaptive tuning, interval recalibration, inventory-policy adjustment, or triggered retraining
occurs during this frozen final replay. The selected second scheduled fresh fit uses only history
already authorized and revealed through its origin. A later adaptive retraining demonstration would require
a separate synthetic or development replay and must not be reported as the same frozen test.

The forecast and inventory scopes are distinct. Primary forecast evaluation retains exactly the
two non-overlapping H14 issue-before-reveal blocks. The approved A-bounded inventory scope in
bounded inventory scope runs two independent origin-frozen H14 episodes on those same origins; daily KPI updates
follow the sequential reveal while each policy continues to use its original frozen target. Those
daily state transitions are not new calibrated rolling forecast decisions, and unsupported
later-review protection coverage is not scored. No new rolling operational forecast origin or
daily suffix recalibration is introduced. The inventory scope does not imply continuous
rolling 28-day validation. bounded inventory scope approves inventory scope only. selected final-evaluation method records the selected
forecast-input/availability assumptions, synthetic planned-Open schedule, Fit B transport, A2
custody, runtime/reproducibility, monitoring, and score/comparator methods. Source identity,
provenance, safe preparation, operator/partition provenance, resource approval, and separate
implementation, rehearsal, staging, and analytical-release gates remain pending.

The selected Phase 13 methods are recorded in selected final-evaluation method. Source identity, covariate provenance,
historical availability assumptions, safe acquisition and authorized preparation remain preflight
requirements. Scope and method selection do not authorize a source read, extraction, protected-data
staging, or analytical release. If required covariates exist only in a combined source containing
protected Sales/Open, a separately reviewed safe-preparation/custody procedure is required before
any access to that source; column projection alone does not establish physical isolation.

---

## 24.1. Monitoring Alert Rules

**Selected Phase 13 method (selected final-evaluation method):** report descriptive daily, trailing 7-calendar-day, and
trailing 14-calendar-day summaries, stratified by forecast origin and horizon. Show descriptive
feature-distribution shifts and post-release forecast errors and interval coverage with their
populations and denominators. Precommit deterministic integrity and data-quality alerts only.
Statistical drift, forecast-performance, interval-coverage, and service-level alarm thresholds are
not selected. Alert definitions must be independent of final outcomes. uncertainty calibration sample
floors do not establish monitoring reliability, and this short replay does not support claims of
statistically reliable drift or service detection. Simple summaries remain sufficient; Evidently is
optional only for a demonstrated unmet need.

Reports must label startup/partial windows, missing evidence, the forecast origin/horizon and
eligible denominators. Phase 13 M1–M3 integration does not implement the later monitoring
milestone. Two H14 blocks over 28 days provide a bounded demonstration, not statistically reliable
evidence of persistent production drift or a validated production alert policy.

## 24.2. Proposed Operational Alerts and Human Retraining Review

**PROPOSED / NOT APPROVED OR IMPLEMENTED.** The following concrete candidate policy addresses
the final delivery requirement to define retraining conditions. It is a reviewable extension to
be designed and approved under a new or superseding decision before implementation in a separate
development-only or synthetic monitoring demonstration. It does not change selected final-evaluation method, operate during
the frozen Phase 13 replay, authorize automatic retraining, or accept broader instructor-feedback proposal wholesale.

All numeric values below are **proposed operational policy parameters**, chosen to demonstrate
minimum-support and persistence rules; none is empirically validated or calibrated here.
An approved development-only rehearsal must justify or revise them and freeze the reference,
parameters and metric/segment rules before use. The final holdout must never calibrate them.

| Policy element | Proposed testable rule and evidence requirement |
|---|---|
| Reference and windows | Version a development-only reference from approved chronological forecasts earlier than the assessment windows, using identical eligibility, metric definitions and comparable origin/horizon/segment populations. Exclude assessed rows from the reference. Assess completed, consecutive **non-overlapping 14-calendar-day windows**; show daily and trailing 7/14-day descriptive views separately. Freeze reference values and boundaries before assessment. |
| Minimum evidence | For a performance or feature-shift decision require at least **10 distinct observed target dates, 100 distinct stores and 1,000 eligible paired rows** in each assessed window and its reference. Use the fixed common-row comparison population; disclose total eligible rows and availability separately. For availability checks apply the same date/store/row floors to the eligible observed-label roster **before** filtering missing forecasts, so an outage cannot hide itself. WAPE comparisons additionally require a positive reference WAPE and actual-value denominator. Unsupported/sparse subgroups, zero denominators or partial windows are **UNAVAILABLE EVIDENCE**, never a passing result. These monitoring floors are distinct from uncertainty contract's calibration floors. |
| Performance warning | If supported window WAPE exceeds **1.20 times** its comparable development reference, issue **WARNING** with MAE/MAPE, error direction and segment/coverage context. One window does not trigger retraining. Reference mismatches or missing labels are unavailable evidence. |
| Availability warning | Warn if raw forecast availability falls below **99%** of eligible observed open-label targets in a complete window. This is a proposed monitoring parameter, not a measured service guarantee; it does not change model-selection coverage rules. Count missing predictions instead of excluding them from availability. |
| Characteristic warning | For a preapproved feature, warn on an absolute category-frequency change of at least **10 percentage points**, or a numeric median shift greater than **0.5 reference interquartile ranges**, with comparable populations and explicit missingness. Zero reference spread, changed category semantics or insufficient support give unavailable evidence for that check. These are descriptive effect-size rules, not significance tests or a new learned drift model. |
| Normal state | A supported check within its approved bounds is **NORMAL** for that window; unavailable evidence is never converted to normal. This status is not proof of production stability. |
| Data-quality failure | A schema/type failure, duplicate required key, non-finite/invalid required value, unauthorized date/field, inconsistent identity/hash or unresolved mandatory issuance input marks the dependent view unavailable and requires integrity/data-owner review immediately. Expected sparse dates/nulls are reported under their contract rather than repaired or automatically called failures. |
| Persistence and escalation | The same supported performance/availability/characteristic warning in **two consecutive completed non-overlapping windows** becomes **REVIEW REQUIRED**. A repeated blocking data-quality failure on **two consecutive daily checks** requires owner review; integrity/access violations stop the affected path immediately. Unavailable-evidence windows break the persistence sequence and must be investigated rather than silently skipped. |
| Human decision | Record trigger, dates, counts, reference/version, affected inputs and reviewer disposition: repair inputs, continue monitoring, or authorize a separate retraining experiment. Verify label availability, source quality, feature comparability and reproducibility first. Compare any retrained candidate chronologically on eligible development evidence before a separately approved promotion; no automatic model replacement or frozen-test adaptation. |

Monitoring acceptance requires fixture cases for normal, warning, unavailable-evidence and
review-required states; persistent versus isolated warnings; invalid/zero denominators; missing
predictions; and delayed-label joins. Record alert decisions and human dispositions in a report or
dashboard with reproducible configuration. This is future acceptance work, not a claim that those
checks or a monitoring artifact were produced by the documentation task. A 28-day final replay
must not be repurposed to validate persistence thresholds or establish long-run drift reliability.

---

## 25. Success criteria, limitations and sequencing

Success means supported comparison, honest uncertainty assessment, conditional inventory trade-offs
and working reviewed course artifacts. LightGBM need not win every scenario; unfavorable or
inconclusive business results are valid. Preserve the selected recipe and all adverse findings.

Shared stores/date shocks, sparse Sunday evidence, late-season windows and weekday/horizon
confounding limit generalization. Historical turnover cannot recover SKU demand, actual stockouts
or procurement stock. Artificial costs, cold starts, stale targets, finite-window censoring and
unvalidated uncertainty transport limit business claims. No optimality, production readiness,
real savings or guaranteed service is established. Local applications/fixtures do not complete
real scenario, final-replay, monitoring or public delivery requirements.

The original eight-week estimate sequenced scope/data (1), preparation/EDA (2), features/baseline
(3), statistical backtests (4), LightGBM/selection (5), uncertainty/scenarios/inventory (6),
applications/monitoring design (7), and authorized final replay/report/slides/demo (8). It is not a
current schedule or completion claim. The [roadmap](PROJECT_PLAN.md) owns remaining dependencies,
including reviews, safe inputs, resources and distinct rehearsal/staging/release approvals.

# 30. Final Deliverables

The required final delivery includes the following artifacts. Status describes recorded evidence,
not an inference that all course requirements have been accepted.

| Deliverable | Existing verified capability | Remaining delivery or approval gap |
|---|---|---|
| Source code on GitHub and reproducibility instructions | Repository contains reusable analytics, scripts, tests, notebooks, locked environment and CI; Phases 0–12 complete | Final handoff must incorporate reviewed remaining work, human ownership review and AI-assistance disclosure |
| Complete Data Dictionary | [Dictionary](DATA_DICTIONARY.md) covers real fields, engineered predictors and synthetic inputs/output semantics | Check final emitted monitoring/release fields against their eventual approved contracts; do not claim fixture values are observations |
| Processing/EDA/modelling notebooks and scripts | Implemented reusable pipeline, thin notebooks and development forecasting runners | Supplementary authorized STL findings and real-data scenario evidence pending |
| Documented synthetic operational extension | Completed Phase 9 deterministic generator; documented assumptions/ranges/dependencies/seed/provenance | Keep synthetic stresses separate from actual Sales and synthetic public fixtures; no real operational-data claim |
| Forecasting model and uncertainty evidence | Selected LightGBM trial A/180-round recipe and reviewed frozen Fit B; three-model development comparison | Sole frozen final replay remains unrun; no final performance/coverage guarantee |
| Inventory decision-support engine | Completed Phase 10 origin-frozen monetary policy simulator and sensitivity analysis, including adverse findings | Authorized two-episode Phase 13 evidence pending; no continuous procurement or measured savings claim |
| Public read-only FastAPI URL | Local API and separate controlled-synthetic adapter implemented | **PUBLIC DEPLOYMENT PENDING**: Milestone B closeout, C review and specific release authorization; no live URL to list |
| Public Streamlit dashboard URL | Completed localhost dashboard and integrated separate synthetic dashboard | **PUBLIC DEPLOYMENT PENDING** under the same gated two-URL release; direct Python services remain supported |
| Monitoring report or dashboard | Validation/availability and simulated-KPI building blocks; selected descriptive final-replay design | Replay monitoring/results pending; broader four-dimension delivery and human trigger policy need approved implementation and evidence |
| PDF report | Proposal, contracts and development evidence available as inputs | Phase 14 final PDF not delivered |
| Presentation slides | Scientific scope and evidence sources documented | Phase 14 slides not delivered |
| Demonstration | Local API/UI implementation and controlled-synthetic interface examples exist | Authorized public demonstration and final live or recorded presentation remain pending |

The team remains accountable for understanding, reviewing and owning the source and analytical
claims, and for disclosing AI assistance as required by course policy. AI-generated code or an
independent AI review is not evidence of exclusively human authorship or academic compliance.
The project uses explicit code and reproducible analytics rather than a no-code/AutoML workflow.
