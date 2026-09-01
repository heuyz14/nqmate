from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from typing import Iterable, Optional, Sequence
from zoneinfo import ZoneInfo

from nqmate_api.market.models import MarketBar, MarketContract, MarketSession

EASTERN = ZoneInfo("America/New_York")
OVERNIGHT_START = time(18, 0)
REGULAR_START = time(9, 30)
REGULAR_END = time(16, 0)
DERIVED_TIMEFRAMES = {"1h": timedelta(hours=1), "4h": timedelta(hours=4), "1d": timedelta(days=1)}


def _local_timestamp(bar: MarketBar) -> datetime:
    return bar.timestamp.astimezone(EASTERN)


def _bars_for_date(bars: Iterable[MarketBar], session_date: date) -> tuple[list[MarketBar], list[MarketBar]]:
    overnight: list[MarketBar] = []
    regular: list[MarketBar] = []
    overnight_start = datetime.combine(session_date - timedelta(days=1), OVERNIGHT_START, EASTERN)
    regular_start = datetime.combine(session_date, REGULAR_START, EASTERN)
    regular_end = datetime.combine(session_date, REGULAR_END, EASTERN)
    for bar in bars:
        timestamp = _local_timestamp(bar)
        if overnight_start <= timestamp < regular_start:
            overnight.append(bar)
        elif regular_start <= timestamp < regular_end:
            regular.append(bar)
    return sorted(overnight, key=lambda item: item.timestamp), sorted(regular, key=lambda item: item.timestamp)


def true_range(current: MarketBar, previous_close: Optional[float]) -> float:
    if previous_close is None:
        return current.high - current.low
    return max(current.high - current.low, abs(current.high - previous_close), abs(current.low - previous_close))


def has_complete_session_bars(bars: Iterable[MarketBar], session_date: date) -> bool:
    overnight, regular = _bars_for_date(bars, session_date)
    return bool(overnight and regular)


def aggregate_bars(bars: Iterable[MarketBar], timeframe: str) -> list[MarketBar]:
    """Aggregate canonical minute bars into deterministic UTC time buckets."""
    if timeframe not in DERIVED_TIMEFRAMES:
        raise ValueError(f"Unsupported derived timeframe: {timeframe}")
    interval = DERIVED_TIMEFRAMES[timeframe]
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    groups: dict[tuple[str, str, datetime], list[MarketBar]] = {}
    for bar in bars:
        timestamp = bar.timestamp.astimezone(timezone.utc)
        bucket = epoch + ((timestamp - epoch) // interval) * interval
        groups.setdefault((bar.symbol, bar.provider, bucket), []).append(bar)
    result: list[MarketBar] = []
    for (symbol, provider, bucket), items in sorted(groups.items(), key=lambda item: item[0][2]):
        ordered = sorted(items, key=lambda item: item.timestamp)
        result.append(MarketBar(
            symbol=symbol, timestamp=bucket, timeframe=timeframe,
            open=ordered[0].open, high=max(item.high for item in ordered),
            low=min(item.low for item in ordered), close=ordered[-1].close,
            volume=sum(item.volume for item in ordered), provider=provider,
            ingested_at=max(item.ingested_at for item in ordered),
            available_at=max(item.available_at for item in ordered),
        ))
    return result


def atr(bars: Sequence[MarketBar], period: int = 14) -> Optional[float]:
    if len(bars) < period:
        return None
    ranges: list[float] = []
    previous_close: Optional[float] = None
    for bar in bars:
        ranges.append(true_range(bar, previous_close))
        previous_close = bar.close
    return mean(ranges[-period:])


def build_market_session(
    bars: Iterable[MarketBar],
    session_date: date,
    contract: MarketContract,
    prior_session: Optional[MarketSession] = None,
) -> MarketSession:
    overnight, regular = _bars_for_date(bars, session_date)
    if not overnight:
        raise ValueError(f"No overnight bars for session {session_date}")
    if not regular:
        raise ValueError(f"No regular-session bars for session {session_date}")
    nq_open = regular[0].open
    nq_close = regular[-1].close
    prior_close = prior_session.nq_close if prior_session else None
    gap_points = nq_open - prior_close if prior_close is not None else None
    gap_pct = gap_points / prior_close if gap_points is not None and prior_close else None
    overnight_return = overnight[-1].close / overnight[0].open - 1 if overnight[0].open else None
    return MarketSession(
        session_date=session_date,
        nq_open=nq_open,
        nq_high=max(bar.high for bar in regular),
        nq_low=min(bar.low for bar in regular),
        nq_close=nq_close,
        overnight_open=overnight[0].open,
        overnight_high=max(bar.high for bar in overnight),
        overnight_low=min(bar.low for bar in overnight),
        overnight_close=overnight[-1].close,
        prior_day_high=prior_session.nq_high if prior_session else None,
        prior_day_low=prior_session.nq_low if prior_session else None,
        prior_day_close=prior_close,
        gap_points=gap_points,
        gap_pct=gap_pct,
        overnight_return=overnight_return,
        overnight_range=max(bar.high for bar in overnight) - min(bar.low for bar in overnight),
        atr_14=atr(regular),
        contract=contract,
    )
