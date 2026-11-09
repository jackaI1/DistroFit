"""Small, labelled synthetic Bloomberg SDK sandbox. No network or market data."""
from datetime import date, timedelta
from pathlib import Path
import json
import random

import blpapi
import blpapi.test

from bloomberg_history import HistoryQuery, fetch_history


def service():
    return blpapi.test.deserializeService(
        Path(__file__).with_name("examples").joinpath("bloomberg", "history-schema.xml").read_text())


def response_event(service, body, *, final=True):
    event = blpapi.test.createEvent(blpapi.Event.RESPONSE if final else blpapi.Event.PARTIAL_RESPONSE)
    definition = service.getOperation("HistoricalDataRequest").getResponseDefinitionAt(0)
    formatter = blpapi.test.appendMessage(event, definition)
    formatter.formatMessageJson(json.dumps(body, default=lambda value: value.isoformat()))
    return event


class SandboxQueue:
    def __init__(self):
        self.events = []

    def nextEvent(self, timeout):
        if self.events:
            return self.events.pop(0)
        return blpapi.test.createEvent(blpapi.Event.TIMEOUT)


class SandboxSession:
    """Transport double only; requests, services and events are native SDK objects."""
    def __init__(self, options):
        self.refdata = service()
        self.stopped = False
        self.cancelled = False
        self.request = None

    def start(self):
        return True

    def openService(self, name):
        return name == "//blp/refdata"

    def getService(self, name):
        return self.refdata

    def sendRequest(self, request, eventQueue):
        self.request = request
        parameters = request.asElement().toPy()
        security = parameters["securities"][0]
        start = date.fromisoformat(parameters["startDate"])
        end = date.fromisoformat(parameters["endDate"])
        price = 100.0
        rng = random.Random(19)
        rows = []
        day = start
        while day <= end:
            if day.weekday() < 5:
                price *= 1 + rng.uniform(-.035, .035)
                rows.append({"date": day, "PX_LAST": round(price, 6)})
            day += timedelta(days=1)
        midpoint = len(rows) // 2
        for part, final in ((rows[:midpoint], False), (rows[midpoint:], True)):
            eventQueue.events.append(response_event(self.refdata, {
                "securityData": {"security": security, "fieldData": part}}, final=final))
        return blpapi.CorrelationId(1)

    def cancel(self, correlation):
        self.cancelled = True

    def stop(self):
        self.stopped = True


def sample_history():
    query = HistoryQuery("SYNTHETIC SDK SAMPLE", date(2026, 1, 5), date(2026, 2, 27))
    return query, fetch_history(query, session_factory=SandboxSession, queue_factory=SandboxQueue)
