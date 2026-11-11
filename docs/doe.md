# Factorial experiments for changeover studies

`doe.py` plans two-level factorial experiments and fits their effects. It is written for
process questions such as "does a second crew member, a faster tooling setup or a
pre-staged kit cut changeover time, and do they help each other?"

## The method

- **Two levels per factor.** Each factor has a low and a high value in real units
  (for example crew size 2 and 4). Coded values are -1 for low, +1 for high and 0 for a
  centre point, a run halfway between them.
- **Full factorial.** Every combination of levels: 2^k runs for k factors.
- **Fractional factorial, 2^(k-p).** Fewer runs. An added factor is set to a product of
  base columns, so `fixture=ABC` means the fixture column is the product of the first
  three base columns. Base factors are labelled A, B, C in the order they are listed.
  The defining relation for `fixture=ABC` is I = ABCD, so AB and CD cannot be told apart.
- **Resolution.** The length of the shortest word in the defining relation. Resolution
  IV (the 4-factor example below) means main effects are not mixed with two-factor
  interactions, though two-factor interactions are mixed with each other.
- **Replicates and centre points.** Replicates repeat each run and give the error
  estimate its degrees of freedom. Centre points give a curvature check: if their mean
  differs from the factorial mean, the response is not a straight line between the levels.
- **Random run order.** The run sheet is shuffled with a seeded generator, so the order
  is random but repeatable.

## Fitting

For each main effect and interaction, the model is an ordinary least-squares fit (statsmodels
OLS) on the coded columns:

- **Effect** = 2 x coefficient, the change in mean response from low to high.
- **Standard error, confidence interval and t** come from the fit.
- **Sum of squares** is N x coefficient², exact because coded columns are orthogonal in a
  balanced design. It is checked in `tests/test_doe.py` against the drop in residual sum
  of squares when a term is removed.
- **ANOVA p-value** is the F test of that sum of squares against the residual mean square.
- **Aliases.** Columns that are identical (up to sign) are fitted once. The table shows
  the other names in `aliased_with`, so AB and CD appear as one estimate.
- **Lenth's pseudo standard error** is a noise estimate from the effects themselves. With
  few effects, as in the example, its margin of error is very wide, so the ANOVA p-values
  are the main test and the Lenth numbers are only a sanity check.

Charts:

- `half_normal.png`: |effect| against half-normal quantiles. Effects that are only noise
  fall near the dashed noise line through zero; large effects leave it.
- `pareto.png`: |effect| from largest to smallest with the cumulative share of the total.

## Commands

```sh
python doe.py plan --factor crew_size=2:4 --factor tooling_minutes=5:15 \
  --factor kit=0:1 --factor fixture=0:1 --fraction fixture=ABC \
  --centre 4 --replicates 2 --out .runtime/changeover-plan
```

Open `.runtime/changeover-plan/run_sheet.csv`, run the trials in the listed order and type
the measured minutes into the `response` column. Then:

```sh
python doe.py analyse --plan .runtime/changeover-plan --out .runtime/changeover-report
```

`plan` refuses a folder that already has files, and so does `analyse`, so earlier results
are never overwritten.

## The saved example

`python doe.py --sample --out .runtime/doe-sample` simulates a changeover study with known
coded effects (crew size -4, tooling time +6, kit -5, fixture +2 and a crew-by-tooling
interaction of +1.5, so the changes from low to high are twice those) and noise with a
standard deviation of 0.8 minutes. It uses a 2^(4-1) fractional design with 2 replicates
and 4 centre points, 20 runs in total.

The fit on the seeded sample gives these effects in minutes:

| term | effect | 95% interval | p-value |
|---|---|---|---|
| tooling_minutes | +12.64 | 12.05 to 13.24 | < 0.001 |
| kit | -10.24 | -10.84 to -9.64 | < 0.001 |
| crew_size | -7.83 | -8.43 to -7.23 | < 0.001 |
| fixture | +3.02 | 2.43 to 3.62 | < 0.001 |
| crew_size x tooling_minutes (aliased with kit x fixture) | +2.85 | 2.25 to 3.44 | < 0.001 |
| crew_size x kit (aliased with tooling x fixture) | +0.16 | -0.43 to 0.76 | 0.56 |
| curvature | +0.13 | -0.54 to 0.79 | 0.65 |

Residual standard deviation is 0.54 minutes and R² is 0.998. Two things to note:

- The fixture effect was built in at +4 minutes and the fit gives +3.0. The 95% interval
  does not include 4, so this is a noise miss, not a model failure. It shows why real
  studies need more replicates before a small effect is trusted.
- The crew-by-tooling interaction is aliased with kit-by-fixture, so the table can't say
  which of the two produced the +2.85 minutes. Only a design with higher resolution, or
  a follow-up run, would separate them.

## Tests

`tests/test_doe.py` checks the designs (corners, run order, replicates, resolution and
aliases), recovers known effects exactly from noise-free data, recovers them within
tolerance from noisy replicated data, checks the sums of squares against the residual
sum of squares, detects aliases and curvature, and checks the saved files and the CLI.
