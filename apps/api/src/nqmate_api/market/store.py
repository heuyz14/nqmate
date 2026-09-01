from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Iterable

from nqmate_api.market.models import MarketBar, MarketContract, MarketSession


class MarketBarStore:
    """Small deterministic store for Phase 1 tests and local development."""

    def __init__(self) -> None:
        self._bars: dict[tuple[str, datetime, str, str], MarketBar] = {}
        self._sessions: dict[date, MarketSession] = {}

    def add_bars(self, bars: Iterable[MarketBar]) -> int:
        added = 0
        for bar in bars:
            key = (bar.symbol, bar.timestamp, bar.timeframe, bar.provider)
            if key not in self._bars:
                self._bars[key] = bar
                added += 1
        return added

    def bars_between(self, start: datetime, end: datetime, symbol: str | None = None) -> list[MarketBar]:
        return sorted(
            (bar for bar in self._bars.values() if start <= bar.timestamp < end and (symbol is None or bar.symbol == symbol)),
            key=lambda bar: bar.timestamp,
        )

    def save_session(self, session: MarketSession) -> None:
        self._sessions[session.session_date] = session

    def get_session(self, session_date: date) -> MarketSession | None:
        return self._sessions.get(session_date)
