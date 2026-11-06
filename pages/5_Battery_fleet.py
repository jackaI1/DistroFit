"""Inspect the reproducible public-data battery study inside DistroFit."""

from pathlib import Path
import json
import pandas as pd
import streamlit as st
from battery_fleet.report import fleet_figure, model_figure

st.set_page_config(page_title="DistroFit battery fleet", layout="wide")
st.title("Battery fleet")
st.write(
    "I compare repeated battery measurements to see which cells lose capacity and which cycles need a closer look."
)
st.caption(
    "Public laboratory measurements. Flags need investigation; they do not confirm a damaged cell."
)
source = Path(__file__).resolve().parents[1] / "examples" / "battery"
cycles = pd.read_csv(source / "cycles.csv").fillna({"flag_reasons": ""})
cells = pd.read_csv(source / "cells.csv")
results = json.loads((source / "results.json").read_text())
selected = st.multiselect("Cells", cells.cell.tolist(), default=cells.cell.tolist())
if not selected:
    st.info("Choose at least one cell.")
    st.stop()
filtered = cycles.loc[cycles.cell.isin(selected)]
selected_cells = cells.loc[cells.cell.isin(selected)]
a, b, c = st.columns(3)
a.metric("Discharge cycles", len(filtered))
b.metric("Flagged cycles", int(filtered.flagged_cycle.sum()))
c.metric("Cells to inspect", int(selected_cells.flagged_cell.sum()))
st.plotly_chart(fleet_figure(filtered, selected_cells), width="stretch")
st.write(
    "Capacity is the charge a cell supplies. Efficiency is discharge charge divided by the preceding charge. "
    "I leave efficiency blank for incomplete charge pairs. The resistance estimate comes from the first current step, "
    "so it includes short-term polarization and is not a laboratory impedance measurement."
)
st.dataframe(selected_cells, width="stretch", hide_index=True)
only_flags = st.checkbox("Show flagged cycles only", value=True)
st.dataframe(
    filtered.loc[filtered.flagged_cycle] if only_flags else filtered,
    width="stretch",
    hide_index=True,
)
st.download_button(
    "Download selected cycles",
    filtered.to_csv(index=False),
    "battery-cycles.csv",
    "text/csv",
)
st.subheader("Discharge and heating model")
st.write(
    "I fitted a physics model to the 1C discharges of three LG M50 cells. A rate of 1C would empty a nominal "
    "5 amp-hour cell in one hour. I then compared the same model with measured voltage and surface temperature "
    "at three rates left out of that fit. These are separate cells from the aging study above."
)
raw = pd.read_csv(source / "model_traces.csv")
traces = []
for (cell, rate), group in raw.groupby(["cell", "rate"]):
    measured = group.dropna(subset=["measured_voltage_v"])
    predicted = group.dropna(subset=["predicted_voltage_v"])
    traces.append(
        dict(
            cell=cell,
            rate=rate,
            time_s=measured.time_s.to_numpy(),
            measured_voltage_v=measured.measured_voltage_v,
            measured_temperature_c=measured.measured_temperature_c,
            predicted_time_s=predicted.time_s.to_numpy(),
            predicted_voltage_v=predicted.predicted_voltage_v,
            predicted_temperature_c=predicted.predicted_temperature_c,
        )
    )
st.plotly_chart(model_figure(traces, results["cooling_sweep"]), width="stretch")
st.dataframe(pd.DataFrame(results["model_errors"]), width="stretch", hide_index=True)
st.caption(
    "RMSE is typical prediction error; lower is better. Coverage is the fraction of the measured duration "
    "before the simulation stops. The lumped temperature is an average, compared here with a surface sensor. "
    "The published starting parameters already used this experiment, so these are held-out rates for my fit, "
    "not an independent validation of those published parameters."
)
st.code(
    "python -m pip install -r requirements-battery.txt\npython -m battery_fleet --out .runtime/my-battery-report",
    language="sh",
)
st.caption(
    "The command downloads checksum-verified public inputs and regenerates the full report in a new folder. "
    "The page displays the committed run; see docs/battery.md for provenance and limits."
)
