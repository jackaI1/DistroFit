"""Build an offline Power BI project from an existing DistroFit CSV export.

Native calculated-table partitions keep the small comparison snapshot portable.
They contain exported fit results, not replacement Python implementations of DAX.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_powerbi import TABLES

HERE = Path(__file__).resolve().parent
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def dax_literal(value, kind):
    if value == '' or value is None:
        return 'BLANK()'
    if kind == 'string':
        return '"' + str(value).replace('"', '""') + '"'
    if kind == 'bool':
        if str(value).lower() not in ('true', 'false'):
            raise ValueError(f'Invalid boolean: {value}')
        return str(value).upper() + '()'
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Nonfinite numbers must be exported as blanks')
    return str(int(number)) if kind == 'int64' else repr(number)


def measures():
    code = re.sub(r'//[^\n]*', '', (HERE / 'measures.dax').read_text())
    parts = list(re.finditer(r'^(?!VAR )([A-Z][\w ]+?) =\s*$', code, re.M))
    result = []
    for i, match in enumerate(parts):
        name = match[1]
        expression = code[match.end():parts[i+1].start() if i+1 < len(parts) else len(code)].strip()
        fmt = '0.0%' if any(w in name for w in ('Rate', 'Share', 'Weight')) else ('0.000' if name == 'Avg KS Statistic' else '0.0' if 'Delta' in name else '0')
        measure = {'name': name, 'expression': expression, 'displayFolder': 'Fit comparison'}
        if name != 'Top Distribution':
            measure['formatString'] = fmt
        result.append(measure)
    return result


def build_model(export):
    types = {'string': 'STRING', 'bool': 'BOOLEAN', 'int64': 'INTEGER', 'double': 'DOUBLE'}
    tom_types = {'string': 'string', 'bool': 'boolean', 'int64': 'int64', 'double': 'double'}
    tables = []
    for name, columns in TABLES.items():
        with (export / 'csv' / f'{name}.csv').open(encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(columns):
                raise ValueError(f'{name}: export schema differs')
            rows = list(reader)
        if not rows:
            raise ValueError(f'{name}: cannot snapshot an empty table')
        header = ', '.join(f'"{c}", {types[k]}' for c, k in columns.items())
        body = ',\n'.join('{ ' + ', '.join(dax_literal(row[c], k) for c, k in columns.items()) + ' }' for row in rows)
        tables.append({'name': name, 'columns': [
            {'name': c, 'dataType': tom_types[k], 'type': 'calculatedTableColumn',
             'sourceColumn': f'[{c}]', 'summarizeBy': 'none',
             'isHidden': c.endswith('_id')} for c, k in columns.items()],
            'partitions': [{'name': name, 'mode': 'import', 'source': {
                'type': 'calculated', 'expression': f'DATATABLE ( {header},\n{{\n{body}\n}}\n)'}}]})
    tables.append({'name': '_Measures', 'columns': [{'name': 'Value', 'dataType': 'int64',
        'type': 'calculatedTableColumn', 'sourceColumn': '[Value]', 'isHidden': True}],
        'partitions': [{'name': '_Measures', 'mode': 'import', 'source': {
            'type': 'calculated', 'expression': 'DATATABLE ( "Value", INTEGER, { { 1 } } )'}}],
        'measures': measures()})
    return {'name': 'DistroFit', 'compatibilityLevel': 1601, 'model': {
        'culture': 'en-US', 'defaultPowerBIDataSourceVersion': 'powerBI_V3',
        'tables': tables, 'relationships': [{'name': f'fit_{key}',
            'fromTable': 'fact_fit', 'fromColumn': f'{key}_id', 'fromCardinality': 'many',
            'toTable': f'dim_{key}', 'toColumn': f'{key}_id', 'toCardinality': 'one',
            'crossFilteringBehavior': 'oneDirection'} for key in ('dataset', 'distribution', 'run')]}}


def field(table, column, measure=False):
    return {('Measure' if measure else 'Column'): {
        'Expression': {'SourceRef': {'Entity': table}}, 'Property': column}}


def projection(table, column, measure=False):
    return {'field': field(table, column, measure), 'queryRef': f'{table}.{column}',
            'nativeQueryRef': column}


def build_report(out):
    root = out / 'DistroFit.Report'
    write_json(out / 'DistroFit.pbip', {'$schema': f'{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json',
        'version': '1.0', 'artifacts': [{'report': {'path': 'DistroFit.Report'}}],
        'settings': {'enableAutoRecovery': True}})
    write_json(out / 'DistroFit.SemanticModel/definition.pbism', {
        '$schema': f'{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json', 'version': '1.0', 'settings': {}})
    write_json(root / 'definition.pbir', {'$schema': f'{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json',
        'version': '4.0', 'datasetReference': {'byPath': {'path': '../DistroFit.SemanticModel'}}})
    definition = root / 'definition'
    write_json(definition / 'version.json', {'$schema': f'{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json', 'version': '2.0.0'})
    write_json(definition / 'report.json', {'$schema': f'{SCHEMA}/item/report/definition/report/2.0.0/schema.json',
        'themeCollection': {}, 'settings': {'useStylableVisualContainerHeader': True}})
    pages = [
        ('overview', 'Overview', ['Datasets Analysed', 'Top Distribution', 'KS Pass Rate', 'Fit Success Rate'],
         ['distribution_name'], ['Best Fit Count', 'Best Fit Share', 'KS Pass Rate'], 'Best Fit Share'),
        ('leaderboard', 'Information criteria', ['Fits', 'AIC Delta', 'BIC Delta'],
         ['distribution_name'], ['AIC Delta', 'BIC Delta', 'AIC Winner Share'], 'AIC Delta'),
        ('goodness', 'Goodness of fit', ['Datasets With Any KS Pass', 'Tail Flag Rate', 'Avg KS Statistic'],
         ['distribution_name'], ['KS Pass Rate', 'Tail Flag Rate', 'Avg KS Statistic', 'Successful Fits'], 'KS Pass Rate'),
        ('dataset', 'Dataset detail', ['Fits', 'Datasets Analysed', 'Akaike Weight'],
         ['distribution_name'], ['Best Fit Count', 'AIC Delta', 'BIC Delta', 'Akaike Weight', 'KS Pass Rate'], 'Akaike Weight'),
    ]
    write_json(definition / 'pages/pages.json', {'$schema': f'{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json',
        'pageOrder': [p[0] for p in pages], 'activePageName': 'overview'})
    for page_id, title, cards, groups, table_measures, bar in pages:
        folder = definition / 'pages' / page_id
        write_json(folder / 'page.json', {'$schema': f'{SCHEMA}/item/report/definition/page/2.0.0/schema.json',
            'name': page_id, 'displayName': title, 'displayOption': 'FitToPage', 'height': 900, 'width': 1440})

        def visual(name, kind, roles, x, y, width, height, caption):
            title_properties = {
                'show': {'expr': {'Literal': {'Value': 'true'}}},
                'text': {'expr': {'Literal': {'Value': "'" + caption.replace("'", "''") + "'"}}},
            }
            obj = {'$schema': f'{SCHEMA}/item/report/definition/visualContainer/2.4.0/schema.json',
                'name': f'{page_id}_{name}',
                'position': {'x': x, 'y': y, 'z': 0, 'width': width, 'height': height, 'tabOrder': y+x/10000},
                'visual': {'visualType': kind,
                    'query': {'queryState': {r: {'projections': fields} for r, fields in roles.items()}},
                    'visualContainerObjects': {'title': [{'properties': title_properties}]}}}
            write_json(folder / f'visuals/{name}/visual.json', obj)
        for i, measure in enumerate(cards):
            visual(f'card_{i}', 'card', {'Values': [projection('_Measures', measure, True)]},
                   24+i*280, 24, 264, 120, measure)
        for i, (table, col, label) in enumerate([
                ('dim_dataset', 'dataset_name', 'Choose datasets'),
                ('dim_dataset', 'source', 'Data source'),
                ('dim_distribution', 'support_type', 'Curve support'),
                ('dim_run', 'run_id', 'Export run')]):
            visual(f'filter_{i}', 'slicer', {'Values': [projection(table, col)]},
                   1160, 24+i*205, 256, 185, label)
        visual('comparison', 'tableEx', {'Values': [projection('dim_distribution', g) for g in groups] +
               [projection('_Measures', m, True) for m in table_measures]}, 24, 168, 1100, 350, title)
        if page_id == 'dataset':
            detail_path = folder / 'visuals/comparison/visual.json'
            detail = json.loads(detail_path.read_text())
            detail['visual']['query']['queryState']['Values']['projections'] = [
                projection('dim_dataset', 'dataset_name'), projection('dim_distribution', 'distribution_name'),
                *[projection('fact_fit', c) for c in ('rank_heldout_nll', 'aic', 'delta_aic', 'akaike_weight', 'shape_1', 'shape_2', 'loc', 'scale')]]
            write_json(detail_path, detail)
        visual('chart', 'clusteredBarChart', {'Category': [projection('dim_distribution', 'distribution_name')],
               'Y': [projection('_Measures', bar, True)]}, 24, 540, 1100, 330, bar + ' by curve')


def build(export, out):
    write_json(out / 'DistroFit.SemanticModel/model.bim', build_model(export))
    build_report(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, default=HERE / 'sample_export')
    parser.add_argument('--out', type=Path, default=HERE)
    args = parser.parse_args()
    build(args.export, args.out)
