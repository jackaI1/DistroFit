"""Fault injection, provenance boundaries and measured-feature calculations."""

from hashlib import sha256, md5
from pathlib import Path
from unittest.mock import patch
import io
import numpy as np
import pandas as pd
import pytest
from battery_fleet.data import (
    clean_series,
    download,
    manifest,
    verify,
    chen_discharges,
    nasa_cycles,
)
from battery_fleet.fleet import amp_hours, cycle_metrics, analyze_cycles
from battery_fleet.report import fleet_figure


def phase(current=-2.0):
    return pd.DataFrame(
        dict(
            time_s=[0.0, 10.0, 20.0, 1800.0, 3600.0],
            current_a=[0.0, current, current, current, current],
            voltage_v=[4.2, 4.0, 3.99, 3.6, 3.0],
            temperature_c=[25.0, 25.0, 26.0, 28.0, 30.0],
        )
    )


def clean_fleet():
    rows = []
    for cell in ("a", "b", "c", "d"):
        for cycle in range(1, 61):
            rows.append(
                dict(
                    cell=cell,
                    cycle=cycle,
                    capacity_ah=2 - 0.002 * cycle,
                    coulombic_efficiency=0.99,
                    resistance_proxy_ohm=0.05,
                    peak_temperature_c=30.0,
                )
            )
    return pd.DataFrame(rows)


def test_seconds_amperes_and_efficiency():
    assert amp_hours([0, 3600], [2, 2]) == 2
    discharge = phase()
    charge = phase(2.0)
    charge["voltage_v"] = [3.2, 3.4, 3.5, 4.1, 4.2]
    metrics = cycle_metrics(discharge, charge)
    assert metrics["capacity_ah"] == pytest.approx(2 - 10 / 3600)
    assert metrics["coulombic_efficiency"] == 1
    assert metrics["resistance_proxy_ohm"] == pytest.approx(0.1)
    assert np.isnan(cycle_metrics(discharge)["coulombic_efficiency"])


@pytest.mark.parametrize(
    "times,current",
    [([0, 0], [1, 1]), ([1, 0], [1, 1]), ([0, 1], [1]), ([0, np.nan], [1, 1])],
)
def test_invalid_integration(times, current):
    with pytest.raises(ValueError):
        amp_hours(times, current)


def test_cleaning_unsorted_duplicates_and_faults():
    f = phase()
    f.loc[3, "time_s"] = 30
    f.loc[4, "time_s"] = 40
    dirty = pd.concat(
        [
            f.iloc[::-1],
            f.iloc[[1]],
            f.iloc[[1]].assign(voltage_v=np.nan),
            f.iloc[[1]].assign(temperature_c=500),
        ]
    )
    cleaned, quality = clean_series(dirty)
    assert quality == dict(dropped_rows=2, duplicate_times=1)
    assert cleaned.time_s.to_list() == [0, 10, 20, 30, 40]
    with pytest.raises(ValueError, match="gap"):
        clean_series(phase().assign(time_s=[0, 10, 20, 30, 3600]))


def test_faults_and_clean_control_and_future_independence():
    baseline = clean_fleet()
    clean, cells = analyze_cycles(baseline)
    assert not clean.flagged_cycle.any()
    assert not cells.flagged_cell.any()
    faulty = baseline.copy()
    faulty.loc[(faulty.cell == "a") & (faulty.cycle == 35), "capacity_ah"] -= 0.4
    faulty.loc[(faulty.cell == "b") & (faulty.cycle >= 45), "resistance_proxy_ohm"] = (
        0.3
    )
    faulty.loc[(faulty.cell == "c") & (faulty.cycle == 40), "coulombic_efficiency"] = (
        0.6
    )
    faulty.loc[(faulty.cell == "d") & (faulty.cycle == 40), "peak_temperature_c"] = 55
    analyzed, summary = analyze_cycles(faulty)
    assert analyzed.query("cell=='a' and cycle==35").flagged_cycle.all()
    assert (
        "capacity_ah" in analyzed.query("cell=='a' and cycle==35").flag_reasons.iloc[0]
    )
    for cell, cycle in [("b", 45), ("c", 40), ("d", 40)]:
        assert analyzed.query("cell==@cell and cycle==@cycle").flagged_cycle.all()
    assert summary.set_index("cell").loc["b", "flagged_cell"]
    pd.testing.assert_frame_equal(
        clean.loc[clean.cycle < 35].reset_index(drop=True),
        analyzed.loc[analyzed.cycle < 35].reset_index(drop=True),
    )
    assert summary.set_index("cell").loc["a", "trend_ah_per_cycle"] == pytest.approx(
        -0.002
    )
    fig = fleet_figure(analyzed, summary)
    assert "a flags" in [t.name for t in fig.data]


def test_persistent_abnormal_fade_cell():
    f = clean_fleet()
    f.loc[f.cell == "d", "capacity_ah"] = 2 - 0.015 * f.loc[f.cell == "d", "cycle"]
    _, cells = analyze_cycles(f)
    assert cells.set_index("cell").loc["d", "flagged_cell"]
    assert cells.set_index("cell").loc["d", "peer_fade_score"] > 5


def test_download_checksum_atomic_and_corrupt_cache(tmp_path):
    payload = b"public measurements\n"
    e = dict(
        name="test.csv",
        url="https://example.test/data",
        bytes=len(payload),
        sha256=sha256(payload).hexdigest(),
        md5=md5(payload).hexdigest(),
    )
    with patch("battery_fleet.data.urlopen", return_value=io.BytesIO(payload)):
        download(tmp_path, [e])
    verify(tmp_path / e["name"], e)
    (tmp_path / e["name"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="Checksum"):
        download(tmp_path, [e])
    (tmp_path / e["name"]).unlink()
    with patch(
        "battery_fleet.data.urlopen", return_value=io.BytesIO(payload + b"oversize")
    ):
        with pytest.raises(ValueError):
            download(tmp_path, [e])
    assert not list(tmp_path.iterdir())


def test_manifest_pins():
    entries = manifest()
    assert len(entries) == 6
    assert sum(e["bytes"] for e in entries) < 50_000_000
    assert all(len(e["sha256"]) == 64 for e in entries)
    assert all(
        "5301bd7e469dc8a1320b55719629571f2c02b6fc" in e["url"]
        for e in entries
        if e["dataset"] == "NASA aging"
    )


def test_public_data_integration():
    import os

    directory = os.environ.get("BATTERY_TEST_DATA")
    if not directory:
        pytest.skip(
            "Set BATTERY_TEST_DATA to checksum-verified public files; battery CI runs this"
        )
    curves = chen_discharges(directory)
    assert len(curves) == 12
    assert {c["rate"] for c in curves} == {0.1, 0.5, 1.0, 1.5}
    frame, rejected = nasa_cycles(directory)
    assert not rejected
    assert len(frame) == 504
    # Independent capacity field in the NASA file agrees with numerical integration.
    assert (abs(frame.capacity_ah - frame.source_capacity_ah) < 0.03).all()
    assert frame.coulombic_efficiency.notna().sum() >= 490
    assert frame.loc[~frame.charge_pair_complete, "coulombic_efficiency"].isna().all()


def test_partial_topup_is_not_reported_as_efficiency():
    metrics = cycle_metrics(phase(), phase(2.0))
    assert not metrics["charge_pair_complete"]
    assert np.isnan(metrics["coulombic_efficiency"])
