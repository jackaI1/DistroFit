import sqlite3
from pathlib import Path
from openpyxl import load_workbook
from process_safety import initialize, notice_report, register_review, changed_nodes


def test_tracker_exports_open_notices(tmp_path):
    db = tmp_path / 'tracker.db'
    initialize(db)
    with sqlite3.connect(db) as con:
        con.execute("INSERT INTO inspections (site, inspected, finding, status, due) VALUES (?, ?, ?, ?, ?)", ('Cafe A', '2026-01-01', 'Clean trap', 'Open', '2026-01-10'))
        con.execute("INSERT INTO inspections (site, inspected, finding, status, due) VALUES (?, ?, ?, ?, ?)", ('Cafe B', '2026-01-01', 'Done', 'Closed', '2026-01-10'))
    out = tmp_path / 'notices.xlsx'
    notice_report(db, out)
    rows = list(load_workbook(out).active.values)
    assert len(rows) == 2 and rows[1][1] == 'Cafe A'


def test_revision_flags_affected_nodes_and_keeps_review_baseline(tmp_path):
    db = tmp_path / 'tracker.db'
    initialize(db)
    pid = tmp_path / 'pid.drawio'
    pid.write_text('revision one')
    register_review(db, pid, ['Inlet', 'Trap'])
    assert changed_nodes(db, pid) == []
    pid.write_text('revision two')
    assert changed_nodes(db, pid) == ['Inlet', 'Trap']
    assert changed_nodes(db, pid) == ['Inlet', 'Trap']
