"""Hand-calculated audit scores and durable, area-specific history workflows."""
import importlib
import importlib.util
import json

import pytest


@pytest.fixture
def core():
    assert importlib.util.find_spec('six_s') is not None, '6S calculation module is missing'
    return importlib.import_module('six_s')


def audit(scores=None, **overrides):
    ids = ['sort-1', 'sort-2', 'order-1', 'order-2', 'shine-1', 'shine-2',
           'standard-1', 'standard-2', 'sustain-1', 'sustain-2', 'safety-1', 'safety-2']
    scores = [4] * 12 if scores is None else scores
    rows = [dict(item_id=item, score=score, evidence='Observed against posted standard',
                 action='Restore standard' if type(score) is int and score < 4 else '',
                 owner='Area lead' if type(score) is int and score < 4 else '',
                 due='2026-11-20' if type(score) is int and score < 4 else '')
            for item, score in zip(ids, scores)]
    return dict(audit_id='A1', area='Measurement bench', date='2026-11-01',
                auditor='Bench reviewer', checklist_version=1, responses=rows) | overrides


def test_score_uses_applicable_points_and_keeps_safety_visible(core):
    result = core.score_audit(audit([4] * 10 + [0, None]))
    assert result['earned'] == 40
    assert result['possible'] == 44
    assert result['percent'] == pytest.approx(100 * 40 / 44)
    assert result['applicable'] == 11 and result['excluded'] == 1
    assert result['pillars']['Safety']['percent'] == 0
    assert result['safety_findings'] == 1
    assert result['findings'] == 1
    excluded = core.score_audit(audit([None, None] + [4] * 10))
    assert excluded['pillars']['Sort']['percent'] is None
    assert excluded['percent'] == 100


@pytest.mark.parametrize('score', [-1, 5, 1.5, True, '3', float('nan'), float('inf')])
def test_invalid_scores_rejected(core, score):
    with pytest.raises(ValueError, match='score'):
        core.score_audit(audit([score] + [4] * 11))


@pytest.mark.parametrize('change', [
    lambda a: a['responses'].pop(),
    lambda a: a['responses'].append(a['responses'][0]),
    lambda a: a['responses'][0].update(item_id='other'),
    lambda a: a.update(checklist_version=2),
    lambda a: a.update(checklist_version=True),
    lambda a: a.update(area=' '),
    lambda a: a.update(date='2026-02-30'),
    lambda a: a.update(date='20261101'),
    lambda a: a['responses'][0].update(evidence=''),
    lambda a: a['responses'][0].update(score=2, action='', owner='', due=''),
    lambda a: a['responses'][0].update(score=2, action='Fix', owner='Lead', due='2026-10-01'),
    lambda a: a['responses'][0].update(score=None, evidence=''),
    lambda a: a.update(responses=None),
])
def test_incomplete_or_untraceable_audits_rejected(core, change):
    entry = audit()
    change(entry)
    with pytest.raises(ValueError):
        core.score_audit(entry)


def test_all_not_applicable_is_not_a_perfect_audit(core):
    with pytest.raises(ValueError, match='applicable'):
        core.score_audit(audit([None] * 12))


def test_history_roundtrip_append_is_immutable_and_ids_unique(core):
    history = {'schema_version': 1, 'audits': []}
    updated = core.append_audit(history, audit())
    assert history['audits'] == []
    assert core.load_history(json.dumps(updated)) == updated
    with pytest.raises(ValueError, match='unique'):
        core.append_audit(updated, audit())
    updated['audits'][0]['responses'][0]['score'] = 0
    assert history['audits'] == []


@pytest.mark.parametrize('raw', ['{}', '[]', '{', '{"schema_version":true,"audits":[]}',
                               '{"schema_version":2,"audits":[]}', '{"schema_version":1,"audits":{}}'])
def test_bad_history_import_cannot_be_accepted(core, raw):
    with pytest.raises(ValueError):
        core.load_history(raw)


def test_trend_sorted_by_date_and_pareto_counts_findings_not_points(core):
    entries = [audit([4] * 10 + [0, 2], audit_id='later', date='2026-11-03'),
               audit([2] * 12, audit_id='early'),
               audit([0] * 12, audit_id='other', area='Packing')]
    history = {'schema_version': 1, 'audits': entries}
    trend = core.audit_trend(history, 'Measurement bench')
    assert trend.audit_id.tolist() == ['early', 'later']
    assert trend.percent.tolist() == [50, 87.5]
    assert trend.applicable.tolist() == [12, 12]
    assert trend.Safety.tolist() == [50, 25]
    pareto = core.findings_pareto(history, 'Measurement bench')
    assert pareto.Category.tolist()[0] == 'Safety'
    assert pareto.Count.tolist() == [4, 2, 2, 2, 2, 2]
    assert pareto['Cumulative %'].iloc[-1] == pytest.approx(100)
    assert pareto.Count.sum() == 14  # two unmet safety checks repeated, not six lost points
    findings = core.findings_table(history, 'Measurement bench')
    assert len(findings) == 14 and set(findings.area) == {'Measurement bench'}
    assert set(findings.owner) == {'Area lead'}
    assert core.audit_trend(history, 'Missing').empty
    assert core.findings_pareto({'schema_version': 1, 'audits': [audit()]}, 'Measurement bench').empty


def test_history_validation_is_not_bypassed_by_analytics(core):
    history = {'schema_version': 1, 'audits': [audit(), audit()]}
    for function in [core.audit_trend, core.findings_table, core.findings_pareto]:
        with pytest.raises(ValueError, match='unique'):
            function(history, 'Measurement bench')
    with pytest.raises(ValueError):
        core.load_history(' ' * 2_000_001)


def test_saved_history_is_always_small_enough_to_restore(core):
    first = audit()
    for row in first['responses']:
        row['evidence'] = 'é' * 2000
    history = {'schema_version': 1, 'audits': [first]}
    with pytest.raises(ValueError, match='2 MB'):
        for i in range(40):
            history = core.append_audit(history, audit(responses=first['responses'], audit_id=f'large-{i}'))
    # The last accepted backup is portable, including JSON escaping and indentation.
    backup = json.dumps(history, indent=2)
    assert len(backup.encode()) <= 2_000_000
    assert core.load_history(backup) == history


def test_same_date_trend_preserves_snapshot_order_instead_of_random_id_order(core):
    history = {'schema_version': 1, 'audits': [audit(audit_id='z-first'),
               audit([2] * 12, audit_id='a-second')]}
    trend = core.audit_trend(history, 'Measurement bench')
    assert trend.audit_id.tolist() == ['z-first', 'a-second']
    assert trend.percent.tolist() == [100, 50]


def test_import_limit_is_bytes_not_unicode_characters(core):
    with pytest.raises(ValueError, match='2 MB'):
        core.load_history('é' * 1_000_001)
