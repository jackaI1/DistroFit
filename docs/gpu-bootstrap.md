# Bootstrap likelihoods on the CPU or a GPU

`gpu_bootstrap.py` computes bootstrap intervals for the 14 candidate curves in
`analysis.py`. `bench_bootstrap.py` times the CPU path and, when a GPU is present, the
GPU path.

## What is computed

1. The data are fitted once per candidate with scipy's maximum-likelihood fit. Candidates
   whose fit fails, or whose support excludes some data, are listed under `excluded`.
2. `resamples` bootstrap samples, each the same size as the data and drawn with
   replacement, are generated from a fixed seed.
3. For each candidate and each resample, the total log-likelihood is computed with the
   fitted parameters. The per-observation mean is the score.
4. The table gives the score on the full sample, a percentile interval (2.5% to 97.5% by
   default) over resamples, the standard error and the **win share**: the fraction of
   resamples in which that candidate has the highest total log-likelihood.

Limitation: parameters are not refitted for each resample. The intervals show how much each
candidate's score moves with the data. They do not show how much its parameters move.
Refitting 14 curves for every resample would be the more complete bootstrap, and the
backend is structured so that the fitting step could be moved to the GPU later.

## Backends

- `backend="cpu"` evaluates scipy's `logpdf` on the resample matrix. It is the default and
  the reference.
- `backend="gpu"` runs a CUDA kernel through CuPy. The kernel holds the standardised
  log-density for each of the 14 families and applies the scale Jacobian. It needs an
  NVIDIA GPU and `requirements-gpu.txt`.
- `backend="auto"` uses the GPU when CuPy reports a device and the CPU otherwise.
  Requesting `gpu` without a GPU raises an error with the reason.

The formulas in the kernel are checked on the CPU against scipy for all 14 families in
`tests/test_gpu_bootstrap.py`, through `standard_logpdf_reference`, which mirrors the
kernel line by line. The GPU-versus-CPU agreement test runs only on a machine with a GPU.

## Benchmark

```sh
python bench_bootstrap.py --sizes 200 1000 5000 --resamples 1000 --out .runtime/bench
```

The output folder holds `benchmark.csv` and `benchmark.json`, with the machine details.
Timings cover likelihood evaluation only. Sizes and resample counts can be changed on the
command line.

Measured on an Apple M-series Mac with the CPU backend, 1,000 resamples, 14 candidates,
median of 3 runs:

| sample size | CPU time |
|---|---|
| 200 | 0.04 s |
| 1,000 | 0.19 s |
| 5,000 | 0.94 s |

No GPU timings have been recorded yet. Hosted continuous integration (CI) runners have no GPU,
so the benchmark step in CI records CPU timings only.
