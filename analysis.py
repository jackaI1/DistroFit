"""Testable distribution fitting, frozen-model diagnostics and PDF export."""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO, StringIO
import json
import math
import textwrap
import warnings

import numpy as np
import pandas as pd
from scipy import stats


def get_supported_distributions():
    return {"Normal": stats.norm, "Gamma": stats.gamma, "Weibull (Min)": stats.weibull_min,
            "Exponential": stats.expon, "Log-Normal": stats.lognorm, "Beta": stats.beta,
            "Uniform": stats.uniform, "Student's t": stats.t, "Chi-Squared": stats.chi2,
            "Cauchy": stats.cauchy, "Pareto": stats.pareto, "Logistic": stats.logistic,
            "Laplace": stats.laplace, "Maxwell": stats.maxwell}


def read_csv(source):
    """Preserve the first numeric observation in headerless CSVs."""
    text = source.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    df = pd.read_csv(StringIO(text))
    try:
        # Only infer no header when every field in the first row is numeric.
        [float(column) for column in df.columns]
    except (ValueError, TypeError):
        return df
    df = pd.read_csv(StringIO(text), header=None)
    df.columns = [f"Column {i+1}" for i in range(df.shape[1])]
    return df


def prepare_data(values, method="None", threshold=3.):
    data = np.asarray(values, dtype=float)
    clean = data[np.isfinite(data)]
    if method == "Z-Score" and len(clean) and np.std(clean) > 0:
        clean = clean[np.abs(stats.zscore(clean)) < threshold]
    elif method == "IQR" and len(clean):
        q1, q3 = np.quantile(clean, [.25, .75])
        clean = clean[(clean >= q1 - 1.5 * (q3-q1)) & (clean <= q3 + 1.5 * (q3-q1))]
    elif method not in ("None", "Z-Score", "IQR"):
        raise ValueError("Unknown outlier method")
    return clean, len(data) - len(clean)


def calculate_bin_count(values, method="Freedman-Diaconis"):
    data = np.asarray(values, dtype=float)
    data = data[np.isfinite(data)]
    n = len(data)
    if n < 2 or np.ptp(data) == 0:
        return 1
    if method == "Sturges":
        count = math.ceil(math.log2(n) + 1)
    elif method == "Square Root":
        count = math.ceil(math.sqrt(n))
    else:
        width = 2 * np.subtract(*np.percentile(data, [75, 25])) * n ** (-1/3)
        ratio = np.ptp(data) / width if width > 0 else math.sqrt(n)
        count = math.ceil(min(ratio, 200))
    return max(1, min(200, count))


def _finite_values(values, minimum=1):
    data = np.asarray(values, dtype=float)
    if data.ndim != 1 or len(data) < minimum or not np.all(np.isfinite(data)):
        raise ValueError(f"Enter at least {minimum} finite numeric observations.")
    return data


def score_values(name, parameters, values):
    data = _finite_values(values)
    logpdf = get_supported_distributions()[name].logpdf(data, *parameters)
    # Outside-support observations have infinite loss; never silently clip them.
    return float(-np.mean(logpdf)) if np.all(np.isfinite(logpdf)) else float("inf")


def tail_check(name, parameters, values, threshold):
    data = _finite_values(values)
    model = float(get_supported_distributions()[name].sf(threshold, *parameters))
    count = int(np.count_nonzero(data > threshold))
    lower, upper = stats.binom.interval(.95, len(data), model)
    return {"threshold": float(threshold), "model_share": model,
            "observed_share": count / len(data), "exceedances": count,
            "observations": len(data), "expected_count_interval": [float(lower), float(upper)],
            "flagged": bool(count < lower or count > upper)}


def fit_candidates(values, candidates, bins=30, validation_fraction=.25, seed=42):
    data = _finite_values(values, minimum=8)
    if np.ptp(data) == 0:
        raise ValueError("Distribution fitting needs varying observations, not a constant series.")
    if not candidates:
        raise ValueError("Select at least one candidate distribution.")
    if not .1 <= validation_fraction <= .5:
        raise ValueError("Held-out fraction must be between 0.1 and 0.5.")
    order = np.random.default_rng(seed).permutation(len(data))
    n_held = max(2, int(math.ceil(len(data) * validation_fraction)))
    train_indices, held_indices = order[n_held:], order[:n_held]
    training, held = data[train_indices], data[held_indices]
    if np.ptp(training) == 0:
        raise ValueError("Training split is constant; change the seed or provide more varying data.")
    counts, edges = np.histogram(training, bins=bins, density=True)
    centers = (edges[:-1] + edges[1:]) / 2
    supported = get_supported_distributions()
    threshold = float(np.quantile(training, .95))

    def fit_one(name):
        try:
            dist = supported[name]
            # scipy optimizers may warn on rejected iterations. Record a failed
            # fit explicitly if the final parameters/likelihood are invalid.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                params = tuple(float(p) for p in dist.fit(training))
                train_nll = score_values(name, params, training)
                if not np.isfinite(train_nll):
                    # Some scipy defaults put a bounded family's location above
                    # training observations. Retry from inside its support;
                    # location and scale remain free optimization parameters.
                    spread = float(np.std(training))
                    params = tuple(float(p) for p in dist.fit(
                        training, loc=float(training.min() - .01 * spread), scale=spread))
                    train_nll = score_values(name, params, training)
            if not np.all(np.isfinite(params)) or params[-1] <= 0 or not np.isfinite(train_nll):
                raise ValueError("No finite maximum-likelihood fit on the training sample")
            fitted_density = dist.pdf(centers, *params)
            sse = float(np.sum((counts - fitted_density) ** 2))
            k = len(params)
            row = {"Distribution": name, "Parameters": params, "Train NLL": train_nll,
                   "Held-out NLL": score_values(name, params, held), "SSE": sse,
                   "AIC": 2*k + 2*len(training)*train_nll,
                   "BIC": k*math.log(len(training)) + 2*len(training)*train_nll,
                   "KS Stat": float(stats.kstest(held, dist.cdf, args=params).statistic),
                   "Tail": tail_check(name, params, held, threshold)}
            return row, None
        except (KeyError, ValueError, TypeError, RuntimeError, FloatingPointError) as error:
            return None, f"{type(error).__name__}: {error}"

    names = list(dict.fromkeys(candidates))
    # Fit all selected families as one bounded parallel batch.
    with ThreadPoolExecutor(max_workers=min(4, len(names))) as pool:
        outcomes = list(pool.map(fit_one, names))
    rows = [row for row, error in outcomes if row is not None]
    errors = {name: error for name, (_, error) in zip(names, outcomes) if error}
    rows.sort(key=lambda row: row["Held-out NLL"])
    return {"data": data, "train_indices": train_indices, "held_indices": held_indices,
            "results": rows, "errors": errors, "seed": seed,
            "validation_fraction": validation_fraction, "bins": bins, "tail_threshold": threshold}


def evaluate_scenario(fit, values):
    data = _finite_values(values)
    rows = [{"Distribution": row["Distribution"],
             "Scenario NLL": score_values(row["Distribution"], row["Parameters"], data),
             "Tail": tail_check(row["Distribution"], row["Parameters"], data, fit["tail_threshold"])}
            for row in fit["results"]]
    return sorted(rows, key=lambda row: row["Scenario NLL"])


def diagnostics(name, parameters, values, bins=30):
    data = np.sort(_finite_values(values))
    dist = get_supported_distributions()[name]
    probabilities = (np.arange(len(data)) + .5) / len(data)
    hist, edges = np.histogram(data, bins=bins, density=True)
    # Integrated model mass per bin is better than evaluating only its midpoint.
    model_density = np.diff(dist.cdf(edges, *parameters)) / np.diff(edges)
    return {"observed": data, "theoretical": dist.ppf(probabilities, *parameters),
            "cdf_residual": probabilities - dist.cdf(data, *parameters),
            "bin_centers": (edges[:-1] + edges[1:]) / 2,
            "density_residual": hist - model_density}


def manual_curve(name, parameters, values, cdf=False):
    params = np.asarray(parameters, dtype=float)
    dist = get_supported_distributions()[name]
    if (len(params) != dist.numargs + 2 or not np.all(np.isfinite(params))
            or params[-1] <= 0 or np.any(params[:-2] <= 0)):
        raise ValueError("Shape and scale must be positive; all parameters must be finite.")
    return (dist.cdf if cdf else dist.pdf)(values, *params)


def adjust_parameters(parameters, training, location_offset=0., scale_multiplier=1.):
    """Apply location in training SDs and a scale factor without refitting."""
    data = _finite_values(training, minimum=2)
    params = np.asarray(parameters, dtype=float).copy()
    if (len(params) < 2 or not np.all(np.isfinite(params))
            or not np.isfinite(location_offset) or not np.isfinite(scale_multiplier)
            or scale_multiplier <= 0):
        raise ValueError("Use finite parameters, a finite offset and a positive scale multiplier.")
    params[-2] += location_offset * np.std(data, ddof=1)
    params[-1] *= scale_multiplier
    return params.tolist()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, np.ndarray)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else str(value)
    if isinstance(value, np.integer):
        return int(value)
    return value


def report_payload(fit, source, settings, scenario=None, manual=None):
    import scipy
    import matplotlib
    method = ("SciPy maximum likelihood on training observations only. Invalid default fits are "
              "retried from an interior starting location; optimization may find a local optimum. Seeded random split; "
              "winner minimizes mean held-out negative log likelihood (NLL). No refit on held-out "
              "or scenario data. AIC/BIC/SSE use training data. Tail threshold is the training "
              "95th percentile; tail flags compare observed counts with a central 95% binomial "
              "prediction interval (exploratory, no multiple-test correction). Q-Q uses fixed "
              "model quantiles with an identity reference; CDF residual = empirical minus model. "
              "Outlier filtering occurs before the split and can change the target population.")
    configuration = {**settings, "seed": fit["seed"], "held_out_fraction": fit["validation_fraction"],
                     "bins": fit["bins"], "candidates": [r["Distribution"] for r in fit["results"]]
                     + list(fit["errors"]), "tail_threshold": fit["tail_threshold"],
                     "versions": {"numpy": np.__version__, "scipy": scipy.__version__,
                                  "pandas": pd.__version__, "matplotlib": matplotlib.__version__}}
    payload = {"method": method, "settings": configuration,
               "source_data": source, "prepared_data": fit["data"],
               "train_indices": fit["train_indices"], "held_indices": fit["held_indices"],
               "results": fit["results"], "failures": fit["errors"],
               "scenario_data": [] if scenario is None else scenario,
               "scenario_results": [] if scenario is None else evaluate_scenario(fit, scenario),
               "manual": manual}
    return _json_safe(payload)


def create_report(payload):
    """One PDF with method, settings, results, diagnostics and every input row.

    An uncompressed page annotation also carries the complete JSON analysis for
    lossless recovery of float values, split membership and current settings.
    """
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure

    output = BytesIO()
    with PdfPages(output, metadata={"Title": "DistroFit reproducible report",
                                   "Author": "DistroFit", "Subject": "Method, settings and source data"}) as pdf:
        lines = ["DistroFit reproducible report", "", "Method", *textwrap.wrap(payload["method"], 95),
                 "", "Settings", *json.dumps(payload["settings"], indent=2).splitlines(),
                 "", f"Source observations: {len(payload['source_data'])}",
                 f"Prepared observations: {len(payload['prepared_data'])}",
                 f"Training: {len(payload['train_indices'])}; held out: {len(payload['held_indices'])}",
                 "", "Candidate comparison (training parameters; lower held-out NLL wins)"]
        for row in payload["results"]:
            lines += [f"{row['Distribution']}: train NLL={row['Train NLL']}; held-out NLL={row['Held-out NLL']}",
                      *textwrap.wrap(f"Parameters={row['Parameters']}; SSE={row['SSE']}; AIC={row['AIC']}; BIC={row['BIC']}", 95),
                      *textwrap.wrap(f"Tail check: {row['Tail']}", 95)]
        lines += ["", "Fit failures", *textwrap.wrap(str(payload["failures"]), 95),
                  "", "Manual adjustment (does not alter candidate ranking)",
                  *textwrap.wrap(str(payload["manual"]), 95), "", "Scenario (frozen parameters)"]
        for row in payload["scenario_results"]:
            lines += textwrap.wrap(str(row), 95)

        held = set(payload["held_indices"])
        lines += ["", "Full source data (before filtering; zero-based source row, value)"]
        lines += [f"{i}, {value!r}" for i, value in enumerate(payload["source_data"])]
        lines += ["", "Prepared data and split (zero-based prepared row, value, role)"]
        lines += [f"{i}, {value!r}, {'held-out' if i in held else 'training'}"
                  for i, value in enumerate(payload["prepared_data"])]
        lines += ["", "Full scenario data (row, value)"]
        lines += [f"{i}, {value!r}" for i, value in enumerate(payload["scenario_data"])]
        for start in range(0, len(lines), 57):
            fig = Figure(figsize=(8.5, 11))
            fig.text(.07, .95, "\n".join(lines[start:start+57]), va="top", fontsize=8,
                     family="monospace", linespacing=1.35)
            fig.text(.9, .025, str(start//57 + 1), fontsize=8)
            if start == 0:
                pdf.attach_note(json.dumps(payload, allow_nan=False))
            pdf.savefig(fig)
            fig.clear()

        if payload["results"]:
            winner = payload["results"][0]
            values = np.asarray(payload["prepared_data"])
            held_values = values[payload["held_indices"]]
            params, name = winner["Parameters"], winner["Distribution"]
            diag = diagnostics(name, params, held_values, payload["settings"]["bins"])
            fig = Figure(figsize=(8.5, 11))
            ax1, ax2, ax3 = fig.subplots(3)
            ax1.hist(values[payload["train_indices"]], bins=payload["settings"]["bins"],
                     density=True, alpha=.4, label="Training")
            x = np.linspace(values.min(), values.max(), 400)
            for row in payload["results"][:3]:
                ax1.plot(x, manual_curve(row["Distribution"], row["Parameters"], x), label=row["Distribution"])
            ax1.set_title("Training fits and untouched held-out observations")
            ax1.plot(held_values, np.zeros(len(held_values)), "|", alpha=.4, label="Held out")
            ax1.legend(fontsize=8)
            ax2.scatter(diag["theoretical"], diag["observed"], s=5)
            low = min(np.min(diag["theoretical"]), np.min(diag["observed"]))
            high = max(np.max(diag["theoretical"]), np.max(diag["observed"]))
            ax2.plot([low, high], [low, high], "--")
            ax2.set_title(f"Held-out Q-Q versus {name} (identity reference)")
            ax3.plot(diag["observed"], diag["cdf_residual"], ".")
            ax3.axhline(0, color="gray")
            ax3.set_title("Held-out empirical minus model CDF")
            fig.tight_layout(pad=3)
            pdf.savefig(fig)
            fig.clear()
    return output.getvalue()
