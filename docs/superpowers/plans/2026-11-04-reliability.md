# Reliability Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add usable censored equipment-life analysis to DistroFit and merge a tested public demonstration.

**Architecture:** Keep statistics in `reliability.py`, file workflows in `reliability_report.py`, and UI in a separate Streamlit page. Both workflows consume the same validated report.

**Tech Stack:** Existing Python 3.12, NumPy, SciPy, pandas, Matplotlib and Streamlit.

**Spec:** `docs/superpowers/specs/2026-11-04-reliability-design.md`

## Global Constraints

- Keep existing features and tests working. No new dependencies or private data.
- One positive age and binary failure indicator per independent lifetime; no silent dropped rows.
- Public repository, PR merge only, green CI on main and independent Sol verification.

## Review Focus

All-censored input keeps the empirical result but no invented mean. Tied failures and suspensions use the same pre-event risk set. Changing time units scales life and interval endpoints. Degenerate data excludes unidentifiable fits. Invalid UI edits clear downloadable stale results.

### Task 1: Censored statistics

**Files:** `reliability.py`, `tests/test_reliability.py`.

**Interfaces:** `validate_lifetimes(table)` returns time and event arrays; `kaplan_meier(table, confidence=.95)` returns a risk/curve DataFrame; `fit_life_model(table, model, confidence=.95)` returns parameters, log likelihood, AIC, mean/B10 and intervals; `analyze_lifetimes(table, confidence=.95)` returns a JSON-safe report. `life_curves(fit, times)` returns survival and hazard.

- [ ] Write tests for NIST Weibull beta 1.7208, eta 606.5280, mean 540.737, log likelihood -75.135 and lognormal AIC 154.39; exponential exposure/failure estimate 30 hours; hand-derived tied KM survival 0.75, 0.5, 0.5, 0; scale invariance; invalid/all-censored/degenerate data; independent SciPy estimates and interval information.
- [ ] Run `.venv/bin/python -m pytest tests/test_reliability.py -q`; verify missing implementation fails.
- [ ] Implement the interfaces using log-density/log-survival likelihood, Weibull profile root, lognormal numerical optimization and observed-information log-delta intervals.
- [ ] Run core tests and full suite; commit the independently useful core.

### Task 2: Usable app and exported maintenance example

**Files:** `reliability_report.py`, `pages/2_Reliability.py`, `examples/reliability/equipment_log.csv`, `tests/test_reliability_workflows.py`.

**Interfaces:** Consumes Task 1 report. `generate_demo()` returns seeded synthetic lifetime rows. `reliability_figure(report)` returns survival/hazard/probability diagnostics. `export_report(report, out)` saves inputs, summary, curves and charts. CLI: `python reliability_report.py --sample --out <new directory>` or `python reliability_report.py log.csv --out <new directory>`.

- [ ] Write and run failing tests for deterministic demo, charts using censored empirical data, CSV CLI, strict exports, no overwrite, invalid inputs, Streamlit edits/confidence/model choice and stale-result prevention.
- [ ] Implement the example, three-panel diagnostic figure, CLI, and editable/uploadable page with download buttons and assumptions beside the results.
- [ ] Run both reliability test files and full suite; commit workflow.

### Task 3: Explain, review and ship

**Files:** `README.md`, `docs/reliability.md`, `.github/workflows/tests.yml`.

- [ ] Add plain-language first-person usage and worked maintenance interpretation, followed by technical method and source links in the guide.
- [ ] Add example execution and artifact upload to existing CI. Run full tests and sample CLI; inspect generated plot.
- [ ] Request a fresh code review of the complete branch. Fix substantive findings with regression tests. Fetch/rebase if necessary, push requested branch, create explanatory PR, watch every check and merge.
- [ ] Verify merged state and green main CI; run required independent Sol verifier, fix through further PRs if needed. Write result JSON and verify cleanup.
