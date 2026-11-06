# Grease-trap source control and change review

The sample creates a local SQLite database with inspections, open notices,
hazard rows and proposed changes. `python process_safety.py sample --db
/tmp/grease-trap.db` creates a new example; `python process_safety.py notices
--db /tmp/grease-trap.db --out /tmp/notices.xlsx` exports open items, ordered by
due date. Use a SQLite client to add or close inspection records. Dates use
ISO format (YYYY-MM-DD). Spreadsheet formula-looking text is escaped.

Open `examples/process-safety/grease-trap.drawio` in draw.io to edit the simple
flow chart. The example hazard and operability review (HAZOP) applies No flow,
More and Reverse guide words to inlet, trap and outlet, records consequences,
safeguards and follow-up actions. It is illustrative, not a complete safety
assessment or an engineered piping and instrumentation diagram (P&ID).

The management-of-change (MOC) table records a proposed drawing change. A SHA-256
file fingerprint records the drawing revision reviewed for each node. Run
`python process_safety.py changes --db /tmp/grease-trap.db` after editing the
file to list nodes needing re-review. Any byte change flags all linked nodes,
including cosmetic edits; it cannot identify which equipment changed. Once the
review is actually complete, call `register_review(db, drawing, nodes)` to record
the new revision. A changed drawing is not approval to operate; a qualified
team must review real hazards, safeguards and changes. Use local synthetic data
only for the example; do not commit private site records.
