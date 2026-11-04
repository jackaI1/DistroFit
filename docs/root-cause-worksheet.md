# Root-cause worksheet: fishbone and 5 whys

This is the reusable blank worksheet. For a populated evidence log, fishbone,
why chain and measured replay result, see the
[completed synthetic investigation](root-cause-investigation.md).

Copy this worksheet for one review-process problem. Start with the Pareto table
from [`spc.pareto_table`](../spc.py) to choose a frequent finding, then investigate
why it occurs. Frequency ranks opportunities; it does not establish causes or
time saved. Pair finding counts with review timestamps when cycle time is the
outcome. The [DMAIC case study](case-study-dmaic.md) supplies illustrative inputs.

## 1. Define the investigation

| Field | Fill in |
|---|---|
| Investigation ID / date / owner | |
| Process and scope (package types, period, exclusions) | |
| Observable effect and requirement | |
| Baseline measure, units, denominator and data source | |
| Pareto category selected and selection reason | |
| Target and review date | |

Keep the effect specific and observable, such as “revision letters differ
between the drawing and BOM.” Record observations separately from explanations.
Use anonymized package IDs rather than private drawings or client details.

## 2. Fishbone: collect possible causes

Write the effect at the arrowhead. Add candidate causes along each branch;
use the table below to record each candidate and the evidence needed to test it.
The six categories are prompts; rename or omit them to fit the process.

```text
        People              Methods             Tools
           \                   \                  \
------------\-------------------\------------------\----> [Observable effect]
            /                   /                  /
           /                   /                  /
        Inputs            Measurement        Environment
```

| Branch | Prompt for a drawing-review process | Candidate ID and hypothesis | Evidence or test needed |
|---|---|---|---|
| People | Is ownership or training clear? | | |
| Methods | Do the release checklist and handoff specify revision checks? | | |
| Tools | Are comparison rules, versions or configuration appropriate? | | |
| Inputs | Do the drawing, BOM and references belong to the same revision? | | |
| Measurement | Are findings and active review time recorded consistently? | | |
| Environment | Do interruptions, workload or access delays affect review? | | |

For every candidate, maintain an evidence record:

| Candidate ID | Observation / source / date | Test and expected result if true | Actual result | Status (untested / supported / rejected) |
|---|---|---|---|---|
| | | | | |

## 3. Five whys: trace one candidate

Candidate ID: ______. Starting effect: ______. Investigator/date: ______.

Each answer must explain the preceding row and cite evidence. Branch into a
separate chain when several explanations fit. Five is a prompt, not a required
depth: stop earlier if a supported, actionable cause is reached, or continue if
the explanation remains incomplete. Mark unknown answers as hypotheses and
collect evidence before calling them root causes. Avoid stopping at “human error.”

| Step | Why did the preceding effect occur? | Answer / hypothesis | Evidence reference or next test | Status |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

Candidate root cause: ______. Alternative explanations still open: ______.
Evidence that changing this cause changes the effect: ______.

## 4. Test a countermeasure and sustain it

| Supported cause ID | Countermeasure / prediction | Owner / due date | Pilot scope and comparable baseline | Outcome / decision |
|---|---|---|---|---|
| | | | | |

- Define success before the pilot: finding rate per package, review time and
  a quality guardrail such as missed findings or rework. Keep definitions and
  sampling comparable; record concurrent changes that could explain the result.
- Re-run the Pareto analysis on the same category definitions and denominator.
  Use `spc.pareto_chart(table)` for count bars and cumulative percentages.
- Monitor time-ordered review durations with
  `spc.imr_chart(values, baseline=n)`, where `n` identifies the initial stable
  reference period. Investigate signals; change limits only after a verified
  process change. Apply the case study's distribution and capability caveats.
- Record the decision, process-document update, responsible owner, next review
  date and response to recurrence. A lower count alone does not prove causality.

## Illustrative starting point

In the case study's synthetic data, revision-letter mismatches occur 38 times
out of 100 total findings. The first three categories account for 79% of findings;
this does not mean 79% of review time or 79 affected packages.

A possible **unverified** Inputs hypothesis is that a package contains a BOM from
an older revision. A first why could ask why those versions were packaged
together. Check anonymized revision metadata and the handoff record before
answering; if the versions match, reject this candidate and investigate another.
An automated revision-consistency check is a candidate countermeasure to pilot
only after the cause is supported. This starting point is unverified; the
[separate worked investigation](root-cause-investigation.md) tests a synthetic
cache-selection mechanism and countermeasure. Neither example adds facts about
D.L. Engineering.
