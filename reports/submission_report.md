# Rossmann Sales Forecasting and Simulated Inventory Decision Support

IT4063E - Introduction to Business Analytics | Semester 20261 | Class 175884

Instructor: Dr. Bui Quoc Trung

Team: Pham Le Minh Quang (20235554); Tran Quoc Tuan (20235569); Vo Ta Quang Nhat (20225454);
Nguyen Trung Hieu (202416689); Nguyen Gia Minh (202400111)

Submission draft - November 8, 2026. Development results are retained from reviewed repository
records; WP-03/WP-04 supply synthetic software evidence. This development-only draft is for
team review, not final acceptance. Public release and final holdout evaluation remain pending.

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
WP-04 ran the controlled synthetic FastAPI/Streamlit candidate in an isolated Linux environment,
including HTTP, live WebSocket, restart and failure checks. Its saved paths are authored examples,
not predictions from an executed LightGBM model. WP-03 verifies forecast-label pairing and
descriptive calendar-window monitoring on a separate synthetic fixture. Numerical triggers remain
PROPOSED. No Rossmann STL findings, final-test score or accepted public deployment is presented. [1-4,12-14]

## 1. Business understanding and data generation (Module 1)

The decision question is how much monetary store turnover to expect over the next 14 days and
how forecast-based inventory-value policies compare under declared operating assumptions. The
dataset contains neither SKU quantities nor actual inventory, procurement, stockouts or unit
prices. Turnover therefore cannot identify physical demand or unmet demand. The analytical unit
is Store x Date; the target is Sales. The project combines descriptive analysis, chronological
prediction and conditional prescriptive simulation without claiming real inventory optimization.

The eight modules distinguish reviewed development results from synthetic demonstrations.
Rossmann STL, real Store-level scenarios, frozen final evaluation and public acceptance remain
pending. A development-only submission needs instructor confirmation; all existing safeguards
remain effective. [1-3,15]

**Dataset and synthetic supply-chain assumptions**

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

## 2. Exploratory data analysis (Module 2)

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

Historical serial diagnostics use uninterrupted observed daily segments rather than filling gaps.
The reviewed representative-store ACF diagnostics report lag-7 correlations of approximately
0.27-0.75, consistent with heterogeneous weekly serial structure. This descriptive association is
neither a new decomposition nor a forecasting result. [5]

Earlier full-source validation/EDA included dates later protected for final evaluation. This
historical exposure is explicitly disclosed; the report makes no claim that the holdout was
never seen descriptively. Those full-period summaries cannot define modeling cohorts, monitoring
references or learned preprocessing. New model/development inputs stop at July 3, 2015. [2,5]

Robust weekly STL is implemented for uninterrupted finite daily segments with at least 56 days,
retaining at most 112 days and selecting the first three eligible Store IDs. Missing dates and
nonfinite observations split segments. The real-input preparation and execution gates are
unmet, so no new Rossmann STL components or findings are presented. [2,10]

**STL evidence slot - BLOCKED (WP-02):** add the approved Store roster, input provenance,
decomposition components/PNGs and reviewed trend/seasonal/residual interpretation only after
authorized execution. No decomposition figure or seasonal finding is substituted here.

## 3. Data cleaning and validation (Module 3)

Preparation preserves original source values, keys and sparse dates. Historical and test tables
join Store metadata many-to-one; unique Store/Date keys and domains are validated. No target
imputation, calendar-row creation, arbitrary category interpretation or spike deletion is
introduced. Missing competition metadata remains missing. Structural promotion nulls remain
distinguishable from invalid or incomplete participant schedules. [4-6]

The 11 missing test Open values for Store 622 remain null in canonical data. A separately
documented historical-context candidate is uncertain and audit-only; it does not overwrite source
Open, determine evaluation eligibility or force a forecast to zero. This distinction prevents
an inferred operational assumption from becoming an observed outcome. [5,6]

Table 1. Documented before/after preparation evidence. Counts are historical records, not new
measurements; metadata counts refer to distinct Stores, not joined training rows. Sources: [4,5].

| Item | Before | After | Disposition | Evidence |
|---|---:|---:|---|---|
| Historical rows | 1,017,209 | 1,017,209 | Preserved | [4,5] |
| Shared absent Store-days | 33,120 | 33,120 | No gap fill | [5] |
| Open=1 / Sales=0 rows | 54 | 54 | Retained | [4,5] |
| Test Open nulls | 11 | 11 | Audit separate | [4,5] |
| Promo2-detail null Stores / field | 544 | 544 | Structural | [4,5] |

Restricted fixture verifiers test schemas, identities and authorized representations, but hashes
alone cannot authenticate custody or grant data access. The existing Parquet fixture contract
also lacks a hard peak-memory bound before materialization. It remains approved only for trusted
synthetic fixtures. A real mixed-source operation requires its own authorized preparation,
independent verification, bindings and purpose-specific execution decision. [2,10]

## 4. Feature engineering (Module 4)

The frozen feature contract contains 29 ordered predictors. It combines Store identity; calendar
features; holiday/promotion inputs; static Store/competition metadata; exact-date Sales lags at
1, 7, 14 and 28 days; and complete 7/14/28-day rolling means and sample standard deviations.
Store is categorical identity, not a continuous magnitude. Customers and Customers-derived
variables are excluded. Date is a key; source Open is eligibility/routing information. [6]

The 29 predictors comprise one Store identity, eight calendar fields, two holiday fields,
three promotion fields (promo, promo2, is_promo2_active), five Store/competition descriptors,
four exact-date lags and six rolling statistics. Learned categorical mappings are fit on each
origin's training population; unknown categories follow the frozen adapter policy. [6,7]

An absent exact lag date produces null, not the preceding observed row. Rolling statistics
require all calendar dates and exclude the target. During recursive inference, actual Sales
ends at the forecast origin; later features use only earlier predictions from the same run.
Precomputed historical feature rows cannot be reused as recursive validation inputs because they
can contain actual values unavailable at issuance. Future calendar/planned fields require an
explicit availability assumption even when a later snapshot contains them. [6,7]

## 5. Model development and decision support (Module 5)

**Forecasting methodology**

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

**Chronological validation and model comparison**

Development origins are May 22, June 5 and June 19, 2015. Their nonoverlapping H14 target windows
end by July 3. Primary errors use observed source Open=1 and available raw forecasts. Candidate
availability and a fixed common population are reported separately. No shuffled split or future
actual Sales/Customers input is used in the accepted recursive protocol. [2,7]

Table 2. Reviewed chronological development comparison. MAE/RMSE use source monetary turnover
units; MAPE is percent and WAPE is a ratio. Source: reviewed results [3].

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

**Forecast uncertainty**

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

**Inventory policy and business trade-offs**

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

## 6. System architecture and deployment (Module 6)

Reusable Python analytics live in src/, scripts expose commands and notebooks present results.
Shared read-only services support FastAPI and a five-screen Streamlit dashboard. The explicit
controlled-synthetic profile uses a verified immutable release/pin and cannot fall back to
canonical Rossmann artifacts. API responses carry synthetic provenance; health means process
liveness and catalog readiness is a separate fact. Missing values retain unavailable reasons.
The dashboard reads Python services directly. [11]

WP-04 created a new source-allowlisted 47-file synthetic candidate and installed locked API/dashboard
dependencies into a fresh Linux Python 3.12.15 environment with uv 0.12.23; download caches were
reused. Actual loopback HTTP checks produced 19 expected 200, two expected 422 and seven expected
503 responses. Fifteen live Streamlit WebSocket renders covered the five saved-service screens,
separate monitoring, restart and failure states. Missing bundle and wrong pin fail closed;
malformed UI errors were redacted. Store/H14 and unavailable-value behavior also passed targeted
AppTests. The scoped fixture suite passed 362 tests, with one Windows-symlink skip and one existing
Starlette/httpx warning. These counts establish software behavior, not model accuracy. [14]

Each Linux service was capped at 512 MiB, zero swap and 0.1 CPU. API catalog readiness took
22.49 seconds; dashboard health took 8.82 seconds. Peak RSS was 136.08 and 233.23 MiB, respectively,
with no OOM events in the measured sequential one-session workload. Monitoring's initial render
took 31.50 seconds. Actual host latency, concurrency, quotas, browser visual acceptance and
independent security acceptance remain unverified. All owned processes were stopped. [14]

The release profile is controlled_synthetic_demo; forecast rows retain model_execution=none.
History, uncertainty and inventory views use authored fixture arithmetic. The monitoring fixture
is separate from this saved-service bundle. Genuine trained-model deployment would require approved
development outputs and a suitable public artifact/provider contract; changing a label is not
sufficient. Both services must receive the same exact release bytes and trusted manifest pin. [11,14]

**Public URL evidence slot - PENDING:** no approved API/dashboard URL pair exists. WP-04's read-only
check found the old HF Space still static, with HTML 200 but health/catalog 404. Its page is not
backend evidence. Human review, successful CI, exact-content/rights/provenance, security/resource
acceptance, hosting scope and explicit Owner release authorization remain required. The local
verdict is READY FOR LOCAL STAGING ONLY, not DEPLOYED. [14]

## 7. Model monitoring (Module 7)

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

The controlled fixture authors predictions from Store/calendar independently of labels. Reference
dates are June 6-19 and current dates June 20-July 3, 2015. Each contains 42 requested pairs across
three synthetic Stores, including 36 eligible Open=1 pairs and six closed labels. Baseline MAE is
250 source-equivalent turnover units, RMSE 252.3225, MAPE 3.7935% and WAPE 0.0380113. These are
fixture metrics, separate from Table 2. The final trailing seven-day window has 21 requested/18
eligible pairs; the fourteen-day window has 42/36. [12,13]

Missing labels/predictions yield PARTIAL_EVIDENCE; no labels yield UNAVAILABLE and null metrics.
Zero actuals are excluded from MAPE with explicit counts; all-zero eligible actuals make MAPE/WAPE
unavailable. DESCRIPTIVE_ONLY describes evidence availability, even when error is large; it is not
a Healthy assessment. Coverage is conditional on supplied keys: loss of an entire Store's forecast
and label records needs an independently verified expected roster to be detected. [12,13]

**Proposed trigger specification - NOT APPROVED OR IMPLEMENTED.** Reference versions must precede
assessment, with identical eligibility and comparable origin/horizon populations. Support S
requires at least ten observed target dates, 100 Stores and 1,000 eligible pairs in each complete
non-overlapping 14-calendar-day assessment window and its reference. Availability support is
assessed before filtering missing predictions. The three-Store fixture is insufficient for these
proposed pooled decisions. These policy parameters have not been calibrated or validated here. [1,12,13]

## Table 3. Proposed human-review rules

| Check | Metric | Proposed rule | Evidence | Human action |
|---|---|---|---|---|
| Performance | WAPE vs ref | >1.20 x ref | 14 days; S | Inspect cause |
| Availability | Raw coverage | <99% | Roster; S | Repair delivery |
| Feature characteristics | Category share | Shift >=10 pp | Comparable; S | Inspect inputs |
| Late labels | Due missing labels | Count >0 | Approved deadline | Check ingestion |
| Integrity / quality | Invalid keys/fields | Confirmed failure | One incident | Stop view |
| Retraining review | Repeated warning | Two valid windows | Consecutive | Human decision |

Source: proposal section 24.2 and WP-03 specification [1,12,13]. Each proposed check yields
TRIGGERED, NOT TRIGGERED or INSUFFICIENT EVIDENCE; unsupported evidence never becomes a pass.

Reference WAPE and actual-value denominators must be positive. Missing labels or incompatible
references prevent a performance decision. Label deadlines are not yet approved; without a roster
and maturity rule, late-label status is insufficient evidence. Integrity/access failures stop the
affected path immediately; repeated blocking quality failures on two daily checks require escalation.
Unavailable windows break a persistence sequence. Retraining and promotion require separate human
approval and chronological development comparison. The adapter implements neither this numerical
engine nor persistence; no automatic retraining or production monitoring is claimed. [1,12,13]

## 8. Conclusions and recommendations (Module 8)

**Limitations, ethics and academic ownership**

The study is limited by monetary targets, missing operational observations, dependent Stores/date
shocks, sparse Sunday labels, only three late-season development origins, historical descriptive
holdout exposure, empirical uncertainty support and unvalidated transport. Cold starts,
artificial costs, finite-window censoring and stale inventory targets further restrict business
inference. Legacy manifests have recorded provenance limitations; none is rewritten to imply a
cleaner history. No final-test result, production readiness, physical-demand accuracy, optimal
policy, service guarantee or real savings is claimed. [2,3,5]

AI assisted prior code corrections, tests, monitoring/report sources and this draft. Members must
verify contributions, citations and conclusions, rehearse explanations and follow course policy.
The inherited roster/course details need team confirmation and do not establish exclusive human
authorship. Independent AI review is separate from human GitHub approval and academic ownership.
No instructor permission for AI-authored application code has been verified. Members must disclose
actual assistance/contributions, obtain the instructor's ruling where needed and approve the final
academic claims. [15]

**Conclusions and business recommendations**

The retained development evidence favors the frozen global recursive LightGBM recipe for the
accepted raw Sales metric contract. It also shows weaker individual horizons and adverse
simulated inventory costs. The defensible conclusion is that improved monetary forecast error
alone does not establish an effective real procurement policy. Uncertainty and synthetic
operating assumptions must remain visible in the decision-support demonstration.

For Business Analytics, the result illustrates why predictive error, uncertainty and business-policy
performance need separate evidence. The current recommendation is to retain the reviewed forecast
recipe for its stated development comparison, investigate the adverse simulation assumptions before
operational adoption, and use the synthetic application only to demonstrate interfaces.

Before submission, the team must resolve the STL and public-delivery gaps or obtain an explicit
instructor-approved scope adjustment, confirm the acceptability of synthetic/development replay,
and accept the report, slides and AI disclosure. Real Store-level scenarios and frozen final
evaluation remain unperformed. This draft does not classify every internal roadmap gate as an
instructor requirement, approve deferral, or waive safeguards. Final evaluation must not be called
complete or independent merely because development results are available.

Future improvements may include authorized development-only STL findings, genuine saved-model
serving and a reviewed human trigger policy. Longer evaluation, uncertainty-transport assessment
and revised inventory assumptions could strengthen inference after separate approval; none is
presented as completed work. This is a submission draft for team review, not final acceptance.

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

[13] WP-03: reports/generated/monitoring/wp03-fixture-20261108-v1/monitoring_summary.json and
manifest.json; tests/test_monitoring.py; session-verified fixture cases and seven-cell notebook
execution. The saved summary contains the baseline only; stress cases were checked in memory.

[14] WP-04: outputs/validation/wp04-staging-20261108-v1/evidence_manifest.json,
linux/linux-report.json, targeted-tests.xml, github-readonly.json and hf-readonly.json.
These are local technical evidence, not public release or human approval.

[15] IT4063E course announcement: Retail_FMCG_Demand_Forecasting_Project_Announcement.pdf,
sections 3, 4 and 6. The course requires monitoring/retraining-trigger definitions and accessible
deployment; exact workflow/support parameters are internal proposals. Code authorship requires
team-member authorship under the instructor's policy.

Reproduce fixture software checks with the locked environment in docs/WORKFLOW.md. Run full
fixtures in a tracked-files-only checkout to avoid optional canonical-artifact discovery.
Python 3.12 and 3.14 are supported; Python 3.14 is the reference. Never execute source-wide
preparation or model commands merely to reproduce this report. Real-source permission is not
implied by an existing path, manifest, binding or notebook. Generated outputs belong under
reports/generated/; their manifests record code, configuration, input/output and environment
identity. See docs/SUBMISSION_READINESS.md for current tests, limitations and delivery status.
