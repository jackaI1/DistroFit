"""Use the CLI and actual Streamlit page, including restore and stale exports."""
import json
from pathlib import Path
import subprocess
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'pages/4_Workplace_organization.py'


def test_cli_exports_portable_history_charts_real_flow_and_sop(tmp_path):
    out = tmp_path / 'review'
    run = subprocess.run([sys.executable, str(ROOT / 'six_s_report.py'), '--sample', '--out', str(out)],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    history = json.loads((out / 'audit_history.json').read_text())
    assert len(history['audits']) == 3
    import pandas as pd
    scores = pd.read_csv(out / 'audit_scores.csv')
    assert scores['percent'].round(2).tolist() == [50, 75, 91.67]
    assert pd.read_csv(out / 'findings.csv').shape[0] == 26
    assert pd.read_csv(out / 'pareto.csv')['Count'].tolist() == [6, 4, 4, 4, 4, 4]
    for name in ['trend.png', 'pareto.png']:
        assert (out / name).read_bytes().startswith(b'\x89PNG')
    assert '<svg' in (out / 'process.svg').read_text()
    assert 'Instrument and method ready?' in (out / 'sop.html').read_text()
    assert 'sop.html' in (out / 'index.html').read_text()
    replay = subprocess.run([sys.executable, str(ROOT / 'six_s_report.py'),
                             '--history', str(out / 'audit_history.json'),
                             '--process', str(out / 'process.json'), '--out', str(tmp_path / 'replay')],
                            capture_output=True, text=True, timeout=60)
    assert replay.returncode == 0, replay.stderr
    assert (tmp_path / 'replay/audit_scores.csv').read_bytes() == (out / 'audit_scores.csv').read_bytes()
    sentinel = out / 'index.html'
    before = sentinel.read_bytes()
    again = subprocess.run([sys.executable, str(ROOT / 'six_s_report.py'), '--sample', '--out', str(out)],
                           capture_output=True, text=True, timeout=60)
    assert again.returncode != 0 and sentinel.read_bytes() == before


def test_cli_bad_history_does_not_leave_partial_report(tmp_path):
    history = tmp_path / 'bad.json'
    history.write_text('{"schema_version":1,"audits":[{}]}')
    out = tmp_path / 'bad-report'
    run = subprocess.run([sys.executable, str(ROOT / 'six_s_report.py'), '--history', str(history),
                          '--process', str(ROOT / 'examples/lean/measurement_process.json'), '--out', str(out)],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode != 0 and not out.exists()


def test_page_demo_history_and_bad_restore_preserve_previous_records():
    assert PAGE.exists(), '6S app page is missing'
    app = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not app.exception
    app.button(key='load_demo').click().run()
    assert not app.exception
    assert len(app.session_state['six_s_history']['audits']) == 3
    assert app.session_state['six_s_trend']['percent'].round(2).tolist() == [50, 75, 91.67]
    app.text_area(key='restore_json').set_value('{}').run()
    app.button(key='restore_history').click().run()
    assert app.error and not app.exception
    assert len(app.session_state['six_s_history']['audits']) == 3
    exported = json.dumps(app.session_state['six_s_history'])
    app.button(key='empty_history').click().run()
    assert app.session_state['six_s_history']['audits'] == []
    app.text_area(key='restore_json').set_value(exported).run()
    app.button(key='restore_history').click().run()
    assert len(app.session_state['six_s_history']['audits']) == 3
    assert not app.exception


def test_page_requires_deliberate_scoring_and_saves_immutable_snapshot():
    assert PAGE.exists(), '6S app page is missing'
    app = AppTest.from_file(str(PAGE), default_timeout=30).run()
    app.button(key='save_audit').click().run()
    assert app.error and app.session_state['six_s_history']['audits'] == []
    for widget in app.selectbox:
        if widget.key.startswith('score_'):
            widget.set_value('4')
    for widget in app.text_area:
        if widget.key.startswith('evidence_'):
            widget.set_value('Observed current standard')
    app.text_input(key='audit_area').set_value('Test bench')
    app.text_input(key='auditor').set_value('Area reviewer')
    app.button(key='save_audit').click().run()
    assert not app.exception
    audits = app.session_state['six_s_history']['audits']
    assert len(audits) == 1 and audits[0]['area'] == 'Test bench'
    assert app.session_state['six_s_last_score']['percent'] == 100
    app.selectbox(key='score_safety-1').set_value('0')
    app.button(key='save_audit').click().run()
    assert app.error
    assert app.session_state['six_s_history']['audits'][0]['responses'][-2]['score'] == 4
    assert len(app.session_state['six_s_history']['audits']) == 1


def test_process_editor_invalidates_old_downloads():
    assert PAGE.exists(), '6S app page is missing'
    app = AppTest.from_file(str(PAGE), default_timeout=30).run()
    app.button(key='generate_process').click().run()
    assert not app.exception and 'six_s_process_package' in app.session_state
    assert 'Download SOP page' in [d.label for d in app.get('download_button')]
    app.text_area(key='process_source').set_value('{}').run()
    assert 'six_s_process_package' not in app.session_state
    assert 'Download SOP page' not in [d.label for d in app.get('download_button')]
    app.button(key='generate_process').click().run()
    assert app.error and not app.exception
