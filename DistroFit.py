"""Local exploratory distribution fitting with untouched validation data."""
import hashlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
import streamlit as st

from analysis import (adjust_parameters, calculate_bin_count, create_report, diagnostics, evaluate_scenario,
                      fit_candidates, get_supported_distributions, manual_curve,
                      prepare_data, read_csv, report_payload)

st.set_page_config(page_title="DistroFit: Statistical Analytics", page_icon="📈", layout="wide")


@st.cache_data
def load_sample_data(kind="Gamma"):
    rng = np.random.default_rng(42)
    if kind == "Gamma":
        values = rng.gamma(2, 2, 1000)
    elif kind == "Log-Normal":
        values = rng.lognormal(0, .9, 1000)
    else:
        values = np.concatenate([rng.normal(0, 1, 600), rng.normal(5, 2, 400)])
    return pd.DataFrame({"Value": values})


@st.cache_data(max_entries=4)
def cached_fit(values, candidates, bins, fraction, seed):
    return fit_candidates(values, candidates, bins, fraction, seed)


@st.cache_data(max_entries=2)
def cached_report(payload):
    return create_report(payload)


def parse_numbers(text):
    return np.array([float(value) for value in text.replace(",", " ").split()])


def chart(figure, title, theme, key, x_label="Value", y_label="Density"):
    figure.update_layout(title=title, template=theme, xaxis_title=x_label,
                         yaxis_title=y_label, margin=dict(l=20, r=20, t=55, b=30))
    st.plotly_chart(figure, width="stretch", key=key)


def main():
    # Invalid/new inputs must never expose a stale winner or report.
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("report_payload", None)
    st.title("📈 DistroFit")
    st.markdown("### Distribution fitting & statistical analysis")
    st.caption("Fit on training observations. Compare on held-out observations. Challenge with another scenario.")
    source_values = None
    source_description = ""
    with st.sidebar:
        st.header("Control panel")
        with st.expander("1. Data Import", expanded=True):
            source = st.radio("Source:", ["Upload CSV", "Manual Entry", "Sample Data"])
            if source == "Upload CSV":
                uploaded = st.file_uploader("Upload .csv", type=["csv"])
                if uploaded is not None:
                    try:
                        frame = read_csv(uploaded)
                        numeric = frame.select_dtypes(include=np.number).columns.tolist()
                        if not numeric:
                            st.error("The CSV has no numeric columns. Add a numeric column and upload again.")
                        else:
                            column = st.selectbox("Target Column:", numeric)
                            source_values = frame[column].to_numpy(dtype=float)
                            source_description = f"CSV column: {column}"
                    except (ValueError, UnicodeError, pd.errors.ParserError) as error:
                        st.error(f"Could not read CSV: {error}")
            elif source == "Manual Entry":
                raw = st.text_area("Paste numbers:", key="manual_input", help="Separated by space, comma or newline")
                if raw.strip():
                    try:
                        source_values = parse_numbers(raw)
                        source_description = "Manual entry"
                    except ValueError:
                        st.error("Enter numbers separated by spaces, commas or newlines.")
            else:
                sample = st.selectbox("Sample Type:", ["Gamma", "Log-Normal", "Bimodal (Mix)"])
                source_values = load_sample_data(sample)["Value"].to_numpy()
                source_description = f"Synthetic {sample}; generator seed=42; N=1000"
        if source_values is None:
            st.info("Choose Sample Data, paste numbers, or upload a numeric CSV to begin.")
            return
        with st.expander("2. Preprocessing", expanded=False):
            outlier_method = st.selectbox("Outlier Removal:", ["None", "Z-Score", "IQR"])
            threshold = st.slider("Z-Threshold", 1.5, 4., 3., .1) if outlier_method == "Z-Score" else 3.
            values, removed = prepare_data(source_values, outlier_method, threshold)
            if removed:
                st.warning(f"Removed {removed} nonfinite observations or outliers.")
            if outlier_method != "None":
                st.caption("Filtering precedes the split and changes the population being fitted, including its tails.")
            bin_method = st.selectbox("Binning Algo:", ["Freedman-Diaconis", "Square Root", "Sturges", "Manual"])
            bins = (st.slider("Number of Bins", 5, 200, 30) if bin_method == "Manual"
                    else calculate_bin_count(values, bin_method))
            st.caption(f"Calculated Bins: {bins}")
        with st.expander("3. Plot Settings", expanded=False):
            theme = st.selectbox("Theme:", ["plotly_white", "plotly_dark", "ggplot2", "seaborn"])
            opacity = st.slider("Histogram Opacity", .1, 1., .6)
            line_width = st.slider("Fit Line Width", 1, 5, 2)
        with st.expander("4. Validation", expanded=False):
            fraction = st.slider("Held-out fraction", .1, .5, .25, .05)
            seed = int(st.number_input("Split seed", min_value=0, max_value=2147483647, value=42, step=1))

    if len(values) < 8 or np.ptp(values) == 0:
        st.error("Provide at least 8 finite, varying observations after filtering.")
        return
    st.subheader("Exploratory data analysis")
    columns = st.columns(5)
    labels = ["Count (N)", "Mean", "Std. Dev", "Skewness", "Kurtosis"]
    numbers = [len(values), np.mean(values), np.std(values, ddof=1),
               stats.skew(values, bias=False), stats.kurtosis(values, bias=False)]
    for column, label, value in zip(columns, labels, numbers):
        column.metric(label, f"{value:.3f}" if label != "Count (N)" else str(value))
    density, box = st.columns([2, 1])
    with density:
        figure = go.Figure(go.Histogram(x=values, nbinsx=bins, histnorm="probability density",
                                       marker_color="#5c7cfa", opacity=opacity, name="Data"))
        chart(figure, "Empirical density histogram", theme, "hist")
    with box:
        chart(go.Figure(go.Box(y=values, name="Data", marker_color="#5c7cfa")),
              "Box plot", theme, "box", y_label="Value")

    st.subheader("Distribution fitting")
    dist_dict = get_supported_distributions()
    selected = st.multiselect("Select Candidates:", list(dist_dict),
                             default=["Normal", "Gamma", "Weibull (Min)", "Log-Normal", "Exponential"])
    if st.button("Recalculate Fit"):
        cached_fit.clear()
    if not selected:
        st.warning("Please select at least one distribution to fit.")
        return
    try:
        with st.spinner("Fitting selected distributions on training data..."):
            fit = cached_fit(values, tuple(selected), bins, fraction, seed)
    except ValueError as error:
        st.error(str(error))
        return
    st.session_state["analysis_result"] = fit
    for name, error in fit["errors"].items():
        st.warning(f"{name} could not be fitted: {error}")
    if not fit["results"]:
        st.error("None of the selected candidates produced a valid training fit. Try other families or inspect the data.")
        return
    rows = fit["results"]
    best = rows[0]
    if not np.isfinite(best["Held-out NLL"]):
        st.warning("Every model rejects held-out observations outside its support. No finite-loss winner; inspect the data and candidates.")
    else:
        st.success(f"Best Fit: **{best['Distribution']}** (Lowest held-out NLL)")
    training = values[fit["train_indices"]]
    held = values[fit["held_indices"]]
    metrics = st.columns(4)
    metrics[0].metric("Training observations", len(training))
    metrics[1].metric("Held-out observations", len(held))
    metrics[2].metric("Families fitted", f"{len(rows)} / {len(selected)}")
    metrics[3].metric("Models failing tail check", sum(row["Tail"]["flagged"] for row in rows))
    tabs = st.tabs(["🚀 Auto-Fit", "📉 Tail & Q-Q", "🎛️ Manual", "Scenario", "Method & export"])
    x = np.linspace(values.min(), values.max(), 500)
    with tabs[0]:
        plot, table = st.columns([2, 1])
        with plot:
            figure = go.Figure(go.Histogram(x=training, nbinsx=bins, histnorm="probability density",
                                           name="Training", marker_color="#ced4da", opacity=opacity))
            figure.add_trace(go.Scatter(x=held, y=np.zeros(len(held)), mode="markers", name="Held out",
                                       marker=dict(symbol="line-ns", size=9, color="#555")))
            for row in rows:
                figure.add_trace(go.Scatter(x=x, y=manual_curve(row["Distribution"], row["Parameters"], x),
                                           name=row["Distribution"], line=dict(width=line_width)))
            chart(figure, "Training curves and untouched held-out observations", theme, "fits")
        with table:
            report_slot = st.empty()
            frame = pd.DataFrame(rows)
            st.dataframe(frame[["Distribution", "Train NLL", "Held-out NLL", "SSE", "AIC", "BIC", "KS Stat"]],
                         hide_index=True, width="stretch")
            st.caption("Lower NLL wins. Infinite loss means the model rejects an observation outside its support. AIC, BIC and SSE describe training only.")
            with st.expander("Fitted parameters"):
                st.json({row["Distribution"]: row["Parameters"] for row in rows})

    with tabs[1]:
        check = best["Tail"]
        left, right = st.columns(2)
        left.metric("Model share above threshold", f"{check['model_share']:.2%}")
        right.metric("Held-out share above threshold", f"{check['observed_share']:.2%}")
        st.caption(f"Threshold: {fit['tail_threshold']:.6g}, the training 95th percentile. "
                   f"Observed {check['exceedances']} of {len(held)}; model 95% count interval: "
                   f"{check['expected_count_interval']}. Exploratory check, not proof of tail adequacy.")
        if check["flagged"]:
            st.warning("Observed held-out tail count falls outside the model's expected interval.")
        survival = go.Figure()
        survival.add_trace(go.Scatter(x=x, y=dist_dict[best["Distribution"]].sf(x, *best["Parameters"]), name="Model survival"))
        ordered = np.sort(held)
        survival.add_trace(go.Scatter(x=ordered, y=(len(held)-np.arange(len(held))-1)/len(held),
                                     name="Held-out survival", mode="lines", line=dict(dash="dot")))
        survival.add_vline(x=fit["tail_threshold"], line_dash="dash")
        chart(survival, "Tail survival", theme, "tail", y_label="Share above value")
        diagnostic = diagnostics(best["Distribution"], best["Parameters"], held, bins)
        qq = go.Figure(go.Scatter(x=diagnostic["theoretical"], y=diagnostic["observed"], mode="markers", name="Held out"))
        limits = [min(diagnostic["theoretical"].min(), held.min()), max(diagnostic["theoretical"].max(), held.max())]
        qq.add_trace(go.Scatter(x=limits, y=limits, mode="lines", name="Identity", line=dict(dash="dash")))
        chart(qq, f"Held-out Q-Q vs {best['Distribution']}", theme, "qq", "Model quantile", "Held-out quantile")
        residual = go.Figure(go.Scatter(x=diagnostic["observed"], y=diagnostic["cdf_residual"], mode="markers", name="CDF residual"))
        residual.add_hline(y=0)
        chart(residual, "Where the fit misses: CDF residual", theme, "cdf-residual", y_label="Empirical minus model CDF")
        residual = go.Figure(go.Bar(x=diagnostic["bin_centers"], y=diagnostic["density_residual"], name="Density residual"))
        chart(residual, "Density residual by bin", theme, "density-residual", y_label="Observed minus model density")

    with tabs[2]:
        controls, plot = st.columns([1, 2])
        with controls:
            name = st.selectbox("Distribution:", list(dist_dict))
            dist = dist_dict[name]
            match = next((row for row in rows if row["Distribution"] == name), None)
            try:
                initial = match["Parameters"] if match else dist.fit(training)
            except (ValueError, RuntimeError):
                initial = [1.] * dist.numargs + [float(training.mean()), float(training.std())]
            signature = hashlib.sha256(values.tobytes()).hexdigest()[:12] + f"_{seed}_{fraction}_{name}"
            labels = ([] if not dist.shapes else [label.strip() for label in dist.shapes.split(",")]) + ["Loc", "Scale"]
            offset_key, multiplier_key = f"offset_{signature}", f"multiplier_{signature}"
            if st.button("Reset shape"):
                for i, value in enumerate(initial):
                    st.session_state[f"manual_{signature}_{i}"] = float(value)
                st.session_state[offset_key] = 0.
                st.session_state[multiplier_key] = 1.
            parameters = []
            for i, (label, value) in enumerate(zip(labels, initial)):
                options = {"min_value": float(np.finfo(float).tiny)} if i != len(initial)-2 else {}
                parameter_key = f"manual_{signature}_{i}"
                if parameter_key not in st.session_state:
                    st.session_state[parameter_key] = float(value)
                parameters.append(st.number_input(label, format="%.8g",
                                                  key=parameter_key, **options))
            base_parameters = parameters[:]
            location_offset = st.slider("Location offset (training standard deviations)",
                                        -3., 3., None if offset_key in st.session_state else 0.,
                                        .1, key=offset_key)
            scale_multiplier = st.slider("Scale multiplier", .1, 5.,
                                         None if multiplier_key in st.session_state else 1.,
                                         .1, key=multiplier_key)
            parameters = adjust_parameters(parameters, training, location_offset, scale_multiplier)
            st.metric("Adjusted location", f"{parameters[-2]:.6g}")
            st.metric("Adjusted scale", f"{parameters[-1]:.6g}")
            cdf = st.checkbox("Show CDF")
            st.caption("Manual parameters affect this curve and the report; candidate rankings retain their training fits.")
        with plot:
            figure = go.Figure()
            if cdf:
                figure.add_trace(go.Scatter(x=np.sort(values), y=(np.arange(len(values))+1)/len(values), name="Empirical CDF"))
            else:
                figure.add_trace(go.Histogram(x=training, nbinsx=bins, histnorm="probability density", opacity=opacity, name="Training"))
            try:
                figure.add_trace(go.Scatter(x=x, y=manual_curve(name, initial, x, cdf), name="Training fit",
                                           line=dict(width=line_width, dash="dash")))
                figure.add_trace(go.Scatter(x=x, y=manual_curve(name, parameters, x, cdf), name="Manual fit", line=dict(width=line_width)))
                chart(figure, f"{name} {'CDF' if cdf else 'PDF'}", theme, "manual", y_label="CDF" if cdf else "Density")
            except ValueError as error:
                st.error(str(error))
        manual = {"distribution": name, "parameters": parameters, "base_parameters": base_parameters,
                  "location_offset": location_offset, "scale_multiplier": scale_multiplier,
                  "view": "CDF" if cdf else "PDF"}

    scenario_values = None
    with tabs[3]:
        st.write("Paste another scenario. Existing training parameters stay fixed; no scenario observation is used to fit them.")
        raw = st.text_area("Scenario observations", key="scenario_input", help="Numbers separated by spaces, commas or newlines")
        if raw.strip():
            try:
                scenario_values = parse_numbers(raw)
                scenario_results = evaluate_scenario(fit, scenario_values)
                st.dataframe(pd.DataFrame(scenario_results)[["Distribution", "Scenario NLL"]], hide_index=True, width="stretch")
                st.caption("This is a sensitivity comparison. It does not replace the held-out winner above.")
                st.json({row["Distribution"]: row["Tail"] for row in scenario_results})
            except ValueError:
                scenario_values = None
                st.error("Enter at least one finite numeric scenario observation.")
        else:
            st.info("Enter a second scenario to compare frozen models.")
    settings = {"source": source_description, "outlier_method": outlier_method, "z_threshold": threshold,
                "removed_count": removed, "bin_method": bin_method,
                "plot_theme": theme, "histogram_opacity": opacity, "line_width": line_width}
    payload = report_payload(fit, source_values, settings, scenario_values, manual)
    st.session_state["report_payload"] = payload
    with tabs[4]:
        st.subheader("Method")
        st.write(payload["method"])
        st.subheader("Settings")
        st.json(payload["settings"])
        st.subheader("Data")
        st.write(f"{len(source_values)} source observations; {len(values)} after filtering; "
                 f"{len(training)} training / {len(held)} held out.")
        st.caption("The PDF contains every source, prepared and scenario observation, split membership, "
                   "fitted and manual parameters, scores, failures, tail checks, plots and package versions. "
                   "Its first-page annotation also stores the full analysis as JSON.")
    with report_slot:
        st.download_button("Download reproducible report", cached_report(payload),
                           file_name="distrofit_report.pdf", mime="application/pdf", on_click="ignore")


if __name__ == "__main__":
    main()
