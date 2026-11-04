# Power BI native report repair

Goal: replace the report recipe with an openable project and execute its DAX in
Microsoft's Power BI engine against the committed public sample.

Design: use PBIP with a TMSL model.bim and PBIR report pages. Snapshot the exported
tables as native calculated tables so the sample opens without machine-specific
paths, credentials or a cloud account. Keep measures.dax as the source for measures.
A builder accepts another export folder to replace the snapshot. Windows CI installs
Power BI Desktop, starts an owned local engine, loads the exact committed model,
processes it and compares queries behind the visuals with reference_measures.csv.

Alternatives: a binary PBIX is harder to review; a cloud-only report needs an account.
The text project is the selected implementation choice for this repair.

1. Add failing tests for an actual model, three relationships, four populated pages,
   valid visual bindings, and deterministic regeneration from the public sample.
2. Build the project and run those tests. Preserve all existing app/export behavior.
3. Add native Windows evaluation for all measures, per-family reference values,
   dataset/source/run filters, empty selections and the four pages' visual queries.
   Record engine version, actual results, assertions and owned process cleanup.
4. Replace recipe documentation with exact opening, refresh, replacement and
   verification instructions; keep the README in first person and plain language.
5. Run the complete Python suite and native CI; commit execution evidence, review,
   rebase if needed, merge through a PR, confirm main CI and run independent Sol.

Review focus: blank metrics stay blank; booleans remain boolean; numeric strings use
invariant culture; slicer filters propagate through relationships; removing family
filters in denominators does not remove dataset filters. A snapshot must be rebuilt
when exported data changes. No private data or local cache may be committed.
