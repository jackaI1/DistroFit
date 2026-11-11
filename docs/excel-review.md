# Excel measurement review

I use this workbook when I want to inspect a fitted sample and try different
cutoffs in a spreadsheet. I can filter the tables, check individual observations
and see the share above a cutoff change in the chart.

## Try it

I install the normal project requirements, then run:

```sh
python excel_report.py --sample --out /tmp/distrofit_review.xlsx
```

I open the file in Excel, select **Review** and change **B4**, the yellow input.
The generated example uses 240 Gamma observations from NumPy seed 27, with shape
2 and scale 2. DistroFit uses split seed 42 to fit on 180 observations and compare
the curves on the other 60. There is no second scenario in this example.

For an existing analysis in the app, **Download Excel review** includes its current
data, split and optional Scenario sample. It leaves the PDF download available.
The command line uses the default split, no outlier removal, and Normal, Gamma and
Exponential candidates. The app preserves the user's current choices.

## What I can change

On **Review**, B4 controls the observed counts and shares above a threshold.
It starts at the training sample's 95th percentile, the value below which 95% of
training observations fall. The comparison is strictly greater than the threshold.
The count and mean for each sample do not depend on that cutoff.

Only B4 is intended as an input. A validation rule asks for a number, including
zero or negative values. If I delete it or paste text over it, formulas show
`n.a.` for the dependent tail results. A missing scenario has count zero and
unavailable statistics, rather than a misleading zero mean or zero tail share.

**Families**, **Summary** and **Pivot** also follow B4, so the family counts above
the cutoff change with it. I leave **Candidates** and **Observations** as the exported record. Filtering
or sorting a table is fine. I regenerate the file to add observations or change
the fitted models; formulas use the bounded exported range, not arbitrary new rows.

## What stays fixed

**Candidates** holds each fitted model, parameters and comparison scores, plus
any failures. Negative log likelihood (NLL) measures how poorly a model explains
the data; lower held-out NLL ranks first. A value of `inf` stays text, meaning
at least one observation had zero density under the fitted model. It is never
converted to a zero score. Multiple failed candidates remain visible individually.

Changing the spreadsheet threshold does not change those scores, refit parameters,
or reproduce the app's predicted tail share or binomial tail flag at a new cutoff.
The Excel chart shows observed shares only. Manual curve edits belong to the PDF
record and are not substituted for the fitted candidates here.

**Observations** has two filterable Excel tables. One contains prepared values
with a Training, Held-out or Scenario label and a one-based index within prepared
or scenario data. The other preserves every original source value in order.
Removed NaN and infinite source values remain explicit text. The source index and
prepared index are different after filtering; the export does not claim a row-level
mapping between them. The settings on Review record filtering and split choices.

## Families, summaries and the pivot

Each measurement needs a family before the groups can be summarized. A family is a
plain-language shape for a fitted curve: **Symmetric, unbounded** (the normal, Student's t,
Cauchy and similar curves), **Positive and skewed** (gamma, exponential, Weibull, lognormal
and similar), and **Bounded between two limits** (beta and uniform). When no fitted curve gives
a value a positive density, the value goes to **Outside every fitted family**.

**Families** has one row per observation. Its **Best-fit distribution** column names the
fitted curve with the highest density at that value. That choice was made when the workbook
was written, from the frozen fits. Its **Family** column is a `VLOOKUP` on **Lookup**, the
table that maps each distribution to its family and plain meaning. If I rename a family on
Lookup, the lookups, Summary and pivot change after recalculation or a refresh.

**Summary** uses `COUNTIF` for observations per family, `SUMIF` for their total value,
`AVERAGEIF` for the average and `COUNTIFS` for those above the cutoff. A second grid uses
`SUMIFS` to total values by family and sample group. Its final check cell confirms that the
grid adds back to the overall total.

**Pivot** is a native Excel PivotTable over the Families rows. Families are the rows, sample
groups are the columns, and each cell counts observations. A PivotChart beside it is linked to
the same pivot. Excel refreshes the pivot when the file opens, and **Data > Refresh All**
updates it after edits. A pivot is a summary I can rearrange in Excel. The pivot is not
recalculated from Families by formulas, so its layout must be refreshed.

## Implementation and checks

`excel_report.py` uses XlsxWriter to create an in-memory `.xlsx` file, Excel's
workbook format. It writes typed numbers, filterable tables, frozen headers,
number formats, a validated input and a chart linked to the summary cells.
It disables automatic conversion of source strings into formulas or hyperlinks.
An input limit of 100,000 original or combined prepared/scenario observations
bounds export memory. The app shows an actionable message if that limit is exceeded
while keeping its other results and PDF available.

The summary uses `COUNTIF` for sample size, `AVERAGEIF` for the sample mean and
`COUNTIFS` for sample-specific exceedances, then divides by the matching count.
`IF`, `OR` and `ISNUMBER` distinguish missing samples and invalid thresholds.
Python supplies independently calculated cached results so previews work before
the first recalculation. Those caches alone are not evidence of live formulas.

XlsxWriter cannot write pivot tables. `excel_pivot.py` adds the standard pivot cache,
records, pivot definition and the chart's pivot link after the workbook is saved, and
the tests read those parts back. Excel refreshes the pivot on open. I have not opened
the file in desktop Excel here; the structure is checked by XML parsing, openpyxl and
LibreOffice in CI.

```sh
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/test_excel_report.py tests/test_excel_families.py -q
```

CI also installs LibreOffice Calc, an independent spreadsheet engine, and opens
disposable copies after changing B4 to zero, a negative value, a large value,
blank and text. The tests compare recalculated means, counts and shares with
independent NumPy calculations and scan for formula errors. A unique office profile
keeps those headless runs separate from any open user session. Set
`REQUIRE_SPREADSHEET_ENGINE=1` to fail rather than skip when that engine is missing.
The CI run publishes a synthetic workbook as a downloadable artifact.

The family tests compare VLOOKUP results, SUMIF and SUMIFS totals, and the pivot's
counts with pandas calculated from the same rows. The pivot definition is checked in the
XML, including its source range, row and column fields and count measure. The tests also
cover the generated and CSV command lines, literal formula-like input,
nonfinite source labels, missing scenarios, failed candidates, infinite loss,
invalid partitions and export limits. The app tests exercise the download control
and stale-result removal. Formula execution is tested in LibreOffice, not Microsoft
Excel itself. There are no macros, external workbook links or account requirements.
