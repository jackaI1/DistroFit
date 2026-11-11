"""Time the bootstrap likelihood evaluation on the CPU and, when present, on an NVIDIA GPU.

    python bench_bootstrap.py --sizes 200 1000 5000 --resamples 1000 --out .runtime/bench

For each sample size it draws a seeded Weibull sample, runs ``bootstrap_loglik`` on every
available backend, and records the median of the evaluation time over ``--repeats`` runs.
The first GPU run is a warm-up, so kernel compilation is not counted. Without a GPU the
report says so and only CPU timings are written. Timings depend on the machine they were
taken on, so compare speedups within one report, not numbers across machines.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

import gpu_bootstrap as gb


def _sample(size, seed=gb.SEED):
    rng = np.random.default_rng(seed)
    return 100 * rng.weibull(1.5, size)


def run(sizes, resamples, repeats, out):
    directory = Path(out)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"{directory} already has files; choose a new folder.")
    directory.mkdir(parents=True, exist_ok=True)
    gpu = gb.gpu_info()
    rows = []
    for size in sizes:
        values = _sample(size)
        backends = ["cpu"] + (["gpu"] if gpu else [])
        medians = {}
        for backend in backends:
            if backend == "gpu":
                gb.bootstrap_loglik(values, resamples=min(resamples, 50), backend="gpu")  # warm-up
            times = [gb.bootstrap_loglik(values, resamples=resamples, backend=backend)["seconds"]
                     for _ in range(repeats)]
            medians[backend] = statistics.median(times)
        row = {"sample_size": size, "resamples": resamples, "candidates": 14,
               "cpu_seconds": medians["cpu"], "gpu_seconds": medians.get("gpu"),
               "speedup_vs_cpu": medians["cpu"] / medians["gpu"] if "gpu" in medians else None}
        rows.append(row)
        print(f"n={size:>6}: CPU {medians['cpu']:.3f} s"
              + (f", GPU {medians['gpu']:.3f} s, speedup {row['speedup_vs_cpu']:.1f}x" if gpu else ", no GPU found"))
    table = pd.DataFrame(rows)
    table.to_csv(directory / "benchmark.csv", index=False)
    report = {"machine": {"platform": platform.platform(), "python": platform.python_version(),
                          "numpy": np.__version__, "gpu": gpu},
              "repeats": repeats, "results": rows,
              "note": "Evaluation time only; the 14 candidate fits are excluded from the timings."}
    (directory / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    return directory


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark CPU and GPU bootstrap likelihood evaluation.")
    parser.add_argument("--sizes", type=int, nargs="+", default=[200, 1000, 5000])
    parser.add_argument("--resamples", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(f"Wrote {run(args.sizes, args.resamples, args.repeats, args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
