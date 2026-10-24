# AI Agent Working Contract

## Project and scope

IT4063E Business Analytics project: forecast Rossmann monetary `Sales` at Store × Date,
primarily 14 calendar days, then demonstrate simulated inventory-value decision support.
Sales is turnover, not physical demand or SKU quantities. Synthetic operational variables and
equivalent units are assumptions, never observed Rossmann inventory or proven business savings.
Prioritize the eight course modules and final deliverables in the proposal without inventing
observations, results, URLs or completion evidence, or changing accepted methods for presentation.

## Read and resolve conflicts

Start each task with `git status --short`, `git branch --show-current` and relevant
`docs/PROGRESS.md` entries. Identify the requested outcome, authorized files/operations,
dependencies and blocking approvals; choose the smallest sufficient plan and validation scope.
Do not infer the next phase from chat history or a completed plan. Read relevant context in this
order, using current working-tree documents and inspecting affected code interfaces when needed:

1. `docs/PROPOSAL.md`: business intent and scope.
2. `docs/DECISIONS.md`: accepted architecture/methodology and superseding records.
3. `docs/PROJECT_PLAN.md`: future priorities, dependencies, gates and acceptance criteria.
4. `docs/PROGRESS.md` plus Git/code: actual state and canonical result evidence.
5. `README.md`: setup, commands, and user-facing capabilities.
6. This file and `docs/WORKFLOW.md`: mandatory agent rules and detailed task/Git/handoff procedures.

Read `docs/DATA_DICTIONARY.md` for field/valuation semantics and `docs/FEATURE_CONTRACT.md`
for feature work. Acquisition, validation, and EDA docs own their historical evidence.
Active plans own scoped execution details; link to canonical evidence instead of copying result
tables or full histories. Read only what the task needs; minor corrections need no full-project reread.
Higher-level intent does not silently override an accepted implementation contract: identify the
conflict and record an authorized clarification/superseding ADR. Edit the proposal only when the
task authorizes it; preserve its approved `$...$` inline-math formatting.

## Scope and approval

- For a small, well-defined correction, work directly, minimize changes, check and summarize.
  Routine approved-scope fixes need no new ADR, design phase, plan or independent review unless
  the existing task contract requires one.
- For substantial work, read the relevant active plan/design and interfaces, reuse one concise
  execution plan, implement in reviewable increments, validate and self-review. State the plan in
  the task response/checklist before work when plan-file edits are restricted; do not create a competing document.
- New phases or material architecture, feature/model/evaluation, inventory, deployment-security
  or data-access changes need a written design/trade-offs and the required authorization before
  dependent behavior. Existing approval carries forward; do not repeatedly ask about covered details.
- Use WORKFLOW's lifecycle states. Tests do not establish review; integration does not establish
  phase completion; a future objective does not establish delivery/deployment. Preserve mandatory
  independent reviews, including existing work-package Sol 6.1 gates. AI review is not human GitHub approval.
- Stop at the requested boundary. Do not begin the next phase, add packages for future features,
  or declare a final model winner merely because one candidate has been implemented.

## Forecast information boundary

- No shuffled/random forecasting splits. Use the accepted chronological origins and metric
  contract in ADR-013 and `src/rossmann_forecasting/forecasting/validation.py`.
- Development model/evaluation reads must filter Date <= 2015-07-03 before labels reach those
  layers, and each fit/history input must also stop at its forecast origin.
- Protect 2015-07-04 through 2015-07-31 from development target inspection, tuning, learned
  preprocessing, and model/policy selection. Final evaluation requires an explicitly authorized
  frozen Phase 13 protocol; see ADR-015. Earlier full-source descriptive exposure is disclosed in
  EDA_FINDINGS; it is not permission to reuse full-period statistics for modeling.
- A precomputed historical lag row is not safe recursive validation input. Rebuild dynamic
  features from actuals through the origin plus earlier predictions from the same forecast run.
  Never teacher-force future actual Sales or use future Customers/Customers-derived predictors.
- Use calendar/holiday/planned promotion or static metadata only under an explicit availability
  assumption. A snapshot containing a value does not prove it was historically known.
- Source Open is eligibility/routing information, not a predictor. Generate the raw path before
  operational routing; unknown future Open stays unknown, and Open_resolved stays audit-only.
  Planned closures may route operational values to zero; target outcome labels cannot feed back
  into the raw path.
- Keep reviewed Seasonal Naive/Holt-Winters algorithms, failure policies, metric denominators,
  and coverage rules intact unless the task explicitly authorizes a methodological change.
  MAE is primary; RMSE, cautious MAPE, and WAPE are supplementary on observed source Open=1.
- Preserve the selected LightGBM recipe, frozen daily/cumulative uncertainty distinction and
  ADR-025/026's two independent origin-frozen inventory episodes. No continuous rolling inventory,
  actual SKU procurement, nominal service guarantee or adaptive final-test retraining is implied.

## Data access and public release

- A mixed source containing protected outcomes requires its separate authorized preparation/custody
  procedure before reads or hashes; a projection, manifest, receipt or binding grants no permission.
  Restricted WP1 fixture support is not a real-source path; use ADR-029 and the relevant active plan.
- ADR-024 keeps the existing app on localhost until a separately authorized release. ADR-030's
  future API/dashboard URLs do not authorize listeners, hosting, purchases, bundle publication or
  deployment. Preserve exact-content/rights/provenance, security, resource and owner-release gates.
  Synthetic interface examples prove behavior, not Rossmann analytical accuracy or fitted uncertainty.
- ADR-026 selects descriptive replay monitoring and deterministic integrity/data-quality alerts.
  Broader trigger policies in the proposal and ADR-028 remain proposed; implement only under their
  own approval, using development-only references, without adapting the frozen final replay.

## Implementation and evidence

- Preserve raw/interim source values and sparse dates. Do not fix missingness, anomalies, or
  category meanings with unsupported assumptions; an absent date is not observed zero Sales.
- Reusable analytics belong in `src/`; notebooks are presentation/exploration and scripts expose
  commands. Favor readable Python, small functions, existing interfaces and deterministic behavior;
  use explicit errors/unavailable states and tests of actual contracts. Avoid clever abstractions,
  hardcoded machine-specific paths, speculative frameworks and unused infrastructure.
- Keep credentials, raw/derived data, models, caches, and temporary outputs untracked. Use the
  artifact conventions in `data/README.md`. New generated manifests record command/configuration,
  source and output hashes, code revision, seed, and environment/lock identity.
- Use `pyproject.toml` and generated `uv.lock`; add dependencies only for implemented scope.
  Use the locked environment and task-appropriate checks in WORKFLOW; preserve required CI gates.
- Validate relevant behavior with fixture tests and inspect `git diff` for leakage/scope.
  Forecasting/data behavior changes require the relevant approved development pipeline; if access
  is not authorized, report the blocked validation. Documentation edits need no model reruns or holdout reads.
- Within authorized file scope, update PROGRESS for meaningful evidence/state changes, DECISIONS
  for material decisions, README for usage and affected contracts together. Report needed out-of-scope
  corrections instead of silently editing them. Preserve immutable artifacts and historical provenance.

## Communication

Use English for repository documentation. Communicate concisely; state material assumptions,
separate facts/plans/recommendations, surface blockers early and report only executed checks.
Avoid repetitive narration, questions already answered by the user/repository, future-completion
claims and promises of background execution. Stop at the requested boundary.

## Git and completion

For new independent work, normally use a focused branch from current `origin/main`; record a
necessary stacked base/integration dependency in its plan or handoff. Follow explicit branch
instructions and continue coherent uncommitted work without forcing a new branch or stashing it.
Never add new independent work to an already merged branch.
Preserve unrelated user edits; do not force-push, rewrite shared history, or delete branches/data
without authorization. Commit, push, PR, merge, and remote cleanup follow the user's task scope;
an implementation request alone does not authorize publication or merge.

A task is done when its scoped result, relevant tests/checks, self-review, and documentation agree.
Archive plans only within authorized closeout scope; keep phase plans active until their required
review, integration and explicit closure. No routine task needs a dedicated closeout PR. Hand off
outcome, changed files, decisions, executed checks/results, limitations, branch/integration state
and the next task's authorization status using WORKFLOW. Task completion is not phase/project
completion or delivery. `main` remains the stable integration branch.
