from datetime import date, datetime, timedelta, timezone

from nqmate_api.market.models import MarketBar
from nqmate_api.market.snapshots import SNAPSHOT_TIMES_ET, build_point_in_time_snapshots


def make_bar(timestamp: datetime, value: float, available_at: datetime | None = None) -> MarketBar:
    return MarketBar("NQU6", timestamp, "1min", value, value + 1, value - 1, value,
                     1, "test", timestamp, available_at or timestamp)


def test_builds_only_declared_snapshot_times_and_excludes_future_bars():
    base = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)  # 08:00 ET
    bars = [make_bar(base + timedelta(minutes=i), 100 + i) for i in range(150)]
    snapshots = build_point_in_time_snapshots(bars, date(2026, 9, 8), "NQU6", "f-v1")
    assert [item.snapshot_timestamp.astimezone(timezone.utc).hour for item in snapshots] == [12, 13, 13, 13, 14, 16]
    assert all(item.snapshot_timestamp.minute in (0, 25, 30) for item in snapshots)
    assert [item.features["bars"] for item in snapshots[:2]] == [30.0, 60.0]


def test_late_availability_keeps_snapshot_missing_instead_of_leaking_future_data():
    timestamp = datetime(2026, 9, 8, 13, 29, tzinfo=timezone.utc)
    bars = [make_bar(timestamp, 100, available_at=timestamp + timedelta(minutes=2))]
    snapshots = build_point_in_time_snapshots(bars, date(2026, 9, 8), "NQU6", "f-v1")
    assert all(item.snapshot_timestamp.astimezone(timezone.utc).hour != 13
               or item.snapshot_timestamp.astimezone(timezone.utc).minute != 30
               for item in snapshots)


def test_snapshot_times_are_explicit_and_stable():
    assert SNAPSHOT_TIMES_ET == ("08:30", "09:00", "09:25", "09:30", "10:00", "12:00")
