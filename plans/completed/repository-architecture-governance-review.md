# Repository Architecture and Governance Review

**Status:** COMPLETE as a scoped review task, 2026-10-05; changes remain local/unpublished.
This task does not implement Phase 6 or close Phase 5.

## Scope and baseline

- Branch: `docs/architecture-governance-review`, based on Phase 5 review HEAD `3d4fbfd`.
- `origin/main` is `01cdedb` (Phases 0–4); Phase 5 is unmerged on `feat/holt-winters`.
- Review all governance/data/feature docs, active/completed plans, package and test structure,
  and public GitHub branch/PR metadata. Preserve historical results and completed plans.
- Correct business claims, holdout sequencing, uncertainty/inventory semantics, Phase 6 handoff,
  source-of-truth ownership, task/phase lifecycle, and branch/CI/dependency policies.
- Add reproducible environment/CI infrastructure. Any Python compatibility edits are syntax-only;
  forecasting algorithms, results, raw data, and model configurations remain outside this task.

## Execution

1. Inspect and cross-check sources, code interfaces, evidence, and GitHub state.
2. Record traceable architecture clarifications/superseding decisions and edit the related docs.
3. Simplify AGENTS/WORKFLOW and future work packages without renumbering completed phases.
4. Add a dependency lock and fixture-only quality CI; validate the supported Python range.
5. Audit terminology, status, phase IDs, branches, paths, links, and mathematical unit consistency.
6. Run pytest, whole-repository Ruff checks, Markdown checks, and diff/self-review; fix findings.
7. Record actual results in PROGRESS; archive this review task plan when validated. Keep the
   Phase 5 plan active pending its own external review and authorized closeout.

## Acceptance

- Real Sales turnover and synthetic retail-equivalent inventory assumptions are distinguished;
  no causal, physical-demand, or actual Rossmann stockout/savings claim is implied.
- Phase 7 selects using development only; intervals/policies/monitoring are locked before the
  single sequential final holdout evaluation. Prior full-source descriptive exposure is disclosed.
- A new agent can locate Phase 6 inputs, windows, metrics, artifacts, tests, and approval boundaries
  from the repository, without interpreting precomputed validation lags as origin-safe inference.
- Each document has one responsibility; historical evidence is retained and current status
  distinguishes main from unmerged Phase 5 and this review branch.
- CI and reproducibility policies have concrete files and commands, with validation honestly
  distinguishing locally executed checks from GitHub settings or checks not yet activated.
- No holdout evaluation, Phase 6 implementation, remote branch deletion, settings change,
  publication, or merge occurs in this task.

## Review evidence

Completed the inspection/edit/cross-check/validation loop. ADR-015–018 record durable changes;
AGENTS/WORKFLOW were simplified, the Phase 6 repository handoff made explicit, and historical
plans/results retained. Added a universal uv lock, fixture-only Python 3.12/3.14 CI and a standard-
library local Markdown checker with persistent positive/negative fixtures. Forecasting source
changes are only three exception-tuple parentheses for compatibility, not algorithm changes.

Independent final cross-review covered concept/inventory semantics, fresh-agent Phase 6 handoff,
and environment/Git operations. Follow-up wording fixes scoped the origin cutoff to fitting/history,
disclosed historical holdout exposure, aligned accepted raw recursion, and required ordered
non-negative interval endpoints. Acquisition setup now uses the same lock as README/CI.

All required local checks and both isolated locked Python suites passed. Phase/ADR numbering,
proposal math delimiters, local links, branches/current state and source hash-only checks passed.
The canonical commands/counts/limitations are recorded in
[PROGRESS](../../docs/PROGRESS.md#repository-architecturegovernance-review--2026-10-05).

No holdout evaluation, Phase 6 implementation, raw mutation, remote deletion/settings change,
commit/push/PR/merge, or Phase 5 closeout occurred. This ordinary task plan is archived; the Phase 5
plan remains active. Publish/integrate this stacked review only with authorization and account for
its unmerged Phase 5 base. Next project boundary: finish Phase 5 review/integration/closeout, then
prepare Phase 6 design.

## Continuation audit

The follow-up request resumed the actual dirty branch at the same base, with no staged changes.
Preserved existing work, reread changed files/diffs, inspected recent commits, and repeated the
fresh-agent handoff. Corrected two remaining wording gaps: predicted-Sales feedback instead of
target-window actual insertion, and precommitted scheduled refitting of model/preprocessing state
from already revealed eligible history versus prohibited recipe selection/recalibration.
Final validations are recorded in PROGRESS; no publication or phase expansion was authorized.
