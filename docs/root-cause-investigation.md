# Worked root-cause investigation: stale BOM in a revision package

**Completed synthetic investigation RC-SYN-001, 2026-11-04, Jack Lai.** I built
this replay because ranking review findings did not tell me what to change.
A bill of materials (BOM) lists the parts associated with a drawing. Here the
requirement is that the packaged BOM revision matches the drawing revision.

Every package, reviewer label, finding and duration below is generated. The
faulty packaging policy is a simulated failure mechanism, not historical
DistroFit behavior. This is separate from the DMAIC study's real-use headline;
it establishes no cause or savings at D.L. Engineering. The result is a completed
controlled investigation **inside this model**, not a field validation.
The [blank worksheet](root-cause-worksheet.md) remains available for new work.

## Reproduce and inspect the evidence

After [installing the project](../README.md#run-it), run from the repository root:

```sh
python docs/root_cause_investigation.py --out /tmp/distrofit-root-cause
python -m pytest tests/test_root_cause.py -q
```

The output directory contains `summary.json`, `evidence.csv` (300 rows), and
`baseline_pareto.csv`, `pilot_pareto.csv`, `followup_pareto.csv`. These files are
recreated from [the deterministic replay](root_cause_investigation.py). The CSV
keeps package ID, phase, drawing/approved/cache/selected revisions, reviewer,
workload, mismatch flag, other findings and modeled minutes. Filter by `phase`
and compare baseline/pilot by `package_id`; the follow-up uses new F-prefixed IDs.

Evidence references used below:

| ID | Reproducible source and observation |
|---|---|
| E1 | `synthetic_inputs()` and baseline CSV: all 100 drawings and approved BOMs are revision B; 38 caches are A. P001 is one example; P003 has a matching B cache. |
| E2 | `cached_first()` and baseline CSV: a nonempty cached revision wins; only document presence is checked. All 38 stale caches are selected and all 38 mismatch flags are 1. The other 62 packages have no revision mismatch. |
| E3 | `run()` cache-only challenges in summary: legacy rule with clean caches gives 0/100 mismatches; replacing only caches with A gives 100/100; the new gate with the same all-stale inputs gives 0/100. Restoring the original inputs restores 38/100 under the legacy rule. |
| E4 | Paired pilot CSV: same package IDs, sources, caches, other findings and base durations as baseline. Only the selector changes; mismatch count falls from 38 to 0. |
| E5 | Follow-up CSV: 100 new package IDs, 19 stale caches, 0 revision mismatches, 62 other findings. Pilot limits remain fixed when checking follow-up times. |
| E6 | `tests/test_root_cause.py`: missing approved revision, incompatible approved revision, blank/whitespace and non-string identifiers block release; valid approved sources work with stale, fresh or absent caches. |

## Define and measure

Scope: one drawing and one approved BOM per synthetic package; no file-content
parsing, authentication or asynchronous updates. Select the most frequent finding
from 100 findings across 100 packages: **revision letter mismatch, 38 findings**.
One package can have several different findings, so 100 findings does not mean
100 defective packages. Each package has at most one finding per category.

The baseline Pareto, calculated by `spc.pareto_table`, is 38 revision mismatches,
27 title-block/BOM mismatches, 14 missing clouds, 9 unchanged tolerances, 7 stale
references and 5 other findings. The first three total 79%; the fourth crosses
80%. Frequency selects an investigation, not a proven cause or share of time.

Predefined pilot acceptance: 0 revision mismatches in the paired 100 packages,
retain all 62 unrelated findings, and reject invalid approved-source metadata.
Follow-up acceptance: 0 revision mismatches in another 100-package challenge,
with no review-time signal against the frozen pilot limits. These are local
acceptance checks, not statistical proof that the population defect rate is zero.

## Fishbone candidates and disposition

Observable effect at the arrowhead: **packaged BOM revision differs from drawing**.
The branches below organize competing explanations rather than assuming blame.

| Branch / candidate | Hypothesis and predicted evidence | Actual test / evidence | Disposition |
|---|---|---|---|
| People P1 | A particular reviewer causes the mismatch; switching reviewers should change selection. | E1/E2: R1 and R2 each have 19 mismatches in 50 packages. Selector has no reviewer input; E3 fixes the effect without changing reviewer labels. | Rejected as the driver in this model; says nothing about real training. |
| Methods M1 | Package acceptance checks presence but omits revision equality, allowing stale cache to pass. | E2: both documents are nonempty so A is accepted beside B; E4/E6: an equality gate prevents that release and rejects invalid approved sources. | Supported, actionable system cause. |
| Tools T1 | The finding detector reports false revision mismatches. | E1/E2: compare selected A directly with drawing B for each of the 38 flags. Matching B/B pairs have zero flags; E3 clean-cache replay has zero. | Rejected for these generated exact identifiers. |
| Inputs I1 | The approved source BOM is already stale. | E1: approved B equals drawing B in all 100 cases; only cache A differs. E6 separately confirms that a stale approved source is blocked. | Rejected as the source in this batch. Stale cache is the triggering input, supported by E3. |
| Measurement Q1 | Duplicate findings inflate the leading category. | E2: 100 unique P IDs; 38 distinct packages with unequal selected/drawing revisions; flags are independently calculated after assembly. | Rejected; 38 is not duplicate counting. |
| Environment W1 | High workload is needed for mismatches. | E1/E2: high and low labels each have 19 mismatches in 50 packages. E3 changes only cache metadata; workload remains fixed. | Rejected as necessary in this model; real workload effects remain untested. |

## Evidence-backed why chain

Candidate M1. Starting effect: 38 of 100 packages contain a BOM revision different
from their drawing. Investigator/date: Jack Lai, 2026-11-04, synthetic replay.

| Step | Why did the preceding effect occur? | Answer | Evidence / status |
|---|---|---|---|
| 1 | Why did the package contain mismatched revisions? | It paired drawing B with cached BOM A in 38 cases. | E1/E2; supported by emitted revisions, not a guessed cause. |
| 2 | Why was A selected when approved B was available? | The simulated assembler preferred any nonempty cache over the approved source. | E2 `cached_first`; E3 cleaning only the cache removes all mismatches. Supported. |
| 3 | Why did the stale selection proceed? | The acceptance predicate asked only whether drawing and selected BOM were present. Both A and B satisfy that predicate. | E2; mismatched nonempty inputs return successfully. Supported. |
| 4 | Why did presence allow an invalid package? | The predicate did not compare selected BOM revision with drawing revision, so it could not distinguish a stale package from a consistent one. | E2 versus E6; missing equality check is directly observable in the simulated contract. Supported. |
| 5 | Why can this recur whenever an old cache exists? | Cache availability authorizes selection without an approved-source revision invariant. The process needs to authorize against the approved source, not cache existence. | E3 all-stale challenge reproduces 100 failures, while E4's approved-source gate removes the effect on identical inputs. Supported within the model. |

**Supported cause:** the package acceptance rule permits cached BOM metadata
without requiring an approved BOM revision equal to the drawing revision. The
stale cache is the trigger; deleting it once would leave the faulty rule intact.
The chain stops at the executable acceptance rule. There is no evidence here
about who designed a real release process or why an organization chose it.

Rejected alternatives are P1, T1, I1 (approved-source version), Q1 and W1 as
drivers of this model's effect. Open alternatives outside scope include wrong
revision labels on actual files, stale approved repositories and concurrent
source changes. The gate does not authenticate files or address those mechanisms.

## Countermeasure, paired pilot and follow-up

Owner: Jack Lai. Implemented/tested: 2026-11-04. Countermeasure:
[`select_bom_revision`](../revision_package.py) selects the approved source only
after checking exact, nonempty revision identifiers against the drawing. Missing
or incompatible approved metadata raises an error and blocks release. Cache
contents cannot authorize release. It is a reusable metadata check, not a CAD
parser or a full document packaging service.

The controlled pilot holds every package attribute fixed and changes only that
rule (E4). The review auditor independently compares the emitted revision to the
drawing, so a successful function call alone cannot count as a good result.

| Measure | Baseline, old rule | Paired pilot, gate | New follow-up batch, gate |
|---|---|---|---|
| Packages reviewed | 100 | 100 (same inputs) | 100 (new IDs / different cache pattern) |
| Stale caches presented | 38 | 38 | 19 |
| Measured revision mismatches in replay | 38 | 0 | 0 |
| Revision mismatches per 100 packages | 38 | 0 | 0 |
| Other findings retained | 62 | 62 | 62 |
| Total findings | 100 | 62 | 62 |
| Modeled mean review time | 35.7 min | 30.0 min | 30.0 min |

The selected defect rate drops **38 percentage points** in the paired replay.
After the countermeasure, title-block/BOM mismatch leads the Pareto at 27/62
findings (43.55%); its absolute count has not improved. Keeping those 62 findings
is the quality guardrail against simply hiding errors.

The time model is deliberately transparent: alternating 29/31 base minutes plus
15 minutes of rework per revision mismatch. Therefore 38 × 15 = **570 modeled
minutes avoided per 100 packages**, a 5.7-minute mean reduction. This is calculated
from the replay, not measured labor savings or the DMAIC study's 75% headline.

Decision: retain the gate for this simulated workflow. E3's cache interventions
and reversal support causality within the program, more strongly than a time
correlation. E5 is a new synthetic challenge, not independent field validation;
its other findings are held at the same counts intentionally. E6 supplies the
invalid-source guardrail rather than assuming every approved source is valid.

## Control plan and next investigation

The replay uses `spc.imr_chart` with the 100 pilot durations as a fixed baseline:
center 30.00 min, lower limit 24.68, upper limit 35.32. No follow-up points signal
under the existing rules. Alternating generated times make this an easy control
example, not evidence of real process stability or a capability claim.

For a real pilot I would save package revisions and observed review timestamps,
keep the same category definitions and review denominator, and record concurrent
changes. I would investigate any revision mismatch immediately, block release on
invalid metadata, and investigate any control-chart signal before changing limits.
Owner for recurrence: package maintainer. Review point: after each next 100
packages; preserve the original pilot limits until a verified process change.
Next opportunity from the new Pareto is title-block/BOM mismatch, with its own
worksheet and evidence rather than extending this cause to every finding.
