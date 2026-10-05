# Project Plan

This document is the implementation roadmap derived from the authoritative [project proposal](proposal.md). It describes planned work; current status is tracked separately in [PROGRESS.md](PROGRESS.md).

## Phase 0 — Repository Foundation

**Objective:** Establish a reliable repository and project-governance system.

**Main work:** Preserve the authoritative proposal; define project rules, workflow, decisions, progress tracking, data-dictionary structure, and phased execution planning.

**Deliverables:** Root governance files, project documentation, and the `plans/` workflow.

**Dependencies:** The approved project proposal.

**Acceptance criteria:** All Phase 0 documents agree with the proposal, accurately describe current status, contain valid internal links, and introduce no implementation or data artifacts.

## Phase 1 — Data Acquisition & Validation

**Objective:** Obtain and verify the Rossmann Store Sales source files without modifying raw data.

**Main work:** Document acquisition; organize `train.csv`, `test.csv`, `store.csv`, and `sample_submission.csv`; inspect schemas, date coverage, missing values, duplicates, categorical values, and invalid observations.

**Deliverables:** Reproducible acquisition instructions, an immutable raw-data layout, a validation workflow, and an initial validation report.

**Dependencies:** Phase 0 and authorized access to the Rossmann dataset.

**Acceptance criteria:** Required files are accounted for, raw inputs remain unchanged, validation results are reproducible, and dataset facts in the data dictionary are updated from observed evidence.

## Phase 2 — Data Preparation & EDA

**Objective:** Produce a clean Store × Date analytical dataset and establish the main descriptive findings.

**Main work:** Join store attributes, classify missingness, handle closed stores and verified data errors, inspect trends and seasonality, and analyze promotions, holidays, store characteristics, competition, and unusual observations.

**Deliverables:** Reproducible preparation logic, a prepared analytical dataset, EDA outputs, and documented findings and limitations.

**Dependencies:** Phase 1 validated source data.

**Acceptance criteria:** Store × Date keys are validated, preparation is reproducible, raw data remain untouched, legitimate demand spikes are retained, and EDA claims are supported by computed evidence.

## Phase 3 — Feature Engineering

**Objective:** Build reusable, forecast-origin-safe features for statistical and machine-learning models.

**Main work:** Implement the approved `phase-3-v1` calendar, holiday, promotion, store,
competition, exact-Sales-lag, and complete rolling-window contract; enforce point-in-time feature
construction. Optional same-weekday statistics are deferred under the reviewed feature contract.

**Deliverables:** Reusable feature pipeline, versioned feature specification, and leakage-focused
validation. Same-weekday statistics are not part of the Phase 3 predictor schema.

**Dependencies:** Phase 2 prepared data and agreed forecast origins.

**Acceptance criteria:** Every implemented feature has a documented source and forecast-time
availability; lag and rolling features use exact, complete, point-in-time history; future
`Customers` is excluded from production forecasting; and optional same-weekday statistics remain
deferred unless a reviewed contract change is approved.

## Phase 4 — Seasonal Naive Baseline

**Objective:** Establish the required weekly baseline for 14-day store-level forecasting.

**Main work:** Implement the seasonal-naive rule $\hat y_t=y_{t-7}$, apply the closed-store rule, generate rolling-origin predictions, and calculate evaluation metrics on open days.

**Deliverables:** Reusable baseline implementation, forecasts, and MAE, RMSE, MAPE, and WAPE results.

**Dependencies:** Phase 2 prepared data and the validation framework needed to generate time-ordered splits.

**Acceptance criteria:** Predictions are reproducible, use no future observations, cover the 14-day horizon, and provide the benchmark that all later models must justify exceeding.

## Phase 5 — Statistical Forecasting

**Objective:** Evaluate Exponential Smoothing / Holt-Winters against the Seasonal Naive baseline.

**Main work:** Model level, trend, and weekly seasonality; define robust behavior for store histories; and evaluate using the same rolling-origin windows and metrics.

**Deliverables:** Reusable statistical forecasting implementation, diagnostics, forecasts, and comparison results.

**Dependencies:** Phase 4 baseline and validated time-series inputs.

**Acceptance criteria:** Statistical forecasts are generated without leakage, evaluated consistently with the baseline, and accompanied by documented limitations and failure handling.

## Phase 6 — Global LightGBM

**Objective:** Develop the proposal's primary machine-learning candidate across all stores.

**Main work:** Train one global LightGBM model using Store, calendar, promotion, competition, lag, and rolling features; implement recursive 14-day forecasting; tune using validation data only.

**Deliverables:** Reusable training and recursive-prediction pipelines, model configuration, feature documentation, and validation forecasts.

**Dependencies:** Phase 3 features, Phase 4 baseline, and defined rolling-origin splits.

**Acceptance criteria:** The model covers all eligible stores, uses only information available at each forecast origin, excludes future `Customers`, and can reproduce every recursive step.

## Phase 7 — Walk-Forward Validation & Model Selection

**Objective:** Compare the model ladder fairly and select the final forecasting method.

**Main work:** Run at least three 14-day validation windows; report overall and segmented MAE, RMSE, MAPE, and WAPE; evaluate by horizon and open-store observations; lock methodology before touching the final holdout.

**Deliverables:** Model comparison report, segment diagnostics, selected-model rationale, and one final evaluation on the latest 28-day holdout.

**Dependencies:** Phases 4–6 and stable metric definitions.

**Acceptance criteria:** No random shuffling is used, the final holdout remains untouched during feature and model selection, and the selected model outperforms Seasonal Naive on the majority of validation windows or its limitations are reported honestly.

## Phase 8 — Forecast Uncertainty

**Objective:** Quantify forecast uncertainty and assess interval reliability by horizon.

**Main work:** Derive horizon-specific empirical residual quantiles from out-of-sample validation residuals, construct 95% prediction intervals, and measure empirical coverage.

**Deliverables:** Interval-calibration logic, prediction intervals, coverage results, and uncertainty diagnostics.

**Dependencies:** Phase 7 out-of-sample residuals and selected forecasting method.

**Acceptance criteria:** Intervals use validation residuals rather than in-sample errors, coverage is measured against the nominal level, and uncertainty is available for each relevant horizon.

## Phase 9 — Synthetic Supply-Chain / Inventory Layer

**Objective:** Add a reproducible simulated operational layer for information absent from Rossmann.

**Main work:** Generate supplier lead time, inventory value, service target, cost, equivalent-unit, discount, and coverage variables; document dependencies and assumptions; create stress-test demand scenarios with fixed seeds.

**Deliverables:** Synthetic-data generator, scenario definitions, validation results, and an updated data dictionary.

**Dependencies:** Prepared demand history and the unit rules defined in the proposal.

**Acceptance criteria:** Synthetic fields pass range, relationship, and distribution checks; generation is reproducible; and every output is clearly labeled as simulated rather than Rossmann-provided.

## Phase 10 — Inventory Simulation & Sensitivity Analysis

**Objective:** Evaluate how forecasts affect inventory-value decisions under multiple operating assumptions.

**Main work:** Calculate lead-time demand, safety stock, reorder points, inventory position, and replenishment value; compare a historical-average policy with forecast-driven policies; vary service level and lead time.

**Deliverables:** Inventory simulation, KPI comparison, sensitivity analysis, and business interpretation.

**Dependencies:** Phases 8 and 9.

**Acceptance criteria:** Results report stockout rate, service level, average inventory value, holding cost, and estimated lost sales; conclusions remain conditional on synthetic assumptions; equivalent units are never presented as actual SKU orders.

## Phase 11 — FastAPI

**Objective:** Expose the validated forecast and inventory decision workflow through a usable API.

**Main work:** Define request and response contracts, package preprocessing and prediction logic, validate inputs, support cached predictions where useful, and document local operation.

**Deliverables:** FastAPI application, API documentation, tests, and reproducible startup instructions.

**Dependencies:** Selected model, calibrated intervals, and inventory decision logic from Phases 7–10.

**Acceptance criteria:** The API returns store-level forecasts, uncertainty, and inventory-value recommendations for supported inputs without manual notebook execution and handles invalid inputs predictably.

## Phase 12 — Streamlit Dashboard

**Objective:** Provide a demand-planning interface for historical analysis, forecasts, uncertainty, and inventory guidance.

**Main work:** Implement store and forecast controls, historical views, forecast intervals, model explanations, inventory recommendations, and business alerts.

**Deliverables:** Streamlit dashboard, usage documentation, and interface validation.

**Dependencies:** Phase 11 API or equivalent reusable application services.

**Acceptance criteria:** A user can select a store and scenario, inspect forecasts and uncertainty, and receive clearly labeled inventory-value guidance without running notebooks.

## Phase 13 — Monitoring & Pseudo-Production

**Objective:** Demonstrate monitoring and retraining logic without assuming a live Rossmann feed.

**Main work:** Reveal holdout observations sequentially; monitor feature distributions, rolling errors, interval coverage, stockout rate, service level, inventory value, and replenishment frequency; calibrate retraining triggers from validation evidence.

**Deliverables:** Pseudo-production workflow, monitoring dashboard or report, drift summaries, and retraining-trigger logic.

**Dependencies:** Phases 7–12 and reserved sequential evaluation data.

**Acceptance criteria:** Each simulated day forecasts before revealing its actual value, monitoring distinguishes data, performance, and business drift, and no claim of live production data is made.

## Phase 14 — Final Evaluation, Documentation, Report & Demo

**Objective:** Integrate and communicate the complete analytics lifecycle and its limitations.

**Main work:** Run final checks, reconcile code and documentation, finalize the report and slides, prepare the live or recorded demonstration, and verify reproducibility and deployment.

**Deliverables:** Final repository, Data Dictionary, report PDF, presentation, demonstration, deployed application, and consolidated evaluation results.

**Dependencies:** Completion and review of all preceding phases.

**Acceptance criteria:** Deliverables agree with implemented behavior; claims are supported by results; synthetic and real data are clearly distinguished; limitations are explicit; and the end-to-end workflow operates without manual notebook execution.
