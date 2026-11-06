"""Create a self-contained DMAIC review from a JSON production record."""
import argparse
import base64
import html
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import spc


def analyze(data):
    values = data['measurements']
    if not (data['lsl'] < data['usl']):
        raise ValueError('Lower specification must be below upper specification.')
    chart = spc.imr_chart(values, baseline=data['baseline'])
    capability = spc.capability(values, data['lsl'], data['usl'], chart['sigma_within'])
    defects = spc.pareto_table(data['defects'])
    if set(defects['Category']) != set(data['root_causes']):
        raise ValueError('Every defect category needs exactly one root cause record.')
    for category, record in data['root_causes'].items():
        if not record.get('fishbone') or len(record.get('whys', [])) != 5 or not all(record['whys']) or not record.get('evidence'):
            raise ValueError(f'Incomplete root cause record: {category}')
    if any(action['category'] not in data['root_causes'] for action in data['actions']):
        raise ValueError('Actions must refer to a defect category.')
    return {'chart': chart, 'capability': capability, 'defects': defects,
            'downtime': spc.downtime_pareto(data['downtime']),
            'out_of_spec': sum(v < data['lsl'] or v > data['usl'] for v in values)}


def _image(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def render_report(data, output):
    result = analyze(data)
    esc = lambda value: html.escape(str(value))
    c = result['chart']['individuals']
    fig, ax = plt.subplots(figsize=(7, 2.2))
    ax.plot(range(1, len(c['values']) + 1), c['values'], marker='o', markersize=3)
    for value, name, color in [(c['center'], 'Centre', 'black'), (c['lcl'], 'LCL', 'red'), (c['ucl'], 'UCL', 'red')]:
        ax.axhline(value, label=f'{name} {value:.2f}', color=color, linestyle='--', linewidth=.8)
    ax.set_xlabel('Reading order'); ax.set_ylabel('Volume (mL)'); ax.legend(fontsize=7, ncol=3)
    control = _image(fig)
    fig = spc.pareto_chart(result['downtime'], 'Downtime Pareto', 'Minutes', 'Minutes stopped')
    downtime = _image(fig)
    causes = ''.join(f"<li><b>{esc(k)}</b> ({esc(v['fishbone'])}): {' → '.join(esc(w) for w in v['whys'])}. Evidence: {esc(v['evidence'])}</li>" for k, v in data['root_causes'].items())
    actions = ''.join('<tr>' + ''.join(f'<td>{esc(a[k])}</td>' for k in ('category', 'action', 'owner', 'due', 'status')) + '</tr>' for a in data['actions'])
    defects = ', '.join(f"{esc(row.Category)}: {row.Count:g}" for row in result['defects'].itertuples())
    flags = sorted(set(c['flagged']))
    mr_flags = result['chart']['moving_range']['flagged']
    cap = result['capability']
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>DMAIC management board</title><style>
    body{{font:12px Arial;margin:1em;color:#172431}} h1,h2{{margin:.3em 0}} h2{{color:#175d68}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:1em}} img{{width:100%}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #bbb;padding:3px;text-align:left}} li{{margin-bottom:3px}} @media print{{@page{{size:landscape;margin:8mm}} body{{font-size:9px}} img{{max-height:150px;object-fit:contain}}}}
    </style><h1>DMAIC visual management board</h1><section><h2>Define</h2>{esc(data['objective'])}</section><div class="grid"><section><h2>Measure</h2><p>Cp {cap['Cp']:.2f}; Cpk {cap['Cpk']:.2f}; {result['out_of_spec']} of {cap['n']} readings outside specifications. Limits {data['lsl']} to {data['usl']}. Within-process variation comes from the first {data['baseline']} readings.</p><img alt="Individuals control chart" src="data:image/png;base64,{control}"><p>Control status: {'signals to investigate' if flags or mr_flags else 'no rule signals'}; individuals signals at readings {esc([i+1 for i in flags])}; moving-range signals ending at readings {esc([i+2 for i in mr_flags])}. Limits are estimated from the baseline, which needs stability review.</p></section><section><h2>Analyze</h2><p>Defects ranked by count: {defects}.</p><img alt="Downtime Pareto" src="data:image/png;base64,{downtime}"><ul>{causes}</ul></section></div><h2>Improve: Action tracker</h2><table><tr><th>Defect</th><th>Action</th><th>Owner</th><th>Due</th><th>Status</th></tr>{actions}</table><h2>Control</h2><p>{esc(data['control_plan'])} Capability assumes approximately normal data and a stable process; investigate chart signals before interpreting it as predictive.</p></html>'''
    Path(output).write_text(page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='examples/dmaic/production.json')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    render_report(json.loads(Path(args.input).read_text()), args.out)


if __name__ == '__main__':
    main()
