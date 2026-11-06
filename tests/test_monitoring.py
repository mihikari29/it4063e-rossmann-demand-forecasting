"""Origin/label/metric regressions using authored fixture inputs only."""

from __future__ import annotations

from copy import deepcopy

import pytest

from rossmann_forecasting.monitoring import (
    build_monitoring_summary,
    pair_forecasts,
    synthetic_monitoring_inputs,
)
from rossmann_forecasting.monitoring_report import render_monitoring_html


def summary(forecasts=None, labels=None, **kwargs):
    issued, actuals = synthetic_monitoring_inputs()
    return build_monitoring_summary(
        issued if forecasts is None else forecasts,
        actuals if labels is None else labels,
        **(
            {
                "as_of": "2015-07-03",
                "reference_start": "2015-06-06",
                "reference_end": "2015-06-19",
                "current_start": "2015-06-20",
                "current_end": "2015-07-03",
                "generated_at": "2026-11-06T00:00:00+00:00",
            }
            | kwargs
        ),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Store", True),
        ("Store", 1116),
        ("horizon", 0),
        ("horizon", 1.5),
        ("target_date", "2015-07-04"),
        ("target_date", "2015-06-07"),
        ("issued_on", "2015-06-06"),
        ("training_through", "2015-06-06"),
        ("features_available_on", "2015-06-06"),
        ("prediction", float("inf")),
        ("prediction", -1),
        ("prediction", "123"),
        ("model_id", "lightgbm"),
        ("evidence_kind", "production"),
        ("issuance_sha256", "A" * 64),
        ("features", {"Customers": 4}),
        ("features", {"Sales": 4}),
        ("features", {"Promo": 3}),
    ],
)
def test_invalid_issuance_rejected_before_pairing(field, value):
    forecasts, labels = synthetic_monitoring_inputs()
    forecasts[0][field] = value
    with pytest.raises(ValueError):
        pair_forecasts(forecasts, labels, as_of="2015-07-03")


def test_issuance_rejects_target_fields_and_duplicate_or_conflicting_identity():
    forecasts, labels = synthetic_monitoring_inputs()
    for mutation in (
        forecasts + [forecasts[0]],
        [{**forecasts[0], "actual_sales": 1}] + forecasts[1:],
        [forecasts[0], {**forecasts[1], "issuance_sha256": "0" * 64}] + forecasts[2:],
    ):
        with pytest.raises(ValueError):
            pair_forecasts(mutation, labels, as_of="2015-07-03")


@pytest.mark.parametrize("change", ["duplicate", "unmatched", "future", "early", "invalid_open"])
def test_label_integrity_and_availability(change):
    forecasts, labels = synthetic_monitoring_inputs()
    if change == "duplicate":
        labels.append(labels[0])
    elif change == "unmatched":
        labels[0]["Store"] = 999
    elif change == "future":
        labels[0]["available_on"] = "2015-07-04"
    elif change == "early":
        labels[0]["available_on"] = "2015-06-05"
    else:
        labels[0]["source_open"] = "1"
    with pytest.raises(ValueError):
        pair_forecasts(forecasts, labels, as_of="2015-07-03")


def test_changing_labels_does_not_change_issued_predictions_or_inputs():
    forecasts, labels = synthetic_monitoring_inputs()
    original = deepcopy(forecasts)
    first = pair_forecasts(forecasts, labels, as_of="2015-07-03")
    labels[0]["actual_sales"] = 999999
    second = pair_forecasts(forecasts, labels, as_of="2015-07-03")
    assert forecasts == original
    assert first["prediction"].equals(second["prediction"])
    assert not first["actual_sales"].equals(second["actual_sales"])


def test_missing_label_and_missing_prediction_do_not_become_zero_or_healthy():
    forecasts, labels = synthetic_monitoring_inputs()
    forecasts[-1]["prediction"] = None
    result = summary(forecasts, labels[:-2])
    assert result["status"] == "PARTIAL_EVIDENCE"
    assert result["current"]["pooled"]["missing_actual_rows"] == 2
    unavailable = summary(labels=[])
    assert unavailable["status"] == "UNAVAILABLE"
    assert unavailable["current"]["pooled"]["mae"] is None


def test_metric_denominators_open_zero_sales_and_closures():
    forecasts, labels = synthetic_monitoring_inputs()
    # Restrict the assessed current population to three labels, two open (one zero), one closed.
    current = [row for row in forecasts if row["forecast_origin"] == "2015-06-19"][:3]
    for row, prediction in zip(current, (2, 12, 99), strict=True):
        row["prediction"] = prediction
    targets = [(row["Store"], row["target_date"]) for row in current]
    labels = [
        {
            "Store": store,
            "target_date": target,
            "available_on": target,
            "actual_sales": actual,
            "source_open": opened,
        }
        for (store, target), actual, opened in zip(targets, (0, 10, 0), (1, 1, 0), strict=True)
    ]
    metrics = summary(current, labels)["current"]["pooled"]
    assert metrics["mae"] == 2
    assert metrics["rmse"] == 2
    assert metrics["mape"] == 20
    assert metrics["mape_rows"] == 1
    assert metrics["zero_actual_rows_excluded_from_mape"] == 1
    assert metrics["wape"] == 0.4
    assert metrics["closed_label_rows"] == 1
    assert metrics["eligible_rows"] == 2


def test_calendar_windows_keep_gaps_and_strata_and_status_matches_html():
    forecasts, labels = synthetic_monitoring_inputs()
    result = summary(forecasts, [row for row in labels if row["target_date"] != "2015-06-22"])
    window = next(
        row for row in result["windows"] if row["end"] == "2015-06-26" and row["nominal_days"] == 7
    )
    assert window["start"] == "2015-06-20"
    assert window["calendar_days"] == 7 and not window["partial"]
    assert window["observed_label_dates"] == 6
    assert len(window["by_store"]) == 3
    assert len(window["by_horizon"]) == 7
    assert [row["horizon"] for row in window["by_horizon"]] == list(range(1, 8))
    assert [row["horizon"] for row in result["current"]["by_horizon"]] == list(range(1, 15))
    assert len(window["by_origin"]) == 1
    assert result["windows"][1]["partial"]
    document = render_monitoring_html(result)
    assert result["status"] in document
    assert result["generated_at"] in document
    assert "System Status: Healthy" not in document


def test_descriptive_feature_change_constant_and_unavailable():
    forecasts, labels = synthetic_monitoring_inputs()
    for row in forecasts:
        row["features"]["Promo"] = int(row["forecast_origin"] == "2015-06-19")
    result = summary(forecasts, labels)
    promo = next(row for row in result["feature_comparison"] if row["feature"] == "Promo")
    assert promo["median_difference"] == 1
    assert promo["reference_constant"] is True
    assert promo["state"] == "DESCRIPTIVE_ONLY"
    missing = next(row for row in result["feature_comparison"] if row["feature"] == "SchoolHoliday")
    assert missing["state"] == "INSUFFICIENT_SAMPLE"
    assert missing["median_difference"] is None
    assert "p_value" not in promo


def test_reference_overlap_rejected_and_adverse_errors_preserved():
    with pytest.raises(ValueError, match="Reference must precede"):
        summary(reference_end="2015-06-20")
    forecasts, labels = synthetic_monitoring_inputs()
    before = summary(forecasts, labels)
    for row in forecasts:
        if row["forecast_origin"] == "2015-06-19":
            row["prediction"] = 0
    after = summary(forecasts, labels)
    assert after["current"]["pooled"]["mae"] > before["current"]["pooled"]["mae"]
    assert "retrain" not in after["status"].lower()


def test_all_zero_actual_denominators_are_unavailable():
    forecasts, labels = synthetic_monitoring_inputs()
    for row in labels:
        row["actual_sales"] = 0
    metrics = summary(forecasts, labels)["current"]["pooled"]
    assert metrics["mae"] > 0
    assert metrics["mape"] is None and metrics["wape"] is None
    assert metrics["mape_unavailable_reason"] and metrics["wape_unavailable_reason"]


def test_closed_missing_prediction_is_partial_and_skewed_reference_is_not_constant():
    forecasts, labels = synthetic_monitoring_inputs()
    closed = next(row for row in forecasts if row["target_date"] == "2015-06-21")
    closed["prediction"] = None
    for row in forecasts:
        row["features"]["Promo"] = 0
    forecasts[0]["features"]["Promo"] = 1
    result = summary(forecasts, labels)
    assert result["status"] == "PARTIAL_EVIDENCE"
    promo = next(row for row in result["feature_comparison"] if row["feature"] == "Promo")
    assert promo["reference"]["q25"] == promo["reference"]["q75"] == 0
    assert promo["reference_constant"] is False


def test_delayed_available_label_and_shared_label_for_overlapping_origins():
    forecasts, _ = synthetic_monitoring_inputs()
    first = deepcopy(forecasts[13])
    second = {
        **first,
        "forecast_origin": "2015-06-06",
        "issued_on": "2015-06-06",
        "horizon": 13,
        "issuance_id": "synthetic_overlap",
    }
    labels = [
        {
            "Store": first["Store"],
            "target_date": "2015-06-19",
            "available_on": "2015-06-20",
            "actual_sales": 100,
            "source_open": 1,
        }
    ]
    frame = pair_forecasts([first, second], labels, as_of="2015-06-20")
    assert len(frame) == 2
    assert frame["actual_sales"].tolist() == [100, 100]
    assert frame["horizon"].tolist() == [14, 13]
    with pytest.raises(ValueError, match="available"):
        pair_forecasts([first, second], labels, as_of="2015-06-19")


def test_synthetic_report_manifest_and_no_overwrite(tmp_path):
    import hashlib
    import json
    from pathlib import Path

    from rossmann_forecasting.monitoring_report import write_synthetic_monitoring_report

    directory = tmp_path / "new-report"
    result = write_synthetic_monitoring_report(directory, Path.cwd())
    stored = json.loads((directory / "monitoring_summary.json").read_text())
    assert result == stored
    assert stored["status"] in (directory / "monitoring_report.html").read_text()
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    assert (
        manifest["source_sha256"]["issued_forecasts"]
        == manifest["output_sha256"]["issued_forecasts.json"]
    )
    with pytest.raises(FileExistsError):
        write_synthetic_monitoring_report(directory, Path.cwd())
