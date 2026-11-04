# DistroFit

I built a measurement comparison app because I wanted to check which mathematical curve still fit when I tried it on measurements it hadn't seen.

## Overview

A histogram groups measurements into bars so I can see their spread. Several curves
might look right against those bars, so I wanted a separate check. DistroFit fits
each curve to some of my measurements, then scores it on the measurements set aside.
I can inspect unusually high or low values, try another sample against the same
curves and save the analysis as a PDF.

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
to compare curves. Tail & Q-Q checks the extremes and compares matching percentiles,
the values below which a given share of observations fall. Scenario tries new numbers
against the same fitted curves; Manual lets me adjust a curve myself. Download
reproducible report saves the analysis and its data in a PDF. Stop the app with
Ctrl-C. Reports contain the input values, so keep private exports private.

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
investigate. These calculations are called from Python and are not in the app
interface yet.

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
synthetic samples. Dependency versions are in [requirements.txt](requirements.txt)
and [requirements-lock.txt](requirements-lock.txt).

## Demo

https://github.com/user-attachments/assets/22ecb55e-d376-41b3-9a65-00a335085e1f

## License

MIT; see [LICENSE](LICENSE). Dependency terms, including native libraries and fonts,
are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
