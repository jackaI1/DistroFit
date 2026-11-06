"""Exercise the real grouped page, including one complete NUTS submission."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = str(Path(__file__).resolve().parents[1] / 'pages/3_Grouped_measurements.py')


def test_explicit_fit_displays_posteriors_and_edits_invalidate_results():
    app = AppTest.from_file(PAGE, default_timeout=600).run()
    assert not app.exception
    assert 'bayesian_result' not in app.session_state
    app.button(key='bayes_fit').click().run()
    assert not app.exception
    assert app.session_state['bayesian_result']['diagnostics']['passed']
    assert len(app.get('plotly_chart')) == 2
    assert len(app.get('download_button')) >= 3
    app.selectbox(key='bayes_group').set_value('Batch D').run()
    assert not app.exception
    assert 'bayesian_result' in app.session_state
    result = app.session_state['bayesian_result']
    result['diagnostics']['passed'] = False
    result['diagnostics']['issues'] = ['R-hat exceeds 1.01; chains disagree.']
    app.run()
    assert app.error and app.warning
    assert not app.get('download_button')
    assert not app.get('plotly_chart')
    # A valid data edit must remove the stale fit as well as failed diagnostics.
    app.session_state['bayes_log'] = {'edited_rows': {0: {'value': 52.}}, 'added_rows': [], 'deleted_rows': []}
    app.run()
    assert 'bayesian_result' not in app.session_state
    app.number_input(key='bayes_draws').set_value(2000).run()
    assert 'bayesian_result' not in app.session_state
    assert not app.get('download_button')
    app.session_state['bayes_log'] = {'edited_rows': {0: {'value': None}}, 'added_rows': [], 'deleted_rows': []}
    app.run()
    assert not app.exception
    assert app.error
    assert 'bayesian_result' not in app.session_state


def test_page_invalid_groups_do_not_sample_or_keep_downloads():
    app = AppTest.from_file(PAGE, default_timeout=30).run()
    assert not app.exception
    app.session_state['bayes_log'] = {'edited_rows': {}, 'added_rows': [], 'deleted_rows': list(range(32, 80))}
    app.run()
    assert not app.exception
    assert app.error
    assert not app.get('download_button')
