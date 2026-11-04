# Completed root-cause investigation implementation plan

**Goal:** Replace the untested starting hypothesis with a separate, completed synthetic investigation, preserving the blank worksheet.

**Design:** Replay a synthetic package assembly process that prefers an existing cached bill of materials (BOM). Compare that policy with a reusable revision-consistency gate on identical inputs. Export package-level evidence, Pareto counts and follow-up results; document six fishbone candidates and a supported why chain. This is a simulation of a failure mechanism, not a claim about an actual DistroFit defect or workplace records.

**Approach:** A prose-only worked example would be harder to audit. A full drawing parser would add unrelated scope. Use revision metadata and deterministic fixtures so every causal claim can be checked by replaying the intervention.

**Constraints:** No private records, new dependencies, app changes, or claims of real production savings. Keep existing SPC and Pareto behavior and the reusable blank worksheet. Execute inline, as authorized in the task.

- [x] Add failing tests for stale-cache prevention, invalid approved sources, independently counted pre/post findings, follow-up and exported evidence.
- [x] Implement `revision_package.py` and `docs/root_cause_investigation.py`; use the existing Pareto and I-MR calculations.
- [x] Complete `docs/root-cause-investigation.md` with evidence references, six candidates, five whys, rejected alternatives, pilot measurements, limitations and a control plan.
- [x] Link the completed case and blank worksheet from the README and DMAIC study. Run the full suite and command-line replay.
Release gate: push, create a plain-language PR, watch checks, merge, confirm main CI, and run the required independent verifier. The PR records these remote results.

**Review focus:** Missing or incompatible approved revisions must fail closed; cache contents must not override approved metadata; all 62 unrelated baseline findings must survive; denominators must remain 100 packages; synthetic review-time savings must stay separate from real observations.

Validation: 10 new investigation tests and 224 full-suite tests passed. The independent read-only code review found no issues and passed 46 investigation/SPC tests.
