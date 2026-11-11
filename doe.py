"""Two-level factorial experiments for process changes: plan the runs, then fit the effects.

A factorial experiment changes several things at once in a fixed pattern, so one
set of runs answers questions about every factor and about how factors interact.
Each factor has a low and a high level. Coded columns use -1 for low and +1 for high,
and 0 for a centre point, a run halfway between the two levels.

Commands:

    python doe.py plan --factor crew_size=2:4 --factor tooling_minutes=5:15 \\
        --factor kit=0:1 --out .runtime/changeover-plan
    python doe.py analyse --plan .runtime/changeover-plan --out .runtime/changeover-report
    python doe.py --sample --out .runtime/doe-sample

``plan`` writes a run sheet in random order. After I run the trials I type the measured
response into the ``response`` column and ``analyse`` fits the effects. The sample
command simulates a changeover study with known effects, so the output can be checked.
"""
from __future__ import annotations

import argparse
import itertools
import json
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

SEED = 20261111
RESPONSE = "response"


def _check_factors(factors):
    if not factors:
        raise ValueError("Give at least one factor.")
    for name, (low, high) in factors.items():
        if not name.isidentifier():
            raise ValueError(f"Factor name {name!r} must be a plain word such as crew_size.")
        if not (np.isfinite(low) and np.isfinite(high)) or low == high:
            raise ValueError(f"Factor {name!r} needs two different finite levels.")


def _coded_to_actual(coded, factors, names):
    """Map -1/+1/0 columns onto the real units, where 0 is the midpoint."""
    actual = {}
    for column, name in enumerate(names):
        low, high = factors[name]
        actual[name] = (low + high) / 2 + coded[:, column] * (high - low) / 2
    return actual


def _assemble(names, coded, factors, centre_points, replicates, generators, seed):
    if replicates < 1:
        raise ValueError("replicates must be at least 1.")
    if centre_points < 0:
        raise ValueError("centre_points cannot be negative.")
    coded = np.repeat(coded, replicates, axis=0)
    if centre_points:
        coded = np.vstack([coded, np.zeros((centre_points, len(names)))])
    is_centre = np.all(coded == 0, axis=1)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(coded))
    standard = np.arange(1, len(coded) + 1)
    values = _coded_to_actual(coded, factors, names)
    frame = pd.DataFrame({
        "run_order": np.arange(1, len(coded) + 1),
        "standard_order": standard,
        "is_centre": is_centre,
    })
    # Keep the standard-order numbers that belong to each physical run, then shuffle the sheet.
    frame = frame.iloc[order].reset_index(drop=True)
    frame["run_order"] = np.arange(1, len(frame) + 1)
    for name in names:
        frame[name] = values[name][order]
    frame.attrs["design"] = {"factors": {k: list(v) for k, v in factors.items()},
                             "generators": dict(generators), "centre_points": int(centre_points),
                             "replicates": int(replicates), "seed": int(seed),
                             "resolution": resolution(names, generators) if generators else None}
    return frame


def full_factorial(factors, *, centre_points=0, replicates=1, seed=SEED):
    """Every combination of low and high for each factor, in random run order.

    ``factors`` maps names to ``(low, high)`` pairs. The run sheet has one row per run,
    with the factor values in real units and ``is_centre`` marking centre points.
    """
    _check_factors(factors)
    names = list(factors)
    coded = np.array(list(itertools.product([-1., 1.], repeat=len(names))))
    return _assemble(names, coded, factors, centre_points, replicates, {}, seed)


def fractional_factorial(factors, generators, *, centre_points=0, replicates=1, seed=SEED):
    """A 2^(k-p) design: a quarter or eighth of the full set of runs.

    ``generators`` maps each added factor to the base letters it multiplies. Base factors
    are labelled A, B, C... in the order they are listed, so ``{"fixture": "ABC"}`` sets
    the fixture column to the product of the first three base columns. Fewer runs means some effects
    share one estimate (are aliased); ``resolution`` says how long the shortest
    word that causes aliasing is, and resolution IV or more keeps main effects clear of
    two-factor interactions.
    """
    _check_factors(factors)
    names = list(factors)
    unknown = set(generators) - set(names)
    if unknown:
        raise ValueError(f"Generators name unknown factors: {sorted(unknown)}")
    base = [name for name in names if name not in generators]
    if not base:
        raise ValueError("At least one base factor must remain without a generator.")

    letters = {chr(ord("A") + i) for i in range(len(base))}
    for added, word in generators.items():
        if not word or any(letter not in letters for letter in word):
            raise ValueError(f"Generator for {added!r} must use base letters A to "
                             f"{chr(ord('A') + len(base) - 1)}, got {word!r}.")
    base_coded = np.array(list(itertools.product([-1., 1.], repeat=len(base))))
    columns = {name: base_coded[:, i] for i, name in enumerate(base)}
    for added, word in generators.items():
        columns[added] = np.prod([base_coded[:, ord(letter) - ord("A")] for letter in word], axis=0)
    coded = np.column_stack([columns[name] for name in names])
    words = {added: [base[ord(letter) - ord("A")] for letter in word] for added, word in generators.items()}
    return _assemble(names, coded, factors, centre_points, replicates, words, seed)


def resolution(names, generators):
    """Length of the shortest defining word: IV or more means main effects are clear of 2-factor interactions."""
    if not generators:
        return None
    words = [frozenset(word) | {added} for added, word in generators.items()]
    shortest = len(names) + 1
    for size in range(1, len(words) + 1):
        for combo in itertools.combinations(words, size):
            word = frozenset()
            for part in combo:
                word = word ^ part
            if word:
                shortest = min(shortest, len(word))
    return shortest


def _term_columns(coded, names, max_order):
    """Each main effect and interaction as a column of products of coded factors, labelled 'a x b'."""
    terms = {}
    for order in range(1, max_order + 1):
        for combo in itertools.combinations(range(len(names)), order):
            label = " x ".join(names[i] for i in combo)
            terms[label] = np.prod(coded[:, list(combo)], axis=1)
    return terms


def _json_safe(value):
    """Replace NaN and infinity with null so the saved JSON is strict."""
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _coded_matrix(runs, factors, names):
    """Coded -1/0/+1 values from the real-unit columns in a run sheet."""
    coded = []
    for name in names:
        low, high = factors[name]
        values = runs[name].to_numpy(dtype=float)
        if np.any(values < min(low, high) - 1e-9) or np.any(values > max(low, high) + 1e-9):
            raise ValueError(f"{name} has values outside its levels {low} to {high}.")
        coded.append((values - (low + high) / 2) / ((high - low) / 2))
    return np.column_stack(coded)


def fit_effects(runs, factors, *, max_order=2, response=RESPONSE, alpha=0.05):
    """Least-squares fit of main effects and interactions, with effect sizes and ANOVA p-values.

    For a two-level factor, the effect is the change in mean response when the factor
    moves from low to high, so it is twice the coded coefficient. Curvature is the
    difference between the centre-point mean and the mean of the factorial runs,
    and it is only reported when the design has centre points.
    """
    names = list(factors)
    if max_order < 1 or max_order > len(names):
        raise ValueError("max_order must be between 1 and the number of factors.")
    if response not in runs:
        raise ValueError(f"Run sheet has no {response!r} column.")
    y = pd.to_numeric(runs[response], errors="coerce").to_numpy(dtype=float)
    if not np.all(np.isfinite(y)):
        raise ValueError("Every run needs a numeric response before analysis.")
    coded = _coded_matrix(runs, factors, names)
    is_centre = np.all(coded == 0, axis=1)
    terms = _term_columns(coded, names, max_order)

    # Drop duplicated columns (aliases) so the fit has full rank. Keep the first name in each group.
    representatives, aliases = {}, {}
    for term, column in terms.items():
        match = next((kept for kept, values in representatives.items()
                      if np.allclose(values, column) or np.allclose(values, -column)), None)
        if match is None:
            representatives[term] = column
        else:
            aliases.setdefault(match, []).append(term)

    columns = {"Intercept": np.ones(len(y))}
    columns.update(representatives)
    has_centre = bool(is_centre.any() and (~is_centre).any())
    if has_centre:
        columns["curvature"] = is_centre.astype(float)
    design = np.column_stack(list(columns.values()))
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("The design cannot estimate every term; remove an interaction or add runs.")
    df_resid = len(y) - design.shape[1]
    if df_resid < 1:
        raise ValueError("Add replicates or centre points: the fit needs at least one residual degree of freedom.")
    model = sm.OLS(y, design).fit()
    beta = np.asarray(model.params)
    se = np.asarray(model.bse)
    residual = np.asarray(model.resid)
    mse = float(model.mse_resid)
    t_crit = stats.t.ppf(1 - alpha / 2, df_resid)
    names_fit = list(columns)

    rows = []
    for position, term in enumerate(names_fit):
        if term == "Intercept":
            continue
        index = position
        coef = beta[index]
        sum_sq = float(np.sum(columns[term] ** 2) * coef ** 2)
        f_stat = sum_sq / mse if mse > 0 else np.inf
        is_curvature = term == "curvature"
        scale = 1. if is_curvature else 2.
        effect = scale * coef
        std_error = scale * se[index]
        if is_curvature:
            kind = "curvature"
        else:
            kind = "main" if " x " not in term else "interaction"
        rows.append({
            "term": "curvature (centre vs factorial)" if is_curvature else term,
            "type": kind,
            "effect": effect,
            "std_error": std_error,
            "ci_low": effect - t_crit * std_error,
            "ci_high": effect + t_crit * std_error,
            "t": coef / se[index] if se[index] > 0 else np.inf,
            "p_value": float(stats.f.sf(f_stat, 1, df_resid)),
            "sum_sq": sum_sq,
            "aliased_with": " = ".join(aliases.get(term, [])),
        })
    effects = pd.DataFrame(rows)
    total = effects["sum_sq"].sum() + float(residual @ residual)
    effects["share_of_variation"] = effects["sum_sq"] / total if total > 0 else np.nan
    effects = effects.reindex(effects["effect"].abs().sort_values(ascending=False).index).reset_index(drop=True)

    main_and_interactions = effects[effects["type"] != "curvature"]["effect"].to_numpy()
    summary = {
        "response": response,
        "runs": int(len(y)),
        "factorial_runs": int((~is_centre).sum()),
        "centre_runs": int(is_centre.sum()),
        "residual_df": int(df_resid),
        "residual_sd": float(np.sqrt(mse)),
        "r_squared": float(1 - (residual @ residual) / np.sum((y - y.mean()) ** 2)) if np.ptp(y) > 0 else float("nan"),
        "lenth_pse": lenth_pse(main_and_interactions),
        "lenth_margin": lenth_margin(main_and_interactions),
        "curvature_p_value": float(effects.loc[effects["type"] == "curvature", "p_value"].iloc[0])
        if has_centre else None,
    }
    return {"effects": effects, "summary": summary, "design": runs.attrs.get("design", {})}


def lenth_pse(effects):
    """Lenth's pseudo standard error: a noise estimate from effects that look like noise."""
    values = np.abs(np.asarray(effects, dtype=float))
    if values.size == 0:
        return float("nan")
    s0 = 1.5 * np.median(values)
    trimmed = values[values < 2.5 * s0]
    return float(1.5 * np.median(trimmed)) if trimmed.size else float("nan")


def lenth_margin(effects, alpha=0.05):
    """Margin of error for Lenth's method; an effect larger than this is probably real."""
    values = np.asarray(effects, dtype=float)
    pse = lenth_pse(values)
    if not np.isfinite(pse) or values.size < 3:
        return float("nan")
    return float(stats.t.ppf(1 - alpha / 2, values.size / 3) * pse)


def half_normal_plot(effects, path, summary=None):
    """Effects against half-normal quantiles: effects that are noise fall on a straight line through zero."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    table = effects[effects["type"] != "curvature"].copy()
    table["abs"] = table["effect"].abs()
    table = table.sort_values("abs").reset_index(drop=True)
    m = len(table)
    probabilities = (np.arange(1, m + 1) - .5) / m
    quantiles = stats.norm.ppf(.5 + .5 * probabilities)
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.scatter(quantiles, table["abs"], color="#4a5568", zorder=3)
    for x, y, name in zip(quantiles, table["abs"], table["term"]):
        if y > 0.5 * table["abs"].max():
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8)
    if summary and np.isfinite(summary.get("lenth_pse", np.nan)):
        # Noise-only effects follow a normal curve with sd = PSE, so they fall near this line.
        ax.axline((0, 0), slope=summary["lenth_pse"], color="#a0aec0", linestyle="--", linewidth=1,
                  label="Lenth noise line")
    if summary:
        ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_xlabel("Half-normal quantile")
    ax.set_ylabel(f"|effect| ({summary['response'] if summary else 'response'} units)")
    ax.set_title("Half-normal plot of effects")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return Path(path)


def pareto_plot(effects, path):
    """Bars of |effect| from largest to smallest, with the running share of the total."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    table = effects[effects["type"] != "curvature"].copy()
    table["abs"] = table["effect"].abs()
    table = table.sort_values("abs", ascending=False).reset_index(drop=True)
    cumulative = table["abs"].cumsum() / table["abs"].sum() * 100 if table["abs"].sum() > 0 else table["abs"] * 0
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    labels = [textwrap.fill(name.replace(" x ", " × "), 18, break_long_words=False, break_on_hyphens=False)
              for name in table["term"]]
    positions = np.arange(len(table))
    ax.bar(positions, table["abs"], color="#4a5568")
    ax.set_xticks(positions, labels, fontsize=7)
    ax.set_ylabel("|effect|")
    twin = ax.twinx()
    twin.plot(positions, cumulative, color="#c05621", marker="o", linewidth=1.2)
    twin.set_ylabel("cumulative share (%)")
    twin.set_ylim(0, 105)
    ax.set_title("Pareto of effects")
    ax.spines[["top"]].set_visible(False)
    twin.spines[["top"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return Path(path)


def save_plan(runs, out):
    """Write the run sheet and the design settings needed to analyse the results later."""
    directory = Path(out)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"{directory} already has files; choose a new folder.")
    directory.mkdir(parents=True, exist_ok=True)
    sheet = runs.copy()
    sheet[RESPONSE] = np.nan
    sheet.to_csv(directory / "run_sheet.csv", index=False)
    (directory / "design.json").write_text(json.dumps(_json_safe(runs.attrs["design"]), indent=2) + "\n")
    return directory


def load_plan(directory):
    """Read a saved run sheet and its design settings; response values are typed in by hand."""
    directory = Path(directory)
    design = json.loads((directory / "design.json").read_text())
    runs = pd.read_csv(directory / "run_sheet.csv")
    factors = {name: tuple(levels) for name, levels in design["factors"].items()}
    runs.attrs["design"] = design
    return runs, factors


def write_analysis(result, out):
    """Save the effect table, the summary, both charts and the run order into a new folder."""
    directory = Path(out)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"{directory} already has files; choose a new folder.")
    directory.mkdir(parents=True, exist_ok=True)
    result["effects"].to_csv(directory / "effects.csv", index=False)
    summary = {**result["summary"], "design": result["design"]}
    (directory / "summary.json").write_text(json.dumps(_json_safe(summary), indent=2) + "\n")
    half_normal_plot(result["effects"], directory / "half_normal.png", result["summary"])
    pareto_plot(result["effects"], directory / "pareto.png")
    return directory


def simulate_changeover(runs, seed=SEED):
    """Changeover minutes for a planned run sheet, with known effects so the fit can be checked.

    Coded effects: crew size -4, tooling time +6, kit -5, fixture +2 and a crew-by-tooling
    interaction of +1.5 on the coded scale, so the true change from low to high is twice
    each value. Gaussian noise has a standard deviation of 0.8 minutes.
    """
    factors = {name: tuple(levels) for name, levels in runs.attrs["design"]["factors"].items()}
    names = list(factors)
    coded = _coded_matrix(runs, factors, names)
    rng = np.random.default_rng(seed)
    mean = (30 - 4 * coded[:, 0] + 6 * coded[:, 1] - 5 * coded[:, 2] + 2 * coded[:, 3]
            + 1.5 * coded[:, 0] * coded[:, 1])
    return mean + rng.normal(0, 0.8, len(runs))


def sample_plan(out):
    """Four-factor fractional plan: crew size, tooling time, kit and fixture, 8 runs times 2 replicates, plus centres."""
    factors = {"crew_size": (2, 4), "tooling_minutes": (5, 15), "kit": (0, 1), "fixture": (0, 1)}
    runs = fractional_factorial(factors, {"fixture": "ABC"}, centre_points=4, replicates=2)
    return save_plan(runs, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Plan and analyse two-level factorial experiments.")
    parser.add_argument("--sample", action="store_true", help="Simulate the changeover study and analyse it")
    parser.add_argument("--out", type=Path, help="New folder for the output")
    commands = parser.add_subparsers(dest="command")
    plan = commands.add_parser("plan", help="Write a randomised run sheet")
    plan.add_argument("--factor", action="append", default=[], metavar="NAME=LOW:HIGH")
    plan.add_argument("--fraction", action="append", default=[], metavar="NEW=BASE",
                      help="Add a factor as a product of base factors, e.g. fixture=ABC")
    plan.add_argument("--centre", type=int, default=0, help="Centre-point runs")
    plan.add_argument("--replicates", type=int, default=1)
    plan.add_argument("--seed", type=int, default=SEED)
    plan.add_argument("--out", type=Path, required=True)
    analyse = commands.add_parser("analyse", help="Fit effects for a run sheet with responses typed in")
    analyse.add_argument("--plan", type=Path, required=True)
    analyse.add_argument("--max-order", type=int, default=2)
    analyse.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.sample:
        if args.out is None:
            parser.error("--sample needs --out")
        plan_dir = sample_plan(Path(args.out) / "plan")
        runs, factors = load_plan(plan_dir)
        runs[RESPONSE] = simulate_changeover(runs)
        result = fit_effects(runs, factors)
        print(f"Wrote {write_analysis(result, Path(args.out) / 'analysis')}")
        return 0
    if args.command == "plan":
        factors = {}
        for item in args.factor:
            name, _, levels = item.partition("=")
            low, _, high = levels.partition(":")
            factors[name] = (float(low), float(high))
        generators = {}
        for item in args.fraction:
            name, _, base = item.partition("=")
            generators[name] = base
        runs = fractional_factorial(factors, generators, centre_points=args.centre,
                                    replicates=args.replicates, seed=args.seed) if generators else \
            full_factorial(factors, centre_points=args.centre, replicates=args.replicates, seed=args.seed)
        print(f"Wrote {save_plan(runs, args.out)} with {len(runs)} runs")
        return 0
    if args.command == "analyse":
        runs, factors = load_plan(args.plan)
        result = fit_effects(runs, factors, max_order=args.max_order)
        print(f"Wrote {write_analysis(result, args.out)}")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
