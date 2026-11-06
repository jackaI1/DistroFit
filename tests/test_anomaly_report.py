import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from anomaly import AnomalyResult, evaluate_events, sample_events
import anomaly_report
from powerbi.anomaly_project import build_anomaly_project


@pytest.fixture(scope='module')
def result():
    return evaluate_events(sample_events())


def test_plotly_marks_exact_flagged_event_ids(result):
    figure = anomaly_report.event_chart(result)
    for kind in ('cycle', 'downtime'):
        for method in ('iforest', 'robust'):
            trace = next(t for t in figure.data if t.name == f'{kind}: {method}')
            expected = result.events.loc[(result.events.event_type == kind) &
                                         result.events[f'{method}_flag'].fillna(False), 'event_id']
            assert list(trace.customdata) == expected.tolist()
            assert len(trace.x) > 0


def test_report_preserves_warmup_truth_and_all_flags_and_refuses_overwrite(tmp_path, result):
    target = tmp_path / 'report'
    anomaly_report.write_report(result, target)
    events = pd.read_csv(target / 'events.csv')
    assert len(events) == 800
    assert events.is_fault.sum() == 40
    assert events.iforest_flag.iloc[:200].isna().all()
    assert events.iforest_flag.sum() == result.events.iforest_flag.sum()
    assert events.robust_flag.sum() == result.events.robust_flag.sum()
    summary = json.loads((target / 'summary.json').read_text())
    assert summary['evaluated_events'] == 600
    assert len(summary['folds']) == 3
    assert 'plotly' in (target / 'events.html').read_text().lower()
    with pytest.raises(FileExistsError):
        anomaly_report.write_report(result, target)


def test_powerbi_project_binds_event_flags_and_metrics_to_real_snapshot(tmp_path, result):
    anomaly_report.write_report(result, tmp_path / 'report')
    project = tmp_path / 'report' / 'powerbi'
    assert (project / 'DistroFit.pbip').is_file()
    model = json.loads((project / 'DistroFit.SemanticModel/model.bim').read_text())['model']
    tables = {t['name']: t for t in model['tables']}
    assert {'events', 'metrics'} == tables.keys()
    assert {'iforest_flag', 'robust_flag', 'event_id', 'evaluated'} <= {c['name'] for c in tables['events']['columns']}
    expression = tables['events']['partitions'][0]['source']['expression']
    assert 'event-0799' in expression
    assert 'DATATABLE' in expression
    bound = set()
    for path in project.glob('DistroFit.Report/definition/pages/*/visuals/*/visual.json'):
        visual = json.loads(path.read_text())['visual']
        for role in visual['query']['queryState'].values():
            for projection in role['projections']:
                binding = projection['field']['Column']
                table = binding['Expression']['SourceRef']['Entity']
                column = binding['Property']
                assert column in {c['name'] for c in tables[table]['columns']}
                bound.add((table, column))
    assert {('events', 'iforest_flag'), ('events', 'robust_flag'), ('events', 'event_id'),
            ('metrics', 'precision'), ('metrics', 'recall')} <= bound


def test_unlabelled_report_uses_null_accuracy_and_no_private_extra_columns(tmp_path):
    sample = sample_events().drop(columns='is_fault')
    sample['private_note'] = 'DO NOT EXPORT'
    result = evaluate_events(sample)
    anomaly_report.write_report(result, tmp_path / 'report')
    summary = json.loads((tmp_path / 'report/summary.json').read_text())
    assert all(row['precision'] is None and row['recall'] is None for row in summary['metrics'])
    assert 'DO NOT EXPORT' not in (tmp_path / 'report/events.csv').read_text()
    model = json.loads((tmp_path / 'report/powerbi/DistroFit.SemanticModel/model.bim').read_text())
    metrics = next(t for t in model['model']['tables'] if t['name'] == 'metrics')
    assert next(c for c in metrics['columns'] if c['name'] == 'precision')['dataType'] == 'double'


def test_committed_sample_regenerates_and_native_counts_are_known(tmp_path, result):
    sample = Path(__file__).resolve().parents[1] / 'examples/anomalies'
    saved_events = pd.read_csv(sample / 'events.csv', float_precision='round_trip', dtype={
        'fold': 'Int64', 'iforest_flag': 'boolean', 'robust_flag': 'boolean'})
    saved_events['timestamp'] = pd.to_datetime(saved_events.timestamp, utc=True)
    saved_metrics = pd.read_csv(sample / 'metrics.csv', float_precision='round_trip')
    # ARM macOS and x64 Linux can differ in the last binary digit of generated
    # durations and scores. Keep discrete results exact and float tolerance tight.
    pd.testing.assert_frame_equal(result.events, saved_events, rtol=1e-12, atol=1e-12)
    pd.testing.assert_frame_equal(result.metrics, saved_metrics, rtol=1e-12, atol=1e-12)
    summary = json.loads((sample / 'summary.json').read_text())
    generated = anomaly_report.summary_dict(result)
    assert len(generated['folds']) == len(summary['folds'])
    for got, want in zip(generated['folds'], summary['folds']):
        assert got['scaler_centers'] == pytest.approx(want['scaler_centers'], rel=1e-12, abs=1e-12)
        assert {k: v for k, v in got.items() if k != 'scaler_centers'} == {
            k: v for k, v in want.items() if k != 'scaler_centers'}
    assert {k: v for k, v in generated.items() if k != 'folds'} == {
        k: v for k, v in summary.items() if k != 'folds'}
    # The portable model must still regenerate byte-for-byte from the committed
    # snapshot. Replaying it avoids treating platform float roundoff as a drift.
    build_anomaly_project(AnomalyResult(saved_events, saved_metrics, summary['folds']), tmp_path / 'powerbi')
    for path in (tmp_path / 'powerbi').rglob('*'):
        if path.is_file():
            committed = sample / path.relative_to(tmp_path)
            assert path.read_bytes() == committed.read_bytes(), str(committed)
    checks = json.loads((sample / 'powerbi/checks.json').read_text())
    assert checks[0]['expected'] == [{'[Events]': 800, '[Evaluated]': 600,
                                     '[Forest flags]': 28, '[Robust flags]': 26}]


def test_command_line_runs_sample_and_own_csv(tmp_path):
    script = str(Path(__file__).resolve().parents[1] / 'anomaly_report.py')
    source = tmp_path / 'own.csv'
    own = sample_events().drop(columns='is_fault')
    own['event_id'] = [f'{i:06d}' for i in range(len(own))]
    own.to_csv(source, index=False)
    for args, name in [(['--sample'], 'sample'), ([str(source)], 'own')]:
        run = subprocess.run([sys.executable, script, *args, '--out', str(tmp_path / name)],
                             capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, run.stderr
        assert (tmp_path / name / 'metrics.csv').is_file()
        if name == 'own':
            saved = pd.read_csv(tmp_path / name / 'events.csv', dtype={'event_id': 'string'})
            assert saved.event_id.iloc[0] == '000000'
            assert saved.event_id.iloc[-1] == '000799'
    run = subprocess.run([sys.executable, script, str(source), '--out', str(tmp_path / 'own')],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode != 0
