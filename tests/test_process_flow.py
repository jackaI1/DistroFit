"""Exercise real Graphviz output and keep SOP routes tied to validated steps."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def flow():
    assert importlib.util.find_spec('process_flow'), 'Process documentation generator is missing'
    return importlib.import_module('process_flow')


def process():
    return dict(title='Measurement handoff', revision='1', purpose='Keep held samples out of accepted data.',
                start='receive', steps=[
                    dict(id='receive', kind='task', title='Receive sample', owner='Bench operator',
                         instruction='Record the sample ID and units.', record='Sample log',
                         next=[dict(to='check', label='')]),
                    dict(id='check', kind='decision', title='Instrument current?', owner='Bench operator',
                         instruction='Read the calibration label.', record='Instrument ID and status',
                         next=[dict(to='finish', label='Yes'), dict(to='hold', label='No')]),
                    dict(id='hold', kind='task', title='Hold sample', owner='Area lead',
                         instruction='Resolve the instrument issue before retrying.', record='Hold log',
                         next=[dict(to='check', label='Recheck')]),
                    dict(id='finish', kind='end', title='Release data', owner='Reviewer',
                         instruction='Approve the traceable measurement log.', record='Approved log', next=[]),
                ])


def test_real_graphviz_diagram_and_sop_share_instructions_and_branch_routes(flow):
    source = process()
    original = copy.deepcopy(source)
    package = flow.build_process(source)
    assert source == original
    root = ET.fromstring(package['svg'])
    ns = {'s': 'http://www.w3.org/2000/svg'}
    nodes = [g.find('s:title', ns).text for g in root.findall('.//s:g[@class="node"]', ns)]
    edges = [g.find('s:title', ns).text.replace(':e', '')
             for g in root.findall('.//s:g[@class="edge"]', ns)]
    assert set(nodes) == {'_start', 'receive', 'check', 'hold', 'finish'}
    assert set(edges) == {'_start->receive', 'receive->check', 'check->finish', 'check->hold', 'hold->check'}
    assert 'Yes' in package['sop'] and 'No' in package['sop'] and 'Recheck' in package['sop']
    assert 'Read the calibration label.' in package['sop']
    assert 'href="#step-hold"' in package['sop']
    assert 'Instrument ID and status' in package['sop']
    assert '<svg' in package['sop']
    assert 'shape=diamond' in package['dot']


@pytest.mark.parametrize('mutate', [
    lambda p: p.update(steps=[]),
    lambda p: p.update(start='missing'),
    lambda p: p['steps'][1]['next'][0].update(to='missing'),
    lambda p: p['steps'][1]['next'][0].update(label=''),
    lambda p: p['steps'][1]['next'][1].update(label='Yes'),
    lambda p: p['steps'][0].update(id='check'),
    lambda p: p['steps'][0].update(id='bad"; URL="https://example.com'),
    lambda p: p['steps'][0].update(kind='other'),
    lambda p: p['steps'][0].update(instruction=''),
    lambda p: p['steps'][0].update(next=[]),
    lambda p: p['steps'][3].update(next=[dict(to='receive', label='')]),
    lambda p: p['steps'][1].update(next=[dict(to='hold', label='No')]),
    lambda p: p['steps'][1]['next'][0].update(to='hold'),  # no route to terminal
    lambda p: p['steps'][0]['next'][0].update(to='finish'),  # unreachable steps
    lambda p: p['steps'][0].update(next='check'),
])
def test_invalid_or_misleading_workflows_rejected_before_rendering(flow, mutate):
    value = process()
    mutate(value)
    with pytest.raises(ValueError):
        flow.validate_process(value)


def test_untrusted_labels_are_text_in_svg_and_sop(flow):
    source = process()
    source['title'] = '<script>alert("x")</script>'
    source['steps'][0]['title'] = 'Receive "sample" \\N <img src=x onerror=alert(1)>'
    source['steps'][0]['instruction'] = '<script>bad()</script> & check'
    result = flow.build_process(source)
    ET.fromstring(result['svg'])
    assert '<script>' not in result['sop'] and '<img src=x' not in result['sop']
    assert '&lt;script&gt;bad()&lt;/script&gt; &amp; check' in result['sop']
    assert '\\N' in ''.join(ET.fromstring(result['svg']).itertext())


def test_missing_graphviz_is_an_actionable_error(flow, monkeypatch):
    monkeypatch.setattr(flow.shutil, 'which', lambda _: None)
    with pytest.raises(ValueError, match='Graphviz'):
        flow.build_process(process())


def test_graph_marks_declared_start_even_when_not_first_step(flow):
    source = process()
    source['steps'][2]['next'][0]['to'] = 'receive'
    source['start'] = 'hold'
    package = flow.build_process(source)
    root = ET.fromstring(package['svg'])
    ns = {'s': 'http://www.w3.org/2000/svg'}
    edges = [g.find('s:title', ns).text for g in root.findall('.//s:g[@class="edge"]', ns)]
    assert '_start->hold' in edges
    assert '_start->receive' not in edges
    assert 'Start at <a href="#step-hold">' in package['sop']


def test_committed_measurement_workflow_builds_real_diagram(flow):
    source = json.loads((ROOT / 'examples/lean/measurement_process.json').read_text())
    result = flow.build_process(source)
    assert len(source['steps']) >= 8
    assert 'calibration' in result['sop'].lower()
    assert 'DistroFit' in result['sop']
    ET.fromstring(result['svg'])
