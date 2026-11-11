import json

import numpy as np
import pytest

import bench_bootstrap
import gpu_bootstrap as gb
from analysis import get_supported_distributions

SUPPORTED = get_supported_distributions()


def _gpu_ready():
    return gb._gpu_available()


needs_gpu = pytest.mark.skipif(not _gpu_ready(), reason="no CUDA GPU with CuPy on this machine")


def _sample(n=300, seed=4):
    rng = np.random.default_rng(seed)
    return 50 * rng.weibull(1.8, n) + 1.


@pytest.mark.parametrize("name", gb.FAMILIES)
def test_kernel_formulas_match_scipy_for_every_family(name):
    """The CUDA kernel is a transliteration of standard_logpdf_reference, so checking that on the CPU checks the maths."""
    dist = SUPPORTED[name]
    rng = np.random.default_rng(9)
    shapes = {"Gamma": [2.3], "Weibull (Min)": [1.7], "Log-Normal": [0.6], "Beta": [2.5, 3.5],
              "Student's t": [4.], "Chi-Squared": [5.], "Pareto": [2.2]}.get(name, [])
    params = shapes + [0., 1.]
    z = dist.rvs(*params, size=400, random_state=rng)
    family = gb.FAMILIES.index(name)
    s1, s2 = (shapes + [0., 0.])[:2]
    expected = dist.logpdf(z, *params)
    got = gb.standard_logpdf_reference(family, z, s1, s2)
    assert np.allclose(got, expected, rtol=1e-10, atol=1e-10)


def test_kernel_formulas_return_negative_infinity_outside_support():
    assert gb.standard_logpdf_reference(5, np.array([-.1, .5, 1.2]), 2.5, 3.5)[0] == -np.inf
    assert gb.standard_logpdf_reference(6, np.array([1.5]))[0] == -np.inf
    assert gb.standard_logpdf_reference(10, np.array([0.5]), 2.)[0] == -np.inf


def test_all_fourteen_candidates_are_evaluated_on_positive_data():
    result = gb.bootstrap_loglik(_sample(), resamples=50, backend="cpu")
    assert len(result["table"]) + len(result["excluded"]) == 14
    assert set(result["table"]["distribution"]) <= set(gb.FAMILIES)
    assert result["table"]["distribution"].is_unique


def test_intervals_bracket_the_point_score_and_win_shares_sum_to_one():
    result = gb.bootstrap_loglik(_sample(), resamples=400, backend="cpu")
    table = result["table"]
    assert (table["boot_ci_low"] <= table["boot_ci_high"]).all()
    best = table.iloc[0]
    assert best["boot_ci_low"] <= best["mean_loglik"] <= best["boot_ci_high"]
    assert table["win_share"].sum() == pytest.approx(1.0)
    # Uniform's log-density is the same everywhere on its support, so its spread is exactly zero.
    assert table["boot_se"].ge(0).all()
    assert table.loc[table["distribution"] != "Uniform", "boot_se"].gt(0).all()


def test_results_repeat_for_the_same_seed():
    first = gb.bootstrap_loglik(_sample(), resamples=100, backend="cpu", seed=1)["table"]
    second = gb.bootstrap_loglik(_sample(), resamples=100, backend="cpu", seed=1)["table"]
    other = gb.bootstrap_loglik(_sample(), resamples=100, backend="cpu", seed=2)["table"]
    assert first.equals(second)
    assert not first["boot_ci_low"].equals(other["boot_ci_low"])


def test_auto_backend_falls_back_to_cpu_without_gpu(monkeypatch):
    monkeypatch.setattr(gb, "_gpu_available", lambda: False)
    result = gb.bootstrap_loglik(_sample(), resamples=20, backend="auto")
    assert result["backend"] == "cpu"


def test_explicit_gpu_request_fails_clearly_without_gpu(monkeypatch):
    monkeypatch.setattr(gb, "_gpu_available", lambda: False)
    with pytest.raises(RuntimeError, match="requirements-gpu.txt"):
        gb.bootstrap_loglik(_sample(), resamples=20, backend="gpu")


def test_bad_inputs_are_rejected():
    with pytest.raises(ValueError, match="backend"):
        gb.bootstrap_loglik(_sample(), backend="tpu")
    with pytest.raises(ValueError, match="finite"):
        gb.fit_candidates([1., np.nan, 2.])
    with pytest.raises(ValueError, match="resamples"):
        gb.bootstrap_loglik(_sample(), resamples=0)


@needs_gpu
@pytest.mark.parametrize("size", [100, 2000])
def test_gpu_and_cpu_loglik_agree(size):
    values = _sample(size)
    cpu = gb.bootstrap_loglik(values, resamples=200, backend="cpu")["table"].set_index("distribution")
    gpu = gb.bootstrap_loglik(values, resamples=200, backend="gpu")["table"].set_index("distribution")
    assert set(cpu.index) == set(gpu.index)
    assert np.allclose(cpu.loc[gpu.index, "boot_ci_low"], gpu["boot_ci_low"], rtol=1e-9, atol=1e-9)
    assert np.allclose(cpu.loc[gpu.index, "boot_ci_high"], gpu["boot_ci_high"], rtol=1e-9, atol=1e-9)


def test_benchmark_writes_a_report_without_gpu(tmp_path, monkeypatch):
    monkeypatch.setattr(gb, "_gpu_available", lambda: False)
    folder = bench_bootstrap.run([60, 120], resamples=20, repeats=1, out=tmp_path / "bench")
    report = json.loads((folder / "benchmark.json").read_text())
    assert [row["sample_size"] for row in report["results"]] == [60, 120]
    assert all(row["gpu_seconds"] is None for row in report["results"])
    assert all(row["cpu_seconds"] > 0 for row in report["results"])
    with pytest.raises(FileExistsError):
        bench_bootstrap.run([60], resamples=5, repeats=1, out=folder)
