from datetime import date, datetime, timedelta, timezone

from nqmate_api.market.models import MarketBar
from nqmate_api.market.models import MarketContract
from jobs.populate_feature_snapshots import build_session_snapshots
from nqmate_api.market.snapshots import SNAPSHOT_TIMES_ET, build_point_in_time_snapshots, market_feature_function


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


def test_market_features_preserve_missing_values_and_add_point_in_time_es_strength():
    base = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    nq = [make_bar(base + timedelta(minutes=i), 100 + i) for i in range(40)]
    es = [make_bar(base + timedelta(minutes=i), 200 + (2 * i)) for i in range(40)]
    features = market_feature_function(es)(nq, datetime(2026, 9, 8, 12, 30, tzinfo=timezone.utc))
    assert features["return_5m"] == (129 / 124) - 1
    assert features["nq_es_relative_strength"] == ((129 / 124) - 1) - ((258 / 248) - 1)
    assert features["ema_50"] is None


def test_reconstructed_policy_uses_closed_event_time_and_labels_snapshot():
    timestamp = datetime(2026, 9, 8, 13, 29, tzinfo=timezone.utc)
    bars = [make_bar(timestamp, 100, available_at=timestamp + timedelta(days=30))]
    snapshots = build_point_in_time_snapshots(
        bars, date(2026, 9, 8), "NQU6", "f-v1", availability_policy="event_time_reconstructed"
    )
    snapshot = next(item for item in snapshots if item.snapshot_timestamp.hour == 9 and item.snapshot_timestamp.minute == 30)
    assert snapshot.availability_policy == "event_time_reconstructed"
    assert snapshot.available_at == datetime(2026, 9, 8, 13, 30, tzinfo=timezone.utc)


def test_session_snapshot_rows_use_nq_primary_and_es_supporting_context():
    base = datetime(2026, 9, 8, 0, 0, tzinfo=timezone.utc)
    nq = [make_bar(base + timedelta(minutes=i), 100 + i) for i in range(1000)]
    es = [make_bar(base + timedelta(minutes=i), 200 + i) for i in range(1000)]
    rows = build_session_snapshots(
        nq, es, date(2026, 9, 8), MarketContract("NQ", "NQU6", "NQ_CONT"), "event_time_reconstructed"
    )
    assert len(rows) == 6
    assert all(row.symbol == "NQU6" and row.contract == "NQU6" for row in rows)
    assert all(row.availability_policy == "event_time_reconstructed" for row in rows)
