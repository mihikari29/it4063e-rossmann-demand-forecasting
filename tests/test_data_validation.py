from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from rossmann_forecasting.data.acquisition import (
    AcquisitionError,
    acquire_official_data,
    sha256_file,
)
from rossmann_forecasting.data.paths import repository_root
from rossmann_forecasting.data.validation import Severity, validate_dataset


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
