from __future__ import annotations

from datetime import date, timedelta

from nqmate_api.market.calculations import build_market_session
from nqmate_api.market.models import MarketContract, MarketSession
from nqmate_api.market.providers import MarketDataProvider
from nqmate_api.market.repository import MarketRepository


async def ingest_session(
    provider: MarketDataProvider,
    repository: MarketRepository,
    session_date: date,
    contract: MarketContract,
) -> MarketSession:
    bars = await provider.get_bars(
        contract.raw_contract_symbol,
        session_date - timedelta(days=1),
        session_date,
    )
    repository.upsert_bars(bars)
    prior_session = repository.get_session(session_date - timedelta(days=1))
    session = build_market_session(bars, session_date, contract, prior_session)
    repository.upsert_session(session)
    return session
