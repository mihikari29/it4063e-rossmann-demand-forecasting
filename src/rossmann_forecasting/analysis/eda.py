"""Leakage-aware descriptive summaries and report figures for historical Rossmann Sales."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow

from rossmann_forecasting.data.paths import repository_root
from rossmann_forecasting.data.preparation import derive_test_open_resolution

METADATA_FIELDS = (
    "CompetitionDistance",
    "CompetitionOpenSinceMonth",
    "CompetitionOpenSinceYear",
    "Promo2SinceWeek",
    "Promo2SinceYear",
    "PromoInterval",
)
OPEN_ZERO_FIELDS = (
    "Store",
    "Date",
    "Sales",
    "Customers",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if pd.isna(value) if np.isscalar(value) else False:
        return None
    return value


def _require_columns(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def select_representative_stores(train: pd.DataFrame) -> pd.DataFrame:
    """Select volume, metadata-coverage, and anomaly examples by fixed rules."""

    required = {
        "Store",
        "Date",
        "Sales",
        "Open",
        "StoreType",
        "Assortment",
        "Promo2",
    }
    _require_columns(train, required, "train")
    opened = train.loc[train["Open"].eq(1)]
    store_summary = (
        opened.groupby("Store", observed=True)
        .agg(
            mean_open_sales=("Sales", "mean"),
            median_open_sales=("Sales", "median"),
            open_days=("Sales", "size"),
            first_date=("Date", "min"),
            last_date=("Date", "max"),
            StoreType=("StoreType", "first"),
            Assortment=("Assortment", "first"),
            Promo2=("Promo2", "first"),
        )
        .reset_index()
    )
    if store_summary.empty:
        raise ValueError("No Open=1 historical observations available for store selection.")

    chosen: dict[int, list[str]] = {}

    def add(row: pd.Series, reason: str) -> None:
        chosen.setdefault(int(row["Store"]), []).append(reason)

    means = store_summary["mean_open_sales"]
    for _label, quantile in (("volume_p10", 0.1), ("volume_p50", 0.5), ("volume_p90", 0.9)):
        target = means.quantile(quantile)
        candidate = (
            store_summary.assign(_distance=(means - target).abs())
            .sort_values(["_distance", "Store"], kind="stable")
            .iloc[0]
        )
        add(candidate, f"nearest store open-day mean to p{int(quantile * 100)}")

    strata = [
        (field, value)
        for field in ("StoreType", "Assortment", "Promo2")
        for value in sorted(store_summary[field].dropna().unique(), key=str)
    ]
    uncovered = set(strata)
    while uncovered:
        candidates = []
        for _, row in store_summary.iterrows():
            if int(row["Store"]) in chosen:
                continue
            covered = {(field, row[field]) for field, _ in uncovered}
            # Keep only uncovered levels this candidate actually represents.
            covered = {(field, value) for field, value in covered if (field, value) in uncovered}
            if not covered:
                continue
            stratum = next(
                ((field, value) for field, value in sorted(uncovered) if row[field] == value), None
            )
            same_stratum = store_summary.loc[
                store_summary[stratum[0]].eq(stratum[1]), "mean_open_sales"
            ]
            distance = abs(float(row["mean_open_sales"]) - float(same_stratum.median()))
            candidates.append((-len(covered), distance, int(row["Store"]), row, covered))
        if not candidates:
            break
        _, _, _, selected, covered = min(candidates, key=lambda item: item[:3])
        add(
            selected,
            "metadata-category coverage: " + ", ".join(f"{f}={v}" for f, v in sorted(covered)),
        )
        uncovered.difference_update(covered)

    gap_stores = train.loc[
        train["Date"].between("2014-06-30", "2015-01-01"), "Store"
    ].drop_duplicates()
    gap_stores = set(gap_stores) - set(
        train.loc[train["Date"].between("2014-07-01", "2014-12-31"), "Store"].drop_duplicates()
    )
    # The approved Phase 1 gap set is the 180 stores without rows in the interval.
    if gap_stores:
        gap_candidates = store_summary.loc[store_summary["Store"].isin(gap_stores)].sort_values(
            "Store"
        )
        if not gap_candidates.empty:
            add(gap_candidates.iloc[0], "shared 2014-07-01 to 2014-12-31 coverage-gap example")

    anomaly_stores = (
        train.loc[train["Open"].eq(1) & train["Sales"].eq(0), "Store"]
        .drop_duplicates()
        .sort_values()
    )
    if len(anomaly_stores):
        anomaly = store_summary.loc[store_summary["Store"].eq(anomaly_stores.iloc[0])].iloc[0]
        add(anomaly, "lowest Store ID with an Open=1, Sales=0 diagnostic row")

    results = store_summary.loc[store_summary["Store"].isin(chosen)].copy()
    results["selection_reasons"] = results["Store"].map(lambda store: "; ".join(chosen[int(store)]))
    return results.sort_values("Store").reset_index(drop=True)


def _gap_diagnostics(train: pd.DataFrame) -> dict[str, Any]:
    all_dates = pd.date_range(train["Date"].min(), train["Date"].max(), freq="D")
    observed_dates = train.groupby("Store", observed=True)["Date"].agg(
        lambda values: pd.DatetimeIndex(values.unique())
    )
    gap_map = {}
    for store, dates in observed_dates.items():
        observed = pd.DatetimeIndex(dates)
        missing = all_dates.difference(observed)
        if len(missing):
            # Coalesce missing dates into contiguous intervals without materializing fake rows.
            blocks = (missing.to_series().diff().dt.days.ne(1)).cumsum()
            intervals = [
                {
                    "start": str(block.min().date()),
                    "end": str(block.max().date()),
                    "days": len(block),
                }
                for _, block in missing.to_series().groupby(blocks)
            ]
            gap_map[int(store)] = intervals
    affected = [
        store
        for store, intervals in gap_map.items()
        if any(item["days"] >= 30 for item in intervals)
    ]
    return {
        "date_range": {"start": str(all_dates.min().date()), "end": str(all_dates.max().date())},
        "calendar_days": len(all_dates),
        "stores_with_any_missing_dates": len(gap_map),
        "stores_with_gap_at_least_30_days": len(affected),
        "affected_store_ids": affected,
        "missing_interval_counts": {
            "2014-07-01_to_2014-12-31": {
                "stores": sum(
                    any(
                        item["start"] <= "2014-07-01" and item["end"] >= "2014-12-31"
                        for item in intervals
                    )
                    for intervals in gap_map.values()
                ),
                "absent_store_days": sum(
                    next(
                        (
                            item["days"]
                            for item in intervals
                            if item["start"] == "2014-07-01" and item["end"] == "2014-12-31"
                        ),
                        0,
                    )
                    for intervals in gap_map.values()
                ),
            }
        },
        "store_intervals": {str(store): intervals for store, intervals in gap_map.items()},
    }


def _open_zero_diagnostics(train: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    rows = train.loc[train["Open"].eq(1) & train["Sales"].eq(0)].copy()
    rows = rows.sort_values(["Store", "Date"]).reset_index(drop=True)
    details = rows[list(OPEN_ZERO_FIELDS)].copy()
    context_fields = ["Open", "Sales", "Customers", "Promo", "StateHoliday", "SchoolHoliday"]
    neighbors = train[["Store", "Date", *context_fields]].copy()
    neighbors = neighbors.sort_values(["Store", "Date"])
    grouped = neighbors.groupby("Store", observed=True)
    neighbors["previous_date"] = grouped["Date"].shift()
    neighbors["next_date"] = grouped["Date"].shift(-1)
    for field in context_fields:
        neighbors[f"previous_{field.lower()}"] = grouped[field].shift()
        neighbors[f"next_{field.lower()}"] = grouped[field].shift(-1)
    neighbors["previous_is_consecutive"] = (
        neighbors["Date"].sub(neighbors["previous_date"]).dt.days.eq(1)
    )
    neighbors["next_is_consecutive"] = neighbors["next_date"].sub(neighbors["Date"]).dt.days.eq(1)
    details = details.merge(
        neighbors[
            [
                column
                for column in neighbors.columns
                if column in {"Store", "Date", "previous_date", "next_date"}
                or column.startswith("previous_")
                or column.startswith("next_")
            ]
        ],
        on=["Store", "Date"],
        validate="one_to_one",
    )
    return (
        {
            "rows": len(rows),
            "stores": int(rows["Store"].nunique()),
            "customers_zero": int(rows["Customers"].eq(0).sum()),
            "customers_positive": int(rows["Customers"].gt(0).sum()),
            "promo_counts": {str(k): int(v) for k, v in rows["Promo"].value_counts().items()},
            "state_holiday_counts": {
                str(k): int(v) for k, v in rows["StateHoliday"].astype(str).value_counts().items()
            },
            "school_holiday_counts": {
                str(k): int(v) for k, v in rows["SchoolHoliday"].value_counts().items()
            },
        },
        details,
    )


def _missingness(train: pd.DataFrame) -> dict[str, Any]:
    metadata = train.drop_duplicates("Store").set_index("Store")
    result = {}
    missing_masks = metadata[list(METADATA_FIELDS)].isna()
    for field in METADATA_FIELDS:
        stores = metadata.index[missing_masks[field]].astype(int).tolist()
        result[field] = {
            "missing_stores": len(stores),
            "percent_of_stores": float(missing_masks[field].mean() * 100),
            "store_ids": stores,
            "overlap_by_field": {
                other: int((missing_masks[field] & missing_masks[other]).sum())
                for other in METADATA_FIELDS
                if other != field
            },
        }
    promo_nonparticipants = metadata["Promo2"].eq(0)
    result["classification"] = {
        "Promo2_details": {
            "nulls_on_nonparticipants": int(
                (missing_masks["Promo2SinceWeek"] & promo_nonparticipants).sum()
            ),
            "nonparticipants": int(promo_nonparticipants.sum()),
            "participants_missing_detail": int(
                (missing_masks["Promo2SinceWeek"] & metadata["Promo2"].eq(1)).sum()
            ),
            "disposition": "structural non-participation; preserve nulls",
        },
        "competition_open_date": {
            "paired_missing_stores": int(
                (
                    missing_masks["CompetitionOpenSinceMonth"]
                    & missing_masks["CompetitionOpenSinceYear"]
                ).sum()
            ),
            "partial_pair_stores": int(
                (
                    missing_masks["CompetitionOpenSinceMonth"]
                    ^ missing_masks["CompetitionOpenSinceYear"]
                ).sum()
            ),
            "disposition": "unexplained paired absence; preserve both nulls",
        },
        "competition_distance": {"disposition": "isolated missing values; preserve nulls"},
    }
    return result


def _store_622_investigation(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[dict[str, Any], pd.DataFrame]:
    missing = test.loc[test["Store"].eq(622) & test["Open"].isna()].copy()
    history = train.loc[train["Store"].eq(622)].copy()
    weekday = history.groupby("DayOfWeek", observed=True).agg(
        observations=("Open", "size"), known_open=("Open", "sum"), known_status=("Open", "count")
    )
    weekday["open_rate_when_known"] = weekday["known_open"] / weekday["known_status"]
    resolution = derive_test_open_resolution(train, test)
    context_rows = []
    predictors = ["DayOfWeek", "Promo", "StateHoliday", "SchoolHoliday"]
    for _, target in missing.iterrows():
        resolved = resolution.loc[resolution["Date"].eq(target["Date"])].iloc[0]
        match = history
        for column in predictors:
            match = match.loc[match[column].eq(target[column])]
        known = match["Open"].dropna()
        context_rows.append(
            {
                **{field: target[field] for field in ["Store", "Date", *predictors]},
                "matching_historical_rows": len(match),
                "matching_known_open_rows": int(known.eq(1).sum()),
                "matching_known_closed_rows": int(known.eq(0).sum()),
                "matching_open_rate": float(known.mean()) if len(known) else None,
                "Open_resolved": _jsonable(resolved["Open_resolved"]),
                "resolution_method": resolved["Open_resolution_method"],
                "resolution_uncertain": bool(resolved["resolution_uncertain"]),
                "support_resolves_missing_open": (
                    resolved["Open_resolution_method"] == "historical_exact_context_consensus"
                ),
            }
        )
    investigation = pd.DataFrame(context_rows)
    return (
        {
            "missing_rows": len(missing),
            "store_ids": sorted(missing["Store"].unique().astype(int).tolist()),
            "historical_rows": len(history),
            "weekday_history": weekday.reset_index().to_dict("records"),
            "exact_known_covariate_matches": investigation.to_dict("records"),
            "disposition": (
                "preserve Open as missing; historical associations do not establish an "
                "independent deterministic schedule rule"
            ),
        },
        investigation,
    )


def _representative_acf(train: pd.DataFrame, representatives: pd.DataFrame) -> dict[str, Any]:
    diagnostics = {}
    for store in representatives["Store"].astype(int):
        series = train.loc[train["Store"].eq(store), ["Date", "Sales"]].sort_values("Date")
        series = series.set_index("Date")["Sales"]
        # ACF is calculated only on the longest contiguous observed daily segment.
        groups = series.index.to_series().diff().dt.days.ne(1).cumsum()
        segments = [part for _, part in series.groupby(groups)]
        if not segments:
            continue
        segment = max(segments, key=len)
        if len(segment) < 56:
            continue
        diagnostics[str(store)] = {
            "segment_start": str(segment.index.min().date()),
            "segment_end": str(segment.index.max().date()),
            "n_days": len(segment),
            "acf_lags_1_to_28": {
                str(lag): float(segment.autocorr(lag=lag)) for lag in range(1, 29)
            },
        }
    return diagnostics


def _summary(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    _require_columns(train, {"Store", "Date", "Sales", "Customers", "Open", "Promo"}, "train")
    _require_columns(test, {"Store", "Date", "Open", "Promo"}, "test")
    opened = train.loc[train["Open"].eq(1)]
    by_store = (
        opened.groupby("Store", observed=True)
        .agg(
            mean_sales=("Sales", "mean"),
            median_sales=("Sales", "median"),
            p10_sales=("Sales", lambda x: x.quantile(0.10)),
            p90_sales=("Sales", lambda x: x.quantile(0.90)),
            std_sales=("Sales", "std"),
            open_days=("Sales", "size"),
            StoreType=("StoreType", "first"),
            Assortment=("Assortment", "first"),
            Promo2=("Promo2", "first"),
            CompetitionDistance=("CompetitionDistance", "first"),
        )
        .reset_index()
    )
    daily = (
        train.groupby("Date", observed=True)
        .agg(
            sales_total=("Sales", "sum"),
            sales_median=("Sales", "median"),
            observed_stores=("Store", "nunique"),
            open_rows=("Open", lambda x: int(x.eq(1).sum())),
        )
        .reset_index()
    )
    weekday = (
        opened.groupby("DayOfWeek", observed=True)
        .agg(
            rows=("Sales", "size"),
            stores=("Store", "nunique"),
            mean=("Sales", "mean"),
            median=("Sales", "median"),
            p10=("Sales", lambda x: x.quantile(0.10)),
            p90=("Sales", lambda x: x.quantile(0.90)),
        )
        .reindex(range(1, 8))
        .rename_axis("DayOfWeek")
        .reset_index()
    )
    monthly = (
        opened.assign(Year=opened["Date"].dt.year, Month=opened["Date"].dt.month)
        .groupby(["Year", "Month"], observed=True)
        .agg(
            rows=("Sales", "size"),
            median_sales=("Sales", "median"),
            mean_sales=("Sales", "mean"),
            store_count=("Store", "nunique"),
        )
        .reset_index()
    )
    promo_store = opened.groupby(["Store", "Promo"], observed=True)["Sales"].mean().unstack("Promo")
    promo_store = promo_store.rename(columns={0: "Promo=0", 1: "Promo=1"}).dropna().reset_index()
    holiday = (
        opened.groupby(["StateHoliday", "SchoolHoliday"], observed=True)
        .agg(rows=("Sales", "size"), stores=("Store", "nunique"), median_sales=("Sales", "median"))
        .reset_index()
    )
    store_attributes = (
        by_store.groupby(["StoreType", "Assortment"], observed=True)
        .agg(
            stores=("Store", "nunique"),
            median_store_mean_sales=("mean_sales", "median"),
            median_open_days=("open_days", "median"),
        )
        .reset_index()
    )
    ranked = by_store.sort_values("Store")["mean_sales"].rank(method="first", pct=True)
    by_store["volume_segment"] = np.select(
        [ranked <= 1 / 3, ranked <= 2 / 3], ["low", "middle"], default="high"
    )
    volume_segments = (
        by_store.groupby("volume_segment", observed=True)
        .agg(
            stores=("Store", "nunique"),
            median_store_mean_sales=("mean_sales", "median"),
            median_store_median_sales=("median_sales", "median"),
            median_open_days=("open_days", "median"),
        )
        .reindex(["low", "middle", "high"])
        .reset_index()
    )
    promo_type_store = (
        opened.groupby(["Store", "StoreType", "Promo"], observed=True)["Sales"]
        .mean()
        .rename("store_mean_sales")
        .reset_index()
    )
    promo_by_type = (
        promo_type_store.groupby(["StoreType", "Promo"], observed=True)
        .agg(
            stores=("Store", "nunique"),
            median_store_mean_sales=("store_mean_sales", "median"),
            mean_store_mean_sales=("store_mean_sales", "mean"),
        )
        .reset_index()
    )
    chronological = train.sort_values(["Store", "Date"]).copy()
    previous_date = chronological.groupby("Store", observed=True)["Date"].shift()
    previous_open = chronological.groupby("Store", observed=True)["Open"].shift()
    adjacent = chronological["Date"].sub(previous_date).dt.days.eq(1) & previous_open.notna()
    transitions = pd.crosstab(
        previous_open.loc[adjacent].astype(int),
        chronological.loc[adjacent, "Open"].astype(int),
        rownames=["previous_open"],
        colnames=["current_open"],
    )
    extremes = pd.concat(
        [opened.nlargest(10, "Sales"), opened.loc[opened["Sales"].gt(0)].nsmallest(10, "Sales")]
    )[["Store", "Date", "Sales", "Customers", "Open", "Promo", "StateHoliday", "SchoolHoliday"]]
    extremes = extremes.drop_duplicates(["Store", "Date"]).sort_values("Sales", ascending=False)
    neighbor_context = train[["Store", "Date", "Sales"]].sort_values(["Store", "Date"]).copy()
    grouped_neighbors = neighbor_context.groupby("Store", observed=True)
    neighbor_context["previous_date"] = grouped_neighbors["Date"].shift()
    neighbor_context["previous_sales"] = grouped_neighbors["Sales"].shift()
    neighbor_context["next_date"] = grouped_neighbors["Date"].shift(-1)
    neighbor_context["next_sales"] = grouped_neighbors["Sales"].shift(-1)
    extremes = extremes.merge(
        neighbor_context[
            ["Store", "Date", "previous_date", "previous_sales", "next_date", "next_sales"]
        ],
        on=["Store", "Date"],
        validate="one_to_one",
    )
    competition = by_store[["Store", "mean_sales", "CompetitionDistance"]].dropna()
    promo2 = (
        by_store.groupby("Promo2", observed=True)
        .agg(
            stores=("Store", "nunique"),
            mean_store_sales=("mean_sales", "mean"),
            median_store_sales=("mean_sales", "median"),
        )
        .reset_index()
    )
    representatives = select_representative_stores(train)
    open_zero, open_zero_rows = _open_zero_diagnostics(train)
    missingness = _missingness(train)
    store_622, store_622_rows = _store_622_investigation(train, test)
    test_stores = set(test["Store"].unique().astype(int))
    train_stores = set(train["Store"].unique().astype(int))
    metadata_stores = set(train.drop_duplicates("Store")["Store"].astype(int))
    gaps = _gap_diagnostics(train)
    summary = {
        "train": {
            "rows": len(train),
            "stores": int(train["Store"].nunique()),
            "start": str(train["Date"].min().date()),
            "end": str(train["Date"].max().date()),
            "open_rows": len(opened),
            "closed_rows": int(train["Open"].eq(0).sum()),
            "sales_all_rows": train["Sales"]
            .describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.99])
            .to_dict(),
            "sales_open_rows": opened["Sales"]
            .describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.99])
            .to_dict(),
            "sales_zero_rows": int(train["Sales"].eq(0).sum()),
            "open_zero_rows": open_zero,
        },
        "test": {
            "rows": len(test),
            "stores": int(test["Store"].nunique()),
            "start": str(test["Date"].min().date()),
            "end": str(test["Date"].max().date()),
            "missing_open_rows": int(test["Open"].isna().sum()),
            "missing_open_stores": sorted(
                test.loc[test["Open"].isna(), "Store"].unique().astype(int).tolist()
            ),
        },
        "metadata_coverage": {
            "train_stores": len(train_stores),
            "test_stores": len(test_stores),
            "metadata_stores": len(metadata_stores),
            "test_stores_without_metadata": sorted(test_stores - metadata_stores),
            "metadata_stores_not_in_test": sorted(metadata_stores - test_stores),
        },
        "date_coverage": gaps,
        "metadata_missingness": missingness,
        "store_622_open_investigation": store_622,
        "representative_stores": representatives.to_dict("records"),
        "representative_acf": _representative_acf(train, representatives),
        "daily_sales_and_coverage": daily.to_dict("records"),
        "weekday_open_sales": weekday.to_dict("records"),
        "monthly_open_sales": monthly.to_dict("records"),
        "holiday_open_sales": holiday.astype(object)
        .where(pd.notna(holiday), None)
        .to_dict("records"),
        "store_attribute_summary": store_attributes.to_dict("records"),
        "store_volume_segments": volume_segments.astype(object)
        .where(pd.notna(volume_segments), None)
        .to_dict("records"),
        "promotion_by_store_type": promo_by_type.to_dict("records"),
        "consecutive_observed_open_transitions": {
            f"{int(previous)}_to_{int(current)}": int(count)
            for previous, row in transitions.iterrows()
            for current, count in row.items()
        },
        "sales_extremes_context": extremes.to_dict("records"),
        "promo_store_means": promo_store.to_dict("records"),
        "competition_by_store": competition.to_dict("records"),
        "promo2_store_summary": promo2.to_dict("records"),
        "store_level_open_sales_summary": by_store.to_dict("records"),
    }
    tables = {
        "store_open_zero_context.csv": open_zero_rows,
        "store_622_open_context.csv": store_622_rows,
        "store_level_open_sales.csv": by_store,
        "daily_sales_coverage.csv": daily,
        "weekday_open_sales.csv": weekday,
        "monthly_open_sales.csv": monthly,
        "representative_stores.csv": representatives,
        "store_attribute_summary.csv": store_attributes,
        "store_volume_segments.csv": volume_segments,
        "promotion_by_store_type.csv": promo_by_type,
        "sales_extremes_context.csv": extremes,
    }
    return summary, tables


def _save_figures(train: pd.DataFrame, summary: dict[str, Any], report_dir: Path) -> list[str]:
    figures = report_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    saved = []
    opened = train.loc[train["Open"].eq(1)]

    def finish(name: str, title: str) -> None:
        plt.suptitle(title, fontsize=12)
        plt.tight_layout()
        plt.savefig(figures / name, dpi=150, bbox_inches="tight")
        plt.close()
        saved.append(name)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(train["Sales"], bins=80, alpha=0.5, label=f"All rows (n={len(train):,})")
    ax.hist(opened["Sales"], bins=80, alpha=0.5, label=f"Open=1 (n={len(opened):,})")
    ax.set(
        xlabel="Sales turnover (monetary value)",
        ylabel="Store-day rows",
        xlim=(0, train["Sales"].quantile(0.995)),
    )
    ax.legend()
    finish("sales_distribution.png", "Rossmann historical Sales distribution")

    daily = pd.DataFrame(summary["daily_sales_and_coverage"])
    daily["Date"] = pd.to_datetime(daily["Date"])
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(daily["Date"], daily["sales_total"], linewidth=0.8, label="Daily observed Sales total")
    ax.set_ylabel("Sales turnover (monetary value)")
    ax2 = ax.twinx()
    ax2.plot(
        daily["Date"],
        daily["observed_stores"],
        color="darkorange",
        alpha=0.7,
        linewidth=0.8,
        label="Stores observed",
    )
    ax2.set_ylabel("Observed stores")
    finish("daily_sales_coverage.png", "Daily turnover and changing source-row coverage")

    weekday = pd.DataFrame(summary["weekday_open_sales"])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(
        weekday["DayOfWeek"],
        weekday["median"],
        yerr=[weekday["median"] - weekday["p10"], weekday["p90"] - weekday["median"]],
        fmt="o",
    )
    ax.set(
        xlabel="Source DayOfWeek code",
        ylabel="Open-day Sales turnover",
        xticks=weekday["DayOfWeek"],
    )
    finish("weekday_sales_profile.png", "Open-day Sales by source weekday code (p10–median–p90)")

    monthly = pd.DataFrame(summary["monthly_open_sales"])
    fig, ax = plt.subplots(figsize=(8, 4))
    for year, rows in monthly.groupby("Year"):
        ax.plot(rows["Month"], rows["median_sales"], marker="o", label=str(year))
    ax.set(xlabel="Calendar month", ylabel="Median open-day Sales turnover", xticks=range(1, 13))
    ax.legend(title="Year")
    finish("monthly_sales_by_year.png", "Monthly median Sales on observed open days")

    by_store = pd.DataFrame(summary["store_level_open_sales_summary"])
    fig, ax = plt.subplots(figsize=(7, 4))
    groups = [
        by_store.loc[by_store["StoreType"].eq(value), "mean_sales"]
        for value in sorted(by_store["StoreType"].unique())
    ]
    ax.boxplot(groups, tick_labels=sorted(by_store["StoreType"].unique()), showfliers=False)
    ax.set(xlabel="StoreType code", ylabel="Per-store mean open-day Sales turnover")
    finish("store_type_volume.png", "Store-level open-day mean Sales by StoreType")

    fig, ax = plt.subplots(figsize=(7, 4))
    assortment_values = sorted(by_store["Assortment"].unique())
    assortment_groups = [
        by_store.loc[by_store["Assortment"].eq(value), "mean_sales"] for value in assortment_values
    ]
    ax.boxplot(assortment_groups, tick_labels=assortment_values, showfliers=False)
    ax.set(xlabel="Assortment code", ylabel="Per-store mean open-day Sales turnover")
    finish("assortment_volume.png", "Store-level open-day mean Sales by Assortment")

    fig, ax = plt.subplots(figsize=(7, 4))
    available = [
        by_store.loc[by_store["Promo2"].eq(value), "mean_sales"]
        for value in sorted(by_store["Promo2"].unique())
    ]
    ax.boxplot(
        available,
        tick_labels=[f"Promo2={v}" for v in sorted(by_store["Promo2"].unique())],
        showfliers=False,
    )
    ax.set(ylabel="Per-store mean open-day Sales turnover")
    finish("promo2_volume.png", "Store-level open-day Sales by Promo2 participation")

    competition = pd.DataFrame(summary["competition_by_store"])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(competition["CompetitionDistance"], competition["mean_sales"], s=12, alpha=0.45)
    ax.set(
        xlabel="Source CompetitionDistance (unit not asserted)",
        ylabel="Per-store mean open-day Sales turnover",
    )
    finish("competition_distance.png", "Store-level turnover and available competition distance")

    fig, ax = plt.subplots(figsize=(9, 4))
    for promo, rows in opened.groupby("Promo", observed=True):
        # Store-aware summaries: equal weight for each store within each Promo group.
        store_means = rows.groupby("Store", observed=True)["Sales"].mean()
        ax.boxplot([store_means], positions=[int(promo) + 1], widths=0.5, showfliers=False)
    ax.set(
        xlabel="Promo",
        ylabel="Per-store mean open-day Sales turnover",
        xticks=[1, 2],
        xticklabels=["Promo=0", "Promo=1"],
    )
    finish("promotion_store_means.png", "Per-store mean Sales by observed promotion status")

    representatives = pd.DataFrame(summary["representative_stores"])
    fig, ax = plt.subplots(figsize=(11, 4))
    for store in representatives["Store"].astype(int):
        history = train.loc[train["Store"].eq(store)].sort_values("Date")
        daily_sales = history.set_index("Date")["Sales"].reindex(
            pd.date_range(history["Date"].min(), history["Date"].max())
        )
        ax.plot(daily_sales.index, daily_sales, linewidth=0.7, label=f"Store {store}")
    ax.set(ylabel="Sales turnover (monetary value)", xlabel="Date")
    ax.legend(ncol=3, fontsize=7)
    finish(
        "representative_store_history.png",
        "Deterministically selected store histories; gaps shown as missing",
    )

    holidays = pd.DataFrame(summary["holiday_open_sales"])
    holidays["label"] = (
        holidays["StateHoliday"].astype(str)
        + " / SchoolHoliday="
        + holidays["SchoolHoliday"].astype(str)
    )
    fig, ax = plt.subplots(figsize=(10, 4))
    ordered = holidays.sort_values(["StateHoliday", "SchoolHoliday"])
    ax.bar(ordered["label"], ordered["median_sales"])
    ax.set(xlabel="Observed holiday codes", ylabel="Median open-day Sales turnover")
    ax.tick_params(axis="x", labelrotation=35)
    finish("holiday_sales_summary.png", "Open-day Sales by source holiday indicators")

    missingness = summary["metadata_missingness"]
    field_names = [field for field in METADATA_FIELDS]
    missing_counts = [missingness[field]["missing_stores"] for field in field_names]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(field_names, missing_counts, color="slateblue")
    ax.set(xlabel="Store metadata field", ylabel="Stores with source null")
    ax.tick_params(axis="x", labelrotation=35)
    finish("metadata_missingness.png", "Field-specific store metadata missingness")

    acf = summary["representative_acf"]
    fig, ax = plt.subplots(figsize=(9, 4))
    plotted = 0
    for store, result in acf.items():
        if plotted == 4:
            break
        values = result["acf_lags_1_to_28"]
        ax.plot(
            [int(lag) for lag in values], list(values.values()), marker=".", label=f"Store {store}"
        )
        plotted += 1
    if plotted:
        ax.axhline(0, color="black", linewidth=0.7)
        ax.set(
            xlabel="Lag (days); contiguous observed segment only", ylabel="Sales autocorrelation"
        )
        ax.legend(fontsize=8)
        finish(
            "representative_store_acf.png",
            "Descriptive ACF on longest uninterrupted store histories",
        )

    fig, ax = plt.subplots(figsize=(9, 2.8))
    timeline = pd.DataFrame(summary["daily_sales_and_coverage"])
    timeline["Date"] = pd.to_datetime(timeline["Date"])
    ax.plot(timeline["Date"], timeline["observed_stores"], color="slateblue")
    ax.set(xlabel="Date", ylabel="Stores with observed rows")
    finish("store_day_coverage.png", "Store-day coverage (180 stores share a six-month gap)")
    return saved


def run_eda(
    train_path: str | Path | None = None,
    test_path: str | Path | None = None,
    report_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Generate local summaries and descriptive figures from prepared Parquet inputs."""

    root = repository_root()
    train_file = Path(train_path) if train_path else root / "data/interim/train.parquet"
    test_file = Path(test_path) if test_path else root / "data/interim/test.parquet"
    if not train_file.is_absolute():
        train_file = root / train_file
    if not test_file.is_absolute():
        test_file = root / test_file
    destination = Path(report_dir) if report_dir else root / "reports/eda"
    if not destination.is_absolute():
        destination = root / destination
    destination.mkdir(parents=True, exist_ok=True)
    train = pd.read_parquet(train_file, engine="pyarrow")
    test = pd.read_parquet(test_file, engine="pyarrow")
    summary, tables = _summary(train, test)
    for name, frame in tables.items():
        frame.to_csv(destination / name, index=False)
    figures = _save_figures(train, summary, destination)
    preparation_manifest_path = train_file.parent / "preparation_manifest.json"
    preparation_manifest = (
        json.loads(preparation_manifest_path.read_text(encoding="utf-8"))
        if preparation_manifest_path.is_file()
        else {}
    )
    manifest = {
        "command": "rossmann-eda",
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "pyarrow_version": pyarrow.__version__,
        "matplotlib_version": matplotlib.__version__,
        "train_rows": len(train),
        "test_rows": len(test),
        "input_schema": {
            "train": {column: str(dtype) for column, dtype in train.dtypes.items()},
            "test": {column: str(dtype) for column, dtype in test.dtypes.items()},
        },
        "source_sha256": preparation_manifest.get("source_sha256"),
        "figures": figures,
        "summary": _jsonable(summary),
    }
    (destination / "eda_summary.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    return manifest


def cli_main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate descriptive Rossmann EDA summaries and figures."
    )
    parser.add_argument("--train", help="Prepared training Parquet path.")
    parser.add_argument("--test", help="Prepared future-covariate Parquet path.")
    parser.add_argument("--report-dir", help="Output directory (default: reports/eda).")
    args = parser.parse_args()
    manifest = run_eda(args.train, args.test, args.report_dir)
    brief = {
        "train_rows": manifest["train_rows"],
        "test_rows": manifest["test_rows"],
        "figures": manifest["figures"],
        "summary_path": str(
            (Path(args.report_dir) if args.report_dir else repository_root() / "reports/eda")
            / "eda_summary.json"
        ),
    }
    print(json.dumps(brief, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
