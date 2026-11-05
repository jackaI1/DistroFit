"""Build a review workbook with an embedded VBA form and legacy import query.

Fits remain in analysis.py; Excel switches between their saved scores and curves.
"""
import argparse
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import xlsxwriter

from analysis import fit_candidates, get_supported_distributions, read_csv

ASSETS = Path(__file__).resolve().parent / "automation"
MAX_VALUES = 100_000
MAX_DATASETS = 20


def create_automation_workbook(datasets, *, candidates=None, template=False):
    """Return .xlsm bytes (.xltm if template=True) from named finite 1D samples.

    pyOpenVBA is an optional build dependency, separate from the Streamlit app.
    No auto-open code or VBA-project access is needed by the delivered workbook.
    """
    from pyopenvba import ExcelFile, PowerQueryWorkbook

    if not datasets or len(datasets) > MAX_DATASETS:
        raise ValueError("Supply 1 to 20 named datasets.")
    if any(not isinstance(name, str) or not name.strip() or len(name) > 80 for name in datasets):
        raise ValueError("Dataset names must contain 1 to 80 characters.")
    if len({name.strip().casefold() for name in datasets}) != len(datasets):
        raise ValueError("Dataset names must be unique after trimming and ignoring case.")
    candidates = ["Normal", "Gamma", "Exponential"] if candidates is None else candidates
    if not candidates or len(set(candidates)) != len(candidates) or any(c not in get_supported_distributions() for c in candidates):
        raise ValueError("Choose distinct supported distributions.")
    values = {name: np.asarray(data, dtype=float) for name, data in datasets.items()}
    if sum(data.size for data in values.values()) > MAX_VALUES:
        raise ValueError("At most 100,000 observations per workbook.")
    models, plots, observations, index = [], [], [], []
    for name, data in values.items():
        if data.ndim != 1 or len(data) < 8 or not np.all(np.isfinite(data)) or np.ptp(data) == 0:
            raise ValueError("Each dataset needs at least eight finite, varying numbers.")
        fitted = fit_candidates(data, candidates)
        if not fitted["results"]:
            raise ValueError(f"No successful fits for dataset {name!r}.")
        index.append([name, len(data), "; ".join(f"{k}: {v}" for k, v in fitted["errors"].items()) or "None"])
        train = set(fitted["train_indices"])
        observations.extend([name, i + 1, float(v), "Training" if i in train else "Held-out"] for i, v in enumerate(data))
        counts, edges = np.histogram(data[list(fitted["train_indices"])], bins=40, density=True)
        centers = (edges[:-1] + edges[1:]) / 2
        for result in fitted["results"]:
            dist = result["Distribution"]
            models.append([name, dist] + [result[k] if np.isfinite(result[k]) else "inf" for k in ("Train NLL", "Held-out NLL", "AIC", "BIC", "KS Stat")] + [str(result["Parameters"])])
            density = get_supported_distributions()[dist].pdf(centers, *result["Parameters"])
            if not np.all(np.isfinite(density)):
                raise ValueError("A fitted curve has nonfinite plot values.")
            plots.extend([name, dist, float(x), float(obs), float(y)] for x, obs, y in zip(centers, counts, density))
    first_name, first_dist = models[0][:2]
    initial_models = [row[1:] for row in models if row[0] == first_name]
    initial_plot = [row[2:] for row in plots if row[:2] == [first_name, first_dist]]
    output = BytesIO()
    with xlsxwriter.Workbook(output, {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False}) as book:
        book.set_vba_name("ThisWorkbook")
        head = book.add_format({"bold": True, "bg_color": "#24374B", "font_color": "white"})
        edit = book.add_format({"bg_color": "#FFF2CC", "num_format": "@"})
        number = book.add_format({"num_format": "0.0000"})
        target = book.add_worksheet("Comparison")
        target.set_column("A:A", 24)
        target.set_column("B:K", 19)
        target.write("A1", "DistroFit saved-model review", head)
        target.write("A3", "Dataset")
        target.write("B3", first_name, edit)
        target.write("A4", "Distribution")
        target.write("B4", first_dist, edit)
        target.write("A6", "Status")
        target.write("B6", "Use the button to update saved fits.")
        target.insert_button("D3", {"macro": "ShowReviewForm", "caption": "Choose dataset and curve", "width": 210, "height": 32})
        headers = ["Distribution", "Train NLL", "Held-out NLL", "AIC", "BIC", "KS Stat", "Parameters"]
        target.add_table("A9:G23", {"name": "ModelComparison", "columns": [{"header": h} for h in headers]})
        for r, row in enumerate(initial_models, 9):
            target.write_row(r, 0, row)
        target.write_row("I9", ["Value", "Observed density", "Fitted density"], head)
        for r, row in enumerate(initial_plot, 9):
            target.write_row(r, 8, row, number)
        target.write("L9", "Finite chart loss", head)
        for r in range(10, 24):
            loss = initial_models[r - 10][2] if r - 10 < len(initial_models) else "inf"
            target.write_formula(f"L{r}", f"=IF(ISNUMBER(C{r}),C{r},NA())", number,
                                 loss if isinstance(loss, (float, int)) else "#N/A")
        scores = book.add_chart({"type": "column"})
        scores.add_series({"name": "Held-out loss (lower is better)", "categories": "=Comparison!$A$10:$A$23", "values": "=Comparison!$L$10:$L$23"})
        scores.set_title({"name": "Saved model comparison"})
        scores.set_legend({"none": True})
        scores.show_blanks_as("gap")
        target.insert_chart("A26", scores)
        curves = book.add_chart({"type": "scatter", "subtype": "straight"})
        for col, label in (("J", "Observed training sample"), ("K", "Selected fitted curve")):
            curves.add_series({"name": label, "categories": "=Comparison!$I$10:$I$49", "values": f"=Comparison!${col}$10:${col}$49"})
        curves.set_title({"name": "Training histogram and saved curve"})
        target.insert_chart("I26", curves)
        tables = {
            "DatasetIndex": ("SavedDatasets", ["Dataset", "Count", "Failed fits"], index),
            "ModelStore": ("SavedModels", ["Dataset"] + headers, models),
            "PlotStore": ("SavedPlots", ["Dataset", "Distribution", "Value", "Observed density", "Fitted density"], plots),
            "Observations": ("SavedObservations", ["Dataset", "Index", "Value", "Sample"], observations),
            "Raw": ("RawInput", [" dataset ", " value ", " unit "], [["Pasted sample", " 12.5 ", "mm"], ["Pasted sample", "bad", "mm"], ["Pasted sample", "", "mm"], ["Pasted sample", "99", "mm"]]),
            "ImportSettings": ("LegacyPath", ["Path"], [["REPLACE_WITH_FULL_PATH_TO_legacy_measurements.csv"]]),
        }
        for sheet_name, (table_name, names, rows) in tables.items():
            sheet = book.add_worksheet(sheet_name)
            sheet.set_column(0, len(names) - 1, 24)
            sheet.freeze_panes(1, 0)
            sheet.add_table(0, 0, len(rows), len(names) - 1, {"name": table_name, "data": rows, "columns": [{"header": n} for n in names]})
        book.add_worksheet("LegacyImport")
        help_sheet = book.add_worksheet("StartHere")
        help_sheet.set_column("A:A", 110)
        for r, text in enumerate([
            "DistroFit Excel automation", "1. Open Comparison and click Choose dataset and curve (desktop Excel with macros enabled).",
            "2. Paste dataset, value and unit columns into Raw at A1. Run clean.ts in Automate, with your limits.",
            "3. Cleaned keeps every row and its flags; QAQC counts accepted and rejected rows. Raw is never changed.",
            "4. Filter Cleaned to OK, save the value column as CSV and rerun Python to fit new measurements.",
            "5. Legacy import: set ImportSettings A2 to the bundled CSV's full path, then Data > Refresh All.",
            "Scores and curves are saved Python fits. Choosing a curve updates the view, not the fit.",
            "Raw uses a dot decimal separator. LegacyImport also accepts decimal commas in semicolon-delimited CSV.",
            "See docs/excel-automation.md for setup and test limits. No macros run automatically.",
        ]):
            help_sheet.write(r, 0, text, head if r == 0 else None)
        target.activate()
    with TemporaryDirectory(prefix="distrofit-excel-") as temp:
        path = Path(temp) / "review.xlsm"
        path.write_bytes(output.getvalue())
        with ExcelFile(path) as book:
            book.add_vba_project()
            book.vba_project().add_module("ReviewAutomation", (ASSETS / "vba/ReviewAutomation.bas").read_text())
            form = book.add_form("ReviewForm", caption="DistroFit review", width=360, height=210)
            for name, caption, top in (("DatasetLabel", "Saved dataset", 12), ("DistributionLabel", "Fitted curve", 66)):
                form.add_control("Label", name, left=12, top=top, width=320, height=18).set_property("Caption", caption)
            for name, top in (("DatasetBox", 32), ("DistributionBox", 86)):
                form.add_control("ComboBox", name, left=12, top=top, width=320, height=24)
            form.add_control("CommandButton", "RefreshButton", left=12, top=122, width=130, height=28).set_property("Caption", "Refresh comparison")
            form.add_control("CommandButton", "CloseButton", left=160, top=122, width=85, height=28).set_property("Caption", "Close")
            form.add_control("Label", "StatusLabel", left=12, top=160, width=330, height=36).set_property("Caption", "Choose a saved sample.")
            book.set_module("ReviewForm", (ASSETS / "vba/ReviewForm.bas").read_text())
            book.save(Path(temp) / "review.xlsm")
        with PowerQueryWorkbook(Path(temp) / "review.xlsm") as book:
            book.add_query("LegacyCsvBinary", 'let Path = Excel.CurrentWorkbook(){[Name="LegacyPath"]}[Content]{0}[Path] in File.Contents(Path)')
            book.add_query("LegacyImport", (ASSETS / "power-query/LegacyImport.pq").read_text())
            book.load_to_sheet("LegacyImport", ["dataset", "value", "unit", "source_row", "import_flag"], sheet="LegacyImport", cell="A1")
            book.query("LegacyImport").refresh.on_open = False
            book.query("LegacyImport").refresh.background = False
            book.save()
        data = (Path(temp) / "review.xlsm").read_bytes()
    # Adding the VBA project preserves XlsxWriter's original .xlsx main type.
    # Declare the delivered format explicitly so Excel does not report a mismatch.
    from zipfile import ZipFile, ZIP_DEFLATED
    converted = BytesIO()
    kind = "template" if template else "sheet"
    content_type = f"application/vnd.ms-excel.{kind}.macroEnabled.main+xml".encode()
    with ZipFile(BytesIO(data)) as archive, ZipFile(converted, "w", ZIP_DEFLATED) as result:
        for item in archive.infolist():
            content = archive.read(item.filename)
            if item.filename == "[Content_Types].xml":
                content = content.replace(b"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml", content_type)
            result.writestr(item, content)
    data = converted.getvalue()
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="*", type=Path)
    parser.add_argument("--column")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.sample == bool(args.csv):
        parser.error("Choose --sample or CSV files with --column.")
    if args.out.suffix.lower() not in (".xlsm", ".xltm"):
        parser.error("--out must end in .xlsm or .xltm")
    if args.sample:
        rng = np.random.default_rng(27)
        datasets = {"Seal baseline": rng.gamma(2, 2, 240), "Seal shifted": rng.gamma(2, 2, 240) + 2}
    else:
        datasets = {}
        for path in args.csv:
            if path.stem in datasets:
                parser.error("CSV filename stems must be distinct.")
            with path.open("rb") as handle:
                frame = read_csv(handle)
            if args.column not in frame.select_dtypes(include=np.number).columns:
                parser.error("--column must name a numeric column in every CSV.")
            datasets[path.stem] = frame[args.column].to_numpy()
    data = create_automation_workbook(datasets, template=args.out.suffix.lower() == ".xltm")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    print(f"Saved {len(datasets)} datasets to {args.out}")


if __name__ == "__main__":
    main()
