# DistroFit

I built a measurement comparison app because I wanted to check which mathematical curve still fit when I tried it on measurements it hadn't seen.

## Overview

A histogram groups measurements into bars so I can see their spread. Several curves
might look right against those bars, so I wanted a separate check. DistroFit fits
each curve to some of my measurements, then scores it on the measurements set aside.
I can inspect unusually high or low values, try another sample against the same
curves and save the analysis as a PDF, an Excel workbook or an editable PowerPoint
presentation. In Excel, I can change a cutoff and see how many measurements exceed
it without rerunning the app.

I also wanted to see where production time went, alongside the measurements.
The equipment page splits lost time into stops, slow running and rejected parts.
It ranks stop reasons by minutes lost and lets me compare a current changeover,
the work needed to switch products, with a proposed shorter one.

I also wanted to estimate equipment life without throwing away the operating hours
from units that were still running. The Reliability page keeps those units in the
calculation, compares possible life curves and shows how uncertain the estimates are.

This is a personal project. It accepts a numeric CSV column, a column from a
plain-text table, as well as pasted numbers or generated samples, and runs without an
account. To try it, start the app below and choose Sample Data, or open Reliability
in the sidebar for a generated equipment log.

## Run it

Use Python 3.12. From the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run DistroFit.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false
```

Open <http://127.0.0.1:8501>. Choose Sample Data or upload a CSV, then use Auto-Fit
to compare curves. For production time, choose **Equipment effectiveness** in the
sidebar; it opens with a worked example I can edit immediately.
Tail & Q-Q checks the extremes and compares matching percentiles,
the values below which a given share of observations fall. Scenario tries new numbers
against the same fitted curves; Manual lets me adjust a curve myself. Download
reproducible report saves the analysis and its data in a PDF. Stop the app with
Ctrl-C. Reports contain the input values, so keep private exports private.

## Estimating equipment life

On **Reliability**, I start with a generated log of 80 pump seals. Each row records
the hours from installation until failure or the last observation. A seal that was
still running gets `failed=0`; a failed seal gets `failed=1`. I can edit the table
or upload a CSV with `time` and `failed` columns, using operating hours throughout.
The example has 45 failures and 35 still-running seals.

I compare the fitted curves with a stepped survival curve, the share of units still
working at each age. I can inspect how failure risk changes with age and estimate
the share lasting beyond a planning age. The page reports mean life and B10, the age
by which the model expects 10% to fail, with confidence intervals to show uncertainty.
For the example, the Weibull model gives **976 hours mean life** and **378 hours B10**.
Mean life is mean time to failure for these first-life seals. It is mean time between
failures (MTBF) only when each independent replacement cycle starts as good as new.

I can save the calculation, life estimates and charts from the page, or run:

```sh
python reliability_report.py --sample --out /tmp/distrofit-reliability
# Or use my own equipment log, with 99% confidence intervals:
python reliability_report.py equipment_log.csv --confidence .99 --out /tmp/my-reliability
```

Each command needs a new output directory and saves JSON, CSV tables and a PNG chart.
The [worked maintenance example](docs/reliability.md) explains why dropping the
still-running seals changes the estimate, how to read the charts and what the
intervals mean. It also covers Weibull, lognormal and exponential models, which
describe different patterns of equipment life. These calculations assume comparable,
independent lifetimes and observation stopping for reasons unrelated to hidden
failure risk. They help me investigate a maintenance question; they do not choose
a replacement schedule automatically.

## Reviewing measurements in Excel

After fitting a sample, I choose **Download Excel review** beside the results.
I open the workbook in Excel and change the yellow cell **B4** on **Review**.
The counts, averages and shares above the cutoff use spreadsheet formulas.
The chart follows those shares. A value exactly equal to the cutoff does not count
as above it. I can also [download a worked example](examples/excel/distrofit_review.xlsx)
made from generated measurements, or recreate it without starting the app:

```sh
python excel_report.py --sample --out /tmp/distrofit_review.xlsx
```

For my own CSV, I use:

```sh
python excel_report.py measurements.csv --column weight --out /tmp/weight_review.xlsx
```

I keep the original values, the values used for fitting and testing, and each model's
scores together in the workbook. The model scores stay fixed when I change the
cutoff. I rerun DistroFit to change the data or refit a curve. The
[Excel guide](docs/excel-review.md) explains the formulas, export limits and tests.

## Switching batches and checking pasted measurements

I wanted to review several batches without rebuilding the Excel charts each time.
I open the [worked workbook](examples/excel/distrofit_automation.xlsm) in desktop
Excel, enable its macros and click **Choose dataset and curve** on **Comparison**.
The selection window updates the batch's model comparison table and plots the
chosen saved curve. A [reusable template](examples/excel/distrofit_automation.xltm)
starts a new copy with the same controls.

Before fitting new measurements, I paste `dataset`, `value` and `unit` columns into
**Raw** and run [Check measurements](automation/office-script/clean.ts) from Excel's
**Automate** tab. I enter my measurement limits and get cleaned values, a reason
beside each rejected row and a **QAQC** quality-check summary. The original paste
stays intact. The included older CSV import also fixes semicolon-separated columns,
header spacing and decimal commas through Power Query, Excel's repeatable import tool.

```sh
python -m pip install -r requirements-automation.txt
python excel_automation.py --sample --out /tmp/distrofit_automation.xlsm
# Or compare my own batches:
python excel_automation.py batch_a.csv batch_b.csv --column weight --out /tmp/batches.xlsm
```

The form uses VBA, Excel's desktop macro language. The cleaning step is an Office
Script, a TypeScript program run from Automate. The fitted scores stay in Python;
I export accepted new values as CSV and rebuild to fit them. The
[step-by-step guide](docs/excel-automation.md) covers macro setup, installing the
script, importing the sample CSV and the limits of the local test environment.

## Keeping a comparison I can check later

I can save the same analysis without opening the app:

```sh
python compare_distributions.py fit --sample --out /tmp/distrofit-comparison
python compare_distributions.py verify /tmp/distrofit-comparison
```

The example compares three curves using 180 measurements for fitting and 60 for
checking. It also tries a deliberately shifted sample against the original curves
to show when the high values stop matching. All example measurements are generated.
I get a readable PDF, the complete calculation as JSON, and a CSV score table.
The second command checks the files and recalculates the saved scores without
fitting the curves again. Each run needs a new output directory so I keep my earlier
results. [The comparison guide](docs/saved-comparisons.md) explains how to use my own
CSV files and what the checks can establish.

## Discussing a result in PowerPoint

I wanted to talk through a curve comparison without rebuilding charts from
screenshots. **Download editable PowerPoint** saves the current comparison as a
presentation. It starts with the result and links to the score chart, the check
of unusually high values and the method. Each candidate has a detail slide with
its fitted values. The [worked example](examples/powerpoint/synthetic-review.pptx)
uses generated measurements and can be opened directly in Microsoft PowerPoint.

I can create the same example without running the app:

```sh
python powerpoint_report.py --sample --out /tmp/distrofit-review.pptx
# Or use my own CSV column:
python powerpoint_report.py measurements.csv --column weight --out /tmp/my-review.pptx
```

In PowerPoint, I can select a chart and choose **Chart Design > Edit Data** to
change its embedded table. **View > Slide Master** changes the shared design.
**Slide Show > Custom Slide Show** offers a short discussion or the full review,
and Presenter View shows the method notes beside each slide. Links on the slides
work during the slide show. [The presentation guide](docs/powerpoint.md) walks
through the editing steps and explains the file design.

The charts contain a saved comparison. Editing a chart does not rerun the
statistics. The presentation leaves out raw measurements, manual curve changes
and the second scenario; the PDF remains the complete analysis record. Infinite
scores appear as exclusions, and an analysis with no finite scores has no winner.

## Finding lost production time

On **Equipment effectiveness**, I enter one machine's shift length, breaks, fastest
time per part, total parts and parts that passed without rework. I enter each stop
once in the editable log, including changeovers. I can replace the example tables
with CSV files or delete their rows to start fresh.

The page calculates overall equipment effectiveness (OEE): how much of the planned
time became good output at the ideal speed. It shows availability (time running),
performance (speed against the ideal) and quality (first-pass good parts) separately.
The downtime Pareto chart puts the reasons that lost the most minutes first, so I
can choose what to investigate instead of counting every short stop equally.
I can download the calculation as JSON or the ranked downtime table as CSV.

The changeover table separates tasks that need the machine stopped from preparation
I could do while it runs. I can propose moving or shortening tasks and see the
potential stopped minutes saved. This follows SMED, a method for shortening
changeovers. It leaves the measured production result alone: a proposal is not
evidence that I have saved time.

I can also run the same calculations without the app:

```sh
python equipment.py --sample --out /tmp/distrofit-oee
```

The example gives **74.79% OEE** and a separate proposed changeover reduction from
**20 to 11 minutes**. It saves JSON summaries, CSV tables and a downtime chart.
[The input guide](docs/oee.md) explains how to use my own files, the calculations,
and where the example numbers come from. The tool handles one machine and one
product at a time; it does not infer overlapping stops or parallel changeover work.

## Comparing several datasets

I wanted to compare several samples without opening a separate analysis for each
one. I use the [Power BI report](powerbi/DistroFit.pbip), an interactive report I can
open in Microsoft's free Power BI Desktop on Windows. It includes twelve public
sample datasets and four pages: an overview, curve rankings, fit checks and the
parameters for each dataset. I choose a dataset or source in the filters to see
which curves win and whether those winners pass the fit check.

To try it, clone this repository, open **powerbi/DistroFit.pbip** in Power BI
Desktop and choose **Home → Refresh** to populate the bundled sample. The report
and its model, the tables and calculations behind the pages, are included as
editable project files. I do not need an online account to use the sample.

For my own measurements, I export the fitted results and rebuild the report's
snapshot:

```sh
python export_powerbi.py measurements.csv --column weight --out powerbi_export
python powerbi/build_project.py --export powerbi_export
```

I close Power BI before rebuilding, remove the local
`powerbi/DistroFit.SemanticModel/.pbi` cache if it exists, then reopen the project
and refresh. Rebuilding replaces the report's data; I keep private exports and
rebuilt projects out of Git. The [report guide](powerbi/REPORT.md) explains the
calculations, reference checks and how to repeat the native Windows test.

## Looking at measurements over time

A curve describes the spread of values; it doesn't say whether a process has changed.
The separate [calculation module](spc.py) makes control charts, which compare later
measurements with a baseline, and compares the spread with chosen specification
limits. I can also rank finding categories by frequency before choosing what to
investigate. The control-chart and capability calculations are called from Python;
the equipment calculations above also have an app page.

Run the [worked example](docs/case-study-dmaic.md) with:

```sh
python docs/dmaic_case_study.py
```

The example uses generated drawing-review times. Its reported two-hour to
thirty-minute real-use comparison is separate from the illustrative data used for the
calculations.

I also wanted to work out why a frequent finding happened before choosing a fix.
The [completed investigation](docs/root-cause-investigation.md) uses generated
drawing packages to trace revision mismatches to a rule that accepts an old cached
parts list. I compare possible causes, test that rule, then check a replacement
that requires the approved parts list to match the drawing. It reduces revision
mismatches from 38 to zero in the same 100 synthetic packages and retains all 62
other findings. A second generated batch checks whether the fix still works.
These are replay results, not production measurements.

```sh
python docs/root_cause_investigation.py --out /tmp/distrofit-root-cause
```

I can inspect the package-by-package evidence and ranked finding tables in that
folder, then copy the [blank worksheet](docs/root-cause-worksheet.md) for a new
investigation. The worked case explains the evidence, rejected alternatives,
time assumptions and follow-up checks.

## Notes and tests

[How the analysis works](docs/analysis.md) explains the split, scoring, tail checks
and PDF contents. The comparison uses one random split, so a different sample can
change the winner. A good score is not proof that a curve describes the real process.
Correlated or time-ordered data need a different validation approach; filtering
outliers can also hide the tails I want to inspect.

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover the calculations, app controls, exported tables and worked example using
synthetic samples. Saved-comparison tests check training-only parameters, frozen
scenario scores, changed files and statistics, invalid inputs, and both commands
in separate processes. Equipment tests also check a published OEE example, hand-calculated
losses and changeover savings, invalid inputs, zero-output periods and both ways of
running the feature. Dependency versions are in [requirements.txt](requirements.txt)
and [requirements-lock.txt](requirements-lock.txt).

Reliability tests check NIST's published censored Weibull example, independent
SciPy fits, hand-calculated survival and life intervals, time-unit changes,
invalid and all-suspended logs, command-line exports and editable app controls.
CI also runs the generated maintenance example and saves its report as an artifact.

The Excel automation checks add 24 pytest cases and 9 Office Script sandbox cases.
CI parses the VBA and Power Query source, runs TypeScript checks and ESLint,
executes the refresh and import logic in local interpreters, and builds the macro
workbook and reusable template. Native Microsoft Excel GUI and service checks are
manual; the [automation guide](docs/excel-automation.md) makes that boundary explicit.

## Demo

https://github.com/user-attachments/assets/22ecb55e-d376-41b3-9a65-00a335085e1f

## License

MIT; see [LICENSE](LICENSE). Dependency terms, including native libraries and fonts,
are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
