"""Run the real Streamlit script with synthetic UI inputs."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "DistroFit.py")


class AppTests(unittest.TestCase):
    def sample(self):
        app = AppTest.from_file(APP, default_timeout=45).run()
        app.radio[0].set_value("Sample Data").run()
        return app

    def test_sample_fits_and_exposes_held_out_tail_scenario_and_report(self):
        app = self.sample()
        self.assertFalse(app.exception)
        labels = {metric.label for metric in app.metric}
        self.assertIn("Held-out observations", labels)
        self.assertIn("Model share above threshold", labels)
        self.assertTrue(app.session_state["analysis_result"]["results"])
        app.text_area(key="scenario_input").set_value("100, 101, 102, 103").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["report_payload"]["scenario_data"], [100, 101, 102, 103])
        self.assertEqual(len(app.get("download_button")), 1)

    def test_manual_large_negative_locations_and_adjustment(self):
        app = AppTest.from_file(APP, default_timeout=45).run()
        app.radio[0].set_value("Manual Entry").run()
        app.text_area(key="manual_input").set_value("-1000,-999,-998,-997,-996,-995,-994,-993,-992,-991").run()
        self.assertFalse(app.exception)
        scale = next(widget for widget in app.number_input if widget.label == "Scale")
        scale.set_value(10.).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["report_payload"]["manual"]["parameters"][-1], 10.)

    def test_bad_inputs_are_actionable_and_clear_previous_analysis(self):
        app = self.sample()
        app.radio[0].set_value("Manual Entry").run()
        app.text_area(key="manual_input").set_value("NaN, inf, 1,1,1").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertNotIn("analysis_result", app.session_state)

    def test_small_measurements_do_not_break_manual_scale_control(self):
        app = AppTest.from_file(APP, default_timeout=45).run()
        app.radio[0].set_value("Manual Entry").run()
        app.text_area(key="manual_input").set_value(
            "1e-15,2e-15,3e-15,4e-15,5e-15,6e-15,7e-15,8e-15,9e-15,1e-14").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["report_payload"]["manual"]["parameters"][-1] > 0)

    def test_no_candidates_cannot_leave_a_stale_winner_or_report(self):
        app = self.sample()
        app.multiselect[0].set_value([]).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.warning)
        self.assertNotIn("analysis_result", app.session_state)
        self.assertFalse(app.get("download_button"))

    def test_histogram_and_preprocessing_controls_recompute(self):
        app = self.sample()
        next(w for w in app.selectbox if w.label == "Binning Algo:").set_value("Manual").run()
        next(w for w in app.slider if w.label == "Number of Bins").set_value(20).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["analysis_result"]["bins"], 20)
        next(w for w in app.selectbox if w.label == "Outlier Removal:").set_value("IQR").run()
        self.assertFalse(app.exception)
        self.assertLess(len(app.session_state["analysis_result"]["data"]), 1000)
        self.assertEqual(app.session_state["report_payload"]["settings"]["outlier_method"], "IQR")

    def test_sample_and_validation_changes_replace_split_and_manual_defaults(self):
        app = self.sample()
        next(w for w in app.number_input if w.label == "Scale").set_value(10.).run()
        next(w for w in app.selectbox if w.label == "Sample Type:").set_value("Log-Normal").run()
        self.assertFalse(app.exception)
        self.assertNotEqual(app.session_state["report_payload"]["manual"]["parameters"][-1], 10.)
        next(w for w in app.number_input if w.label == "Split seed").set_value(7).run()
        next(w for w in app.slider if w.label == "Held-out fraction").set_value(.3).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["analysis_result"]["held_indices"]), 300)
        self.assertEqual(app.session_state["report_payload"]["settings"]["seed"], 7)

    def test_relative_shape_controls_and_reset_update_the_actual_curve(self):
        app = self.sample()
        baseline = app.session_state["report_payload"]["manual"]["parameters"][:]
        sliders = {widget.label: widget for widget in app.slider}
        self.assertIn("Scale multiplier", sliders)
        sliders["Scale multiplier"].set_value(3.).run()
        self.assertAlmostEqual(app.session_state["report_payload"]["manual"]["parameters"][-1], baseline[-1]*3)
        next(w for w in app.slider if w.label.startswith("Location offset")).set_value(1.).run()
        self.assertNotEqual(app.session_state["report_payload"]["manual"]["parameters"][-2], baseline[-2])
        with self.assertNoLogs("streamlit.elements.lib.policies", level="WARNING"):
            next(w for w in app.button if w.label == "Reset shape").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["report_payload"]["manual"]["parameters"], baseline)


if __name__ == "__main__":
    unittest.main()
