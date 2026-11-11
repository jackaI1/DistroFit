import json
import itertools

import numpy as np
import pandas as pd
import pytest

import doe

FACTORS = {"crew_size": (2., 4.), "tooling_minutes": (5., 15.), "kit": (0., 1.)}


def _truth(runs, names=("crew_size", "tooling_minutes", "kit")):
    factors = {name: tuple(levels) for name, levels in runs.attrs["design"]["factors"].items()}
    coded = doe._coded_matrix(runs, factors, list(names))
    return coded


def test_full_factorial_has_every_corner_once_plus_centres_and_random_order():
    runs = doe.full_factorial(FACTORS, centre_points=3, seed=5)
    corners = runs[~runs["is_centre"]][list(FACTORS)].to_numpy()
    expected = np.array(list(itertools.product(*FACTORS.values())))
    assert len(runs) == 8 + 3
    assert sorted(map(tuple, corners)) == sorted(map(tuple, expected))
    assert runs["is_centre"].sum() == 3
    assert np.allclose(runs.loc[runs["is_centre"], list(FACTORS)], [3., 10., .5])
    assert runs["run_order"].tolist() == list(range(1, 12))
    assert sorted(runs["standard_order"]) == list(range(1, 12))
    # Randomised: the sheet is not in standard order, and the same seed gives the same sheet.
    assert runs["standard_order"].tolist() != sorted(runs["standard_order"])
    again = doe.full_factorial(FACTORS, centre_points=3, seed=5)
    assert runs[list(FACTORS)].equals(again[list(FACTORS)])


def test_replicates_repeat_each_corner():
    runs = doe.full_factorial(FACTORS, replicates=2)
    assert len(runs) == 16
    counts = runs.groupby(list(FACTORS)).size()
    assert set(counts) == {2}


def test_fractional_design_has_expected_runs_resolution_and_aliases():
    runs = doe.fractional_factorial({**FACTORS, "fixture": (0., 1.)}, {"fixture": "ABC"})
    assert len(runs) == 8
    assert runs.attrs["design"]["resolution"] == 4
    coded = _truth(runs, ("crew_size", "tooling_minutes", "kit", "fixture"))
    # D = ABC means the defining relation is I = ABCD, so AB and CD are the same column.
    assert np.array_equal(coded[:, 0] * coded[:, 1], coded[:, 2] * coded[:, 3])


def test_fractional_generator_must_use_base_letters():
    with pytest.raises(ValueError, match="base letters"):
        doe.fractional_factorial({**FACTORS, "fixture": (0., 1.)}, {"fixture": "AZ"})
    with pytest.raises(ValueError, match="unknown factors"):
        doe.fractional_factorial(FACTORS, {"nozzle": "AB"})


def test_factor_validation():
    with pytest.raises(ValueError, match="plain word"):
        doe.full_factorial({"crew size": (2, 4)})
    with pytest.raises(ValueError, match="two different"):
        doe.full_factorial({"crew_size": (2, 2)})
    with pytest.raises(ValueError, match="at least one"):
        doe.full_factorial({})


def test_fit_recovers_known_effects_exactly_without_noise():
    runs = doe.full_factorial(FACTORS, centre_points=3)
    coded = _truth(runs)
    runs["response"] = 30 - 4 * coded[:, 0] + 6 * coded[:, 1] - 5 * coded[:, 2] + 1.5 * coded[:, 0] * coded[:, 1]
    result = doe.fit_effects(runs, FACTORS)
    effects = result["effects"].set_index("term")["effect"]
    assert effects["crew_size"] == pytest.approx(-8.)
    assert effects["tooling_minutes"] == pytest.approx(12.)
    assert effects["kit"] == pytest.approx(-10.)
    assert effects["crew_size x tooling_minutes"] == pytest.approx(3.)
    assert effects["crew_size x kit"] == pytest.approx(0., abs=1e-9)
    assert effects["curvature (centre vs factorial)"] == pytest.approx(0., abs=1e-9)


def test_fit_recovers_effects_from_noisy_replicated_data():
    rng = np.random.default_rng(7)
    runs = doe.full_factorial(FACTORS, replicates=4, centre_points=4)
    coded = _truth(runs)
    mean = 30 - 4 * coded[:, 0] + 6 * coded[:, 1] - 5 * coded[:, 2]
    runs["response"] = mean + rng.normal(0, .5, len(runs))
    result = doe.fit_effects(runs, FACTORS)
    effects = result["effects"].set_index("term")
    assert effects.loc["crew_size", "effect"] == pytest.approx(-8., abs=0.8)
    assert effects.loc["tooling_minutes", "effect"] == pytest.approx(12., abs=0.8)
    assert effects.loc["kit", "effect"] == pytest.approx(-10., abs=0.8)
    assert effects.loc["kit", "p_value"] < 1e-6
    assert effects.loc["crew_size x kit", "p_value"] > 0.01


def test_anova_sum_of_squares_match_drop_in_residuals():
    rng = np.random.default_rng(3)
    runs = doe.full_factorial(FACTORS, replicates=3)
    coded = _truth(runs)
    y = 5 + 2 * coded[:, 0] - coded[:, 2] + rng.normal(0, 1, len(runs))
    runs["response"] = y
    effects = doe.fit_effects(runs, FACTORS, max_order=1)["effects"].set_index("term")
    # In a balanced design the main-effect columns are orthogonal, so the sum of squares for
    # crew_size equals the rise in residual sum of squares when crew_size is dropped.
    def rss(columns):
        x = np.column_stack([np.ones(len(y))] + columns)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        return float(((y - x @ beta) ** 2).sum())
    drop = rss([coded[:, 1], coded[:, 2]]) - rss([coded[:, 0], coded[:, 1], coded[:, 2]])
    assert effects.loc["crew_size", "sum_sq"] == pytest.approx(drop, rel=1e-9)


def test_aliases_are_reported_for_fractional_fit():
    runs = doe.fractional_factorial({**FACTORS, "fixture": (0., 1.)}, {"fixture": "ABC"}, replicates=2,
                                    centre_points=3)
    coded = _truth(runs, ("crew_size", "tooling_minutes", "kit", "fixture"))
    runs["response"] = 20 + coded[:, 0] + 0.5 * coded[:, 2] * coded[:, 3]
    result = doe.fit_effects(runs, {**FACTORS, "fixture": (0., 1.)})
    effects = result["effects"].set_index("term")
    assert effects.loc["crew_size x tooling_minutes", "aliased_with"] == "kit x fixture"
    assert "kit x fixture" not in effects.index  # only one name per alias group is fitted
    assert result["summary"]["residual_df"] > 0


def test_curvature_detects_a_centre_point_shift():
    runs = doe.full_factorial({"crew_size": (2., 4.), "kit": (0., 1.)}, centre_points=4, replicates=2)
    coded = _truth(runs, ("crew_size", "kit"))
    centre = runs["is_centre"].to_numpy()
    runs["response"] = 10 + coded[:, 0] + np.where(centre, 3., 0.)
    result = doe.fit_effects(runs, {"crew_size": (2., 4.), "kit": (0., 1.)})
    curvature = result["effects"].set_index("type").loc["curvature", "effect"]
    assert curvature == pytest.approx(3., abs=1e-9)
    assert result["summary"]["curvature_p_value"] < 1e-6


def test_fit_needs_error_degrees_of_freedom():
    runs = doe.full_factorial(FACTORS)
    runs["response"] = np.arange(8.)
    with pytest.raises(ValueError, match="residual degree"):
        doe.fit_effects(runs, FACTORS, max_order=3)  # every term fitted, nothing left for error


def test_fit_rejects_bad_responses_and_out_of_range_values():
    runs = doe.full_factorial(FACTORS, replicates=2)
    runs["response"] = np.nan
    with pytest.raises(ValueError, match="numeric response"):
        doe.fit_effects(runs, FACTORS)
    runs["response"] = 1.
    runs.loc[0, "crew_size"] = 99.
    with pytest.raises(ValueError, match="outside its levels"):
        doe.fit_effects(runs, FACTORS)


def test_lenth_pse_is_a_noise_estimate():
    effects = np.array([0.1, -0.2, 0.15, 0.05, -0.1, 30., 0.12])
    assert doe.lenth_pse(effects) == pytest.approx(0.165, abs=1e-9)
    assert np.isnan(doe.lenth_pse([]))


def test_plots_and_saved_analysis_are_written(tmp_path):
    runs = doe.full_factorial(FACTORS, replicates=2, centre_points=2)
    coded = _truth(runs)
    rng = np.random.default_rng(11)
    runs["response"] = 30 - 4 * coded[:, 0] + rng.normal(0, .5, len(runs))
    result = doe.fit_effects(runs, FACTORS)
    folder = doe.write_analysis(result, tmp_path / "analysis")
    for name in ["effects.csv", "summary.json", "half_normal.png", "pareto.png"]:
        assert (folder / name).stat().st_size > 0
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["runs"] == len(runs)
    with pytest.raises(FileExistsError):
        doe.write_analysis(result, folder)


def test_plan_round_trip_and_sample_command(tmp_path):
    plan = doe.save_plan(doe.fractional_factorial({**FACTORS, "fixture": (0., 1.)}, {"fixture": "ABC"},
                                                  centre_points=2, replicates=2), tmp_path / "plan")
    runs, factors = doe.load_plan(plan)
    assert len(runs) == 18
    assert "response" in runs and runs["response"].isna().all()
    assert factors["fixture"] == (0., 1.)
    runs["response"] = np.arange(len(runs), dtype=float)
    assert doe.fit_effects(runs, factors)["summary"]["runs"] == 18
    with pytest.raises(FileExistsError):
        doe.save_plan(runs, plan)
    assert doe.main(["--sample", "--out", str(tmp_path / "sample")]) == 0
    summary = json.loads((tmp_path / "sample" / "analysis" / "summary.json").read_text())
    assert summary["design"]["resolution"] == 4
    assert summary["runs"] == 20


def test_cli_plan_and_analyse(tmp_path):
    assert doe.main(["plan", "--factor", "crew_size=2:4", "--factor", "tooling_minutes=5:15",
                     "--factor", "kit=0:1", "--centre", "2", "--out", str(tmp_path / "plan")]) == 0
    sheet = pd.read_csv(tmp_path / "plan" / "run_sheet.csv")
    assert len(sheet) == 10
    sheet["response"] = np.arange(len(sheet), dtype=float) * 0.5 + 3
    sheet.to_csv(tmp_path / "plan" / "run_sheet.csv", index=False)
    assert doe.main(["analyse", "--plan", str(tmp_path / "plan"), "--out", str(tmp_path / "report")]) == 0
    assert (tmp_path / "report" / "effects.csv").exists()
