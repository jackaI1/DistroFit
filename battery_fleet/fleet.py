"""Measured cycle features and past-only, trend-aware robust fleet screening."""

import numpy as np
import pandas as pd
from scipy.stats import theilslopes


def amp_hours(time_s, current_a):
    time_s, current_a = np.asarray(time_s), np.asarray(current_a)
    if (
        time_s.ndim != 1
        or time_s.shape != current_a.shape
        or len(time_s) < 2
        or not np.isfinite(time_s).all()
        or not np.isfinite(current_a).all()
        or (np.diff(time_s) <= 0).any()
    ):
        raise ValueError(
            "Finite equally sized arrays with strictly increasing seconds required"
        )
    return float(np.trapezoid(current_a, time_s) / 3600)


def cycle_metrics(discharge, charge=None):
    # NASA uses negative current for discharge. Ignore brief opposite-sign switching spikes.
    capacity = amp_hours(discharge.time_s, np.maximum(-discharge.current_a, 0))
    charged = (
        amp_hours(charge.time_s, np.maximum(charge.current_a, 0))
        if charge is not None
        else np.nan
    )
    # A top-up from an already charged cell has no matching full charge input.
    charge_complete = bool(
        charge is not None
        and charge.loc[charge.time_s.le(60), "voltage_v"].min() <= 3.6
        and charge.voltage_v.iloc[-1] >= 4.15
        and charged >= 0.5 * capacity
    )
    start = discharge.loc[discharge.time_s.le(60)]
    di = np.diff(start.current_a)
    dv = np.diff(start.voltage_v)
    transitions = (di < -0.5) & (dv < 0)
    resistance = (
        float(np.median(dv[transitions] / di[transitions]))
        if transitions.any()
        else np.nan
    )
    return dict(
        capacity_ah=capacity,
        charge_ah=charged,
        coulombic_efficiency=(
            capacity / charged if charge_complete and charged > 0 else np.nan
        ),
        charge_pair_complete=charge_complete,
        resistance_proxy_ohm=resistance,
        peak_temperature_c=float(discharge.temperature_c.max()),
    )


FEATURES = {
    "capacity_ah": 0.01,
    "coulombic_efficiency": 0.005,
    "resistance_proxy_ohm": 0.005,
    "peak_temperature_c": 0.5,
}


def analyze_cycles(frame, window=20, minimum=8, threshold=5.0):
    if minimum < 3 or window < minimum or threshold <= 0:
        raise ValueError("Require window >= minimum >= 3 and positive threshold")
    if frame.duplicated(["cell", "cycle"]).any():
        raise ValueError("Duplicate cell/cycle identity")
    out = frame.sort_values(["cell", "cycle"]).copy().reset_index(drop=True)
    if out.empty:
        raise ValueError("No cycles to analyze")
    out["flag_reasons"] = ""
    out["max_robust_score"] = 0.0
    out["baseline_ready"] = False
    summaries = []
    for cell, group in out.groupby("cell", sort=True):
        indices = group.index.to_list()
        initial = float(group.capacity_ah.head(3).median())
        if not np.isfinite(initial) or initial <= 0:
            raise ValueError("Positive initial capacity required")
        out.loc[indices, "retention_pct"] = 100 * group.capacity_ah / initial
        for position, idx in enumerate(indices):
            history = out.loc[indices[max(0, position - window) : position]]
            if len(history) < minimum:
                continue
            out.loc[idx, "baseline_ready"] = True
            reasons, scores = [], []
            for feature, floor in FEATURES.items():
                past = history[["cycle", feature]].dropna()
                value = out.loc[idx, feature]
                if len(past) < minimum or not np.isfinite(value):
                    continue
                slope, intercept, *_ = theilslopes(past[feature], past.cycle)
                residuals = past[feature] - (intercept + slope * past.cycle)
                centre = float(np.median(residuals))
                scale = max(floor, 1.4826 * float(np.median(abs(residuals - centre))))
                score = (
                    abs(value - (intercept + slope * out.loc[idx, "cycle"]) - centre)
                    / scale
                )
                scores.append(score)
                if score > threshold:
                    reasons.append(feature)
            out.loc[idx, "flag_reasons"] = ", ".join(reasons)
            out.loc[idx, "max_robust_score"] = max(scores, default=0)
        split = max(3, int(0.6 * len(group)))
        train = group.iloc[:split]
        slope, intercept, *_ = theilslopes(train.capacity_ah, train.cycle)
        held = group.iloc[split:]
        predicted = intercept + slope * group.cycle
        out.loc[indices, "trend_capacity_ah"] = predicted
        recent = out.loc[indices[-window:]]
        flagged = recent.flag_reasons.ne("").mean()
        final_retention = float(out.loc[indices[-1], "retention_pct"])
        summaries.append(
            dict(
                cell=cell,
                cycles=len(group),
                initial_capacity_ah=initial,
                final_retention_pct=final_retention,
                trend_ah_per_cycle=float(slope),
                train_cycles=len(train),
                heldout_mae_ah=(
                    float(
                        abs(held.capacity_ah - (intercept + slope * held.cycle)).mean()
                    )
                    if len(held)
                    else None
                ),
                flagged_cycles=int(out.loc[indices, "flag_reasons"].ne("").sum()),
                recent_flag_fraction=float(flagged),
                flagged_cell=bool(flagged >= 0.2 or final_retention < 70),
            )
        )
    out["flagged_cycle"] = out.flag_reasons.ne("")
    summary = pd.DataFrame(summaries)
    # Compare like-for-like normalized fade rates, with a physical floor and robust centre.
    slopes = summary.trend_ah_per_cycle / summary.initial_capacity_ah
    centre = float(slopes.median())
    scale = max(0.0005, 1.4826 * float(abs(slopes - centre).median()))
    summary["peer_fade_score"] = abs(slopes - centre) / scale
    summary["flagged_cell"] |= summary.peer_fade_score.gt(threshold)
    return out, summary
