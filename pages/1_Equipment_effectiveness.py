"""Interactive view over the same SPC functions used by the CLI and tests."""
import json

import pandas as pd
import streamlit as st

from equipment import build_equipment_report, load_example
from spc import pareto_chart

st.set_page_config(page_title="DistroFit: Equipment effectiveness", layout="wide")
st.title("Equipment effectiveness")
st.write("Find where planned production time went: stopped equipment, slow running, or rejected parts.")
st.caption("For individual unusual stop durations and cycle times, open Production anomalies in the sidebar.")
st.caption("Use one machine and one product with a single ideal cycle time per report. The initial values are a worked example, not factory measurements.")
st.session_state.pop("equipment_report", None)
sample_shift, sample_stops, sample_tasks = load_example()

st.subheader("1. Production period")
st.write("Exclude breaks when production was not scheduled. Keep changeovers in the stop log below.")
left, right = st.columns(2)
with left:
    shift_minutes = st.number_input("Shift length (minutes)", min_value=0., value=float(sample_shift["shift_minutes"]))
    excluded_minutes = st.number_input("Excluded breaks (minutes)", min_value=0., value=float(sample_shift["excluded_minutes"]))
    ideal_cycle_seconds = st.number_input("Ideal cycle time (seconds per part)", min_value=0., value=1., format="%.4f",
                                         help="The fastest achievable time per part, not the average measured time.")
with right:
    total_count = st.number_input("Total parts (including rejects)", min_value=0, value=19271, step=1)
    good_count = st.number_input("First-pass good parts", min_value=0, value=18848, step=1,
                                help="Do not count scrap or parts needing rework as first-pass good.")


def input_table(title, sample, key, column_config):
    st.subheader(title)
    upload = st.file_uploader("Replace with CSV", type=["csv"], key=f"{key}_upload")
    source = pd.read_csv(upload) if upload is not None else sample
    # Sample/CSV integer columns must still allow fractional-minute edits.
    for column in ("minutes", "proposed_minutes"):
        if column in source and pd.api.types.is_numeric_dtype(source[column]):
            source = source.astype({column: float})
    return st.data_editor(source, num_rows="dynamic", hide_index=True, width="stretch",
                          key=key, column_config=column_config)


try:
    st.write("Record each stop once, within planned production. Durations must not overlap. Delete the example rows to enter your own; an empty log means no stops.")
    stops = input_table("2. Stop log", sample_stops, "stops", {
        "category": st.column_config.TextColumn("Reason", required=True),
        "minutes": st.column_config.NumberColumn("Stopped minutes", min_value=0., required=True),
    })
    st.write("A changeover switches the machine to another product. Internal tasks need the machine stopped; external tasks can happen while it runs. Proposed times are estimates for one serial changeover, not measured improvements.")
    tasks = input_table("3. Changeover task study (optional)", sample_tasks, "tasks", {
        "step": st.column_config.TextColumn("Task", required=True),
        "kind": st.column_config.SelectboxColumn("Current type", options=["internal", "external"], required=True),
        "proposed_kind": st.column_config.SelectboxColumn("Proposed type", options=["internal", "external"], required=True),
        "minutes": st.column_config.NumberColumn("Current minutes", min_value=0., required=True),
        "proposed_minutes": st.column_config.NumberColumn("Proposed minutes", min_value=0., required=True),
    })
    report = build_equipment_report({"shift_minutes": shift_minutes, "excluded_minutes": excluded_minutes,
                                    "ideal_cycle_seconds": ideal_cycle_seconds,
                                    "total_count": total_count, "good_count": good_count}, stops, tasks)
except (ValueError, UnicodeError, pd.errors.ParserError) as error:
    st.error(f"Check the inputs: {error}")
    st.stop()

st.session_state["equipment_report"] = report
result = report["oee"]
st.subheader("Measured production result")
st.write("Overall equipment effectiveness (OEE) combines availability, the share of planned time running; performance, speed against the ideal; and quality, the share good on the first pass.")
for column, name in zip(st.columns(4), ("availability", "performance", "quality", "oee")):
    value = result[name]
    column.metric(name.upper() if name == "oee" else name.capitalize(), "N/A" if value is None else f"{value:.2%}")
st.caption("OEE = availability × performance × quality. With no run time or no parts, the undefined factors show N/A and OEE is zero.")
losses = pd.DataFrame({"Where the planned time went": ["Stops", "Slow running / small stops", "Rejects / rework", "Fully productive"],
                       "Equivalent minutes": [result[key] for key in ("availability_loss_minutes", "performance_loss_minutes", "quality_loss_minutes", "fully_productive_minutes")]})
st.dataframe(losses, hide_index=True, width="stretch")
st.caption(f"Planned: {result['planned_minutes']:g} min. Running: {result['run_minutes']:g} min. Losses plus fully productive time equal planned time.")
st.subheader("Downtime Pareto")
st.write("This ranks reasons by stopped minutes, rather than how often they happened. The darker bars reach at least 80% of stopped time; this helps choose what to investigate first.")
st.dataframe(report["downtime"], hide_index=True, width="stretch")
fig = pareto_chart(report["downtime"], "Downtime by reason", "Minutes", "Stopped minutes")
try:
    st.pyplot(fig)
finally:
    fig.clear()

st.subheader("Proposed changeover plan")
smed = report["changeover"]
before, after, saved = st.columns(3)
before.metric("Current stopped time", f"{smed['baseline_stop_minutes']:g} min")
after.metric("Proposed stopped time", f"{smed['proposed_stop_minutes']:g} min")
saved.metric("Potential time freed per changeover", f"{smed['saved_stop_minutes']:g} min")
st.caption(f"External task time: {smed['baseline_external_minutes']:g} → {smed['proposed_external_minutes']:g} min. Moving work outside the stop does not remove that work. The task study is separate from the period's stop log; it never changes measured OEE.")
st.dataframe(smed["tasks"], hide_index=True, width="stretch")
download = {"production": result, "downtime": report["downtime"].to_dict(orient="records"),
            "changeover": {k: v for k, v in smed.items() if k != "tasks"},
            "changeover_tasks": smed["tasks"].to_dict(orient="records")}
st.download_button("Download calculation (JSON)", json.dumps(download, indent=2, allow_nan=False),
                   file_name="equipment_report.json", mime="application/json")
st.download_button("Download downtime table (CSV)", report["downtime"].to_csv(index=False),
                   file_name="downtime_pareto.csv", mime="text/csv")
