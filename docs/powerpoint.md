# Editable comparison presentations

I use this export when I want to discuss the comparison without copying plots
and rebuilding a presentation by hand. The app's **Download editable PowerPoint**
button and `powerpoint_report.py` use the same current training and held-out
results. The export never refits them.

## A two-minute walkthrough

1. Install the normal Python dependencies from the README. Run
   `python powerpoint_report.py --sample --out /tmp/distrofit-review.pptx`,
   or open `examples/powerpoint/synthetic-review.pptx` in desktop PowerPoint.
2. Start the slide show. Click **Compare scores**, then **Candidate details**.
   Each candidate links back to the summary and onward to the next candidate.
   A score is mean negative log likelihood, a measure of how much probability
   density the model assigned to the held-out observations. Lower is better.
3. Exit the show. Select the score chart and choose **Chart Design > Edit Data**.
   The workbook opens inside Office. Change a number and the bar updates. Undo
   the edit before presenting the measured result. Values are snapshots, so
   editing the workbook does not change DistroFit's fitted model or detail tables.
4. Select the tail chart. Its separate series compare the model probability
   above the training 95th percentile with the share actually observed in the
   held-out data. The percentage axis runs from 0 to 100%. Candidate slides
   show the exploratory flag; presenter notes record counts and the interval.
5. Open **View > Slide Master**. The common master owns the footer and background.
   The named Summary, Chart and Detail layouts provide title placement. Change
   **Design > Variants > Colors** or the theme fonts to restyle inherited colors
   and fonts throughout the deck. A locally formatted object can override a theme.
6. Open **Slide Show > Custom Slide Show** (sometimes **Custom Shows** on Mac).
   **Quick discussion** uses summary, scores, tails and method. **Full review**
   also visits every candidate. The underlying slides stay together in one file.
7. Open the Notes pane or Presenter View to read the fitting method, split seed,
   filtering, versions and limitations while showing a simple slide to the audience.

These instructions target desktop Microsoft PowerPoint. PowerPoint for the web
and other viewers may not offer all custom-show and master editing controls.
Microsoft documents [custom shows](https://support.microsoft.com/en-us/powerpoint/create-and-present-a-custom-show)
and [slide masters](https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-slide-masters).

## My own measurements

```sh
python powerpoint_report.py measurements.csv --column weight --out review.pptx
```

The CLI compares Normal, Gamma and Exponential curves using seed 42 and a 25%
held-out split. The app export instead keeps its selected families and current
settings. Invalid numeric input gives an error before a deck is written.
The CLI removes nonfinite observations using the existing preparation function.

The synthetic example contains 240 generated Gamma observations, with 180 used
for fitting and 60 set aside. Gamma has the lowest held-out loss for this fixture.
This is an example result, not a claim that Gamma fits arbitrary measurements.

The file includes fitted parameters, aggregate scores, tail shares and method
notes. It deliberately omits raw observations, source filenames, manual edits
and the separate scenario. Aggregate results can still be private. I use the PDF
report when I need every observation and exact split membership.

## File design

I chose an offline exporter so I can edit chart data without a cloud account
or service. Slide images would lose that editing ability. The command-line
and app downloads share the same exporter and frozen analysis results.

`powerpoint_report.py` writes a ZIP package containing PresentationML, the XML
format used by PowerPoint, and SpreadsheetML, the embedded Excel data format.
It uses Python's standard library and adds no runtime dependency or account.
There are no macros, remote workbook links or external relationships.

- `ppt/slideMasters` and `ppt/slideLayouts` hold the shared design and three layouts.
  `ppt/theme` holds colors and Arial fonts. Text, parameter tables and charts
  remain native editable objects, rather than pictures of those objects.
- `ppt/charts` stores series caches and references to embedded workbooks in
  `ppt/embeddings`. Each series refers to actual worksheet cells, with the same
  ordering and precision as the cached values. Chart edits use those local files.
- `ppt/slides` contains named navigation links, referring to slides by package
  relationship ID. Candidate pages let a discussion move between overview and detail.
- `ppt/notesSlides` stores the full method and settings. `ppt/presentation.xml`
  defines the two custom shows by slide ID, avoiding duplicated short/full decks.

Infinite loss means a model assigned zero or invalid density to a held-out value.
It is excluded from the numeric chart and explicitly listed in the slide or notes.
All-infinite and failed-fit analyses have no finite winner. Negative finite losses
remain negative. Score bar axes always include zero, including all-negative
and all-zero comparisons. Score and tail charts use horizontal bars so candidate names fit
when all fourteen supported families are selected. More than fourteen candidates
or a title longer than eighty characters is rejected rather than silently clipped.
I also measure the summary title and reject text too wide for one line. Slide titles
inherit their geometry and type size so layout edits carry through to existing slides.

## Verification and limitations

```sh
python -m pytest -q
python tools/powerpoint_fixtures.py /tmp/powerpoint-fixtures
dotnet run --project tools/ValidatePowerPoint -p:UseSharedCompilation=false -- examples/powerpoint/synthetic-review.pptx /tmp/powerpoint-fixtures/*.pptx
```

The validator uses Microsoft's Open XML SDK 3.3.0 on .NET 8. It checks both the
presentation and each embedded workbook against the Office schemas. Tests also
read the package independently to check values, relationships, navigation and
custom-show membership. CI generates the real synthetic report and boundary
fixtures, validates them, and renders the synthetic deck with LibreOffice. The
rendered PDF and editable deck are available as workflow artifacts.

Schema validation and a second viewer do not prove that every desktop PowerPoint
version behaves identically. Microsoft PowerPoint was not installed on the build
Mac. Custom-show playback and Edit Data should be checked in the intended desktop
version before relying on them for a live presentation.
