"""Save and independently check a frozen distribution comparison, without a server."""
import argparse
import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
import shutil

import numpy as np
from scipy import stats

from analysis import (create_report, evaluate_scenario, fit_candidates,
                      get_supported_distributions, manual_curve, read_csv,
                      report_payload, score_values, tail_check)


FORMAT = "distrofit-comparison-v1"
ARTIFACTS = ("comparison.json", "comparison.pdf", "scores.csv")
DEFAULT_CANDIDATES = ("Normal", "Gamma", "Exponential")


def _values(values, minimum=1):
    data = np.asarray(values, dtype=float)
    if (data.ndim != 1 or len(data) < minimum
            or not np.all(np.isfinite(data))):
        raise ValueError(f"Use at least {minimum} finite numeric observations; no rows are dropped.")
    return data


def load_column(path, column):
    """Read an explicit column, preserving numeric headerless CSV observations."""
    with Path(path).open(encoding="utf-8-sig") as source:
        table = read_csv(source, skip_blank_lines=False)
    if column not in table.columns:
        raise ValueError("The requested column is missing. Headerless columns are named 'Column 1', etc.")
    try:
        return _values(table[column].to_numpy())
    except (ValueError, TypeError):
        raise ValueError("The selected column must contain only finite numeric observations; no rows are dropped.") from None


def sample_data():
    """Synthetic measurements and a deliberately shifted independent sample."""
    training_source = np.random.default_rng(27).gamma(2, 2, 240)
    scenario = np.random.default_rng(28).gamma(2, 2, 60) + 12
    return training_source, scenario


def build_comparison(values, candidates=DEFAULT_CANDIDATES, *, scenario=None,
                     seed=42, held_out_fraction=.25, bins=30):
    data = _values(values, minimum=8)
    if not candidates or any(name not in get_supported_distributions() for name in candidates):
        raise ValueError("Choose supported distribution names.")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("Seed must be a nonnegative integer.")
    if isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= 200:
        raise ValueError("Bins must be an integer between 1 and 200.")
    scenario_data = None if scenario is None else _values(scenario)
    fit = fit_candidates(data, candidates, bins=bins,
                         validation_fraction=held_out_fraction, seed=seed)
    if not any(np.isfinite(row["Held-out NLL"]) for row in fit["results"]):
        raise ValueError("No candidate has a finite held-out score. Change the candidates or inspect the data.")
    payload = report_payload(fit, data, {"outlier_method": "None"}, scenario=scenario_data)
    return {"format": FORMAT, "analysis": payload}


def _json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _scores_csv(payload):
    output = StringIO(newline="")
    fields = ("distribution", "training_nll", "held_out_nll", "tail_threshold",
              "held_out_exceedances", "held_out_observations", "held_out_tail_flag",
              "scenario_nll", "scenario_exceedances", "scenario_observations", "scenario_tail_flag")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(fields)
    scenarios = {row["Distribution"]: row for row in payload["scenario_results"]}
    for row in payload["results"]:
        tail = row["Tail"]
        other = scenarios.get(row["Distribution"])
        scenario_fields = ((other["Scenario NLL"], other["Tail"]["exceedances"],
                            other["Tail"]["observations"], other["Tail"]["flagged"])
                           if other else ("", "", "", ""))
        writer.writerow((row["Distribution"], row["Train NLL"], row["Held-out NLL"],
                         tail["threshold"], tail["exceedances"], tail["observations"], tail["flagged"],
                         *scenario_fields))
    return output.getvalue().encode("utf-8")


def write_bundle(comparison, directory):
    """Create a new directory only; leave existing files and directories alone."""
    target = Path(directory)
    if target.exists():
        raise ValueError("The output path already exists. Choose a new directory to preserve previous results.")
    payload = comparison["analysis"]
    # Render before creating any files, so invalid reports leave no partial bundle.
    contents = {"comparison.json": _json_bytes(comparison),
                "comparison.pdf": create_report(payload),
                "scores.csv": _scores_csv(payload)}
    manifest = {"format": FORMAT, "sha256": {
        name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}}
    target.mkdir(parents=True, exist_ok=False)
    try:
        for name, content in contents.items():
            (target / name).write_bytes(content)
        (target / "manifest.json").write_bytes(_json_bytes(manifest))
    except BaseException:
        shutil.rmtree(target)
        raise
    return manifest


def _same(actual, expected):
    """Compare recomputed statistics; infinity is stored as an explicit string."""
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and actual.keys() == expected.keys()
                and all(_same(actual[key], value) for key, value in expected.items()))
    if isinstance(expected, (list, tuple)):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(_same(a, b) for a, b in zip(actual, expected)))
    if isinstance(expected, bool):
        return type(actual) is bool and actual == expected
    if isinstance(expected, (int, float)):
        if not math.isfinite(expected):
            return actual == str(expected)
        return (type(actual) in (int, float)
                and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10))
    return actual == expected


def _require_same(actual, expected, label):
    if not _same(actual, expected):
        raise ValueError(f"Stored {label} does not match the frozen-model calculation.")


def _reject_constant(value):
    raise ValueError("Nonstandard JSON numbers are not accepted.")


def _read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise ValueError("A comparison JSON document must be an object.")
    return value


def verify_bundle(directory):
    """Check hashes, split membership and scores without estimating any parameters.

    Hashes detect changed files, not authorship or engine provenance. This checks
    Python/SciPy calculations only; it never calls an external modeling platform.
    """
    target = Path(directory)
    manifest = _read_json(target / "manifest.json")
    if manifest.get("format") != FORMAT or set(manifest.get("sha256", {})) != set(ARTIFACTS):
        raise ValueError("Unrecognized comparison manifest.")
    for name in ARTIFACTS:
        if hashlib.sha256((target / name).read_bytes()).hexdigest() != manifest["sha256"][name]:
            raise ValueError(f"Checksum mismatch for {name}.")
    comparison = _read_json(target / "comparison.json")
    if comparison.get("format") != FORMAT:
        raise ValueError("Unrecognized comparison format.")
    payload = comparison["analysis"]
    data = _values(payload["prepared_data"], minimum=8)
    _require_same(payload["source_data"], data.tolist(), "source observations")
    settings = payload["settings"]
    if settings["outlier_method"] != "None":
        raise ValueError("This bundle format does not filter observations.")
    seed, fraction, bins = settings["seed"], settings["held_out_fraction"], settings["bins"]
    if type(seed) is not int or seed < 0 or type(fraction) not in (int, float) or not .1 <= fraction <= .5:
        raise ValueError("Invalid saved split settings.")
    if type(bins) is not int or not 1 <= bins <= 200:
        raise ValueError("Invalid saved histogram settings.")
    order = np.random.default_rng(seed).permutation(len(data))
    n_held = max(2, math.ceil(len(data) * fraction))
    train_indices, held_indices = order[n_held:], order[:n_held]
    for key, expected in (("train_indices", train_indices), ("held_indices", held_indices)):
        actual = payload[key]
        if not isinstance(actual, list) or any(type(i) is not int for i in actual) or actual != expected.tolist():
            raise ValueError("Saved split membership does not match the recorded seed and fraction.")
    training, held = data[train_indices], data[held_indices]
    threshold = float(np.quantile(training, .95))
    _require_same(settings["tail_threshold"], threshold, "tail threshold")
    rows = payload["results"]
    names = [row["Distribution"] for row in rows]
    failures = payload["failures"]
    if (not names or len(set(names)) != len(names) or set(names) & set(failures)
            or settings["candidates"] != names + list(failures)):
        raise ValueError("Invalid saved candidate list.")
    losses = []
    counts, edges = np.histogram(training, bins=bins, density=True)
    centers = (edges[:-1] + edges[1:]) / 2
    for row in rows:
        name, params = row["Distribution"], row["Parameters"]
        if name not in get_supported_distributions():
            raise ValueError("Unrecognized saved distribution.")
        manual_curve(name, params, held)  # Validate parameter count, shape and scale.
        train_nll = score_values(name, params, training)
        if not math.isfinite(train_nll):
            raise ValueError("Saved parameters have no finite training score.")
        loss = score_values(name, params, held)
        losses.append(loss)
        dist = get_supported_distributions()[name]
        k = len(params)
        expected = {"Train NLL": train_nll, "Held-out NLL": loss,
                    "AIC": 2*k + 2*len(training)*train_nll,
                    "BIC": k*math.log(len(training)) + 2*len(training)*train_nll,
                    "SSE": float(np.sum((counts - dist.pdf(centers, *params)) ** 2)),
                    "KS Stat": float(stats.kstest(held, dist.cdf, args=params).statistic),
                    "Tail": tail_check(name, params, held, threshold)}
        for key, value in expected.items():
            _require_same(row[key], value, key)
    if losses != sorted(losses) or not any(math.isfinite(loss) for loss in losses):
        raise ValueError("The saved ranking has no finite winner or is out of order.")
    scenario = payload["scenario_data"]
    expected_scenario = [] if not scenario else evaluate_scenario(
        {"results": rows, "tail_threshold": threshold}, _values(scenario))
    _require_same(payload["scenario_results"], expected_scenario, "scenario scores")
    if (target / "scores.csv").read_bytes() != _scores_csv(payload):
        raise ValueError("The CSV does not match the saved comparison.")
    return {"winner": names[0], "training": len(training), "held_out": len(held),
            "scenario": len(scenario), "candidates": len(rows)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("fit", help="Fit measurements and save a reproducible comparison")
    source = create.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", action="store_true", help="Use synthetic measurements and a shifted sample")
    source.add_argument("--input", type=Path, help="Input CSV file")
    create.add_argument("--column", help="Exact numeric column name")
    create.add_argument("--scenario", type=Path, help="Independent scenario CSV, scored without refitting")
    create.add_argument("--scenario-column", help="Scenario column; defaults to --column")
    create.add_argument("--candidate", action="append", choices=list(get_supported_distributions()))
    create.add_argument("--seed", type=int, default=42)
    create.add_argument("--held-out-fraction", type=float, default=.25)
    create.add_argument("--bins", type=int, default=30)
    create.add_argument("--out", type=Path, required=True, help="New output directory")
    check = commands.add_parser("verify", help="Check a bundle's files and recompute frozen-model scores")
    check.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "fit":
            if args.sample:
                if args.column or args.scenario or args.scenario_column:
                    raise ValueError("--sample includes its own measurements and scenario; do not add column or scenario options.")
                values, scenario = sample_data()
            else:
                if not args.column:
                    raise ValueError("--input requires --column.")
                if args.scenario_column and not args.scenario:
                    raise ValueError("--scenario-column requires --scenario.")
                values = load_column(args.input, args.column)
                scenario = None if args.scenario is None else load_column(
                    args.scenario, args.scenario_column or args.column)
            comparison = build_comparison(values, args.candidate or DEFAULT_CANDIDATES,
                                          scenario=scenario, seed=args.seed,
                                          held_out_fraction=args.held_out_fraction, bins=args.bins)
            write_bundle(comparison, args.out)
            summary = verify_bundle(args.out)
            print(f"Saved and checked {args.out}")
        else:
            summary = verify_bundle(args.directory)
        print(json.dumps(summary, allow_nan=False))
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, OSError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
