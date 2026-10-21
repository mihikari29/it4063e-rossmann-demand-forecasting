from __future__ import annotations

import csv
import io
from decimal import Decimal

import pandas as pd
import pytest

from rossmann_forecasting.data.wp1_preparation import (
    OBSERVATION_COLUMNS,
    SOURCE_COLUMNS,
    WP1PreparationError,
    build_promo_membership,
    prepare_candidate_records,
    prepare_target_observations,
)
from rossmann_forecasting.forecasting.model_selection import CANDIDATE_IDS, FORECAST_COLUMNS
from rossmann_forecasting.forecasting.validation import APPROVED_DEVELOPMENT_WINDOWS


def _source_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    cases = [
        (1, 1, 0, 1, 0),
        (1, 14, 20, 0, 1),
        (2, 1, None, 1, None),
        (2, 14, 30, None, 0),
    ]
    for window_index, window in enumerate(APPROVED_DEVELOPMENT_WINDOWS):
        for case_index, (store, horizon, sales, source_open, promo) in enumerate(cases):
            if window_index == 1 and store == 2 and horizon == 14:
                continue  # retain a sparse, unfilled observed-key population
            target = (window.forecast_origin + pd.Timedelta(days=horizon)).date().isoformat()
            rows.append(
                [
                    str(store),
                    str(pd.Timestamp(target).isoweekday()),
                    target,
                    "" if sales is None else str(sales + window_index + case_index),
                    "synthetic-customer-value-not-retained",
                    "" if source_open is None else str(source_open),
                    "" if promo is None else str(promo),
                    "0",
                    "0",
                ]
            )
    return rows


def _csv_bytes(rows: list[list[str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(SOURCE_COLUMNS)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _candidate_records(source_rows: list[list[str]]) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for index, candidate in enumerate(CANDIDATE_IDS):
        records = []
        for row in source_rows:
            store = int(row[0])
            target = pd.Timestamp(row[2])
            window = next(
                item
                for item in APPROVED_DEVELOPMENT_WINDOWS
                if item.target_start <= target <= item.target_end
            )
            horizon = int((target - window.forecast_origin).days)
            sales = None if row[3] == "" else float(row[3])
            source_open = None if row[5] == "" else float(row[5])
            available = not (
                candidate == CANDIDATE_IDS[1]
                and store == 1
                and horizon == 14
                and window.name == "validation_3"
            )
            record = {
                "Store": store,
                "forecast_origin": window.forecast_origin,
                "Date": target,
                "horizon": horizon,
                "validation_window": window.name,
                "actual_sales": sales,
                "source_open": source_open,
                FORECAST_COLUMNS[candidate]: float(100 + index + horizon) if available else None,
                "forecast_available": available,
                "primary_evaluation_eligible": available and source_open == 1 and sales is not None,
            }
            if candidate == CANDIDATE_IDS[1]:
                record["fit_failure_reason"] = None if available else "synthetic_fit_failure"
            records.append(record)
        result[candidate] = pd.DataFrame(records)
    return result


def test_source_projection_preserves_sparse_null_zero_and_promo_membership() -> None:
    rows = _source_rows()
    observations = prepare_target_observations(_csv_bytes(rows))
    assert tuple(observations.columns) == OBSERVATION_COLUMNS
    assert len(observations) == len(rows)
    assert observations.duplicated(["Store", "Date"]).sum() == 0
    assert observations["Sales"].eq(0).any()
    assert observations["Sales"].isna().any()
    assert observations["Open"].isna().any()
    assert observations["Promo"].dropna().isin([0, 1]).all()
    assert observations["Promo"].isna().any()
    # Sparse dates stay sparse; there is no Store × Date grid completion.
    assert len(observations) < observations["Store"].nunique() * observations["Date"].nunique()

    membership = build_promo_membership(observations)
    assert tuple(membership.columns) == ("Store", "forecast_origin", "Date", "Promo")
    assert len(membership) == len(observations)
    assert membership["Promo"].isna().any()
    assert membership["Promo"].dropna().isin([0, 1]).all()


def test_protected_rows_are_classified_before_other_values_and_never_emitted() -> None:
    rows = _source_rows()
    rows.append(
        ["SECRET_STORE", "bad", "2015-07-04", "PROTECTED_SALES_SENTINEL", "x", "8", "9", "x", "x"]
    )
    observations = prepare_target_observations(_csv_bytes(rows))
    assert observations["Date"].max() <= pd.Timestamp("2015-07-03")
    assert "PROTECTED_SALES_SENTINEL" not in observations.to_string()


@pytest.mark.parametrize(
    ("field", "value"),
    [(0, "0"), (3, "-1"), (5, "2"), (6, "3")],
)
def test_invalid_retained_source_values_fail_closed(field: int, value: str) -> None:
    rows = _source_rows()
    rows[0][field] = value
    with pytest.raises(WP1PreparationError):
        prepare_target_observations(_csv_bytes(rows))


def test_duplicate_source_keys_and_malformed_eligible_rows_fail_closed() -> None:
    rows = _source_rows()
    with pytest.raises(WP1PreparationError, match="duplicate"):
        prepare_target_observations(_csv_bytes([*rows, rows[0]]))
    malformed = [row.copy() for row in rows]
    malformed[0].pop()
    with pytest.raises(WP1PreparationError, match="malformed"):
        prepare_target_observations(_csv_bytes(malformed))


@pytest.mark.parametrize("horizon", [65537, -65535])
def test_original_horizons_are_rejected_before_phase7_narrowing(horizon: int) -> None:
    candidates = _candidate_records(_source_rows())
    candidates[CANDIDATE_IDS[0]].loc[0, "horizon"] = horizon
    with pytest.raises(WP1PreparationError, match="original horizons"):
        prepare_candidate_records(candidates)


@pytest.mark.parametrize("horizon", [1, 14])
def test_date_consistent_horizon_boundaries_remain_valid(horizon: int) -> None:
    candidates = _candidate_records(_source_rows())
    candidate = CANDIDATE_IDS[0]
    row_index = candidates[candidate].index[candidates[candidate]["horizon"].eq(horizon)][0]
    checked = prepare_candidate_records(candidates)
    assert int(checked[candidate].loc[row_index, "horizon"]) == horizon


def test_candidate_validation_preserves_reason_fields_without_mutating_callers() -> None:
    candidates = _candidate_records(_source_rows())
    before = {name: frame.copy(deep=True) for name, frame in candidates.items()}
    checked = prepare_candidate_records(candidates)
    pd.testing.assert_frame_equal(candidates[CANDIDATE_IDS[1]], before[CANDIDATE_IDS[1]])
    assert "fit_failure_reason" in checked[CANDIDATE_IDS[1]]
    assert checked[CANDIDATE_IDS[1]]["fit_failure_reason"].eq("synthetic_fit_failure").any()
    assert (
        checked[CANDIDATE_IDS[1]]["forecast_unavailable_reason"].eq("synthetic_fit_failure").any()
    )


def test_candidate_schema_rejects_operational_forecast_substitution() -> None:
    candidates = _candidate_records(_source_rows())
    candidates[CANDIDATE_IDS[0]]["operational_forecast"] = 0.0
    with pytest.raises(WP1PreparationError, match="schema"):
        prepare_candidate_records(candidates)


def test_candidate_mapping_must_be_exact_and_candidate_keys_match() -> None:
    candidates = _candidate_records(_source_rows())
    with pytest.raises(WP1PreparationError, match="exactly"):
        prepare_candidate_records({CANDIDATE_IDS[0]: candidates[CANDIDATE_IDS[0]]})
    candidates[CANDIDATE_IDS[2]].loc[0, "actual_sales"] = 999.0
    with pytest.raises(WP1PreparationError, match="original shared"):
        prepare_candidate_records(candidates)


@pytest.mark.parametrize("sales", [2**53, 2**53 + 1])
def test_prepared_candidate_records_preserve_large_integer_sales(sales: int) -> None:
    candidates = _candidate_records(_source_rows())
    for frame in candidates.values():
        frame["actual_sales"] = pd.Series(frame["actual_sales"].tolist(), dtype="object")
        frame.at[0, "actual_sales"] = sales

    prepared = prepare_candidate_records(candidates)

    for candidate in CANDIDATE_IDS:
        value = prepared[candidate].at[0, "actual_sales"]
        assert isinstance(value, int)
        assert value == sales
    # Preserve an ordinary float and a missing label alongside exact large integers.
    assert isinstance(prepared[CANDIDATE_IDS[0]].at[1, "actual_sales"], float)
    missing_sales = (
        prepared[CANDIDATE_IDS[0]]
        .loc[
            prepared[CANDIDATE_IDS[0]]["Store"].eq(2)
            & prepared[CANDIDATE_IDS[0]]["Date"].eq(pd.Timestamp("2015-05-23")),
            "actual_sales",
        ]
        .iloc[0]
    )
    assert pd.isna(missing_sales)


def test_original_candidate_store_domain_accepts_positive_int64_boundaries() -> None:
    candidates = _candidate_records(_source_rows())
    largest_store = 2**63 - 1
    for frame in candidates.values():
        frame["Store"] = pd.Series(frame["Store"].tolist(), dtype="object")
        frame.at[0, "Store"] = largest_store

    prepared = prepare_candidate_records(candidates)

    for candidate in CANDIDATE_IDS:
        located = prepared[candidate].loc[prepared[candidate]["Store"].eq(largest_store), "Store"]
        assert located.tolist() == [largest_store]


@pytest.mark.parametrize(
    "store",
    [Decimal("1.0000000000000001"), 1.5, "1", 2**63, None, True, float("inf")],
)
@pytest.mark.parametrize("candidate", CANDIDATE_IDS)
def test_invalid_original_store_is_rejected_before_numeric_coercion(
    candidate: str, store: object
) -> None:
    candidates = _candidate_records(_source_rows())
    frame = candidates[candidate]
    frame["Store"] = pd.Series(frame["Store"].tolist(), dtype="object")
    frame.at[0, "Store"] = store

    with pytest.raises(WP1PreparationError, match="Store"):
        prepare_candidate_records(candidates)


@pytest.mark.parametrize("source_open", [0, 1, 0.0, 1.0, None])
def test_original_candidate_open_domain_accepts_exact_binary_values(source_open: object) -> None:
    candidates = _candidate_records(_source_rows())
    for frame in candidates.values():
        frame["source_open"] = pd.Series(frame["source_open"].tolist(), dtype="object")
        frame.at[0, "source_open"] = source_open
        frame.at[0, "primary_evaluation_eligible"] = (
            source_open == 1 and frame.at[0, "actual_sales"] is not None
        )

    prepared = prepare_candidate_records(candidates)

    for candidate in CANDIDATE_IDS:
        located = (
            prepared[candidate]
            .loc[prepared[candidate]["Date"].eq(pd.Timestamp("2015-05-23")), "source_open"]
            .iloc[0]
        )
        if source_open is None:
            assert pd.isna(located)
        else:
            assert located == source_open


@pytest.mark.parametrize(
    "source_open",
    [
        Decimal("1.0000000000000001"),
        "1.0000000000000001",
        0.9999999999999999,
        float("inf"),
        2,
        True,
    ],
)
@pytest.mark.parametrize("candidate", CANDIDATE_IDS)
def test_invalid_original_candidate_open_is_rejected_before_numeric_coercion(
    candidate: str, source_open: object
) -> None:
    candidates = _candidate_records(_source_rows())
    frame = candidates[candidate]
    frame["source_open"] = pd.Series(frame["source_open"].tolist(), dtype="object")
    frame.at[0, "source_open"] = source_open

    with pytest.raises(WP1PreparationError, match="Open"):
        prepare_candidate_records(candidates)
