"""Read exported Office files as a consumer, including their embedded data."""
from copy import deepcopy
from io import BytesIO
import math
import posixpath
import subprocess
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pytest

from analysis import fit_candidates, report_payload

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

@pytest.fixture
def payload():
    values = np.random.default_rng(27).gamma(2, 2, 240)
    return report_payload(fit_candidates(values, ['Normal', 'Gamma', 'Exponential']), values,
                          {'source': 'Synthetic Gamma fixture'})

def export(payload, title='DistroFit analysis'):
    from powerpoint_report import create_powerpoint
    return ZipFile(BytesIO(create_powerpoint(payload, title=title)))

def xml(deck, name):
    return ET.fromstring(deck.read(name))

def text(deck, name):
    return ' '.join(xml(deck, name).itertext())

def test_exports_real_chart_data_and_embedded_editable_workbooks(payload):
    with export(payload) as deck:
        scores = xml(deck, 'ppt/charts/chart1.xml')
        values = [float(v.text) for v in scores.findall('.//c:val/c:numRef/c:numCache/c:pt/c:v', NS)]
        assert values == pytest.approx([r['Held-out NLL'] for r in payload['results']])
        with ZipFile(BytesIO(deck.read('ppt/embeddings/data1.xlsx'))) as book:
            cells = xml(book, 'xl/worksheets/sheet1.xml')
            assert [float(c.find('s:v', NS).text) for c in cells.findall('.//s:c', NS)
                    if c.get('r', '').startswith('B') and c.find('s:v', NS) is not None] == pytest.approx(values)
        assert scores.find('c:externalData', NS) is not None
        tails = xml(deck, 'ppt/charts/chart2.xml')
        assert len(tails.findall('.//c:ser', NS)) == 2
        assert '0%' in deck.read('ppt/charts/chart2.xml').decode()

def test_layout_notes_navigation_and_custom_shows_are_native(payload):
    with export(payload) as deck:
        presentation = xml(deck, 'ppt/presentation.xml')
        assert len(presentation.findall('p:sldIdLst/p:sldId', NS)) == 7
        shows = presentation.findall('p:custShowLst/p:custShow', NS)
        assert {s.get('name') for s in shows} == {'Quick discussion', 'Full review'}
        assert [len(s.findall('p:sldLst/p:sld', NS)) for s in shows] == [4, 7]
        assert len([n for n in deck.namelist() if n.startswith('ppt/slideLayouts/slideLayout') and n.endswith('.xml')]) == 3
        assert 'training' in text(deck, 'ppt/notesSlides/notesSlide1.xml').lower()
        assert 'ppt/slides/slide1.xml' in deck.namelist()
        assert xml(deck, 'ppt/slides/slide1.xml').find('.//a:hlinkClick', NS) is not None
        assert 'Gamma' in text(deck, 'ppt/slides/slide1.xml')
        assert 'http' not in text(deck, 'ppt/slides/_rels/slide1.xml.rels')
        for name in deck.namelist():
            if name.endswith('.rels'):
                base = posixpath.dirname(posixpath.dirname(name)) if '/' in name else ''
                for rel in xml(deck, name):
                    assert rel.get('TargetMode') != 'External'
                    assert posixpath.normpath(posixpath.join(base, rel.get('Target'))) in deck.namelist()

def test_infinite_scores_are_excluded_explicitly_and_never_turn_into_zero(payload):
    payload = deepcopy(payload)
    payload['results'][0]['Held-out NLL'] = 'inf'
    with export(payload) as deck:
        chart = xml(deck, 'ppt/charts/chart1.xml')
        values = [float(v.text) for v in chart.findall('.//c:val/c:numRef/c:numCache/c:pt/c:v', NS)]
        assert len(values) == 2
        assert all(math.isfinite(v) for v in values)
        assert 'Excluded from score chart: Gamma' in text(deck, 'ppt/slides/slide2.xml')
        assert min(payload['results'][1:], key=lambda r: r['Held-out NLL'])['Distribution'] in text(deck, 'ppt/slides/slide1.xml')

@pytest.mark.parametrize('kind', ['no_fits', 'all_infinite', 'negative', 'many'])
def test_extreme_analyses_remain_readable_and_honest(payload, kind):
    if kind == 'no_fits':
        payload['results'] = []
        payload['failures'] = {'Normal': 'No finite fit'}
    elif kind == 'all_infinite':
        for row in payload['results']:
            row['Held-out NLL'] = 'inf'
    elif kind == 'negative':
        payload['results'][0]['Held-out NLL'] = -2.5
    else:
        payload['results'] = [dict(deepcopy(payload['results'][0]), Distribution=f'Candidate {i}') for i in range(14)]
    with export(payload) as deck:
        summary = text(deck, 'ppt/slides/slide1.xml')
        if kind in ('no_fits', 'all_infinite'):
            assert 'No finite held-out winner' in summary
        if kind == 'negative':
            assert '-2.5' in text(deck, 'ppt/charts/chart1.xml')
        if kind == 'many':
            assert len(xml(deck, 'ppt/presentation.xml').findall('p:sldIdLst/p:sldId', NS)) == 18


def test_xml_escaping_and_title_limit(payload):
    with export(payload, 'A & B <review>') as deck:
        assert 'A & B <review>' in text(deck, 'ppt/slides/slide1.xml')
    from powerpoint_report import create_powerpoint
    with pytest.raises(ValueError, match='title'):
        create_powerpoint(payload, title='x'*81)


def test_cli_uses_real_csv_and_writes_a_valid_deck(tmp_path):
    source = tmp_path / 'measurements.csv'
    source.write_text('weight\n' + '\n'.join(str(v) for v in range(1, 81)))
    out = tmp_path / 'analysis.pptx'
    result = subprocess.run([sys.executable, 'powerpoint_report.py', str(source), '--column', 'weight',
                             '--out', str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with ZipFile(out) as deck:
        assert '60 training / 20 held out' in text(deck, 'ppt/slides/slide1.xml')


def test_all_chart_series_match_workbook_cells_and_keep_data_private(payload):
    payload['source_data'] = [123456789987.321]
    with export(payload) as deck:
        for index in (1, 2):
            chart = xml(deck, f'ppt/charts/chart{index}.xml')
            with ZipFile(BytesIO(deck.read(f'ppt/embeddings/data{index}.xlsx'))) as book:
                sheet = xml(book, 'xl/worksheets/sheet1.xml')
                numbers = {c.get('r'): float(c.find('s:v', NS).text)
                           for c in sheet.findall('.//s:c', NS) if c.find('s:v', NS) is not None}
                for series_index, series in enumerate(chart.findall('.//c:ser', NS)):
                    cache = [float(v.text) for v in series.findall('.//c:numCache/c:pt/c:v', NS)]
                    assert cache == [numbers[f'{chr(66+series_index)}{i+2}'] for i in range(len(cache))]
        assert all(b'123456789987' not in deck.read(name) for name in deck.namelist())


def test_candidate_details_are_reachable_and_return_to_summary(payload):
    with export(payload) as deck:
        def navigation(number):
            rels = {r.get('Id'): r.get('Target') for r in xml(deck, f'ppt/slides/_rels/slide{number}.xml.rels')}
            return [rels[h.get('{'+NS['r']+'}id')] for h in xml(deck, f'ppt/slides/slide{number}.xml').findall('.//a:hlinkClick', NS)]
        assert 'slide4.xml' in navigation(2)
        assert 'slide1.xml' in navigation(4)
        assert 'slide5.xml' in navigation(4)


@pytest.mark.parametrize('args', [[], ['--sample', 'measurements.csv']])
def test_cli_errors_do_not_leave_partial_output(tmp_path, args):
    out = tmp_path/'report.pptx'
    result = subprocess.run([sys.executable, 'powerpoint_report.py', *args, '--out', str(out)], capture_output=True)
    assert result.returncode != 0
    assert not out.exists()


def test_overwide_titles_are_rejected_before_they_can_overlap(payload):
    from powerpoint_report import create_powerpoint
    with pytest.raises(ValueError, match='title'):
        create_powerpoint(payload, title='W'*80)


def test_title_placeholders_inherit_layout_geometry_and_master_type_size(payload):
    with export(payload) as deck:
        # ElementTree supports only simple predicates, so identify by placeholder.
        titles = [sp for sp in xml(deck, 'ppt/slides/slide1.xml').findall('.//p:sp', NS)
                  if sp.find('p:nvSpPr/p:nvPr/p:ph', NS) is not None]
        assert len(titles) == 1
        assert titles[0].find('p:spPr/a:xfrm', NS) is None
        assert all('sz' not in run.attrib for run in titles[0].findall('.//a:rPr', NS))
        assert xml(deck, 'ppt/slideMasters/slideMaster1.xml').find('p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr', NS).get('sz') == '3200'


@pytest.mark.parametrize('score, expected_min', [(2.5, 0), (-2.5, -2.5), (0, 0)])
def test_score_bar_axis_includes_zero_without_hiding_negative_values(payload, score, expected_min):
    payload['results'] = [payload['results'][0]]
    payload['results'][0]['Held-out NLL'] = score
    with export(payload) as deck:
        axis = xml(deck, 'ppt/charts/chart1.xml').find('c:chart/c:plotArea/c:valAx/c:scaling/c:min', NS)
        assert axis is not None
        assert float(axis.get('val')) == expected_min
        upper = xml(deck, 'ppt/charts/chart1.xml').find('c:chart/c:plotArea/c:valAx/c:scaling/c:max', NS)
        assert upper is not None
        assert float(upper.get('val')) >= max(0, score)
        assert float(upper.get('val')) > expected_min
