# Development Workflow

Use one reviewable change at a time: understand → plan → implement → validate → review → integrate
→ hand off. Scale the work to its risk. [AGENTS.md](../AGENTS.md) defines mandatory information,
source-access and runtime boundaries; the user's scoped task determines authorized operations.

## Document responsibilities

| Document | Responsibility |
|---|---|
| [Proposal](PROPOSAL.md) | Business scope, eight modules and intended deliverables |
| [Decisions](DECISIONS.md) | Accepted rationale, contracts, supersession and clearly unapproved proposals |
| [Project plan](PROJECT_PLAN.md) | Remaining priorities, dependencies and acceptance gates |
| [Progress](PROGRESS.md) | Current verified state, canonical numerical findings and limitations |
| [README](../README.md) | Concise entrypoint, installation, usage and current delivery status |
| Data/feature documents | Field semantics, scientific definitions, source validation and EDA evidence |
| Active plans | One scoped design/execution contract per unfinished work package |
| Completed specifications | Durable methods still needed to reproduce or interpret the implementation |

Git owns commit/PR/branch history; structured manifests own machine-readable provenance. Do not
maintain duplicate result tables, review transcripts or task checkpoint diaries in Markdown.
Immutable historical artifacts remain unchanged. Documentation cleanup does not change approvals.

## Scope and lifecycle

Start with Git status/current branch and relevant progress. Read the proposal, accepted decisions,
roadmap, actual evidence and affected interfaces needed for the task. Preserve unrelated edits;
never reset/stash/discard them. Small approved corrections need only a brief scope/check summary.
For substantial work, reuse a concise plan covering objective, included files/operations,
dependencies, implementation, validation and approval boundaries. No competing planning log is needed.

New phases or material model/feature/evaluation/inventory/security/data-access decisions require
written trade-offs and the applicable authorization before dependent implementation. Existing
approval carries forward. A proposed objective is not source/execution/release authority.

| State | Evidence required |
|---|---|
| PLANNED | Identified design/work, without dependent execution authority |
| APPROVED | Named scope/operation authorized; separate access/release gates still apply |
| IMPLEMENTED / UNDER REVIEW | Scoped result and checks exist; required acceptance pending |
| REVIEWED | Required independent review accepted the identified implementation/evidence |
| INTEGRATED | Authorized integration verified; closure/delivery may still be pending |
| COMPLETE | Scoped acceptance/checks/review agree; a phase also has verified integration and explicit closure |
| DELIVERED / DEPLOYED | Approved artifact/runtime is actually accessible to its intended audience |

Tests are not independent review. Integration is not phase closure. AI review is not human GitHub
approval. Existing named Sol 6.1, owner, security and human visual-review gates remain mandatory.
Routine fixes do not need newly invented review or closeout ceremonies.

## Implementation and validation

Keep reusable analytics in `src/`, scripts thin and notebooks presentational. Favor explicit errors,
determinism and small readable functions. Preserve sparse/null/source semantics and public interfaces.
No speculative dependencies or infrastructure. Generated outputs remain ignored under
[artifact conventions](../data/README.md); new manifests include command/configuration,
source/output hashes, code/seed and environment/lock identity.

Use Python 3.12–3.14 (3.14 reference), uv 0.12.23 and the committed lock:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dev --extra api --extra dashboard python -m pytest
uv run --locked --extra dev --extra api --extra dashboard python -m ruff check .
uv run --locked --extra dev --extra api --extra dashboard python -m ruff format --check .
uv run --locked --extra dev --extra api --extra dashboard python scripts/check_docs.py
uv pip check
uv lock --check
git diff --check
```

Choose relevant fixture checks for a focused change; broaden for shared interfaces, dependencies,
failures, unresolved concerns or required package/CI gates. Docs-only edits need link/claim/diff
checks, without model reruns. Forecasting/data behavior changes also need the approved origin-safe
development pipeline; if access is unavailable, report that validation gap rather than reading data.
Use a tracked-files-only checkout without ignored source/canonical artifacts for fixture-only
full suites: an optional inventory integration test otherwise discovers existing artifacts.

Self-review behavior, scope, leakage, metric populations, real/synthetic meaning, unavailable
states, assumptions, links/claims and the full diff. Record only executed checks. Performance changes
need representative fixture before/after measurements and identical outputs. Keep unfavourable results.
The [quality workflow](../.github/workflows/quality.yml) runs locked fixtures, dependency consistency,
Ruff and links on Python 3.12/3.14; local checks do not establish remote CI status.

`pyproject.toml` is the hand-maintained dependency source. Deliberate dependency changes use
`uv lock`, review the resolved diff and check the lock; never hand-edit it or maintain a second
requirements list. Add acquisition extras only for implemented authorized Kaggle use.

## Git and completion

Independent work normally starts on a focused branch from current `origin/main`; document any
necessary stack dependency. Continue coherent existing edits on their branch and never add new
independent work to a merged branch. Preserve unique changes during squash-merge cleanup.
Commit/push/PR/merge/deletion/publication/deployment follow the user's explicit scope; implementation
alone grants no remote publication or merge authority. Never force-push or rewrite shared history.

Integrate only after authorization, required independent review and actual CI checks. Do not claim
repository protections are enabled without checking. Branch/settings changes need their own scope.
Keep active phase plans until required review, integration and explicit closure. Archive/consolidate
only within authorized scope; routine tasks need no separate closeout PR.

Hand off outcome, affected files, material decisions, executed checks/results, limitations,
branch/worktree/commit state and remaining approval boundaries concisely. Update canonical owner
documents for meaningful state/usage changes without creating logs. A local task can finish without
publication; task completion does not establish phase, course or deployment completion.
