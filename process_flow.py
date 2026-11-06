"""One validated step list produces a Graphviz flow chart and an HTML SOP."""
import copy
from html import escape
import json
import re
import shutil
import subprocess
import textwrap


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError(f'{name} must be nonblank text of at most 2000 characters.')
    if any(ord(c) < 32 and c not in '\n\t\r' for c in value):
        raise ValueError(f'{name} contains a control character.')
    return value.strip()


def validate_process(source):
    """Allow rework loops, but require reachable steps with a route to an end."""
    if not isinstance(source, dict) or set(source) != {'title', 'revision', 'purpose', 'start', 'steps'}:
        raise ValueError('Process needs title, revision, purpose, start and steps.')
    result = copy.deepcopy(source)
    for key in ('title', 'revision', 'purpose'):
        result[key] = _text(source[key], key)
    steps = result['steps']
    if not isinstance(steps, list) or not 1 <= len(steps) <= 100:
        raise ValueError('Supply between 1 and 100 steps.')
    ids = set()
    for step in steps:
        if not isinstance(step, dict) or set(step) != {'id', 'kind', 'title', 'owner', 'instruction', 'record', 'next'}:
            raise ValueError('Every step needs id, kind, title, owner, instruction, record and next.')
        sid = step['id']
        if not isinstance(sid, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', sid) or sid in ids:
            raise ValueError('Step IDs must be unique letters, numbers, underscores or hyphens, starting with a letter.')
        ids.add(sid)
        if step['kind'] not in ('task', 'decision', 'end'):
            raise ValueError('Step kind must be task, decision or end.')
        for key in ('title', 'owner', 'instruction', 'record'):
            step[key] = _text(step[key], f'{sid} {key}')
        routes = step['next']
        expected = {'task': 1, 'decision': 2, 'end': 0}[step['kind']]
        if not isinstance(routes, list) or len(routes) != expected:
            raise ValueError('Tasks need one route, decisions two labelled routes, and ends no routes.')
        for route in routes:
            if (not isinstance(route, dict) or set(route) != {'to', 'label'}
                    or not isinstance(route['to'], str) or not isinstance(route['label'], str)):
                raise ValueError('Each route needs text to and label fields.')
            if route['label']:
                route['label'] = _text(route['label'], 'Route label')
        if step['kind'] == 'decision' and (any(not r['label'] for r in routes)
                                          or len({r['label'] for r in routes}) != 2
                                          or len({r['to'] for r in routes}) != 2):
            raise ValueError('A decision needs two distinct destinations and nonblank, distinct route labels.')
    if not isinstance(result['start'], str) or result['start'] not in ids:
        raise ValueError('Start must name an existing step.')
    graph = {step['id']: [route['to'] for route in step['next']] for step in steps}
    if any(target not in ids for targets in graph.values() for target in targets):
        raise ValueError('Every route must name an existing step.')

    def reachable(start, edges):
        seen, pending = set(), list(start)
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending.extend(edges[current])
        return seen

    if reachable([result['start']], graph) != ids:
        raise ValueError('Every step must be reachable from start.')
    reverse = {sid: [] for sid in ids}
    for sid, targets in graph.items():
        for target in targets:
            reverse[target].append(sid)
    ends = [step['id'] for step in steps if step['kind'] == 'end']
    if reachable(ends, reverse) != ids:
        raise ValueError('Every step must have a route to an end; closed loops cannot finish.')
    return result


def process_dot(source):
    """Quote all text as DOT strings; user input cannot add graph attributes."""
    source = validate_process(source)
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = ['digraph process {', 'graph [rankdir=TB, bgcolor="white", nodesep=0.45, ranksep=0.55];',
             'node [fontname="Helvetica", fontsize=12, margin="0.18,0.10"];',
             'edge [fontname="Helvetica", fontsize=11];',
             '_start [shape=oval, label="Start"];', f'_start -> {quote(source["start"])};']
    positions = {step['id']: index for index, step in enumerate(source['steps'], 1)}
    for index, step in enumerate(source['steps'], 1):
        shape = {'task': 'box', 'decision': 'diamond', 'end': 'oval'}[step['kind']]
        label = f"{index}. " + '\n'.join(textwrap.wrap(step['title'], 38))
        lines.append(f'{quote(step["id"])} [shape={shape}, label={quote(label)}];')
        for route in step['next']:
            # Put backward/recheck routes on the outside to separate their labels.
            ports = ', tailport=e, headport=e' if positions[route['to']] <= index else ''
            lines.append(f'{quote(step["id"])} -> {quote(route["to"])} [label={quote(route["label"])}{ports}];')
    return '\n'.join([*lines, '}'])


def build_process(source):
    """Run the installed Graphviz binary, then embed its SVG in a portable SOP."""
    source = validate_process(source)
    dot = process_dot(source)
    executable = shutil.which('dot')
    if not executable:
        raise ValueError('Install Graphviz first: brew install graphviz (macOS) or apt-get install graphviz (Linux).')
    try:
        rendered = subprocess.run([executable, '-Tsvg'], input=dot, text=True,
                                  capture_output=True, timeout=20, check=True)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError('Graphviz could not render this process. Check the step list and Graphviz installation.') from error
    svg = rendered.stdout
    # Embed only the SVG root, without the XML declaration and document type.
    inline_svg = svg[svg.index('<svg'):]
    steps = {step['id']: step for step in source['steps']}
    sections = []
    for index, step in enumerate(source['steps'], 1):
        routes = ''.join(f'<li>{escape(route["label"] or "Next")}: '
                         f'<a href="#step-{route["to"]}">{escape(steps[route["to"]]["title"])}</a></li>'
                         for route in step['next'])
        sections.append(f'<section id="step-{step["id"]}"><h2>{index}. {escape(step["title"])}</h2>'
                        f'<p><strong>Responsible role:</strong> {escape(step["owner"])}</p>'
                        f'<p class="instruction">{escape(step["instruction"])}</p>'
                        f'<p><strong>Record:</strong> {escape(step["record"])}</p>'
                        + (f'<ul>{routes}</ul>' if routes else '<p>End of this route.</p>') + '</section>')
    title = escape(source['title'])
    sop = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | SOP</title><style>
body {{font: 17px/1.6 system-ui,sans-serif;color:#172d3a;background:#fff;max-width:74ch;margin:40px auto;padding:0 24px}}
h1,h2 {{line-height:1.2}} h2 {{margin-top:2em}} a {{color:#075a8c;text-underline-offset:3px}}
.diagram {{overflow:auto}} svg {{max-width:100%;height:auto}} .instruction {{white-space:pre-wrap}}
section {{break-inside:avoid}} :focus-visible {{outline:3px solid #075a8c;outline-offset:3px}}
@media print {{body {{font-size:11pt;margin:0;max-width:none}} .diagram {{break-after:page}}}}
</style></head><body><h1>{title}</h1><p>Standard operating procedure (SOP), revision {escape(source['revision'])}.</p>
<p>{escape(source['purpose'])}</p><p>Start at <a href="#step-{source['start']}">{escape(steps[source['start']]['title'])}</a>.
Follow the labelled routes, including holds and rechecks. The list order is a reference, not permission to skip a decision.</p>
<div class="diagram" aria-label="Process flow chart">{inline_svg}</div>
{''.join(sections)}</body></html>'''
    return {'dot': dot, 'svg': svg, 'sop': sop}
