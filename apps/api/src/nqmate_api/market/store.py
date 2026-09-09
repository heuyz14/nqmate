from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Iterable

from nqmate_api.market.models import ContractRollover, MarketBar, MarketContract, MarketSession


class MarketBarStore:
    """Small deterministic store for Phase 1 tests and local development."""

    def __init__(self) -> None:
        self._bars: dict[tuple[str, datetime, str, str], MarketBar] = {}
        self._sessions: dict[tuple[str, date], MarketSession] = {}
        self._rollovers: dict[tuple[str, str, str], ContractRollover] = {}

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

    def get_bars(self, start: datetime, end: datetime, symbol: str | None = None) -> list[MarketBar]:
        bars = self.bars_between(start, end, symbol)
        return bars if symbol else [bar for bar in bars if bar.symbol.startswith("NQ")]

    def save_session(self, session: MarketSession) -> None:
        from nqmate_api.market.repository import session_table
        session_table(session.contract.product)
        self._sessions[session.contract.product, session.session_date] = session

    def upsert_bars(self, bars: Iterable[MarketBar]) -> int:
        return self.add_bars(bars)

    def upsert_contract(self, contract: MarketContract) -> None:
        return None

    def upsert_rollover(self, rollover: ContractRollover) -> None:
        self._rollovers[(rollover.product, rollover.from_contract, rollover.to_contract)] = rollover

    def upsert_session(self, session: MarketSession) -> None:
        self.save_session(session)

    def get_session(self, session_date: date, product: str = "NQ") -> MarketSession | None:
        from nqmate_api.market.repository import session_table
        session_table(product)
        return self._sessions.get((product, session_date))

    def get_previous_session(self, session_date: date, product: str = "NQ") -> MarketSession | None:
        from nqmate_api.market.repository import session_table
        session_table(product)
        prior_dates = [day for p, day in self._sessions if p == product and day < session_date]
        return self._sessions[product, max(prior_dates)] if prior_dates else None
