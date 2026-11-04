"""Statistical Process Control: control charts, capability and Pareto analysis.

Everything here is a pure function over NumPy/pandas data so it can be tested
against hand-calculated textbook values. Non-normal capability reuses the
distribution that ``analysis.fit_candidates`` ranks first on held-out data.

References: D. C. Montgomery, *Introduction to Statistical Quality Control*
(control-chart constants, Western Electric rules); ISO 22514-2 (percentile
method for non-normal capability); Western Electric, *Statistical Quality
Control Handbook* (1956).
"""
import numpy as np
import pandas as pd
from scipy import stats

from analysis import get_supported_distributions

# Control-chart constants for subgroup sizes 2..10 (Montgomery, Appendix VI).
# d2 converts an average range to a standard deviation; A2, D3, D4 give the
# X-bar and R chart limits as multiples of the average range.
D2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}
A2 = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
D3 = {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
D4 = {2: 3.267, 3: 2.575, 4: 2.282, 5: 2.114, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}

WESTERN_ELECTRIC_RULES = {
    1: "1 point beyond 3 sigma",
    2: "2 of 3 consecutive points beyond 2 sigma on the same side",
    3: "4 of 5 consecutive points beyond 1 sigma on the same side",
    4: "8 consecutive points on the same side of the centre line",
}

# ISO 22514-2 percentile method: the +/-3 sigma span of a normal distribution
# covers the 0.135th to 99.865th percentiles.
LOWER_PERCENTILE = 0.00135
UPPER_PERCENTILE = 0.99865


def _series(values, minimum=2):
    data = np.asarray(values, dtype=float)
    if data.ndim != 1 or len(data) < minimum or not np.all(np.isfinite(data)):
        raise ValueError(f"Enter at least {minimum} finite numeric observations.")
    return data


def _specs(lsl, usl):
    if lsl is None and usl is None:
        raise ValueError("Provide at least one specification limit (LSL or USL).")
    if lsl is not None and usl is not None and not lsl < usl:
        raise ValueError("The lower specification limit must be below the upper limit.")
    return lsl, usl


# --------------------------------------------------------------------------
# Western Electric rules
# --------------------------------------------------------------------------

def western_electric_signals(values, center, sigma):
    """Apply the four Western Electric rules to a plotted series.

    ``sigma`` is the standard deviation of the *plotted statistic* (one third
    of the distance from the centre line to a control limit). Each rule maps to
    the zero-based indices of the point that completes the pattern. For rules
    2 and 3 that completing point must itself lie in the outer zone, so one
    run of points is not reported twice.
    """
    data = _series(values, minimum=1)
    if not sigma > 0 or not np.isfinite(sigma) or not np.isfinite(center):
        raise ValueError("Centre line must be finite and sigma positive.")
    z = (data - center) / sigma
    signals = {rule: [] for rule in WESTERN_ELECTRIC_RULES}
    for i, zi in enumerate(z):
        if abs(zi) > 3:
            signals[1].append(i)
        for rule, window, count, zone in ((2, 3, 2, 2.0), (3, 5, 4, 1.0)):
            if i + 1 < window or abs(zi) <= zone:
                continue
            recent = z[i + 1 - window:i + 1]
            same_side = recent > zone if zi > 0 else recent < -zone
            if np.count_nonzero(same_side) >= count:
                signals[rule].append(i)
        if i >= 7:
            recent = z[i - 7:i + 1]
            if np.all(recent > 0) or np.all(recent < 0):
                signals[4].append(i)
    return signals


def _chart(values, center, lcl, ucl, sigma, label):
    signals = western_electric_signals(values, center, sigma)
    flagged = sorted({i for indices in signals.values() for i in indices})
    return {"label": label, "values": np.asarray(values, dtype=float), "center": float(center),
            "lcl": float(lcl), "ucl": float(ucl), "sigma": float(sigma),
            "signals": signals, "flagged": flagged}


# --------------------------------------------------------------------------
# Control charts
# --------------------------------------------------------------------------

def xbar_r_chart(subgroups):
    """X-bar and R charts from rational subgroups (rows) of equal size 2..10.

    Limits follow Montgomery: X-bar = X-double-bar +/- A2 * R-bar and
    R = D3 * R-bar .. D4 * R-bar. ``sigma_within`` = R-bar / d2 is the
    short-term standard deviation used for Cp and Cpk. Western Electric rules
    are applied to the X-bar chart only; the R chart gets rule 1 (its limits are
    asymmetric, so the zone rules do not apply).
    """
    groups = np.asarray(subgroups, dtype=float)
    if groups.ndim != 2 or groups.shape[0] < 2 or not np.all(np.isfinite(groups)):
        raise ValueError("Subgroups must be a finite 2-D array with at least two rows.")
    n = groups.shape[1]
    if n not in D2:
        raise ValueError("Subgroup size must be between 2 and 10.")
    means = groups.mean(axis=1)
    ranges = np.ptp(groups, axis=1)
    grand_mean, r_bar = float(means.mean()), float(ranges.mean())
    xbar = _chart(means, grand_mean, grand_mean - A2[n] * r_bar, grand_mean + A2[n] * r_bar,
                  A2[n] * r_bar / 3, "X-bar")
    r_chart = {"label": "R", "values": ranges, "center": r_bar, "lcl": D3[n] * r_bar,
               "ucl": D4[n] * r_bar, "sigma": None, "signals": {1: []}, "flagged": []}
    r_chart["signals"][1] = [int(i) for i in np.flatnonzero((ranges > r_chart["ucl"]) | (ranges < r_chart["lcl"]))]
    r_chart["flagged"] = list(r_chart["signals"][1])
    return {"subgroup_size": n, "xbar": xbar, "range": r_chart,
            "sigma_within": r_bar / D2[n], "grand_mean": grand_mean, "r_bar": r_bar}


def imr_chart(values, baseline=None):
    """Individuals and moving-range (span 2) charts.

    Limits: X +/- 3 * MR-bar / d2 (the familiar 2.66 * MR-bar) and MR upper
    limit D4 * MR-bar = 3.267 * MR-bar. ``sigma_within`` = MR-bar / d2.

    By default the limits come from all observations. Pass ``baseline`` (a
    count of leading observations) to fix the limits from a stable reference
    period and then monitor everything after it (Phase I / Phase II practice).
    """
    data = _series(values, minimum=3)
    reference = data
    if baseline is not None:
        if not 3 <= baseline <= len(data):
            raise ValueError("baseline must be between 3 and the number of observations.")
        reference = data[:baseline]
    moving = np.abs(np.diff(data))
    mr_bar, mean = float(np.abs(np.diff(reference)).mean()), float(reference.mean())
    sigma = mr_bar / D2[2]
    individuals = _chart(data, mean, mean - 3 * sigma, mean + 3 * sigma, sigma, "Individuals")
    mr_chart = {"label": "Moving range", "values": moving, "center": mr_bar, "lcl": 0.0,
                "ucl": D4[2] * mr_bar, "sigma": None, "signals": {}, "flagged": []}
    mr_chart["signals"][1] = [int(i) for i in np.flatnonzero(moving > mr_chart["ucl"])]
    mr_chart["flagged"] = list(mr_chart["signals"][1])
    return {"individuals": individuals, "moving_range": mr_chart,
            "sigma_within": sigma, "mean": mean, "mr_bar": mr_bar}


# --------------------------------------------------------------------------
# Process capability
# --------------------------------------------------------------------------

def capability(values, lsl=None, usl=None, sigma_within=None):
    """Classic normal-theory indices.

    Pp/Ppk use the overall sample standard deviation (ddof=1); Cp/Cpk use
    ``sigma_within`` (R-bar/d2 or MR-bar/d2 from a control chart) and are None
    when it is not supplied. Cp and Pp need both limits; Cpk and Ppk use the
    nearer one when only one limit exists.
    """
    data = _series(values)
    lsl, usl = _specs(lsl, usl)
    mean, sigma_overall = float(data.mean()), float(data.std(ddof=1))
    if not sigma_overall > 0:
        raise ValueError("Capability needs varying observations, not a constant series.")

    def indices(sigma):
        spread = None if lsl is None or usl is None else (usl - lsl) / (6 * sigma)
        sides = []
        if usl is not None:
            sides.append((usl - mean) / (3 * sigma))
        if lsl is not None:
            sides.append((mean - lsl) / (3 * sigma))
        return spread, min(sides)

    pp, ppk = indices(sigma_overall)
    cp = cpk = None
    if sigma_within is not None:
        if not sigma_within > 0:
            raise ValueError("sigma_within must be positive.")
        cp, cpk = indices(sigma_within)
    return {"mean": mean, "sigma_overall": sigma_overall, "sigma_within": sigma_within,
            "Pp": pp, "Ppk": ppk, "Cp": cp, "Cpk": cpk, "lsl": lsl, "usl": usl,
            "n": len(data), "method": "normal"}


def capability_percentile(name, parameters, lsl=None, usl=None):
    """Non-normal Pp/Ppk by the ISO 22514-2 percentile method.

    Pp  = (USL - LSL) / (x99.865 - x0.135)
    Ppk = min((USL - x50) / (x99.865 - x50), (x50 - LSL) / (x50 - x0.135))

    The percentiles come from the named SciPy distribution with the given
    (shape..., loc, scale) parameters, as returned by ``analysis.fit_candidates``.
    For a normal distribution these reduce exactly to the classic formulas.
    Also returns the model's expected parts per million outside specification.
    """
    lsl, usl = _specs(lsl, usl)
    dist = get_supported_distributions()[name]
    x_low, median, x_high = (float(v) for v in dist.ppf([LOWER_PERCENTILE, 0.5, UPPER_PERCENTILE], *parameters))
    if not (np.isfinite([x_low, median, x_high]).all() and x_low < median < x_high):
        raise ValueError(f"{name} does not give a usable percentile spread for these parameters.")
    pp = None if lsl is None or usl is None else (usl - lsl) / (x_high - x_low)
    sides = []
    if usl is not None:
        sides.append((usl - median) / (x_high - median))
    if lsl is not None:
        sides.append((median - lsl) / (median - x_low))
    below = 0.0 if lsl is None else float(dist.cdf(lsl, *parameters))
    above = 0.0 if usl is None else float(dist.sf(usl, *parameters))
    return {"distribution": name, "parameters": tuple(float(p) for p in parameters),
            "Pp": pp, "Ppk": min(sides), "median": median,
            "x_0.135": x_low, "x_99.865": x_high, "lsl": lsl, "usl": usl,
            "ppm_below": below * 1e6, "ppm_above": above * 1e6,
            "ppm_total": (below + above) * 1e6, "method": "percentile (ISO 22514-2)"}


def capability_from_fit(fit, lsl=None, usl=None):
    """Percentile capability using the winner of ``analysis.fit_candidates``.

    The winner is the family with the lowest held-out negative log likelihood;
    its parameters were estimated on the training split only.
    """
    if not fit.get("results"):
        raise ValueError("No fitted distribution is available; every candidate failed.")
    best = fit["results"][0]
    return capability_percentile(best["Distribution"], best["Parameters"], lsl, usl)


# --------------------------------------------------------------------------
# Pareto analysis
# --------------------------------------------------------------------------

def pareto_table(data, threshold=80.0):
    """Ranked Pareto table from ``{category: count}`` or a list of labels.

    ``Vital few`` marks the categories needed to first reach ``threshold``
    percent of the total (the category that crosses it is included).
    """
    if isinstance(data, dict):
        counts = pd.Series(data, dtype=float)
    else:
        counts = pd.Series(list(data), dtype=object).value_counts(sort=False).astype(float)
    if len(counts) == 0 or (counts < 0).any() or not np.all(np.isfinite(counts)) or counts.sum() <= 0:
        raise ValueError("Pareto analysis needs non-negative counts with a positive total.")
    # Stable sort keeps first-seen order for ties, so the output is reproducible.
    counts = counts.sort_values(ascending=False, kind="stable")
    percent = counts / counts.sum() * 100
    cumulative = percent.cumsum()
    table = pd.DataFrame({"Category": counts.index.astype(str), "Count": counts.values,
                          "Percent": percent.values, "Cumulative %": cumulative.values,
                          "Vital few": ((cumulative - percent) < threshold).values})
    return table.reset_index(drop=True)


def pareto_chart(table, title="Pareto chart"):
    """Matplotlib Figure: bars for counts, line for cumulative percent."""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(8, 4.5))
    ax = fig.subplots()
    x = np.arange(len(table))
    colors = ["#1f77b4" if few else "#9ecae1" for few in table["Vital few"]]
    ax.bar(x, table["Count"], color=colors)
    ax.set_xticks(x, table["Category"], rotation=30, ha="right")
    ax.set_ylabel("Count")
    ax.set_title(title)
    line = ax.twinx()
    line.plot(x, table["Cumulative %"], color="#d62728", marker="o")
    line.axhline(80, color="gray", linestyle="--", linewidth=1)
    line.set_ylim(0, 105)
    line.set_ylabel("Cumulative %")
    fig.tight_layout()
    return fig


def control_chart_figure(chart, title=None):
    """Matplotlib Figure of one chart dict, with limits and flagged points."""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(8, 3.5))
    ax = fig.subplots()
    values = chart["values"]
    x = np.arange(1, len(values) + 1)
    ax.plot(x, values, marker="o", markersize=3, color="#1f77b4")
    for level, style in ((chart["center"], "-"), (chart["ucl"], "--"), (chart["lcl"], "--")):
        ax.axhline(level, color="gray", linestyle=style, linewidth=1)
    if chart["flagged"]:
        ax.plot(x[chart["flagged"]], values[chart["flagged"]], "o", color="#d62728", markersize=7)
    ax.set_title(title or chart["label"])
    ax.set_xlabel("Observation")
    fig.tight_layout()
    return fig
