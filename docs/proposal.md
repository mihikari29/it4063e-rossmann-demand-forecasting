# PROJECT PROPOSAL

## Retail Demand Forecasting for Inventory Optimization (FMCG)

### A Store-Level Business Analytics and Inventory Decision Support System Using Rossmann Store Sales Data

### Course Information

**Course:** IT4063E – Introduction to Business Analytics  
**Semester:** 20261  
**Class ID:** 175884  
**Instructor:** Dr. Bui Quoc Trung

**Team Members**

- Pham Le Minh Quang – 20235554
- Tran Quoc Tuan – 20235569
- Vo Ta Quang Nhat – 20225454
- Nguyen Trung Hieu – 202416689
- Nguyen Gia Minh – 202400111

---

# 1. Project Background and Business Problem

In the retail and FMCG sectors, inventory management is one of the most important operational decisions. If demand is underestimated, businesses may experience **stockouts**, resulting in lost sales and lower customer service levels. Conversely, if demand is overestimated, businesses may incur excessive inventory holding costs, tied-up capital, and risks of markdowns or product spoilage.

The project requires the team to act as the **demand-planning analytics function** of a retail/FMCG business and answer the following question:

> How much store-level sales turnover is expected over the next 14 days, and how do forecast-based inventory-value policies compare under explicit simulated operating assumptions?

The project must cover the complete analytics lifecycle, from data analysis and forecasting to deployment, monitoring, and business recommendations.

The Rossmann dataset does not provide SKU-level sales or physical quantities sold for individual products. Instead, it provides **daily sales turnover at the store level**. Therefore, the project defines the demand signal as:

$$
\boxed{
\text{Observed Daily Sales Turnover}
\approx
\text{Store-Level Demand Signal}
}
$$

The project will forecast demand at the **Store × Date** level and then combine the forecasts with a simulated supply-chain and inventory layer to support replenishment decisions.

Here, “demand” is shorthand for an observed sales-turnover proxy. Sales can change because of
prices, product mix, promotions, or unmet demand; the data do not identify latent physical demand,
actual stockouts, or the inventory policy that generated the observations. Business results are
therefore conditional simulation results, not measured Rossmann inventory savings.

This approach ensures that the core forecasting component remains grounded in real data, while synthetic data are used only for operational information that is unavailable in the original dataset.

---

# 2. Project Objectives

## 2.1. General Objective

To develop an end-to-end Business Analytics system capable of:

> **Forecasting each Rossmann store's daily monetary Sales for the next 14 days and demonstrating inventory-value decisions under documented synthetic scenarios.**

## 2.2. Specific Objectives

1. Explore trends, weekly seasonality, holiday effects, promotion effects, store characteristics, competition, and other patterns associated with sales.
2. Develop and compare forecasting approaches ranging from baseline and statistical forecasting models to machine-learning models.
3. Forecast `Sales` for each store over a primary **14-day forecast horizon**.
4. Quantify forecast uncertainty through prediction intervals.
5. Transform forecasts into inventory-related indicators such as lead-time demand, safety stock, reorder point, and replenishment recommendations.
6. Compare simulated stockout, service, and holding-cost indicators under common operating scenarios.
7. Deliver reusable application services, a thin local/demo API, and one deployed dashboard.
8. Demonstrate monitoring of historical data, forecast errors, and simulated business indicators.

These objectives are aligned with the project requirements concerning forecast horizon, stockouts, holding costs, service-level targets, deployment, and monitoring.

---

# 3. Scope of the Project

## 3.1. Unit of Analysis

The primary unit of analysis is:

$$
\boxed{\text{Store} \times \text{Date}}
$$

The project **does not perform SKU-level forecasting**, because the dataset does not contain product IDs or physical quantities sold.

---

## 3.2. Target Variable

The target variable is:

$$
\boxed{Sales_{s,t}}
$$

where:

- $s$: store;
- $t$: date;
- `Sales`: the store's sales turnover on that date.

---

## 3.3. Coverage

The team plans to use all **1,115 stores** available in the Rossmann dataset rather than selecting only a small subset.

The dataset contains more than one million observations, but its scale remains manageable on personal computers using tools such as pandas and LightGBM.

---

## 3.4. Forecast Horizon

The primary forecast horizon is:

$$
\boxed{H=14\text{ days}}
$$

At forecast origin $t$, the system will predict:

$$
\hat y_{t+1},\hat y_{t+2},...,\hat y_{t+14}
$$

The dashboard may show the first seven days of a supported 14-day forecast. A 28-day forecast is
an optional extension requiring a reviewed design and validation; a 28-day holdout does not imply
that a model supports 28 forecast steps. The **14-day horizon is the standard for comparison**.

---

# 4. Main Analytics Questions

**AQ1.** How do daily sales vary according to weekday, month, holidays, promotions, and store characteristics?

**AQ2.** Which factors are most strongly associated with variations in daily sales?

**AQ3.** How do baseline, statistical forecasting, and machine-learning forecasting methods differ in terms of predictive performance?

**AQ4.** Which forecasting model provides the most accurate and stable performance for 14-day forecasting?

**AQ5.** How does forecast uncertainty change across forecast horizons and store types?

**AQ6.** Under simulated inventory, lead-time, and service assumptions, what inventory-value recommendation does the chosen policy produce?

**AQ7.** Under which simulated scenarios does a forecast-driven policy improve or worsen service and cost indicators relative to a baseline policy?

Therefore, the project covers all three levels of Business Analytics:

$$
\boxed{
Descriptive
\rightarrow
Predictive
\rightarrow
Prescriptive\ Analytics
}
$$

---

# 5. Data Sources

## 5.1. Real Data

The required real-world dataset is:

**Rossmann Store Sales – Kaggle**

The main data files are:

| Dataset | Description |
|---|---|
| `train.csv` | Historical store-day observations including `Sales` |
| `test.csv` | Future observations without `Sales` |
| `store.csv` | Store-level attributes |
| `sample_submission.csv` | Competition submission structure |

Important variables include:

`Store`, `Date`, `Sales`, `Customers`, `Open`, `Promo`, `StateHoliday`, `SchoolHoliday`, `StoreType`, `Assortment`, `CompetitionDistance`, `Promo2`, `Promo2SinceWeek`, `Promo2SinceYear`, and `PromoInterval`.

The main tables will be joined using:

$$
train.Store=store.Store
$$

The project requires Rossmann Store Sales as the primary dataset and combines it with synthetic supply-chain context.

---

# 6. Synthetic Data Design

Synthetic data will not replace the real sales data. Instead, they will supplement the Rossmann dataset with supply-chain and inventory variables that are not available in the original data.

All synthetic variables must have clearly documented **generation logic, business assumptions, and data dictionary definitions**.

## 6.1. Proposed Synthetic Variables

| Variable | Unit | Purpose | Generation Logic |
|---|---|---|---|
| `SupplierLeadTime` | days | Replenishment lead time | Store-specific; for example, approximately 2–7 days |
| `StockOnHandValue` | retail-equivalent value | Simulated inventory | Origin-safe recent Sales and coverage; common starting state across policies |
| `ServiceLevelTarget` | probability | Target cycle service, not value fill rate | Base 0.95; scenario range 0.90–0.98 |
| `HoldingCostRate` | cost per inventory-value unit per day | Simulated holding-cost proxy | Daily rate fixed by scenario |
| `StockoutPenalty` | cost per unmet sales-value unit | Simulated shortfall-cost proxy | Non-negative multiplier fixed by scenario |
| `AverageUnitValue` | retail-equivalent value/equivalent unit | Simulated conversion | Positive store-level assumption |
| `DiscountDepth` | proportion | Synthetic stress-scenario promotion intensity | 0 when `Promo=0`; positive when `Promo=1`; not a Rossmann predictor |
| `InventoryCoverageDays` | days | Initial inventory policy | Generated within a reasonable business range |

All synthetic data-generation procedures will use a **fixed random seed** to ensure reproducibility.

---

## 6.2. Synthetic Data Generation Principles

Synthetic variables will not be generated independently or purely at random.

For example:

$$
Promo_t=0
\Rightarrow
DiscountDepth_t=0
$$

and:

$$
StockOnHandValue
\propto
RollingAverageSales \times CoverageDays
$$

Stores with higher historical demand are therefore expected to carry higher inventory values.

Initial stocks and any demand-dependent parameters use only history available at the simulation
origin. Compare policies with the same demand path, scenario inputs, seeds, and starting stocks.
Synthetic discount assumptions do not alter the historical Rossmann Sales replay or enter its
forecast feature schema.

---

## 6.3. Synthetic Scenario Generator

To satisfy the requirement of generating data that incorporate **trend, seasonality, promotion, and supply-chain context**, the team will develop a **synthetic demand scenario generator**.

The generator will not replace the Rossmann dataset. Instead, it will be used for:

- pipeline testing;
- stress testing;
- monitoring simulation;
- testing model behavior under promotional spikes;
- testing stockout scenarios.

A synthetic demand series may be represented as:

$$
Demand_t
=
Base_t
+
Seasonality_t
+
PromoEffect_t
+
HolidayEffect_t
+
Noise_t
$$

and subsequently combined with:

$$
LeadTime,\ StockOnHand,\ DiscountDepth
$$

These are designed stress scenarios, not evidence that their distributions reproduce Rossmann
operations. The real forecasting benchmark remains separate from the synthetic scenario branch.

---

## 6.4. Synthetic Data Validation

Synthetic data will be validated at three levels.

### Range Validity

$$
SupplierLeadTime>0
$$

$$
StockOnHandValue\ge0
$$

$$
0\le DiscountDepth<1
$$

### Relationship Validity

For example:

$$
Promo=0 \Rightarrow DiscountDepth=0
$$

Stores with higher historical demand should, on average, have higher expected inventory levels.

### Distribution Validity

The team will inspect:

- mean;
- median;
- variance;
- quantiles;
- histograms;
- extreme values.

Each synthetic variable will be documented in the Data Dictionary using:

**Name – Type – Unit – Valid Range – Generation Rule – Dependency – Business Assumption – Random Seed**

---

# 7. Modelling Assumptions and Unit Consistency

Rossmann `Sales` represents monetary turnover rather than physical units sold.

Forecasts use observed sales-turnover units. The inventory simulation uses **retail-equivalent
value on the same scale**, including stock on hand, outstanding orders, inventory position,
reorder targets, and replenishment. This is a valuation assumption, not procurement-cost inventory;
any acquisition-cost conversion would need a separate documented synthetic margin assumption.

$$
\hat y_{s,t}
=
\text{forecasted sales value}
$$

$$
D_L
=
\text{expected sales value during lead time}
$$

$$
StockOnHandValue
=
\text{simulated inventory in retail-equivalent value}
$$

$$
ReplenishmentValue
=
\text{simulated retail-equivalent replenishment value}
$$

If a quantity-based illustration is required:

$$
EquivalentUnits=
\left\lceil
\frac{ReplenishmentValue}
{AverageUnitValue}
\right\rceil
$$

`EquivalentUnits` is only a **simulation output** and must not be interpreted as the actual number of SKUs to order.

Therefore, the project is positioned as a:

> **Store-level inventory-value decision-support system rather than a production SKU replenishment system.**

---

# 8. Data Preparation

The Data Preparation stage will include the following steps.

### Data Validation

The team will check for:

- duplicated `(Store, Date)` records;
- invalid dates;
- missing dates;
- incorrect data types;
- inconsistent categorical variables;
- impossible or invalid values.

### Missing Values

Particular attention will be paid to:

`CompetitionDistance`  
`CompetitionOpenSinceMonth`  
`CompetitionOpenSinceYear`  
`Promo2SinceWeek`  
`Promo2SinceYear`

The team will distinguish among:

- structural missing values;
- unavailable information;
- true missing values or data errors.

Source missingness remains visible. Any later model-specific encoding, indicators, or imputation
must be documented and learned from eligible training data only; the frozen Phase 3 contract
introduces no imputation or missingness predictors.

### Closed Stores

When:

$$
Open=0
$$

the operational forecast will be set to:

$$
\hat y=0
$$

according to the business rule.

This operational zero requires an opening schedule supplied or assumed known at the forecast
origin. Observed target Open establishes evaluation eligibility, not proof that the future schedule
was historically available. Missing Open remains unknown; an uncertain historical-context candidate
does not establish a closure or overwrite source truth. Raw model forecasts stay separate from
post-forecast operational routing.

### Outliers

High-sales observations will not automatically be removed because they may reflect legitimate events such as:

- promotions;
- holidays;
- genuine demand spikes.

Outliers will only be removed or corrected when there is clear evidence that they represent data errors.

### Chronological Integrity

Random shuffling will not be used in the time-series forecasting workflow.

---

# 9. Prevention of Data Leakage

The key principle is:

> Every feature must already exist or be knowable at the forecast origin.

### Future-Known Information

The following variables may be used:

- calendar information;
- weekday;
- month;
- holidays;
- planned promotions;
- store characteristics;
- competition information;
- historical sales.

The supplied store metadata is a single static snapshot, not a history of information releases.
Using it at earlier origins is an explicit backtest assumption; competition dates and promotion
start schedules are applied at their documented precision, without claiming proven historic
availability. Planned promotion, holiday, and opening schedules must be supplied for operational
use. Unknown future values are not inferred from target Sales or Customers.

### Future-Unknown Information

Future actual values will not be used.

In particular:

`Customers_t`

will not be used directly to predict `Sales_t` in production forecasting because the number of customers on a future date is unknown at the time the forecast is generated.

### Lag and Rolling Features

All lag and rolling features will be constructed only from:

$$
y_{\tau},\quad \tau\le t
$$

at forecast origin $t$.

Later recursive steps may also use their own earlier predictions, never actual Sales after the
origin. Full historical feature rows are suitable for historical training but must be rebuilt at
each recursive forecast origin.

---

# 10. Exploratory Data Analysis

EDA will focus on both descriptive analytics and business insights.

The main analyses will include:

- overall sales trends;
- daily and weekly seasonality;
- monthly and yearly patterns;
- autocorrelation;
- sales decomposition;
- promotion vs. non-promotion periods;
- holiday effects;
- StoreType comparisons;
- Assortment comparisons;
- CompetitionDistance;
- Promo2 participation;
- store-level variability;
- high-volume vs. low-volume stores;
- promotion × store-type interactions;
- unusual spikes and drops.

Seasonal decomposition may be represented as:

$$
Sales_t
=
Trend_t+Seasonal_t+Residual_t
$$

or in multiplicative form when appropriate.

The earlier source-validation and Phase 2 EDA work inspected full historical data, including the
dates later designated as final holdout. That descriptive exposure is retained and disclosed in
[EDA findings](EDA_FINDINGS.md); it is not an independent forecast test. Subsequent modeling must
use development-only, origin-safe analysis and must not reuse full-history EDA volume tiers or
representative-store rankings as learned model-selection inputs.

---

# 11. Feature Engineering

## 11.1. Calendar Features

`day_of_week`  
`week_of_year`  
`month`  
`quarter`  
`year`  
`is_weekend`  
`is_month_start`  
`is_month_end`

## 11.2. Holiday and Promotion Features

`StateHoliday`  
`SchoolHoliday`  
`Promo`  
`Promo2`  
`IsPromo2Active`

## 11.3. Store Features

`StoreType`  
`Assortment`  
`CompetitionDistance`

## 11.4. Competition Features

$$
CompetitionAgeMonths=
\max(0,MonthIndex(Date)-MonthIndex(CompetitionOpeningYearMonth))
$$

Use supplied month/year precision, not an invented opening day; paired missing opening metadata
remains null. The implemented semantics are specified in the Feature Contract.

## 11.5. Lag Features

$$
Sales_{t-1},
Sales_{t-7},
Sales_{t-14},
Sales_{t-28}
$$

## 11.6. Rolling Features

$$
MA_7,\ MA_{14},\ MA_{28}
$$

$$
STD_7,\ STD_{14},\ STD_{28}
$$

Same-weekday rolling statistics are a deferred extension, not part of the frozen 29 predictors.

Categorical features will be encoded appropriately. Numerical scaling will only be applied to models that require it and will not be considered mandatory for tree-based models.

---

# 12. Forecasting Models

The project will follow a **model ladder** rather than training many models solely to increase model count.

## Model 0 – Seasonal Naive

The primary baseline is:

$$
\hat y_t=y_{t-7}
$$

For a 14-day forecast from a fixed origin, horizons 1–7 use exact prior-calendar-date actuals
available at the origin; horizons 8–14 use the previously generated raw weekly prediction.
Missing exact history remains unavailable, with no prior-row substitution or gap filling. The
reviewed implementation and metric/routing contract are recorded in ADR-013.

If an advanced model cannot consistently outperform the Seasonal Naive baseline, there is insufficient evidence that the additional model complexity provides value.

---

## Model 1 – Exponential Smoothing / Holt-Winters

This classical forecasting model will be used to capture:

- level;
- trend;
- weekly seasonality.

The reviewed candidate is fixed univariate additive Holt-Winters with weekly seasonality and
origin-censored contiguous daily history, including observed closed-day zeros. Its approved
history, failure, clipping, and comparison rules are recorded in ADR-014; it does not use the
LightGBM predictors or a fallback model.

If necessary, SARIMA may be tested on several representative time series, but the project does not require training 1,115 separate SARIMA models.

---

## Model 2 – Global LightGBM Forecasting Model

The primary machine-learning candidate is:

$$
Sales_{s,t}
=
f(
Store,
Calendar,
Promotion,
Competition,
Lags,
RollingFeatures
)
$$

A single global model will be trained across stores using eligible development observations.

For the initial LightGBM candidate, training-label eligibility uses source `Open == 1`; all
observed historical Sales, including closed-day zeros, remain available as origin-safe history.
Before implementation, its Phase 6 design must fix categorical mappings, null handling, objective,
non-negative forecast treatment, a finite tuning budget, fit/refit policy, coverage requirements,
and artifact/test contracts. No model-specific encoding or imputation is silently added to the
reviewed [Feature Contract](FEATURE_CONTRACT.md).

This approach allows the model to exploit information across stores and avoids the need to build 1,115 separate machine-learning models.

---

# 13. Multi-Step Forecasting Strategy

The forecast horizon is 14 days, making this a multi-step forecasting problem.

The LightGBM model will initially use a **recursive forecasting strategy**.

At forecast origin $t$:

1. calculate all features using historical data;
2. predict $\hat y_{t+1}$;
3. insert the non-negative raw prediction into the temporary raw history;
4. update lag and rolling features;
5. predict $\hat y_{t+2}$;
6. repeat until $\hat y_{t+14}$ is obtained.

Mathematically:

$$
\hat y_{t+h}
=
f(
X_{t+h},
y_{\le t},
\hat y_{t+1},
...,
\hat y_{t+h-1}
)
$$

where:

$$
h=1,...,14
$$

Future-known calendar, holiday, and promotion schedules may be used directly.

Actual future sales will never be used during forecasting.

The initial recursive model feeds its own clipped raw predictions into subsequent lag and
rolling features. Generate the complete raw 14-step path before applying supplied/planned Open
to a separate operational output. Target Open never changes the raw recursion; unknown Open gives
an unresolved operational value. This preserves the existing raw/operational boundary, while the
training-history versus predicted-history mismatch remains a limitation to assess by horizon.
A closure-aware feedback strategy would be a separately reviewed methodological extension, not
an implicit change to the Seasonal Naive baseline or this initial LightGBM design.

### Optional Extension

If development-only horizon diagnostics show material recursive error accumulation, a reviewed
extension may evaluate:

- direct forecasting;
- horizon-as-feature models;
- hybrid direct-recursive strategies.

Such alternatives require origin-safe training examples and a documented comparison budget;
they are not part of the initial candidate and cannot be motivated by final-holdout outcomes.

---

# 14. Validation Strategy

The project will use **rolling-origin / walk-forward validation**.

The validation structure is:

$$
Training
\rightarrow
Validation_1
\rightarrow
Validation_2
\rightarrow
Validation_3
\rightarrow
FinalHoldout
$$

Each validation window covers:

$$
14\text{ days}
$$

The procedure is:

1. train the model using historical observations only;
2. forecast the next 14 days;
3. compare forecasts with actual values;
4. move the forecast origin forward;
5. repeat the process.

The primary ladder comparison uses the **three approved 14-day development windows** in
[ADR-013](DECISIONS.md#adr-013---phase-4-seasonal-naive-evaluation-contract). Preserve their origins,
populations, metrics, and existing evidence. They cover a short period and share a weekday at the
origin, so they do not establish year-round performance or isolate horizon effects from weekdays.
Any supplementary earlier development windows must be specified before new comparisons and
applied consistently across candidates. Phase 7 owns final development model selection.

---

## 14.1. Final Holdout

The latest **28 labeled days**, 2015-07-04 through 2015-07-31, are reserved for the final forecast
evaluation. Earlier source-quality summaries and full-source EDA have already exposed descriptive
information, so the project does not claim a pristine unseen-label experiment.

During development, the final holdout will not be used to:

- select features;
- tune hyperparameters;
- select the final model;
- estimate preprocessing parameters;
- choose interval calibration, inventory policies/scenarios, or monitoring thresholds.

Phase 7 selects on development data only. After the model, preprocessing recipe, uncertainty,
inventory policy/scenarios, and monitoring thresholds are locked, Phase 13 performs the sole
authorized sequential final replay. Use origin 2015-07-03 for July 4–17 and origin 2015-07-17 for
July 18–31, each issuing a complete 14-day forecast before revealing that block's observations
day by day. The second origin may use actual history already revealed through July 17 under a
precommitted refit recipe; it may not adapt choices to holdout performance. Phase 14 reports those
results rather than reopening selection.

The freeze fixes model/preprocessing specifications and hyperparameters, not necessarily fitted
state. A scheduled refit may relearn model or preprocessing parameters only if its precommitted
recipe requires it, using eligible training rows already revealed through that origin. Unrevealed
rows and outcome-driven recipe changes remain prohibited. Interval calibration, inventory
policies/scenarios and monitoring thresholds stay fixed throughout the final replay.

---

# 15. Evaluation Metrics

The following required metrics will be reported:

$$
MAE,\ RMSE,\ MAPE
$$

### Primary Metric

$$
\boxed{MAE}
$$

MAE is selected as the primary metric because it is relatively easy to interpret in the same scale as sales.

### Secondary Metrics

$$
RMSE
$$

will be used to place greater penalties on large forecasting errors.

$$
MAPE
$$

will be used with caution because observations with actual values close to zero may make the metric unstable.

The project will additionally report:

$$
WAPE=
\frac{\sum|y-\hat y|}
{\sum y}
$$

to evaluate aggregate forecasting quality.

---

## 15.1. Evaluation Segmentation

Forecasting metrics will be reported by:

- overall performance;
- StoreType;
- Promo vs. non-Promo periods;
- high-volume vs. low-volume stores;
- forecast horizon $h$;
- selected individual stores.

---

## 15.2. Open vs. Closed Store Evaluation

Primary forecasting metrics will only be calculated for:

$$
Open=1
$$

store-days.

Closed-store days will remain in the operational forecasting pipeline and will receive zero forecasts according to the business rule. However, these observations will not be allowed to artificially improve the forecasting metrics.

The report will therefore distinguish between:

**Model performance on open days** – primary evaluation.

**Calendar-level operational performance** – secondary evaluation.

Primary metrics use available raw forecasts on observed source `Open == 1` labels; report
forecast-availability counts and denominators so missing forecasts cannot silently improve scores.
MAPE alone excludes zero-actual eligible rows, adds no epsilon, and reports its excluded count and
coverage. WAPE is unavailable with an explicit reason when the eligible actual-value sum is zero.
Compare candidates on identical available-label rows and report each model's standalone coverage.

---

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

The project will target a:

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

Phase 8 must assign calibration and coverage evaluation to distinct chronological development
residual roles before fitting quantiles. Coverage on the quantile-calibration sample is a
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
$S_P=D_P+SafetyStock_P=\max(D_P,U_P)$. Receipt, demand, holding-cost, and order placement timing
must be frozen in the Phase 10 design so these periods are applied consistently.

That design must also fix forecast-refresh cadence, supported review dates, and terminal-state
handling. A stored 14-step path does not provide a complete $P$-day forecast for every later daily
review in its block. Restrict unsupported recommendations or approve a separate origin-safe
refresh protocol without changing the two-origin primary forecast evaluation or inventing unknown
future covariates.

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
- **Cycle service:** fraction of completed replenishment cycles with no unmet value; distinguish this from the scenario's target.
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

The expected trade-off is:

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

# 20. Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Data processing | pandas, NumPy |
| Data format | CSV → Parquet |
| Visualization | matplotlib, Plotly |
| Statistical forecasting | statsmodels |
| Machine learning | LightGBM, scikit-learn |
| Explainability | Feature importance; SHAP only if needed for a supported analysis |
| Application core | Reusable Python services shared by API and dashboard |
| API | Thin FastAPI local/demo adapter; separate deployment optional |
| Dashboard | Streamlit calling shared services; one deployed dashboard |
| Monitoring | pandas summaries and plots; Evidently optional with a demonstrated need |
| Version control | Git, GitHub |
| Deployment | Streamlit Community Cloud / Render |
| Optional packaging | Docker |

### Spark

Spark will not be part of the project's critical path because the current dataset is not sufficiently large for distributed computing to provide a clear practical benefit.

PySpark may be implemented as an optional ETL experiment if the team wishes to demonstrate knowledge from the course lectures.

---

# 21. Proposed System Architecture

```text
Immutable Rossmann source -> validation -> source-faithful prepared tables
  -> descriptive EDA + point-in-time real-data features
  -> Seasonal Naive / Holt-Winters / Global LightGBM
  -> development walk-forward comparison -> model selection -> uncertainty
                                                        |
Synthetic operational scenarios ------------------------+-> inventory-value engine
                                                           -> shared Python services
                                                              -> Streamlit dashboard
                                                              -> thin FastAPI adapter
Frozen recipes + sequential final replay -> monitoring summaries and final report
```

The synthetic operational/scenario branch is separate from the real-data modeling path and joins
forecasts only for simulated decisions. FastAPI and Streamlit share the same reusable services;
the dashboard need not make HTTP requests to a separately deployed API. Historical monitoring
reports alerts and delayed errors, not an assumed live feed or an autonomous retraining system.

This architecture is also consistent with the Decision Support System structure introduced in the course, which includes data management, model management, and user-interface components.

---

# 22. Dashboard Design

The dashboard will be designed for a demand planner or store manager.

## Inputs

- Store ID
- Forecast Origin
- Supported Forecast Horizon (14 days, or its first seven days)
- Current Inventory Value
- Supplier Lead Time
- Target Service Level
- Average Unit Value

## Historical Analytics

- historical sales;
- promotion periods;
- weekly patterns;
- holidays;
- rolling demand.

## Forecast Panel

- point forecast;
- 95% prediction interval;
- daily forecasts;
- forecast uncertainty.

## Model Explanation

- global feature importance;
- SHAP explanations where appropriate.

## Inventory Decision

The dashboard will display:

- Lead-Time Demand;
- Safety Stock;
- Reorder Point;
- Current Inventory Position;
- Recommended Replenishment Value;
- Equivalent Units.

## Business Alert

For example:

> **HIGH STOCKOUT RISK**

or:

> **CURRENT INVENTORY SUFFICIENT**

---

# 23. Model Monitoring

Monitoring will be conducted at three levels.

## 23.1. Data Drift

The system will monitor distributional changes in:

- lagged sales;
- rolling demand;
- Promo;
- StoreType mix;
- calendar patterns.

## 23.2. Performance Drift

Rolling performance metrics will include:

$$
MAE_t
$$

$$
WAPE_t
$$

$$
IntervalCoverage_t
$$

## 23.3. Business Drift

The system will monitor:

- stockout rate;
- service level;
- inventory level;
- replenishment frequency.

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
7. precommitted monitoring conditions generate alerts.

Use the two fixed 14-day origins and daily reveal protocol from Section 14.1. Forecasts at the
start of a block cannot use observations later revealed within that block; once a target becomes
observable, monitoring joins its actual value to the stored forecast with matching origin/horizon.
No adaptive tuning, interval recalibration, inventory-policy adjustment, or triggered retraining
occurs during this frozen final replay. The second scheduled fit, if specified in advance, uses
only history revealed through its origin. A later adaptive retraining demonstration would require
a separate synthetic or development replay and must not be reported as the same frozen test.

---

## 24.1. Monitoring Alert Rules

For example:

$$
RollingMAE
>
1.2\times BaselineValidationMAE
$$

for two consecutive monitoring windows,

or when:

- substantial data drift is detected;
- interval coverage declines significantly;
- service level falls below an acceptable range.

Thresholds and monitoring-window definitions must be fixed using development evidence before
the final replay. These examples are candidate alert rules, not established requirements or proof
that a 28-day historical replay supports robust drift detection. Evidently is optional; simple
summaries must remain usable without it.

---

# 25. Expected Results

The project is expected to:

1. Identify important factors and patterns associated with daily store sales.
2. Compare the required model ladder fairly, selecting an advanced model only when its development evidence justifies the complexity; retaining Seasonal Naive is a valid result.
3. Quantify forecast uncertainty.
4. Develop an interpretable inventory decision framework.
5. Measure simulated inventory-policy trade-offs and report improvements, deterioration, or no benefit without presupposing a favorable outcome.
6. Deploy a functioning analytics application.
7. Demonstrate a historical monitoring workflow with precommitted alert conditions.

The proposal does not assume in advance that LightGBM will necessarily be the best-performing model.

---

# 26. Success Criteria

## Analytics

A more complex candidate must justify selection through paired development MAE, coverage, and
stability, including improvement over Seasonal Naive on the majority of the fixed windows. If
the evidence does not support it, retain the baseline and explain the limitation. A valid,
reproducible comparison is the success criterion; an improvement is not guaranteed.

## Forecast Uncertainty

Report interval coverage and width on chronologically distinct evaluation residuals and then the
frozen final replay. Explain deviations, small samples, and heterogeneous-store limitations rather
than promising nominal coverage in advance.

## Business

Compare service and cost proxies under common scenarios, with explicit denominators and
sensitivity analysis. Report whether a policy improves any KPI without unacceptable deterioration
elsewhere; unfavorable or inconclusive results remain valid project findings.

## Engineering

The application should support the complete workflow:

$$
Store
\rightarrow
Forecast
\rightarrow
Uncertainty
\rightarrow
InventoryRecommendation
$$

without requiring manual notebook execution.

## Monitoring

The system should demonstrate:

- drift detection;
- rolling performance monitoring;
- business monitoring;
- alert rules derived from development evidence.

---

# 27. Key Limitations

### No Product/SKU Data

SKU-level forecasting cannot be directly performed using the original dataset.

### Sales is Monetary Turnover

The primary forecasting and inventory-planning calculations are therefore conducted in monetary-value units.

Observed turnover is not uncensored demand or procurement-cost stock. Inventory comparisons use
a simulated retail-equivalent-value basis and cannot recover actual Rossmann product availability.

### Synthetic Supply-Chain Data

Lead time, inventory, unit value, and cost parameters are not real Rossmann operational data.

### Historical Dataset

The project is not intended to serve as a forecasting system for Rossmann's current operations.

### Synthetic Business Evaluation

The inventory simulation is intended to demonstrate the methodology rather than provide actual inventory-policy recommendations for Rossmann.

### Evaluation Scope

The three development windows cover only 42 days and confound weekday with horizon. Earlier
full-source descriptive EDA included holdout dates; final evaluation remains protected from model
selection, but is not described as a pristine unseen-label experiment. Empirical pooled intervals
and simulated cost/service metrics have the assumptions and limits described above.

---

# 28. Project Risks and Mitigation

| Risk | Consequence | Mitigation |
|---|---|---|
| Future leakage | Artificially high forecasting accuracy | Strict time-aware pipeline |
| Recursive error accumulation | Performance degradation at longer horizons | Evaluate by horizon; consider a direct forecasting strategy if necessary |
| Synthetic assumptions dominate results | Weak business validity | Keep the forecasting core based on real data and conduct sensitivity analysis |
| Store heterogeneity | Aggregate metrics may hide poorly performing stores | Conduct segment-level evaluation |
| Promotion spikes | Large forecasting errors | Use promotion-aware features and separate evaluations |
| MAPE instability | Misleading conclusions | Use MAE as the primary metric and WAPE as a supplementary metric |
| Closed days inflate metrics | Artificially improved performance | Primary evaluation only on `Open=1` observations |
| Cloud resource limitations | Deployment or demo failure | Use compact models and prediction caching |
| No live Rossmann data feed | Monitoring becomes artificial | Use sequential pseudo-production simulation on the holdout set |

---

# 29. Proposed 8-Week Plan

| Week | Main Work |
|---|---|
| **1** | Finalize scope, assumptions, Data Dictionary, and data acquisition |
| **2** | Data cleaning, validation, integration, and EDA |
| **3** | Feature engineering + Seasonal Naive baseline |
| **4** | Exponential Smoothing + initial backtesting |
| **5** | Approved LightGBM design + bounded tuning + development model selection (Phases 6–7) |
| **6** | Separate uncertainty calibration/evaluation + synthetic scenarios + inventory simulation (Phases 8–10) |
| **7** | Shared services + thin API + Streamlit + locked monitoring design (Phases 11–13 preparation) |
| **8** | Authorized sequential final replay + final checks, report, slides, and demo (Phases 13–14) |

This is a planning estimate, not a claim of completed work. Retain Phase 0–14 identifiers for
historical traceability, but adjacent future phases may share one coherent execution plan and
branch. Separate design or closeout branches are not required for every phase.

---

# 30. Final Deliverables

The scoped project deliverables are:

- a GitHub repository containing source code written by the team;
- a complete Data Dictionary;
- notebooks/scripts for data processing, EDA, and modelling;
- a synthetic data-generation module;
- the final forecasting model;
- an inventory decision engine;
- reusable application services and a thin, tested local/demo FastAPI adapter;
- one deployed Streamlit demand-planning dashboard; separate API deployment is optional;
- a historical monitoring report with clearly labeled simulated business indicators;
- a final report in PDF format;
- presentation slides;
- a live or recorded demonstration.

All source code will be developed by the team members, and no no-code/AutoML platform will be used.
