# Development Workflow

This workflow keeps `main` stable and gives the five-person team a reviewable record of project work.

## Branches

Create a focused branch for each task:

- `feat/*` — new project capabilities;
- `fix/*` — defect corrections;
- `docs/*` — documentation-only work;
- `refactor/*` — internal restructuring without intended behavior changes;
- `test/*` — test additions or corrections.

Use task-based branch names such as `feat/seasonal-naive` or `docs/data-dictionary`. Avoid personal-name branches. Do not develop features directly on `main`.

## Commits

Use focused commits with conventional-style prefixes:

- `feat: add seasonal naive forecasting baseline`
- `fix: prevent future sales leakage in rolling features`
- `docs: document synthetic inventory assumptions`
- `test: cover open-day forecast metrics`
- `refactor: extract reusable validation helpers`
- `chore: configure project linting`

Keep unrelated changes in separate commits. Never commit secrets, credentials, raw datasets, generated model artifacts, or temporary files.

## Normal Development Loop

1. Select an issue or clearly scoped task.
2. Read the relevant sources of truth and inspect the current implementation.
3. Create or update an execution plan under `plans/active/` for substantial work.
4. Create the appropriate task branch.
5. Implement the scoped change.
6. Run relevant validation and tests.
7. Self-review the implementation and inspect `git diff`.
8. Update documentation that changed in substance.
9. Commit focused changes and push the task branch.
10. Open a Pull Request, obtain review, and address findings.
11. Merge only after the branch is reviewable and required checks pass.

Do not force-push shared branches or rewrite shared history. Keep `main` in a stable, reviewable state.

## Documentation Updates

- Update `docs/PROGRESS.md` after meaningful tasks so it reflects the actual repository state.
- Update `docs/DECISIONS.md` only when a durable architectural or methodological decision changes.
- Update `README.md` when user-facing setup, usage, architecture, status, or repository structure changes.
- Do not modify `docs/proposal.md` unless the user explicitly requests it.

## Codex Task Handoff

When Codex finishes a coding task, it must:

1. list the changed files;
2. report only validation and tests actually run;
3. identify unresolved issues or state that none are known;
4. provide a concise Git status and diff summary;
5. leave commits, pushes, and merges to an explicit user request.
