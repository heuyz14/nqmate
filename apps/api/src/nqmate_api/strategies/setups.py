from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Sequence

from nqmate_api.market.calculations import EASTERN
from nqmate_api.market.models import MarketBar, MarketSession
from nqmate_api.strategies.models import Strategy


@dataclass(frozen=True)
class SetupOccurrence:
    strategy_id: str
    session_date: str
    trigger_at: datetime
    conditions: tuple[str, ...]


def detect_setup(strategy_id: str, strategy: Strategy, session: MarketSession, bars: Sequence[MarketBar]) -> SetupOccurrence | None:
    regular_start = datetime.combine(session.session_date, time(9, 30), EASTERN).astimezone(timezone.utc)
    regular_end = datetime.combine(session.session_date, time(16), EASTERN).astimezone(timezone.utc)
    regular = sorted((bar for bar in bars if regular_start <= bar.timestamp < regular_end), key=lambda bar: bar.timestamp)
    if not regular:
        return None
    midpoint = (session.overnight_high + session.overnight_low) / 2
    triggers: list[datetime] = []
    for condition in strategy.required_conditions:
        if condition == "price_above_overnight_midpoint":
            match = next((bar for bar in regular if bar.close > midpoint), None)
        elif condition == "onh_break":
            match = next((bar for bar in regular if bar.high >= session.overnight_high), None)
        elif condition == "onl_break":
            match = next((bar for bar in regular if bar.low <= session.overnight_low), None)
        else:
            return None
        if match is None:
            return None
        triggers.append(match.timestamp)
    return SetupOccurrence(strategy_id, session.session_date.isoformat(), max(triggers, default=regular[0].timestamp), strategy.required_conditions)
