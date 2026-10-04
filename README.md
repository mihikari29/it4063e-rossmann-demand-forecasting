# Retail Demand Forecasting for Inventory Optimization (FMCG)

Store-level Business Analytics and inventory decision support using the Rossmann Store Sales dataset.

This repository is the group project for **IT4063E – Introduction to Business Analytics**. It addresses the business problem of forecasting near-term store demand and translating forecasts into inventory-value replenishment guidance.

## Project Objective

The planned system will forecast Rossmann `Sales` at the **Store × Date** level for a primary horizon of **14 days**. Because `Sales` represents monetary turnover rather than physical product quantities, inventory outputs will be expressed as inventory-value decision support. Any equivalent-unit output and supply-chain fields will be explicitly simulated.

The planned analytics flow is:

**Descriptive → Predictive → Prescriptive**

The intended modelling ladder is:

1. Seasonal Naive baseline
2. Exponential Smoothing / Holt-Winters
3. Global LightGBM candidate

Models will be compared through rolling-origin validation. LightGBM is the primary machine-learning candidate, not a predetermined winner.

## Current Status

The project is in **Phase 0 — Repository Foundation**. This repository currently contains project governance and planning documents only. Data acquisition, EDA, forecasting models, inventory simulation, APIs, dashboards, deployment, and monitoring remain future work.

## Documentation

- [Authoritative proposal](docs/proposal.md)
- [Project roadmap](docs/PROJECT_PLAN.md)
- [Current progress](docs/PROGRESS.md)
- [Development workflow](docs/WORKFLOW.md)
- [Decision log](docs/DECISIONS.md)
- [Initial data dictionary](docs/DATA_DICTIONARY.md)

## Team

- Pham Le Minh Quang — 20235554
- Tran Quoc Tuan — 20235569
- Vo Ta Quang Nhat — 20225454
- Nguyen Trung Hieu — 202416689
- Nguyen Gia Minh — 202400111

## Repository Structure

```text
.
├── AGENTS.md
├── README.md
├── .gitignore
├── docs/
│   ├── proposal.md
│   ├── PROJECT_PLAN.md
│   ├── PROGRESS.md
│   ├── WORKFLOW.md
│   ├── DECISIONS.md
│   └── DATA_DICTIONARY.md
└── plans/
    └── completed/
        └── phase-0-repository-foundation.md
```

Dependency management and source, notebook, data, model, application, and test directories will be introduced only when their project phases begin.
