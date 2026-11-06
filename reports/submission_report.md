# Rossmann Sales Forecasting and Simulated Inventory Decision Support

IT4063E - Introduction to Business Analytics | Semester 20261 | Class 175884

Instructor: Dr. Bui Quoc Trung

Team: Pham Le Minh Quang (20235554); Tran Quoc Tuan (20235569); Vo Ta Quang Nhat (20225454);
Nguyen Trung Hieu (202416689); Nguyen Gia Minh (202400111)

Submission draft - November 6, 2026. Development evidence is retained from reviewed repository
records. Final holdout, public release and human academic acceptance remain pending.

## Abstract

This project forecasts monetary Sales for each Rossmann Store and Date over a primary horizon
of 14 calendar days, then evaluates inventory-value policies under explicit simulation assumptions.
The development comparison uses three chronological origins and 38,553 common observed open-store
labels. The reviewed pooled mean absolute errors are 1,681.2703 for Seasonal Naive, 1,281.7446 for
additive Holt-Winters and 871.0612 for global recursive LightGBM. The accepted selection retains
the fixed LightGBM recipe; these are development scores, not final holdout or production results.
Daily and cumulative empirical uncertainty are distinct outputs. The forecast-driven inventory
policy has higher simulated holding-plus-shortfall cost than the baseline in the accepted base
and conditional historical examples. This adverse finding limits the business recommendation.
Read-only local API/dashboard services expose saved artifacts, while a separate controlled
synthetic profile demonstrates interfaces. Corrected monitoring pairs independently issued
predictions with subsequently available labels and reports descriptive calendar-window metrics.
The July 4-31 final evaluation and public two-service deployment remain gated. [1-4]

## 1. Introduction and business problem

The decision question is how much monetary store turnover to expect over the next 14 days and
how forecast-based inventory-value policies compare under declared operating assumptions. The
dataset contains neither SKU quantities nor actual inventory, procurement, stockouts or unit
prices. Turnover therefore cannot identify physical demand or unmet demand. The analytical unit
is Store x Date; the target is Sales. The project combines descriptive analysis, chronological
prediction and conditional prescriptive simulation without claiming real inventory optimization.

The eight course modules cover business understanding/data generation, EDA, cleaning, features,
models, deployment, monitoring and reporting. Their evidence is uneven: the development/local
foundation is complete, while real Store-level scenario analysis, supplementary STL findings,
the protected final evaluation and external delivery are incomplete. This report preserves those
boundaries instead of treating a working fixture or a branch integration as course completion.
The proposal, accepted decisions and current evidence remain authoritative. [1-3]

## 2. Dataset and synthetic supply-chain assumptions

The validated official snapshot has 1,017,209 training records, 41,088 separate competition-test
covariate records and 1,115 Store metadata rows. Historical training dates extend from January 1,
2013 through July 31, 2015. The competition-test data contains no Sales or Customers. The public
dictionary documents source domains, missingness, feature definitions and simulated values. [4-6]

Sales is monetary turnover in source units; this report does not invent a currency conversion.
Store metadata includes StoreType, Assortment, CompetitionDistance and Promo2 schedules. Holiday
and promotion inputs are future-known only under explicit calendar/planning assumptions.
Source Open determines retrospective eligibility and conditional operational routing, never the
raw predictor set. Unknown future Open stays unknown; inferred Open_resolved remains audit-only.

Synthetic operating inputs include lead time, target probability, initial inventory value,
procurement-cost ratio, annual holding rate and goodwill penalty. Their values are assumptions,
not measured Rossmann operations. For example, cost ratio c lies in [0.55,0.85), holding rate a
in [0.10,0.30), and goodwill penalty g in [0.10,0.75). Daily holding rate is c*a/365 and the
shortfall penalty is (1-c)+g. These define a cost proxy, not real margin, profit or savings. [4,9]

## 3. Exploratory data analysis

Historical EDA disclosed a shared July-December 2014 gap for 180 Stores, representing 33,120
absent Store-days. Sparse dates are not observed zero turnover. Store 988 also lacks the first
dataset date. Metadata missingness includes three missing competition distances and 354 Stores
with jointly missing competition opening month/year. All 544 nonparticipants in Promo2 lack the
associated schedule fields, consistent with structural nonparticipation. [5]

The EDA retained 54 observed Open=1/Sales=0 rows and valid large observations rather than applying
unsupported anomaly corrections. Descriptive promotion and Store-type differences are
associations; promotional assignment and Store composition prevent a causal interpretation.
Sunday/open-label support is sparse and differs from the usual weekday population. Counts and
denominators therefore accompany comparative interpretation. [5]

Earlier full-source validation/EDA included dates later protected for final evaluation. This
historical exposure is explicitly disclosed; the report makes no claim that the holdout was
never seen descriptively. Those full-period summaries cannot define modeling cohorts, monitoring
references or learned preprocessing. New model/development inputs stop at July 3, 2015. [2,5]

Robust weekly STL is implemented for uninterrupted finite daily segments with at least 56 days,
retaining at most 112 days and selecting the first three eligible Store IDs. Missing dates and
nonfinite observations split segments. The real-input preparation and execution gates are
unmet, so no new Rossmann STL components or findings are presented. [2,10]

## 4. Data cleaning and validation

Preparation preserves original source values, keys and sparse dates. Historical and test tables
join Store metadata many-to-one; unique Store/Date keys and domains are validated. No target
imputation, calendar-row creation, arbitrary category interpretation or spike deletion is
introduced. Missing competition metadata remains missing. Structural promotion nulls remain
distinguishable from invalid or incomplete participant schedules. [4-6]

The 11 missing test Open values for Store 622 remain null in canonical data. A separately
documented historical-context candidate is uncertain and audit-only; it does not overwrite source
Open, determine evaluation eligibility or force a forecast to zero. This distinction prevents
an inferred operational assumption from becoming an observed outcome. [5,6]

Restricted fixture verifiers test schemas, identities and authorized representations, but hashes
alone cannot authenticate custody or grant data access. The existing Parquet fixture contract
also lacks a hard peak-memory bound before materialization. It remains approved only for trusted
synthetic fixtures. A real mixed-source operation requires its own authorized preparation,
independent verification, bindings and purpose-specific execution decision. [2,10]

## 5. Feature engineering

The frozen feature contract contains 29 ordered predictors. It combines Store identity; calendar
features; holiday/promotion inputs; static Store/competition metadata; exact-date Sales lags at
1, 7, 14 and 28 days; and complete 7/14/28-day rolling means and sample standard deviations.
Store is categorical identity, not a continuous magnitude. Customers and Customers-derived
variables are excluded. Date is a key; source Open is eligibility/routing information. [6]

An absent exact lag date produces null, not the preceding observed row. Rolling statistics
require all calendar dates and exclude the target. During recursive inference, actual Sales
ends at the forecast origin; later features use only earlier predictions from the same run.
Precomputed historical feature rows cannot be reused as recursive validation inputs because they
can contain actual values unavailable at issuance. Future calendar/planned fields require an
explicit availability assumption even when a later snapshot contains them. [6,7]

## 6. Forecasting methodology

Seasonal Naive supplies a reviewed weekly baseline. Additive Holt-Winters supplies the statistical
candidate, with retained fit/failure/clipping diagnostics. Global LightGBM pools Stores and
recursively predicts the H14 path using the unchanged ordered feature schema. Raw paths are
generated before operational routing; actual target outcomes never alter the raw prediction.
The reviewed failure and coverage policies remain unchanged. [2,7]

The selected recipe is CPU GBDT regression L1, learning rate 0.05, 15 leaves, maximum depth 4,
minimum data per leaf 200, and 180 boosting rounds. Selection freezes the recipe; it does not
establish a fitted future July model. The prior fixed tuning and selection artifacts are retained
without regeneration. An offline course demonstration is the accepted operating context; no
production latency, throughput or memory guarantee is claimed. [2,3]

## 7. Chronological validation and model comparison

Development origins are May 22, June 5 and June 19, 2015. Their nonoverlapping H14 target windows
end by July 3. Primary errors use observed source Open=1 and available raw forecasts. Candidate
availability and a fixed common population are reported separately. No shuffled split or future
actual Sales/Customers input is used in the accepted recursive protocol. [2,7]

| Candidate | Pooled MAE | Pooled RMSE | MAPE (%) | WAPE (ratio) |
|---|---:|---:|---:|---:|
| Seasonal Naive | 1681.2703 | 2416.9677 | 26.2671 | 0.232748 |
| Additive Holt-Winters | 1281.7446 | 1708.3073 | 18.3669 | 0.177439 |
| Global LightGBM | 871.0612 | 1350.9138 | 11.3531 | 0.120586 |

The table reproduces the reviewed development summary on 38,553 common eligible observations,
with 100% candidate availability. MAE is primary. RMSE emphasizes large errors; MAPE requires
positive actuals and WAPE divides total absolute error by actual turnover total. These reported
MAPE rows are all positive, with no zero-actual exclusions. Window scores are pooled from rows,
not averaged. [3]

LightGBM improves pooled MAE by 48.1903% over Seasonal Naive and wins all three windows under the
accepted selection heuristics. The rule is a transparent project heuristic chosen after initial
candidate results, not a preregistered significance test. Holt-Winters fails its h8-14 regression
cap. LightGBM is weaker than Seasonal Naive at h2, h9 and h10; sparse h2/h9 support and
weekday/horizon confounding limit interpretation. No unapproved horizon-specific replacement is
introduced. Real Store-level scenario comparison remains pending its input/execution gates. [3]

The protected final period is July 4-31. The accepted protocol issues full H14 blocks at July 3
and July 17 before matching labels are released, with only already released history available
for the scheduled second fit. Implementation, resources, rehearsal, source custody and each
chronological release remain gated. This report contains no final-period score. [2,8]

## 8. Forecast uncertainty

Daily uncertainty consists of marginal empirical horizon-specific intervals. Cumulative
uncertainty uses complete prefix residual paths for upper bounds; daily interval endpoints
cannot be summed to obtain those bounds. Fit A assesses the June 5 origin using earlier
development information; Fit B assesses the June 19 origin. The accepted Fit B artifact remains
frozen. These methods do not imply conformal, simultaneous, per-Store or service guarantees. [2,3]

Fit A provides 12,258 daily intervals among 13,438 eligible open labels (91.22% availability),
with 10,344 hits among usable intervals (84.39% empirical coverage). Fit B provides 13,437 among
13,437 (100%), with 12,263 hits (91.26%). Fit A sparse h2/h3/h9 strata remain unavailable rather
than borrowing unsupported intervals. Availability and assessed-coverage denominators differ.
Conditional operational coverage is higher when deterministic closed [0,0] routes are pooled;
that increase is not improved raw-model accuracy. [3]

Illustrative inventory buffers derived from cumulative upper bounds are not nominal service
guarantees. Synthetic-stress transport is uncalibrated. Applying frozen June Fit B to July
fresh fits is explicitly unvalidated transport, with no July recalibration or empirical July
coverage established. These limitations affect any stock-policy recommendation. [2,8,9]

## 9. Inventory policy and business trade-offs

The accepted simulator compares a historical-mean baseline with a forecast-driven standing
order-up-to target. Inventory position includes on-hand and pipeline values. The forecast target
uses the greater of the origin-prefix forecast sum and cumulative upper value; replenishment is
the positive gap to inventory position. Lead time counts full intervening calendar demand days,
and an end-of-day order arrives at beginning-of-day t+L+1. Both policies follow the same event
order and finite H14 accounting. These are monetary-value proxies, not actual SKU purchases. [9]

The reviewed development simulation has 383,560 targets/summaries, 5,753,400 ledger rows, 172 cases
and 1,720 comparisons. In the synthetic base case, holding-plus-shortfall cost is 90,786,517.967853
cost-proxy units for the baseline and 113,929,065.505821 for the forecast policy, a deterioration
of 23,142,547.537968. Conditional historical replay also deteriorates by 4,276,098.731339.
Sensitivity cost differences remain positive in the recorded panel. These results support
neither real savings nor a claim that lower forecast MAE guarantees lower simulated cost. [3]

Value fill rate pools fulfilled/demand totals. Stockout rate uses positive-demand days.
Completed positive-demand receipt-cycle service has a policy-dependent denominator; initial and
terminal intervals are censored. Terminal stock and outstanding procurement commitment are
reported separately from the primary objective. All final intervals remain right-censored,
including receipt-on-T cases. A short cold-start episode with stale origin targets cannot
establish long-run optimality. [3,9]

The practical recommendation is to retain the adverse comparison and investigate approved
operating assumptions before recommending a policy. No new policy tuning is performed here.
The final protocol uses two independent origin-frozen episodes, not continuous rolling 28-day
inventory. Its remaining gates prevent treating development evidence as final business validation.

## 10. System architecture and deployment

Reusable Python analytics live in src/, scripts expose commands and notebooks present results.
Shared read-only services support FastAPI and a five-screen Streamlit dashboard. The explicit
controlled-synthetic profile uses a verified immutable release/pin and cannot fall back to
canonical Rossmann artifacts. API responses carry synthetic provenance; health means process
liveness and catalog readiness is a separate fact. Missing values retain unavailable reasons.
The dashboard reads Python services directly. [11]

The integration correction removes a static JavaScript mock tester, fixed inventory outcomes,
invented p-values and a hardcoded Healthy badge. The historical Hugging Face Space is static;
its presence does not establish a FastAPI deployment. The replacement builder writes an offline
notice and has no upload operation. Two real local loopback services and a bounded HTTP probe
form the deployment candidate. Public endpoints require independent review, exact content/rights,
security/resource/rollback and explicit owner release approval. No public API URL is asserted. [11]

## 11. Model monitoring

The monitoring chain is immutable forecast issuance, subsequent label availability, validated
pairing, descriptive performance/characteristic summaries and human review. The adapter accepts
authorized in-memory development records only. It validates Store/origin/target/horizon keys,
model/evidence identity, issue-before-target, origin-safe training/features and label availability.
Duplicate/mismatched keys and unsupported fields fail explicitly. It cannot authenticate real
custody or grant source access; upstream authorization remains necessary. [12]

Daily and trailing 7/14-calendar-day views retain Store/origin/horizon strata, startup flags,
requested keys, observed/missing labels and metric denominators. Missing dates do not become
zero or shorten the calendar window. Feature quartiles/frequencies compare declared origin-known
calendar/planned features in disjoint earlier reference and current windows. Small samples,
missingness and constant references are explicit. There is no KS significance claim. [12]

The controlled fixture authors predictions from Store/calendar independently of labels and uses
a synthetic model identity. JSON, HTML, chart and notebook share one calculation API. Evidence
states describe availability, not system health. No automatic retraining, numeric warning or
unimplemented persistence rule is retained. The broader operational trigger proposal requires
separate approval/rehearsal and cannot adapt the frozen final replay. Genuine post-deployment
performance monitoring cannot yet be demonstrated without new real observations. [12]

## 12. Limitations, ethics and academic ownership

The study is limited by monetary targets, missing operational observations, dependent Stores/date
shocks, sparse Sunday labels, only three late-season development origins, historical descriptive
holdout exposure, empirical uncertainty support and unvalidated transport. Cold starts,
artificial costs, finite-window censoring and stale inventory targets further restrict business
inference. Legacy manifests have recorded provenance limitations; none is rewritten to imply a
cleaner history. No final-test result, production readiness, physical-demand accuracy, optimal
policy, service guarantee or real savings is claimed. [2,3,5]

AI assistance proposed code corrections, tests, monitoring/report source and this academic draft.
The team must inspect, understand, test and accept those contributions, verify citations and
conclusions, rehearse explanations and follow the instructor's AI policy. The named authorship
list identifies project membership, not a claim that each member manually wrote all generated
code or this prose. Independent AI review is separate from human GitHub approval and academic
ownership. Human reviewers must resolve pending analytical/release decisions before submission.

## 13. Conclusions and recommendations

The retained development evidence favors the frozen global recursive LightGBM recipe for the
accepted raw Sales metric contract. It also shows weaker individual horizons and adverse
simulated inventory costs. The defensible conclusion is that improved monetary forecast error
alone does not establish an effective real procurement policy. Uncertainty and synthetic
operating assumptions must remain visible in the decision-support demonstration.

The local candidate improves engineering truthfulness and reproducibility without changing the
scientific recipe. Course submission still requires authorized real scenario/final evidence,
selected monitoring integration, approved public API/dashboard release and team acceptance of
report/slides. Pending work is an explicit limitation of this draft, not a positive result.

## References and reproducibility appendix

[1] Repository docs/PROPOSAL.md: business scope, eight modules and assignment traceability.

[2] Repository docs/DECISIONS.md: accepted methods, information boundaries and release gates.

[3] Repository docs/PROGRESS.md: canonical reviewed development findings and limitations. Numerical
tables in this report are transcribed from that record; no canonical artifact or source was read.

[4] Repository docs/DATA_DICTIONARY.md and docs/DATA_VALIDATION.md: real/synthetic semantics.

[5] Repository docs/EDA_FINDINGS.md: historical descriptive evidence and exposure disclosure.

[6] Repository docs/FEATURE_CONTRACT.md: exact 29-predictor schema and origin-safe recursion.

[7] Repository src/rossmann_forecasting/forecasting/validation.py and plans/completed/: retained
baseline, Holt-Winters, LightGBM and selection specifications.

[8] Repository plans/active/phase-13-sequential-final-evaluation.md: frozen two-block protocol.

[9] Repository plans/completed/phase-9-synthetic-inventory.md and
plans/completed/phase-10-inventory-simulation.md: scenario and simulator contracts.

[10] Repository docs/CC-02D_CUSTODIAN_RUNBOOK.md and
plans/active/wp1-scenario-forecast-evaluation.md: separate safe-input and execution gates.

[11] Repository docs/LOCAL_DEMO_DEPLOYMENT.md and plans/active/public-course-demo.md:
local services, read-only external inspection and pending release checklist.

[12] Repository docs/MONITORING.md and notebooks/03_model_monitoring.ipynb: adapter, populations,
synthetic reproduction and limitations.

Reproduce fixture software checks with the locked environment in docs/WORKFLOW.md. Run full
fixtures in a tracked-files-only checkout to avoid optional canonical-artifact discovery.
Python 3.12 and 3.14 are supported; Python 3.14 is the reference. Never execute source-wide
preparation or model commands merely to reproduce this report. Real-source permission is not
implied by an existing path, manifest, binding or notebook. Generated outputs belong under
reports/generated/; their manifests record code, configuration, input/output and environment
identity. See docs/SUBMISSION_READINESS.md for current tests, limitations and delivery status.
