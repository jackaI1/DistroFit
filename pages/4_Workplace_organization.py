"""Measurement-bench audits and process instructions, with portable history."""
from datetime import date
import json
from uuid import uuid4

import streamlit as st

from process_flow import build_process
from six_s import (CHECKLIST, PILLARS, append_audit, audit_trend, findings_pareto,
                   findings_table, load_history, score_audit)
from six_s_report import load_example, trend_chart
from spc import pareto_chart

st.set_page_config(page_title='DistroFit: Workplace organization', layout='wide')
st.title('Workplace organization')
st.write('Check the measurement bench, keep evidence of what changed, and turn the agreed process into clear instructions.')
st.caption('6S means sort, set in order, shine, standardize, sustain and safety. The example data are generated. These checks support local review; they are not a safety certification.')
example_history, example_process = load_example()
if 'six_s_history' not in st.session_state:
    st.session_state['six_s_history'] = {'schema_version': 1, 'audits': []}

audit_tab, history_tab, process_tab = st.tabs(['Record an audit', 'History and findings', 'Process and SOP'])

with audit_tab:
    st.subheader('Record what you observed')
    st.write('Use the same posted standard each time. Score 0: absent; 1: informal or rarely followed; 2: partly followed; 3: mostly met with a remaining gap; 4: fully observed. Choose N/A only with a reason.')
    st.info('Every check needs evidence. Any score below 4 needs a corrective action, responsible role and due date. Resolve an unsafe condition through the local safety process regardless of the total score.')
    with st.form('audit_form'):
        left, right = st.columns(2)
        with left:
            area = st.text_input('Area', 'Measurement bench', key='audit_area')
            auditor = st.text_input('Reviewer or role', key='auditor')
        with right:
            audited = st.date_input('Audit date', date.today(), key='audit_date')
        responses = []
        for pillar in PILLARS:
            with st.expander(pillar):
                for item, group, prompt in CHECKLIST:
                    if group != pillar:
                        continue
                    st.write(prompt)
                    score = st.selectbox('Observed score', ['Not scored', '0', '1', '2', '3', '4', 'N/A'],
                                         key=f'score_{item}')
                    evidence = st.text_area('Evidence or N/A reason', key=f'evidence_{item}', max_chars=2000)
                    action = st.text_input('Corrective action (below 4)', key=f'action_{item}', max_chars=2000)
                    owner = st.text_input('Responsible role (below 4)', key=f'owner_{item}', max_chars=2000)
                    due = st.text_input('Due date, YYYY-MM-DD (below 4)', key=f'due_{item}', max_chars=10)
                    responses.append(dict(item_id=item, score=score, evidence=evidence, action=action, owner=owner, due=due))
        saved = st.form_submit_button('Save audit snapshot', key='save_audit')
    if saved:
        try:
            if any(row['score'] == 'Not scored' for row in responses):
                raise ValueError('Score all 12 checks or choose N/A with a reason. Open each pillar to finish the checklist.')
            for row in responses:
                row['score'] = None if row['score'] == 'N/A' else int(row['score'])
            draft = dict(area=area, date=audited.isoformat(), auditor=auditor,
                         checklist_version=1, responses=responses)
            fingerprint = json.dumps(draft, sort_keys=True)
            if fingerprint == st.session_state.get('six_s_saved_draft'):
                raise ValueError('This draft is already saved. Change the observations or date before recording another audit.')
            entry = draft | {'audit_id': str(uuid4())}
            score = score_audit(entry)
            st.session_state['six_s_history'] = append_audit(st.session_state['six_s_history'], entry)
            st.session_state['six_s_last_score'] = score
            st.session_state['six_s_saved_draft'] = fingerprint
            st.success(f'Saved audit {entry["audit_id"]}: {score["earned"]}/{score["possible"]} applicable points ({score["percent"]:.1f}%).')
        except ValueError as error:
            st.error(f'Audit was not saved: {error}')

with history_tab:
    st.subheader('Keep and restore audit history')
    st.write('History stays in this browser session. Download the JSON backup before closing or restarting the app. Restore it next time to add another dated snapshot. Downloads contain your entered evidence; keep private records private.')
    with st.expander('Restore a backup or try generated audits'):
        st.caption('Restoring replaces the current session history. Download the current backup first.')
        uploaded = st.file_uploader('Audit history JSON', type=['json'], max_upload_size=2, key='history_upload')
        pasted = st.text_area('Or paste audit history JSON', key='restore_json', max_chars=2_000_000)
        if st.button('Restore history (replace session)', key='restore_history'):
            try:
                history = load_history(uploaded.getvalue() if uploaded is not None else pasted)
                st.session_state['six_s_history'] = history
                st.session_state.pop('six_s_saved_draft', None)
                st.success(f'Restored {len(history["audits"])} audit snapshots.')
            except ValueError as error:
                st.error(f'History was not replaced: {error}')
        if st.button('Use synthetic demo (replace session)', key='load_demo'):
            st.session_state['six_s_history'] = example_history
            st.session_state.pop('six_s_saved_draft', None)
        if st.button('Start empty history (replace session)', key='empty_history'):
            st.session_state['six_s_history'] = {'schema_version': 1, 'audits': []}
            st.session_state.pop('six_s_saved_draft', None)
    history = st.session_state['six_s_history']
    st.download_button('Download audit history (JSON)', json.dumps(history, indent=2, allow_nan=False),
                       file_name='audit_history.json', mime='application/json')
    areas = sorted({entry['area'] for entry in history['audits']})
    st.session_state.pop('six_s_trend', None)
    if not areas:
        st.info('No audits yet. Record an audit or open the restore panel to try three generated audits.')
    else:
        selected = st.selectbox('Review one area', areas, key='review_area')
        trend = audit_trend(history, selected)
        st.session_state['six_s_trend'] = trend
        latest = next(a for a in history['audits'] if a['audit_id'] == trend.iloc[-1]['audit_id'])
        score = score_audit(latest)
        left, middle, right = st.columns(3)
        left.metric('Latest applicable points', f'{score["earned"]}/{score["possible"]} ({score["percent"]:.1f}%)')
        middle.metric('Latest N/A checks', score['excluded'])
        right.metric('Latest safety findings', score['safety_findings'])
        if score['safety_findings']:
            st.warning('Safety checks remain unmet in the latest audit. Review those observations even when the overall score is high.')
        st.subheader('Scores over time')
        st.caption('Compare the same area and checklist version. Check the applicable and excluded counts: changing N/A answers can change the score without improving the bench. A pillar with only N/A checks has no score.')
        figure = trend_chart(trend, selected)
        try:
            st.pyplot(figure)
        finally:
            figure.clear()
        st.dataframe(trend, hide_index=True, width='stretch')
        st.subheader('Repeated findings')
        st.write('The Pareto chart ranks unmet checklist observations by pillar. A repeated gap counts again on each audit date. Bars count findings, not lost points or safety risk; review safety separately. Historical actions are snapshots, not an open-ticket register.')
        pareto = findings_pareto(history, selected)
        figure = pareto_chart(pareto, 'Unmet checks by 6S pillar')
        try:
            st.pyplot(figure)
        finally:
            figure.clear()
        st.dataframe(pareto, hide_index=True, width='stretch')
        findings = findings_table(history, selected)
        st.dataframe(findings, hide_index=True, width='stretch')
        st.download_button('Download findings (CSV)', findings.to_csv(index=False),
                           file_name='audit_findings.csv', mime='text/csv')

with process_tab:
    st.subheader('One step list, one diagram and one SOP')
    st.write('The example follows a sample from receipt to a reviewed DistroFit analysis, with holds and rechecks. Edit the JSON step list below, then generate the flow chart and standard operating procedure (SOP), the written instructions for each step.')
    st.caption('Each task has one next step, each decision has two labelled routes, and each end has none. Every step needs a responsible role, instructions and a record. Rework loops are allowed when a route can still reach an end. See docs/6s.md for the format.')
    source = st.text_area('Documented process steps (JSON)', json.dumps(example_process, indent=2),
                          key='process_source', height=300, max_chars=200_000)
    if source != st.session_state.get('six_s_process_source'):
        st.session_state.pop('six_s_process_package', None)
    if st.button('Generate flow chart and SOP', key='generate_process'):
        st.session_state.pop('six_s_process_package', None)
        try:
            package = build_process(json.loads(source))
            st.session_state['six_s_process_package'] = package
            st.session_state['six_s_process_source'] = source
        except (ValueError, RecursionError) as error:
            st.error(f'Process was not generated: {error}')
    if 'six_s_process_package' in st.session_state:
        package = st.session_state['six_s_process_package']
        st.image(package['svg'], caption='Rendered by Graphviz from the current step list.')
        st.download_button('Download SOP page', package['sop'], file_name='sop.html', mime='text/html')
        st.download_button('Download flow chart (SVG)', package['svg'], file_name='process.svg', mime='image/svg+xml')
        st.download_button('Download Graphviz source', package['dot'], file_name='process.dot', mime='text/plain')
        st.download_button('Download process steps (JSON)', source, file_name='process.json', mime='application/json')
