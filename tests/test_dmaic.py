import json
from pathlib import Path

import pytest

from dmaic import analyze, render_report


def sample():
    return json.loads(Path('examples/dmaic/production.json').read_text())


def test_capability_and_pareto():
    data = sample()
    result = analyze(data)
    assert result['capability']['Cp'] > result['capability']['Cpk']
    assert result['defects'].iloc[0]['Category'] == 'Seal leak'
    assert result['defects'].iloc[0]['Count'] == 9
    assert result['out_of_spec'] == 1
    assert set(result['defects']['Category']) == set(data['root_causes'])


def test_mean_outside_spec_has_negative_cpk():
    data = sample()
    data['measurements'] = [12, 12.1, 12.2, 12.1, 12.3]
    data['baseline'] = 5
    assert analyze(data)['capability']['Cpk'] < 0


def test_missing_root_cause_rejected():
    data = sample()
    del data['root_causes']['Seal leak']
    with pytest.raises(ValueError, match='root cause'):
        analyze(data)


def test_board_contains_all_stages_and_escapes_text(tmp_path):
    data = sample()
    data['objective'] = '<script>bad</script>'
    output = tmp_path / 'board.html'
    render_report(data, output)
    page = output.read_text()
    assert '&lt;script&gt;' in page
    for text in ['Define', 'Measure', 'Analyze', 'Improve', 'Control', 'Downtime', 'Action tracker']:
        assert text in page
    assert 'data:image/png;base64' in page
