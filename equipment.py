"""Shared OEE report and command-line export for DistroFit's SPC tools."""
import argparse
import json
from pathlib import Path

import pandas as pd

from spc import calculate_oee, downtime_pareto, pareto_chart, smed_analysis

EXAMPLE = Path(__file__).resolve().parent / "examples" / "oee"


def load_example():
    """Published OEE inputs; synthetic stop breakdown and changeover study."""
    return (json.loads((EXAMPLE / "shift.json").read_text()),
            pd.read_csv(EXAMPLE / "downtime.csv"), pd.read_csv(EXAMPLE / "changeover.csv"))


def build_equipment_report(shift, downtime, changeover=()):
    """Derive OEE stop time from exactly the events ranked in the Pareto."""
    if not isinstance(shift, dict):
        raise ValueError("Shift must be a JSON object of production inputs.")
    expected = {"shift_minutes", "excluded_minutes", "ideal_cycle_seconds", "total_count", "good_count"}
    if set(shift) != expected:
        raise ValueError(f"Shift needs exactly these fields: {', '.join(sorted(expected))}.")
    pareto = downtime_pareto(downtime)
    oee = calculate_oee(**shift, stop_minutes=float(pareto["Minutes"].sum()))
    return {"oee": oee, "downtime": pareto, "changeover": smed_analysis(changeover)}


def export_report(report, directory):
    """Save machine-readable results and a correctly labelled duration chart."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "oee.json").write_text(json.dumps(report["oee"], indent=2, allow_nan=False) + "\n")
    report["downtime"].to_csv(directory / "downtime_pareto.csv", index=False)
    fig = pareto_chart(report["downtime"], "Downtime by reason", "Minutes", "Stopped minutes")
    try:
        fig.savefig(directory / "downtime_pareto.png", dpi=150)
    finally:
        fig.clear()
    changeover = report["changeover"]
    (directory / "changeover.json").write_text(json.dumps(
        {key: value for key, value in changeover.items() if key != "tasks"}, indent=2, allow_nan=False) + "\n")
    changeover["tasks"].to_csv(directory / "changeover_tasks.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description="Calculate OEE, downtime Pareto and a proposed changeover plan.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", action="store_true", help="Use the bundled worked example")
    source.add_argument("--shift", type=Path, help="JSON production inputs (see examples/oee/shift.json)")
    parser.add_argument("--downtime", type=Path, help="CSV with category,minutes; required with --shift")
    parser.add_argument("--changeover", type=Path, help="Optional CSV task study, see examples/oee/changeover.csv")
    parser.add_argument("--out", type=Path, required=True, help="Directory for JSON, CSV and PNG results")
    args = parser.parse_args()
    if args.sample and (args.downtime or args.changeover):
        parser.error("--sample cannot be mixed with custom input files.")
    if args.shift and args.downtime is None:
        parser.error("--shift requires --downtime (a header-only CSV means no stops).")
    try:
        shift, downtime, changeover = load_example() if args.sample else (
            json.loads(args.shift.read_text()), pd.read_csv(args.downtime),
            pd.read_csv(args.changeover) if args.changeover else [])
        report = build_equipment_report(shift, downtime, changeover)
        export_report(report, args.out)
    except (ValueError, OSError, UnicodeError, pd.errors.ParserError) as error:
        parser.error(str(error))
    print(f"OEE: {report['oee']['oee']:.2%}; stopped: {report['oee']['stop_minutes']:g} min")
    print(f"Proposed changeover saving: {report['changeover']['saved_stop_minutes']:g} min (estimate)")
    print(f"Saved results to {args.out}")


if __name__ == "__main__":
    main()
