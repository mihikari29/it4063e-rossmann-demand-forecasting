# AGENTS.md

## Project

This repository contains the IT4063E Introduction to Business Analytics
group project:

"Retail Demand Forecasting for Inventory Optimization (FMCG):
A Store-Level Business Analytics and Inventory Decision Support System
Using Rossmann Store Sales Data."

## Sources of Truth

Read these files before making substantial changes:

1. `docs/proposal.md` — authoritative project requirements.
2. `docs/PROJECT_PLAN.md` — project roadmap and milestones.
3. `docs/PROGRESS.md` — current implementation status.
4. `docs/WORKFLOW.md` — development and Git workflow.
5. `docs/DECISIONS.md` — important architectural decisions.
6. `docs/DATA_DICTIONARY.md` — dataset and synthetic variable definitions.

Do not modify `docs/proposal.md` unless explicitly instructed by the user.
Its current `$...$` inline-math formatting is approved and must not be reverted.

## Core Project Constraints

The unit of analysis is Store × Date.

The primary forecast target is Rossmann `Sales`.

The primary forecast horizon is 14 days.

This project is NOT SKU-level forecasting.

Rossmann `Sales` represents monetary turnover, not physical product units.

Inventory calculations must therefore be described as inventory-value
decision support unless explicitly operating on simulated equivalent units.

Synthetic supply-chain data must never be presented as real Rossmann data.

## Data Leakage Rules

Time-series integrity is mandatory.

Never randomly shuffle observations for forecasting validation.

Features must only contain information available at the forecast origin.

Do not use future actual `Sales` when constructing features.

Lag and rolling features must be time-safe.

Do not use future `Customers` to predict future `Sales`.

Future-known calendar, holiday, and planned promotion information may be used.

## Forecasting Strategy

Required model ladder:

1. Seasonal Naive
2. Exponential Smoothing / Holt-Winters
3. Global LightGBM

More complex models require justification.

Use rolling-origin / walk-forward validation.

Keep the final holdout untouched during model and feature selection.

Primary metric: MAE.

Also report RMSE, MAPE with caution, and WAPE.

Evaluate primary forecasting metrics on `Open = 1` observations.

## Engineering Rules

Reusable logic belongs in `src/`, not only in notebooks.

Notebooks are primarily for exploration, analysis, and presentation.

Raw data must never be modified in place.

Generated/intermediate data should be reproducible from scripts.

Use fixed random seeds where randomness is required.

Do not commit secrets, API keys, credentials, large raw datasets,
generated model binaries, or temporary files.

Prefer small, testable functions.

Avoid unnecessary abstractions.

## Task Workflow

For substantial work:

1. Read the relevant sources of truth.
2. Inspect the existing implementation.
3. Create or update a coherent execution plan under `plans/active/`.
4. Implement the scoped work.
5. Validate and test it.
6. Self-review the result and `git diff`.
7. Update `docs/PROGRESS.md`.
8. Update `docs/DECISIONS.md` only when a durable decision changed.
9. Move the completed execution plan to `plans/completed/`.

## Definition of Done

Before considering a coding task complete:

1. Run relevant tests.
2. Run lint/static checks if configured.
3. Confirm no obvious time-series leakage was introduced.
4. Check `git diff`.
5. Update tests where appropriate.
6. Update `docs/PROGRESS.md`.
7. Update `docs/DECISIONS.md` if an architectural decision changed.
8. Update README only if setup, usage, architecture, or user-facing
   behavior changed.

Never claim a test passed unless it was actually run.

## Git Rules

`main` is the stable integration branch. Do not work directly on it for
feature development.

Use focused branches such as:

- `feat/...`
- `fix/...`
- `docs/...`
- `refactor/...`
- `test/...`

Prefer small, reviewable commits.

Do not force-push or rewrite shared history.

Do not merge into `main` unless explicitly requested.

## Documentation Rule

Code, documentation, implementation, and current project state must agree.

If implementation differs from the current plan, either:

- fix the implementation; or
- document and justify the changed decision in `docs/DECISIONS.md`.

Never silently change project assumptions.
