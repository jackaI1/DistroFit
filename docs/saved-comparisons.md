# Saving a comparison I can check later

I wanted to keep the numbers behind a comparison without opening the app each time.
This command uses the same fitting and reporting code as the app. It saves a PDF
I can read, the complete calculation as JSON, and a small CSV score table.

## Try the example

After installing the dependencies from the README, run from the repository root:

```sh
python compare_distributions.py fit --sample --out /tmp/distrofit-comparison
python compare_distributions.py verify /tmp/distrofit-comparison
```

Choose a new output directory on each run. I deliberately preserve existing results
instead of overwriting them. Both commands finish without starting a server.

The example generates 240 synthetic measurements, fits Normal, Gamma and Exponential
curves to 180 of them, and compares the curves on the remaining 60. Gamma has the
lowest held-out loss for this example. Held-out means measurements set aside before
fitting. Loss is the average negative log probability density; lower is better when
comparing curves against the same measurements in the same units.

Another 60 synthetic observations have a deliberate upward shift of 12 units.
I score these against the original parameters, the numbers that define each fitted
curve. I never fit the curves again to make the changed observations look better.
The tail check counts values above the training sample's 95th percentile and
compares that count with the curve's prediction. The shifted example raises a flag.
It is an illustration of a mismatch, not evidence about any real population.

## Use my own measurements

```sh
python compare_distributions.py fit \
  --input measurements.csv --column value \
  --scenario later_measurements.csv --scenario-column value \
  --candidate Normal --candidate Gamma --candidate Exponential \
  --seed 42 --held-out-fraction 0.25 --bins 30 \
  --out /tmp/my-distrofit-comparison
python compare_distributions.py verify /tmp/my-distrofit-comparison
```

Omit `--scenario` and `--scenario-column` if I have no later sample. A scenario
column defaults to the input column's name. For a numeric CSV without a header,
use `--column 'Column 1'`; the first number is retained as an observation.
Blank cells, nonnumeric cells and nonfinite values in the selected column cause an
error. This command does not filter outliers or silently remove invalid values.

The same random split is inappropriate for a time series or related measurements.
I need independent observations for its held-out comparison to be meaningful.
Repeated selection against the same held-out sample can also overfit the choice.

## What I save

| File | What I use it for |
| --- | --- |
| `comparison.pdf` | Read the method, scores, diagnostic plots and every input value. |
| `comparison.json` | Recover every observation, exact split indices, fitted parameters, failed fits, versions and scenario checks. |
| `scores.csv` | Compare the candidate scores and tail counts in a table. |
| `manifest.json` | Check the other three files against their SHA-256 fingerprints. |

These files contain my input measurements. I keep private results outside the
repository. The bundle does not include the input filename or its filesystem path.

## How verification works

`verify` first checks the file fingerprints, which detect accidental changes.
It then regenerates the split membership from the recorded seed and sample size,
checks the training tail threshold, and recalculates training, held-out and scenario
scores from the saved parameters. It checks the ranking, diagnostic statistics and
CSV contents as well. It does not call a fitting routine. A regression test makes
fitting raise an error during verification to enforce that boundary.

A fingerprint is not a signature. Someone who changes both a file and its
fingerprint can replace a bundle. Recalculating scores helps detect inconsistent
statistics, but does not prove where data came from, how parameters were obtained,
or whether the PDF is an authentic third-party report. I use the pinned Python
dependencies in the repository to reproduce calculations. Numerical comparisons
allow a relative and absolute tolerance of `1e-10`. PDF creation dates can differ
between runs; the JSON calculation is deterministic for fixed inputs and versions.

Infinite loss remains the explicit JSON string `"inf"` and CSV value `inf` when
an observation lies outside a curve's support, the values that curve permits.
It is never clipped to an apparently acceptable score. If no candidate has a
finite held-out score, the command fails before creating an output directory.
Individual fitting failures remain visible when another candidate succeeds.

## External actuarial platforms

This workflow runs Python and SciPy. I have not run Moody's AXIS or Milliman
MG-ALFA, and this bundle is neither a native file for either platform nor evidence
of operating one. There is no invented vendor API, simulated license, or substitute
engine presented as one of those products.

I checked the public access routes on November 4, 2026.
[Moody's AXIS site](https://www.ggy.com/) says documentation and other services need
separately provisioned access; its product-documentation link redirects to a login
with a permission violation. [Milliman's Integrate overview](https://integrate.milliman.com/en)
describes its relationship to MG-ALFA, but the pages I inspected did not provide
an executable public sandbox. I found no local installation of either platform.
This establishes the access boundary I encountered, not a claim that evaluation
access is impossible for everyone.

To verify an actual integration later, I would need authorized runtime access,
version-specific interface documentation and a nonconfidential sample model I am
allowed to publish. I would then run that model in the actual product, check its
outputs against independently calculated expectations, and preserve a publishable
execution record and tests. This project does not claim that step is complete.
