# DistroFit

I built a measurement comparison app because I wanted to check which mathematical curve still fit when I tried it on measurements it hadn't seen.

## Overview

A histogram groups measurements into bars so I can see their spread. Several curves
might look right against those bars, so I wanted a separate check. DistroFit fits
each curve to some of my measurements, then scores it on the measurements set aside.
I can inspect unusually high or low values, try another sample against the same
curves and save the analysis as a PDF or an Excel workbook. In Excel, I can change
a cutoff and see how many measurements exceed it without rerunning the app.

I also wanted to see where production time went, alongside the measurements.
The equipment page splits lost time into stops, slow running and rejected parts.
It ranks stop reasons by minutes lost and lets me compare a current changeover,
the work needed to switch products, with a proposed shorter one.

This is a personal project. It accepts a numeric CSV column, a column from a
plain-text table, as well as pasted numbers or generated samples, and runs without an
account. To try it, start the app below and choose Sample Data.

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

I can also export results as tables to compare datasets in Power BI, Microsoft's
interactive reporting tool:

```sh
python export_powerbi.py --sample --out powerbi_export
```

This uses the bundled public datasets. For my own file, I can replace `--sample` with
`measurements.csv --column weight`. The [report guide](powerbi/REPORT.md) explains
how to load the CSV or Parquet tables (a compact table format) and assemble the
report in Power BI Desktop. The repository includes the queries, measures and sample
export, but no finished `.pbix` report. The measures still need checking in Power BI
Desktop.

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
calculations. The [investigation worksheet](docs/root-cause-worksheet.md) helps
record possible causes, evidence and follow-up checks without treating a frequent
category as a proven cause.

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

## Demo

https://github.com/user-attachments/assets/22ecb55e-d376-41b3-9a65-00a335085e1f

## License

MIT; see [LICENSE](LICENSE). Dependency terms, including native libraries and fonts,
are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
