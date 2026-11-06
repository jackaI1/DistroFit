"""Run the real production page, including edits that invalidate results."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = Path(__file__).resolve().parents[1] / 'pages/4_Production_anomalies.py'


def test_sample_runs_both_methods_and_exposes_flagged_rows_and_downloads():
    app = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not app.exception
    next(w for w in app.button if w.label == 'Analyze events').click().run()
    assert not app.exception
    assert app.session_state['anomaly_result'].events.evaluated.sum() == 600
    assert len(app.get('plotly_chart')) == 1
    assert len(app.get('download_button')) == 3
    assert len(app.dataframe) >= 2


def test_changed_or_invalid_input_clears_previous_flags_and_downloads():
    app = AppTest.from_file(str(PAGE), default_timeout=60).run()
    next(w for w in app.button if w.label == 'Analyze events').click().run()
    assert 'anomaly_result' in app.session_state
    # AppTest edits the same widget-state payload sent by Streamlit's data editor.
    app.session_state['anomaly_editor'] = {
        'edited_rows': {0: {'duration_seconds': 0.}}, 'added_rows': [], 'deleted_rows': []}
    app.run()
    assert not app.exception
    assert 'anomaly_result' not in app.session_state
    assert not app.get('download_button')
    next(w for w in app.button if w.label == 'Analyze events').click().run()
    assert not app.exception
    assert app.error
    assert not app.get('download_button')
