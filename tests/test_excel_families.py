"""Family lookup (VLOOKUP), SUMIF/SUMIFS summaries and the native pivot over observations.

Each check reads the workbook back and compares it with pandas computed from the same
rows. The pivot is checked at the XML level, because openpyxl cannot write pivot tables.
"""
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
from xml.etree import ElementTree
import zipfile

import numpy as np
import pandas as pd
from openpyxl import load_workbook
import pytest
import xlsxwriter

from analysis import fit_candidates, get_supported_distributions, report_payload
from excel_pivot import add_count_pivot
from excel_report import FAMILY_OF, FAMILIES, NO_FIT, create_excel_report

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FAMILY_COLUMNS = ["Index", "Sample", "Value", "Best-fit distribution", "Family", "Above threshold"]
SAMPLES = ["Training", "Held-out", "Scenario"]


@pytest.fixture
def payload():
    source = np.random.default_rng(3).gamma(2, 2, 60)
    fit = fit_candidates(source, ["Normal", "Gamma", "Exponential"])
    return report_payload(fit, source, {"source": "Synthetic gamma", "outlier_method": "None"},
                          scenario=[0.5, 4., 30.])


def families_frame(book_bytes):
    """Families rows read from cached values, as a pandas frame."""
    sheet = load_workbook(BytesIO(book_bytes), data_only=True)["Families"]
    rows = [row for row in sheet.iter_rows(min_row=7, max_col=6, values_only=True) if row[0] is not None]
    return pd.DataFrame(rows, columns=FAMILY_COLUMNS)


def pivot_parts(book_bytes):
    archive = zipfile.ZipFile(BytesIO(book_bytes))
    table = ElementTree.fromstring(archive.read("xl/pivotTables/pivotTable1.xml"))
    cache = ElementTree.fromstring(archive.read("xl/pivotCache/pivotCacheDefinition1.xml"))
    records = ElementTree.fromstring(archive.read("xl/pivotCache/pivotCacheRecords1.xml"))
    return table, cache, records


def test_lookup_map_covers_every_supported_distribution_and_the_fallback():
    source = np.arange(-5., 15.)
    fit = fit_candidates(source, ["Normal", "Uniform"])
    book = load_workbook(BytesIO(create_excel_report(report_payload(fit, source, {"source": "Lookup"}))))
    lookup = book["Lookup"]
    entries = [(lookup[f"A{row}"].value, lookup[f"B{row}"].value) for row in range(5, 20)]
    assert len(entries) == len(get_supported_distributions()) + 1
    assert {name for name, _ in entries[:-1]} == set(get_supported_distributions())
    assert entries[-1] == (NO_FIT, FAMILIES[-1])
    assert {family for _, family in entries} <= set(FAMILIES)


def test_family_column_is_a_vlookup_on_the_lookup_sheet(payload):
    families = load_workbook(BytesIO(create_excel_report(payload)))["Families"]
    last = 6 + len(payload["prepared_data"]) + len(payload["scenario_data"])
    for row in range(7, last + 1):
        assert families[f"E{row}"].value == f"=VLOOKUP(D{row},Lookup!$A$5:$B$19,2,FALSE)"
        assert families[f"B{row}"].value == f"=Observations!B{row}"
        assert families[f"F{row}"].value.startswith("=IF(ISNUMBER(Review!$B$4)")


def test_family_values_match_a_pandas_lookup(payload):
    data = families_frame(create_excel_report(payload))
    mapping = {**FAMILY_OF, NO_FIT: FAMILIES[-1]}
    assert list(data["Family"]) == list(data["Best-fit distribution"].map(mapping))


def test_best_fit_is_the_highest_density_candidate(payload):
    data = families_frame(create_excel_report(payload))
    supported = get_supported_distributions()
    params = {row["Distribution"]: row["Parameters"] for row in payload["results"]}
    values = data["Value"].to_numpy()
    densities = pd.DataFrame({name: supported[name].logpdf(values, *p) for name, p in params.items()})
    expected = np.where(np.isfinite(densities.max(axis=1)), densities.idxmax(axis=1), NO_FIT)
    assert list(data["Best-fit distribution"]) == list(expected)


def test_summary_sumif_averageif_and_countifs_match_pandas(payload):
    book_bytes = create_excel_report(payload)
    data = families_frame(book_bytes)
    summary = load_workbook(BytesIO(book_bytes), data_only=True)["Summary"]
    threshold = payload["settings"]["tail_threshold"]
    for row, family in enumerate(FAMILIES, start=4):
        assert summary[f"A{row}"].value == family
        values = data.loc[data["Family"] == family, "Value"]
        assert summary[f"B{row}"].value == len(values)
        assert summary[f"C{row}"].value == pytest.approx(values.sum())
        if len(values):
            assert summary[f"D{row}"].value == pytest.approx(values.mean())
            assert summary[f"E{row}"].value == int((values > threshold).sum())
            assert summary[f"F{row}"].value == pytest.approx((values > threshold).mean())
        else:
            assert summary[f"D{row}"].value == "n.a."
            assert summary[f"F{row}"].value == "n.a."
    assert summary["B8"].value == len(data)
    assert summary["C8"].value == pytest.approx(data["Value"].sum())
    assert summary["E8"].value == int((data["Value"] > threshold).sum())


def test_sumifs_grid_matches_a_pandas_pivot_and_checks_itself(payload):
    book_bytes = create_excel_report(payload)
    data = families_frame(book_bytes)
    grid = pd.pivot_table(data, index="Family", columns="Sample", values="Value", aggfunc="sum", fill_value=0.)
    summary = load_workbook(BytesIO(book_bytes), data_only=True)["Summary"]
    formulas = load_workbook(BytesIO(book_bytes))["Summary"]
    for row, family in enumerate(FAMILIES, start=13):
        for column, sample in zip("BCD", SAMPLES):
            expected = grid.loc[family, sample] if family in grid.index and sample in grid.columns else 0.
            assert summary[f"{column}{row}"].value == pytest.approx(expected)
            assert formulas[f"{column}{row}"].value.startswith("=SUMIFS(")
    assert summary["B19"].value == "Matches the value sum"
    assert formulas["C4"].value.startswith("=SUMIF(")
    assert formulas["D4"].value.startswith('=IF(B4=0,"n.a.",AVERAGEIF(')
    assert formulas["E4"].value.startswith('=IF(ISNUMBER(Review!$B$4),COUNTIFS(')


def test_pivot_definition_reads_families_rows(payload):
    book_bytes = create_excel_report(payload)
    data = families_frame(book_bytes)
    table, cache, records = pivot_parts(book_bytes)
    assert table.get("name") == "FamilyPivot"
    source = cache.find("m:cacheSource/m:worksheetSource", NS)
    assert source.get("sheet") == "Families"
    assert source.get("ref") == f"A6:F{6 + len(data)}"
    assert int(cache.get("recordCount")) == len(data) == len(records.findall("m:r", NS))
    names = [f.get("name") for f in cache.findall("m:cacheFields/m:cacheField", NS)]
    assert names == FAMILY_COLUMNS
    row_field = int(table.find("m:rowFields/m:field", NS).get("x"))
    col_field = int(table.find("m:colFields/m:field", NS).get("x"))
    assert names[row_field] == "Family"
    assert names[col_field] == "Sample"
    data_field = table.find("m:dataFields/m:dataField", NS)
    assert data_field.get("subtotal") == "count"
    assert names[int(data_field.get("fld"))] == "Index"
    row_items = [s.get("v") for s in cache.findall("m:cacheFields/m:cacheField", NS)[row_field]
                 .findall("m:sharedItems/m:s", NS)]
    col_items = [s.get("v") for s in cache.findall("m:cacheFields/m:cacheField", NS)[col_field]
                 .findall("m:sharedItems/m:s", NS)]
    assert sorted(row_items) == sorted(set(data["Family"]))
    assert col_items == [s for s in SAMPLES if s in set(data["Sample"])]
    # Rows: two header rows, one per family, then the grand total. Columns: label, samples, total.
    last_row = 4 + 2 + len(row_items)
    last_col = chr(ord("A") + 1 + len(col_items) + 1 - 1)
    assert table.find("m:location", NS).get("ref") == f"A4:{last_col}{last_row}"
    assert len(table.findall("m:rowItems/m:i", NS)) == len(row_items) + 1
    assert len(table.findall("m:colItems/m:i", NS)) == len(col_items) + 1


def test_pivot_cells_match_a_pandas_crosstab_of_the_source(payload):
    book_bytes = create_excel_report(payload)
    data = families_frame(book_bytes)
    crosstab = pd.crosstab(data["Family"], data["Sample"], margins=True, margins_name="Grand Total")
    pivot = load_workbook(BytesIO(book_bytes), data_only=True)["Pivot"]
    headers = [pivot.cell(row=5, column=c).value for c in range(2, 2 + len(crosstab.columns))]
    assert sorted(headers) == sorted(crosstab.columns)
    for row in range(6, 6 + len(crosstab.index)):
        label = pivot.cell(row=row, column=1).value
        for column, header in enumerate(headers, start=2):
            assert pivot.cell(row=row, column=column).value == crosstab.loc[label, header]


def test_pivot_chart_is_linked_to_the_pivot(payload):
    archive = zipfile.ZipFile(BytesIO(create_excel_report(payload)))
    linked = [archive.read(name).decode() for name in archive.namelist()
              if name.startswith("xl/charts/") and "<c:pivotSource>" in archive.read(name).decode()]
    assert len(linked) == 1
    assert "[DistroFit review.xlsx]Pivot!FamilyPivot" in linked[0]
    assert "Pivot!$B$6" in linked[0]


def test_unfit_values_and_absent_training_fall_back_to_the_last_family():
    source = np.arange(-5., 15.)
    fit = fit_candidates(source, ["Uniform"])
    payload = report_payload(fit, source, {"source": "Uniform only", "outlier_method": "None"},
                             scenario=[100.])
    book_bytes = create_excel_report(payload)
    data = families_frame(book_bytes)
    scenario = data[data["Sample"] == "Scenario"]
    assert list(scenario["Best-fit distribution"]) == [NO_FIT]
    assert list(scenario["Family"]) == [FAMILIES[-1]]
    table, _, _ = pivot_parts(book_bytes)
    # Three sample columns plus the grand total are three <i> items and one more.
    assert len(table.findall("m:colItems/m:i", NS)) == 4


def test_pivot_rejects_values_outside_its_item_order():
    book = BytesIO()
    with xlsxwriter.Workbook(book, {"in_memory": True}) as workbook:
        workbook.add_worksheet("Data").write_row(0, 0, ["Name"])
        workbook.add_worksheet("Pivot")
    with pytest.raises(ValueError):
        add_count_pivot(book.getvalue(), source_sheet="Data", header_row=1, headers=["Name"],
                        records=[["x"]], row_field=0, col_field=0, row_order=["y"], col_order=["y"],
                        pivot_sheet_part="xl/worksheets/sheet2.xml", pivot_name="P", top_row=1,
                        data_caption="Count", row_caption="Name", col_caption="Name")


def test_live_engine_recalculates_the_summary_for_a_new_threshold(payload, tmp_path):
    engine = shutil.which("libreoffice") or shutil.which("soffice")
    if not engine:
        if os.environ.get("REQUIRE_SPREADSHEET_ENGINE"):
            pytest.fail("CI requires LibreOffice to execute the exported formulas")
        pytest.skip("Install LibreOffice to run the live spreadsheet recalculation tests")
    book = load_workbook(BytesIO(create_excel_report(payload)))
    new_threshold = 2.5
    book["Review"]["B4"] = new_threshold
    path = tmp_path / "families.xlsx"
    book.save(path)
    output = Path(tmp_path / "recalculated")
    # A unique profile keeps this owned headless process away from any open office session.
    subprocess.run([engine, f"-env:UserInstallation={(tmp_path / 'profile').as_uri()}",
                    "--headless", "--convert-to", "xlsx", "--outdir", str(output), str(path)],
                   check=True, timeout=120, capture_output=True)
    result = load_workbook(output / path.name, data_only=True)
    data = families_frame(create_excel_report(payload))
    assert result["Summary"]["E8"].value == int((data["Value"] > new_threshold).sum())
    assert result["Summary"]["B19"].value == "Matches the value sum"
    for sheet in result:
        assert all(cell.data_type != "e" for cells in sheet for cell in cells)
