# Architecture and Methodology Decision Log

Only durable decisions supported by the authoritative proposal or explicitly approved phase design
belong here. Changes require a new or superseding decision record rather than a silent rewrite.

## ADR-001 — Forecast Granularity

**Status:** Accepted

**Decision:** Forecast at the Store × Date level.

**Reason:** Rossmann provides daily observations for stores, and this is the finest demand granularity supported by the selected data.

**Consequences:** Data keys, features, forecasts, metrics, and dashboard views must preserve store-day granularity.

## ADR-002 — Forecast Target

**Status:** Accepted

**Decision:** Use Rossmann `Sales` as the store-level monetary demand signal.

**Reason:** `Sales` is the available historical outcome associated with store demand, but it represents turnover rather than physical quantity.

**Consequences:** Forecasts and core inventory calculations use monetary-value units and must not be described as product-unit demand.

## ADR-003 — No SKU-Level Forecasting

**Status:** Accepted

**Decision:** Do not claim SKU-level forecasting or production SKU replenishment capability from the Rossmann dataset.

**Reason:** The dataset contains neither product identifiers nor physical quantities sold.

**Consequences:** Equivalent units may appear only as explicitly simulated illustrations based on a synthetic average unit value.

## ADR-004 — Primary Forecast Horizon

**Status:** Accepted

**Decision:** Use 14 days as the primary forecast horizon for model comparison and evaluation.

**Reason:** The proposal defines two weeks as the standard planning horizon while allowing optional 7-day and 28-day dashboard views.

**Consequences:** Validation windows and primary comparisons must produce 14 forecast steps and should report performance by horizon.

## ADR-005 — Synthetic Operational Layer

**Status:** Accepted

**Decision:** Simulate supply-chain and inventory fields absent from Rossmann and keep them explicitly separated from real data.

**Reason:** Lead time, inventory position, unit value, and cost inputs are required for decision support but are unavailable in the source dataset.

**Consequences:** Generation rules, assumptions, dependencies, ranges, and fixed seeds must be documented. Business conclusions remain conditional on those assumptions.

## ADR-006 — Forecasting Baseline

**Status:** Accepted

**Decision:** Use Seasonal Naive with a seven-day lag as the required primary baseline.

**Reason:** Daily store sales exhibit weekly seasonality, and advanced models must demonstrate value over a transparent benchmark.

**Consequences:** Every candidate model must be evaluated against the same baseline using the same time-ordered windows and metrics.

## ADR-007 — Main Machine-Learning Strategy

**Status:** Accepted

**Decision:** Use one global LightGBM model across stores as the primary machine-learning candidate rather than 1,115 independent machine-learning models.

**Reason:** A global model can share information across stores and use store, calendar, promotion, competition, lag, and rolling features efficiently.

**Consequences:** Store identity and store characteristics become model inputs. LightGBM must still earn final selection through validation.

## ADR-008 — Validation Strategy

**Status:** Accepted

**Decision:** Use rolling-origin / walk-forward validation and keep the latest 28 labeled days as a final untouched holdout during feature and model selection.

**Reason:** Time-ordered evaluation represents forecasting conditions and prevents future information from contaminating model selection.

**Consequences:** Random shuffling is prohibited. At least three 14-day validation windows are planned, primary metrics use `Open = 1`, and the final holdout is evaluated only after the methodology is locked.

## ADR-009 — Spark Is Optional

**Status:** Accepted

**Decision:** Keep Spark off the critical path; PySpark may be used only as an optional ETL demonstration.

**Reason:** The dataset is manageable on personal computers and does not require distributed processing for the proposed workflow.

**Consequences:** Core deliverables must not depend on Spark infrastructure or an optional PySpark experiment.

## ADR-010 - Python Environment and Packaging

**Status:** Accepted

**Decision:** Use Python 3.14 and `pyproject.toml` as the supported development baseline and single
hand-maintained source for package metadata, dependencies, command entry points, pytest, and Ruff.
Keep acquisition and development tools in optional extras.

**Reason:** The available Python 3.14.5 environment supports the current stable Phase 1 packages.
A standard `src/` package and one configuration file keep reusable logic importable and avoid
duplicated dependency lists.

**Consequences:** Contributors create a repository-local virtual environment and install the
appropriate extras. Later-phase dependencies are added only when needed. Deployment-specific lock
or constraints files may be generated later instead of manually duplicating requirements.

## ADR-011 - Official, Immutable Raw Data

**Status:** Accepted

**Decision:** Acquire Rossmann files only from the official Kaggle competition into the ignored
`data/raw/rossmann/` directory. Acquisition is atomic and refuses overwrite; validation is
read-only and checks file hashes.

**Reason:** A single authoritative source and immutable local files make provenance reproducible
without committing restricted data or credentials.

**Consequences:** Each contributor must obtain authorized competition access. A source refresh
requires explicitly moving the existing raw directory aside and rerunning acquisition and
validation. Derived data must be written elsewhere in a later phase.

## ADR-012 - Phase 3 Point-in-Time Feature Contract

**Status:** Accepted for Phase 3 implementation; contract version `phase-3-v1`.

**Decision:** Use one ordered 29-predictor schema for historical training and inference. Preserve
`Store` unchanged as both a key and later categorical model input; keep Date key-only and Sales as
label/history source. Dynamic target-history features use exact calendar dates, complete trailing
windows, and origin-censored actual history with optional earlier recursive predictions. Missing
exact history stays null. Competition opening status/age use month-level semantics, and invalid or
missing metadata is not imputed. Open-resolution candidates remain audit-only. The latest 28
labeled days are protected by a holdout firewall.

**Reason:** This preserves source precision and sparse coverage while making target-history
availability explicit for recursive forecasting; it also prevents train/inference schema drift and
future actuals from leaking through precomputed historical rows.

**Consequences:** The detailed, versioned field manifest and output roles are defined in
[`FEATURE_CONTRACT.md`](FEATURE_CONTRACT.md). Phase 3 adds no model-specific encoding, scaling,
same-weekday features, imputation, or forecasting model. Any later contract change must be reviewed,
regenerated, and must not be selected using final-holdout outcomes.

## ADR-013 - Phase 4 Seasonal Naive Evaluation Contract

**Status:** Accepted by explicit user approval on 2026-10-05.

**Decision:** Implement the weekly Seasonal Naive baseline on exactly three non-overlapping,
chronological 14-day development windows: `validation_1` (origin 2015-05-22, targets 2015-05-23
through 2015-06-05), `validation_2` (origin 2015-06-05, targets 2015-06-06 through 2015-06-19),
and `validation_3` (origin 2015-06-19, targets 2015-06-20 through 2015-07-03). For each Store and
origin, forecast the exact same-Store calendar date seven days earlier. Horizons 1–7 use actual
Sales only through the origin; horizons 8–14 recursively use the already generated raw forecast
from seven days earlier. Teacher forcing is prohibited. Missing exact weekly history remains
unavailable/null, with no prior-row fallback, interpolation, imputation, or zero fill. For each
Store with at least one observed target key in a window, construct internal forecast states for all
14 calendar horizons, but emit/evaluate only source-observed Store × Date target keys; internal
states have no target labels and may feed later recursive horizons.

Keep pure `raw_baseline_forecast` separate from post-forecast `operational_forecast`: known source
`Open == 0` routes operational output to zero only after raw generation; `Open == 1` retains the raw
forecast; unknown Open remains unresolved and is not treated as closed. `Open_resolved` is not
source truth. Attach actual Sales, source Open, and the validation label only after raw forecast
generation. Primary metrics use observed source `Open == 1` targets with actual Sales and an
available raw forecast. MAE is primary; RMSE, MAPE, and WAPE are secondary under the approved
metric contract. MAPE excludes zero-actual eligible rows only from MAPE (no epsilon) and reports
the excluded count and coverage. WAPE is unavailable/null with a reason when the actual denominator
is zero. Report availability coverage with explicit numerators and denominators. The final holdout,
2015-07-04 through 2015-07-31, is not forecast or evaluated during Phase 4.

**Reason:** The fixed weekly rule is a transparent benchmark for the approved 14-day horizon. Exact
calendar lookup and origin-censored recursion preserve time-series integrity and sparse source
coverage; separating raw predictions, operational routing, and labels prevents leakage and keeps
model quality distinct from the closed-store business rule.

**Consequences:** Results are development-only and are reported by validation window, pooled over
eligible observations, and by horizon. Missing raw forecasts remain visible in output and coverage
summaries rather than silently changing the metric population. No validation window, missing-history
rule, metric, or routing rule may be changed based on final-holdout outcomes. Phase 4 remains under
review until its implementation and results are externally reviewed and explicitly closed.
