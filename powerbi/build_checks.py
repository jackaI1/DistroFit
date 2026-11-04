"""Independent expected values for native engine checks; no DAX interpreter."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_project import HERE, measures, write_json

TABLES = {n: pd.read_csv(HERE / f'sample_export/csv/{n}.csv').replace({np.nan: None})
          for n in ('fact_fit', 'dim_dataset', 'dim_distribution', 'dim_run')}
FACT = TABLES['fact_fit']
NAMES = [m['name'] for m in measures()]


def expected(filters):
    base = FACT.copy()
    for table, column, value in filters:
        if table == 'dim_distribution':
            continue
        dim = TABLES[table]
        key = {'dim_dataset': 'dataset_id', 'dim_run': 'run_id'}[table]
        base = base[base[key].isin(dim[dim[column] == value][key])]
    selected = base.copy()
    for table, column, value in filters:
        if table == 'dim_distribution':
            dim = TABLES[table]
            selected = selected[selected.distribution_id.isin(dim[dim[column] == value].distribution_id)]
    good = selected[selected.fit_status != 'failed']
    wins = selected[selected.is_best_fit == True]
    denominator = base.dataset_id.nunique()
    successful = len(good)
    aic, bic = [], []
    for (run, ds), group in selected.groupby(['run_id', 'dataset_id']):
        unfiltered = base[(base.run_id == run) & (base.dataset_id == ds)]
        for col, values in [('aic', aic), ('bic', bic)]:
            v = group[col].dropna()
            if len(v):
                values.append(v.min() - unfiltered[col].dropna().min())
    totals = wins.groupby('distribution_id').size()
    top = None
    if len(totals):
        top_ids = totals[totals == totals.max()].index
        top = TABLES['dim_distribution'].set_index('distribution_id').loc[top_ids].distribution_name.max()
    def ratio(n, d):
        return float(n / d) if n and d else None
    return dict(zip(NAMES, [
        len(selected) or None, successful or None, good.dataset_id.nunique() or None,
        ratio(successful, len(selected)), len(wins), float(len(wins)/denominator) if denominator else None,
        top, float(np.mean(aic)) if aic else None, float(np.mean(bic)) if bic else None,
        float(pd.to_numeric(selected.akaike_weight).sum()) if selected.akaike_weight.notna().any() else None,
        ratio((selected.rank_aic == 1).sum(), denominator),
        ratio((selected.ks_pass == True).sum(), successful),
        float(pd.to_numeric(selected.ks_statistic).mean()) if selected.ks_statistic.notna().any() else None,
        ratio((selected.tail_flagged == True).sum(), successful),
        selected[selected.ks_pass == True][['run_id','dataset_id']].drop_duplicates().shape[0] or None,
    ]))


def literal(value):
    return '"' + str(value).replace('"', '""') + '"'


def expression(table, column):
    return f"'{table}'[{column}]"


def run(out=HERE / 'checks.json'):
    cases = []
    contexts = [('overall', [])]
    for table, column in [('dim_distribution', 'distribution_id'), ('dim_dataset', 'dataset_id'),
                          ('dim_dataset', 'source'), ('dim_distribution', 'support_type'), ('dim_run', 'run_id')]:
        for value in TABLES[table][column].unique():
            contexts.append((f'{table}.{column}={value}', [(table, column, value)]))
    contexts += [('dataset-and-family', [('dim_dataset','dataset_id','faithful_eruptions'), ('dim_distribution','distribution_id','uniform')]),
                 ('empty-run', [('dim_run','run_id','missing')])]
    for name, filters in contexts:
        query = 'EVALUATE CALCULATETABLE ( ROW ( ' + ', '.join(f'{literal(m)}, [{m}]' for m in NAMES) + ' )'
        for table, column, value in filters:
            query += f', TREATAS ( {{ {literal(value)} }}, {expression(table, column)} )'
        query += ' )'
        cases.append({'name': name, 'query': query, 'expected': [{f'[{m}]': v for m,v in expected(filters).items()}]})
    # Independently supplied reference, not a regenerated self-comparison.
    reference = pd.read_csv(HERE / 'sample_export/reference_measures.csv')
    reference_names = {'datasets_fitted':'Datasets Analysed', 'best_fit_count':'Best Fit Count',
        'best_fit_share':'Best Fit Share', 'avg_delta_aic':'AIC Delta', 'ks_pass_rate':'KS Pass Rate', 'fit_success_rate':'Fit Success Rate'}
    query = 'EVALUATE SUMMARIZECOLUMNS ( dim_distribution[distribution_id], ' + ', '.join(f'{literal(m)}, [{m}]' for m in reference_names.values()) + ' ) ORDER BY dim_distribution[distribution_id]'
    rows = []
    for _, row in reference.sort_values('distribution_id').iterrows():
        rows.append({'dim_distribution[distribution_id]':row.distribution_id, **{f'[{m}]':float(row[c]) for c,m in reference_names.items()}})
    cases.append({'name':'supplied-reference-14-families', 'query':query, 'expected':rows})
    # Query every bound visual using the actual fields committed in PBIR.
    for path in sorted((HERE / 'DistroFit.Report/definition/pages').glob('*/visuals/*/visual.json')):
        visual = json.loads(path.read_text())
        projections = [p for role in visual['visual']['query']['queryState'].values() for p in role['projections']]
        groups, metric_names = [], []
        for p in projections:
            field = p['field']; kind = next(iter(field)); binding = field[kind]
            table = binding['Expression']['SourceRef']['Entity']; col = binding['Property']
            if kind == 'Measure': metric_names.append(col)
            else: groups.append((table,col))
        args = [expression(t,c) for t,c in groups] + [f'{literal(m)}, [{m}]' for m in metric_names]
        if not groups:
            query = 'EVALUATE ROW ( ' + ', '.join(args) + ' )'
            rows = [{f'[{m}]':expected([])[m] for m in metric_names}]
        elif not metric_names and len({t for t,c in groups}) == 1:
            table = groups[0][0]
            query = 'EVALUATE SUMMARIZE ( '+table+', '+', '.join(args)+' )'
            data = TABLES[table][[c for t,c in groups]].drop_duplicates().sort_values([c for t,c in groups])
            rows = [{expression(t,c).replace("'",''): row[c] for t,c in groups} for _,row in data.iterrows()]
        else:
            if not metric_names:
                args.append('"__rows", COUNTROWS ( fact_fit )')
            query = 'EVALUATE SUMMARIZECOLUMNS ( '+', '.join(args)+' )'
            data = FACT.copy()
            for table in ('dim_dataset','dim_distribution','dim_run'):
                key = {'dim_dataset':'dataset_id','dim_distribution':'distribution_id','dim_run':'run_id'}[table]
                data = data.merge(TABLES[table], on=key, suffixes=('', '_'+table))
            cols = [c for t,c in groups]
            data = data[cols].drop_duplicates().sort_values(cols, na_position='first')
            rows=[]
            for _,row in data.iterrows():
                filters = [(t,c,row[c]) for t,c in groups]
                values = expected(filters) if metric_names else {}
                rows.append({**{expression(t,c).replace("'",''): row[c] for t,c in groups},
                             **{f'[{m}]':values[m] for m in metric_names}})
        if groups:
            query += ' ORDER BY '+', '.join(expression(t,c) for t,c in groups)
        cases.append({'name':'visual:'+visual['name'], 'query':query, 'expected':rows})
    write_json(out, cases)
    print(f'{len(cases)} native queries prepared')


if __name__ == '__main__':
    run()
