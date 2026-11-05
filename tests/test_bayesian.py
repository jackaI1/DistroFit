"""Real NUTS recovery and checks which reject misleading sampled results."""
import importlib
import json
from pathlib import Path

import arviz as az
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from scipy.special import logsumexp


@pytest.fixture(scope="session")
def core():
    assert importlib.util.find_spec("bayesian") is not None, "Grouped Bayesian fitting is missing"
    return importlib.import_module("bayesian")


@pytest.fixture(scope="session")
def recovered(core):
    rng = np.random.default_rng(2026)
    table = pd.concat([pd.DataFrame({"group": name, "value": rng.normal(mean, 1.2, n)})
                       for name, mean, n in zip("ABCDE", [49, 49.5, 50, 50.5, 50], [72, 60, 48, 36, 12])],
                      ignore_index=True)
    return core.fit_grouped(table, seed=42, draws=1500, tune=1500)


def test_recovers_known_means_noise_and_partial_pooling(recovered):
    comparison = recovered["comparison"].set_index("group")
    covered = 0
    for name, truth in zip("ABCDE", [49, 49.5, 50, 50.5, 50]):
        row = comparison.loc[name]
        covered += int(row.mean_lower < truth < row.mean_upper)
        # Known simulation noise gives an independent, sample-size-aware recovery
        # tolerance. A 95% interval is not guaranteed to cover every small batch.
        assert abs(row.bayes_mean - truth) < 3 * 1.2 / np.sqrt(row.n_train)
    assert covered >= 4
    sigma = recovered["inference"].posterior.sigma.values
    assert np.quantile(sigma, .025) < 1.2 < np.quantile(sigma, .975)
    population = recovered["inference"].posterior.population_mean.values.mean()
    small = comparison.loc["E"]
    assert abs(small.bayes_mean - population) < abs(small.mle_mean - population)
    assert recovered["diagnostics"]["passed"], recovered["diagnostics"]


def test_same_rows_and_true_mixture_predictive_score(recovered):
    data, inference = recovered["data"], recovered["inference"]
    train, held = recovered["train_indices"], recovered["held_indices"]
    assert not set(train) & set(held)
    assert sorted([*train, *held]) == list(range(len(data)))
    for row in recovered["comparison"].itertuples():
        training = data.iloc[train].query("group == @row.group").value.to_numpy()
        checking = data.iloc[held].query("group == @row.group").value.to_numpy()
        assert row.mle_mean == pytest.approx(training.mean())
        assert row.mle_sd == pytest.approx(training.std())
        assert row.mle_held_nll == pytest.approx(-stats.norm.logpdf(checking, training.mean(), training.std()).mean())
        mu = inference.posterior.group_mean.sel(group=row.group).values.ravel()
        sigma = inference.posterior.sigma.values.ravel()
        log_density = stats.norm.logpdf(checking[:, None], mu, sigma)
        expected = -(logsumexp(log_density, axis=1) - np.log(len(mu))).mean()
        assert row.bayes_held_nll == pytest.approx(expected)


def test_prior_and_posterior_checks_are_sampled_in_measurement_units(recovered):
    inference = recovered["inference"]
    assert {"prior", "prior_predictive", "posterior", "posterior_predictive", "sample_stats"} <= set(inference.groups())
    training = recovered["data"].iloc[recovered["train_indices"]]
    posterior = inference.posterior_predictive.measurement.values
    assert posterior.shape[-1] == len(training)
    assert 45 < posterior.mean() < 55
    assert inference.prior_predictive.measurement.values.std() > posterior.std()
    checks = recovered["predictive_checks"]
    assert len(checks) == 15  # mean, SD and maximum for each group
    for row in checks.itertuples():
        values = training.loc[training.group == row.group, "value"].to_numpy()
        expected = {"mean": values.mean(), "sd": values.std(), "maximum": values.max()}[row.statistic]
        assert row.observed == pytest.approx(expected)
        assert 0 <= row.posterior_upper_probability <= 1
        assert row.posterior_lower < row.posterior_upper


@pytest.mark.parametrize("problem", ["shifted", "constant", "short", "divergent", "missing", "nan"])
def test_bad_diagnostics_fail_closed(core, problem):
    rng = np.random.default_rng(6)
    samples = rng.normal(size=(4, 1000))
    divergent = np.zeros((4, 1000), dtype=bool)
    if problem == "shifted":
        samples[2:] += 8
    elif problem == "constant":
        samples[:] = 1
    elif problem == "short":
        samples = samples[:, :20]
        divergent = divergent[:, :20]
    elif problem == "divergent":
        divergent[0, 0] = True
    elif problem == "nan":
        samples[0, 0] = np.nan
    inference = az.from_dict(posterior={"theta": samples},
                             sample_stats=None if problem == "missing" else {"diverging": divergent})
    diagnostics = core.convergence_diagnostics(inference)
    assert not diagnostics["passed"]
    assert diagnostics["issues"]
    with pytest.raises(core.ConvergenceError):
        core.require_convergence(diagnostics)


def test_well_mixed_draws_pass_with_unrounded_metrics(core):
    inference = az.from_dict(posterior={"theta": np.random.default_rng(5).normal(size=(4, 1500))},
                             sample_stats={"diverging": np.zeros((4, 1500), dtype=bool)})
    diagnostics = core.convergence_diagnostics(inference)
    assert diagnostics["passed"]
    assert diagnostics["max_rhat"] <= 1.01
    assert diagnostics["min_ess_bulk"] >= 400
    assert diagnostics["min_ess_tail"] >= 400
    assert diagnostics["divergences"] == 0


@pytest.mark.parametrize("change", ["one_group", "few_rows", "constant_group", "missing_group", "missing_value", "infinite", "numeric_text", "too_large"])
def test_invalid_grouped_inputs_are_rejected_before_sampling(core, change):
    data = core.generate_demo()
    if change == "one_group":
        data["group"] = "only"
    elif change == "few_rows":
        data = pd.concat([data[data.group != "Batch D"], data[data.group == "Batch D"].head(7)])
    elif change == "constant_group":
        data.loc[data.group == "Batch D", "value"] = 4
    elif change == "missing_group":
        data.loc[0, "group"] = None
    elif change == "missing_value":
        data.loc[0, "value"] = np.nan
    elif change == "infinite":
        data.loc[0, "value"] = np.inf
    elif change == "numeric_text":
        data["value"] = data.value.astype(str)
    else:
        data = pd.concat([data] * 30)
    with pytest.raises(ValueError):
        core.fit_grouped(data)


def test_demo_export_contains_reusable_draws_and_plotly(core, recovered, tmp_path):
    pd.testing.assert_frame_equal(core.generate_demo(), pd.read_csv(Path(__file__).resolve().parents[1] / "examples/bayesian/grouped_measurements.csv"))
    assert len(core.generate_demo()) == 80
    core.export_report(recovered, tmp_path / "report")
    payload = json.loads((tmp_path / "report/report.json").read_text())
    assert payload["diagnostics"]["passed"]
    assert payload["settings"]["seed"] == 42
    assert (tmp_path / "report/posterior.nc").stat().st_size > 10000
    assert len(pd.read_csv(tmp_path / "report/comparison.csv")) == 5
    assert "plotly" in (tmp_path / "report/posteriors.html").read_text().lower()
    figure = core.posterior_figure(recovered)
    assert len(figure.data) >= 6
    predictive = core.predictive_figure(recovered, "E")
    assert len(predictive.data) == 4
    with pytest.raises(FileExistsError):
        core.export_report(recovered, tmp_path / "report")


def test_autocorrelated_draws_fail_effective_sample_size(core):
    rng = np.random.default_rng(19)
    innovations = rng.normal(size=(4, 2000))
    samples = np.zeros_like(innovations)
    for i in range(1, samples.shape[1]):
        samples[:, i] = .999 * samples[:, i - 1] + innovations[:, i]
    inference = az.from_dict(posterior={"theta": samples},
                             sample_stats={"diverging": np.zeros_like(samples, dtype=bool)})
    checks = core.convergence_diagnostics(inference)
    assert not checks["passed"]
    assert checks["min_ess_bulk"] < 400
    assert any("effective sample size" in issue for issue in checks["issues"])


def test_cli_rejects_invalid_csv_and_existing_output_without_sampling(tmp_path):
    import subprocess
    import sys
    script = Path(__file__).resolve().parents[1] / "bayesian.py"
    csv = tmp_path / "bad.csv"
    csv.write_text("group,value\nA,5\n")
    output = tmp_path / "result"
    result = subprocess.run([sys.executable, str(script), str(csv), "--out", str(output)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert not output.exists()
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("original")
    result = subprocess.run([sys.executable, str(script), "--sample", "--out", str(output)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert sentinel.read_text() == "original"


def test_complex_readings_are_rejected_without_discarding_imaginary_parts(core):
    data = core.generate_demo()
    data['value'] = data.value.astype(complex) + 2j
    with pytest.raises(ValueError, match="finite number"):
        core.validate_grouped(data)


def test_real_undersampled_fit_raises_instead_of_returning_estimates(core):
    # Removing the fit-level gate must break this test, even if the standalone
    # diagnostic helper still correctly flags low information.
    with pytest.raises(core.ConvergenceError, match="Sampling checks failed"):
        core.fit_grouped(core.generate_demo(), draws=100, tune=100, chains=2)
