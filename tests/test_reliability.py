"""Independent references and small, hand-calculated censored life tests."""
import json

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from reliability import (analyze_lifetimes, fit_life_model, kaplan_meier,
                         life_curves, validate_lifetimes)


def nist():
    # NIST 8.4.1.3: ten failures and ten suspensions at 500 hours.
    return pd.DataFrame({"time": [54, 187, 216, 240, 244, 335, 361, 373, 375, 386] + [500] * 10,
                         "failed": [1] * 10 + [0] * 10})


def test_nist_published_weibull_and_lognormal_results():
    fit = fit_life_model(nist(), "weibull")
    assert fit["parameters"]["shape"] == pytest.approx(1.7208, abs=.0001)
    assert fit["parameters"]["scale"] == pytest.approx(606.5280, abs=.01)
    assert fit["mean_life"]["estimate"] == pytest.approx(540.737, abs=.02)
    assert fit["log_likelihood"] == pytest.approx(-75.135, abs=.001)
    assert fit["aic"] == pytest.approx(154.27, abs=.01)
    assert fit_life_model(nist(), "lognormal")["aic"] == pytest.approx(154.39, abs=.01)


def test_exponential_censoring_uses_all_exposure_and_information_interval():
    # Exposure=10+20+30=60; two failures => mean=30, not failure-only mean=15.
    table = pd.DataFrame({"time": [10, 20, 30], "failed": [1, 1, 0]})
    fit = fit_life_model(table, "exponential")
    assert fit["mean_life"]["estimate"] == pytest.approx(30)
    assert fit["b10"]["estimate"] == pytest.approx(3.1608154697)
    # Information for log mean is d=2, so SE(log mean)=1/sqrt(2).
    assert fit["mean_life"]["lower"] == pytest.approx(7.5029295978, rel=1e-5)
    assert fit["mean_life"]["upper"] == pytest.approx(119.9531447375, rel=1e-5)
    assert fit["log_likelihood"] == pytest.approx(-2 * np.log(30) - 2)
    values = life_curves(fit, [0, 10, 30])
    assert values["survival"] == pytest.approx([1, .7165313106, .3678794412])
    assert values["hazard"] == pytest.approx([1 / 30] * 3)


def test_km_ties_keep_suspensions_in_failure_risk_set():
    table = pd.DataFrame({"time": [1, 2, 2, 4], "failed": [1, 1, 0, 1]})
    km = kaplan_meier(table)
    assert km.time.tolist() == [0, 1, 2, 4]
    assert km.at_risk.tolist() == [4, 4, 3, 1]
    assert km.survival.tolist() == pytest.approx([1, .75, .5, 0])
    assert km.failures.tolist() == [0, 1, 1, 1]
    assert km.suspended.tolist() == [0, 0, 1, 0]
    assert km.lower.iloc[1] == pytest.approx(.1279469176)
    assert km.upper.iloc[1] == pytest.approx(.9605486423)
    assert km.lower.iloc[-1] == km.upper.iloc[-1] == 0


@pytest.mark.parametrize("model", ["weibull", "lognormal", "exponential"])
def test_unit_scaling_order_and_confidence_changes(model):
    original = fit_life_model(nist(), model)
    scaled = nist().sample(frac=1, random_state=3)
    scaled["time"] = scaled["time"] * 1e-9
    converted = fit_life_model(scaled, model)
    wider = fit_life_model(nist(), model, confidence=.99)
    for metric in ["mean_life", "b10"]:
        for key in ["estimate", "lower", "upper"]:
            assert converted[metric][key] / 1e-9 == pytest.approx(original[metric][key], rel=2e-5)
        assert wider[metric]["lower"] < original[metric]["lower"] < original[metric]["estimate"]
        assert wider[metric]["upper"] > original[metric]["upper"] > original[metric]["estimate"]


@pytest.mark.parametrize("model,distribution", [("weibull", stats.weibull_min), ("lognormal", stats.lognorm)])
def test_mle_matches_independent_scipy_censored_fit(model, distribution):
    rng = np.random.default_rng(19)
    actual = rng.lognormal(5, .65, 300)
    censor = rng.uniform(80, 260, 300)
    table = pd.DataFrame({"time": np.minimum(actual, censor), "failed": (actual <= censor).astype(int)})
    fit = fit_life_model(table, model)
    sample = stats.CensoredData(uncensored=table.time[table.failed == 1], right=table.time[table.failed == 0])
    shape, _, scale = distribution.fit(sample, floc=0)
    assert fit["parameters"]["shape"] == pytest.approx(shape, rel=2e-4)
    assert fit["parameters"]["scale"] == pytest.approx(scale, rel=2e-4)
    assert fit["mean_life"]["estimate"] == pytest.approx(distribution.mean(shape, scale=scale), rel=2e-4)


def test_complete_lognormal_matches_closed_form_and_weibull_hazard_increases():
    table = pd.DataFrame({"time": np.exp([1., 2., 3., 4.]), "failed": [1] * 4})
    fit = fit_life_model(table, "lognormal")
    assert fit["parameters"]["shape"] == pytest.approx(np.sqrt(1.25))
    assert fit["parameters"]["scale"] == pytest.approx(np.exp(2.5))
    weibull = fit_life_model(nist(), "weibull")
    curves = life_curves(weibull, [10, 100, 300])
    assert np.all(np.diff(curves["survival"]) < 0)
    assert np.all(np.diff(curves["hazard"]) > 0)


@pytest.mark.parametrize("values", [
    [], [{"time": 0, "failed": 1}], [{"time": -1, "failed": 0}],
    [{"time": np.inf, "failed": 1}], [{"time": np.nan, "failed": 0}],
    [{"time": True, "failed": 1}], [{"time": "ten", "failed": 0}],
    [{"time": 1, "failed": "running"}], [{"time": 1, "failed": 2}],
    [{"time": 1, "failed": .5}], [{"time": 1, "failed": None}],
    [{"age": 1, "failed": 1}],
])
def test_invalid_rows_are_rejected_without_dropping_them(values):
    with pytest.raises(ValueError):
        validate_lifetimes(values)


def test_duplicate_columns_and_boolean_times_rejected():
    with pytest.raises(ValueError):
        validate_lifetimes(pd.DataFrame([[1, 2, 1]], columns=["time", "time", "failed"]))
    with pytest.raises(ValueError):
        validate_lifetimes(pd.DataFrame({"time": [True, 5], "failed": [1, 0]}, dtype=object))


def test_all_suspended_and_sparse_data_never_invent_fits():
    table = pd.DataFrame({"time": [10, 20, 30], "failed": [0, 0, 0]})
    result = analyze_lifetimes(table)
    assert not result["fits"]
    assert len(result["excluded"]) == 3
    assert all(row["survival"] == 1 for row in result["kaplan_meier"])
    assert result["summary"] == {"units": 3, "failures": 0, "suspensions": 3, "total_time": 60.0}
    for model in ("weibull", "lognormal"):
        with pytest.raises(ValueError, match="distinct"):
            fit_life_model(pd.DataFrame({"time": [10, 10, 20], "failed": [1, 1, 0]}), model)
    single = analyze_lifetimes(pd.DataFrame({"time": [10, 20], "failed": [1, 0]}))
    assert [fit["model"] for fit in single["fits"]] == ["exponential"]
    assert single["warnings"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("confidence", [0, 1, -.5, np.nan, True])
def test_bad_confidence_rejected(confidence):
    with pytest.raises(ValueError):
        analyze_lifetimes(nist(), confidence=confidence)


def test_report_is_sorted_and_json_safe_and_km_pure_suspension_does_not_drop():
    report = analyze_lifetimes(nist())
    assert [f["aic"] for f in report["fits"]] == sorted(f["aic"] for f in report["fits"])
    assert report["confidence"] == .95
    json.dumps(report, allow_nan=False)
    km = kaplan_meier(pd.DataFrame({"time": [1, 2, 3], "failed": [1, 0, 0]}))
    assert km.survival.tolist() == pytest.approx([1, 2/3, 2/3, 2/3])


def test_weibull_hazard_does_not_cancel_when_survival_underflows():
    # Direct Weibull formula: (500/100) * (120/100)**499.
    fit = {"model": "weibull", "parameters": {"shape": 500., "scale": 100.}}
    curves = life_curves(fit, [120])
    assert curves["survival"][0] == 0
    assert curves["hazard"][0] == pytest.approx(1.623348567461589e40, rel=1e-10)


@pytest.mark.parametrize("shape,expected", [(.5, np.inf), (1., .01), (2., 0.)])
def test_weibull_hazard_at_zero_handles_each_shape(shape, expected):
    fit = {"model": "weibull", "parameters": {"shape": shape, "scale": 100.}}
    assert life_curves(fit, [0])["hazard"][0] == pytest.approx(expected)
