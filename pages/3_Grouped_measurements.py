"""Compare related measurement batches with a partially pooled normal model."""
import hashlib
import json

import pandas as pd
import streamlit as st

from bayesian import (fit_grouped, generate_demo, posterior_figure, predictive_figure,
                      validate_grouped)

st.set_page_config(page_title="DistroFit: Grouped measurements", layout="wide")
st.title("Grouped measurements")
st.write("Compare related batches while showing how uncertain each batch's average is. "
         "Small batches borrow information from the others, a method called partial pooling.")
st.caption("The starting table contains 80 synthetic readings from four batches, in arbitrary measurement units. "
           "This model assumes independent readings with a bell-shaped spread and the same noise level in every batch.")

upload = st.file_uploader("Replace the example with a grouped CSV", type=["csv"], key="bayes_upload",
                          help="Columns: group (batch or machine label), value (numeric measurement). "
                               "Use 2 to 20 comparable groups, at least 8 varying readings per group, at most 2000 rows.")
try:
    source = pd.read_csv(upload) if upload is not None else generate_demo()
    table = st.data_editor(source, key="bayes_log", num_rows="dynamic", hide_index=True, width="stretch")
    data = validate_grouped(table)
except (ValueError, OSError, UnicodeError, pd.errors.ParserError) as error:
    st.session_state.pop("bayesian_result", None)
    st.session_state.pop("bayesian_signature", None)
    st.error(f"Check the readings: {error}")
    st.stop()

controls = st.columns(2)
with controls[0]:
    draws = st.number_input("Retained draws per chain", min_value=1500, max_value=5000,
                            value=1500, step=500, key="bayes_draws")
with controls[1]:
    seed = st.number_input("Random seed", min_value=0, max_value=2147483646, value=42, step=1, key="bayes_seed")
st.caption("Four NUTS chains, 1500 warm-up steps each, target acceptance 0.95, one CPU core. "
           "NUTS explores plausible parameter values; warm-up steps are discarded. "
           "Allow a few minutes for the first run while the model compiles.")
with st.expander("Model, priors and shared comparison rows"):
    st.write("Each group has its own mean around a shared population mean. All groups share a within-group "
             "standard deviation. A weakly informative prior allows a broad range of plausible means and spreads "
             "before fitting. Its units are calibrated from training readings only.")
    st.code("Standardized population mean ~ Normal(0, 2)\n"
            "Between-group SD ~ HalfNormal(1)\nWithin-group SD ~ HalfNormal(1)\n"
            "Group offset ~ Normal(0, 1)\nGroup mean = population mean + between-group SD × offset")
    st.write("I hold out 25% of each group's readings. Both PyMC and DistroFit's independent normal "
             "maximum-likelihood fits use the other 75%. Neither method sees held-out readings during fitting. "
             "Prior calibration from the training data is an empirical choice; inspect the prior predictive "
             "check before trusting it for a new process.")

signature = hashlib.sha256(data.to_csv(index=False).encode() + f"{draws}:{seed}".encode()).hexdigest()
if st.session_state.get("bayesian_signature") != signature:
    st.session_state.pop("bayesian_result", None)
if st.button("Fit grouped model", type="primary", key="bayes_fit"):
    st.session_state.pop("bayesian_result", None)
    try:
        with st.spinner("Sampling four chains and checking the predictions..."):
            result = fit_grouped(data, draws=int(draws), seed=int(seed), strict=False)
        st.session_state["bayesian_result"] = result
        st.session_state["bayesian_signature"] = signature
    except (ValueError, RuntimeError) as error:
        st.error(f"The model could not be fitted: {error}")
        st.stop()

if "bayesian_result" not in st.session_state:
    st.info("Edit or upload readings, then choose Fit grouped model. Sampling runs only when you press the button.")
    st.stop()
result = st.session_state["bayesian_result"]
checks = result["diagnostics"]
st.subheader("Can I trust the sampling?")
st.write("R-hat checks whether chains agree. Effective sample size (ESS) estimates the independent information "
         "in correlated draws, for both the centre and tails. Divergences flag paths the sampler could not follow reliably.")
st.dataframe(pd.DataFrame([{"Largest R-hat": checks["max_rhat"], "Smallest bulk ESS": checks["min_ess_bulk"],
                            "Smallest tail ESS": checks["min_ess_tail"], "Divergences": checks["divergences"]}]),
             hide_index=True, width="stretch")
with st.expander("Diagnostics for every parameter"):
    st.dataframe(pd.DataFrame(checks["parameters"]), hide_index=True, width="stretch")
if not checks["passed"]:
    st.error("Sampling checks failed. " + " ".join(checks["issues"]))
    st.warning("Increase retained draws or check whether these groups belong in the same normal model. "
               "Do not use these estimates for a decision. Downloads are withheld until the checks pass.")
    st.stop()
st.success("Sampling checks passed: R-hat ≤ 1.01, bulk and tail ESS ≥ 400, and zero divergences. "
           "These checks do not prove the model describes the process.")

st.subheader("Batch averages and uncertainty")
st.plotly_chart(posterior_figure(result), width="stretch")
st.caption("Blue distributions show plausible group means after seeing the training readings (the posterior). "
           "Bars contain the middle 95% of each mean's posterior probability. "
           "Gray crosses are independent maximum-likelihood (MLE) estimates. "
           "These are intervals for group means, not ranges for individual future readings.")
st.dataframe(result["comparison"].rename(columns={
    "group": "Group", "n_train": "Training readings", "n_held": "Held-out readings",
    "mle_mean": "Independent MLE mean", "mle_sd": "Independent MLE SD",
    "bayes_mean": "Partially pooled mean", "mean_lower": "Mean 95% lower", "mean_upper": "Mean 95% upper",
    "mle_held_nll": "MLE held-out NLL", "bayes_held_nll": "Bayesian held-out NLL"}),
    hide_index=True, width="stretch")
st.write("The last two columns score held-out readings using negative log likelihood (NLL). Lower is better. "
         "The Bayesian score averages predictive densities across posterior draws; the MLE score uses one fitted "
         "curve. Compare methods within a group. A single split is not proof one method is better.")

st.subheader("Do the predictions look like the readings?")
group = st.selectbox("Group to inspect", list(result["comparison"].group), key="bayes_group")
st.plotly_chart(predictive_figure(result, group), width="stretch")
st.write("The prior predictive curve generates readings before fitting. The posterior predictive curve "
         "generates readings after fitting. Compare their location, spread and extremes with the training histogram. "
         "Use the legend and zoom to inspect a narrow range.")
st.dataframe(result["predictive_checks"].query("group == @group"), hide_index=True, width="stretch")
st.caption("Checks compare each group's observed mean, SD and maximum with 95% ranges of replicated training "
           "datasets. Upper probability is the fraction of replicated statistics at least as large as observed. "
           "Flagged statistics fall outside the posterior range. These are in-sample exploratory checks, "
           "not held-out accuracy or formal pass/fail tests of the model.")

st.subheader("Keep the comparison")
st.download_button("Download group comparison", result["comparison"].to_csv(index=False),
                   "grouped-comparison.csv", "text/csv")
st.download_button("Download predictive checks", result["predictive_checks"].to_csv(index=False),
                   "predictive-checks.csv", "text/csv")
payload = {"settings": result["settings"], "diagnostics": checks,
           "comparison": result["comparison"].to_dict("records"),
           "predictive_checks": result["predictive_checks"].to_dict("records")}
st.download_button("Download settings and diagnostics", json.dumps(payload, indent=2, allow_nan=False),
                   "grouped-diagnostics.json", "application/json")
st.caption("Use python bayesian.py --sample --out /tmp/distrofit-grouped for a complete record including "
           "posterior draws and row-level split membership. Keep reports made from private readings private.")
