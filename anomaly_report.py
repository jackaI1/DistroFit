"""Save duration screening as an interactive chart and a Power BI snapshot."""
import argparse
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from anomaly import AnomalyResult, SEED, evaluate_events, read_event_csv, sample_events
from powerbi.anomaly_project import build_anomaly_project


def event_chart(result: AnomalyResult) -> go.Figure:
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           subplot_titles=('Cycle times', 'Downtime events'))
    for row, kind in enumerate(('cycle', 'downtime'), 1):
        events = result.events[result.events.event_type == kind]
        figure.add_trace(go.Scatter(x=events.timestamp, y=events.duration_seconds,
                                   customdata=events.event_id, name=f'{kind}: all events', mode='markers',
                                   marker=dict(color='#8c959f', size=5),
                                   hovertemplate='%{customdata}<br>%{y:.2f} seconds<extra></extra>'), row=row, col=1)
        for method, color, symbol in [('iforest', '#c2410c', 'circle-open'), ('robust', '#1d4ed8', 'x')]:
            flagged = events[events[f'{method}_flag'].fillna(False)]
            figure.add_trace(go.Scatter(x=flagged.timestamp, y=flagged.duration_seconds,
                                       customdata=flagged.event_id, mode='markers', name=f'{kind}: {method}',
                                       marker=dict(color=color, size=11, symbol=symbol),
                                       hovertemplate='%{customdata}<br>%{y:.2f} seconds<extra>%{fullData.name}</extra>'),
                             row=row, col=1)
        figure.update_yaxes(title_text='Duration (seconds)', row=row, col=1)
    figure.add_vrect(x0=result.events.timestamp.iloc[0].isoformat(), x1=result.folds[0]['train_end'],
                     fillcolor='#8c959f', opacity=.12, line_width=0,
                     annotation_text='Reference only; no flags', row=1, col=1)
    figure.update_layout(height=720, title='Events to investigate, not confirmed faults',
                         legend=dict(orientation='h'), margin=dict(t=100, b=100))
    figure.update_xaxes(title_text='Event time (UTC)', row=2, col=1)
    return figure


def summary_dict(result: AnomalyResult) -> dict:
    metrics = result.metrics.astype(object).where(pd.notna(result.metrics), None).to_dict(orient='records')
    return {'seed': SEED, 'events': len(result.events), 'evaluated_events': int(result.events.evaluated.sum()),
            'validation': 'Three expanding chronological folds; first quarter is reference only.',
            'settings': {'iforest_trees': 200, 'iforest_contamination': .05, 'robust_threshold': 3.5},
            'metrics': metrics, 'folds': result.folds,
            'limitations': 'Generated faults are not factory accuracy. Flags require investigation. '
                           'Compare one machine/product at a time; do not mix operating regimes.'}


def write_report(result: AnomalyResult, out: Path) -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    result.events.to_csv(out / 'events.csv', index=False)
    result.metrics.to_csv(out / 'metrics.csv', index=False)
    (out / 'summary.json').write_text(json.dumps(summary_dict(result), indent=2, allow_nan=False) + '\n')
    # Embedded JavaScript makes the saved chart usable offline, without a CDN.
    event_chart(result).write_html(out / 'events.html', include_plotlyjs=True)
    build_anomaly_project(result, out / 'powerbi')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--sample', action='store_true', help='Use the fixed generated production log.')
    source.add_argument('csv', nargs='?', type=Path, help='One machine/product event CSV.')
    parser.add_argument('--out', type=Path, required=True, help='A new output folder.')
    args = parser.parse_args()
    try:
        frame = sample_events() if args.sample else read_event_csv(args.csv)
        result = evaluate_events(frame)
        write_report(result, args.out)
    except (ValueError, OSError) as error:
        parser.exit(2, f'Cannot build report: {error}\n')
    print(result.metrics.to_string(index=False))
    print(f'Saved {len(result.events)} events to {args.out}')


if __name__ == '__main__':
    main()
