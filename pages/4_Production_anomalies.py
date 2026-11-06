"""Screen production events with the same past-only detector used by the CLI."""
import json

import streamlit as st

from anomaly import evaluate_events, read_event_csv, sample_events, validate_events
from anomaly_report import event_chart, summary_dict

st.set_page_config(page_title='DistroFit: Production anomalies', layout='wide')
st.title('Production anomalies')
st.write('Find unusually long stops and fast or slow cycle times to investigate alongside equipment losses.')
st.caption('The starting log is generated, not factory data. Use one machine and product per report, '
           'with duration_seconds in seconds and event_type set to cycle or downtime.')
upload = st.file_uploader('Replace the example with an event CSV', type=['csv'])
st.session_state.pop('anomaly_pending_error', None)
try:
    source = read_event_csv(upload) if upload is not None else sample_events()
    if 'timestamp' in source:
        source['timestamp'] = source.timestamp.astype(str)
    edited = st.data_editor(source, key='anomaly_editor', hide_index=True, num_rows='dynamic', width='stretch')
    identity = edited.to_csv(index=False)
    if st.session_state.get('anomaly_input') != identity:
        st.session_state.pop('anomaly_result', None)
        st.session_state['anomaly_input'] = identity
    validate_events(edited)
except (ValueError, OSError, UnicodeError) as error:
    st.session_state.pop('anomaly_result', None)
    st.session_state['anomaly_pending_error'] = str(error)

st.write('Analyze events checks three later periods, always learning from earlier rows only. '
         'The first quarter is reference data and has no flags. Each event type needs at least '
         '20 reference rows. Optional is_fault labels (0 or 1) let me measure misses and false alarms.')
st.caption('Timestamps must be unique dates. Times without a timezone are treated as UTC. '
           'Each event_id must also be unique.')
if st.button('Analyze events', type='primary'):
    st.session_state.pop('anomaly_result', None)
    try:
        if st.session_state.get('anomaly_pending_error'):
            raise ValueError(st.session_state['anomaly_pending_error'])
        with st.spinner('Checking later events against earlier production...'):
            st.session_state['anomaly_result'] = evaluate_events(edited)
    except ValueError as error:
        st.error(f'Check the event log: {error}')
if st.session_state.get('anomaly_pending_error'):
    st.error(f'Check the event log: {st.session_state["anomaly_pending_error"]}')

if 'anomaly_result' in st.session_state:
    result = st.session_state['anomaly_result']
    st.subheader('Held-out comparison')
    st.write('Precision is the share of flagged events that were injected faults. Recall is the '
             'share of injected faults found. Blank accuracy means the log has no known fault labels. '
             'The counts include only the later periods.')
    st.dataframe(result.metrics, hide_index=True, width='stretch')
    st.plotly_chart(event_chart(result), width='stretch')
    flagged = result.events.iforest_flag.fillna(False) | result.events.robust_flag.fillna(False)
    st.subheader('Events flagged by either method')
    st.dataframe(result.events[flagged], hide_index=True, width='stretch')
    st.caption('IsolationForest looks for easy-to-isolate durations. The robust baseline compares '
               'distance from the typical duration using the median and median absolute deviation. '
               'Different operating modes and a changing process can cause false alarms. A flag is '
               'a reason to inspect the record, not proof of a fault. Scores are not probabilities.')
    st.download_button('Download event flags (CSV)', result.events.to_csv(index=False),
                       file_name='anomaly_events.csv', mime='text/csv')
    st.download_button('Download comparison (CSV)', result.metrics.to_csv(index=False),
                       file_name='anomaly_metrics.csv', mime='text/csv')
    st.download_button('Download fold audit (JSON)', json.dumps(summary_dict(result), indent=2, allow_nan=False),
                       file_name='anomaly_summary.json', mime='application/json')
st.write('For a saved offline chart and a Power BI report with flag filters, run '
         '`python anomaly_report.py --sample --out /tmp/distrofit-anomalies` '
         'or replace `--sample` with your event CSV path. The output folder must be new.')
