"""Reproduces every number in docs/case-study-dmaic.md.

ALL DATA HERE IS ILLUSTRATIVE. It is generated from a seeded random number
generator to resemble a drawing-revision review whose typical time fell from
about 2 hours to about 30 minutes after automation. It is not D.L. Engineering
data. Run from the repository root:  python docs/dmaic_case_study.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analysis  # noqa: E402
import spc  # noqa: E402

USL_MINUTES = 60.0          # assumed requirement: review finished within 1 hour
CANDIDATES = ("Normal", "Gamma", "Log-Normal", "Weibull (Min)")
SUBGROUPS, SUBGROUP_SIZE = 20, 5   # 20 weeks x 5 reviews per week

# Illustrative counts of review findings per 100 revision packages (before).
FINDINGS = {"Revision letter mismatch": 38, "Title block / BOM mismatch": 27,
            "Missing revision cloud": 14, "Tolerance not updated": 9,
            "Stale referenced drawing": 7, "Other": 5}


def illustrative_times():
    # Seed 2029 was picked from a scan of ten seeds because its baseline phases
    # show no false alarms; other seeds can signal by chance (see the case study).
    rng = np.random.default_rng(2029)
    before = rng.gamma(shape=16, scale=7.5, size=SUBGROUPS * SUBGROUP_SIZE)   # mean ~120 min
    after = rng.gamma(shape=12, scale=2.5, size=SUBGROUPS * SUBGROUP_SIZE)    # mean ~30 min
    # Control phase: 30 stable post-improvement reviews, then 10 after an
    # (illustrative) template change adds about 15 minutes to each review.
    monitor = np.concatenate([rng.gamma(12, 2.5, 30), rng.gamma(12, 2.5, 10) + 15])
    return before, after, monitor


def describe(times):
    groups = times.reshape(SUBGROUPS, SUBGROUP_SIZE)
    chart = spc.xbar_r_chart(groups)
    fit = analysis.fit_candidates(times, CANDIDATES)
    return {"chart": chart,
            "normal": spc.capability(times, usl=USL_MINUTES, sigma_within=chart["sigma_within"]),
            "fit": fit,
            "percentile": spc.capability_from_fit(fit, usl=USL_MINUTES),
            "mean": float(times.mean()), "sd": float(times.std(ddof=1))}


def run():
    before, after, monitor = illustrative_times()
    return {"before": describe(before), "after": describe(after),
            "pareto": spc.pareto_table(FINDINGS),
            "control": spc.imr_chart(monitor, baseline=30), "monitor": monitor}


if __name__ == "__main__":
    out = run()
    for phase in ("before", "after"):
        r = out[phase]
        print(f"[{phase}] mean={r['mean']:.1f} sd={r['sd']:.1f} "
              f"Xbar-bar={r['chart']['grand_mean']:.1f} Rbar={r['chart']['r_bar']:.1f} "
              f"flagged weeks={[i + 1 for i in r['chart']['xbar']['flagged']]}")
        n, p = r["normal"], r["percentile"]
        print(f"   normal: Ppk={n['Ppk']:.2f} Cpk={n['Cpk']:.2f}")
        print(f"   best fit={p['distribution']}  Ppk={p['Ppk']:.2f}  x99.865={p['x_99.865']:.1f} "
              f"ppm>USL={p['ppm_above']:.0f}")
    print(out["pareto"].round(1).to_string(index=False))
    c = out["control"]["individuals"]
    print(f"I-MR: CL={c['center']:.1f} LCL={c['lcl']:.1f} UCL={c['ucl']:.1f}")
    print("signals:", {k: [i + 1 for i in v] for k, v in c["signals"].items()})
