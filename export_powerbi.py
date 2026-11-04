"""Export DistroFit runs as a Power BI-ready star schema (CSV and Parquet).

Tables written (grain in brackets):

    fact_fit          one row per run x dataset x candidate distribution
    dim_dataset       one row per dataset (descriptive statistics, split sizes)
    dim_distribution  one row per supported distribution family
    dim_run           one row per export run (seed, split, library versions)

Every metric comes from ``analysis.fit_candidates``: parameters, AIC and BIC are
estimated on the training split, ranks and the KS statistic use the held-out
split. Command line use is documented in ``powerbi/REPORT.md``.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd
from scipy import stats

from analysis import fit_candidates, get_supported_distributions, prepare_data

SCHEMA_VERSION = 1
KS_ALPHA = .05
MAX_SHAPES = 2  # beta is the widest supported family: a, b, loc, scale

# Static descriptors for the dimension table, keyed by SciPy's distribution name.
_SUPPORT = {"norm": "Unbounded", "t": "Unbounded", "cauchy": "Unbounded",
            "logistic": "Unbounded", "laplace": "Unbounded",
            "gamma": "Lower-bounded", "weibull_min": "Lower-bounded", "expon": "Lower-bounded",
            "lognorm": "Lower-bounded", "chi2": "Lower-bounded", "pareto": "Lower-bounded",
            "maxwell": "Lower-bounded", "beta": "Bounded", "uniform": "Bounded"}
_HEAVY_TAILED = {"cauchy", "pareto", "t", "lognorm"}

FACT_COLUMNS = {
    "run_id": "string", "dataset_id": "string", "distribution_id": "string",
    "fit_status": "string", "failure_reason": "string",
    "shape_1": "double", "shape_2": "double", "loc": "double", "scale": "double",
    "parameter_count": "int64", "train_observations": "int64", "held_observations": "int64",
    "train_nll": "double", "log_likelihood": "double", "aic": "double", "bic": "double",
    "heldout_nll": "double", "sse": "double",
    "ks_statistic": "double", "ks_p_value": "double", "ks_pass": "bool",
    "rank_heldout_nll": "int64", "rank_aic": "int64", "rank_bic": "int64",
    "is_best_fit": "bool", "delta_aic": "double", "delta_bic": "double",
    "delta_heldout_nll": "double", "akaike_weight": "double",
    "tail_model_share": "double", "tail_observed_share": "double", "tail_flagged": "bool",
}
DIM_DATASET_COLUMNS = {
    "dataset_id": "string", "dataset_name": "string", "source": "string", "variable": "string",
    "analysis_status": "string", "skip_reason": "string",
    "source_observations": "int64", "prepared_observations": "int64", "removed_observations": "int64",
    "train_observations": "int64", "held_observations": "int64", "tail_threshold": "double",
    "minimum": "double", "maximum": "double", "mean": "double", "std_dev": "double",
    "skewness": "double", "excess_kurtosis": "double",
}
DIM_DISTRIBUTION_COLUMNS = {
    "distribution_id": "string", "distribution_name": "string", "support_type": "string",
    "tail_behaviour": "string", "shape_parameter_count": "int64", "parameter_count": "int64",
    "parameter_names": "string",
}
DIM_RUN_COLUMNS = {
    "run_id": "string", "created_utc": "string", "schema_version": "int64", "seed": "int64",
    "held_out_fraction": "double", "histogram_bins": "int64", "outlier_method": "string",
    "outlier_threshold": "double", "ks_alpha": "double", "candidate_count": "int64",
    "numpy_version": "string", "scipy_version": "string", "pandas_version": "string",
}
TABLES = {"fact_fit": FACT_COLUMNS, "dim_dataset": DIM_DATASET_COLUMNS,
          "dim_distribution": DIM_DISTRIBUTION_COLUMNS, "dim_run": DIM_RUN_COLUMNS}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_") or "dataset"


def distribution_ids():
    """Map DistroFit display names to stable SciPy-based identifiers."""
    return {name: dist.name for name, dist in get_supported_distributions().items()}


def build_dim_distribution():
    rows = []
    for name, dist in get_supported_distributions().items():
        shapes = [s.strip() for s in (dist.shapes or "").split(",") if s.strip()]
        rows.append({"distribution_id": dist.name, "distribution_name": name,
                     "support_type": _SUPPORT[dist.name],
                     "tail_behaviour": "Heavy" if dist.name in _HEAVY_TAILED else "Light",
                     "shape_parameter_count": len(shapes), "parameter_count": len(shapes) + 2,
                     "parameter_names": ", ".join(shapes + ["loc", "scale"])})
    return pd.DataFrame(rows)


def _describe(clean):
    if len(clean) == 0:
        return {k: None for k in ("minimum", "maximum", "mean", "std_dev", "skewness", "excess_kurtosis")}
    constant = np.ptp(clean) == 0 or len(clean) < 3
    return {"minimum": float(clean.min()), "maximum": float(clean.max()), "mean": float(clean.mean()),
            "std_dev": float(clean.std(ddof=1)) if len(clean) > 1 else None,
            "skewness": None if constant else float(stats.skew(clean, bias=False)),
            "excess_kurtosis": None if constant else float(stats.kurtosis(clean, bias=False))}


def _rank(series, ascending=True):
    """Competition rank (1 = best, ties share a rank); NaN stays null, +inf ranks last."""
    return series.rank(method="min", ascending=ascending, na_option="keep")


def _fit_rows(run_id, dataset_id, fit, ids, ks_alpha):
    supported = get_supported_distributions()
    n_train, n_held = len(fit["train_indices"]), len(fit["held_indices"])
    held = fit["data"][fit["held_indices"]]
    rows = []
    for result in fit["results"]:
        name, params = result["Distribution"], list(result["Parameters"])
        shapes = params[:-2]
        ks = stats.kstest(held, supported[name].cdf, args=tuple(params))
        held_nll = result["Held-out NLL"]
        tail = result["Tail"]
        rows.append({
            "run_id": run_id, "dataset_id": dataset_id, "distribution_id": ids[name],
            "fit_status": "fitted" if math.isfinite(held_nll) else "heldout_outside_support",
            "failure_reason": None if math.isfinite(held_nll)
            else "Held-out observations fall outside the fitted support",
            "shape_1": shapes[0] if len(shapes) > 0 else None,
            "shape_2": shapes[1] if len(shapes) > 1 else None,
            "loc": params[-2], "scale": params[-1], "parameter_count": len(params),
            "train_observations": n_train, "held_observations": n_held,
            "train_nll": result["Train NLL"], "log_likelihood": -n_train * result["Train NLL"],
            "aic": result["AIC"], "bic": result["BIC"],
            # +inf is kept in a private column for ranking and exported as null.
            "heldout_nll": held_nll if math.isfinite(held_nll) else None, "_heldout_sort": held_nll,
            "sse": result["SSE"], "ks_statistic": float(ks.statistic), "ks_p_value": float(ks.pvalue),
            "ks_pass": bool(ks.pvalue >= ks_alpha),
            "tail_model_share": tail["model_share"], "tail_observed_share": tail["observed_share"],
            "tail_flagged": bool(tail["flagged"])})
    for name, message in fit["errors"].items():
        rows.append({"run_id": run_id, "dataset_id": dataset_id, "distribution_id": ids[name],
                     "fit_status": "failed", "failure_reason": message,
                     "train_observations": n_train, "held_observations": n_held})
    frame = pd.DataFrame(rows).reindex(columns=list(FACT_COLUMNS) + ["_heldout_sort"])
    ok = frame["fit_status"] != "failed"
    frame["rank_heldout_nll"] = _rank(frame["_heldout_sort"].where(ok))
    frame["rank_aic"] = _rank(frame["aic"])
    frame["rank_bic"] = _rank(frame["bic"])
    frame["is_best_fit"] = frame["rank_heldout_nll"] == 1
    frame["delta_aic"] = frame["aic"] - frame["aic"].min()
    frame["delta_bic"] = frame["bic"] - frame["bic"].min()
    frame["delta_heldout_nll"] = frame["heldout_nll"] - frame["heldout_nll"].min()
    weights = np.exp(-frame["delta_aic"] / 2)
    frame["akaike_weight"] = weights / weights.sum()
    return frame.drop(columns="_heldout_sort")


def _normalise(frame, columns):
    """Return `frame` with exactly the declared columns, order and nullable types."""
    frame = frame.reindex(columns=list(columns))
    for column, kind in columns.items():
        if kind == "int64":
            frame[column] = frame[column].astype("Int64")
        elif kind == "double":
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("float64")
        elif kind == "bool":
            frame[column] = frame[column].astype("boolean")
        else:
            frame[column] = frame[column].astype("object").where(frame[column].notna(), None)
    return frame.reset_index(drop=True)


def build_star_schema(datasets, candidates=None, seed=42, held_out_fraction=.25, bins=30,
                      outlier_method="None", outlier_threshold=3., ks_alpha=KS_ALPHA, created_utc=None):
    """Fit every dataset and return the four star-schema tables as DataFrames.

    ``datasets`` is a sequence of dicts with ``dataset_id`` (optional slug),
    ``dataset_name``, ``values`` and optional ``source``/``variable``. Datasets
    that cannot be fitted (fewer than eight finite varying values) are kept in
    ``dim_dataset`` with ``analysis_status == "skipped"`` and the reason.
    """
    import scipy
    candidates = list(candidates or get_supported_distributions())
    ids = distribution_ids()
    unknown = [c for c in candidates if c not in ids]
    if unknown:
        raise ValueError(f"Unknown distribution(s): {', '.join(unknown)}")
    if not datasets:
        raise ValueError("Provide at least one dataset.")
    created = created_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    config = f"{SCHEMA_VERSION}|{seed}|{held_out_fraction}|{bins}|{outlier_method}|{outlier_threshold}|{sorted(candidates)}"
    run_id = hashlib.sha256(f"{config}|{created}".encode()).hexdigest()[:12]

    dim_rows, fact_frames, seen = [], [], set()
    for item in datasets:
        dataset_id = item.get("dataset_id") or slugify(item["dataset_name"])
        if dataset_id in seen:
            raise ValueError(f"Duplicate dataset_id: {dataset_id}")
        seen.add(dataset_id)
        raw = np.asarray(item["values"], dtype=float)
        clean, removed = prepare_data(raw, outlier_method, outlier_threshold)
        row = {"dataset_id": dataset_id, "dataset_name": item["dataset_name"],
               "source": item.get("source"), "variable": item.get("variable"),
               "source_observations": len(raw), "prepared_observations": len(clean),
               "removed_observations": removed, **_describe(clean)}
        try:
            fit = fit_candidates(clean, candidates, bins=bins, validation_fraction=held_out_fraction, seed=seed)
        except ValueError as error:
            dim_rows.append({**row, "analysis_status": "skipped", "skip_reason": str(error)})
            continue
        dim_rows.append({**row, "analysis_status": "fitted", "skip_reason": None,
                         "train_observations": len(fit["train_indices"]),
                         "held_observations": len(fit["held_indices"]),
                         "tail_threshold": fit["tail_threshold"]})
        fact_frames.append(_fit_rows(run_id, dataset_id, fit, ids, ks_alpha))

    run = {"run_id": run_id, "created_utc": created, "schema_version": SCHEMA_VERSION, "seed": seed,
           "held_out_fraction": held_out_fraction, "histogram_bins": bins,
           "outlier_method": outlier_method,
           "outlier_threshold": outlier_threshold if outlier_method == "Z-Score" else None,
           "ks_alpha": ks_alpha, "candidate_count": len(candidates), "numpy_version": np.__version__,
           "scipy_version": scipy.__version__, "pandas_version": pd.__version__}
    fact = pd.concat(fact_frames) if fact_frames else pd.DataFrame(columns=list(FACT_COLUMNS))
    return {"fact_fit": _normalise(fact, FACT_COLUMNS),
            "dim_dataset": _normalise(pd.DataFrame(dim_rows), DIM_DATASET_COLUMNS),
            "dim_distribution": _normalise(build_dim_distribution(), DIM_DISTRIBUTION_COLUMNS),
            "dim_run": _normalise(pd.DataFrame([run]), DIM_RUN_COLUMNS)}


def _arrow_table(frame, columns):
    import pyarrow as pa
    types = {"string": pa.string(), "double": pa.float64(), "int64": pa.int64(), "bool": pa.bool_()}
    schema = pa.schema([(name, types[kind]) for name, kind in columns.items()])
    arrays = [pa.array(frame[name].astype(object).where(frame[name].notna(), None).tolist(), type=schema.field(name).type)
              for name in columns]
    return pa.Table.from_arrays(arrays, schema=schema)


def write_star_schema(tables, out_dir, formats=("csv", "parquet")):
    """Write each table as ``<out_dir>/<format>/<table>.<format>``; return the paths."""
    unknown = set(formats) - {"csv", "parquet"}
    if unknown:
        raise ValueError(f"Unsupported format(s): {', '.join(sorted(unknown))}")
    written = []
    for fmt in formats:
        folder = Path(out_dir) / fmt
        folder.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            path = folder / f"{name}.{fmt}"
            if fmt == "csv":
                # Plain UTF-8 and ISO values load cleanly in Power BI's Text/CSV connector.
                frame.to_csv(path, index=False, lineterminator="\n")
            else:
                import pyarrow.parquet as pq
                pq.write_table(_arrow_table(frame, TABLES[name]), path, compression="snappy")
            written.append(path)
    return written


def reference_measures(tables):
    """Pandas equivalents of the DAX measures in powerbi/measures.dax.

    Used by the tests and written beside the sample export, so numbers shown in
    Power BI can be checked against an independent calculation.
    """
    fact, dists = tables["fact_fit"], tables["dim_distribution"]
    fitted = fact[fact["fit_status"] != "failed"]
    datasets = fact["dataset_id"].nunique()
    rows = []
    for _, dist in dists.iterrows():
        mine = fitted[fitted["distribution_id"] == dist["distribution_id"]]
        every = fact[fact["distribution_id"] == dist["distribution_id"]]
        rows.append({
            "distribution_id": dist["distribution_id"], "distribution_name": dist["distribution_name"],
            "datasets_fitted": mine["dataset_id"].nunique(),
            "best_fit_count": int(mine["is_best_fit"].fillna(False).sum()),
            "best_fit_share": float(mine["is_best_fit"].fillna(False).sum() / datasets) if datasets else None,
            "avg_delta_aic": float(mine["delta_aic"].mean()) if len(mine) else None,
            "ks_pass_rate": float(mine["ks_pass"].fillna(False).mean()) if len(mine) else None,
            "fit_success_rate": float(len(mine) / len(every)) if len(every) else None})
    return pd.DataFrame(rows)


def load_sample_datasets(folder):
    """Read ``dataset_catalog.csv`` + ``public_datasets.csv`` from `folder`."""
    folder = Path(folder)
    catalog = pd.read_csv(folder / "dataset_catalog.csv")
    values = pd.read_csv(folder / "public_datasets.csv")
    return [{"dataset_id": row.dataset_id, "dataset_name": row.dataset_name, "source": row.source,
             "variable": row.variable,
             "values": values.loc[values["dataset_id"] == row.dataset_id, "value"].to_numpy()}
            for row in catalog.itertuples()]


def load_csv_datasets(path, columns=None, source=None):
    """Each numeric column of a CSV becomes one dataset."""
    from analysis import read_csv
    with open(path, "rb") as handle:
        frame = read_csv(handle)
    numeric = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c])]
    chosen = list(columns) if columns else numeric
    missing = [c for c in chosen if c not in numeric]
    if missing:
        raise ValueError(f"Not numeric columns in {Path(path).name}: {', '.join(map(str, missing))}")
    if not chosen:
        raise ValueError(f"No numeric columns found in {Path(path).name}")
    stem = Path(path).stem
    return [{"dataset_id": slugify(f"{stem}_{c}"), "dataset_name": f"{stem}: {c}",
             "source": source or Path(path).name, "variable": str(c),
             "values": frame[c].to_numpy(dtype=float)} for c in chosen]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export DistroFit fits as a Power BI star schema.")
    parser.add_argument("csv", nargs="*", help="numeric CSV file(s); each numeric column becomes a dataset")
    parser.add_argument("--column", action="append", help="limit to this column (repeatable)")
    parser.add_argument("--sample", action="store_true",
                        help="export the bundled public datasets in powerbi/sample_data")
    parser.add_argument("--out", default="powerbi_export", help="output folder (default: powerbi_export)")
    parser.add_argument("--format", choices=["csv", "parquet", "both"], default="both")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--held-out-fraction", type=float, default=.25)
    parser.add_argument("--bins", type=int, default=30)
    parser.add_argument("--outliers", choices=["None", "Z-Score", "IQR"], default="None")
    parser.add_argument("--created-utc", help="timestamp stored in dim_run (default: now)")
    args = parser.parse_args(argv)
    if not args.csv and not args.sample:
        parser.error("give at least one CSV file or --sample")
    datasets = []
    if args.sample:
        datasets += load_sample_datasets(Path(__file__).resolve().parent / "powerbi" / "sample_data")
    for path in args.csv:
        datasets += load_csv_datasets(path, args.column)
    tables = build_star_schema(datasets, seed=args.seed, held_out_fraction=args.held_out_fraction,
                               bins=args.bins, outlier_method=args.outliers, created_utc=args.created_utc)
    formats = ("csv", "parquet") if args.format == "both" else (args.format,)
    paths = write_star_schema(tables, args.out, formats)
    reference_measures(tables).to_csv(Path(args.out) / "reference_measures.csv", index=False, lineterminator="\n")
    fact = tables["fact_fit"]
    print(f"Wrote {len(paths)} files to {args.out}: {len(fact)} fits across "
          f"{fact['dataset_id'].nunique()} datasets, {int((fact['fit_status'] == 'failed').sum())} failed fits.")
    skipped = tables["dim_dataset"].query("analysis_status == 'skipped'")
    for row in skipped.itertuples():
        print(f"Skipped {row.dataset_id}: {row.skip_reason}", file=sys.stderr)


if __name__ == "__main__":
    main()
