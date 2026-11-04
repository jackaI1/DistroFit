"""Censored life analysis using the same calculation module as the CLI."""
import io
import json

import pandas as pd
import streamlit as st

from reliability import analyze_lifetimes, life_curves
from reliability_report import generate_demo, model_table, read_lifetime_csv, reliability_figure

st.set_page_config(page_title="DistroFit: Reliability", layout="wide")
st.title("Reliability")
st.write("Estimate equipment life while keeping units that were still running when observation stopped.")
st.caption("The starting log contains 80 generated pump-seal lifetimes, not factory measurements. All ages on this page are operating hours.")
st.session_state.pop("reliability_report", None)

st.subheader("Failure and suspension log")
st.write("Enter one row per independent unit from installation to failure or last observation. Set failed to 1 for a failure, or 0 for a suspension: a unit still running at its recorded age. Use one comparable component population with the same operating conditions.")
upload = st.file_uploader("Replace the example with a CSV", type=["csv"], key="life_upload",
                          help="Required columns: time (positive hours), failed (1 or 0). Extra columns are not analyzed or exported.")
confidence = st.selectbox("Confidence level", [.90, .95, .99], index=1,
                          format_func=lambda value: f"{value:.0%}", key="life_confidence")
try:
    source = read_lifetime_csv(upload) if upload is not None else generate_demo()
    if "time" in source and pd.api.types.is_numeric_dtype(source["time"]):
        source = source.astype({"time": float})
    table = st.data_editor(source, key="life_log", num_rows="dynamic", hide_index=True, width="stretch",
                           column_config={"time": st.column_config.NumberColumn("Observed age (hours)", required=True),
                                          "failed": st.column_config.NumberColumn("Failed (1=yes, 0=still running)",
                                                                                 min_value=0, max_value=1, step=1, required=True)})
    report = analyze_lifetimes(table, confidence=confidence)
except (ValueError, OSError, UnicodeError, pd.errors.ParserError) as error:
    st.error(f"Check the log: {error}")
    st.stop()

st.session_state["reliability_report"] = report
summary = report["summary"]
st.write(f"{summary['units']} units: {summary['failures']} failures and {summary['suspensions']} suspensions, with {summary['total_time']:,.1f} total operating hours observed.")
for warning in report["warnings"]:
    st.warning(warning)

st.subheader("Life estimates")
st.write("Each curve uses both failures and still-running hours. Mean life is mean time to failure (MTTF) for first-life units. It represents mean time between failures (MTBF) only for independent replacement cycles that restore the unit to as-new condition. B10 is the age by which the fitted model expects 10% to fail.")
selected = None
if report["fits"]:
    models = [fit["model"] for fit in report["fits"]]
    if st.session_state.get("life_model") not in models:
        st.session_state["life_model"] = models[0]
    selected = st.selectbox("Inspect model", models, key="life_model")
    fit = next(f for f in report["fits"] if f["model"] == selected)
    age = st.number_input("Planning age (hours)", min_value=.001, value=500., key="planning_age")
    a, b, c = st.columns(3)
    a.metric("Mean life (MTTF / renewal MTBF)", f"{fit['mean_life']['estimate']:,.1f} hours")
    b.metric("B10 life", f"{fit['b10']['estimate']:,.1f} hours")
    c.metric(f"Survival at {age:g} hours", f"{float(life_curves(fit, [age])['survival'][0]):.1%}")
    for label, key in [("Mean life", "mean_life"), ("B10 life", "b10")]:
        interval = fit[key]
        st.write(f"{label}: approximate {confidence:.0%} confidence interval {interval['lower']:,.1f} to {interval['upper']:,.1f} hours.")
    st.caption("These intervals describe uncertainty in model estimates, not the range of individual lifetimes. They use a large-sample approximation and can be unreliable with few failures or heavy censoring.")
    st.dataframe(model_table(report), hide_index=True, width="stretch")
    st.caption("AIC compares the fit of these models on the same censored log while accounting for parameter count; lower is better. A close ranking does not establish the true life distribution. Shape and scale parameters are included in the JSON download.")
else:
    st.warning("No life model can be estimated from this log. The empirical curve below still shows the observed evidence.")
for excluded in report["excluded"]:
    st.info(f"{excluded['model'].capitalize()} excluded: {excluded['reason']}")

st.subheader("Check the curves")
st.write("Survival is the share expected to last beyond an age. Hazard is the instantaneous failure rate among surviving units, per operating hour. The stepped Kaplan-Meier curve uses observed failures without choosing a life model; marks show suspensions. On the probability plot, points close to the line support that model's shape.")
figure = reliability_figure(report, model=selected)
try:
    st.pyplot(figure, width="stretch")
    png = io.BytesIO()
    figure.savefig(png, format="png", dpi=150)
finally:
    figure.clear()
st.caption("The gray band is a pointwise confidence interval for empirical survival. Model curves beyond the last observed age are extrapolations. A final survival value of zero cannot be shown on the probability scale, so that endpoint is omitted.")
with st.expander("Risk counts and assumptions"):
    st.dataframe(pd.DataFrame(report["kaplan_meier"]), hide_index=True, width="stretch")
    st.write("Suspensions must be unrelated to hidden failure risk. Removing a unit because it appears close to failure violates this assumption. Do not mix different failure modes, operating stresses, left or interval censoring, or units already in service when observation began. The page does not model repairable-system trends or choose a maintenance interval automatically.")

st.download_button("Download reliability calculation (JSON)", json.dumps(report, indent=2, allow_nan=False),
                   file_name="reliability.json", mime="application/json")
st.download_button("Download life estimates (CSV)", model_table(report).to_csv(index=False),
                   file_name="life_estimates.csv", mime="text/csv")
st.download_button("Download reliability charts (PNG)", png.getvalue(), file_name="reliability.png", mime="image/png")
