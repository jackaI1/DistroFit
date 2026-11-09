"""Import Bloomberg adjusted closing prices as dated returns for DistroFit.

The optional blpapi dependency is imported only when this feature is used.
The sample uses Bloomberg's native SDK test messages, never downloaded prices.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
import shutil
import time


class HistoryError(ValueError):
    """An incomplete or invalid history must not become a fitted sample."""


@dataclass(frozen=True)
class HistoryQuery:
    security: str
    start: date
    end: date

    def __post_init__(self):
        if not self.security.strip() or len(self.security) > 256:
            raise HistoryError("Provide one Bloomberg security identifier.")
        if self.start >= self.end:
            raise HistoryError("Start must be before end.")

    def parameters(self):
        return {
            "securities": [self.security], "fields": ["PX_LAST"],
            "startDate": self.start.strftime("%Y%m%d"),
            "endDate": self.end.strftime("%Y%m%d"),
            "periodicitySelection": "DAILY",
            "nonTradingDayFillOption": "ACTIVE_DAYS_ONLY",
            "adjustmentNormal": True, "adjustmentAbnormal": True,
            "adjustmentSplit": True,
        }


def build_request(service, query):
    request = service.createRequest("HistoricalDataRequest")
    request.fromPy(query.parameters())
    return request


def decode_message(message, query):
    """Decode a native blpapi.Message, preserving error and date boundaries."""
    body = message.toPy()
    if body.get("responseError"):
        raise HistoryError(f"Bloomberg response error: {body['responseError']}")
    data = body.get("securityData")
    if not isinstance(data, dict) or data.get("security") != query.security:
        raise HistoryError("Missing or unexpected security in historical response.")
    for key in ("securityError", "fieldExceptions"):
        if data.get(key):
            raise HistoryError(f"Bloomberg {key}: {data[key]}")
    rows = []
    for row in data.get("fieldData", []):
        day, price = row.get("date"), row.get("PX_LAST")
        if type(day) is not date:
            raise HistoryError("Each closing price needs a date.")
        if not query.start <= day <= query.end:
            raise HistoryError("Price date falls outside the requested range.")
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise HistoryError("Missing or nonnumeric PX_LAST; no forward filling is allowed.")
        if not math.isfinite(price) or price <= 0:
            raise HistoryError("Closing prices must be finite and positive.")
        rows.append((day, float(price)))
    return rows


def collect_history(queue, query, timeout, *, clock=time.monotonic):
    import blpapi

    if not math.isfinite(timeout) or timeout <= 0:
        raise HistoryError("Timeout must be a positive finite number.")
    deadline = clock() + timeout
    rows = []
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError("Bloomberg did not finish the historical response in time.")
        event = queue.nextEvent(max(1, min(1000, math.ceil(remaining * 1000))))
        kind = event.eventType()
        if kind in (blpapi.Event.PARTIAL_RESPONSE, blpapi.Event.RESPONSE):
            for message in event:
                if str(message.messageType()) != "HistoricalDataResponse":
                    raise HistoryError("Unexpected Bloomberg response type.")
                rows.extend(decode_message(message, query))
            if kind == blpapi.Event.RESPONSE:
                break
        elif kind in (blpapi.Event.REQUEST_STATUS, blpapi.Event.SESSION_STATUS):
            raise HistoryError("Bloomberg request/session failed; history was not exported.")
    rows.sort()
    if len(rows) < 2:
        raise HistoryError("At least two closing prices are needed.")
    if len({day for day, _ in rows}) != len(rows):
        raise HistoryError("Duplicate trading dates in Bloomberg history.")
    return rows


def fetch_history(query, *, host="localhost", port=8194, timeout=30,
                  session_factory=None, queue_factory=None):
    """One synchronous request with a private queue and guaranteed session stop.

    Default mode is Bloomberg Desktop API on an already authorised machine.
    Injection points let the SDK sandbox exercise the identical request path.
    """
    import blpapi

    if not math.isfinite(timeout) or timeout <= 0:
        raise HistoryError("Timeout must be a positive finite number.")
    if not 1 <= port <= 65535 or not host.strip():
        raise HistoryError("Provide a host and a port between 1 and 65535.")
    options = blpapi.SessionOptions()
    options.setServerHost(host)
    options.setServerPort(port)
    options.setConnectTimeout(max(1, min(5000, int(timeout * 1000))))
    options.setServiceCheckTimeout(max(1, min(5000, int(timeout * 1000))))
    options.setServiceDownloadTimeout(max(1, min(5000, int(timeout * 1000))))
    options.setNumStartAttempts(1)
    options.setAutoRestartOnDisconnection(False)
    session = (session_factory or blpapi.Session)(options)
    correlation = None
    try:
        if not session.start():
            raise HistoryError("Bloomberg connection unavailable. Live mode needs licensed access; use --sample to try the SDK sandbox.")
        if not session.openService("//blp/refdata"):
            raise HistoryError("Bloomberg //blp/refdata service unavailable.")
        request = build_request(session.getService("//blp/refdata"), query)
        queue = (queue_factory or blpapi.EventQueue)()
        correlation = session.sendRequest(request, eventQueue=queue)
        return collect_history(queue, query, timeout)
    except blpapi.Exception as error:
        raise HistoryError(f"Bloomberg SDK request failed: {error}") from error
    finally:
        try:
            if correlation is not None:
                session.cancel(correlation)
        finally:
            session.stop()


def dated_returns(prices):
    """Decimal simple returns between consecutive available trading dates."""
    return [(previous_day, day, price / previous_price - 1)
            for (previous_day, previous_price), (day, price)
            in zip(prices, prices[1:])]


def compare_returns(returns):
    """Fit earlier returns, score later returns without shuffling or filtering."""
    import numpy as np
    from analysis import get_supported_distributions, score_values

    values = np.array([row[2] for row in returns])
    if len(values) < 12 or not np.isfinite(values).all() or np.ptp(values) == 0:
        raise HistoryError("Comparison needs at least twelve finite, varying returns.")
    split = len(values) - max(3, math.ceil(len(values) * .25))
    training, held = values[:split], values[split:]
    if np.ptp(training) == 0:
        raise HistoryError("Earlier training returns are constant.")
    results = []
    for name in ("Normal", "Student's t"):
        parameters = tuple(float(p) for p in get_supported_distributions()[name].fit(training))
        loss = score_values(name, parameters, held)
        if not all(math.isfinite(p) for p in parameters) or parameters[-1] <= 0 or not math.isfinite(loss):
            raise HistoryError(f"No finite {name} comparison.")
        results.append({"distribution": name, "parameters": parameters, "held_out_nll": loss})
    return {"split": "chronological, earliest 75% train, latest 25% held out (rounded up)",
            "train_count": split, "held_count": len(held),
            "last_training_date": returns[split - 1][1].isoformat(),
            "first_held_date": returns[split][1].isoformat(),
            "results": sorted(results, key=lambda row: row["held_out_nll"]),
            "limitation": "One historical split is exploratory, not a forecast or investment advice."}


def export_history(prices, query, output, *, source, compare=False):
    import blpapi

    returns = dated_returns(prices)
    comparison = compare_returns(returns) if compare else None
    metadata = {"source": source, "sdk_version": blpapi.version(),
                "service": "//blp/refdata", "request": query.parameters(),
                "price_count": len(prices), "return_count": len(returns),
                "units": "decimal simple price return; 0.01 means 1%",
                "calendar": "consecutive available trading dates; no missing-day filling",
                "comparison": comparison,
                "warning": "Adjusted PX_LAST changes, not a guaranteed total-return series. No live data is included in the repository."}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()  # Refuse to overwrite a saved export or an existing directory.
    try:
        for name, header, rows in (
            ("prices.csv", ["date", "adjusted_close"], prices),
            ("dated_returns.csv", ["previous_date", "date", "simple_return"], returns),
            ("returns.csv", ["simple_return"], [(row[2],) for row in returns]),
        ):
            with (output / name).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerows(rows)
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    except BaseException:
        shutil.rmtree(output)
        raise
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", action="store_true", help="Synthetic prices through the real Bloomberg SDK test facilities")
    mode.add_argument("--live", action="store_true", help="An authorised Bloomberg Desktop API session is required")
    parser.add_argument("--security")
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8194)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.sample:
            if args.security or args.start or args.end:
                raise HistoryError("Sample mode uses its own labelled security and dates.")
            from bloomberg_sandbox import sample_history
            query, prices = sample_history()
            source = "synthetic Bloomberg SDK sandbox; not Bloomberg market data"
        else:
            if not all((args.security, args.start, args.end)):
                raise HistoryError("Live mode requires --security, --start and --end.")
            query = HistoryQuery(args.security, args.start, args.end)
            prices = fetch_history(query, host=args.host, port=args.port, timeout=args.timeout)
            source = "Bloomberg Desktop API; licensed user export, keep private"
        metadata = export_history(prices, query, args.out, source=source, compare=args.compare)
    except (HistoryError, TimeoutError, OSError, ImportError) as error:
        parser.exit(2, f"History export failed: {error}\n")
    print(json.dumps({key: metadata[key] for key in ("source", "price_count", "return_count")}))


if __name__ == "__main__":
    main()
