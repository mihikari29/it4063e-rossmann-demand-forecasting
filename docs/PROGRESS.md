# Project Progress

## Current implementation and Git state — 2026-10-09

| Scope | State | Integration |
|---|---|---|
| Phases 0–4 | COMPLETE | On `main`; Phase 3 PR #3/#4, Phase 4 PR #5/#6 |
| Phase 5 — additive Holt-Winters | COMPLETE | PR #7 squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`; formal closeout recorded here |
| Repository architecture/governance review | COMPLETE | Integrated with Phase 5 by PR #7 at `76707a03b7d10dbaa79d3ef26b39e31994431d70` |
| Phase 6 — Global LightGBM | COMPLETE | [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10) merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; [completed plan](../plans/completed/phase-6-global-lightgbm.md) |
| Phase 7 — model selection | COMPLETE | [PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`; [completed plan](../plans/completed/phase-7-model-selection.md); selected LightGBM identity and ADR-020 remain intact |
| Phase 8 - forecast uncertainty | COMPLETE | PR #15 merged at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`; PR #16 merged at `4dd7717fed57ff3b1f14789b980772c1968f3cba`; accepted Fit B freeze; [completed plan](../plans/completed/phase-8-forecast-uncertainty.md) |
| Phase 9 — synthetic inventory layer | **COMPLETE** | [Completed plan](../plans/completed/phase-9-synthetic-inventory.md); [PR #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/19) squash-merged at `7451c50ff685d92e8e74b5014d07b3bbfaca0a22` |
| Phase 10 - inventory simulation | **COMPLETE** | PR #23 `15bce83cd63a4edfeed6defb95788da90d0f36d9`; PR #24 `fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`; closeout PR #25 merged at `d437269b9f0cf36a842cdfd496ad50a310804768`; [completed plan](../plans/completed/phase-10-inventory-simulation.md) |
| Phase 11 — Application Services & Thin API | **COMPLETE** | PR #26 squash-merged into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; [completed plan](../plans/completed/phase-11-application-services.md) |
| Phase 12 - Streamlit Dashboard | M1 ACCEPTED / INTEGRATED; M2 ACCEPTED / INTEGRATED; M3 IMPLEMENTED / UNDER REVIEW | M2 PR #30 merged at `327a274bfdad0bb97cdd614a36dc04cbbf8291a2`. M3 branch `feat/phase-12-streamlit-m3` starts directly from that `main` SHA and is in [draft PR #31](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/31), open and unmerged; [active plan](../plans/active/phase-12-streamlit-dashboard.md). M4 NOT AUTHORIZED; deployment undecided; Phase 13 unauthorized. |

At closeout start, the clean `docs/phase-5-closeout` branch was created from fetched latest
`origin/main`; both resolved to `76707a03b7d10dbaa79d3ef26b39e31994431d70`, the actual PR #7
squash-merge commit reported by GitHub. PR #7 is merged into `main`. The merged tree contains the
reusable Holt-Winters forecaster, development runner, evaluation code, and tests. The closeout
changes lifecycle/documentation only: no forecasting algorithm or historical metric is changed, and
no final-holdout forecast or evaluation was performed. Main protection was reported disabled in
the 2026-10-05 branch-metadata snapshot; no settings were changed.

Completed plans under `plans/completed/` preserve their historical approval/results/checkpoint
records, including the [completed Phase 5 plan](../plans/completed/phase-5-statistical-forecasting.md).
PROGRESS is the canonical maintained numerical-results record; duplicated plan tables are dated
snapshots, not separate results to update. Phase 7's development-only selection is integrated and
formally closed. Its result and closeout do not constitute final-holdout evaluation or production
approval. Phase 8 methodology is approved in ADR-021; implementation PR #15 and results-acceptance
PR #16 are integrated, and the external results review accepted the canonical development run.
Fit B values are frozen for that run. Phase 8 is COMPLETE following the explicit closeout recorded
below and in the completed plan. Phase 9 is COMPLETE after PR #19 integration, accepted independent
implementation and numerical review, and formal closeout. Its accepted canonical run and manifest
are recorded below and were not regenerated. Phase 10 methodology is accepted under ADR-023. PR #23 integrated the implementation at
`15bce83cd63a4edfeed6defb95788da90d0f36d9`; corrective PR #24 integrated the B1-B3 fixes at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. Final focused independent external/model-assisted review
accepted the implementation and numerical evidence. Closeout PR #25 was squash-merged into `main`
at `d437269b9f0cf36a842cdfd496ad50a310804768`; Phase 10 is COMPLETE. Phase 11 is COMPLETE after
PR #26 squash-merged into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; M1-M4 are accepted,
M3-01, M4-01 and FR-01 are resolved, and post-merge Quality #81 passed. The [completed Phase 11
plan](../plans/completed/phase-11-application-services.md) preserves its acceptance and handoff
record. The protected final holdout remains unreleased.

### Phase 11 formal closeout — 2026-10-09

The Technical Lead authorized documentation-only formal closeout after verifying PR #26's squash
merge into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`. The original feature branch was
`feat/phase-11-application-services`, and the final reviewed PR head was
`77128a3b589cbe662833962cd20aacb03241dd55`. M1-M4 are accepted; independent reviews returned M1
`ACCEPT`, M2 `ACCEPT`, M3 `ACCEPT_WITH_MINOR_CHANGES`, M4 `ACCEPT_WITH_MINOR_CHANGES`, and the final
full-PR merge-readiness review returned `READY_WITH_MINOR_CHANGES`. Findings M3-01, M4-01 and FR-01
were resolved before merge. All implementation and integration gates are satisfied.

Post-merge GitHub Quality [#81](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37902479835)
passed at the squash merge SHA on Python 3.12 and 3.14. The previously accepted baselines were 431
full-suite tests and 151 focused application tests. For this closeout, the full suite was rerun and
431 passed; the 151-test focused subset was not rerun. The nonblocking Starlette TestClient
deprecation warning remains. Earlier accepted Quality #80 evidence and milestone checkpoints remain
recorded in the archived plan and historical entries below.

The application serves saved development forecasts without new inference. Historical access ends on
2015-07-03 and projects only Store, Date, Sales and Open; Customers are not exposed. Sales are
monetary turnover; saved uncertainty is empirical without guaranteed coverage; inventory outputs
are conditional synthetic monetary simulations, not observed physical inventory, actual stockouts,
proven savings or validated optimal policies. Positive forecast-minus-baseline simulated cost is
adverse: the accepted reference difference is +1,842,931.0502027555 and `buffer_090` is
+2,657,553.7797287568, both existing results and not new calculations. The protected July 4-31
holdout remains unreleased. The Phase 10 simulation ledger and canonical artifacts were not read,
hashed, regenerated or changed. No real-data forecast fit, final-holdout evaluation, recalibration
or canonical simulation/artifact regeneration was performed; the closeout repository test run used
the fixture suite. Phase 12 and Phase 13 remain outside this authorization.

### Phase 12 architecture audit and design proposal — 2026-10-09

The authorized task is design documentation, commit/push and a draft PR only. The worktree was clean
on the already merged `docs/phase-11-closeout` branch. Fetch and live GitHub metadata verified
`origin/main` at `2a47ae7dd959daac8eacf2b5410f090edbbcd7cb`, the actual PR #27 Phase 11 closeout
merge; all 27 existing PRs were merged and none open. The new `docs/phase-12-streamlit-design`
branch starts directly from that main SHA. Phase 11 remains COMPLETE.

The [active Phase 12 plan](../plans/active/phase-12-streamlit-dashboard.md) audits the existing
reader/service/API contracts and tests, proposes five screens using direct `ApplicationServices`
calls, and separates the seven candidate content sections into implementation-ready specifications.
Four proposed milestones have bounded Luna 6 task/review boundaries. Public service DTO omissions
limit richer EDA, calibration diagnostics, structured case selectors and operational parameters;
the core proposes bounded Sales/Open history and saved-case comparisons. It explicitly records
the narrower scope relative to proposal §22 for Technical Lead review without editing the proposal.

Deployment remains undecided; private course LAN is one candidate, subject to later approval that it
satisfies the course requirement. Private canonical-file cloud
provisioning and a separately reviewed reduced DTO evidence snapshot are alternatives, each requiring
additional distribution/contract approval. A clean checkout or synthetic fixtures cannot substitute
for accepted analytical evidence. No source, API, service, model, simulation, dependency or canonical
artifact changed; no canonical artifact contents, ledger or protected outcomes were read/hashed.
Design-task checks passed on Python 3.14.5 / uv 0.12.23: 151 focused application tests and all
431 fixture tests, Ruff lint/format, 259 local documentation destinations/anchors, lock consistency
and installed dependency compatibility, plus diff/scope self-review. The existing nonblocking
Starlette TestClient deprecation warning remains. Detailed check scope is recorded in the active
plan; no Streamlit implementation, UI test or deployment was performed.

At the end of that original design task, Phase 12 was **PROPOSED / AWAITING REVIEW**. That historical
boundary was superseded by the later M1 authorization recorded below; Phase 13 and Phase 14 remain
future work, and the holdout is unreleased.

### Phase 12 M1 implementation checkpoint — 2026-10-09

Technical Lead authorization followed verification that design PR #28 was merged into `main` at
`9b4ab7f54abff0ca1abfe8b6c547de960c8be8b1`. M1 is limited to the Streamlit shell, static overview
and catalog/readiness presentation, pure display helpers, sanitized UI errors and fixture-backed
tests. The other four screens remain data-free placeholders and make no service queries. The
optional dashboard extra is used only by the dashboard and AppTest suite; pandas/matplotlib remain
the visualization foundation. Deployment is undecided, the proposal's interactive what-if scope is
excluded from M1–M3, and M2–M4 and Phase 13 remain unauthorized. No holdout or ledger access is
authorized.

Implementation branch: `feat/phase-12-streamlit-m1`, based directly on the verified merge SHA above.
M1 is IMPLEMENTED / UNDER REVIEW only; it is not accepted, merged or a Phase 12 closeout. The
focused UI/presenter tests passed (13 before the final empty-checkout test was added); the final
suite includes 14 dashboard tests. Whole-repository pytest passed with 445 tests on Python 3.12 and
445 on Python 3.14, each with one existing Starlette/httpx deprecation warning. The 3.12 run used a
locked isolated uv environment; the 3.14 run used the locked project environment.

Ruff lint and format checks passed (102 files formatted), documentation links passed (259 local
destinations/anchors across 27 Markdown files), `uv lock --check` passed with 109 resolved packages,
and `uv pip check` passed with 93 compatible installed packages. The dashboard extra resolves
Streamlit 1.65.0 under `streamlit>=1.50,<2`. AppTests use temporary fixture roots; the empty-checkout
case renders static content and unavailable statuses without provenance, while the corrupt-catalog
case displays a fixed integrity error without a local path. Navigation tests confirm that only the
overview calls `catalog()` and its reader opens only the Phase 9 scenario catalog and Phase 10
comparison output. No manual browser/performance test, real-data pipeline, deployment, canonical
artifact regeneration, ledger access or protected holdout access was performed.

The feature branch is pushed in [draft PR #29](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/29)
targeting `main`; the final task report records its current head SHA. M2–M4 remain unauthorized;
do not merge or start subsequent work.

### Phase 12 M1 independent review corrections — 2026-10-09

The narrow corrective task addresses review findings M1-01 through M1-03 on the existing PR #29
branch. M1-01 adds an explicit **Refresh resource status** button to Overview. Each click reruns
the existing `catalog()` service under its existing lock and reader validation; no new application
cache or inference/artifact-generation path is introduced. An AppTest removes a fixture scenario
artifact, verifies the unavailable state, restores its original bytes, clicks refresh, and verifies
recovery and provenance. The reader spy confirms each run reads only the Phase 9 scenario catalog
and Phase 10 comparison resources.

M1-02 moves both resource-readiness and provenance conversions inside a sanitized presentation
boundary and completes both before emitting resource tables/status cards. Invalid injected resource
and provenance DTOs each render the fixed `internal_error` notice with no partial table or path.
The existing `ArtifactReadError` mapping is unchanged. M1-03 replaces catalog-specific shared error
copy with resource-neutral language. Table-driven tests preserve all stable error codes and distinct
unavailable, integrity, schema, duplicate-key, unsupported-selector, invalid-request and unsafe-path
messages without raw exception details. Focused dashboard/presenter tests pass (**24 passed**).

Whole-repository pytest passed on Python 3.12 and 3.14 (**455 passed each**) with the existing
Starlette/httpx deprecation warning. Python 3.12 used the locked isolated uv environment with dev,
API and dashboard extras; Python 3.14 used the locked project environment. Ruff lint and format
passed (102 files formatted), documentation links passed (259 local destinations/anchors across 27
Markdown files), `uv lock --check` passed (109 resolved packages), `uv pip check` passed (93
compatible installed packages), and `git diff --check` passed. No dependency or lockfile changed.

GitHub's Python 3.12/3.14 Quality result and PR metadata are verified after the corrective push and
reported in the final task handoff. M1 remains IMPLEMENTED / UNDER REVIEW; PR #29 remains draft and
unmerged. No model inference, canonical artifact generation, real-data pipeline, ledger access,
protected holdout access or deployment occurred.

### Phase 12 M1 integration and M2 implementation checkpoint — 2026-10-09

PR #29 was accepted and squash-merged into `main` at
`cb508a0bbdefe6afeba6e1ea8ebad5a0614a03f6`. The reviewed M1 head
`2460b3d59ef1fce90702719c59501e84dd5f36af` has the same Git tree as the merge. The conditional M2
authorization gate is satisfied. Branch `feat/phase-12-streamlit-m2` starts directly from that main
SHA. M1 is ACCEPTED / INTEGRATED; M2 is IMPLEMENTED / UNDER REVIEW. This does not close Phase 12.

M2 implements the Historical Sales and Forecast Explorer/uncertainty screens from the approved
plan. The UI uses only `catalog()`, `sales_history(HistoryQuery)`,
`forecast_issuance(ForecastQuery)` and `forecast_uncertainty(UncertaintyQuery)` with the existing
DTOs. It adds no service, model inference, analytical producer change, metric, inventory assumption,
dependency or lockfile change. History validates Store/date bounds before dispatch and distinguishes
observed zero, null and missing calendar dates. Forecast output is saved H14; H7 filters display
only. Raw/operational availability stays separate. Fit A/June 5 and Fit B/June 19 map from the
catalog; May 22 sends no uncertainty request. Daily and cumulative saved values, unavailable
reasons and their separate provenance are retained without recalculation or rounding.

The UI labels history as retrospective development evidence, displays source Open separately,
describes operational routing as a conditional historical replay, and exposes empirical/sparse
uncertainty limitations. It does not access Customers, model-comparison results, inventory ledgers,
or July 4–31 protected outcomes. M3/M4 remain NOT AUTHORIZED, deployment remains pending, and the
Phase 13 holdout remains protected.

Focused dashboard/presenter/M2 tests passed (**64 passed**). The full fixture suite passed on Python
3.12 (**495 passed**) and Python 3.14 (**495 passed**); each run reported the existing
Starlette/httpx deprecation warning. Ruff lint/format passed (103 files already formatted),
`uv lock --check` passed with 109 resolved packages, and `uv pip check` passed with 93 compatible
packages. `scripts/check_docs.py` passed with 259 local destinations/anchors across 27 Markdown
files, and `git diff --check` passed. Git emitted configured LF-to-CRLF normalization notices for
modified files.

The optional read-only development smoke used Store 1, history 2015-06-19–2015-07-03, the June 19
H14 forecast and Fit B uncertainty. It returned 15 history rows, 14 forecast rows (14 raw and 14
operational available), 28 daily interval rows and 42 cumulative rows, with the service's saved
provenance. No source values were printed, no artifact was changed or regenerated, and the Phase 10
ledger and protected holdout were not accessed. No manual browser, performance or deployment test
was performed.

## Immediate next boundary

Phase 5 is formally COMPLETE following PR #7 integration and PR #8 closeout. Phase 6 is **COMPLETE**:
ADR-019 remains accepted, and [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10)
was merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed plan is
archived.
The Phase 6 development-only results and coverage evidence remain recorded below. Phase 6 closeout
[PR #11](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/11) merged at
`0b8d55144ace29cb8b5367d11aeedc59cfb33a65`. Phase 7 methodology is approved in ADR-020, and
[PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged into
`main` at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`. Phase 7 is **COMPLETE**; the selected
`global_lightgbm_gbdt_regression_l1` recipe remains trial A at exactly 180 rounds.
Phase 8 implementation/results were accepted after PR #15 merged at
`c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`; the Fit B freeze was integrated by PR #16 at
`4dd7717fed57ff3b1f14789b980772c1968f3cba`. Phase 8 is **COMPLETE** following the closeout
recorded below. Its completed plan preserves the approved method and review checkpoints.
Final-holdout evaluation remains unreleased. The
[historical Phase 6 implementation handoff](PROJECT_PLAN.md#phase-6-implementation-handoff-historical)
records the interfaces and boundary used.

PR #17 integrated Phase 8's formal closeout at `f08a62aa980d0670186ed25ae1f6e5a018ff3781`.
PR #18 integrated the accepted Phase 9 design and ADR-022 at
`97795ca5d868b512e5c2f6cae59bcec1d6ce19a4`. PR #19 subsequently merged into `main` at
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22`, completing Phase 9 after independent implementation
and numerical review acceptance. PR #20 merged into `main` at
`ff3c11554144e79ee84c627c2bcd3619d23072d0`; that commit is integrated into the current `origin/main`.
The PR #19 branch was synchronized by merging `origin/main`, preserving the uppercase canonical
proposal path and its unchanged content. At the Phase 9 closeout checkpoint, Phase 10's review,
queue, policy and comparison design was outside the accepted scope; the subsequent ADR-023
approval is recorded below. No final-holdout release or access is authorized.

The [completed Phase 10 plan](../plans/completed/phase-10-inventory-simulation.md) and accepted
[ADR-023](DECISIONS.md#adr-023--origin-frozen-daily-inventory-policy-simulation-and-finite-window-accounting)
record the methodology and lifecycle. The current canonical development run is
`phase10-dev-20261008-validator-fix`, manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`. PR #23 and corrective PR #24
are integrated at the SHAs in the current-state table. Phase 10's final closeout is recorded in the
completed plan; Phase 10 is COMPLETE after closeout PR #25 merged into `main` at
`d437269b9f0cf36a842cdfd496ad50a310804768`. Phase 11 M1, M2 and M3 are formally accepted;
M3-01 is resolved; M4 is accepted with minor changes; and M4-01 is resolved by this correction.
Phase 11 is COMPLETE following PR #26 squash merge at
`725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; its [completed plan](../plans/completed/phase-11-application-services.md)
records formal acceptance. Phase 12 M1 is IMPLEMENTED / UNDER REVIEW on the feature branch, as
recorded in the [active plan](../plans/active/phase-12-streamlit-dashboard.md); the current
checkpoint below supersedes that earlier M1-only state: M1 is ACCEPTED / INTEGRATED and M2 is
IMPLEMENTED / UNDER REVIEW. M3/M4 remain unauthorized. Phase 13 still requires a
separate frozen protocol and explicit authorization to release holdout outcomes. The holdout remains
unreleased.

The current forecasting firewall excludes July 4–31 from tuning/selection/calibration and has
produced no final-holdout forecasts/metrics; final-holdout evaluation remains unreleased. Earlier
full-source validation and descriptive EDA
did include those labels; [EDA_FINDINGS](EDA_FINDINGS.md) records that exposure. Do not claim an
entirely never-inspected test set or reuse those full-period cohorts for modeling. ADR-015 defers
the single authorized sequential final evaluation until model, intervals and policies are frozen.

### Phase 11 M1 implementation and review-fix checkpoint — 2026-10-08

M1 provides typed contracts and fixed, read-only readers for the accepted Phase 7–10 canonical
outputs, plus a bounded historical Sales reader. Phase 7/8 projected Parquet fields are checked
against their accepted Arrow types; Phase 9/10 artifacts are checked against producer schemas and
mandatory manifest descriptors, including field nullability. CSV fields are read with nullable
string, integer, float and boolean types; malformed numeric/boolean values and missing required
identifiers are rejected while documented unavailable values remain null. Model-comparison nulls
are allowed only in optional grouping-key fields. Output hash memoization remains process-local under
the immutable, locally trusted artifact assumption: fingerprint changes trigger rehashing, while
matching metadata does not prove byte immutability. There is no selector for the Phase 10 ledger and
no `current.json` fallback.

The history reader accepts one Store and at most 366 days from 2013-01-01 through 2015-07-03. It
rejects unsupported query dates before opening the dataset and accepts only the prepared source's
timezone-naive `timestamp[ns]` Date schema. The fixed `Store`, `Date`, `Sales`, `Open` projection and
Store/date predicate are applied in Arrow before materialization. Fixtures cover extreme dates,
timezone-aware schemas/requests, sanitized conversion errors, and the protected cutoff. Selection-
driven case/Store reads from Phase 10 summaries remain an M2 prerequisite; M1 retains fixed
projections. A read-only smoke read passed for all ten registered outputs (including Phase 10 summary
and target tables); the simulation ledger was not read. No forecast or inventory output was
regenerated, and no protected July 4–31 outcome rows were inspected.

Validation on the existing Python 3.14.5 environment: the full pytest suite passed (332 tests),
including the focused app-reader suite; Ruff lint and format, documentation links, `git diff --check`,
`uv lock --check` (84 resolved packages), and `uv pip check` (62 compatible installed packages)
passed. No dependency or lockfile changed. M1 remains **IMPLEMENTED / UNDER REVIEW** pending
independent acceptance; Phase 11 is not complete, and M2–M4, final-holdout access and merge remain
outside this authorization.

The targeted M1 correctness fix rejects any CSV source containing an embedded NUL before pandas
tokenization. The bounded 1 MiB byte scan runs in the same pass as output SHA-256 verification;
matching verified fingerprints reuse that result under the documented immutable local-artifact
assumption, and changed fingerprints trigger a fresh hash and scan. Public-reader fixtures cover
all three reproduced integer-token bypasses, NUL bytes in string columns across all four CSV
selectors, a NUL outside field data, and unchanged values, UTF-8, nullable `Int64`, row counts and
source bytes for valid CSVs. Focused reader tests passed (80 tests), and the full suite passed (360
tests). Ruff, formatting, documentation links, `git diff --check`, lock consistency (84 packages)
and installed dependency compatibility (62 packages) passed. Read-only smoke reads passed for all
ten registered canonical development outputs; output, manifest and binding sizes and modification
times were unchanged. The Phase 10 ledger and final holdout were not read. M1 remains
**IMPLEMENTED / UNDER REVIEW**; M2–M4 remained unauthorized at that checkpoint.

### Phase 11 M1 acceptance and M2 implementation checkpoint — 2026-10-08

The Technical Lead formally accepted M1 after the final independent targeted review returned
`ACCEPT` on exact PR #26 head `1fef9c7f27cb27068f8fcb415378771b878d4aed`. The PR remains open,
draft and unmerged; `main` remains at Phase 10 closeout commit
`d437269b9f0cf36a842cdfd496ad50a310804768`. This records M1 review acceptance, not phase completion
or integration.

The Technical Lead authorized M2 on the same branch and PR. M2 is in implementation and remains
pending independent review. Before code changes, the active plan froze supported selectors, query
bounds, service response whitelists, selective-read integrity behavior and comparison semantics
against the producer contracts. M2 is limited to shared read-only services and fixture tests;
M3–M4 remain unauthorized, PR #26 must stay draft/unmerged, and no final-holdout outcome, inference,
or Phase 10 ledger artifact is part of this work.

### Phase 11 M2 initial implementation checkpoint — 2026-10-08

M2 adds closed typed queries and bounded shared services for readiness/catalog, forecast issuance,
saved uncertainty, model comparisons, policy comparisons and the existing cutoff-safe history reader.
Parquet selection uses Arrow predicates after full-file hash, footer schema and global manifest-row
verification; selected rows have independent bounds. Large CSV comparisons stream exact matches and
never materialize the complete Phase 7 comparison frame. Service DTOs whitelist response fields,
preserve unavailable values and provenance, reject non-finite JSON numbers, and do not expose artifact
paths. The corrective checkpoint below fixes the initial `pd.NaT` serialization edge case. Policy
cost differences are shown only for valid complete matched pairs; producer case-level comparisons,
denominators and signed adverse results remain unchanged.

Initial implementation validation on Python 3.14.5: focused app-reader/service tests passed (**98**);
full pytest passed (**379**). Ruff lint and format, documentation links (**229** local destinations/anchors),
`git diff --check`, and the environment's `pip check` passed. The `uv` executable was not available
in this shell, so `uv lock --check` could not run; no dependency or lockfile changed. A read-only
canonical service smoke covered 10 registered non-ledger resources, 82 scenario entries, 172 case
IDs, all service views, and 1,115 matched Store pairs. Responses were JSON-safe and cutoff-safe;
canonical output and manifest sizes/modification times were unchanged. No final-holdout outcomes,
Phase 10 ledger, or raw historical source data were read; no artifact was generated or mutated.

M2 is **IMPLEMENTED / UNDER REVIEW** pending independent review. M1 remains reviewed/accepted on the
unmerged feature branch. PR #26 stays draft and unmerged; M3–M4 remain unauthorized and Phase 11 is
not complete.

### Phase 11 M2 corrective review-fix checkpoint — 2026-10-09

The targeted correction separates target unavailability from episode failure in each policy DTO and
allows baseline and forecast validity/availability to differ. A pair is comparable only when both
episodes are complete, both targets are available with saved values, both matched-comparison flags
are true, and both saved costs exist. For a non-comparable pair, the stable reason priority is:
first incomplete episode (using that policy's summary reason), then unavailable target (using that
policy's target reason), then invalid matched comparison, then unavailable saved cost. Available
targets with null values and unavailable targets with non-null values are rejected as integrity
failures. `json_safe` now converts `pd.NaT` and `pd.NA` to JSON null before date handling.

The earlier test counts above are the initial implementation checkpoint. Corrective validation on
Python 3.14.5: focused app-reader/service tests passed (**107**); full pytest passed (**387**).
Ruff lint and format, documentation links (**229** local destinations/anchors), `git diff --check`,
`uv lock --check` (**84** resolved packages) and installed dependency compatibility (`pip check`)
passed. A read-only canonical service smoke opened all ten registered non-ledger outputs and
confirmed their output hashes, schemas and manifest identities. The base reference and buffer-090
sensitivity case-level forecast-minus-baseline cost differences remained positive (+1,842,931.05
and +2,657,553.78 respectively); all 1,115 Store pairs were comparable for each case. These are
synthetic simulated monetary costs, not observed inventory or proven savings. No Phase 10 ledger,
final-holdout outcome or raw historical source data was read; no producer, canonical artifact or
manifest was changed.

M2 is formally accepted as recorded in the 2026-10-09 review/authorization checkpoint below. M1
remains accepted on the unmerged feature branch; PR #26 stays open, draft and unmerged. M3–M4 were
unauthorized at this historical checkpoint, and Phase 11 was not complete.

### Phase 11 M2 formal acceptance and M3 authorization — 2026-10-09

The Technical Lead formally accepted M2 following the independent `ACCEPT` review of exact PR #26
head `cd7d3319760379716244e4db6c0cf0cb96ec6cbd`. This records the project acceptance checkpoint;
the PR remains draft and unmerged. M1 and M2 are REVIEWED / ACCEPTED on the feature branch.

The Technical Lead separately authorized M3 implementation on the same branch and PR. M3 is
AUTHORIZED / IN IMPLEMENTATION pending independent review. The HTTP route, query, response and
sanitized error contract was frozen in the [completed Phase 11 plan](../plans/completed/phase-11-application-services.md)
before adapter implementation. M4, merge and Phase 11 closeout remain outside this authorization.
The Phase 10 ledger and protected final holdout remain excluded.

### Phase 11 M3 implementation checkpoint — 2026-10-09

Implemented the frozen seven-route, read-only FastAPI adapter in `src/rossmann_forecasting/app/api.py`
over the accepted M2 services. Added fixture-backed endpoint, selector, bound, error-sanitization,
serialization and mutation-method tests in `tests/test_app_api.py`; added optional API dependencies,
locked them, enabled that extra in CI and documented local use. The routes expose only accepted
development artifacts and the M1 bounded Sales history view. No inference, simulation, producer
changes, ledger access or holdout access was added.

The full fixture suite passed: 424 tests on Python 3.14.5 in 119.56 seconds. The M1/M2/M3 focused
suite passed 144 tests. Ruff lint and formatting, Markdown-link validation (230 destinations across
26 files), `uv lock --check`, `pip check` and `git diff --check` passed. The full test run emitted one
upstream Starlette deprecation warning because its TestClient currently uses `httpx`; no test failed.

A canonical-data API smoke returned 200 for all seven routes, including forecast, uncertainty,
comparison, inventory and history. The 82 scenario entries, 172 cases and 1,115 policy pairs were
available as expected. Before/after snapshots confirmed 15 registered non-ledger canonical files
were unchanged. The smoke did not read the simulation ledger, protected holdout or raw historical
source beyond the authorized bounded-history route.

M3 is **IMPLEMENTED / UNDER REVIEW**, pending independent review. GitHub Quality run [#75 /
37882356772](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37882356772)
passed on exact implementation head `8ee9c0639b8598dfe7f79ad6175f4f87a1b030f1` for Python 3.12
and 3.14. PR #26 remains draft and unmerged. M4 remains unauthorized; Phase 11 is not complete.


### Phase 11 M3 formal acceptance and M4 authorization — 2026-10-09

The Technical Lead formally accepted M3 with the single minor follow-up M3-01 after the independent
`ACCEPT_WITH_MINOR_CHANGES` review of exact PR #26 head
`6169e850d824e3f6eccc1faa57b3d4a311646bd6`. M3-01 is the omitted framework-provided `Allow`
header on HTTP 405 responses. The Technical Lead authorized M4 implementation on the same branch
and draft PR. M4 is limited to that correction, cross-layer fixture integration evidence, and
reproducible startup/use guidance and handoff. M1 and M2 remain accepted; Phase 11 remains
incomplete; PR #26 remains draft and unmerged.


### Phase 11 M4 implementation and local verification — 2026-10-09

M4 resolves M3-01 by preserving only Starlette's framework-provided `Allow` header on sanitized
HTTP 405 responses. New fixture-backed HTTP-to-reader tests exercise the shared service chain,
validated artifact provenance, null/unavailable results, Store versus case-level inventory views,
the history cutoff, and process-only health. The tests use synthetic fixtures and do not require
canonical artifacts or Kaggle credentials.

The locked full repository suite passed **431 tests** with one existing Starlette TestClient
deprecation warning. GitHub Quality run #77 passed on exact pushed M4 head
`6f5eaccd7b0f5f11574c4c60e278dc72c0819980` for Python 3.12 and 3.14. The focused
application suites passed **151 tests**; the locked API and integration invocation passed **44 tests**. Ruff, repository formatting (96 Python files), the docs
link/anchor check (232 local targets across 26 documents), locked dependency sync, lock check, and
installed dependency compatibility check passed. The documented local Uvicorn command was started
on `127.0.0.1`; health, catalog, forecast, and inventory reference requests returned 200.

A read-only canonical API smoke made seven successful requests across health, catalog, forecast,
uncertainty, model comparison, and both inventory cases. It returned the pinned 14-point forecast,
28 daily intervals, 42 cumulative prefixes, four comparison rows, and 1,115 policy pairs per case.
Reference and `buffer_090` signed differences remained respectively +1,842,931.0502027555 and
+2,657,553.7797287568. All 15 registered canonical file snapshots were unchanged; the smoke read
no ledger, history source, or holdout. No inference, simulation, or canonical artifact generation
was performed. M4 remains implemented / under independent review; PR #26 remains draft and
unmerged, and Phase 11 remains incomplete.


### Phase 11 M4 acceptance and M4-01 correction - 2026-10-09

The independent M4 review of expected PR #26 head
`db2d8ce47e7704e7beb11f7c7b08fd846ac1619c` returned `ACCEPT_WITH_MINOR_CHANGES`. It confirmed
M3-01 is resolved and identified M4-01 as the sole remaining finding: the current "Immediate next
boundary" paragraph still described M3 as under review and M4 as unauthorized. This documentation-
only correction updates that status; no product finding remains. The Technical Lead formally
accepted M4 with minor changes.

M1, M2 and M3 are formally accepted; M3-01 and M4-01 are resolved; M4 is accepted with minor
changes. The implementation milestones are accepted, but the separate final PR integration and
merge-readiness review and formal Phase 11 closeout remain pending. PR #26 remains open, draft and
unmerged. No final-holdout release is authorized. Prior implementation test totals and canonical
results remain recorded in the preceding M4 checkpoint.


## Branch cleanup inventory

GitHub snapshot, 2026-10-05; cleanup is recommended only after checking unique commits and working
changes. No local or remote branches were deleted in this review.

| Candidate branch | Merged work | Disposition |
|---|---|---|
| `feat/data-preparation-eda` | [PR #2](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/2) | Retire after unique-change check |
| `feat/feature-engineering` | [PR #3](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/3) | Retire after unique-change check |
| `docs/phase-3-closeout` | [PR #4](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/4) | Retire after unique-change check |
| `feat/seasonal-naive` | [PR #5](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/5) | Retire after unique-change check |
| `docs/phase-4-closeout` | [PR #6](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/6) | Retire after unique-change check |

`feat/holt-winters` is active, not a cleanup candidate. The old
`origin/feat/data-acquisition-validation` exists only as a stale local tracking ref: that branch
is absent from GitHub's current branch list. Prune it during authorized maintenance. Main and this
review branch are retained; fresh work should not continue on merged branches.

## Source and Preparation Evidence

- Official raw CSVs remain unchanged and Git-ignored; their four SHA-256 hashes matched the
  documented source snapshot before and after preparation.
- Historical train: 1,017,209 rows, 1,115 stores, 2013-01-01 through 2015-07-31. Test: 41,088
  future-covariate rows, 856 stores, 2015-08-01 through 2015-09-17. Both metadata joins preserve
  row counts and unique Store × Date keys.
- The sparse historical output retains all source rows, including closed and open/zero-Sales days.
  No synthetic calendar rows or zero fills were added. Test remains separate and has no Sales or
  Customers.
- The 180-store 184-day gap, 54 open/zero-Sales rows, 11 missing test Open statuses, and 259
  metadata stores unused by test have documented evidence and dispositions. Store 622's original
  missing Open statuses remain null in `test.parquet`; the separate audit output contains 11
  uncertain unanimous historical-context candidates.
- Promo2 details retain structural nulls for all 544 nonparticipants. The 354 paired missing
  competition-open dates remain unexplained and unfilled; three missing CompetitionDistance
  values remain missing.
- Ignored Parquet outputs are reproducible through PyArrow 24.0.0. EDA tables, manifests, and
  figures are local generated artifacts under `reports/eda/`.

## Phase 3 Implementation and Closeout Evidence

- `python scripts/build_features.py` completed with contract `phase-3-v1`: 1,017,209 training
  rows and 41,088 inference rows, preserving input Store × Date keys and the shared ordered
  29-predictor schema. The outputs and manifest are ignored under `data/processed/`.
- Development feature-coverage diagnostics end on 2015-07-03. They record 313,436 nulls each for
  `competition_has_opened` and `competition_age_months` (the 354 jointly missing competition
  metadata stores), 2,558 missing `competition_distance` values, and expected exact-history warm-up
  and sparse-gap nulls. No imputations were introduced. Promo2 produced no invalid/incomplete
  schedule findings in the prepared snapshot; nonparticipants remain inactive despite structural
  schedule nulls.
- For a gap-affected store, all dynamic history fields are unavailable on 2015-01-01; lag 1 resumes
  on Jan 2; lag 7 and the 7-day window resume Jan 8; lag 14 and the 14-day windows resume Jan 15;
  all ten dynamic fields resume Jan 29 after the complete 28-day window exists. No absent dates
  were bridged or synthesized.
- The final holdout remains 2015-07-04 through 2015-07-31 (31,220 store-days). Its audit is
  mechanical only: predictor schema/order, unique keys, and dtype compatibility. No holdout
  distribution or forecast metric was summarized. Development coverage stops July 3.
- The feature runner verified all four raw-source hashes and the three prepared Parquet hashes
  against the approved source snapshot and Phase 2 manifest before and after the build. The raw
  validator also passed without errors. Store 622 Open candidates remain audit fields; inference
  contains no Sales, Customers, or Customers-derived fields.
- Future-known/static inference predictors are materialized for all test rows. Without recursive
  predictions, dynamic values needing exact dates after the forecast origin remain null; later
  recursive steps can supply predictions through the origin-censored history API.
- Repeated deterministic builds produced the same SHA-256 for each corresponding artifact:
  `features_train.parquet` matched its prior build, and `features_inference.parquet` matched its
  prior build. These two distinct artifacts do not share a hash. No holdout distributions were
  summarized.
- Detailed field semantics, roles, dtypes, null behavior, and point-in-time rules are in
  [Feature Contract](FEATURE_CONTRACT.md); the completed execution plan is archived at
  `plans/completed/phase-3-feature-engineering.md`.
- External review follow-up canonicalizes history keys before duplicate/overlap checks, grouping,
  or exact-date lookup: Store IDs are validated positive exact integers representable as int64;
  Dates are parsed as midnight calendar values and stored as datetime64[ns]. The shared key path
  copies inputs and is also used by static predictor assembly. Focused regression coverage now
  includes fractional/out-of-range IDs, canonical Store/Date collisions, valid coercion, and input
  non-mutation.

## Phase 3 Quality Checkpoint (Historical)

- `python scripts/validate_data.py --report reports/validation/rossmann.json`: PASS — 0 errors,
  4 reviewed warnings, 12 informational findings.
- `python scripts/build_features.py`: PASS — raw/interim provenance checks, key preservation,
  matching predictor schemas/dtypes, holdout mechanical audit, and output generation.
- Full suite chronology: 45 passed before the external-review key-canonicalization fix; 56 passed
  after the fix and again at PR readiness, including the key-canonicalization regression cases.
- `ruff check .`: passed; `ruff format --check .`: 45 files already formatted.
- `git diff --check`: passed. Relative Markdown links in changed user-facing documentation: passed.
- Preparation and EDA commands completed against the official data; both notebooks validated and
  executed successfully with cleared committed outputs.

## Phase 4 Scope Confirmation at Closeout

At the Phase 4 closeout checkpoint, only the explicitly approved Seasonal Naive baseline was
implemented; Holt-Winters and later-phase work had not begun. Sales remains monetary turnover at
Store × Date; future Customers remain unavailable to forecasts. Primary evaluation uses actual
source Open=1 observations, while the known-closed zero rule is applied only to the separate
operational forecast after raw generation.

## Phase 4 Implementation and Development Results

- The approved methodology is recorded in accepted ADR-013, which remains unchanged. External
  review found no blocking issue; PR #5 received final approval and merged into `main` at
  `12f80b5fe8a8580b3d8367cd473766decd3ebf31`. The completed execution plan is archived at
  [`plans/completed/phase-4-seasonal-naive.md`](../plans/completed/phase-4-seasonal-naive.md).
- `python scripts/run_seasonal_naive.py` completed successfully against the existing prepared
  Rossmann historical table. The runner read only `Store`, `Date`, `Sales`, and source `Open`, and
  applied the Parquet Date filter through 2015-07-03 before evaluation. It ran exactly the three
  approved development windows and emitted 46,830 observed target records. Generated outputs are
  ignored under `data/processed/seasonal_naive/`; the manifest records the methodology, windows,
  source hashes, and artifact hashes.
- Coverage and primary metrics by window (coverage is available raw forecasts / denominator):

  | Window | Observed targets | Eligible open labels | All-target coverage | Open-label coverage | MAE | RMSE | MAPE | MAPE rows / eligible | Zero rows excluded from MAPE | WAPE |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 15,610 | 11,678 | 15,610 / 15,610 (100%) | 11,678 / 11,678 (100%) | 1,101.5940 | 1,444.9870 | 15.0088% | 11,678 / 11,678 (100%) | 0 | 0.143224 |
  | validation_2 | 15,610 | 13,438 | 15,610 / 15,610 (100%) | 13,438 / 13,438 (100%) | 2,269.7721 | 3,141.3506 | 36.1046% | 13,438 / 13,438 (100%) | 0 | 0.324782 |
  | validation_3 | 15,610 | 13,437 | 15,610 / 15,610 (100%) | 13,437 / 13,437 (100%) | 1,596.5170 | 2,253.3165 | 26.2135% | 13,437 / 13,437 (100%) | 0 | 0.226393 |

- Pooled eligible development rows: 38,553. Pooled MAE **1,681.2703**, RMSE **2,416.9677**,
  MAPE **26.2671%** (38,553 MAPE rows, 0 zero-actual rows excluded, 100% MAPE coverage), and
  WAPE **0.232748**. These are computed over pooled eligible observations, not averaged window
  metrics.
- Horizon-level eligible counts and metrics (WAPE is a ratio; MAPE is a percent):

  | Horizon | Eligible | MAE | RMSE | MAPE | WAPE |
  |---:|---:|---:|---:|---:|---:|
  | 1 | 3,344 | 672.2425 | 981.3211 | 11.9931% | 0.114442 |
  | 2 | 97 | 861.8763 | 1,187.4567 | 14.7578% | 0.108050 |
  | 3 | 2,262 | 4,259.5504 | 4,747.9555 | 72.8666% | 0.677632 |
  | 4 | 3,344 | 2,307.4554 | 2,739.8971 | 39.9556% | 0.368580 |
  | 5 | 3,344 | 2,131.9731 | 2,459.9699 | 38.2207% | 0.362656 |
  | 6 | 3,344 | 2,405.0329 | 3,161.1523 | 42.6760% | 0.407425 |
  | 7 | 3,344 | 1,765.8403 | 2,232.6592 | 30.0997% | 0.273202 |
  | 8 | 3,344 | 832.9013 | 1,125.0257 | 14.0842% | 0.135236 |
  | 9 | 96 | 752.7188 | 1,039.2468 | 10.4863% | 0.089113 |
  | 10 | 3,344 | 1,025.8322 | 1,418.5733 | 9.7639% | 0.097370 |
  | 11 | 3,344 | 1,141.4202 | 1,587.1030 | 11.6617% | 0.122944 |
  | 12 | 3,343 | 1,124.9399 | 1,441.6304 | 13.9331% | 0.137552 |
  | 13 | 2,660 | 2,460.7320 | 3,971.0272 | 33.6384% | 0.324489 |
  | 14 | 3,343 | 1,091.0808 | 1,453.2243 | 13.6778% | 0.136541 |

- All 46,830 observed target records had an available raw forecast (46,830 / 46,830); therefore
  there were no unavailable weekly baseline forecasts, no affected Store × Date rows, and no
  unavailable-store cases to report. Open-labelled forecast coverage was also 100% in each window.
- No final-holdout forecast, score, metric, or target summary was produced. Phase 4 reads are
  restricted to dates through 2015-07-03 before the evaluation layer; only development outputs
  appear in the generated artifact directory.
- Raw Rossmann inputs and Phase 2 `train.parquet` hashes matched their recorded provenance before
  and after the run. The runner wrote only Git-ignored generated files; no raw, interim, or Phase 3
  files were modified, and generated results remain ignored and untracked. `docs/PROPOSAL.md` is
  unchanged.
- Validation at Phase 4 completion: full pytest suite **73 passed**; `ruff check .`,
  `ruff format --check .`, and `git diff --check` passed. The Seasonal Naive CLI completed
  successfully with unchanged input provenance. Phase 4 is formally COMPLETE. At the Phase 4
  closeout checkpoint, Phase 5 implementation had not begun; no final-holdout result was produced.

## Phase 5 Statistical Forecasting Approval and Implementation

- Status at approval checkpoint: **APPROVED / IMPLEMENTATION IN PROGRESS**. The user explicitly
  approved the fixed Holt-Winters methodology and its 99% coverage guardrail on 2026-10-05. Phase 5
  implementation and real-data results are recorded below as they are produced.
- The archived design plan is [`plans/completed/phase-5-statistical-forecasting.md`](../plans/completed/phase-5-statistical-forecasting.md).
- A mechanical history-availability audit projected only `Store` and `Date` from the existing
  training feature Parquet and filtered dates to `<= 2015-07-03`. It used no Sales, Open,
  Customers, forecast, metric, or holdout field/value. All 1,115 target Stores in each approved
  development window had at least 28 consecutive observed dates ending at the origin:

  | Window | Target Stores | Origin-row Stores | ≥28 days | 14–27 days | 7–13 days | 2–6 days | 0–1 day | Eligible |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
  | validation_2 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
  | validation_3 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |

- At the approval checkpoint, this date-only result suggested no date-availability coverage loss
  under the minimum-history rule. It did not establish Sales validity or model-fit success;
  numerical failures were then unmeasured. The implementation evidence below records the later
  successful fits. The approved policy has no fallback.
- The audit stopped at 2015-07-03 and did not read holdout Sales. It produced no holdout forecast
  or evaluation; the earlier descriptive exposure is disclosed above.

### Phase 5 Implementation and Development Results

- The approved design is implemented on `feat/holt-winters` under accepted ADR-014. The package
  provides origin-censored, per-Store additive Holt-Winters fitting, latest-contiguous-history
  eligibility, a single internal 14-step forecast operation, clipped raw forecasts with retained
  unclipped values, explicit unavailable reasons, and post-forecast Open routing. There is no
  fallback model. The dependency resolved to statsmodels 0.15.0.
- `python scripts/run_holt_winters.py` completed successfully against the existing Phase 2
  `train.parquet`. Its Parquet projection includes only Store, Date, Sales, and Open, and the Date
  predicate is applied at read time through 2015-07-03. It evaluated the three approved development
  windows and recomputed Seasonal Naive from the reviewed Phase 4 implementation. Raw Rossmann and
  Phase 2 hashes matched before and after the run. No final-holdout forecast, score, or metric was
  produced.
- The run generated 46,830 observed target forecasts and 46,830 internal 14-step path records
  across 3,345 Store-origin fits. All 3,345 fits succeeded; there were no unavailable forecasts,
  fit/forecast failures, warnings, or optimizer non-convergence flags. All three windows achieved
  100% raw and Open-label forecast coverage, above the precommitted 99% coverage guardrail.
- Standalone Holt-Winters metrics (primary population: observed source Open=1 and Sales, with
  available clipped raw forecast):

  | Window | Observed targets | Eligible open labels | Open-label coverage | MAE | RMSE | MAPE | WAPE |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 15,610 | 11,678 | 11,678 / 11,678 (100%) | 1,195.5661 | 1,617.4146 | 15.2155% | 0.155442 |
  | validation_2 | 15,610 | 13,438 | 13,438 / 13,438 (100%) | 1,136.8306 | 1,483.1660 | 16.9474% | 0.162669 |
  | validation_3 | 15,610 | 13,437 | 13,437 / 13,437 (100%) | 1,501.5664 | 1,974.7435 | 22.5253% | 0.212929 |

- Pooled over 38,553 eligible rows, Holt-Winters MAE was **1,281.7446**, RMSE **1,708.3073**,
  MAPE **18.3669%**, and WAPE **0.177439**. MAPE included 38,553 positive-actual rows, excluded
  zero rows: 0, and had 100% MAPE coverage. Pooled values are calculated over rows, not averaged
  from window metrics.
- Paired comparison uses the identical 38,553 eligible Store-origin-Date rows where both
  recomputed Seasonal Naive and Holt-Winters forecasts were available. A negative MAE difference
  means Holt-Winters MAE is lower; this fixed-candidate development comparison is not final model
  selection:

  | Window | Paired rows | Holt-Winters MAE | Seasonal Naive MAE | Difference (HW - SN) | Relative change | Lower paired MAE |
  |---|---:|---:|---:|---:|---:|---|
  | validation_1 | 11,678 | 1,195.5661 | 1,101.5940 | +93.9721 | +8.5306% | Seasonal Naive |
  | validation_2 | 13,438 | 1,136.8306 | 2,269.7721 | -1,132.9415 | -49.9143% | Holt-Winters |
  | validation_3 | 13,437 | 1,501.5664 | 1,596.5170 | -94.9506 | -5.9474% | Holt-Winters |
  | pooled | 38,553 | 1,281.7446 | 1,681.2703 | -399.5257 | -23.7633% | Holt-Winters |

- Additive forecasts below zero were clipped only for the raw metric forecast; unclipped values
  remain in the audit output. In the full internal paths, 1,085 of 46,830 forecasts (2.3169%)
  were clipped. The minimum unclipped forecast was -4,175.2857. By window, clipping was
  354 / 15,610 (2.2678%), 408 / 15,610 (2.6137%), and 323 / 15,610 (2.0692%), respectively.
- Ignored artifacts and a manifest are under `data/processed/holt_winters/`: observed-key
  forecasts, internal 14-step paths, per-fit and aggregated diagnostics, window/pooled/horizon
  metrics, coverage guardrail, identical-row paired forecasts and metrics, and clipping
  diagnostics. All emitted dates are 2015-05-23 through 2015-07-03; all 46,830 composite keys are
  unique. The generated forecast table does not expose the protected holdout.
- Initial executions exposed two post-fit reporting defects (strict JSON serialization of a
  missing pooled label, and a clipping-rate denominator reference); both were corrected and covered
  by tests. The final real-data runner completed with exit code 0 and regenerated all artifacts.
- Initial Phase 5 implementation checks: full pytest suite **95 passed**;
  `ruff check src tests scripts` and `ruff format --check src tests scripts` passed. Artifact paths
  were verified Git-ignored;
  provenance checks passed before and after evaluation. At this implementation checkpoint, Phase 5
  was **IMPLEMENTED / UNDER REVIEW**, not formally closed. `docs/PROPOSAL.md`, reviewed Phase 4 model code/artifacts, raw data,
  and Phase 2 prepared data were not modified.
- External review found that the reusable Holt-Winters API validated horizons from 1–14 but still
  generated a fixed 14-step path. The forecaster now consistently uses the validated
  horizon for model forecasts, output-length validation, and internal path rows, records
  `forecast_horizon` for successful and failed fits, and computes clipping rates over successful
  requested forecast steps. Regression tests cover 7- and 14-step behavior, target bounds, output
  lengths, failed-fit paths, and horizon-aware clipping rates. The approved Phase 5 runner continues
  to request 14 days. Its post-fix rerun reproduced the recorded metrics unchanged: 46,830 forecasts,
  3,345 successful Store-origin fits, 100% availability in every window, and a passed 99% coverage
  guardrail. The ignored fit-diagnostics artifact now includes `forecast_horizon`; artifact hashes
  were regenerated for the updated output schema. Full-repository validation passed: pytest **102
  passed**, `ruff check .`, `ruff format --check .`, `git diff --check`, and relative Markdown-link
  validation across 19 files. No holdout forecast or evaluation occurred; at that review checkpoint,
  Phase 5 was **IMPLEMENTED / UNDER REVIEW**.

## Repository Architecture/Governance Review — 2026-10-05

The [completed review task plan](../plans/completed/repository-architecture-governance-review.md)
records scope and cross-review. Verdict: **READY for the next authorized design task**, not an
authorization to implement Phase 6 or a declaration that Phase 5 is closed.

- Reviewed all listed governance/data docs, active/completed plans, source/script/test/notebook
  structure, and public branch/merged-PR metadata. Current-state, branch, phase, artifact-path,
  terminology and local Markdown references were cross-checked; archived evidence was preserved.
- ADR-015–018 trace the fixes: final evaluation after all choices freeze, disclosed descriptive
  exposure, consistent simulated inventory values/cumulative uncertainty, simpler application and
  work-package boundaries, portable locked environments and fixture CI. AGENTS/WORKFLOW now own
  approval/lifecycle rules; this document owns maintained results, not duplicated plan tables.
- The Phase 6 handoff specifies origin-censored fitting/history, future-known covariates,
  categorical/null adapter design, raw recursion versus Open routing, metric/coverage interfaces,
  outputs, tests and approval. No LightGBM or later-phase module/dependency was implemented.
- Forecast algorithms/configurations and existing numerical evidence were unchanged. Three
  exception clauses gained tuple parentheses for Python 3.12 compatibility. Source hash-only
  verification matched all four documented raw hashes; no data/model pipeline or holdout
  forecasting/evaluation was run for this review.

The continuation recovered the existing dirty review branch at HEAD `3d4fbfd`: 18 modified and
five new files, nothing staged. Full-file rereads, diff/history inspection and a fresh repository-
only Phase 6 handoff audit preserved that work. Two residual ambiguities were corrected: LightGBM
feeds predictions, never unrevealed target actuals; final scheduled preprocessing/model refits may
update fitted state only under the frozen recipe using already revealed training rows. No new
phase scope or methodology search was introduced. The quality gate was rerun after these fixes.

Final checks actually executed:

| Check | Result |
|---|---|
| `python -m pytest` in the original Python 3.14.5 environment | 106 passed; includes four new Markdown-checker fixtures |
| Complete fixture suite in isolated locked Python 3.12.15 / 3.14.5 | 106 passed in each environment |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS; 63 files already formatted |
| `python scripts/check_docs.py` | PASS; local files/directories/common heading anchors across 20 Markdown files |
| `git diff --check` | PASS |
| `uv lock --check` / `uv pip check` | PASS; current lock and compatible installed packages |
| Numbering and math checks | Phase 0–14, proposal 1–30, ADR-001–018 and paired proposal dollar delimiters PASS |

Remaining non-blocking limits: only 42 development target days and prior descriptive holdout
exposure; pooled empirical intervals/simulated policies require their later reviewed designs.
At the review checkpoint recorded here, main protection was not enabled, and stale branch cleanup
needed separate authorization/unique-change checks. PR #7 integration followed by Phase 5 explicit
closeout remained the immediate project gate. Phase 6 had not started.

## Phase 5 Formal Closeout — 2026-10-05

PR #7 was squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`. The GitHub
PR metadata's `merge_commit_sha` matches the fetched `origin/main` and the closeout branch base.
Phase 5 is **COMPLETE**; its fixed additive Holt-Winters implementation and development-only
evaluation are integrated. The completed execution plan is archived at
[`plans/completed/phase-5-statistical-forecasting.md`](../plans/completed/phase-5-statistical-forecasting.md).
No final-holdout forecasting or evaluation was performed, and Phase 6 implementation began only
after the separate authorization recorded in its active plan. The historical metric tables and
methodology above are unchanged.

## Phase 6 Global LightGBM Implementation — 2026-10-06

At the implementation checkpoint, Phase 6 was **IMPLEMENTED / UNDER REVIEW** on
`feat/phase-6-global-lightgbm`. The candidate follows
ADR-019 and the [completed Phase 6 plan](../plans/completed/phase-6-global-lightgbm.md). It is a
development candidate only; Phase 7 has not started, and no final project model has been selected.

- `lightgbm>=4.7,<4.8` resolved to LightGBM 4.7.0 in the locked Python 3.14.5 / Windows 11
  environment. The runner writes ignored outputs only under `data/processed/lightgbm/` and
  `artifacts/lightgbm/`; `git check-ignore` confirmed the generated outputs are ignored.
- The exact 29-predictor phase-3-v1 matrix and four frozen trial recipes were used. Inner tuning
  ran 109 recursive checkpoints: A 23, B 6, C 40, and D 40. It selected trial A at 180 rounds
  (learning rate 0.05, 15 leaves, max depth 4, min_data_in_leaf 200), with inner open-label MAE
  **1,305.1707** and **100%** open-label coverage. Trials C and D reached the 400-round cap; A and
  B stopped after five checkpoints without strict improvement. Every fit succeeded.
- The predeclared outer refits completed for all three origins. Each 14-day window emitted 15,610
  target rows; the 46,830 pooled target rows include 38,553 eligible observed source Open=1 labels.
  Open-label coverage was 100% in every window (11,678/11,678; 13,438/13,438; and
  13,437/13,437), exceeding the frozen 99% guardrail. There were no unavailable forecasts and no
  negative-output clipping events.

Standalone development metrics use the primary population of observed source Open=1 and Sales with
an available clipped raw forecast. MAPE is reported as a percentage; WAPE is a ratio.

| Scope | Eligible rows | Open-label coverage | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 100% | 1,051.4335 | 1,512.2577 | 12.5686% | 0.136702 |
| validation_2 | 13,438 | 100% | 790.9941 | 1,193.4810 | 10.9700% | 0.113184 |
| validation_3 | 13,437 | 100% | 794.3741 | 1,350.5876 | 10.6797% | 0.112646 |
| pooled | 38,553 | 100% | **871.0612** | 1,350.9138 | 11.3531% | 0.120586 |

The pooled values are recomputed over eligible rows. Paired baseline summaries use the identical
38,553 eligible Store × Date rows with both forecasts available; these are descriptive Phase 6
development comparisons, not final model selection.

| Scope | Paired rows | LightGBM MAE | Seasonal Naive MAE | Holt-Winters MAE | LightGBM MAE change vs SN | vs Holt-Winters |
|---|---:|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 1,051.4335 | 1,101.5940 | 1,195.5661 | -4.55% | -12.06% |
| validation_2 | 13,438 | 790.9941 | 2,269.7721 | 1,136.8306 | -65.15% | -30.42% |
| validation_3 | 13,437 | 794.3741 | 1,596.5170 | 1,501.5664 | -50.24% | -47.10% |
| pooled | 38,553 | **871.0612** | 1,681.2703 | 1,281.7446 | -48.19% | -32.04% |

The final manifest records `development_only_through=2015-07-03`,
`final_holdout_forecast_or_evaluation=false`, and that Phase 6 neither read nor hashed final-holdout
outcomes. Emitted inner forecasts end on 2015-05-08; outer forecasts end on 2015-07-03. Phase 7
and the protected 2015-07-04 through 2015-07-31 holdout remain outside this implementation.

Implementation tuning exposed a repeated history-index build across recursive steps; a reusable
origin-censored history cache now matches the reviewed builder exactly across fixture horizons and
preserves missing-date behavior. LightGBM also required `feature_pre_filter=false` on the shared
Dataset because the frozen trial grid varies `min_data_in_leaf`; the four recipes and objective
were unchanged. The final real-data run completed without fit failures.

Final quality checks after the documentation update:

| Check | Result |
|---|---|
| Full fixture suite (`python -m pytest`, Python 3.14.5) | PASS — 151 passed in 22.39s |
| PR #10 GitHub Quality workflow | PASS — Python 3.12 and 3.14 jobs; tests, dependency check, Ruff, formatting, and Markdown links |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 69 files already formatted |
| `python scripts/check_docs.py` | PASS — 85 local destinations/anchors across 21 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved |
| `python -m pip check` | PASS — no broken requirements |
| `git diff --check` | PASS — Git reported only the existing uv.lock LF-to-CRLF working-copy warning |

At the implementation checkpoint, the runner completed successfully and its manifest hashed the
ignored development outputs and date-censored input projections. External review, authorized
integration, and formal closeout were then pending; the closeout is recorded below.

### External-review follow-up — 2026-10-06

- Recursive feature/history construction now has its own failure boundary; prediction API errors
  use the approved `model_fit_failure` reason, while explicit schema and categorical-adapter
  failures keep their approved reasons. The fake-booster regression and feature-construction
  failure fixture pass.
- Removed the `narwhals!=2.27.0` resolver exclusion after the LightGBM fixtures passed with
  LightGBM 4.7.0 and Narwhals 2.27.0 on Python 3.12.15 and 3.14.5 (46 passed in each
  environment). PyPI marks 2.27.0 yanked for Pointblank breakage; no incompatibility relevant to
  this repository or LightGBM was reproduced. The normal resolver therefore keeps the yanked
  release out and `uv.lock` remains at Narwhals 2.26.0; the effective locked runtime is unchanged.
- The review fixes do not alter the successful Phase 6 forecasts or recorded metrics. The
  approved real-data development command was not rerun because the locked runtime did not change.
  At this follow-up checkpoint Phase 6 remained **IMPLEMENTED / UNDER REVIEW**; Phase 7 and the
  final holdout remained untouched.
- Follow-up validation passed: full suite **152 passed** on Python 3.12.15 and **152 passed** on
  Python 3.14.5; Ruff lint and formatting, documentation links, `uv lock --check`, dependency
  consistency in both environments, and `git diff --check` passed.

## Phase 6 Formal Closeout — 2026-10-06

Phase 6 is **COMPLETE**. PR #10 merged into `main` at
`dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed execution plan is
[archived](../plans/completed/phase-6-global-lightgbm.md). The external-review fixes are in final
commit `9a33e8f673ec438fe4a5546011d06219d66e6a92`, and final-head
[Quality workflow run #12](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37419362812)
passed on Python 3.12 and 3.14. Review did not change the approved development results documented
above: trial A at 180 rounds, 100% open-label coverage, pooled MAE 871.0612, and the 99% coverage
guardrail passed. The full
fixture suite finished with 152 passing tests. No final-holdout forecast or evaluation occurred.
Phase 7 has not started and requires a separate approved design and authorization.

## Phase 7 Design and Development Evidence Audit — 2026-10-06

**At the evidence-audit checkpoint: design started, implementation not started, methodology
awaiting approval, and no final model officially selected.** The [active plan](../plans/completed/phase-7-model-selection.md)
was PROPOSED / AWAITING APPROVAL on `docs/phase-7-model-selection-design`, based on verified PR #11
integration. Its thresholds were proposed after observing the existing results, not
preregistered. Historical Phase 4–6 result records above remain unchanged.

Read-only audit of ignored development outputs: SHA-256 checks match the original manifests for
all three candidates' forecast, pooled/window/horizon metric files and saved HW/LightGBM fit
diagnostics. Exact label/key joining reproduces 46,830 targets and 38,553 common eligible rows
(11,678 / 13,438 / 13,437 per window); recomputed pooled MAEs match the reported values above.
No model/tuning runner or source-data read was needed. Newly verified horizon block MAEs,
pooled over the same common eligible rows rather than averaged daily metrics:

| Horizon block | Seasonal Naive | Holt-Winters | LightGBM |
|---|---:|---:|---:|
| 1–7 | 2,136.3558 | 1,155.6570 | 643.0551 |
| 8–14 | 1,235.4154 | 1,405.2746 | 1,094.4426 |

LightGBM beats each baseline on 11 of 14 pooled horizons, but Sunday h2/h9 MAEs are
1,572.8966 / 1,707.5285 versus SN 861.8763 / 752.7188 and HW 879.1219 / 903.0457;
these strata contain only 97 / 96 eligible rows. At h10 LightGBM MAE 2,280.9889 is worse
than SN 1,025.8322, though below HW 2,341.7674. At h8 it is slightly worse than HW
(733.6691 versus 716.2542). Friday origins confound horizon/weekday; these are descriptive
tradeoffs, not independent replication or confidence evidence.

Saved LightGBM outer `training_seconds` are 6.0427 / 6.1840 / 6.2647 on the recorded
Python 3.14.5, LightGBM 4.7.0 Windows CPU environment with four model threads. Runner inspection
confirms the timer surrounds fitting only. No comparable SN/HW times, end-to-end inference
timings or peak-memory measurements are available; none are fabricated here.

Cached provenance limits remain visible: SN/HW manifests lack modern code/lock identity;
LightGBM records revision `79ddb510e94fe5695c4bc17814153fd47695e16f` with modified worktree and
working-tree source hash, preceding the committed review fixes. The plan requires explicit
acceptance of that lineage and unchanged reviewed specifications, not a claim that these outputs
were regenerated from current main. This audit accessed only saved development evidence ending
July 3; no final-holdout read, hashing, fit, forecast or evaluation, nor Phase 8 work, occurred.

Design quality gate passed: full pytest **152 passed** on each of Python 3.14.5 and 3.12.15,
Ruff lint/format (70 files), Markdown links (107 local destinations/anchors, 22 documents),
`uv lock --check` and `git diff --check`. Only documentation changes; no new tests, models,
dependencies, selection artifacts or interval calculations. Full diff reviewed before publication.

## Phase 7 Methodology Approval Sync — 2026-10-06

External methodology approval was synchronized for reviewed PR #12 head
`1c15ab0b6ee94f3ecccb8f04c84da97d58bbb225`. Phase 7 is **APPROVED / IMPLEMENTATION NOT
STARTED**, and [ADR-020](DECISIONS.md#adr-020--development-only-model-selection-and-frozen-refit-policy)
records the accepted policy. PR #12 remains the open design integration gate; implementation may
begin only after it merges into `main`.

The approved phase-7-v1 rule is unchanged: SN → HW → LightGBM; same three-way eligible/available
open-label population; ≥5% pooled MAE improvement, lower MAE in at least 2/3 windows, and ≤10%
regression in each window and pooled horizon block 1–7/8–14; ties or failed gates retain the
simpler incumbent. Each standalone candidate and the common population must meet 99% coverage in
every approved window, with integrity checks passing. Thresholds remain disclosed as introduced
after observing results, not preregistered; there is no significance or generalization claim.
Keep individual-horizon weaknesses visible, including sparse Sundays and horizon 10; no horizon
veto or forecast mixing is added.

Qualitative operational assessment is accepted for the existing offline CPU course demonstration
without a new benchmark. This grants no API, production, end-to-end runtime, measured-memory or
savings claims. The existing artifact lineage is accepted only for this development selection,
subject to rechecking hashes, keys, labels, masks and configurations; original metadata remains
unchanged. Later operational inputs must be explicit, versioned and auditable.

The selection runner remains unimplemented; no final model is officially selected. Phase 8 has
not started. Final-holdout access remains prohibited until a separately authorized ADR-015 Phase
13 protocol; no holdout was accessed in this approval sync.

Approval-sync checks passed: full pytest **152 passed** on Python 3.14.5 and **152 passed** on
Python 3.12.15; Ruff lint and format (70 files), Markdown checker (109 local destinations/anchors
across 22 Markdown files), `uv lock --check` and `git diff --check`. No fixture tests or model
pipelines were added or run; the requested existing fixture suites passed. Full documentation diff
was inspected.

## Phase 7 Implementation Checkpoint — 2026-10-06

Phase 7 is **IMPLEMENTED / UNDER REVIEW** on `feat/phase-7-model-selection`, based on `main`
after approved design PR #12 merged at `64dbf2359c34cc06d81ee4fc1640ad7225db3973`. The reusable
selection engine and thin CLI use only the three reviewed candidates and their cached development
forecasts. The fixed ADR-020 policy is unchanged. No candidate-level operational decision was
found, so all three reviews remain `unknown`; the result is `operational_review_required`, with no
official selected model or selected-model artifacts.

The runner verified all 34 original candidate artifact hashes (5 Seasonal Naive, 11 Holt-Winters,
18 LightGBM), preserved all three source manifests and their original artifact metadata, checked
the approved source snapshot and Phase 2 identity, and validated the saved candidate keys, labels,
availability/eligibility masks, origins, windows, configurations and model identities. Each saved
candidate contained 46,830 observed Store-origin-Date targets from 2015-05-23 through 2015-07-03.
All 46,830 raw forecasts were available for each candidate, yielding 38,553 identical eligible
Open=1 observed-Sales rows. All three standalone and the three-way common population had 100%
open-label coverage in every window (11,678 / 11,678; 13,438 / 13,438; and 13,437 / 13,437).

Pooled results use the same 38,553 common eligible rows; values are direct row-pooled metrics:

| Candidate | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|
| Seasonal Naive | 1,681.2703 | 2,416.9677 | 26.2671% | 0.232748 |
| Holt-Winters | 1,281.7446 | 1,708.3073 | 18.3669% | 0.177439 |
| LightGBM | 871.0612 | 1,350.9138 | 11.3531% | 0.120586 |

Window MAE (all candidate comparison populations use identical rows):

| Window | Seasonal Naive | Holt-Winters | LightGBM |
|---|---:|---:|---:|
| validation_1 | 1,101.5940 | 1,195.5661 | 1,051.4335 |
| validation_2 | 2,269.7721 | 1,136.8306 | 790.9941 |
| validation_3 | 1,596.5170 | 1,501.5664 | 794.3741 |

The numeric ladder keeps Seasonal Naive after Holt-Winters improves pooled MAE by 23.7633% and
wins 2/3 windows, because its pooled h8–14 MAE is 1,405.2746 versus 1,235.4154 for Seasonal
Naive (+13.7492%, above the 10% cap). The h1–7 block improves 45.9052%, and every window remains
within its 10% cap. LightGBM is then compared directly with the retained Seasonal Naive: pooled
MAE improves 48.1903%, all three windows win, and both pooled horizon blocks pass their caps
(h1–7 improves 69.8994%; h8–14 improves 11.4110%). LightGBM passes the numeric gates; operational
review still prevents selection.

| Horizon | Eligible rows | Seasonal Naive MAE | Holt-Winters MAE | LightGBM MAE | LightGBM change vs Seasonal Naive |
|---:|---:|---:|---:|---:|---:|
| 2 (Sunday) | 97 | 861.8763 | 879.1219 | 1,572.8966 | +82.50% |
| 9 (Sunday) | 96 | 752.7188 | 903.0457 | 1,707.5285 | +126.85% |
| 10 (Monday) | 3,344 | 1,025.8322 | 2,341.7674 | 2,280.9889 | +122.35% |

These horizon rows are descriptive and do not add a veto. The comparison file includes MAE, RMSE,
MAPE, WAPE, denominators, pairwise/common changes, horizon 1–14, pooled week blocks, Store-level
diagnostics and unavailable-reason counts. The ignored output directory is
`data/processed/model_selection/`: `model_comparison.csv` (190,680 rows),
`selection_decision.json`, and `manifest.json`. No `selected_model_config.json`, refit recipe,
selected forecasts or residual paths were emitted because operational approval is unresolved.

SN/HW legacy lineage limits and LightGBM's original modified-worktree revision/hash remain
disclosed in the new manifest; old manifests were not rewritten and no model was rerun. The
qualitative operational scope is only the offline CPU course demonstration. No production latency,
reliability, memory SLA, measured end-to-end runtime advantage or real business savings are
established. The runner read no raw/interim data or final-holdout outcomes, emitted no July 4–31
forecast or metric, performed no fit/tuning, and did not begin Phase 8. ADR-015 still blocks later
July 3 and July 17 refits until separately authorized.

The fixture-first suite has **179 passing tests** on Python 3.14.5 and **179 passing tests** on
Python 3.12.15. `ruff check .` passed; `ruff format --check .` passed (73 files); the documentation
checker passed (111 local destinations/anchors across 22 documents); `uv lock --check` resolved 84
packages; `python -m pip check` passed on Python 3.14.5; and `uv pip check` passed on the locked
Python 3.12 environment (60 packages). `git diff --check` passed with only expected Windows
LF-to-CRLF notices on the three new Python files. [Implementation PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13)
is open for review and records these checks. Its [Quality workflow run #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37429992491)
passed both Python 3.12 and Python 3.14 jobs, including dependency checks, fixture tests, lint,
formatting and Markdown links, on implementation commit `f95fa9d`. Later PR-head commits only
updated review documentation; the documentation checker and diff check passed locally, and no new
workflow run was created for those doc-only updates. Phase 7 remains under review; this checkpoint
is not a phase closeout.

## Phase 7 External Review Follow-up — 2026-10-06

The PR #13 review follow-up hardens generated-artifact lifecycle handling without changing
ADR-020. Before reading candidate evidence, the runner atomically replaces its prior manifest with
an in-progress marker. It stages the comparison, decision, and—only for a selected decision—all
four selected-model artifacts under one run ID; each output is hashed, and the complete manifest is
published last. An interrupted publication therefore cannot leave a complete manifest pointing at
a partial selection. Unresolved or failed runs publish no selected identity or selected-artifact
references. Cleanup is limited to the four fixed selected-output names and only removes files whose
hashes match prior runner-owned metadata. Modified or unverified paths are preserved and reported as
conflicts. Original candidate manifests and files are read-only.

Synthetic lifecycle coverage now includes successful approvals and all four hashed outputs,
subsequent unknown reviews, integrity failure, selected-artifact generation failure, ownership
conflicts, inability to invalidate the existing manifest, preservation of unrelated files and
original manifests, no fit/tuning calls, and residual path keys/masks/errors/completeness. The full
suite passed **187 tests** on Python 3.14.5 and **187 tests** on Python 3.12.15.

The real cached selection command ran without an operational-review file. It returned
`operational_review_required`, selected candidate `null`, and no selected-model files. On the same
38,553 common eligible rows, pooled MAE remained Seasonal Naive **1,681.2703**, Holt-Winters
**1,281.7446**, and LightGBM **871.0612**. All 12 standalone/common per-window coverage gates
passed. The pre-run verification and post-run checks confirmed every original candidate manifest
and every artifact hash still matches its source manifest. No candidate was fitted or tuned, no
final-holdout outcomes were read or hashed, and Phase 8 did not start. Phase 7 remains
**IMPLEMENTED / UNDER REVIEW**; there is no official final model selection.

Final review-fix checks passed: `ruff check .`; `ruff format --check .` (73 files);
`python scripts/check_docs.py` (112 local destinations/anchors across 22 documents);
`uv lock --check` (84 packages); Python 3.14 `pip check`; Python 3.12 `uv pip check` (60
packages); and `git diff --check` (only expected Windows LF-to-CRLF notices for the two changed
Python files). Implementation commit `dbb1712bdc856a2c9b6787a34493cb429d5b8e3c` was pushed to
PR #13; GitHub Actions [Quality run #22](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37441277676)
passed both Python 3.12 and Python 3.14 jobs on that commit.

## Phase 7 Offline Operational Acceptance and Selection 2026-10-06

The external technical review supplied for PR #13 records candidate-level operational decisions
for the **offline CPU course demonstration** only. These are project technical-review decisions;
this record does not assert a named human reviewer or signature. The versioned input is
[configs/phase-7-operational-review-v1.json](../configs/phase-7-operational-review-v1.json), and
its reviewer reference points back to this section.

| Candidate | Decision | Rationale |
|---|---|---|
| Seasonal Naive | approved | Minimal computational complexity and deterministic same-weekday recurrence make it suitable as the initial incumbent. It needs no optimization or native model dependency. |
| Holt-Winters additive weekly | unknown | It fails ADR-020's pooled h8–14 regression cap; a candidate-specific operational approval is unnecessary for this selection. The operational decision remains unknown rather than being inferred as a rejection. |
| Global LightGBM GBDT regression L1 | approved | The reviewed global CPU implementation uses frozen trial A at 180 rounds in the reproducible locked environment, has 100% development coverage, improves pooled MAE substantially, and had no observed development fit failure. |

This approval is limited to the existing offline CPU demonstration. It establishes no production
latency SLA, reliability guarantee, end-to-end inference-speed comparison, memory SLA, real
inventory result, business savings, or universal accuracy superiority. The h2, h9 and h10
weaknesses and the original candidate-provenance limitations remain in force. The input does not
change ADR-020 thresholds, authorize fitting or tuning, or authorize access to final-holdout
outcomes. The actual CLI result and output integrity checks are recorded next.

### Selection result and artifact verification

The reviewed command ran with the versioned input:
`python scripts/run_model_selection.py --operational-review configs/phase-7-operational-review-v1.json`.
The runner returned **`selected`**; artifact integrity, record integrity and coverage statuses all
**passed**. The selected candidate is `global_lightgbm_gbdt_regression_l1`, selection run ID
`365f22d4c3f94722a594ab934a22c4f6`, and publication state **`complete`**. This is the Phase 7
offline development selection, **RECORDED / AWAITING EXTERNAL INTEGRATION REVIEW**; Phase 7 remains
**IMPLEMENTED / UNDER REVIEW**.

All original candidate-manifest artifacts were rehashed and passed: 5 Seasonal Naive, 11
Holt-Winters and 18 LightGBM artifacts. Their unchanged manifest SHA-256 identities are:

| Candidate | Original manifest SHA-256 |
|---|---|
| Seasonal Naive | `f5e3a18a0a8bff709cb06b4e6282e22cbe3f84668937d3c3e57245b7c76072e3` |
| Holt-Winters | `37b46babad1d197143bfda2f4f11aa65291c350b6b0687410bc4496b7171903b` |
| LightGBM | `ddd379fe4264dd90f618ba57791b97fcce3fd64199ffe95410c4f0d0695810c1` |

The runner matched 46,830 saved Store-origin target rows across 3,345 H14 paths, all ending on
2015-07-03. All 12 standalone/common 99% coverage gates passed at 100%: denominators were 11,678,
13,438 and 13,437 in `validation_1`, `validation_2` and `validation_3`, respectively. The common
eligible population contains 38,553 observed source Open=1 Sales rows.

| Candidate | Pooled common-row MAE | Policy result versus incumbent |
|---|---:|---|
| Seasonal Naive | 1,681.2703 | Initial incumbent |
| Holt-Winters additive weekly | 1,281.7446 | Improves 23.7633% and wins 2/3 windows, but fails the pooled h8–14 cap at +13.7492%; Seasonal Naive remains incumbent. Operational decision remains `unknown`. |
| Global LightGBM GBDT regression L1 | 871.0612 | Improves 48.1903% against Seasonal Naive, wins all 3 windows, and passes every window and pooled horizon-block cap; approved operationally for the scoped demonstration and selected. |

Actual window MAEs and the 10% caps against the retained Seasonal Naive incumbent:

| Window | Seasonal Naive MAE | Holt-Winters MAE (change; cap) | LightGBM MAE (change; cap) |
|---|---:|---:|---:|
| validation_1 | 1,101.5940 | 1,195.5661 (+8.5306%; pass) | 1,051.4335 (-4.5534%; pass) |
| validation_2 | 2,269.7721 | 1,136.8306 (-49.9143%; pass) | 790.9941 (-65.1509%; pass) |
| validation_3 | 1,596.5170 | 1,501.5664 (-5.9474%; pass) | 794.3741 (-50.2433%; pass) |

The pooled horizon-block comparisons also pass for LightGBM and fail only for Holt-Winters h8–14:

| Horizon block | Seasonal Naive MAE | Holt-Winters MAE (change; cap) | LightGBM MAE (change; cap) |
|---|---:|---:|---:|
| h1–7 | 2,136.3558 | 1,155.6570 (-45.9052%; pass) | 643.0551 (-69.8994%; pass) |
| h8–14 | 1,235.4154 | 1,405.2746 (+13.7492%; fail) | 1,094.4426 (-11.4110%; pass) |

The selection output retains the weaker h2 and h9 Sunday results and h10 Monday result: their
LightGBM MAEs are 1,572.8966 (97 rows), 1,707.5285 (96 rows) and 2,280.9889 (3,344 rows),
versus Seasonal Naive MAEs 861.8763, 752.7188 and 1,025.8322. No per-horizon veto was introduced.

The selected recipe exactly matches the reviewed LightGBM candidate configuration: global CPU
GBDT regression L1, trial A, 180 rounds and the ordered 29 Phase 3 predictors. It is a recipe only;
`fit_performed=false`, `no_tuning_or_refit_performed=true`, and no fitted future July model was
generated. The four selected artifacts share the run ID above. Their SHA-256 hashes, plus the two
comparison outputs and completed manifest, are:

| Generated artifact | SHA-256 |
|---|---|
| `selected_model_config.json` | `de53a477b4bed768a9fbaa459e7f347be28c05063f5c5e379c0dfbb40d21960b` |
| `refit_recipe.json` | `9ef3ee340ac57f14394857203ca3de5445ebae70972ec541a51947f38a49f799` |
| `selected_development_forecasts.parquet` | `72566349b233ef26c8de5b4f9c1623ac66df8676ad0370ad63b192ed4c1b5b09` |
| `development_residual_paths.parquet` | `509bb4a822157850e8fb0309114a4003b98bcbc6b56f4a49244d8b6593e03382` |
| `model_comparison.csv` | `c648e8e407dc367e56f26cb421656dabc8d742a9a3cd3d3b092b746a84b10357` |
| `selection_decision.json` | `02c00b7f0b72e260db03b6f786e443db93844a146f3a93fb8c4c4ea076f2e5de` |
| `manifest.json` | `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` |

The manifest binds the review input at SHA-256
`9ef1c1fa28fc12db318d510a5ae48a29fd2198116a0114e0d5ee866dc66d7516`. Its selection code revision
is reviewed PR #13 head `ca3d51fff53e6e98b55fae2ac84a5cfe1af7324a`, with current source hash
`20028b1133053489f8b3a68b5a38b272e7bf8a9947581395f96e64e5d57be997`; the runner records a
modified worktree because the review input and this record were present. No forecasting source or
runner code differed from that reviewed head. The original cached provenance limitations remain:
legacy SN/HW manifests lack modern source-code/lock identity, and the LightGBM manifest records its
historical modified-worktree run. All seven published files remain Git-ignored.

Residual checks verified the signed definition `actual_sales - forecast`, raw-primary masks,
operational masks and their complete/partial counts. Every Store-origin path has exactly horizons
1–14; 96 raw-primary paths are complete and 3,249 are partial because closed-day labels are not in
the primary population. All 3,345 operational paths are complete under the saved Open routing.
Closed-day raw residuals remain descriptive and excluded from primary metrics; unavailable values
were not filled. The manifest records no July 4–31 read/hash/forecast/evaluation and
`phase_8_started=false`; no Phase 8 work began.

Acceptance quality checks: full pytest passed **187 tests** on Python 3.14.5 (71.21s) and **187
tests** on Python 3.12.15 (69.61s); Ruff lint passed; Ruff format check passed (73 files); the
documentation checker passed (115 local destinations/anchors across 22 Markdown files);
`uv lock --check` resolved 84 packages; Python 3.14 `pip check` and locked Python 3.12 `uv pip
check` (60 packages) passed; `git diff --check` passed. The runner output and all original
candidate hashes were independently reverified after publication. No implementation code, tests,
dependencies or methodology changed. No candidate was fit or tuned and no protected outcome was
read or hashed.

## Phase 7 formal closeout and Phase 8 evidence audit — 2026-10-06

GitHub and fetched `origin/main` verify PR #13 merged at
`89bcb861642ee28259e4a402e8e8ee98a999a6e5`. Its integrated tree matches the reviewed final head
`688d673f3ebaf802cbe47f9fa3236fcb4aaa3dea`; final-head Quality run #25 passed Python 3.12 and
3.14. The accepted external review, verified integration and this explicitly authorized closeout
make Phase 7 **COMPLETE**. The [completed plan](../plans/completed/phase-7-model-selection.md)
preserves historical approval, implementation and selection checkpoints. ADR-020 and the selected
`global_lightgbm_gbdt_regression_l1` identity remain unchanged: frozen trial A, 180 rounds,
29 predictors and the same raw recursive/operational routing behavior.

The clean `docs/phase-8-uncertainty-design` branch started from that latest `origin/main`.
A read-only audit of existing ignored development exports verified the seven selection-file
hashes above and all 34 original candidate artifacts; no source dataset or protected outcomes were
read or hashed. The selected run ID remains `365f22d4c3f94722a594ab934a22c4f6`. Recipe and
manifest still record no refit, tuning or future-origin forecasting. Historical candidate
provenance limitations remain disclosed rather than being repaired by regenerating evidence.

The residual export has 35 fields and 46,830 unique Store-origin-Date rows, ending 2015-07-03:
3,345 paths with exactly h1–14. Masks, signed residuals (`actual_sales - forecast`), path flags
and saved Open routing match the implementation. No target keys are absent, no Open values are
unknown, and all required labels/forecasts are finite in these saved records.

| Audited population | Result and interpretation |
|---|---|
| Complete raw-primary H14 paths | 96, from the same 32 distinct stores in each of three origins; 3,249 paths are partial. Closed labels are outside the raw-primary Open=1 population. |
| Complete operational H14 paths | 3,345, covering all 1,115 stores per origin under saved Open routing. |
| Observed closed-day rows | 8,277, all with actual Sales=0 and routed forecast=0. These are observed turnover outcomes, not imputed missing residuals or uncensored physical demand. |
| Raw-primary counts at sparse h2 / h3 / h9, validation_1 | 32 / 33 / 32. |
| Raw-primary counts at h2 / h9, validation_1 + validation_2 | 65 / 64, reusing only 33 / 32 distinct stores across two origins. |

Operational completeness depends on using saved historical Open. This does not establish that
the schedule was known at origin. The proposed Phase 8 plan explicitly separates that unverified
availability from a newly proposed, conditional offline replay assumption; unknown future Open
must remain operationally unavailable.

### Phase 8 design checkpoint

At the reviewed PR #14 design head, the [Phase 8 plan active at that checkpoint](../plans/completed/phase-8-forecast-uncertainty.md)
was **PROPOSED / AWAITING APPROVAL** and included a draft ADR-021. The 2026-10-06 approval sync
below supersedes that proposal checkpoint; the accepted methodology is recorded in ADR-021.

No uncertainty runner or tests were added; no intervals, empirical quantile values, inventory
outcomes or new forecasts were calculated. Phase 8 implementation and Phases 9–10 remain
unstarted. Final-holdout outcomes for 2015-07-04 through 2015-07-31 remain protected under ADR-015;
their release requires the separately authorized frozen Phase 13 protocol.

### Phase 8 design delivery validation

Executed on Python 3.14.5 in the development environment with uv 0.12.23; a subsequent
`uv sync --locked --extra dev --python 3.14` verified the same environment (60 managed packages,
no package changes):

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS — 187 tests in 87.93s; existing fixtures only |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 74 files already formatted |
| `python scripts/check_docs.py` | PASS — 146 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 61 compatible installed packages |
| `git diff --check` | PASS |

Complete diff review confirms changes are limited to Phase 7 lifecycle closeout/archive, the
Phase 8 proposal and mechanical links/current-status synchronization. No code, tests, dependencies,
proposal or selected artifacts
changed. New-PR CI is not yet verified; delivery stops after opening the authorized design PR.

## Phase 8 methodology approval sync — 2026-10-06

The external Phase 8 methodology review is accepted in [ADR-021](DECISIONS.md#adr-021--chronological-empirical-forecast-uncertainty-and-conditional-operational-replay).
Phase 8 is **APPROVED / IMPLEMENTATION NOT STARTED**. PR #14 remains open and unmerged as the
design integration gate; implementation of the approved bounded protocol may begin after it
integrates into `main`.

Approval fixes the daily signed-residual estimator, exact horizon-specific ranks and n>=40 floor,
Fit A/Fit B chronology, and the complete operational-prefix estimator with p={0.90,0.95,0.98},
upper-rank rule and n>=50 floor. The saved historical Open values authorize development-only
conditional course replay and do not prove origin-time schedule availability. For Phase 13, actual
holdout Open must not be read, hashed, loaded or substituted before issuance; operational outputs
requiring future Open remain unavailable without separately reviewed origin-known schedule
provenance or a separately approved synthetic/conditional schedule that is not derived from
protected actual Open.

No uncertainty runner, fixture tests, interval calculations, quantile tables or fitted-table
freeze were produced in this approval sync. Fit B's actual tables, diagnostics, hashes and
availability require separate external implementation/results review before the values are
frozen. No Phase 9/10 implementation, final-holdout access or evaluation occurred; protected
2015-07-04 through 2015-07-31 outcomes remain unreleased.

Approval-sync local validation on Python 3.14.5 with the locked environment:

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS — 187 tests in 92.93s; existing fixtures only |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 74 files already formatted |
| `python scripts/check_docs.py` | PASS — 148 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 61 installed packages compatible |
| `git diff --check` | PASS |

## Phase 8 development-only implementation checkpoint - 2026-10-06

The approved ADR-021 implementation is **IMPLEMENTED / UNDER REVIEW** on branch
`feat/phase-8-uncertainty-implementation`, based on merged PR #14 commit
`305ddc80a4e3399698f64762ec26da2fc79cfb10`. Implementation PR
[#15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) is open and
unmerged; external implementation/results review is pending. The selected Phase 7 identity remains
`global_lightgbm_gbdt_regression_l1`; this work reads its saved paths only and performs no point
model fit, refit, tuning or selection change.

The canonical development run is `phase8-impl-20261006-final`, under the ignored directory
`data/processed/uncertainty/phase8-impl-20261006-final/`. An earlier implementation-validation run,
`phase8-impl-20261006`, is retained as an immutable prior run; `current.json` points to the canonical
run recorded here. Its manifest status is
`complete_with_unavailable_strata`; dates are 2015-05-23 through 2015-07-03 across the three
approved development windows. The run read 46,830 selected residual-path rows, with 38,553
Open=1 raw-primary errors and 46,830 routed operational errors. The saved Phase 7 outputs,
selected candidate manifest and all three original candidate output sets were SHA-256 verified
before and after the run; every input hash was unchanged. The run did not read or hash source
datasets or protected July 4-31 Open, Sales or Customers values.

Fit A has 22 of 28 daily tail strata available. Its h2 (n=32), h3 (n=33) and h9 (n=32) lower and
upper tails remain unavailable as `insufficient_calibration`; no neighboring-horizon fallback
was used. Fit B has 28 of 28 daily tail strata available. All 42 cumulative `(k,p)` strata are
available for each fit: 1,115 complete calibration Store-origin prefixes for Fit A and 2,230 for
Fit B at every k=1-14. The saved schedule interpretation is explicitly
`saved_source_open_assumed_known_at_origin`, a conditional historical replay. Empirical coverage
and width diagnostics are descriptive and have no approved numeric acceptance threshold or
production/service guarantee. Fit B fitted values remain unfrozen pending external review.

The run manifest records source revision `305ddc80a4e3399698f64762ec26da2fc79cfb10`,
`worktree_modified=true`, implementation source hash
`993e9e687eaa3ec3f662e0851e57a8fd7c93c499642c13c5d0a103cd6f36edce`, and `uv.lock` hash
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. Output row counts and
hashes are recorded in that manifest; primary table identities are:

| Artifact | Rows | SHA-256 |
|---|---:|---|
| `calibration_config.json` | - | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |
| `daily_residual_quantiles.csv` | 56 | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | 84 | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| `daily_intervals.parquet` | 62,440 | `160e68f4dd0237b61e60d20d041e06d0760fd94b006f7e89730e24e96b601fd2` |
| `cumulative_uncertainty.parquet` | 93,660 | `f338ff7189d652e64c8aa27f3d03c205c313185fb205f9f8a50b9776d59c0a0e` |
| `coverage_diagnostics.csv` | 392 | `7517435e7e4dd4bf0d08aa705c3555bb1ea945d6cae3dff8db8dfdf46ca0aaa4` |

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS - 199 tests in 92.05s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS - 77 files already formatted |
| `python scripts/check_docs.py` | PASS - 149 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS - 84 packages resolved; lock unchanged |
| `git diff --check` | PASS |

The implementation adds `src/rossmann_forecasting/forecasting/uncertainty.py`,
`scripts/run_forecast_uncertainty.py` and fixture coverage in `tests/test_uncertainty.py`. It also
updates this state record, the Phase 8 active plan, README usage/state text, and the ignored-data
layout guide. No ADR-021 methodology, Phase 7 algorithm/artifact, proposal, inventory layer,
Phase 9/10 work or final-holdout protocol changed. Canonical run manifest SHA-256 is
`d32ea0d3de331fc9e61ece091742edd8d23291383a2bb64779a1af945073a2bb`; its canonical policy/config hash is
`49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93`. Whole-repository checks on
Python 3.14.5 with the locked environment passed as listed above.

## Phase 8 targeted provenance and results review (2026-10-06)

PR #15 remains **OPEN / UNMERGED**; Phase 8 remains **IMPLEMENTED / UNDER REVIEW**, and Fit B is
**UNFROZEN**. The focused follow-up did not change ADR-021, quantile ranks/sample floors, Fit A/B
chronology, the selected LightGBM recipe, conditional saved-Open replay, or the final-holdout
firewall.

### Post-computation input-integrity gate

After estimation and staged-output verification, the runner now reruns the same allowlisted Phase 7
integrity verifier and compares the complete canonical input-lineage snapshot with the identities
verified before computation. The second pass rechecks the Phase 7 selection manifest and all six
manifest-listed selection outputs, then the three original candidate manifests and all 34
manifest-listed candidate artifacts. Candidate paths must still match the reviewed allowlist and
Parquet Date metadata must still stop by 2015-07-03 before file hashing. A failed recheck occurs
before the run manifest, official run-directory rename, or `current.json` update; staging is
removed, and earlier runs/current pointer remain unchanged. No raw/interim or unexpected source
path is opened or hashed.

A targeted fixture mutates the previously verified residual-path artifact during uncertainty
calculation. The post-computation identity comparison rejects publication; the fixture confirms
that an existing run and pointer retain their exact bytes and no failed run/staging directory is
left behind.

### New canonical development run and provenance

After the code fix, the runner published `phase8-impl-20261006-provenance-review` and atomically
advanced `current.json` to it. Both earlier immutable runs, `phase8-impl-20261006` and
`phase8-impl-20261006-final`, and every listed output hash in those runs were checked before and
after and remained unchanged. The runner's post-computation pass and an independent post-run
verification matched the initial Phase 7 input identities. The new manifest records all six Phase
7 selection outputs, all three original candidate manifests, and all 34 candidate-artifact hashes.

The new run manifest SHA-256 is
`63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2`. Its current implementation
source SHA-256 is `b89e3a9f16e5395632b2de55be90327aad6e546ead4251812606a878cabad04b`, matching the
source bytes measured for the new run; `uv.lock` remains
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. The prior canonical run
recorded source hash `993e9e687eaa3ec3f662e0851e57a8fd7c93c499642c13c5d0a103cd6f36edce`; direct
source-byte hashing confirmed that it matched the then-current implementation before this fix. It
does not match the implementation after adding the integrity gate. The new run's recorded Git
revision is `95d988abb0e381ed3c4b0aab58218435b494ee39` with `worktree_modified=true`; its source
hash, rather than Git revision alone, identifies the code bytes used.

The selected Phase 7 lineage remains unchanged: selection manifest
`03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc`; selected residual paths
`509bb4a822157850e8fb0309114a4003b98bcbc6b56f4a49244d8b6593e03382`; selected forecasts
`72566349b233ef26c8de5b4f9c1623ac66df8676ad0370ad63b192ed4c1b5b09`; recipe
`9ef3ee340ac57f14394857203ca3de5445ebae70972ec541a51947f38a49f799`; and original candidate
manifest hashes remain SN `f5e3a18a0a8bff709cb06b4e6282e22cbe3f84668937d3c3e57245b7c76072e3`, HW
`37b46babad1d197143bfda2f4f11aa65291c350b6b0687410bc4496b7171903b`, LightGBM
`ddd379fe4264dd90f618ba57791b97fcce3fd64199ffe95410c4f0d0695810c1`. The new output artifact
hashes match the prior canonical output hashes byte-for-byte; the new run ID and manifest bind this
publication to the post-fix code.

### Chronological assessment results

The run covers 46,830 selected residual-path rows from 2015-05-23 through 2015-07-03, with 38,553
raw-primary Open=1 errors and 46,830 conditional operational errors. Fit A assesses validation_2
(origin 2015-06-05); Fit B assesses validation_3 (origin 2015-06-19). Daily widths below use only
available raw-primary intervals; coverage denominators are the usable assessed interval rows.

| Fit | Open=1 labels | Daily intervals available | Availability | Hits / usable denominator | Empirical coverage | Width n | Mean width | Median width |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 13,438 | 12,258 | 91.22% | 10,344 / 12,258 | 84.39% | 12,258 | 4,128.75 | 4,203.37 |
| B | 13,437 | 13,437 | 100.00% | 12,263 / 13,437 | 91.26% | 13,437 | 4,116.49 | 4,152.12 |

Individual horizon diagnostics retain the approved sparse-stratum reasons and expose calibration
sample sizes separately from assessment denominators:

| Fit / horizon | Calibration n (distinct stores) | Assessment Open=1 eligible | Available / usable | Hits / usable | Coverage | Mean / median width |
|---|---:|---:|---:|---:|---:|---:|
| A / h2 | 32 (32) | 33 | 0 / 0 | - | unavailable | - |
| A / h3 | 33 (33) | 1,115 | 0 / 0 | - | unavailable | - |
| A / h9 | 32 (32) | 32 | 0 / 0 | - | unavailable | - |
| A / h10 | 1,115 | 1,114 | 1,114 / 1,114 | 1,084 / 1,114 | 97.31% | 7,382.53 / 7,382.53 |
| B / h2 | 65 (33) | 32 | 32 / 32 | 32 / 32 | 100.00% | 13,870.23 / 13,870.23 |
| B / h9 | 64 (32) | 32 | 32 / 32 | 32 / 32 | 100.00% | 15,183.32 / 15,212.95 |
| B / h10 | 2,229 | 1,115 | 1,115 / 1,115 | 1,069 / 1,115 | 95.87% | 6,873.54 / 6,873.54 |

Both tails at Fit A h2, h3, and h9 remain unavailable as `insufficient_calibration`; their
assessment populations include 33, 1,115, and 32 Open=1 labels respectively, with zero usable
intervals. No coverage value is reported where the issued interval is unavailable. Fit B h2/h9
results use only 33/32 distinct calibration stores across two origins and remain fragile despite
valid support.

| Fit | Operational population | Label-eligible rows | Available / eligible | Hits / usable denominator | Coverage |
|---|---|---:|---:|---:|---:|
| A | Open=1 | 13,438 | 12,258 / 13,438 (91.22%) | 10,344 / 12,258 | 84.39% |
| A | Open=0 | 2,172 | 2,172 / 2,172 (100.00%) | 2,172 / 2,172 | 100.00% |
| A | Pooled | 15,610 | 14,430 / 15,610 (92.44%) | 12,516 / 14,430 | 86.74% |
| B | Open=1 | 13,437 | 13,437 / 13,437 (100.00%) | 12,263 / 13,437 | 91.26% |
| B | Open=0 | 2,173 | 2,173 / 2,173 (100.00%) | 2,173 / 2,173 | 100.00% |
| B | Pooled | 15,610 | 15,610 / 15,610 (100.00%) | 14,436 / 15,610 | 92.48% |

Deterministic closed `[0,0]` routes account for 15.05% of Fit A's pooled usable denominator and
13.92% of Fit B's. Pooled coverage is respectively 2.35 and 1.22 percentage points above the
Open=1 branch. The diagnostics record zero Open=0 / positive-Sales violations for both fits.
This closure-driven increase is conditional-replay coverage inflation, not raw-model accuracy.

Cumulative upper-bound results are coverage of assessed actual operational prefixes `actual_total
<= U_k`. Every cell has 1,115 complete assessment prefixes and 1,115 available bounds; calibration
support is 1,115 prefixes for Fit A and 2,230 for Fit B. There are no unavailable reasons for
k=3..8.

| k | Fit A p=.90 | Fit A p=.95 | Fit A p=.98 | Fit B p=.90 | Fit B p=.95 | Fit B p=.98 |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 861/1,115 (77.22%) | 970/1,115 (87.00%) | 1,075/1,115 (96.41%) | 1,040/1,115 (93.27%) | 1,079/1,115 (96.77%) | 1,101/1,115 (98.74%) |
| 4 | 1,044/1,115 (93.63%) | 1,070/1,115 (95.96%) | 1,101/1,115 (98.74%) | 1,095/1,115 (98.21%) | 1,102/1,115 (98.83%) | 1,107/1,115 (99.28%) |
| 5 | 1,044/1,115 (93.63%) | 1,084/1,115 (97.22%) | 1,100/1,115 (98.65%) | 1,096/1,115 (98.30%) | 1,101/1,115 (98.74%) | 1,107/1,115 (99.28%) |
| 6 | 1,047/1,115 (93.90%) | 1,091/1,115 (97.85%) | 1,100/1,115 (98.65%) | 1,098/1,115 (98.48%) | 1,107/1,115 (99.28%) | 1,110/1,115 (99.55%) |
| 7 | 1,100/1,115 (98.65%) | 1,105/1,115 (99.10%) | 1,107/1,115 (99.28%) | 1,106/1,115 (99.19%) | 1,110/1,115 (99.55%) | 1,111/1,115 (99.64%) |
| 8 | 1,103/1,115 (98.92%) | 1,106/1,115 (99.19%) | 1,111/1,115 (99.64%) | 1,106/1,115 (99.19%) | 1,110/1,115 (99.55%) | 1,110/1,115 (99.55%) |

Across k=1..14 pooled by the 15,610 assessed prefixes per level, Fit A coverage is 15,009/15,610
(96.15%) at p=.90, 15,271/15,610 (97.83%) at p=.95, and 15,467/15,610 (99.08%) at p=.98.
Fit B coverage is 15,058/15,610 (96.46%), 15,317/15,610 (98.12%), and 15,477/15,610 (99.15%),
respectively. These repeated, dependent prefixes are descriptive, not independent replications or
service guarantees.

New run output hashes (byte-identical to the earlier canonical run's six outputs):

| Artifact | Rows | SHA-256 |
|---|---:|---|
| `calibration_config.json` | - | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |
| `daily_residual_quantiles.csv` | 56 | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | 84 | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| `daily_intervals.parquet` | 62,440 | `160e68f4dd0237b61e60d20d041e06d0760fd94b006f7e89730e24e96b601fd2` |
| `cumulative_uncertainty.parquet` | 93,660 | `f338ff7189d652e64c8aa27f3d03c205c313185fb205f9f8a50b9776d59c0a0e` |
| `coverage_diagnostics.csv` | 392 | `7517435e7e4dd4bf0d08aa705c3555bb1ea945d6cae3dff8db8dfdf46ca0aaa4` |

| Follow-up check | Result |
|---|---|
| Focused Phase 8 fixtures | PASS - 13 tests in 28.98s |
| Full `python -m pytest` | PASS - 200 tests in 95.14s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS - 77 files already formatted |
| `python scripts/check_docs.py` | PASS - 149 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS - 84 packages resolved; lock unchanged |
| Python 3.14 `pip check` | PASS - no broken requirements |
| `git diff --check` | PASS - only Git's expected LF-to-CRLF notices for the two edited Python files |

The implementation adds no model fit/refit/tuning or methodology change; the selected identity
remains `global_lightgbm_gbdt_regression_l1`. No raw/interim data or protected July 4-31 Open, Sales
or Customers were read, loaded or hashed. Fit B stays unfrozen pending external results review;
Phase 8 remains under review and Phases 9-10 remain unstarted.

## Phase 8 external results acceptance and Fit B freeze — 2026-10-07 (historical pre-closeout checkpoint)

GitHub confirms PR #15 was squash-merged into `main` at
`c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`. The external reviewer decision supplied for the
canonical Phase 8 results is **ACCEPT**: all 56 daily quantiles, 84 cumulative quantiles, 62,440
issued daily interval records, 93,660 cumulative records, and all 392 diagnostics passed independent
numerical review. This acceptance freezes the Fit B fitted quantile values only for the exact
canonical run `phase8-impl-20261006-provenance-review` below. It does not change ADR-021, the Phase 7
selected recipe, or any saved artifact.

| Frozen Fit B identity | SHA-256 |
|---|---|
| Canonical run manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| `daily_residual_quantiles.csv` | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` |
| `calibration_config.json` file SHA-256 (separate file identity) | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |

The immutable run was published before this review and its manifest/config retain their recorded
publication-time state (`external_fit_b_results_review_pending=true`,
`fit_b_quantiles_frozen=false`). The later dated acceptance above is the governance record that
freezes Fit B for those exact table/config identities; no canonical run, quantile, source artifact,
or pointer was rewritten or regenerated.

The review accepted the numerical record without establishing nominal coverage as a pass threshold.
Fit B raw-primary daily assessment coverage is **12,263/13,437 (91.26%)**, below nominal 95%, with
100% interval availability. Fit B h2/h9 calibration uses 65/64 rows but only 33/32 distinct stores
across two origins; the 32/32 assessment hits at each Sunday horizon remain fragile evidence. Fit A
h2/h3/h9 remain unavailable under the approved sample floor.

Under the conditional `saved_source_open_assumed_known_at_origin` replay, Fit B operational coverage
is 12,263/13,437 (91.26%) for Open=1, 2,173/2,173 (100%) for Open=0, and 14,436/15,610 (92.48%)
pooled. The deterministic closed `[0,0]` branch contributes 13.92% of the pooled usable denominator
and raises pooled coverage by 1.22 percentage points over Open=1. This is closure-driven inflation,
not raw-model accuracy or evidence that source Open was known prospectively. The saved schedule is
conditional; the dataset does not establish origin-time schedule availability.

The three Friday origins share stores and calendar shocks, and observations are dependent across
stores and origins. Accepted empirical coverage remains descriptive: there is no conformal validity,
per-store guarantee, or production/service guarantee. Cumulative values apply only to the approved
origin-anchored prefixes; no daily-review suffix calibration is authorized for Phase 10. The
2015-07-04 through 2015-07-31 final holdout remains protected under ADR-015 and was not accessed.
The selected identity remains `global_lightgbm_gbdt_regression_l1` (trial A, 180 rounds). No Phase
9/10 work has started.

### Documentation integration validation — 2026-10-07 (historical pre-closeout checkpoint)

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 200 tests in 96.50s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 77 files already formatted |
| `python scripts/check_docs.py` | PASS — 150 local destinations/anchors across 23 Markdown files |
| `uv lock --check` (uv 0.12.23) | PASS — 84 packages resolved; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

The pinned uv executable was isolated in a temporary directory for the lock check; the project
environment and `uv.lock` were not changed.

**Lifecycle:** Phase 8 is **REVIEWED / FORMAL CLOSEOUT PENDING**, not COMPLETE. Keep the active plan
in place. This documentation/governance change must first be reviewed and integrated; afterward,
perform a separate explicit closeout verification against the merged PR, accepted review, frozen
artifact identities, and holdout firewall. Only that authorized closeout may mark Phase 8 COMPLETE
and archive the plan.

## Phase 8 formal closeout — 2026-10-07

The closeout branch started from fetched `origin/main` at
`4dd7717fed57ff3b1f14789b980772c1968f3cba`. GitHub reports PR #15 and PR #16 as merged; the
verified squash-merge commits are `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821` and
`4dd7717fed57ff3b1f14789b980772c1968f3cba`, respectively. Both commits are ancestors of
`origin/main`, and PR #16's merge commit directly follows PR #15's merge commit.

The independent external results review ACCEPTED the canonical development results: all 56 daily
quantiles, 84 cumulative quantiles, 62,440 daily interval records, 93,660 cumulative records, and
392 diagnostics. The Fit B freeze record is present on merged `main`. The canonical run is
`phase8-impl-20261006-provenance-review`; its immutable local artifacts were available and checked
without regeneration:

| Frozen identity | SHA-256 | Local artifact verification |
|---|---|---|
| Run manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` | Match |
| Daily quantiles | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` | Match |
| Cumulative quantiles | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` | Match |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` | Match to the config's self-excluding canonical identity |
| `calibration_config.json` file | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` | Match |

The immutable run manifest retains its original publication-time flags:
`external_fit_b_results_review_pending=true` and `fit_b_quantiles_frozen=false`. The later
governance freeze does not rewrite the manifest, config, quantile tables, other run artifacts, or
current pointer. ADR-021 and the selected LightGBM recipe are unchanged.

**Closeout decision:** Phase 8 is **COMPLETE** as of 2026-10-07 based on verified PR #15/#16
integration, independent results acceptance, frozen identity checks, and confirmation of the
holdout firewall. The explicit acceptance limitations remain:

- Fit B raw-primary coverage is 12,263/13,437 (91.26%), below nominal 95%.
- Sunday h2/h9 calibration is sparse: 65/64 rows from 33/32 distinct stores across two origins.
- Forecast errors are dependent across stores and forecast origins.
- Operational results are a conditional historical replay assuming saved source Open was known at
  origin. Fit B's 14,436/15,610 (92.48%) pooled coverage is closure-inflated relative to its
  12,263/13,437 (91.26%) Open=1 coverage; deterministic closed routes contribute 13.92% of the
  pooled usable denominator.
- No conformal, per-store, production, or service-level guarantee is established.
- Cumulative quantiles apply only to approved origin-anchored prefixes. No later daily-review
  suffix calibration is authorized.
- The protected 2015-07-04 through 2015-07-31 final holdout remains unreleased.
- The target is monetary Sales turnover, not SKU-level physical demand.

At this Phase 8 closeout checkpoint, Phase 9 was PLANNED and Phase 10 had not started. The closeout
changed documentation only and did not change implementation, calibration results, quantile tables,
model artifacts, or dependencies.

### Formal closeout quality gates — 2026-10-07

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 200 tests |
| Ruff lint | PASS — `ruff check .` |
| Ruff format | PASS — 77 files already formatted |
| Documentation link checker | PASS — 154 local destinations/anchors across 23 Markdown files |
| `uv lock --check` (uv 0.12.23) | PASS — 84 packages resolved; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS — no whitespace errors |

The project virtual environment was used for Python/Ruff checks. Pinned uv 0.12.23 was run from
a temporary directory because no uv executable was installed on PATH; `uv.lock` and project
dependencies remain unchanged.

## Phase 9 design proposal — 2026-10-07 (historical proposal checkpoint)

**State at this historical proposal checkpoint:** Design **PROPOSED / AWAITING APPROVAL**. Phase 9
implementation had not started, and Phase 10 remained PLANNED / NOT STARTED. External methodology
acceptance and implementation authorization were the next boundary.

Fetched `origin/main` and verified
[PR #17](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/17) merged at
`f08a62aa980d0670186ed25ae1f6e5a018ff3781`. That commit is the clean base of
`docs/phase-9-inventory-design` and contains PR #15/#16 and the accepted Phase 8 closeout.
Unrelated worktree changes were absent at branch creation.

The [Phase 9 plan, now completed](../plans/completed/phase-9-synthetic-inventory.md) and
[proposal-stage ADR-022, now accepted](DECISIONS.md#adr-022--synthetic-monetary-scenario-contract) specify:

- Two development origins, June 5/June 19, H14 ending by July 3; 56-day Open=1 turnover anchors
  with a 28-row minimum, preserved missingness and cold-start retail-equivalent stock.
- Fixed seed 4209, exact keyed draws, five paired replicates, eight synthetic stress families,
  synthetic schedules/promotions/trend/seasonality and shared-shock dependencies.
- Explicit procurement conversion, carrying/unmet-value costs, display-only equivalent units,
  schema/keys/nullability, immutable artifacts/manifest hashes, failure behavior and planned
  fixture/numerical acceptance criteria.
- Separate observed Sales, frozen point forecasts/uncertainty and synthetic quantities.
  No synthetic feature enters LightGBM. No inferred physical/latent demand or real stockout.
- Phase 10 receives exogenous paths/parameters and provenance only; event order, queue,
  policies, KPIs and cost aggregation require its own design.

Open Phase 9 approval choices are the anchor/initial state, cost assumptions, deterministic
scenario/schedule specification and lineage/availability contract. The plan supplies concrete
recommended defaults for each. Phase 10's later daily-review suffix method is unresolved;
Phase 8 q values remain origin-prefix-only and do not automatically transport to synthetic
stress. Fit A is bound to June 5, Fit B to June 19; frozen artifacts are not altered.

This checkpoint adds no generated results. It references the previously accepted Phase 8
identities without new local artifact verification. Fit B raw-primary coverage remains
12,263/13,437 (91.26%), below nominal 95%; sparse Sunday h2/h9, store/origin dependence,
conditional saved-source-Open replay and closure-inflated pooled coverage remain disclosed.
No conformal, per-store, production or service-level guarantee is introduced.
The protected 2015-07-04 through 2015-07-31 holdout remains unreleased.

## Phase 9 methodology approval — 2026-10-07 (historical approval checkpoint)

**Decision:** External methodology review **ACCEPTED** the Phase 9 design at PR #18's reviewed
head `3820c2c34749b3baa4df954afc3daa0636cff271`. The decision was supplied for this
synchronization; the reviewer identity was not specified. The current design state is
**APPROVED / IMPLEMENTATION NOT STARTED**. The historical proposal checkpoint above retains its
original PROPOSED / AWAITING APPROVAL state.

The approval covers the four choices recorded in [ADR-022](DECISIONS.md#adr-022--synthetic-monetary-scenario-contract)
and the [Phase 9 plan, now completed](../plans/completed/phase-9-synthetic-inventory.md): origin-safe
56-day/Open=1 initialization with a 28-record floor, no imputation/fallback, zero anchors and
an empty initial order pipeline; illustrative c/a/g cost ranges and approved formulas; seed
4209's exact SHA-256 draw contract and paired synthetic scenario families; and the two-origin
development chronology, frozen Phase 7/8 bindings and immutable fail-closed artifacts.

**Required weekday-factor clarification:** Monday–Sunday factors sum to 7 and average 1 over
the calendar week. The default Monday–Saturday open-day factors sum to 6.20 and average
1.033333... . They are illustrative synthetic multipliers, not open-day-normalized factors
preserving the historical anchor's mean. The accepted factor values and generation formula
were not changed.

This is design approval only; no Phase 9 implementation or scenario generation occurred.
Phase 10 remains PLANNED and unstarted. Its rolling suffix calibration, event timing, queue,
replenishment policy and KPI methodology remain separately unapproved. Phase 8 q is restricted
to approved origin-anchored prefixes and does not transport to synthetic stress. Fit B raw-primary
coverage remains 12,263/13,437 (91.26%), below nominal 95%; Sunday h2/h9 evidence is sparse;
stores/origins are dependent; saved-source-Open replay is conditional and closure-inflated; no
conformal, per-store, production or service-level guarantee follows. The final holdout
2015-07-04 through 2015-07-31 remains unreleased and was not accessed.

### Executed design-proposal validation

| Check | Result |
|---|---|
| Full existing fixture suite, Python 3.14.5 | PASS — 200 tests in 95.93s; no Phase 9 tests or implementation added |
| Ruff lint | PASS |
| Ruff format check | PASS — 78 files already formatted |
| Documentation link checker | PASS — no broken local destinations/anchors |
| `uv lock --check`, uv 0.12.23 | PASS — 84 packages; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

Self-review checked the full documentation diff, schema/factor/count arithmetic, unavailable
anchor precedence, Monday reopening pulse, frozen-input metadata-before-hash ordering,
conditional quantile transport and phase boundaries.
Only Markdown files are changed; no Python implementation/test, dependency, real-data scenario,
calibration table, quantile or model artifact was changed or regenerated. No real-data pipeline
or final-holdout read was run. Accepted ADR-015 through ADR-021 methodology and completed
Phase 8 historical checkpoints are preserved. Local checks validate repository consistency,
not Phase 9's future numerical implementation or external methodology acceptance.

### Approval synchronization validation — 2026-10-07

| Check | Result |
|---|---|
| Full existing fixture suite, Python 3.14.5 | PASS — 200 tests in 97.11s |
| Ruff lint | PASS |
| Ruff format check | PASS — 78 files already formatted |
| Documentation link checker | PASS — 181 local destinations/anchors across 24 Markdown files |
| `uv lock --check`, uv 0.12.23 | PASS — 84 packages; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

Self-review confirms only the seven listed Markdown files changed; the approved weekday-factor
values and demand formula are unchanged. ADR-015/016/020/021, Phase 7/8 plans, code, tests,
dependencies, model and quantile artifacts remain unchanged. No scenario was generated and the
protected final holdout was not accessed. These checks validate documentation and repository
consistency; they do not implement or numerically validate Phase 9.

## Phase 9 implementation checkpoint — 2026-10-07 (historical pre-closeout checkpoint)

**State:** Design APPROVED by ADR-022; implementation **IMPLEMENTED / UNDER REVIEW** on
`feat/phase-9-synthetic-inventory`. Source commit is
`8dae4e43e06d815746456a1786acfc264b77093b`. [PR #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/19)
is open for implementation review. PR #18 is the merged design synchronization at
`97795ca5d868b512e5c2f6cae59bcec1d6ce19a4`; the implementation PR is pending. Phase 9 is not
closed, no Phase 10 work is authorized, and the final holdout remains protected.

### Canonical development run

Run `phase9-dev-20261007-canonical2` completed at `2026-10-07T00:59:31Z` with manifest
SHA-256 `cc148d3670c0b20c769f245488ddd7f535f4333e6b0cf759c60e544e9c6c8a82`. The manifest records
source revision `8dae4e43e06d815746456a1786acfc264b77093b`, source-file digest
`fbeaaea4623360ea41e631346e770090b3875cc40b20e9d07b4353e1e6eee49b`, `worktree_modified=false`,
and lock digest `584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. It binds
Phase 7 selection manifest `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc`
and Phase 8 manifest `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2`.
The canonical config hash is `8ded15545911738c9b6551a8af00627e65a231a2d89fea8687cd8c4d6e6b52d7`;
its serialized byte hash is `08fe01cf94866913388312ad30be81b2a831c0abc2524f50185b31980417820b`.

| Output | Rows | Bytes | Byte SHA-256 | Logical SHA-256 |
|---|---:|---:|---|---|
| `scenario_catalog.parquet` | 82 | 4,236 | `7c521c8b2956e2f4de30c70a903216b4a0e2727aee3f5b29947ac25876548e83` | `502c03238a1bf0f8932160199ab4e9c76d0583dd9b70516ee1d98d993e762b04` |
| `origin_anchors.parquet` | 2,230 | 112,699 | `e9bec421447771cae277b437e9e15eff14b0ac4e3c7b009120de70f9be69b131` | `6daee5caeaf50d33c7472a4bbf49e9daf72f62834743fe7409537942561d1bd3` |
| `store_parameters.parquet` | 91,430 | 2,498,919 | `c75aab0c9e54eb3ffe8519c53569ec68db9a2199df0674fd75e4bfc777400427` | `73d4e57d0792e0df529908db52bda242d19a8fabd3a7664db9aa835169bdd315` |
| `scenario_daily.parquet` | 1,280,020 | 41,921,287 | `f43920eed64fb83ebeb7d82effd345f54744994949e637735622d927dfb2203b` | `967b091a28887326c9024fe191722a3a95f887c7da5a873dd1200a28589a642d` |
| `scenario_config.json` | — | 32,991 | `08fe01cf94866913388312ad30be81b2a831c0abc2524f50185b31980417820b` | canonical hash above |
| `upstream_bindings.json` | — | 16,184 | `f1312ef684ab4b2335d8a3b194764f7aac81d6d35b21700e43b602644e1da357` | canonical hash recorded in the manifest |
| `validation_summary.json` | — | 26,521 | `09378b79139dd508ee911dc2a9d442165ec577e362ba15e4ca60bf553b69d0ce` | canonical hash recorded in the manifest |

The four output Parquet byte hashes were independently recomputed after publication. The output
logical hashes all match a reversed-input-order determinism run. The manifest records status
`complete`, all expected row counts, empty structural failures, and output reread/hash validation.
Scenario grid is 2 origins × (1 historical reference + 8 synthetic families × 5 replicates), with
all 1,115 configured stores and 14 target dates per scenario-store.

### Availability, ranges and arithmetic

| Origin | Stores | Available anchors | Unavailable | Zero anchors | Missing calendar dates | Closed-positive Sales rows |
|---|---:|---:|---:|---:|---:|---:|
| 2015-06-05 | 1,115 | 1,115 | 0 | 0 | 0 | 0 |
| 2015-06-19 | 1,115 | 1,115 | 0 | 0 | 0 | 0 |

The initializer read only `Store, Date, Sales, Open` from `data/interim/train.parquet` under
`origin-55 <= Date <= origin` and configured Store membership, then rechecked the input snapshot
before publication. It did not rehash the full prepared train file. Protected 2015-07-04 through
2015-07-31 values were neither read nor hashed. The run records `model_refit_or_tuning=false`,
`phase8_residuals_recomputed=false`, `forecast_or_uncertainty_used_as_synthetic_truth=false` and
`inventory_simulation_performed=false`.

Observed parameter ranges across the synthetic scenarios:

| Field | Minimum | Maximum |
|---|---:|---:|
| Supplier lead time (days) | 2 | 7 |
| Review period (days) | 1 | 1 |
| Protection period (days) | 3 | 8 |
| Initial coverage (open-day equivalents) | 1 | 11 |
| Initial stock value | 2,717.911111 | 254,647.8 |
| Procurement cost ratio | 0.5500066 | 0.8499613 |
| Annual holding rate | 0.1000006 | 0.2999871 |
| Holding-cost rate per calendar day | 0.00015436 | 0.00069392 |
| Goodwill penalty rate | 0.1000259 | 0.7499823 |
| Total stockout penalty | 0.2577159 | 1.1938692 |
| Average equivalent-unit value | 5 | 50 |
| Trend end change | -0.0999815 | 0.30 |
| Promotion response slope | 0.5000557 | 1.4996728 |
| Planned discount depth | 0.0500242 | 0.2999961 |

Observed daily factor ranges:

| Field | Minimum | Maximum |
|---|---:|---:|
| Weekday factor | 0.80 | 1.15 |
| Trend factor | 0.9000185 | 1.30 |
| Promotion factor | 1.0 | 1.5998691 |
| Common shock | -0.0984010 | 0.0995949 |
| Store-date noise | -0.1499999 | 0.1499960 |
| Combined noise factor | 0.7517842 | 1.2482753 |
| Demand stress factor | 0 | 2.0 |
| Discount depth | 0 | 0.40 |
| Synthetic turnover proxy | 0 | 106,054.2063 |

Holding-cost and stockout-penalty arithmetic maximum absolute error is 0. Combined-factor maximum
is 4.9650810021, below the approved 6.0 ceiling. No unavailable store or zero anchor was excluded;
zero synthetic turnover includes the declared zero-turnover scenario and closure routing, not a
claim about lost demand. Historical reference rows have future outcome fields unloaded.

### Checks and boundary

| Check | Result |
|---|---|
| Full fixture suite, Python 3.14.5 | PASS — 218 tests in 113.01s |
| Ruff lint, whole repository | PASS |
| Ruff format, whole repository | PASS — 82 files already formatted |
| Markdown checker | PASS — 182 destinations/anchors across 24 Markdown files |
| `uv lock --check`, pinned uv 0.12.23 | PASS — 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |
| GitHub Actions PR matrix | PASS — run [#45](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37555928596) on head `f9c41f0`; Python 3.12 and 3.14 jobs succeeded |

The real-data artifacts are ignored local outputs, not part of the PR. Sales, demand, inventory,
costs and equivalent units retain the approved monetary proxy semantics; no physical quantity,
actual inventory, true lost demand, policy winner, service result or savings is inferred. Do not
merge this implementation PR, start Phase 10, or mark Phase 9 complete at this checkpoint.

## Phase 9 external review fix — 2026-10-07 (historical review checkpoint)

The approved-configuration validation finding from PR #19 was fixed in source commit
`2ec2488adf065e692141eceb8e3f979df4679f45`. `_validate_config()` now reconstructs the accepted
contract through `default_config()` for the supplied normalized fixture store subset, preserves
run-specific upstream bindings and publication fields, and compares the full JSON-compatible
configuration. Changes to nested assumptions, omitted settings or unexpected configuration fields
fail before generation. No ADR, RNG, equation, schema or scenario-generation formula changed.

Because the source digest changed, a new immutable canonical development run
`phase9-dev-20261007-config-validation-fix` completed at `2026-10-07T01:26:56+00:00`. Its manifest
SHA-256 is `573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`. It records source
revision `2ec2488adf065e692141eceb8e3f979df4679f45`, source digest
`9b753cae8efdaca718f1f93dce6f4eb22c426abef24f48953b9b6f5eadbbcc0f`,
`worktree_modified=false`, and the unchanged lock digest
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. The approved semantic
config hash remains `8ded15545911738c9b6551a8af00627e65a231a2d89fea8687cd8c4d6e6b52d7`; the new
serialized config byte hash is `40a150dfa8e8aa734bf3a7a1ca9b917b7eca7b3b8386721ea4b35fcd66d86421`.

| Parquet output | Rows in both runs | Logical SHA-256 in both runs | Byte SHA-256 in both runs | Comparison |
|---|---:|---|---|---|
| `scenario_catalog.parquet` | 82 | `502c03238a1bf0f8932160199ab4e9c76d0583dd9b70516ee1d98d993e762b04` | `7c521c8b2956e2f4de30c70a903216b4a0e2727aee3f5b29947ac25876548e83` | Identical |
| `origin_anchors.parquet` | 2,230 | `6daee5caeaf50d33c7472a4bbf49e9daf72f62834743fe7409537942561d1bd3` | `e9bec421447771cae277b437e9e15eff14b0ac4e3c7b009120de70f9be69b131` | Identical |
| `store_parameters.parquet` | 91,430 | `73d4e57d0792e0df529908db52bda242d19a8fabd3a7664db9aa835169bdd315` | `c75aab0c9e54eb3ffe8519c53569ec68db9a2199df0674fd75e4bfc777400427` | Identical |
| `scenario_daily.parquet` | 1,280,020 | `967b091a28887326c9024fe191722a3a95f887c7da5a873dd1200a28589a642d` | `f43920eed64fb83ebeb7d82effd345f54744994949e637735622d927dfb2203b` | Identical |

The run validation status is `complete` with no structural failures. It reconfirmed 1,115 stores at
each of the two approved origins, the H14 development cutoff of 2015-07-03, and that protected
holdout values were neither read nor hashed. The previous `canonical2` directory and manifest
remain untouched; its manifest SHA-256 is still
`cc148d3670c0b20c769f245488ddd7f535f4333e6b0cf759c60e544e9c6c8a82`.

| Check | Result |
|---|---|
| Inventory scenario fixtures | PASS — 30 tests |
| Full fixture suite, Python 3.14.5 | PASS — 230 tests in 96.11s |
| Ruff lint, whole repository | PASS |
| Ruff format, whole repository | PASS — 82 files already formatted |
| Documentation link checker | PASS — 183 destinations/anchors across 24 Markdown files |
| `uv lock --check`, uv 0.12.23 | PASS — 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

The review fix is committed on the existing PR #19 branch. Phase 9 remains
**IMPLEMENTED / UNDER REVIEW**. The protected holdout remains unreleased, Phase 10 remains
unstarted, and this checkpoint does not authorize merge or closeout.

## Phase 9 independent implementation and numerical review — 2026-10-07 (historical pre-integration acceptance checkpoint)

**Decision: ACCEPTED.** The independent external code and numerical review accepted the final
Phase 9 implementation at source revision `2ec2488adf065e692141eceb8e3f979df4679f45` and the
canonical run `phase9-dev-20261007-config-validation-fix`, manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`. The reviewer identity was
not supplied. This acceptance is implementation and numerical evidence; Phase 9 remains
**IMPLEMENTED / UNDER REVIEW** until PR #19 is merged and formally closed.

The audit accepted 82 scenario catalog rows, 2,230 origin anchors, 91,430 store-parameter rows,
and 1,280,020 scenario-daily rows. All four Parquet output byte hashes exactly match `canonical2`.
The review confirmed monetary initialization and cost arithmetic, deterministic keyed sampling and
stress overrides, synthetic turnover calculations, and preservation of historical-reference
missingness. These results do not introduce any policy simulation or inventory-performance claim.

The accepted run and manifest were not regenerated or rewritten for this documentation-only
integration. It remains development-only: origin H14 ends on 2015-07-03, protected
2015-07-04 through 2015-07-31 outcomes were not accessed, and Phase 10 had not started at this
pre-integration checkpoint. PR #19
remains open and unmerged pending this synchronized head's external integration review and CI.

### PR #19 integration quality gates — 2026-10-07 (historical pre-merge checkpoint)

These checks were run after merging PR #20's `origin/main` into the existing PR #19 branch. They
are new integration evidence, separate from the earlier 230-test checkpoint above.

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 230 tests in 144.03s |
| Ruff lint | PASS — `ruff check .` |
| Ruff format | PASS — 82 files already formatted |
| Markdown link checker | PASS — 184 local destinations/anchors across 24 Markdown files |
| `uv lock --check` (uv 0.12.23) | PASS — 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |
| GitHub Actions Quality matrix | PASS — [run #50](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37562153977) on integration head `a82d080`; Python 3.12 and 3.14 jobs succeeded |

These fixture and repository checks do not read final-holdout outcomes or regenerate the accepted
Phase 9 run. Run #50's result is recorded here; the latest PR-head CI status is recorded in the
PR #19 description for final external integration review.

## Phase 9 formal closeout — 2026-10-07

**Decision: COMPLETE.** PR #19 is verified merged into `main` by squash merge
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22`, which is present in fetched `origin/main`. GitHub
identifies that commit as the PR #19 merge commit; the reviewed integration head was
`46788db3f5b81af37cda78bf44f054be2bc0098b`. PR #20's proposal rename remains integrated at
`ff3c11554144e79ee84c627c2bcd3619d23072d0`, and `docs/PROPOSAL.md` remains the canonical proposal
path. The accepted Phase 9 methodology remains ADR-022.

The external independent implementation and numerical review accepted source revision
`2ec2488adf065e692141eceb8e3f979df4679f45` and canonical run
`phase9-dev-20261007-config-validation-fix`, manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`. Accepted counts are 82
scenario catalog rows, 2,230 origin anchors, 91,430 store-parameter rows and 1,280,020
scenario-daily rows. Review confirmed approved synthetic generation, deterministic sampling,
monetary cost calculations, historical-reference missingness and artifact integrity. This
documentation closeout did not regenerate or rewrite the run or manifest.

The complete plan, including historical proposal, approval, implementation and review checkpoints,
is archived at [plans/completed/phase-9-synthetic-inventory.md](../plans/completed/phase-9-synthetic-inventory.md).
The closeout branch was started from fetched `origin/main` at
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22`. No Phase 9 generator, CLI, test, frozen Phase 7/8
model, quantile or artifact was changed. The protected final-holdout outcomes were not accessed
or hashed. The completed scope is synthetic monetary scenario generation only; it does not claim
physical inventory, observed stockouts, actual savings or policy performance. Phase 10 remains
PLANNED and not started, and no Phase 10 methodology is approved.

### Phase 9 closeout quality gates — 2026-10-07

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 230 passed in 131.42s |
| Ruff lint | PASS — `ruff check .` |
| Ruff format | PASS — 82 files already formatted |
| Markdown link checker | PASS — 189 local destinations/anchors across 24 Markdown files |
| `uv lock --check` | PASS — uv 0.12.23; 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

The approved link-maintenance change updates only ADR-022's plan pointer to the completed plan.
Its accepted status, methodology and substantive content remain unchanged. The relocated plan's
internal links and all repository-local Markdown destinations pass validation.

## Phase 10 methodology approval and integration — 2026-10-07

**State: APPROVED; IMPLEMENTATION NOT STARTED.** Human approval of the Phase 10 methodology and
ADR-023 was given on 2026-10-07. The initial technical methodology review and fresh independent
review both returned ACCEPT; the independent verdict is
`INDEPENDENT_PHASE10_DESIGN_REVIEW=ACCEPT`, with no blocking findings or required methodology
changes. This is model-assisted review evidence plus explicit human approval, not a claim of
GitHub-native reviewer approval. Phase 10 implementation is authorized as the next separate task.
This approval/integration task changes documentation only. Phase 9 remains COMPLETE; Phase 11 has
not started and is not authorized. The protected holdout remains unreleased.

The original design branch, `docs/phase-10-inventory-simulation-design`, was created from fetched
`origin/main` at `8234ab2170b7c76b00623c0f4e11a82dd8f2d4b2`, the Phase 9 closeout PR #21 commit.

The then-active Phase 10 plan, now at `plans/completed/phase-10-inventory-simulation.md`, and accepted
ADR-023 record the two approved origin/fit relationships, origin-frozen baseline/LightGBM-buffer
targets, daily review,
L full intervening demand days and EOD-t to BO-day t+L+1 receipts. They define lost-sales balances,
ending-stock holding-plus-shortfall costs, exact KPI denominators, the project-specific completed
positive-demand receipt-cycle service rate, finite-window terminal exposures and nine paired
sensitivity overlays. Synthetic q transport is explicitly uncalibrated. Future interfaces,
immutable artifact schemas/publication and fixture/numerical acceptance are design requirements,
not implemented capabilities or simulated results.

Self-review inspected the entire seven-file documentation diff. No source, scripts, tests,
dependencies, lock, accepted Phase 0–9 method or approved proposal content changed. Current status
and terminology agree across the active plan, ADR, roadmap, dictionary and READMEs. No contradiction
requires editing `docs/PROPOSAL.md`. Upstream manifest identities were copied from existing
governance records, not freshly verified by artifact access or hashing. No real-data pipeline,
model/scenario regeneration or simulation was run. Protected July 4–31 outcomes were not accessed,
inspected, hashed, summarized or evaluated.

### Documentation proposal quality gates

Commands use `.venv/Scripts/python.exe` (Python 3.14.5) and `.venv/Scripts/uv.exe` (uv 0.12.23).
The locked sync used `--inexact` to retain installed environment tooling; project dependencies and
`uv.lock` remain unchanged. These are existing fixtures/repository checks, not Phase 10 tests.

| Check | Actual result |
|---|---|
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv sync --locked --extra dev --inexact --python C:\Users\Minh\AppData\Local\Programs\Python\Python314\python.exe` | PASS — 84 packages resolved; existing project package rebuilt; no dependency/lock change |
| `uv pip check` | PASS — 62 packages checked; all installed packages compatible |
| `python -m pytest` | PASS — 230 passed in 107.94s |
| `python -m ruff check .` | PASS — all checks passed; nonfatal cache-write access warning |
| `python -m ruff check --no-cache .` | PASS — all checks passed without the cache warning |
| `python -m ruff format --check .` | PASS — 83 files already formatted |
| `python scripts/check_docs.py` | PASS — 213 local destinations/anchors across 25 Markdown files |
| `git diff --check` | PASS |

The approval changes no method or accepted Phase 0–9 contract, starts no simulator, and produces
no results or artifacts. The active plan remains in `plans/active/` during implementation and
review. The next authorized boundary is Phase 10 implementation under the accepted plan; Phase 11
and protected holdout access remain outside this approval.

### Approval integration quality gates

The following required checks ran after the approval documentation update using the locked
`.venv` environment. No Phase 10 implementation test or model/scenario pipeline was run.

| Check | Actual result |
|---|---|
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 62 packages checked; all installed packages compatible |
| `python -m pytest` | PASS — 230 passed in 130.21s |
| `python -m ruff check --no-cache .` | PASS — all checks passed |
| `python -m ruff format --check .` | PASS — 83 files already formatted |
| `python scripts/check_docs.py` | PASS — 214 local destinations/anchors across 25 Markdown files |
| `git diff --check` | PASS |

## Phase 10 implementation and development validation — 2026-10-07 (pre-review merge checkpoint)

**State at the merge checkpoint: IMPLEMENTED / UNDER REVIEW.** Implementation branch:
`feat/phase-10-inventory-simulation`; source/test correction commit:
`4aefc8c1f21a392270150d46aae610a5dea428e0`. PR #23 merged into `main` as
`15bce83cd63a4edfeed6defb95788da90d0f36d9` on 2026-10-07 before the external implementation review
was resolved. The later review returned REQUEST CHANGES with B1–B3; this historical section records
pre-review implementation evidence only. Phase 10 is not COMPLETE. Phase 11 remains NOT STARTED /
NOT AUTHORIZED, and the protected holdout remains unreleased.

The pre-review canonical development run was
`phase10-dev-20261007-implementation-v2`, with manifest SHA-256
`889e8e513c68791dae3c547e9df531ed9ed0c98ce257518c0c011b2a9fe6056e`. Its code revision is
`4aefc8c1f21a392270150d46aae610a5dea428e0`, source SHA-256
`347d6021923b7a82ddd4746335e8cfc7e827c338027c215b605efe7a9c572337`, and recorded worktree state
is clean. It verified these frozen development inputs:

| Phase | Run | Manifest SHA-256 |
|---|---|---|
| 7 | `365f22d4c3f94722a594ab934a22c4f6` | `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` |
| 8 | `phase8-impl-20261006-provenance-review` | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| 9 | `phase9-dev-20261007-config-validation-fix` | `573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761` |

The seven ignored artifacts are `simulation_config.json`, `policy_targets.parquet`,
`simulation_ledger.parquet`, `policy_summary.parquet`, `comparison_summary.csv`,
`validation_summary.json`, and `manifest.json`. Actual counts match the approved design: 383,560
target rows, 383,560 summary rows, 5,753,400 ledger rows, 172 cases, and 1,720 comparison rows;
the reference grid has 182,860 tracks and 2,742,900 ledger rows. There are 191,780 matched
case/Store pairs. Every requested track is complete: unavailable/incomplete tracks, exclusions,
and historical Open-assumption violations are zero. Both target and ledger artifacts contain the
valid `synthetic_stress` and `historical_replay` mode labels. The ledger spans June 5 through July 3,
2015, with zero post-cutoff rows.

All staged checks pass: zero invalid foreign keys, queue identity and daily/terminal balance
validation, target arithmetic, paired exogenous-input identity, cost-only trajectory identity,
exact nine-variant grid, and pinned upstream identities. `holdout_access`,
`protected_outcome_dates_read_or_hashed`, and `raw_train_file_hashed` are false; the target allowlist,
freeze-before-outcomes rule, unsupported-origin rejection, and terminal-day order suppression are
confirmed. Phase 9 was not regenerated, and no refit or recalibration occurred.

At the `synthetic_base` reference, pooled simulated holding-plus-shortfall cost is 90.787 million
for the historical-mean policy and 113.929 million for the LightGBM-buffer policy, a
forecast-minus-baseline difference of +23.143 million across 11,150 Store tracks. Conditional
historical replay is 15.101 million versus 19.377 million (+4.276 million across 2,230 tracks).
Across the remaining reference cases, the forecast policy is lower by 6,758 in demand-slump and
higher by about 70 in zero-turnover; the other reference cases are higher by 3.749–25.076 million.
These results describe the approved simulated assumptions and do not claim savings or superiority.

For the synthetic-base sensitivity cases, forecast-minus-baseline cost is +32.403 million at
p=.90, +9.034 million at p=.98, +22.349 million at L=2, +14.593 million at L=7, and +25.857
million at one-day initial coverage. Holding-rate overlays retain physical trajectories (+23.147
million at .10; +23.138 million at .30). The goodwill overlays are +12.759 million at .10 and
+33.473 million at .75.

For the synthetic-base reference, terminal on-hand/pipeline values are 8.830/292.443 million for
the baseline and 7.551/274.097 million for the forecast policy. Terminal stock-cost diagnostics
are 6.155/5.259 million, and terminal procurement commitments are 204.447/191.629 million.
These exposures are not included in the primary objective and are not savings.

At that checkpoint, the corrected v2 run was the current-pointer target. It followed an earlier
immutable publication whose target builder had serialized a Pandas `Series.mode` method
representation into the `mode` metadata. The source then used explicit column indexing, with a
regression assertion for both targets. The first run remains ignored and immutable under
`phase10-dev-20261007-implementation`; it is superseded and is not canonical evidence.

No second full run was performed after the corrected canonical run at that checkpoint. Fixture
determinism and ordering-invariance tests pass. A deterministic representative replay covered 18
June-5 Store-1 cases:
historical reference, all eight Phase 9 families at reference, and all nine synthetic-base OFAT
variants, both policies, 36 tracks and 540 ledger rows. Replayed ledger rows and summaries matched
the published subset exactly after explicit-schema casting; source/replay subset logical SHA-256
was `05da21fb002b14772c1eacb3aeb50b1f362d196170851075e26f787851b4a002`.

Quality gates after the correction: 34 focused Phase 10 tests passed; the full repository suite
passed (264 tests in 104.61 seconds); Ruff check and format, docs validation, `uv lock --check`,
`uv pip check`, and `git diff --check` passed. The data outputs remain ignored; no dependency, lock,
Phase 9 source/artifact, accepted methodology, or proposal text changed.

## Phase 10 external implementation review and corrective follow-up — 2026-10-08

The independent implementation review returned **REQUEST CHANGES** after PR #23 had merged. It
identified three implementation blockers, with no change to accepted ADR-023 methodology:

- **B1:** Phase 9's semantic date/schema preflight could be bypassed by a timestamp field and did
  not prove rejection occurred before Parquet byte hashing.
- **B2:** the first missing-demand row could retain dependent post-demand values, and the streaming
  validator did not validate an incomplete track's available prefix and unavailable suffix.
- **B3:** a positive receipt on terminal day T incorrectly removed the terminal right-censored
  receipt interval.

The fixes and regression tests were recovered onto `fix/phase-10-review-findings`, based on
`origin/main` at `15bce83cd63a4edfeed6defb95788da90d0f36d9`. Recovery matched the external binary patch
backup exactly. Source/test commit `296feac19cd69f94a74f7d3322044377f1f1413f` passed 48 focused
tests and 278 full-suite tests. Ruff check/format, documentation validation, `uv lock --check`,
`uv pip check`, and `git diff --check` passed. No Phase 7, 8, or 9 code, artifacts, or methods
changed.

A fresh full canonical run, `phase10-dev-20261008-review-fixes`, completed with manifest SHA-256
`0716fc92623b66f4d8a6024eecb608aa992596809458fa1b7c40595b66cbdd91`, code revision
`296feac19cd69f94a74f7d3322044377f1f1413f`, source SHA-256
`bb0e0f6f52e3d744da7d17a4a094e2e3ddbded19e9e69bc6fd2a1d9ccec8df7d`, clean-worktree provenance,
and `uv.lock` SHA-256 `584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. It pins the
existing Phase 7/8/9 runs and identities, records ADR-023, and states that protected holdout values
were not read or hashed, no refit/recalibration was performed, and Phase 9 was not regenerated.
`data/processed/inventory_simulation/current.json` points to this run. The v1 and v2 run directories
remain present with their original manifest hashes: v1
`4e5e992760836b93b44fffaff3baa497b79a6a24f6587694cece1a2891a45921`; v2
`889e8e513c68791dae3c547e9df531ed9ed0c98ce257518c0c011b2a9fe6056e`. V2 remains immutable
pre-review evidence and is superseded as the current canonical run.

The output has 383,560 target rows, 383,560 summary rows, 5,753,400 ledger rows, 172 cases, and
1,720 comparison rows. All 383,560 tracks are complete; incomplete/unavailable tracks and
historical Open-assumption violations are zero. Independent reconstruction from ledger receipt
dates found exactly 383,560 right-censored terminal intervals and zero summary mismatches. The
final positive receipt was before T for 108,556 tracks, on T for 236,743, and absent for 38,261.
The corrected summary counts the unfinished final interval for every track, including a receipt on
T and episodes with no positive receipts.

Headline primary costs are unchanged from v2. For synthetic-base reference, baseline is
90,786,517.967853, LightGBM-buffer is 113,929,065.505821, and forecast-minus-baseline is
+23,142,547.537968. Historical conditional replay is 15,100,677.170801 vs 19,376,775.902140,
difference +4,276,098.731339. The nine paired sensitivity differences are +32.403m (p=.90),
+9.034m (p=.98), +22.349m (L=2), +14.593m (L=7), +25.857m (C=1), +23.147m (a=.10), +23.138m
(a=.30), +12.759m (g=.10), and +33.473m (g=.75). Synthetic-base terminal stock is 8.830303m /
7.551179m, terminal pipeline 292.442932m / 274.096540m, terminal stock cost 6.155105m /
5.259219m, and outstanding procurement commitment 204.447440m / 191.629078m, respectively.
These are simulated monetary-turnover exposures, not realized inventory or savings.

Validation reports zero invalid foreign keys and post-cutoff rows and passes queue identity, daily
and terminal balances, target arithmetic, common policy input identity, and cost-only sensitivity
trajectory identity. Complete-track validation passed; incomplete-prefix and dependent-null checks
were not applicable because the canonical grid has no incomplete tracks. A representative
deterministic replay of historical reference, synthetic base, `promo_peak`, both origins, both
policies, and `holding_010` matched exactly: 16 tracks and 240 ledger rows. Published/replay logical
hashes match for ledger (`5277ff63e999658e5264cf207f5e1bed56674ddcd28b333a8b279adbfb1962bc`) and
summaries (`dd752db39d28c0913fbeb8fa14668acd8de296e0f5ea00ee1481b29a58f4e233`). A two-policy
terminal-receipt fixture replay verified a completed cycle plus a censored terminal interval and
has logical SHA-256 `7db6fe4f292dda065bc384cfe574819d3be8364111a2bd04ad33b1033c1406ee`.

The external backup remains at
`C:\Users\Minh\Desktop\hust\introba\project\phase10-review-fixes-local-backup.patch`; stash
`stash@{0}` remains applied and retained through safe push. The new [follow-up PR #24](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/24)
is open and unmerged. Focused re-review #1 returned REQUEST CHANGES: B1 pre-hash firewall, B3
terminal censoring, and B2 missing-demand simulation semantics passed; the sole remaining blocker was
incomplete-track validator coverage. The correction and refreshed evidence follow.

### Phase 10 focused re-review validator correction — 2026-10-08

The focused external re-review of PR #24 returned `PHASE10_FOCUSED_REREVIEW=REQUEST_CHANGES`.
B1 pre-hash firewall, B3 terminal censoring, B2 simulation semantics, and their prior regression
coverage passed. The only blocker was incomplete-track validator coverage. Commit
`5504d855fd60b8a038a4d6574e35b579ed0f439d` hardens the validator without changing simulation
semantics or ADR-023: it validates all available origin-row invariants and origin order arithmetic;
checks fixed policy/cost metadata and holding/penalty rate equations on every incomplete-track row;
and rejects receipt IDs after the first unavailable suffix row while allowing actual receipts on the
first missing-demand boundary. New fixtures reject each reviewer mutation independently, including
a valid L=2 prefix with an origin order and a receipt before missing demand. The fixture also checks
corrupt receipt amount/IDs, post-receipt pipeline, prefix stock, and prefix rate. Focused Phase 10 tests
pass (**50 passed**); the full suite passes (**280 passed**). Ruff, format, docs, locked dependency,
environment, and diff checks also pass.

The fresh immutable canonical run `phase10-dev-20261008-validator-fix` has manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`, source revision
`5504d855fd60b8a038a4d6574e35b579ed0f439d`, source digest
`a4c1ec83d4211c45d75afe4db9845b359ddb41f88f04f3611a0c3cda872096db`, a clean worktree record, and
the unchanged lock digest `584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`.
It uses the same pinned Phase 7/8/9 inputs. Independent content-hash comparison confirms identical
logical results to `phase10-dev-20261008-review-fixes` for targets
(`25d127258800c584edbb72685ff11c8043e464d88ed7539967b109c8923413f9`), ledger
(`0d58757f8b9cb099537f57d4a79b2f89be698dbf7704f93a67a1aa7db9a9ccbe`), policy summary
(`b9610f414bfd38a363cafe25afe7821eb3ed79a241423920bafa35126b9374c2`), and comparison
(`0133e439a6e6644fb565cbe317440a02e5617b7c668769b974dbbf29bb426bfd`).

The run again has 383,560 targets/summaries, 5,753,400 ledger rows, 172 cases, 1,720 comparisons,
383,560 complete tracks, and zero incomplete/unavailable tracks, Open-assumption violations,
invalid foreign keys, or post-cutoff rows. Incomplete-prefix and unavailable-dependent-null
validation fields are `not_applicable` because this canonical grid contains no incomplete tracks;
the new fixtures exercise those branches. An independent receipt-date reconstruction gives 108,556
final receipts before T, 236,743 on T, 38,261 with no positive receipt, 383,560 right-censored
terminal intervals, and zero summary mismatches. Headline costs, nine sensitivity differences,
terminal exposures, and representative replay results match the prior canonical run; their numerical
record remains above. No Phase 7/8 refit, Phase 8 recalibration, Phase 9 regeneration, or protected
holdout read/hash occurred. `current.json` now points to this run; v1, v2, and
`phase10-dev-20261008-review-fixes` remain immutable, with the latter superseded as current evidence.

At this validator-correction checkpoint, Phase 10 remained IMPLEMENTED / UNDER REVIEW pending final
focused external re-review. The accepted review and formal closeout are recorded below. Phase 11
remains NOT STARTED / NOT AUTHORIZED, and the protected holdout remains unreleased.

## Phase 10 formal closeout - 2026-10-08

PR #23 integrated the Phase 10 implementation at `15bce83cd63a4edfeed6defb95788da90d0f36d9`.
PR #24 integrated the B1/B2/B3 corrective implementation at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. Both PRs are closed and merged. The final focused
independent external/model-assisted technical review returned
`PHASE10_FINAL_FOCUSED_REREVIEW=ACCEPT_WITH_MINOR_CHANGES`. It was not a GitHub-native APPROVE review.

Review chronology and outcome:

- Initial implementation review: `PHASE10_IMPLEMENTATION_REVIEW=REQUEST_CHANGES`, identifying B1,
  B2 and B3 findings.
- Focused re-review #1: `PHASE10_FOCUSED_REREVIEW=REQUEST_CHANGES`; B1 PASS, B3 PASS, B2 simulation
  semantics PASS; the remaining B2 validator coverage blocker was subsequently fixed.
- Final focused review: B1 PASS, B2 PASS, B3 PASS; no blocking findings. Holdout firewall, canonical
  provenance, numerical regression, sensitivity, terminal accounting, reproducibility evidence and
  repository quality gates PASS.
- Sole minor issue: stale PR #24 metadata. The PR description was corrected with the accepted current
  canonical evidence before/around integration.

Accepted canonical run: `phase10-dev-20261008-validator-fix`; manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`. Source revision
`5504d855fd60b8a038a4d6574e35b579ed0f439d`; source digest
`a4c1ec83d4211c45d75afe4db9845b359ddb41f88f04f3611a0c3cda872096db`; `uv.lock` SHA-256
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. The canonical current pointer
continues to identify this run. Prior immutable runs remain preserved:
`phase10-dev-20261007-implementation`, `phase10-dev-20261007-implementation-v2`,
`phase10-dev-20261008-review-fixes`, and `phase10-dev-20261008-validator-fix`.

Canonical counts: 383,560 targets, 383,560 policy summaries, 5,753,400 ledger rows, 172 cases and
1,720 comparison rows. All 383,560 tracks are complete; incomplete tracks, unavailable tracks,
historical Open-assumption violations and post-cutoff outcome rows are zero.

Receipt accounting: final positive receipt before T for 108,556 tracks, on T for 236,743, and no
positive receipt for 38,261; total 383,560. The 383,560 terminal right-censored intervals and zero
summary mismatches preserve the rule that a final positive receipt begins an unfinished interval,
even when it occurs on T.

At the synthetic-base reference, baseline cost is 90,786,517.967853 and forecast-policy cost is
113,929,065.505821 (forecast minus baseline +23,142,547.537968). Historical conditional replay is
15,100,677.170801 versus 19,376,775.902140 (+4,276,098.731339). These are higher simulated
holding-plus-shortfall costs under the stated assumptions, not realized losses or universal model
performance claims.

Forecast-minus-baseline sensitivity differences remain +32.403m (p=.90), +9.034m (p=.98), +22.349m
(L=2), +14.593m (L=7), +25.857m (C=1), +23.147m (a=.10), +23.138m (a=.30), +12.759m (g=.10) and
+33.473m (g=.75). Cost-only overlays retain identical physical trajectories. Synthetic-base terminal
stock is 8.830303m / 7.551179m, terminal pipeline 292.442932m / 274.096540m, terminal stock cost
6.155105m / 5.259219m, and outstanding procurement commitment 204.447440m / 191.629078m for baseline /
forecast. These exposures remain outside the primary cost.

Representative replay covered 16 tracks and 240 ledger rows; the accepted replay ledger logical
SHA-256 is `5277ff63e999658e5264cf207f5e1bed56674ddcd28b333a8b279adbfb1962bc`. The accepted results are
reproducibility evidence for conditional simulated policy comparisons, not evidence of actual
Rossmann inventory or savings. Focused tests passed (50); the full suite passed (280). GitHub Quality
run [#64 / 37718032966](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37718032966)
passed on Python 3.12 and 3.14 for the reviewed implementation head.

**Phase 10 is COMPLETE once this closeout PR is integrated into `main`.** The implementation and
numerical evidence are accepted, corrective review findings are resolved, and formal closeout is
recorded in the completed plan. No Phase 11 work is part of this PR. Phase 11 remains PLANNED / NOT
STARTED / NOT AUTHORIZED. No final holdout evaluation occurred; the holdout remains unreleased.

### Phase 12 M2 independent review corrections — 2026-10-09

M2 remains IMPLEMENTED / UNDER REVIEW on `feat/phase-12-streamlit-m2`; existing Draft PR #30 remains
open and unmerged. This corrective task resolves findings M2-01 and M2-02 without starting M3/M4,
deployment or Phase 13.

M2-01 moves all Historical Sales, forecast and uncertainty DTO conversion ahead of their analytical
tables and charts. Safe typed provenance conversion rejects arbitrary objects and path-like values.
Malformed result data now produces a fixed `internal_error` for its panel, with no partial saved
rows or chart. Forecast and uncertainty remain independent: an uncertainty conversion error keeps
the successfully converted forecast visible.

M2-02 keeps `fill_between()` for contiguous intervals with multiple horizons and draws singleton
intervals as vertical saved lower-to-upper ranges with endpoint markers. The saved point remains
separate from its interval and can appear outside it. Missing and unavailable horizons split chart
segments, and saved table bounds, widths, reasons, points and nulls remain unchanged.

Validation: 71 focused dashboard/presenter/M2 tests passed. Whole-repository pytest passed 502 tests
on Python 3.12 and 502 on Python 3.14, with one existing Starlette/httpx deprecation warning per run.
Ruff lint and format passed. `uv lock --check` resolved 109 packages. `uv pip check` passed with 91
packages in the Python 3.12 environment and 93 in Python 3.14. The docs checker passed with 259
local destinations/anchors across 27 Markdown files; `git diff --check` passed. Git reported only
the configured LF-to-CRLF normalization notices for the modified files.

Tests used fixtures; no producer, saved artifact, model, metric, dependency or lockfile changed.
No real-data rerun, model fitting, ledger access, protected July outcome access, manual browser,
performance or deployment check was performed. PR #30 requires final external review; Phase 12 is
not complete.

## Phase 12 M3 implementation checkpoint - 2026-10-09

M2 is accepted and integrated by PR #30 at `327a274bfdad0bb97cdd614a36dc04cbbf8291a2`. Main-branch Quality [run #37955545881](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37955545881) passed for Python 3.12 and 3.14, satisfying the M3 authorization gate. M3 is IMPLEMENTED / UNDER REVIEW on `feat/phase-12-streamlit-m3`, based directly on that main SHA, in [draft PR #31](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/31), open and unmerged. Its model/inventory behavior, exact read-only smoke queries, row counts and service provenance are recorded in the [active Phase 12 plan](../plans/active/phase-12-streamlit-dashboard.md).

The focused dashboard/M2/presenter suite passed 98 tests. The full fixture suite passed 529 tests on each of Python 3.12 and 3.14, each with one existing Starlette/httpx deprecation warning. Ruff lint/format, Markdown links, lock consistency, the locked Python 3.14 dependency check and `git diff --check` passed. M3 smoke used only public application services and confirmed the adverse whole-case reference and `buffer_090` cost differences already recorded above remain visible. Store 1 policy pairs were comparable in that smoke; no noncomparable canonical pair was observed. No Phase 10 daily ledger, protected July outcome, producer, simulation, fit, or canonical artifact mutation was part of the work.

M3 remains under review; no merge or Phase 12 closeout is authorized. M4 is NOT AUTHORIZED, deployment remains undecided, Phase 13 is not authorized, and the final holdout remains protected.
