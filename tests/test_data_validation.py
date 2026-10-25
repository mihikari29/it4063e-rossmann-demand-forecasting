from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.data import validation
from rossmann_forecasting.data.acquisition import (
    AcquisitionError,
    acquire_official_data,
    sha256_file,
)
from rossmann_forecasting.data.paths import repository_root
from rossmann_forecasting.data.validation import Severity, validate_dataset

INVALID_SOURCE_IDENTITIES = [
    pytest.param(0, id="zero"),
    pytest.param(-1, id="negative"),
    pytest.param(1.5, id="fractional"),
    pytest.param(np.float64(1.5), id="numpy_fractional"),
    pytest.param(True, id="true"),
    pytest.param(False, id="false"),
    pytest.param(np.bool_(True), id="numpy_true"),
    pytest.param(np.bool_(False), id="numpy_false"),
    pytest.param(np.inf, id="infinity"),
    pytest.param(-np.inf, id="negative_infinity"),
    pytest.param("invalid", id="malformed_text"),
    pytest.param("0_1", id="malformed_numeric_text"),
    pytest.param("1.5", id="fractional_text"),
    pytest.param("1.0000000000000000000000000001", id="precise_fractional_text"),
    pytest.param(Decimal("1.0000000000000000000000000001"), id="precise_fractional_decimal"),
]


def _train_rows() -> list[dict[str, object]]:
    return [
        {
            "Store": 1,
            "DayOfWeek": 1,
            "Date": "2015-01-01",
            "Sales": 1000,
            "Customers": 100,
            "Open": 1,
            "Promo": 0,
            "StateHoliday": "0",
            "SchoolHoliday": 0,
        },
        {
            "Store": 1,
            "DayOfWeek": 2,
            "Date": "2015-01-02",
            "Sales": 1100,
            "Customers": 110,
            "Open": 1,
            "Promo": 1,
            "StateHoliday": "0",
            "SchoolHoliday": 0,
        },
    ]


def _store_rows() -> list[dict[str, object]]:
    return [
        {
            "Store": 1,
            "StoreType": "a",
            "Assortment": "a",
            "CompetitionDistance": 100.0,
            "CompetitionOpenSinceMonth": 1,
            "CompetitionOpenSinceYear": 2010,
            "Promo2": 0,
            "Promo2SinceWeek": None,
            "Promo2SinceYear": None,
            "PromoInterval": None,
        }
    ]


def _test_rows() -> list[dict[str, object]]:
    return [
        {
            "Id": 1,
            "Store": 1,
            "DayOfWeek": 3,
            "Date": "2015-01-03",
            "Open": 1,
            "Promo": 0,
            "StateHoliday": "0",
            "SchoolHoliday": 0,
        }
    ]


def _write_fixture(
    directory: Path,
    *,
    train: list[dict[str, object]] | None = None,
    stores: list[dict[str, object]] | None = None,
    test: list[dict[str, object]] | None = None,
) -> Path:
    directory.mkdir()
    pd.DataFrame(train if train is not None else _train_rows()).to_csv(
        directory / "train.csv", index=False
    )
    pd.DataFrame(stores if stores is not None else _store_rows()).to_csv(
        directory / "store.csv", index=False
    )
    test_frame = pd.DataFrame(test if test is not None else _test_rows())
    test_frame.to_csv(directory / "test.csv", index=False)
    pd.DataFrame({"Id": test_frame["Id"], "Sales": 0}).to_csv(
        directory / "sample_submission.csv", index=False
    )
    return directory


def _codes(report, severity: Severity | None = None) -> set[str]:
    return {
        finding.code
        for finding in report.findings
        if severity is None or finding.severity == severity
    }


def _frame_for_file(filename: str) -> pd.DataFrame:
    rows = {"train.csv": _train_rows, "test.csv": _test_rows, "store.csv": _store_rows}
    return pd.DataFrame(rows[filename]())


def _validate_frame(filename: str, frame: pd.DataFrame) -> validation.ValidationReport:
    validators = {
        "train.csv": validation._validate_train,
        "test.csv": validation._validate_test,
        "store.csv": validation._validate_store_metadata,
    }
    report = validation.ValidationReport(data_dir="in-memory-synthetic")
    validation._profile_missingness(filename, frame, report)
    validators[filename](frame, report)
    return report


@pytest.mark.parametrize(
    "filename, column, value",
    [
        ("train.csv", "Store", 0),
        ("train.csv", "Store", 1.5),
        ("train.csv", "DayOfWeek", 99),
        ("test.csv", "Store", 0),
        ("test.csv", "Store", 1.5),
        ("test.csv", "DayOfWeek", 99),
        ("store.csv", "Store", 0),
        ("store.csv", "Store", 1.5),
    ],
)
def test_audit_invalid_source_domains_fail(filename, column, value):
    frame = _frame_for_file(filename)
    frame[column] = value
    report = _validate_frame(filename, frame)
    assert not report.passed
    assert report.finding_counts["ERROR"] > 0


@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
@pytest.mark.parametrize("value", INVALID_SOURCE_IDENTITIES)
def test_invalid_store_identifiers_report_field_and_count_without_mutation(filename, value):
    frame = _frame_for_file(filename)
    frame["Store"] = pd.Series([value] * len(frame), dtype=object)
    before = frame.copy(deep=True)
    report = _validate_frame(filename, frame)

    findings = [finding for finding in report.findings if finding.code == "INVALID_STORE_ID"]
    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].context == {
        "file": filename,
        "column": "Store",
        "count": len(frame),
        "minimum": 1,
        "maximum": None,
    }
    assert not report.passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
@pytest.mark.parametrize("value", [*INVALID_SOURCE_IDENTITIES, 8, 99])
def test_invalid_weekdays_report_field_and_count_without_mutation(filename, value):
    frame = _frame_for_file(filename)
    frame["DayOfWeek"] = pd.Series([value] * len(frame), dtype=object)
    before = frame.copy(deep=True)
    report = _validate_frame(filename, frame)

    findings = [finding for finding in report.findings if finding.code == "INVALID_DAY_OF_WEEK"]
    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].context == {
        "file": filename,
        "column": "DayOfWeek",
        "count": len(frame),
        "minimum": 1,
        "maximum": 7,
    }
    assert not report.passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
@pytest.mark.parametrize("value", [None, np.nan, pd.NA])
def test_missing_store_keeps_existing_required_value_finding(filename, value):
    frame = _frame_for_file(filename)
    frame["Store"] = pd.Series([value] * len(frame), dtype=object)
    before = frame.copy(deep=True)
    report = _validate_frame(filename, frame)

    errors = [finding for finding in report.findings if finding.severity == Severity.ERROR]
    assert [(finding.code, finding.context) for finding in errors] == [
        ("MISSING_REQUIRED_VALUE", {"file": filename, "column": "Store", "count": len(frame)})
    ]
    assert not report.passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
@pytest.mark.parametrize("value", [None, np.nan, pd.NA])
def test_missing_weekday_values_retain_information_only_semantics(filename, value):
    frame = _frame_for_file(filename)
    frame["DayOfWeek"] = pd.Series([value] * len(frame), dtype=object)
    before = frame.copy(deep=True)
    report = _validate_frame(filename, frame)

    assert report.passed
    assert report.finding_counts["ERROR"] == 0
    assert "MISSING_VALUES_OBSERVED" in _codes(report, Severity.INFO)
    assert report.missingness[filename]["DayOfWeek"]["count"] == len(frame)
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
@pytest.mark.parametrize(
    "value",
    [
        1,
        1_000_000,
        2**53 + 1,
        np.int32(2),
        np.int64(3),
        np.uint64(4),
        1.0,
        np.float32(2),
        np.float64(3),
        "1",
        "2.0",
        "3e0",
        Decimal("4"),
    ],
)
def test_supported_positive_integer_store_representations_remain_valid(filename, value):
    frame = _frame_for_file(filename)
    frame["Store"] = pd.Series([value] * len(frame), dtype=object)
    before = frame.copy(deep=True)
    assert _validate_frame(filename, frame).passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
@pytest.mark.parametrize(
    "value",
    [*range(1, 8), np.int32(1), np.int64(7), 2.0, np.float64(3), "4.0", "5e0", Decimal("6")],
)
def test_all_weekday_codes_and_supported_integer_representations_remain_valid(filename, value):
    frame = _frame_for_file(filename)
    frame["DayOfWeek"] = pd.Series([value] * len(frame), dtype=object)
    before = frame.copy(deep=True)
    assert _validate_frame(filename, frame).passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("dtype", ["Int8", "Int64", "Float64"])
@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
def test_nullable_numeric_columns_preserve_valid_identities(filename, dtype):
    frame = _frame_for_file(filename)
    for column in ("Store", "DayOfWeek"):
        if column in frame:
            frame[column] = frame[column].astype(dtype)
    before = frame.copy(deep=True)
    assert _validate_frame(filename, frame).passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
@pytest.mark.parametrize("dtype", ["Int64", "Float64", "string"])
def test_nullable_store_domain_errors_keep_missing_values_separate(filename, dtype):
    frame = pd.concat([_frame_for_file(filename).iloc[[0]]] * 3, ignore_index=True)
    if "Date" in frame:
        frame["Date"] = pd.date_range("2015-01-01", periods=3).strftime("%Y-%m-%d")
    frame["Store"] = pd.Series([1, None, 0], dtype=dtype)
    before = frame.copy(deep=True)

    report = _validate_frame(filename, frame)

    errors = [finding for finding in report.findings if finding.severity == Severity.ERROR]
    assert [(finding.code, finding.context["count"]) for finding in errors] == [
        ("MISSING_REQUIRED_VALUE", 1),
        ("INVALID_STORE_ID", 1),
    ]
    assert not report.passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
@pytest.mark.parametrize("dtype", ["Int64", "Float64", "string", "boolean"])
def test_nullable_weekday_domain_errors_preserve_optional_nulls(filename, dtype):
    frame = pd.concat([_frame_for_file(filename).iloc[[0]]] * 3, ignore_index=True)
    frame["Date"] = pd.date_range("2015-01-01", periods=3).strftime("%Y-%m-%d")
    values = [True, None, False] if dtype == "boolean" else [1, None, 8]
    frame["DayOfWeek"] = pd.Series(values, dtype=dtype)
    before = frame.copy(deep=True)

    report = _validate_frame(filename, frame)

    errors = [finding for finding in report.findings if finding.severity == Severity.ERROR]
    assert [(finding.code, finding.context["count"]) for finding in errors] == [
        ("INVALID_DAY_OF_WEEK", 2 if dtype == "boolean" else 1)
    ]
    assert report.missingness[filename]["DayOfWeek"]["count"] == 1
    assert not report.passed
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize(
    "filename, column, values, expected_code, expected_count",
    [
        (
            "train.csv",
            "Store",
            [2, 3.0, 0, 1.5, np.bool_(True), None, "bad"],
            "INVALID_STORE_ID",
            4,
        ),
        ("test.csv", "Store", [2, 3.0, 0, 1.5, np.bool_(True), None, "bad"], "INVALID_STORE_ID", 4),
        (
            "store.csv",
            "Store",
            [2, 3.0, 0, 1.5, np.bool_(True), None, "bad"],
            "INVALID_STORE_ID",
            4,
        ),
        ("train.csv", "DayOfWeek", [1, 7, 0, 8, 1.5, True, None, "bad"], "INVALID_DAY_OF_WEEK", 5),
        ("test.csv", "DayOfWeek", [1, 7, 0, 8, 1.5, True, None, "bad"], "INVALID_DAY_OF_WEEK", 5),
    ],
)
def test_mixed_original_values_have_independent_expected_counts_and_deterministic_json(
    filename, column, values, expected_code, expected_count, tmp_path
):
    frame = pd.concat([_frame_for_file(filename).iloc[[0]]] * len(values), ignore_index=True)
    if "Date" in frame:
        frame["Date"] = pd.date_range("2015-01-01", periods=len(frame)).strftime("%Y-%m-%d")
    frame[column] = pd.Series(values, dtype=object)
    before = frame.copy(deep=True)
    report = _validate_frame(filename, frame)
    finding = next(item for item in report.findings if item.code == expected_code)
    assert finding.severity == Severity.ERROR
    assert finding.context["count"] == expected_count
    assert finding.context["file"] == filename
    assert finding.context["column"] == column
    assert not report.passed
    assert report.to_dict() == _validate_frame(filename, frame).to_dict()
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    report.write_json(first)
    report.write_json(second)
    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL"
    assert set(payload) == {
        "status",
        "data_dir",
        "finding_counts",
        "findings",
        "files",
        "missingness",
        "date_ranges",
        "observed_values",
        "numeric_summaries",
        "join_integrity",
        "cross_tabs",
    }
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
def test_optional_weekday_column_can_remain_absent(tmp_path, filename):
    rows = _train_rows() if filename == "train.csv" else _test_rows()
    for row in rows:
        del row["DayOfWeek"]
    overrides = {"train" if filename == "train.csv" else "test": rows}
    report = validate_dataset(_write_fixture(tmp_path / "synthetic", **overrides))
    assert report.passed
    assert "MISSING_REQUIRED_COLUMNS" not in _codes(report, Severity.ERROR)


@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
def test_store_column_remains_required(tmp_path, filename):
    rows = {"train.csv": _train_rows, "test.csv": _test_rows, "store.csv": _store_rows}[filename]()
    for row in rows:
        del row["Store"]
    override = {"train.csv": "train", "test.csv": "test", "store.csv": "stores"}[filename]
    report = validate_dataset(_write_fixture(tmp_path / "synthetic", **{override: rows}))
    finding = next(item for item in report.findings if item.code == "MISSING_REQUIRED_COLUMNS")
    assert finding.context == {"file": filename, "columns": ["Store"]}
    assert not report.passed


def test_fixture_csv_domains_and_cli_failure_preserve_join_and_report_contracts(tmp_path, capsys):
    train, test, stores = _train_rows(), _test_rows(), _store_rows()
    for row in [*train, *test, *stores]:
        row["Store"] = 0
    for row in [*train, *test]:
        row["DayOfWeek"] = 99
    directory = _write_fixture(tmp_path / "synthetic", train=train, test=test, stores=stores)
    before = {path.name: path.read_bytes() for path in directory.iterdir()}
    output = tmp_path / "report.json"
    assert validation.cli_main(["--data-dir", str(directory), "--report", str(output)]) == 1
    assert "Validation FAIL" in capsys.readouterr().out
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL"
    assert payload["finding_counts"]["ERROR"] == 5
    domains = [
        item
        for item in payload["findings"]
        if item["code"] in {"INVALID_STORE_ID", "INVALID_DAY_OF_WEEK"}
    ]
    assert {
        (item["code"], item["context"]["file"], item["context"]["count"]) for item in domains
    } == {
        ("INVALID_STORE_ID", "train.csv", 2),
        ("INVALID_STORE_ID", "test.csv", 1),
        ("INVALID_STORE_ID", "store.csv", 1),
        ("INVALID_DAY_OF_WEEK", "train.csv", 2),
        ("INVALID_DAY_OF_WEEK", "test.csv", 1),
    }
    assert payload["join_integrity"]["train.csv"]["row_count_preserved"] is True
    assert payload["join_integrity"]["test.csv"]["row_count_preserved"] is True
    assert before == {path.name: path.read_bytes() for path in directory.iterdir()}


@pytest.mark.parametrize(
    "filename, column, code",
    [
        ("train.csv", "Store", "INVALID_STORE_ID"),
        ("test.csv", "Store", "INVALID_STORE_ID"),
        ("store.csv", "Store", "INVALID_STORE_ID"),
        ("train.csv", "DayOfWeek", "INVALID_DAY_OF_WEEK"),
        ("test.csv", "DayOfWeek", "INVALID_DAY_OF_WEEK"),
    ],
)
@pytest.mark.parametrize(
    "value", ["1.0000000000000000000000000001", "0.99999999999999999", "7.00000000000000001"]
)
def test_csv_inference_cannot_hide_fractional_source_identities(
    tmp_path, filename, column, code, value
):
    rows = {"train.csv": _train_rows, "test.csv": _test_rows, "store.csv": _store_rows}[filename]()
    rows[0][column] = value
    override = {"train.csv": "train", "test.csv": "test", "store.csv": "stores"}[filename]
    directory = _write_fixture(tmp_path / "synthetic", **{override: rows})
    before = {path.name: path.read_bytes() for path in directory.iterdir()}
    inferred = pd.read_csv(directory / filename)
    assert float(inferred.loc[0, column]).is_integer()

    report = validate_dataset(directory)

    findings = [finding for finding in report.findings if finding.code == code]
    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].context["file"] == filename
    assert findings[0].context["column"] == column
    assert findings[0].context["count"] == 1
    assert not report.passed
    assert report.files[filename]["dtypes"] == {
        name: str(dtype) for name, dtype in inferred.dtypes.items()
    }
    assert before == {path.name: path.read_bytes() for path in directory.iterdir()}


@pytest.mark.parametrize("value", [1, 1.0, "1.0", "1e0", 2**53 + 1])
def test_valid_csv_identities_keep_inferred_dtypes_and_join_cardinality(tmp_path, value):
    train, test, stores = _train_rows(), _test_rows(), _store_rows()
    for row in [*train, *test, *stores]:
        row["Store"] = value
    for row in [*train, *test]:
        row["DayOfWeek"] = "7.0"
    directory = _write_fixture(tmp_path / "synthetic", train=train, test=test, stores=stores)

    report = validate_dataset(directory)

    assert report.passed
    assert report.finding_counts["ERROR"] == 0
    for filename in ("train.csv", "test.csv", "store.csv"):
        inferred = pd.read_csv(directory / filename)
        assert report.files[filename]["dtypes"] == {
            column: str(dtype) for column, dtype in inferred.dtypes.items()
        }
    for filename in ("train.csv", "test.csv"):
        assert report.join_integrity[filename]["row_count_preserved"] is True


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
def test_csv_missing_weekday_remains_information_only(tmp_path, filename):
    rows = _train_rows() if filename == "train.csv" else _test_rows()
    rows[0]["DayOfWeek"] = None
    override = "train" if filename == "train.csv" else "test"
    report = validate_dataset(_write_fixture(tmp_path / "synthetic", **{override: rows}))

    assert report.passed
    assert report.finding_counts["ERROR"] == 0
    assert report.missingness[filename]["DayOfWeek"]["count"] == 1


def test_missing_future_open_retains_warning_and_null(tmp_path):
    test = _test_rows()
    test[0]["Open"] = None
    report = validate_dataset(_write_fixture(tmp_path / "synthetic", test=test))
    assert report.passed
    assert _codes(report, Severity.WARNING) == {"MISSING_FUTURE_OPEN"}
    assert report.missingness["test.csv"]["Open"]["count"] == 1


@pytest.mark.parametrize("filename", ["train.csv", "test.csv"])
def test_duplicate_source_keys_keep_existing_error_counts_and_join_cardinality(tmp_path, filename):
    rows = _train_rows() if filename == "train.csv" else _test_rows()
    duplicate = rows[0].copy()
    if filename == "test.csv":
        duplicate["Id"] = 2
    rows.append(duplicate)
    overrides = {"train" if filename == "train.csv" else "test": rows}
    report = validate_dataset(_write_fixture(tmp_path / "synthetic", **overrides))
    errors = [finding for finding in report.findings if finding.severity == Severity.ERROR]
    assert [(finding.code, finding.context) for finding in errors] == [
        ("DUPLICATE_STORE_DATE", {"file": filename, "rows": 2})
    ]
    assert not report.passed
    assert report.join_integrity[filename]["row_count_preserved"] is True


@pytest.mark.parametrize("filename", ["train.csv", "test.csv", "store.csv"])
def test_unrelated_nonnegative_measurements_keep_fractional_values_valid(filename):
    frame = _frame_for_file(filename)
    if filename == "train.csv":
        frame["Sales"], frame["Customers"] = 10.5, 2.5
    elif filename == "store.csv":
        frame["CompetitionDistance"] = 10.5
    before = frame.copy(deep=True)
    assert _validate_frame(filename, frame).passed
    pd.testing.assert_frame_equal(frame, before)


def test_valid_minimum_dataset_passes(tmp_path: Path) -> None:
    report = validate_dataset(_write_fixture(tmp_path / "raw"))

    assert report.passed
    assert report.join_integrity["train.csv"]["row_count_preserved"] is True
    assert report.join_integrity["test.csv"]["row_count_preserved"] is True
    assert "UNIQUE_STORE_DATE" in _codes(report, Severity.INFO)
    assert "CUSTOMERS_FUTURE_UNAVAILABLE" in _codes(report, Severity.INFO)


def test_missing_required_file_fails(tmp_path: Path) -> None:
    data_dir = _write_fixture(tmp_path / "raw")
    (data_dir / "train.csv").unlink()

    report = validate_dataset(data_dir)

    assert not report.passed
    assert "REQUIRED_FILE_MISSING" in _codes(report, Severity.ERROR)


def test_duplicate_store_date_fails(tmp_path: Path) -> None:
    rows = _train_rows()
    rows.append(rows[0].copy())

    report = validate_dataset(_write_fixture(tmp_path / "raw", train=rows))

    assert "DUPLICATE_STORE_DATE" in _codes(report, Severity.ERROR)


def test_duplicate_store_metadata_fails_join_cardinality(tmp_path: Path) -> None:
    stores = _store_rows() * 2

    report = validate_dataset(_write_fixture(tmp_path / "raw", stores=stores))

    errors = _codes(report, Severity.ERROR)
    assert "DUPLICATE_STORE_METADATA" in errors
    assert "INVALID_JOIN_CARDINALITY" in errors


def test_unmatched_store_fails(tmp_path: Path) -> None:
    rows = _train_rows()
    rows[0] = rows[0] | {"Store": 2}

    report = validate_dataset(_write_fixture(tmp_path / "raw", train=rows))

    assert "MISSING_STORE_METADATA" in _codes(report, Severity.ERROR)


def test_invalid_date_and_open_value_fail(tmp_path: Path) -> None:
    rows = _train_rows()
    rows[0] = rows[0] | {"Date": "2015-99-99", "Open": 2}

    report = validate_dataset(_write_fixture(tmp_path / "raw", train=rows))

    errors = _codes(report, Severity.ERROR)
    assert "INVALID_DATE" in errors
    assert "INVALID_BINARY_VALUE" in errors


def test_schema_reports_missing_and_unexpected_columns(tmp_path: Path) -> None:
    rows = _train_rows()
    for row in rows:
        row.pop("Sales")
        row["Mystery"] = "value"

    report = validate_dataset(_write_fixture(tmp_path / "raw", train=rows))

    assert "MISSING_REQUIRED_COLUMNS" in _codes(report, Severity.ERROR)
    assert "UNEXPECTED_COLUMNS" in _codes(report, Severity.INFO)


def test_negative_and_non_finite_measurements_fail(tmp_path: Path) -> None:
    rows = _train_rows()
    rows[0] = rows[0] | {"Sales": -1, "Customers": float("inf")}

    report = validate_dataset(_write_fixture(tmp_path / "raw", train=rows))

    errors = _codes(report, Severity.ERROR)
    assert "NEGATIVE_VALUE" in errors
    assert "NON_FINITE_VALUE" in errors


def test_closed_store_inconsistency_warns_without_mutating_raw_files(tmp_path: Path) -> None:
    rows = _train_rows()
    rows[0] = rows[0] | {"Open": 0, "Sales": 100, "Customers": 10}
    data_dir = _write_fixture(tmp_path / "raw", train=rows)
    hashes_before = {path.name: sha256_file(path) for path in data_dir.glob("*.csv")}

    report = validate_dataset(data_dir)

    assert report.passed
    warnings = _codes(report, Severity.WARNING)
    assert "CLOSED_WITH_POSITIVE_SALES" in warnings
    assert "CLOSED_WITH_POSITIVE_CUSTOMERS" in warnings
    assert hashes_before == {path.name: sha256_file(path) for path in data_dir.glob("*.csv")}


def test_promo2_missingness_distinguishes_structural_and_suspicious(tmp_path: Path) -> None:
    stores = _store_rows()
    stores.append(
        stores[0]
        | {
            "Store": 2,
            "Promo2": 1,
            "Promo2SinceWeek": None,
            "Promo2SinceYear": None,
            "PromoInterval": None,
        }
    )

    report = validate_dataset(_write_fixture(tmp_path / "raw", stores=stores))

    assert "PROMO2_LIKELY_STRUCTURAL_MISSINGNESS" in _codes(report, Severity.INFO)
    assert "PROMO2_PARTICIPANT_MISSING_DETAILS" in _codes(report, Severity.WARNING)


def test_cli_writes_machine_readable_report_and_returns_success(tmp_path: Path) -> None:
    data_dir = _write_fixture(tmp_path / "portable fixture")
    output = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_data.py",
            "--data-dir",
            str(data_dir),
            "--report",
            str(output),
        ],
        cwd=repository_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert payload["status"] == "PASS"
    assert payload["files"]["train.csv"]["rows"] == 2
    assert "Validation PASS" in result.stdout


def test_acquisition_refuses_to_overwrite_existing_target(tmp_path: Path) -> None:
    target = tmp_path / "raw"
    target.mkdir()

    with pytest.raises(AcquisitionError, match="will not be modified"):
        acquire_official_data(target)
