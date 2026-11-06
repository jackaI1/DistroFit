"""Small, pinned public inputs. Raw measurements are never silently replaced."""

from hashlib import sha256, md5
from importlib.resources import files
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from scipy.io import loadmat


def manifest():
    return json.loads(files("battery_fleet").joinpath("data_manifest.json").read_text())


def verify(path, entry):
    data = Path(path).read_bytes()
    if (
        len(data) != entry["bytes"]
        or sha256(data).hexdigest() != entry["sha256"]
        or md5(data).hexdigest() != entry["md5"]
    ):
        raise ValueError(f"Checksum/size mismatch: {entry['name']}")


def download(directory, entries=None):
    """Verify existing files too; bound transfers and atomically publish valid bytes."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for entry in manifest() if entries is None else entries:
        path = directory / entry["name"]
        if path.exists():
            verify(path, entry)
            continue
        temp = path.with_suffix(path.suffix + ".part")
        try:
            with urlopen(entry["url"], timeout=60) as source, temp.open("wb") as target:
                remaining = entry["bytes"] + 1
                while remaining:
                    chunk = source.read(min(65536, remaining))
                    if not chunk:
                        break
                    target.write(chunk)
                    remaining -= len(chunk)
            verify(temp, entry)
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    return directory


def clean_series(frame):
    """Canonical SI columns; reject unusable cycles rather than bridging large gaps."""
    cols = ["time_s", "current_a", "voltage_v", "temperature_c"]
    numeric = frame[cols].apply(pd.to_numeric, errors="coerce")
    valid = (
        np.isfinite(numeric).all(axis=1)
        & (numeric.time_s >= 0)
        & numeric.voltage_v.between(0, 6)
        & numeric.current_a.abs().le(20)
        & numeric.temperature_c.between(-40, 120)
    )
    dropped = int((~valid).sum())
    good = numeric.loc[valid].sort_values("time_s")
    duplicates = int(good.time_s.duplicated().sum())
    good = good.groupby("time_s", as_index=False).median()
    if len(good) < 3:
        raise ValueError("At least three finite, distinct times required")
    good.time_s -= good.time_s.iloc[0]
    dt = np.diff(good.time_s)
    if dt.max() > max(600, 10 * np.median(dt)):
        raise ValueError(
            "Large sampling gap; refusing to integrate missing measurements"
        )
    return good, {"dropped_rows": dropped, "duplicate_times": duplicates}


def nasa_cycles(directory):
    """Pair each discharge only with the immediately preceding unused charge."""
    from .fleet import cycle_metrics

    rows, rejected = [], []
    for entry in manifest():
        if entry["dataset"] != "NASA aging":
            continue
        path = Path(directory) / entry["name"]
        verify(path, entry)
        cell = path.stem
        cycles = loadmat(path, simplify_cells=True)[cell]["cycle"]
        charge, number = None, 0
        for record in cycles:
            mode = record["type"]
            if mode not in ("charge", "discharge"):
                continue
            if mode == "discharge":
                number += 1
            d = record["data"]
            raw = pd.DataFrame(
                dict(
                    time_s=d["Time"],
                    current_a=d["Current_measured"],
                    voltage_v=d["Voltage_measured"],
                    temperature_c=d["Temperature_measured"],
                )
            )
            try:
                series, quality = clean_series(raw)
            except ValueError as error:
                rejected.append(
                    dict(cell=cell, cycle=number, phase=mode, reason=str(error))
                )
                charge = None
                continue
            if mode == "charge":
                charge = (series, quality)
            else:
                metrics = cycle_metrics(series, charge[0] if charge else None)
                rows.append(
                    dict(
                        cell=cell,
                        cycle=number,
                        **metrics,
                        **quality,
                        charge_dropped_rows=(
                            charge[1]["dropped_rows"] if charge else None
                        ),
                        source_capacity_ah=float(d["Capacity"]),
                    )
                )
                charge = None
    return pd.DataFrame(rows), rejected


def chen_discharges(directory):
    """Keep full discharges after a complete charge; the initial partial step is excluded."""
    curves = []
    for entry in manifest():
        if entry["dataset"] != "Chen2020 validation":
            continue
        path = Path(directory) / entry["name"]
        verify(path, entry)
        frame = pd.read_csv(path, skiprows=13)
        for cycle, group in frame.loc[frame.Md.eq("D")].groupby("Cycle C"):
            if cycle == 1:
                continue
            series, quality = clean_series(
                group.rename(
                    columns={
                        "Step Time [s]": "time_s",
                        "Current [A]": "current_a",
                        "Voltage [V]": "voltage_v",
                        "Temperature Cell [degC]": "temperature_c",
                    }
                )
            )
            rate = min(
                (0.1, 0.5, 1.0, 1.5),
                key=lambda r: abs(r * 5 - series.current_a.median()),
            )
            curves.append(
                dict(
                    cell=path.stem,
                    rate=rate,
                    series=series,
                    ambient_k=float(group["Temperature Chamber [degC]"].median())
                    + 273.15,
                    initial_k=float(series.temperature_c.iloc[0]) + 273.15,
                    **quality,
                )
            )
    return sorted(curves, key=lambda c: (c["cell"], c["rate"]))
