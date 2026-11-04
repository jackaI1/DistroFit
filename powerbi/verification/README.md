# Recorded Power BI execution

I opened the committed report in a fresh Power BI Desktop installation on
Windows, refreshed its native model, and compared its returned values with the
independent public-data reference. This is output from Microsoft's engine, not
Python evaluating the DAX.

- Run: [Power BI native checks, 4 November 2026](https://github.com/jackaI1/DistroFit/actions/runs/41781560355).
- Engine: Microsoft Power BI Desktop Analysis Services **17.0.93.23**.
- Result: **79 queries, 2,796 value assertions, all passed**.
- [native-results.json](native-results.json) records every query and actual row,
  plus a SHA-256 fingerprint of the model it executed (Windows checkout, CRLF
  line endings).
- [displayed-family-values.csv](displayed-family-values.csv) extracts actual
  family values for comparison with [the supplied reference](../sample_export/reference_measures.csv).
- [desktop-open.json](desktop-open.json) records all four pages opened.
- [desktop-cleanup.json](desktop-cleanup.json) records the owned process, start
  time, loopback port and descendants. **Zero owned processes remained**.

Actual Desktop captures: [overview](../screenshots/overview.png),
[information criteria](../screenshots/information-criteria.png),
[goodness of fit](../screenshots/goodness-of-fit.png),
[dataset detail](../screenshots/dataset-detail.png).
These capture a fresh installation, including Power BI's first-use tips. In my
own Desktop session I can dismiss those tips and collapse the editing panes for
more room. The images are screen captures; they were not recreated in Python.

The Windows workflow repeats the execution on pull requests and on main. The
Python tests check that this historical evidence still fingerprints the committed
model; they do not claim to execute Power BI on macOS or Linux.
