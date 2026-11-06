"""A cylindrical LG M50 DFN model, calibrated only on 1C measured discharges."""

import os

os.environ.setdefault("PYBAMM_DISABLE_TELEMETRY", "true")
import numpy as np
from scipy.optimize import least_squares
from .fleet import amp_hours


def kelvin(value, unit="degC"):
    if unit not in ("degC", "K"):
        raise ValueError("Temperature unit must be degC or K")
    result = np.asarray(value, dtype=float) + (273.15 if unit == "degC" else 0)
    if not np.isfinite(result).all() or (result <= 0).any():
        raise ValueError("Temperature must be finite and above absolute zero")
    return result


def simulate(
    rate,
    time_s,
    ambient_k=298.15,
    initial_k=298.15,
    h=10.0,
    diffusivity_scale=1.0,
    mesh=12,
):
    import pybamm

    t = np.asarray(time_s, dtype=float)
    if (
        not np.isfinite([rate, h, diffusivity_scale]).all()
        or rate <= 0
        or h <= 0
        or diffusivity_scale <= 0
        or t.ndim != 1
        or len(t) < 2
        or t[0] != 0
        or not np.isfinite(t).all()
        or (np.diff(t) <= 0).any()
    ):
        raise ValueError(
            "Positive rate, cooling and diffusivity; increasing seconds starting at zero required"
        )
    kelvin([ambient_k, initial_k], "K")
    model = pybamm.lithium_ion.DFN(
        options={"thermal": "lumped", "calculate discharge energy": "true"}
    )
    parameters = pybamm.ParameterValues("Chen2020")
    parameters.update(
        {
            "Current function [A]": float(rate * 5),
            "Initial temperature [K]": float(initial_k),
            "Ambient temperature [K]": float(ambient_k),
            "Total heat transfer coefficient [W.m-2.K-1]": float(h),
            "Negative particle diffusivity [m2.s-1]": 3.3e-14 * diffusivity_scale,
        }
    )
    simulation = pybamm.Simulation(
        model,
        parameter_values=parameters,
        solver=pybamm.CasadiSolver(mode="safe", rtol=1e-6, atol=1e-6),
        var_pts={name: mesh for name in ("x_n", "x_s", "x_p", "r_n", "r_p")},
    )
    solution = simulation.solve(t)
    # No extrapolation past the model's low-voltage termination.
    times = t[t <= solution.t[-1]]
    if solution.t[-1] < t[-1] and solution.t[-1] > times[-1]:
        times = np.append(times, solution.t[-1])
    voltage = np.asarray(solution["Terminal voltage [V]"](times)).ravel()
    return dict(
        time_s=times,
        voltage_v=voltage,
        temperature_k=np.asarray(
            solution["Volume-averaged cell temperature [K]"](times)
        ).ravel(),
        current_a=np.full(len(times), rate * 5),
        discharge_capacity_ah=np.asarray(
            solution["Discharge capacity [A.h]"](times)
        ).ravel(),
        discharge_energy_wh=np.asarray(
            solution["Discharge energy [W.h]"](times)
        ).ravel(),
    )


def sampled_curve(curve, points=101):
    f = curve["series"]
    t = np.linspace(0, float(f.time_s.iloc[-1]), points)
    return (
        t,
        np.interp(t, f.time_s, f.voltage_v),
        np.interp(t, f.time_s, f.temperature_c) + 273.15,
    )


def predict(curve, h, diffusivity_scale, points=101):
    t, v, temp = sampled_curve(curve, points)
    result = simulate(
        curve["rate"], t, curve["ambient_k"], curve["initial_k"], h, diffusivity_scale
    )
    return t, v, temp, result


def fit_parameters(curves):
    training = [c for c in curves if c["rate"] == 1.0]
    if not training:
        raise ValueError("1C calibration curves required")

    def residual(x):
        result = []
        for curve in training:
            t, v, temp, pred = predict(curve, x[0], x[1], points=61)
            # Fixed residual size: early termination is penalized, not silently discarded.
            pv = np.interp(t, pred["time_s"], pred["voltage_v"])
            pt = np.interp(t, pred["time_s"], pred["temperature_k"])
            result.extend((pv - v) / 0.05)
            result.extend((pt - temp) / 2.0)
            result.append(max(0, t[-1] - pred["time_s"][-1]) / t[-1] * 100)
        return np.asarray(result)

    initial = residual([10.0, 1.0])
    fit = least_squares(
        residual,
        [10.0, 1.0],
        bounds=([0.5, 0.2], [50.0, 10.0]),
        diff_step=0.02,
        max_nfev=30,
        ftol=0.002,
        xtol=0.002,
    )
    if not fit.success or not np.isfinite(fit.fun).all():
        raise RuntimeError(f"Calibration did not converge: {fit.message}")
    return dict(
        h_w_m2_k=float(fit.x[0]),
        negative_diffusivity_scale=float(fit.x[1]),
        training_rate=1.0,
        training_cells=[c["cell"] for c in training],
        initial_weighted_sse=float(initial @ initial),
        weighted_sse=float(fit.fun @ fit.fun),
        optimizer_evaluations=int(fit.nfev),
        converged=bool(fit.success),
        at_bound=bool(np.any(fit.active_mask)),
    )


def evaluate(curves, fit):
    metrics, traces = [], []
    for curve in curves:
        t, v, temp, pred = predict(
            curve, fit["h_w_m2_k"], fit["negative_diffusivity_scale"]
        )
        keep = t <= pred["time_s"][-1]
        pv = np.interp(t[keep], pred["time_s"], pred["voltage_v"])
        pt = np.interp(t[keep], pred["time_s"], pred["temperature_k"])
        metrics.append(
            dict(
                cell=curve["cell"],
                rate=curve["rate"],
                split="calibration" if curve["rate"] == 1 else "held-out rate",
                voltage_rmse_v=float(np.sqrt(np.mean((pv - v[keep]) ** 2))),
                temperature_rmse_k=float(np.sqrt(np.mean((pt - temp[keep]) ** 2))),
                time_coverage=float(pred["time_s"][-1] / t[-1]),
                compared_points=int(keep.sum()),
                measured_peak_c=float(temp.max() - 273.15),
                predicted_peak_c=float(pred["temperature_k"].max() - 273.15),
                measured_duration_s=float(t[-1]),
                predicted_duration_s=float(pred["time_s"][-1]),
            )
        )
        traces.append(
            dict(
                cell=curve["cell"],
                rate=curve["rate"],
                time_s=t,
                measured_voltage_v=v,
                measured_temperature_c=temp - 273.15,
                predicted_time_s=pred["time_s"],
                predicted_voltage_v=pred["voltage_v"],
                predicted_temperature_c=pred["temperature_k"] - 273.15,
            )
        )
    return metrics, traces


def cooling_study(curve, fit):
    results = []
    for h in (2.0, 5.0, 10.0, 20.0, 40.0):
        _, _, _, pred = predict(curve, h, fit["negative_diffusivity_scale"])
        results.append(
            dict(
                h_w_m2_k=h,
                peak_temperature_c=float(pred["temperature_k"].max() - 273.15),
                duration_s=float(pred["time_s"][-1]),
                rate=curve["rate"],
            )
        )
    return results


def conservation(result):
    """Compare numerical current and power integrals with independent DFN state variables."""
    t, i, v = result["time_s"], result["current_a"], result["voltage_v"]
    charge = amp_hours(t, i)
    energy = amp_hours(t, i * v)
    model_charge = (
        result["discharge_capacity_ah"][-1] - result["discharge_capacity_ah"][0]
    )
    model_energy = result["discharge_energy_wh"][-1] - result["discharge_energy_wh"][0]
    return dict(
        integrated_charge_ah=charge,
        model_charge_ah=float(model_charge),
        integrated_energy_wh=energy,
        model_energy_wh=float(model_energy),
        charge_relative_error=float(
            abs(charge - model_charge) / max(abs(model_charge), 1e-12)
        ),
        energy_relative_error=float(
            abs(energy - model_energy) / max(abs(model_energy), 1e-12)
        ),
    )
