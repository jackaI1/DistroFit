"""The report must be a project with real model/visual bindings, not a recipe."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / 'powerbi'


def test_openable_project_has_model_relationships_and_measures():
    assert (PBI / 'DistroFit.pbip').is_file(), 'missing loadable Power BI project'
    model = json.loads((PBI / 'DistroFit.SemanticModel/model.bim').read_text())['model']
    tables = {t['name']: t for t in model['tables']}
    assert {'fact_fit', 'dim_dataset', 'dim_distribution', 'dim_run'} <= tables.keys()
    assert len(model['relationships']) == 3
    for relationship in model['relationships']:
        assert relationship['fromTable'] == 'fact_fit'
        assert relationship['crossFilteringBehavior'] == 'oneDirection'
        assert relationship['toCardinality'] == 'one'
    assert len(tables['_Measures']['measures']) >= 15
    assert all(t['partitions'] for t in tables.values())


def test_four_pages_have_bound_visuals():
    definition = PBI / 'DistroFit.Report/definition'
    pages = list((definition / 'pages').glob('*/page.json'))
    assert len(pages) == 4, 'missing real report pages'
    model = json.loads((PBI / 'DistroFit.SemanticModel/model.bim').read_text())['model']
    columns = {t['name']: {c['name'] for c in t['columns']} for t in model['tables']}
    measures = {m['name'] for t in model['tables'] for m in t.get('measures', [])}
    for page in pages:
        visuals = list(page.parent.glob('visuals/*/visual.json'))
        assert len(visuals) >= 3
        for path in visuals:
            visual = json.loads(path.read_text())['visual']
            for role in visual['query']['queryState'].values():
                for projection in role['projections']:
                    field = projection['field']
                    kind = next(iter(field))
                    binding = field[kind]
                    table = binding['Expression']['SourceRef']['Entity']
                    assert table in columns
                    if kind == 'Measure':
                        assert binding['Property'] in measures
                    else:
                        assert binding['Property'] in columns[table]


def test_project_regenerates_exactly_from_export(tmp_path):
    from powerbi.build_project import build
    build(PBI / 'sample_export', tmp_path)
    for generated in tmp_path.rglob('*'):
        if generated.is_file():
            committed = PBI / generated.relative_to(tmp_path)
            assert generated.read_bytes() == committed.read_bytes(), str(committed)


def test_snapshot_literals_preserve_types_quotes_and_blanks():
    from powerbi.build_project import dax_literal
    import pytest
    assert dax_literal('He said "hi"', 'string') == '"He said ""hi"""'
    assert dax_literal('False', 'bool') == 'FALSE()'
    assert dax_literal('True', 'bool') == 'TRUE()'
    assert dax_literal('', 'double') == 'BLANK()'
    assert dax_literal('1e-20', 'double') == '1e-20'
    with pytest.raises(ValueError):
        dax_literal('nan', 'double')
    with pytest.raises(ValueError):
        dax_literal('yes', 'bool')


def test_dax_variables_are_not_mistaken_for_measures():
    from powerbi.build_project import measures
    parsed = {m['name']: m['expression'] for m in measures()}
    assert 'VAR Winner' not in parsed
    assert 'VAR Winner' in parsed['Top Distribution']
    assert 'RETURN' in parsed['Top Distribution']


def test_native_query_expectations_regenerate_exactly(tmp_path):
    from powerbi.build_checks import run
    target = tmp_path / 'checks.json'
    run(target)
    assert target.read_bytes() == (PBI / 'checks.json').read_bytes()
