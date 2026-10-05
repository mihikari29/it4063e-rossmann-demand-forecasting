# Phase 1 — Data Acquisition & Validation

## 1. Objective

Establish a reproducible, inspectable, and validated Rossmann Store Sales data foundation before any exploratory analysis, feature engineering, or modelling begins. Phase 1 must document how authorized team members obtain the official files, preserve raw inputs unchanged, verify the actual schemas and Store × Date keys, and produce a concise data-quality record that later phases can trust.

## 2. Scope

### Included

- Acquire the official Rossmann Store Sales competition files through a documented process.
- Define a minimal local data layout and a Python environment strategy.
- Keep raw source files immutable and excluded from Git.
- Verify the expected source-file set and record file metadata or checksums.
- Inspect actual headers, parsed data types, row counts, and file sizes.
- Parse and validate dates without inventing or filling observations.
- Validate Store × Date uniqueness and store-key integrity.
- Profile missing values, categorical values, numerical ranges, and suspicious records.
- Validate the cardinality of joins between store-day files and store metadata without creating a prepared modelling dataset.
- Inspect relationships among `Open`, `Sales`, and `Customers` while preserving observed records.
- Produce reproducible validation outputs and update verified entries in `docs/DATA_DICTIONARY.md`.
- Add focused tests for reusable acquisition and validation logic.

### Excluded

- Exploratory data analysis and business interpretation.
- Data cleaning decisions beyond reporting verified validation failures.
- Feature engineering, lags, rolling statistics, or future-looking transformations.
- Forecasting, model training, tuning, or model selection.
- Synthetic supply-chain variables or inventory simulation.
- Notebooks, dashboards, APIs, deployment, or monitoring.
- Any SKU-level transformation or claim.

Phase 1 may inspect and validate values, but Phase 2 owns analytical preparation and EDA.

## 3. Expected Rossmann Source Files

The proposal identifies four expected files:

| File | Proposal-level expectation | Phase 1 verification |
|---|---|---|
| `train.csv` | Historical store-day observations including `Sales` | Confirm the complete header, row count, types after parsing, date coverage, and target/customer availability |
| `test.csv` | Future observations without `Sales` | Confirm the complete header and which operational/calendar fields are supplied |
| `store.csv` | Store-level attributes | Confirm one-row-per-store expectations, complete metadata header, and missingness patterns |
| `sample_submission.csv` | Competition submission structure | Confirm its identifier and prediction columns and relationship to `test.csv` |

These files do not currently exist in the repository. Their schemas must be verified from the authorized download and the official dataset description. Proposal-listed fields are provisional validation expectations rather than permission to fabricate a schema. Unexpected columns must be reported and reviewed instead of silently discarded.

## 4. Proposed Repository Structure

Introduce only the structure needed for reproducible acquisition and validation:

```text
.
├── pyproject.toml
├── data/
│   ├── README.md
│   └── raw/
│       └── rossmann/              # local, immutable, ignored dataset files
├── docs/
│   ├── DATA_ACQUISITION.md
│   ├── DATA_VALIDATION.md
│   ├── DATA_DICTIONARY.md         # updated only from observed evidence
│   └── PROGRESS.md
├── reports/
│   └── validation/                # generated local reports, ignored by Git
├── scripts/
│   ├── acquire_data.py            # thin command entry point
│   └── validate_data.py           # thin command entry point
├── src/
│   └── rossmann_forecasting/
│       ├── __init__.py
│       └── data/
│           ├── __init__.py
│           ├── acquisition.py
│           └── validation.py
└── tests/
    └── test_data_validation.py
```

Rationale:

- `data/README.md` records source, retrieval, layout, and immutability rules without tracking data.
- `data/raw/rossmann/` holds the official extracted files locally. It must remain ignored.
- `src/.../data/` holds reusable logic; scripts remain small command wrappers.
- `reports/validation/` holds replaceable machine-readable or detailed generated output and remains ignored.
- `docs/DATA_VALIDATION.md` holds a concise version-controlled summary without copying data rows.
- `tests/` uses small constructed fixtures designed solely to test validation behavior.

Do not create `data/interim/`, `data/processed/`, notebooks, model, API, or dashboard directories in Phase 1. Interim and processed datasets belong to Phase 2 when their transformations are defined.

## 5. Python Environment Strategy

### Options considered

- `requirements.txt` is familiar and easy to install, but by itself it does not provide project metadata, package layout, tool configuration, or a clean distinction between runtime and development dependencies.
- `pyproject.toml` can define project metadata, the supported Python version, runtime dependencies, optional development dependencies, and formatter/test configuration in one standard file. It also supports the planned `src/` package layout and later FastAPI and Streamlit dependencies.

### Recommendation

Use `pyproject.toml` as the single hand-maintained dependency and tooling source. Define a small Phase 1 runtime set for tabular loading and validation, plus a development extra for tests and linting. Add later-phase packages only when their phase begins. If exact environment locking is required, generate a lock or constraints file from this source rather than manually maintaining a second dependency list.

During implementation, the team must agree on and document one supported Python version after checking all required packages and team machines. Each contributor should use a repository-local virtual environment. No global package installation should be required.

Do not recreate an empty `requirements.txt`. If a later deployment platform requires that format, generate it from the chosen project configuration and document the generation command.

## 6. Data Acquisition Strategy

Use the official Kaggle Rossmann Store Sales competition as the authoritative download source.

Preferred workflow:

1. Each authorized contributor accepts any required competition rules and configures Kaggle authentication outside the repository.
2. A thin acquisition command invokes the supported Kaggle API/CLI for the competition slug, downloads the archive into the local raw-data area, and extracts the expected files.
3. The command refuses to overwrite existing raw files by default. An explicit, documented refresh action is required to replace a download.
4. The workflow records retrieval time, source identifier, filenames, byte sizes, and checksums so team members can compare their local copies.
5. The acquisition guide includes a manual-download fallback for contributors who cannot use the API/CLI. The fallback must place the same files in the same directory and run the same checksum and validation steps.

Kaggle tokens, usernames, API keys, browser cookies, and credential files must remain in user-level configuration or environment variables and must never be committed. The implementation must verify current official Kaggle authentication and command details rather than relying on undocumented assumptions in this plan.

## 7. Raw Data Policy

- Files under `data/raw/` are immutable source artifacts.
- Acquisition may create a missing raw file, but validation and transformation code must never edit it in place.
- Re-running acquisition must not silently overwrite or merge raw files.
- All transformations must write to a different future directory such as `data/interim/` or `data/processed/`; those directories are deferred until Phase 2.
- Dataset archives and extracted tables remain ignored by Git.
- Source, retrieval steps, expected filenames, and integrity metadata are documented in version-controlled text.
- Validation should calculate checksums before and after reading when practical so accidental mutation can be detected.
- Raw paths must be resolved with portable path handling rather than Windows-only string concatenation.

## 8. Validation Specification

The implementation should distinguish hard failures, which make the foundation unsafe, from warnings that require documentation and later decisions.

### File-Level Checks

- Confirm all four expected filenames exist in the configured raw directory.
- Confirm files are regular, non-empty files and can be parsed with the declared encoding and delimiter.
- Record file sizes, row counts, headers, and checksums.
- Detect duplicate or ambiguous copies rather than choosing one silently.
- Fail clearly on corrupt archives, unreadable CSV files, or missing required files.

### Schema Checks

- Compare actual columns with a versioned expected-column specification created from the verified download and official description.
- Require proposal-critical fields where applicable: `Store`, `Date`, `Sales`, `Customers`, `Open`, `Promo`, `StateHoliday`, `SchoolHoliday`, store attributes, competition fields, and Promo2 fields.
- Confirm `Sales` appears in historical training data and is absent from the future test target set.
- Parse fields into explicit types and report values that cannot be converted.
- Report unexpected columns for review; do not drop them automatically.
- Keep source columns unchanged during validation.

### Key and Join Checks

- Require `(Store, Date)` uniqueness in historical store-day data.
- Check the corresponding store-day key in the test data after its actual schema is confirmed.
- Require a unique `Store` key in `store.csv`.
- Confirm every store referenced by train and test matches exactly one metadata row.
- Validate joins as many store-days to one store and assert that a left join does not change row counts.
- Report metadata stores unused by train or test rather than deleting them.

### Date Checks

- Parse `Date` strictly and report unparseable or missing values.
- Record minimum and maximum dates for each store-day file.
- Detect duplicate dates within each store through the key checks.
- Report calendar gaps by store, including leading and trailing coverage differences, without automatically inserting rows.
- Treat a missing calendar date as an observation to investigate, not immediate proof of bad data, because store operation and source coverage must first be understood.

### Target and Business-Field Checks

- Verify `Sales` is numeric, finite, and non-negative; record zero-sales frequency separately.
- Verify `Customers` is numeric, finite, and non-negative where present.
- Profile and validate `Open`, `Promo`, and `SchoolHoliday` domains after their actual encodings are confirmed.
- Profile `StateHoliday` values and distinguish valid codes from malformed or inconsistent encodings.
- Report nulls and impossible values with file, field, and count context.
- Keep `Customers` available for historical validation and descriptive work, while marking it unavailable as a future production forecasting feature.

### Store-Metadata Checks

- Verify and profile `StoreType`, `Assortment`, and `CompetitionDistance`.
- Verify the presence and joint missingness of competition-open month/year fields.
- Verify `Promo2`, `Promo2SinceWeek`, `Promo2SinceYear`, and `PromoInterval` together.
- Profile categorical domains before assigning meaning to their codes.
- Distinguish missing values caused by non-participation or unavailable concepts from suspicious incomplete records.

### Missing-Value Checks

- Produce null counts and percentages by file and column.
- Test conditional missingness, such as Promo2 detail fields relative to Promo2 participation and competition dates relative to competition information.
- Label a missingness pattern as structural only when the observed relationships and official description support it.
- Leave ambiguous cases documented as unresolved rather than imputing them in Phase 1.

### Closed-Store Checks

- Cross-tabulate `Open` with zero and positive `Sales` and `Customers`.
- Report records such as `Open = 0` with positive `Sales` or `Customers`, and `Open = 1` with zero `Sales`.
- Do not change values or impose the later zero-forecast rule during source validation.
- Carry verified anomalies and decisions forward to Phase 2.

### Outlier Checks

- Report distributions, quantiles, extreme values, and affected store-dates for numerical fields.
- Flag negative, non-finite, or clearly invalid values as validation failures.
- Treat high positive sales as review candidates rather than errors because promotions, holidays, and legitimate demand spikes may explain them.
- Do not remove or cap observations in Phase 1.

### Data-Leakage Checks

- Phase 1 must not create lags, rolling features, target encodings, or train/validation splits.
- Validation summaries may use the full source files only to describe data quality; they must not be presented as forecasting performance.
- No future `Sales` or future `Customers` values may be transformed into production features.
- Row order must never be randomized as part of validation.

## 9. Data Dictionary Update Strategy

After validation succeeds, update `docs/DATA_DICTIONARY.md` from observed evidence:

1. Record the actual source file for each Rossmann field.
2. Replace `TBD` types, encodings, categories, and ranges only when verified by the downloaded data and official description.
3. Record observed missingness and whether its structural interpretation is verified or still unresolved.
4. Preserve the forecast-time availability warning for `Customers`.
5. Keep derived-feature definitions separate; Phase 1 must not claim those features have been implemented.
6. Leave synthetic operational variables unchanged and explicitly simulated; they are outside Phase 1.
7. Cite the validation date or source version so later changes are auditable.

Unknown or ambiguous facts remain `TBD` with an explanation. Do not infer business meanings from category codes without evidence.

## 10. Validation Outputs

Use three output levels:

- **Console summary:** concise pass/fail counts, warnings, source paths, and a non-zero exit code for hard failures. This supports local and future CI execution.
- **Generated local report:** structured JSON and, where useful, small CSV summaries under `reports/validation/`. These outputs are reproducible and ignored by Git; they must not contain unnecessary raw rows.
- **Version-controlled summary:** `docs/DATA_VALIDATION.md` records the source version, file checksums or identifiers, validation command, key findings, known issues, and disposition. Keep it concise and exclude large tables.

Recommended report sections are schema summary, missingness profile, duplicate/key report, invalid-value report, date-coverage report, join-integrity report, closed-store cross-tabulation, outlier summary, and overall validation status.

## 11. Test Strategy

Implement tests with tiny constructed fixtures created inside the test suite. Do not copy rows from the Rossmann dataset into Git.

Required cases:

- valid minimum datasets pass required file, schema, key, and join checks;
- a duplicate `(Store, Date)` is detected;
- a duplicate `Store` metadata key is detected;
- an unmatched store key or row-multiplying join fails;
- an invalid or unparseable date is detected;
- a missing required column and an unexpected column are reported correctly;
- an invalid `Open` value is detected after its domain is confirmed;
- negative or non-finite `Sales` and `Customers` are rejected;
- closed-store inconsistencies are reported without mutating data;
- structural and suspicious missingness are distinguished according to explicit rules;
- validation leaves raw-file bytes and checksums unchanged;
- path handling works with a temporary directory and does not depend on the repository's absolute Windows path.

Tests should target small reusable functions. One command should run the complete Phase 1 suite.

## 12. Proposed Files to Create or Modify

Expected implementation changes, subject to review before coding:

### Create

- `pyproject.toml`
- `data/README.md`
- local ignored directory `data/raw/rossmann/`
- `docs/DATA_ACQUISITION.md`
- `docs/DATA_VALIDATION.md`
- local ignored directory `reports/validation/`
- `scripts/acquire_data.py`
- `scripts/validate_data.py`
- `src/rossmann_forecasting/__init__.py`
- `src/rossmann_forecasting/data/__init__.py`
- `src/rossmann_forecasting/data/acquisition.py`
- `src/rossmann_forecasting/data/validation.py`
- `tests/test_data_validation.py`

### Modify

- `.gitignore`, only if the final generated-output paths need additional coverage
- `README.md`, with verified setup and validation commands
- `docs/DATA_DICTIONARY.md`, with observed facts only
- `docs/PROGRESS.md`, with actual Phase 1 status and checks
- `docs/DECISIONS.md`, only if an environment or acquisition choice becomes a durable project decision

Do not create any of these implementation files or directories during this planning task.

## 13. Acceptance Criteria

Phase 1 may be declared complete only when:

- authorized team members can reproducibly obtain all required source files from documented instructions;
- raw data files and credentials remain untracked and raw bytes remain unchanged by validation;
- actual file headers, types, row counts, date ranges, and checksums have been inspected and recorded;
- Store × Date uniqueness, store-key uniqueness, and many-to-one metadata join integrity have been checked;
- missingness, categorical domains, numeric ranges, closed-store relationships, and outliers have been reported;
- every hard validation failure is corrected at the acquisition/configuration level or explicitly documented as an unresolved source-data issue;
- one documented command runs the validation pipeline and returns a meaningful exit status;
- the Phase 1 tests pass and the exact test command and result are recorded;
- `docs/DATA_DICTIONARY.md` contains verified observations instead of guesses while unresolved facts remain `TBD`;
- no EDA, feature engineering, forecasting, synthetic operational data, or inventory logic has been introduced;
- no dataset, credential, large generated report, or temporary artifact is committed;
- `docs/PROGRESS.md`, relevant documentation, and the completed execution plan match the repository state.

## 14. Risks and Open Questions

- **Kaggle access:** Does each contributor have an account, accepted competition access, and a working authentication method?
- **Official schema:** What exact columns and encodings are present in the current authorized download, especially in `test.csv` and `sample_submission.csv`?
- **Dataset version:** Will Kaggle deliver identical archives and checksums to every contributor, and how should a source refresh be approved?
- **Python version:** Which single Python version is available to all team members and compatible with the later analytics, FastAPI, and Streamlit stack?
- **Dependency locking:** Which lock or constraints workflow best fits the team's available tooling after `pyproject.toml` is adopted?
- **Structural missingness:** Which competition and Promo2 null patterns are supported by official semantics versus only suggested by observed correlations?
- **Closed-store anomalies:** Do any positive-sales or positive-customer records occur while `Open = 0`, and how should Phase 2 handle verified exceptions?
- **Calendar coverage:** Are date gaps expected source behavior, store closures, or missing records?
- **Windows portability:** Acquisition and validation commands must work from PowerShell while remaining portable to other operating systems.
- **Storage and runtime:** Confirm archive size, extracted size, parse memory, and validation runtime on the team's least-capable computer.
- **Manual fallback:** If Kaggle API access is unavailable, what exact manual verification steps ensure all contributors use the same source version?

Do not resolve these questions by guessing. Record evidence during implementation and escalate choices that affect project methodology.

## 15. Definition of Done

- [x] Phase 1 implementation stayed within acquisition and validation scope.
- [x] The approved environment strategy and supported Python version are documented.
- [x] Official Rossmann files are reproducibly obtainable by authorized contributors.
- [x] Credentials and datasets are excluded from Git.
- [x] Raw files are immutable and protected from silent overwrite.
- [x] File, schema, type, key, date, missingness, domain, join, closed-store, and outlier checks run successfully or have documented findings.
- [x] Store × Date remains the validated unit of analysis.
- [x] `Sales` remains a monetary target and no SKU-level claim is introduced.
- [x] `Customers` is marked unavailable as a future production feature.
- [x] No future-looking transformations or random shuffling are introduced.
- [x] Synthetic supply-chain and inventory data remain outside Phase 1.
- [x] The Data Dictionary contains only verified updates.
- [x] Focused validation tests pass, and their command and results are recorded.
- [x] Generated reports contain no unnecessary raw data and large outputs remain untracked.
- [x] Relevant documentation and `docs/PROGRESS.md` match actual implementation.
- [x] `git diff` and `git status` show only intended Phase 1 changes.
- [x] This plan is moved to `plans/completed/` only after implementation and validation are finished.

## 16. Implementation Record - 2026-10-05

Implementation began only after this plan was committed as
`e8a0409 docs: add phase 1 data acquisition and validation plan`.

Implemented the planned package, acquisition command, read-only validator, JSON report, fixture
suite, and documentation. Two small structural additions were made to keep path resolution reusable:
`src/rossmann_forecasting/data/paths.py` and console entry points in `pyproject.toml`.

The local environment used Python 3.14.5, pandas 3.0.6, Kaggle CLI 2.2.4, pytest 9.1.1, and Ruff
0.16.10. Twelve tests passed; Ruff lint and format checks passed. The tests include a CLI run against
a temporary constructed fixture and verify that raw checksums do not change.

Acquisition readiness found no local source files, found the Kaggle CLI, and detected a
structurally configured user credential without printing its values. The official download then
returned HTTP 403 Forbidden. The command left no partial `data/raw/rossmann/` directory.

This was State C from the implementation instructions. Phase 1 remained blocked until an official
source became available.

## 17. Completion Record - 2026-10-05

The user confirmed that the four files in `data/raw/rossmann/` were downloaded manually from the
official Kaggle competition. The manual path is now the verified acquisition method; the earlier API
HTTP 403 response did not affect this snapshot and is no longer a blocker. File sizes and SHA-256
hashes are recorded in `docs/DATA_ACQUISITION.md`.

Formal validation passed with 0 errors, 4 reviewed warnings, and 12 informational findings. It
verified schemas, date coverage, missingness, categorical domains, non-negative finite targets,
unique Store × Date and metadata keys, many-to-one joins, and unchanged raw hashes. The warnings
cover a shared 184-day source gap for 180 stores, 54 open-store zero-sales rows, 11 missing test
`Open` values for Store 622, and 259 metadata stores absent from the 856-store test subset. None was
suppressed or treated as permission to modify raw data.

The Data Dictionary now records observed source types, ranges, categories, and missingness while
keeping future actual `Customers` unavailable, derived features unimplemented, and synthetic
operational fields explicitly simulated. The reproducible JSON report remains ignored; concise
verified facts are version-controlled in Markdown. All acceptance criteria were reviewed and
satisfied, so Phase 1 is complete and this plan is ready for `plans/completed/`.
