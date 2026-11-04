"""Workbook content, live formulas, injection resistance and CLI regressions."""
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from openpyxl import load_workbook
import pytest

from analysis import fit_candidates, prepare_data, report_payload
from excel_report import create_excel_report


@pytest.fixture
def payload():
    source = np.arange(-5., 15.)
    fit = fit_candidates(source, ["Normal", "Uniform", "Not a distribution"])
    return report_payload(fit, source, {"source": "Synthetic arithmetic sequence", "outlier_method": "None"},
                          scenario=[0., 10., 20.])


def workbook(payload, cached=False):
    return load_workbook(BytesIO(create_excel_report(payload)), data_only=cached)


def test_values_split_indices_formulas_and_caches_match_analysis(payload):
    book = workbook(payload)
    cached = workbook(payload, cached=True)
    assert book.sheetnames == ["Review", "Candidates", "Observations"]
    threshold = payload["settings"]["tail_threshold"]
    for row, key in [(7, "train_indices"), (8, "held_indices"), (9, None)]:
        data = np.asarray(payload["scenario_data"] if key is None else
                          [payload["prepared_data"][i] for i in payload[key]])
        assert cached["Review"][f"B{row}"].value == len(data)
        assert cached["Review"][f"C{row}"].value == pytest.approx(data.mean())
        assert cached["Review"][f"D{row}"].value == int(sum(data > threshold))
        assert cached["Review"][f"E{row}"].value == pytest.approx(np.mean(data > threshold))
        assert book["Review"][f"D{row}"].value.startswith("=IF(")
    observations = book["Observations"]
    for i, value in enumerate(payload["prepared_data"]):
        row = 7 + i
        assert observations[f"A{row}"].value == i + 1
        assert observations[f"B{row}"].value == ("Training" if i in payload["train_indices"] else "Held-out")
        assert observations[f"C{row}"].value == value
    assert len(observations.tables) == 2
    assert observations.freeze_panes == "C7"
    assert len(book["Review"]._charts) == 1
    assert book["Review"].data_validations.dataValidation[0].sqref == "B4"
    assert book["Candidates"]["A2"].value == "Frozen model comparison"
    assert "Not a distribution" in [cell.value for cell in book["Candidates"]["A"]]


def test_absent_scenario_and_filtered_source_remain_explicit(payload):
    payload["scenario_data"] = []
    payload["source_data"] = ["nan", "inf", "-inf"] + payload["source_data"]
    book = workbook(payload, cached=True)
    assert book["Review"]["B9"].value == 0
    assert [book["Review"][f"{col}9"].value for col in "CDE"] == ["n.a."] * 3
    assert [book["Observations"][f"G{row}"].value for row in range(7, 10)] == ["nan", "inf", "-inf"]


def test_infinite_loss_and_multiple_failures_are_not_hidden(payload):
    payload["results"][0]["Held-out NLL"] = "inf"
    payload["failures"] = {"bad one": "failure one", "bad two": "failure two"}
    book = workbook(payload)
    assert book["Candidates"]["C7"].value == "inf"
    text = [cell.value for row in book["Candidates"] for cell in row if cell.value]
    assert all(value in text for value in ["bad one", "bad two", "failure one", "failure two"])


def test_untrusted_strings_never_become_formulas_or_external_links(payload):
    payload["settings"]["source"] = '=HYPERLINK("https://example.invalid","open")'
    payload["failures"] = {"=1+2": "https://example.invalid"}
    payload["source_data"] = ["=1+2", "@SUM(1,2)", "https://example.invalid"]
    book = workbook(payload)
    for sheet in book:
        for row in sheet:
            for cell in row:
                if sheet.title != "Review" or cell.coordinate not in {
                        f"{column}{r}" for column in "BCDE" for r in (7, 8, 9)}:
                    assert cell.data_type != "f"
                assert cell.hyperlink is None
    assert book["Observations"]["G7"].value == "=1+2"


@pytest.mark.parametrize("invalid", ["partition", "nonfinite", "too many", "threshold"])
def test_invalid_or_oversized_payloads_are_rejected(payload, invalid):
    if invalid == "partition":
        payload["train_indices"].append(payload["held_indices"][0])
    elif invalid == "nonfinite":
        payload["scenario_data"] = [float("nan")]
    elif invalid == "too many":
        payload["source_data"] = [1.] * 100_001
    else:
        payload["settings"]["tail_threshold"] = float("inf")
    with pytest.raises(ValueError):
        create_excel_report(payload)


def test_cli_sample_and_csv(tmp_path):
    output = tmp_path / "sample.xlsx"
    subprocess.run([sys.executable, "excel_report.py", "--sample", "--out", str(output)], check=True, capture_output=True)
    assert load_workbook(output, data_only=True)["Review"]["B7"].value == 180
    source = tmp_path / "input.csv"
    source.write_text("measurement\n" + "\n".join(str(i) for i in range(20)))
    subprocess.run([sys.executable, "excel_report.py", str(source), "--column", "measurement", "--out", str(output)],
                   check=True, capture_output=True)
    assert load_workbook(output, data_only=True)["Review"]["B7"].value == 15


@pytest.mark.parametrize("threshold", [0., -100., 100., None, "invalid"])
def test_real_engine_recalculates_changed_threshold(payload, tmp_path, threshold):
    engine = shutil.which("libreoffice") or shutil.which("soffice")
    if not engine:
        if os.environ.get("REQUIRE_SPREADSHEET_ENGINE"):
            pytest.fail("CI requires LibreOffice to execute the exported formulas")
        pytest.skip("Install LibreOffice to run the live spreadsheet recalculation tests")
    book = workbook(payload)
    book["Review"]["B4"] = threshold
    path = tmp_path / "input.xlsx"
    book.save(path)
    output = tmp_path / "recalculated"
    # Unique profile prevents touching a user's open office session. This command
    # waits for its owned headless process to exit; there is no detached server.
    subprocess.run([engine, f"-env:UserInstallation={(tmp_path / 'profile').as_uri()}",
                    "--headless", "--convert-to", "xlsx", "--outdir", str(output), str(path)],
                   check=True, timeout=60, capture_output=True)
    result = load_workbook(output / path.name, data_only=True)
    for row, key in [(7, "train_indices"), (8, "held_indices"), (9, None)]:
        data = payload["scenario_data"] if key is None else [payload["prepared_data"][i] for i in payload[key]]
        if threshold is None or isinstance(threshold, str):
            assert result["Review"][f"D{row}"].value == "n.a."
            assert result["Review"][f"E{row}"].value == "n.a."
        else:
            count = sum(value > threshold for value in data)
            assert result["Review"][f"D{row}"].value == count
            assert result["Review"][f"E{row}"].value == pytest.approx(count / len(data))
        assert result["Review"][f"C{row}"].value == pytest.approx(np.mean(data))
    for sheet in result:
        assert all(cell.data_type != "e" for cells in sheet for cell in cells)
