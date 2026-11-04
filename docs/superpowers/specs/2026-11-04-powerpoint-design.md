# Editable PowerPoint analysis report

I want to discuss a fitted curve without rebuilding charts or copying screenshots.
The report exports the existing frozen analysis as a native PowerPoint file.

I chose an offline PresentationML exporter, the XML format PowerPoint reads,
over a cloud add-in (requires a service and sign-in) or slide images (cannot edit
chart data). Python's standard library writes the package, so the app adds no
runtime dependency. This is repository feature code rather than a one-off deck
created with a private authoring runtime.

The report has a summary, native score and tail charts with embedded Excel
workbooks, one candidate detail slide each, and method notes. A shared theme,
master and title/chart/detail layouts keep it reusable. Internal hyperlinks
connect the summary and candidate slides; two custom shows offer a short or
complete discussion. Speaker notes preserve settings and caveats. No macros,
external data links, services or confidential fixtures are included.

Scores use held-out observations only. Infinite scores are excluded from the
numeric score chart with an explicit visible warning. Empty successful fits and
all-infinite results have no finite winner. Negative scores stay negative.
Export contains aggregate values and parameters, not raw observations. CSV CLI,
Streamlit download and a committed synthetic sample share one implementation.

Tests inspect numerical chart caches against embedded workbook cells, resolve
all package relationships, check navigation and notes, exercise CLI and app,
and reject invalid inputs. Microsoft's Open XML SDK validates generated files
in CI. Render the synthetic deck locally with the available presentation viewer;
do not imply PowerPoint desktop was tested when it was not installed.
