# DMAIC production board

The sample JSON is an editable record: objective and specifications (Define),
ordered readings and a baseline count (Measure), defect counts, downtime events,
and one fishbone branch and five questions per defect category (Analyze),
assigned actions (Improve), and a control plan (Control). Run `python dmaic.py
--input examples/dmaic/production.json --out /tmp/board.html` and print the
self-contained HTML in landscape. No data leaves the computer. Keep private
production records and exported boards out of version control.

The individuals and moving-range chart uses a fixed initial baseline. The report
shows all four Western Electric rule signals on individuals and points beyond the
moving-range limit. Cp and Cpk use baseline mean moving range / 1.128 for the
within-process standard deviation, while the mean uses all readings; Cp is the
specification width divided by six standard deviations and Cpk is the distance
from the mean to the nearer limit divided by three. Out-of-spec counts use strict
inequalities. A negative Cpk means the mean is beyond a limit. Defects are ranked
by count and downtime by minutes; equal categories retain their input order.

These estimates assume representative, independent observations, a stable process
and approximately normal measurements. Baseline limits are estimated, not proof
of stability. The five whys are hypotheses, not established causes; validate
them with evidence before changing a process. This example is synthetic and does
not demonstrate an actual improvement. Print layout can vary by browser and
length of supplied text.
