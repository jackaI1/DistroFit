# Battery measurement review

I added this study because I wanted to try DistroFit's measurement checks on real battery experiments and learn where a physical model stops matching those measurements. I did not collect these readings or test a battery pack. Two public experiments answer different questions: NASA's aging cells show repeated-cycle fade; the LG M50 experiment checks voltage and heating at different loads.

## Try the saved run

Start DistroFit normally and select **Battery fleet**. The page reads `examples/battery/`, so it works without downloading data or installing the optional model. Select cells, hover over flags, show all cycles, and download the selected table. The lower charts compare measured and simulated discharge, followed by the numerical errors for every cell and rate.

To reproduce the calculation on Python 3.12:

```sh
python -m pip install -r requirements-battery.txt -r requirements-dev.txt
python -m battery_fleet --out .runtime/my-battery-report
python tools/check_battery_study.py .runtime/my-battery-report/results.json
BATTERY_TEST_DATA=.runtime/battery-data python -m pytest tests/test_battery_fleet.py tests/test_battery_thermal.py tests/test_battery_app.py -q
```

Open `.runtime/my-battery-report/index.html` directly. Its charts contain Plotly locally and work offline. Each output directory must be new. `--fleet-only` skips model calibration; `--download-only` verifies or fetches the raw files. `--data PATH` chooses another cache. I can also install the small Python package with `pip install '.[thermal]'` and run `distrofit-battery --out PATH`; the requirements file supplies the repository's tested versions.

The report saves cycle features, cell summaries, model errors, measured and predicted traces, cooling results and `results.json`. The JSON contains every input's provenance, hashes and byte count, fitted values, evaluation split and time coverage. The saved example contains derived tables, not raw downloads. To update the page, I regenerate the report and copy its six CSV/JSON tables into `examples/battery/`.

## Where the readings came from

`battery_fleet/data_manifest.json` pins six files, under 50 MB in total. Each download has a size limit, a temporary file, SHA-256 and MD5 checks, and an atomic rename after verification. Existing cached files are checked again. A mismatch fails explicitly; it never falls back to invented measurements. The SHA-256 values pin the exact bytes inspected for this study; they are not publisher signatures.

- **Aging:** B. Saha and K. Goebel, *Battery Data Set*, NASA Ames Prognostics Data Repository (2007). The [official repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) describes the experiment. I use B0005, B0006 and B0007, three nominal 2 Ah cylindrical cells cycled at 2 A, with different lower voltage limits. The small individual MAT files come from the [public mirror at immutable commit 5301bd7](https://github.com/changyeon99/Battery-Data-Set/tree/5301bd7e469dc8a1320b55719629571f2c02b6fc), rather than downloading a larger archive. This is an independently maintained copy of NASA data; I pin and expose that dependency instead of presenting the mirror as NASA's download service.
- **Discharge and temperature:** C.-H. Chen, F. Brosa Planella, K. O'Regan, D. Gastol, W. D. Widanage and E. Kendrick, [validation data, version 1](https://doi.org/10.5281/zenodo.4032561), accompanying [Chen et al., 2020](https://doi.org/10.1149/1945-7111/ab9050). The three LG M50 cells are 21700 cylinders with nominal 5 Ah capacity. This record is CC BY 4.0. I checked each MD5 against the record's published value and additionally pinned SHA-256. The files include cell-surface and chamber temperatures at 0.1C, 0.5C, 1C and 1.5C. A C-rate expresses current relative to nominal capacity: 1C here means 5 A.

## Cycle calculations and flags

I coerce numeric columns, remove non-finite or physically impossible rows, sort times and combine duplicate timestamps by their median. I count removals and duplicates. Fewer than three distinct points or a gap longer than both ten usual sampling intervals and ten minutes rejects that phase; I do not fill long missing intervals. NASA current is positive on charge and negative on discharge. I integrate the appropriate sign using the trapezoid rule, in ampere-seconds divided by 3600, to get amp-hours (Ah), a measure of charge.

A discharge pairs with the latest unused charge, across intervening impedance measurements. A rejected phase clears the pairing. Efficiency is discharge Ah / charge Ah. I leave it blank when the charge appears incomplete: its first minute never falls to 3.6 V, it does not finish at 4.15 V, or recorded charge is less than half the discharge. These are screening criteria for these particular cells, not proof of a complete cycle. Ten pairs in this run are excluded. Some retained ratios exceed one, so I keep the observed values for inspection rather than clipping them. Initial state, rest periods and logging boundaries make these estimates different from a precision efficiency experiment.

The resistance proxy is the median voltage change divided by current change for falling current steps exceeding 0.5 A in the first minute. A missing step gives a blank value. This includes polarization and depends on sampling interval; it is not electrochemical impedance spectroscopy (a frequency-based resistance measurement). The integrated capacities differ from NASA's separate capacity fields by at most 0.0281 Ah, under 1.5% of nominal capacity. The report preserves both values rather than silently substituting NASA's number.

For each cell and feature, I fit a robust local line to up to 20 **previous** cycles, requiring eight. Theil-Sen regression takes the median of pairwise slopes, so one extreme point has limited influence. A flag means distance from that predicted baseline exceeds five robust scales. Each scale is 1.4826 times median absolute deviation of previous residuals, with floors of 0.01 Ah, 0.005 efficiency ratio, 0.005 ohm and 0.5 °C. The first eight cycles have no baseline flags. Missing values do not become zeroes.

I fit a separate capacity trend on the first 60% of each cell's cycles and report absolute error on later cycles. That dashed trend is an early prediction, while cycle flags use their rolling past. Cell flags mean at least 20% flagged cycles in the latest 20, retention below 70%, or a normalized fade slope more than five robust scales from peers (scale floor 0.0005 per cycle). I show the reason-bearing cycle table. Different cutoff voltages and only three cells limit cross-cell conclusions; these flags prioritize inspection, not replacement.

## Physical model and evaluation

I use PyBaMM 25.10.2's Doyle-Fuller-Newman (DFN) lithium-ion model. It resolves lithium transport and electrochemical reactions across both electrodes and the electrolyte. The lumped thermal model balances generated heat against cooling with one average cell temperature. Chen2020 parameters describe an LG M50 cylinder; cooling area is 0.00531 m² and volume is 2.42e-5 m³. The model uses the measured initial cell temperature and median chamber temperature for each discharge, full initial charge, nominal constant current and a 2.5 V cutoff. The initial partial discharge in each file is excluded.

I fit two shared parameters using **only the three 1C curves**: total surface heat-transfer coefficient and a multiplier on negative-particle diffusivity (how quickly lithium spreads within particles). Bounded least squares starts at 10 W/m²/K and a multiplier of 1, with bounds [0.5, 50] and [0.2, 10]. Residuals weight voltage by 0.05 V and temperature by 2 K. Calibration uses 61 equally spaced points per curve, penalizes early termination and rejects non-convergence. I use 12 spatial points per region and particle; a test compares against 20 points.

The remaining nine curves, at 0.1C, 0.5C and 1.5C, never enter my optimizer. I evaluate 101 equally spaced times per curve over the shared measured/simulated interval, reporting root mean square error (RMSE, a typical size of prediction error), duration and coverage. I never extrapolate a prediction past voltage cutoff for reported errors. The fitting penalty uses a fixed residual length and holds the endpoint only within the optimizer when a trial terminates early.

These are held-out **rates for my two-parameter fit**, not unseen cells. More importantly, the published Chen2020 starting parameters were themselves developed using this experiment. The rate split does not turn this into independent validation of that published parameter set. A single lumped temperature is compared with a surface sensor, and the starting parameters omit measured reversible-heat detail. Stronger validation needs a separately collected experiment and a temperature-dependent parameter set. The cooling sweep at 1.5C varies the coefficient through 2, 5, 10, 20 and 40 W/m²/K without fitting again; it is a model prediction, not measured cooling performance.

## Results and checks

The exact run is in [results.json](../examples/battery/results.json), with [all model errors](../examples/battery/model_errors.csv). Battery CI downloads the data, checks hashes, runs fault tests, reruns calibration and the complete study, checks broad numerical acceptance limits, and uploads the offline dashboard. It runs on pull requests and main alongside the existing suite.

Tests inject capacity loss, resistance increases, efficiency loss and temperature spikes into an otherwise clean aging trajectory. They check clean controls, persistent abnormal fade, no future leakage in flags, timestamp cleaning, checksum rejection, incomplete charges and real public-file parsing. Actual DFN solutions check charge conservation against the model's capacity state and energy conservation against its energy state, plus temperature units, mesh refinement and the cooling response. The UI test exercises cell selection, flagged-only filtering and clearing selection.

The saved run contains 504 discharges, 494 usable efficiency pairs, 29 flagged
cycles and one flagged cell (B0006, with 59.1% retention). Fitted cooling is
9.934 W/m²/K and the diffusivity multiplier is 0.6185. The nine held-out-rate
curves have voltage RMSE 0.0601–0.0697 V and temperature RMSE 0.402–2.954 K,
with 97.15–100% time coverage. The 1.5C cooling sweep predicts peak temperature
falling from 79.98 °C at 2 W/m²/K to 36.54 °C at 40 W/m²/K.
