# AI Agent Working Contract

## Project and scope

IT4063E Business Analytics project: forecast Rossmann monetary `Sales` at Store × Date,
primarily 14 calendar days, then demonstrate simulated inventory-value decision support.
Sales is turnover, not physical demand or SKU quantities. Synthetic operational variables and
equivalent units are assumptions, never observed Rossmann inventory or proven business savings.

## Read and resolve conflicts

Start with `git status`, the current branch, and `docs/PROGRESS.md`; do not infer the current
phase from a completed plan or chat history. For substantial work read the relevant sources in
this order, and inspect their code interfaces:

1. `docs/PROPOSAL.md`: business intent and scope.
2. `docs/DECISIONS.md`: accepted architecture/methodology and superseding records.
3. `docs/PROJECT_PLAN.md`: dependencies, acceptance criteria, and Phase 6 handoff.
4. `docs/PROGRESS.md` plus Git/code: actual state and canonical result evidence.
5. `README.md`: setup, commands, and user-facing capabilities.
6. This file and `docs/WORKFLOW.md`: agent and contribution rules.

Read `docs/DATA_DICTIONARY.md` for field/valuation semantics and `docs/FEATURE_CONTRACT.md`
for feature work. Acquisition, validation, and EDA docs own their historical evidence.
Higher-level intent does not silently override an accepted implementation contract: identify the
conflict and record an authorized clarification/superseding ADR. Edit the proposal only when the
task authorizes it; preserve its approved `$...$` inline-math formatting.

## Scope and approval

- Work within the requested task. New phases, feature-contract changes, alternative models,
  validation/metric changes, and new inventory assumptions need a written design before code.
  Implement those decisions only when the user has authorized them; existing authorization carries
  forward. Routine fixes within an approved design need no new ceremony.
- Read the current phase's active plan. Use one concise execution plan for substantial work or
  update the existing plan for review fixes; a small scoped correction needs no new plan.
- Distinguish PLANNED, APPROVED, IMPLEMENTED / UNDER REVIEW, REVIEWED, and COMPLETE as defined
  in WORKFLOW. Implementation/testing alone does not close a phase.
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

## Implementation and evidence

- Preserve raw/interim source values and sparse dates. Do not fix missingness, anomalies, or
  category meanings with unsupported assumptions; an absent date is not observed zero Sales.
- Reusable analytics belong in `src/`; notebooks are presentation/exploration and scripts expose
  commands. Prefer small functions and fixed seeds; avoid speculative frameworks/directories.
- Keep credentials, raw/derived data, models, caches, and temporary outputs untracked. Use the
  artifact conventions in `data/README.md`. New generated manifests record command/configuration,
  source and output hashes, code revision, seed, and environment/lock identity.
- Use `pyproject.toml` and generated `uv.lock`; add dependencies only for implemented scope.
  Use the locked environment and the whole-repository quality commands in WORKFLOW.
- Validate relevant behavior with fixture tests and inspect `git diff` for leakage/scope.
  Run a real-data development pipeline when forecasting/data behavior changes; documentation
  edits do not justify expensive model reruns or new holdout reads.
- Report only checks actually run. Update PROGRESS for meaningful results/state changes,
  DECISIONS for durable changes, README for setup/usage changes, and affected contracts together.
  Keep detailed numerical results in PROGRESS, linking rather than copying them into new plans.

## Git and completion

Use a focused branch from current `origin/main`; a necessary stacked branch must name its base
and integration dependency in its plan. Never continue new work on an already merged branch.
Preserve unrelated user edits; do not force-push, rewrite shared history, or delete branches/data
without authorization. Commit, push, PR, merge, and remote cleanup follow the user's task scope;
an implementation request alone does not authorize publication or merge.

A task is done when its scoped result, relevant tests/checks, self-review, and documentation agree.
Archive a completed ordinary task plan after validation; retain a phase plan active until reviewed,
merged, and explicitly closed. Hand off changed files, executed validation, unresolved limitations,
Git state, and the next authorized boundary. `main` remains the stable integration branch.
