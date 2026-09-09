"""Point-in-time market snapshot contracts for historical research."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Callable, Literal, Mapping, Sequence
from zoneinfo import ZoneInfo

from nqmate_api.market.models import MarketBar
from nqmate_api.market.calculations import technical_features

EASTERN = ZoneInfo("America/New_York")
SNAPSHOT_TIMES_ET = ("08:30", "09:00", "09:25", "09:30", "10:00", "12:00")


@dataclass(frozen=True)
class PointInTimeSnapshot:
    session_date: date
    snapshot_timestamp: datetime
    symbol: str
    contract: str
    feature_version: str
    features: Mapping[str, float | None]
    available_at: datetime
    availability_policy: str = "strict"


def build_point_in_time_snapshots(
    bars: Sequence[MarketBar], session_date: date, contract: str, feature_version: str,
    feature_fn: Callable[[Sequence[MarketBar], datetime], Mapping[str, float | None]] | None = None,
    availability_policy: Literal["strict", "event_time_reconstructed"] = "strict",
) -> tuple[PointInTimeSnapshot, ...]:
    """Build immutable snapshots from bars known by each snapshot timestamp.

    Bars at the snapshot minute are excluded because that minute is not closed
    until the following minute. Bars unavailable at the snapshot are excluded;
    an empty eligible input produces no snapshot rather than fabricated values.
    """
    if availability_policy not in ("strict", "event_time_reconstructed"):
        raise ValueError("unsupported availability policy")
    selected = tuple(sorted((bar for bar in bars if bar.symbol == contract and bar.timeframe == "1min"),
                            key=lambda bar: bar.timestamp))
    if not selected:
        return ()
    make_features = feature_fn or (lambda available, _timestamp: {"bars": float(len(available))})
    snapshots: list[PointInTimeSnapshot] = []
    for value in SNAPSHOT_TIMES_ET:
        hour, minute = (int(item) for item in value.split(":"))
        timestamp = datetime.combine(session_date, time(hour, minute), EASTERN)
        snapshot_utc = timestamp.astimezone(timezone.utc)
        eligible = tuple(bar for bar in selected if bar.timestamp < timestamp and (
            bar.available_at <= snapshot_utc if availability_policy == "strict"
            else bar.timestamp + timedelta(minutes=1) <= snapshot_utc
        ))
        if not eligible:
            continue
        features = {name: (None if number is None else float(number))
                    for name, number in make_features(eligible, timestamp.astimezone(timezone.utc)).items()}
        snapshots.append(PointInTimeSnapshot(
            session_date, timestamp, contract, contract, feature_version,
            features, (max(bar.available_at for bar in eligible) if availability_policy == "strict"
                       else max(bar.timestamp + timedelta(minutes=1) for bar in eligible)),
            availability_policy,
        ))
    return tuple(snapshots)


def market_feature_function(
    es_bars: Sequence[MarketBar], prior_high: float | None = None,
    prior_low: float | None = None,
    availability_policy: Literal["strict", "event_time_reconstructed"] = "strict",
) -> Callable[[Sequence[MarketBar], datetime], Mapping[str, float | None]]:
    """Return a timestamp-aware NQ feature function with supporting ES strength."""
    def build(nq_bars: Sequence[MarketBar], snapshot_timestamp: datetime) -> Mapping[str, float | None]:
        def visible(bar: MarketBar) -> bool:
            if bar.timestamp >= snapshot_timestamp:
                return False
            if availability_policy == "strict":
                return bar.available_at <= snapshot_timestamp
            if availability_policy == "event_time_reconstructed":
                return bar.timestamp + timedelta(minutes=1) <= snapshot_timestamp
            raise ValueError("unsupported availability policy")
        nq_visible = [bar for bar in nq_bars if visible(bar)]
        nq = technical_features(nq_visible, prior_high, prior_low)
        es = [bar for bar in es_bars if visible(bar)]
        if len(nq_visible) > 5 and len(es) > 5:
            nq_return = nq.get("return_5m")
            es_closes = [bar.close for bar in sorted(es, key=lambda item: item.timestamp)]
            es_return = (es_closes[-1] / es_closes[-6] - 1) if es_closes[-6] else None
            nq["nq_es_relative_strength"] = (nq_return - es_return
                                               if nq_return is not None and es_return is not None else None)
        return nq
    return build
