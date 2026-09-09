from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from nqmate_api.market.models import MarketBar, MarketContract
from nqmate_api.market.quality import audit_session_bars, session_window


DAY = date(2026, 9, 3)
CONTRACT = MarketContract("NQ", "NQU6", "NQ_CONT")


def complete_bars(day=DAY):
    start, end = session_window(day)
    return [MarketBar(
        "NQU6", start + timedelta(minutes=i), "1min", 100, 102, 99, 101,
        10, "massive", end + timedelta(days=1),
        start + timedelta(minutes=i + 1),
    ) for i in range(int((end - start).total_seconds() // 60))]


def test_complete_session_is_eligible_and_order_independent():
    bars = complete_bars()
    report = audit_session_bars(bars, DAY, CONTRACT)
    assert report.eligible
    assert report.expected_minutes == report.observed_minutes == 1320
    assert report == audit_session_bars(list(reversed(bars)), DAY, CONTRACT)


def test_missing_interior_and_last_minutes_quarantine_session():
    bars = complete_bars()
    report = audit_session_bars(bars[:400] + bars[401:-1], DAY, CONTRACT)
    assert not report.eligible
    assert report.issue_counts == {"missing_minutes": 2}
    assert report.missing_timestamps == (bars[400].timestamp, bars[-1].timestamp)


@pytest.mark.parametrize("changes,issue", [
    ({"high": 98}, "invalid_ohlcv"),
    ({"close": float("nan")}, "invalid_ohlcv"),
    ({"volume": -1}, "invalid_ohlcv"),
    ({"symbol": "ESU6"}, "contract_mismatch"),
    ({"timestamp": datetime(2026, 9, 3, 10)}, "invalid_timestamp"),
    ({"timestamp": datetime(2026, 9, 3, 10, 0, 1, tzinfo=timezone.utc)}, "unaligned_minute"),
])
def test_invalid_source_rows_fail_closed(changes, issue):
    bars = complete_bars()
    bars[0] = replace(bars[0], **changes)
    report = audit_session_bars(bars, DAY, CONTRACT)
    assert not report.eligible
    assert report.issue_counts[issue] == 1


def test_duplicate_across_providers_is_not_independent_minute():
    bars = complete_bars()
    report = audit_session_bars(bars + [replace(bars[0], provider="other")], DAY, CONTRACT)
    assert report.issue_counts == {"duplicate_minutes": 1}
    assert not report.eligible


def test_derived_and_outside_window_bars_do_not_supply_coverage():
    bars = complete_bars()
    outside = replace(bars[0], timestamp=bars[0].timestamp - timedelta(minutes=1))
    report = audit_session_bars(bars + [replace(bars[0], timeframe="5m"), outside], DAY, CONTRACT)
    assert report.eligible


def test_empty_session_and_naive_availability_fail_closed():
    assert audit_session_bars([], DAY, CONTRACT).issue_counts == {"missing_minutes": 1320}
    bars = complete_bars()
    bars[0] = replace(bars[0], available_at=datetime(2026, 9, 3))
    assert audit_session_bars(bars, DAY, CONTRACT).issue_counts["invalid_availability"] == 1


def test_retrieval_after_session_is_not_itself_future_price_leakage():
    bars = complete_bars()
    bars[0] = replace(bars[0], available_at=bars[0].ingested_at)
    assert audit_session_bars(bars, DAY, CONTRACT).eligible


@pytest.mark.parametrize("day,hour", [(date(2026, 3, 9), 22), (date(2026, 11, 2), 23)])
def test_session_window_observes_eastern_dst(day, hour):
    start, end = session_window(day)
    assert start.hour == hour
    assert end - start == timedelta(hours=22)


def test_availability_before_bar_close_fails_closed():
    bars = complete_bars()
    bars[0] = replace(bars[0], available_at=bars[0].timestamp)
    assert audit_session_bars(bars, DAY, CONTRACT).issue_counts["invalid_availability"] == 1
