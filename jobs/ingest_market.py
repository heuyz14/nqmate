from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta

from nqmate_api.config import Settings
from nqmate_api.market.providers import MassiveMarketDataProvider
from nqmate_api.market.repository import SupabaseMarketRepository
from nqmate_api.market.service import ingest_session
from nqmate_api.market.models import ContractRollover, MarketContract


def trading_dates(start: date, end: date) -> list[date]:
    dates: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            dates.append(current)
        current += timedelta(days=1)
    return dates


async def run(start: date, end: date) -> int:
    settings = Settings()
    if not settings.massive_api_key:
        raise RuntimeError("MASSIVE_API_KEY is required")
    provider = MassiveMarketDataProvider(settings.massive_api_key)
    repository = SupabaseMarketRepository.from_settings(settings)
    processed = 0
    previous_contract: MarketContract | None = None
    for session_date in trading_dates(start, end):
        contract = await provider.get_contract("NQ", session_date)
        if previous_contract and previous_contract.raw_contract_symbol != contract.raw_contract_symbol:
            repository.upsert_rollover(ContractRollover(
                product=contract.product,
                from_contract=previous_contract.raw_contract_symbol,
                to_contract=contract.raw_contract_symbol,
                roll_date=session_date,
                provider="massive",
            ))
        await ingest_session(provider, repository, session_date, contract)
        previous_contract = contract
        processed += 1
        print(f"ingested {session_date.isoformat()} {contract.raw_contract_symbol}")
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill NQ minute bars and market sessions")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(f"processed {asyncio.run(run(args.start, args.end))} trading sessions")


if __name__ == "__main__":
    main()
