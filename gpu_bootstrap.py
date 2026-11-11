"""Bootstrap intervals for the 14 candidate curves, evaluated on the CPU or on an NVIDIA GPU.

A bootstrap resample is a sample of the same size drawn with replacement from my data.
For each candidate curve I evaluate its log-likelihood (how probable the data are under
that curve) on every resample. Bootstrap intervals come from the spread across resamples.

The curves are fitted once on the full sample, with scipy's maximum-likelihood fit. The
resamples then reuse those fitted parameters, so the intervals show how much the score of
each curve moves with the data, not how much its parameters move. That makes the work a
large batch of likelihood evaluations, which is what the GPU runs in parallel.

Backends:

* ``cpu`` (default when no GPU is found) calls scipy's ``logpdf`` on the resample matrix.
* ``gpu`` uses CuPy with a custom CUDA kernel. It needs ``requirements-gpu.txt``, an NVIDIA
  GPU and a CUDA driver. The kernel holds closed-form log-densities for the same 14
  families, written in the same parameterisation as scipy's standardised distributions.
* ``auto`` uses the GPU when CuPy reports a device and falls back to the CPU otherwise.

The random resamples are drawn on the CPU from a fixed seed, so both backends see the
same data and their totals should agree to floating-point rounding.
"""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from scipy import special

from analysis import get_supported_distributions

SEED = 20261111
BACKENDS = ("auto", "cpu", "gpu")
FAMILIES = list(get_supported_distributions())

# CUDA source for the standardised log-density of each family (z = (x - loc) / scale),
# with the Jacobian -log(scale) added. Parameter order: family index, z, shape 1, shape 2.
# Family indices follow FAMILIES above. Unused shapes are passed as 0.
_KERNEL_SOURCE = r"""
__device__ double family_logpdf(int f, double z, double s1, double s2) {
    const double LOG_SQRT_2PI = 0.9189385332046727;
    const double LOG_PI = 1.1447298858494002;
    const double LOG_2 = 0.6931471805599453;
    const double NEG_INF = -1.0 / 0.0;
    switch (f) {
        case 0: return -0.5 * z * z - LOG_SQRT_2PI;
        case 1: if (z <= 0.0) return NEG_INF;
                return (s1 - 1.0) * log(z) - z - lgamma(s1);
        case 2: if (z <= 0.0) return NEG_INF;
                return log(s1) + (s1 - 1.0) * log(z) - pow(z, s1);
        case 3: if (z < 0.0) return NEG_INF;
                return -z;
        case 4: if (z <= 0.0) return NEG_INF;
                return -log(z) - log(s1) - LOG_SQRT_2PI - (log(z) * log(z)) / (2.0 * s1 * s1);
        case 5: if (z <= 0.0 || z >= 1.0) return NEG_INF;
                return (s1 - 1.0) * log(z) + (s2 - 1.0) * log1p(-z)
                       - (lgamma(s1) + lgamma(s2) - lgamma(s1 + s2));
        case 6: if (z < 0.0 || z > 1.0) return NEG_INF;
                return 0.0;
        case 7: return lgamma((s1 + 1.0) / 2.0) - lgamma(s1 / 2.0) - 0.5 * log(s1 * 3.141592653589793)
                       - ((s1 + 1.0) / 2.0) * log1p(z * z / s1);
        case 8: if (z < 0.0) return NEG_INF;
                return (s1 / 2.0 - 1.0) * log(z) - z / 2.0 - (s1 / 2.0) * LOG_2 - lgamma(s1 / 2.0);
        case 9: return -LOG_PI - log1p(z * z);
        case 10: if (z < 1.0) return NEG_INF;
                 return log(s1) - (s1 + 1.0) * log(z);
        case 11: return -fabs(z) - 2.0 * log1p(exp(-fabs(z)));
        case 12: return -fabs(z) - LOG_2;
        case 13: if (z < 0.0) return NEG_INF;
                 return 0.5 * (LOG_2 - LOG_PI) + 2.0 * log(z) - z * z / 2.0;
        default: return NEG_INF;
    }
}

extern "C" __global__ void standard_logpdf(const double* x, double* out, const long long total,
                                           const int family, const double loc, const double scale,
                                           const double s1, const double s2) {
    long long i = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (i >= total) return;
    double z = (x[i] - loc) / scale;
    out[i] = family_logpdf(family, z, s1, s2) - log(scale);
}
"""

_gpu_state = {"checked": False, "available": False, "kernel": None, "cupy": None, "reason": ""}


def _gpu_available():
    """True when CuPy imports and reports at least one CUDA device. The answer is cached."""
    if not _gpu_state["checked"]:
        _gpu_state["checked"] = True
        try:
            import cupy
            if cupy.cuda.runtime.getDeviceCount() < 1:
                raise RuntimeError("no CUDA device")
            _gpu_state.update(available=True, cupy=cupy)
        except Exception as error:  # ImportError, CUDA driver errors, or no device
            _gpu_state.update(available=False, reason=f"{type(error).__name__}: {error}")
    return _gpu_state["available"]


def _gpu_kernel():
    if _gpu_state["kernel"] is None:
        _gpu_state["kernel"] = _gpu_state["cupy"].RawKernel(_KERNEL_SOURCE, "standard_logpdf")
    return _gpu_state["kernel"]


def standard_logpdf_reference(family, z, s1=0., s2=0.):
    """NumPy version of the CUDA kernel's formulas, used to check the kernel's maths on the CPU.

    ``family`` is the index in FAMILIES. This mirrors ``family_logpdf`` line for line.
    """
    z = np.asarray(z, dtype=float)
    neg_inf = -np.inf
    log_sqrt_2pi = 0.9189385332046727
    log_pi = 1.1447298858494002
    log_2 = 0.6931471805599453
    with np.errstate(divide="ignore", invalid="ignore"):
        if family == 0:
            return -0.5 * z * z - log_sqrt_2pi
        if family == 1:
            return np.where(z <= 0, neg_inf, (s1 - 1) * np.log(z) - z - special.gammaln(s1))
        if family == 2:
            return np.where(z <= 0, neg_inf, np.log(s1) + (s1 - 1) * np.log(z) - z ** s1)
        if family == 3:
            return np.where(z < 0, neg_inf, -z)
        if family == 4:
            lz = np.log(z)
            return np.where(z <= 0, neg_inf, -lz - np.log(s1) - log_sqrt_2pi - lz * lz / (2 * s1 * s1))
        if family == 5:
            value = ((s1 - 1) * np.log(z) + (s2 - 1) * np.log1p(-z)
                     - (special.gammaln(s1) + special.gammaln(s2) - special.gammaln(s1 + s2)))
            return np.where((z <= 0) | (z >= 1), neg_inf, value)
        if family == 6:
            return np.where((z < 0) | (z > 1), neg_inf, 0.)
        if family == 7:
            return (special.gammaln((s1 + 1) / 2) - special.gammaln(s1 / 2) - 0.5 * np.log(s1 * np.pi)
                    - ((s1 + 1) / 2) * np.log1p(z * z / s1))
        if family == 8:
            return np.where(z < 0, neg_inf, (s1 / 2 - 1) * np.log(z) - z / 2 - (s1 / 2) * log_2
                            - special.gammaln(s1 / 2))
        if family == 9:
            return -log_pi - np.log1p(z * z)
        if family == 10:
            return np.where(z < 1, neg_inf, np.log(s1) - (s1 + 1) * np.log(z))
        if family == 11:
            return -np.abs(z) - 2 * np.log1p(np.exp(-np.abs(z)))
        if family == 12:
            return -np.abs(z) - log_2
        if family == 13:
            return np.where(z < 0, neg_inf, 0.5 * (log_2 - log_pi) + 2 * np.log(z) - z * z / 2)
    raise ValueError(f"unknown family index {family}")


def _split(dist, params):
    """Shape parameters, location and scale from a scipy fit, padded to two shapes for the kernel."""
    params = [float(p) for p in params]
    shapes = params[:dist.numargs]
    loc, scale = params[-2], params[-1]
    padded = (shapes + [0., 0.])[:2]
    return shapes, loc, scale, padded


def fit_candidates(values, names=None):
    """Maximum-likelihood fit of each candidate on the full sample.

    Returns a table of parameters and point log-likelihoods, plus the names excluded
    because the fit failed or the data fall outside the curve's support.
    """
    data = np.asarray(values, dtype=float)
    if data.ndim != 1 or data.size < 3 or not np.all(np.isfinite(data)):
        raise ValueError("Give at least three finite numbers.")
    supported = get_supported_distributions()
    rows, excluded = [], {}
    for name in (names or FAMILIES):
        dist = supported[name]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                params = dist.fit(data)
        except Exception as error:  # scipy raises several types for failed fits
            excluded[name] = f"fit failed: {error}"
            continue
        loglik = float(np.sum(dist.logpdf(data, *params)))
        if not np.isfinite(loglik):
            excluded[name] = "data fall outside the fitted support"
            continue
        rows.append({"distribution": name, "family": FAMILIES.index(name), "params": tuple(params),
                     "loglik": loglik})
    return pd.DataFrame(rows), excluded


def _totals_cpu(dist, params, matrix):
    return dist.logpdf(matrix, *params).sum(axis=1)


def _totals_gpu(family, shapes_padded, loc, scale, matrix):
    cp = _gpu_state["cupy"]
    kernel = _gpu_kernel()
    flat = cp.ascontiguousarray(matrix.reshape(-1))
    out = cp.empty_like(flat)
    total = np.int64(flat.size)
    threads = 256
    blocks = (int(total) + threads - 1) // threads
    kernel((blocks,), (threads,),
           (flat, out, total, np.int32(family), np.float64(loc), np.float64(scale),
            np.float64(shapes_padded[0]), np.float64(shapes_padded[1])))
    return out.reshape(matrix.shape).sum(axis=1)


def resample_indices(n, resamples, seed=SEED):
    """Row indices for ``resamples`` bootstrap samples of size ``n``, drawn with replacement."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, size=(resamples, n))


def bootstrap_loglik(values, *, resamples=1000, seed=SEED, backend="auto", names=None, ci=.95):
    """Bootstrap log-likelihood per candidate: point score, interval and bootstrap win share.

    Returns a dict with a ``table`` (one row per candidate), the ``backend`` actually used,
    the ``excluded`` candidates and the wall-clock ``seconds`` spent on likelihood evaluation.
    """
    if backend not in BACKENDS:
        raise ValueError(f"backend must be one of {BACKENDS}.")
    if resamples < 1:
        raise ValueError("resamples must be at least 1.")
    if backend == "gpu" and not _gpu_available():
        raise RuntimeError(f"No CUDA GPU is available for backend='gpu' ({_gpu_state['reason'] or 'not checked'}). "
                           "Use backend='cpu' or install requirements-gpu.txt on a machine with an NVIDIA GPU.")
    chosen = "gpu" if backend == "gpu" or (backend == "auto" and _gpu_available()) else "cpu"

    data = np.asarray(values, dtype=float)
    fits, excluded = fit_candidates(data, names)
    supported = get_supported_distributions()
    indices = resample_indices(data.size, resamples, seed)
    matrix = data[indices]
    if chosen == "gpu":
        cp = _gpu_state["cupy"]
        gpu_matrix = cp.asarray(matrix)

    totals = {}
    seconds = 0.
    for row in fits.itertuples(index=False):
        dist = supported[row.distribution]
        start = time.perf_counter()
        if chosen == "gpu":
            shapes, loc, scale, padded = _split(dist, row.params)
            value = _totals_gpu(row.family, padded, loc, scale, gpu_matrix)
            totals[row.distribution] = cp.asnumpy(value)
        else:
            totals[row.distribution] = _totals_cpu(dist, row.params, matrix)
        seconds += time.perf_counter() - start

    rows = []
    stacked = np.column_stack([totals[name] for name in fits["distribution"]]) if len(fits) else np.empty((resamples, 0))
    winners = stacked.argmax(axis=1) if len(fits) else np.array([], dtype=int)
    tail = (1 - ci) / 2
    for position, row in enumerate(fits.itertuples(index=False)):
        per_obs = totals[row.distribution] / data.size
        rows.append({
            "distribution": row.distribution,
            "parameters": [round(p, 6) for p in row.params],
            "mean_loglik": row.loglik / data.size,
            "boot_ci_low": float(np.quantile(per_obs, tail)),
            "boot_ci_high": float(np.quantile(per_obs, 1 - tail)),
            "boot_se": float(np.std(per_obs, ddof=1)) if resamples > 1 else float("nan"),
            "win_share": float(np.mean(winners == position)) if len(winners) else float("nan"),
        })
    table = pd.DataFrame(rows).sort_values("mean_loglik", ascending=False).reset_index(drop=True)
    return {"table": table, "backend": chosen, "excluded": excluded, "seconds": seconds,
            "resamples": int(resamples), "n": int(data.size), "seed": int(seed)}


def gpu_info():
    """Device name and memory for the benchmark report, or None when no GPU is found."""
    if not _gpu_available():
        return None
    cp = _gpu_state["cupy"]
    props = cp.cuda.runtime.getDeviceProperties(cp.cuda.runtime.getDevice())
    name = props["name"]
    return {"name": name.decode() if isinstance(name, bytes) else str(name),
            "memory_gb": round(cp.cuda.runtime.memGetInfo()[1] / 1e9, 2)}
