# Development Workflow

Use one reviewable change at a time. Current phase/branch facts live in [PROGRESS](PROGRESS.md);
the [roadmap](PROJECT_PLAN.md) owns future dependencies. This workflow defines contribution
mechanics, not another copy of project status or forecast results.

## Document ownership and precedence

Read AGENTS first for operating constraints, then resolve substantive conflicts in this order:

| Level / document | Responsibility | Do not duplicate |
|---|---|---|
| 1. [Proposal](PROPOSAL.md) | Business questions, scope, limitations, planned system | Current phase status or run tables |
| 2. [Decisions](DECISIONS.md) | Accepted choices and traceable supersession | Every routine task/fix |
| 3. [Project plan](PROJECT_PLAN.md) | Phase dependencies, boundaries, acceptance and handoff | Current results |
| 4. [Progress](PROGRESS.md) + Git/code | Actual implementation/review/integration state; canonical result evidence | Entire execution plans |
| 5. [README](../README.md) | Short entry point, setup, commands, limitations | Proposal or full metric tables |
| 6. [AGENTS](../AGENTS.md) + this workflow | Agent rules and contribution lifecycle | Hard-coded current phase |
| Data/feature docs | Acquisition/validation/EDA evidence; dictionary and versioned field contracts | New model configuration |
| Active/completed plans | Scope, design options/approval, execution/checkpoint record | Another maintained source of metrics |

Completed plans are dated historical records: their “next phase” and old environment/test counts
describe that checkpoint. Preserve them; later accepted ADRs and PROGRESS determine current state.
Existing duplicated result tables are historical snapshots, not independently maintained result
sources. New plans link to PROGRESS. Keep one coherent plan per substantial work package and reuse
it for review fixes; minor corrections do not require a new plan or ADR.

## Authority and phase lifecycle

The task defines authority. Already approved scope/design does not need repeated approval.
A new phase or material methodology/feature/validation/business assumption change needs a written
design and authorization before dependent implementation. Commit/push/PR/merge/deletion are
performed only when included in the user's request or established authorization.

| State | Meaning |
|---|---|
| PLANNED | Design/options exist; implementation not authorized |
| APPROVED | Relevant design is accepted; implementation may start within its scope |
| IMPLEMENTED / UNDER REVIEW | Code and development evidence exist; external review/closeout pending |
| REVIEWED | External findings addressed and evidence accepted; integration may still be pending |
| COMPLETE | Required review, authorized merge, and explicit closeout verified |

Record integration separately from implementation: a feature branch can be implemented while
`main` still contains an earlier phase. Test passage does not imply review, merge, or completion.
An ordinary review/fix task can finish without closing the phase it touches.

## Branch and review loop

1. Check the worktree, fetch origin, inspect PROGRESS and relevant branches/PRs. Preserve unrelated
   changes. Start from current `origin/main`; record a stacked base/dependency when working on
   necessary unmerged code. Never add new phase work to an already merged branch.
2. Create a focused `feat/*`, `fix/*`, `docs/*`, `refactor/*`, or `test/*` branch.
   Read sources/code and reuse/create a concise active execution plan.
3. For a new phase/material decision, write the design and approval checkpoint before code.
   A design and its implementation may share a branch; a docs-only planning branch is optional.
4. Implement the scoped work and its relevant tests. Run the quality gate; run development-data
   pipelines when behavior changes, recording provenance and respecting the holdout boundary.
5. Self-review the full diff and cross-check affected docs. Record only actual checks/results.
6. If publishing is authorized, make focused conventional commits, push normally, open one PR,
   and obtain external review. Include the concrete problem/behavior, validation, limitations,
   phase state and integration dependency. Address findings on that same branch/PR.
7. Merge only when authorized, review is accepted, and required checks pass. Prefer squash merge
   for a focused PR; preserve meaningful design/evidence history in docs. Never force-push shared
   history. Rebase/merge conflict resolution must preserve already accepted contracts.
8. Verify the actual merged state. Record explicit phase closeout and archive its plan only then.
   A small post-merge correction may share the next authorized documentation/task branch; a
   dedicated closeout branch/PR is an exception, not a required phase ritual.

Prefer one implementation PR with its design, tests, docs, and review fixes. PR #4/#6 were
historical separate closeouts; they do not establish a requirement to repeat that pattern.
Do not mark COMPLETE in advance of a verified merge merely to avoid a later status correction.

## Environment, CI, and checks

`pyproject.toml` is the only hand-maintained dependency source; `uv.lock` is generated.
The reference Python is 3.14; the supported range is 3.12–3.14 (ADR-018).
Use pinned uv 0.12.23, then `uv sync --locked --extra dev --extra api --extra dashboard --python 3.14`
to install the fixture-test, local API and Streamlit AppTest extras; optionally add
`--extra acquisition` for Kaggle. The API and dashboard extras keep FastAPI, its server/client and
Streamlit out of the core forecasting dependencies.
See [README setup](../README.md#environment-and-quick-start).

After changing dependency bounds, run `uv lock`, review the resolved diff, and check
`uv lock --check`. Do not hand-edit the lock, copy an unfiltered pip freeze, or maintain a second
requirements list. Use `uv sync --locked` for reproducible environments; update packages deliberately
and rerun relevant behavior tests. Dependency addition alone must not silently change model design.
Future manifests should record Python/package versions and the lock hash with their code revision;
older manifests retain their documented limitations.

Activate the environment and run from the repository root:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/check_docs.py
git diff --check
```

The [quality workflow](../.github/workflows/quality.yml) runs locked fixture tests, package
consistency, Ruff and Markdown links for published PRs and pushes to `main` on Python 3.12 and
3.14. It needs no Rossmann files, Kaggle credentials, model fitting, or holdout outcomes. A local
pass does not establish the current PR head's remote check status; verify the live checks before
merge.
Real-data development runs are separate local evidence when relevant, not a mandatory docs gate.

Recommended `main` settings: require PRs, one human approval and the quality matrix; block force
pushes. Do not claim those settings are enabled without checking GitHub. The 2026-10-05 review
observed `main` unprotected; settings changes require separate authorization.

## Cleanup and handoff

After a verified merge, inventory the branch's unique commits and uncommitted work before cleanup.
A squash-merged branch may fail `git branch --merged`; verify its merged PR and compare changes,
rather than treating ancestry as the only proof. Retain unique changes until adjudicated. Delete
local/remote task branches only within authorized cleanup scope, then fetch/prune stale tracking
refs, fast-forward local `main`, and create a fresh branch for the next task.

A handoff lists changed files, checks actually executed, remaining limitations, current branch/
worktree/integration state, and the next authorized boundary. Do not label draft CI, an unmerged
phase, or a future package as already deployed, complete, or implemented.
