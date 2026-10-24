# Project Plan

This roadmap derives from the [proposal](PROPOSAL.md) and accepted [decisions](DECISIONS.md).
[PROGRESS](PROGRESS.md) owns current implementation/review/integration state. Each phase below is
a milestone, not a requirement for a separate plan, branch, PR, or closeout ceremony.

## Execution packages and gates

Preserve Phase 0–14 IDs for auditability; do not renumber completed work. The historical milestone
groups remain useful for traceability; current remaining work is in the delivery matrix below:

| Package | Milestones | Exit evidence |
|---|---|---|
| Forecast comparison | 6–7 | Recursive global candidate, comparable development results, selected-method rationale |
| Uncertainty and inventory | 8–10 | Chronological interval diagnostics, reproducible scenarios, conditional policy comparison |
| Usable demonstration | 11–13 | Shared services/API/UI, frozen protocol, one sequential final evaluation |
| Delivery | 14 | Consolidated results, reproducible demo, report and slides |

A package may share one concise execution plan; required methodology approvals and phase boundaries
stay explicit. [PROGRESS](PROGRESS.md) owns closeout, integration and canonical run evidence for
completed Phases 0–12. Retain ADR-020's selected LightGBM trial A / 180-round recipe and ADR-021's
reviewed Fit B freeze for its exact artifact identities. The phase contracts and completed plans
below preserve historical milestones; their dated next-phase statements are not current task authority.
No final holdout scoring belongs to Phase 7. Freeze the model/preprocessing/refit recipe, uncertainty,
inventory policies/scenarios and selected deterministic monitoring rules before separately authorized
Phase 13 execution (ADR-015/025/026).

## Remaining delivery roadmap

The [proposal](PROPOSAL.md#23-assignment-requirement-traceability) maps all eight assignment
modules, and its [deliverables](PROPOSAL.md#30-final-deliverables) define the final artifacts.
This matrix owns future priorities, dependencies and acceptance; [PROGRESS](PROGRESS.md) plus
Git/code own actual state. Current status summaries are orientation, not new completion evidence.

### Priorities

- **P0 — Required for course completion:** scenario evidence, authorized final evaluation,
  public API and dashboard, monitoring/retraining-review design, supported inventory interpretation,
  and final repository/report/presentation/demonstration delivery, including their necessary inputs.
- **P1 — Quality and reproducibility improvements:** supporting EDA, documentation, provenance
  and robustness work needed to make results defensible. A required supporting check remains an
  acceptance dependency for its affected deliverable; it is not permission to skip a safeguard.
- **P2 — Optional extensions:** on-demand inference, additional models/features, cross-model
  inventory simulation, longer horizons, SHAP/Evidently/Spark/Docker or other infrastructure only
  for a demonstrated approved need. These do not block P0 delivery and require their own scope approval.

### Remaining work packages

| Priority / objective | Dependencies and current evidence | Required output and observable acceptance | Blocking approval or release gate | Next actionable step |
|---|---|---|---|---|
| **P0 — Safe analytical inputs:** prepare the inputs needed by WP1 and Phase 13 | Source/field/date identities and operator/custody design; fixture readiness is integrated, but no real WP1 preparation or Phase 13 execution is established in PROGRESS | Independently verified, versioned views/bundles with exact hashes, allowed purposes/dates/fields, availability assumptions and effective external bindings; no unauthorized protected values reach development layers | Separate source access, preparation, verification, binding/provider and protected staging authorizations under each work package; a grant for one context does not authorize another | Specify the pending real-input operation and trust boundary in the existing plan for owner review; do not execute fixture decoders on real inputs |
| **P0 — Forecast scenario comparison:** explain where the three accepted candidates differ | [WP1 plan](../plans/active/wp1-scenario-forecast-evaluation.md); L1/L2/L3-F and fixture M1/M2 integrated; real inputs and L4 analysis pending | Reproducible development-only paired comparisons, same three H14 origins/common eligible rows, primary MAE and supported supplementary metrics, coverage/missingness/segment counts, business interpretation and failure cases; reviewed results without reselection | Real-source handoff and L4 authorization; pending competition/volume/other extensions require an approved design. H segmentation remains blocked; ADR-028 is not accepted wholesale | Reuse accepted L1/L2 definitions; resolve pending input/method prerequisites and freeze the authorized analysis scope rather than restart model selection |
| **P0 — Final evaluation:** assess the frozen system once | [Phase 13 plan](../plans/active/phase-13-sequential-final-evaluation.md); M1–M3 integrated, phase PLANNED / NOT APPROVED; final replay unrun | Reviewed immutable issue-before-reveal ledger, exact two H14 blocks, LightGBM with Seasonal Naive contextual comparator, point/interval/availability results, monitoring and environment identity; explicit phase closeout | Independent M3 review, remaining milestones, provenance/custody preflight, approved resource budget, separately authorized rehearsal, mechanical staging and chronological analytical release | Obtain the pending independent read-only M3 review; advance only the next separately authorized milestone |
| **P0 — Public FastAPI demonstration:** deliver one reachable read-only API URL | [Public-demo plan](../plans/active/public-course-demo.md); synthetic bundle/provider/API integrated, S22 corrections present in Git, independent corrective review/B closeout unrecorded; no public deployment | Approved reachable URL with bounded read-only routes, explicit synthetic labels, health/readiness/view-availability distinctions, sanitized errors and recorded external checks against the pinned bundle | B review/closeout; Milestone C content/rights/security/resource/rollback/hosting/audience/window and explicit owner release approval; ADR-024 remains effective | Complete the existing independent Sol 6.1 corrective review, then prepare the C release decision for approval; no listener or host change now |
| **P0 — Public Streamlit demonstration:** deliver one reachable dashboard URL | Same approved immutable bundle and B/C gates as API; separate synthetic dashboard integrated; existing canonical dashboard COMPLETE locally | Approved reachable URL and tested relevant views, direct Python services, truthful evidence/unavailable states, trusted manifest pin and no fallback to canonical artifacts; recorded release/shutdown checks | Same release gates, including any required visual/security review; a future objective or local visual PASS is not public-release authority | Share the API release review and bundle approval; verify dashboard-specific acceptance within the same coherent release work package |
| **P0 — Monitoring and retraining review:** deliver a functioning report/dashboard and defined review triggers | ADR-026 selects narrow descriptive replay monitoring; implementation/results pending. [Proposal Sections 23–24](PROPOSAL.md#23-model-monitoring) describe broader commitments and an unvalidated candidate policy | Reproducible data-quality, characteristic, delayed forecast-performance and simulated-business views with populations/denominators; documented warning/unavailable/review states, development-only reference/windows/support/persistence and human dispositions | Later Phase 13 monitoring milestone for frozen summaries; separate accepted methodology/implementation scope for broader numeric triggers/bias/drift. ADR-028 and proposal policy parameters remain proposed | Prepare one concise extension design reusing the proposal, justify parameters only on eligible development evidence, and obtain approval before implementation; no adaptive final-test retraining |
| **P0 — Inventory recommendations and business interpretation:** report conditional policy trade-offs | Completed Phase 9/10 generator/simulator and adverse development evidence; any final episodes depend on authorized Phase 13 | Interpretable monetary targets/recommendations and matched service/cost/sensitivity results with exact denominators, missingness and terminal exposure; retain adverse findings. Final scope is two independent origin-frozen H14 episodes | ADR-025/026 execution/resource/release gates for final evidence; no new policy, rolling suffix calibration or assumptions without approval | Draft interpretation from reviewed development evidence now; incorporate reviewed final episodes later without claiming SKU procurement, observed savings or continuous 28-day optimization |
| **P0 — Final report and presentation:** deliver the course artifacts | GitHub source, dictionary and development evidence exist; final conclusions depend on reviewed WP1/Phase 13/monitoring evidence and authorized public links | Working repository handoff, complete Data Dictionary, reproducibility/evidence index, PDF report, PPTX slides and demonstration; checked claims/links and human ownership/AI-assistance disclosure | Completion/review of required evidence and each release/publication authorization; no invented URLs or unrun results | Draft report/slides structure and evidence index in parallel; finalize analytical claims and demonstration only after their dependencies pass |
| **P1 — Supporting source preparation and EDA:** produce the pending bounded STL evidence | [CC-02D runbook](CC-02D_CUSTODIAN_RUNBOOK.md); preparation/provider/diagnostic code integrated; no real bundle, binding or Rossmann STL findings | Authorized development-only bundle, independent verification/binding, reproducible decomposition/status/figures and reviewed findings with historical exposure and sparse-date limitations | Distinct source-access, preparation, verification, binding/provider-loading, STL and findings-publication approvals; mixed-source reads are protected access | Review the runbook's exact source/operator/purpose/implementation approval packet before any source read; keep this evidence separate from model selection |
| **P1 — Reproducibility and evidence audit:** make required outputs reviewable | Existing lock, fixture CI, canonical evidence and contracts; apply to each changed deliverable | Task-appropriate checks, original manifest/run identities, complete dictionary coverage, working local commands, consistent status/claims and reviewable handoffs; canonical numbers stay in PROGRESS | Data/artifact access, regeneration, file edits and publication stay within task authority; no historical reruns for cosmetic documentation changes | Audit only the affected links/interfaces/claims alongside each P0 task; record out-of-scope corrections for their owner |

### Parallel work and genuine dependencies

- Independent M3 review and the public-demo S22 corrective review can proceed in parallel with
  pending input/monitoring design and report-outline work. An available review/implementation
  agent may assist; retain each package's specified reviewer and owner gates.
- Controlled-synthetic public-demo readiness and release planning do not require Rossmann source
  access, WP1 results or final-holdout release. The API/dashboard share a release bundle and review
  package; neither must add on-demand inference or HTTP coupling. Render remains a candidate for
  assessment, not a selected host or authorized purchase.
- WP1 real analysis needs its approved real-input chain and analysis scope. CC-02 STL needs its
  own runbook authorizations. Phase 13 needs its own remaining implementation, provenance, resource,
  rehearsal, staging and release gates. Sharing source identities never transfers access permission.
- Broader operational monitoring can be designed as a separate development/synthetic demonstration.
  It is not a prerequisite for implementing ADR-026's already selected descriptive method. Resolve
  any proposal that would affect final-test choices before protected release; do not add numeric
  alarms, recalibration, retraining or model/policy changes during the frozen replay.
- Report outlines, dictionary/evidence audits and interpretation of reviewed development results
  can progress now. Final empirical conclusions require reviewed analytical results; live public
  claims require the actual authorized URLs. Synthetic interface examples cannot replace those results.

The [workflow](WORKFLOW.md) defines proportional plans/checks and handoff evidence. Reuse current
plans and one coherent PR per work package when publication is authorized; no routine correction
needs a new ADR or dedicated closeout branch. This roadmap grants no new implementation, source
access, scenario analysis, hosting, deployment, artifact generation or Phase 13 release authority.

## Phase 0 — Repository Foundation

**Objective:** Establish sources, scope, contribution rules, and reproducible planning.
**Dependencies:** Project intent/course requirements.
**Deliverables:** Proposal, roadmap, decisions/progress, compact agent/workflow rules.
**Acceptance / boundary:** Documents agree and distinguish planned from actual work; no speculative
model/data/application implementation is introduced merely to populate the tree.

## Phase 1 — Data Acquisition & Validation

**Objective:** Obtain and verify official immutable Rossmann inputs.
**Dependencies:** Phase 0 and authorized Kaggle access.
**Deliverables:** Acquisition/validation commands and snapshot evidence.
**Acceptance / boundary:** Source hashes, schemas, keys, coverage, missingness and warnings are
recorded; no raw mutation, unsupported correction, model or inventory work.
Full-source quality inspection is descriptive evidence, not forecasting validation.

## Phase 2 — Data Preparation & EDA

**Objective:** Preserve source meaning and document supported descriptive findings.
**Dependencies:** Phase 1 validated snapshot.
**Deliverables:** Separate joined train/test Parquet, reusable summaries, thin notebooks and EDA.
**Acceptance / boundary:** Many-to-one joins preserve rows/keys/nulls; absent dates remain absent,
valid spikes are retained, and associations are not causal effects. Historical full-source EDA
exposure is disclosed; model-facing statistics must later be recomputed from origin training data.

## Phase 3 — Feature Engineering

**Objective:** Provide forecast-origin-safe reusable predictors.
**Dependencies:** Phase 2 prepared data and approved feature definitions.
**Deliverables:** Frozen `phase-3-v1` 29-predictor schema, exact-calendar history API, audits/tests.
**Acceptance / boundary:** Shared ordered train/inference schema, complete lag/windows, no future
Customers, gap fill, target leakage, model-specific encoding or holdout-based feature selection.
[FEATURE_CONTRACT](FEATURE_CONTRACT.md) owns field semantics; later model adapters do not silently
rewrite the artifact contract.

## Phase 4 — Seasonal Naive Baseline

**Objective:** Establish the weekly, recursive 14-day benchmark.
**Dependencies:** Phase 2 history, shared keys and approved development windows.
**Deliverables:** Reusable forecasts/evaluation, coverage and MAE/RMSE/MAPE/WAPE evidence.
**Acceptance / boundary:** ADR-013 exact-date raw recursion, unavailable-history rules and
post-forecast Open routing are enforced. Evaluate observed open labels on development only;
no future actuals, fallback, holdout or final selection.

## Phase 5 — Statistical Forecasting

**Objective:** Evaluate fixed additive Holt-Winters against the benchmark.
**Dependencies:** Phase 4 and approved ADR-014.
**Deliverables:** Origin-censored fits, forecasts/diagnostics, coverage and identical-row comparison.
**Acceptance / boundary:** Fixed specification, >=28 contiguous-day minimum, complete recent
segment, clipped raw values, explicit failures/no fallback, same windows/metrics, and 99%
open-label availability guardrail. Final selection and holdout scoring are later work.

## Phase 6 — Global LightGBM

**Objective:** Implement one global recursive ML candidate.
**Dependencies:** Reviewed/closed Phase 5, Phase 3 contract, reviewed baselines and shared metrics.
**Deliverables:** Approved concise model plan, model adapter/training, 14-step recursive predictor,
fixture tests, development forecasts, reproducible configuration/manifest.
**Acceptance / boundary:** Follow the handoff below; use a finite predeclared tuning budget, fixed
seeds and chronological development evidence. Every recursive step is reproducible. No alternative
model, new feature schema, inventory input, final selection or holdout outcome access is implicit.

## Phase 7 — Walk-Forward Validation & Model Selection

**Objective:** Choose the simplest model whose additional complexity has defensible value.
**Dependencies:** Phases 4–6 and stable metrics/configurations.
**Deliverables:** Development-only paired model comparison, coverage/segment/horizon diagnostics,
selected-method and refit recipe, configuration freeze.
**Acceptance / boundary:** Use the three approved windows and identical-row comparisons while also
reporting standalone coverage. MAE is primary; include RMSE/MAPE/WAPE, compute/operational costs,
window stability and limitations. Retaining Seasonal Naive is a valid outcome. Do not force a
winner or inspect final holdout outcomes.
The 42-day late-season evidence and shared Friday origins limit annual/weekday generalization;
horizon and weekday are confounded. Any supplementary earlier origins require a precommitted
reviewed protocol used consistently for all candidates, not opportunistic window selection.

## Phase 8 — Forecast Uncertainty

**Objective:** Quantify daily and cumulative uncertainty for the selected fixed method.
**Dependencies:** Phase 7 development out-of-sample forecasts/residuals.
**Status:** COMPLETE following verified PR #15/#16 integration, accepted results review and
explicit closeout on 2026-10-07. See the [completed Phase 8 plan](../plans/completed/phase-8-forecast-uncertainty.md).
**Design:** [Phase 8 uncertainty plan](../plans/completed/phase-8-forecast-uncertainty.md),
approved in ADR-021 and integrated by PR #14. PR #15 implemented the unchanged approved protocol
from saved Phase 7 development artifacts and was merged at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`.
External numerical review accepted the canonical results; Fit B values are frozen for that exact
run, with identities in [PROGRESS](PROGRESS.md). The selected point model remains unchanged.
**Deliverables:** Horizon-specific 95% intervals, cumulative lead/protection-period quantiles,
chronological coverage diagnostics and explicit sample/availability counts.
**Acceptance / boundary:** Calibrate on earlier development residuals and assess on later origins
not used for that calibration; fitting-set coverage is diagnostic only. Selection-related
development assessment is not an independent final test. Preserve complete Store-origin residual
paths for cumulative errors, including the explicitly conditional saved-Open development replay;
never sum marginal daily upper bounds or assume independent errors silently. Pooled empirical
intervals promise neither per-store coverage nor conformal guarantees. The external implementation/
results review is accepted and Fit B values are frozen only for the identified canonical run;
PROGRESS records the hashes and observed coverage, including raw Fit B coverage below nominal 95%.
Final-holdout actual Open cannot serve as a planned schedule before issuance; operational outputs
requiring future Open remain unavailable without separately reviewed origin-known schedule
provenance or a separately approved synthetic/conditional schedule not derived from protected
actual Open. Cumulative results support origin-anchored prefixes only; no Phase 10 suffix
calibration is authorized here. No final-holdout evaluation is authorized. Phase 8 is COMPLETE
for the accepted canonical development run. Phase 9 is formally closed as COMPLETE. Phase 10's
methodology is accepted under ADR-023; its implementation and B1-B3 corrections are integrated, final
external/model-assisted review is accepted, and formal closeout is recorded in the
[completed plan](../plans/completed/phase-10-inventory-simulation.md) and [PROGRESS](PROGRESS.md).
Phase 10 is COMPLETE on `main` after closeout PR #25 merged at
`d437269b9f0cf36a842cdfd496ad50a310804768`.

## Phase 9 — Synthetic Supply-Chain / Inventory Layer

**Objective:** Provide reproducible operational scenarios absent from Rossmann.
**Status:** **COMPLETE.** PR #19 was squash-merged into `main` at
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22` after independent implementation and numerical review
acceptance. See the [completed Phase 9 plan](../plans/completed/phase-9-synthetic-inventory.md),
accepted ADR-022 and formal closeout in [PROGRESS](PROGRESS.md).
**Design:** [Completed Phase 9 plan](../plans/completed/phase-9-synthetic-inventory.md) and
accepted ADR-022. PR #18's methodology synchronization remains integrated at
`97795ca5d868b512e5c2f6cae59bcec1d6ce19a4`.
**Dependencies:** Phase 2 origin-censored development history, dictionary, ADR-016 units and
read-only Phase 7/8 lineage.
**Deliverables:** Fixed-seed scenario generator, assumptions/range/relationship checks, stress data.
The implementation writes 56-day open-turnover anchors, synthetic stock/cost/lead-time parameters,
separately labelled historical references and artificial stress paths, plus immutable artifacts and
validation evidence. The canonical development counts and hashes are recorded in PROGRESS.
**Acceptance / boundary:** Initialization uses only history at the June 5/June 19 development
origins; no protected final-holdout read, new forecast, calibration or frozen-artifact mutation.
Synthetic discount/lead-time/stock/costs stay outside the real Rossmann model feature matrix;
synthetic demand stress tests are separate from forecasting accuracy on real Sales.
No physical units, observed inventory, latent-demand correction or real-stockout inference.
Phase 9 supplies exogenous inputs and provenance to Phase 10; event order, queue, policy
comparisons and inventory KPIs are excluded. Phase 8 quantiles remain origin-prefix-only;
synthetic-regime transport and later daily-review suffix calibration are not approved here.
The accepted canonical run and manifest are recorded in [PROGRESS](PROGRESS.md); Phase 9 does not
implement inventory policies or establish physical inventory, observed stockouts or savings.

## Phase 10 - Inventory Simulation & Sensitivity Analysis

**Objective:** Compare simple replenishment policies under stated assumptions.
**Status:** COMPLETE. Formal closeout PR #25 merged into `main` at
`d437269b9f0cf36a842cdfd496ad50a310804768`.
**Design:** [Completed Phase 10 plan](../plans/completed/phase-10-inventory-simulation.md) and accepted
ADR-023. Human methodology approval, corrective implementation review, integration and formal closeout
are recorded in the plan and [PROGRESS](PROGRESS.md).
**Integration:** PR #23 merged at `15bce83cd63a4edfeed6defb95788da90d0f36d9`; corrective PR #24
merged at `fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. The accepted canonical development run is
`phase10-dev-20261008-validator-fix`, manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`.
**Deliverables:** Stateful order/receipt/stock ledger, policy/KPI comparison and sensitivity evidence;
final review accepted B1-B3 corrections with no blocking findings.
**Acceptance / boundary:** At June 5/Fit A or June 19/Fit B, freeze a historical-mean or
LightGBM-plus-buffer standing target from the original h1..P prefix. R=1, L=2–7, P=L+1<=14;
L means full intervening demand days, so EOD-t orders arrive BO-day t+L+1. Execute daily lost-sales
queue/stock transitions against the unchanged target through day 13; suppress day-14 ordering. No
forecast refresh, suffix bounds, q scaling, fit or recalibration. Synthetic q transport is explicitly
uncalibrated. Compare common inputs and complete matched episodes using value fill, positive-demand
stockout, ending-stock inventory and simulated holding-plus-shortfall cost. Use the project-specific
completed positive-demand receipt-cycle service rate, with policy-dependent denominator/censoring; no
guaranteed CSL. Retain terminal orders/exposure with identical treatment. Negative cost comparisons
remain part of the accepted evidence; no actual inventory, stockout, savings or optimality claim.
No final holdout evaluation or release occurred. At the Phase 10 closeout checkpoint, Phase 11 had
not started; its current M1 implementation/review state is maintained in [PROGRESS](PROGRESS.md).

## Phase 11 — Application Services & Thin API

**Status:** COMPLETE. M1-M4 are accepted; M3-01, M4-01 and FR-01 are resolved. PR #26 was
squash-merged into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`, and the implementation
and integration gates are satisfied.
**Execution plan:** [Phase 11 completed plan](../plans/completed/phase-11-application-services.md).
**Objective:** Expose the frozen analytics through reusable Python services and a small HTTP adapter.
**Dependencies:** Phases 7–10.
**Deliverables:** Forecast/uncertainty/inventory services, thin FastAPI adapter, fixture-backed
cross-layer integration evidence, and reproducible local startup/handoff guidance.
**Acceptance / boundary:** No notebook dependency, duplicated model logic or microservice system.
M1 safe readers, M2 DTO services, and M3 HTTP routes remain the shared chain; M3-01 was
resolved by preserving Starlette's `Allow` header on sanitized 405 responses. Future Streamlit calls
`ApplicationServices` directly. No new model/policy tuning, inference, simulation or artifact
packaging is authorized. Ignored canonical artifacts are local prerequisites for demo data routes;
fixture tests and process health require no Rossmann data or Kaggle credentials. M4 is accepted with
minor changes, including the resolved M4-01 documentation correction. PR #26 integration and final
merge-readiness review are complete; Quality #81 passed on the merge SHA for Python 3.12 and 3.14.

## Phase 12 — Streamlit Dashboard

**Status: COMPLETE.** M1-M4 are accepted and integrated. M3 PR #31 is merged at
`28aa42fdb2186dbbc340bef72917ce2e2ec06425`, with main Quality #96 passing both Python jobs.
M4 PR #32 is squash-merged at `5527e780d1a59108c041bb4ca33a32dbb3bc3aca`; main Quality #103
passed Python 3.12 and 3.14. The Technical Lead independently accepted the exact reviewed M4 head
`8b4275a24030f4ceb21b2f3d5f88b2c23016aae1`; the user reported PASS on human visual review of all
five screens, recorded as user-attested. The approved localhost-only use remains
`http://127.0.0.1:8501` under ADR-024; LAN, network, tunnel, firewall, cloud and public exposure
are out of scope. See the [completed plan](../plans/completed/phase-12-streamlit-dashboard.md),
[localhost runbook](DEPLOYMENT_LAN.md) and [M4 evidence](PROGRESS.md#phase-12-m4-integration-browser-and-local-performance-2026-10-10).
**Objective:** Provide an understandable course demonstration.
**Dependencies:** Accepted Phase 11 shared services (see the [completed Phase 11 plan](../plans/completed/phase-11-application-services.md)); it need not call FastAPI over HTTP.
**Deliverables:** Store/scenario controls, history/forecast/interval views, inventory assumptions and
alerts; one localhost-only Streamlit demonstration at `http://127.0.0.1:8501` under ADR-024,
now integrated and formally closed.
**Acceptance / boundary:** UI claims match supported inputs and clearly label synthetic quantities,
unknown future Open and empirical interval limitations. A 7-day view is a subset of the 14-day
path; 28-day capability requires separate design/evaluation. SHAP is optional if ordinary feature
importance and limitations suffice.

## Phase 13 — Monitoring & Sequential Final Evaluation

**Design proposal:** [M0.4 Phase 13 plan](../plans/active/phase-13-sequential-final-evaluation.md)
— METHOD SELECTED under ADR-026; the owner's A-bounded inventory scope remains recorded in
ADR-025. PR #38 integrated M1 at `6e7d11a29a593c5eddee640f7c44ca1b3b9cd923`; M2 PR #39 integrated
at `2a935aea30ab22110153d33d3a55dac44e67a1c8`, where main Quality #125 passed on Python 3.12 and
3.14. PR #40 integrated the synthetic M3 adapter and P40 corrections at
`1426f29878fd8d7aaa920482310c02842498198b`. M1–M3 are integrated; independent M3 review, source/
preparation preflight, development rehearsal, protected-source staging, analytical release, M4 and
later work remain separately gated. Phase 13 remains PLANNED / NOT APPROVED, and the final holdout
remains unreleased.

**Objective:** Evaluate the frozen system once and demonstrate historical monitoring.
**Dependencies:** Phases 7–12 frozen choices; source identity, provenance, availability, safe
acquisition and authorized preparation preflight; reviewed custody/provenance for any existing
partitions; an approved full-panel host resource budget; independent review of M3; and separate
authorization for development rehearsal, mechanical staging, and each analytical data-release gate.
**Deliverables:** Auditable forecast-before-reveal ledger, final point/interval/KPI summaries,
simulated inventory policy comparison, descriptive monitoring summaries/alerts, and
protocol/environment identity.

**Selected methods (ADR-026):** Use exactly two non-overlapping 14-day blocks: origin 2015-07-03
for July 4–17, then origin 2015-07-17 for July 18–31. Issue each complete block forecast before
revealing its targets and reveal observations in chronological daily order. The second origin may
use only Block 1 history already authorized and released through July 17 under the precommitted
refitting recipe. Configuration,
calibration, and policy changes and adaptive retraining remain prohibited during the final test.
Scheduled model/preprocessing refits may update fitted state only as required by that fixed recipe,
on eligible already-revealed training rows; no interval recalibration or recipe selection.

Retain the 1,115-store grid and exact 29-feature schema. Use separately versioned origin-safe
covariates with documented retrospective assumed-known availability where historical availability
is unverified, plus the conditional synthetic Monday–Saturday-open / Sunday-closed planning schedule
for scenario and observed-Sales-reference simulations. Keep actual Open post-release and separate
from planned Open and `ScenarioOpen`; report schedule mismatches after release and preserve positive
observed Sales. Source identity, provenance, safe preparation, and authorized acquisition remain
preconditions. If required covariates exist only in a combined source containing protected Sales or
Open, a separately reviewed safe preparation/custody procedure is required before any source access.
Do not infer physical isolation from column projection.

Use A2 logical/operator-enforced custody with separately staged default-deny views, immutable issue,
durable per-date intents, journals, and idempotent checkpoints; disclose the trusted-operator
assumption and do not claim strict physical isolation. A1 Windows identities/NTFS ACLs are optional
hardening. Mechanical staging and analytical revelation are distinct and separately authorized.
Apply the frozen June Fit B tables unchanged to July fresh fits only as an explicitly unvalidated
transport assumption, preserving ADR-021 identities, signed formulas, sample floors, availability,
and clipping; no recalibration, retuning, suffix borrowing, or coverage guarantee. Preserve the
ADR-025 A-bounded inventory scope and full-panel resource gate. Use descriptive daily/trailing
7/14-day monitoring by origin/horizon and deterministic integrity/data-quality alerts only, with no
arbitrary statistical or service thresholds. LightGBM is primary; issue the frozen Seasonal Naive
H14 contextual baseline and preserve standalone/common-row populations without new selection.

**Approved inventory scope — A-bounded (ADR-025, scope only):** Run two independent origin-frozen
H14 inventory episodes on those same July 3 and July 17 origins. Each episode sets the accepted
Phase 10 standing-target policy pair once at its origin; subsequent daily reviews execute those
unchanged targets while the simulated inventory state and daily KPIs advance after authorized
chronological revelation. A daily review in this scope is not a new forecast issuance or a freshly
calibrated protection-period recommendation; no new rolling forecast origin or daily suffix
recalibration is introduced. This is the explicit scope exception to the earlier
requirement to score only daily decisions with complete fresh protection-period coverage: do not
score or imply unsupported later-review protection coverage. These episodes do not demonstrate
continuous rolling 28-day inventory operation. Preserve Phase 10 paired event accounting, common
finite-window terminal treatment/censoring, and unavailable-decision reporting. Keep model and
policy behavior frozen; do not invent future demand/covariates or count overlapping forecasts as
extra independent primary tests. The full precommitted scenario/sensitivity panel is in scope
subject to a measured resource-feasibility gate; stop for an explicit scope/resource decision if
it exceeds the declared budget, without silent sampling.

**Selected-method and release boundary:** P13 methods are selected in ADR-026, while source identity,
availability/provenance, safe preparation, operator/partition provenance, host resource approval,
and all execution authorizations remain outstanding preconditions. A-full rolling inventory
capability remains unapproved. Development rehearsal, protected-source staging, and analytical
outcome release retain separate written authorization gates. This is one sequential final
evaluation, not a second unseen dataset after earlier holdout scoring. Simple pandas
summaries/plots suffice; Evidently is optional only for a demonstrated unmet need.

## Phase 14 — Final Documentation, Report & Demo

**Objective:** Deliver reproducible, evidence-based course outputs.
**Dependencies:** Final analytical claims require reviewed WP1, frozen Phase 13 and monitoring
evidence; public demonstration links require their own authorized release. Outlines, evidence
indexing and development-result interpretation can proceed in parallel before those final inputs.
**Deliverables:** GitHub repository handoff, complete Data Dictionary, reproducibility/evidence
index, PDF report, PPTX slides, demonstration, monitoring report/dashboard and consolidated results;
one public read-only FastAPI URL and one public Streamlit URL under the separately approved release.
**Acceptance / boundary:** Report the recorded final evaluation; no new tuning or repeated selection
on holdout outcomes. State historical descriptive exposure, short evaluation span, simulation
assumptions and negative results honestly. Deployment is a course demonstration, not a live
Rossmann production claim. The future two-URL public course-demo objective is narrowly accepted in
ADR-030; Milestone A is synthetic-only. Public runtime, exact content/rights, hosting and release
remain separately gated, and ADR-024's localhost behavior stays in force until release approval.
Verify delivered artifacts and reachable authorized views, report unavailable evidence and
adverse findings, and include human ownership/AI-assistance disclosure. Monitoring trigger
parameters in the proposal remain proposed until justified and approved in their separate scope;
Phase 14 reporting does not authorize adaptive retraining or reopen frozen evaluation choices.

## Phase 6 implementation handoff (historical)

Phase 6 is complete under accepted ADR-019 and was integrated into `main` by PR #10. This section
records the repository interfaces and boundary used for that implementation; the
[completed Phase 6 plan](../plans/completed/phase-6-global-lightgbm.md) records its execution and
formal closeout. Phase 7 owns later model selection and awaits separate design approval.

| Need | Source / interface |
|---|---|
| Current readiness | [PROGRESS](PROGRESS.md), Git/merged PRs and completed Phase 5 plan |
| Predictor order/roles | [FEATURE_CONTRACT](FEATURE_CONTRACT.md), [contract.py](../src/rossmann_forecasting/features/contract.py) `PREDICTOR_COLUMNS` |
| Prepared inputs | `data/interim/train.parquet`, Phase 2 manifest; [preparation.py](../src/rossmann_forecasting/data/preparation.py) |
| Static and dynamic assembly | [pipeline.py](../src/rossmann_forecasting/features/pipeline.py) `build_inference_features`; [history.py](../src/rossmann_forecasting/features/history.py) `build_origin_history_features` |
| Origins/firewall | [validation.py](../src/rossmann_forecasting/forecasting/validation.py) `APPROVED_DEVELOPMENT_WINDOWS`, `LAST_DEVELOPMENT_DATE`; ADR-013 |
| Metrics | [metrics.py](../src/rossmann_forecasting/forecasting/metrics.py) `summarize_forecast_metrics(..., forecast_column=...)` |
| Baselines | [seasonal_naive.py](../src/rossmann_forecasting/forecasting/seasonal_naive.py), [holt_winters.py](../src/rossmann_forecasting/forecasting/holt_winters.py); recompute on identical keys |
| Artifacts | Planned `data/processed/lightgbm/`; model binaries `artifacts/lightgbm/`, both ignored; manifests per WORKFLOW |
| Validation examples | [feature tests](../tests/test_feature_engineering.py), [baseline tests](../tests/test_seasonal_naive.py), [statistical tests](../tests/test_holt_winters.py), [metric tests](../tests/test_forecasting_metrics.py) |

At each origin, filter labeled fitting/history inputs through that origin (and development through
2015-07-03). Future-dated target covariates are allowed only under the declared origin-time
availability assumption. Fit labels on `training_label_eligible` / source Open=1; keep all observed
pre-origin Sales, including closed-day zeros, as history. Select exactly the frozen predictors; fit category
vocabularies/any learned preprocessing on training only and treat Store categorically.
`features_train.parquet` is a historical fitting artifact, not teacher-forced recursive validation
input. Default `features_inference.parquet` has origin July 31 and Kaggle target dates; it is not
development inference. Build each validation horizon from origin-censored actuals and earlier
predictions with the shared APIs. Missing dates/covariates cannot be manufactured from labels.

The initial recursive history uses non-negative clipped raw predictions; generate the raw path
without future Open/Customers/target labels, then apply known planned Open only to separate
operational routing. Unknown Open remains unresolved. This preserves the reviewed raw comparison
boundary; closed actual zeros versus raw recursive values can cause training/inference mismatch,
which must be reported in development horizon diagnostics. Closure-aware feedback or direct
multi-horizon forecasting is a separately reviewed extension, justified by development evidence.

The Phase 6 plan fixed the following before implementation: categorical/nullable adapter;
loss/objective and negative handling; recursive state and unavailable-path policy; future-covariate availability
assumptions; finite tuning budget/seed; chronological early stopping (inner training split or
approved origin evaluation); coverage/paired-comparison protocol and artifact manifest.
No shuffled split, full-history volume cohort, future Customers, Open_resolved routing, broad
model search or final-holdout-based decision is allowed.

The required behavioral evidence included target Sales/Open mutation invariance of raw forecasts,
origin rejection and h>1 recursion without teacher forcing, key/schema/category/null consistency,
missing-date/covariate behavior, raw/operational separation, coverage and identical-row metrics,
input non-mutation and ignored/provenance outputs. Run fixture/whole-repository checks and an
approved real-data development runner. PROGRESS and the completed execution plan record the
outcome. Phase 7 owns final selection under a separate approved design; no Phase 7 design or
implementation has started.
