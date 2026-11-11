# DistroFit

I built a measurement comparison app because I wanted to check which mathematical curve still fit when I tried it on measurements it hadn't seen.

## Overview

A histogram groups measurements into bars so I can see their spread. Several curves
might look right against those bars, so I wanted a separate check. DistroFit fits
each curve to some of my measurements, then scores it on the measurements set aside.
I can inspect unusually high or low values, try another sample against the same
curves and save the analysis as a PDF, an Excel workbook or an editable PowerPoint
presentation. In Excel, I can change a cutoff and see how many measurements exceed
it without rerunning the app. For a very large file, the command line can fit a random
sample of its rows instead of the whole file, as described in
[Fitting a very large data file](#fitting-a-very-large-data-file).

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

I can also inspect real battery measurements on **Battery fleet**. The saved study
shows how three laboratory cells lost capacity over repeated use and marks cycles
that differ from their recent history. A second experiment lets me compare a cell
model with measured discharge and heating at rates left out of my fit. Start the
app below and choose **Battery fleet** to try it without a data download.

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

## Comparing daily price changes

I wanted to learn how daily price changes behave under the same curve checks.
I added an importer using Bloomberg's Python SDK, the library for requesting
Bloomberg data. It turns closing prices into returns, the fractional change
from one available trading date to the next. A return of `0.01` means 1%.
I can try it without an account using invented prices:

```sh
python -m pip install --index-url https://blpapi.bloomberg.com/repository/releases/python/simple -r requirements-bloomberg.txt
python bloomberg_history.py --sample --compare --out .runtime/price-example
```

After the normal installation above, these commands save 40 synthetic prices,
39 returns and a comparison in `.runtime/price-example/metadata.json`.
In the app, I choose **Upload CSV**, select that folder's `returns.csv` and
use `simple_return` as the target column. The folder also keeps dated prices,
dated returns and the request settings so I can trace each number.
Each export needs a new folder to protect saved results.

For this time-ordered input, `--compare` fits Normal and Student's t curves to
the earlier 29 returns and checks the later 10. Student's t allows heavier tails,
meaning unusually large changes can be more likely than under a Normal curve.
The app's ordinary Auto-Fit uses a random split, so I use the saved chronological
comparison when I want to preserve time order. Neither result is a price forecast.

The sample builds real requests and response messages with Bloomberg's SDK test
facilities; its connection is simulated and every price is invented. I have not
used a licensed Bloomberg Terminal or verified live market-data access.
The separate `--live` command is implemented for an authorised Desktop API
session. The [price-history guide](docs/bloomberg.md) explains setup, error handling,
adjustments and why licensed exports should stay private.

## Reviewing battery fade and heating

I wanted to try the measurement checks on public battery experiments and learn
how well a physical cell model predicted readings I left out of its fit. On
**Battery fleet**, I choose cells, inspect flagged cycles and download their
measurements. Capacity means how much charge a cell can supply; fade is its loss
with repeated use. The saved run has **504 discharge cycles across three cells**.
It flags **29 cycles** and one cell for inspection, not confirmed failures.

The lower charts compare a separate experiment's measured voltage and surface
temperature with a model of discharge and heating. I fitted it at a rate that would
empty the nominal cell in one hour, then checked three other rates without fitting
again. Across nine held-out curves, voltage error was **0.060 to 0.070 V** and
temperature error was **0.40 to 2.95 °C**. The simulation covered at least **97.1%**
of each measured discharge duration. These are rates held out of my own fit;
the published starting parameters already used this experiment, so this is not
independent validation of those parameters.

To download the public data, check its file fingerprints and reproduce the report:

```sh
python -m pip install -r requirements-battery.txt
python -m battery_fleet --out .runtime/my-battery-report
```

Open `.runtime/my-battery-report/index.html` in a browser. It includes interactive
charts and works offline. The command needs a new output folder. It saves the
source fingerprints, cycle and cell tables, fitted parameters, errors and cooling
study beside the dashboard. The app shows the committed run, so I can inspect it
without installing the optional model. The download is under 50 MB.

Further down, the model uses PyBaMM's Doyle-Fuller-Newman equations, which describe
lithium movement and reactions, coupled to one average cell temperature. A cooling
study changes how easily heat escapes through the surface. At the highest tested
rate, changing that coefficient from 2 to 40 W/m²/K lowered predicted peak
temperature from **80.0 to 36.5 °C**. This is a simulation, not a measured cooling
improvement. The [battery guide](docs/battery.md) explains the public sources,
calculations, charge-pair exclusions, model assumptions and full results.

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
cutoff. I rerun DistroFit to change the data or refit a curve.

The workbook also sorts each measurement into a plain-language family, such as
"symmetric, unbounded" for bell-shaped curves or "positive and skewed" for curves
with a long tail toward high values. A **Lookup** sheet holds that mapping, so I
can rename a family in one place. **Summary** totals the measurements per family
with `SUMIF` and `COUNTIFS` formulas. **Pivot** is a real Excel pivot table, with a
chart linked to it, that counts measurements by family and by training, held-out
or scenario group. I can rearrange it in Excel, and **Data > Refresh All** updates it
after I change the lookup. The [Excel guide](docs/excel-review.md) explains how each
family and summary is calculated, along with the export limits and tests.

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

## Finding mixed failure modes in a notebook

I built a notebook because my Reliability page can give a misleading life estimate
when one sample mixes two kinds of failure. Some bearings wear out late, and others
fail soon after installation, usually from dirt or a poor fit. One curve fitted to
both groups describes neither group well. The notebook looks for groups in the
records, fits a curve to each group and compares it with the curve for the whole sample.
It also asks whether readings taken at installation can flag the early failures.

The records are invented, so the notebook runs anywhere and every number can be
checked. In the saved run, the whole sample gives a Weibull shape of **0.80**. Two of
the three groups it finds have failures, and their shapes are **0.71** and **1.72**. The
third group has 275 units and no failures, so no curve can be fitted to it. The pooled
curve sits between the two fitted shapes and describes neither. Shape is the number that says whether the failure rate rises with
age (above 1) or falls (below 1).

The notebook uses a Jupyter notebook, a document that mixes code, text and charts
so I can read each step. To try it, install the notebook tools and open the file:

```sh
python -m pip install -r requirements.txt -r requirements-notebook.txt
python -m jupyter lab notebooks/failure_modes.ipynb
```

Run the cells from the top. The first cell prints the seed, the fixed number that
makes every random step repeat. To use my own records, replace the generated table
with a CSV that has `time` (hours), `failed` (1 for a failure, 0 for a unit still
running), `load` and `contamination` columns.

I choose the number of groups two ways. For 2, 3 and 4 groups, K-means shows how
tight each group is, and a Gaussian mixture model shows how well a set of overlapping
bell-shaped groups explains the data. Both picked **3 groups** in the saved run. If
they had disagreed, I would compare the fits before trusting either one.

The early-failure test uses install-time readings, load and contamination, to predict
failures before 300 hours. Each bearing is scored by a model that did not see it,
using 5-fold cross-validation. On the saved run, logistic regression reaches an AUC of
**0.75**, where 0.5 is chance, and the prevalence-only reference reaches 0.50. At the
usual 0.5 cutoff it catches only about a fifth of early failures, so I check the
calibration plot before treating its probabilities as risk.

The technical side: `failure_modes.py` holds the functions (scaling, the cluster scans,
the per-group Weibull fits from `reliability.py`, and the cross-validated baselines), and
the notebook shows them with charts. The seeds are fixed, so the results repeat.
Continuous integration (CI) runs the notebook headlessly with `nbmake` in a separate job
and the tests in `tests/test_failure_modes.py` in the main job. The full method, limits and
how each choice was made are in [the notebook guide](docs/failure-modes.md).

## Testing changeover options with designed experiments

I built a planner for designed experiments because I want to compare changeover options
without guessing which change made the difference. A changeover is the time it takes to
switch a line from one product to the next. I can change the crew size, how long the
tooling takes to set up and whether the kit is pre-staged. Changing one thing at a time
misses cases where two changes work better together, such as a bigger crew helping only
when the tooling is slow.

A designed experiment changes several factors at once in a fixed pattern. Each factor has
a low and a high setting, and the runs cover combinations of them. The run order is shuffled
with a fixed seed, so the order looks random but I can reproduce it. Centre points are runs
halfway between the settings. If they come out differently from the other runs, the response
bends and a straight-line model is not enough.

After I run the trials and type in the measured minutes, DistroFit reports each factor and
each pair of factors. For every one it gives the effect, which is how many minutes the change
from low to high moves the changeover, a 95% interval and a p-value from an ANOVA test.
A p-value below 0.05 means the effect is unlikely to be noise. Two charts show the results:
a half-normal plot, where noise falls along a line through zero, and a Pareto chart that
ranks the effects by size.

To plan and analyse a study:

```sh
python -m pip install -r requirements.txt
python doe.py plan --factor crew_size=2:4 --factor tooling_minutes=5:15 \
  --factor kit=0:1 --factor fixture=0:1 --fraction fixture=ABC \
  --centre 4 --replicates 2 --out .runtime/changeover-plan
python doe.py analyse --plan .runtime/changeover-plan --out .runtime/changeover-report
```

The plan step writes `run_sheet.csv` in random order. I run the trials in that order, type
the minutes into the `response` column and run the analysis. To see a complete example
without any shop data, run `python doe.py --sample --out .runtime/doe-sample`. It simulates
a changeover study with effects I set in advance and fits it.

In that simulated study, the tooling setup time moves the changeover by **12.6 minutes**
(the built-in value was 12), the kit by **-10.2** and the crew size by **-7.8**. The fixture
came out at **3.0 minutes** against a built-in 4.0. The interval does not include 4, so
that is noise from the simulated readings, not a model failure, and it shows why I want more
replicates before I trust a small effect. The crew-and-tooling interaction is **2.8 minutes**,
but it shares its estimate with the kit-and-fixture interaction, so the table cannot say which
one produced it.

The technical side: `doe.py` builds the designs with coded values of -1, 0 and +1. A fractional
design such as `fixture=ABC` uses fewer runs, and the fit reports which effects share an
estimate in an `aliased_with` column. The least-squares fit is done with statsmodels, and
each ANOVA p-value comes from the sum of squares of its term. The tests in `tests/test_doe.py`
recover known effects exactly from noise-free data, recover them within tolerance from noisy
replicated data, check the sums of squares against the drop in residual error and check the
command line. The full method, the saved numbers and the limits are in
[the design-of-experiments guide](docs/doe.md).

## Faster bootstrap intervals on a GPU

I built an optional GPU path because bootstrap intervals are slow when I want them for all 14
of my candidate curves at once. A bootstrap interval comes from drawing many resamples, which
are new samples of the same size taken from my data with replacement, and seeing how much a
score moves across them. With 1,000 resamples and 14 curves, that is 14,000 full-sample
likelihood calculations. The likelihood is a score for how well a curve explains the data.

The CPU path is the default and works on any computer. When a CUDA graphics card is present
and I install the optional GPU requirements, the same calculation runs as a custom CUDA kernel
through CuPy, which evaluates all resamples in parallel. If no GPU is found, DistroFit falls
back to the CPU without asking me.

The intervals describe how much each curve's score moves with the resampled data. The curves
are fitted once on the full sample and their parameters are not refitted for each resample, so
the intervals do not show how much the parameters themselves would move. The
[GPU guide](docs/gpu-bootstrap.md) explains that limit.

On this Mac's CPU, a full run over 1,000 resamples took **0.04 s** for 200 values, **0.19 s**
for 1,000 values and **0.94 s** for 5,000 values. I have not yet run the GPU path on a GPU, and
the GPU-to-CPU agreement test is skipped on machines without one. To benchmark on a machine
with an NVIDIA card:

```sh
python -m pip install -r requirements.txt -r requirements-gpu.txt
python bench_bootstrap.py --sizes 200 1000 5000 --resamples 1000 --out .runtime/bench
```

Technically, `gpu_bootstrap.py` holds the closed-form log-densities for all 14 families in a
CUDA kernel, and `standard_logpdf_reference` in the same file mirrors them in NumPy so the
formulas are checked against scipy in every CI run. `tests/test_gpu_bootstrap.py` covers the
fallback, the error for a missing GPU, the repeatability of seeded results and the benchmark
report. GitHub's hosted runners have no GPU, so CI runs the CPU tests and a small CPU benchmark.

## Fitting a very large data file

I built a way to fit a curve to a huge file of measurements without opening the whole
file, because my laptop slows to a crawl on files with millions of rows. A CSV is a plain
text spreadsheet, one row per line. I wanted DistroFit to read a file like that a piece at
a time and keep a random handful of rows to work with.

The command reads the file in pieces of 100,000 rows. For each row with a number in the
chosen column, it gives that row a random score and keeps only the rows with the lowest
scores seen so far. That leaves a random sample of the size I ask for, where every row has
the same chance of being picked, and the memory use stays about the same whether the file
has thousands of rows or millions. Blank cells, text and infinite values are skipped and counted.
The saved report records how many rows were scanned, how many were skipped, the piece size,
the sample size and the seed, so the sample can be explained later.

To fit a random 5,000-row sample from a large file:

```sh
python compare_distributions.py fit --input measurements.csv --column Gamma_Measurement \
  --sample-size 5000 --out .runtime/large-fit
python compare_distributions.py verify .runtime/large-fit
```

The file needs a header row with the column name. To make a test file of two million rows:

```sh
python tools/make_large_csv.py --rows 2000000 --out .runtime/large/measurements.csv
```

The fit then works on the sample, not the whole file. The winner can differ from a fit of
every row, and the report says so through its sample settings. `tests/test_large_csv.py`
checks that every sampled value matches its source row, that the same seed repeats the
sample, that the piece size does not change it, and that the command line writes the sampling
record. CI generates a two-million-row file on each run and fits a 5,000-row sample from it.

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

The complete local suite passed 434 tests, including 15 battery checks.
Battery checks cover synthetic fault injection, public-file parsing, checksum
rejection, unit checks and real DFN charge/energy conservation tests. Battery CI
reruns the measured-data calibration and held-out study, checks error and coverage
limits, and saves the offline dashboard. See the [battery guide](docs/battery.md).

The Bloomberg history job installs the real native SDK and runs 33 importer
checks plus the 16 existing analysis checks. They cover real request construction,
partial messages, missing prices, provider errors, timeouts, session cleanup,
protected exports and chronological fitting. CI saves the synthetic example;
no licensed prices or credentials are published.

## Demo

https://github.com/user-attachments/assets/22ecb55e-d376-41b3-9a65-00a335085e1f

## License

MIT; see [LICENSE](LICENSE). Dependency terms, including native libraries and fonts,
are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
