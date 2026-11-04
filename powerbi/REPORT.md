# DistroFit Power BI report — layout spec

A four-page report over the star schema written by
[`export_powerbi.py`](../export_powerbi.py). The `.pbix` itself is built by hand
in Power BI Desktop (Windows) from this spec; DAX lives in
[`measures.dax`](measures.dax), the Power Query loader in
[`queries.pq`](queries.pq), and a ready-made export from 12 public datasets in
[`sample_export/`](sample_export/).

## 1. Producing data

```sh
# bundled public datasets (powerbi/sample_data, provenance in dataset_catalog.csv)
python export_powerbi.py --sample --out powerbi/sample_export --created-utc 2026-11-03T00:00:00Z

# your own numeric CSV: every numeric column becomes a dataset
python export_powerbi.py measurements.csv --column weight --column length --out my_export
```

Options: `--format csv|parquet|both`, `--seed`, `--held-out-fraction`, `--bins`,
`--outliers None|Z-Score|IQR`. The same fitting code as the app is used
(`analysis.fit_candidates`): parameters, AIC and BIC come from the training
split; rank, KS statistic and tail flag from the held-out split.

## 2. Data model

| Table | Grain | Key columns |
|---|---|---|
| `fact_fit` | run × dataset × distribution (168 rows in the sample) | `run_id`, `dataset_id`, `distribution_id`; `shape_1`, `shape_2`, `loc`, `scale`, `log_likelihood`, `aic`, `bic`, `heldout_nll`, `ks_statistic`, `ks_p_value`, `ks_pass`, `rank_heldout_nll`, `rank_aic`, `rank_bic`, `is_best_fit`, `delta_aic`, `akaike_weight`, `tail_flagged`, `fit_status` |
| `dim_dataset` | dataset | `dataset_id`, `dataset_name`, `source`, `variable`, observation counts, `skewness`, `excess_kurtosis`, `analysis_status` |
| `dim_distribution` | distribution family (14) | `distribution_id` (SciPy name), `distribution_name`, `support_type`, `tail_behaviour`, `parameter_count` |
| `dim_run` | export run | `run_id`, `created_utc`, `seed`, `held_out_fraction`, `ks_alpha`, library versions |

Relationships (many-to-one, single direction, from `fact_fit`):
`dataset_id → dim_dataset`, `distribution_id → dim_distribution`, `run_id → dim_run`.

Notes: failed fits are kept as rows (`fit_status = failed`, metrics blank).
`heldout_outside_support` means the held-out sample has points outside the
fitted support (held-out NLL is infinite and exported blank; the fit ranks last).
Dataset too small/constant → `dim_dataset.analysis_status = skipped`.

## 3. Loading in Power BI Desktop

1. Home → Get data → Blank query → Advanced editor; follow [`queries.pq`](queries.pq)
   (Parquet), **or** Get data → Text/CSV for each file in `sample_export/csv/`.
2. Name the four queries exactly `fact_fit`, `dim_dataset`, `dim_distribution`, `dim_run`.
3. Model view: confirm the three relationships above (auto-detected on matching names).
4. Create a `_Measures` table and paste the measures from `measures.dax`; apply
   the display folders and format strings noted in comments.
5. Sort `dim_distribution[distribution_name]` and set `dataset_name` as the display field.

## 4. Pages

### Page 1 — Overview
- **Cards** (top row): `Datasets Analysed`, `Top Distribution`, `KS Pass Rate`, `Fit Success Rate`.
- **Bar chart** — axis `dim_distribution[distribution_name]`, values `[Best Fit Share]`,
  sorted descending, data labels on (how often each family wins on held-out NLL).
- **Clustered bar** — axis `distribution_name`, values `[KS Pass Rate]` (is the winner actually adequate?).
- **Slicers**: `dim_run[run_id]` (single select, default first), `dim_distribution[support_type]`, `dim_dataset[source]`.

### Page 2 — Leaderboard (information criteria)
- **Matrix** — rows `dataset_name`, columns `distribution_name`, values `[AIC Delta]`;
  conditional formatting: white → red, minimum 0, diverging at 10 (delta > 10 = no support).
- **Column chart** — axis `distribution_name`, values `[AIC Delta]` and `[BIC Delta]` (average over the filtered datasets).
- **Scatter** — x `[AIC Delta]`, y `[Best Fit Share]`, details `distribution_name`, size `[Fits]`.
- Slicers: `dim_dataset[skewness]` (range), `dim_distribution[tail_behaviour]`.

### Page 3 — Goodness of fit
- **Table** — `dataset_name`, `distribution_name`, `ks_statistic`, `ks_p_value`,
  `ks_pass` (icon: ✓/✗), `tail_flagged`; filter to `is_best_fit = TRUE` by default.
- **100% stacked bar** — axis `dataset_name`, legend `ks_pass`, values `[Fits]`.
- **Card** — `Datasets With Any KS Pass`; **Card** — `Tail Flag Rate`.
- Slicer: `fit_status`.

### Page 4 — Dataset drill-through
Drill-through target filtered by `dim_dataset[dataset_name]` (add as a drill-through field).
- **Cards**: observation count, skewness, excess kurtosis (from `dim_dataset`).
- **Table** — `distribution_name`, `rank_heldout_nll`, `aic`, `delta_aic`, `akaike_weight`, `shape_1`, `shape_2`, `loc`, `scale`.
- **Bar** — `distribution_name` × `[Akaike Weight]`.
- Back button.

Theme: one accent colour for "best/pass", grey for the rest; keep family names
on the category axis rather than in legends (14 categories).

## 5. Validate before screenshotting

The DAX was written without access to Power BI (macOS), so confirm the measures
reproduce the independent pandas calculation
(`export_powerbi.reference_measures`, saved as
[`sample_export/reference_measures.csv`](sample_export/reference_measures.csv)).
With the sample export and no slicers:

| Distribution | Best Fit Count | Best Fit Share | AIC Delta (avg) | KS Pass Rate |
|---|---:|---:|---:|---:|
| Normal | 0 | 0.0% | 172.1 | 33.3% |
| Gamma | 0 | 0.0% | 117.1 | 33.3% |
| Weibull (Min) | 2 | 16.7% | 82.2 | 58.3% |
| Exponential | 2 | 16.7% | 147.1 | 33.3% |
| Log-Normal | 1 | 8.3% | 110.3 | 41.7% |
| Beta | 1 | 8.3% | 59.8 | 50.0% |
| Uniform | 2 | 16.7% | 177.6 | 25.0% |
| Student's t | 0 | 0.0% | 149.4 | 41.7% |
| Chi-Squared | 2 | 16.7% | 922.5 | 33.3% |
| Cauchy | 0 | 0.0% | 249.2 | 41.7% |
| Pareto | 1 | 8.3% | 142.4 | 41.7% |
| Logistic | 0 | 0.0% | 178.4 | 50.0% |
| Laplace | 0 | 0.0% | 202.8 | 25.0% |
| Maxwell | 1 | 8.3% | 150.8 | 41.7% |

Overall: 12 datasets, 168 fits, KS pass rate 39.3%. If a number differs, fix the
DAX (the repo's tests check the pandas side).

## 6. Reading the sample honestly

- The held-out-NLL winner often fails the KS test (e.g. Chi-Squared on
  earthquake magnitudes): the ranking picks the best of 14 candidates, not a
  good one. Page 3 exists to show this.
- Some SciPy fits (e.g. Weibull with a huge negative `loc`) are numerically
  unstable; extreme `loc`/`scale` values in the parameter table are real output.
- KS p-values have no multiple-comparison correction across candidates.

## 7. Files to commit after building

- `powerbi/DistroFit.pbix`
- `powerbi/screenshots/01-overview.png` … `04-drillthrough.png`
- Publish to the web service only if the data are public (they are); a
  "Publish to web" link may be added to the README.
