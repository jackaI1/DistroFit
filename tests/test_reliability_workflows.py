"""Run the real reliability page, CLI and diagnostic/export workflows."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from reliability import analyze_lifetimes
from reliability_report import export_report, generate_demo, reliability_figure

ROOT = Path(__file__).resolve().parents[1]
PAGE = str(ROOT / "pages/2_Reliability.py")


def test_generated_equipment_log_reproduces_committed_data_and_uses_suspensions():
    demo = generate_demo()
    pd.testing.assert_frame_equal(demo, pd.read_csv(ROOT / "examples/reliability/equipment_log.csv"))
    assert len(demo) == 80
    assert 20 < demo.failed.sum() < 70
    assert demo.unit_id.is_unique
    report = analyze_lifetimes(demo)
    assert len(report["fits"]) == 3
    censored = next(f for f in report["fits"] if f["model"] == "weibull")
    naive = analyze_lifetimes(demo.loc[demo.failed == 1])
    failure_only = next(f for f in naive["fits"] if f["model"] == "weibull")
    assert censored["mean_life"]["estimate"] > failure_only["mean_life"]["estimate"] * 1.15


@pytest.mark.parametrize("model", ["weibull", "lognormal", "exponential"])
def test_probability_diagnostics_use_empirical_censored_failures(model):
    report = analyze_lifetimes(generate_demo())
    figure = reliability_figure(report, model=model)
    try:
        assert len(figure.axes) == 3
        survival, hazard, probability = figure.axes
        assert "Survival" in survival.get_ylabel()
        assert "per hour" in hazard.get_ylabel()
        assert "probability" in probability.get_title().lower()
        # Empirical points come from failure jumps, with no censored-as-failed ranks.
        km = pd.DataFrame(report["kaplan_meier"])
        expected = km[(km.failures > 0) & (km.survival > 0) & (km.survival < 1)]
        scatter = probability.collections[0].get_offsets()
        np.testing.assert_allclose(np.asarray(scatter[:, 0]), expected.time.to_numpy())
        assert len(scatter) == len(expected)
        assert len(survival.lines) >= 4  # empirical plus all three fitted curves
        assert len(hazard.lines) == 3
    finally:
        figure.clear()


def test_exports_are_readable_finite_and_never_overwrite(tmp_path):
    report = analyze_lifetimes(generate_demo())
    out = tmp_path / "report"
    export_report(report, out)
    assert json.loads((out / "reliability.json").read_text()) == report
    assert len(pd.read_csv(out / "observations.csv")) == 80
    assert len(pd.read_csv(out / "models.csv")) == 3
    curves = pd.read_csv(out / "curves.csv")
    assert set(curves.model) == {"weibull", "lognormal", "exponential"}
    assert np.isfinite(curves[["time", "survival", "hazard"]].to_numpy()).all()
    assert curves.survival.between(0, 1).all()
    assert (out / "reliability.png").read_bytes().startswith(b"\x89PNG")
    assert pd.read_csv(out / "kaplan_meier.csv").suspended.sum() == report["summary"]["suspensions"]
    original = (out / "reliability.json").read_bytes()
    with pytest.raises(FileExistsError):
        export_report(report, out)
    assert (out / "reliability.json").read_bytes() == original


def run_cli(*args):
    return subprocess.run([sys.executable, "reliability_report.py", *map(str, args)], cwd=ROOT,
                          capture_output=True, text=True, timeout=30)


def test_cli_sample_and_custom_csv_produce_the_same_results(tmp_path):
    sample = run_cli("--sample", "--out", tmp_path / "sample")
    assert sample.returncode == 0, sample.stderr
    assert "80 units" in sample.stdout
    custom = run_cli("examples/reliability/equipment_log.csv", "--confidence", ".99", "--out", tmp_path / "csv")
    assert custom.returncode == 0, custom.stderr
    a = json.loads((tmp_path / "sample/reliability.json").read_text())
    b = json.loads((tmp_path / "csv/reliability.json").read_text())
    assert b["confidence"] == .99
    assert a["summary"] == b["summary"]
    assert a["fits"][0]["mean_life"]["estimate"] == pytest.approx(b["fits"][0]["mean_life"]["estimate"])
    again = run_cli("--sample", "--out", tmp_path / "sample")
    assert again.returncode == 2


def test_cli_bad_rows_fail_without_creating_report(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("time,failed\n12,1\n15,running\n")
    result = run_cli(path, "--out", tmp_path / "invalid")
    assert result.returncode == 2
    assert "failed" in result.stderr
    assert not (tmp_path / "invalid").exists()


def test_all_censored_report_exports_without_fitted_curves(tmp_path):
    report = analyze_lifetimes(pd.DataFrame({"time": [10, 20], "failed": [0, 0]}))
    export_report(report, tmp_path / "censored")
    assert pd.read_csv(tmp_path / "censored/models.csv").empty
    assert pd.read_csv(tmp_path / "censored/curves.csv").empty
    assert json.loads((tmp_path / "censored/reliability.json").read_text())["excluded"]


def test_page_demo_confidence_selection_and_planning_age():
    app = AppTest.from_file(PAGE, default_timeout=30).run()
    assert not app.exception
    assert app.session_state["reliability_report"]["summary"]["units"] == 80
    assert len(app.get("download_button")) == 3
    app.selectbox(key="life_model").set_value("exponential").run()
    app.selectbox(key="life_confidence").set_value(.99).run()
    app.number_input(key="planning_age").set_value(400.).run()
    assert not app.exception
    assert app.session_state["reliability_report"]["confidence"] == .99
    metrics = {m.label: m.value for m in app.metric}
    assert "Mean life (MTTF / renewal MTBF)" in metrics
    assert "Survival at 400 hours" in metrics


def test_page_invalid_edit_clears_old_downloads_then_all_censored_stays_usable():
    app = AppTest.from_file(PAGE, default_timeout=30).run()
    app.session_state["life_log"] = {"edited_rows": {0: {"time": -10}}, "added_rows": [], "deleted_rows": []}
    app.run()
    assert not app.exception
    assert app.error
    assert "reliability_report" not in app.session_state
    assert not app.get("download_button")
    app.session_state["life_log"] = {"edited_rows": {i: {"failed": 0} for i in range(80)},
                                      "added_rows": [], "deleted_rows": []}
    app.run()
    assert not app.exception
    assert not app.session_state["reliability_report"]["fits"]
    assert app.warning
    assert len(app.get("download_button")) == 3
