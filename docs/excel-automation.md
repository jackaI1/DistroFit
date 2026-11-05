# Switching saved curves and checking incoming measurements

I wanted to review several measurement batches in one workbook, then catch bad
pasted values before fitting the next batch. The workbook has a small selection
window, two charts and a separate intake area. It keeps the original measurements
and the saved fits together so I can check what changed.

## Open the worked example

1. Download [distrofit_automation.xlsm](../examples/excel/distrofit_automation.xlsm)
   and open it in desktop Microsoft Excel on Windows. The reusable
   [distrofit_automation.xltm](../examples/excel/distrofit_automation.xltm) opens a new
   workbook from the same starting point; save that copy as `.xlsm` to keep the form.
2. Review the [macro source](../automation/vba/ReviewAutomation.bas) and
   [form handlers](../automation/vba/ReviewForm.bas). If Windows blocks this downloaded
   file, close it, use **Properties > Unblock** on this specific file, then reopen
   it and enable its macros. There is no automatic opening macro.
3. On **Comparison**, click **Choose dataset and curve**. Pick **Seal shifted**
   and **Normal**, then **Refresh comparison**. The table changes to that batch's
   saved model scores; the second chart changes to the chosen fitted curve.
   Selecting another curve changes that plot while keeping the batch comparison.
4. **Close** dismisses the window. The source tables remain on **ModelStore**,
   **PlotStore**, **DatasetIndex** and **Observations**.

A distribution is a mathematical curve describing how values are spread out.
Held-out loss measures how well a curve predicts measurements excluded from
fitting; lower is better. `inf` means the curve assigns zero density to a held-out
value, so it has no finite loss bar. It is not a zero score. **KS Stat** compares
the held-out values with the fitted curve. The plots show the training sample,
with 40 histogram bins, and the selected saved density curve.

The form is a real embedded VBA UserForm, Excel's small custom window, with two
lists, status text and buttons. The two lists cannot accept arbitrary typed
selections. Invalid selections or malformed plot data leave the previous valid
view intact. The table and charts follow the refreshed source cells.

## Check a pasted table

The cleaning script runs separately in Excel's **Automate** tab, which requires an
Excel edition/account that supports Office Scripts. For a web-only workflow, save
a copy as `.xlsx` first; the VBA window needs desktop Excel.

1. On **Raw**, clear the previous sample and paste a table at **A1**. It needs
   exactly three columns named `dataset`, `value` and `unit`. Column order,
   capitalization and surrounding spaces can vary. Use one measurement unit
   within a dataset and a dot decimal separator for the values.
2. Open **Automate > New Script**, replace the editor contents with
   [clean.ts](../automation/office-script/clean.ts), and save it as **Check measurements**.
3. Click **Run** and enter meaningful minimum and maximum limits in the same units
   as the measurements. Both endpoints count as in range. Defaults are 0 and 20
   for the bundled example, not universal engineering limits.
4. Read **QAQC**, the quality assurance/quality control summary. The bundled four
   rows give **1 accepted, 3 rejected** at limits 0 to 20. Read the reason on each
   row of **Cleaned**. A row can have several reasons, so issue counts can overlap.
5. Filter **Cleaned** to `OK`. Copy its `value` column, with the header, into a new
   CSV file and rerun DistroFit or the command below to fit the new measurements.

The script trims text, standardizes headers, converts complete finite numeric
strings into numbers, lowercases units, and flags blank dataset/unit/value fields,
invalid numbers and values outside the limits. It preserves every row inside the
used input range, with its original worksheet row number. It does not alter Raw.
Formula-like output text is escaped. Trailing fully empty worksheet rows are not
part of the used range. Decimal commas, booleans and strings such as `12bad` are
rejected instead of guessed. It does not convert units or detect mixed units.

**Cleaned** and **QAQC** belong to the script and are replaced on each run, including
stale rows from a larger previous paste. Other sheets are left alone. Keep notes
on another sheet. Validation of bounds, headers and size happens before output
replacement. It supports up to 100,000 data rows.

## Import the older CSV format

Power Query is Excel's repeatable import and table-cleaning tool. The template
contains **LegacyCsvBinary** and **LegacyImport** queries and a connected result
table on **LegacyImport**. They do not refresh automatically on opening.

1. Download [legacy_measurements.csv](../automation/power-query/legacy_measurements.csv).
   It uses semicolons between columns, inconsistent header spacing, mixed unit
   capitalization and decimal commas, with deliberately bad and missing values.
2. In **ImportSettings!A2**, replace the placeholder with that file's full local
   path. The path belongs to the local copy; do not commit a private path or data.
3. Choose **Data > Refresh All** in desktop Excel with Power Query support.
   Six rows load onto **LegacyImport**. Three are `OK`, two are `BLANK`, and one
   is `INVALID_NUMBER`. The first measurement is the number **12.5**, in **mm**.
4. Copy the result's `dataset`, `value` and `unit` columns into **Raw** and run
   **Check measurements** to apply the engineering limits. Missing required CSV
   columns stop the import rather than silently using the wrong measurement.

The [M query](../automation/power-query/LegacyImport.pq), Power Query's formula
language, is also reviewable on disk. **LegacyCsvBinary** reads the path from the
workbook table; **LegacyImport** promotes and trims headers, checks the required
columns, trims cells, parses comma or dot decimals and preserves rejected rows.
It retains the CSV row number, including the header, as `source_row`. Extra legacy
columns are ignored. For this format a comma means a decimal point, never a
thousands separator. Review the flags before fitting; Power Query does not apply
specification limits.

## Build a workbook from my own measurements

From the repository root, with Python 3.12:

```sh
python -m pip install -r requirements-automation.txt
python excel_automation.py --sample --out /tmp/distrofit_automation.xlsm
python excel_automation.py --sample --out /tmp/distrofit_automation.xltm
python excel_automation.py batch_a.csv batch_b.csv --column weight --out /tmp/batches.xlsm
```

Each CSV's filename stem becomes its dataset name. The selected column must be
numeric in every CSV, with at least eight finite, varying measurements per batch.
There are at most 20 batches and 100,000 total observations. Ambiguous names,
unsupported distributions and invalid data are rejected before export. From Python,
`create_automation_workbook({"Batch A": values}, candidates=["Normal", "Gamma"])`
returns the same packaged workbook as bytes. A failed fit is recorded in
**DatasetIndex**; a batch with no successful fits stops the build.

## Design and verification limits

I kept the statistical fitting in `analysis.py` so VBA does not introduce a second
implementation of the models. Python stores the training split, actual fitted
parameters, scores and histogram/curve points. VBA selects a saved dataset and
curve, validates them, copies their result rows, and recalculates the view. New
Raw or Cleaned data never silently replace the saved fits.

XlsxWriter creates the workbook and charts. pyOpenVBA packages the source and the
binary form designer, adds the Microsoft Forms reference and embeds the Power
Query connections. The final package declares the correct macro workbook or macro
template file type. No VBIDE access, ActiveX worksheet controls, shell commands,
network calls or automatic macro execution are needed by the delivered VBA.

```sh
python -m pip install -r requirements-dev.txt
npm ci --ignore-scripts
python automation/lint.py
npm run lint
npm test
python -m pytest -q
```

The automation CI job parses both VBA modules and the M query, type-checks the
Office Script against Microsoft's vendored API declarations, runs ESLint, executes
the script's real `main` in a small workbook API sandbox, and builds both downloadable
formats. Pytest checks the packaged form, macro source, charts, connections,
file types, data limits and scores against the existing Python engine. It executes
the embedded VBA refresh in pyOpenVBA's Excel interpreter and executes the unchanged
form handlers with simulated list and label controls. The M test runs the delivered
transformation against the bundled CSV; only the binary file source is supplied
by the test.

These are local interpreter and sandbox tests, not a recorded native Microsoft
Excel test. The form designer and Microsoft Forms GUI, Excel's Office Script
service, and native Power Query refresh still need a manual check in their
Microsoft hosts. LibreOffice and Excel for the web do not replace desktop Excel
for the VBA window. The existing `.xlsx` cutoff review remains available without
macros or the optional automation dependency.
