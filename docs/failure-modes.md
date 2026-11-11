# Mixed failure modes notebook

The notebook `notebooks/failure_modes.ipynb` and the module `failure_modes.py`
answer two questions about a lifetime sample that may contain more than one
failure mode.

1. Do the records form groups, and how many? Silhouette (K-means) and BIC
   (Gaussian mixture) each choose a count from 2, 3 and 4.
2. Does a Weibull curve fitted to each group describe it better than one curve
   for the pooled sample? Each group is fitted with `fit_life_model` from
   `reliability.py`, so suspensions stay in the fit.

A third question uses install-time readings only: can logistic regression or a
random forest flag early failures? Here "early" means failure before 300 hours.

## Inputs

| column | meaning |
| --- | --- |
| `time` | hours from installation to failure or to the last check |
| `failed` | 1 if the unit failed at `time`, 0 if it was still running (a suspension) |
| `load` | fraction of rated load, read at installation |
| `contamination` | contamination reading, read at installation |

`generate_records()` produces 600 invented bearings from two modes. The
`invented_mode` column is the answer key for that generator only. Real records
do not have it, and the notebook does not use it for any fit.

## Design choices

- **Features for clustering.** Life is logged, because failure ages spread over
  several decades. Suspension status is included so that a unit still running
  is not treated as the same as one that failed at the same age. All four
  columns are standardised.
- **Count of groups.** The scans stop at 4. An engineer can act on a few groups,
  and each group needs failures to support its own fit.
- **Suspended groups.** A group with no failures cannot support a Weibull fit,
  so the row is kept with a note instead of a guessed curve.
- **Early-failure labels.** A unit suspended before 300 hours could still fail
  early, so it is removed from the supervised test. Units that survived past the
  cutoff are labelled not early.
- **No leakage.** Age, suspension status and group labels come from the outcome,
  so they are never inputs to the early-failure models.
- **Cross-validation.** Stratified 5-fold, shuffled with the fixed seed. Every
  unit is scored by a model that did not train on it.
- **Reference model.** The prevalence-only model predicts the training average.
  Any useful model should clearly beat it on AUC.

## Saved run (seed 20261110)

- K-means silhouette: 2 groups 0.33, 3 groups 0.35, 4 groups 0.34. Picks 3.
- Gaussian mixture BIC: 2 groups -1633, 3 groups -1858, 4 groups -1833. Picks 3.
- Adjusted Rand agreement between the two 3-group labelings: 0.91.
- Pooled Weibull: shape 0.80, scale 2016 h. Groups: shape 0.71 (97 units, all
  failed), no failures (275 units, all suspended), shape 1.72 (228 units, all failed).
- Early-failure test: 580 usable units, 114 early failures (19.7%).
  Out-of-fold AUC: logistic regression 0.748, random forest 0.748, prevalence
  reference 0.496. Brier scores 0.135 and 0.138 against 0.158.

## Limits

- Clusters are a hypothesis about the process, not proof of two causes.
- Censored units are placed by their last-check age, which can move them into
  the wrong group. The no-failure group in the saved run is mostly that effect.
- The 300-hour cutoff suits this invented process. Choose the cutoff from the
  engineering question for real data.
- Calibration is checked on out-of-fold probabilities for one sample. Recheck it
  on a new batch before using the probabilities as risk numbers.

## Tests

- `tests/test_failure_modes.py` (main CI job): reproducibility, scaling, the
  scans, a known Weibull shape, the no-failure rule, the early-failure labels
  and the baseline checks.
- `pytest --nbmake notebooks/failure_modes.ipynb` (notebooks CI job): runs every
  cell headlessly and stops on the sanity checks at the end.
