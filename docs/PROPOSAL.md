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

**Instructor-aligned scope.** The instructor acceptance recorded in ADR-028 confirms
**Store × Date monetary Sales forecasting with a primary H14 horizon**. This is consistent with
accepted ADR-001–004 and answers the business question at the finest granularity supported by
Rossmann. Inventing SKU identifiers or category-level demand would not add observed information.
The required synthetic operational extension supports conditional inventory-value decisions;
it does not turn turnover into observed physical or unconstrained demand.

**Delivery and approval status (2026-10-24).** This canonical proposal specifies the full course
delivery, rather than certifying completion. [PROGRESS](PROGRESS.md) records Phases 0–12 as
COMPLETE; Phase 13 M1–M3 are integrated, but the phase remains PLANNED / NOT APPROVED and final
evaluation has not run. WP1 scenario analysis is incomplete and no real-data scenario experiment
has run. The controlled-synthetic public-demo implementation is integrated with Milestone B
closeout pending; there are no authorized public deployment URLs. ADR-028 remains PROPOSED.
ADR-030 accepts only the narrow future two-URL objective; ADR-024 still governs the existing
localhost runtime. Further monitoring methods and release actions retain their separate gates.

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
7. Deliver reusable application services and, after the required release approvals, one publicly
   accessible read-only FastAPI demonstration URL and one publicly accessible Streamlit dashboard URL.
8. Demonstrate data-quality, data-characteristic, delayed forecast-performance, and simulated
   business monitoring, with documented alerts and human retraining-review conditions.
9. Compare the three existing forecasting approaches across approved Store-level scenarios,
   explaining coverage, failure cases, uncertainty, and supported business implications.
10. Deliver reproducible GitHub source, a complete Data Dictionary, a monitoring report or
    dashboard, a PDF report, presentation slides, and a demonstration.

These objectives are aligned with the project requirements concerning forecast horizon, stockouts, holding costs, service-level targets, deployment, and monitoring.

## 2.3. Assignment Requirement Traceability

The assignment requires eight modules, Rossmann Store Sales as the base dataset, and a documented
synthetic operational/supply-chain extension. Example synthetic fields are illustrative rather
than individually mandatory. The matrix distinguishes implemented evidence from acceptance still
needed; the final artifact checklist is in Section 30.

| Assignment module | Project solution and existing evidence | Current status and remaining acceptance gate |
|---|---|---|
| 1. Business Understanding and Data Generation | Store-level monetary business question; separate deterministic operational scenarios; [Data Dictionary](DATA_DICTIONARY.md), ADR-001–005/022 | Core scope and Phase 9 generator complete; disclose synthetic assumptions and limits in final delivery |
| 2. Exploratory Data Analysis | Trends, seasonality, promotion/Store associations and anomalies in [EDA findings](EDA_FINDINGS.md); bounded weekly STL implementation under ADR-027 | Phase 2 complete with historical full-source exposure disclosed; authorized real-data STL and published findings still pending |
| 3. Data Cleaning | Source-faithful validation, sparse-date/null retention and checked joins; [validation evidence](DATA_VALIDATION.md) | Phases 1–2 complete; preserve unresolved source conditions rather than invent corrections |
| 4. Feature Engineering | Frozen 29-predictor [Feature Contract](FEATURE_CONTRACT.md), exact-calendar lags and recursive origin-safe history | Phase 3 complete; no new predictors or learned full-source cohorts authorized |
| 5. Model Development | Seasonal Naive, additive Holt-Winters, Global LightGBM; ADR-013/020/021 and [development evidence](PROGRESS.md) | Phases 4–8 complete, LightGBM recipe selected and Fit B frozen; real-data WP1 scenario analysis and gated Phase 13 final evaluation pending |
| 6. Model Deployment | Shared services, local read-only FastAPI and five-screen Streamlit; [public-demo plan](../plans/active/public-course-demo.md) | Phases 11–12 complete locally; synthetic adapters integrated, B closeout pending; two public URLs require Milestone C/security/content/owner release approval |
| 7. Model Monitoring | Existing validation/availability checks and inventory KPI definitions; ADR-026 descriptive replay design; Sections 23–24 | Final replay monitoring/report not delivered; broader alerts and retraining-review policy are proposed and need a separate accepted method |
| 8. Final Report and Presentation | Phase 14 consolidates reviewed analytics, limitations, reproducibility, PDF, slides and demo | Incomplete; requires remaining analytical evidence and authorized demonstrations, with human ownership and AI-assistance disclosure |

No row substitutes implementation, fixture tests, or a proposed design for a delivered course
artifact. Source access, analytical release, and public content release are distinct approvals.

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

**AQ3.** How do Seasonal Naive, additive Holt-Winters, and Global LightGBM differ on the same chronological origins and eligible target rows, overall and within supported Store-level scenarios?

**AQ4.** What development evidence supports the selected H14 LightGBM recipe, and where do simpler methods, sparse coverage, or horizon-specific failures limit its use? The accepted Phase 7 selection is retained.

**AQ5.** How does forecast uncertainty change across forecast horizons and store types?

**AQ6.** Under simulated inventory, lead-time, and service assumptions, what inventory-value recommendation does the chosen policy produce?

**AQ7.** Under which simulated scenarios does a forecast-driven policy improve or worsen service and cost indicators relative to a baseline policy?

**AQ8.** Which data-quality, availability, distribution, and delayed-error indicators warrant a
human review, and what can a short historical replay demonstrate about those indicators?

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

## 6.1. Implemented Synthetic Operational Variables

Phase 9 is COMPLETE under ADR-022. The table summarizes its implemented inputs and the Phase 10
state they initialize; [Data Dictionary Sections D–E](DATA_DICTIONARY.md#d-synthetic-operational-variables)
and the [completed Phase 9 plan](../plans/completed/phase-9-synthetic-inventory.md) own the exact
schema, ranges, dependencies, and deterministic generation algorithm.

| Variable | Unit | Purpose | Generation Logic |
|---|---|---|---|
| `SupplierLeadTime` | calendar days | Replenishment lead time | Store-specific integer 2–7; daily review R=1 gives protection P=L+1=3–8 |
| `StockOnHandValue` | retail-equivalent value | Simulated inventory | Mean observed Open=1 Sales in the 56 calendar days through origin, requiring at least 28 valid open rows, times initial coverage |
| `ServiceLevelTarget` | probability label | Nominal cumulative buffer parameter, not achieved service or value fill | Base 0.95; sensitivity 0.90/0.98; no calibrated synthetic-service guarantee |
| `HoldingCostRate` | cost per inventory-value unit per day | Simulated holding-cost proxy | Synthetic procurement ratio c in [0.55,0.85), annual rate a in [0.10,0.30); rate c*a/365 |
| `StockoutPenalty` | cost per unmet sales-value unit | Simulated shortfall-cost proxy | (1-c)+g with synthetic goodwill rate g in [0.10,0.75); includes the hypothetical margin component once |
| `AverageUnitValue` | retail-equivalent value/equivalent unit | Display-only conversion assumption | Store-level draw from {5,10,20,50}; no real SKU mapping |
| `DiscountDepth` | proportion | Implemented synthetic stress promotion intensity | Zero without synthetic promotion; normal promotion [0.05,0.30), specified peak 0.40; never a Rossmann predictor |
| `InventoryCoverageDays` | reference open-day equivalents | Initial inventory policy | Base L+1+B, B in {0,1,2,3}, giving 3–11; thin-stock stress uses 1 |

The generator uses **master seed 4209**, SHA-256 keyed draws, five paired replicates, eight synthetic
families and a separate historical reference at the two development origins June 5 and June 19.
Replicates are designed cases, not estimates of scenario likelihood. The controlled-synthetic
application demonstration in Section 21 uses its own fixture contract and seed; it is not this
Rossmann-anchored generator or an inventory-simulation run.

---

## 6.2. Synthetic Data Generation Principles

Synthetic variables follow the accepted dependencies rather than independent arbitrary draws.

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

An unavailable anchor remains unavailable without fallback or gap filling; observed zero turnover
is valid. The outstanding-order queue starts empty only at initialization and evolves in Phase 10.
Ranges and dependencies are illustrative business assumptions, not fitted Rossmann supply-chain
distributions. Manifests pin code/configuration, seed, source/output hashes and environment/lock
identity, keeping the accepted historical artifact provenance intact.

---

## 6.3. Synthetic Scenario Generator

The implemented Phase 9 generator supplies **trend, seasonality, promotion, and supply-chain
context** under its accepted deterministic contract. It supplements the real forecasting benchmark
with synthetic monetary consumption paths for conditional inventory-policy sensitivity analysis.

The generator does not replace the Rossmann dataset. Its designed paths support:

- pipeline testing;
- stress testing;
- possible separately approved development/synthetic monitoring demonstrations;
- inventory stress under synthetic promotional spikes;
- testing stockout scenarios.

A synthetic demand series can be described schematically as:

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
The additive expression above is conceptual; the implemented Phase 9 path uses the exact
multiplicative anchor/trend/weekday/promotion/holiday/shock rules in its completed plan. Frozen
forecasts and uncertainty are not retrained on synthetic paths. Perishability and weather sensitivity
are optional, unimplemented scenario extensions requiring a separate design; illustrative assignment
examples do not require inventing those observations.

---

## 6.4. Synthetic Data Validation

The Phase 9 contract validates synthetic data at three levels, with explicit unavailable states
and integrity checks. The following conditions summarize the design; exact checks and accepted
development-run evidence are linked from [PROGRESS](PROGRESS.md).

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

An advanced candidate must justify its complexity under the accepted development-selection rule;
it need not beat Seasonal Naive in every store, horizon, or scenario. ADR-020's paired MAE,
coverage and stability gates selected Global LightGBM trial A at 180 rounds in completed Phase 7.
That result remains fixed; the scenario analysis below characterizes its limits without restarting
selection or requiring a favorable result.

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

SARIMA is an optional extension requiring a separately authorized design and development-only
comparison; it is outside the approved three-model ladder.

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
Completed Phase 6 fixed these choices in ADR-019: regression_l1, fit-only category vocabularies,
native numeric missing handling, non-negative raw clipping, four predeclared inner-origin trials,
coverage gates and origin-safe recursive evaluation. Phase 7 selected trial A at exactly 180 rounds
under ADR-020. No model-specific encoding or imputation changes the reviewed
[Feature Contract](FEATURE_CONTRACT.md); the selected fit/refit recipe and numerical development
results remain as recorded in [PROGRESS](PROGRESS.md).

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

Phase 7 selected on development data only. After the model, preprocessing recipe, uncertainty,
inventory policy/scenarios, monitoring definitions and deterministic integrity/data-quality rules
are locked, Phase 13 may perform the sole final replay only under its separate execution, staging
and analytical-release authorizations. None is granted by this proposal. Use origin 2015-07-03 for
July 4–17 and origin 2015-07-17 for
July 18–31, each issuing a complete 14-day forecast before revealing that block's observations
day by day. The second origin may use actual history already revealed through July 17 under a
precommitted refit recipe; it may not adapt choices to holdout performance. Phase 14 reports those
results rather than reopening selection.

The freeze fixes model/preprocessing specifications and hyperparameters, not necessarily fitted
state. A scheduled refit may relearn model or preprocessing parameters only if its precommitted
recipe requires it, using eligible training rows already revealed through that origin. Unrevealed
rows and outcome-driven recipe changes remain prohibited. Interval calibration, inventory
policies/scenarios, monitoring definitions and deterministic integrity/data-quality rules stay
fixed throughout the final replay. Numeric performance/drift thresholds are not selected for it.

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

Overall, per-window and forecast-horizon $h$ diagnostics are part of the accepted development comparison.
Additional scenario comparisons follow Section 15.3 and the
[active WP1 plan](../plans/active/wp1-scenario-forecast-evaluation.md); the presence of a Store
attribute does not authorize a real-data source operation or a new segmentation method.

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

## 15.3. Scenario-Based Forecast Evaluation

The mandatory forecast scenario comparison asks **where and why the existing LightGBM recipe
behaves differently from Seasonal Naive and additive Holt-Winters**. It preserves the completed
Phase 7 selection and the three ADR-013 chronological H14 development windows. LightGBM need not
lead in every stratum. A cross-model inventory simulation is optional bonus work with a separate
design; synthetic inventory stresses are not observed forecasting scenario strata.

| Scenario dimension | Supported interpretation and method boundary |
|---|---|
| Store type and assortment | Source category strata with missing/unrecognized values explicit; WP1 L2 definitions exist, but real metadata preparation/provider approval is pending |
| Promotion versus non-promotion | Retrospective keyed source Promo membership; does not prove origin-time plan availability; fixture handoff currently enables Promo only |
| Weekday/weekend and holidays | Implemented ISO weekday strata; a combined weekday/weekend summary requires a predeclared approved aggregation. Source StateHoliday/SchoolHoliday codes only where interpretable and available; no invented holiday meanings or causal effects |
| Competition characteristics | Candidate distance/opening-status strata using documented static-snapshot and month-precision assumptions; bin rules and source access require a separate approved extension |
| High/low store volume | Proposed cohorts using eligible origin-training/development history only; never full-source EDA tiers or final outcomes; H segmentation remains BLOCKED pending its own approved definition and inputs |
| Forecast origin and horizon | Retain all three windows, h1–14 and h1–7 versus h8–14, including unfavorable and sparse horizons; shared Friday origins confound weekday and horizon |

Before any real-data analysis, freeze the permitted strata, membership sources, bin/cutoff rules,
minimum-support and unavailable-result rules, comparison outputs and interpretation limits.
Interactions, new origins, competition/volume cohorts, statistical inference and other extensions
need separate approval; descriptive category differences are not causal effects.

Fair comparison requires:

1. The same three forecast origins and source-observed Store × Date target roster for all three
   frozen candidates, with Sales/Open attached only after raw issuance. Preserve the development
   ceiling Date <= 2015-07-03 and exact candidate identities.
2. The identical three-way common eligible/available observed Open=1 rows for primary scenario
   comparisons. Also report standalone and pairwise availability, eligible-label counts,
   missing-prediction reasons and common-row exclusions; a model cannot improve its score by
   silently dropping difficult rows.
3. MAE as primary, with RMSE/WAPE and the existing cautious MAPE contract as supporting evidence.
   Preserve each metric's denominator, zero-actual MAPE exclusions and zero-total WAPE
   unavailability. Existing WP1 L2 emits MAE/RMSE/WAPE and directional errors; it does not add
   scenario MAPE. Scenario MAPE needs a separately approved extension or a clearly labeled link
   to existing Phase 7 diagnostics, rather than a claim that L2 already produces it.
4. For each stratum, disclose stores, dates, origins, eligible rows, common rows, forecast coverage,
   metric denominators and unavailable results. Sparse groups remain descriptive or unavailable
   under the approved support rule; no pooling, fallback, confidence or significance claim is
   introduced to manufacture support.
5. Interpret error direction, magnitude and horizon failures alongside opening/promotion assumptions
   and availability. Discuss when a simpler method is adequate and when missing inputs prevent a
   conclusion. Keep point-error comparisons distinct from uncertainty: any segment interval
   assessment preserves frozen daily/cumulative definitions, reports support and empirical
   coverage, and needs its own approved scope without recalibration or guaranteed store coverage.

**Current evidence and gate:** WP1 L1/L2/L3-F and fixture Milestones 1–2 are REVIEWED / INTEGRATED.
They provide common-population aggregation and controlled-synthetic handoff tests, not Rossmann
scenario findings. ADR-029 restricts the fixture verifier/provider; hashes and bindings do not
authorize real inputs, prove custody or enforce hard peak-memory containment. WP1-S7-01 remains
unresolved under its original contract. Real-source M/C/H operations, real L3 preparation/
verification/binding and L4 analysis remain separately gated. ADR-028 is still PROPOSED; this
subsection specifies the delivery need and pending extensions without approving their execution.

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

Completed Phase 8 assigned distinct chronological development residual roles in ADR-021:
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
accounting in ADR-023: an end-of-day order at t arrives before demand at t+L+1; receipts precede
consumption, unmet value is lost, costs use ending stock, and the final day suppresses new ordering.
Targets are frozen once at origin, the outstanding-order queue evolves, and due-after-window
orders remain separate terminal exposures without cancellation or salvage.

For Phase 13, the owner has approved the A-bounded inventory scope and its explicit
acceptance limitation under ADR-025: inventory evaluation uses two independent origin-frozen H14
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
| API | Thin read-only FastAPI adapter; local implementation exists, one public demonstration URL required for final delivery after release approval |
| Dashboard | Streamlit calling shared Python services directly; local implementation exists, one public dashboard URL required after release approval |
| Monitoring | pandas summaries and plots; frozen descriptive Phase 13 method, broader alert/retraining-review extensions pending approval; Evidently optional |
| Version control | Git, GitHub |
| Deployment | Pending; Render preferred for assessment under ADR-030, with no host selected or provisioned |
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

Separate controlled-synthetic bundle -> explicit read-only demonstration provider
  -> synthetic FastAPI adapter + direct-service Streamlit dashboard
  -> two future public URLs only after content/security/hosting/owner release approval
```

The synthetic operational/scenario branch is separate from the real-data modeling path and joins
forecasts only for simulated decisions. FastAPI and Streamlit share the same reusable services;
the dashboard need not make HTTP requests to a separately deployed API. Historical monitoring
reports alerts and delayed errors, not an assumed live feed or an autonomous retraining system.

The final course delivery commits to **one publicly accessible read-only FastAPI URL and one
publicly accessible Streamlit URL**. Precomputed outputs suffice; on-demand inference is optional.
ADR-017's earlier optional independent API hosting is historical delivery sufficiency. ADR-030
accepts the narrow future two-URL objective, conditional on a separately authorized release; it
does not supersede ADR-024's current localhost runtime or approve ADR-028's remaining proposals.

Phases 11–12 implement the canonical local services/API/dashboard over pinned development
artifacts. The separate controlled-synthetic bundle, provider, API adapter and dashboard are
integrated; Milestone B closeout and corrective independent review remain pending in the
[public-demo plan](../plans/active/public-course-demo.md). Their fixture arithmetic demonstrates
interfaces and availability states only: it is not observed Rossmann history, historical model
execution/accuracy, fitted uncertainty, inventory-simulator output or actual inventory quantities.
Actual Rossmann-derived analytical evidence remains a separate, governed local evidence stream.
Git already places the WP2-S22 minor corrections on `origin/main` at `a8edc487`; their independent
acceptance and formal Milestone B closeout are not recorded. Pending-integration wording in the
older progress/plan checkpoint does not override that observed Git state.

No public runtime configuration, published bundle or live deployment URL exists. Milestone C
requires exact-content/rights approval, a trusted manifest hash supplied independently,
independent implementation/security review, a host resource and rollback plan, explicit owner
authorization for the deployment/audience/window, staged external checks, and a release/shutdown
record. Any later source-derived public content requires separate source-access, provenance,
redistribution-rights and exact-content approval. Missing synthetic inputs must fail closed without
fallback to canonical artifacts. The [release contract](PUBLIC_DEMO_RELEASE_CONTRACT.md) governs
content; this documentation work grants no release permission.

This architecture is also consistent with the Decision Support System structure introduced in the course, which includes data management, model management, and user-interface components.

---

# 22. Dashboard Design

The dashboard will be designed for a demand planner or store manager.

The following is the intended decision-support design. The completed canonical five-screen
application presents bounded history, saved forecasts/uncertainty, model comparisons and synthetic
inventory comparisons through shared services. It does not perform on-demand fitting, forecasting,
simulation, or unrestricted scenario editing. The separate synthetic demo presents labeled fixture
views. Extra input controls, explanation panels and business alerts below are delivery concepts
requiring verification/design before they can be claimed as implemented; SHAP is optional.

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

The final monitoring report or dashboard must distinguish four dimensions. Existing validation,
forecast-availability and simulated-KPI components provide building blocks; they do not constitute
a completed monitoring report. Phase 13's selected monitoring design in ADR-026 is narrower than
the broader instructor-feedback proposals in ADR-028. Its monitoring implementation and final
replay evidence remain pending.

## 23.1. Data Quality Monitoring

Record schema/type consistency, duplicate Store-Date and issuance keys, missing/invalid values,
missing calendar dates, coverage changes, and missing or inconsistent operational inputs. Preserve
absent dates, nulls and observed zeros as different states. Distinguish expected source sparsity
from a failed declared input contract. Report forecast availability and unresolved planned Open,
schedule provenance or protection-period inputs with counts, reasons and affected Store/origin/
horizon. Unavailable operational values remain unavailable rather than zero.

Existing validators and integrity/availability checks support these diagnostics. ADR-026 selects
precommitted deterministic integrity/data-quality alerts for the future replay; the exact rule
catalog and output still require the relevant implementation/review gates.

## 23.2. Data Characteristics and Drift Monitoring

Describe selected supported distributions: Promo frequency, calendar/holiday categories, StoreType
and Assortment mix, and missingness and quantiles of origin-safe lagged/rolling Sales histories.
Compare with a versioned eligible development reference, retaining segment sizes and static-snapshot
availability assumptions. Sales-history summaries use only observations already available through
the relevant origin; they do not create new target-derived cohorts or feed revealed within-block
actuals back into a previously issued forecast.

Descriptive frequency/quantile shifts fit ADR-026. Numeric distribution-shift alerts, new tests,
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

Descriptive delayed errors/coverage are selected under ADR-026. A future bias summary can use a
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
remain pending. Numeric business-service alerts are not selected by ADR-026 and need separate
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
ADR-025 runs two independent origin-frozen H14 episodes on those same origins; daily KPI updates
follow the sequential reveal while each policy continues to use its original frozen target. Those
daily state transitions are not new calibrated rolling forecast decisions, and unsupported
later-review protection coverage is not scored. No new rolling operational forecast origin or
daily suffix recalibration is introduced. The inventory scope does not imply continuous
rolling 28-day validation. ADR-025 approves inventory scope only. ADR-026 records the selected
forecast-input/availability assumptions, synthetic planned-Open schedule, Fit B transport, A2
custody, runtime/reproducibility, monitoring, and score/comparator methods. Source identity,
provenance, safe preparation, operator/partition provenance, resource approval, and separate
implementation, rehearsal, staging, and analytical-release gates remain pending.

The selected Phase 13 methods are recorded in ADR-026. Source identity, covariate provenance,
historical availability assumptions, safe acquisition and authorized preparation remain preflight
requirements. Scope and method selection do not authorize a source read, extraction, protected-data
staging, or analytical release. If required covariates exist only in a combined source containing
protected Sales/Open, a separately reviewed safe-preparation/custody procedure is required before
any access to that source; column projection alone does not establish physical isolation.

---

## 24.1. Monitoring Alert Rules

**Selected Phase 13 method (ADR-026):** report descriptive daily, trailing 7-calendar-day, and
trailing 14-calendar-day summaries, stratified by forecast origin and horizon. Show descriptive
feature-distribution shifts and post-release forecast errors and interval coverage with their
populations and denominators. Precommit deterministic integrity and data-quality alerts only.
Statistical drift, forecast-performance, interval-coverage, and service-level alarm thresholds are
not selected. Alert definitions must be independent of final outcomes. ADR-021 calibration sample
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
development-only or synthetic monitoring demonstration. It does not change ADR-026, operate during
the frozen Phase 13 replay, authorize automatic retraining, or accept ADR-028 wholesale.

All numeric values below are **proposed operational policy parameters**, chosen to demonstrate
minimum-support and persistence rules; none is empirically validated or calibrated here.
An approved development-only rehearsal must justify or revise them and freeze the reference,
parameters and metric/segment rules before use. The final holdout must never calibrate them.

| Policy element | Proposed testable rule and evidence requirement |
|---|---|
| Reference and windows | Version a development-only reference from approved chronological forecasts earlier than the assessment windows, using identical eligibility, metric definitions and comparable origin/horizon/segment populations. Exclude assessed rows from the reference. Assess completed, consecutive **non-overlapping 14-calendar-day windows**; show daily and trailing 7/14-day descriptive views separately. Freeze reference values and boundaries before assessment. |
| Minimum evidence | For a performance or feature-shift decision require at least **10 distinct observed target dates, 100 distinct stores and 1,000 eligible paired rows** in each assessed window and its reference. Use the fixed common-row comparison population; disclose total eligible rows and availability separately. For availability checks apply the same date/store/row floors to the eligible observed-label roster **before** filtering missing forecasts, so an outage cannot hide itself. WAPE comparisons additionally require a positive reference WAPE and actual-value denominator. Unsupported/sparse subgroups, zero denominators or partial windows are **UNAVAILABLE EVIDENCE**, never a passing result. These monitoring floors are distinct from ADR-021's calibration floors. |
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

# 25. Expected Results

The project is expected to:

1. Identify important factors and patterns associated with daily store sales.
2. Compare the required model ladder fairly, selecting an advanced model only when its development evidence justifies the complexity; retaining Seasonal Naive is a valid result.
3. Quantify forecast uncertainty.
4. Develop an interpretable inventory decision framework.
5. Measure simulated inventory-policy trade-offs and report improvements, deterioration, or no benefit without presupposing a favorable outcome.
6. Deliver both public demonstration URLs after authorized content/security/hosting release.
7. Demonstrate the approved historical monitoring workflow and separately document proposed human
   retraining-review triggers, with their evidence and approval limits.
8. Explain model differences across supported Store-level scenarios without inventing physical
   demand, business savings or universal model superiority.

The completed development selection chose LightGBM under ADR-020. This does not establish that it
is best in every scenario, future period or business simulation, or permit reopening selection on
final outcomes.

---

# 26. Success Criteria

## Analytics

The completed ADR-020 selection justifies the selected recipe through paired development MAE,
coverage and stability under its fixed simplicity ladder. Retain its selected LightGBM identity,
frozen refit recipe and historical evidence. Success also requires the separately approved WP1
scenario comparison with shared rows/denominators, missing-prediction accounting, segment support,
business interpretation and unfavorable cases. No model must win every scenario and no new model
selection is performed. Final evaluation uses the frozen LightGBM system and Seasonal Naive
contextual comparator under ADR-026, rather than another three-candidate selection.

## Forecast Uncertainty

Report interval coverage and width on chronologically distinct evaluation residuals and then the
frozen final replay. Explain deviations, small samples, and heterogeneous-store limitations rather
than promising nominal coverage in advance.

## Business

Compare service and cost proxies under common scenarios, with explicit denominators and
sensitivity analysis. Report whether a policy improves any KPI without unacceptable deterioration
elsewhere; unfavorable or inconclusive results remain valid project findings.

Phase 13's owner-approved A-bounded scope evaluates paired simulated inventory policies in two
independent H14 episodes using the accepted Phase 10 standing-target mechanics and full
precommitted scenario/sensitivity panel, subject to the resource-feasibility gate. The episodes
have no fresh calibrated protection-period forecast at each later daily review and make no claim
of continuous rolling 28-day inventory operation. They remain monetary simulations, not actual
Rossmann stock or demand, causal improvement, guaranteed service, or business savings.

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

Final deployment acceptance additionally requires two actually reachable, authorized, read-only
public URLs, a pinned approved immutable demonstration bundle, clear synthetic evidence labels,
bounded queries, per-view unavailable states and recorded external checks under Milestone C.
Existing localhost acceptance and synthetic fixture tests alone do not satisfy that criterion.

## Monitoring

The Phase 13 monitoring method is selected in ADR-026: descriptive daily/trailing 7/14-day windows
stratified by origin/horizon; descriptive feature shifts and post-release errors/coverage; and
deterministic integrity/data-quality alerts only. No arbitrary numeric drift, performance,
coverage, or service threshold is selected. Report denominators and partial windows; do not claim
statistically reliable drift or service detection from this replay.

The final monitoring report or dashboard must distinguish all four dimensions in Section 23 and
document human retraining-review conditions. The broader operational policy in Section 24.2 needs
separate methodology approval, development-only justification and implementation/verification;
its warning, unavailable-evidence and review-required examples are additional acceptance work,
not authority to introduce new alarms or adaptive retraining into Phase 13.

## Delivery

Provide the GitHub source and reproducibility instructions, complete real/engineered/synthetic
Data Dictionary, authorized API/dashboard URLs, monitoring report or dashboard, PDF report,
presentation slides and demonstration. Each artifact must cite reviewed evidence and distinguish
real analytical results from synthetic interface illustrations. Human team ownership, review and
appropriate AI-assistance disclosure remain part of delivery acceptance.

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

### Delivery and Approval Gaps

Integrated local applications and synthetic adapters are not public deployment. Real-data scenario
findings, authorized STL evidence, final replay monitoring/results, PDF and slides remain pending.
ADR-028's additional methods are proposed, ADR-030 grants only a narrow future objective, and
ADR-024 remains the current runtime boundary. This proposal describes a route to course compliance;
documentation changes alone do not complete those deliverables or authorize their execution.

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
| No live Rossmann data feed | Monitoring has limited external validity | Use only the separately authorized frozen sequential replay; disclose its short span and keep operational trigger validation separate |
| Release or rights gate unresolved | Required public URLs remain undelivered | Complete exact-content/security/resource review and explicit owner release authorization; retain localhost operation until then |

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

## 29.1. Remaining Delivery Roadmap

The eight-week table preserves the original sequencing estimate. Actual work follows
[PROGRESS](PROGRESS.md), the [project roadmap](PROJECT_PLAN.md) and the three relevant active plans;
it is not a new schedule or blanket implementation authorization.

| Remaining work | Dependency and reviewable exit evidence |
|---|---|
| Complete mandatory scenario evidence | [WP1](../plans/active/wp1-scenario-forecast-evaluation.md): retain integrated L1/L2 and fixture handoffs; approve real input preparation/verification/provider binding and L4, resolve blocked volume/other extension methods before use, then review paired development-only results and failure cases |
| Publish supplementary EDA findings | [CC-02D runbook](CC-02D_CUSTODIAN_RUNBOOK.md): separately authorize source access, preparation, independent verification/binding, provider loading, STL execution and findings publication; readiness code is not a completed operation |
| Finish the two-URL demonstration | [Public-demo plan](../plans/active/public-course-demo.md): finish B corrective review/explicit closeout; obtain Milestone C exact-content/rights/security/resource/hosting/audience authorization and verified public access; synthetic examples remain separate from Rossmann evidence |
| Define broader monitoring delivery | Approve and justify a development-only operational alert/retraining-review design such as Section 24.2, with testable state examples and a report/dashboard; keep it outside ADR-026's frozen replay and disclose unvalidated parameters |
| Complete the single final evaluation | [Phase 13 plan](../plans/active/phase-13-sequential-final-evaluation.md): independent M3 review, safe source/preparation/custody provenance, remaining implementation/review, resource gate, separately authorized rehearsal/staging and chronological analytical release; frozen recipes and two A-bounded episodes unchanged |
| Complete final report, slides and demonstration | Phase 14 after reviewed evidence: consolidate model/scenario/uncertainty/inventory/monitoring findings, adverse results, rights and scientific limitations, reproducibility and human ownership/AI disclosure; link actual authorized URLs only |

Any new method that could affect the final protocol must be resolved and frozen before release.
If the intended monitoring or deployment delivery requires superseding an accepted constraint,
record the scoped approval explicitly; this proposal does not amend existing ADRs by implication.

---

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
