"""Reusable, read-only validation for Rossmann Store Sales source files."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from rossmann_forecasting.data.acquisition import EXPECTED_SOURCE_FILES, sha256_file
from rossmann_forecasting.data.paths import repository_root, resolve_data_dir

REQUIRED_FILES = EXPECTED_SOURCE_FILES

TRAIN_REQUIRED_COLUMNS = {
    "Store",
    "Date",
    "Sales",
    "Customers",
    "Open",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
}
TRAIN_KNOWN_COLUMNS = TRAIN_REQUIRED_COLUMNS | {"DayOfWeek"}
TEST_REQUIRED_COLUMNS = {
    "Store",
    "Date",
    "Open",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
}
TEST_KNOWN_COLUMNS = TEST_REQUIRED_COLUMNS | {"Id", "DayOfWeek"}
STORE_REQUIRED_COLUMNS = {
    "Store",
    "StoreType",
    "Assortment",
    "CompetitionDistance",
    "CompetitionOpenSinceMonth",
    "CompetitionOpenSinceYear",
    "Promo2",
    "Promo2SinceWeek",
    "Promo2SinceYear",
    "PromoInterval",
}
SAMPLE_SUBMISSION_REQUIRED_COLUMNS = {"Id", "Sales"}


class Severity(StrEnum):
    """Validation finding severity."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    """One concise validation observation."""

    severity: Severity
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Machine-readable validation result."""

    data_dir: str
    findings: list[Finding] = field(default_factory=list)
    files: dict[str, dict[str, Any]] = field(default_factory=dict)
    missingness: dict[str, dict[str, dict[str, float | int]]] = field(default_factory=dict)
    date_ranges: dict[str, dict[str, Any]] = field(default_factory=dict)
    observed_values: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    numeric_summaries: dict[str, dict[str, dict[str, float | int | None]]] = field(
        default_factory=dict
    )
    join_integrity: dict[str, dict[str, Any]] = field(default_factory=dict)
    cross_tabs: dict[str, dict[str, int]] = field(default_factory=dict)

    def add(
        self,
        severity: Severity,
        code: str,
        message: str,
        **context: Any,
    ) -> None:
        self.findings.append(Finding(severity, code, message, context))

    @property
    def passed(self) -> bool:
        return not any(item.severity == Severity.ERROR for item in self.findings)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"

    @property
    def finding_counts(self) -> dict[str, int]:
        return {
            severity.value: sum(item.severity == severity for item in self.findings)
            for severity in Severity
        }

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(
            {
                "status": self.status,
                "data_dir": self.data_dir,
                "finding_counts": self.finding_counts,
                "findings": [asdict(item) for item in self.findings],
                "files": self.files,
                "missingness": self.missingness,
                "date_ranges": self.date_ranges,
                "observed_values": self.observed_values,
                "numeric_summaries": self.numeric_summaries,
                "join_integrity": self.join_integrity,
                "cross_tabs": self.cross_tabs,
            }
        )

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return _jsonable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _normalise_category(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _load_csv(path: Path, report: ValidationReport) -> pd.DataFrame | None:
    name = path.name
    before_hash = sha256_file(path)
    metadata: dict[str, Any] = {
        "present": True,
        "bytes": path.stat().st_size,
        "sha256": before_hash,
    }

    try:
        frame = pd.read_csv(path, low_memory=False)
    except (EmptyDataError, ParserError, OSError, UnicodeError) as error:
        report.files[name] = metadata | {"readable": False}
        report.add(
            Severity.ERROR,
            "FILE_PARSE_FAILED",
            f"Could not parse {name} as CSV.",
            file=name,
            error_type=type(error).__name__,
        )
        return None

    after_hash = sha256_file(path)
    if after_hash != before_hash:
        report.add(
            Severity.ERROR,
            "RAW_FILE_MUTATED",
            f"Raw file changed while it was being validated: {name}.",
            file=name,
        )

    metadata.update(
        {
            "readable": True,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        }
    )
    report.files[name] = metadata

    if frame.empty:
        report.add(Severity.ERROR, "EMPTY_TABLE", f"{name} contains no data rows.", file=name)
    return frame


def _validate_columns(
    frame: pd.DataFrame,
    filename: str,
    required: set[str],
    known: set[str],
    report: ValidationReport,
) -> None:
    actual = set(frame.columns)
    missing = sorted(required - actual)
    unexpected = sorted(actual - known)
    if missing:
        report.add(
            Severity.ERROR,
            "MISSING_REQUIRED_COLUMNS",
            f"{filename} is missing required columns.",
            file=filename,
            columns=missing,
        )
    if unexpected:
        report.add(
            Severity.INFO,
            "UNEXPECTED_COLUMNS",
            f"{filename} contains columns outside the current minimum schema.",
            file=filename,
            columns=unexpected,
        )


def _profile_missingness(filename: str, frame: pd.DataFrame, report: ValidationReport) -> None:
    row_count = len(frame)
    report.missingness[filename] = {}
    for column in frame.columns:
        count = int(frame[column].isna().sum())
        report.missingness[filename][column] = {
            "count": count,
            "percent": round((count / row_count * 100) if row_count else 0.0, 6),
        }
    missing_columns = [
        column for column, values in report.missingness[filename].items() if values["count"] > 0
    ]
    if missing_columns:
        report.add(
            Severity.INFO,
            "MISSING_VALUES_OBSERVED",
            f"{filename} contains missing values that require field-specific review.",
            file=filename,
            columns=missing_columns,
        )


def _numeric_series(
    frame: pd.DataFrame,
    column: str,
    filename: str,
    report: ValidationReport,
    *,
    non_negative: bool = False,
    require_complete: bool = False,
) -> pd.Series | None:
    if column not in frame.columns:
        return None
    original = frame[column]
    numeric = pd.to_numeric(original, errors="coerce")
    invalid = original.notna() & numeric.isna()
    if invalid.any():
        report.add(
            Severity.ERROR,
            "INVALID_NUMERIC_VALUE",
            f"{filename}.{column} contains values that are not numeric.",
            file=filename,
            column=column,
            count=int(invalid.sum()),
        )
    if require_complete and numeric.isna().any():
        report.add(
            Severity.ERROR,
            "MISSING_REQUIRED_VALUE",
            f"{filename}.{column} contains missing required values.",
            file=filename,
            column=column,
            count=int(numeric.isna().sum()),
        )
    finite = numeric.dropna().map(math.isfinite)
    if not finite.all():
        report.add(
            Severity.ERROR,
            "NON_FINITE_VALUE",
            f"{filename}.{column} contains non-finite values.",
            file=filename,
            column=column,
            count=int((~finite).sum()),
        )
    if non_negative:
        negative_count = int((numeric < 0).sum())
        if negative_count:
            report.add(
                Severity.ERROR,
                "NEGATIVE_VALUE",
                f"{filename}.{column} contains negative values.",
                file=filename,
                column=column,
                count=negative_count,
            )
    return numeric


def _validate_binary(
    frame: pd.DataFrame,
    column: str,
    filename: str,
    report: ValidationReport,
    *,
    require_complete: bool = True,
) -> pd.Series | None:
    numeric = _numeric_series(
        frame,
        column,
        filename,
        report,
        non_negative=True,
        require_complete=require_complete,
    )
    if numeric is None:
        return None
    invalid = numeric.notna() & ~numeric.isin([0, 1])
    if invalid.any():
        values = sorted({_normalise_category(value) for value in numeric[invalid].unique()})
        report.add(
            Severity.ERROR,
            "INVALID_BINARY_VALUE",
            f"{filename}.{column} contains values outside {{0, 1}}.",
            file=filename,
            column=column,
            count=int(invalid.sum()),
            values=values,
        )
    return numeric


def _profile_categories(
    filename: str,
    frame: pd.DataFrame,
    columns: list[str],
    report: ValidationReport,
) -> None:
    report.observed_values.setdefault(filename, {})
    for column in columns:
        if column not in frame.columns:
            continue
        values = sorted({_normalise_category(value) for value in frame[column].dropna().unique()})
        report.observed_values[filename][column] = values[:100]


def _validate_expected_categories(
    filename: str,
    frame: pd.DataFrame,
    column: str,
    expected: set[str],
    report: ValidationReport,
) -> None:
    if column not in frame.columns:
        return
    observed = {_normalise_category(value) for value in frame[column].dropna().unique()}
    unexpected = sorted(observed - expected)
    if unexpected:
        report.add(
            Severity.WARNING,
            "UNEXPECTED_CATEGORY",
            f"{filename}.{column} contains categories requiring review.",
            file=filename,
            column=column,
            values=unexpected,
        )


def _validate_dates(
    filename: str,
    frame: pd.DataFrame,
    report: ValidationReport,
) -> pd.Series | None:
    if "Date" not in frame.columns:
        return None

    parsed = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    invalid_count = int(parsed.isna().sum())
    if invalid_count:
        report.add(
            Severity.ERROR,
            "INVALID_DATE",
            f"{filename}.Date contains missing or unparseable dates.",
            file=filename,
            count=invalid_count,
        )

    valid = parsed.dropna()
    if not valid.empty:
        report.date_ranges[filename] = {
            "min": valid.min(),
            "max": valid.max(),
        }

    if "Store" not in frame.columns:
        return parsed

    dated = pd.DataFrame({"Store": frame["Store"], "Date": parsed}).dropna()
    increasing = 0
    decreasing = 0
    unordered = 0
    for _, group in dated.groupby("Store", sort=False):
        dates = group["Date"]
        if dates.is_monotonic_increasing:
            increasing += 1
        elif dates.is_monotonic_decreasing:
            decreasing += 1
        else:
            unordered += 1
    report.add(
        Severity.INFO,
        "DATE_ORDER",
        f"Observed per-store date ordering in {filename}.",
        file=filename,
        increasing_stores=increasing,
        decreasing_stores=decreasing,
        unordered_stores=unordered,
    )
    if unordered:
        report.add(
            Severity.WARNING,
            "UNORDERED_STORE_DATES",
            f"{filename} contains stores whose input rows are not chronologically ordered.",
            file=filename,
            stores=unordered,
        )

    unique_dates = dated.drop_duplicates().sort_values(["Store", "Date"])
    differences = unique_dates.groupby("Store")["Date"].diff().dt.days
    gap_mask = differences > 1
    gap_rows = int(gap_mask.sum())
    missing_days = int((differences[gap_mask] - 1).sum()) if gap_rows else 0
    affected_stores = int(unique_dates.loc[gap_mask, "Store"].nunique()) if gap_rows else 0
    if gap_rows:
        report.add(
            Severity.WARNING,
            "DATE_GAPS",
            f"{filename} contains per-store calendar gaps for review.",
            file=filename,
            gap_intervals=gap_rows,
            missing_calendar_days=missing_days,
            affected_stores=affected_stores,
        )
    return parsed


def _validate_store_date_key(
    filename: str,
    frame: pd.DataFrame,
    report: ValidationReport,
) -> None:
    if not {"Store", "Date"}.issubset(frame.columns):
        return
    duplicate_count = int(frame.duplicated(["Store", "Date"], keep=False).sum())
    if duplicate_count:
        report.add(
            Severity.ERROR,
            "DUPLICATE_STORE_DATE",
            f"{filename} contains duplicate Store × Date rows.",
            file=filename,
            rows=duplicate_count,
        )
    else:
        report.add(
            Severity.INFO,
            "UNIQUE_STORE_DATE",
            f"{filename} has unique Store × Date rows.",
            file=filename,
        )


def _profile_numeric(
    filename: str,
    frame: pd.DataFrame,
    columns: list[str],
    report: ValidationReport,
) -> None:
    report.numeric_summaries.setdefault(filename, {})
    for column in columns:
        if column not in frame.columns:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        numeric = numeric[
            numeric.map(lambda value: math.isfinite(value) if pd.notna(value) else False)
        ]
        if numeric.empty:
            continue
        report.numeric_summaries[filename][column] = {
            "count": int(numeric.count()),
            "min": float(numeric.min()),
            "p01": float(numeric.quantile(0.01)),
            "median": float(numeric.median()),
            "p99": float(numeric.quantile(0.99)),
            "max": float(numeric.max()),
        }


def _validate_train(frame: pd.DataFrame, report: ValidationReport) -> None:
    filename = "train.csv"
    _validate_store_date_key(filename, frame, report)
    _validate_dates(filename, frame, report)
    _numeric_series(frame, "Store", filename, report, non_negative=True, require_complete=True)
    sales = _numeric_series(
        frame, "Sales", filename, report, non_negative=True, require_complete=True
    )
    customers = _numeric_series(
        frame, "Customers", filename, report, non_negative=True, require_complete=True
    )
    open_values = _validate_binary(frame, "Open", filename, report)
    _validate_binary(frame, "Promo", filename, report)
    _validate_binary(frame, "SchoolHoliday", filename, report)
    _profile_categories(
        filename,
        frame,
        ["Open", "Promo", "StateHoliday", "SchoolHoliday"],
        report,
    )
    _validate_expected_categories(filename, frame, "StateHoliday", {"0", "a", "b", "c"}, report)
    _profile_numeric(filename, frame, ["Sales", "Customers"], report)

    if sales is not None:
        report.add(
            Severity.INFO,
            "ZERO_SALES_COUNT",
            "Observed historical rows with zero Sales.",
            count=int((sales == 0).sum()),
        )
    if customers is not None:
        report.add(
            Severity.INFO,
            "ZERO_CUSTOMERS_COUNT",
            "Observed historical rows with zero Customers.",
            count=int((customers == 0).sum()),
        )
    if open_values is None:
        return

    if sales is not None:
        report.cross_tabs["train_open_sales"] = {
            "closed_zero": int(((open_values == 0) & (sales == 0)).sum()),
            "closed_positive": int(((open_values == 0) & (sales > 0)).sum()),
            "open_zero": int(((open_values == 1) & (sales == 0)).sum()),
            "open_positive": int(((open_values == 1) & (sales > 0)).sum()),
        }
        closed_positive_sales = int(((open_values == 0) & (sales > 0)).sum())
        open_zero_sales = int(((open_values == 1) & (sales == 0)).sum())
        if closed_positive_sales:
            report.add(
                Severity.WARNING,
                "CLOSED_WITH_POSITIVE_SALES",
                "Closed-store rows with positive Sales require review.",
                count=closed_positive_sales,
            )
        if open_zero_sales:
            report.add(
                Severity.WARNING,
                "OPEN_WITH_ZERO_SALES",
                "Open-store rows with zero Sales require review.",
                count=open_zero_sales,
            )
    if customers is not None:
        report.cross_tabs["train_open_customers"] = {
            "closed_zero": int(((open_values == 0) & (customers == 0)).sum()),
            "closed_positive": int(((open_values == 0) & (customers > 0)).sum()),
            "open_zero": int(((open_values == 1) & (customers == 0)).sum()),
            "open_positive": int(((open_values == 1) & (customers > 0)).sum()),
        }
        closed_positive_customers = int(((open_values == 0) & (customers > 0)).sum())
        if closed_positive_customers:
            report.add(
                Severity.WARNING,
                "CLOSED_WITH_POSITIVE_CUSTOMERS",
                "Closed-store rows with positive Customers require review.",
                count=closed_positive_customers,
            )

    report.add(
        Severity.INFO,
        "CUSTOMERS_FUTURE_UNAVAILABLE",
        "Customers is historical-only and must not become a future production feature.",
    )


def _validate_test(frame: pd.DataFrame, report: ValidationReport) -> None:
    filename = "test.csv"
    _validate_store_date_key(filename, frame, report)
    _validate_dates(filename, frame, report)
    _numeric_series(frame, "Store", filename, report, non_negative=True, require_complete=True)
    open_values = _validate_binary(frame, "Open", filename, report, require_complete=False)
    if open_values is not None and open_values.isna().any():
        report.add(
            Severity.WARNING,
            "MISSING_FUTURE_OPEN",
            "test.csv.Open contains missing values that need a documented Phase 2 rule.",
            count=int(open_values.isna().sum()),
        )
    _validate_binary(frame, "Promo", filename, report)
    _validate_binary(frame, "SchoolHoliday", filename, report)
    _profile_categories(
        filename,
        frame,
        ["Open", "Promo", "StateHoliday", "SchoolHoliday"],
        report,
    )
    _validate_expected_categories(filename, frame, "StateHoliday", {"0", "a", "b", "c"}, report)
    if "Sales" in frame.columns:
        report.add(
            Severity.ERROR,
            "TEST_CONTAINS_TARGET",
            "test.csv unexpectedly contains Sales.",
            file=filename,
        )


def _validate_store_metadata(frame: pd.DataFrame, report: ValidationReport) -> None:
    filename = "store.csv"
    _numeric_series(frame, "Store", filename, report, non_negative=True, require_complete=True)
    if "Store" in frame.columns:
        duplicate_count = int(frame.duplicated("Store", keep=False).sum())
        if duplicate_count:
            report.add(
                Severity.ERROR,
                "DUPLICATE_STORE_METADATA",
                "store.csv contains duplicate Store identifiers.",
                rows=duplicate_count,
            )
        else:
            report.add(
                Severity.INFO,
                "UNIQUE_STORE_METADATA",
                "store.csv has unique Store identifiers.",
            )

    _profile_categories(
        filename, frame, ["StoreType", "Assortment", "Promo2", "PromoInterval"], report
    )
    _validate_expected_categories(filename, frame, "StoreType", {"a", "b", "c", "d"}, report)
    _validate_expected_categories(filename, frame, "Assortment", {"a", "b", "c"}, report)
    _validate_binary(frame, "Promo2", filename, report)
    _numeric_series(frame, "CompetitionDistance", filename, report, non_negative=True)
    competition_month = _numeric_series(
        frame, "CompetitionOpenSinceMonth", filename, report, non_negative=True
    )
    competition_year = _numeric_series(
        frame, "CompetitionOpenSinceYear", filename, report, non_negative=True
    )
    promo_week = _numeric_series(frame, "Promo2SinceWeek", filename, report, non_negative=True)
    promo_year = _numeric_series(frame, "Promo2SinceYear", filename, report, non_negative=True)
    _profile_numeric(
        filename,
        frame,
        [
            "CompetitionDistance",
            "CompetitionOpenSinceMonth",
            "CompetitionOpenSinceYear",
            "Promo2SinceWeek",
            "Promo2SinceYear",
        ],
        report,
    )

    for column, numeric, low, high in (
        ("CompetitionOpenSinceMonth", competition_month, 1, 12),
        ("Promo2SinceWeek", promo_week, 1, 53),
        ("CompetitionOpenSinceYear", competition_year, 1900, 2100),
        ("Promo2SinceYear", promo_year, 1900, 2100),
    ):
        if numeric is None:
            continue
        invalid = numeric.notna() & ~numeric.between(low, high)
        if invalid.any():
            report.add(
                Severity.ERROR,
                "INVALID_METADATA_RANGE",
                f"store.csv.{column} contains values outside the expected range.",
                column=column,
                count=int(invalid.sum()),
                minimum=low,
                maximum=high,
            )

    if competition_month is not None and competition_year is not None:
        mismatched = int((competition_month.isna() ^ competition_year.isna()).sum())
        both_missing = int((competition_month.isna() & competition_year.isna()).sum())
        if mismatched:
            report.add(
                Severity.WARNING,
                "COMPETITION_DATE_PARTIAL",
                "Competition opening month/year has partial missingness.",
                count=mismatched,
            )
        if both_missing:
            report.add(
                Severity.INFO,
                "COMPETITION_DATE_MISSING",
                "Competition opening month/year is jointly missing and requires semantic review.",
                count=both_missing,
            )

    if "Promo2" in frame.columns:
        promo2 = pd.to_numeric(frame["Promo2"], errors="coerce")
        detail_columns = ["Promo2SinceWeek", "Promo2SinceYear", "PromoInterval"]
        available_details = [column for column in detail_columns if column in frame.columns]
        if available_details:
            detail_missing = frame[available_details].isna().any(axis=1)
            non_participant_missing = int(((promo2 == 0) & detail_missing).sum())
            participant_missing = int(((promo2 == 1) & detail_missing).sum())
            if non_participant_missing:
                report.add(
                    Severity.INFO,
                    "PROMO2_LIKELY_STRUCTURAL_MISSINGNESS",
                    "Promo2 details are missing for non-participating stores.",
                    count=non_participant_missing,
                )
            if participant_missing:
                report.add(
                    Severity.WARNING,
                    "PROMO2_PARTICIPANT_MISSING_DETAILS",
                    "Promo2 participants have missing Promo2 details.",
                    count=participant_missing,
                )


def _validate_join(
    filename: str,
    frame: pd.DataFrame,
    stores: pd.DataFrame,
    report: ValidationReport,
) -> None:
    if "Store" not in frame.columns or "Store" not in stores.columns:
        return

    source_ids = set(frame["Store"].dropna().tolist())
    metadata_ids = set(stores["Store"].dropna().tolist())
    unmatched = sorted(source_ids - metadata_ids, key=str)
    unused = sorted(metadata_ids - source_ids, key=str)
    result: dict[str, Any] = {
        "source_rows": int(len(frame)),
        "unmatched_store_count": len(unmatched),
        "unused_metadata_store_count": len(unused),
    }

    if unmatched:
        report.add(
            Severity.ERROR,
            "MISSING_STORE_METADATA",
            f"{filename} references stores absent from store.csv.",
            file=filename,
            store_count=len(unmatched),
            sample=unmatched[:20],
        )
    if unused:
        report.add(
            Severity.WARNING,
            "UNUSED_STORE_METADATA",
            f"store.csv contains stores unused by {filename}.",
            file=filename,
            store_count=len(unused),
            sample=unused[:20],
        )

    try:
        joined = frame[["Store"]].merge(
            stores[["Store"]], on="Store", how="left", validate="many_to_one"
        )
        result["joined_rows"] = int(len(joined))
        result["row_count_preserved"] = len(joined) == len(frame)
        if len(joined) != len(frame):
            report.add(
                Severity.ERROR,
                "JOIN_ROW_MULTIPLICATION",
                f"Joining metadata changes the row count for {filename}.",
                file=filename,
                source_rows=len(frame),
                joined_rows=len(joined),
            )
    except pd.errors.MergeError:
        result["row_count_preserved"] = False
        report.add(
            Severity.ERROR,
            "INVALID_JOIN_CARDINALITY",
            f"Store metadata is not many-to-one for {filename}.",
            file=filename,
        )
    report.join_integrity[filename] = result


def validate_dataset(data_dir: str | Path | None = None) -> ValidationReport:
    """Validate Rossmann source files without modifying them."""

    directory = resolve_data_dir(data_dir)
    report = ValidationReport(data_dir=str(directory))
    frames: dict[str, pd.DataFrame] = {}

    if not directory.is_dir():
        report.add(
            Severity.ERROR,
            "DATA_DIRECTORY_MISSING",
            "The raw Rossmann data directory does not exist.",
            data_dir=str(directory),
        )

    for filename in EXPECTED_SOURCE_FILES:
        path = directory / filename
        if not path.is_file():
            severity = Severity.ERROR if filename in REQUIRED_FILES else Severity.WARNING
            report.add(
                severity,
                "REQUIRED_FILE_MISSING" if severity == Severity.ERROR else "OPTIONAL_FILE_MISSING",
                f"Expected source file is missing: {filename}.",
                file=filename,
            )
            report.files[filename] = {"present": False}
            continue
        report.files[filename] = {"present": True}
        frame = _load_csv(path, report)
        if frame is not None:
            frames[filename] = frame

    schemas = {
        "train.csv": (TRAIN_REQUIRED_COLUMNS, TRAIN_KNOWN_COLUMNS),
        "test.csv": (TEST_REQUIRED_COLUMNS, TEST_KNOWN_COLUMNS),
        "store.csv": (STORE_REQUIRED_COLUMNS, STORE_REQUIRED_COLUMNS),
        "sample_submission.csv": (
            SAMPLE_SUBMISSION_REQUIRED_COLUMNS,
            SAMPLE_SUBMISSION_REQUIRED_COLUMNS,
        ),
    }
    for filename, frame in frames.items():
        if filename in schemas:
            required, known = schemas[filename]
            _validate_columns(frame, filename, required, known, report)
        _profile_missingness(filename, frame, report)

    train = frames.get("train.csv")
    stores = frames.get("store.csv")
    test = frames.get("test.csv")
    sample = frames.get("sample_submission.csv")

    if train is not None:
        _validate_train(train, report)
    if stores is not None:
        _validate_store_metadata(stores, report)
    if test is not None:
        _validate_test(test, report)
    if train is not None and stores is not None:
        _validate_join("train.csv", train, stores, report)
    if test is not None and stores is not None:
        _validate_join("test.csv", test, stores, report)
    if test is not None and sample is not None and len(test) != len(sample):
        report.add(
            Severity.ERROR,
            "SUBMISSION_ROW_COUNT_MISMATCH",
            "sample_submission.csv row count does not match test.csv.",
            test_rows=len(test),
            submission_rows=len(sample),
        )
    if test is not None and sample is not None and "Id" in test and "Id" in sample:
        test_ids = test["Id"]
        sample_ids = sample["Id"]
        if test_ids.duplicated().any() or sample_ids.duplicated().any():
            report.add(
                Severity.ERROR,
                "DUPLICATE_SUBMISSION_ID",
                "test.csv and sample_submission.csv must have unique Id values.",
            )
        if set(test_ids.dropna()) != set(sample_ids.dropna()):
            report.add(
                Severity.ERROR,
                "SUBMISSION_ID_MISMATCH",
                "sample_submission.csv Id values do not match test.csv.",
            )

    for filename, metadata in report.files.items():
        if not metadata.get("present") or "sha256" not in metadata:
            continue
        current_hash = sha256_file(directory / filename)
        if current_hash != metadata["sha256"]:
            report.add(
                Severity.ERROR,
                "RAW_FILE_MUTATED",
                f"Raw file changed during validation: {filename}.",
                file=filename,
            )

    return report


def _print_summary(report: ValidationReport) -> None:
    counts = report.finding_counts
    print(
        f"Validation {report.status}: {counts['ERROR']} error(s), "
        f"{counts['WARNING']} warning(s), {counts['INFO']} info finding(s)"
    )
    print(f"Data directory: {report.data_dir}")
    for filename in EXPECTED_SOURCE_FILES:
        metadata = report.files.get(filename, {})
        if metadata.get("present") is False:
            print(f"- {filename}: missing")
        elif metadata.get("readable"):
            print(f"- {filename}: {metadata['rows']} row(s), {metadata['bytes']} bytes")
    for finding in report.findings:
        if finding.severity in {Severity.ERROR, Severity.WARNING}:
            print(f"[{finding.severity}] {finding.code}: {finding.message}")


def cli_main(argv: list[str] | None = None) -> int:
    """Run source-data validation from the command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        help="Raw-data directory; relative paths resolve from the repository root.",
    )
    parser.add_argument(
        "--report",
        help="Optional JSON report path; relative paths resolve from the repository root.",
    )
    args = parser.parse_args(argv)

    report = validate_dataset(args.data_dir)
    _print_summary(report)
    if args.report:
        output = Path(args.report).expanduser()
        if not output.is_absolute():
            output = repository_root() / output
        report.write_json(output.resolve(strict=False))
        print(f"JSON report: {output.resolve(strict=False)}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(cli_main())
