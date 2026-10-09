# Phase 12 — Streamlit Dashboard Design

**Phase status:** PLANNED. M1 design and implementation scope are APPROVED / AUTHORIZED;
M1 is IMPLEMENTED / UNDER REVIEW with evidence in §11. M2–M4 remain PLANNED / NOT AUTHORIZED.
**Date:** 2026-10-09. **Authority:** The original design task authorized documentation and a draft
PR. The subsequent Technical Lead task authorizes M1 implementation, a compatible optional
Streamlit dependency, commit, push and a draft PR; it does not authorize merge, deployment,
artifact distribution, M2–M4 or Phase 13.
**Implementation branch:** `feat/phase-12-streamlit-m1`, directly from fetched `origin/main`
`9b4ab7f54abff0ca1abfe8b6c547de960c8be8b1`; no stacked integration dependency.

## 1. Verified baseline and design boundary

The initial worktree was clean on the already merged `docs/phase-11-closeout` branch at
`5cbb7ff10eff51430aeab7d288119ccb3d3653dc`. Git fetch and the live GitHub main-branch API agreed
on the base above. The live all-PR collection contained 27 PRs, all merged, with none open.
PR #26 integrated services at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; PR #27 integrated
formal Phase 11 closeout at the current main SHA. The local `main` branch was behind and was
not used as the original design base. Phase 12 was unimplemented at that audit baseline; Phase 13
remains unauthorized.

Audit sources, in project precedence order: [proposal](../../docs/PROPOSAL.md),
[accepted decisions](../../docs/DECISIONS.md), [roadmap](../../docs/PROJECT_PLAN.md),
[progress](../../docs/PROGRESS.md), [README](../../README.md), [agent contract](../../AGENTS.md)
and [workflow](../../docs/WORKFLOW.md). Field meaning comes from the
[dictionary](../../docs/DATA_DICTIONARY.md) and [feature contract](../../docs/FEATURE_CONTRACT.md).
The [completed Phase 11 plan](../completed/phase-11-application-services.md) supplies the
accepted reader/service/API boundary. Interfaces were checked against
[contracts.py](../../src/rossmann_forecasting/app/contracts.py),
[services.py](../../src/rossmann_forecasting/app/services.py),
[artifacts.py](../../src/rossmann_forecasting/app/artifacts.py),
[api.py](../../src/rossmann_forecasting/app/api.py) and the four application test modules.
Producer dimensions were checked in model selection, uncertainty and inventory simulation code.
Canonical numerical evidence remains in PROGRESS; this plan does not maintain another result table.

**Objective:** Present accepted saved development evidence so a course reviewer or planning analyst
can follow monetary Sales history → frozen forecast → empirical uncertainty → conditional policy
comparison, including unfavorable results and missing evidence.

**Non-goals:** New training, inference, calibration, selection, simulation, metrics or denominators;
live operational orders; SKU quantities; source-wide EDA; new opening schedules; ledger exploration;
feature importance/SHAP; monitoring or final reporting; Phase 13/14 work. No protected July 4–31
Sales, Open or Customers access, hashing, export or reveal. No canonical artifacts are regenerated.

## 2. Decisions and contract conflicts

| Item | Authority / recommendation |
|---|---|
| Direct Python services, thin separate API | Already accepted by ADR-017 and Phase 11. Streamlit calls `ApplicationServices`, without HTTP loopback or importing `app.api`. |
| Frozen analytical outputs and reader trust | Already accepted. Keep manifest pins, output hashes, producer schemas, row caps, lineage checks, path checks and unavailable states. No `current.json` fallback. |
| Five screens and a single sidebar navigation control | Proposed. Combine forecast and uncertainty; combine overview and provenance. Render only the active screen. |
| Presentation technology | Proposed: Streamlit plus existing pandas/matplotlib, with an optional `dashboard` extra added only during authorized implementation. No Plotly, SHAP or other chart package is necessary. Generate the lock through uv. |
| Result caching | Proposed: no Streamlit DTO/data cache initially. Retain existing process-local output-hash memoization and immutable-artifact assumptions. |
| Deployment | UNDECIDED. Private LAN on the artifact-owning machine remains one candidate only. Course acceptance, audience, and distribution are not approved. |
| Service extensions | Excluded from the core. Calibration counts/coverage, structured inventory case metadata and per-store operational parameters need separate typed service designs if requested. |

Conflicts are explicit rather than edits to the approved proposal:

- Proposal §22 lists editable stock, lead time, service target and unit value, plus replenishment,
  ROP, equivalent units and risk alerts. Phase 11 exposes saved cases and standing targets, with no
  what-if computation or live inventory state. The proposed Phase 12 minimum uses saved case
  selection and descriptive availability/cost notices. It requires Technical Lead acceptance of
  that narrower demonstration; it does not claim the full proposed interactive decision workflow.
- Proposal §22's promotion/holiday/rolling analytics and feature explanations lack public service
  DTOs. Core history shows only bounded Sales/Open. Full-source historical EDA must not be loaded
  into this dashboard because it includes the protected period. Those richer views are deferred.
- Proposal §20 names Community Cloud / Render. ADR-017 leaves deployment details for this plan.
  Deployment mode remains undecided. Private LAN is a candidate, subject to a later audience and
  course-requirement decision. No deployment or artifact distribution is approved here.
- ADR-004's old reference to optional 28-day views is superseded by ADR-017 and the current proposal:
  only H14 and its first-seven-day display are supported.
- Some dictionary/data-layout/roadmap paragraphs retain older Phase 10/11 lifecycle language.
  Current PROGRESS, completed plans and merged Git state establish completion. They are not
  instructions to reopen those phases or permission for new work; broad historical cleanup is
  outside this change.

No ADR or proposal text changes in this design task. Any later accepted material distribution or
service-contract change must be recorded with explicit approval before dependent code.

## Approval checkpoint — 2026-10-09

The Technical Lead's explicit M1 authorization is recorded in the implementation task following
the review and merge of design PR #28 into `main` at
`9b4ab7f54abff0ca1abfe8b6c547de960c8be8b1`. This accepts the five-screen architecture, direct
`ApplicationServices` calls, and M1 shell/presentation scope. It authorizes a compatible optional
Streamlit dependency only; existing pandas/matplotlib remain the presentation foundation. The
feature implementation branch is `feat/phase-12-streamlit-m1`, based directly on current main.

M1 may implement the application shell, overview/readiness screen, pure presentation helpers,
sanitized UI errors and fixture-backed tests. Other four screens stay honest, data-free placeholders;
their service queries are out of scope. The proposal's interactive stock/lead-time/service-level
what-if behavior is excluded from M1–M3. Phase 13 holdout access is not authorized. Deployment
remains undecided; LAN is only a candidate. M2–M4 remain PLANNED / NOT AUTHORIZED.

## 3. Actual Phase 11 interfaces

Request dataclasses live in `app.contracts`; view/row/provenance dataclasses live in `app.services`.
They are frozen dataclasses, not Pydantic models. Construction alone does not validate a query:
the reader enforces bounds. UI validation improves interaction and never replaces those checks.

| Service / typed input → typed output | Verified bounds and relevant semantics |
|---|---|
| `catalog()` → `ApplicationCatalog` | Store IDs 1–1115; three Phase 7 origins; Fit A/B pairs; `ScenarioEntry` rows; opaque inventory case IDs; ten `ResourceStatus` entries and the additional history selector. Catalogue data require Phase 9 catalog and Phase 10 comparison reads. Missing files are caught; integrity/schema failures propagate. |
| `forecast_issuance(ForecastQuery(store_id, forecast_origin))` → `ForecastIssuanceView` | Origins 2015-05-22, 2015-06-05, 2015-06-19 only; ≤14 `ForecastPoint` rows. Dates/horizons, raw/operational values and separate availability flags, candidate/run identity. No actual Sales, source Open, unavailability reason or planned-schedule field in this DTO. |
| `forecast_uncertainty(UncertaintyQuery(store_id, forecast_origin, fit_id))` → `ForecastUncertaintyView` | A ↔ 2015-06-05; B ↔ 2015-06-19. ≤56 `DailyInterval` rows and ≤42 `CumulativeUncertainty` rows. Separate daily/cumulative provenance and interpretation. No actual outcomes, quantile sample counts, distinct-store counts or coverage diagnostics. |
| `model_comparison(ModelComparisonQuery(...))` → `ModelComparisonView` | Exact filters: `candidate_id`, `population`, `scope`, `validation_window`, `horizon`, `store_id`, `metric`; at least one required. `limit` defaults 200, accepts 1–500. Text ≤128 characters without control characters; windows restricted to validation_1/2/3, horizon 1–14, Store 1–1115. Excess matching rows raise invalid request; the limit is not pagination or silent truncation. Arbitrary valid text may yield empty rows. |
| `inventory_comparison(InventoryComparisonQuery(case_id, store_id=None))` → `InventoryComparisonView` | Case syntax `[A-Za-z0-9._-]{1,128}` and a saved comparison case must exist. Optional Store 1–1115. ≤32 comparison rows; ≤2230 rows each from summary/targets; ≤1115 `InventoryPolicyPair` objects. Whole-case aggregates remain whole-case when a Store is selected. Unknown case is invalid before policy tables are read; a known case without that Store can be empty while aggregates remain present. |
| `sales_history(HistoryQuery(store_id, start_date, end_date))` → `SalesHistoryView` | One Store, ≤366 inclusive days/rows, 2013-01-01 through 2015-07-03. Fixed Arrow projection Store/Date/Sales/Open and storage-side Store/date filtering. Requires timezone-naive timestamp[ns] source dates. No Customers, promotion, store metadata or artifact-hash provenance in the result. |

`ArtifactProvenance` fields are `selector`, `phase`, `run_id`, `manifest_sha256`,
`output_sha256`, `selected_rows`, `manifest_rows`. `ResourceStatus` adds actual validation level,
presence/manifest/hash booleans and an optional sanitized error code. Supported Store IDs indicate
query validity, not guaranteed observations or complete forecast paths. History is a bounded,
locally trusted prepared-source read; it is not hash-pinned by this service and is not included in
the ten readiness entries. Do not invent a history verification badge or code/seed/lock fields
that these DTOs do not return.

Reader behavior is intentionally retained: selected Parquet reads first verify the full output
hash, footer schema and global manifest row count, then materialize the bounded fixed projection.
Selected CSV comparisons scan the entire CSV to check row counts while retaining only exact
matches; a narrow filter bounds returned memory, not source I/O. Catalog verifies two small data
outputs; `inspect_readiness()` does not freshly read/hash every output. Hash memoization is keyed
by device/inode/size/mtime; matching metadata is not proof against malicious same-fingerprint
mutation. No ledger selector exists.

`available`/`empty` view states describe row presence. A view can be available while all its
numerical rows are unavailable. Catalog alone uses `unavailable` states for missing catalog/case
resources. Other missing artifacts raise `ArtifactUnavailableError`, with `missing_manifest` or
`missing_artifact`. `ArtifactReadError.code` is one of `artifact_unavailable`,
`artifact_integrity_error`, `artifact_schema_error`, `artifact_duplicate_key`,
`unsupported_artifact_selector`, `invalid_artifact_request`, `unsafe_artifact_path`.
Messages are fixed and sanitized. Existing HTTP mapping is 422 for request/selector errors, 503
for resource errors and fixed 500 for unexpected errors; Streamlit must implement its own display
mapping because it calls Python directly. Seven GET routes exist; no API route is needed for UI.

Evidence includes application tests for whitelisted issuance fields, unavailable uncertainty,
producer denominators, signed positive and negative costs, asymmetric policy availability, empty
Store selections, JSON sentinel handling, pre-open history rejection, filtered Arrow reads,
streamed CSV limits, wrong hashes/lineage/schema/keys and sanitized exceptions. The fixture store
supports isolated trusted hashes; fixture identities must never replace production pins.

## 4. Screen specifications

Five sidebar destinations: **Overview & Evidence**, **Historical Sales**, **Forecast Explorer**,
**Model Comparison**, **Inventory Comparison**. The seven candidate sections are specified below;
uncertainty is a panel in Forecast Explorer and assumptions/provenance are in Overview and repeated
beside results. Only the active screen fetches its data. Inventory has its own case selection;
the forecast-origin control must not appear to filter inventory results.

### 4.1 Project overview / business problem

**Question / user:** What does this project demonstrate, and what evidence is available? Course
reviewer, team member and first-time planning analyst.

**Source / required fields:** Approved static explanatory copy grounded in proposal/ADRs;
`catalog()` → `ApplicationCatalog`, including `phases`, `selectors`, supported Stores/origins/fits,
catalog states, scenarios/case IDs, `resources` and both catalog provenance objects.

**Controls:** Five-screen navigation and explicit refresh/retry. No model selector or arbitrary
date/run/path inputs. Initial selected Store is 1, origin June 19 if offered; deterministic UI
defaults are not claimed to be representative stores or recommended operating decisions.

**Presentation:** Short business question; descriptive → predictive → simulated decision diagram;
static H14, selected frozen LightGBM trial A/180 rounds and development-only labels. Resource-status
table displays logical selector, actual validation level and error code. Do not promote presence,
manifest validation or process startup to full verification. Data availability counts are UI
resource counts, not forecasting accuracy KPIs.

**States / interpretation:** Static purpose/limitations always render. Missing artifacts produce
an explanatory clean-checkout state and disable only dependent controls. An empty catalog is
explicitly different from missing files. Catalog corruption blocks its selectors and shows a
sanitized integrity failure; do not fabricate fallback options. Navigation/static information remain
usable. Independent screens may query their own services with fixed validated controls when a
catalog failure does not supply those controls; a failed catalog is never shown as trustworthy.

**Acceptance / tests:** AppTest with absent fixtures starts without an uncaught exception or zero
metrics; catalog corruption is visible. No reader calls for ledger or history on overview; no
HTTP client, model import/inference or producer command execution. Copy identifies turnover,
synthetic costs and protected cutoff before the viewer opens analytical screens.

### 4.2 Historical Sales, deliberately limited EDA

**Question / user:** How did this Store's observed monetary turnover vary in a selected development
period? Planning analyst or reviewer inspecting source context.

**Source / required fields:** `sales_history(HistoryQuery(...))` → `SalesHistoryView`; each
`SalesHistoryRow` has `store_id`, `date`, nullable `sales`, nullable `open`; also `state`,
`through_date`, `selector`. No static EDA exports or broader prepared-table read.

**Controls:** Store 1–1115; start/end dates within 2013-01-01–2015-07-03, ≤366 inclusive days;
apply form validates before service dispatch. Default 2015-05-09–2015-07-03 (56 days). Clearly
label this as retrospective development history, not origin-time information for fitting.

**Presentation:** Dated Sales line/points with source Open status shown in a separate trace/table;
observed-row count and actual requested bounds only. Keep observed closed-day zero points.
Break lines across missing calendar dates and null values; a plotting-only calendar index may
contain null placeholders, never invented observations or zeros. A data table retains all returned
rows and unknown Open. No rolling-statistic, causal promotion, StoreType or cohort KPI.

**States / interpretation:** Empty valid range shows “No observed rows for this selection.” Missing
history shows “Historical source unavailable” independently of forecast readiness. Integrity/schema
failure suppresses the history chart and displays the fixed code. Source absence is not closure.
No full-file history hashing for UI provenance: the prepared file also contains protected outcomes.

**Acceptance / tests:** Valid cutoff endpoints; inverted/oversized/cross-cutoff dates rejected before
service/data access; missing calendar date vs observed zero; unknown Open and null Sales; empty
history; error sanitation. Fixture can use artificial boundary sentinels, never real holdout values.
No forecast-history overlay or per-selection error metric is introduced in the core.

### 4.3 Forecast Explorer

**Question / user:** What saved H14 monetary Sales path did the frozen selected candidate issue for
this Store and origin? Analyst reviewing a historical forecast, not placing a current order.

**Source / required fields:** `forecast_issuance(ForecastQuery(...))` → `ForecastIssuanceView` with
query, state, provenance; `ForecastPoint.date`, `horizon`, `raw_forecast`,
`operational_forecast`, both availability flags, `candidate_id`, `model_selection_run_id`.

**Controls:** Store and exactly the three catalog origins; first 7 days / all 14 days is a display
choice after the H14 service request. Default raw view; optional saved operational trace. No
28-day, current-date, arbitrary-origin or alternative-model request. Label the complete origin and
target calendar interval even when only seven horizons are displayed.

**Presentation:** Raw and operational paths with distinct legends; dashed origin boundary and
no “actual” trace. Table shows every returned date, horizon, value and availability. Report supported
H14 and the number of returned/available rows in the displayed subset. These are display counts,
not producer coverage metrics. No total-forecast KPI on a partial path and no calculated accuracy.

**States / interpretation:** Empty points stay empty; an absent horizon is a gap, not an unavailable
zero. Numeric zero with availability true is retained. Unavailable operational points remain null;
the DTO does not identify their exact cause. Explain that future opening can be unknown and saved
operational routing is a conditional historical replay assuming source Open known at origin.
Never infer a closure from zero or expose source Open by reading around the DTO. Missing/integrity
errors clear prior result panels, retaining only the current selection and sanitized error.

**Acceptance / tests:** All three origins; 7-day toggle makes no new origin/horizon query and cannot
alter model comparison or inventory scores; two availability flags remain independent; sparse paths
break lines. DTO conversion omits actual/source Open/assessment fields. Store/origin changes cannot
retain a result labelled with the old query. Model identity and provenance are visible.

### 4.4 Forecast uncertainty panel

**Question / user:** Which saved empirical daily ranges and cumulative prefix buffers are supported,
and what assumptions limit them? Analyst assessing uncertainty and course methodology reviewer.

**Source / required fields:** `forecast_uncertainty(UncertaintyQuery(...))` →
`ForecastUncertaintyView`, including interpretation and two provenance objects. `DailyInterval`:
date, horizon, interval_kind, point_forecast, lower, upper, width, available, unavailable_reason,
units, schedule_assumption_flag. `CumulativeUncertainty`: prefix_days, probability,
issued_prefix_complete, unavailable_reason, demand_value, signed_error_quantile,
upper_turnover_value, safety_stock_value, target_value, units, schedule_assumption_flag.

**Controls:** Store and current forecast origin; derive fit from the catalog matching A/June 5 or
B/June 19. May 22 has no fit and shows an unsupported-uncertainty notice without dispatching an
invalid query. Daily raw/operational choice; cumulative k=1–14 and saved p in {0.90,0.95,0.98}.
The seven-day display filters only daily chart/table rows; cumulative prefixes retain their own
explicit k and H14 context. These controls select saved rows, not calibration or inventory settings.

**Presentation:** Separate daily point-and-shaded-range plot, never an error-bar standard deviation;
draw each contiguous available segment independently. The point need not be inside its interval.
Table preserves unavailable rows/reasons and stored widths. A separate prefix table/cards show
saved D_k, signed q, U_k, safety stock and target. No sum of marginal bounds, recalculation or
inferred service probability. If prefix completeness is true but the quantile or saved values are
null, show unavailable with its reason; completeness alone is not numerical availability.

**States / interpretation:** “Nominal 95% empirical daily interval; no guaranteed coverage.”
Prominent Fit A h2/h3/h9 unavailable and Fit B sparse Sunday limitations, grounded in accepted ADR-021;
these are methodology copy, not invented per-row sample fields. Include the below-nominal Fit B
finding by linking to canonical PROGRESS evidence, without calculating coverage or copying a new
result table. Conditional operational closure routing must not be presented as improved model
accuracy. Cumulative prefixes are origin-anchored; no calibrated later-review suffix or synthetic
transport claim. Available view with all unavailable bands renders the table/notices and no band.
Empty rows, missing files and integrity failures follow the distinct common states.

**Acceptance / tests:** Missing fit, unavailable tails, all-null intervals, isolated available
segments, unknown-schedule reasons, negative q, point outside band, complete prefix with unavailable
quantile and incomplete prefix with null values. Exact saved numbers survive conversion. No service
call for raw quantile artifacts/coverage files to compensate for missing public DTO fields.

### 4.5 Model comparison

**Question / user:** Why was the development LightGBM recipe selected, and where is it weaker?
Course reviewer and analyst comparing accuracy on a stated population.

**Source / required fields:** `model_comparison(ModelComparisonQuery(...))` → `ModelComparisonView`;
all `ModelComparisonRow` fields: candidate_id, population, paired_with, scope, validation_window,
horizon, week_block_start_horizon, week_block_end_horizon, store_id, metric, value, numerator,
denominator, unavailable_reason, paired_mae_delta, paired_mae_change_fraction; plus provenance.

**Controls / exact query presets:** Candidate ladder is `seasonal_naive`,
`holt_winters_additive_weekly`, `global_lightgbm_gbdt_regression_l1`. Core primary population is
`three_way_common`; availability panel uses `standalone`. Core scopes `pooled`,
`validation_window`, `horizon`, `week_block`, `store` are emitted producer values. No free-text
filters. Use one bounded primary table query for common population plus selected scope; supply
validation_1/2/3 for window scope or Store for Store scope, with limit=200. For horizon scope,
request one metric at a time, returning at most 42 rows; for a detailed horizon table additionally
filter h=1–14. The primary metric defaults to `mae`; secondary choices `rmse`, `mape`, `wape`.
Week-block rows are selected/displayed by their saved start/end fields; these are not query fields.
Pairwise populations are optional later display work, not part of the minimum selector set.

**Presentation:** Common-population candidate bars for MAE, saved metric table and MAE horizon line
containing all h1–14 (including h2, h9, h10). Standalone coverage comes from separate bounded
queries for `open_label_forecast_coverage_rate`, preserving numerators/denominators per window.
MAPE tables also fetch saved `mape_rows` and `zero_actual_rows_excluded_from_mape`; WAPE retains
the saved denominator. MAPE is already a percentage; WAPE is a fraction in the producer metric
contract. Format WAPE, coverage rates and paired-change fractions as percent only for labelled
display, without changing stored values; retain original scalars in the data table.
Sorting and exact pivoting require one saved row per dimension; never average duplicate rows.

**States / interpretation:** MAE is primary on source Open=1 eligible/common rows; operational zeros
do not inflate primary performance. Standalone results are not the common comparison population.
Preserve all candidate rows and unfavorable horizons. Label development selection, dependence,
three late-season Friday origins and weekday/horizon confounding. No significance/production or
universal winner claim. Empty query has a normal empty notice, numerical null has a reason, excessive
matches have a “Narrow the selection” request error without partial results. Integrity failure
suppresses the affected comparison; do not use hardcoded metrics as fallback.

**Acceptance / tests:** Recorded common vs standalone population/denominator labels; unchanged
numerical values; null WAPE, zero-actual MAPE exclusions and unfavorable h10 remain visible.
Verify every preset returns ≤limit with fixtures and later accepted development service smoke.
No row averaging, new winner selection, re-scoring or altered metric/coverage denominator.

### 4.6 Inventory policy comparison

**Question / user:** Under this saved case, how do the two simulated standing-target policies differ
in monetary cost/service exposures? Analyst or reviewer exploring conditional tradeoffs.

**Source / required fields:** `catalog()` case IDs (and separately `ScenarioEntry` metadata);
`inventory_comparison(InventoryComparisonQuery(...))` → `InventoryComparisonView`. Each
`InventoryAggregate` retains case/metric, requested/standalone/matched Store counts, baseline and
forecast numerator/denominator/value, signed and relative differences, null reasons and interpretation.
Each `InventoryPolicyPair` retains case_id/store_id, comparable flag, signed cost difference/reason
and baseline/forecast `PolicyResult`. Policy fields: policy_id, episode_status/completeness,
target_available/reason, episode availability_reason, valid_matched_comparison, saved cost,
demand/fulfilled/unmet totals, target_value, synthetic, calibration_transport_valid,
schedule_assumption. No daily ledger or source stock is present.

**Controls:** One exact opaque case ID from `inventory_case_ids`, and one Store 1–1115. Default
`synthetic_base-20150605-r00--reference` only if catalog offers it, otherwise first catalog case.
All cases remain selectable, including sensitivities. No freeform stock/cost/lead/service/seed
sliders and no scenario regeneration. No case-to-origin/family parsing: the public case list has
no typed mapping to scenarios. Show scenario catalog as separate explanatory metadata without
claiming it describes the selected case; defer dependent scenario/family/replicate filters until
a typed case-metadata service is approved.

**Presentation:** Two plainly separated blocks: “Whole saved case — all matched Stores” with saved
cost, value fill and positive-demand stockout KPIs; “Selected Store — saved policy pair” with
two targets, costs, totals and availability states. Show positive signed forecast-minus-baseline
cost as adverse, negative as favorable only under these assumptions, zero as equal. Use words and
signs alongside color, with a visible zero reference. Suppress difference KPI if not comparable.
Whole-case table includes all ten saved metrics, counts/denominators/null reasons, including
inventory, unmet value, completed positive-demand receipt-cycle service rate and four terminal
exposures. Terminal exposure is separate from primary holding-plus-shortfall cost. No invented
per-store fill/cycle/stockout ratio from exposed totals and no pooling of Store percentages.

**States / interpretation:** Saved policy IDs are `historical_mean_standing_target` and
`lightgbm_buffer_standing_target`. Both policies' completeness/target/validity can differ; show
individual reasons plus the service's fixed pair-level priority. A zero target is valid when
available. Empty Store pair leaves whole-case aggregates visible with their scope unchanged.
Unknown case is invalid, missing output is unavailable, integrity/schema/key failure is blocking
for that comparison. Do not show old case numbers after a failed selection.

Keep synthetic stress distinct from conditional historical Sales replay; neither is observed
inventory. q transport to synthetic paths is uncalibrated. Targets are frozen at origin, with
R=1, L=2–7 and P=L+1; these are accepted design context, not this Store's unexposed parameter
values. No later-review uncertainty guarantee or current replenishment recommendation. Cycle-rate
denominators depend on policy and terminal censoring; a zero denominator stays unavailable.
No “savings”, “optimal policy”, real-stockout warning or concealed adverse result.

**Acceptance / tests:** Positive/negative/zero differences, null costs, asymmetric/incomplete pairs,
valid zero target, selected Store without pair, unchanged whole-case aggregates under Store
filtering, service-provided difference reason priority and terminal exposure separation. Include
the adverse reference and buffer_090 cases in later read-only development smoke; compare with
PROGRESS rather than a copied plan result table. Ledger must never be opened or hashed.

### 4.7 Assumptions, limitations and artifact provenance

**Question / user:** What precisely backs the displayed result and what does its verification mean?
All viewers, especially methodology/reproducibility reviewers.

**Source / required fields:** `catalog()` → `ApplicationCatalog`/`ResourceStatus` for overview;
each analytical result's `ArtifactProvenance` near that result; approved static copy/links to
dictionary, ADRs and canonical PROGRESS. History has only selector/cutoff and locally trusted
source semantics, without hash provenance.

**Controls / presentation:** Expandable provenance tables and explicit retry. Show logical selector,
run ID, full manifest/output SHA-256 when supplied, selected/global row counts and the actual
validation level. Display returned provenance rather than request-controlled file links. Static
limitations remain visible beside their relevant chart, with fuller explanation on Overview.
No artifact path, manifest dump, raw-data download or browser-selected run override.

**States / interpretation:** A result's successful read proves that requested output passed its
reader checks under the accepted local immutability trust model; it does not verify every sibling
artifact or deploy reliability. A missing provenance value says unavailable, never verified.
Refreshing catalog can reflect hashes verified by prior reads but does not initiate a ledger/full
source audit. Preserve historical manifest freeze flags and original lineage limitations.

**Acceptance / tests:** Path-free JSON-safe rendering and accurate selected/global counts;
presence vs manifest vs output verification; history cannot receive a forged digest badge;
failure never displays a success badge; limitations survive empty/missing states. No copied
calibration-count, code-revision, seed or environment values masquerade as service-returned facts.

## 5. Minimal modules, state, errors and performance

Proposed files, created only after approval:

| File | Responsibility |
|---|---|
| `streamlit_app.py` | Thin Streamlit entrypoint, importing `run_dashboard`; runnable from repository root with editable package installation. |
| `src/rossmann_forecasting/app/dashboard.py` | `run_dashboard(services=None)`, shared frame, five render functions, forms, screen-local service calls and safe error display. Default provider is existing `ApplicationServices()`. Test injection has no viewer control. |
| `src/rossmann_forecasting/app/dashboard_presenters.py` | Small pure DTO-to-table/chart-series conversions, gap segmentation, formatting, bounded comparison query presets and explanatory labels; no I/O/business calculations. |
| `tests/test_dashboard_presenters.py`, `tests/test_dashboard.py` | Presentation unit tests and fixture-backed Streamlit AppTest, reusing isolated producer-schema fixture construction. No runtime test-fixture import. |
| `pyproject.toml`, generated `uv.lock`, `.streamlit/config.toml` | Authorized dashboard dependency extra and safe local/demo settings; keep existing dependencies/methodology intact. |

Data flow: widget/form values → validated typed query → existing service → verified reader →
typed DTO → `json_safe` and explicit field-whitelist conversion → chart/table. Nulls are preserved;
do not apply `fillna(0)` or a blanket pandas reduction. `json_safe` handles pd.NA/NaT, dates, enums
and NumPy scalars and rejects nonfinite numbers. Presentation conversion errors show fixed
internal-error text, without `st.exception` or raw exception strings. Exact numerical values remain
in tables; rounding belongs only to display formatting.

Use one keyed sidebar radio for navigation, page-specific keyed forms and scalar selections in
`st.session_state`. Fit follows origin; case is independent; reset unsupported stale widget values
when a fresh catalog changes options. No query-parameter bookmarks in the minimum. A changed form
shows “Apply selection” and clears or visibly marks the old result until applied. Do not fetch all
pages through tabs or preserve DTOs as a hidden stale-result cache. UI input validation and core
reader errors both remain testable.

Default services share `_DEFAULT_READER`, including a mutable hash memo, even if their wrapper is
per-session. Proposed UI dispatch uses a small process-local standard-library RLock around service
calls, including catalog, to serialize that shared state for the small course audience. Charts
render after releasing it. No parallel fragments/background work or FastAPI server in this process.
This is adapter synchronization, not a reader or methodology change. Global
[Streamlit resource caches](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource)
require thread-safe objects; none are introduced. A per-session wrapper alone is not reader isolation.

Caching initially consists only of existing verified-file fingerprints; every submitted service
query still checks current manifests/fingerprints and reads its selected output. No TTL cache of
DTOs, catalog or errors can mask a changed/missing file. Read-only, operator-controlled immutable
files are required; hot replacement is disallowed, and operator refresh restarts the process.
Tests with changed fingerprints must still expose reader failures. Later result caching needs
measured need and a written identity/invalidation contract before implementation.

Use existing matplotlib for lines, interval bands and bars plus `st.dataframe`/`st.metric`.
Close each created figure. Tables accompany plots, errors/signs are textual, units and populations
are explicit, and plots use no color-only meaning. No currency symbol is asserted without evidence
for the original Sales unit. Current charts need no new plotting dependency.

| UI state | Required behavior |
|---|---|
| Empty selection | No observations/matches; no zero score or fabricated table. Inventory may still retain labelled whole-case rows. |
| Unavailable numerical result | Keep row/status/reason and other available values; omit unsupported band/KPI. |
| Missing manifest/output | Explain local prerequisites; enable retry; static navigation remains. No fixture fallback. |
| Invalid request / unsupported selector | Fixed bounded-selection message; do not show partial results. Narrow oversized model queries. |
| Integrity/schema/duplicate/unsafe path | Fixed blocking resource message + stable code and logical selector; clear related result, never downgrade to missing or ignore a check. |
| Unexpected exception | Fixed internal-error message, operator-only logs, no path/stack/input echo. Hosted configuration suppresses framework error detail too. |

Performance targets are proposed acceptance budgets, not measured capability: on the selected host,
cold first visit ≤15 seconds; warm submitted screen ≤3 seconds in at least 19 of 20 measured runs;
application resident memory ≤1 GiB with two browser sessions. Record machine/OS/Python/lock/revision,
resource sizes, cold versus warm state, timing method and peak memory. CSV filters still rescan the
source; serialized calls can queue. Do not promise latency from row caps. If budgets fail, first
reduce UI calls and redundant panels; changing readers/caching needs a reviewed follow-up.
Never read/hash the ledger or protected history for performance instrumentation.

## 6. One deployed demo: alternatives and recommendation

A Git clone supplies code and tests, not accepted evidence. Ten registered outputs are ignored,
with pinned manifests and fixed repository-relative paths. Putting a few rows at those paths
fails byte hashes/global row checks. Fetching `current.json`, substituting fixture pins or stripping
hash checks is unacceptable. A model binary is unnecessary because no inference runs.

### A. Candidate: private LAN deployment on the artifact-owning machine

Run one authorized Streamlit process on the existing trusted Windows/team machine and make its UI
reachable from another course device on an approved private LAN. Keep the canonical files in place;
no data upload, tunnel, new storage service, cloud account or API deployment. The operator retains
artifact access and accepts the read-only local-file trust model. Existing files are not exposed as
static downloads. The service reader continues every accepted hash/schema/bounds/lineage check.

Required local runtime closure: Phase 7 manifest, selected forecasts and model comparison; Phase 8
manifest, daily intervals and cumulative uncertainty; Phase 9 manifest, scenario catalog and
`upstream_bindings.json`; Phase 10 manifest, comparison summary, policy summary and targets.
Quantile CSVs are optional for resource status, with no public numerical service view in the core.
Sibling outputs named in a manifest need not be uploaded or opened merely to support this UI.
History additionally uses the existing local prepared train through its bounded service; do not
copy, hash, export or serve the full source. Readiness must truthfully mark absent optional outputs.
No ledger, model binaries, raw source, Kaggle credentials or protected labels are distributed.

Security/access: trusted course network and an explicit host firewall audience restriction; default
local launch stays localhost until exposure is authorized. Disable static serving and file watching,
retain CORS/XSRF protections and set framework browser error details to none; no upload widgets,
path controls, filesystem browser or artifact download button. An open LAN listener is not user
authentication or suitability for internet exposure. A wider/untrusted network requires a separately
approved authenticated hosting path. Logs stay with the operator and are not downloadable.

Constraints: host must remain running; network reachability/firewall and two-client concurrent use
must be demonstrated. Reproduce from pinned code/uv lock and existing canonical identities, not
from claims that historical producers reran at current main. Cost is existing hardware and small
operator effort; uptime beyond the course session is not promised. Missing artifacts show static
purpose/limitations and honest unavailable screens, which is useful diagnostics but does not pass
the analytical deployment gate. Acceptance needs one actual viewer URL and genuine accepted
development forecast, comparison and inventory views. Human approval must confirm private course
access counts toward the deployment deliverable.

### B. Cloud host with an approved private canonical-file provision

A small managed host can run the same editable checkout and direct services against an operator-
provisioned private, read-only disk at the exact repository-relative paths. Full bytes of requested
outputs/manifests/bindings are preserved. No subset masquerades as a canonical file. Omit raw data,
model binaries and ledger; disable history unless its separate safe-source provision is approved.
The existing full prepared train must never be transferred because it contains protected outcomes.

This can provide a persistent viewer URL and unchanged canonical reader behavior, but requires
explicit later authority to transfer ignored development artifacts, review applicable distribution
rights and viewer access, configure credentials privately, and select storage/host lifecycle. None
of those transfers/infrastructure actions is authorized here. Protect storage from viewer writes;
HTTPS plus host authentication/access restriction for nonpublic evidence. No runtime arbitrary URL
fetch or secret in Git. Provisioning and initial output verification finish before readiness; absent
provision gives the same explicit unavailable screen, never automatic regeneration.

Reproducibility needs a checked provisioning allowlist, original byte hashes, pinned code/lock,
resource limits and operator startup record. Artifact location changes must remain real directories,
not symlinks rejected by the reader. Cost/complexity is higher than A: ongoing host/storage and
secure deployment administration. Provider capabilities/prices/resources are not selected or
promised by this proposal. If transfer authorization is unavailable, this route is blocked.

### C. Cloud demo using a separately reviewed reduced evidence snapshot

An alternative to large canonical-file distribution is a small, human-approved text/JSON snapshot
of exact bounded service DTOs: selected Store/origin forecast/uncertainty views, producer aggregate
model tables including all horizons, case aggregates and selected Store policy pairs including
unfavorable cases. Restrict controls to included selections; exclude all historical source rows,
protected values, Customers, filesystem paths, ledger and binaries. It remains genuine derived
development evidence only when extracted from verified services with documented identity; test
fixtures must be labelled synthetic interface demonstrations and cannot satisfy evidence acceptance.

This needs a **new proposed contract**, not a change to `_ArtifactReader`: versioned snapshot schema,
typed read-only provider for the same UI, fixed included-query index, source output/manifest pins,
snapshot hashes, extraction command/configuration/code revision/seed applicability and environment/
lock identity, publication approval and independent exact DTO parity review. Hash the snapshot and
record source verification; do not label it freshly reverified canonical data. Never override
production pins or silently fall back from missing canonical files. This plan specifies a feasible
alternative, not its implementation or approved public content.

After authorization, one Streamlit Community Cloud instance could serve that restricted snapshot
with code and an approved publication package; visibility/access and distribution rights need
explicit review. Its official docs say code is cloned from Git, recognize uv.lock, require explicit
dependency setup and allow configured Python versions. Our dashboard optional extra must actually
be installed by the chosen build path; recognition of uv.lock alone does not establish that. Verify
src-package editable/root behavior, Linux scientific dependencies and the tested Python version.
Use generated deployment inputs only if needed, never a second hand-maintained dependency list.
Missing/corrupt snapshot yields an explicit blocked evidence state. Lower data footprint reduces
runtime I/O, but adding a second provider/exporter and accepting limited selections increases code
and review complexity. It also narrows the all-Store demo and does not supply historical analytics.

References checked on 2026-10-09: [Cloud file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization),
[dependency resolution](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
[deployment/Python selection](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
and [viewer sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app).
Platform behavior must be rechecked during any later deployment task.

**Recommendation:** Approve A for a minimal course demonstration if the course permits private
session hosting. If a persistent external URL is mandatory, decide B vs C and approve its data
distribution/provider contract before expanding implementation scope. A code-only cloud deployment
with absent artifacts or a fixture-only site is not an accepted analytical demo. This task performs
no packaging, transfer, provisioning or deployment.

## 7. Milestones and independent Luna 6 task boundaries

M1 is APPROVED / AUTHORIZED only under the checkpoint above. M2–M4 remain PLANNED / NOT
AUTHORIZED. Assign each future milestone only after its separate authorization; passing M1 tests
does not start later work. Record exact reviewed heads and independent acceptance in this same
active plan. A future feature branch must start from then-current main, or explicitly record any
unmerged integration dependency. No agent delegation occurred in this task.

| Milestone | Luna 6 implementation boundary and dependencies | Required review / acceptance evidence |
|---|---|---|
| M1 — Shell and presentation boundary | Authorized scope. Add dashboard extra/lock, thin entrypoint, five-screen shell, pure presentation helpers, safe errors and fixture injection. Implement static overview/provenance and clean-checkout states only. No forecasting/history/comparison screens, hosting or service extension. | Locked install on Python 3.12/3.14; missing/corrupt catalog AppTest; accurate readiness; conversion/null/error tests; no file paths/raw exception echo or HTTP/model dispatch. Independent review accepts shell before M2. |
| M2 — History, forecast and uncertainty | Accepted M1. Implement §§4.2–4.4 using exactly current services and DTOs. Source/date/fit/form validation, sparse plots, raw/operational distinction, cumulative table and caveats. No metrics/simulation/deployment or new quantile/coverage reader. | Fixture UI→services→reader tests, cutoff-before-open assertions, all origin/fit cases, H7 display subset, partial/all-unavailable intervals and negative-q cases. Read-only non-ledger development smoke only after implementation authorization. Independent methodology/UI review before M3. |
| M3 — Model and inventory comparisons | Accepted M2. Implement §§4.5–4.6 and proposed bounded query presets; exact producer tables/denominators, case vs Store scope and adverse-result display. No sliders, ratio aggregation, daily ledger or service changes. | All candidates/horizons and coverage preserved; bounded-query fixtures and canonical service smoke; positive/negative/null/asymmetric pair UI tests; unchanged aggregates under Store selection; scientific-language review. Independent review before M4. |
| M4 — Integration and one authorized deployment | Accepted M3, explicit host/audience approval and distribution-contract approval if B/C replaces A. Run full fixture/quality matrix, manual browser layout and two-session checks, benchmark selected host, document real deployment startup/failure behavior and obtain final independent review. The approval must name any extra B/C work before assigning it to Luna 6. | One audience-accessible URL showing accepted development evidence; absent/corrupt-resource behavior; no publicly served raw/ignored files/holdout; measured latency/memory evidence; code/lock/run provenance; Technical Lead acceptance, authorized merge and explicit Phase 12 closeout. Stop there. |

Do not spawn or implement these Luna tasks in this proposal. M4 cannot be declared complete from a
localhost screenshot, a health endpoint, fixture-only evidence or a successful build without data.

## 8. Validation plan and definition of done

**Unit:** Pure presenter gap/null/zero handling, exact scalar preservation, safe formatting/signs,
candidate/population labels, query caps and duplicate-dimension rejection. Test behavior with
meaningful contrasting fixtures rather than tests duplicating helper internals.

**Integration:** Streamlit → injected real `ApplicationServices` → isolated `_ArtifactReader` with
trusted synthetic producer-schema fixtures. Reuse fixture creation without using real Rossmann
files in CI or importing test modules into production. Assert protected-cutoff predicates/projection,
immutable fixture bytes, no ledger/raw source access and no inference/calibration/simulation. The
existing reader/API suite retains its full responsibilities; new UI tests need not replicate each
CSV token/security permutation. Artificial boundary-date sentinels are test data, not a holdout read.

**UI:** [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
for navigation, forms, dependent fit selection, retries, stale-result clearing, rendered text/tables
and safe empty/error states. Inject services at the composition boundary, never replace production
pins via a runtime user option. AppTest does not establish pixel layout or actual chart visibility:
manual browser verification checks axes, gaps, band segmentation, narrow viewport, tooltips/legends,
table readability, keyboard controls, color/sign interpretation and two-session behavior.

**Repository/dependency:** The future locked `dashboard` extra must work alongside dev/api on both
CI Python versions; preserve the 3.12/3.14 matrix. Run whole-repository pytest, Ruff lint/format,
Markdown links, `uv lock --check`, `uv pip check`, `git diff --check` and diff/scope review. No new
real-data pipeline runs are needed because UI does not change forecasting/data behavior. Authorized
implementation smoke uses bounded existing development services, not regeneration. Record its
queries, actual provenance and unchanged files without hashing full source or the ledger.

**Scientific/business:** Review every screen for monetary units, H14/H7 labels, frozen candidate,
unknown Open, conditional operational replay, empirical/sparse/unavailable intervals, origin-only
cumulative prefixes, synthetic costs, signed adverse cost differences, saved denominators, policy-
dependent cycles and separate terminal exposure. No superiority, service guarantee, savings,
observed stockout or current order claim. No hidden unfavorable candidate/horizon/case values.

**Deployment/performance:** Check the chosen approved host from an independent viewer device;
confirm access restrictions, sanitized framework errors, static-serving disabled, source files not
downloadable, no automatic data regeneration/fallback, dependency installation and measured budgets
in §5. Record cold/warm behavior and resource failures. Filesystem/operator trust is a deliberate
limit, not protection against a compromised host. Configuration reference:
[Streamlit config](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).

Phase 12 is done only after all four authorized milestones are implemented, independently reviewed,
accepted, deployed with genuine accepted development evidence, tested/documented, merged with
authorization and explicitly closed under WORKFLOW. Archive this phase plan only then. This design
deliverable is done after documentation validation, self-review, commit/push and a draft PR; its
completion does not approve or complete Phase 12.

## 9. Risks, blockers and Technical Lead approval checklist

| Decision / risk | Required resolution before dependent work |
|---|---|
| Narrowed proposal §22 experience | Accept saved-case comparisons and bounded Sales/Open history as the Phase 12 minimum; otherwise request a separate scoped service extension design. |
| Deployment audience and course requirement | Confirm private LAN A qualifies, name host/audience and approve exposure for M4; otherwise choose B/C with reviewed distribution authority. No persistent public URL is currently promised. |
| Missing ignored files | Operator confirms runtime closure exists; absent files are explicit unavailable state, not a reason to change pins or regenerate. Design audit has not certified current artifact readiness. |
| Wider hosting / distribution rights | Review any later artifact/snapshot publication and protected-source exclusion. No uploads or cloud provisioning are authorized now. |
| Missing calibration/case metadata | Approve omission from the core; any extension adds typed public DTOs and independent tests before UI consumption. Existing small quantile readers are not a public service shortcut. |
| Dependency and packaging | Approve Streamlit dashboard extra and existing matplotlib; lock exact compatible versions during M1. Validate actual target build/extras, editable root and Python versions. No dependency changed now. |
| Unmeasured service I/O / concurrency | Accept initial no-result-cache design, serialized calls and proposed budgets, then measure in M4. Full CSV scanning and source hash cold reads can dominate latency. |
| Sparse scientific evidence and synthetic costs | Accept prominent caveats and unfavorable results; neither UI polish nor deployment adds independent methodological evidence. |
| Approval/integration boundary | Approve design and each implementation milestone explicitly; draft PR/CI passes are not methodology acceptance or merge authorization. Phase 13/14 remain outside scope. |

## 10. Design-task validation and publication record

Executed on the existing locked Windows environment, Python 3.14.5 / uv 0.12.23:

| Check | Actual result |
|---|---|
| Focused application readers/services/API/integration pytest | 151 passed; existing nonblocking Starlette TestClient deprecation warning. |
| Whole-repository `python -m pytest` | 431 passed; the same warning. All tests use constructed fixtures; no model/data pipeline was run. |
| `python -m ruff check .` / `python -m ruff format --check .` | Passed; 97 files already formatted. |
| `python scripts/check_docs.py` | Passed; 259 local destinations/anchors across 27 Markdown files. External links are not certified by this check. |
| `uv lock --check` / `uv pip check` | Passed; 98 resolved packages / 78 compatible installed packages. No dependency or lock modification. These current counts differ from historical closeout environment counts. |
| `git diff --check` and full documentation self-review | Passed. Exactly seven section specifications, five screens and four proposed milestones; review corrected WAPE fraction vs MAPE percentage formatting. |
| Scope comparison against base | Source/tests, pyproject/lock, proposal/ADRs, CI and data documentation unchanged. Only this plan, PROGRESS, PROJECT_PLAN and README changed. |
| Refetch before publication | `origin/main` still `2a47ae7dd959daac8eacf2b5410f090edbbcd7cb`. |

No local Python 3.12 or Streamlit UI/deployment check was run at the design-task checkpoint:
Streamlit was not installed by that task. No canonical artifact contents, ledger, protected outcomes,
source-wide EDA files or model binaries were opened/hashed for that audit. Official Streamlit
documentation and GitHub repository metadata were read. At that checkpoint the design still awaited
review; those checks alone did not approve implementation or methodology. See the M1 implementation
checkpoint below for its separate authorization and evidence.

## 11. M1 implementation checkpoint — 2026-10-09

Status: IMPLEMENTED / UNDER REVIEW. Approval and scope are recorded above. Implementation is
limited to the shell, static overview/readiness presentation, pure display helpers, safe error
handling and fixture-backed tests. Other screens are data-free placeholders and do not dispatch
services. M2–M4, deployment, publication of artifacts and Phase 13 remain outside this task.

The implementation branch is `feat/phase-12-streamlit-m1`, based on the PR #28 merge SHA
`9b4ab7f54abff0ca1abfe8b6c547de960c8be8b1`. Initial implementation commit `911f25a` is included in
[draft PR #29](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/29), targeting
`main`. The final task report records the PR's current head SHA. This checkpoint does not mark M1
accepted or Phase 12 complete.

| Checkpoint | Actual evidence |
|---|---|
| Branch and base | `feat/phase-12-streamlit-m1` from `origin/main` at `9b4ab7f54abff0ca1abfe8b6c547de960c8be8b1`; the design PR #28 is merged. |
| Commit / review | Initial implementation commit `911f25a`; see PR #29 for the current head. Merge is not authorized. |
| Focused dashboard tests | `pytest tests/test_dashboard.py tests/test_dashboard_presenters.py -q`: 13 passed before the final clean-checkout test was added. The final full-suite run includes all 14 dashboard tests. |
| Full suite, Python 3.12 | Locked isolated `uv run --isolated --locked --extra dev --extra api --extra dashboard --python 3.12 python -m pytest`: 445 passed; one existing Starlette/httpx deprecation warning. |
| Full suite, Python 3.14 | Locked project environment `python -m pytest`: 445 passed; the same existing warning. |
| Ruff | `python -m ruff check .` and `python -m ruff format --check .`: passed; 102 files already formatted. |
| Documentation | `python scripts/check_docs.py`: passed; 259 local destinations/anchors across 27 Markdown files. |
| Dependencies | `uv lock --check`: passed, 109 resolved packages. `uv pip check`: passed, 93 installed packages compatible. Streamlit 1.65.0 resolved under `dashboard = ["streamlit>=1.50,<2"]`. |
| AppTest behavior | Fixture-backed tests cover successful readiness/provenance, fully empty checkout, missing/corrupt catalogs, empty state, safe conversion and errors, all five screens and no non-catalog service dispatch. The reader spy observes only Phase 9 catalog and Phase 10 comparison reads; fixtures are isolated under pytest temporary paths. |
| `git diff --check` | Passed before commit. |
| Not performed | No manual browser, performance, deployment, real-data pipeline, canonical artifact regeneration, ledger access or protected holdout access. |

Full-suite testing used fixtures only. The empty-checkout case injects an `_ArtifactReader` rooted
in an empty temporary directory; it shows static project context, ten unavailable resource statuses
and no fabricated provenance without reading repository artifacts. The other four navigation entries
remain placeholders and issue no service calls. The draft PR is under review; M1 is not accepted and
no later milestone has started.
