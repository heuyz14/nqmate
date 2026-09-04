from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from nqmate_api.config import Settings
from nqmate_api.market.repository import SupabaseMarketRepository
from nqmate_api.strategies.models import Strategy
from nqmate_api.strategies.repository import SupabaseStrategyRepository
from nqmate_api.strategies.setups import detect_setup
from nqmate_api.strategies.setups_repository import SupabaseSetupRepository


async def detect_setups(start: date, end: date) -> int:
    settings = Settings()
    market = SupabaseMarketRepository.from_settings(settings)
    strategies = SupabaseStrategyRepository.from_settings(settings).list(active=True)
    setups = SupabaseSetupRepository.from_settings(settings)
    count = 0
    eastern = ZoneInfo("America/New_York")
    for row in strategies:
        strategy = Strategy(
            row["name"], row.get("description") or "", tuple(row.get("allowed_regimes") or ()),
            tuple(row.get("required_conditions") or ()), tuple(row.get("confirmation_conditions") or ()),
            tuple(row.get("invalidation_conditions") or ()), row["entry_logic"], row["target_logic"],
            row["stop_logic"], bool(row.get("active", True)),
        )
        day = start
        while day <= end:
            session = market.get_session(day)
            if session is not None:
                bars = market.get_bars(
                    datetime.combine(day - timedelta(days=1), time(18), eastern).astimezone(timezone.utc),
                    datetime.combine(day, time(16), eastern).astimezone(timezone.utc),
                )
                occurrence = detect_setup(str(row["id"]), strategy, session, bars)
                if occurrence is not None:
                    setups.upsert(occurrence)
                    count += 1
            day += timedelta(days=1)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect and persist structured strategy setups")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    import asyncio
    print(f"strategy setups detected: {asyncio.run(detect_setups(args.start, args.end))}", flush=True)


if __name__ == "__main__":
    main()
