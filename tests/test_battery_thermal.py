import numpy as np
import pytest

pybamm = pytest.importorskip("pybamm")
from battery_fleet.thermal import kelvin, simulate, conservation


def test_temperature_units():
    assert kelvin(25) == 298.15
    assert kelvin(298.15, "K") == 298.15
    with pytest.raises(ValueError):
        kelvin(25, "F")
    with pytest.raises(ValueError):
        kelvin(-274)
    with pytest.raises(ValueError):
        simulate(-1, [0, 10])
    with pytest.raises(ValueError):
        simulate(1, [1, 10])


def test_real_dfn_charge_and_energy_conservation_and_cooling():
    t = np.linspace(0, 1500, 151)
    low = simulate(1.0, t, h=2.0)
    high = simulate(1.0, t, h=40.0)
    for prediction in (low, high):
        check = conservation(prediction)
        assert check["charge_relative_error"] < 1e-5
        assert check["energy_relative_error"] < 0.002
        assert check["integrated_charge_ah"] == pytest.approx(5 * 1500 / 3600)
        assert (prediction["voltage_v"] > 2.5).all()
        assert (prediction["temperature_k"] >= 298.15 - 1e-4).all()
    assert low["temperature_k"].max() > high["temperature_k"].max() + 2
    # Mesh refinement checks that the result is not a coarse-grid artefact.
    refined = simulate(1.0, t, h=40.0, mesh=20)
    assert abs(refined["voltage_v"][-1] - high["voltage_v"][-1]) < 0.02
    assert abs(refined["temperature_k"][-1] - high["temperature_k"][-1]) < 0.2
