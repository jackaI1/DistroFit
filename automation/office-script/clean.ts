/** Paste this entire file into Excel's Automate > New Script editor.
 * Raw must have exactly dataset, value, unit headers at A1 (any case/spacing).
 * Output sheets belong to this script. Raw is read-only; rejected rows stay visible.
 */
function main(workbook: ExcelScript.Workbook, minimum: number = 0, maximum: number = 20) {
  if (!Number.isFinite(minimum) || !Number.isFinite(maximum) || minimum > maximum) {
    throw new Error("Enter finite limits with minimum no greater than maximum.");
  }
  const raw = workbook.getWorksheet("Raw");
  if (!raw) throw new Error("Create a Raw sheet and paste dataset, value, unit at A1.");
  const used = raw.getUsedRange(true);
  if (!used || used.getRowIndex() !== 0 || used.getColumnIndex() !== 0) {
    throw new Error("Paste the headers at Raw!A1.");
  }
  if (used.getRowCount() > 100001 || used.getColumnCount() !== 3) {
    throw new Error("Use exactly three columns and at most 100,000 data rows.");
  }
  const input = used.getValues();
  const headers = input[0].map(cell => String(cell).trim().toLowerCase());
  const expected = ["dataset", "value", "unit"];
  if (new Set(headers).size !== 3 || expected.some(name => headers.indexOf(name) < 0)) {
    throw new Error("Headers must be dataset, value, unit, each used once.");
  }
  const datasetColumn = headers.indexOf("dataset");
  const valueColumn = headers.indexOf("value");
  const unitColumn = headers.indexOf("unit");
  const output: (string | number | boolean)[][] = [["dataset", "value", "unit", "source_row", "flags"]];
  const issueCounts = [0, 0, 0, 0, 0];
  let accepted = 0;
  for (let row = 1; row < input.length; row++) {
    const dataset = String(input[row][datasetColumn]).trim();
    const unit = String(input[row][unitColumn]).trim().toLowerCase();
    const rawValue = input[row][valueColumn];
    const text = String(rawValue).trim();
    const flags: string[] = [];
    if (dataset === "") { flags.push("BLANK_DATASET"); issueCounts[0]++; }
    if (unit === "") { flags.push("BLANK_UNIT"); issueCounts[1]++; }
    let value: number | string = "";
    if (text === "") {
      flags.push("BLANK_VALUE"); issueCounts[2]++;
    } else if (typeof rawValue === "boolean" ||
               !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(text) ||
               !Number.isFinite(Number(text))) {
      flags.push("INVALID_NUMBER"); issueCounts[3]++;
      value = literalText(text);
    } else {
      value = Number(text);
      if (value < minimum || value > maximum) { flags.push("OUT_OF_RANGE"); issueCounts[4]++; }
    }
    if (flags.length === 0) accepted++;
    output.push([literalText(dataset), value, literalText(unit), row + 1, flags.join("; ") || "OK"]);
  }
  // Everything above validates and computes before replacing a previous report.
  const cleaned = workbook.getWorksheet("Cleaned") || workbook.addWorksheet("Cleaned");
  const qa = workbook.getWorksheet("QAQC") || workbook.addWorksheet("QAQC");
  const oldCleaned = cleaned.getUsedRange();
  if (oldCleaned) oldCleaned.clear();
  const oldQA = qa.getUsedRange();
  if (oldQA) oldQA.clear();
  for (const column of [0, 2, 4]) {
    cleaned.getRangeByIndexes(0, column, output.length, 1).setNumberFormat("@");
  }
  cleaned.getRangeByIndexes(0, 0, output.length, 5).setValues(output);
  const summary: (string | number | boolean)[][] = [
    ["Check", "Result"], ["Rows checked", input.length - 1], ["Accepted", accepted],
    ["Rejected", input.length - 1 - accepted], ["Blank datasets", issueCounts[0]],
    ["Blank units", issueCounts[1]], ["Blank values", issueCounts[2]],
    ["Invalid numbers", issueCounts[3]], ["Out of range", issueCounts[4]],
    ["Minimum (inclusive)", minimum], ["Maximum (inclusive)", maximum],
    ["Rule", "OK requires dataset, unit, a finite number and inclusive limits. Counts can overlap."],
    ["Next step", "Filter Cleaned to OK, save value as CSV, and rerun DistroFit to fit new curves."]
  ];
  qa.getRangeByIndexes(0, 0, summary.length, 2).setValues(summary);
}

function literalText(value: string): string {
  // Apostrophe plus text formatting prevents formula interpretation in Excel.
  return /^[=+@-]/.test(value) ? "'" + value : value;
}
