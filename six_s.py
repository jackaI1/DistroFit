"""Versioned 6S checklist, immutable audit snapshots and area-specific analysis.

The 0-4 rubric is a project convention, not a safety certification. See docs/6s.md.
"""
import copy
from datetime import date
import json

import pandas as pd

from spc import pareto_table

CHECKLIST_VERSION = 1
PILLARS = ('Sort', 'Set in order', 'Shine', 'Standardize', 'Sustain', 'Safety')
CHECKLIST = (
    ('sort-1', 'Sort', 'Only the tools and samples needed for this batch are on the bench.'),
    ('sort-2', 'Sort', 'Obsolete files and rejected samples are identified and separated.'),
    ('order-1', 'Set in order', 'Tools and reference samples have labelled storage locations.'),
    ('order-2', 'Set in order', 'Incoming, accepted and held samples have distinct labelled locations.'),
    ('shine-1', 'Shine', 'The bench and measuring surfaces are clean before measurements.'),
    ('shine-2', 'Shine', 'Cleaning checks reveal and record damage, leaks or wear.'),
    ('standard-1', 'Standardize', 'The current measurement procedure and acceptance limits are available.'),
    ('standard-2', 'Standardize', 'Instrument identity, units and calibration status are recorded.'),
    ('sustain-1', 'Sustain', 'The scheduled area checks have a dated record.'),
    ('sustain-2', 'Sustain', 'Previous corrective actions have been checked against the standard.'),
    ('safety-1', 'Safety', 'Access routes and emergency equipment are clear and accessible.'),
    ('safety-2', 'Safety', 'Required guards, protective equipment and handling instructions are available.'),
)
ITEMS = {item: (pillar, prompt) for item, pillar, prompt in CHECKLIST}
MAX_HISTORY_BYTES = 2_000_000
PARETO_COLUMNS = ['Category', 'Count', 'Percent', 'Cumulative %', 'Vital few']
FINDING_COLUMNS = ['audit_id', 'area', 'date', 'item_id', 'pillar', 'question', 'score',
                   'evidence', 'action', 'owner', 'due']


def _text(value, name, *, required=True):
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > 2000:
        raise ValueError(f'{name} must be text, at most 2000 characters' + (' and not blank.' if required else '.'))
    return value.strip()


def _date(value, name):
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f'{name} must be a real date in YYYY-MM-DD format.') from None
    if parsed.isoformat() != value:
        raise ValueError(f'{name} must use YYYY-MM-DD format.')
    return parsed


def validate_audit(audit):
    """Validate and copy a full checklist; findings require a dated action owner."""
    fields = {'audit_id', 'area', 'date', 'auditor', 'checklist_version', 'responses'}
    if not isinstance(audit, dict) or set(audit) != fields:
        raise ValueError(f'An audit needs exactly: {", ".join(sorted(fields))}.')
    if type(audit['checklist_version']) is not int or audit['checklist_version'] != CHECKLIST_VERSION:
        raise ValueError('Unsupported checklist_version; expected 1.')
    result = copy.deepcopy(audit)
    for field in ('audit_id', 'area', 'auditor'):
        result[field] = _text(audit[field], field)
    audited = _date(audit['date'], 'Audit date')
    rows = audit['responses']
    if not isinstance(rows, list) or len(rows) != len(CHECKLIST):
        raise ValueError('Record every checklist item exactly once (use null with a reason for N/A).')
    seen = set()
    applicable = 0
    for row in result['responses']:
        if not isinstance(row, dict) or set(row) != {'item_id', 'score', 'evidence', 'action', 'owner', 'due'}:
            raise ValueError('Each response needs item_id, score, evidence, action, owner and due.')
        item = row['item_id']
        if not isinstance(item, str) or item not in ITEMS or item in seen:
            raise ValueError('Checklist item IDs must be known and unique.')
        seen.add(item)
        score = row['score']
        if score is not None and (type(score) is not int or not 0 <= score <= 4):
            raise ValueError('Each score must be an integer from 0 to 4, or null for N/A.')
        applicable += score is not None
        row['evidence'] = _text(row['evidence'], 'Evidence or N/A reason')
        finding = score is not None and score < 4
        for field in ('action', 'owner', 'due'):
            row[field] = _text(row[field], field, required=finding)
        if row['due'] and _date(row['due'], 'Action due date') < audited:
            raise ValueError('Action due date cannot precede the audit date.')
    if not applicable:
        raise ValueError('At least one checklist item must be applicable.')
    # Canonical question order keeps exports stable after reordered imports.
    result['responses'].sort(key=lambda row: list(ITEMS).index(row['item_id']))
    return result


def score_audit(audit):
    """Points / (4 × applicable questions); N/A is excluded, never a pass."""
    audit = validate_audit(audit)
    pillars = {}
    findings = safety = 0
    for pillar in PILLARS:
        scores = [row['score'] for row in audit['responses']
                  if ITEMS[row['item_id']][0] == pillar and row['score'] is not None]
        earned, possible = sum(scores), len(scores) * 4
        pillars[pillar] = dict(earned=earned, possible=possible,
                               percent=100 * earned / possible if possible else None)
        count = sum(score < 4 for score in scores)
        findings += count
        if pillar == 'Safety':
            safety = count
    earned = sum(p['earned'] for p in pillars.values())
    possible = sum(p['possible'] for p in pillars.values())
    return dict(earned=earned, possible=possible, percent=100 * earned / possible,
                applicable=possible // 4, excluded=len(CHECKLIST) - possible // 4,
                findings=findings, safety_findings=safety, pillars=pillars)


def validate_history(history):
    if (not isinstance(history, dict) or set(history) != {'schema_version', 'audits'}
            or type(history['schema_version']) is not int or history['schema_version'] != 1
            or not isinstance(history['audits'], list) or len(history['audits']) > 1000):
        raise ValueError('History needs schema_version 1 and an audits list (at most 1000 audits).')
    audits = [validate_audit(a) for a in history['audits']]
    if len({a['audit_id'] for a in audits}) != len(audits):
        raise ValueError('Audit IDs must be unique in history.')
    result = {'schema_version': 1, 'audits': audits}
    # Match the app and CLI backup format so every accepted history can be restored.
    if len(json.dumps(result, indent=2, allow_nan=False).encode('utf-8')) > MAX_HISTORY_BYTES:
        raise ValueError('History backup exceeds 2 MB. Archive this history and start a new one.')
    return result


def load_history(raw):
    """Import a portable JSON backup; never silently discard malformed records."""
    if (not isinstance(raw, (str, bytes))
            or len(raw.encode('utf-8') if isinstance(raw, str) else raw) > MAX_HISTORY_BYTES):
        raise ValueError('History input must be JSON up to 2 MB.')
    try:
        return validate_history(json.loads(raw))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError('History is not valid JSON.') from None


def append_audit(history, audit):
    """Return a new history, leaving both caller inputs untouched."""
    history = validate_history(history)
    return validate_history(history | {'audits': [*history['audits'], audit]})


def audit_trend(history, area):
    rows = []
    for audit in validate_history(history)['audits']:
        if audit['area'] == area:
            score = score_audit(audit)
            rows.append({key: audit[key] for key in ('audit_id', 'date', 'area')} |
                        {key: score[key] for key in ('percent', 'applicable', 'excluded', 'safety_findings')} |
                        {pillar: score['pillars'][pillar]['percent'] for pillar in PILLARS})
    return pd.DataFrame(rows, columns=['audit_id', 'date', 'area', 'percent', 'applicable', 'excluded',
                                       'safety_findings', *PILLARS]).sort_values('date', kind='stable').reset_index(drop=True)


def findings_table(history, area):
    rows = []
    for audit in validate_history(history)['audits']:
        if audit['area'] != area:
            continue
        for response in audit['responses']:
            if response['score'] is not None and response['score'] < 4:
                pillar, question = ITEMS[response['item_id']]
                rows.append({key: audit[key] for key in ('audit_id', 'area', 'date')} |
                            response | {'pillar': pillar, 'question': question})
    return pd.DataFrame(rows, columns=FINDING_COLUMNS)


def findings_pareto(history, area):
    """Count unmet checklist observations, including repeats at later audits."""
    findings = findings_table(history, area)
    if findings.empty:
        return pd.DataFrame(columns=PARETO_COLUMNS)
    counts = {pillar: int((findings.pillar == pillar).sum()) for pillar in PILLARS}
    return pareto_table({pillar: count for pillar, count in counts.items() if count})
