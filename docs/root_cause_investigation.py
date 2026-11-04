"""Replay a completed SYNTHETIC investigation; no workplace data or measured savings.

Run: python docs/root_cause_investigation.py --out /tmp/distrofit-root-cause
The cached-first policy is a deliberately faulty simulation, not past DistroFit
behavior. Review minutes are a fixed cost model, not stopwatch observations.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from revision_package import select_bom_revision  # noqa: E402
import spc  # noqa: E402

REVISION = "Revision letter mismatch"
OTHER = {"Title block / BOM mismatch": 27, "Missing revision cloud": 14,
         "Tolerance not updated": 9, "Stale referenced drawing": 7, "Other": 5}


def synthetic_inputs(followup=False):
    """100 explicit metadata records; finding categories can overlap per package.

    Every fifth package has stale cache in the first 95 (19 in follow-up).
    Baseline also includes its next neighbor (38). Reviewer and workload are
    balanced descriptors; they have no effect on the simulated assembly rule.
    """
    records = []
    for i in range(100):
        stale = i < 95 and (i % 5 == 0 or (not followup and i % 5 == 1))
        records.append({"package_id": f"{'F' if followup else 'P'}{i + 1:03}",
                        "drawing_revision": "B", "approved_bom_revision": "B",
                        "cached_bom_revision": "A" if stale else "B",
                        "reviewer": "R1" if i % 2 == 0 else "R2",
                        "load": "high" if i % 4 < 2 else "low",
                        "base_minutes": 29 if i % 2 == 0 else 31,
                        "other_categories": [name for name, count in OTHER.items() if i < count]})
    return records


def cached_first(drawing_revision, approved_bom_revision, cached_bom_revision):
    """Synthetic legacy contract: a nonempty BOM exists, so accept the package."""
    bom = cached_bom_revision or approved_bom_revision
    if not drawing_revision or not bom:
        raise ValueError("Missing document")
    return bom


def replay(records, phase, selector):
    rows = []
    for record in records:
        selected = selector(record["drawing_revision"], record["approved_bom_revision"],
                            record["cached_bom_revision"])
        # Independent review checks the result against drawing metadata, rather
        # than trusting the selector's success status.
        mismatch = selected != record["drawing_revision"]
        rows.append({"phase": phase, **{k: v for k, v in record.items() if k != "other_categories"},
                     "selected_bom_revision": selected, "mismatch": int(mismatch),
                     "other_categories": ";".join(record["other_categories"]),
                     "other_findings": len(record["other_categories"]),
                     "review_minutes": record["base_minutes"] + 15 * mismatch})
    return rows


def summarize(rows):
    mismatches = sum(r["mismatch"] for r in rows)
    other = sum(r["other_findings"] for r in rows)
    return {"packages": len(rows), "revision_mismatches": mismatches,
            "revision_mismatches_per_100_packages": 100 * mismatches / len(rows),
            "stale_cache_packages": sum(r["cached_bom_revision"] != r["drawing_revision"] for r in rows),
            "other_findings": other, "total_findings": mismatches + other,
            "mean_review_minutes": sum(r["review_minutes"] for r in rows) / len(rows)}


def pareto(rows):
    counts = {REVISION: sum(r["mismatch"] for r in rows)}
    counts.update({name: sum(name in r["other_categories"].split(";") for r in rows) for name in OTHER})
    return spc.pareto_table(counts)


def run():
    inputs = synthetic_inputs()
    before = replay(inputs, "baseline", cached_first)
    pilot = replay(inputs, "pilot", select_bom_revision)
    followup = replay(synthetic_inputs(followup=True), "followup", select_bom_revision)
    # Hold all metadata constant and change only the cache, then restore it.
    clean_cache = [{**r, "cached_bom_revision": r["drawing_revision"]} for r in inputs]
    all_stale = [{**r, "cached_bom_revision": "A"} for r in inputs]
    challenges = {
        "legacy_clean_cache_mismatches": summarize(replay(clean_cache, "challenge", cached_first))["revision_mismatches"],
        "legacy_all_stale_mismatches": summarize(replay(all_stale, "challenge", cached_first))["revision_mismatches"],
        "gate_all_stale_mismatches": summarize(replay(all_stale, "challenge", select_bom_revision))["revision_mismatches"],
    }
    control = spc.imr_chart([r["review_minutes"] for r in pilot + followup], baseline=100)["individuals"]
    out = {"synthetic": True, "baseline": summarize(before), "pilot": summarize(pilot),
           "followup": summarize(followup), "challenges": challenges,
           "paired_rework_minutes_avoided": sum(a["review_minutes"] - b["review_minutes"]
                                               for a, b in zip(before, pilot)),
           "control": {"baseline_packages": 100, "center": control["center"],
                       "lcl": control["lcl"], "ucl": control["ucl"],
                       "followup_flagged_packages": [i - 99 for i in control["flagged"] if i >= 100]}}
    return out, before + pilot + followup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write summary.json, evidence.csv and phase Pareto tables")
    args = parser.parse_args()
    out, rows = run()
    print("SYNTHETIC investigation; modeled minutes, not measured production savings")
    print(json.dumps(out, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "summary.json").write_text(json.dumps(out, indent=2) + "\n")
        with (args.out / "evidence.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        for phase in ("baseline", "pilot", "followup"):
            pareto([r for r in rows if r["phase"] == phase]).to_csv(args.out / f"{phase}_pareto.csv", index=False)


if __name__ == "__main__":
    main()
