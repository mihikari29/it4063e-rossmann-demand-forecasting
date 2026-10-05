# Phase 2 — Data Preparation & Exploratory Data Analysis

## 1. Objective

Create a modelling-ready, reproducible understanding of the Rossmann historical data while preserving chronological integrity and without introducing forecast leakage. Phase 2 will explain what the data contain, how store-level monetary Sales behaves over time, how observed store, calendar, and promotion variables relate to Sales, what preparation policies the verified data require, which observations should be retained, and which decisions must pass to Phase 3 feature engineering.

Phase 1 is complete. The validated raw snapshot is under data/raw/rossmann/; its provenance, checksums, measured facts, and four warning dispositions are recorded in the Phase 1 documentation. The four policy approvals below are recorded before implementation. No Phase 2 preparation, analysis, notebooks, or datasets have been created yet.

## 2. Scope and Phase Boundaries

### A. Data preparation decisions

- Re-read the four immutable source files and confirm the documented hashes before processing.
- Parse dates and types deterministically; preserve source fields and values.
- Join store metadata to store-day rows with an asserted many-to-one relationship and unchanged row count and Store × Date keys.
- Profile the four Phase 1 warnings and the six metadata fields with missing values; apply only the approved source-preserving dispositions below.
- Produce a source-meaning-preserving joined analytical view with sparse historical rows. Do not fill the shared date gap, impute missing test Open, drop closed days, or remove open/zero-sales rows.
- Document any proposed treatment, evidence, alternatives, and consequences before applying a transformation that changes row inclusion or values.

### B. Descriptive and diagnostic EDA

- Answer proposal questions about sales distributions and time patterns, weekday, month and year, promotion, holidays, store attributes, competition, Promo2, store heterogeneity, and anomalies.
- Use descriptive summaries, segment comparisons, time plots, autocorrelation diagnostics, and a small deterministic set of representative stores.
- Describe association and observed patterns only. EDA does not establish causal effects or forecasting performance.
- Document important findings and limitations with reproducible summaries and report-quality figures.

### C. Deferred to Phase 3 or later

- Model feature construction, including lag and rolling predictors, target encoding, and feature availability rules at forecast origin.
- Final choices for model-training eligibility, temporal split boundaries, model selection, and forecast metrics.
- Imputation or calendar reindexing policies that require forecast-origin or model-specific decisions, except to record a justified Phase 2 disposition and pass it forward.
- Forecast models, tuning, backtests, causal promotion claims, inventory simulation, and synthetic operational data.

## 3. Inputs and Invariants

Inputs are train.csv, test.csv, store.csv, and sample_submission.csv, identified by the file sizes and SHA-256 hashes in docs/DATA_ACQUISITION.md. The official Kaggle test file contains future covariates but no Sales or Customers; sample_submission.csv contains placeholder submission values and is not labelled history.

The following remain fixed:

- Unit of analysis: Store × Date.
- Target: monetary store-level Rossmann Sales, not physical units or SKU demand.
- Raw data are immutable and never rewritten by preparation or EDA.
- Customers is historical real data, but future actual Customers is unavailable as a production forecasting input.
- No random row shuffling or random train/test split.
- No future actual Sales or Customers in future-date analysis, preparation, or predictors.
- Full historical train.csv may be summarized descriptively, but estimates intended as model features must later be recomputed using only information available at each forecast origin.
- Primary forecast metrics in later phases use Open = 1; known closed dates receive zero operational forecasts under the proposal’s business rule.

## 4. Preparation Investigations and Decision Records

For every policy below, record the question, observed evidence, options considered, chosen disposition, affected rows, and impact on chronological coverage. No row or value changes until this record exists. Preserve the original four files and hashes.

### 4.1 Shared date gap

Phase 1 found 180 stores each missing the same 184 days, 2014-07-01 through 2014-12-31, for 33,120 absent store-days in total.

Investigate and report:

1. The exact affected Store IDs and whether each has observations immediately before 2014-07-01 and after 2014-12-31, including its observed coverage boundaries.
2. Whether all affected stores share the same contiguous gap and whether unaffected stores cover those dates.
3. Whether any source field supplies Open or closure information for absent Store × Date rows. An absent source row has no observed Open value; do not infer a closure from absence.
4. Whether these omissions change store eligibility, observed history length, seasonal plots, autocorrelation, decomposition, or potential later validation windows.
5. The canonical prepared history remains sparse observed rows. A separate diagnostic calendar-coverage index may be generated for gap inspection only, with absent Sales/Open explicitly missing; it is never a replacement modeling table and never inserts zero Sales.

The approved disposition is to retain sparse source rows and optionally generate a separate diagnostic coverage index. Record this in the Phase 2 findings. Any future rolling statistic or split must recognize that a 184-day absence is not 184 zero-sales observations and must not bridge the gap as if dates were consecutive.

### 4.2 Open store with zero Sales

Phase 1 found 54 rows across 41 stores where Open = 1 and Sales = 0; 52 also have zero Customers, while 2 have positive Customers.

Inspect the Store, Date, Customers, Promo, StateHoliday, SchoolHoliday, and surrounding available store-days for all 54 rows. Compare patterns across affected stores without replacing or removing records. Classify each as plausible source behavior, unresolved anomaly, or confirmed data issue only when evidence supports the classification. Preserve all rows unless a documented correction is approved; any correction belongs in a separate reproducible derived output with an audit trail.

### 4.3 Missing test Open

Phase 1 found 11 missing Open values in test.csv, all for Store 622. Inspect Store 622’s historical Open values by weekday, observed closure patterns, the 11 future dates’ known calendar and promotion covariates, and surrounding future Open values that are actually present.

The approved default is to preserve source Open nulls. Investigate historical Store 622 schedule evidence and known future calendar/promotion context. The implemented candidate rule may resolve a missing status only when at least 30 historical observations for the same store and exact `DayOfWeek`, `Promo`, `StateHoliday`, and `SchoolHoliday` context are unanimous; label every derived status uncertain. Keep this as a separate audit output and leave source `Open` null. If a row does not meet that criterion, leave its resolution missing. Do not use future Sales or Customers, and report the operational consequence for Phase 3/forecast delivery.

### 4.4 Store metadata missingness

Treat each field and missingness pattern separately:

| Field | Phase 1 evidence | Phase 2 investigation |
|---|---|---|
| CompetitionDistance | 3 missing of 1,115 | Identify affected stores; retain missing values and do not infer a structural cause absent evidence. |
| CompetitionOpenSinceMonth | 354 missing; all paired with missing year | Identify affected stores; retain both fields and classify the cause as unexplained unless evidence supports a narrower interpretation. |
| CompetitionOpenSinceYear | Same 354 paired missing rows | Diagnose jointly with month, retain original nulls, and do not invent an opening date. |
| Promo2SinceWeek | 544 missing, exactly for Promo2 = 0; present for all 571 participants | Preserve as structural non-participation missingness; do not replace with week zero or conflate with missing participant data. |
| Promo2SinceYear | Same structural pattern as week | Preserve original nulls and participation relation. |
| PromoInterval | Same structural pattern as week/year | Preserve original nulls; document observed schedules without assuming unobserved intervals. |

For each field report count, rate, affected Store IDs in local diagnostics, overlap with other missing fields, relationship to Promo2, and classification supported by the evidence. Do not impute, add model-oriented indicators, or use complete-case deletion. Diagnostic classifications must not overwrite source columns. Distinguish known structural Promo2 absence, unexplained paired competition-date absence, and isolated missing distance.

### 4.5 Closed stores and the three row roles

Investigate historical Open, Sales, and Customers jointly, including zero and positive values, weekday/calendar context, and continuity. Phase 1 observed no positive Sales or Customers when Open = 0, 54 open/zero-sales rows, and 52 open/zero-customer rows among those.

Maintain the following distinctions in the prepared data design:

- **Rows retained in history:** retain all valid observed source rows, including closed days, because they describe the store calendar and support later operational forecasts.
- **Rows eligible for model training:** Phase 2 may prepare an explicitly labelled analytical view and compare distributions by Open; final target-row eligibility is a Phase 3 modeling decision. Do not discard closed rows from the base prepared table. Carry forward the proposal’s open-day primary target/evaluation rule.
- **Rows used for primary evaluation:** later model evaluation is limited to actual Open = 1 rows; report any separate calendar-level operational assessment distinctly.
- **Operational post-processing:** the proposal sets forecasts to zero on known closed dates. Missing future Open is not “known closed” and needs the explicit policy in Section 4.3.

Do not make a zero-sales or zero-customers source rewrite to enforce an operational forecast rule.

### 4.6 Test-subset metadata coverage

Phase 1 found 259 stores in store.csv that do not appear in test.csv, while all 856 test stores
match exactly one metadata row and the many-to-one join preserves the test row count. Compare the
test Store set with the train and metadata Store sets, record the expected cohort difference, and
confirm the same join invariants in any prepared output. Do not delete unused metadata rows from the
source or describe this expected subset difference as a join failure.

## 5. Descriptive and Diagnostic EDA Work

Use train.csv for labelled historical Sales analysis. Use test.csv only to inspect available future covariates, schema, and operational coverage; do not use it to infer future target behavior, tune historical conclusions, or represent its sample-submission Sales values as observed data. Report sample sizes and denominators for every aggregation, particularly open-day-only summaries.

Required EDA topics and proposed outputs:

| Question | Variables / aggregation | Diagnostic or report figure | Why it matters |
|---|---|---|---|
| What is the overall target distribution? | Sales; all rows and Open = 1 separately; zeros and quantiles | Histogram or ECDF plus compact quantile table | Shows scale, skew, zero mass, and tail without treating extremes as errors. |
| How does total and typical Sales change over time? | Daily sum, median, and store-level distribution bands; label coverage | Daily line with robust bands and missing-coverage annotation | Separates aggregate movement from changing store coverage. |
| Is there weekly seasonality? | Daily totals and per-store normalized weekday summaries | Weekday profile and representative-store time plots | Establishes weekly shape for later forecasting context. |
| How do weekdays differ? | DayOfWeek; count, mean, median, quantiles, open-day denominator | Ordered point/range or box plot by weekday | Describes day-level variation without claiming a causal weekday effect. |
| How do month and year patterns vary? | Date month/year; calendar aggregates and coverage | Monthly seasonal profile and yearly trend facets | Shows within-year patterns and year-to-year changes. |
| How are promotions associated with Sales? | Promo; open-day Sales distributions and store-aware summaries | Paired distribution plot with counts and robust summaries | Quantifies observed association while acknowledging confounding and store mix. |
| How do state and school holidays align with Sales? | StateHoliday, SchoolHoliday; open-day summaries | Small-multiple distributions with category counts | Describes holiday-period behavior and sparse categories. |
| How do store attributes relate to Sales? | StoreType, Assortment; store-level and open-day summaries | Faceted distribution/range plot | Shows heterogeneity while avoiding pseudoreplication from treating days as independent stores. |
| How does competition distance relate to stores? | CompetitionDistance; store-level open-day Sales summaries | Scatter with a restrained smooth or binned medians | Describes cross-store association and missingness; does not infer competition impact. |
| How does Promo2 participation relate to Sales? | Promo2; store-level summaries and time coverage | Grouped distribution plus participation counts | Separates participation context from promotion dates and missing schedule fields. |
| How heterogeneous are stores? | Store-level open-day mean/median/quantiles, variability, and coverage | Distribution of store summaries and ranked range plot | Prevents aggregate totals from hiding store differences. |
| What differs among high-, middle-, and low-volume stores? | Reproducible open-day store volume bands; calendar and promo profiles | Segment comparison panels | Provides interpretable volume segments for planning and later evaluation design. |
| Are there unusual Sales spikes or drops? | Store-day Sales, neighboring observed days, open/promo/holiday context | Annotated candidate table and selected time plots | Supports review while retaining legitimate promotion or holiday spikes. |
| What happens around closures? | Consecutive observed Open, Sales, Customers around known closures/reopenings | Event-centered line panels for selected stores | Distinguishes observed closure patterns from missing calendar rows. |
| Where are the missing values? | Six metadata fields plus test Open, by file/store/condition | Missingness matrix or field-specific bar/table | Supports distinct, evidence-based preparation policies. |
| What serial structure remains? | Representative-store historical Sales on observed dates; weekly ACF and optional decomposition | ACF and decomposition for eligible uninterrupted examples, with gap warnings | Describes diagnostics for later time-series work without choosing a model. |

Use decomposition only for a clearly labelled diagnostic example with adequate, contiguous coverage. Do not fill gaps to make a decomposition run. Keep plots descriptive; do not perform model selection, forecast scoring, causal tests, or feature importance analysis in Phase 2.

## 6. EDA Granularity and Representative Stores

Do not generate one plot per store. Use whole-sample aggregates, store-level distributions, segment-based comparisons, and a small representative set.

After inspecting the data, select representatives reproducibly:

1. Calculate each store’s open-day mean Sales and number of observed open days using historical train.csv; publish the definition and coverage requirement before selecting examples.
2. Identify low-, median-, and high-volume candidates by nearest distance to the 10th, 50th, and 90th percentiles of the store-level open-day mean. Do not publish fixed IDs before running this method.
3. Add candidates to cover each observed StoreType, Assortment, and Promo2 state where possible. Choose the candidate nearest its stratum’s median open-day mean Sales; resolve ties by ascending Store ID. Document unavailable or overlapping strata.
4. Add stores tied to documented anomalies (the shared date gap or open/zero-sales rows) for diagnostic plots only, and label why each was selected.
5. Deduplicate the combined set, keep it small, and report the selection rule, IDs, and coverage in the generated summary. Never select examples by visual appeal after seeing the plots.

For store comparisons, distinguish store-level sample size from the number of store-day rows. Use per-store summaries or uncertainty-aware displays where useful so long-running stores do not silently dominate every segment statistic.

## 7. Data Outputs, Formats, and Reproducibility

### Raw

data/raw/rossmann/ remains the immutable official source. Verify recorded hashes before each pipeline run and never write into this directory.

### Interim

Phase 2 should introduce data/interim/ only when the pipeline is implemented. Its role is a reproducible, parsed and metadata-joined analytical table that preserves source meaning, row coverage, missing values, and source keys. Store-day train and test covariates should remain distinguishable; test must not be represented as labelled history. Keep store metadata separate unless a join is required for an analysis.

Use Parquet for typed, compressed local intermediate tables. Add PyArrow as a project dependency only after confirming compatibility with the supported Python environment. If PyArrow is unavailable or incompatible, stop and report the blocker for review; do not silently switch the canonical output format to CSV. Do not create redundant copies of the same joined data.

### Processed

Do not introduce data/processed/ during Phase 2 unless an output with a distinct, documented consumer and schema is justified. Model-specific matrices and feature sets belong to Phase 3 and must not be created here.

### Reproducibility

Preparation must be callable from a thin script and reusable src/ functions, accept portable paths, validate join cardinality and output schema, and write only to ignored derived-data paths. EDA summaries and figures must be regenerated from those functions and notebooks with fixed seeds where sampling is used. Record source hashes, command, dependency versions, row counts, and output schema in a concise report. Do not manually edit generated data.

## 8. Historical Train and Kaggle Test Roles

- train.csv is the only historical labelled source and the only source of observed target Sales.
- test.csv is a later Kaggle future-covariate period without Sales or Customers. It can support schema/operational preparation, including inspection of the missing Open values, but cannot provide labels, measure forecast accuracy, or tune EDA decisions about future targets.
- sample_submission.csv is a submission template; its Sales column is not observed sales.
- Academic forecasting validation and the final holdout must later be carved chronologically from labelled train.csv, following the proposal. Phase 2 must not select or tune model windows.
- Keep test rows identifiable as test in every derived output. Never concatenate test as if it had historical target observations.

## 9. Leakage and Interpretation Boundaries

- Preserve source order and dates; no random splitting or shuffled analysis tables.
- Do not use future actual Sales or Customers for any future-date result or predictor.
- Historical full-sample plots are explicitly descriptive. Any statistic later used as a predictor, scaler, imputation value, encoding, threshold, or representative model input must be estimated from training history available at that forecast origin in Phase 3 or later.
- Diagnostic ACF/decomposition and lagged visual overlays may use historical outcomes only and must be labelled diagnostics, not implementable model features.
- Summaries of Promo, holidays, store type, assortment, competition, or Promo2 describe association, not causal effects.
- Never interpret turnover as item units or infer SKU-level demand.
- Preserve observations with unusual but valid high Sales; flag for review and document context.

## 10. Notebook and Source-Code Strategy

Critical logic belongs in reusable modules under src/rossmann_forecasting/; notebooks provide ordered exploration and presentation, not the only copy of cleaning or metric logic. Thin scripts should expose reproducible preparation and EDA report commands. Keep plots and tabular summaries in small reusable analysis functions that notebooks call.

Minimal numbered notebook proposal:

1. notebooks/01_data_preparation_diagnostics.ipynb — load source through reusable preparation functions, inspect warning investigations and missingness decisions, verify row/key preservation.
2. notebooks/02_exploratory_data_analysis.ipynb — generate the planned descriptive summaries, diagnostic time-series views, representative-store comparisons, and report figures.

Each notebook should state purpose, source hash, command/environment, and expected generated outputs. Keep execution deterministic; commit concise, reviewable notebooks with cleared transient outputs where practical, while writing generated figure exports and tables to ignored report paths. Re-running from a clean kernel must regenerate the same summaries and figures within documented numeric/visual tolerances.

## 11. Visualization Plan

Create only figures that answer a stated question. Diagnostic figures support data and series inspection; report-quality figures use stable labels, units, captions, denominators, and source coverage annotations.

| Figure | Business question | Variables and aggregation | Proposed type | Role |
|---|---|---|---|---|
| Sales distribution | What is the target scale and tail? | Sales overall and open-only; counts, quantiles, zero mass | ECDF plus compact histogram or box summary | Report |
| Daily sales over time | How does observed turnover change? | Daily sum and median with observed row coverage | Line with robust bands and gap annotation | Report |
| Weekday profile | Which weekdays have different observed levels? | DayOfWeek × open-day median/quantiles | Ordered point-range or box plot | Report |
| Monthly/yearly profile | Are within-year patterns stable? | Calendar month × year, open-day median or sum with denominators | Seasonal line/facet plot | Report |
| Promotion comparison | How do open-day values differ by Promo? | Promo × open-day Sales distribution and store-aware summary | Paired distributions and summary intervals | Report |
| Holiday comparison | How do observed holiday dates differ? | StateHoliday / SchoolHoliday × open-day Sales; category counts | Small-multiple box/point plots | Diagnostic/report |
| Store segment comparison | How heterogeneous are formats and assortments? | StoreType, Assortment; per-store statistics | Faceted distribution plot | Report |
| Competition association | How does store Sales vary with available competition distance? | Store-level open-day Sales summaries and CompetitionDistance | Scatter or binned medians, missingness marked | Diagnostic/report |
| Promo2 comparison | How do participating stores compare descriptively? | Promo2 × per-store open-day Sales summary | Grouped distribution with counts | Report |
| Store heterogeneity | How spread are store-level volume and variability? | Per-store mean/median/quantiles/coverage | ECDF or ranked dot/range plot | Report |
| Closure event | What surrounds known open/closed transitions? | Sales, Customers, Open by relative observed date for selected stores | Annotated event-centered line | Diagnostic |
| Gap pattern | Are omissions shared and how do edges appear? | Store × Date coverage matrix/summary, no target fill | Coverage heatmap or compact timeline matrix | Diagnostic |
| ACF/decomposition | What temporal structure appears in eligible history? | Selected contiguous store Sales history | ACF and additive decomposition panels | Diagnostic |

Use clear monetary-value labels for Sales, identify the open-day filter, show sample counts, and avoid axes or normalization that imply physical units or causal impact.

## 12. Future Test Strategy

Use tiny constructed fixtures wherever possible. Add tests for:

- raw inputs and their checksums remain unchanged after preparation;
- deterministic date parsing and stable, documented dtypes;
- unique Store × Date keys remain unique;
- metadata joins assert many_to_one, preserve row count, and fail on duplicate metadata keys;
- missing fields and missing test Open are represented according to the approved policy, never silently filled;
- the shared absent-date block stays absent or explicitly missing in a calendar representation, never becomes zero Sales by default;
- all observed rows, including closed rows and open/zero-sales rows, remain in the base history;
- train and test are kept separately labelled and test never gains fabricated target values;
- output schemas and column order are deterministic;
- representative-store selection is deterministic and documents criteria;
- summary functions use declared denominators and do not mutate inputs.

Tests must not depend on the full Rossmann files or copy real rows into fixtures. Phase 2 implementation will run pytest and configured Ruff checks and record actual results.

## 13. Expected Files and Directories for Phase 2 Implementation

The following are proposals for implementation after this plan is reviewed; none is created by this planning task.

### Create and track

- src/rossmann_forecasting/data/preparation.py — typed parsing, read-only joins, gap/missingness diagnostics, policy-aware derived view construction.
- src/rossmann_forecasting/analysis/__init__.py and a small EDA summaries/figures module — reusable grouped summaries and plot builders.
- scripts/prepare_data.py and scripts/run_eda.py — thin reproducible entry points.
- notebooks/01_data_preparation_diagnostics.ipynb and notebooks/02_exploratory_data_analysis.ipynb — reviewable, numbered exploration.
- tests/test_data_preparation.py and tests/test_eda_summaries.py — fixture-based tests.
- docs/PROGRESS.md, docs/DATA_VALIDATION.md, docs/DATA_DICTIONARY.md, and docs/EDA_FINDINGS.md — update only with measured preparation and EDA outcomes; README only if user-facing commands or layout change.
- plans/active/phase-2-data-preparation-eda.md — this execution plan.

### Create locally and keep ignored

- data/interim/ — only the necessary parsed/joined Parquet outputs; stop and report if PyArrow is incompatible.
- data/interim/test_open_resolution.parquet — separate, auditable historical exact-context consensus candidates; source `test.parquet` remains unchanged.
- reports/eda/ — generated charts, summary tables, selection manifests, and run metadata.
- Jupyter checkpoints, caches, and temporary exports.

No data/processed/, model features, model binaries, or synthetic data are planned for Phase 2. If generated figure/table paths need ignore coverage, update .gitignore during implementation. Raw files, credentials, and large generated outputs must not be staged.

## 14. Acceptance Criteria

Phase 2 is complete only when all of the following are evidenced:

- [x] The four Phase 1 warnings are investigated and dispositioned, including the shared gap, all open/zero-sales rows, missing test Open, and unused test metadata stores.
- [x] Missingness for each of the six store metadata fields is separately profiled and treated; Promo2 non-participant missingness remains distinct from unexplained missingness.
- [x] Preparation decisions, alternatives, affected counts, and limitations are documented before value-changing or row-changing rules are applied.
- [x] Raw files remain unchanged and their hashes match the recorded source snapshot.
- [x] Reusable preparation functions and thin commands exist; no critical preparation logic is notebook-only.
- [x] Train and test retain their separate labelled/future-covariate roles.
- [x] Store × Date keys and many-to-one metadata join integrity are checked in the output.
- [x] Base historical data retain closed rows and valid unusual observations; no automatic zero fill of the 184-day gap or deletion of open/zero-sales rows occurs.
- [x] Outputs and schemas are deterministic and reproducible from documented commands.
- [x] Proposal-required descriptive questions are addressed by supported summaries and figures.
- [x] Representative-store selection follows a documented deterministic rule and is not cherry-picked.
- [x] Important EDA findings, denominators, limits, and remaining Phase 3 decisions are documented.
- [x] No random split, future-target use, future-Customers use, causal claim, forecasting model, model selection, or Phase 3 feature pipeline is introduced.
- [x] Fixture tests pass; lint, formatting, link, and relevant scope checks pass.
- [x] Derived datasets and large generated artifacts remain ignored or have an explicit reviewed reason to be version-controlled.
- [x] docs/PROGRESS.md, Phase 2 outputs, and this plan agree with the actual repository state.

## 15. Approved Policy Decisions

The user reviewed and approved these policies before implementation:

1. The canonical prepared historical dataset remains sparse observed source rows. A separate calendar-coverage diagnostic may be generated, but no gap rows are inserted into the canonical dataset and no absent Sales/Open values are filled with zero.
2. Preserve raw and prepared source `Open` nulls, including Store 622's 11 test rows. Investigate historical and known-covariate evidence; create a separate derived resolution only if a deterministic forecast-time-available rule is supported. Otherwise retain missingness.
3. Do not impute unexplained competition metadata. Keep the Promo2=0 structural null pattern intact; classify missingness only as far as evidence permits. No model-specific missingness indicators or treatment are introduced.
4. Canonical local interim outputs use Parquet via PyArrow. If compatibility or operation fails, stop and report rather than silently using CSV.

These decisions authorize source-preserving preparation and diagnostics only; they do not authorize row deletion, unsupported imputation, or model implementation.
