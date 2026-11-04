"""Right-censored, zero-location life models for independent equipment lifetimes.

Failures contribute log density; suspensions contribute log survival. No histogram,
outlier removal, or train/test split is applied to these exposure records.
"""
from numbers import Real

import numpy as np
import pandas as pd
from scipy import optimize, special, stats

MODELS = ("weibull", "lognormal", "exponential")


def _confidence(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not 0 < value < 1:
        raise ValueError("Confidence must be a finite number between 0 and 1.")
    return float(stats.norm.ppf((1 + value) / 2))


def validate_lifetimes(table):
    """Return positive observed ages and binary failure flags; never drop bad rows."""
    frame = pd.DataFrame(table)
    if not frame.columns.is_unique or not {"time", "failed"}.issubset(frame.columns):
        raise ValueError("Use unique columns named time and failed (1=failure, 0=suspension).")
    if frame.empty:
        raise ValueError("Enter at least one lifetime.")
    if any(isinstance(value, (bool, np.bool_)) for value in frame["time"]):
        raise ValueError("Time must be a finite positive number, not a boolean.")
    try:
        times = pd.to_numeric(frame["time"], errors="raise").to_numpy(dtype=float)
        flags = pd.to_numeric(frame["failed"], errors="raise").to_numpy(dtype=float)
    except (ValueError, TypeError) as error:
        raise ValueError("Time must be numeric; failed must be 1 or 0.") from error
    if not np.all(np.isfinite(times) & (times > 0)) or not np.isfinite(times.sum()):
        raise ValueError("Every time and the total exposure must be finite and positive.")
    if not np.all(np.isin(flags, [0, 1])):
        raise ValueError("Every failed flag must be 1 (failure) or 0 (suspension).")
    return times, flags.astype(bool)


def kaplan_meier(table, confidence=.95):
    """Product-limit survival with risk counts and log-log Greenwood pointwise bounds.

    A suspension at a failure age remains in that age's pre-event risk set.
    The time-zero row anchors step plots and does not count as an observation.
    """
    z = _confidence(confidence)
    times, failed = validate_lifetimes(table)
    ages, inverse, counts = np.unique(times, return_inverse=True, return_counts=True)
    deaths = np.bincount(inverse, weights=failed, minlength=len(ages)).astype(int)
    risk = len(times)
    survival, greenwood = 1., 0.
    rows = [dict(time=0., at_risk=risk, failures=0, suspended=0, survival=1., lower=1., upper=1.)]
    for age, count, death in zip(ages, counts, deaths):
        if death:
            survival *= 1 - death / risk
            if risk > death:
                greenwood += death / (risk * (risk - death))
        lower = upper = survival
        if 0 < survival < 1:
            se = np.sqrt(greenwood) / abs(np.log(survival))
            center = np.log(-np.log(survival))
            with np.errstate(over="ignore"):
                lower = np.exp(-np.exp(center + z * se))
                upper = np.exp(-np.exp(center - z * se))
        rows.append(dict(time=float(age), at_risk=int(risk), failures=int(death),
                         suspended=int(count - death), survival=float(survival),
                         lower=float(lower), upper=float(upper)))
        risk -= count
    return pd.DataFrame(rows)


def _information(nll, theta):
    """Central differences in dimensionless log parameters, at the MLE."""
    step = 1e-4
    matrix = np.empty((len(theta), len(theta)))
    center = nll(theta)
    directions = np.eye(len(theta)) * step
    for i, ei in enumerate(directions):
        matrix[i, i] = (nll(theta + ei) - 2 * center + nll(theta - ei)) / step**2
        for j in range(i):
            ej = directions[j]
            matrix[i, j] = matrix[j, i] = (
                nll(theta + ei + ej) - nll(theta + ei - ej)
                - nll(theta - ei + ej) + nll(theta - ei - ej)) / (4 * step**2)
    if not np.all(np.isfinite(matrix)) or np.linalg.eigvalsh(matrix).min() <= 1e-8:
        raise ValueError("The fit has no stable positive information matrix; collect more failures.")
    return np.linalg.inv(matrix)


def _life_interval(log_value, gradient, covariance, z):
    variance = float(gradient @ covariance @ gradient)
    if not np.isfinite(variance) or variance < 0:
        raise ValueError("Life uncertainty is not estimable from these observations.")
    width = z * np.sqrt(variance)
    with np.errstate(over="ignore", under="ignore"):
        values = np.exp([log_value, log_value - width, log_value + width])
    if not np.all(np.isfinite(values) & (values > 0)):
        raise ValueError("Life estimate or interval exceeds the supported numeric range.")
    return dict(zip(("estimate", "lower", "upper"), map(float, values)))


def fit_life_model(table, model, confidence=.95):
    """Fit a life model and approximate log-delta intervals for mean life and B10.

    ``shape`` is Weibull beta or lognormal log-standard-deviation. ``scale`` is
    Weibull eta, lognormal exp(mu), or exponential mean. Location is always zero.
    Mean life is MTTF for first lives, or MTBF only for as-new renewal cycles.
    """
    z = _confidence(confidence)
    if model not in MODELS:
        raise ValueError(f"Choose a model from {MODELS}.")
    times, failed = validate_lifetimes(table)
    d = int(failed.sum())
    if not d:
        raise ValueError("No observed failures: finite mean life cannot be estimated.")
    if model != "exponential" and np.unique(times[failed]).size < 2:
        raise ValueError("Two-parameter models need at least two distinct failure ages.")
    log_reference = float(np.mean(np.log(times)))
    x = np.log(times) - log_reference
    if model == "exponential":
        log_mean = float(special.logsumexp(np.log(times)) - np.log(d))
        theta = np.array([log_mean - log_reference])
        covariance = np.array([[1 / d]])
        log_likelihood = -d * log_mean - d
        log_b10 = log_mean + np.log(-np.log(.9))
        mean_gradient = b10_gradient = np.array([1.])
        parameters = {"scale": float(np.exp(log_mean))}
    elif model == "weibull":
        def score(k):
            weights = special.softmax(k * x)
            return 1 / k + x[failed].mean() - float(weights @ x)

        # A finite profile root identifies the two-parameter MLE. Wide shape
        # limits reject boundary/degenerate solutions rather than clipping them.
        if score(1e-4) <= 0 or score(1e4) >= 0:
            raise ValueError("No stable interior Weibull fit; check variation in failure ages.")
        shape = optimize.brentq(score, 1e-4, 1e4, xtol=1e-12)
        log_scale = float((special.logsumexp(shape * x) - np.log(d)) / shape)
        theta = np.array([np.log(shape), log_scale])

        def nll(v):
            k = np.exp(v[0])
            return float(-d * v[0] + d * k * v[1] - (k - 1) * x[failed].sum()
                         + np.exp(k * (x - v[1])).sum())

        covariance = _information(nll, theta)
        log_likelihood = -nll(theta) - d * log_reference
        log_mean = log_scale + log_reference + special.gammaln(1 + 1 / shape)
        log_b10 = log_scale + log_reference + np.log(-np.log(.9)) / shape
        mean_gradient = np.array([-special.digamma(1 + 1 / shape) / shape, 1.])
        b10_gradient = np.array([-np.log(-np.log(.9)) / shape, 1.])
        parameters = {"shape": float(shape), "scale": float(np.exp(log_scale + log_reference))}
    else:
        def nll(v):
            sigma = np.exp(v[1])
            standardized = (x - v[0]) / sigma
            return float(-np.sum(stats.norm.logpdf(standardized[failed]) - v[1] - x[failed])
                         - np.sum(stats.norm.logsf(standardized[~failed])))

        initial = [float(np.mean(x[failed])), np.log(max(float(np.std(x[failed])), .3))]
        fit = optimize.minimize(nll, initial, method="L-BFGS-B", bounds=[(-40, 40), (-10, 8)],
                                options={"ftol": 1e-13, "gtol": 1e-7, "maxiter": 1000})
        if not fit.success or not (-39.9 < fit.x[0] < 39.9 and -9.9 < fit.x[1] < 7.9):
            raise ValueError("No stable interior lognormal fit; check the data or collect more failures.")
        theta = fit.x
        covariance = _information(nll, theta)
        mu, sigma = float(theta[0] + log_reference), float(np.exp(theta[1]))
        log_likelihood = -nll(theta) - d * log_reference
        log_mean, log_b10 = mu + sigma**2 / 2, mu + stats.norm.ppf(.1) * sigma
        mean_gradient = np.array([1., sigma**2])
        b10_gradient = np.array([1., stats.norm.ppf(.1) * sigma])
        parameters = {"shape": sigma, "scale": float(np.exp(mu))}
    mean = _life_interval(log_mean, mean_gradient, covariance, z)
    b10 = _life_interval(log_b10, b10_gradient, covariance, z)
    if not np.isfinite(log_likelihood) or not all(np.isfinite(v) and v > 0 for v in parameters.values()):
        raise ValueError("The fit exceeds the supported numeric range.")
    return dict(model=model, parameters=parameters, location=0., confidence=float(confidence),
                log_likelihood=float(log_likelihood), aic=float(2 * len(theta) - 2 * log_likelihood),
                mean_life=mean, b10=b10, interval_method="observed information, log-delta (approximate)")


def life_curves(fit, times):
    """Evaluate survival and instantaneous failure rate in the input age unit."""
    ages = np.asarray(times, dtype=float)
    if not np.all(np.isfinite(ages) & (ages >= 0)):
        raise ValueError("Curve ages must be finite and non-negative.")
    parameters = fit["parameters"]
    if fit["model"] == "weibull":
        shape, scale = parameters["shape"], parameters["scale"]
        # Subtracting logpdf and logsf loses the hazard once the cumulative
        # hazard is huge. The analytic log hazard avoids that cancellation.
        with np.errstate(divide="ignore", over="ignore", under="ignore"):
            log_ratio = np.log(ages) - np.log(scale)
            survival = np.exp(-np.exp(shape * log_ratio))
            hazard = (np.full_like(ages, 1 / scale) if shape == 1 else
                      np.exp(np.log(shape) - np.log(scale) + (shape - 1) * log_ratio))
        return {"survival": survival, "hazard": hazard}
    distribution = {"weibull": stats.weibull_min, "lognormal": stats.lognorm, "exponential": stats.expon}[fit["model"]]
    args = () if fit["model"] == "exponential" else (parameters["shape"],)
    log_survival = distribution.logsf(ages, *args, scale=parameters["scale"])
    with np.errstate(over="ignore", invalid="ignore"):
        hazard = np.exp(distribution.logpdf(ages, *args, scale=parameters["scale"]) - log_survival)
    return {"survival": np.exp(log_survival), "hazard": hazard}


def analyze_lifetimes(table, confidence=.95):
    """Build a JSON-safe report, retaining empirical results for excluded fits."""
    _confidence(confidence)
    times, failed = validate_lifetimes(table)
    normalized = pd.DataFrame({"time": times, "failed": failed.astype(int)})
    fits, excluded = [], []
    for model in MODELS:
        try:
            fits.append(fit_life_model(normalized, model, confidence))
        except ValueError as error:
            excluded.append({"model": model, "reason": str(error)})
    warnings = []
    if failed.sum() < 10:
        warnings.append("Fewer than 10 failures: model estimates and approximate confidence intervals can be unreliable.")
    if not failed.any():
        warnings.append("No failures observed. The flat empirical curve does not establish infinite life or certain survival.")
    if (~failed).mean() > .8:
        warnings.append("More than 80% suspended: life estimates depend strongly on model extrapolation.")
    return dict(schema_version=1, confidence=float(confidence),
                summary=dict(units=len(times), failures=int(failed.sum()), suspensions=int((~failed).sum()),
                             total_time=float(times.sum())),
                observations=normalized.to_dict(orient="records"),
                kaplan_meier=kaplan_meier(normalized, confidence).to_dict(orient="records"),
                fits=sorted(fits, key=lambda fit: fit["aic"]), excluded=excluded, warnings=warnings)
