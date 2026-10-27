# Seasonal Naive Evaluation

The implemented weekly baseline is complete. This reference specifies its accepted recursive, routing and metric behavior.

[Verified results](../../docs/PROGRESS.md) · [Decisions](../../docs/DECISIONS.md)

## 5. Approved development validation windows

**APPROVED.** The final holdout boundary remains fixed at 2015-07-04.

| Window | Forecast origin | Target dates | Calendar days |
|---|---|---|---:|
| `validation_1` | 2015-05-22 | 2015-05-23 through 2015-06-05 | 14 |
| `validation_2` | 2015-06-05 | 2015-06-06 through 2015-06-19 | 14 |
| `validation_3` | 2015-06-19 | 2015-06-20 through 2015-07-03 | 14 |

The target windows are chronologically ordered and non-overlapping. Each begins the calendar day
after its origin; the next origin is the prior window's final target date, so each later origin may
use the expanded actual history available by that date. The final target window ends immediately
before the protected 2015-07-04–2015-07-31 holdout. The three target ranges were verified
mechanically against the historical calendar using only its `Date` column: every origin is present,
and each requested range contains exactly the 14 expected consecutive dates. No Sales values,
forecast outputs, or metrics were read or calculated for this check.

### Approved distinction: internal forecast path vs. observed target rows

Emit and evaluate only Store × Date target keys actually present in the source validation window.
Do not synthesize Store × Date label rows, fake `Open`, or treat absent target rows as zero Sales.
However, for every Store with at least one observed target row in a window, internally construct
the complete calendar path `h = 1..14`. An intermediate date without an observed target key still
gets an internal forecast state, with no target label; that state may feed a later recursive
forecast. For example, if h=1 has no observed target row but h=8 does, generate internal h=1 from
origin-safe history and use that forecast for h=8. Only the observed h=8 key is emitted/scored.
Internal states are ephemeral forecast state, not synthetic labels or evaluation records.

Why these windows were selected: they provide three non-overlapping two-week tests, move forward in
time, allow the actual history to expand at each origin, and finish directly before the untouched
holdout. Do not choose or revise windows based on their eventual forecast performance.

## 6. Approved 14-day Seasonal Naive semantics

**APPROVED.** For store `s`, forecast origin `o`, and target calendar date
`d`, use the exact same-Store date `d - 7 calendar days`:

```text
if d - 7 days <= o:
    raw_forecast(s, d) = actual Sales(s, d - 7 days)
else:
    raw_forecast(s, d) = previously generated raw_forecast(s, d - 7 days)
```

Consequently, h=1 uses actual Sales at `o-6`, h=2 at `o-5`, through h=7 at `o`; horizons 8–14 use
the previously generated forecasts at h=1–7 respectively. The second week is recursive: actual
Sales revealed inside the 14-day target window never enters later predictions. In particular,
horizon 8 must use the horizon 1 forecast, not actual Sales at horizon 1 (teacher forcing is
rejected).

Lookup is exact by Store and calendar date. If the required `d - 7` source date is absent, the raw
forecast is null. Do not search backward for a previous observed row, interpolate, impute, or
replace the missing value with zero. Any later recursive forecast depending on that unavailable
weekly value is also null. An observed `Sales == 0` on the exact weekly source date is valid and
yields a raw forecast of zero. The public API rejects null, non-finite, or negative Sales values in
the supplied actual-history frame; a missing exact Store × Date key is represented as unavailable.

Generate the raw 14-day sequence independently for each store and origin. State transitions between
validation windows are walk-forward: at a later origin, actual observations through that new origin
are available. Within a single origin's 14-day run, only the origin-censored actual history and
earlier predictions from that run are available.

## 7. Approved raw and operational forecast separation

**APPROVED.** Keep model quality separate from business routing:

- `raw_baseline_forecast` is the pure Seasonal Naive result from Section 6. It is generated without
  consulting target-date `Open` and is retained unchanged for evaluation.
- `operational_forecast` applies the known-closed rule after the raw forecast is generated:
  - source `Open == 0` → `0`, even if the raw forecast is unavailable;
  - source `Open == 1` → the raw forecast, including null if raw history is unavailable;
  - missing/unknown source `Open` → null, never silently treated as closed.
- For historical validation, source target-date `Open` is an evaluation/routing attribute attached
  after raw predictions have been generated; it is never a predictor or input to the raw rule.
  `Open_resolved` remains uncertain audit data and cannot establish known-open/known-closed status.
- In a future operational application, zero routing is permitted only when target-date closure is
  known from an approved source; this design does not authorize inferring closure from unknown
  `Open`.

Define `forecast_available` as whether `raw_baseline_forecast` is non-null. If useful for audit,
also emit `operational_forecast_available`; do not overload raw forecast availability with the
closed-store zero rule. Primary model metrics use raw forecasts on open rows; on those rows the
operational forecast equals the raw forecast whenever available.

## 8. Approved evaluation eligibility and coverage

**APPROVED.** A primary-evaluation row must satisfy all of the following:

1. Its target date lies in one of the approved development windows.
2. The observed source target-date `Open` equals 1.
3. Actual target `Sales` is present.
4. The raw Seasonal Naive forecast is available.

Preserve every observed target row in forecast outputs, including closed, unknown-Open, and
unavailable-forecast rows. Do not delete closed rows to make metrics easier. Closed and unknown
rows are excluded from primary forecasting metrics; known-closed rows still retain their
operational zero. Uncertain `Open_resolved` candidates are not evaluation truth.

Report raw-forecast availability coverage so missing predictions cannot disappear silently. At a
minimum, report available raw forecasts divided by observed historical target rows in each
window, plus available raw forecasts divided by observed `Open == 1` rows with actual Sales. State
both numerator and denominator. Primary metric eligibility is then the intersection of observed
open labels and available raw forecasts. Coverage is descriptive; it must not be used to select a
window or change missing-history semantics based on performance.

No final-holdout forecast, evaluation, or result is allowed in Phase 4.

## 9. Approved metric contract

**APPROVED.** Use the primary eligible population from Section 8. For
each validation window, for pooled development rows across the three windows, and by forecast
horizon `h = 1..14`, calculate:

- **MAE (primary):** `mean(abs(actual_sales - raw_baseline_forecast))` over eligible rows.
- **RMSE:** `sqrt(mean((actual_sales - raw_baseline_forecast) ** 2))` over the same eligible rows.
- **MAPE (caution):** calculate only on primary-eligible rows with `actual_sales > 0`, as
  `mean(abs(actual - forecast) / actual) * 100`. Do not add epsilon or alter zero Sales. Report the
  count of primary-eligible zero-actual rows excluded from MAPE, the MAPE denominator row count,
  and MAPE coverage (`positive-actual MAPE rows / primary-eligible rows`). If there are no positive
  actual rows, return null with an explicit unavailable reason.
- **WAPE:** `sum(abs(actual_sales - raw_baseline_forecast)) / sum(actual_sales)` over the primary
  eligible rows. If the actual-Sales denominator is zero, return null with a clear reason; never
  divide by zero or add an epsilon.

For the pooled result, concatenate the eligible observations from the approved development windows
and compute each metric over that pooled row set; do not substitute an unweighted average of
window-level metrics. For horizon results, apply the same definitions to eligible rows with that
horizon. Record row counts and availability coverage alongside metrics. MAE remains the primary
comparison metric; MAPE and WAPE are not replacements for it.

## 10. Approved forecast record and field roles

**APPROVED.** Use one auditable record per observed target Store × Date and forecast origin. The
composite key is `(Store, forecast_origin, Date)`; `horizon` is also stored and checked against the
date difference. The approved validation windows do not overlap.

| Field | Role and timing |
|---|---|
| `Store` | Key; unchanged source store identity. |
| `forecast_origin` | Key/audit field; date at which the forecast information set is cut off. |
| `Date` | Key; forecast target date. |
| `horizon` | Forecast audit field; integer calendar lead `1..14`, not an independent key. |
| `raw_baseline_forecast` | Forecast output; pure recursive weekly Seasonal Naive. |
| `operational_forecast` | Forecast output after known-closed routing; unknown Open stays null. |
| `actual_sales` | Label joined only after raw forecasts are generated; never a forecast input for dates after origin. |
| `source_open` | Evaluation/routing audit field joined after raw generation; not a predictor. |
| `forecast_available` | Audit flag for non-null raw forecast. |
| `operational_forecast_available` | Optional audit flag, distinct from raw availability and useful when Open is unknown. |
| `primary_evaluation_eligible` | Evaluation mask derived from window membership, source Open, actual Sales availability, and raw forecast availability. |
| `validation_window` | Evaluation/audit label, e.g. `validation_1`, `validation_2`, or `validation_3`. |

No `Customers`, Customers-derived field, future-actual predictor, model feature, or holdout result
belongs in this record. Keep forecast generation and post-forecast label/routing joins as separate
steps so evaluation labels cannot influence raw predictions.

## 11. Final-holdout firewall

The final holdout remains 2015-07-04 through 2015-07-31. During Phase 4 development, its Sales,
forecast errors, metric distributions, and performance must not be inspected or used to:

- change Seasonal Naive or recursive semantics;
- choose or revise development windows based on performance;
- choose missing-history behavior;
- choose metric or eligibility rules;
- decide Open routing;
- compare variants, inspect performance, or report forecast metrics.

Prefer no holdout contact in Phase 4. If a later implementation requires a check, it must be
strictly mechanical (date boundary, key uniqueness, schema compatibility, or row integrity) and
must not summarize targets, forecasts, or their distributions. No holdout forecast or evaluation
command is in this phase's scope. The three approved validation windows end on 2015-07-03.
