# Comparing DistroFit samples in Power BI

I built this report because I wanted to see whether the same curves kept winning
across different samples, and whether a winning curve actually fit well. The
report opens as a complete local Power BI project. Its bundled snapshot contains
12 public datasets, 14 curve families and 168 fitted results.

## Open and use the report

1. Install the free [Power BI Desktop for Windows](https://www.microsoft.com/download/details.aspx?id=58494).
   I use the October 2026 release in CI. No Power BI Service account is required.
2. Clone or download the **whole repository**. Keep the report and model folders
   beside [DistroFit.pbip](DistroFit.pbip), then open that file in Desktop.
3. Choose **Home → Refresh**. Project files contain the data definition, while
   Desktop's local data cache is deliberately excluded from Git.
4. Use the page tabs and the dataset, source, curve support and export-run filters.
   Clear a filter with its eraser icon to return to the full sample.

| Page | What I use it for |
|---|---|
| Overview | See dataset count, most frequent winner, fit success and winners by curve |
| Information criteria | Compare AIC and BIC, scores that balance fit against complexity; lower differences are better |
| Goodness of fit | See KS pass rates, a check of how close the test measurements are to each fitted curve, and tail warnings |
| Dataset detail | Select one dataset, inspect its curve ranks and parameters, and compare Akaike weights, relative support based on AIC |

The overview displays **12 datasets**, **Weibull (Min)** as the most frequent winner
(tied families use the alphabetically last name), **39.3% KS pass rate** and
**100.0% fit success**. The information-criteria total cards show 0.0 because at
that level they compare the best candidate with itself; the per-family table and
chart are the useful comparisons. The model always retains failed fits when an
export contains them.

## Use my own measurements

From the repository root with the Python dependencies installed:

```sh
python export_powerbi.py measurements.csv --column weight --column length --out my_export
python powerbi/build_project.py --export my_export
```

I close Desktop first, delete `DistroFit.SemanticModel/.pbi` if I previously opened
the project, reopen `DistroFit.pbip`, and refresh. Deleting that generated cache
avoids loading an older snapshot over the new model. The builder replaces the
model and report definition. I make a copy before customizing the pages.

The builder also accepts `--out /path/to/report-copy` to leave the bundled example
alone. It reads the four exported CSV files, preserves their declared types and
blanks, and embeds their rows in native DAX calculated-table partitions. DAX is
Power BI's calculation language. This small snapshot design avoids paths tied to
my computer, cloud credentials and data gateways. Refresh calculates that snapshot;
it does **not** reread a changed CSV. I export and rebuild to update it. This is a
comparison report, not a continuously updated monitoring service.

To recreate the original snapshot:

```sh
python powerbi/build_project.py
```

I never commit a rebuilt project containing private measurements. The bundled
public-data provenance is in [dataset_catalog.csv](sample_data/dataset_catalog.csv).
The original [Power Query loader](queries.pq) remains available for a separate
CSV/Parquet import workflow; the committed project does not depend on it.

## What is included

- [DistroFit.pbip](DistroFit.pbip): the entry point to the report.
- [DistroFit.Report/](DistroFit.Report/): four PBIR pages with cards, tables, bar
  charts and slicers, which are interactive filters.
- [DistroFit.SemanticModel/model.bim](DistroFit.SemanticModel/model.bim): the actual
  TMSL model, Microsoft's JSON model format, including data, relationships and
  15 DAX measures. [measures.dax](measures.dax) is their editable source.
- [build_project.py](build_project.py): deterministic builder for the project.
- [checks.json](checks.json): native DAX queries and independent expected values.
- [NativeCheck/](NativeCheck/): the Windows runner that processes the committed
  model and executes the queries with Microsoft's Analysis Services client.

The model has one result table, `fact_fit`, at run × dataset × curve grain, and
three lookup tables: `dim_dataset`, `dim_distribution` and `dim_run`. Each has a
one-to-many, single-direction relationship to the result table on its matching
ID. This makes filters reach the fitted results while keeping family-share
denominators independent of the chart's family axis. I keep one export run per
snapshot; the exporter creates one run at a time.

## Native calculation verification

The [Power BI native checks workflow](../.github/workflows/powerbi.yml) installs a
hash-pinned Microsoft Power BI Desktop on a disposable Windows runner. It starts
Desktop's real `msmdsrv.exe` calculation engine on a loopback port, deploys the
**exact committed model.bim**, processes its tables and executes DAX through
Microsoft's ADOMD client. It does not translate DAX into Python or substitute
Python results for engine output.

[build_checks.py](build_checks.py) prepares independent expected results from the
CSV tables. The checks include all 15 measures, each dataset and family, source,
support and run filters, a combined dataset/family selection, an empty run, and
the data queries for every committed visual. The supplied
[reference_measures.csv](sample_export/reference_measures.csv) is compared
separately, covering all 14 families. Values are checked before display rounding,
with relative tolerance `1e-8`; the report formats rates as percentages.

On Windows, with .NET 8 and Desktop installed, I can repeat it:

```powershell
dotnet run --project powerbi/NativeCheck -- powerbi "C:\Program Files\Microsoft Power BI Desktop\bin\msmdsrv.exe" native-evidence
```

The workflow uploads `native-results.json` with actual returned values, query text,
engine version and model SHA-256, plus `cleanup.json` with the owned process and
port. The runner requests shutdown, waits for that exact process and removes its
temporary directory in a finally block, including failure paths. The report's
queries verify the values bound to visuals; the Python schema tests alone do not
establish that the DAX works.

## Reading the results

A held-out winner has the lowest negative log-likelihood on measurements set
aside before fitting. It can still fail the KS check: best among the candidates
does not mean a good description of the process. AIC and BIC use the training
measurements, while KS and held-out rankings use the test measurements.

Some fitted parameters are extreme, especially for Weibull; the detail page shows
the exported values rather than hiding numerical instability. KS p-values have
no multiple-comparison correction across the candidates. Tail warnings are
exploratory checks, not proof of a process problem.
