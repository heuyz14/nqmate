"""Deterministic historical inputs for the PB Blake / ICT evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from nqmate_api.market.models import MarketBar
from nqmate_api.strategies.pb_blake import Inversion, LiquidityEvent


@dataclass(frozen=True)
class FairValueGap:
    timeframe: str
    direction: str
    lower: float
    upper: float
    formed_at: datetime


def detect_fvgs(bars: Sequence[MarketBar], timeframe: str) -> tuple[FairValueGap, ...]:
    """Find three-bar gaps using only bars available at their own timestamp."""
    ordered = sorted(
        (bar for bar in bars if bar.timeframe == timeframe and bar.available_at <= bar.timestamp),
        key=lambda bar: bar.timestamp,
    )
    gaps: list[FairValueGap] = []
    for first, _, third in zip(ordered, ordered[1:], ordered[2:]):
        if first.high < third.low:
            gaps.append(FairValueGap(timeframe, "bullish", first.high, third.low, third.timestamp))
        elif first.low > third.high:
            gaps.append(FairValueGap(timeframe, "bearish", third.high, first.low, third.timestamp))
    return tuple(gaps)


def detect_post_liquidity_inversions(
    bars: Sequence[MarketBar], timeframe: str, liquidity: LiquidityEvent
) -> tuple[Inversion, ...]:
    """Return the first close-through inversion for each post-event FVG.

    A bearish FVG becomes a long inversion after a close above its upper bound;
    a bullish FVG becomes a short inversion after a close below its lower bound.
    """
    ordered = sorted(
        (bar for bar in bars if bar.timeframe == timeframe and bar.available_at <= bar.timestamp),
        key=lambda bar: bar.timestamp,
    )
    result: list[Inversion] = []
    for gap in detect_fvgs(ordered, timeframe):
        if gap.formed_at <= liquidity.swept_at:
            continue
        after_gap = (bar for bar in ordered if bar.timestamp > gap.formed_at)
        confirmation = next(
            (
                bar for bar in after_gap
                if (gap.direction == "bearish" and bar.close > gap.upper)
                or (gap.direction == "bullish" and bar.close < gap.lower)
            ),
            None,
        )
        if confirmation is None:
            continue
        result.append(Inversion(
            timeframe=timeframe,
            direction="LONG" if gap.direction == "bearish" else "SHORT",
            lower=gap.lower,
            upper=gap.upper,
            confirmed_at=confirmation.timestamp,
        ))
    return tuple(result)
