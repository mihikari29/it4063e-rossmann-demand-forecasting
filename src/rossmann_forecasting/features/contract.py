"""Versioned predictor names, order, and dtypes for train and inference."""

FEATURE_CONTRACT_VERSION = "phase-3-v1"

STATIC_PREDICTOR_COLUMNS = (
    "Store",
    "day_of_week",
    "week_of_year",
    "month",
    "quarter",
    "year",
    "is_weekend",
    "is_month_start",
    "is_month_end",
    "state_holiday",
    "school_holiday",
    "promo",
    "promo2",
    "is_promo2_active",
    "store_type",
    "assortment",
    "competition_distance",
    "competition_has_opened",
    "competition_age_months",
)

DYNAMIC_PREDICTOR_COLUMNS = (
    "sales_lag_1",
    "sales_lag_7",
    "sales_lag_14",
    "sales_lag_28",
    "sales_ma_7",
    "sales_ma_14",
    "sales_ma_28",
    "sales_std_7",
    "sales_std_14",
    "sales_std_28",
)

PREDICTOR_COLUMNS = STATIC_PREDICTOR_COLUMNS + DYNAMIC_PREDICTOR_COLUMNS
KEY_COLUMNS = ("Store", "Date")
HISTORY_COLUMNS = ("Store", "Date", "Sales")
COMPETITION_HELPER_COLUMNS = ("competition_open_date_proxy",)

PREDICTOR_DTYPES = {
    "Store": "int64",
    "day_of_week": "int8",
    "week_of_year": "int8",
    "month": "int8",
    "quarter": "int8",
    "year": "int16",
    "is_weekend": "bool",
    "is_month_start": "bool",
    "is_month_end": "bool",
    "state_holiday": "string[python]",
    "school_holiday": "bool",
    "promo": "bool",
    "promo2": "bool",
    "is_promo2_active": "boolean",
    "store_type": "string[python]",
    "assortment": "string[python]",
    "competition_distance": "float64",
    "competition_has_opened": "boolean",
    "competition_age_months": "Int16",
    **{name: "float64" for name in DYNAMIC_PREDICTOR_COLUMNS},
}


def predictor_schema(columns: tuple[str, ...] = PREDICTOR_COLUMNS) -> dict[str, str]:
    """Return an ordered, serializable schema for a predictor selection."""

    return {name: PREDICTOR_DTYPES[name] for name in columns}
