# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 17:59:43 2025

@author: jackl
"""

import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="DistroFit: Statistical Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    /* Metric Card Styling */
    .stMetric {
        background-color: var(--background-color);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid var(--secondary-background-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Tab Styling - Cleaner & More Compact */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--secondary-background-color);
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: nowrap;
        background-color: transparent;
        border-radius: 4px;
        padding: 0px 20px;
        font-weight: 600;
        border: none;
        color: var(--text-color);
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--secondary-background-color);
        color: var(--primary-color);
        border-bottom: 2px solid var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

@st.cache_data
def load_sample_data(type="Gamma"):
    """Generates complex sample datasets for demo purposes."""
    np.random.seed(42)
    if type == "Gamma":
        data = stats.gamma.rvs(a=2, loc=0, scale=2, size=1000)
    elif type == "Bimodal (Mix)":
        data1 = np.random.normal(0, 1, 600)
        data2 = np.random.normal(5, 2, 400)
        data = np.concatenate([data1, data2])
    elif type == "Log-Normal":
        data = stats.lognorm.rvs(s=0.9, size=1000)
    else:
        data = np.random.normal(0, 1, 1000)
    return pd.DataFrame(data, columns=['Value'])

def filter_outliers(df, col, method="None", threshold=3.0):
    """Filters outliers based on Z-Score or IQR."""
    data = df[col]
    if method == "Z-Score":
        z_scores = np.abs(stats.zscore(data))
        df_filtered = df[z_scores < threshold]
        return df_filtered, len(df) - len(df_filtered)
    elif method == "IQR":
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        df_filtered = df[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR)))]
        return df_filtered, len(df) - len(df_filtered)
    return df, 0

def get_supported_distributions():
    """Returns a dictionary of supported scipy stats distributions."""
    return {
        "Normal": stats.norm,
        "Gamma": stats.gamma,
        "Weibull (Min)": stats.weibull_min,
        "Exponential": stats.expon,
        "Log-Normal": stats.lognorm,
        "Beta": stats.beta,
        "Uniform": stats.uniform,
        "Student's t": stats.t,
        "Chi-Squared": stats.chi2,
        "Cauchy": stats.cauchy,
        "Pareto": stats.pareto,
        "Logistic": stats.logistic,
        "Laplace": stats.laplace,
        "Maxwell": stats.maxwell
    }

def calculate_bin_count(data, method="Freedman-Diaconis"):
    """Calculates optimal bin count using statistical rules."""
    n = len(data)
    if n == 0: return 10
    
    if method == "Square Root":
        return int(np.sqrt(n))
    elif method == "Sturges":
        return int(np.ceil(np.log2(n) + 1))
    elif method == "Freedman-Diaconis":
        q25, q75 = np.percentile(data, [25, 75])
        iqr = q75 - q25
        bin_width = 2 * iqr * (n ** (-1/3))
        if bin_width == 0: return int(np.sqrt(n))
        return int(np.ceil((data.max() - data.min()) / bin_width))
    else:
        return 30 # Default

# --- MAIN APPLICATION ---

def main():
    st.title("📈 DistroFit")
    st.markdown("### Advanced Distribution Fitting & Statistical Analysis")
    
    # --- 1. SIDEBAR CONTROLS ---
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        with st.expander("1. Data Import", expanded=True):
            data_source = st.radio("Source:", ["Upload CSV", "Manual Entry", "Sample Data"])
            
            df = None
            if data_source == "Upload CSV":
                uploaded_file = st.file_uploader("Upload .csv", type=["csv"])
                if uploaded_file:
                    try:
                        df = pd.read_csv(uploaded_file)
                        
                        # Auto-detect if CSV has no header (first row is numeric)
                        try:
                            float(df.columns[0])
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, header=None)
                            df.columns = [f"Column {i+1}" for i in range(df.shape[1])]
                        except (ValueError, TypeError):
                            pass

                        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
                        target_column = st.selectbox("Target Column:", numeric_cols)
                        df = df[[target_column]].dropna()
                        df.columns = ['Value']
                    except Exception as e:
                        st.error(f"Error: {e}")
            elif data_source == "Manual Entry":
                raw = st.text_area("Paste numbers:", height=100, help="Separated by space, comma or newline")
                if raw:
                    try:
                        vals = [float(x) for x in raw.replace(',', ' ').split()]
                        df = pd.DataFrame(vals, columns=['Value'])
                    except:
                        st.error("Invalid numeric input")
            else:
                sample_type = st.selectbox("Sample Type:", ["Gamma", "Log-Normal", "Bimodal (Mix)"])
                df = load_sample_data(sample_type)

        if df is not None and not df.empty:
            with st.expander("2. Preprocessing", expanded=False):
                outlier_method = st.selectbox("Outlier Removal:", ["None", "Z-Score", "IQR"])
                
                threshold = 3.0
                if outlier_method == "Z-Score":
                    threshold = st.slider("Z-Threshold", 1.5, 4.0, 3.0, 0.1)
                
                df_clean, dropped_count = filter_outliers(df, 'Value', outlier_method, threshold)
                
                if dropped_count > 0:
                    st.warning(f"Removed {dropped_count} outliers.")
                
                bin_method = st.selectbox("Binning Algo:", ["Freedman-Diaconis", "Square Root", "Sturges", "Manual"])
                if bin_method == "Manual":
                    bins = st.slider("Number of Bins", 5, 200, 30)
                else:
                    bins = calculate_bin_count(df_clean['Value'], bin_method)
                    st.caption(f"Calculated Bins: {bins}")

            with st.expander("3. Plot Settings", expanded=False):
                plot_theme = st.selectbox("Theme:", ["plotly_white", "plotly_dark", "ggplot2", "seaborn"])
                bar_opacity = st.slider("Histogram Opacity", 0.1, 1.0, 0.6)
                line_width = st.slider("Fit Line Width", 1, 5, 2)

    # --- 2. MAIN DASHBOARD ---
    
    if df is not None and not df.empty:
        # Use cleaned data for analysis
        data_values = df_clean['Value'].values

        # --- A. EXPLORATORY DATA ANALYSIS (EDA) ---
        st.markdown("---")
        st.subheader("📊 Exploratory Data Analysis")
        
        # Metric Cards
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Count (N)", f"{len(df_clean)}")
        m2.metric("Mean", f"{np.mean(data_values):.3f}")
        
        # FIX: Use Sample Standard Deviation (ddof=1) to match standard statistical software
        m3.metric("Std. Dev", f"{np.std(data_values, ddof=1):.3f}")
        
        # FIX: Use bias=False to calculate Unbiased Skewness and Kurtosis (Sample stats)
        m4.metric("Skewness", f"{stats.skew(data_values, bias=False):.3f}")
        m5.metric("Kurtosis", f"{stats.kurtosis(data_values, bias=False):.3f}")

        # EDA Plots
        col_eda_1, col_eda_2 = st.columns([2, 1])
        
        with col_eda_1:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=data_values, nbinsx=bins, name="Data",
                marker_color='#5c7cfa', opacity=bar_opacity,
                histnorm='probability density'
            ))
            fig_hist.update_layout(title="Empirical Density Histogram", template=plot_theme, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with col_eda_2:
            fig_box = px.box(df_clean, y="Value", title="Box Plot")
            fig_box.update_traces(marker_color='#5c7cfa')
            fig_box.update_layout(template=plot_theme, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_box, use_container_width=True)

        # --- B. FITTING ENGINE ---
        st.markdown("---")
        st.subheader("🧩 Distribution Fitting")

        tab_auto, tab_manual, tab_qq = st.tabs(["🚀 Auto-Fit", "🎛️ Manual", "📉 Q-Q Plot"])
        
        dist_dict = get_supported_distributions()

        # >>> TAB 1: AUTO FIT <<<
        with tab_auto:
            col_opts, col_action = st.columns([3, 1])
            with col_opts:
                selected_dists = st.multiselect(
                    "Select Candidates:",
                    options=list(dist_dict.keys()),
                    default=["Normal", "Gamma", "Weibull (Min)", "Log-Normal", "Exponential"]
                )
            with col_action:
                st.write("") # Spacer
                st.write("") 
                run_fit = st.button("Recalculate Fit", type="secondary", use_container_width=True, help="Click to force a re-run")

            # --- AUTO-RUN LOGIC ---
            # 1. Create a state signature (Data Hash + Bins + Selected Dists)
            # We hash the dataframe values to detect data changes
            data_hash = pd.util.hash_pandas_object(df_clean['Value']).sum()
            current_state_id = (data_hash, bins, tuple(sorted(selected_dists)))

            # 2. Check if state has changed
            if 'last_state_id' not in st.session_state:
                st.session_state['last_state_id'] = None
                
            should_run = (current_state_id != st.session_state['last_state_id']) or run_fit
            
            # 3. Logic Execution
            if should_run:
                if not selected_dists:
                    st.warning("Please select at least one distribution to fit.")
                    st.session_state['fitting_results'] = None
                else:
                    results = []
                    
                    # Spinner prevents UI freezing feeling without feedback
                    with st.spinner("Fitting distributions to new data..."):
                        # Histogram prep for SSE calc
                        hist_counts, bin_edges = np.histogram(data_values, bins=bins, density=True)
                        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                        for name in selected_dists:
                            dist = dist_dict[name]
                            try:
                                # 1. Fit
                                params = dist.fit(data_values)
                                
                                # 2. Metrics
                                ks_stat, ks_p = stats.kstest(data_values, dist.name, args=params)
                                
                                # SSE
                                pdf_fitted = dist.pdf(bin_centers, *params)
                                pdf_fitted = np.nan_to_num(pdf_fitted) 
                                sse = np.sum((hist_counts - pdf_fitted) ** 2)
                                
                                # AIC & BIC
                                log_lik = np.sum(dist.logpdf(data_values, *params))
                                k = len(params)
                                n = len(data_values)
                                aic = 2*k - 2*log_lik
                                bic = k * np.log(n) - 2 * log_lik

                                results.append({
                                    "Distribution": name,
                                    "SSE": sse,
                                    "AIC": aic,
                                    "BIC": bic,
                                    "KS Stat": ks_stat,
                                    "P-Value": ks_p,
                                    "Parameters": params,
                                    "Object": dist
                                })
                            except Exception:
                                pass 
                        
                        # Save results and update state ID
                        if results:
                            st.session_state['fitting_results'] = pd.DataFrame(results)
                        else:
                            st.session_state['fitting_results'] = None
                            
                st.session_state['last_state_id'] = current_state_id

            # Display Results if they exist in state
            if st.session_state.get('fitting_results') is not None and not st.session_state['fitting_results'].empty:
                results_df = st.session_state['fitting_results']

                # Ranking Logic
                rank_metric = st.radio("Rank By:", ["SSE (Error)", "AIC (Info)", "BIC (Bayes)"], horizontal=True)
                sort_key = rank_metric.split()[0]
                
                results_df = results_df.sort_values(by=sort_key)
                best_fit = results_df.iloc[0]

                st.success(f"Best Fit: **{best_fit['Distribution']}** (Lowest {sort_key})")
                
                col_plot, col_stats = st.columns([2, 1])
                
                with col_plot:
                    fig_fit = go.Figure()
                    # Data Hist
                    fig_fit.add_trace(go.Histogram(
                        x=data_values, nbinsx=bins, histnorm='probability density',
                        name='Data', marker_color='#ced4da', opacity=0.6
                    ))
                    # Top 3 Lines
                    x_axis = np.linspace(min(data_values), max(data_values), 500)
                    colors = ['#228be6', '#fa5252', '#40c057'] # Blue, Red, Green
                    
                    for idx in range(min(3, len(results_df))):
                        row = results_df.iloc[idx]
                        y_vals = row['Object'].pdf(x_axis, *row['Parameters'])
                        fig_fit.add_trace(go.Scatter(
                            x=x_axis, y=y_vals, mode='lines',
                            name=f"{row['Distribution']}",
                            line=dict(width=3 if idx==0 else 2, color=colors[idx], dash='solid' if idx==0 else 'dot')
                        ))
                    
                    fig_fit.update_layout(title="Top Fits Visualization", xaxis_title="Value", yaxis_title="Density", template=plot_theme)
                    st.plotly_chart(fig_fit, use_container_width=True)

                with col_stats:
                    st.markdown("#### Leaderboard")
                    
                    display_df = results_df[['Distribution', 'SSE', 'AIC', 'BIC', 'P-Value']].copy()
                    
                    st.dataframe(
                        display_df.style.background_gradient(subset=[sort_key], cmap="Blues_r")\
                            .format("{:.4f}", subset=['SSE', 'AIC', 'BIC', 'P-Value']),
                        width="stretch",
                        height=400
                    )
                    
                    csv = results_df.drop(columns=['Object']).to_csv(index=False).encode('utf-8')
                    st.download_button("Download Report", csv, "fitting_results.csv", "text/csv")
                    
                    # Store best fit for Q-Q tab
                    st.session_state['best_fit_name'] = best_fit['Distribution']
                    st.session_state['best_fit_params'] = best_fit['Parameters']
                    st.session_state['best_fit_obj'] = best_fit['Object']

        # >>> TAB 2: MANUAL LAB <<<
        with tab_manual:
            man_col1, man_col2 = st.columns([1, 2])
            
            with man_col1:
                man_dist_name = st.selectbox("Distribution:", list(dist_dict.keys()))
                man_dist = dist_dict[man_dist_name]
                
                try:
                    init_params = man_dist.fit(data_values)
                except:
                    init_params = [1.0] * man_dist.numargs + [0.0, 1.0]

                curr_params = []
                arg_names = [f"Shape {i+1}" for i in range(man_dist.numargs)] + ["Loc", "Scale"]
                
                st.markdown("#### Parameters")
                for i, p_val in enumerate(init_params):
                    min_v = -5.0 if i >= len(init_params)-2 else 0.01
                    max_v = float(max(p_val * 3, 5.0))
                    val = st.slider(f"{arg_names[i]}", min_value=float(min_v), max_value=float(max_v), value=float(p_val), step=0.01, key=f"man_{i}")
                    curr_params.append(val)
                
                show_cdf = st.checkbox("Show CDF", value=False)

            with man_col2:
                fig_man = go.Figure()
                
                if not show_cdf:
                    fig_man.add_trace(go.Histogram(
                        x=data_values, nbinsx=bins, histnorm='probability density',
                        name='Data', marker_color='#ced4da', opacity=0.5
                    ))
                else:
                    sorted_data = np.sort(data_values)
                    y_cdf = np.arange(1, len(sorted_data)+1) / len(sorted_data)
                    fig_man.add_trace(go.Scatter(x=sorted_data, y=y_cdf, name='Empirical CDF', mode='lines', line=dict(color='gray', dash='dot')))

                x_axis = np.linspace(min(data_values), max(data_values), 500)
                try:
                    if show_cdf:
                        y_man = man_dist.cdf(x_axis, *curr_params)
                        title_t = f"{man_dist_name} CDF"
                    else:
                        y_man = man_dist.pdf(x_axis, *curr_params)
                        title_t = f"{man_dist_name} PDF"
                    
                    fig_man.add_trace(go.Scatter(
                        x=x_axis, y=y_man, mode='lines', name='Manual Fit',
                        line=dict(color='#228be6', width=3)
                    ))
                    
                    fig_man.update_layout(title=title_t, template=plot_theme)
                    st.plotly_chart(fig_man, use_container_width=True)
                except:
                    st.error("Invalid parameters.")

        # >>> TAB 3: Q-Q PLOT <<<
        with tab_qq:
            if 'best_fit_name' in st.session_state:
                bf_name = st.session_state['best_fit_name']
                bf_params = st.session_state['best_fit_params']
                bf_obj = st.session_state['best_fit_obj']
                
                (osm, osr), (slope, intercept, r) = stats.probplot(data_values, dist=bf_obj, sparams=bf_params, fit=True)
                
                fig_qq = go.Figure()
                fig_qq.add_trace(go.Scatter(
                    x=osm, y=osr, mode='markers', name='Data',
                    marker=dict(color='#228be6', size=6, opacity=0.7)
                ))
                
                x_line = np.array([min(osm), max(osm)])
                y_line = slope * x_line + intercept
                fig_qq.add_trace(go.Scatter(
                    x=x_line, y=y_line, mode='lines', name='Theoretical',
                    line=dict(color='#fa5252', width=2)
                ))
                
                fig_qq.update_layout(
                    title=f"Q-Q Plot vs {bf_name} (R²={r**2:.4f})",
                    xaxis_title="Theoretical Quantiles",
                    yaxis_title="Ordered Values",
                    template=plot_theme
                )
                st.plotly_chart(fig_qq, use_container_width=True)
            else:
                st.info("Run Auto-Fit Analysis to generate Q-Q Plot.")

    else:
        st.info("👋 **Welcome to DistroFit**\n\nUpload a dataset or load sample data from the sidebar to begin.")

if __name__ == "__main__":
    main()