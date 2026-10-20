# DistroFit

A local Streamlit application that fits probability distributions on training observations, ranks them by held-out loss and exports the analysis with its data.

https://github.com/user-attachments/assets/5dd039d0-0a6c-4b1d-8c2b-f692d58ff349

## Overview

A curve can fit the observations used to estimate it and still predict new
observations poorly. Histogram appearance alone can also conceal tail mismatch
or a model whose support excludes part of the data.

DistroFit separates parameter estimation from comparison. It fits selected
SciPy families to one training split, ranks the frozen models on held-out
observations, and exposes tail checks and residual plots. Another scenario can
challenge the same parameters without refitting. A PDF records the method,
settings, scores and every observation used.

This personal project accepts generated samples, pasted numbers or a numeric CSV
column. The included evaluation fixtures are synthetic and require no external
account or model service.

## How it works

1. **Load and prepare data.** [`DistroFit.py`](DistroFit.py) handles sample,
   pasted and uploaded inputs. [`analysis.py`](analysis.py), `read_csv`, preserves
   the first observation in a fully numeric headerless CSV. `prepare_data`
   removes nonfinite values and optionally applies Z-score or IQR filtering.
   Fitting requires at least eight finite, varying observations after filtering.
2. **Create a fixed split.** `fit_candidates` in
   [`analysis.py`](analysis.py) permutes observation indices using NumPy's seeded
   generator. The held-out size is `max(2, ceil(N × fraction))`, with fraction
   between 0.1 and 0.5. The default is 0.25 and seed 42. Remaining observations
   form training data; returned indices retain the exact split membership.
3. **Estimate candidate parameters.** Each selected family calls SciPy's `fit`
   on training data only. At most four worker threads fit families concurrently.
   Invalid default fits are retried from an interior location with free location
   and scale; nonfinite final fits become visible failures. The 14 supported
   families are listed by `get_supported_distributions` in `analysis.py`.
4. **Select by held-out loss.** With parameters frozen, `score_values` computes
   `-mean(logpdf(x))` on held-out observations. The lowest mean negative log
   likelihood ranks first. A nonfinite density log value produces infinite loss;
   observations outside support are not clipped into a finite score. Training
   NLL, AIC, BIC and histogram SSE are displayed, but do not select the winner.
5. **Inspect mismatch.** `tail_check` uses the training 95th percentile as a
   fixed threshold, the model survival function for predicted exceedance share,
   and held-out counts for the observed share. A central 95% binomial prediction
   interval supplies an exploratory flag. `diagnostics` computes fixed-model
   Q-Q values, empirical-minus-model CDF residuals and density residuals using
   integrated model mass per histogram bin.
6. **Challenge and adjust.** `evaluate_scenario` scores another numeric sample
   without changing training parameters. `manual_curve` and `adjust_parameters`
   provide PDF/CDF views and user adjustments. Relative location moves use the
   training sample standard deviation; scale is multiplied. These edits do not
   change the held-out candidate ranking.
7. **Export a reproducible record.** `report_payload` and `create_report` in
   [`analysis.py`](analysis.py) write a PDF containing method, versions, failures,
   parameters, diagnostics, source/prepared/scenario data and split membership.
   A first-page annotation stores the full JSON payload as well as the readable
   report. The export control is in [`DistroFit.py`](DistroFit.py).

The split, winner, support, scenario and export claims are tested in
[`tests/test_analysis.py`](tests/test_analysis.py); interface state and controls
are covered in [`tests/test_app.py`](tests/test_app.py).

## Design decisions and trade-offs

- Held-out loss compares predictive density rather than histogram appearance.
  It reduces in-sample selection bias but has sampling variability, especially
  with few observations. It is one split, not cross-validation.
- Support violations retain infinite loss. This makes incompatible models
  visible, although small held-out samples can expose a fitted boundary abruptly.
- Filtering occurs before splitting. This makes the prepared population explicit
  but can remove the tail behaviour a reader wants to investigate.
- Fitting uses a bounded thread pool rather than one process per family. It
  limits concurrent workers; SciPy optimiser cost still depends on the data and
  family. No general constant runtime is claimed.
- PDF export includes the data and machine-readable analysis rather than only
  plots. Reports can become long, and an exported PDF contains the uploaded values.

## Results and evaluation

Reproducible here: the synthetic regression fixture draws 240 observations from
`np.random.default_rng(27).gamma(2, 2, 240)`. With a 0.25 held-out fraction, 180
observations train the candidates and 60 evaluate them. Normal, Gamma and
Exponential are all fitted; Gamma has the lowest held-out loss in that fixture.
Run the backing tests with:

```sh
python -m pytest tests/test_analysis.py -q
```

`test_split_is_reproducible_disjoint_and_parameters_use_training_only` checks
split membership and Normal parameters against training mean/standard deviation.
`test_winner_uses_held_out_loss_and_exposes_training_loss` independently computes
Normal's held-out loss from SciPy log densities and checks the selected family.
These are controlled regression results, not a claim that Gamma fits arbitrary data.

The UI's generated Gamma sample has 1,000 observations with generator seed 42;
the default split produces 750 training and 250 held-out observations. Changing
the seed, family selection, filtering or input can change the winner and tail
flags. No external-data accuracy or performance benchmark is claimed.

## Getting started

Use CPython 3.12; fresh-copy verification used 3.12.14 on macOS arm64.
Direct versions are pinned in [`requirements.txt`](requirements.txt), including
Streamlit 1.66.0 and SciPy 1.18.1; [`requirements-lock.txt`](requirements-lock.txt)
constrains the transitive resolution. Run from the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run DistroFit.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false
```

Open `http://127.0.0.1:8501` and choose Sample Data in Data Import. The default
Gamma sample displays 1,000 observations and a 750/250 training/held-out split,
with candidate comparison and diagnostic tabs. The initial Upload CSV view waits
for input. Stop the server with Ctrl-C.

Use Auto-Fit to compare candidates, Tail & Q-Q to inspect mismatch, Scenario to
paste another sample, and Manual to adjust a curve. Download reproducible report
exports the current analysis as a PDF. Private source files should remain outside
the repository; exported reports contain their values.

## Testing

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The current suite has 24 passing tests:

- [`tests/test_analysis.py`](tests/test_analysis.py): 16 tests cover concurrent
  fitting, training-only estimation, reproducible splits, held-out selection,
  support violations, failed-fit recovery, tails, frozen scenario parameters,
  residual definitions, manual controls, preprocessing, CSV input and PDF payload.
- [`tests/test_app.py`](tests/test_app.py): 8 Streamlit AppTest cases cover sample
  changes, invalid input/stale-result removal, manual adjustments/reset, histogram
  and filtering controls, scenario input and report availability.

Tests use synthetic samples and real SciPy fits. AppTest may print its standard
missing ScriptRunContext warning outside a running server. No separate lint,
typecheck or package build is configured.

## Project structure

```text
DistroFit.py                 Streamlit input controls, plots and export
analysis.py                  preparation, fitting, scoring, diagnostics and PDF
tests/test_analysis.py      numerical and export regressions
tests/test_app.py           synthetic Streamlit interaction tests
requirements.txt             pinned direct dependencies
requirements-lock.txt        audited transitive constraints
THIRD_PARTY_NOTICES.md        dependency terms and attribution
```

## Limitations and known issues

- Observations are randomly split, without grouping or time-order constraints.
  Correlated records or time series need an appropriate independent validation
  design outside this app.
- Repeatedly adjusting candidates against the same held-out data weakens its
  independence. There is no untouched final test set or automatic cross-validation.
- SciPy optimisation can reach local optima. A completed fit is not proof that a
  family describes the generating process.
- Tail flags are exploratory, use a 95% binomial prediction interval and have no
  multiple-comparison correction. Held-out KS is a distance, not a calibrated
  model-selection significance test.
- Outlier filtering can hide tails. Mixtures, dependencies and discrete models
  are not automatically inferred by the supported continuous families.
- Fresh-copy checks cover macOS/Python 3.12; other platforms and future dependency
  versions need their own validation.

## License

MIT; see [`LICENSE`](LICENSE). Dependency licences remain applicable, including
MPL/font terms and SciPy native-library LGPL/GCC-runtime obligations and exceptions.
They are documented in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
