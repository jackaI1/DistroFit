"""Numerical acceptance limits for the complete public-data run, not mock outputs."""

import json
import sys
from pathlib import Path


def check(path):
    results = json.loads(Path(path).read_text())
    assert results["fleet"]["cycles"] == 504
    assert results["fleet"]["cells"] == 3
    assert not results["rejected_phases"]
    fit = results["calibration"]
    assert fit["converged"] and not fit["at_bound"]
    assert fit["training_rate"] == 1.0
    assert fit["weighted_sse"] < fit["initial_weighted_sse"]
    errors = results["model_errors"]
    assert len(errors) == 12
    held = [e for e in errors if e["split"] == "held-out rate"]
    assert len(held) == 9 and {e["rate"] for e in held} == {0.1, 0.5, 1.5}
    assert all(
        e["voltage_rmse_v"] < 0.12
        and e["temperature_rmse_k"] < 5
        and e["time_coverage"] > 0.9
        and e["compared_points"] >= 90
        for e in held
    )
    sweep = results["cooling_sweep"]
    assert len(sweep) == 5
    assert all(
        a["peak_temperature_c"] > b["peak_temperature_c"]
        for a, b in zip(sweep, sweep[1:])
    )
    print(
        f"504 cycles; 9 held-out curves; worst errors {max(e['voltage_rmse_v'] for e in held):.4f} V, "
        f"{max(e['temperature_rmse_k'] for e in held):.2f} K"
    )


if __name__ == "__main__":
    check(sys.argv[1])
