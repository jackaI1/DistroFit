# Comparing related batches

I added this comparison because a batch with eight readings can look very different
from a batch with thirty, even when they come from similar processes. Pooling every
reading into one curve hides batch differences. Fitting each batch separately can
overreact to a small sample. Partial pooling takes a middle path: each batch keeps
its own average, while the averages inform one another.

## Try the grouped page

Install the repository requirements with Python 3.12, start `streamlit run
DistroFit.py`, and choose **Grouped measurements** in the sidebar. The editable
example has 80 synthetic readings in four batches of 32, 24, 16 and 8. Choose
**Fit grouped model**, wait for sampling, and inspect the checks before the charts.
Sampling only runs on submission. Changing the readings, seed or draw count clears
the previous result and its downloads. Selecting a plotted group reuses the fit.

For a real comparison, upload a CSV like this, with at least eight varying readings
in **each** of two to twenty groups, up to 2000 rows total:

```csv
group,value
Machine A,49.7
Machine A,50.2
Machine B,50.6
```

Those three lines illustrate the format; they are too few to fit. The complete
[synthetic CSV](../examples/bayesian/grouped_measurements.csv) is ready to run.
Missing labels, missing numbers and infinite values are errors. No outlier filter
or silent row removal changes the question. Values must use the same units.

A command saves the complete analysis without the app:

```sh
python bayesian.py --sample --out /tmp/distrofit-grouped
python bayesian.py examples/bayesian/grouped_measurements.csv --out /tmp/distrofit-my-groups
```

Each output folder must be new. It contains group comparisons, predictive checks,
every parameter's diagnostics, the settings as JSON, original readings with their
training/held-out roles, self-contained Plotly HTML charts, and `posterior.nc`.
That NetCDF file stores prior, posterior and predictive draws and sampler statistics;
I can open it with `arviz.from_netcdf`. Reports include input readings. I keep
reports from private data out of this public repository.

On macOS 27 with Apple's current linker, the pinned PyTensor release has an
[upstream compiler issue](https://github.com/pymc-devs/pytensor/issues/2268).
The documented Numba backend avoids the failing C linker:

```sh
PYTENSOR_FLAGS='cxx=,mode=NUMBA' python -m streamlit run DistroFit.py
PYTENSOR_FLAGS='cxx=,mode=NUMBA' python bayesian.py --sample --out /tmp/distrofit-grouped-mac
PYTENSOR_FLAGS='cxx=,mode=NUMBA' python -m pytest -q
```

Linux CI uses the normal compiled path. I keep NumPy at 2.4.6 because the pinned
Numba dependency supports NumPy below 2.5; the other existing runtime pins remain.

## Read the result

The blue distributions describe plausible **group averages**, after fitting the
training readings. Their bars are equal-tail 95% credible intervals: 2.5% of the
sampled probability lies below the lower end and 2.5% above the upper end.
They do not contain 95% of future individual measurements. The gray crosses show
independent normal maximum-likelihood estimates (MLE), the values that make each
group's training readings most likely without borrowing from other groups.
The comparison table keeps those means and each independent MLE standard deviation.
The shared Bayesian within-group SD appears as `sigma` in the saved posterior.

Both approaches fit the **same rows**. I call DistroFit's existing
`analysis.fit_candidates(..., ["Normal"])` in each group, using seed 42 by default
and a 25% holdout rounded up. The Bayesian model uses exactly those training rows;
held-out rows do not influence its prior calibration. For eight rows, six train
the models and two check them. I compare held-out negative log likelihood (NLL),
the average penalty for assigning little probability density to unseen readings.
Lower is better within the same group and units. The Bayesian score uses the
log of the mean predictive density across draws, which includes parameter
uncertainty, rather than averaging the log densities. I do not compare Bayesian
scores against MLE AIC/BIC or claim one split proves a winner.

## Model and priors

I use a hierarchical normal model in `bayesian.py`: each group's mean is drawn
from a common population of means, and all groups share one within-group SD.
PyMC samples it using NUTS (No-U-Turn Sampler), an algorithm that explores plausible
parameter combinations. Four chains run sequentially on one CPU core with one
BLAS thread. Defaults are 1500 warm-up and 1500 retained draws per chain, with
0.95 target acceptance. Increasing retained draws can improve Monte Carlo accuracy;
it cannot fix an inappropriate likelihood.

Let `c` and `s` be the mean and population SD of **training** readings only. In
standardized units:

```text
mu ~ Normal(0, 2)
tau ~ HalfNormal(1)
sigma_standard ~ HalfNormal(1)
z[group] ~ Normal(0, 1)
group_mean[group] = c + s * (mu + tau * z[group])
measurement[i] ~ Normal(group_mean[group[i]], s * sigma_standard)
```

A HalfNormal keeps a spread positive. These proper, weakly informative priors
allow broad variation at the training scale. This is empirical calibration, not
a prior specified independently of the data. The population mean prior has SD
`2*s`; both spread priors have scale `s`. For a new setting, inspect the predictive
checks and consider domain-specific prior scales before using a decision-critical
result. The non-centred offsets `z` help sampling when groups have few observations.
Posterior quantities are converted to original measurement units inside the model.

## Checks before interpretation

I sample 300 prior predictive datasets before fitting and a posterior predictive
dataset for every retained draw afterward. Both use the training groups and group
sizes. The chart compares replicated individual readings with the observed
histogram and independent MLE curve. A wide prior curve is expected; wildly
implausible values mean the scale assumptions deserve attention.

For each group's **mean, population SD and maximum**, I show the observed statistic,
the middle 95% of its prior and posterior replicated statistics, and the proportion
of replicates at least as large as observed. A flag means the observation is
outside the posterior 95% range. These are exploratory, in-sample discrepancy
checks, not calibrated hypothesis tests or independent predictive accuracy.
The held-out NLL is the separate unseen-data check. Passing sampler diagnostics
cannot override a poor predictive check.

ArviZ computes unrounded rank-normalized split **R-hat**, which checks agreement
between chains, and bulk/tail **effective sample size**, which measures independent
information in correlated samples. Every posterior variable is checked, including
population parameters, group means and non-centred offsets. The gate requires:

- R-hat at most 1.01 for every parameter.
- Bulk and tail ESS at least 400 for every parameter.
- Zero divergent transitions, sampler paths that became numerically unreliable.
- At least two chains, 100 retained draws per chain and finite diagnostics.

Missing divergence statistics, non-finite draws and undefined diagnostics also
fail the gate. The Python API raises `ConvergenceError` by default and the CLI
exits with code 2 before exporting. `strict=False` lets the app show failed
diagnostics, but the app withholds estimates and downloads. More draws or warm-up,
a higher target acceptance or a revised model may help, depending on the problem.
I never silently relax the thresholds to make a run pass.

## Assumptions and limits

This is for related, independent measurements with roughly normal noise and a
common within-group spread. It is unsuitable for censored lifetimes, counts,
strongly skewed values, serial correlation or groups with very different noise
levels. I use the Reliability page for suspended lifetime observations and the
main curve comparison for choosing other distribution families. Partial pooling
can hide genuine differences if unrelated groups are combined. Five or fewer
groups also give limited information about the population's between-group spread.
A credible interval reflects this model and its priors, not a guarantee about the
physical process. The small synthetic sample demonstrates behaviour, not factory
performance.

## Reproduce the checks

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The Bayesian tests run real seeded NUTS fits, recover known group means and common
noise, check pooling, independently recalculate mixture predictive scores, inspect
sampled prior/posterior checks, reject shifted/constant/short/divergent chains and
missing statistics, and exercise edits and downloads on the actual Streamlit page.
CI runs the full suite and the real sample CLI, retaining its report and posterior
draws as a seven-day artifact. Sampling and a single recovery example do not
establish calibration across every possible dataset.

References: [PyMC sampling](https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html),
[ArviZ diagnostics](https://python.arviz.org/en/v0.22.0/api/generated/arviz.summary.html),
and [rank-normalized R-hat](https://doi.org/10.1214/20-BA1221).
