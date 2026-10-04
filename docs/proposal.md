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

> How much will sell over the coming days/weeks, and how should replenishment quantities be set based on that forecast?

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

This approach ensures that the core forecasting component remains grounded in real data, while synthetic data are used only for operational information that is unavailable in the original dataset.

---

# 2. Project Objectives

## 2.1. General Objective

To develop an end-to-end Business Analytics system capable of:

> **Forecasting the daily sales of each Rossmann store for the next 14 days and transforming those forecasts into replenishment recommendations to support inventory management decisions.**

## 2.2. Specific Objectives

1. Explore trends, weekly seasonality, holiday effects, promotion effects, store characteristics, competition, and other patterns associated with sales.
2. Develop and compare forecasting approaches ranging from baseline and statistical forecasting models to machine-learning models.
3. Forecast `Sales` for each store over a primary **14-day forecast horizon**.
4. Quantify forecast uncertainty through prediction intervals.
5. Transform forecasts into inventory-related indicators such as lead-time demand, safety stock, reorder point, and replenishment recommendations.
6. Evaluate not only forecast accuracy but also business outcomes such as stockout rate, service level, and inventory holding cost.
7. Deploy the system as a usable API and dashboard.
8. Develop a monitoring layer to track data drift, forecasting errors, and business performance.

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

The dashboard may additionally allow users to view 7-day or 28-day forecasts. However, the **14-day horizon will be used as the standard horizon for model comparison and evaluation**.

---

# 4. Main Analytics Questions

**AQ1.** How do daily sales vary according to weekday, month, holidays, promotions, and store characteristics?

**AQ2.** Which factors are most strongly associated with variations in daily sales?

**AQ3.** How do baseline, statistical forecasting, and machine-learning forecasting methods differ in terms of predictive performance?

**AQ4.** Which forecasting model provides the most accurate and stable performance for 14-day forecasting?

**AQ5.** How does forecast uncertainty change across forecast horizons and store types?

**AQ6.** Given current inventory, supplier lead time, and a target service level, how much inventory should each store replenish?

**AQ7.** Can forecast-driven replenishment improve stockout rates or service levels compared with a baseline inventory policy?

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
| `StockOnHandValue` | monetary unit | Current inventory | Depends on recent demand and inventory coverage |
| `ServiceLevelTarget` | % | Target product availability | Base scenario of 95%; scenario range of 90–98% |
| `HoldingCostRate` | % of inventory value | Inventory-cost simulation | Defined through documented business assumptions |
| `StockoutPenalty` | monetary unit | Lost-sales/service cost | Defined through documented business assumptions |
| `AverageUnitValue` | monetary unit/unit | Conversion to equivalent units | Store-level synthetic variable |
| `DiscountDepth` | % | Promotion intensity | 0 when `Promo=0`; positive when `Promo=1` |
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

This allows the project to generate realistic synthetic daily/weekly demand scenarios while keeping the main forecasting task grounded in the real Rossmann data.

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

Therefore, the core calculations will initially be performed in **monetary-value units**.

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
\text{current inventory monetary value}
$$

$$
ReplenishmentValue
=
\text{inventory value recommended for replenishment}
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

Missing-value indicators may be added before imputation where appropriate.

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
CompetitionAge=
Date-CompetitionOpenDate
$$

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

Same-weekday rolling statistics may also be included.

Categorical features will be encoded appropriately. Numerical scaling will only be applied to models that require it and will not be considered mandatory for tree-based models.

---

# 12. Forecasting Models

The project will follow a **model ladder** rather than training many models solely to increase model count.

## Model 0 – Seasonal Naive

The primary baseline is:

$$
\hat y_t=y_{t-7}
$$

If an advanced model cannot consistently outperform the Seasonal Naive baseline, there is insufficient evidence that the additional model complexity provides value.

---

## Model 1 – Exponential Smoothing / Holt-Winters

This classical forecasting model will be used to capture:

- level;
- trend;
- weekly seasonality.

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

A single global model will be trained using all store-day observations.

This approach allows the model to exploit information across stores and avoids the need to build 1,115 separate machine-learning models.

---

# 13. Multi-Step Forecasting Strategy

The forecast horizon is 14 days, making this a multi-step forecasting problem.

The LightGBM model will initially use a **recursive forecasting strategy**.

At forecast origin $t$:

1. calculate all features using historical data;
2. predict $\hat y_{t+1}$;
3. insert the prediction into the temporary history;
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

### Optional Extension

If recursive error accumulation becomes significant, the team may evaluate:

- direct forecasting;
- horizon-as-feature models;
- hybrid direct-recursive strategies.

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

At least **three validation windows** are planned.

---

## 14.1. Final Holdout

The latest **28 days** of labeled historical data will be reserved as a final untouched holdout set.

The final holdout will not be used to:

- select features;
- tune hyperparameters;
- select the final model;
- estimate preprocessing parameters.

After the methodology has been finalized using the validation windows, the selected model will be evaluated on the final holdout.

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

Empirical coverage will also be evaluated:

$$
Coverage=
\frac{\#\{y_t\in PI_t\}}
N
$$

This ensures that forecast uncertainty is not merely visualized on the dashboard but also quantitatively evaluated.

---

# 17. Inventory Decision Framework

Let the supplier lead time be:

$$
L
$$

The expected forecast demand value during the lead time is:

$$
D_L=
\sum_{h=1}^{L}\hat y_{t+h}
$$

Let $U_L$ denote the upper bound of cumulative demand corresponding to the selected service level.

Then:

$$
\boxed{
SafetyStock=
U_L-D_L
}
$$

and:

$$
\boxed{
ReorderPoint=
D_L+SafetyStock
}
$$

or equivalently:

$$
ROP=U_L
$$

---

## 17.1. Inventory Position

In the complete inventory model:

$$
InventoryPosition
=
StockOnHand
+
OnOrder
-
Backorders
$$

In the simplified version:

$$
InventoryPosition
\approx
StockOnHandValue
$$

because `OnOrder` and `Backorders` are not available in the Rossmann dataset.

---

## 17.2. Recommended Replenishment

$$
\boxed{
ReplenishmentValue
=
\max(0,ROP-InventoryPosition)
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

This is a decision-support recommendation rather than an SKU-level operational order quantity.

---

# 18. Business Evaluation

The forecasting model will not be evaluated solely using MAE or RMSE.

The team will conduct an **inventory simulation**.

The business KPIs include:

$$
StockoutRate
$$

$$
ServiceLevel
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

The primary business question is:

> Does a better forecast actually lead to better inventory decisions?

---

# 19. Inventory Sensitivity Analysis

Because the supply-chain variables are synthetic, the business conclusions must be tested under multiple scenarios.

| Scenario | Service Level | Lead Time |
|---|---:|---:|
| Low protection | 90% | 2–3 days |
| Base | 95% | 4–5 days |
| High protection | 98% | 6–7 days |

The expected trade-off is:

$$
ServiceLevel\uparrow
\Rightarrow
SafetyStock\uparrow
\Rightarrow
HoldingCost\uparrow
$$

while:

$$
StockoutRisk\downarrow
$$

Therefore, the system does not simply attempt to maximize the service level. Instead, it demonstrates the trade-off between inventory cost and product availability.

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
| Explainability | Feature Importance, SHAP |
| API | FastAPI |
| Dashboard | Streamlit |
| Monitoring | Evidently |
| Version control | Git, GitHub |
| Deployment | Streamlit Community Cloud / Render |
| Optional packaging | Docker |

### Spark

Spark will not be part of the project's critical path because the current dataset is not sufficiently large for distributed computing to provide a clear practical benefit.

PySpark may be implemented as an optional ETL experiment if the team wishes to demonstrate knowledge from the course lectures.

---

# 21. Proposed System Architecture

$$
\boxed{
Rossmann\ Raw\ Data
}
$$

↓

**Validation & Cleaning**

↓

**Store Data Integration**

↓

**Synthetic Data Generation**

↓

**Feature Engineering**

↓

**EDA / Descriptive Analytics**

↓

**Seasonal Naive + Exponential Smoothing + LightGBM**

↓

**Walk-Forward Validation**

↓

**Model Selection**

↓

**Forecast + Prediction Interval**

↓

**Inventory Decision Engine**

↓

**FastAPI**

↓

**Streamlit Dashboard**

↓

**Monitoring & Retraining Logic**

This architecture is also consistent with the Decision Support System structure introduced in the course, which includes data management, model management, and user-interface components.

---

# 22. Dashboard Design

The dashboard will be designed for a demand planner or store manager.

## Inputs

- Store ID
- Forecast Origin
- Forecast Horizon
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

On each simulated production day:

1. the model generates a forecast;
2. the actual observation is subsequently revealed;
3. the rolling forecasting error is updated;
4. feature distributions are compared with the training reference;
5. prediction-interval coverage is updated;
6. inventory KPIs are updated;
7. retraining conditions are evaluated.

---

## 24.1. Retraining Triggers

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

The final thresholds will be calibrated using validation data.

---

# 25. Expected Results

The project is expected to:

1. Identify important factors and patterns associated with daily store sales.
2. Develop a forecasting model that outperforms the Seasonal Naive baseline on the majority of validation windows.
3. Quantify forecast uncertainty.
4. Develop an interpretable inventory decision framework.
5. Demonstrate that a forecast-driven inventory policy can potentially improve one or more business KPIs compared with the baseline policy.
6. Deploy a functioning analytics application.
7. Develop a monitoring workflow and retraining logic.

The proposal does not assume in advance that LightGBM will necessarily be the best-performing model.

---

# 26. Success Criteria

## Analytics

The final model should outperform the Seasonal Naive baseline on the **majority of walk-forward validation windows** according to the primary metric.

## Forecast Uncertainty

The empirical prediction-interval coverage should be reasonably close to its nominal coverage level.

## Business

Forecast-driven replenishment should improve at least one important KPI relative to the baseline without causing an unacceptable deterioration in another major KPI.

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
- retraining triggers.

---

# 27. Key Limitations

### No Product/SKU Data

SKU-level forecasting cannot be directly performed using the original dataset.

### Sales is Monetary Turnover

The primary forecasting and inventory-planning calculations are therefore conducted in monetary-value units.

### Synthetic Supply-Chain Data

Lead time, inventory, unit value, and cost parameters are not real Rossmann operational data.

### Historical Dataset

The project is not intended to serve as a forecasting system for Rossmann's current operations.

### Synthetic Business Evaluation

The inventory simulation is intended to demonstrate the methodology rather than provide actual inventory-policy recommendations for Rossmann.

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
| **1** | Finalize scope, assumptions, Data Dictionary, and synthetic-data generator |
| **2** | Data cleaning, validation, integration, and EDA |
| **3** | Feature engineering + Seasonal Naive baseline |
| **4** | Exponential Smoothing + initial backtesting |
| **5** | LightGBM + tuning + walk-forward evaluation |
| **6** | Prediction intervals + inventory simulation + sensitivity analysis |
| **7** | FastAPI + Streamlit + monitoring |
| **8** | Final testing, documentation, report, slides, and demo |

---

# 30. Final Deliverables

In accordance with the Project Announcement, the team will deliver:

- a GitHub repository containing source code written by the team;
- a complete Data Dictionary;
- notebooks/scripts for data processing, EDA, and modelling;
- a synthetic data-generation module;
- the final forecasting model;
- an inventory decision engine;
- a deployed FastAPI service;
- a Streamlit demand-planning dashboard;
- a monitoring dashboard/report;
- a final report in PDF format;
- presentation slides;
- a live or recorded demonstration.

All source code will be developed by the team members, and no no-code/AutoML platform will be used.
