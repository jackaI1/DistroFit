# Equipment effectiveness and changeovers

I use this part of DistroFit to put a measurement study beside a time-loss study.
A stable process can still spend too long stopped, run slowly or make rejects.
These calculations help me see which loss to investigate; they do not prove a cause.

## Try it

After the README's installation steps, run `python -m streamlit run DistroFit.py`
and choose **Equipment effectiveness** in the sidebar. The editable tables accept
new rows, deleted rows and replacement CSV files. The calculation updates after
each edit. The downloads contain the current calculation and ranked downtime.

For the same calculation from a terminal:

```sh
python equipment.py --sample --out /tmp/distrofit-oee
python equipment.py --shift examples/oee/shift.json \
  --downtime examples/oee/downtime.csv \
  --changeover examples/oee/changeover.csv --out /tmp/distrofit-oee-custom
```

I copy those input files and replace the values for my own period. No server,
account or network connection is needed by the command-line calculation. Outputs
are `oee.json`, `downtime_pareto.csv`, `downtime_pareto.png`, `changeover.json` and
`changeover_tasks.csv`. Reusing an output directory replaces those files.
The script prints an actionable error and exits with code 2 for invalid inputs.

## What goes in

Each report covers **one machine, one period, one product and one ideal cycle time**.
I split mixed products into separate reports rather than average their percentages.

`shift.json` has exactly these fields:

| Field | Meaning |
| --- | --- |
| `shift_minutes` | Entire period length, in minutes |
| `excluded_minutes` | Time with no production scheduled, such as breaks |
| `ideal_cycle_seconds` | Fastest achievable seconds per part, not average cycle time |
| `total_count` | All produced parts, including rejects and rework |
| `good_count` | Parts that pass the first time without rework |

`downtime.csv` has `category,minutes`. Each row is one stop inside planned
production, such as a breakdown, material wait or changeover. **Changeovers remain
losses even when planned**. Breaks already excluded from the shift are not logged
again. Minor stops captured by reduced running speed are not also logged as downtime.
The stop total for OEE comes directly from these rows, so it reconciles with the
Pareto table. The table ranks **minutes**, reports event counts separately, preserves
first-seen order on ties and includes the reason that first reaches 80% of total time.
Empty or all-zero logs have zero shares and no highlighted reasons.

The duration-only log cannot detect overlapping events or duplicate entries. I must
deduplicate and clip events to the period before entering them. I never mix different
machines' simultaneous stops in this log. An empty log needs CSV headers but no rows.

`changeover.csv` is an optional, separate task study for a single changeover:

| Field | Meaning |
| --- | --- |
| `step` | Unique task name |
| `minutes` | Observed duration |
| `kind` | `internal` if stopped, `external` if done while running |
| `proposed_minutes` | Estimated duration after the proposed improvement |
| `proposed_kind` | `internal` or `external` under that proposal |

I omit `--changeover` for no task study, or delete all its rows in the page.
The table is independent of the shift's downtime log and never rewrites measured OEE.
It models serial tasks only: summing parallel tasks would overstate stopped time.
The study should cover the whole changeover, including adjustment and first-piece
checks up to the point I can resume acceptable production.

## Calculation design

The pure functions live in [`spc.py`](../spc.py). [`equipment.py`](../equipment.py)
joins them for the command line and
[`pages/1_Equipment_effectiveness.py`](../pages/1_Equipment_effectiveness.py) calls
the same report builder for the app. Both use the same source stop events.
The existing control-chart, capability and count-based Pareto functions retain
their interfaces; the Pareto plotting function also accepts a duration column and label.

With minutes throughout, except for the explicit seconds-per-part input:

```text
planned = shift - excluded
run = planned - sum(stop minutes)
net = ideal_cycle_seconds / 60 * total_count
fully_productive = ideal_cycle_seconds / 60 * good_count
availability = run / planned
performance = net / run
quality = good_count / total_count
OEE = availability * performance * quality = fully_productive / planned
```

The API returns fractions, so `0.7479` means `74.79%`. The loss table reconciles:

```text
planned = stop + (run - net) + (net - fully_productive) + fully_productive
          availability loss   speed loss   quality loss    productive time
```

The latter three are equivalent minutes at the ideal rate, not measured stop events.
Counts must be whole and non-negative, and good cannot exceed total. Inputs must
be finite, planned time and ideal cycle must be positive, and stops cannot exceed
planned time. Performance above 100% is rejected so an incorrect cycle time is not
quietly capped. Only sub-nanominute floating-point roundoff is tolerated. With no
output, quality is undefined (`None` in Python, `null` in JSON, N/A in the app).
With no run time, performance is also undefined. OEE is zero in either case.

SMED means single-minute exchange of die, a method aimed at changeovers under ten
minutes. This tool makes no claim that a proposal meets that goal. It sums current
internal work, compares proposed internal work and ranks tasks by stopped minutes
freed. A negative saving is reported honestly. External work is reported separately:
moving six minutes outside the stop frees machine time but does not remove six
minutes of labour. Feasibility, staffing and safety still need a real trial.

## Worked examples and references

The production inputs reproduce the published [Vorne OEE calculation example](https://www.oee.com/calculating-oee/):
480 shift minutes, 60 excluded break minutes, 47 stopped minutes, a 1-second ideal
cycle, 19,271 parts and 18,848 first-pass good parts. The resulting availability,
performance and quality are **88.81%, 86.11% and 97.80%**, giving **74.79% OEE**.
Tests use the exact fractions before checking the displayed rounded values.

The stop-reason breakdown and changeover task durations are **synthetic**. They
illustrate the [SMED internal/external distinction and conversion method](https://www.leanproduction.com/smed/),
not a measured improvement or a published SMED dataset. In the study, current stopped
work is 6 + 5 + 7 + 2 = 20 minutes. Moving the 6-minute tool preparation outside the
stop and shortening two internal tasks gives 4 + 5 + 2 = 11 minutes, a proposed
9-minute (45%) reduction. External work grows from 4 to 10 minutes.

`tests/test_oee.py` checks that published example, a second hand-calculated OEE
case, loss reconciliation, all-scrap/no-output/full-stop cases, duration ranking,
bad inputs, task conversion, exports, CLI errors, and actual Streamlit page edits.
Run `python -m pytest -q` for these and all existing tests. These examples validate
arithmetic and data flow; they do not establish the accuracy of a factory's records.
