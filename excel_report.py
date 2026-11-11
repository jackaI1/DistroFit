"""Portable Excel review of a frozen DistroFit analysis, with live tail counts."""
import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
import xlsxwriter

from analysis import fit_candidates, get_supported_distributions, prepare_data, read_csv, report_payload
from excel_pivot import add_count_pivot, add_pivot_chart_link, count_grid


MAX_OBSERVATIONS = 100_000
# Each fitted curve belongs to one plain-language family. The Lookup sheet holds this map.
FAMILY_OF = {
    "Normal": "Symmetric, unbounded", "Student's t": "Symmetric, unbounded",
    "Logistic": "Symmetric, unbounded", "Laplace": "Symmetric, unbounded", "Cauchy": "Symmetric, unbounded",
    "Gamma": "Positive and skewed", "Exponential": "Positive and skewed", "Weibull (Min)": "Positive and skewed",
    "Log-Normal": "Positive and skewed", "Chi-Squared": "Positive and skewed", "Pareto": "Positive and skewed",
    "Maxwell": "Positive and skewed",
    "Beta": "Bounded between two limits", "Uniform": "Bounded between two limits",
}
FAMILY_MEANING = {
    "Symmetric, unbounded": "Spreads out evenly on both sides of the middle, with no hard limit",
    "Positive and skewed": "Usually has a lower limit and a long tail toward high values",
    "Bounded between two limits": "Stays between a lowest and a highest value",
    "Outside every fitted family": "No fitted curve gives this value a positive density",
}
FAMILIES = list(FAMILY_MEANING)
NO_FIT = "No fitted density"
SAMPLE_ORDER = ["Training", "Held-out", "Scenario"]
PIVOT_HEADERS = ["Index", "Sample", "Value", "Best-fit distribution", "Family", "Above threshold"]


def best_fit_distribution(results, value):
    """Fitted curve with the highest density at one value; ties keep the sorted results order."""
    supported = get_supported_distributions()
    best, best_density = NO_FIT, -np.inf
    for row in results:
        density = float(supported[row["Distribution"]].logpdf(value, *row["Parameters"]))
        if np.isfinite(density) and density > best_density:
            best, best_density = row["Distribution"], density
    return best


def _add_family_sheets(book, sheets, fmt, payload, rows, threshold):
    """Write Lookup, Families, Summary and Pivot; return the pivot's source records and layout."""
    lookup, families, summary, pivot = sheets["Lookup"], sheets["Families"], sheets["Summary"], sheets["Pivot"]
    for sheet in (lookup, families, summary, pivot):
        sheet.hide_gridlines(2)
        sheet.set_column("A:A", 30, fmt["body"])
        sheet.set_column("B:F", 19, fmt["body"])
    lookup.set_tab_color("#4C7295")
    lookup.write("A1", "Distribution family lookup", fmt["title"])
    lookup.merge_range("A2:C2", "Each fitted curve belongs to one family. Families uses VLOOKUP on the "
                       "table below, so a family renamed here changes the lookups, Summary and pivot after a refresh.",
                       fmt["note"])
    lookup.write_row("A4", ["Distribution", "Family", "Plain meaning"], fmt["header"])
    entries = list(FAMILY_OF.items()) + [(NO_FIT, FAMILIES[-1])]
    for offset, (name, family) in enumerate(entries):
        lookup.write_row(4 + offset, 0, [name, family, FAMILY_MEANING[family]], fmt["body"])
    lookup_range = f"Lookup!$A$5:$B${4 + len(entries)}"
    lookup.set_column("C:C", 60, fmt["note"])

    last = 6 + len(rows)
    families.freeze_panes(6, 0)
    families.write("A1", "Each measurement with its family", fmt["title"])
    families.merge_range("A2:F3", "Best-fit distribution is the fitted curve with the highest density at that "
                         "value, chosen when the workbook was written. Family is looked up on Lookup. "
                         "Above threshold follows the yellow cell on Review.", fmt["note"])
    families.write_row("A6", PIVOT_HEADERS, fmt["header"])
    families.set_row(5, 32)
    records = []
    for i, (index, sample, value) in enumerate(rows):
        row = 7 + i
        best = best_fit_distribution(payload["results"], value)
        family = FAMILY_OF.get(best, FAMILIES[-1])
        above = "Yes" if value > threshold else "No"
        families.write_formula(f"A{row}", f"=Observations!A{row}", fmt["integer"], index)
        families.write_formula(f"B{row}", f"=Observations!B{row}", fmt["body"], sample)
        families.write_formula(f"C{row}", f"=Observations!C{row}", fmt["number"], value)
        families.write_string(f"D{row}", best, fmt["body"])
        families.write_formula(f"E{row}", f"=VLOOKUP(D{row},{lookup_range},2,FALSE)", fmt["body"], family)
        families.write_formula(f"F{row}", f'=IF(ISNUMBER(Review!$B$4),IF(C{row}>Review!$B$4,"Yes","No"),"n.a.")',
                               fmt["body"], above)
        records.append([index, sample, float(value), best, family, above])
    families.set_column("A:A", 12, fmt["integer"])
    families.set_column("D:D", 26, fmt["body"])
    families.set_column("E:E", 28, fmt["body"])

    value_range = f"Families!$C$7:$C${last}"
    family_range = f"Families!$E$7:$E${last}"
    sample_range = f"Families!$B$7:$B${last}"
    above_range = f"Families!$F$7:$F${last}"
    summary.write("A1", "Summary by family", fmt["title"])
    summary.merge_range("A2:F2", "COUNTIF, SUMIF, AVERAGEIF and COUNTIFS over the Families sheet. "
                        "Above threshold uses the cutoff on Review.", fmt["note"])
    summary.write_row("A3", ["Family", "Observations", "Sum of values", "Average value",
                             "Above threshold", "Share above"], fmt["header"])
    summary.set_row(2, 32)
    for offset, family in enumerate(FAMILIES):
        row = 4 + offset
        members = [r for r in records if r[4] == family]
        count = len(members)
        total = float(sum(r[2] for r in members))
        above = sum(r[2] > threshold for r in members)
        summary.write_string(f"A{row}", family, fmt["body"])
        summary.write_formula(f"B{row}", f"=COUNTIF({family_range},A{row})", fmt["integer"], count)
        summary.write_formula(f"C{row}", f"=SUMIF({family_range},A{row},{value_range})", fmt["number"], total)
        summary.write_formula(f"D{row}", f'=IF(B{row}=0,"n.a.",AVERAGEIF({family_range},A{row},{value_range}))',
                              fmt["number"], total / count if count else "n.a.")
        summary.write_formula(f"E{row}", f'=IF(ISNUMBER(Review!$B$4),COUNTIFS({family_range},A{row},'
                              f'{value_range},">"&Review!$B$4),"n.a.")',
                              fmt["integer"], above)
        summary.write_formula(f"F{row}", f'=IF(OR(B{row}=0,NOT(ISNUMBER(E{row}))),"n.a.",E{row}/B{row})',
                              fmt["percent"], above / count if count else "n.a.")
    grand_count = len(records)
    grand_total = float(sum(r[2] for r in records))
    grand_above = sum(r[2] > threshold for r in records)
    summary.write("A8", "All families", fmt["body"])
    summary.write_formula("B8", "=SUM(B4:B7)", fmt["integer"], grand_count)
    summary.write_formula("C8", "=SUM(C4:C7)", fmt["number"], grand_total)
    summary.write_formula("D8", '=IF(B8=0,"n.a.",C8/B8)', fmt["number"], grand_total / grand_count)
    summary.write_formula("E8", '=IF(ISNUMBER(Review!$B$4),SUM(E4:E7),"n.a.")', fmt["integer"], grand_above)
    summary.write_formula("F8", '=IF(OR(B8=0,NOT(ISNUMBER(E8))),"n.a.",E8/B8)', fmt["percent"],
                          grand_above / grand_count)

    summary.write("A11", "Sum of values by family and sample group (SUMIFS)", fmt["title"])
    summary.write_row("A12", ["Family", *SAMPLE_ORDER, "Total"], fmt["header"])
    summary.set_row(11, 32)
    for offset, family in enumerate(FAMILIES):
        row = 13 + offset
        summary.write_string(f"A{row}", family, fmt["body"])
        cells = []
        for column, sample in zip("BCD", SAMPLE_ORDER):
            value = float(sum(r[2] for r in records if r[4] == family and r[1] == sample))
            cells.append(value)
            summary.write_formula(f"{column}{row}", f"=SUMIFS({value_range},{family_range},$A{row},"
                                  f"{sample_range},{column}$12)", fmt["number"], value)
        summary.write_formula(f"E{row}", f"=SUM(B{row}:D{row})", fmt["number"], sum(cells))
    for column, sample in zip("BCD", SAMPLE_ORDER):
        total = float(sum(r[2] for r in records if r[1] == sample))
        summary.write_formula(f"{column}17", f"=SUM({column}13:{column}16)", fmt["number"], total)
    summary.write_formula("E17", "=SUM(E13:E16)", fmt["number"], grand_total)
    summary.write("A17", "Total", fmt["body"])
    summary.write("A19", "Check", fmt["body"])
    summary.write_formula("B19", f'=IF(ABS(E17-SUM({value_range}))<0.000001,"Matches the value sum","Check the lookups")',
                          fmt["body"], "Matches the value sum")

    # Native PivotTable: rows are families, columns are sample groups, cells count observations.
    top_row = 4
    row_order = [family for family in FAMILIES if any(r[4] == family for r in records)]
    col_order = [sample for sample in SAMPLE_ORDER if any(r[1] == sample for r in records)]
    pivot.write("A1", "Pivot table of measurements by family", fmt["title"])
    pivot.merge_range("A2:E2", "A native Excel PivotTable over the Families sheet. Excel refreshes it when the "
                      "file opens; use Data > Refresh All after editing Families or Lookup.", fmt["note"])
    grid = count_grid(records, 4, 1, row_order, col_order, data_caption="Observations",
                      row_caption="Family", col_caption="Sample group")
    for r, cells in enumerate(grid):
        for c, cell in enumerate(cells):
            if cell is None:
                continue
            if isinstance(cell, int):
                pivot.write_number(top_row - 1 + r, c, cell, fmt["integer"])
            else:
                pivot.write_string(top_row - 1 + r, c, str(cell), fmt["body"])
    chart = book.add_chart({"type": "column"})
    colours = ["#24374B", "#4C7295", "#A9C4DB"]
    last_pivot_row = top_row + 1 + len(row_order)
    for j, sample in enumerate(col_order):
        column = "BCD"[SAMPLE_ORDER.index(sample)]
        chart.add_series({"name": f"=Pivot!${column}${top_row + 1}",
                          "categories": f"=Pivot!$A${top_row + 2}:$A${last_pivot_row}",
                          "values": f"=Pivot!${column}${top_row + 2}:${column}${last_pivot_row}",
                          "fill": {"color": colours[j]}})
    chart.set_title({"name": "Measurements per family, by sample group"})
    chart.set_y_axis({"name": "Observations", "min": 0})
    chart.set_legend({"position": "bottom"})
    pivot.insert_chart(f"H{top_row}", chart, {"x_scale": 1.1, "y_scale": 1.05})
    pivot.set_column("A:A", 30, fmt["body"])
    return records, row_order, col_order, top_row


def create_excel_report(payload):
    """Return an .xlsx snapshot. Only the review threshold is a what-if input.

    Numerical fits remain in SciPy. Formula caches are independently computed
    here for previews; Excel recalculates the formulas when the input changes.
    The cap bounds memory in the interactive app, below Excel's row limit.
    """
    prepared = payload["prepared_data"]
    scenario = payload["scenario_data"]
    source = payload["source_data"]
    if max(len(prepared) + len(scenario), len(source)) > MAX_OBSERVATIONS:
        raise ValueError(f"Excel export supports at most {MAX_OBSERVATIONS:,} source or combined review observations.")
    if not prepared or not np.all(np.isfinite(prepared + scenario)):
        raise ValueError("Excel review needs finite prepared and scenario observations.")
    train = set(payload["train_indices"])
    held = set(payload["held_indices"])
    if (train & held or train | held != set(range(len(prepared)))
            or len(train) != len(payload["train_indices"])
            or len(held) != len(payload["held_indices"]) or not train or not held):
        raise ValueError("Training and held-out indices must partition the prepared data.")
    threshold = float(payload["settings"]["tail_threshold"])
    if not np.isfinite(threshold):
        raise ValueError("The review threshold must be finite.")
    output = BytesIO()
    with xlsxwriter.Workbook(output, {"in_memory": True, "strings_to_formulas": False,
                                      "strings_to_urls": False}) as book:
        book.set_properties({"title": "DistroFit measurement review", "author": "DistroFit"})
        review = book.add_worksheet("Review")
        candidates = book.add_worksheet("Candidates")
        observations = book.add_worksheet("Observations")
        lookup = book.add_worksheet("Lookup")
        families = book.add_worksheet("Families")
        summary = book.add_worksheet("Summary")
        pivot = book.add_worksheet("Pivot")
        title =book.add_format({"font_name": "Arial", "font_size": 14, "bold": True})
        body = book.add_format({"font_name": "Arial", "font_size": 11, "valign": "vcenter"})
        note = book.add_format({"font_name": "Arial", "font_size": 11, "text_wrap": True,
                                "valign": "top"})
        number = book.add_format({"font_name": "Arial", "font_size": 11, "num_format": "0.0000", "align": "right"})
        percent = book.add_format({"font_name": "Arial", "font_size": 11, "num_format": "0.0%", "align": "right"})
        integer = book.add_format({"font_name": "Arial", "font_size": 11, "num_format": "#,##0", "align": "right"})
        header = book.add_format({"font_name": "Arial", "font_size": 11, "bold": True,
                                  "bg_color": "#24374B", "font_color": "#FFFFFF",
                                  "align": "center", "text_wrap": True, "valign": "vcenter"})
        edit = book.add_format({"font_name": "Arial", "font_size": 11, "bg_color": "#FFF2CC",
                                "num_format": "0.0000"})
        for sheet in (review, candidates, observations):
            sheet.hide_gridlines(2)
            sheet.set_column("A:L", 18, body)
            sheet.set_default_row(22)
        review.set_tab_color("#24374B")
        review.set_column("A:A", 23, body)
        review.set_column("B:E", 19, body)
        review.set_column("F:F", 3)
        review.write("A2", "DistroFit measurement review", title)
        review.write("A4", "Review threshold", body)
        review.write_number("B4", threshold, edit)
        review.merge_range("C4:E4", "Edit the yellow cell to try a different cutoff.", note)
        review.data_validation("B4", {"validate": "custom", "value": "=ISNUMBER(B4)",
                                      "ignore_blank": False, "error_type": "stop",
                                      "error_title": "Enter a number",
                                      "error_message": "Enter a numeric threshold, including zero or a negative value."})
        review.write_row("A6", ["Sample", "Count", "Mean", "Above threshold", "Share above"], header)
        review.set_row(5, 32)
        rows = [[i + 1, "Training" if i in train else "Held-out", value]
                for i, value in enumerate(prepared)]
        rows += [[i + 1, "Scenario", value] for i, value in enumerate(scenario)]
        observations.write("A2", "Values used in the review", title)
        observations.merge_range("A3:C4", "Index is within prepared data or scenario. Filtering happens before the split.", note)
        observations.add_table(5, 0, 5 + len(rows), 2, {
            "name": "ReviewValues", "data": rows, "columns": [
                {"header": "Index", "header_format": header}, {"header": "Sample", "header_format": header},
                {"header": "Value", "header_format": header, "format": number}]})
        observations.write("F2", "Original source values", title)
        observations.merge_range("F3:H4", "Original order, before filtering. Nonfinite values stay labelled as text.", note)
        observations.add_table(5, 5, 5 + len(source), 6, {
            "name": "SourceValues", "data": [[i + 1, value] for i, value in enumerate(source)],
            "columns": [{"header": "Source index", "header_format": header},
                        {"header": "Original value", "header_format": header, "format": number}]})
        observations.freeze_panes(6, 2)
        observations.set_column("C:C", 23, number)
        observations.set_column("D:E", 3)
        observations.set_column("G:G", 23, number)
        last = 6 + len(rows)
        groups = f"Observations!$B$7:$B${last}"
        values = f"Observations!$C$7:$C${last}"
        for row, label in enumerate(("Training", "Held-out", "Scenario"), start=7):
            data = [entry[2] for entry in rows if entry[1] == label]
            count = len(data)
            above = sum(value > threshold for value in data)
            review.write(f"A{row}", label)
            review.write_formula(f"B{row}", f'=COUNTIF({groups},A{row})', integer, count)
            review.write_formula(f"C{row}", f'=IF(B{row}=0,"n.a.",AVERAGEIF({groups},A{row},{values}))',
                                 number, float(np.mean(data)) if count else "n.a.")
            review.write_formula(f"D{row}", f'=IF(OR(B{row}=0,NOT(ISNUMBER($B$4))),"n.a.",COUNTIFS({groups},A{row},{values},">"&$B$4))',
                                 integer, above if count else "n.a.")
            review.write_formula(f"E{row}", f'=IF(OR(B{row}=0,NOT(ISNUMBER($B$4))),"n.a.",D{row}/B{row})',
                                 percent, above / count if count else "n.a.")
        review.merge_range("A12:E13", "Above means strictly greater than the threshold. Blank or text thresholds make tail results unavailable. No scenario gives a zero count and n.a. statistics.", note)
        review.merge_range("A15:E16", "The chart and counts respond to B4. Candidates contains the original fitted models and scores. Changing this threshold does not refit models or update their original tail checks.", note)
        chart = book.add_chart({"type": "column"})
        chart.add_series({"name": "Share above threshold", "categories": "=Review!$A$7:$A$9",
                          "values": "=Review!$E$7:$E$9", "fill": {"color": "#4C7295"}})
        chart.set_title({"name": "Observed share above the review threshold"})
        chart.set_y_axis({"num_format": "0%", "min": 0, "max": 1})
        chart.set_legend({"none": True})
        chart.show_blanks_as("gap")
        review.insert_chart("G6", chart, {"x_scale": 1.05, "y_scale": 1.05})
        review.write("A19", "Analysis settings", title)
        for row, (key, value) in enumerate(payload["settings"].items(), start=20):
            review.write(row, 0, key)
            review.merge_range(row, 1, row, 4, value if isinstance(value, (int, float)) else str(value), note)
            review.set_row(row, 40 if len(str(value)) > 80 else 23)
        candidates.write("A2", "Frozen model comparison", title)
        candidates.merge_range("A3:H4", "NLL is average negative log likelihood: lower held-out loss ranks first. inf means a model assigns zero density to at least one observation. Scores and parameters do not change in Excel.", note)
        columns = ["Distribution", "Train NLL", "Held-out NLL", "AIC", "BIC", "SSE", "KS Stat", "Parameters"]
        fitted = [[entry[key] if key != "Parameters" else str(entry[key]) for key in columns]
                  for entry in payload["results"]]
        if fitted:
            candidates.add_table(5, 0, 5 + len(fitted), 7, {
                "name": "FittedModels", "data": fitted,
                "columns": [{"header": key, "header_format": header,
                             "format": number if 0 < i < 7 else (note if i == 7 else body)}
                            for i, key in enumerate(columns)]})
            for row in range(6, 6 + len(fitted)):
                candidates.set_row(row, 40)
        else:
            candidates.write("A6", "No successful fits")
        candidates.set_column("A:A", 23, body)
        candidates.set_column("B:G", 19, number)
        candidates.set_column("H:H", 65, note)
        candidates.freeze_panes(6, 1)
        failure_row = len(fitted) + 9
        candidates.write(failure_row, 0, "Failed candidates", title)
        for i, (name, reason) in enumerate(payload["failures"].items()):
            row = failure_row + 1 + 3 * i
            candidates.write(row, 0, name)
            candidates.merge_range(row, 1, row + 1, 7, reason, note)
        if not payload["failures"]:
            candidates.write(failure_row + 1, 0, "None")
        records, row_order, col_order, top_row = _add_family_sheets(
            book, {"Lookup": lookup, "Families": families, "Summary": summary, "Pivot": pivot},
            {"title": title, "body": body, "note": note, "number": number, "percent": percent,
             "integer": integer, "header": header}, payload, rows, threshold)
        review.activate()
    # xlsxwriter cannot write PivotTables, so the pivot parts are added after the workbook is saved.
    pivot_xlsx = add_count_pivot(
        output.getvalue(), source_sheet="Families", header_row=6, headers=PIVOT_HEADERS, records=records,
        row_field=4, col_field=1, row_order=row_order, col_order=col_order,
        pivot_sheet_part="xl/worksheets/sheet7.xml", pivot_name="FamilyPivot", top_row=top_row,
        data_caption="Observations", row_caption="Family", col_caption="Sample group")
    return add_pivot_chart_link(pivot_xlsx, pivot_name="FamilyPivot", pivot_sheet="Pivot",
                                file_name="DistroFit review.xlsx")


def main():
    parser = argparse.ArgumentParser(description="Export a DistroFit analysis to Excel.")
    parser.add_argument("csv", nargs="?", type=Path)
    parser.add_argument("--column", help="Numeric CSV column name")
    parser.add_argument("--sample", action="store_true", help="Use a reproducible synthetic Gamma sample")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.sample == bool(args.csv):
        parser.error("Choose either --sample or one CSV file.")
    if args.sample:
        source = np.random.default_rng(27).gamma(2, 2, 240)
        description = "Synthetic Gamma sample, seed 27, shape 2, scale 2"
    else:
        with args.csv.open("rb") as handle:
            frame = read_csv(handle)
        if args.column not in frame.select_dtypes(include=np.number).columns:
            parser.error("--column must name a numeric CSV column.")
        source = frame[args.column].to_numpy()
        description = f"CSV column: {args.column}"  # Do not expose a local file path.
    data, removed = prepare_data(source)
    fit = fit_candidates(data, ["Normal", "Gamma", "Exponential"])
    payload = report_payload(fit, source, {"source": description, "outlier_method": "None",
                                           "removed_count": removed})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(create_excel_report(payload))
    print(f"Saved Excel review to {args.out}")


if __name__ == "__main__":
    main()
