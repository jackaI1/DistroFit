// Power Query (M) loader for the Parquet export.
// Power BI Desktop: Home > Get data > Blank query > Advanced editor.
// Create ONE query named ExportFolder (type Text) holding the folder path, e.g.
//   "C:\Users\you\DistroFit\powerbi\sample_export\parquet\"
// (keep the trailing backslash), then create one query per table below,
// pasting the matching three lines. Names must match the DAX in measures.dax.

// --- fact_fit
let Source = Parquet.Document(File.Contents(ExportFolder & "fact_fit.parquet")) in Source

// --- dim_dataset
let Source = Parquet.Document(File.Contents(ExportFolder & "dim_dataset.parquet")) in Source

// --- dim_distribution
let Source = Parquet.Document(File.Contents(ExportFolder & "dim_distribution.parquet")) in Source

// --- dim_run
let Source = Parquet.Document(File.Contents(ExportFolder & "dim_run.parquet")) in Source
