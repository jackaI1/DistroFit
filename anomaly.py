"""Past-only duration screening, kept separate from labels and presentation."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

SEED = 42
REQUIRED = ('event_id', 'timestamp', 'event_type', 'duration_seconds')


def read_event_csv(source) -> pd.DataFrame:
    """Keep identifiers verbatim and bound the import before validation."""
    return pd.read_csv(source, dtype={'event_id': 'string'}, nrows=5001)


def validate_events(events: pd.DataFrame) -> pd.DataFrame:
    """Return a chronological copy; reject bad rows rather than silently dropping them."""
    if not set(REQUIRED) <= set(events.columns):
        raise ValueError(f'Required columns: {", ".join(REQUIRED)}')
    if not 1 <= len(events) <= 5000:
        raise ValueError('Use between 1 and 5000 events per machine/product report.')
    columns = list(REQUIRED) + (['is_fault'] if 'is_fault' in events else [])
    frame = events[columns].copy()
    if frame.event_id.isna().any() or frame.event_id.astype(str).str.strip().eq('').any():
        raise ValueError('Every event_id must be nonempty.')
    frame['event_id'] = frame.event_id.astype(str).str.strip()
    if frame.event_id.duplicated().any():
        raise ValueError('event_id values must be unique.')
    if not frame.event_type.isin(['cycle', 'downtime']).all():
        raise ValueError('event_type must be cycle or downtime.')
    try:
        frame['duration_seconds'] = pd.to_numeric(frame.duration_seconds, errors='raise').astype(float)
    except (ValueError, TypeError) as error:
        raise ValueError('duration_seconds must be numeric.') from error
    if not np.isfinite(frame.duration_seconds).all():
        raise ValueError('Durations must be finite.')
    if (frame.duration_seconds <= 0).any():
        raise ValueError('Durations must be positive seconds.')
    try:
        frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True, errors='raise', format='mixed')
    except (ValueError, TypeError) as error:
        raise ValueError('Each timestamp must be a valid date/time.') from error
    if frame.timestamp.isna().any() or frame.timestamp.duplicated().any():
        raise ValueError('Each timestamp must be present and unique; order simultaneous events explicitly.')
    if 'is_fault' in frame:
        if not frame.is_fault.isin([0, 1]).all():
            raise ValueError('is_fault must contain only 0 or 1, without missing labels.')
        frame['is_fault'] = frame.is_fault.astype(int)
    return frame.sort_values('timestamp', kind='stable').reset_index(drop=True)


def sample_events() -> pd.DataFrame:
    """One synthetic machine/product log, including long stops and fast/slow cycles."""
    rng = np.random.default_rng(SEED)
    count = 800
    kinds = np.where(np.arange(count) % 2 == 0, 'cycle', 'downtime')
    durations = np.where(kinds == 'cycle', rng.normal(45, 3, count), rng.normal(240, 25, count))
    faults = rng.choice(count, 40, replace=False)
    labels = np.zeros(count, dtype=int)
    labels[faults] = 1
    durations[faults] *= np.where(kinds[faults] == 'downtime', 4.,
                                 np.where(np.arange(len(faults)) % 2 == 0, 3., .25))
    return pd.DataFrame({'event_id': [f'event-{i:04d}' for i in range(count)],
                         'timestamp': pd.date_range('2026-01-01', periods=count, freq='15min', tz='UTC'),
                         'event_type': kinds, 'duration_seconds': durations, 'is_fault': labels})


class DurationDetector:
    """Fit once on reference events, then score later events without refitting."""

    def __init__(self):
        self.models = {}
        self.baselines = {}

    def fit(self, reference: pd.DataFrame):
        frame = validate_events(reference)
        self.models = {}
        self.baselines = {}
        for kind, group in frame.groupby('event_type'):
            if len(group) < 20:
                raise ValueError(f'At least 20 reference events required for {kind}.')
            values = group[['duration_seconds']]
            pipeline = Pipeline([('scale', RobustScaler()),
                                 ('forest', IsolationForest(n_estimators=200, contamination=.05,
                                                            random_state=SEED, n_jobs=1))])
            pipeline.fit(values)
            median = float(values.duration_seconds.median())
            mad = float(np.median(np.abs(values.duration_seconds - median)))
            # A constant reference has no estimated spread. Use a small, finite
            # tolerance for roundoff; any material departure merits review.
            spread = max(mad / .6744897501960817, max(abs(median), 1.) * 1e-9)
            self.models[kind] = pipeline
            self.baselines[kind] = (median, spread)
        return self

    def score(self, events: pd.DataFrame) -> pd.DataFrame:
        frame = validate_events(events)
        for kind, group in frame.groupby('event_type'):
            if kind not in self.models:
                raise ValueError(f'No fitted reference for {kind}; include it in the reference period.')
            values = group[['duration_seconds']]
            median, spread = self.baselines[kind]
            robust = np.abs(values.duration_seconds - median) / spread
            # Both scores point upwards toward more unusual events. Forest zero
            # and robust 3.5 are boundaries, not comparable probabilities.
            frame.loc[group.index, 'iforest_score'] = -self.models[kind].decision_function(values)
            frame.loc[group.index, 'robust_score'] = robust
        frame['iforest_flag'] = frame.iforest_score > 0
        frame['robust_flag'] = frame.robust_score > 3.5
        return frame


@dataclass
class AnomalyResult:
    events: pd.DataFrame
    metrics: pd.DataFrame
    folds: list[dict]


def evaluate_events(events: pd.DataFrame) -> AnomalyResult:
    """Three expanding folds: the first quarter warms up, later rows score once.

    Labels are read only for reporting. Hyperparameters are fixed, not selected
    against these folds. Unlabelled real logs get flag counts, never fake accuracy.
    """
    frame = validate_events(events)
    if len(frame) < 80:
        raise ValueError('Need at least 20 reference events per type; provide at least 80 rows.')
    frame['fold'] = pd.Series(pd.NA, index=frame.index, dtype='Int64')
    for method in ('iforest', 'robust'):
        frame[f'{method}_score'] = np.nan
        frame[f'{method}_flag'] = pd.Series(pd.NA, index=frame.index, dtype='boolean')
    frame['evaluated'] = False
    folds = []
    for fold, (train, test) in enumerate(TimeSeriesSplit(n_splits=3).split(frame), 1):
        detector = DurationDetector().fit(frame.iloc[train])
        scored = detector.score(frame.iloc[test])
        for column in ('iforest_score', 'robust_score', 'iforest_flag', 'robust_flag'):
            frame.loc[test, column] = scored[column].to_numpy()
        frame.loc[test, 'fold'] = fold
        frame.loc[test, 'evaluated'] = True
        folds.append({'fold': fold, 'train_count': len(train), 'test_count': len(test),
                      'train_start': frame.timestamp.iloc[train[0]].isoformat(),
                      'train_end': frame.timestamp.iloc[train[-1]].isoformat(),
                      'test_start': frame.timestamp.iloc[test[0]].isoformat(),
                      'test_end': frame.timestamp.iloc[test[-1]].isoformat(),
                      'scaler_centers': {k: float(v.named_steps['scale'].center_[0])
                                         for k, v in detector.models.items()}})
    metrics = []
    for kind, group in frame[frame.evaluated].groupby('event_type'):
        for method in ('iforest', 'robust'):
            predicted = group[f'{method}_flag'].to_numpy(dtype=bool)
            row = dict(event_type=kind, method=method, evaluated=len(group), flagged=int(predicted.sum()),
                       tp=None, fp=None, tn=None, fn=None, precision=None, recall=None)
            if 'is_fault' in group:
                tn, fp, fn, tp = confusion_matrix(group.is_fault, predicted, labels=[0, 1]).ravel()
                row.update(tp=int(tp), fp=int(fp), tn=int(tn), fn=int(fn),
                           precision=float(tp / (tp + fp)) if tp + fp else 0.,
                           recall=float(tp / (tp + fn)) if tp + fn else 0.)
            metrics.append(row)
    return AnomalyResult(frame, pd.DataFrame(metrics), folds)
