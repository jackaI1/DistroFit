# How the analysis works

Details of fitting, comparison and report export.

## How it works

1. **Load and prepare data.** [`DistroFit.py`](../DistroFit.py) handles sample,
   pasted and uploaded inputs. [`analysis.py`](../analysis.py), `read_csv`, preserves
   the first observation in a fully numeric headerless CSV. `prepare_data`
   removes nonfinite values and optionally applies Z-score or IQR filtering.
   Fitting requires at least eight finite, varying observations after filtering.
2. **Create a fixed split.** `fit_candidates` in
   [`analysis.py`](../analysis.py) permutes observation indices using NumPy's seeded
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
   [`analysis.py`](../analysis.py) write a PDF containing method, versions, failures,
   parameters, diagnostics, source/prepared/scenario data and split membership.
   A first-page annotation stores the full JSON payload as well as the readable
   report. The export control is in [`DistroFit.py`](../DistroFit.py).

The split, winner, support, scenario and export claims are tested in
[`tests/test_analysis.py`](../tests/test_analysis.py); interface state and controls
are covered in [`tests/test_app.py`](../tests/test_app.py).
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
