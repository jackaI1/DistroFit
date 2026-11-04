"""Portable Excel review of a frozen DistroFit analysis, with live tail counts."""
import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
import xlsxwriter

from analysis import fit_candidates, prepare_data, read_csv, report_payload


MAX_OBSERVATIONS = 100_000


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
        title = book.add_format({"font_name": "Arial", "font_size": 14, "bold": True})
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
        review.activate()
    return output.getvalue()


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
