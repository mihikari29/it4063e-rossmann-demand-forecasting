"""Pure in-memory preparation for the WP1 synthetic-fixture milestone.

The public functions accept only caller-supplied synthetic bytes or frames. They do not open
files, load cached forecasts, authenticate provenance, or grant access to real inputs. Protected
date rows are classified from their Date field before any other row value is interpreted.
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections.abc import Mapping
from datetime import date, datetime
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd

from rossmann_forecasting.forecasting.model_selection import (
    BASE_COLUMNS,
    CANDIDATE_IDS,
    FORECAST_COLUMNS,
    KEY_COLUMNS,
    EvidenceReviewRequired,
    validate_candidate_records,
)
from rossmann_forecasting.forecasting.validation import (
    APPROVED_DEVELOPMENT_WINDOWS,
    LAST_DEVELOPMENT_DATE,
)

# Match the accepted Rossmann train.csv header. Only Store, Date, Sales, Open and Promo are
# interpreted or returned by this fixture-only projection.
SOURCE_COLUMNS = (
    "Store",
    "DayOfWeek",
    "Date",
    "Sales",
    "Customers",
    "Open",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
)
OBSERVATION_COLUMNS = ("Store", "Date", "Sales", "Open", "Promo")
PROMO_MEMBERSHIP_COLUMNS = ("Store", "forecast_origin", "Date", "Promo")
DEVELOPMENT_CUTOFF = LAST_DEVELOPMENT_DATE.date()
_INTEGER_TOKEN = re.compile(r"[+-]?[0-9]+\Z")
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1
_PREPARED_ONLY_COLUMNS = frozenset(
    {"candidate_id", "raw_model_forecast", "forecast_unavailable_reason"}
)
_WINDOWS_BY_DATE = {
    window.name: (
        window.forecast_origin.date(),
        window.target_start.date(),
        window.target_end.date(),
    )
    for window in APPROVED_DEVELOPMENT_WINDOWS
}


class WP1PreparationError(ValueError):
    """A synthetic WP1 source or candidate fixture violates the accepted contract."""


def _window_for_date(value: date) -> tuple[str, date] | None:
    for name, (origin, start, end) in _WINDOWS_BY_DATE.items():
        if start <= value <= end:
            return name, origin
    return None


def _int64(token: str, field: str, *, nullable: bool = False) -> int | None:
    if token == "" and nullable:
        return None
    if not _INTEGER_TOKEN.fullmatch(token):
        raise WP1PreparationError(f"eligible {field} value is not a base-10 integer")
    try:
        value = int(token)
    except ValueError:
        raise WP1PreparationError(f"eligible {field} value is outside signed int64") from None
    if not _INT64_MIN <= value <= _INT64_MAX:
        raise WP1PreparationError(f"eligible {field} value is outside signed int64")
    return value


def _source_values(row: list[str]) -> tuple[int, int | None, int | None, int | None]:
    store = _int64(row[0], "Store")
    sales = _int64(row[3], "Sales", nullable=True)
    source_open = _int64(row[5], "Open", nullable=True)
    promo = _int64(row[6], "Promo", nullable=True)
    assert store is not None
    if store <= 0:
        raise WP1PreparationError("eligible Store values must be positive")
    if sales is not None and sales < 0:
        raise WP1PreparationError("eligible Sales values must be non-negative")
    if source_open not in (None, 0, 1):
        raise WP1PreparationError("eligible Open values must be 0, 1, or missing")
    if promo not in (None, 0, 1):
        raise WP1PreparationError("eligible Promo values must be 0, 1, or missing")
    return store, sales, source_open, promo


def prepare_target_observations(source_csv_bytes: bytes) -> pd.DataFrame:
    """Project synthetic Rossmann-style CSV bytes to observed targets in approved windows.

    The returned frame has exactly Store, Date, Sales, Open and Promo columns, is sorted by
    Store × Date, retains sparse keys and nullable values, and never contains later-date rows.
    Errors are generic and do not include source values.
    """

    if not isinstance(source_csv_bytes, bytes):
        raise WP1PreparationError("synthetic source snapshot must be immutable bytes")
    try:
        reader = csv.reader(
            io.StringIO(source_csv_bytes.decode("utf-8", errors="strict"), newline=""),
            strict=True,
        )
        header = next(reader, None)
        if header != list(SOURCE_COLUMNS) or len(set(header or ())) != len(SOURCE_COLUMNS):
            raise WP1PreparationError("source CSV header is missing, duplicated, or unsupported")

        stores: list[int] = []
        dates: list[datetime] = []
        sales_values: list[int | None] = []
        open_values: list[int | None] = []
        promo_values: list[int | None] = []
        observed_keys: set[tuple[int, date]] = set()
        for row in reader:
            # At least the Date field must exist to classify a row. Never echo row values.
            if len(row) <= 2:
                raise WP1PreparationError(
                    "source CSV contains a record without a classifiable Date"
                )
            date_token = row[2]
            try:
                parsed_date = date.fromisoformat(date_token)
            except ValueError:
                raise WP1PreparationError("source CSV contains an invalid calendar date") from None
            if parsed_date.isoformat() != date_token:
                raise WP1PreparationError("source CSV Date must use canonical YYYY-MM-DD")

            # Classification precedes row-width and field-value checks. This keeps canary values
            # after the development cutoff out of errors and output.
            if parsed_date > DEVELOPMENT_CUTOFF:
                continue
            window = _window_for_date(parsed_date)
            if window is None:
                continue
            if len(row) != len(SOURCE_COLUMNS):
                raise WP1PreparationError("eligible source CSV contains a malformed record")

            store, sales, source_open, promo = _source_values(row)
            key = (store, parsed_date)
            if key in observed_keys:
                raise WP1PreparationError("eligible source contains duplicate Store × Date keys")
            observed_keys.add(key)
            stores.append(store)
            dates.append(datetime(parsed_date.year, parsed_date.month, parsed_date.day))
            sales_values.append(sales)
            open_values.append(source_open)
            promo_values.append(promo)
    except WP1PreparationError:
        raise
    except (UnicodeDecodeError, csv.Error, StopIteration):
        raise WP1PreparationError("source snapshot is not a valid UTF-8 CSV") from None

    if not stores:
        raise WP1PreparationError("source CSV contains no approved target observations")

    frame = pd.DataFrame(
        {
            "Store": pd.Series(stores, dtype="int64"),
            "Date": pd.Series(pd.DatetimeIndex(dates).as_unit("us")),
            "Sales": pd.Series(pd.array(sales_values, dtype="Int64")),
            "Open": pd.Series(pd.array(open_values, dtype="Int8")),
            "Promo": pd.Series(pd.array(promo_values, dtype="Int8")),
        }
    )
    return frame.sort_values(["Store", "Date"], kind="stable", ignore_index=True).loc[
        :, list(OBSERVATION_COLUMNS)
    ]


def _check_original_horizons(candidate_id: str, frame: pd.DataFrame) -> None:
    if "horizon" not in frame.columns:
        raise WP1PreparationError(f"{candidate_id} is missing its original horizon field")
    values = frame["horizon"]
    if pd.api.types.is_bool_dtype(values.dtype):
        raise WP1PreparationError(f"{candidate_id} original horizons must be integer days")
    for value in values.tolist():
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
            raise WP1PreparationError(f"{candidate_id} original horizons must be integer days")
        # Compare before any cast, including the int16 narrowing in the accepted Phase 7 validator.
        if not 1 <= int(value) <= 14:
            raise WP1PreparationError(f"{candidate_id} original horizons must be within 1..14")


def _is_missing_scalar(value: Any) -> bool:
    return (
        value is None
        or value is pd.NA
        or (isinstance(value, (float, np.floating)) and math.isnan(float(value)))
    )


def _candidate_store_key(value: Any, *, candidate_id: str) -> int:
    """Accept only original Python/NumPy integer Store keys in the positive int64 domain."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise WP1PreparationError(
            f"{candidate_id} original Store values must be positive integer keys"
        )
    result = int(value)
    if not 1 <= result <= _INT64_MAX:
        raise WP1PreparationError(
            f"{candidate_id} original Store values must be positive int64 keys"
        )
    return result


def _candidate_sales_value(value: Any, *, candidate_id: str) -> int | float | None:
    """Preserve a valid original Sales integer or float without coercing integers to float."""

    if _is_missing_scalar(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        raise WP1PreparationError(f"{candidate_id} original Sales must be numeric or missing")
    if isinstance(value, Integral):
        result = int(value)
        if not 0 <= result <= _INT64_MAX:
            raise WP1PreparationError(
                f"{candidate_id} original Sales is outside non-negative int64"
            )
        return result
    if isinstance(value, (float, np.floating)):
        try:
            if not np.isfinite(value) or value < 0:
                raise WP1PreparationError(
                    f"{candidate_id} original Sales must be finite and non-negative"
                )
            result = float(value)
        except (OverflowError, TypeError, ValueError):
            raise WP1PreparationError(
                f"{candidate_id} original Sales must be finite and non-negative"
            ) from None
        if not math.isfinite(result):
            raise WP1PreparationError(
                f"{candidate_id} original Sales must be finite and non-negative"
            )
        if isinstance(value, np.floating) and np.longdouble(result) != np.longdouble(value):
            raise WP1PreparationError(
                f"{candidate_id} original Sales cannot be represented losslessly as float64"
            )
        return result
    raise WP1PreparationError(f"{candidate_id} original Sales must be numeric or missing")


def _candidate_open_value(value: Any, *, candidate_id: str) -> int | float | None:
    """Accept exact binary Open values as integers or floats, plus a missing value."""

    if _is_missing_scalar(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        raise WP1PreparationError(f"{candidate_id} original Open must be 0, 1, or missing")
    if isinstance(value, Integral):
        result = int(value)
        if result in (0, 1):
            return result
    elif isinstance(value, (float, np.floating)):
        try:
            if np.isfinite(value) and value in (0, 1):
                return float(value)
        except (TypeError, ValueError):
            pass
    raise WP1PreparationError(f"{candidate_id} original Open must be exactly 0, 1, or missing")


def _candidate_timestamp(value: Any, *, candidate_id: str, field: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError):
        raise WP1PreparationError(f"{candidate_id} original {field} is invalid") from None
    if pd.isna(timestamp) or timestamp.tzinfo is not None or timestamp.normalize() != timestamp:
        raise WP1PreparationError(
            f"{candidate_id} original {field} must be a timezone-free midnight"
        )
    return timestamp.normalize()


def _candidate_original_labels(
    candidate_id: str, frame: pd.DataFrame
) -> dict[tuple[int, pd.Timestamp, pd.Timestamp], tuple[int | float | None, int | float | None]]:
    """Capture validated original labels by canonical key before Phase 7 can normalize them."""

    labels: dict[
        tuple[int, pd.Timestamp, pd.Timestamp], tuple[int | float | None, int | float | None]
    ] = {}
    for record in frame.to_dict(orient="records"):
        store = _candidate_store_key(record["Store"], candidate_id=candidate_id)
        key = (
            store,
            _candidate_timestamp(
                record["forecast_origin"], candidate_id=candidate_id, field="forecast_origin"
            ),
            _candidate_timestamp(record["Date"], candidate_id=candidate_id, field="Date"),
        )
        if key in labels:
            raise WP1PreparationError(f"{candidate_id} original candidate keys are duplicated")
        sales = _candidate_sales_value(record["actual_sales"], candidate_id=candidate_id)
        source_open = _candidate_open_value(record["source_open"], candidate_id=candidate_id)
        labels[key] = (sales, source_open)
    return labels


def _exact_numeric_equal(left: int | float | None, right: int | float | None) -> bool:
    """Compare numeric values exactly, with equal integer-valued floats treated as equivalent."""

    if left is None or right is None:
        return left is None and right is None
    return bool(left == right)


def _canonical_output_key(
    record: dict[str, Any], *, candidate_id: str
) -> tuple[int, pd.Timestamp, pd.Timestamp]:
    return (
        _candidate_store_key(record["Store"], candidate_id=candidate_id),
        _candidate_timestamp(
            record["forecast_origin"], candidate_id=candidate_id, field="forecast_origin"
        ),
        _candidate_timestamp(record["Date"], candidate_id=candidate_id, field="Date"),
    )


def _raw_candidate_frame(candidate_id: str, frame: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    if frame.columns.duplicated().any():
        raise WP1PreparationError(f"{candidate_id} contains duplicate candidate fields")
    present = _PREPARED_ONLY_COLUMNS.intersection(frame.columns)
    if present and present != _PREPARED_ONLY_COLUMNS:
        raise WP1PreparationError(f"{candidate_id} prepared candidate fields are incomplete")
    if not present:
        return frame.copy(deep=True), False
    if frame["candidate_id"].isna().any() or not frame["candidate_id"].eq(candidate_id).all():
        raise WP1PreparationError(f"{candidate_id} prepared candidate identity is inconsistent")
    return frame.drop(columns=list(_PREPARED_ONLY_COLUMNS)).copy(deep=True), True


def _validate_prepared_claims(
    candidate_id: str, supplied: pd.DataFrame, regenerated: pd.DataFrame
) -> None:
    claims: dict[tuple[int, pd.Timestamp, pd.Timestamp], dict[str, Any]] = {}
    for record in supplied.to_dict(orient="records"):
        key = _canonical_output_key(record, candidate_id=candidate_id)
        if key in claims:
            raise WP1PreparationError(f"{candidate_id} prepared candidate keys are duplicated")
        claims[key] = record
    generated = {
        _canonical_output_key(record, candidate_id=candidate_id): record
        for record in regenerated.to_dict(orient="records")
    }
    if set(claims) != set(generated):
        raise WP1PreparationError(f"{candidate_id} prepared candidate keys changed")
    raw_column = FORECAST_COLUMNS[candidate_id]
    for key, claim in claims.items():
        expected = generated[key]
        claimed_raw = _normalized_forecast_value(
            claim["raw_model_forecast"], candidate_id=candidate_id
        )
        expected_raw = _normalized_forecast_value(
            expected["raw_model_forecast"], candidate_id=candidate_id
        )
        if not _exact_numeric_equal(claimed_raw, expected_raw):
            raise WP1PreparationError(f"{candidate_id} prepared raw forecast is inconsistent")
        if claim["candidate_id"] != candidate_id or not _same_optional_text(
            claim["forecast_unavailable_reason"], expected["forecast_unavailable_reason"]
        ):
            raise WP1PreparationError(f"{candidate_id} prepared derived fields are inconsistent")
        if not _exact_numeric_equal(
            _normalized_forecast_value(claim[raw_column], candidate_id=candidate_id),
            _normalized_forecast_value(expected[raw_column], candidate_id=candidate_id),
        ):
            raise WP1PreparationError(f"{candidate_id} prepared raw forecast mapping changed")


def _normalized_forecast_value(value: Any, *, candidate_id: str) -> float | None:
    if _is_missing_scalar(value):
        return None
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise WP1PreparationError(f"{candidate_id} prepared raw forecast is invalid")
    try:
        normalized = float(value)
    except (OverflowError, TypeError, ValueError):
        raise WP1PreparationError(f"{candidate_id} prepared raw forecast is invalid") from None
    if not math.isfinite(normalized) or normalized < 0:
        raise WP1PreparationError(f"{candidate_id} prepared raw forecast is invalid")
    return normalized


def _same_optional_text(left: Any, right: Any) -> bool:
    return (
        (left is None or _is_missing_scalar(left))
        and (right is None or _is_missing_scalar(right))
        or isinstance(left, str)
        and isinstance(right, str)
        and left == right
    )


def _candidate_input_columns(candidate_id: str, frame: pd.DataFrame) -> tuple[str, ...]:
    if frame.columns.duplicated().any():
        raise WP1PreparationError(f"{candidate_id} contains duplicate candidate fields")
    raw = FORECAST_COLUMNS[candidate_id]
    required = (*BASE_COLUMNS, raw, "forecast_available", "primary_evaluation_eligible")
    reasons = tuple(name for name in ("unavailable_reason", "fit_failure_reason") if name in frame)
    allowed = set(required).union(reasons)
    if set(frame.columns) != allowed or len(frame.columns) != len(allowed):
        raise WP1PreparationError(f"{candidate_id} candidate schema is unsupported")
    for name in reasons:
        for value in frame[name].tolist():
            if (
                value is None
                or value is pd.NA
                or (isinstance(value, (float, np.floating)) and np.isnan(value))
            ):
                continue
            if not isinstance(value, str) or not value.strip():
                raise WP1PreparationError(
                    f"{candidate_id} original reason fields must be text or missing"
                )
    return (*required, *reasons)


def prepare_candidate_records(
    records_by_candidate: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Validate exactly the three original raw candidate records without fitting or repair.

    Store keys are original Python/NumPy integers in the positive int64 range. Sales accepts
    non-negative int64 integers, finite non-negative float64 values, and missing cells. Open
    accepts exact integer/float zero or one and missing cells. Booleans, decimal/string aliases,
    fractional Open values, and unsupported numeric representations are rejected before coercion.
    Integer-versus-float label equality means exact numeric equality (for example, 20 and 20.0);
    no tolerance or float conversion is used for integer Sales labels.

    Horizon and original label values are checked before Phase 7 normalization. Returned frames
    are newly allocated, retain original Sales/Open values in object columns, and preserve the
    accepted raw field and any original unavailable/fit-failure reason columns.
    """

    if (
        not isinstance(records_by_candidate, Mapping)
        or set(records_by_candidate) != set(CANDIDATE_IDS)
        or len(records_by_candidate) != len(CANDIDATE_IDS)
    ):
        raise WP1PreparationError(
            "candidate IDs must be exactly the three accepted Phase 7 candidates"
        )
    ordered: dict[str, pd.DataFrame] = {}
    original_labels: dict[
        str,
        dict[
            tuple[int, pd.Timestamp, pd.Timestamp],
            tuple[int | float | None, int | float | None],
        ],
    ] = {}
    prepared_inputs: dict[str, pd.DataFrame] = {}
    for candidate_id in CANDIDATE_IDS:
        frame = records_by_candidate[candidate_id]
        if not isinstance(frame, pd.DataFrame):
            raise WP1PreparationError(f"{candidate_id} records must be a DataFrame")
        raw_frame, was_prepared = _raw_candidate_frame(candidate_id, frame)
        _candidate_input_columns(candidate_id, raw_frame)
        _check_original_horizons(candidate_id, raw_frame)
        original_labels[candidate_id] = _candidate_original_labels(candidate_id, raw_frame)
        ordered[candidate_id] = raw_frame
        if was_prepared:
            prepared_inputs[candidate_id] = frame.copy(deep=True)

    reference_labels = original_labels[CANDIDATE_IDS[0]]
    for candidate_id in CANDIDATE_IDS[1:]:
        candidate_labels = original_labels[candidate_id]
        if set(candidate_labels) != set(reference_labels):
            raise WP1PreparationError("candidate original key populations differ")
        for key, reference in reference_labels.items():
            candidate = candidate_labels[key]
            if not _exact_numeric_equal(reference[0], candidate[0]) or not _exact_numeric_equal(
                reference[1], candidate[1]
            ):
                raise WP1PreparationError(
                    "candidates disagree on original shared Sales/Open labels"
                )
    try:
        validated = validate_candidate_records(ordered)
    except (EvidenceReviewRequired, TypeError, ValueError, OverflowError):
        raise WP1PreparationError("candidate records failed accepted Phase 7 validation") from None

    prepared: dict[str, pd.DataFrame] = {}
    for candidate_id in CANDIDATE_IDS:
        result = validated[candidate_id].copy(deep=True)
        labels = original_labels[candidate_id]
        result_keys = [
            _canonical_output_key(record, candidate_id=candidate_id)
            for record in result.to_dict(orient="records")
        ]
        if len(result_keys) != len(labels) or set(result_keys) != set(labels):
            raise WP1PreparationError(
                f"{candidate_id} original labels do not align to validated keys"
            )
        result["actual_sales"] = pd.Series(
            [labels[key][0] for key in result_keys], index=result.index, dtype="object"
        )
        result["source_open"] = pd.Series(
            [labels[key][1] for key in result_keys], index=result.index, dtype="object"
        )
        if candidate_id in prepared_inputs:
            _validate_prepared_claims(candidate_id, prepared_inputs[candidate_id], result)
        prepared[candidate_id] = result
    return prepared


def build_promo_membership(observations: pd.DataFrame) -> pd.DataFrame:
    """Build complete keyed retrospective Promo membership for prepared target observations."""

    if not isinstance(observations, pd.DataFrame) or observations.columns.duplicated().any():
        raise WP1PreparationError("target observations must have a unique DataFrame schema")
    if tuple(observations.columns) != OBSERVATION_COLUMNS:
        raise WP1PreparationError("target observations do not match the exact source schema")
    frame = observations.copy(deep=True)
    if frame.empty or frame[["Store", "Date"]].isna().any().any():
        raise WP1PreparationError("target observations must contain non-null observed keys")
    if frame.duplicated(["Store", "Date"]).any():
        raise WP1PreparationError("target observations contain duplicate Store × Date keys")

    membership_rows: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False, name=None):
        store, timestamp, _sales, _source_open, promo = row
        if isinstance(store, (bool, np.bool_)) or not isinstance(store, Integral):
            raise WP1PreparationError("target observation Store keys must be positive integers")
        if not 1 <= int(store) <= _INT64_MAX:
            raise WP1PreparationError("target observation Store keys must be positive integers")
        if not pd.isna(_sales) and (
            isinstance(_sales, (bool, np.bool_))
            or not isinstance(_sales, Integral)
            or not 0 <= int(_sales) <= _INT64_MAX
        ):
            raise WP1PreparationError(
                "target observation Sales must be non-negative int64 or missing"
            )
        if not pd.isna(_source_open) and (
            isinstance(_source_open, (bool, np.bool_))
            or not isinstance(_source_open, Integral)
            or int(_source_open) not in (0, 1)
        ):
            raise WP1PreparationError("target observation Open must be 0, 1, or missing")
        if not pd.isna(promo) and (
            isinstance(promo, (bool, np.bool_))
            or not isinstance(promo, Integral)
            or int(promo) not in (0, 1)
        ):
            raise WP1PreparationError("target observation Promo must be 0, 1, or missing")
        try:
            parsed_timestamp = pd.Timestamp(timestamp)
        except (TypeError, ValueError, OverflowError):
            raise WP1PreparationError(
                "target observation Date must be a timezone-free midnight"
            ) from None
        if (
            pd.isna(parsed_timestamp)
            or parsed_timestamp.tzinfo is not None
            or parsed_timestamp.normalize() != parsed_timestamp
        ):
            raise WP1PreparationError("target observation Date must be a timezone-free midnight")
        parsed_date = parsed_timestamp.date()
        window = _window_for_date(parsed_date)
        if window is None:
            raise WP1PreparationError("target observation Date is outside approved windows")
        promo_value = None if pd.isna(promo) else int(promo)
        if promo_value not in (None, 0, 1):
            raise WP1PreparationError("Promo membership values must be 0, 1, or missing")
        membership_rows.append(
            {
                "Store": int(store),
                "forecast_origin": pd.Timestamp(window[1]),
                "Date": pd.Timestamp(parsed_date),
                "Promo": promo_value,
            }
        )
    result = pd.DataFrame(membership_rows, columns=PROMO_MEMBERSHIP_COLUMNS)
    result["Store"] = result["Store"].astype("int64")
    result["forecast_origin"] = pd.to_datetime(result["forecast_origin"]).astype("datetime64[ns]")
    result["Date"] = pd.to_datetime(result["Date"]).astype("datetime64[ns]")
    result["Promo"] = pd.array(result["Promo"], dtype="Int8")
    return result.sort_values(list(KEY_COLUMNS), kind="stable", ignore_index=True)
