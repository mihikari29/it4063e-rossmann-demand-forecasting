"""Synthetic-only tests for the development-only weekly STL diagnostic."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.analysis import seasonal_decomposition as decomposition


def _sales_frame(
    store: int = 1,
    start: str = "2015-01-01",
    days: int = 84,
    *,
    offset: float = 0.0,
) -> pd.DataFrame:
    dates = pd.date_range(start, periods=days, freq="D")
    weekly = np.array([0.0, -32.0, 21.0, 15.0, -24.0, 39.0, -19.0])
    sales = 900.0 + np.arange(days, dtype=float) * 1.7 + weekly[np.arange(days) % 7] + offset
    return pd.DataFrame({"Store": store, "Date": dates, "Sales": sales})


def _source(source_id: str = "cc02-synthetic-weekly-fixture") -> decomposition.InputProvenance:
    return decomposition.InputProvenance("synthetic_fixture", source_id)


def _run(frame: pd.DataFrame) -> decomposition.DecompositionRun:
    return decomposition.decompose_development_sales(frame, provenance=_source())


def test_weekly_stl_reconstructs_observations_and_recovers_weekly_signal() -> None:
    run = _run(_sales_frame(days=84))
    components = run.components

    assert len(components) == 84
    assert components["PeriodDays"].eq(7).all()
    assert components["Robust"].all()
    assert components["Method"].eq("statsmodels.tsa.seasonal.STL").all()
    np.testing.assert_allclose(
        components["ObservedSales"],
        components["Trend"] + components["Seasonal"] + components["Residual"],
        rtol=1e-10,
        atol=1e-8,
    )
    assert components["Seasonal"].abs().max() > 15
    expected = (
        pd.DataFrame(
            {
                "weekday": components["Date"].dt.dayofweek,
                "pattern": np.array([0.0, -32.0, 21.0, 15.0, -24.0, 39.0, -19.0])[
                    np.arange(len(components)) % 7
                ],
            }
        )
        .groupby("weekday")["pattern"]
        .mean()
    )
    estimated = (
        components.assign(weekday=components["Date"].dt.dayofweek)
        .groupby("weekday")["Seasonal"]
        .mean()
    )
    assert np.corrcoef(expected.sort_index(), estimated.sort_index())[0, 1] > 0.99


def test_store_and_recent_segment_selection_are_deterministic() -> None:
    first = _sales_frame(store=4, days=70)
    store_one = _sales_frame(store=1, days=56)
    # A later eligible segment follows a genuine calendar gap; it is selected over the earlier one.
    recent = _sales_frame(store=1, start="2015-04-01", days=63, offset=75.0)
    store_two = _sales_frame(store=2, days=60, offset=200.0)
    store_three = _sales_frame(store=3, days=65, offset=400.0)
    frame = pd.concat([store_three, first, recent, store_one, store_two], ignore_index=True)
    frame = frame.sort_values(["Store", "Date"], kind="stable").reset_index(drop=True)

    left = _run(frame)
    right = _run(frame)
    pd.testing.assert_frame_equal(left.components, right.components)
    pd.testing.assert_frame_equal(left.store_status, right.store_status)
    assert left.store_status.loc[left.store_status["status"].eq("available"), "Store"].tolist() == [
        1,
        2,
        3,
    ]
    status_one = left.store_status.set_index("Store").loc[1]
    assert status_one["contiguous_segment_start"] == "2015-04-01"
    assert status_one["contiguous_segment_days"] == 63
    assert left.store_status.set_index("Store").loc[4, "status"] == "eligible_not_selected"
    assert left.input_sha256 == right.input_sha256


def test_missing_calendar_dates_split_segments_without_filling() -> None:
    early = _sales_frame(days=56)
    late = _sales_frame(start="2015-03-01", days=61, offset=20.0)
    frame = pd.concat([early, late], ignore_index=True)

    run = _run(frame)
    assert len(run.components) == 61
    assert run.components["Date"].min() == pd.Timestamp("2015-03-01")
    assert run.components["Date"].max() == pd.Timestamp("2015-04-30")
    assert pd.Timestamp("2015-02-26") not in set(run.components["Date"])
    assert run.store_status.loc[0, "contiguous_segment_start"] == "2015-03-01"


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_missing_or_nonfinite_sales_is_a_segment_boundary(bad_value: float) -> None:
    frame = _sales_frame(days=84)
    frame.loc[40, "Sales"] = bad_value

    run = _run(frame)
    status = run.store_status.iloc[0]
    assert status["status"] == "unavailable_insufficient_contiguous_history"
    assert "longest segment has 43 days" in status["reason"]
    assert run.components.empty


def test_duplicate_store_date_keys_are_rejected() -> None:
    frame = _sales_frame(days=56)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True).sort_values(
        ["Store", "Date"], kind="stable"
    )

    with pytest.raises(ValueError, match=r"unique \(Store, Date\) keys"):
        _run(frame)


def test_observed_closed_day_zero_is_retained_without_replacement() -> None:
    frame = _sales_frame(days=56)
    frame.loc[20, "Sales"] = 0.0
    before = frame.copy(deep=True)

    run = _run(frame)
    actual = run.components.loc[run.components["Date"].eq(frame.loc[20, "Date"]), "ObservedSales"]
    assert actual.tolist() == [0.0]
    pd.testing.assert_frame_equal(frame, before)


def test_insufficient_and_exact_minimum_history_have_explicit_status() -> None:
    short = _run(_sales_frame(days=55))
    exact = _run(_sales_frame(days=56))

    assert short.store_status.loc[0, "status"] == "unavailable_insufficient_contiguous_history"
    assert "longest segment has 55 days" in short.store_status.loc[0, "reason"]
    assert exact.store_status.loc[0, "status"] == "available"
    assert len(exact.components) == 56


def test_latest_112_rows_of_longest_recent_segment_are_used() -> None:
    frame = _sales_frame(start="2015-01-01", days=140)

    run = _run(frame)
    status = run.store_status.iloc[0]
    assert status["contiguous_segment_days"] == 140
    assert status["analysis_segment_days"] == 112
    assert status["analysis_segment_start"] == "2015-01-29"
    assert status["analysis_segment_end"] == "2015-05-20"
    assert run.components["Date"].min() == pd.Timestamp("2015-01-29")
    assert run.components["Date"].max() == pd.Timestamp("2015-05-20")


def test_dates_after_development_ceiling_are_rejected_not_filtered() -> None:
    frame = _sales_frame(start="2015-06-01", days=34)

    with pytest.raises(ValueError, match="after the development ceiling"):
        _run(frame)


def test_input_must_be_in_chronological_store_date_order() -> None:
    frame = _sales_frame(days=56).iloc[::-1].reset_index(drop=True)

    with pytest.raises(ValueError, match="ordered by Store ascending and Date ascending"):
        _run(frame)


@pytest.mark.parametrize(
    ("column", "values", "error"),
    [
        ("Date", ["2015-01-01"] * 56, TypeError),
        ("Sales", ["not numeric"] * 56, TypeError),
    ],
)
def test_required_value_types_are_validated(
    column: str, values: list[str], error: type[Exception]
) -> None:
    frame = _sales_frame(days=56)
    frame[column] = values

    with pytest.raises(error):
        _run(frame)


def test_frame_is_unchanged_and_repeated_metadata_is_deterministic() -> None:
    frame = _sales_frame(days=70)
    before = frame.copy(deep=True)

    first = _run(frame)
    second = _run(frame)

    pd.testing.assert_frame_equal(frame, before)
    pd.testing.assert_frame_equal(first.store_status, second.store_status)
    assert first.input_sha256 == second.input_sha256
    assert first.store_status.loc[0, "status"] == "available"


def test_figure_has_four_aligned_panels_and_retrospective_source_note() -> None:
    run = _run(_sales_frame(days=70))

    figure = decomposition.build_decomposition_figure(run, 1)
    assert len(figure.axes) == 4
    assert all(len(axis.lines[0].get_xdata()) == 70 for axis in figure.axes)
    assert "not a forecast" in figure._suptitle.get_text()
    assert "Synthetic fixture" in figure._suptitle.get_text()
    assert figure.axes[-1].get_xlabel() == "Date"
    assert all(axis.get_ylabel() for axis in figure.axes)
    decomposition.plt.close(figure)


def test_development_figure_has_accurate_source_designation() -> None:
    run = _run(_sales_frame(days=56))
    development_provenance = decomposition.InputProvenance(
        "approved_development_only", "development-fixture", "test-only-preflight-reference"
    )
    run = decomposition.DecompositionRun(
        components=run.components,
        store_status=run.store_status,
        input_sha256=run.input_sha256,
        input_rows=run.input_rows,
        provenance=development_provenance,
    )

    figure = decomposition.build_decomposition_figure(run, 1)
    assert "Development-only input" in figure._suptitle.get_text()
    assert "not a forecast" in figure._suptitle.get_text()
    decomposition.plt.close(figure)


def test_synthetic_export_manifest_is_truthful_and_hashes_outputs(tmp_path) -> None:
    run = _run(_sales_frame(days=56))

    manifest_path = decomposition.export_decomposition_outputs(run, tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["designation"] == "synthetic_fixture"
    assert manifest["execution_mode"] == "python_api"
    assert manifest["entry_point"] == (
        "rossmann_forecasting.analysis.seasonal_decomposition.export_decomposition_outputs"
    )
    assert manifest["command"] is None
    assert manifest["source"]["identity"] == "cc02-synthetic-weekly-fixture"
    assert manifest["source"]["authorized_in_memory_projection_sha256"] == run.input_sha256
    assert {output["path"] for output in manifest["outputs"]} == {
        "components.csv",
        "store_status.csv",
        "store_1_stl.png",
    }
    for output in manifest["outputs"]:
        output_path = tmp_path / output["path"]
        assert hashlib.sha256(output_path.read_bytes()).hexdigest() == output["sha256"]
        assert output_path.stat().st_size == output["bytes"]
    assert "not a forecast" in manifest["interpretation"]


def test_caller_supplied_invocation_metadata_is_preserved_deterministically(tmp_path) -> None:
    run = _run(_sales_frame(days=56))
    command = ["synthetic-review-runner", "--fixture", "weekly-01"]
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first_path = decomposition.export_decomposition_outputs(run, first_dir, command=command)
    second_path = decomposition.export_decomposition_outputs(run, second_dir, command=command)
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))

    assert first["execution_mode"] == "caller_supplied"
    assert first["entry_point"] == (
        "rossmann_forecasting.analysis.seasonal_decomposition.export_decomposition_outputs"
    )
    assert first["command"] == command
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["outputs"] == second["outputs"]


def test_export_rejects_occupied_directory_without_changing_existing_run(tmp_path) -> None:
    output_dir = tmp_path / "existing-run"
    first_run = _run(_sales_frame(store=1, days=56))
    manifest_path = decomposition.export_decomposition_outputs(first_run, output_dir)
    before = {
        path.relative_to(output_dir).as_posix(): path.read_bytes()
        for path in output_dir.rglob("*")
        if path.is_file()
    }

    second_run = _run(_sales_frame(store=9, days=56, offset=250.0))
    with pytest.raises(FileExistsError, match="output directory must be empty"):
        decomposition.export_decomposition_outputs(second_run, output_dir)

    after = {
        path.relative_to(output_dir).as_posix(): path.read_bytes()
        for path in output_dir.rglob("*")
        if path.is_file()
    }
    assert after == before
    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved_manifest["source"]["authorized_in_memory_projection_sha256"] == (
        first_run.input_sha256
    )
    assert {output["path"] for output in saved_manifest["outputs"]} == {
        "components.csv",
        "store_status.csv",
        "store_1_stl.png",
    }
    assert not (output_dir / "store_9_stl.png").exists()


def test_failed_fresh_export_does_not_publish_manifest(tmp_path, monkeypatch) -> None:
    run = _run(_sales_frame(days=56))

    def fail_figure(*_args, **_kwargs):
        raise RuntimeError("injected synthetic figure failure")

    monkeypatch.setattr(decomposition, "build_decomposition_figure", fail_figure)
    with pytest.raises(RuntimeError, match="injected synthetic figure failure"):
        decomposition.export_decomposition_outputs(run, tmp_path)

    assert (tmp_path / "components.csv").is_file()
    assert (tmp_path / "store_status.csv").is_file()
    assert not (tmp_path / "manifest.json").exists()
    assert not (tmp_path / ".manifest.json.tmp").exists()


def test_failed_manifest_replace_does_not_publish_manifest(tmp_path, monkeypatch) -> None:
    run = _run(_sales_frame(days=56))

    def fail_replace(_path, _target):
        raise OSError("injected synthetic manifest replace failure")

    monkeypatch.setattr(decomposition.Path, "replace", fail_replace)
    with pytest.raises(OSError, match="injected synthetic manifest replace failure"):
        decomposition.export_decomposition_outputs(run, tmp_path)

    assert not (tmp_path / "manifest.json").exists()
    assert not (tmp_path / ".manifest.json.tmp").exists()


def test_real_input_provenance_requires_a_preflight_reference() -> None:
    with pytest.raises(ValueError, match="reviewed preflight reference"):
        decomposition.InputProvenance("approved_development_only", "separate-dev-projection")


def test_command_fails_closed_before_any_data_reader_is_called(monkeypatch, capsys) -> None:
    def forbidden_reader(*_args, **_kwargs):
        pytest.fail("the command must not invoke a data reader without an approved provider")

    monkeypatch.setattr(pd, "read_parquet", forbidden_reader)
    monkeypatch.setattr(pd, "read_csv", forbidden_reader)
    with pytest.raises(SystemExit) as error:
        decomposition.cli_main(["--input", "data/interim/train.parquet"])

    assert error.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_command_describes_contract_without_opening_data(monkeypatch, capsys) -> None:
    def forbidden_reader(*_args, **_kwargs):
        pytest.fail("contract description must not invoke a data reader")

    monkeypatch.setattr(pd, "read_parquet", forbidden_reader)
    monkeypatch.setattr(pd, "read_csv", forbidden_reader)

    assert decomposition.cli_main(["--describe-input-contract"]) == 0
    contract = json.loads(capsys.readouterr().out)
    assert contract["status"] == "no filesystem input provider is currently configured"
    assert "combined prepared train artifact" in contract["preflight_requirements"][0]
