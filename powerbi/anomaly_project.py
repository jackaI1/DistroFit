"""Portable event/metric snapshot, with native Power BI table and slicer visuals."""
import pandas as pd

from powerbi.build_project import SCHEMA, dax_literal, projection, write_json


def build_anomaly_project(result, out):
    tables = []
    for name, frame in [('events', result.events), ('metrics', result.metrics)]:
        kinds = {column: ('bool' if pd.api.types.is_bool_dtype(frame[column]) else
                          'int64' if pd.api.types.is_integer_dtype(frame[column]) else
                          'double' if pd.api.types.is_float_dtype(frame[column]) else 'string')
                 for column in frame.columns}
        if name == 'metrics':
            # Missing ground truth must not change the report's numeric schema.
            kinds.update({c: 'int64' for c in ('evaluated', 'flagged', 'tp', 'fp', 'tn', 'fn')})
            kinds.update(precision='double', recall='double')
        dax_types = dict(string='STRING', bool='BOOLEAN', int64='INTEGER', double='DOUBLE')
        model_types = dict(string='string', bool='boolean', int64='int64', double='double')
        header = ', '.join(f'"{column}", {dax_types[kind]}' for column, kind in kinds.items())
        rows = []
        for record in frame.to_dict(orient='records'):
            rows.append('{ ' + ', '.join(dax_literal(None if pd.isna(value) else str(value), kinds[column])
                                         for column, value in record.items()) + ' }')
        tables.append({'name': name, 'columns': [
            {'name': column, 'dataType': model_types[kind], 'type': 'calculatedTableColumn',
             'sourceColumn': f'[{column}]', 'summarizeBy': 'none'} for column, kind in kinds.items()],
            'partitions': [{'name': name, 'mode': 'import', 'source': {'type': 'calculated',
                           'expression': f'DATATABLE ( {header}, {{\n' + ',\n'.join(rows) + '\n} )'}}]})
    write_json(out / 'DistroFit.SemanticModel/model.bim', {
        'name': 'DistroFit production anomalies', 'compatibilityLevel': 1601,
        'model': {'culture': 'en-US', 'defaultPowerBIDataSourceVersion': 'powerBI_V3', 'tables': tables}})
    write_json(out / 'DistroFit.SemanticModel/definition.pbism', {
        '$schema': f'{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json',
        'version': '1.0', 'settings': {}})
    write_json(out / 'DistroFit.pbip', {'$schema': f'{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json',
        'version': '1.0', 'artifacts': [{'report': {'path': 'DistroFit.Report'}}],
        'settings': {'enableAutoRecovery': True}})
    root = out / 'DistroFit.Report'
    write_json(root / 'definition.pbir', {'$schema': f'{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json',
        'version': '4.0', 'datasetReference': {'byPath': {'path': '../DistroFit.SemanticModel'}}})
    definition = root / 'definition'
    write_json(definition / 'version.json', {
        '$schema': f'{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json', 'version': '2.0.0'})
    write_json(definition / 'report.json', {
        '$schema': f'{SCHEMA}/item/report/definition/report/2.0.0/schema.json',
        'themeCollection': {}, 'settings': {'useStylableVisualContainerHeader': True}})
    write_json(definition / 'pages/pages.json', {
        '$schema': f'{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json',
        'pageOrder': ['anomalies'], 'activePageName': 'anomalies'})
    page = definition / 'pages/anomalies'
    write_json(page / 'page.json', {'$schema': f'{SCHEMA}/item/report/definition/page/2.0.0/schema.json',
        'name': 'anomalies', 'displayName': 'Production anomalies', 'displayOption': 'FitToPage',
        'height': 900, 'width': 1440})
    visuals = [
        ('events', 'tableEx', 'events', ['event_id', 'timestamp', 'event_type', 'duration_seconds',
          'evaluated', 'fold', 'iforest_flag', 'robust_flag', 'iforest_score', 'robust_score'],
         24, 200, 1100, 440, 'Event flags: blank means reference only'),
        ('metrics', 'tableEx', 'metrics', ['event_type', 'method', 'evaluated', 'flagged', 'tp', 'fp',
          'tn', 'fn', 'precision', 'recall'], 24, 24, 1100, 160, 'Held-out results: accuracy needs known fault labels'),
        ('kind', 'slicer', 'events', ['event_type'], 1150, 24, 265, 150, 'Choose event type'),
        ('forest', 'slicer', 'events', ['iforest_flag'], 1150, 200, 265, 150, 'Forest: True selects flagged events'),
        ('robust', 'slicer', 'events', ['robust_flag'], 1150, 370, 265, 150, 'Robust: True selects flagged events'),
        ('evaluated', 'slicer', 'events', ['evaluated'], 1150, 540, 265, 150, 'Evaluated: False selects warm-up'),
    ]
    for name, kind, table, columns, x, y, width, height, title in visuals:
        write_json(page / f'visuals/{name}/visual.json', {
            '$schema': f'{SCHEMA}/item/report/definition/visualContainer/2.4.0/schema.json',
            'name': f'anomalies_{name}',
            'position': dict(x=x, y=y, z=0, width=width, height=height, tabOrder=y + x / 10000),
            'visual': {'visualType': kind, 'query': {'queryState': {'Values': {
                'projections': [projection(table, column) for column in columns]}}},
                'visualContainerObjects': {'title': [{'properties': {
                    'show': {'expr': {'Literal': {'Value': 'true'}}},
                    'text': {'expr': {'Literal': {'Value': "'" + title + "'"}}}}}]}}})
    checks = []
    counts = {'Events': len(result.events), 'Evaluated': int(result.events.evaluated.sum()),
              'Forest flags': int(result.events.iforest_flag.sum()),
              'Robust flags': int(result.events.robust_flag.sum())}
    checks.append({'name': 'duration-event-counts', 'query':
        'EVALUATE ROW ( "Events", COUNTROWS(events), '
        '"Evaluated", COALESCE(COUNTROWS(FILTER(events, events[evaluated] = TRUE())), 0), '
        '"Forest flags", COALESCE(COUNTROWS(FILTER(events, events[iforest_flag] = TRUE())), 0), '
        '"Robust flags", COALESCE(COUNTROWS(FILTER(events, events[robust_flag] = TRUE())), 0) )',
        'expected': [{f'[{key}]': value for key, value in counts.items()}]})
    # Exercise the zero-row path in the native engine even when the example has
    # flags. DAX COUNTROWS returns BLANK rather than 0 for an empty result.
    checks.append({'name': 'empty-context-has-zero-flags', 'query':
        'EVALUATE CALCULATETABLE ( ROW ( '
        '"Forest flags", COALESCE(COUNTROWS(FILTER(events, events[iforest_flag] = TRUE())), 0), '
        '"Robust flags", COALESCE(COUNTROWS(FILTER(events, events[robust_flag] = TRUE())), 0) ), '
        'FILTER(events, FALSE()) )',
        'expected': [{'[Forest flags]': 0, '[Robust flags]': 0}]})
    for row in result.metrics.astype(object).where(pd.notna(result.metrics), None).to_dict(orient='records'):
        columns = [c for c in row if c not in ('event_type', 'method')]
        expressions = ', '.join(f'"{c}", MAX(metrics[{c}])' for c in columns)
        checks.append({'name': f'{row["event_type"]}-{row["method"]}', 'query':
            f'EVALUATE CALCULATETABLE ( ROW ( {expressions} ), '
            f'metrics[event_type] = "{row["event_type"]}", metrics[method] = "{row["method"]}" )',
            'expected': [{f'[{c}]': row[c] for c in columns}]})
    write_json(out / 'checks.json', checks)
