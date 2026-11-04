"""Rebuild the sample inputs from the public R `datasets` collection.

Run from the repository root (needs network access; uses only pandas):

    python powerbi/sample_data/fetch_public_datasets.py

Writes two files next to this script:
  dataset_catalog.csv   one row per analysed variable, with provenance
  public_datasets.csv   long format (dataset_id, value), one row per observation

The values come from the Rdatasets mirror of the base-R `datasets` package
(https://vincentarelbundock.github.io/Rdatasets/). They are published
measurements (eruption times, earthquake magnitudes, river lengths ...).
"""
from pathlib import Path

import pandas as pd

MIRROR = "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/{}.csv"
OUT = Path(__file__).resolve().parent

# dataset_id, R dataset, column, display name, description
SPECS = [
    ("faithful_eruptions", "faithful", "eruptions", "Old Faithful eruption duration (min)",
     "Eruption durations at Old Faithful geyser, Yellowstone; bimodal."),
    ("faithful_waiting", "faithful", "waiting", "Old Faithful waiting time (min)",
     "Time between Old Faithful eruptions; bimodal."),
    ("quakes_magnitude", "quakes", "mag", "Fiji earthquake magnitude",
     "Richter magnitude of 1,000 seismic events near Fiji."),
    ("quakes_depth", "quakes", "depth", "Fiji earthquake depth (km)",
     "Focal depth of the same 1,000 Fiji events; clustered."),
    ("airquality_wind", "airquality", "Wind", "New York wind speed (mph)",
     "Daily mean wind speed, New York, May-Sep 1973."),
    ("airquality_temp", "airquality", "Temp", "New York max temperature (F)",
     "Daily maximum temperature, New York, May-Sep 1973."),
    ("airquality_ozone", "airquality", "Ozone", "New York ozone (ppb)",
     "Mean ozone concentration; missing days dropped."),
    ("precip_cities", "precip", "dat", "Annual precipitation, US cities (in)",
     "Average annual precipitation in 70 US cities."),
    ("rivers_length", "rivers", "dat", "Length of major North American rivers (mi)",
     "Lengths of 141 rivers; right-skewed."),
    ("islands_area", "islands", "dat", "Area of major landmasses (1000 sq mi)",
     "Areas of 48 landmasses; extremely heavy-tailed."),
    ("chickweight_weight", "ChickWeight", "weight", "Chick body weight (g)",
     "All weigh-ins of the ChickWeight diet experiment."),
    ("mtcars_mpg", "mtcars", "mpg", "Car fuel economy (mpg)",
     "Motor Trend 1974 road tests of 32 cars."),
]


def main():
    cache, catalog, long_rows = {}, [], []
    for dataset_id, source, column, name, description in SPECS:
        if source not in cache:
            cache[source] = pd.read_csv(MIRROR.format(source))
        values = pd.to_numeric(cache[source][column], errors="coerce").dropna()
        catalog.append({"dataset_id": dataset_id, "dataset_name": name,
                        "source": f"R datasets::{source} (Rdatasets mirror)",
                        "variable": column, "description": description,
                        "n_values": len(values)})
        long_rows.append(pd.DataFrame({"dataset_id": dataset_id, "value": values.to_numpy()}))
    pd.DataFrame(catalog).to_csv(OUT / "dataset_catalog.csv", index=False)
    pd.concat(long_rows).to_csv(OUT / "public_datasets.csv", index=False)


if __name__ == "__main__":
    main()
