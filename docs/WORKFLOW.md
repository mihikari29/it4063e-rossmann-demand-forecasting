# Development Workflow

Use one reviewable change at a time. Current phase/branch facts live in [PROGRESS](PROGRESS.md);
the [roadmap](PROJECT_PLAN.md) owns future dependencies. This workflow defines contribution
mechanics, not another copy of project status or forecast results.

Follow **Understand → Plan → Implement → Validate → Review → Integrate → Close/Handoff**.
Scale the work to the task: a small correction can use a brief checklist and relevant checks;
substantial work reuses one concise execution plan. Integration happens only when authorized.

## Document ownership and precedence

Read AGENTS first for operating constraints, then resolve substantive conflicts in this order:

| Level / document | Responsibility | Do not duplicate |
|---|---|---|
| 1. [Proposal](PROPOSAL.md) | Business questions, scientific scope, limitations, intended deliverables | Current phase status or run tables |
| 2. [Decisions](DECISIONS.md) | Accepted choices and traceable supersession | Every routine task/fix |
| 3. [Project plan](PROJECT_PLAN.md) | Phase dependencies, boundaries, acceptance and handoff | Current results |
| 4. [Progress](PROGRESS.md) + Git/code | Actual implementation/review/integration state; canonical result evidence | Entire execution plans |
| 5. [README](../README.md) | Short entry point, setup, commands, limitations | Proposal or full metric tables |
| 6. [AGENTS](../AGENTS.md) + this workflow | Agent rules and contribution lifecycle | Hard-coded current phase |
| Data/feature docs | Acquisition/validation/EDA evidence; dictionary and versioned field contracts | New model configuration |
| Active/completed plans | Task-specific scope, design/approval, execution/checkpoint record | Another maintained source of metrics |

Completed plans are dated historical records: their “next phase” and old environment/test counts
describe that checkpoint. Preserve them; later accepted ADRs and PROGRESS determine current state.
Existing duplicated result tables are historical snapshots, not independently maintained result
sources. New plans link to PROGRESS. Keep one coherent plan per substantial work package and reuse
it for review fixes; minor corrections do not require a new plan or ADR.

## Authority and lifecycle evidence

The user's task and existing scoped approvals define authority. Routine details within an accepted
design do not need repeated approval. A new phase or material architecture, methodology, feature,
validation, inventory, deployment-security or data-access decision needs a written design and the
applicable authorization before dependent implementation. A proposed objective grants no execution
or release permission. A routine correction needs no new ADR or standalone design phase.

| State | Meaning |
|---|---|
| PLANNED | Work/design is identified; dependent implementation or execution is not yet authorized |
| APPROVED | The stated scope/design or operation has been authorized; separate source, execution and release gates still apply |
| IMPLEMENTED / UNDER REVIEW | Scoped changes and evidence exist; required review/acceptance remains pending |
| REVIEWED | The review required by that task contract accepted the identified snapshot and evidence; integration may remain pending |
| INTEGRATED | Authorized integration is verified at an identified revision; phase closeout or delivery may remain pending |
| COMPLETE | Scoped acceptance, validation and required review are satisfied; phases also require verified integration and explicit closeout |
| DELIVERED / DEPLOYED | The named artifact or runtime is available to its intended audience under the required acceptance/release authorization, with delivery or access evidence |

These are distinct evidence claims, not an automatic linear progression. A phase can remain
PLANNED while separately authorized fixture milestones are INTEGRATED; an integrated implementation
can await review or closeout. A task can finish locally without publication when that is its scoped
outcome. Passing tests is not review approval, merge authority or delivery. Local UI acceptance and
synthetic fixtures do not prove public deployment or empirical Rossmann results. Preserve historical
labels as dated checkpoints rather than rewriting them into new states.

## 1. Understand

Inspect `git status --short`, `git branch --show-current`, relevant diffs and current PROGRESS.
Identify the requested outcome, authorized files/operations, dependencies and blocking approvals.
Read the relevant proposal, accepted ADRs, contracts, active plan and interfaces; do not infer the
next phase from old chat or a completed plan. Distinguish current Git evidence from a recorded
historical checkpoint and report discrepancies without inventing acceptance.

Course completion means the eight modules and required deliverables in the proposal, within the
accepted Store × Date monetary Sales/H14 scope. Preserve the three-model ladder, selected recipe,
metric/feature/uncertainty contracts and simulated-inventory limits. No course requirement permits
fabricated SKU observations, future-target leakage, unsupported savings or invented completion.

Respect the [agent information boundary](../AGENTS.md), ADR-015 and ADR-025/026: development inputs
stop at the approved cutoff/origin, and protected source access, preparation, staging and analytical
release have distinct gates. Fixture-only approval does not authorize real inputs. ADR-024 keeps
the current application on localhost; ADR-030's future two-URL objective still needs content,
rights, security and specific owner release authorization. ADR-028's additional proposed methods
do not become accepted through documentation. The [public release contract](PUBLIC_DEMO_RELEASE_CONTRACT.md)
and [custodian runbook](CC-02D_CUSTODIAN_RUNBOOK.md) retain their specific controls.

## 2. Plan

For a small, well-defined approved-scope correction, work directly with a brief scope/check
summary; do not create a plan file, ADR or separate closeout PR by default. For substantial work,
reuse its active plan and update it for review fixes. Create a new plan only when the work needs
one and file creation is authorized. If plan-file edits are outside scope, state the concise plan
in the task response/checklist before work. A compact plan contains:

| Field | Required content |
|---|---|
| Objective | Concrete outcome and priority within the course roadmap |
| Scope / non-goals | Included behavior and the boundary where work stops |
| Dependencies | Accepted contracts, prerequisite evidence and any stacked branch/base |
| Authorized files / operations | What may change or run; protected operations excluded or separately gated |
| Approach | Small implementation increments using existing interfaces |
| Acceptance | Observable evidence that satisfies this task |
| Validation | Relevant checks, fixtures, compatibility and any separately authorized data run |
| Approval / release gates | Required design, named independent review, integration, data-access or delivery decisions |

Record material new methods and trade-offs before dependent code; do not repeatedly reapprove
accepted routine details. Independent workstreams may proceed in parallel when their own gates
permit; optional extensions must not block required deliverables.

## 3. Implement

Change only what the task needs and preserve unrelated user modifications. Follow accepted
interfaces and scientific contracts, favor readable reusable functions, deterministic behavior,
explicit errors/unavailable states and minimal dependencies. Avoid speculative abstractions,
future infrastructure, machine-specific paths and expansion into the next phase.

Keep behavior, usage and affected contracts synchronized within authorized files. Update the owner
document for durable decisions or actual evidence when authorized; otherwise report the needed
follow-up. Link canonical numerical results rather than copying tables. Preserve immutable
sources/artifacts, sparse dates and null semantics; keep credentials and generated data/models/
caches untracked under [artifact conventions](../data/README.md). New manifests retain command,
configuration, code/seed, source/output hashes and environment/lock identity without granting new
permission to access a source.

## 4. Validate

Choose checks by changed behavior and risk, and report only what actually ran:

| Task type | Minimum relevant validation | Additional gate when applicable |
|---|---|---|
| Documentation only | `python scripts/check_docs.py`, `git diff --check`, review links/claims and the full scoped diff | No model rerun, data regeneration or protected holdout read to verify prose |
| Code within an accepted design | Contract-focused fixture tests and relevant Ruff/format/documentation checks | Broaden to full fixtures and supported-version checks for shared interfaces, dependencies, broad regressions or an explicit package/CI requirement |
| Data / forecasting / inventory behavior | Relevant fixture/static checks plus the approved origin-safe development pipeline and provenance when behavior changes | Use only authorized inputs; source/preparation permission is separate. If unavailable, report the validation gap and obtain the required authorization before running it |

Repeat or broaden checks when failures, new edits or unresolved concerns justify it. A small change
does not automatically require expensive historical experiments or every local test; mandatory
package acceptance and CI checks remain in force. Use fixture-only or artifact-free validation
where required; do not discover or open ignored datasets merely to establish a test environment.

### Environment, CI, and command reference

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

Activate the locked environment and run the commands relevant to the validation scope from the
repository root. These are the whole-repository quality commands when that scope is required:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/check_docs.py
uv pip check
uv lock --check
git diff --check
```

The [quality workflow](../.github/workflows/quality.yml) runs locked fixture tests, package
consistency, Ruff and Markdown links for published PRs and pushes to `main` on Python 3.12 and
3.14. It needs no Rossmann files, Kaggle credentials, model fitting, or holdout outcomes. A local
pass does not establish the current PR head's remote check status; verify the live checks before
merge.
Real-data development runs are separate local evidence when relevant, not a mandatory docs gate.

## 5. Review

Self-review every scoped diff against this checklist:

- Correct behavior, readable implementation and relevant contract tests/checks.
- Authorized scope only; unrelated edits and accepted history preserved.
- Scientific validity, exact metric populations and real/synthetic meaning retained.
- No future-information leakage, protected-data access or changed release permissions.
- Assumptions, errors, unavailable results and validation gaps stated explicitly.
- Documentation agrees with code, Git and recorded evidence; no false completion claims.

Use independent review when the task contract requires it. Existing named Sol 6.1, Technical Lead,
owner, security and human visual-review gates in work-package plans remain binding; do not replace
them with self-review, another model or passing tests. Other routine tasks need no new independent
review requirement. When separate implementation/review agents are available, divide work to
improve review, but do not assume a particular model or delegated authority is always available.
An AI review must be identified as such and cannot be presented as a human GitHub approval.

## 6. Integrate

New authorized work normally uses a focused `feat/*`, `fix/*`, `docs/*`, `refactor/*` or `test/*`
branch from current `origin/main`, checking/fetching the remote base when needed. Preserve existing
uncommitted work before any switch. Continuing work and review corrections normally stay on the
same branch/PR; do not force a new branch during an explicitly continuing documentation task.
Record the base and integration dependency for a necessary stack. Never add new phase work to an
already merged branch.

Commit, push, PR creation, merge, branch deletion and deployment require the applicable user
authorization; implementation authority alone does not grant them. Prefer one coherent PR with
design, implementation, tests, docs and review fixes over tiny administrative PRs. Describe the
concrete problem/result, validation, limitations, lifecycle state and dependencies; address findings
on that PR. A design-only or separate closeout PR is optional unless a contract requires it.

Merge only when authorized, required review is accepted and required checks pass. Passing tests
does not authorize merge. Prefer squash merge for a focused PR; preserve meaningful design and
evidence in the documents. Never force-push shared history or rewrite accepted commits/ADRs.
Conflict resolution must preserve accepted contracts. Verify the actual integrated revision and
applicable CI after merge; do not infer integration from a local test or draft PR.

Recommended `main` settings: require PRs, one human approval and the quality matrix; block force
pushes. Do not claim those settings are enabled without checking GitHub. The 2026-10-05 review
observed `main` unprotected; settings changes require separate authorization.

## 7. Close / Handoff

A scoped task is done when its result, relevant validation, self-review and required acceptance
agree. Task completion does not close its phase or project. Phases still require their stated
review, verified integration and explicit closeout; record that evidence in the existing plan and
PROGRESS when authorized. Do not mark a phase COMPLETE in advance of a verified merge. Archive an
ordinary completed task plan after acceptance when archiving is in scope; keep a phase plan active
until its closure criteria are met and archiving is authorized. No dedicated closeout branch/PR
is required by default.

After a verified merge, inventory the branch's unique commits and uncommitted work before cleanup.
A squash-merged branch may fail `git branch --merged`; verify its merged PR and compare changes,
rather than treating ancestry as the only proof. Retain unique changes until adjudicated. Delete
local/remote task branches only within authorized cleanup scope. Fetch/prune stale tracking refs
and fast-forward local `main` when appropriate; do not let cleanup discard uncommitted or unique
work or implicitly start the next task.

Give a concise final handoff containing:

1. Objective and actual outcome, separating facts from recommendations.
2. Files changed and any intentionally preserved unrelated work.
3. Important decisions and assumptions, with canonical references.
4. Checks actually executed and their results; identify unrun required checks.
5. Remaining limitations, blockers and approval gaps.
6. Current branch, worktree, review and integration/delivery state.
7. The next recommended task and its authorization status or smallest action needed to unblock it.

Report material blockers early and avoid repeated questions already answered by the task or
repository. Keep documentation and handoffs in English. Do not promise background execution or
label draft CI, an unmerged phase or a future package as already deployed, complete or implemented.
