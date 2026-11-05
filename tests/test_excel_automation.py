"""Exercise the delivered VBA and M code as well as the workbook builder."""
from io import BytesIO
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
import pytest
from pyopenvba import ExcelFile, PowerQueryWorkbook
from pyopenvba.apps.excel import ExcelApplication
from pyopenvba.mlang import evaluate_query

from excel_automation import create_automation_workbook

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def built(tmp_path):
    samples = {"Batch A": np.arange(1., 25.), "Batch B": np.linspace(10., 40., 30)}
    path = tmp_path / "review.xlsm"
    path.write_bytes(create_automation_workbook(samples, candidates=["Normal", "Exponential"]))
    return path


def test_embedded_form_sources_query_and_charts(built):
    with ExcelFile(built) as book:
        form = book.forms()[0]
        assert form.name == "ReviewForm"
        assert {c.name for c in form.walk()} >= {"DatasetBox", "DistributionBox", "RefreshButton", "StatusLabel"}
        for name in ("ReviewAutomation", "ReviewForm"):
            assert (ROOT / "automation/vba" / f"{name}.bas").read_text().strip() in book.get_module(name).replace("\r\n", "\n")
    with PowerQueryWorkbook(built) as book:
        assert "Csv.Document" in book.query("LegacyImport").formula
    book = load_workbook(built, keep_vba=True)
    assert len(book["Comparison"]._charts) == 2
    assert book["Comparison"]["B3"].value == "Batch A"
    assert len(book["ModelStore"].tables) == 1
    assert book["Raw"]["A1"].value.strip() == "dataset"


def test_vba_refresh_executes_and_rejects_unknown_selection(built):
    app = ExcelApplication.open(built)
    assert app.run("RefreshReview", "Batch B", "Normal")
    view = app.sheet("Comparison")
    assert view.value("B3") == "Batch B"
    assert view.value("B4") == "Normal"
    assert view.value("A10") == "Normal" or view.value("A11") == "Normal"
    assert isinstance(view.value("J10"), float)
    before = view.value("A10:G11")
    assert not app.run("RefreshReview", "missing", "Normal")
    assert view.value("A10:G11") == before
    assert not app.run("RefreshReview", "Batch A", "missing")
    assert view.value("B3") == "Batch B"


def test_generated_scores_match_existing_python_engine(built):
    from analysis import fit_candidates
    expected = fit_candidates(np.arange(1., 25.), ["Normal", "Exponential"])
    book = load_workbook(built, data_only=True)
    rows = list(book["ModelStore"].values)[1:]
    for model in expected["results"]:
        row = next(r for r in rows if r[0:2] == ("Batch A", model["Distribution"]))
        assert row[3] == pytest.approx(model["Held-out NLL"])


@pytest.mark.parametrize("samples", [{}, {"": [1, 2]}, {"a": [1, float('nan')]}, {"a": [2.] * 20}, {"a": range(7)}])
def test_invalid_dataset_rejected(samples):
    with pytest.raises(ValueError):
        create_automation_workbook(samples)


def test_formula_like_dataset_names_are_literal():
    book = load_workbook(BytesIO(create_automation_workbook({"=1+2": np.arange(20.)}, candidates=["Normal"])))
    assert book["DatasetIndex"]["A2"].data_type == "s"


def test_actual_power_query_standardizes_legacy_csv():
    code = (ROOT / "automation/power-query/LegacyImport.pq").read_text()
    # Inject the binary source only. All transformation steps are the delivered M.
    source = (ROOT / "automation/power-query/legacy_measurements.csv").read_bytes()
    table = evaluate_query(code, {"LegacyCsvBinary": source})
    assert table.columns == ["dataset", "value", "unit", "source_row", "import_flag"]
    assert len(table.rows) == 6
    assert table.rows[0][:3] == ["Legacy seal", 12.5, "mm"]
    assert [r[4] for r in table.rows] == ["OK", "OK", "BLANK", "INVALID_NUMBER", "BLANK", "OK"]


@pytest.mark.parametrize("template", [False, True])
def test_excel_package_declares_correct_macro_content_type(template):
    from zipfile import ZipFile
    data = create_automation_workbook({"Example": np.arange(20.)}, candidates=["Normal"], template=template)
    with ZipFile(BytesIO(data)) as archive:
        kind = "template" if template else "sheet"
        assert f'application/vnd.ms-excel.{kind}.macroEnabled.main+xml'.encode() in archive.read("[Content_Types].xml")
        assert b'vbaProject' in archive.read('xl/_rels/workbook.xml.rels')


@pytest.mark.parametrize("samples", [
    {"Batch": np.arange(20.), " batch ": np.arange(20.)},
    {"a": np.arange(100001.)},
    {"a": np.ones((8, 2))},
])
def test_ambiguous_oversized_and_nondimensional_data_rejected(samples):
    with pytest.raises(ValueError):
        create_automation_workbook(samples)


def test_cli_builds_both_deliverable_formats(tmp_path):
    import subprocess
    import sys
    for suffix in ("xlsm", "xltm"):
        out = tmp_path / f"sample.{suffix}"
        result = subprocess.run([sys.executable, "excel_automation.py", "--sample", "--out", str(out)],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert out.stat().st_size > 10000


def test_vba_changes_curve_plot_and_preserves_a_malformed_plot(built):
    app = ExcelApplication.open(built)
    assert app.run("RefreshReview", "Batch A", "Normal")
    first = app.sheet("Comparison").value("K10:K49")
    assert app.run("RefreshReview", "Batch A", "Exponential")
    assert app.sheet("Comparison").value("K10:K49") != first
    before = app.sheet("Comparison").value("I10:K49")
    app.sheet("PlotStore").set_value("C2", "invalid")
    assert not app.run("RefreshReview", "Batch A", "Normal")
    assert app.sheet("Comparison").value("I10:K49") == before


def test_power_query_rejects_missing_required_columns():
    from pyopenvba.mlang import MError
    code = (ROOT / "automation/power-query/LegacyImport.pq").read_text()
    with pytest.raises(MError):
        evaluate_query(code, {"LegacyCsvBinary": b"dataset;measurement;unit\na;3;mm\n"})


def test_actual_form_event_code_in_a_control_sandbox(built):
    """Run unchanged handlers with minimal combo/label controls, not an MSForms GUI."""
    app = ExcelApplication.open(built)
    app.add_module('''
Public Value As String
Public ListCount As Long
Public Style As Long
Private selected As Long
Private items() As String
Public Sub Clear()
    ListCount = 0
    selected = -1
    Value = ""
End Sub
Public Sub AddItem(ByVal item As String)
    ReDim Preserve items(ListCount)
    items(ListCount) = item
    ListCount = ListCount + 1
End Sub
Public Property Get ListIndex() As Long
    ListIndex = selected
End Property
Public Property Let ListIndex(ByVal index As Long)
    selected = index
    If index >= 0 Then Value = items(index)
End Property
''', name="TestCombo", kind="class")
    app.add_module("Public Caption As String", name="TestLabel", kind="class")
    code = (ROOT / "automation/vba/ReviewForm.bas").read_text()
    code = code.replace("Option Explicit", """Option Explicit
Public DatasetBox As TestCombo
Public DistributionBox As TestCombo
Public StatusLabel As TestLabel
Public Sub Prepare()
    Set DatasetBox = New TestCombo
    Set DistributionBox = New TestCombo
    Set StatusLabel = New TestLabel
    UserForm_Initialize
    DatasetBox_Change
End Sub
Public Sub ChooseSecondDataset()
    DatasetBox.ListIndex = 1
    DatasetBox_Change
End Sub
Public Sub ApplySelection()
    RefreshButton_Click
End Sub
""", 1)
    app.add_module(code, name="FormControlSandbox", kind="class")
    app.add_module('''
Public Sub ExerciseForm()
    Dim form As New FormControlSandbox
    form.Prepare
    ThisWorkbook.Worksheets("Comparison").Range("M1").Value2 = form.DatasetBox.ListCount
    form.ChooseSecondDataset
    form.ApplySelection
    ThisWorkbook.Worksheets("Comparison").Range("M2").Value2 = form.StatusLabel.Caption
    form.DistributionBox.ListIndex = -1
    form.ApplySelection
    ThisWorkbook.Worksheets("Comparison").Range("M3").Value2 = form.StatusLabel.Caption
End Sub
''', name="ControlSandboxTest")
    app.run("ExerciseForm")
    view = app.sheet("Comparison")
    assert view.value("M1") == 2
    assert view.value("B3") == "Batch B"
    assert view.value("M2") == "Comparison and both charts updated."
    assert view.value("M3") == "Choose both a dataset and a curve."


def test_infinite_scores_stay_visible_but_never_enter_numeric_chart_cache():
    from zipfile import ZipFile
    data = create_automation_workbook({"Bounded": np.random.default_rng(2).uniform(1, 10, 30)},
                                      candidates=["Normal", "Uniform"])
    cached = load_workbook(BytesIO(data), data_only=True)
    formula = load_workbook(BytesIO(data), data_only=False)
    row = next(r for r in range(10, 24) if cached['Comparison'][f'C{r}'].value == 'inf')
    assert cached['Comparison'][f'L{row}'].data_type == 'e'
    assert cached['Comparison'][f'L{row}'].value == '#N/A'
    assert formula['Comparison'][f'L{row}'].value == f'=IF(ISNUMBER(C{row}),C{row},NA())'
    with ZipFile(BytesIO(data)) as archive:
        chart = archive.read('xl/charts/chart1.xml')
        assert b'<c:v>inf</c:v>' not in chart
        assert b'Comparison!$L$10:$L$23' in chart


@pytest.mark.parametrize('value', ['1e309', '-1e309', 'NaN', 'Infinity'])
def test_power_query_never_marks_nonfinite_numbers_as_accepted(value):
    code = (ROOT / "automation/power-query/LegacyImport.pq").read_text()
    table = evaluate_query(code, {"LegacyCsvBinary": f'dataset;value;unit\nA;{value};mm\n'.encode()})
    assert table.rows[0][4] == 'INVALID_NUMBER'
    assert table.rows[0][1] is None
