"""Small local source-control and process-change register.

The sample is synthetic and the review flag is conservative: a changed drawing
flags every node linked to that drawing, not only the edited component.
"""
import argparse
import hashlib
import sqlite3
from pathlib import Path
from openpyxl import Workbook

SCHEMA = '''
CREATE TABLE IF NOT EXISTS inspections (id INTEGER PRIMARY KEY, site TEXT NOT NULL, inspected TEXT NOT NULL, finding TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Open','Closed')), due TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reviews (drawing TEXT NOT NULL, node TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(drawing,node));
CREATE TABLE IF NOT EXISTS hazards (node TEXT NOT NULL, guideword TEXT NOT NULL, deviation TEXT NOT NULL, consequence TEXT NOT NULL, safeguard TEXT NOT NULL, action TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS changes (id INTEGER PRIMARY KEY, drawing TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Proposed','Reviewed','Closed')));
'''


def initialize(db):
    with sqlite3.connect(db) as con:
        con.executescript(SCHEMA)


def notice_report(db, output):
    with sqlite3.connect(db) as con:
        rows = con.execute("SELECT id, site, inspected, finding, due FROM inspections WHERE status = 'Open' ORDER BY due, id").fetchall()
    wb = Workbook(); ws = wb.active; ws.title = 'Open notices'
    ws.append(['ID', 'Site', 'Inspected', 'Finding', 'Due'])
    for row in rows:
        # Text from a site or finding must not become a spreadsheet formula.
        ws.append(["'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v for v in row])
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 24
    wb.save(output)


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def register_review(db, drawing, nodes):
    """Record an explicit completed review of these nodes at the current file revision."""
    digest = _digest(drawing)
    with sqlite3.connect(db) as con:
        con.executemany('INSERT OR REPLACE INTO reviews VALUES (?, ?, ?)', [(str(Path(drawing).resolve()), node, digest) for node in nodes])


def changed_nodes(db, drawing):
    digest = _digest(drawing)
    with sqlite3.connect(db) as con:
        rows = con.execute('SELECT node FROM reviews WHERE drawing=? AND sha256<>? ORDER BY node', (str(Path(drawing).resolve()), digest)).fetchall()
    return [r[0] for r in rows]


def sample(db, drawing):
    initialize(db)
    with sqlite3.connect(db) as con:
        con.execute('INSERT INTO inspections (site, inspected, finding, status, due) VALUES (?, ?, ?, ?, ?)', ('Example cafe', '2026-10-01', 'Arrange trap cleaning and submit record', 'Open', '2026-11-15'))
        con.executemany('INSERT INTO hazards VALUES (?,?,?,?,?,?)', [
            ('Inlet', 'No flow', 'Blocked inlet', 'Wastewater backs up', 'Inspection and cleaning schedule', 'Check inlet during inspection'),
            ('Trap', 'More', 'More grease than expected', 'Grease escapes to sewer', 'Routine pump-out', 'Review pump-out frequency'),
            ('Outlet', 'Reverse', 'Backflow', 'Contamination and overflow', 'Outlet inspection', 'Check backflow protection')])
        con.execute('INSERT INTO changes (drawing, description, status) VALUES (?,?,?)', (str(Path(drawing).resolve()), 'Proposed outlet modification', 'Proposed'))
    register_review(db, drawing, ['Inlet', 'Trap', 'Outlet'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['sample', 'notices', 'changes'])
    parser.add_argument('--db', required=True)
    parser.add_argument('--drawing', default='examples/process-safety/grease-trap.drawio')
    parser.add_argument('--out')
    args = parser.parse_args()
    if args.command == 'sample':
        if Path(args.db).exists():
            parser.error('Use a new database for the sample.')
        sample(args.db, args.drawing)
    elif args.command == 'notices':
        if not args.out: parser.error('--out is required for notices')
        notice_report(args.db, args.out)
    else:
        print('Nodes requiring re-review: ' + (', '.join(changed_nodes(args.db, args.drawing)) or 'none'))


if __name__ == '__main__':
    main()
