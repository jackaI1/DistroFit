"""Published OEE example, hand-calculated SMED study and real report workflows."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from equipment import build_equipment_report, export_report, load_example
from spc import calculate_oee, downtime_pareto, pareto_chart, smed_analysis

ROOT = Path(__file__).resolve().parents[1]
PAGE = str(ROOT / "pages" / "1_Equipment_effectiveness.py")
PUBLISHED = dict(shift_minutes=480, excluded_minutes=60, stop_minutes=47,
                 ideal_cycle_seconds=1, total_count=19271, good_count=18848)


def test_published_oee_example():
    # Vorne's worked example: https://www.oee.com/calculating-oee/
    # Hand-derived fractions are checked before rounding to published percents.
    result = calculate_oee(**PUBLISHED)
    assert result["planned_minutes"] == 420
    assert result["run_minutes"] == 373
    assert result["availability"] == pytest.approx(373 / 420)
    assert result["performance"] == pytest.approx(19271 / (373 * 60))
    assert result["quality"] == pytest.approx(18848 / 19271)
    assert result["oee"] == pytest.approx(18848 / (420 * 60))
    assert [round(result[k] * 100, 2) for k in ("availability", "performance", "quality", "oee")] == [88.81, 86.11, 97.80, 74.79]
    assert result["oee"] == pytest.approx(result["availability"] * result["performance"] * result["quality"])


def test_second_hand_calculated_example_and_loss_reconciliation():
    # 60 planned, 10 stopped, 40 ideal minutes of output, 30 ideal good minutes.
    result = calculate_oee(shift_minutes=70, excluded_minutes=10, stop_minutes=10,
                           ideal_cycle_seconds=30, total_count=80, good_count=60)
    assert result["availability"] == pytest.approx(5 / 6)
    assert result["performance"] == .8
    assert result["quality"] == .75
    assert result["oee"] == .5
    assert [result[k] for k in ("availability_loss_minutes", "performance_loss_minutes", "quality_loss_minutes", "fully_productive_minutes")] == [10, 10, 10, 30]


@pytest.mark.parametrize("stop,total,good,expected", [
    (0, 60, 60, (1, 1, 1, 1)),
    (0, 60, 0, (1, 1, 0, 0)),
    (0, 0, 0, (1, 0, None, 0)),
    (60, 0, 0, (0, None, None, 0)),
])
def test_perfect_scrap_no_output_and_fully_stopped_periods(stop, total, good, expected):
    result = calculate_oee(shift_minutes=60, excluded_minutes=0, stop_minutes=stop,
                           ideal_cycle_seconds=60, total_count=total, good_count=good)
    assert tuple(result[k] for k in ("availability", "performance", "quality", "oee")) == expected
    assert sum(result[k] for k in ("availability_loss_minutes", "performance_loss_minutes", "quality_loss_minutes", "fully_productive_minutes")) == 60
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("overrides", [
    {"shift_minutes": 0}, {"excluded_minutes": 480}, {"excluded_minutes": 481},
    {"stop_minutes": 421}, {"stop_minutes": -1}, {"ideal_cycle_seconds": 0},
    {"ideal_cycle_seconds": 2}, {"good_count": 20000}, {"total_count": 1.5},
    {"good_count": .5}, {"total_count": -1}, {"stop_minutes": 420},
])
def test_impossible_production_inputs_rejected(overrides):
    with pytest.raises(ValueError):
        calculate_oee(**(PUBLISHED | overrides))


@pytest.mark.parametrize("field", list(PUBLISHED))
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, "5", None])
def test_nonfinite_and_nonnumeric_inputs_rejected(field, value):
    with pytest.raises(ValueError, match="finite non-negative"):
        calculate_oee(**(PUBLISHED | {field: value}))


def test_downtime_is_ranked_by_time_and_repeated_reasons_aggregate():
    events = [{"category": "Frequent", "minutes": 1}] * 8 + [
        {"category": "Changeover", "minutes": 20}, {"category": " Breakdown ", "minutes": 7},
        {"category": "Breakdown", "minutes": 5}]
    table = downtime_pareto(events)
    assert list(table["Category"]) == ["Changeover", "Breakdown", "Frequent"]
    assert list(table["Minutes"]) == [20, 12, 8]
    assert list(table["Events"]) == [1, 2, 8]
    assert list(table["Percent"]) == [50, 30, 20]
    assert list(table["Cumulative %"]) == [50, 80, 100]
    assert list(table["Vital few"]) == [True, True, False]
    figure = pareto_chart(table, value_column="Minutes", ylabel="Stopped minutes")
    try:
        assert figure.axes[0].get_ylabel() == "Stopped minutes"
        assert [bar.get_height() for bar in figure.axes[0].patches] == [20, 12, 8]
    finally:
        figure.clear()


def test_pareto_stable_ties_empty_and_zero_duration():
    assert list(downtime_pareto([{"category": c, "minutes": 2} for c in ["B", "A"]])["Category"]) == ["B", "A"]
    assert downtime_pareto([]).empty
    zero = downtime_pareto([{"category": "No stop", "minutes": 0}])
    assert zero["Percent"].sum() == 0
    assert not zero["Vital few"].any()


@pytest.mark.parametrize("events", [
    [{"category": "", "minutes": 5}], [{"category": None, "minutes": 5}],
    [{"category": "A", "minutes": -1}], [{"category": "A", "minutes": np.nan}],
    [{"category": "A", "minutes": "ten"}], [{"category": "A"}],
    [{"category": "A", "minutes": True}],
])
def test_bad_downtime_rejected(events):
    with pytest.raises(ValueError):
        downtime_pareto(events)


def test_smed_externalizes_preparation_and_streamlines_internal_work():
    _, _, tasks = load_example()
    result = smed_analysis(tasks)
    # Hand calculation: baseline 6+5+7+2 = 20; proposal 4+5+2 = 11.
    assert result["baseline_stop_minutes"] == 20
    assert result["proposed_stop_minutes"] == 11
    assert result["saved_stop_minutes"] == 9
    assert result["reduction_percent"] == 45
    assert result["baseline_external_minutes"] == 4
    assert result["proposed_external_minutes"] == 10  # six minutes moved, not eliminated
    assert list(result["tasks"]["saved_stop_minutes"]) == [6, 2, 1, 0, 0]
    assert tasks.columns.tolist() == ["step", "minutes", "kind", "proposed_minutes", "proposed_kind"]


def test_empty_external_only_and_worsening_changeover():
    assert smed_analysis([])["reduction_percent"] is None
    external = [{"step": "Prepare", "minutes": 4, "kind": "external",
                 "proposed_minutes": 6, "proposed_kind": "external"}]
    assert smed_analysis(external)["saved_stop_minutes"] == 0
    slower = [{"step": "Align", "minutes": 4, "kind": "internal",
               "proposed_minutes": 6, "proposed_kind": "internal"}]
    assert smed_analysis(slower)["saved_stop_minutes"] == -2
    assert smed_analysis(slower)["reduction_percent"] == -50


@pytest.mark.parametrize("field,value", [("step", " "), ("kind", "parallel"),
    ("proposed_kind", None), ("minutes", -1), ("proposed_minutes", float("inf"))])
def test_invalid_changeover_tasks_rejected(field, value):
    task = dict(step="Align", minutes=4, kind="internal", proposed_minutes=3, proposed_kind="internal")
    with pytest.raises(ValueError):
        smed_analysis([task | {field: value}])


def test_duplicate_tasks_and_duplicate_table_columns_rejected():
    _, _, tasks = load_example()
    with pytest.raises(ValueError, match="unique"):
        smed_analysis(pd.concat([tasks, tasks.iloc[:1]]))
    with pytest.raises(ValueError, match="unique columns"):
        downtime_pareto(pd.DataFrame([["A", 1, 2]], columns=["category", "minutes", "minutes"]))


def test_report_uses_same_downtime_total_and_does_not_apply_smed_estimates(tmp_path):
    shift, stops, tasks = load_example()
    report = build_equipment_report(shift, stops, tasks)
    assert report["oee"]["stop_minutes"] == report["downtime"]["Minutes"].sum() == 47
    assert report["oee"]["oee"] == pytest.approx(.7479365079365079)
    assert report["changeover"]["saved_stop_minutes"] == 9
    assert build_equipment_report(shift, stops)["oee"] == report["oee"]
    export_report(report, tmp_path)
    assert json.loads((tmp_path / "oee.json").read_text()) == report["oee"]
    assert pd.read_csv(tmp_path / "downtime_pareto.csv")["Minutes"].sum() == 47
    assert (tmp_path / "downtime_pareto.png").read_bytes().startswith(b"\x89PNG")
    assert json.loads((tmp_path / "changeover.json").read_text())["proposed_stop_minutes"] == 11
    assert len(pd.read_csv(tmp_path / "changeover_tasks.csv")) == 5


@pytest.mark.parametrize("shift", [[], {}, {"stop_minutes": 5}])
def test_report_rejects_incomplete_or_independent_stop_inputs(shift):
    with pytest.raises(ValueError):
        build_equipment_report(shift, [])


def test_cli_custom_files_and_invalid_input(tmp_path):
    result = subprocess.run([sys.executable, "equipment.py", "--shift", "examples/oee/shift.json",
                             "--downtime", "examples/oee/downtime.csv", "--changeover", "examples/oee/changeover.csv",
                             "--out", str(tmp_path / "valid")], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "74.79%" in result.stdout
    bad = tmp_path / "bad.csv"
    bad.write_text("category,minutes\nBreakdown,500\n")
    result = subprocess.run([sys.executable, "equipment.py", "--shift", "examples/oee/shift.json",
                             "--downtime", str(bad), "--out", str(tmp_path / "invalid")],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "cannot exceed" in result.stderr
    assert not (tmp_path / "invalid").exists()


def test_cli_sample_and_empty_stop_log(tmp_path):
    result = subprocess.run([sys.executable, "equipment.py", "--sample", "--out", str(tmp_path / "sample")],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    shift, _, _ = load_example()
    report = build_equipment_report(shift, pd.DataFrame(columns=["category", "minutes"]))
    export_report(report, tmp_path / "no-stops")
    assert report["oee"]["availability"] == 1


def test_equipment_page_sample_changes_and_stale_result_prevention():
    app = AppTest.from_file(PAGE, default_timeout=30).run()
    assert not app.exception
    assert {m.label: m.value for m in app.metric}["OEE"] == "74.79%"
    assert len(app.get("download_button")) == 2
    next(w for w in app.number_input if w.label == "First-pass good parts").set_value(18000).run()
    assert not app.exception
    assert app.session_state["equipment_report"]["oee"]["good_count"] == 18000
    next(w for w in app.number_input if w.label == "Ideal cycle time (seconds per part)").set_value(2.).run()
    assert not app.exception
    assert "Performance exceeds 100%" in app.error[0].value
    assert "equipment_report" not in app.session_state
    assert not app.get("download_button")


def test_equipment_page_edit_stop_and_changeover_tables():
    app = AppTest.from_file(PAGE, default_timeout=30).run()
    # Emulate the exact editor deltas Streamlit receives from table edits.
    app.session_state["stops"] = {"edited_rows": {0: {"minutes": 10}}, "added_rows": [], "deleted_rows": []}
    app.session_state["tasks"] = {"edited_rows": {0: {"proposed_kind": "internal"}}, "added_rows": [], "deleted_rows": []}
    app.run()
    assert not app.exception
    assert app.session_state["equipment_report"]["oee"]["stop_minutes"] == 37
    assert app.session_state["equipment_report"]["changeover"]["saved_stop_minutes"] == 3


def test_equipment_page_fractional_minutes_and_empty_optional_tables():
    app = AppTest.from_file(PAGE, default_timeout=30).run()
    app.session_state["stops"] = {"edited_rows": {0: {"minutes": 10.5}}, "added_rows": [], "deleted_rows": []}
    app.session_state["tasks"] = {"edited_rows": {1: {"proposed_minutes": 3.5}}, "added_rows": [], "deleted_rows": []}
    app.run()
    assert not app.exception
    assert app.session_state["equipment_report"]["oee"]["stop_minutes"] == 37.5
    assert app.session_state["equipment_report"]["changeover"]["saved_stop_minutes"] == 9.5
    app.session_state["stops"] = {"edited_rows": {}, "added_rows": [], "deleted_rows": [0, 1, 2, 3]}
    app.session_state["tasks"] = {"edited_rows": {}, "added_rows": [], "deleted_rows": [0, 1, 2, 3, 4]}
    app.run()
    assert not app.exception
    assert app.session_state["equipment_report"]["oee"]["availability"] == 1
    assert app.session_state["equipment_report"]["downtime"].empty
    assert app.session_state["equipment_report"]["changeover"]["tasks"].empty
