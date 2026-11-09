"""Native Bloomberg SDK messages, error paths and the DistroFit CSV boundary."""
from datetime import date
from io import StringIO
import json
import math
from pathlib import Path
import subprocess
import socket
import sys
from unittest.mock import patch

import pytest

blpapi = pytest.importorskip("blpapi", reason="Optional SDK has its own required CI job")
import blpapi.test

from bloomberg_history import (HistoryError, HistoryQuery, build_request, collect_history,
                               compare_returns, dated_returns, export_history, fetch_history)
from bloomberg_sandbox import (SandboxQueue, SandboxSession, response_event,
                               sample_history, service)


QUERY = HistoryQuery("SYNTHETIC SDK SAMPLE", date(2026, 1, 5), date(2026, 2, 27))


def body(rows=None, **extra):
    return {"securityData": {"security": QUERY.security,
                              "fieldData": rows if rows is not None else [
                                  {"date": date(2026, 1, 5), "PX_LAST": 100},
                                  {"date": date(2026, 1, 6), "PX_LAST": 103}], **extra}}


def collect(*bodies, final=True):
    queue = SandboxQueue()
    refdata = service()
    queue.events = [response_event(refdata, item, final=final and i == len(bodies) - 1)
                    for i, item in enumerate(bodies)]
    return collect_history(queue, QUERY, 2)


def test_native_request_uses_adjusted_active_daily_prices():
    request = build_request(service(), QUERY)
    assert isinstance(request, blpapi.Request)
    assert request.asElement().toPy() == QUERY.parameters()
    assert QUERY.parameters()["fields"] == ["PX_LAST"]
    assert all(QUERY.parameters()[key] for key in
               ("adjustmentNormal", "adjustmentAbnormal", "adjustmentSplit"))


def test_partial_responses_are_sorted_and_converted_to_simple_returns():
    rows = collect(body([{"date": date(2026, 1, 6), "PX_LAST": 103}]),
                   body([{"date": date(2026, 1, 5), "PX_LAST": 100}]))
    assert rows == [(date(2026, 1, 5), 100), (date(2026, 1, 6), 103)]
    assert dated_returns(rows)[0][2] == pytest.approx(.03)


def test_weekend_gap_is_one_observation_without_filled_zeroes():
    rows = collect(body([{"date": date(2026, 1, 9), "PX_LAST": 100},
                         {"date": date(2026, 1, 12), "PX_LAST": 98}]))
    returns = dated_returns(rows)
    assert len(returns) == 1
    assert returns[0] == (date(2026, 1, 9), date(2026, 1, 12), pytest.approx(-.02))


@pytest.mark.parametrize("bad", [0, -2, None])
def test_invalid_or_missing_price_rejects_entire_history(bad):
    with pytest.raises(HistoryError, match="positive|Missing"):
        collect(body([{"date": date(2026, 1, 5), "PX_LAST": bad}]))


def test_duplicate_dates_are_rejected_even_between_events():
    with pytest.raises(HistoryError, match="Duplicate"):
        collect(body(), body())


@pytest.mark.parametrize("rows,pattern", [
    ([], "At least two"),
    ([{"date": date(2026, 1, 5), "PX_LAST": 100}], "At least two"),
    ([{"PX_LAST": 100}], "needs a date"),
    ([{"date": date(2025, 12, 31), "PX_LAST": 100}], "outside"),
])
def test_incomplete_or_wrong_date_range_is_rejected(rows, pattern):
    with pytest.raises(HistoryError, match=pattern):
        collect(body(rows))


@pytest.mark.parametrize("error_body,pattern", [
    ({"responseError": {"category": "NO_AUTH", "message": "synthetic denial"}}, "response error"),
    (body(securityError={"category": "BAD_SEC", "message": "synthetic security error"}), "securityError"),
    (body(fieldExceptions=[{"fieldId": "PX_LAST", "errorInfo": {
        "category": "NO_AUTH", "message": "synthetic field denial"}}]), "fieldExceptions"),
    (body(security="WRONG SECURITY"), "unexpected security"),
])
def test_bloomberg_errors_never_become_successful_samples(error_body, pattern):
    with pytest.raises(HistoryError, match=pattern):
        collect(error_body)


def test_partial_only_response_times_out_instead_of_exporting():
    queue = SandboxQueue()
    queue.events = [response_event(service(), body(), final=False)]
    ticks = iter([0, 0, 2])
    with pytest.raises(TimeoutError, match="did not finish"):
        collect_history(queue, QUERY, 1, clock=lambda: next(ticks))


def test_request_failure_event_is_fatal():
    queue = SandboxQueue()
    queue.events = [blpapi.test.createEvent(blpapi.Event.REQUEST_STATUS)]
    with pytest.raises(HistoryError, match="request/session failed"):
        collect_history(queue, QUERY, 1)


@pytest.mark.parametrize("failure", ["start", "service", "send", "response", "cancel", "success"])
def test_session_is_stopped_on_every_exit(failure):
    created = []

    class Session(SandboxSession):
        def __init__(self, options):
            super().__init__(options)
            created.append(self)

        def start(self):
            return failure != "start"

        def openService(self, name):
            return failure != "service"

        def sendRequest(self, request, eventQueue):
            if failure == "send":
                raise RuntimeError("send failed")
            result = super().sendRequest(request, eventQueue)
            if failure == "response":
                eventQueue.events = [response_event(self.refdata, body(security="WRONG SECURITY"))]
            return result

        def cancel(self, correlation):
            super().cancel(correlation)
            if failure == "cancel":
                raise RuntimeError("cancel failed")

    if failure == "success":
        assert len(fetch_history(QUERY, session_factory=Session, queue_factory=SandboxQueue)) == 40
    else:
        with pytest.raises((HistoryError, RuntimeError)):
            fetch_history(QUERY, session_factory=Session, queue_factory=SandboxQueue)
    assert created[0].stopped
    assert created[0].cancelled == (failure in ("response", "cancel", "success"))


@pytest.mark.parametrize("timeout", [0, -1, math.nan, math.inf])
def test_bad_timeout_never_starts_session(timeout):
    with pytest.raises(HistoryError, match="Timeout"):
        fetch_history(QUERY, timeout=timeout, session_factory=lambda _: pytest.fail("started"))


def test_real_native_session_fails_cleanly_without_a_licensed_endpoint():
    # Hold an unlistening loopback port; never connect to another owner's service.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        with pytest.raises(HistoryError, match="connection unavailable"):
            fetch_history(QUERY, host="127.0.0.1", port=reserved.getsockname()[1], timeout=.05)


def test_sandbox_export_loads_into_distrofit_and_comparison_keeps_time_order(tmp_path):
    import numpy as np
    from analysis import read_csv

    query, prices = sample_history()
    out = tmp_path / "export"
    metadata = export_history(prices, query, out, source="synthetic SDK sandbox", compare=True)
    frame = read_csv(StringIO((out / "returns.csv").read_text()))
    returns = dated_returns(prices)
    np.testing.assert_allclose(frame["simple_return"], [row[2] for row in returns])
    assert metadata["price_count"] == 40 and metadata["return_count"] == 39
    comparison = metadata["comparison"]
    assert (comparison["train_count"], comparison["held_count"]) == (29, 10)
    assert comparison["last_training_date"] < comparison["first_held_date"]
    normal = next(row for row in comparison["results"] if row["distribution"] == "Normal")
    earlier = frame["simple_return"].to_numpy()[:29]
    np.testing.assert_allclose(normal["parameters"], [earlier.mean(), earlier.std()])
    assert json.loads((out / "metadata.json").read_text()) == json.loads(json.dumps(metadata))
    assert len((out / "dated_returns.csv").read_text().splitlines()) == 40


def test_saved_export_is_preserved_and_failed_write_removes_only_owned_output(tmp_path):
    query, prices = sample_history()
    existing = tmp_path / "saved"
    existing.mkdir()
    marker = existing / "keep.txt"
    marker.write_text("saved record")
    with pytest.raises(FileExistsError):
        export_history(prices, query, existing, source="synthetic")
    assert marker.read_text() == "saved record"
    with patch.object(Path, "write_text", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            export_history(prices, query, tmp_path / "failed", source="synthetic")
    assert not (tmp_path / "failed").exists()
    assert marker.exists()


@pytest.mark.parametrize("count", [0, 8])
def test_too_short_comparison_is_rejected(count):
    with pytest.raises(HistoryError, match="twelve"):
        compare_returns([(date(2026, 1, 5), date(2026, 1, 6), i / 100) for i in range(count)])


def test_command_line_sample_and_missing_live_arguments(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "bloomberg_history.py"), "--sample",
                             "--compare", "--out", str(tmp_path / "sample")],
                            text=True, capture_output=True, timeout=60, cwd=root)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["return_count"] == 39
    bad = subprocess.run([sys.executable, str(root / "bloomberg_history.py"), "--live",
                          "--out", str(tmp_path / "bad")], text=True, capture_output=True,
                         timeout=30, cwd=root)
    assert bad.returncode == 2 and "requires" in bad.stderr
    assert not (tmp_path / "bad").exists()
