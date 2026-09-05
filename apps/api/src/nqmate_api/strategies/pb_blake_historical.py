"""Build point-in-time PB Blake evidence from stored historical candles."""

from __future__ import annotations

from datetime import datetime, time
from typing import Sequence

from nqmate_api.market.calculations import EASTERN, REGULAR_END, REGULAR_START
from nqmate_api.market.models import MarketBar, MarketSession
from nqmate_api.strategies.pb_blake import HtfContext, Inversion, LiquidityEvent
from nqmate_api.strategies.pb_blake_data import detect_post_liquidity_inversions


def _regular_bars(session: MarketSession, bars: Sequence[MarketBar], analyzed_at: datetime) -> list[MarketBar]:
    start = datetime.combine(session.session_date, REGULAR_START, EASTERN).astimezone(analyzed_at.tzinfo)
    end = datetime.combine(session.session_date, REGULAR_END, EASTERN).astimezone(analyzed_at.tzinfo)
    return sorted((bar for bar in bars if bar.timeframe == "1m" and start <= bar.timestamp < end and bar.timestamp <= analyzed_at), key=lambda item: item.timestamp)


def _contexts(bars: Sequence[MarketBar], analyzed_at: datetime) -> tuple[HtfContext, ...]:
    result: list[HtfContext] = []
    for timeframe in ("1d", "4h"):
        candidates = sorted((bar for bar in bars if bar.timeframe == timeframe and bar.timestamp <= analyzed_at), key=lambda item: item.timestamp)
        if candidates:
            latest = candidates[-1]
            result.append(HtfContext(timeframe, "bullish" if latest.close >= latest.open else "bearish", True))
    return tuple(result)


def _liquidity(session: MarketSession, bars: Sequence[MarketBar], analyzed_at: datetime) -> LiquidityEvent | None:
    for bar in _regular_bars(session, bars, analyzed_at):
        if bar.high >= session.overnight_high:
            return LiquidityEvent("ONH", session.overnight_high, bar.timestamp)
        if bar.low <= session.overnight_low:
            return LiquidityEvent("ONL", session.overnight_low, bar.timestamp)
    return None


def build_pb_inputs(session: MarketSession, bars: Sequence[MarketBar], analyzed_at: datetime) -> dict[str, object]:
    """Return deterministic assessment inputs using bars available at ``analyzed_at`` only."""
    liquidity = _liquidity(session, bars, analyzed_at)
    inversions: list[Inversion] = []
    if liquidity is not None:
        for timeframe in ("1m", "2m", "3m", "5m"):
            inversions.extend(detect_post_liquidity_inversions(bars, timeframe, liquidity))
    eligible = [item for item in inversions if liquidity and liquidity.swept_at < item.confirmed_at <= analyzed_at]
    entry = stop = None
    targets: list[float] = []
    if eligible and liquidity is not None:
        selected = max(eligible, key=lambda item: {"1m": 1, "2m": 2, "3m": 3, "5m": 5}[item.timeframe])
        entry = round((selected.lower + selected.upper) / 2, 2)
        leg = [bar for bar in _regular_bars(session, bars, analyzed_at) if bar.timestamp >= liquidity.swept_at and bar.timestamp <= selected.confirmed_at]
        if selected.direction == "LONG":
            stop = round(min((bar.low for bar in leg), default=liquidity.price) - 0.25, 2)
            if session.overnight_high > entry:
                targets = [session.overnight_high]
        else:
            stop = round(max((bar.high for bar in leg), default=liquidity.price) + 0.25, 2)
            if session.overnight_low < entry:
                targets = [session.overnight_low]
    return {"contexts": _contexts(bars, analyzed_at), "liquidity": liquidity, "inversions": tuple(inversions), "entry": entry, "stop": stop, "targets": tuple(targets)}
