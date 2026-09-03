from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta, datetime, time
from zoneinfo import ZoneInfo

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.analogues.service import session_features
from nqmate_api.config import Settings
from nqmate_api.market.repository import SupabaseMarketRepository


async def populate(start: date, end: date) -> int:
    settings = Settings()
    market = SupabaseMarketRepository.from_settings(settings)
    analogue = SupabaseAnalogueRepository.from_settings(settings)
    count = 0
    day = start
    while day <= end:
        session = market.get_session(day)
        if session is not None:
            available_at = datetime.combine(day, time(9, 30), ZoneInfo("America/New_York"))
            analogue.upsert(HistoricalSession(day.isoformat(), session_features(session), available_at, {}))
            count += 1
        day += timedelta(days=1)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate pre-session historical analogue vectors")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(f"analogue vectors populated: {asyncio.run(populate(args.start, args.end))}", flush=True)


if __name__ == "__main__":
    main()
