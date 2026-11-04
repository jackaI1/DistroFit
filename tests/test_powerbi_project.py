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
