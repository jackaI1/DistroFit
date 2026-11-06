# Reviewing unusual production events

I use this page when the equipment totals tell me time was lost and I want to
find the individual records behind it. A flag means a duration differs from the
earlier log. It does not establish a mechanical fault or its cause.

## Try it

With the README's Python 3.12 environment installed:

```sh
python -m streamlit run DistroFit.py
```

Open **Production anomalies**, then **Analyze events**. The initial table is an
800-event generated log for one machine and product. I can edit it or upload a
CSV. Changing a row clears the old analysis and downloads. Analysis is explicit,
so editing the table does not repeatedly fit the forest.

For a saved report, use a new output directory:

```sh
python anomaly_report.py --sample --out /tmp/distrofit-anomalies
python anomaly_report.py events.csv --out /tmp/my-production-review
```

The CLI refuses to replace an existing folder. It saves `events.csv`,
`metrics.csv`, `summary.json`, an offline `events.html` Plotly chart and a
`powerbi/` native report project. These exports include the input rows, so I keep
private production exports private. Only the generated sample is committed.

## Input format

```csv
event_id,timestamp,event_type,duration_seconds
cycle-001,2026-01-01T08:00:00Z,cycle,45.2
stop-001,2026-01-01T08:01:00Z,downtime,240
```

This shows the columns, not a complete reference log. The analysis needs at least
80 rows and at least 20 rows of each event type in its first training period.
For two alternating event types, 160 or more rows meets that requirement.

- `event_id`: a unique nonempty record identifier, preserved in the chart and exports.
- `timestamp`: a unique date and time. Offsets are converted to UTC; an absent
  timezone means UTC. Rows are sorted chronologically. Simultaneous events must
  be ordered explicitly with distinct timestamps before import.
- `event_type`: `cycle` or `downtime`. One type alone is also supported.
- `duration_seconds`: a finite, positive number of seconds. Convert minutes first.
- `is_fault`, optional: 0 for normal and 1 for a known fault. If supplied, every
  row needs a valid label. It is used only to measure accuracy, never for fitting.

Other columns are excluded. Missing or invalid rows are rejected with a reason
instead of quietly changing the sample. Reports are limited to 5,000 events so
the interactive review and portable snapshot remain manageable.

## What I compare

Each method fits durations separately for cycles and stops. Mixing a normal
four-minute stop with a normal 45-second cycle would otherwise confuse their
different scales. I also keep different machines, products and operating modes
in separate reports.

The scikit-learn pipeline contains `RobustScaler` and `IsolationForest`.
The scaler learns a median and interquartile range, the spread of the middle
half of the training values. The forest uses 200 trees, contamination 0.05,
random seed 42 and one worker. Contamination sets a threshold using the expected
unusual share of the reference data; it is not an estimate of the fault rate.
Scaling is not necessary for a one-dimensional forest, but keeping it inside
the fitted pipeline ensures preprocessing stays local to each training fold.

The robust baseline computes `abs(duration - training_median) / (MAD / 0.67448975)`.
MAD is the median absolute distance from that median. A score above 3.5 is flagged.
If MAD is zero, a tolerance of `max(abs(median), 1) * 1e-9` avoids division by zero
and flags material departures from a constant reference. A forest trained on
constant values cannot learn a useful outside boundary, which the tests expose.
Forest score is the negative decision function; values above zero are flagged.
Neither method's score is a probability, and their score magnitudes differ.

## Checking future events

`TimeSeriesSplit(n_splits=3)` creates three expanding chronological folds. With
800 rows, the first 200 are reference only. The next 200 are checked against them;
then 400 reference rows check the next 200, and 600 check the final 200. Every
later event is checked exactly once. Previous test periods become part of later
training periods, like a periodically refreshed production model. Known fault
labels do not remove rows from training, so earlier faults can mask later ones.

Both scaling and baseline statistics are freshly fitted inside each fold.
The fixed settings are not selected using these test labels. `summary.json`
records all fold boundaries, training counts, scaler medians and settings.
Python callers can use `DurationDetector().fit(reference).score(later_events)`
for a frozen reference, or `evaluate_events(frame)` for the full comparison.

## Reading the worked results

The generator injects 40 faults into 800 records: long stops and both slow and
fast cycles. Fourteen faults fall in the initial reference period; the accuracy
table covers only the remaining 26 faults in 600 evaluated events.

| Event type | Method | Found faults | False alarms | Missed faults | Precision | Recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Cycle | IsolationForest | 10 | 0 | 5 | 100% | 66.7% |
| Cycle | Robust baseline | 15 | 0 | 0 | 100% | 100% |
| Downtime | IsolationForest | 11 | 7 | 0 | 61.1% | 100% |
| Downtime | Robust baseline | 11 | 0 | 0 | 100% | 100% |

Precision is `TP / (TP + FP)` and recall is `TP / (TP + FN)`: TP means a found
fault, FP a false alarm, FN a missed fault, TN a correctly unflagged normal event.
A zero denominator is reported as zero. Without labels, all accuracy fields are
blank rather than treating model predictions as truth. Counts still work.

The injected changes are deliberately obvious. These are reproducibility and
integration checks, not evidence that either detector has this accuracy on real
equipment. This implementation uses duration alone, so a combination of normal
durations with unusual pressure or temperature will need more features. Trend,
maintenance, a new product or a contaminated reference can all change the result.

## Power BI

Open `powerbi/DistroFit.pbip` inside the output directory in Power BI Desktop on
Windows, with project-format support enabled. No account, gateway or Python
installation is needed to view it. The report snapshots exported values in native
calculated tables, using the same project format as DistroFit's fit comparisons.
The committed [sample project](../examples/anomalies/powerbi/DistroFit.pbip) is ready
to open. Rebuild through Python to update the snapshot.

The top table shows comparison results by method and event type. The event table
shows both flags, durations and record IDs. Choose **True** on a method's flag
filter to inspect its flagged events. Selecting both True filters shows their
intersection; clear both to see all rows. Blank flags belong to warm-up rows,
not confirmed normal events. Event filters affect the event table only: the top
accuracy table deliberately stays the complete held-out comparison. Both tables
can also be imported directly from CSV through **Get data > Text/CSV**.

## Tests and implementation

`anomaly.py` owns validation, generation, fitting and evaluation;
`anomaly_report.py` owns plots and saved reports; `powerbi/anomaly_project.py`
builds native model and visual bindings. The app uses these same functions.

```sh
python -m pytest tests/test_anomaly.py tests/test_anomaly_report.py tests/test_anomaly_app.py -q
python -m pytest -q
```

Tests check reproducibility, future-value isolation, hand-counted confusion
matrices, training-only medians, frozen scoring, missing labels, bad records,
constant references, chart event IDs, CLI exports, Power BI fields and stale app
downloads. CI also runs the sample CLI and retains its outputs. The Windows job
opens the committed anomaly project, executes native DAX count and accuracy
checks, captures the page and verifies cleanup of its owned Desktop process.
There are 26 anomaly tests and 354 tests in the complete Python suite. On macOS 27,
I use the existing [PyTensor fallback](bayesian.md#try-the-grouped-page) when running
the full suite: `PYTENSOR_FLAGS='cxx=,mode=NUMBA' python -m pytest -q`.

References: [IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html),
[RobustScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html),
and [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
