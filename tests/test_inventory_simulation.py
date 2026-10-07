from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from rossmann_forecasting.inventory import scenarios, simulation


def _target_inputs(
    *,
    probability: float = 0.95,
    quantile: float | None = 30.0,
    quantile_available: bool = True,
    open_values: tuple[int | None, ...] = (1, 1, 1),
    point_values: tuple[float | None, ...] = (20.0, 30.0, 30.0),
) -> pd.DataFrame:
    values = []
    for horizon, (opening, point) in enumerate(
        zip(open_values, point_values, strict=True), start=1
    ):
        values.append(
            {
                "case_id": "fixture--reference",
                "scenario_id": "fixture",
                "Store": 1,
                "forecast_origin": date(2015, 6, 5),
                "family": "synthetic_base",
                "mode": "synthetic_stress",
                "replicate": 0,
                "sensitivity_variant": "reference",
                "SupplierLeadTime": 2,
                "ReviewPeriod": 1,
                "ProtectionPeriod": 3,
                "buffer_probability": probability,
                "mean_open_sales_value": 100.0,
                "anchor_available": True,
                "initial_stock_value": 50.0,
                "ProcurementCostRatio": 0.70,
                "AnnualHoldingRate": 0.20,
                "GoodwillPenaltyRate": 0.50,
                "horizon": horizon,
                "schedule_open": opening,
                "raw_point_forecast": point,
                "forecast_available": point is not None,
                "cumulative_signed_quantile": quantile,
                "quantile_available": quantile_available,
                "quantile_unavailable_reason": None if quantile_available else "sample_floor",
                "fit_id": "A",
                "model_id": "global_lightgbm_gbdt_regression_l1",
                "upstream_identity": "frozen-test-identity",
                "synthetic": True,
                "schedule_assumption": "phase9_scenario_open_known_at_origin",
            }
        )
    return pd.DataFrame.from_records(values, columns=simulation.TARGET_INPUT_COLUMNS)


def _targets(**kwargs):
    frame = _target_inputs(**kwargs)
    before = frame.copy(deep=True)
    table = simulation.build_policy_targets(frame)
    pd.testing.assert_frame_equal(frame, before)
    return {row["policy_id"]: row for row in table.to_pylist()}, table


def _target(policy_id: str, *, target_value: float = 100.0, stock: float = 50.0, lead: int = 2):
    targets, _ = _targets()
    result = dict(targets[policy_id])
    result.update(
        {
            "target_available": True,
            "availability_reason": None,
            "target_value": target_value,
            "initial_stock_value": stock,
            "SupplierLeadTime": lead,
            "ProtectionPeriod": lead + 1,
        }
    )
    return result


def _demand(values, *, open_values=None, missing_horizons=(), source_open=None):
    if open_values is None:
        open_values = [1] * len(values)
    if source_open is None:
        source_open = [None] * len(values)
    return [
        {
            "horizon": horizon,
            "ScenarioOpen": open_values[horizon - 1],
            "source_open": source_open[horizon - 1],
            "demand_value": value,
            "demand_available": horizon not in missing_horizons,
            "unavailable_reason": "fixture_missing" if horizon in missing_horizons else None,
            "historical_open_assumption_violation": bool(
                source_open[horizon - 1] == 0 and value is not None and value > 0
            ),
        }
        for horizon, value in enumerate(values, start=1)
    ]


def test_approved_config_has_exact_domains_and_nine_one_factor_overlays():
    config = simulation.default_simulation_config()
    assert config["horizon_days"] == 14
    assert config["review_period"] == 1
    assert config["lead_times"] == [2, 3, 4, 5, 6, 7]
    assert config["reference_probability"] == 0.95
    assert set(config["sensitivity_variants"]) == {
        "lead_2",
        "lead_7",
        "buffer_090",
        "buffer_098",
        "holding_010",
        "holding_030",
        "goodwill_010",
        "goodwill_075",
        "coverage_1",
    }
    assert simulation.POLICY_IDS == (
        "historical_mean_standing_target",
        "lightgbm_buffer_standing_target",
    )
    variants = simulation._case_variants(
        {"family": "synthetic_base", "mode": "synthetic_stress"}, {}, {}
    )
    variant_ids = [item["id"] for item in variants]
    assert variant_ids == sorted(variant_ids)
    assert len(variant_ids) == 10


def test_target_arithmetic_preserves_signed_quantile_and_open_day_baseline():
    targets, table = _targets()
    baseline = targets[simulation.POLICY_IDS[0]]
    forecast = targets[simulation.POLICY_IDS[1]]
    assert baseline["mode"] == "synthetic_stress"
    assert forecast["mode"] == "synthetic_stress"
    assert baseline["open_days_in_protection_period"] == 3
    assert baseline["target_value"] == 300.0
    assert forecast["forecast_protection_demand_value"] == 80.0
    assert forecast["cumulative_signed_quantile"] == 30.0
    assert forecast["upper_turnover_value"] == 110.0
    assert forecast["safety_stock_value"] == 30.0
    assert forecast["target_value"] == 110.0
    assert table.schema.equals(simulation.POLICY_TARGET_SCHEMA)
    negative, _ = _targets(quantile=-20.0)
    forecast_negative = negative[simulation.POLICY_IDS[1]]
    assert forecast_negative["upper_turnover_value"] == 60.0
    assert forecast_negative["safety_stock_value"] == 0.0
    assert forecast_negative["target_value"] == 80.0


def test_target_builder_rejects_outcomes_future_stress_and_unknown_columns():
    frame = _target_inputs()
    frame["actual_sales"] = 0.0
    with pytest.raises(simulation.SimulationIntegrityError, match="outcome columns"):
        simulation.build_policy_targets(frame)
    frame = _target_inputs()
    frame["SyntheticDemandValue"] = 5.0
    with pytest.raises(simulation.SimulationIntegrityError, match="outcome columns"):
        simulation.build_policy_targets(frame)
    frame = _target_inputs()
    frame["DemandStressFactor"] = 1.2
    with pytest.raises(simulation.SimulationIntegrityError, match="outcome columns"):
        simulation.build_policy_targets(frame)
    frame = _target_inputs()
    frame["unreviewed_future_field"] = 1
    with pytest.raises(simulation.SimulationIntegrityError, match="schema mismatch"):
        simulation.build_policy_targets(frame)


def test_unavailable_target_components_do_not_fall_back():
    q_missing, _ = _targets(quantile=None, quantile_available=False)
    forecast = q_missing[simulation.POLICY_IDS[1]]
    assert forecast["target_available"] is False
    assert forecast["target_value"] is None
    assert forecast["availability_reason"] == "sample_floor"
    assert q_missing[simulation.POLICY_IDS[0]]["target_available"] is True
    unknown, _ = _targets(open_values=(1, None, 1))
    assert all(not row["target_available"] for row in unknown.values())
    closed, _ = _targets(open_values=(0, 1, 1), point_values=(None, 30.0, 30.0))
    assert closed[simulation.POLICY_IDS[1]]["target_available"] is True
    assert closed[simulation.POLICY_IDS[1]]["forecast_protection_demand_value"] == 60.0
    closed_baseline, _ = _targets(open_values=(0, 1, 1), point_values=(None, 30.0, 30.0))
    assert closed_baseline[simulation.POLICY_IDS[0]]["target_value"] == 200.0
    missing_open_point, _ = _targets(point_values=(None, 30.0, 30.0))
    assert missing_open_point[simulation.POLICY_IDS[0]]["target_available"] is True
    assert missing_open_point[simulation.POLICY_IDS[1]]["target_available"] is False
    assert missing_open_point[simulation.POLICY_IDS[1]]["target_value"] is None


def test_target_building_is_deterministic_and_invariant_to_case_store_and_row_order():
    first = _target_inputs()
    second = first.copy(deep=True)
    second["case_id"] = "fixture-2--reference"
    second["scenario_id"] = "fixture-2"
    second["Store"] = 2
    combined = pd.concat([first, second], ignore_index=True)
    expected = simulation.build_policy_targets(combined)
    actual = simulation.build_policy_targets(combined.sample(frac=1, random_state=17))
    assert expected.equals(actual)
    assert expected.equals(simulation.build_policy_targets(combined))
    keys = list(
        zip(
            expected.column("case_id").to_pylist(),
            expected.column("Store").to_pylist(),
            expected.column("policy_id").to_pylist(),
            strict=True,
        )
    )
    assert keys == sorted(keys)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"SupplierLeadTime": 1, "ProtectionPeriod": 2}, "L/R/P"),
        ({"ProtectionPeriod": 15}, "L/R/P"),
        ({"buffer_probability": 0.93}, "p in"),
        ({"fit_id": "B"}, "fit identity"),
        ({"model_id": "another_model"}, "model identity"),
    ],
)
def test_target_builder_rejects_unapproved_domain_and_fit(changes, message):
    frame = _target_inputs()
    for column, value in changes.items():
        frame[column] = value
    with pytest.raises(simulation.SimulationIntegrityError, match=message):
        simulation.build_policy_targets(frame)


def test_unsupported_origin_is_rejected_before_any_artifact_access(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise AssertionError("artifact access occurred before origin rejection")

    monkeypatch.setattr(scenarios, "verify_frozen_bindings", fail)
    monkeypatch.setattr(simulation, "_read_json", fail)
    monkeypatch.setattr(simulation, "_sha256_file", fail)
    monkeypatch.setattr(simulation.pq, "ParquetFile", fail)
    with pytest.raises(simulation.SimulationIntegrityError, match="before opening"):
        simulation.verify_simulation_inputs(tmp_path, origin="2015-07-04")


def test_wrong_phase7_identity_fails_before_phase9_inputs(monkeypatch, tmp_path):
    monkeypatch.setattr(
        scenarios,
        "verify_frozen_bindings",
        lambda _: {"identity_snapshot": {"phase7_selection_manifest_sha256": "wrong"}},
    )
    with pytest.raises(simulation.SimulationIntegrityError, match="Phase 7"):
        simulation.verify_simulation_inputs(tmp_path, origin="2015-06-05")


def test_wrong_phase9_run_identity_fails_closed_before_hashing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        scenarios,
        "verify_frozen_bindings",
        lambda _: {
            "identity_snapshot": {
                "phase7_selection_manifest_sha256": simulation.PHASE7_MANIFEST_SHA256,
                "phase8_manifest_sha256": simulation.PHASE8_MANIFEST_SHA256,
            }
        },
    )
    monkeypatch.setattr(
        simulation,
        "_read_json",
        lambda _: {"run_id": "wrong-phase9-run", "status": "complete"},
    )
    monkeypatch.setattr(
        simulation,
        "_sha256_file",
        lambda _: (_ for _ in ()).throw(AssertionError("wrong run must fail before hashing")),
    )
    with pytest.raises(simulation.SimulationIntegrityError, match="run identity/status"):
        simulation.verify_simulation_inputs(tmp_path, origin="2015-06-05")


def test_golden_receipt_queue_lost_sales_and_cost_fixture():
    target = _target(simulation.POLICY_IDS[1], target_value=100.0, stock=50.0, lead=2)
    path = _demand([40.0, 30.0, 0.0] + [0.0] * 11)
    ledger, summary = simulation.simulate_case(target, path, common_input_identity="shared-fixture")
    assert ledger[0]["order_value"] == 50.0
    assert ledger[0]["order_due_date"] == date(2015, 6, 8)
    day1, day2, day3 = ledger[1], ledger[2], ledger[3]
    assert day1["receipts_today_value"] == 0.0
    assert day2["receipts_today_value"] == 0.0
    assert (day1["ending_inventory_value"], day1["pipeline_before_receipt_value"]) == (10.0, 50.0)
    assert day1["inventory_position_value"] == 60.0
    assert day1["order_value"] == 40.0
    assert day2["fulfilled_value"] == 10.0
    assert day2["unmet_value"] == 20.0
    assert day2["ending_inventory_value"] == 0.0
    assert day2["pipeline_before_receipt_value"] == 90.0
    assert day2["inventory_position_value"] == 90.0
    assert day2["order_value"] == 10.0
    assert day2["unmet_penalty"] == pytest.approx(16.0)
    assert day3["receipts_today_value"] == 50.0
    assert day3["received_order_ids"] == ledger[0]["order_id"]
    assert summary["episode_complete"] is True
    assert summary["holding_cost_total"] == pytest.approx(
        0.14 / 365 * sum(row["ending_inventory_value"] for row in ledger[1:])
    )
    assert ledger[-1]["review_status"] == "terminal_boundary"
    assert ledger[-1]["order_value"] == 0.0


def test_future_demand_cannot_change_target_or_earlier_orders():
    targets_a, _ = _targets(quantile=30.0)
    targets_b, _ = _targets(quantile=30.0)
    assert targets_a == targets_b
    target = _target(simulation.POLICY_IDS[1], target_value=100.0)
    first = [0.0] * 14
    second = list(first)
    second[9] = 500.0
    ledger_a, _ = simulation.simulate_case(target, _demand(first), common_input_identity="a")
    ledger_b, _ = simulation.simulate_case(target, _demand(second), common_input_identity="b")
    for horizon in range(1, 10):
        assert ledger_a[horizon]["order_value"] == ledger_b[horizon]["order_value"]
        assert (
            ledger_a[horizon]["ending_inventory_value"]
            == ledger_b[horizon]["ending_inventory_value"]
        )


def test_simulation_is_deterministic_and_order_up_to_handles_below_equal_above():
    target = _target(simulation.POLICY_IDS[1], target_value=100.0, stock=50.0)
    path = _demand([10.0] + [0.0] * 13)
    first = simulation.simulate_case(target, path, common_input_identity="deterministic")
    second = simulation.simulate_case(target, path, common_input_identity="deterministic")
    assert first == second

    below, _ = simulation.simulate_case(
        _target(simulation.POLICY_IDS[1], target_value=100.0, stock=50.0),
        _demand([10.0] + [0.0] * 13),
        common_input_identity="below",
    )
    equal, _ = simulation.simulate_case(
        _target(simulation.POLICY_IDS[1], target_value=100.0, stock=50.0),
        _demand([0.0] * 14),
        common_input_identity="equal",
    )
    above, _ = simulation.simulate_case(
        _target(simulation.POLICY_IDS[1], target_value=100.0, stock=120.0),
        _demand([0.0] * 14),
        common_input_identity="above",
    )
    assert below[1]["inventory_position_value"] == 90.0
    assert below[1]["order_value"] == 10.0
    assert equal[1]["inventory_position_value"] == 100.0
    assert equal[1]["order_value"] == 0.0
    assert above[1]["inventory_position_value"] == 120.0
    assert above[1]["order_value"] == 0.0
    assert all(row["ending_inventory_value"] >= 0 for row in below if row["state_available"])


def test_missing_demand_stops_state_but_retains_earlier_rows():
    target = _target(simulation.POLICY_IDS[0])
    path = _demand([10.0] * 14, missing_horizons=(3,))
    ledger, summary = simulation.simulate_case(target, path, common_input_identity="missing")
    assert ledger[1]["state_available"] is True
    assert ledger[2]["state_available"] is True
    assert ledger[3]["review_status"] == "demand_unavailable"
    assert ledger[3]["demand_value"] is None
    assert all(not row["state_available"] for row in ledger[3:])
    assert summary["episode_status"] == "incomplete_episode"
    assert summary["availability_reason"] == "fixture_missing"
    assert summary["SimulatedHoldingPlusShortfallCost"] is None


def test_closed_day_demand_zero_but_stock_receipts_review_and_holding_continue():
    target = _target(simulation.POLICY_IDS[0])
    path = _demand([0.0] * 14, open_values=[0] + [1] * 13)
    path[0]["demand_value"] = 0.0
    ledger, summary = simulation.simulate_case(target, path, common_input_identity="closed")
    assert ledger[1]["demand_value"] == 0.0
    assert ledger[1]["state_available"] is True
    assert ledger[1]["holding_cost"] > 0
    assert ledger[3]["receipts_today_value"] == 50.0
    assert ledger[3]["review_status"] == "reviewed"
    assert summary["PositiveDemandStockoutRate"] is None
    assert summary["ValueFillRate"] is None


def test_historical_closed_day_positive_sales_is_preserved_and_flagged():
    historical = simulation._historical_path(
        1,
        date(2015, 6, 5),
        {
            (1, date(2015, 6, 5), 1): {
                "sales": 10.0,
                "source_open": 0,
                "target_key_observed": True,
            },
            **{
                (1, date(2015, 6, 5), horizon): {
                    "sales": 0.0,
                    "source_open": 1,
                    "target_key_observed": True,
                }
                for horizon in range(2, 15)
            },
        },
    )
    target = _target(simulation.POLICY_IDS[0])
    ledger, summary = simulation.simulate_case(
        target, historical, common_input_identity="closed-positive"
    )
    assert ledger[1]["demand_value"] == 10.0
    assert ledger[1]["historical_open_assumption_violation"] is True
    assert summary["historical_open_assumption_violation"] is True
    assert summary["valid_matched_comparison"] is False


def test_day14_receipt_and_after_window_order_are_both_retained():
    target = _target(simulation.POLICY_IDS[1], target_value=100.0, stock=50.0, lead=2)
    demand = [0.0] * 14
    demand[10] = 50.0
    demand[12] = 50.0
    ledger, summary = simulation.simulate_case(
        target, _demand(demand), common_input_identity="terminal"
    )
    day14 = ledger[14]
    assert day14["receipts_today_value"] == 50.0
    assert day14["review_status"] == "terminal_boundary"
    assert day14["order_value"] == 0.0
    assert summary["terminal_on_order_value"] == 50.0
    assert summary["late_order_count"] == 1
    assert summary["late_order_value"] == 50.0
    assert summary["OutstandingProcurementCommitment"] == pytest.approx(35.0)
    assert summary["completed_cycles_total"] == 1
    assert summary["completed_positive_demand_cycles"] == 1
    # The cycle ends immediately before the day-14 receipt boundary, so the
    # two positive-demand days before that boundary are both fulfilled.
    assert summary["zero_unmet_positive_demand_cycles"] == 1
    assert summary["CompletedPositiveDemandReceiptCycleServiceRate"] == 1.0


def test_zero_demand_ratios_are_null_and_receipt_cycle_censoring_is_explicit():
    target = _target(simulation.POLICY_IDS[0])
    ledger, summary = simulation.simulate_case(
        target, _demand([0.0] * 14), common_input_identity="zero-demand"
    )
    assert summary["ValueFillRate"] is None
    assert summary["PositiveDemandStockoutRate"] is None
    assert summary["CompletedPositiveDemandReceiptCycleServiceRate"] is None
    assert summary["completed_cycles_total"] == 0
    assert summary["initial_left_censored_intervals"] == 1
    assert summary["terminal_right_censored_intervals"] == 1
    assert summary["AverageInventoryValue"] is not None
    assert ledger[-1]["pipeline_after_review_value"] == summary["terminal_on_order_value"]


def test_cost_only_parameter_changes_leave_physical_trajectory_identical():
    target = _target(simulation.POLICY_IDS[1], target_value=100.0)
    demand = _demand([20.0] * 14)
    baseline, base_summary = simulation.simulate_case(target, demand, common_input_identity="same")
    cost_variant = dict(target, AnnualHoldingRate=0.30, GoodwillPenaltyRate=0.75)
    changed, changed_summary = simulation.simulate_case(
        cost_variant, demand, common_input_identity="same"
    )
    assert simulation._trajectory_signature(baseline) == simulation._trajectory_signature(changed)
    assert (
        base_summary["SimulatedHoldingPlusShortfallCost"]
        != changed_summary["SimulatedHoldingPlusShortfallCost"]
    )


def test_cost_and_terminal_exposure_are_separate():
    target = _target(simulation.POLICY_IDS[1], target_value=100.0)
    _, summary = simulation.simulate_case(
        target, _demand([0.0] * 14), common_input_identity="exposure"
    )
    assert summary["SimulatedHoldingPlusShortfallCost"] == pytest.approx(
        summary["SimulatedHoldingCost"] + summary["SimulatedUnmetPenalty"]
    )
    assert summary["OutstandingProcurementCommitment"] == pytest.approx(
        0.70 * summary["terminal_on_order_value"]
    )
    assert summary["TerminalStockCostValue"] == pytest.approx(
        0.70 * summary["terminal_on_hand_value"]
    )


def test_stream_validator_reconstructs_orders_and_all_state_balances(tmp_path):
    targets, _ = _targets()
    target = targets[simulation.POLICY_IDS[0]]
    ledger, summary = simulation.simulate_case(
        target, _demand([20.0] * 14), common_input_identity="stream"
    )
    path = tmp_path / "ledger.parquet"
    summary_path = tmp_path / "summary.parquet"
    target_path = tmp_path / "targets.parquet"
    pq.write_table(
        pa.Table.from_pylist([target], schema=simulation.POLICY_TARGET_SCHEMA), target_path
    )
    pq.write_table(pa.Table.from_pylist(ledger, schema=simulation.SIMULATION_LEDGER_SCHEMA), path)
    pq.write_table(
        pa.Table.from_pylist([summary], schema=simulation.POLICY_SUMMARY_SCHEMA), summary_path
    )
    result = simulation._validate_ledger_stream(
        path,
        expected_tracks=1,
        expected_rows=15,
        summary_path=summary_path,
        target_path=target_path,
    )
    assert result["queue_identity"] == "passed"
    assert result["daily_and_terminal_balances"] == "passed"
    assert result["invalid_foreign_keys"] == 0
    bad_summary = dict(summary, demand_total=summary["demand_total"] + 1)
    pq.write_table(
        pa.Table.from_pylist([bad_summary], schema=simulation.POLICY_SUMMARY_SCHEMA),
        summary_path,
    )
    with pytest.raises(simulation.SimulationIntegrityError, match="differs from the ledger"):
        simulation._validate_ledger_stream(
            path,
            expected_tracks=1,
            expected_rows=15,
            summary_path=summary_path,
            target_path=target_path,
        )

    bad_target = dict(target, case_id="other-case--reference")
    pq.write_table(
        pa.Table.from_pylist([bad_target], schema=simulation.POLICY_TARGET_SCHEMA), target_path
    )
    with pytest.raises(simulation.SimulationIntegrityError, match="foreign key"):
        simulation._validate_ledger_stream(
            path,
            expected_tracks=1,
            expected_rows=15,
            target_path=target_path,
        )


def test_public_output_validator_checks_paired_exogenous_identity():
    targets, target_table = _targets()
    target_rows = []
    ledger_rows = []
    summaries = []
    path = _demand([20.0] * 14)
    for policy_id in simulation.POLICY_IDS:
        target = dict(targets[policy_id])
        target.update(target_available=True, initial_stock_value=50.0)
        target_rows.append(target)
        ledger, summary = simulation.simulate_case(target, path, common_input_identity="equal")
        ledger_rows.extend(ledger)
        summaries.append(summary)
    target_table = pa.Table.from_pylist(target_rows, schema=simulation.POLICY_TARGET_SCHEMA)
    ledger_table = pa.Table.from_pylist(ledger_rows, schema=simulation.SIMULATION_LEDGER_SCHEMA)
    summary_table = pa.Table.from_pylist(summaries, schema=simulation.POLICY_SUMMARY_SCHEMA)
    comparison = pd.DataFrame(columns=["case_id", "metric"])
    result = simulation.validate_simulation_outputs(
        target_table, ledger_table, summary_table, comparison
    )
    assert result["paired_exogenous_identity"] == "passed"
    bad_summary = summary_table.to_pylist()
    bad_summary[1]["common_input_identity"] = "different"
    with pytest.raises(simulation.SimulationIntegrityError, match="exogenous identity"):
        simulation.validate_simulation_outputs(
            target_table,
            ledger_table,
            pa.Table.from_pylist(bad_summary, schema=simulation.POLICY_SUMMARY_SCHEMA),
            comparison,
        )


def test_pooled_comparison_ratios_use_summed_sufficient_statistics():
    targets, _ = _targets()
    summaries = []
    for store, demand_value in ((1, 20.0), (2, 200.0)):
        path = _demand([demand_value] * 14)
        for policy_id in simulation.POLICY_IDS:
            target = dict(targets[policy_id], Store=store, initial_stock_value=50.0)
            _, summary = simulation.simulate_case(
                target, path, common_input_identity=f"shared-{store}"
            )
            summaries.append(summary)
    rows = simulation._comparison_rows("fixture--reference", summaries)
    fill = next(row for row in rows if row["metric"] == "ValueFillRate")
    baseline = [row for row in summaries if row["policy_id"] == simulation.POLICY_IDS[0]]
    expected = sum(row["fulfilled_total"] for row in baseline) / sum(
        row["demand_total"] for row in baseline
    )
    average_of_store_rates = sum(row["ValueFillRate"] for row in baseline) / len(baseline)
    assert fill["baseline_value"] == pytest.approx(expected)
    assert fill["baseline_value"] != pytest.approx(average_of_store_rates)


def test_relative_cost_difference_is_null_when_baseline_cost_is_zero():
    targets, _ = _targets()
    summaries = []
    for policy_id in simulation.POLICY_IDS:
        target = dict(
            targets[policy_id],
            target_available=True,
            target_value=0.0,
            initial_stock_value=0.0,
        )
        _, summary = simulation.simulate_case(
            target, _demand([0.0] * 14), common_input_identity="zero-cost"
        )
        summaries.append(summary)
    cost = next(
        row
        for row in simulation._comparison_rows("fixture--reference", summaries)
        if row["metric"] == "SimulatedHoldingPlusShortfallCost"
    )
    assert cost["baseline_value"] == 0.0
    assert cost["forecast_minus_baseline"] == 0.0
    assert cost["forecast_minus_baseline_relative"] is None
    assert cost["relative_difference_null_reason"] == "zero_baseline_cost"


def test_lead_and_coverage_overlay_inputs_change_only_declared_fields(monkeypatch):
    monkeypatch.setattr(
        simulation,
        "_quantile_row",
        lambda *args: {"value": 10.0, "available": True, "reason": None},
    )
    scenario = {
        "scenario_id": "base-origin-a-r0",
        "forecast_origin": date(2015, 6, 5),
        "family": "synthetic_base",
        "mode": "synthetic_stress",
        "replicate": 0,
    }
    parameter = {
        "Store": 1,
        "SupplierLeadTime": 4,
        "InitialStockOnHandValue": 400.0,
        "ProcurementCostRatio": 0.70,
        "AnnualHoldingRate": 0.20,
        "GoodwillPenaltyRate": 0.50,
    }
    anchor = {"anchor_available": True, "mean_open_sales_value": 100.0}
    schedule = {f"{scenario['scenario_id']}\0{1}": {h: 1 for h in range(1, 9)}}
    points = {
        (1, scenario["forecast_origin"], h): {
            "raw_forecast": 20.0,
            "forecast_available": True,
            "source_open": 1.0,
        }
        for h in range(1, 9)
    }
    common = {
        "schedule_by_case": schedule,
        "point_by_key": points,
        "quantiles": pd.DataFrame(),
        "upstream_identity": "pinned",
    }
    coverage = simulation._build_case_target_inputs(
        scenario,
        {"id": "coverage_1", "InventoryCoverageDays": 1},
        parameter,
        anchor,
        **common,
    )
    assert {row["initial_stock_value"] for row in coverage} == {100.0}
    coverage_targets = simulation.build_policy_targets(pd.DataFrame(coverage))
    assert set(coverage_targets.column("initial_stock_value").to_pylist()) == {100.0}

    lead_seven = simulation._build_case_target_inputs(
        scenario,
        {"id": "lead_7", "SupplierLeadTime": 7},
        parameter,
        anchor,
        **common,
    )
    assert len(lead_seven) == 8
    assert {row["ProtectionPeriod"] for row in lead_seven} == {8}
    lead_targets = simulation.build_policy_targets(pd.DataFrame(lead_seven))
    baseline = next(
        row for row in lead_targets.to_pylist() if row["policy_id"] == simulation.POLICY_IDS[0]
    )
    ledger, _ = simulation.simulate_case(
        baseline, _demand([0.0] * 14), common_input_identity="lead-7"
    )
    assert ledger[0]["order_due_date"] == date(2015, 6, 13)


def test_emitted_target_stream_reconstructs_signed_target_arithmetic(tmp_path):
    _, targets = _targets(quantile=-20.0)
    path = tmp_path / "targets.parquet"
    pq.write_table(targets, path)
    result = simulation._validate_target_stream(path, expected_tracks=2)
    assert result["target_arithmetic"] == "passed"
    rows = pq.read_table(path).to_pylist()
    forecast = next(row for row in rows if row["policy_id"] == simulation.POLICY_IDS[1])
    forecast["target_value"] = 60.0
    pq.write_table(
        pa.Table.from_pylist(
            [row if row["policy_id"] != simulation.POLICY_IDS[1] else forecast for row in rows],
            schema=simulation.POLICY_TARGET_SCHEMA,
        ),
        path,
    )
    with pytest.raises(simulation.SimulationIntegrityError, match="arithmetic"):
        simulation._validate_target_stream(path, expected_tracks=2)


def test_protected_path_and_hash_spies_are_quiet_for_pinned_inputs(monkeypatch):
    repo = Path(__file__).resolve().parents[1]
    required = (
        repo / "data/processed/synthetic_inventory" / simulation.PHASE9_RUN_ID / "manifest.json"
    )
    if not required.is_file():
        pytest.skip("Canonical ignored upstream artifacts are not present in CI.")
    forbidden = ("holdout", "feature_inference", "data/raw", "data/interim/train")
    accessed: list[str] = []
    original_hash = simulation._sha256_file
    original_repo_file = simulation._repo_file
    original_scenario_hash = scenarios._sha256_file

    def checked_hash(path):
        value = str(path).replace("\\", "/").lower()
        accessed.append(value)
        assert not any(part in value for part in forbidden)
        return original_hash(path)

    def checked_repo_file(root, relative):
        value = relative.replace("\\", "/").lower()
        accessed.append(value)
        assert not any(part in value for part in forbidden)
        return original_repo_file(root, relative)

    def checked_scenario_hash(path):
        value = str(path).replace("\\", "/").lower()
        accessed.append(value)
        assert not any(part in value for part in forbidden)
        return original_scenario_hash(path)

    monkeypatch.setattr(simulation, "_sha256_file", checked_hash)
    monkeypatch.setattr(simulation, "_repo_file", checked_repo_file)
    monkeypatch.setattr(scenarios, "_sha256_file", checked_scenario_hash)
    result = simulation.verify_simulation_inputs(repo, origin="2015-06-19")
    assert result["protected_holdout_values_read_or_hashed"] is False
    assert accessed


def test_immutable_run_id_rejected_without_verification(monkeypatch, tmp_path):
    existing = tmp_path / "data/processed/inventory_simulation/run-a"
    existing.mkdir(parents=True)
    monkeypatch.setattr(simulation, "_assert_git_ignored", lambda *args: None)
    monkeypatch.setattr(
        simulation,
        "verify_simulation_inputs",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not verify")),
    )
    with pytest.raises(FileExistsError, match="already exists"):
        simulation.run_inventory_simulation(tmp_path, run_id="run-a")


def test_atomic_pointer_failure_removes_new_run_and_preserves_old_pointer(monkeypatch, tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    current = output_root / "current.json"
    current.write_text('{"run_id":"old"}\n', encoding="utf-8")
    stage = output_root / ".stage"
    stage.mkdir()
    (stage / "manifest.json").write_text("{}", encoding="utf-8")
    final = output_root / "new-run"
    original_replace = simulation.os.replace

    def fail_pointer(source, destination):
        if Path(destination) == current:
            raise OSError("simulated pointer replacement failure")
        return original_replace(source, destination)

    monkeypatch.setattr(simulation.os, "replace", fail_pointer)
    with pytest.raises(OSError, match="pointer replacement"):
        simulation._atomic_publish(stage, final, output_root, {"run_id": "new-run"})
    assert current.read_text(encoding="utf-8") == '{"run_id":"old"}\n'
    assert not final.exists()
    assert not list(output_root.glob(".current-*.tmp"))


def test_atomic_publish_moves_closed_parquet_stage_and_updates_pointer(tmp_path):
    output_root = tmp_path / "inventory_simulation"
    output_root.mkdir()
    stage = output_root / ".stage"
    stage.mkdir()
    target = _target(simulation.POLICY_IDS[0])
    pq.write_table(
        pa.Table.from_pylist([target], schema=simulation.POLICY_TARGET_SCHEMA),
        stage / "policy_targets.parquet",
    )
    reader = pq.ParquetFile(stage / "policy_targets.parquet")
    assert reader.metadata.num_rows == 1
    reader.close()
    final = output_root / "run-a"
    simulation._atomic_publish(stage, final, output_root, {"run_id": "run-a"})
    assert (final / "policy_targets.parquet").is_file()
    assert simulation._read_json(output_root / "current.json")["run_id"] == "run-a"


def test_historical_loader_projection_is_safe_and_cutoff_bounded(monkeypatch, tmp_path):
    calls = {}
    schema = pa.schema(
        [
            ("Store", pa.int64()),
            ("forecast_origin", pa.timestamp("ns")),
            ("Date", pa.timestamp("ns")),
            ("target_key_observed", pa.bool_()),
            ("actual_sales", pa.float64()),
            ("source_open", pa.float64()),
        ]
    )
    table = pa.Table.from_pylist(
        [
            {
                "Store": 1,
                "forecast_origin": pd.Timestamp("2015-06-05"),
                "Date": pd.Timestamp("2015-06-06"),
                "target_key_observed": True,
                "actual_sales": 10.0,
                "source_open": 1.0,
            }
        ],
        schema=schema,
    )

    class Dataset:
        def __init__(self):
            self.schema = schema

        def to_table(self, *, columns, filter, use_threads):
            calls["columns"] = columns
            calls["filter"] = filter
            calls["threads"] = use_threads
            return table

    monkeypatch.setattr(simulation, "_repo_file", lambda root, relative: tmp_path / "safe.parquet")
    monkeypatch.setattr(
        simulation.scenarios,
        "_verify_development_parquet_metadata",
        lambda *args, **kwargs: {"rows": 46_830, "maximum_date": "2015-07-03"},
    )
    monkeypatch.setattr(simulation.ds, "dataset", lambda *args, **kwargs: Dataset())
    inputs = {"repository": tmp_path}
    values = simulation._load_historical_outcomes(inputs)
    assert set(calls["columns"]) == {
        "Store",
        "forecast_origin",
        "Date",
        "target_key_observed",
        "actual_sales",
        "source_open",
    }
    assert "Customers" not in calls["columns"]
    assert values[(1, date(2015, 6, 5), 1)]["sales"] == 10.0
