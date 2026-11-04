"""Generated maintenance example, diagnostic plots and command-line exports."""
import argparse
import csv
import io
import json
from pathlib import Path
import shutil

from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from scipy import stats

from reliability import analyze_lifetimes, life_curves

MODEL_COLUMNS = ["model", "aic", "log_likelihood", "mean_life", "mean_lower", "mean_upper",
                 "b10", "b10_lower", "b10_upper"]
CURVE_COLUMNS = ["model", "time", "survival", "hazard"]


def generate_demo():
    """80 generated pump-seal first lives, not field or personal measurements."""
    rng = np.random.default_rng(20261104)
    lifetime = 1200 * rng.weibull(2.1, 80)
    # Monitoring ages are sampled independently of lifetimes. A still-running
    # seal is observed only up to its monitoring age, not its hidden future life.
    monitoring = rng.uniform(600, 1400, 80)
    return pd.DataFrame({"unit_id": [f"SEAL-{i:03}" for i in range(1, 81)],
                         "time": np.round(np.minimum(lifetime, monitoring), 3),
                         "failed": (lifetime <= monitoring).astype(int)})


def read_lifetime_csv(source):
    """Read a path or upload, rejecting duplicate headers before pandas renames them."""
    content = source.read() if hasattr(source, "read") else Path(source).read_bytes()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    try:
        records = csv.reader(io.StringIO(content), strict=True)
        header = next(records, [])
        for number, record in enumerate(records, start=2):
            if record and len(record) != len(header):
                raise ValueError(f"CSV record {number} has {len(record)} fields; expected {len(header)}.")
    except csv.Error as error:
        raise ValueError(f"Invalid CSV: {error}") from error
    if not header or len(header) != len(set(header)):
        raise ValueError("CSV must have unique column names, including time and failed.")
    return pd.read_csv(io.StringIO(content))


def model_table(report):
    rows = []
    for fit in report["fits"]:
        mean, b10 = fit["mean_life"], fit["b10"]
        rows.append(dict(model=fit["model"], aic=fit["aic"], log_likelihood=fit["log_likelihood"],
                         mean_life=mean["estimate"], mean_lower=mean["lower"], mean_upper=mean["upper"],
                         b10=b10["estimate"], b10_lower=b10["lower"], b10_upper=b10["upper"]))
    return pd.DataFrame(rows, columns=MODEL_COLUMNS)


def curve_table(report):
    times = np.array([row["time"] for row in report["observations"]])
    rows = []
    for fit in report["fits"]:
        parameters = fit["parameters"]
        distribution = {"weibull": stats.weibull_min, "lognormal": stats.lognorm,
                        "exponential": stats.expon}[fit["model"]]
        args = () if fit["model"] == "exponential" else (parameters["shape"],)
        # Arbitrary extrapolation is especially misleading for nearly identical
        # failure ages. Stop remote tails at survival 1e-8, before enormous or
        # unrepresentable hazards can destroy an otherwise useful report.
        with np.errstate(over="ignore", under="ignore"):
            tail = float(distribution.isf(1e-8, *args, scale=parameters["scale"]))
        upper = min(float(times.max()) * 1.15, tail)
        lower = max(min(float(times.min()) * .5, upper * .5), np.nextafter(0., 1.))
        grid = np.geomspace(lower, upper, 300)
        curves = life_curves(fit, grid)
        finite = np.isfinite(curves["survival"]) & np.isfinite(curves["hazard"])
        rows.extend(dict(model=fit["model"], time=float(t), survival=float(s), hazard=float(h))
                    for t, s, h in zip(grid[finite], curves["survival"][finite], curves["hazard"][finite]))
    table = pd.DataFrame(rows, columns=CURVE_COLUMNS)
    if not table.empty and not np.isfinite(table[["time", "survival", "hazard"]].to_numpy()).all():
        raise ValueError("Curve values exceed the supported numeric range.")
    return table


def _probability_axis(survival, model):
    if model == "weibull":
        return np.log(-np.log(survival))
    if model == "lognormal":
        return stats.norm.isf(survival)
    return -np.log(survival)


def reliability_figure(report, model=None, unit="hours"):
    """Survival, hazard and a model-specific censored probability diagnostic.

    Probability points are KM failure jumps, not uncensored median ranks. No
    regression is fitted to those points; the line is the censored MLE model.
    """
    figure = Figure(figsize=(14, 5), layout="constrained")
    survival, hazard, probability = figure.subplots(1, 3)
    km = pd.DataFrame(report["kaplan_meier"])
    survival.step(km.time, km.survival, where="post", color="black", label="Kaplan-Meier")
    survival.fill_between(km.time, km.lower, km.upper, step="post", alpha=.12, color="black",
                          label=f"{report['confidence']:.0%} pointwise bounds")
    suspended = km[km.suspended > 0]
    survival.scatter(suspended.time, suspended.survival, marker="|", color="black", label="Suspension")
    curves = curve_table(report)
    for fit in report["fits"]:
        values = curves[curves.model == fit["model"]]
        survival.plot(np.r_[0, values.time], np.r_[1, values.survival], label=fit["model"].capitalize())
        hazard.plot(values.time, values.hazard, label=fit["model"].capitalize())
    survival.set(title="Survival and still-running units", xlabel=f"Age ({unit})",
                 ylabel="Survival probability", ylim=(-.02, 1.03))
    hazard.set(title="Instantaneous failure rate", xlabel=f"Age ({unit})",
               ylabel=f"Hazard (per {unit.rstrip('s')})")
    survival.legend(fontsize=7, loc="lower left")
    if report["fits"]:
        hazard.legend(fontsize=8)
        model = model or report["fits"][0]["model"]
        if model not in {fit["model"] for fit in report["fits"]}:
            raise ValueError("The selected probability model is not available in this report.")
        points = km[(km.failures > 0) & (km.survival > 0) & (km.survival < 1)]
        probability.scatter(points.time, _probability_axis(points.survival.to_numpy(), model),
                            color="black", s=16, label="KM failure probabilities")
        values = curves[(curves.model == model) & (curves.survival > 0) & (curves.survival < 1)]
        probability.plot(values.time, _probability_axis(values.survival.to_numpy(), model), label="Censored MLE")
        if model != "exponential":
            probability.set_xscale("log")
        fractions = np.array([.01, .05, .1, .2, .5, .8, .95, .99])
        probability.set_yticks(_probability_axis(1 - fractions, model), [f"{p:g}" for p in fractions * 100])
        probability.set(title=f"{model.capitalize()} probability plot", xlabel=f"Age ({unit})",
                        ylabel="Failed by this age (%)")
        probability.legend(fontsize=8)
    else:
        probability.set(title="Probability plot", xlabel=f"Age ({unit})", ylabel="Failed by this age (%)")
        probability.text(.5, .5, "No estimable life model", ha="center", transform=probability.transAxes)
    for axis in figure.axes:
        axis.grid(alpha=.2)
        axis.spines[["top", "right"]].set_visible(False)
    return figure


def export_report(report, out):
    """Write a new report directory; remove only our own partial export on failure."""
    payload = json.dumps(report, indent=2, allow_nan=False)
    models, curves = model_table(report), curve_table(report)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        (out / "reliability.json").write_text(payload + "\n", encoding="utf-8")
        pd.DataFrame(report["observations"]).to_csv(out / "observations.csv", index=False)
        pd.DataFrame(report["kaplan_meier"]).to_csv(out / "kaplan_meier.csv", index=False)
        models.to_csv(out / "models.csv", index=False)
        curves.to_csv(out / "curves.csv", index=False)
        figure = reliability_figure(report)
        try:
            figure.savefig(out / "reliability.png", dpi=150)
        finally:
            figure.clear()
    except BaseException:
        shutil.rmtree(out)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fit equipment lifetimes including still-running units. All times use hours.")
    parser.add_argument("csv", nargs="?", help="CSV with time and failed (1=failure, 0=suspension)")
    parser.add_argument("--sample", action="store_true", help="Use generated pump-seal lifetimes")
    parser.add_argument("--confidence", type=float, default=.95, help="Confidence fraction, e.g. .95")
    parser.add_argument("--out", type=Path, required=True, help="New output directory; existing directories are never overwritten")
    args = parser.parse_args(argv)
    if args.sample == bool(args.csv):
        parser.error("Choose either a CSV or --sample.")
    try:
        table = generate_demo() if args.sample else read_lifetime_csv(args.csv)
        report = analyze_lifetimes(table, confidence=args.confidence)
        export_report(report, args.out)
    except (ValueError, OSError, UnicodeError, pd.errors.ParserError) as error:
        parser.error(str(error))
    summary = report["summary"]
    print(f"{summary['units']} units: {summary['failures']} failures, {summary['suspensions']} suspensions. Saved {args.out}")
    for fit in report["fits"]:
        print(f"{fit['model']}: mean life {fit['mean_life']['estimate']:.2f} hours; B10 {fit['b10']['estimate']:.2f} hours")
    for warning in report["warnings"]:
        print(f"Note: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
