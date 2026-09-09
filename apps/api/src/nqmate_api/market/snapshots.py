"""Point-in-time market snapshot contracts for historical research."""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Callable, Mapping, Sequence
from zoneinfo import ZoneInfo

from nqmate_api.market.models import MarketBar

EASTERN = ZoneInfo("America/New_York")
SNAPSHOT_TIMES_ET = ("08:30", "09:00", "09:25", "09:30", "10:00", "12:00")


@dataclass(frozen=True)
class PointInTimeSnapshot:
    session_date: date
    snapshot_timestamp: datetime
    symbol: str
    contract: str
    feature_version: str
    features: Mapping[str, float]
    available_at: datetime


def build_point_in_time_snapshots(
    bars: Sequence[MarketBar], session_date: date, contract: str, feature_version: str,
    feature_fn: Callable[[Sequence[MarketBar]], Mapping[str, float]] | None = None,
) -> tuple[PointInTimeSnapshot, ...]:
    """Build immutable snapshots from bars known by each snapshot timestamp.

    Bars at the snapshot minute are excluded because that minute is not closed
    until the following minute. Bars unavailable at the snapshot are excluded;
    an empty eligible input produces no snapshot rather than fabricated values.
    """
    selected = tuple(sorted((bar for bar in bars if bar.symbol == contract and bar.timeframe == "1min"),
                            key=lambda bar: bar.timestamp))
    if not selected:
        return ()
    make_features = feature_fn or (lambda available: {"bars": float(len(available))})
    snapshots: list[PointInTimeSnapshot] = []
    for value in SNAPSHOT_TIMES_ET:
        hour, minute = (int(item) for item in value.split(":"))
        timestamp = datetime.combine(session_date, time(hour, minute), EASTERN)
        eligible = tuple(bar for bar in selected
                         if bar.timestamp < timestamp and bar.available_at <= timestamp.astimezone(timezone.utc))
        if not eligible:
            continue
        features = {name: float(number) for name, number in make_features(eligible).items()}
        snapshots.append(PointInTimeSnapshot(
            session_date, timestamp, contract, contract, feature_version,
            features, max(bar.available_at for bar in eligible),
        ))
    return tuple(snapshots)
