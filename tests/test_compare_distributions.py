"""Real fits and independent score checks for portable comparison bundles."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest
from scipy import stats

import compare_distributions as compare


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def comparison():
    values, scenario = compare.sample_data()
    return compare.build_comparison(values, scenario=scenario)


def test_parameters_use_only_training_and_scenario_keeps_them_frozen(comparison):
    payload = comparison["analysis"]
    training = np.array(payload["prepared_data"])[payload["train_indices"]]
    held = np.array(payload["prepared_data"])[payload["held_indices"]]
    normal = next(row for row in payload["results"] if row["Distribution"] == "Normal")
    np.testing.assert_allclose(normal["Parameters"], [training.mean(), training.std()])
    assert not set(payload["train_indices"]) & set(payload["held_indices"])
    assert len(training) == 180 and len(held) == 60
    assert normal["Held-out NLL"] == pytest.approx(-stats.norm.logpdf(held, *normal["Parameters"]).mean())
    scenario_normal = next(row for row in payload["scenario_results"] if row["Distribution"] == "Normal")
    assert scenario_normal["Scenario NLL"] == pytest.approx(
        -stats.norm.logpdf(payload["scenario_data"], *normal["Parameters"]).mean())
    assert scenario_normal["Tail"]["flagged"] is True
    assert scenario_normal["Tail"]["threshold"] == pytest.approx(np.quantile(training, .95))


def test_bundle_is_strict_json_has_readable_pdf_and_verifies_without_refitting(tmp_path, comparison):
    folder = tmp_path / "result"
    compare.write_bundle(comparison, folder)
    assert json.loads((folder / "comparison.json").read_text()) == comparison
    pdf = (folder / "comparison.pdf").read_bytes()
    assert pdf.startswith(b"%PDF-")
    assert b"DistroFit reproducible report" in pdf
    assert b'"source_data": [' in pdf and b'"scenario_results": [' in pdf
    assert str(comparison["analysis"]["source_data"][0]).encode() in pdf
    with patch.object(compare, "fit_candidates", side_effect=AssertionError("verification must not refit")):
        summary = compare.verify_bundle(folder)
    assert summary == {"winner": "Gamma", "training": 180, "held_out": 60, "scenario": 60, "candidates": 3}
    with (folder / "scores.csv").open(newline="") as source:
        rows = list(csv.DictReader(source))
    assert rows[0]["distribution"] == "Gamma"
    assert {row["scenario_observations"] for row in rows} == {"60"}


def test_json_is_reproducible_and_no_scenario_stays_absent(tmp_path):
    values, _ = compare.sample_data()
    first = compare.build_comparison(values)
    assert first == compare.build_comparison(values)
    assert first["analysis"]["scenario_data"] == []
    folder = tmp_path / "result"
    compare.write_bundle(first, folder)
    assert compare.verify_bundle(folder)["scenario"] == 0


@pytest.mark.parametrize("name", compare.ARTIFACTS)
def test_each_changed_artifact_is_detected(tmp_path, comparison, name):
    folder = tmp_path / "result"
    compare.write_bundle(comparison, folder)
    with (folder / name).open("ab") as artifact:
        artifact.write(b"changed")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        compare.verify_bundle(folder)


@pytest.mark.parametrize("field", ["held_indices", "tail_threshold", "Held-out NLL", "scenario_results", "scores.csv"])
def test_rechecks_statistics_even_if_someone_updates_checksums(tmp_path, comparison, field):
    folder = tmp_path / "result"
    changed = copy.deepcopy(comparison)
    payload = changed["analysis"]
    if field == "held_indices":
        payload[field][0] = payload["train_indices"][0]
    elif field == "tail_threshold":
        payload["settings"][field] += 1
    elif field == "Held-out NLL":
        payload["results"][0][field] += 1
    elif field == "scenario_results":
        payload[field][0]["Scenario NLL"] += 1
    compare.write_bundle(changed, folder)
    if field == "scores.csv":
        (folder / field).write_text("invented results\n")
        manifest = json.loads((folder / "manifest.json").read_text())
        manifest["sha256"][field] = hashlib.sha256((folder / field).read_bytes()).hexdigest()
        (folder / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        compare.verify_bundle(folder)


def test_manifest_cannot_redirect_verifier_to_an_arbitrary_file(tmp_path, comparison):
    folder = tmp_path / "result"
    compare.write_bundle(comparison, folder)
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["sha256"]["../outside"] = "pretend"
    (folder / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="manifest"):
        compare.verify_bundle(folder)


def test_outside_support_keeps_explicit_infinite_scenario_loss(tmp_path):
    values, _ = compare.sample_data()
    result = compare.build_comparison(values, candidates=("Exponential",), scenario=[-100, -200])
    assert result["analysis"]["scenario_results"][0]["Scenario NLL"] == "inf"
    folder = tmp_path / "result"
    compare.write_bundle(result, folder)
    assert compare.verify_bundle(folder)["scenario"] == 2


@pytest.mark.parametrize("values,options", [
    ([1, 2, float("nan"), 3, 4, 5, 6, 7], {}),
    ([1] * 10, {}),
    (list(range(20)), {"bins": 0}),
    (list(range(20)), {"seed": -1}),
    (list(range(20)), {"held_out_fraction": .9}),
    (list(range(20)), {"candidates": ["Unknown"]}),
    (list(range(20)), {"scenario": []}),
])
def test_invalid_input_is_rejected_without_dropping_observations(values, options):
    with pytest.raises(ValueError):
        compare.build_comparison(values, **options)


def test_csv_headerless_first_row_and_invalid_columns(tmp_path):
    source = tmp_path / "values.csv"
    source.write_text("1\n2\n3\n4\n")
    np.testing.assert_array_equal(compare.load_column(source, "Column 1"), [1, 2, 3, 4])
    with pytest.raises(ValueError, match="missing"):
        compare.load_column(source, "weight")
    for text in ("weight\n1\n\n3\n", "weight\n1\n3\nNaN\n"):
        source.write_text(text)
        with pytest.raises(ValueError, match="finite"):
            compare.load_column(source, "weight")


def test_existing_output_is_preserved_and_render_failure_leaves_no_bundle(tmp_path, comparison):
    folder = tmp_path / "result"
    folder.mkdir()
    original = folder / "original.txt"
    original.write_text("keep this")
    with pytest.raises(ValueError, match="already exists"):
        compare.write_bundle(comparison, folder)
    assert original.read_text() == "keep this"
    missing = tmp_path / "failed"
    with patch.object(compare, "create_report", side_effect=RuntimeError("render failed")):
        with pytest.raises(RuntimeError, match="render failed"):
            compare.write_bundle(comparison, missing)
    assert not missing.exists()


def test_failed_fit_is_recorded_and_all_failed_fits_create_no_result():
    values, _ = compare.sample_data()
    with patch.object(compare, "fit_candidates", return_value={"results": [], "errors": {"Normal": "failed"}}):
        with pytest.raises(ValueError, match="No candidate"):
            compare.build_comparison(values, candidates=["Normal"])
    # A failed candidate remains visible alongside a valid fit.
    import analysis
    actual_fit = analysis.fit_candidates

    def one_failure(*args, **kwargs):
        fit = actual_fit(*args, **kwargs)
        fit["results"] = [row for row in fit["results"] if row["Distribution"] != "Gamma"]
        fit["errors"]["Gamma"] = "RuntimeError: synthetic optimizer failure"
        return fit

    with patch.object(compare, "fit_candidates", side_effect=one_failure):
        result = compare.build_comparison(values)
    assert result["analysis"]["failures"]["Gamma"] == "RuntimeError: synthetic optimizer failure"


def _run(*args):
    return subprocess.run([sys.executable, "compare_distributions.py", *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=60)


def test_documented_commands_run_in_separate_processes(tmp_path):
    output = tmp_path / "sample"
    fitted = _run("fit", "--sample", "--out", output)
    assert fitted.returncode == 0, fitted.stderr
    verified = _run("verify", output)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["winner"] == "Gamma"
    values, scenario = compare.sample_data()
    source, challenge = tmp_path / "measurements.csv", tmp_path / "challenge.csv"
    source.write_text("value\n" + "\n".join(map(str, values)))
    challenge.write_text("value\n" + "\n".join(map(str, scenario)))
    own = _run("fit", "--input", source, "--column", "value", "--scenario", challenge,
               "--candidate", "Normal", "--out", tmp_path / "own")
    assert own.returncode == 0, own.stderr
    assert json.loads(own.stdout.splitlines()[-1])["candidates"] == 1
    invalid = _run("fit", "--input", source, "--out", tmp_path / "invalid")
    assert invalid.returncode != 0 and "requires --column" in invalid.stderr
    assert not (tmp_path / "invalid").exists()
