"""SPC calculations checked against hand-computed and closed-form values."""
import importlib.util
import math
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy import integrate, stats

import analysis
import spc


def montgomery_piston_ring_subgroups():
    """25 subgroups of 5 built to match Montgomery Ex. 6.1's summary statistics
    (X-double-bar = 74.001, R-bar = 0.023). The raw textbook readings are not
    reproduced; these constructed readings have exactly those summary values."""
    offsets = np.array([-0.0115, -0.0045, 0.0, 0.0045, 0.0115])
    return np.tile(74.001 + offsets, (25, 1))


def exact_sample(mean, sd, n=50):
    """Deterministic sample whose mean and ddof=1 standard deviation are exact."""
    z = np.random.default_rng(5).standard_normal(n)
    return mean + sd * (z - z.mean()) / z.std(ddof=1)


class ControlChartConstants(unittest.TestCase):
    def test_d2_matches_expected_range_of_standard_normal_samples(self):
        # d2(n) = E[range of n standard normals] = integral of 1 - F^n - (1-F)^n.
        for n, d2 in spc.D2.items():
            exact, _ = integrate.quad(lambda x: 1 - stats.norm.cdf(x) ** n - stats.norm.sf(x) ** n, -12, 12)
            self.assertAlmostEqual(d2, exact, delta=1e-3, msg=f"n={n}")

    def test_a2_equals_three_over_d2_root_n(self):
        for n in spc.A2:
            self.assertAlmostEqual(spc.A2[n], 3 / (spc.D2[n] * math.sqrt(n)), delta=2e-3)

    def test_published_table_values(self):
        self.assertEqual((spc.A2[5], spc.D3[5], spc.D4[5], spc.D2[5]), (0.577, 0.0, 2.114, 2.326))
        self.assertEqual((spc.D3[7], spc.D4[2]), (0.076, 3.267))


class XbarRChart(unittest.TestCase):
    def setUp(self):
        self.chart = spc.xbar_r_chart(montgomery_piston_ring_subgroups())

    def test_limits_match_hand_calculation(self):
        self.assertEqual(self.chart["subgroup_size"], 5)
        self.assertAlmostEqual(self.chart["grand_mean"], 74.001, places=9)
        self.assertAlmostEqual(self.chart["r_bar"], 0.023, places=9)
        xbar = self.chart["xbar"]
        self.assertAlmostEqual(xbar["ucl"], 74.001 + 0.577 * 0.023, places=9)   # 74.01427
        self.assertAlmostEqual(xbar["lcl"], 74.001 - 0.577 * 0.023, places=9)   # 73.98773
        self.assertAlmostEqual(self.chart["range"]["ucl"], 2.114 * 0.023, places=9)  # 0.04862
        self.assertEqual(self.chart["range"]["lcl"], 0.0)
        self.assertAlmostEqual(self.chart["sigma_within"], 0.023 / 2.326, places=9)  # 0.0098882

    def test_in_control_data_has_no_signals(self):
        self.assertEqual(self.chart["xbar"]["flagged"], [])
        self.assertEqual(self.chart["range"]["flagged"], [])

    def test_shifted_subgroup_and_wide_range_are_flagged(self):
        groups = montgomery_piston_ring_subgroups()
        groups[10] += 0.03                                   # mean beyond the X-bar UCL
        groups[20] = groups[20] + np.array([-0.03, 0, 0, 0, 0.03])   # range 0.083 > 0.0486
        chart = spc.xbar_r_chart(groups)
        self.assertIn(10, chart["xbar"]["signals"][1])
        self.assertEqual(chart["range"]["flagged"], [20])

    def test_invalid_subgroups_are_rejected(self):
        for bad in (np.ones(10), np.ones((1, 5)), np.ones((10, 1)), np.ones((10, 11)),
                    np.full((5, 3), np.nan)):
            with self.assertRaises(ValueError):
                spc.xbar_r_chart(bad)


class ImrChart(unittest.TestCase):
    def test_limits_match_hand_calculation(self):
        # x = 10,12,11,13,12  ->  MR = 2,1,2,1  ->  MR-bar = 1.5, mean = 11.6
        chart = spc.imr_chart([10, 12, 11, 13, 12])
        ind, mr = chart["individuals"], chart["moving_range"]
        self.assertAlmostEqual(chart["mr_bar"], 1.5)
        self.assertAlmostEqual(ind["center"], 11.6)
        self.assertAlmostEqual(ind["ucl"], 11.6 + 3 * 1.5 / 1.128)   # 15.5894 (2.66 * MR-bar)
        self.assertAlmostEqual(ind["lcl"], 11.6 - 3 * 1.5 / 1.128)
        self.assertAlmostEqual(mr["ucl"], 3.267 * 1.5)               # 4.9005
        self.assertEqual(mr["lcl"], 0.0)
        self.assertAlmostEqual(chart["sigma_within"], 1.5 / 1.128)
        self.assertAlmostEqual(3 / 1.128, 2.66, places=2)

    def test_moving_range_flags_a_jump(self):
        values = [10, 10.5, 9.8, 10.2, 10.1, 9.9, 10.3, 10.0, 16.0, 10.1]
        chart = spc.imr_chart(values)
        self.assertEqual(chart["moving_range"]["flagged"], [7, 8])   # the jump up and the drop back
        self.assertIn(8, chart["individuals"]["signals"][1])

    def test_baseline_fixes_limits_so_a_later_shift_is_detected(self):
        stable = [30 + (-1) ** i * (1 + i % 3) for i in range(30)]
        values = stable + [45] * 10
        chart = spc.imr_chart(values, baseline=30)
        reference = spc.imr_chart(stable)
        self.assertEqual(chart["individuals"]["ucl"], reference["individuals"]["ucl"])
        self.assertEqual(chart["individuals"]["signals"][4], [37, 38, 39])  # 8th..10th point in the run
        self.assertEqual(chart["individuals"]["signals"][1][0], 30)

    def test_input_validation(self):
        for call in (lambda: spc.imr_chart([1, 2]), lambda: spc.imr_chart([1, 2, float("nan")]),
                     lambda: spc.imr_chart([1, 2, 3, 4], baseline=2),
                     lambda: spc.imr_chart([1, 2, 3, 4], baseline=5)):
            with self.assertRaises(ValueError):
                call()


class WesternElectricRules(unittest.TestCase):
    def signals(self, values):
        return spc.western_electric_signals(values, 0.0, 1.0)

    def test_rule_1_is_strictly_beyond_three_sigma(self):
        result = self.signals([0, 3.0, 3.5, -3.5, 0])
        self.assertEqual(result[1], [2, 3])

    def test_rule_2_two_of_three_beyond_two_sigma_same_side(self):
        self.assertEqual(self.signals([0, 2.5, 2.5, 0])[2], [2])
        self.assertEqual(self.signals([2.5, 0, 2.5])[2], [2])
        self.assertEqual(self.signals([2.5, 0, -2.5])[2], [])       # opposite sides
        self.assertEqual(self.signals([2.5, 0, 0, 2.5])[2], [])     # not within three points
        self.assertEqual(self.signals([-2.5, -2.1])[2], [])         # window not yet full

    def test_rule_3_four_of_five_beyond_one_sigma_same_side(self):
        result = self.signals([1.5, 1.5, 0, 1.5, 1.5])
        self.assertEqual(result[3], [4])
        self.assertEqual(result[2], [])
        self.assertEqual(self.signals([1.5, 1.5, 0, 0, 1.5])[3], [])   # only three of five
        self.assertEqual(self.signals([-1.2, -1.2, -1.2, 0.1, -1.2])[3], [4])

    def test_rule_4_eight_in_a_row_on_one_side(self):
        self.assertEqual(self.signals([0.5] * 8)[4], [7])
        self.assertEqual(self.signals([0.5] * 9)[4], [7, 8])
        self.assertEqual(self.signals([-0.5] * 8)[4], [7])
        self.assertEqual(self.signals([0.5] * 7)[4], [])
        self.assertEqual(self.signals([0.5] * 4 + [0.0] + [0.5] * 4)[4], [])  # a point on the line breaks the run
        self.assertEqual(self.signals([0.5] * 4 + [-0.5] + [0.5] * 4)[4], [])

    def test_centre_and_sigma_scale_the_zones(self):
        result = spc.western_electric_signals([100, 100, 130.5], 100.0, 10.0)
        self.assertEqual(result[1], [2])

    def test_invalid_inputs(self):
        for center, sigma in ((0.0, 0.0), (0.0, -1.0), (float("nan"), 1.0)):
            with self.assertRaises(ValueError):
                spc.western_electric_signals([1, 2, 3], center, sigma)
        with self.assertRaises(ValueError):
            spc.western_electric_signals([], 0.0, 1.0)


class NormalCapability(unittest.TestCase):
    def test_pp_ppk_cp_cpk_hand_values(self):
        data = exact_sample(10.0, 0.5)
        result = spc.capability(data, lsl=8.0, usl=11.5, sigma_within=0.4)
        self.assertAlmostEqual(result["Pp"], 3.5 / 3.0)                 # (USL-LSL)/(6*0.5)
        self.assertAlmostEqual(result["Ppk"], 1.5 / 1.5)                # nearer side: (11.5-10)/(3*0.5)
        self.assertAlmostEqual(result["Cp"], 3.5 / 2.4)                 # 1.4583
        self.assertAlmostEqual(result["Cpk"], 1.5 / 1.2)                # 1.25
        self.assertAlmostEqual(result["sigma_overall"], 0.5)

    def test_centred_process_has_cp_equal_cpk(self):
        result = spc.capability(exact_sample(50, 2), lsl=44, usl=56, sigma_within=2)
        self.assertAlmostEqual(result["Cp"], 1.0)
        self.assertAlmostEqual(result["Cpk"], 1.0)

    def test_one_sided_specifications(self):
        data = exact_sample(10.0, 0.5)
        upper = spc.capability(data, usl=12.0)
        self.assertIsNone(upper["Pp"])
        self.assertAlmostEqual(upper["Ppk"], 2.0 / 1.5)
        lower = spc.capability(data, lsl=9.0)
        self.assertAlmostEqual(lower["Ppk"], 1.0 / 1.5)
        self.assertIsNone(lower["Cpk"])

    def test_negative_index_when_mean_is_outside_the_limit(self):
        self.assertAlmostEqual(spc.capability(exact_sample(70, 5), usl=60)["Ppk"], -10 / 15)

    def test_cpk_one_point_three_three_is_about_63_ppm(self):
        # Textbook: Cp = Cpk = 1.33 (+/-4 sigma) gives 63.3 ppm for a centred normal process.
        result = spc.capability_percentile("Normal", (0.0, 1.0), lsl=-4.0, usl=4.0)
        self.assertAlmostEqual(result["ppm_total"], 2 * stats.norm.sf(4) * 1e6)
        self.assertAlmostEqual(result["ppm_total"], 63.34, places=2)

    def test_invalid_inputs(self):
        data = exact_sample(10, 1)
        for kwargs in ({}, {"lsl": 5, "usl": 5}, {"lsl": 6, "usl": 5}):
            with self.assertRaises(ValueError):
                spc.capability(data, **kwargs)
        with self.assertRaises(ValueError):
            spc.capability([3, 3, 3, 3], usl=5)
        with self.assertRaises(ValueError):
            spc.capability(data, usl=15, sigma_within=0)


class PercentileCapability(unittest.TestCase):
    def test_reduces_to_classic_formulas_for_a_normal_model(self):
        # ISO 22514-2: x0.135 and x99.865 are the normal mean -/+ 3 sigma (to 1e-5).
        result = spc.capability_percentile("Normal", (10.0, 0.5), lsl=8.0, usl=11.5)
        self.assertAlmostEqual(result["Pp"], 3.5 / 3.0, places=3)
        self.assertAlmostEqual(result["Ppk"], 1.0, places=3)
        self.assertAlmostEqual(result["median"], 10.0)

    def test_exponential_matches_closed_form(self):
        # Exp(scale=1): quantile(p) = -ln(1-p); median = ln 2; P(X>USL) = exp(-USL).
        low, high, median = -math.log(1 - 0.00135), -math.log(1 - 0.99865), math.log(2)
        result = spc.capability_percentile("Exponential", (0.0, 1.0), usl=10.0)
        self.assertAlmostEqual(result["Ppk"], (10 - median) / (high - median))   # 1.5736
        self.assertAlmostEqual(result["Ppk"], 1.5736, places=3)
        self.assertIsNone(result["Pp"])
        self.assertAlmostEqual(result["ppm_above"], math.exp(-10) * 1e6)
        self.assertEqual(result["ppm_below"], 0.0)
        both = spc.capability_percentile("Exponential", (0.0, 1.0), lsl=0.05, usl=10.0)
        self.assertAlmostEqual(both["Pp"], (10 - 0.05) / (high - low))
        self.assertAlmostEqual(both["Ppk"], min((10 - median) / (high - median), (median - 0.05) / (median - low)))

    def test_location_and_scale_are_applied(self):
        shifted = spc.capability_percentile("Exponential", (5.0, 2.0), usl=25.0)
        base = spc.capability_percentile("Exponential", (0.0, 1.0), usl=10.0)
        self.assertAlmostEqual(shifted["Ppk"], base["Ppk"])    # (25-5)/2 = 10

    def test_uses_the_fitted_winner_from_distrofit(self):
        data = np.random.default_rng(27).gamma(2, 2, 240)
        fit = analysis.fit_candidates(data, ("Normal", "Gamma", "Exponential"))
        result = spc.capability_from_fit(fit, lsl=0.0, usl=20.0)
        best = fit["results"][0]
        self.assertEqual(result["distribution"], best["Distribution"])
        expected = spc.capability_percentile(best["Distribution"], best["Parameters"], 0.0, 20.0)
        self.assertEqual(result["Ppk"], expected["Ppk"])

    def test_normal_theory_overstates_capability_for_a_right_skewed_process(self):
        data = np.random.default_rng(3).lognormal(0.0, 0.6, 2000)
        fit = analysis.fit_candidates(data, ("Normal", "Log-Normal", "Gamma"))
        usl = 6.0
        classic = spc.capability(data, usl=usl)["Ppk"]
        skewed = spc.capability_from_fit(fit, usl=usl)
        self.assertNotEqual(skewed["distribution"], "Normal")
        self.assertGreater(classic, skewed["Ppk"])

    def test_failed_fit_and_bad_specs_raise(self):
        with self.assertRaises(ValueError):
            spc.capability_from_fit({"results": []}, usl=1.0)
        with self.assertRaises(ValueError):
            spc.capability_percentile("Normal", (0.0, 1.0))
        with self.assertRaises(ValueError):
            spc.capability_percentile("Normal", (0.0, -1.0), usl=3.0)


class ParetoAnalysis(unittest.TestCase):
    def test_sorted_percent_cumulative_and_vital_few(self):
        table = spc.pareto_table({"C": 15, "A": 50, "D": 5, "B": 30})
        self.assertEqual(list(table["Category"]), ["A", "B", "C", "D"])
        self.assertEqual(list(table["Percent"]), [50, 30, 15, 5])
        self.assertEqual(list(table["Cumulative %"]), [50, 80, 95, 100])
        # B reaches exactly 80%, so C is not needed.
        self.assertEqual(list(table["Vital few"]), [True, True, False, False])

    def test_crossing_category_is_included(self):
        table = spc.pareto_table({"A": 60, "B": 25, "C": 10, "D": 5})
        self.assertEqual(list(table["Vital few"]), [True, True, False, False])   # 60 -> 85 crosses 80
        self.assertEqual(list(spc.pareto_table({"A": 90, "B": 10})["Vital few"]), [True, False])

    def test_counts_labels_and_stable_ties(self):
        table = spc.pareto_table(["x", "y", "y", "z", "x", "y", "w"])
        self.assertEqual(list(table["Category"]), ["y", "x", "z", "w"])
        self.assertEqual(list(table["Count"]), [3, 2, 1, 1])
        self.assertAlmostEqual(table["Percent"].sum(), 100)

    def test_invalid_inputs(self):
        for bad in ({}, {"A": 0, "B": 0}, {"A": -1, "B": 5}, []):
            with self.assertRaises(ValueError):
                spc.pareto_table(bad)

    def test_chart_figures_render_the_data(self):
        table = spc.pareto_table({"A": 50, "B": 30, "C": 20})
        fig = spc.pareto_chart(table, "Defects")
        bars = fig.axes[0].patches
        self.assertEqual([round(b.get_height()) for b in bars], [50, 30, 20])
        self.assertEqual(list(fig.axes[1].lines[0].get_ydata()), [50, 80, 100])
        chart = spc.imr_chart([10, 12, 11, 13, 12, 30])["individuals"]
        control = spc.control_chart_figure(chart)
        self.assertEqual(len(control.axes[0].lines[0].get_xdata()), 6)


class CaseStudyIsReproducible(unittest.TestCase):
    """docs/case-study-dmaic.md quotes these numbers; they must stay in sync."""

    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parent.parent / "docs" / "dmaic_case_study.py"
        spec = importlib.util.spec_from_file_location("dmaic_case_study", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        cls.out = module.run()

    def test_headline_numbers_quoted_in_the_case_study(self):
        before, after = self.out["before"], self.out["after"]
        self.assertAlmostEqual(before["mean"], 118.9, delta=0.05)
        self.assertAlmostEqual(after["mean"], 30.0, delta=0.05)
        self.assertAlmostEqual(before["normal"]["Ppk"], -0.60, delta=0.005)
        self.assertAlmostEqual(after["normal"]["Ppk"], 1.11, delta=0.005)
        self.assertAlmostEqual(before["percentile"]["Ppk"], -0.58, delta=0.005)
        self.assertAlmostEqual(after["percentile"]["Ppk"], 0.97, delta=0.005)
        self.assertEqual(before["chart"]["xbar"]["flagged"] + after["chart"]["xbar"]["flagged"], [])

    def test_control_phase_detects_the_late_shift_only(self):
        signals = self.out["control"]["individuals"]["signals"]
        self.assertTrue(all(i >= 30 for indices in signals.values() for i in indices))
        self.assertEqual(signals[4], [36, 37, 38, 39])
        self.assertEqual(list(self.out["pareto"]["Vital few"]), [True] * 4 + [False] * 2)


if __name__ == "__main__":
    unittest.main()
