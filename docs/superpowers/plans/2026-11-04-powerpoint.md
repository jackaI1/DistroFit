# PowerPoint report implementation plan

**Goal:** Export an editable, navigable analysis report from existing DistroFit results.
**Spec:** ../specs/2026-11-04-powerpoint-design.md
**Architecture:** A Python package writer consumes report_payload without refitting.
Native charts refer to embedded XLSX data. CLI and app share create_powerpoint.
**Constraints:** Preserve all existing behavior, use synthetic public data, no external
relationships or macros, no extra runtime packages, no skills-list README section.

## Task 1: Native report
- [ ] Write failing tests for chart/workbook agreement, finite winner selection,
  package relationships, master/layout reuse, notes, links and custom shows.
- [ ] Implement powerpoint_report.py: create_powerpoint(payload, title) -> bytes.
- [ ] Test missing fits, infinite/negative scores, 14 candidates and XML characters.
- [ ] Validate the native file with the Open XML SDK, fixing schema errors.

## Task 2: Use and ship
- [ ] Write failing CLI and Streamlit download tests, then implement both paths.
- [ ] Commit a synthetic example and explain editing charts/layouts/custom shows.
- [ ] Run full pytest, SDK validation and render the synthetic example for inspection.
- [ ] Obtain a fresh code review and resolve material findings.
- [ ] Push, watch CI, merge PR, watch main CI, run independent Sol verification.

## Review focus
Check nonfinite scores never become zero, negative loss axes remain honest,
all chart numbers match their workbooks, all links stay internal, and many
candidates remain usable. Empty analyses must remain informative.

## Progress
Design/plan recorded before implementation. Owner explicitly opted out of questions
and authorized implementation, push and merge. Baseline test run started.

Task 1 complete: red-to-green package tests; five fixtures and their embedded
workbooks pass Microsoft Open XML SDK validation with zero errors.
Task 2 integration complete: CLI and real Streamlit AppTest checks pass. Full
suite: 173 passed. Fresh reviewer found an overwide-title defect and title
layout overrides. Both now have failing-then-passing regression tests: titles
are measured and rejected if too wide, and title placeholders inherit geometry
and master font size. No deferred review findings. Local Quick Look thumbnail
confirms the summary renders. Full chart rendering is the remaining local check.

Final visual review: CI's LibreOffice PDFs exposed cropped score axes and a
wrapped last label in the fourteen-candidate tail chart. Added red-to-green
positive/negative/zero-axis regressions, forced score bounds to include zero,
and used 12 pt labels for dense charts. The final local LibreOffice render
shows the zero baseline and every candidate name without clipping. All 176
Python tests pass, with zero schema errors across five files. The owned viewer
process group 67087 exited and process/port checks found nothing remaining.

Rebased onto 722f316 after the Excel feature merged. Preserved Excel's cached
export, download, documentation and recalculation CI job alongside PowerPoint.
Updated the shared app assertion for all three downloads. Combined suite:
190 passed, including the real spreadsheet-engine recalculation test.

Rebased again onto e4c5a68 after saved comparisons merged before the merge call.
Preserved both README sections and the existing CLI artifact CI steps. Full
combined local suite now passes 214 tests. No feature code changed in this rebase.
