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
On **Production anomalies**, I can also find individual stops and cycle times
that look unusual compared with earlier production. I can inspect the flagged
records and compare two ways of finding them before deciding what to investigate.

Before collecting those measurements, I can check that the bench is ready. On
**Workplace organization**, I score a 6S checklist, six areas for keeping work
organized, consistent and safe, and record evidence and follow-up actions. I can
compare dated audits, see which gaps repeat, and turn the measurement steps into
a flow chart and written procedure. To try it, open that page and load the
generated audits under **History and findings**.

I also wanted to estimate equipment life without throwing away the operating hours
from units that were still running. The Reliability page keeps those units in the
calculation, compares possible life curves and shows how uncertain the estimates are.

This is a personal project. It accepts a numeric CSV column, a column from a
plain-text table, as well as pasted numbers or generated samples, and runs without an
account. To try it, start the app below and choose Sample Data, or open Reliability
in the sidebar for a generated equipment log. Choose **Grouped measurements** to
compare related batches and see how uncertain their averages are.

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
For unusual stops or cycle times, open **Production anomalies** and click
**Analyze events** to try a generated log with known faults.
Tail & Q-Q checks the extremes and compares matching percentiles,
the values below which a given share of observations fall. Scenario tries new numbers
against the same fitted curves; Manual lets me adjust a curve myself. Download
reproducible report saves the analysis and its data in a PDF. Stop the app with
Ctrl-C. Reports contain the input values, so keep private exports private.

## Improving a production process

I use the DMAIC board to organize a production problem from definition through
measurement, analysis, improvement and control. The worked example looks at fill
volume, defects and stopped time. It shows whether readings fall outside the
specification, ranks the reasons for defects and downtime, and keeps a five-why
investigation and actions beside each category. The example is invented, so its
causes and improvements still need to be checked in a real process.

```sh
python dmaic.py --input examples/dmaic/production.json --out /tmp/dmaic-board.html
```

Open the resulting page in a browser and print it in landscape to make a one-page
board. Edit a copy of the JSON input to use another process. Cp compares the
allowed range to process variation; Cpk also accounts for an off-centre average.
The chart uses the first 12 readings as its reference period. Investigate signals
and check that the process is stable and approximately normal before relying on
capability as a prediction. The [guide](docs/dmaic.md) explains the inputs and
limitations.

I also keep an example grease-trap inspection and change-review register. It
stores inspections in SQLite, a local database, exports open notices to Excel,
and tracks a process drawing so a changed file flags its reviewed nodes for
another look. The drawing opens in draw.io, a free diagram editor. Try it with:

```sh
python process_safety.py sample --db /tmp/grease-trap.db
python process_safety.py notices --db /tmp/grease-trap.db --out /tmp/notices.xlsx
python process_safety.py changes --db /tmp/grease-trap.db
```

Use a new database path for each sample. The [process safety guide](docs/process-safety.md)
explains the example hazard review, change tracking and practical limits.

## Checking the bench and keeping the process clear

I wanted a record of bench readiness alongside the measurement results. On
**Workplace organization**, I open each of the six checklist sections: sort,
set in order, shine, standardize, sustain and safety. I enter what I observed,
score each check from 0 to 4, and assign an action, responsible role and due date
for every gap. A check that does not apply needs a reason and is excluded from
the possible points. Safety findings stay visible beside the overall score.

**History and findings** compares dated audits for one area. The Pareto chart,
bars ranked from most frequent to least frequent, shows which kinds of gaps keep
returning. I download the JSON history, a portable text backup, before closing
the app and restore it next time. This is session storage, so restarting the app
without a backup loses the entered history. Old action records stay as audit
snapshots rather than becoming a shared task tracker.

Under **Process and SOP**, I edit a documented step list and choose **Generate
flow chart and SOP**. An SOP is a standard operating procedure, the written
instructions for doing the work consistently. The diagram and instructions come
from the same steps, including who is responsible, what record to keep and where
to go when a check fails. The example follows samples from receipt through bench
preparation, calibration checks, measurement, review and a saved DistroFit analysis.

The diagram generator needs Graphviz. I can also create the complete worked
review without opening the app:

```sh
brew install graphviz
# Ubuntu or Debian: sudo apt-get install graphviz
python six_s_report.py --sample --out /tmp/distrofit-bench-review
```

I open `/tmp/distrofit-bench-review/index.html` in a browser to see the charts
and SOP. The folder must be new. The three generated audits score 50%, 75% and
91.67%, while the last audit still has two safety findings. These are example
observations, not a measured workplace improvement or a safety certification.
The [bench audit guide](docs/6s.md) explains the scoring, backup format, process
routes and limitations. I can also inspect the
[generated flow chart](examples/lean/process.svg) and
[SOP page](examples/lean/sop.html) in the repository.

## Finding unusual stops and cycle times

I wanted to see which individual production events deserved a closer look, beyond
the total minutes lost. On **Production anomalies**, I start with 800 generated
events, edit the table or upload an event CSV, then click **Analyze events**.
The chart marks unusually long stops and unusually fast or slow cycles. The table
keeps each event's ID so I can find it in the original log.

I compare IsolationForest, a method that finds values easy to separate from the
rest, with a robust baseline that measures distance from the typical duration.
Both learn from earlier events and check later ones. The first quarter of the log
is reference data and has no flags. The generated faults let me count false alarms
and missed faults; my own unlabelled data gets flags without an accuracy claim.

I can save the comparison without opening the app:

```sh
python anomaly_report.py --sample --out /tmp/distrofit-anomalies
# Or use one machine/product log:
python anomaly_report.py events.csv --out /tmp/my-production-review
```

The output folder must be new. I open `events.html` for the offline interactive
chart, or `powerbi/DistroFit.pbip` in Power BI Desktop on Windows for the event
table and flag filters. CSV files keep all events, both methods' flags and scores,
and the comparison results. The [production event guide](docs/anomalies.md) gives
the input format and explains the report.

In the generated example, the forest finds **21 of 26 faults** in the later
periods, with **7 false alarms**. The robust baseline finds all 26 without false
alarms. That is a useful warning against assuming the more complex method wins.
These faults are deliberately large changes, so this result says nothing about
accuracy at a factory. Flags need inspection, especially after a product change.

## Comparing batches with different sample sizes

I wanted to compare related batches without letting a handful of readings make a
small batch look more certain than it is. On **Grouped measurements**, I start
with 80 generated readings across four batches, or upload a CSV with `group` and
`value` columns. I choose **Fit grouped model** to estimate each batch's average
and a range of plausible values. Small batches borrow information from the others,
called partial pooling, while keeping their own averages.

The blue charts show plausible averages after fitting, called posterior
distributions, beside separate fits for each batch. I check whether the sampling
was reliable and whether simulated readings resemble the input. Both methods use
the same training rows and are scored on the same readings set aside. Changing
the input clears the old results, so I cannot download a stale comparison.

The model uses PyMC and assumes independent, roughly bell-shaped readings with a
shared noise level. It is useful for related batches or machines; it does not
replace the other curve choices or censored lifetime analysis. The page explains
its assumptions and withholds results when sampling checks fail.

I can also save the complete example, including sampled values and interactive
charts, without opening the app:

```sh
python bayesian.py --sample --out /tmp/distrofit-grouped
```

The output folder must be new. The [grouped comparison guide](docs/bayesian.md)
explains the CSV format, priors (assumptions before fitting), uncertainty intervals,
held-out scores and convergence checks. On macOS 27, that guide includes the
Numba fallback for an upstream compiler issue.

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

The grouped-model tests run real
NUTS sampling with fixed seeds, recover known batch averages and noise, check
partial pooling and predictive scores, and reject
poor or missing convergence diagnostics. The app tests fit the generated sample
and check that edits remove stale downloads. CI also saves a sampled comparison
with posterior draws and diagnostic tables.

The 59 bench-audit and process checks include hand-calculated scores, portable
history, real Graphviz output, invalid routes, and the app and command-line
workflows. CI installs Graphviz, generates the complete bench-review bundle and
saves it as an artifact alongside the existing reports.

The anomaly tests check fixed-seed fault recovery, training-only scaling, future
data leakage, constant durations, missing labels, invalid logs, exported flags,
Power BI bindings and real app edits. CI runs the full pytest suite, saves the
generated anomaly report, and opens both Power BI projects on Windows to execute
native calculations and capture their pages. The [event guide](docs/anomalies.md)
records the test results and assumptions.

## Demo

https://github.com/user-attachments/assets/22ecb55e-d376-41b3-9a65-00a335085e1f

## License

MIT; see [LICENSE](LICENSE). Dependency terms, including native libraries and fonts,
are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
