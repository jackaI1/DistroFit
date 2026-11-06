"""Production errors these tests catch: leakage, lost rows and misleading scores."""
import numpy as np
import pandas as pd
import pytest
from io import StringIO

import anomaly


def test_csv_import_used_by_cli_and_upload_preserves_distinct_string_ids():
    source = StringIO('event_id,timestamp,event_type,duration_seconds\n'
                      '000123,2026-01-01T00:00:00Z,cycle,45\n'
                      '123,2026-01-01T00:01:00Z,cycle,46\n')
    events = anomaly.validate_events(anomaly.read_event_csv(source))
    assert events.event_id.tolist() == ['000123', '123']


def test_seeded_faults_are_recovered_and_reproducible():
    sample = anomaly.sample_events()
    first = anomaly.evaluate_events(sample)
    second = anomaly.evaluate_events(sample)
    pd.testing.assert_frame_equal(first.events, second.events)
    pd.testing.assert_frame_equal(first.metrics, second.metrics)
    assert len(sample) == 800
    assert sample.is_fault.sum() == 40
    assert first.events.evaluated.sum() == 600
    assert first.events.loc[~first.events.evaluated, 'iforest_flag'].isna().all()
    for row in first.metrics.itertuples():
        assert row.precision >= .6
        # Forest masking of short-cycle faults is a real limitation of this
        # fixed reference/threshold, retained in the comparison rather than tuned away.
        assert row.recall >= .6
        assert row.tp + row.fp + row.tn + row.fn == 300


def test_future_values_and_truth_cannot_change_earlier_predictions():
    sample = anomaly.sample_events()
    before = anomaly.evaluate_events(sample)
    changed = sample.copy()
    changed.loc[600:, 'duration_seconds'] *= 100
    changed['is_fault'] = 1 - changed.is_fault
    after = anomaly.evaluate_events(changed)
    pd.testing.assert_frame_equal(before.events.iloc[200:600].drop(columns='is_fault'),
                                  after.events.iloc[200:600].drop(columns='is_fault'))
    for fold in before.folds:
        assert fold['train_end'] < fold['test_start']
        train = sample.iloc[:fold['train_count']]
        for kind, center in fold['scaler_centers'].items():
            assert center == pytest.approx(train.loc[train.event_type == kind, 'duration_seconds'].median())


def test_labels_are_optional_and_never_enter_the_fit():
    sample = anomaly.sample_events()
    labelled = anomaly.evaluate_events(sample)
    unlabelled = anomaly.evaluate_events(sample.drop(columns='is_fault'))
    pd.testing.assert_frame_equal(labelled.events.drop(columns='is_fault'), unlabelled.events)
    assert unlabelled.metrics[['precision', 'recall', 'tp', 'fp', 'tn', 'fn']].isna().all().all()
    assert unlabelled.metrics.flagged.sum() > 0


def test_constant_reference_flags_a_real_departure_without_nan_scores():
    sample = anomaly.sample_events()
    sample['duration_seconds'] = 60.
    detector = anomaly.DurationDetector().fit(sample.iloc[:200])
    query = sample.iloc[200:202].copy()
    query['duration_seconds'] = [60., 120.]
    scored = detector.score(query)
    assert scored.robust_flag.tolist() == [False, True]
    assert np.isfinite(scored.robust_score).all()
    assert np.isfinite(scored.iforest_score).all()
    # A forest cannot extrapolate a useful boundary from an entirely constant log.
    assert not scored.iforest_flag.any()


def test_fit_reuses_frozen_reference_and_rejects_unseen_event_types():
    sample = anomaly.sample_events()
    detector = anomaly.DurationDetector().fit(sample.iloc[:200])
    center = detector.models['cycle'].named_steps['scale'].center_.copy()
    detector.score(sample.iloc[200:])
    np.testing.assert_array_equal(center, detector.models['cycle'].named_steps['scale'].center_)
    with pytest.raises(ValueError, match='reference'):
        anomaly.DurationDetector().fit(sample[sample.event_type == 'cycle']).score(sample)


@pytest.mark.parametrize('column,value,match', [
    ('duration_seconds', np.nan, 'finite'),
    ('duration_seconds', np.inf, 'finite'),
    ('duration_seconds', 0., 'positive'),
    ('duration_seconds', -1., 'positive'),
    ('duration_seconds', 'bad', 'numeric'),
    ('event_type', 'other', 'event_type'),
    ('event_id', '', 'event_id'),
    ('event_id', None, 'event_id'),
    ('timestamp', 'bad', 'timestamp'),
    ('is_fault', 2, 'is_fault'),
])
def test_invalid_events_are_rejected_with_a_reason(column, value, match):
    sample = anomaly.sample_events().astype({column: object})
    sample.loc[0, column] = value
    with pytest.raises(ValueError, match=match):
        anomaly.evaluate_events(sample)


def test_missing_duplicate_small_and_late_event_types_are_rejected():
    sample = anomaly.sample_events()
    with pytest.raises(ValueError, match='columns'):
        anomaly.evaluate_events(sample.drop(columns='timestamp'))
    sample.loc[1, 'event_id'] = sample.loc[0, 'event_id']
    with pytest.raises(ValueError, match='unique'):
        anomaly.evaluate_events(sample)
    with pytest.raises(ValueError, match='20'):
        anomaly.evaluate_events(anomaly.sample_events().iloc[:40])
    sample = anomaly.sample_events()
    sample.loc[:199, 'event_type'] = 'cycle'
    with pytest.raises(ValueError, match='reference'):
        anomaly.evaluate_events(sample)


def test_metrics_count_held_out_faults_by_hand():
    # With a constant training period, the robust baseline flags only row 200.
    sample = anomaly.sample_events().iloc[:400].copy()
    sample['duration_seconds'] = 60.
    sample['is_fault'] = 0
    sample.loc[[200, 201], 'is_fault'] = 1
    sample.loc[200, 'duration_seconds'] = 120.
    result = anomaly.evaluate_events(sample)
    metric = result.metrics.query("method == 'robust' and event_type == 'cycle'").iloc[0]
    assert (metric.tp, metric.fp, metric.tn, metric.fn) == (1, 0, 149, 0)
    assert metric.precision == 1.
    assert metric.recall == 1.
    downtime = result.metrics.query("method == 'robust' and event_type == 'downtime'").iloc[0]
    assert (downtime.tp, downtime.fp, downtime.tn, downtime.fn) == (0, 0, 149, 1)
    assert downtime.precision == 0.
    assert downtime.recall == 0.
