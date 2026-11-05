"""Partially pooled normal measurements, shared-split MLE comparison and checks.

Only independent, exchangeable groups with a common within-group spread are modeled.
See docs/bayesian.md for priors, interpretation and limitations.
"""
import argparse
import json
from pathlib import Path
import warnings

import arviz as az
import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import logsumexp

from analysis import fit_candidates


class ConvergenceError(ValueError):
    """The sampled estimates have not met the diagnostic gate."""


def generate_demo(seed=27):
    """80 synthetic measurements, including a batch with only eight readings."""
    rng = np.random.default_rng(seed)
    return pd.concat([pd.DataFrame({"group": f"Batch {name}", "value": rng.normal(mean, 1.3, n)})
                      for name, mean, n in zip("ABCD", [49.5, 50, 50.5, 50], [32, 24, 16, 8])],
                     ignore_index=True)


def validate_grouped(table):
    """Reject incomplete rows rather than silently change the population."""
    if not isinstance(table, pd.DataFrame) or not {"group", "value"} <= set(table.columns):
        raise ValueError("Provide group and value columns.")
    data = table[["group", "value"]].copy().reset_index(drop=True)
    if not 16 <= len(data) <= 2000:
        raise ValueError("Provide 16 to 2000 rows, with at least eight per group.")
    if (data.group.isna().any() or not data.group.map(lambda x: isinstance(x, str) and bool(x.strip())).all()):
        raise ValueError("Every group must have a non-empty text label.")
    if (not pd.api.types.is_numeric_dtype(data.value) or pd.api.types.is_bool_dtype(data.value)
            or pd.api.types.is_complex_dtype(data.value)
            or not np.isfinite(data.value.to_numpy(dtype=float)).all()):
        raise ValueError("Every value must be a finite number; no rows are dropped.")
    if not 2 <= data.group.nunique() <= 20:
        raise ValueError("Provide between two and twenty related groups.")
    for name, group in data.groupby("group", sort=False):
        if len(group) < 8 or group.value.std(ddof=0) <= 0:
            raise ValueError(f"Group {name!r} needs at least eight varying measurements.")
    data["value"] = data.value.astype(float)
    return data


def convergence_diagnostics(inference):
    """Fail closed on absent/non-finite diagnostics, bad mixing or divergences.

    Uses unrounded rank-normalized split R-hat and bulk/tail ESS for every
    posterior variable, including the non-centred offsets and hyperparameters.
    """
    result = {"passed": False, "issues": [], "max_rhat": None, "min_ess_bulk": None,
              "min_ess_tail": None, "divergences": None, "parameters": [],
              "thresholds": {"max_rhat": 1.01, "min_ess": 400, "max_divergences": 0}}
    if "posterior" not in inference.groups():
        result["issues"].append("Posterior draws are missing.")
        return result
    posterior = inference.posterior
    if posterior.sizes.get("chain", 0) < 2 or posterior.sizes.get("draw", 0) < 100:
        result["issues"].append("At least two chains and 100 retained draws per chain are required.")
    if any(not np.isfinite(v.values).all() for v in posterior.data_vars.values()):
        result["issues"].append("Posterior draws contain non-finite values.")
    if not result["issues"]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # constant draws are rejected below
            summary = az.summary(inference, kind="diagnostics", round_to="none")
        columns = ["r_hat", "ess_bulk", "ess_tail"]
        if summary.empty or not np.isfinite(summary[columns].to_numpy()).all():
            result["issues"].append("R-hat or effective sample size is missing or non-finite.")
        else:
            result.update(max_rhat=float(summary.r_hat.max()), min_ess_bulk=float(summary.ess_bulk.min()),
                          min_ess_tail=float(summary.ess_tail.min()))
            result["parameters"] = summary.reset_index(names="parameter").to_dict("records")
            if result["max_rhat"] > 1.01:
                result["issues"].append("R-hat exceeds 1.01; chains disagree.")
            if min(result["min_ess_bulk"], result["min_ess_tail"]) < 400:
                result["issues"].append("Bulk or tail effective sample size is below 400.")
    if "sample_stats" not in inference.groups() or "diverging" not in inference.sample_stats:
        result["issues"].append("Divergence diagnostics are missing.")
    else:
        divergences = inference.sample_stats.diverging.values
        expected = (posterior.sizes.get("chain", 0), posterior.sizes.get("draw", 0))
        if divergences.shape != expected or not np.isin(divergences, [0, 1]).all():
            result["issues"].append("Divergence diagnostics have invalid shape or values.")
        else:
            result["divergences"] = int(divergences.sum())
            if result["divergences"]:
                result["issues"].append(f"{result['divergences']} divergent transitions were found.")
    result["passed"] = not result["issues"]
    return result


def require_convergence(diagnostics):
    if not diagnostics["passed"]:
        raise ConvergenceError("Sampling checks failed: " + " ".join(diagnostics["issues"]))


def _predictive_checks(inference, training):
    rows = []
    prior = inference.prior_predictive.measurement.values.reshape(-1, len(training))
    posterior = inference.posterior_predictive.measurement.values.reshape(-1, len(training))
    for group in training.group.unique():
        mask = (training.group == group).to_numpy()
        observed = training.value.to_numpy()[mask]
        for name, function in [("mean", np.mean), ("sd", np.std), ("maximum", np.max)]:
            value = float(function(observed))
            row = {"group": group, "statistic": name, "observed": value}
            for phase, draws in [("prior", prior), ("posterior", posterior)]:
                replicated = function(draws[:, mask], axis=1)
                low, high = np.quantile(replicated, [.025, .975])
                row.update({f"{phase}_lower": float(low), f"{phase}_upper": float(high),
                            f"{phase}_upper_probability": float(np.mean(replicated >= value))})
            row["posterior_flagged"] = not row["posterior_lower"] <= value <= row["posterior_upper"]
            rows.append(row)
    return pd.DataFrame(rows)


def fit_grouped(table, *, seed=42, draws=1500, tune=1500, chains=4,
                target_accept=.95, prior_draws=300, strict=True):
    """Fit on each group's training rows; holdouts never enter the model or priors.

    Default strict mode refuses an unreliable fit. strict=False returns diagnostics
    for display/review, and must never be interpreted as passing convergence.
    All chains run sequentially, with one BLAS thread, to bound resource use.
    """
    data = validate_grouped(table)
    for name, value, low, high in [("draws", draws, 100, 5000), ("tune", tune, 100, 5000),
                                   ("chains", chains, 2, 4), ("prior_draws", prior_draws, 100, 1000)]:
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or not low <= value <= high:
            raise ValueError(f"{name} must be an integer between {low} and {high}.")
    if not np.isfinite(target_accept) or not .8 <= target_accept < 1:
        raise ValueError("target_accept must be between 0.8 and 1 (exclusive).")
    train_indices, held_indices, mle = [], [], []
    labels = list(data.group.unique())
    for label in labels:
        positions = data.index[data.group == label].to_numpy()
        fit = fit_candidates(data.loc[positions, "value"], ["Normal"], seed=seed)
        if not fit["results"]:
            raise ValueError(f"Group {label!r} has no valid training normal fit: {fit['errors']}")
        train_indices.extend(positions[fit["train_indices"]])
        held_indices.extend(positions[fit["held_indices"]])
        mle.append(fit["results"][0])
    training = data.iloc[train_indices].reset_index(drop=True)
    center, scale = float(training.value.mean()), float(training.value.std(ddof=0))
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Training measurements must have a finite positive spread.")
    index = pd.Categorical(training.group, categories=labels).codes
    import pymc as pm
    with pm.Model(coords={"group": labels, "observation": np.arange(len(training))}) as model:
        # Train-calibrated, weakly informative priors in standardized units.
        mu = pm.Normal("mu_standard", 0, 2)
        tau = pm.HalfNormal("tau_standard", 1)
        noise = pm.HalfNormal("sigma_standard", 1)
        z = pm.Normal("offset", 0, 1, dims="group")
        population = pm.Deterministic("population_mean", center + scale * mu)
        pm.Deterministic("between_group_sd", scale * tau)
        means = pm.Deterministic("group_mean", population + scale * tau * z, dims="group")
        sigma = pm.Deterministic("sigma", scale * noise)
        pm.Normal("measurement", means[index], sigma, observed=training.value.to_numpy(), dims="observation")
        prior = pm.sample_prior_predictive(draws=prior_draws, random_seed=seed)
        inference = pm.sample(draws=draws, tune=tune, chains=chains, cores=1, blas_cores=1,
                              target_accept=target_accept, random_seed=seed,
                              nuts_sampler="pymc", progressbar=False, return_inferencedata=True)
        pm.sample_posterior_predictive(inference, random_seed=seed + 1, extend_inferencedata=True,
                                       progressbar=False)
    inference.extend(prior)
    diagnostics = convergence_diagnostics(inference)
    if strict:
        require_convergence(diagnostics)
    rows = []
    sigma_draws = inference.posterior.sigma.values.ravel()
    for label, fit in zip(labels, mle):
        means = inference.posterior.group_mean.sel(group=label).values.ravel()
        low, high = np.quantile(means, [.025, .975])
        held = data.iloc[held_indices].loc[lambda x: x.group == label, "value"].to_numpy()
        # Integrate uncertainty: log of the average density, not average log density.
        log_density = stats.norm.logpdf(held[:, None], means, sigma_draws)
        predictive_nll = float(-(logsumexp(log_density, axis=1) - np.log(len(means))).mean())
        rows.append({"group": label, "n_train": int((training.group == label).sum()), "n_held": len(held),
                     "mle_mean": fit["Parameters"][0], "mle_sd": fit["Parameters"][1],
                     "bayes_mean": float(means.mean()), "mean_lower": float(low), "mean_upper": float(high),
                     "mle_held_nll": fit["Held-out NLL"], "bayes_held_nll": predictive_nll})
    return {"inference": inference, "data": data, "train_indices": np.asarray(train_indices),
            "held_indices": np.asarray(held_indices), "comparison": pd.DataFrame(rows),
            "predictive_checks": _predictive_checks(inference, training), "diagnostics": diagnostics,
            "settings": {"seed": seed, "draws": draws, "tune": tune, "chains": chains,
                         "target_accept": target_accept, "prior_draws": prior_draws, "held_fraction": .25,
                         "training_center": center, "training_scale": scale, "credible_mass": .95,
                         "pymc": pm.__version__, "arviz": az.__version__}}


def posterior_figure(result):
    """Group mean distributions and unpooled MLE markers in original units."""
    import plotly.graph_objects as go
    figure = go.Figure()
    for row in result["comparison"].itertuples():
        samples = result["inference"].posterior.group_mean.sel(group=row.group).values.ravel()
        samples = samples[::max(1, len(samples) // 1000)]
        figure.add_trace(go.Violin(x=samples, y=[row.group] * len(samples), orientation="h",
                                  name=row.group, line_color="#2563a6", showlegend=False,
                                  meanline_visible=True, points=False, spanmode="hard"))
    comparison = result["comparison"]
    figure.add_trace(go.Scatter(x=comparison.mle_mean, y=comparison.group, mode="markers",
                                name="Independent MLE mean", marker={"symbol": "x", "color": "#505050", "size": 12}))
    figure.add_trace(go.Scatter(x=comparison.bayes_mean, y=comparison.group, mode="markers",
                                name="Posterior mean and 95% credible interval", marker_color="#2563a6",
                                error_x={"type": "data", "symmetric": False,
                                         "array": comparison.mean_upper - comparison.bayes_mean,
                                         "arrayminus": comparison.bayes_mean - comparison.mean_lower}))
    figure.update_layout(template="plotly_white", xaxis_title="Group mean (measurement units)",
                         yaxis_title="Group", height=max(350, 70 * len(comparison)), violinmode="overlay",
                         legend={"orientation": "h", "y": 1.2}, margin={"t": 80})
    return figure


def predictive_figure(result, group):
    """Prior/posterior replicated measurements, training histogram and MLE."""
    import plotly.graph_objects as go
    training = result["data"].iloc[result["train_indices"]]
    mask = (training.group == group).to_numpy()
    if not mask.any():
        raise ValueError("Choose a group in this fit.")
    observed = training.value.to_numpy()[mask]
    inference = result["inference"]
    figure = go.Figure()
    figure.add_trace(go.Histogram(x=observed, histnorm="probability density", name="Training readings",
                                  marker_color="#a0a0a0", opacity=.45, nbinsx=15))
    for phase, color in [("prior", "#b06012"), ("posterior", "#2563a6")]:
        samples = getattr(inference, f"{phase}_predictive").measurement.values[..., mask].ravel()
        # Bound rendering payload; the numerical checks use every sample.
        samples = samples[::max(1, len(samples) // 100000)]
        density, edges = np.histogram(samples, bins=100, density=True)
        figure.add_trace(go.Scatter(x=(edges[:-1] + edges[1:]) / 2, y=density,
                                    name=f"{phase.capitalize()} predictive", line_color=color))
    row = result["comparison"].set_index("group").loc[group]
    x = np.linspace(observed.min() - 3 * row.mle_sd, observed.max() + 3 * row.mle_sd, 200)
    figure.add_trace(go.Scatter(x=x, y=stats.norm.pdf(x, row.mle_mean, row.mle_sd), name="Independent MLE",
                                line={"color": "#505050", "dash": "dash"}))
    figure.update_layout(template="plotly_white", xaxis_title="Measurement value", yaxis_title="Density",
                         legend={"orientation": "h", "y": 1.2}, margin={"t": 80})
    return figure


def export_report(result, output):
    """Save diagnostics, split membership, posterior draws and standalone charts."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    data = result["data"].copy()
    data["role"] = "held-out"
    data.loc[result["train_indices"], "role"] = "training"
    data.to_csv(output / "observations.csv", index=False)
    result["comparison"].to_csv(output / "comparison.csv", index=False)
    result["predictive_checks"].to_csv(output / "predictive_checks.csv", index=False)
    pd.DataFrame(result["diagnostics"]["parameters"]).to_csv(output / "diagnostics.csv", index=False)
    payload = {"settings": result["settings"], "diagnostics": result["diagnostics"],
               "comparison": result["comparison"].to_dict("records"),
               "predictive_checks": result["predictive_checks"].to_dict("records")}
    (output / "report.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    result["inference"].to_netcdf(output / "posterior.nc", engine="h5netcdf")
    posterior_figure(result).write_html(output / "posteriors.html", include_plotlyjs=True)
    predictive_figure(result, result["comparison"].group.iloc[-1]).write_html(
        output / "predictive.html", include_plotlyjs=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("csv", nargs="?", type=Path, help="CSV with group and value columns")
    source.add_argument("--sample", action="store_true")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise FileExistsError("Output already exists; choose a new folder.")
        result = fit_grouped(generate_demo() if args.sample else pd.read_csv(args.csv))
        export_report(result, args.out)
    except (ValueError, OSError, pd.errors.ParserError) as error:
        parser.exit(2, f"{error}\n")
    checks = result["diagnostics"]
    print(f"{len(result['data'])} readings; R-hat {checks['max_rhat']:.4f}; "
          f"minimum bulk ESS {checks['min_ess_bulk']:.0f}; minimum tail ESS {checks['min_ess_tail']:.0f}; "
          f"{checks['divergences']} divergences. Saved {args.out}")


if __name__ == "__main__":
    main()
