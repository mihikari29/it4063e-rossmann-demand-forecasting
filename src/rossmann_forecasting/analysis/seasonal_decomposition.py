"""Development-only, retrospective weekly STL diagnostics for Store × Date Sales."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels
from matplotlib.figure import Figure
from statsmodels.tsa.seasonal import STL

SOURCE_COLUMNS = ("Store", "Date", "Sales")
METHOD = "statsmodels.tsa.seasonal.STL"
PERIOD_DAYS = 7
ROBUST = True
SEASONAL_WINDOW = 7
SEASONAL_DEGREE = 1
TREND_DEGREE = 1
LOW_PASS_DEGREE = 1
SEASONAL_JUMP = 1
TREND_JUMP = 1
LOW_PASS_JUMP = 1
MIN_CONTIGUOUS_DAYS = 56
MAX_SEGMENT_DAYS = 112
MAX_ELIGIBLE_DATE = pd.Timestamp("2015-07-03")
MAX_STORES = 3
OUTPUT_SUBDIRECTORY = Path("reports/generated/seasonal_decomposition")
SOURCE_KIND = Literal["synthetic_fixture", "approved_development_only"]


@dataclass(frozen=True)
class InputProvenance:
    """Caller-supplied identity for an already-authorized in-memory input frame."""

    source_kind: SOURCE_KIND
    source_id: str
    preflight_reference: str | None = None

    def __post_init__(self) -> None:
        if self.source_kind not in {"synthetic_fixture", "approved_development_only"}:
            raise ValueError("source_kind must be synthetic_fixture or approved_development_only")
        if (
            not isinstance(self.source_id, str)
            or not self.source_id.strip()
            or "/" in self.source_id
            or "\\" in self.source_id
        ):
            raise ValueError("source_id must be a non-empty identifier, not a path")
        if self.source_kind == "approved_development_only" and not (
            self.preflight_reference and self.preflight_reference.strip()
        ):
            raise ValueError(
                "approved development inputs require a reviewed preflight reference; "
                "this metadata does not itself establish source isolation"
            )


@dataclass(frozen=True)
class DecompositionRun:
    """Components and audit status for one in-memory input frame."""

    components: pd.DataFrame
    store_status: pd.DataFrame
    input_sha256: str
    input_rows: int
    provenance: InputProvenance


def method_configuration() -> dict[str, object]:
    """Return the fixed CC-02 method configuration as JSON-compatible values."""

    return {
        "method": METHOD,
        "period_days": PERIOD_DAYS,
        "robust": ROBUST,
        "seasonal_window": SEASONAL_WINDOW,
        "trend_window": None,
        "low_pass_window": None,
        "seasonal_degree": SEASONAL_DEGREE,
        "trend_degree": TREND_DEGREE,
        "low_pass_degree": LOW_PASS_DEGREE,
        "seasonal_jump": SEASONAL_JUMP,
        "trend_jump": TREND_JUMP,
        "low_pass_jump": LOW_PASS_JUMP,
        "minimum_contiguous_days": MIN_CONTIGUOUS_DAYS,
        "maximum_segment_days": MAX_SEGMENT_DAYS,
        "maximum_eligible_date": MAX_ELIGIBLE_DATE.date().isoformat(),
        "maximum_selected_stores": MAX_STORES,
        "store_selection": "first three eligible Store IDs in ascending numeric order",
        "segment_selection": (
            "most recent eligible contiguous segment by end date, then start date; "
            "retain its most recent 112 rows"
        ),
    }


def _validate_and_copy(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    missing = sorted(set(SOURCE_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(f"input frame is missing required columns: {missing}")
    source = frame.loc[:, SOURCE_COLUMNS].copy(deep=True)
    if source.empty:
        raise ValueError("input frame must contain at least one Store × Date row")

    store_type = source["Store"].dtype
    if (
        not pd.api.types.is_integer_dtype(store_type)
        or pd.api.types.is_bool_dtype(store_type)
        or source["Store"].isna().any()
        or source["Store"].le(0).any()
    ):
        raise TypeError("Store values must be non-null positive integers")

    date_type = source["Date"].dtype
    if not pd.api.types.is_datetime64_any_dtype(date_type):
        raise TypeError("Date must use a pandas datetime dtype")
    if getattr(date_type, "tz", None) is not None:
        raise TypeError("Date must be timezone-naive calendar dates")
    if source["Date"].isna().any():
        raise ValueError("Date values cannot be null")
    if not source["Date"].eq(source["Date"].dt.normalize()).all():
        raise ValueError("Date values must be at midnight; intraday timestamps are not supported")
    if source["Date"].gt(MAX_ELIGIBLE_DATE).any():
        raise ValueError(
            f"input contains Date after the development ceiling {MAX_ELIGIBLE_DATE.date()}; "
            "future rows are rejected, not filtered"
        )

    sales_type = source["Sales"].dtype
    if (
        not pd.api.types.is_numeric_dtype(sales_type)
        or pd.api.types.is_bool_dtype(sales_type)
        or pd.api.types.is_complex_dtype(sales_type)
    ):
        raise TypeError("Sales must use a real numeric dtype; missing/non-finite values split runs")

    if source.duplicated(["Store", "Date"]).any():
        raise ValueError("input must have unique (Store, Date) keys")
    keys = pd.MultiIndex.from_frame(source[["Store", "Date"]])
    if not keys.is_monotonic_increasing:
        raise ValueError("input rows must be ordered by Store ascending and Date ascending")
    return source


def _canonical_input_sha256(frame: pd.DataFrame) -> str:
    canonical = frame.loc[:, SOURCE_COLUMNS].copy()
    payload = canonical.to_csv(
        index=False,
        date_format="%Y-%m-%d",
        float_format="%.17g",
        na_rep="",
        lineterminator="\n",
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _contiguous_finite_segments(group: pd.DataFrame) -> list[pd.DataFrame]:
    values = group["Sales"].to_numpy(dtype=np.float64, na_value=np.nan)
    dates = group["Date"].tolist()
    pieces: list[list[int]] = []
    active: list[int] = []
    previous_date: pd.Timestamp | None = None

    for position, (date, value) in enumerate(zip(dates, values, strict=True)):
        usable = bool(np.isfinite(value))
        consecutive = previous_date is not None and (date - previous_date).days == 1
        if not usable:
            if active:
                pieces.append(active)
                active = []
        elif active and not consecutive:
            pieces.append(active)
            active = [position]
        else:
            active.append(position)
        previous_date = date

    if active:
        pieces.append(active)
    return [group.iloc[positions].copy() for positions in pieces]


def _segment_order(segment: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    return (segment["Date"].iloc[-1], segment["Date"].iloc[0])


def _status_row(
    store: int,
    status: str,
    reason: str,
    segment: pd.DataFrame | None = None,
    analysis_segment: pd.DataFrame | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "Store": store,
        "status": status,
        "reason": reason,
        "contiguous_segment_start": None,
        "contiguous_segment_end": None,
        "contiguous_segment_days": 0,
        "analysis_segment_start": None,
        "analysis_segment_end": None,
        "analysis_segment_days": 0,
        **method_configuration(),
    }
    if segment is not None:
        row.update(
            contiguous_segment_start=segment["Date"].iloc[0].date().isoformat(),
            contiguous_segment_end=segment["Date"].iloc[-1].date().isoformat(),
            contiguous_segment_days=len(segment),
        )
    if analysis_segment is not None:
        row.update(
            analysis_segment_start=analysis_segment["Date"].iloc[0].date().isoformat(),
            analysis_segment_end=analysis_segment["Date"].iloc[-1].date().isoformat(),
            analysis_segment_days=len(analysis_segment),
        )
    return row


def decompose_development_sales(
    frame: pd.DataFrame,
    *,
    provenance: InputProvenance,
) -> DecompositionRun:
    """Fit fixed weekly STL on eligible, contiguous rows of a pre-authorized frame.

    The caller must obtain ``frame`` from a separately approved trusted development-only
    provider. This function performs no source or data-file I/O and rejects any row beyond the
    development ceiling. Non-finite numeric Sales values and absent dates split candidate runs;
    they are never interpolated or converted to zero.
    """

    if not isinstance(provenance, InputProvenance):
        raise TypeError("provenance must be an InputProvenance record")
    source = _validate_and_copy(frame)
    input_sha256 = _canonical_input_sha256(source)
    segments_by_store = {
        int(store): _contiguous_finite_segments(group)
        for store, group in source.groupby("Store", sort=True, observed=True)
    }
    eligible_by_store = {
        store: [segment for segment in segments if len(segment) >= MIN_CONTIGUOUS_DAYS]
        for store, segments in segments_by_store.items()
    }
    eligible_stores = sorted(store for store, segments in eligible_by_store.items() if segments)
    selected_stores = set(eligible_stores[:MAX_STORES])

    status_rows: list[dict[str, object]] = []
    component_frames: list[pd.DataFrame] = []
    for store in sorted(segments_by_store):
        eligible_segments = eligible_by_store[store]
        if not eligible_segments:
            longest = max(segments_by_store[store], key=len, default=None)
            status_rows.append(
                _status_row(
                    store,
                    "unavailable_insufficient_contiguous_history",
                    (
                        "No finite uninterrupted daily segment reaches the 56-day minimum; "
                        f"longest segment has {len(longest) if longest is not None else 0} days."
                    ),
                    segment=longest,
                )
            )
            continue

        segment = max(eligible_segments, key=_segment_order)
        if store not in selected_stores:
            status_rows.append(
                _status_row(
                    store,
                    "eligible_not_selected",
                    "Eligible, but outside the first three eligible Store IDs in ascending order.",
                    segment=segment,
                )
            )
            continue

        analysis_segment = segment.tail(MAX_SEGMENT_DAYS).copy()
        observed = analysis_segment["Sales"].to_numpy(dtype=np.float64, na_value=np.nan)
        try:
            fitted = STL(
                observed,
                period=PERIOD_DAYS,
                seasonal=SEASONAL_WINDOW,
                trend=None,
                low_pass=None,
                robust=ROBUST,
                seasonal_deg=SEASONAL_DEGREE,
                trend_deg=TREND_DEGREE,
                low_pass_deg=LOW_PASS_DEGREE,
                seasonal_jump=SEASONAL_JUMP,
                trend_jump=TREND_JUMP,
                low_pass_jump=LOW_PASS_JUMP,
            ).fit()
            trend = np.asarray(fitted.trend, dtype=np.float64)
            seasonal = np.asarray(fitted.seasonal, dtype=np.float64)
            residual = np.asarray(fitted.resid, dtype=np.float64)
            if not all(np.isfinite(values).all() for values in (trend, seasonal, residual)):
                raise FloatingPointError("STL returned a non-finite component")
            if not np.allclose(observed, trend + seasonal + residual, rtol=1e-10, atol=1e-8):
                raise RuntimeError("STL components failed the observed-value reconstruction check")
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
            status_rows.append(
                _status_row(
                    store,
                    "unavailable_stl_error",
                    f"STL could not produce finite components ({type(exc).__name__}).",
                    segment=segment,
                    analysis_segment=analysis_segment,
                )
            )
            continue

        component_frames.append(
            pd.DataFrame(
                {
                    "Store": store,
                    "Date": analysis_segment["Date"].to_numpy(copy=True),
                    "ObservedSales": observed,
                    "Trend": trend,
                    "Seasonal": seasonal,
                    "Residual": residual,
                    "Method": METHOD,
                    "PeriodDays": PERIOD_DAYS,
                    "Robust": ROBUST,
                    "SourceType": provenance.source_kind,
                }
            )
        )
        status_rows.append(
            _status_row(
                store,
                "available",
                "",
                segment=segment,
                analysis_segment=analysis_segment,
            )
        )

    component_columns = [
        "Store",
        "Date",
        "ObservedSales",
        "Trend",
        "Seasonal",
        "Residual",
        "Method",
        "PeriodDays",
        "Robust",
        "SourceType",
    ]
    components = (
        pd.concat(component_frames, ignore_index=True).loc[:, component_columns]
        if component_frames
        else pd.DataFrame(columns=component_columns)
    )
    if not components.empty:
        components = components.sort_values(["Store", "Date"], kind="stable").reset_index(drop=True)
    return DecompositionRun(
        components=components,
        store_status=pd.DataFrame(status_rows),
        input_sha256=input_sha256,
        input_rows=len(source),
        provenance=provenance,
    )


def build_decomposition_figure(run: DecompositionRun, store: int) -> Figure:
    """Build the required four-panel retrospective plot for an available Store."""

    selected = run.components.loc[run.components["Store"].eq(store)].copy()
    if selected.empty:
        raise ValueError(f"Store {store} has no available decomposition in this run")
    selected = selected.sort_values("Date", kind="stable")
    dates = pd.DatetimeIndex(selected["Date"])
    panels = (
        ("ObservedSales", "Observed Sales"),
        ("Trend", "Estimated trend"),
        ("Seasonal", "Weekly seasonal component"),
        ("Residual", "Residual component"),
    )
    figure, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    for axis, (field, panel_title) in zip(axes, panels, strict=True):
        axis.plot(dates, selected[field].to_numpy(dtype=float), linewidth=1.0)
        axis.set_title(panel_title, loc="left", fontsize=9, pad=3)
        axis.set_ylabel("Sales value", fontsize=8)
        axis.grid(axis="y", alpha=0.25)
    axes[3].axhline(0, color="black", linewidth=0.7, alpha=0.7)
    locator = mdates.AutoDateLocator(minticks=5, maxticks=9)
    axes[3].xaxis.set_major_locator(locator)
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    axes[3].tick_params(axis="x", labelsize=8)
    axes[3].set_xlabel("Date")
    start = dates.min().date().isoformat()
    end = dates.max().date().isoformat()
    figure.suptitle(
        f"Store {store}: weekly STL ({start} to {end})\n"
        "Retrospective description of monetary Sales turnover; not a forecast",
        fontsize=12,
    )
    figure.subplots_adjust(left=0.12, right=0.99, top=0.90, bottom=0.10, hspace=0.34)
    figure.text(
        0.12,
        0.025,
        "Sales is monetary turnover. Components are descriptive; they do not imply causes.",
        fontsize=8,
    )
    return figure


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _code_identity() -> dict[str, object]:
    repository = Path(__file__).resolve().parents[3]
    revision_result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, capture_output=True, text=True, check=False
    )
    status_result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    lockfile = repository / "uv.lock"
    return {
        "revision": revision_result.stdout.strip() if revision_result.returncode == 0 else None,
        "working_tree_dirty": bool(status_result.stdout.strip())
        if status_result.returncode == 0
        else None,
        "uv_lock_sha256": _sha256_file(lockfile) if lockfile.is_file() else None,
    }


def export_decomposition_outputs(
    run: DecompositionRun,
    output_dir: str | Path = OUTPUT_SUBDIRECTORY,
    *,
    command: Sequence[str] | None = None,
) -> Path:
    """Write component/status CSVs, per-Store figures, and a manifest written last."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    components_path = destination / "components.csv"
    status_path = destination / "store_status.csv"
    run.components.to_csv(
        components_path, index=False, date_format="%Y-%m-%d", float_format="%.17g"
    )
    run.store_status.to_csv(status_path, index=False)

    outputs = [components_path, status_path]
    for store in run.components["Store"].drop_duplicates().sort_values().tolist():
        figure = build_decomposition_figure(run, int(store))
        figure_path = destination / f"store_{int(store)}_stl.png"
        figure.savefig(figure_path, dpi=140, metadata={"Software": "CC-02 weekly STL"})
        plt.close(figure)
        outputs.append(figure_path)

    output_identities = [
        {"path": path.name, "sha256": _sha256_file(path), "bytes": path.stat().st_size}
        for path in outputs
    ]
    code_identity = _code_identity()
    manifest = {
        "schema_version": 1,
        "command": list(command) if command is not None else ["rossmann-seasonal-decomposition"],
        "designation": run.provenance.source_kind,
        "source": {
            "identity": run.provenance.source_id,
            "preflight_reference": run.provenance.preflight_reference,
            "authorized_in_memory_projection_sha256": run.input_sha256,
            "input_rows": run.input_rows,
            "fields_used": list(SOURCE_COLUMNS),
        },
        "method_configuration": method_configuration(),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "statsmodels": statsmodels.__version__,
            "uv_lock_sha256": code_identity["uv_lock_sha256"],
        },
        "random_seed": None,
        "randomness": "not applicable; this STL procedure is deterministic",
        "code": {key: value for key, value in code_identity.items() if key != "uv_lock_sha256"},
        "outputs": output_identities,
        "interpretation": (
            "retrospective descriptive decomposition; not a forecast or causal result"
        ),
    }
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    return manifest_path


def input_contract() -> dict[str, object]:
    """Describe the preflight a future separately authorized input provider must satisfy."""

    return {
        "status": "no filesystem input provider is currently configured",
        "accepted_runtime_input": "an already-authorized in-memory pandas DataFrame",
        "required_fields": list(SOURCE_COLUMNS),
        "date_ceiling": MAX_ELIGIBLE_DATE.date().isoformat(),
        "preflight_requirements": [
            (
                "The input is a physically separate development-only partition, not the combined "
                "prepared train artifact."
            ),
            (
                "Its source lineage and separation are reviewed before any source data is opened "
                "or hashed."
            ),
            (
                "The trusted provider proves all included dates are on or before the date ceiling "
                "before returning the frame."
            ),
            (
                "The owner separately approves the provider and records a reviewable preflight "
                "reference."
            ),
            "Only Store, Date, and Sales are exposed to this analysis API.",
        ],
        "current_cli_behavior": "fails closed without opening or reading a data file",
    }


def cli_main(argv: Sequence[str] | None = None) -> int:
    """Expose the command contract and fail closed until a trusted provider is approved."""

    parser = argparse.ArgumentParser(
        prog="rossmann-seasonal-decomposition",
        description=(
            "Report the CC-02 input contract. The command has no file-path or bypass option and "
            "cannot run until a trusted development-only provider receives separate approval."
        ),
    )
    parser.add_argument(
        "--describe-input-contract",
        action="store_true",
        help="Print the trusted-input preflight contract without opening any data.",
    )
    args = parser.parse_args(argv)
    if args.describe_input_contract:
        print(json.dumps(input_contract(), indent=2, sort_keys=True))
        return 0
    parser.error(
        "no approved development-only input provider is configured; no data file was opened. "
        "Obtain a separately reviewed provider and preflight approval before real-data execution."
    )


if __name__ == "__main__":
    raise SystemExit(cli_main())
