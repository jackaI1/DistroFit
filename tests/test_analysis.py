"""Synthetic regression cases for film and README capabilities."""
import importlib
import unittest
from threading import Barrier
from unittest.mock import patch

import numpy as np
from scipy import stats


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        # Removing the analysis engine must fail a capability assertion.
        self.assertIsNotNone(importlib.util.find_spec("analysis"), "Missing analysis engine")
        self.core = importlib.import_module("analysis")
        self.data = np.random.default_rng(27).gamma(2, 2, 240)

    def fit(self, data=None, names=("Normal", "Gamma", "Exponential"), **kwargs):
        return self.core.fit_candidates(self.data if data is None else data, names, **kwargs)

    def test_all_selected_candidates_are_fitted(self):
        result = self.fit()
        self.assertEqual({r["Distribution"] for r in result["results"]},
                         {"Normal", "Gamma", "Exponential"})
        self.assertFalse(result["errors"])

    def test_candidate_batch_runs_concurrently_with_bounded_workers(self):
        # Serializing the fits makes the barrier fail; scoring still uses scipy.
        barrier = Barrier(2, timeout=5)
        supported = self.core.get_supported_distributions()

        class SynchronizedDistribution:
            def __init__(self, distribution):
                self.distribution = distribution

            def fit(self, values, **kwargs):
                barrier.wait()
                return self.distribution.fit(values, **kwargs)

            def __getattr__(self, name):
                return getattr(self.distribution, name)

        synchronized = {name: SynchronizedDistribution(supported[name]) for name in ("Normal", "Gamma")}
        with patch.object(self.core, "get_supported_distributions", return_value=synchronized):
            fit = self.fit(names=("Normal", "Gamma"))
        self.assertFalse(fit["errors"])
        self.assertEqual(len(fit["results"]), 2)

    def test_split_is_reproducible_disjoint_and_parameters_use_training_only(self):
        result = self.fit(names=("Normal",), seed=12, validation_fraction=.25)
        train, held = result["train_indices"], result["held_indices"]
        self.assertEqual(len(train), 180)
        self.assertEqual(len(held), 60)
        self.assertFalse(set(train) & set(held))
        self.assertEqual(sorted(list(train) + list(held)), list(range(240)))
        loc, scale = result["results"][0]["Parameters"]
        self.assertAlmostEqual(loc, float(self.data[train].mean()))
        self.assertAlmostEqual(scale, float(self.data[train].std()))
        np.testing.assert_array_equal(held, self.fit(seed=12)["held_indices"])

    def test_winner_uses_held_out_loss_and_exposes_training_loss(self):
        result = self.fit()
        losses = [r["Held-out NLL"] for r in result["results"]]
        self.assertEqual(losses, sorted(losses))
        self.assertEqual(result["results"][0]["Distribution"], "Gamma")
        row = next(r for r in result["results"] if r["Distribution"] == "Normal")
        expected = -stats.norm.logpdf(self.data[result["held_indices"]], *row["Parameters"]).mean()
        self.assertAlmostEqual(row["Held-out NLL"], expected)
        self.assertNotAlmostEqual(row["Train NLL"], row["Held-out NLL"])

    def test_support_violations_are_not_clipped_to_a_finite_score(self):
        self.assertTrue(np.isinf(self.core.score_values("Exponential", (0, 1), [-2, 1])))

    def test_weibull_recovers_from_optimizer_start_outside_training_support(self):
        # scipy's default start can converge with loc above real training rows.
        data = np.random.default_rng(42).gamma(2, 2, 1000)
        fit = self.fit(data=data, names=("Weibull (Min)",))
        self.assertFalse(fit["errors"])
        self.assertEqual(len(fit["results"]), 1)
        self.assertTrue(np.isfinite(fit["results"][0]["Train NLL"]))

    def test_tail_check_uses_survival_function_and_observed_exceedances(self):
        check = self.core.tail_check("Exponential", (0, 1), [0, 1, 3, 4], 2.)
        self.assertAlmostEqual(check["model_share"], .1353352832366127)
        self.assertEqual(check["observed_share"], .5)
        self.assertEqual(check["exceedances"], 2)
        severe = self.core.tail_check("Normal", (0, 1), [10] * 20, 3.)
        self.assertTrue(severe["flagged"])

    def test_scenario_scores_frozen_parameters_and_shows_shift(self):
        fit = self.fit(names=("Normal",))
        original = tuple(fit["results"][0]["Parameters"])
        baseline = self.core.evaluate_scenario(fit, self.data)
        shifted = self.core.evaluate_scenario(fit, self.data + 100)
        self.assertGreater(shifted[0]["Scenario NLL"], baseline[0]["Scenario NLL"] + 10)
        self.assertEqual(tuple(fit["results"][0]["Parameters"]), original)

    def test_residuals_are_empirical_minus_model_and_qq_is_not_refitted(self):
        diagnostic = self.core.diagnostics("Normal", (0, 1), [-1., 0., 1.], bins=3)
        np.testing.assert_allclose(diagnostic["cdf_residual"],
                                   [.16666666666666666 - .15865525393145707, 0.,
                                    .8333333333333334 - .8413447460685429])
        np.testing.assert_allclose(diagnostic["theoretical"],
                                   stats.norm.ppf([1/6, .5, 5/6]))
        self.assertEqual(len(diagnostic["density_residual"]), 3)

    def test_manual_curve_changes_and_invalid_scale_is_rejected(self):
        x = np.array([-1., 0., 1.])
        before = self.core.manual_curve("Normal", (0, 1), x)
        after = self.core.manual_curve("Normal", (0, 3), x)
        self.assertGreater(before[1], after[1])
        np.testing.assert_allclose(self.core.manual_curve("Normal", (0, 1), x, cdf=True),
                                   [.15865525393145707, .5, .8413447460685429])
        for params in [(0, 0), (0, -1), (float("nan"), 1)]:
            with self.assertRaises(ValueError):
                self.core.manual_curve("Normal", params, x)

    def test_relative_manual_adjustments_use_training_standard_deviation(self):
        self.assertTrue(hasattr(self.core, "adjust_parameters"), "Missing relative manual controls")
        adjusted = self.core.adjust_parameters([4, 2], [0, 2, 4], location_offset=1.5, scale_multiplier=3)
        np.testing.assert_allclose(adjusted, [7, 6])
        with self.assertRaises(ValueError):
            self.core.adjust_parameters([4, 2], [0, 2, 4], scale_multiplier=0)

    def test_preprocessing_handles_nonfinite_constant_and_outliers(self):
        values, removed = self.core.prepare_data([1, 1, 1, float("nan"), float("inf")], "Z-Score")
        np.testing.assert_array_equal(values, [1, 1, 1])
        self.assertEqual(removed, 2)
        for method in ["Z-Score", "IQR"]:
            values, removed = self.core.prepare_data([1] * 20 + [100], method)
            self.assertEqual(len(values), 20)
            self.assertEqual(removed, 1)

    def test_bins_are_positive_and_bounded_for_degenerate_or_extreme_data(self):
        for method in ["Freedman-Diaconis", "Sturges", "Square Root"]:
            for values in [[], [1], [1] * 10, [0] * 999 + [1e12]]:
                self.assertTrue(1 <= self.core.calculate_bin_count(values, method) <= 200)

    def test_invalid_fit_inputs_and_candidate_failures_are_visible(self):
        for values in [[], [1, 2], [1] * 20, [1, 2, 3, 4, 5, 6, 7, float("inf")]]:
            with self.assertRaises(ValueError):
                self.fit(data=values)
        with self.assertRaises(ValueError):
            self.fit(names=())
        result = self.fit(names=("Normal", "not a distribution"))
        self.assertIn("not a distribution", result["errors"])
        self.assertEqual(len(result["results"]), 1)

    def test_csv_headerless_numeric_and_nonnumeric_inputs(self):
        from io import StringIO
        df = self.core.read_csv(StringIO("1,2\n3,4\n"))
        self.assertEqual(df.shape, (2, 2))
        self.assertEqual(list(df.iloc[:, 0]), [1, 3])
        df = self.core.read_csv(StringIO("amount,label\n1,a\n2,b\n"))
        self.assertEqual(list(df["amount"]), [1, 2])
        self.assertEqual(list(df.select_dtypes(include=np.number).columns), ["amount"])

    def test_report_contains_method_settings_all_data_and_current_analysis(self):
        fit = self.fit()
        settings = {"seed": 42, "outlier_method": "None", "bins": 30}
        manual = {"distribution": "Normal", "parameters": [0, 3]}
        payload = self.core.report_payload(fit, self.data, settings, scenario=[123.456, 200], manual=manual)
        self.assertEqual(payload["source_data"], self.data.tolist())
        self.assertEqual(len(payload["prepared_data"]), 240)
        self.assertEqual(len(payload["held_indices"]), 60)
        self.assertEqual(payload["scenario_data"], [123.456, 200])
        self.assertEqual(payload["manual"], manual)
        self.assertIn("maximum likelihood", payload["method"])
        self.assertEqual(payload["settings"]["seed"], 42)
        pdf = self.core.create_report(payload)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertIn(b"source_data", pdf)  # machine-readable annotation, not just a screenshot
        self.assertIn(b"123.456", pdf)
        self.assertGreater(pdf.count(b"/Type /Page"), 4)


if __name__ == "__main__":
    unittest.main()
