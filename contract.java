# TASK — WP2-S16: Implement Controlled-Synthetic Streamlit Dashboard (Milestone B2-B)

## Role and objective

You are Luna 6, acting as Implementation Engineer.

Repository:
`mihikari29/it4063e-rossmann-demand-forecasting`

Implement Milestone B2-B: a separate, truthful, read-only Streamlit dashboard over the integrated controlled-synthetic `DemoServices`.

The deliverable is a five-screen synthetic demonstration that can be tested entirely offline using Streamlit AppTest.

The dashboard must call Python services directly. It must not communicate with the FastAPI application through HTTP.

Also resolve the deferred nonblocking regression-test finding:

`WP2-S14-01 — Inventory aggregate test compares two unfiltered requests.`

**Do not commit, push, open a PR, merge, publish the generated JSON release, start an HTTP listener, or deploy.**

## 1. Verified project baseline

Expected `origin/main`:

`232c7307f75d1ae7906af621853a8753ebe81795`

Integrated prerequisites:

### Milestone A

Controlled-synthetic release builder, manifest and verifier.

PR #52, squash merge:

`086c59183e237279a21139a62265e7450890fa63`

### Milestone B1

Pinned immutable provider and six typed synthetic services.

PR #53, squash merge:

`a31f9d610ea7922629d24c4b134cd986f634bcb4`

### Milestone B2-A

Explicit synthetic FastAPI adapter.

PR #54:

https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/54

Publication head:

`26eaed63f272cb931275b080e66b7eb982fb9790`

Squash merge:

`232c7307f75d1ae7906af621853a8753ebe81795`

PR Quality run:

`39934550249`

Post-merge Quality run:

`39935158003`

Python 3.12 and 3.14 succeeded in both workflows.

Each job reported:

`1548 passed, 8 skipped, 1 existing Starlette/httpx warning`

The previous independent Sol 6.1 review returned `ACCEPT`.

Milestone B2-A is REVIEWED / INTEGRATED.

Milestone B overall remains INCOMPLETE.

Milestone C and public deployment remain unauthorized.

## 2. Git preflight

Read:

- `AGENTS.md`
- `docs/WORKFLOW.md`
- `docs/DECISIONS.md`
- `docs/PROGRESS.md`
- `docs/PROJECT_PLAN.md`
- `docs/PUBLIC_DEMO_RELEASE_CONTRACT.md`
- `plans/active/public-course-demo.md`

Inspect local branch, HEAD, working tree, index and origin.

Fetch `origin/main`.

Create a new focused branch:

`feat/public-demo-synthetic-streamlit-dashboard`

Base it on:

`232c7307f75d1ae7906af621853a8753ebe81795`

Do not continue working on the merged B2-A branch.

Preserve unrelated user work and ignored artifacts.

If main has advanced, inspect the discrepancy before editing.

No Git publication is authorized during WP2-S16.

## 3. Authoritative interfaces

Read and inspect:

- `src/rossmann_forecasting/app/demo_provider.py`
- `src/rossmann_forecasting/app/demo_services.py`
- `src/rossmann_forecasting/app/demo_api.py`
- `src/rossmann_forecasting/app/demo_bundle.py`
- `src/rossmann_forecasting/app/contracts.py`
- `src/rossmann_forecasting/app/dashboard.py`
- `src/rossmann_forecasting/app/dashboard_presenters.py`
- `streamlit_app.py`
- `.streamlit/config.toml`
- Existing dashboard and Streamlit AppTest tests.
- Existing synthetic service/API regression tests.

The existing canonical Streamlit dashboard contains Phase 7–10 assumptions and must remain operational under ADR-024.

Inspect the exact B1 DTOs before designing tables or charts.

Do not assume synthetic result types can be directly passed to canonical presenters.

In particular:

- `DemoSalesHistory` differs from `SalesHistoryView`.
- `DemoForecastIssuance` differs from `ForecastIssuanceView`.
- `DemoForecastUncertainty` differs from `ForecastUncertaintyView`.
- `DemoModelComparison` differs from `ModelComparisonView`.
- `DemoInventoryComparison` differs from `InventoryComparisonView`.

Their differences are scientifically meaningful, not simply naming differences.

## 4. Establish a concise B2-B interface contract

Before implementation, update the active plan with:

1. Explicit synthetic mode selection.
2. Mandatory independent manifest SHA-256.
3. Read-only service injection.
4. Five screen definitions.
5. Navigation and bounded selectors.
6. Visible synthetic provenance.
7. Per-view availability.
8. Correct null/unavailable semantics.
9. Chart/table presentation rules.
10. Sanitized error handling.
11. Startup and rerun behavior.
12. Local AppTest validation.
13. Strict separation from canonical Streamlit.
14. No public bundle or hosting authorization.

Prefer a clear and narrow design.

Do not introduce a general-purpose dashboard framework or arbitrary profile registry.

## 5. Separate synthetic dashboard architecture

Prefer new modules:

`src/rossmann_forecasting/app/demo_dashboard.py`

Optionally, if meaningful:

`src/rossmann_forecasting/app/demo_dashboard_presenters.py`

Provide a separate local synthetic entrypoint only if needed:

`demo_streamlit_app.py`

Create focused tests:

`tests/test_public_demo_dashboard.py`

Optional focused pure-presenter tests may be added when justified.

### Important isolation rule

Do NOT modify these accepted canonical files:

- `src/rossmann_forecasting/app/dashboard.py`
- `src/rossmann_forecasting/app/dashboard_presenters.py`
- `streamlit_app.py`
- `.streamlit/config.toml`

Do not change the default canonical dashboard entrypoint.

Do not make canonical `run_dashboard()` automatically select synthetic services.

Do not alter existing canonical dashboard widget keys, selectors, or scientific captions.

The new synthetic UI should have a separate explicit renderer such as:

`run_demo_dashboard(services: DemoServices)`

It must receive a verified service instance rather than constructing one from arbitrary widget inputs.

Do not instantiate canonical `ApplicationServices` anywhere in the new synthetic dashboard.

## 6. Explicit trusted configuration

A runnable synthetic entrypoint may obtain configuration from an explicitly documented, trusted local process configuration.

For example:

- `ROSSMANN_DEMO_PROFILE`
- `ROSSMANN_DEMO_MANIFEST_SHA256`

If those names are chosen, document and test them consistently.

The profile must explicitly equal the controlled-synthetic profile.

The manifest pin must be a separately supplied, lowercase SHA-256 digest.

No pin may be read from the untrusted release manifest as its own expected identity.

Do not:

- Hardcode a historical or fixture manifest pin.
- Accept a user-entered manifest pin in a Streamlit widget.
- Accept user-selected release directories.
- Scan for available release files.
- Switch to canonical services when configuration is missing.
- Download a release automatically.
- Regenerate a missing bundle.
- Fall back to a different release revision.

For missing or malformed configuration, show a fixed, sanitized setup/unavailable state without displaying secrets or local paths.

For missing or invalid pinned release content, fail closed and show a controlled-synthetic unavailable message.

Do not expose Python tracebacks or host configuration.

### Rerun and caching semantics

Streamlit reruns must not cause inconsistent provider state.

If the implementation retains a verified provider between reruns:

- Scope it to the explicitly configured profile and manifest pin.
- Avoid sharing a provider across differing trusted configurations.
- Never silently retain an old service after a changed or invalid pin.
- Avoid repeated filesystem verification on each analytical widget interaction.
- Document when a new verified construction is required.
- Preserve the B1 guarantee that service queries read only immutable verified in-memory data.

Use minimal session-local state or bounded caching if necessary.

Do not introduce a cross-user mutable cache.

No external networking is needed.

## 7. Global scientific evidence banner

Every screen must prominently display a persistent label:

`CONTROLLED SYNTHETIC DEMONSTRATION — NOT OBSERVED ROSSMANN DATA`

Also display the relevant verified release identity and a concise limitation appropriate to the screen.

Keep source identity machine-readable where feasible through tables or expander content.

Use the exact `SyntheticProvenance` fields:

- `release_id`
- `evidence_kind`
- `bundle_sha256`
- `manifest_sha256`
- `schema_version`
- `source_kind`
- `view_id`
- `selected_rows`

Do not invent canonical Phase/run/model-selection IDs.

A SHA-256 identity is not evidence of independent distribution permission, authenticated authorship, or empirical validity.

The dashboard must never describe synthetic figures as observed Rossmann performance.

## 8. Screen 1 — Overview & Evidence

Build an overview showing:

- Fixed release identity.
- Schema version.
- Controlled-synthetic evidence kind.
- Supported Stores 101/202/303.
- The three synthetic forecast origins.
- Available synthetic Fit pairings.
- Three comparison-path identities.
- Two inventory-case identities.
- The six analytical catalog/availability categories.
- Source declaration and limitations.
- Sales and inventory-cost units.
- Provenance.

Use `DemoServices.catalog()`.

Clearly distinguish:

- Verified bundle readiness.
- Individual view availability.
- Application/process availability.

Do not infer a successful HTTP process-health state from the catalog.

Remove canonical-only wording such as:

- Observed Rossmann history.
- Frozen LightGBM winner.
- Empirical calibration.
- Canonical Phase 7/8/9/10 run validation.
- Realized inventory savings.

The page should explain that the saved fixture illustrates a forecasting and decision-support workflow without executing models.

## 9. Screen 2 — Historical Sales

Use:

`DemoServices.sales_history(HistoryQuery(...))`

Selectors:

- Only Stores 101/202/303.
- Dates 2015-05-09 through 2015-07-03.
- Maximum 56 inclusive calendar days.
- Valid chronological ordering.

Default date bounds should be valid for the fixed synthetic release, not the canonical history defaults.

Show:

- The exact stored monetary Sales values.
- A time-series plot with gaps for missing/null data.
- Store and date context.
- Synthetic Open separately from Sales.
- Unknown Open as unknown, not a closure.
- Zero Sales as zero, not missing.
- Missing dates as absent or explicitly missing, not fabricated observations.
- A compact provenance section.

Avoid the phrase "observed source rows" for synthetic rows.

Use labels such as:

`Saved synthetic Sales values`

Do not present the fixture as real historical Rossmann observations.

Do not extrapolate or forecast from the history chart.

## 10. Screen 3 — Forecast Explorer and Uncertainty

Use:

`DemoServices.forecast_issuance(ForecastQuery(...))`

and, for supported pairings:

`DemoServices.forecast_uncertainty(UncertaintyQuery(...))`

### Forecast controls

Provide:

- Store selector using catalog Stores.
- Forecast-origin selector using the three saved origins.
- H1–H14 display options only.

Show the exact stored:

- Target date.
- Horizon.
- Raw forecast.
- Operational forecast.
- Availability flags.
- Synthetic Open eligibility.
- Trajectory identity.
- `model_execution = none`.
- Synthetic provenance.

Keep raw forecast and operational values visually distinct.

A known synthetic closure may leave a raw forecast present while routing the operational value to zero.

Unknown eligibility must not be silently converted to zero.

Do not interpolate missing values for scientific display.

### Uncertainty controls

Only allow the accepted pairings:

- `demo_fit_a` with 2015-06-05.
- `demo_fit_b` with 2015-06-19.

May 22 has no approved uncertainty view.

Display a truthful unavailable state rather than selecting a different origin automatically.

Show:

- Stored daily intervals.
- Stored cumulative uncertainty rows.
- Probabilities 0.90, 0.95 and 0.98.
- Missing values and explicit unavailable reasons.
- Incomplete prefixes.
- Schedule-assumption flags.
- Monetary units.
- Synthetic provenance.

Do not construct new interval bounds or estimate quantiles in the presentation code.

Do not call these empirically calibrated predictive intervals.

If showing interval bands, plot only saved valid values and break lines where values are unavailable.

Do not repurpose the existing canonical Fit `A/B` helper without validating its semantics.

## 11. Screen 4 — Model Comparison

Use:

`DemoServices.model_comparison(ModelComparisonQuery(...))`

The candidate IDs are:

- `demo_path_a`
- `demo_path_b`
- `demo_path_c`

Use the saved synthetic candidate labels and definitions.

Do not relabel them as:

- Seasonal Naive.
- Holt-Winters.
- LightGBM.
- Approved development winner.

Render supported controls for:

- Candidate.
- Population.
- Validation window.
- Scope.
- Metric.
- Horizon when meaningful.
- Store when meaningful.
- Maximum result count.

Use the accepted bounded synthetic allowlists.

Prefer selectors derived from B1 catalog/result metadata and the documented finite bundle contract rather than canonical presenter constants.

Do not invent a metric, population or window that B1 cannot return.

If a valid intersection contains no rows, show an empty result rather than claiming an unavailable release.

If a query would exceed the accepted limit, show a sanitized user-facing validation message.

Display:

- Exact stored metric value.
- Numerator.
- Denominator.
- Unavailable reason.
- Scope and window.
- Candidate label.
- Provenance.

Any chart must plot saved results only.

Do not calculate new MAE, RMSE, MAPE, WAPE or winner rankings.

Do not imply the synthetic comparison establishes real model superiority.

## 12. Screen 5 — Inventory Comparison

Use:

`DemoServices.inventory_comparison(InventoryComparisonQuery(...))`

The accepted cases are:

- `synthetic_demo_reference_20150605`
- `synthetic_demo_adverse_20150605`

Provide:

- Case selector.
- Optional Store-level detail selector.
- Case-wide aggregate table.
- Store-level baseline and forecast-policy detail.
- Signed illustrative cost difference.
- Unavailability and null reasons.
- Source/provenance declaration.

### Critical aggregate rule

Store filtering must affect policy-pair detail only.

It must NOT alter the case-level aggregate population, denominators or saved case-wide values.

Clearly label case aggregates:

`All Stores in the selected synthetic case`

Clearly label filtered detail:

`Selected Store policy detail`

Preserve signed differences:

- Reference case: negative differences for Stores 101, 202 and 303.
- Adverse case: positive differences for Stores 101 and 202; Store 303 unavailable.

Do not turn signed differences into absolute values or force all negatives to be improvements.

Use the stored inventory-cost proxy units.

Do not describe the fixture as observed physical stock, SKU inventory, real stockouts or documented monetary savings.

If a value is null or comparison is unavailable, show the reason rather than `0`.

Do not invoke the Phase 10 simulator.

## 13. Presentation-only transformations

Pure display helpers may:

- Convert frozen DTOs to chart/table records.
- Format dates.
- Format numbers.
- Map exact saved values to labels.
- Select rows from already returned results.
- Produce plotting coordinates.
- Group saved rows for visual organization.

They must not:

- Recalculate scientific metrics.
- Estimate forecast error.
- Build new forecasts.
- Calibrate interval bounds.
- Derive new inventory policy targets.
- Reaggregate case-wide inventory results.
- Fill missing scientific values.
- Infer unavailable operational values.
- Reclassify candidate performance.

Use small, type-aware helper functions.

Charts and tables must be deterministic under identical service inputs.

Avoid unsafe HTML and untrusted Markdown rendering.

Close Matplotlib figures after rendering.

## 14. Error handling and availability

Handle B1's sanitized exceptions:

- `DemoInvalidRequestError`
- `DemoReleaseUnavailableError`
- `DemoReleaseIntegrityError`
- Other bounded `DemoProviderError` cases.

Display concise fixed error messages.

Do not show:

- Filesystem paths.
- Stack traces.
- Environment variables.
- Raw manifest content.
- Package or lock metadata.
- Arbitrary exception representations.
- Secrets.

Differentiate:

- Invalid user-selected analytical query.
- Verified release unavailable.
- Verified release invalid.
- Valid empty query result.
- Saved scientific values unavailable.

No failure may trigger canonical fallback.

Show source/evidence warnings even on unavailable screens.

Do not implement an automatic repair/retry/download button.

## 15. Resolve WP2-S14-01

Modify the existing permanent test:

`tests/test_public_demo_api.py`

Finding:

`WP2-S14-01 — MINOR`

The current reference-case inventory aggregate assertion compares two unfiltered requests.

Required correction:

1. Change the reference-case filtered request to include Store 101.
2. Assert that returned policy-pair detail contains only Store 101.
3. Make a separate unfiltered request for the same reference case.
4. Compare case-level aggregates between filtered and unfiltered responses.
5. Check that their exact population and denominators are identical.
6. Preserve the adverse Store 303 unavailable test.
7. Add the same aggregate-scope check for an appropriate filtered adverse case, where useful.
8. Preserve all prior API contract tests.
9. Record the finding as resolved only after actual regression tests pass.

Keep this correction narrow.

Do not change production API or B1 service behavior to satisfy the test.

## 16. Streamlit AppTest coverage

Add focused `streamlit.testing.v1.AppTest` coverage.

Use controlled-synthetic temporary fixtures and independently supplied test manifest pins.

Exercise all five screens.

Required scenarios include:

### App startup

- Valid explicitly configured services.
- Absent configuration.
- Invalid profile.
- Malformed manifest pin.
- Missing release.
- Wrong pin.
- Tampered release.
- No canonical fallback.
- No import-time release scan.
- No silent use of a previously cached service under changed configuration.

### Overview

- Persistent synthetic label.
- Exact catalog identities.
- Six availability records.
- Correct source declaration.
- No LightGBM winner/empirical claims.
- Consistent provenance.

### History

- All three Stores.
- Correct 56-day limit.
- Empty selection behavior.
- Sparse dates.
- Null versus zero.
- Unknown synthetic Open.
- Chart/table alignment.

### Forecast Explorer

- All three origins.
- H1–H14.
- Both saved forecast paths.
- Known closure routing.
- Unknown eligibility.
- May 22 uncertainty unavailable.
- Both valid June Fit pairings.
- Incomplete cumulative prefixes.
- Probability/interval labels.
- No recomputation.

### Model Comparison

- All three synthetic paths.
- Exact saved metrics and labels.
- Supported filters.
- Valid empty intersections.
- Limit boundaries.
- No fabricated winner.
- No canonical candidate names.

### Inventory Comparison

- Both cases.
- All Store filters.
- Case-wide aggregates unchanged by Store selection.
- Signed differences.
- Store 303 adverse-case unavailable.
- No claim of physical stock or savings.

### Cross-screen behavior

- Navigation stability.
- Session-state isolation.
- No stale values after switching Stores/origins/cases.
- No cross-screen selector collision.
- No dependency on FastAPI HTTP.
- No filesystem read after verified provider construction.
- No network calls.
- No scientific module execution.
- No unexpected traceback exposure.
- Correct source banner and provenance on every screen.

Use independently specified expected values for representative output cases.

Do not merely snapshot the dashboard's own generated tables without checking expected scientific meaning.

Tests may render charts with a headless backend.

Do not launch a browser or Streamlit listener.

## 17. Preserve canonical compatibility

Run existing canonical Streamlit regression and AppTest tests.

Verify:

- Existing `streamlit_app.py` remains unchanged.
- Existing `run_dashboard()` remains unchanged.
- Existing canonical page text and selectors remain unchanged.
- Canonical Fit IDs stay `A/B`.
- Synthetic Fit IDs stay `demo_fit_a/demo_fit_b`.
- Existing localhost deployment settings remain unchanged.
- Existing canonical API module remains unchanged.
- New synthetic modules do not instantiate `ApplicationServices` or read canonical artifacts.
- Importing the new entrypoint does not mutate canonical Streamlit global state.
- No shared mutable cache contaminates canonical and synthetic service instances.

If code sharing would require changing established canonical presenters, prefer a small synthetic-specific pure helper instead.

Do not make a substantial shared-presenter refactor without an explicit design review.

## 18. Strict scope

Expected implementation paths:

- `src/rossmann_forecasting/app/demo_dashboard.py`
- Optional `src/rossmann_forecasting/app/demo_dashboard_presenters.py`
- Optional `demo_streamlit_app.py`
- `tests/test_public_demo_dashboard.py`
- `tests/test_public_demo_api.py` for WP2-S14-01
- `docs/PROGRESS.md`
- `plans/active/public-course-demo.md`

Only create additional tests if directly justified.

Do not modify:

- `src/rossmann_forecasting/app/dashboard.py`
- `src/rossmann_forecasting/app/dashboard_presenters.py`
- `src/rossmann_forecasting/app/api.py`
- `src/rossmann_forecasting/app/demo_api.py`
- `src/rossmann_forecasting/app/demo_provider.py`
- `src/rossmann_forecasting/app/demo_services.py`
- `src/rossmann_forecasting/app/demo_bundle.py`
- `streamlit_app.py`
- `.streamlit/config.toml`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/quality.yml`
- Scientific and canonical artifact-reader modules.

Do not add hosting configuration, Dockerfiles, Render files or deployment scripts.

If an essential dashboard requirement cannot be satisfied without changing an accepted B1/B2-A contract or the canonical dashboard, stop and report `DESIGN_REVIEW_REQUIRED` rather than silently expanding scope.

## 19. Documentation updates

Update:

- `docs/PROGRESS.md`
- `plans/active/public-course-demo.md`

Record actual B2-A integration evidence:

- PR #54.
- Publication head:
  `26eaed63f272cb931275b080e66b7eb982fb9790`
- Tested temporary PR merge-ref:
  `bc547266b964924beab06e3fe732eede16326b26`
- Squash merge:
  `232c7307f75d1ae7906af621853a8753ebe81795`
- PR Quality run:
  `39934550249`
- Post-merge Quality run:
  `39935158003`
- Python 3.12 and 3.14 SUCCESS.

Do not confuse PR workflow head identity with the temporary checkout commit.

Append an accurate correction checkpoint for WP2-S14-01 when the actual new regression test passes.

Document:

- Explicit synthetic dashboard interface.
- Five screen mappings.
- Trusted configuration boundary.
- Verified-service construction behavior.
- Streamlit rerun/cache behavior.
- Local fixture and AppTest evidence.
- Scientific claims intentionally excluded.
- Remaining Milestone B review/integration requirements.
- No public content release or deployment authority.

Status:

`WP2 Milestone B2-B — IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1`

Milestone B overall:

`INCOMPLETE`

Milestone C:

`NOT AUTHORIZED`

Do not mark WP2 complete.

Preserve the historical Milestone A/B1/B2-A checkpoints.

## 20. Validation requirements

Use the locked Python 3.14 development/API/dashboard environment.

Run:

- New Streamlit AppTest suite.
- Corrected API regression test.
- Existing synthetic API tests.
- Existing provider/services tests.
- Existing Milestone A bundle tests.
- Existing canonical dashboard tests.
- Existing canonical API tests.
- Full isolated fixture suite in a tracked-only checkout.
- Ruff lint.
- Ruff format check.
- Markdown validation.
- Offline lock check.
- Dependency consistency check.
- Git whitespace checks.

Record actual commands, counts, skips, warnings and durations.

Do not claim visual human acceptance solely from AppTest success.

Human visual review of the synthetic dashboard may become a separate acceptance step after technical review and local integration.

### Numerical bundle preservation

The generated synthetic numerical bundle must retain:

- Size: 326,074 bytes.
- SHA-256:
  `9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`

Population counts:

`165 / 126 / 6 / 168 / 252 / 126 / 69 / 2 / 6 / 20`

Regenerate in controlled temporary locations only.

Manifest SHA-256 depends on exact source/revision/environment bytes. Record its actual identity; do not force a historical hash.

Do not add generated JSON files to Git.

## 21. Project and authorization boundaries

Preserve:

- ADR-024: existing canonical localhost-only operation.
- ADR-028: unaccepted proposals remain gated.
- ADR-030: narrow future two-URL demonstration objective.
- WP1: still incomplete.
- WP1-S7-01: unresolved under the original real-input contract.
- ADR-029: fixture-only limitations remain.
- Phase 13: separately gated.
- Protected final holdout: never accessed.
- Rossmann source and canonical artifacts: never accessed during this task.

No real-source inference, empirical forecasting, calibration or inventory simulation is authorized.

Do not claim synthetic Sales are observed Rossmann Sales.

Do not claim synthetic inventory comparisons prove actual savings.

Do not:

- Commit.
- Push.
- Open a PR.
- Merge.
- Publish the demo bundle.
- Upload a manifest.
- Create a GitHub Release.
- Start Uvicorn or Streamlit listeners.
- Create public URLs.
- Modify networking/firewall settings.
- Provision Render or Streamlit Community Cloud.
- Execute Milestone C.
- Deploy an external demonstration.

No public content/redistribution approval has been granted.

## 22. Required final report

Respond in English.

### A. Outcome

Choose exactly one:

- `IMPLEMENTED_AWAITING_SOL_REVIEW`
- `PARTIALLY_IMPLEMENTED`
- `DESIGN_REVIEW_REQUIRED`
- `VALIDATION_FAILED`

### B. Git state

Branch, approved main base, complete changed/untracked file inventory, staging/publication state.

### C. Dashboard architecture

Renderer, optional entrypoint, explicit configuration, provider injection, rerun/cache semantics and fail-closed behavior.

### D. Five screen implementation

Describe actual catalog, history, forecast/uncertainty, comparison and inventory rendering, controls, provenance and null semantics.

### E. Scientific integrity and security

Explicit synthetic labeling, no false empirical claims, no canonical fallback, no query-time model execution, no network activity and no data publication.

### F. WP2-S14-01 resolution

Exact permanent test change, filtered/unfiltered aggregate evidence and regression results.

### G. AppTest and compatibility evidence

Actual screen tests, service/API/canonical compatibility, validation counts and observed warnings/skips.

### H. Reproducibility and quality

Generated bundle bytes/hash, manifest identity, Ruff, Markdown, lock, dependencies, whitespace and full-suite evidence.

### I. Snapshot identities

Raw-byte SHA-256 for every changed or new file.

### J. Remaining boundaries

Independent Sol 6.1 review is the next step.

No Git integration, external deployment, public release or Milestone C activity is authorized.

## Final instruction

Implement a separate controlled-synthetic five-screen Streamlit dashboard using only the already integrated, verified B1 Python services.

Keep canonical Streamlit and FastAPI behavior unchanged.

Preserve saved scientific values, incomplete data and case-wide inventory aggregates without recalculation.

Make synthetic evidence identity visible on every screen.

Resolve WP2-S14-01 through a permanent filtered-versus-unfiltered inventory regression test.

Use local AppTest only and keep everything uncommitted and unpublished.

**Begin with Git preflight, B1 DTO inspection and a concise synthetic-dashboard interface contract. Stop when implementation, tests and documentation are ready for independent Sol 6.1 review.**