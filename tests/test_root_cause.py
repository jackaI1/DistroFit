"""Protect the causal replay and the revision check it evaluates."""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_replay():
    path = ROOT / "docs" / "root_cause_investigation.py"
    assert path.exists(), "The completed investigation needs a runnable evidence replay"
    spec = importlib.util.spec_from_file_location("root_cause_investigation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_revision_gate_uses_approved_source_even_with_stale_cache():
    from revision_package import select_bom_revision
    assert select_bom_revision("B", "B", "A") == "B"
    assert select_bom_revision("C2", "C2", None) == "C2"
    assert select_bom_revision("B", "B", "B") == "B"


@pytest.mark.parametrize("drawing,approved", [("B", "A"), ("B", None), ("", ""),
                                                   (" B", " B"), (1, 1)])
def test_revision_gate_blocks_missing_ambiguous_or_incompatible_sources(drawing, approved):
    from revision_package import select_bom_revision
    with pytest.raises(ValueError):
        select_bom_revision(drawing, approved, "B")


def test_paired_replay_removes_selected_cause_without_hiding_other_findings():
    out, rows = load_replay().run()
    assert out["synthetic"] is True
    assert out["baseline"]["packages"] == out["pilot"]["packages"] == 100
    assert out["baseline"]["revision_mismatches"] == 38
    assert out["pilot"]["revision_mismatches"] == 0
    assert out["baseline"]["total_findings"] == 100
    assert out["pilot"]["total_findings"] == 62
    assert out["paired_rework_minutes_avoided"] == 570
    assert out["baseline"]["mean_review_minutes"] == pytest.approx(35.7)
    assert out["pilot"]["mean_review_minutes"] == pytest.approx(30.0)
    assert len(rows) == 300  # same 100 packages twice, plus a new follow-up batch
    # The raw evidence must independently reproduce the headline counts.
    assert sum(r["mismatch"] for r in rows if r["phase"] == "baseline") == 38
    assert sum(r["mismatch"] for r in rows if r["phase"] == "pilot") == 0
    before = {r["package_id"]: r for r in rows if r["phase"] == "baseline"}
    for row in (r for r in rows if r["phase"] == "pilot"):
        old = before[row["package_id"]]
        assert row["other_findings"] == old["other_findings"]
        assert row["review_minutes"] <= old["review_minutes"]


def test_followup_challenges_gate_with_new_stale_cache_and_frozen_limits():
    out, rows = load_replay().run()
    assert out["followup"]["packages"] == 100
    assert out["followup"]["stale_cache_packages"] == 19
    assert out["followup"]["revision_mismatches"] == 0
    assert out["followup"]["other_findings"] == 62
    assert out["control"]["baseline_packages"] == 100
    assert out["control"]["followup_flagged_packages"] == []
    assert len([r for r in rows if r["phase"] == "followup"]) == 100


def test_cache_only_intervention_and_reversal_explain_the_selected_effect():
    replay = load_replay()
    out, _ = replay.run()
    assert out["challenges"] == {"legacy_clean_cache_mismatches": 0,
                                 "legacy_all_stale_mismatches": 100,
                                 "gate_all_stale_mismatches": 0}
    # A hand-written package, outside the generated fixture, reproduces the
    # mechanism. Reintroducing stale cache must restore the legacy defect.
    package = {"package_id": "X1", "drawing_revision": "C",
               "approved_bom_revision": "C", "cached_bom_revision": "B",
               "base_minutes": 10, "other_categories": ["Missing revision cloud"]}
    old = replay.replay([package], "baseline", replay.cached_first)[0]
    assert (old["selected_bom_revision"], old["mismatch"], old["review_minutes"]) == ("B", 1, 25)
    package["cached_bom_revision"] = "C"
    assert replay.replay([package], "challenge", replay.cached_first)[0]["mismatch"] == 0
    package["cached_bom_revision"] = "B"
    assert replay.replay([package], "challenge", replay.cached_first)[0]["mismatch"] == 1
    from revision_package import select_bom_revision
    fixed = replay.replay([package], "pilot", select_bom_revision)[0]
    assert (fixed["selected_bom_revision"], fixed["mismatch"], fixed["review_minutes"],
            fixed["other_findings"]) == ("C", 0, 10, 1)


def test_cli_exports_readable_summary_and_package_level_evidence(tmp_path):
    script = ROOT / "docs" / "root_cause_investigation.py"
    assert script.exists(), "Missing investigation replay"
    result = subprocess.run([sys.executable, str(script), "--out", str(tmp_path)],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["paired_rework_minutes_avoided"] == 570
    with (tmp_path / "evidence.csv").open() as handle:
        assert len(list(csv.DictReader(handle))) == 300
    with (tmp_path / "baseline_pareto.csv").open() as handle:
        first = next(csv.DictReader(handle))
        assert (first["Category"], first["Count"]) == ("Revision letter mismatch", "38.0")
    assert "SYNTHETIC" in result.stdout
