# Price history for a curve comparison

I added this to learn how daily price changes compare with the curves already in
DistroFit. It is an import and analysis tool, not a trading system. The default
sample is invented and does not establish access to a Bloomberg subscription.

## Try the sample

From the repository root, in the Python 3.12 environment from the README:

```sh
python -m pip install -r requirements.txt
python -m pip install --index-url https://blpapi.bloomberg.com/repository/releases/python/simple -r requirements-bloomberg.txt
python bloomberg_history.py --sample --compare --out .runtime/price-example
```

This makes a new folder with four files:

| File | What I can inspect |
| --- | --- |
| `prices.csv` | Closing price and date for each observation |
| `dated_returns.csv` | Previous date, current date and fractional price change |
| `returns.csv` | A single numeric column ready for DistroFit's CSV upload |
| `metadata.json` | Source label, request, SDK version, units, counts and optional comparison |

The fixed seed generates 40 weekday prices between January 5 and February 27,
2026, then 39 returns. This is a synthetic weekday calendar, not an exchange's
holiday calendar. The sandbox never opens a socket or starts another process.
Its transport is a small Python double. Requests, service definitions, typed
dates, partial events and response messages are real native Bloomberg objects.
The minimal XML file defines only the historical fields used in this test; it
is not a downloaded production service schema.

To examine the CSV in the app, run the README's Streamlit command, choose
**Upload CSV** and select `returns.csv`. The app accepts decimal returns with
positive and negative values. Some families such as Exponential have incompatible
support for negative returns. Normal and Student's t are sensible starting
comparisons, not an assertion about which distribution describes a market.

## Use an authorised Bloomberg connection

The live adapter uses Bloomberg Desktop API. It expects an already authorised
local Bloomberg session, normally on the licensed user's Windows computer. I do
not start or install a Terminal. This path is implemented but has not been
verified against a licensed service. A subscription and permissions for the
requested security and fields are required; installing the SDK grants neither.
I have not used Morningstar Direct.

On that authorised computer, after the Python setup above:

```sh
python bloomberg_history.py --live --security "IBM US Equity" \
  --start 2026-01-05 --end 2026-02-27 --timeout 30 \
  --compare --out .runtime/my-private-history
```

`--host` defaults to `localhost`, `--port` to `8194`. This is a Desktop API
connection, not a Server API authentication implementation. A remote host is
only appropriate where the user's Bloomberg configuration permits it. Do not
publish licensed exports or send them to a hosted demo; follow the licence and
keep the files on the authorised machine. `.runtime/` is ignored by Git.
The repository and CI contain only synthetic messages, not credentials, licensed
prices or personal account data.

## Request and validation

`bloomberg_history.py` opens `//blp/refdata` and creates a
`HistoricalDataRequest` for one security's `PX_LAST` closing prices. It requests
daily frequency, active trading days only, and explicitly enables normal cash,
abnormal cash and split adjustments. These settings are recorded, not inferred
from a Terminal default. Adjusted price changes are not a guaranteed total-return
series, and the code does not calculate reinvested dividends or currency returns.

Each request has its own event queue, so another request cannot mix in its
responses. The collector waits for the final response after all partial responses
and uses a monotonic clock, one that cannot jump with a wall-clock change, to
limit its response wait. Connection attempts are limited to one, with at most
five seconds for the initial connection. Request/session failures, provider
errors, field exceptions, mismatched securities, missing or nonpositive prices,
dates outside the request and duplicate dates reject the whole import.

Rows are sorted by date before calculating `current / previous - 1`.
Missing days are never filled with yesterday's price. A Friday-to-Monday change
is one observation, not three daily zero-filled observations. The dated export
keeps the interval visible. A missing unreported trading day cannot be detected
without an external exchange calendar; I do not claim that validation here.

The adapter cancels its request and stops its session on success, timeout or
failure. Validation and the optional comparison finish before an output folder
is created. Existing folders are refused. A write error removes only the new
folder owned by that export. There is no background service to clean up.

## Comparison and limits

`--compare` requires at least 12 varying returns. It reserves the latest 25%,
rounded up and with at least three observations, to check curves fitted only to
the earlier values. It calls DistroFit's existing distribution and scoring
functions, without filtering or shuffling the input. The Normal fit has two
parameters; Student's t also estimates tail weight. Lower held-out negative log
likelihood means that a curve assigned more density to the later observations.
It can be negative because density is not a probability and returns use decimal
units. The sample has 29 training observations and 10 held-out observations.

This is one historical check with a small sample. Dependence, changing market
conditions and transaction costs are not modelled. No forecast, investment
recommendation or Terminal proficiency is established by it.

## Tests and references

```sh
python -m pip install pytest==9.1.1
python -m pytest -q tests/test_bloomberg_history.py tests/test_analysis.py
```

The dedicated GitHub Actions job requires the SDK import before running tests,
so its SDK tests cannot silently skip. The ordinary suite can skip this optional
feature when the SDK is not installed. The Linux job also runs the complete
sample and uploads its four output files for inspection. Existing project
workflows continue to test the app and its other features.

I followed Bloomberg's documentation for
[request creation](https://bloomberg.github.io/blpapi-docs/python/3.26.9/_autosummary/blpapi.Request.html),
[SDK test services](https://bloomberg.github.io/blpapi-docs/python/3.26.9/_autosummary/blpapi.test.deserializeService.html)
and [message formatting](https://bloomberg.github.io/blpapi-docs/python/3.26.9/_autosummary/blpapi.test.MessageFormatter.html).
The SDK is downloaded from Bloomberg's own package index, with its own licence;
its wheels are not redistributed here. The schema and transport in this repo
are small project-owned synthetic fixtures, not a replacement Bloomberg server.
