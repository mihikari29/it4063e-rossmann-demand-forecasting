# Point-in-Time Features

**Complete.**

The implemented `phase-3-v1` contract is complete and fixed at 29 ordered predictors. The [Feature Contract](../../docs/FEATURE_CONTRACT.md) is the single definition of fields/dtypes, exact-date history, complete windows, eligibility, raw recursion and holdout firewall. The [dictionary](../../docs/DATA_DICTIONARY.md) separates real, engineered and synthetic fields. Historical features are one-step training rows, not safe recursive target rows; rebuild dynamic features from actuals through origin plus earlier predictions. Learned categories belong in the model adapter. Future Customers, Open as a predictor, imputation and target-selected cohorts remain prohibited.

[Current results and limitations](../../docs/PROGRESS.md)
