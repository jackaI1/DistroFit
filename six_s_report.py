"""Portable 6S review bundle, using the same calculations as the app page."""
import argparse
from html import escape
import io
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import pandas as pd

from process_flow import build_process, validate_process
from six_s import audit_trend, findings_pareto, findings_table, load_history, validate_history
from spc import pareto_chart

EXAMPLES = Path(__file__).resolve().parent / 'examples' / 'lean'


def load_example():
    return (load_history((EXAMPLES / 'audit_history.json').read_bytes()),
            json.loads((EXAMPLES / 'measurement_process.json').read_text()))


def trend_chart(trend, area):
    figure = Figure(figsize=(9, 4), layout='constrained')
    axis = figure.subplots()
    if not trend.empty:
        axis.plot(range(len(trend)), trend['percent'], marker='o', label='Overall')
        axis.plot(range(len(trend)), trend['Safety'], marker='s', label='Safety')
        axis.set_xticks(range(len(trend)), [f'{r.date}\n{r.audit_id}' for r in trend.itertuples()], rotation=30)
        axis.legend()
    else:
        axis.text(.5, .5, 'No audits for this area', ha='center', transform=axis.transAxes)
    axis.set(ylim=(0, 105), ylabel='Applicable checklist points (%)', title=f'6S audit history: {area}')
    axis.grid(axis='y', alpha=.2)
    return figure


def _png(figure):
    try:
        buffer = io.BytesIO()
        figure.savefig(buffer, format='png', dpi=130)
        return buffer.getvalue()
    finally:
        figure.clear()


def export_report(history, process, out):
    """Validate everything before creating a new output directory; never overwrite."""
    history = validate_history(history)
    process = validate_process(process)
    package = build_process(process)
    areas = sorted({a['area'] for a in history['audits']})
    assets = {'audit_history.json': json.dumps(history, indent=2, allow_nan=False).encode(),
              'process.json': json.dumps(process, indent=2).encode(),
              'process.dot': package['dot'].encode(), 'process.svg': package['svg'].encode(),
              'sop.html': package['sop'].encode()}
    links, trends, all_findings, paretos = [], [], [], []
    # Single-area filenames are convenient; multiple areas get separate charts.
    for index, area in enumerate(areas):
        trend = audit_trend(history, area)
        findings = findings_table(history, area)
        pareto = findings_pareto(history, area)
        trends.append(trend)
        all_findings.append(findings)
        paretos.append(pareto.assign(area=area))
        suffix = '' if len(areas) == 1 else f'-{index + 1}'
        assets[f'trend{suffix}.png'] = _png(trend_chart(trend, area))
        assets[f'pareto{suffix}.png'] = _png(pareto_chart(pareto, f'Unmet checks: {area}'))
        links.append(f'<h2>{escape(area)}</h2><p>Audits: {len(trend)}. Finding observations: {len(findings)}.</p>'
                     f'<img src="trend{suffix}.png" alt="Overall and safety scores over time">'
                     f'<img src="pareto{suffix}.png" alt="Findings ranked by 6S pillar">')
    empty = {'schema_version': 1, 'audits': []}
    tables = {'audit_scores.csv': pd.concat(trends, ignore_index=True) if trends else audit_trend(empty, ''),
              'findings.csv': pd.concat(all_findings, ignore_index=True) if all_findings else findings_table(empty, ''),
              'pareto.csv': pd.concat(paretos, ignore_index=True) if paretos else findings_pareto(empty, '').assign(area=[])}
    for name, table in tables.items():
        assets[name] = table.to_csv(index=False).encode()
    assets['index.html'] = ('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>6S bench review</title>
<style>body{font:17px/1.6 system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#172d3a}
img{max-width:100%;height:auto}a{color:#075a8c}</style><h1>6S bench review</h1>
<p>Each score is earned points divided by four times the applicable checks. N/A checks are excluded.
Compare the same area and review exclusions before reading a trend. Safety findings require attention regardless of the overall score.</p>
<p>Pareto bars count unmet checklist observations, including repeats across dates. They do not count risk or lost points.
Historical actions are snapshots, not an open-ticket register. These checks are not a safety certification.</p>'''
                           + ''.join(links) + '''<h2>Process instructions</h2><p><a href="sop.html">Open the SOP with its flow chart</a>.
<a href="process.svg">Open the diagram</a>.</p><p><a href="audit_history.json">Portable audit history</a> ·
<a href="audit_scores.csv">Score table</a> · <a href="findings.csv">Finding details</a> · <a href="pareto.csv">Pareto table</a></p></html>''').encode()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        for name, data in assets.items():
            (out / name).write_bytes(data)
    except BaseException:
        shutil.rmtree(out)
        raise
    return out


def main():
    parser = argparse.ArgumentParser(description='Save a 6S audit review, Graphviz flow chart and SOP.')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--sample', action='store_true', help='Use generated measurement-bench audits')
    source.add_argument('--history', type=Path, help='Portable audit JSON')
    parser.add_argument('--process', type=Path, help='Documented process step JSON (required with --history)')
    parser.add_argument('--out', type=Path, required=True, help='New output directory')
    args = parser.parse_args()
    if args.history and not args.process:
        parser.error('--history requires --process')
    try:
        if args.sample:
            history, process = load_example()
        else:
            history = load_history(args.history.read_bytes())
        if args.process:
            process = json.loads(args.process.read_text())
        output = export_report(history, process, args.out)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Cannot build report: {error}\n')
    print(f'Saved {len(history["audits"])} audits and a process SOP to {output}')


if __name__ == '__main__':
    main()
