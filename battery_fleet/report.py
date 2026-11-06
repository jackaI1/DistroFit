"""Portable Plotly report and auditable CSV/JSON tables."""

import html
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .data import download, nasa_cycles, chen_discharges, manifest
from .fleet import analyze_cycles


def fleet_figure(cycles, cells):
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Capacity remaining relative to first three cycles",
            "Charge recovered / charge put in",
            "Early current-step resistance proxy",
            "Cells needing inspection",
        ),
    )
    for cell, group in cycles.groupby("cell"):
        fig.add_trace(
            go.Scatter(x=group.cycle, y=group.retention_pct, name=cell, mode="lines"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=group.cycle, y=group.coulombic_efficiency, name=cell, showlegend=False
            ),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=group.cycle, y=group.resistance_proxy_ohm, name=cell, showlegend=False
            ),
            row=2,
            col=1,
        )
        flagged = group.loc[group.flagged_cycle]
        fig.add_trace(
            go.Scatter(
                x=flagged.cycle,
                y=flagged.retention_pct,
                text=flagged.flag_reasons,
                mode="markers",
                marker=dict(color="#b33b22", symbol="x", size=9),
                name=f"{cell} flags",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=group.cycle,
                y=100 * group.trend_capacity_ah / group.capacity_ah.head(3).median(),
                name=f"{cell} early trend",
                line=dict(dash="dash"),
                showlegend=False,
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Bar(
            x=cells.cell,
            y=cells.final_retention_pct,
            marker_color=["#b33b22" if f else "#227569" for f in cells.flagged_cell],
            text=["inspect" if f else "no cell flag" for f in cells.flagged_cell],
            name="Latest retention",
        ),
        row=2,
        col=2,
    )
    fig.update_xaxes(title_text="Discharge cycle", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (%)", row=1, col=1)
    fig.update_yaxes(title_text="Ratio", row=1, col=2)
    fig.update_yaxes(title_text="Resistance proxy (ohm)", row=2, col=1)
    fig.update_yaxes(title_text="Capacity (%)", row=2, col=2)
    fig.update_layout(
        height=800, template="plotly_white", title="DistroFit battery fleet review"
    )
    return fig


def model_figure(traces, sweep):
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Voltage: solid measured, dashed simulated",
            "Surface temperature and lumped prediction",
            "Cooling coefficient sweep at 1.5C",
            "Measured discharge duration",
        ),
    )
    colors = {0.1: "#3366aa", 0.5: "#227569", 1.0: "#a85c12", 1.5: "#983950"}
    for tr in traces:
        if tr["cell"] != "LGM50_cell02":
            continue
        label = f"{tr['rate']}C"
        for col, observed, predicted in (
            (1, "measured_voltage_v", "predicted_voltage_v"),
            (2, "measured_temperature_c", "predicted_temperature_c"),
        ):
            fig.add_trace(
                go.Scatter(
                    x=tr["time_s"],
                    y=tr[observed],
                    name=f"{label} measured",
                    legendgroup=label,
                    showlegend=col == 1,
                    line=dict(color=colors[tr["rate"]]),
                ),
                row=1,
                col=col,
            )
            fig.add_trace(
                go.Scatter(
                    x=tr["predicted_time_s"],
                    y=tr[predicted],
                    name=f"{label} DFN",
                    legendgroup=label,
                    showlegend=col == 1,
                    line=dict(dash="dash", color=colors[tr["rate"]]),
                ),
                row=1,
                col=col,
            )
    fig.add_trace(
        go.Scatter(
            x=[r["h_w_m2_k"] for r in sweep],
            y=[r["peak_temperature_c"] for r in sweep],
            mode="lines+markers",
            name="Cooling sweep",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=[f"{r['rate']}C" for r in traces if r["cell"] == "LGM50_cell02"],
            y=[r["time_s"][-1] / 3600 for r in traces if r["cell"] == "LGM50_cell02"],
            name="Hours",
        ),
        row=2,
        col=2,
    )
    fig.update_xaxes(title_text="Seconds", row=1, col=1)
    fig.update_xaxes(title_text="Seconds", row=1, col=2)
    fig.update_yaxes(title_text="Voltage (V)", row=1, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=2)
    fig.update_xaxes(title_text="Heat transfer coefficient (W/m²/K)", row=2, col=1)
    fig.update_yaxes(title_text="Peak temperature (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Hours", row=2, col=2)
    fig.update_layout(
        height=800,
        template="plotly_white",
        title="LG M50: 1C calibration, other rates held out",
    )
    return fig


def build_report(data_dir, output, thermal=True):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    download(data_dir)
    measurements, rejected = nasa_cycles(data_dir)
    cycles, cells = analyze_cycles(measurements)
    cycles.to_csv(output / "cycles.csv", index=False)
    cells.to_csv(output / "cells.csv", index=False)
    fleet = fleet_figure(cycles, cells)
    sections = [fleet.to_html(full_html=False, include_plotlyjs=True)]
    summary = dict(
        data_manifest=manifest(),
        fleet=dict(
            cells=len(cells),
            cycles=len(cycles),
            flagged_cycles=int(cycles.flagged_cycle.sum()),
            flagged_cells=int(cells.flagged_cell.sum()),
        ),
        rejected_phases=rejected,
    )
    if thermal:
        from .thermal import fit_parameters, evaluate, cooling_study

        curves = chen_discharges(data_dir)
        fit = fit_parameters(curves)
        metrics, traces = evaluate(curves, fit)
        sweep = cooling_study(next(c for c in curves if c["rate"] == 1.5), fit)
        pd.DataFrame(metrics).to_csv(output / "model_errors.csv", index=False)
        pd.DataFrame(sweep).to_csv(output / "cooling_sweep.csv", index=False)
        summary.update(calibration=fit, model_errors=metrics, cooling_sweep=sweep)
        sections += [
            model_figure(traces, sweep).to_html(
                full_html=False, include_plotlyjs=False
            ),
            "<h2>All cells and rates</h2>"
            + pd.DataFrame(metrics).round(4).to_html(index=False),
        ]
        trace_rows = []
        for trace in traces:
            for k, t in enumerate(trace["time_s"]):
                trace_rows.append(
                    dict(
                        cell=trace["cell"],
                        rate=trace["rate"],
                        time_s=t,
                        measured_voltage_v=trace["measured_voltage_v"][k],
                        measured_temperature_c=trace["measured_temperature_c"][k],
                    )
                )
            for k, t in enumerate(trace["predicted_time_s"]):
                trace_rows.append(
                    dict(
                        cell=trace["cell"],
                        rate=trace["rate"],
                        time_s=t,
                        predicted_voltage_v=trace["predicted_voltage_v"][k],
                        predicted_temperature_c=trace["predicted_temperature_c"][k],
                    )
                )
        pd.DataFrame(trace_rows).to_csv(output / "model_traces.csv", index=False)
    summary_text = json.dumps(summary, indent=2, allow_nan=False)
    (output / "results.json").write_text(summary_text + "\n")
    (output / "index.html").write_text(
        """<!doctype html><html lang="en"><meta charset="utf-8">
<title>DistroFit battery review</title><style>body{font:16px system-ui;max-width:1250px;margin:32px auto;padding:0 20px;color:#18332f}table{border-collapse:collapse;font-size:13px}td,th{padding:5px}p{max-width:850px}</style>
<h1>Battery measurements I can inspect</h1><p>NASA aging cells show capacity fade over repeated charges and discharges.
A red mark means a cycle differs from earlier measurements; it needs inspection. Red bars mark cells
with repeated recent flags, unusually fast fade, or less than 70% of their starting capacity.
Flags are screening results, not confirmed failures. Hover and zoom to inspect the curves.</p>
<p>Efficiency compares a discharge with its preceding charge. The resistance value is a short current-step
proxy, not an impedance measurement. Dashed capacity lines fit the first 60% of cycles only.</p>
<p>The separate LG M50 model fits cooling and negative-electrode diffusivity using 1C data from three cells.
Other rates are held out. Measured surface temperature is compared with a single average cell temperature.
Errors use the shared time interval; coverage reveals early voltage cutoff. The two datasets describe different cells.</p>"""
        + "".join(sections)
        + "<h2>Cell screening</h2>"
        + cells.round(4).to_html(index=False)
        + "<details><summary>Provenance and results</summary><pre>"
        + html.escape(summary_text)
        + "</pre></details></html>"
    )
    return summary
