from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

from jobs.ingest_market import run

EASTERN = ZoneInfo("America/New_York")


def session_date_today() -> date:
    return datetime.now(EASTERN).date()


async def ingest_daily(session_date: date) -> int:
    processed = await run(session_date, session_date)
    print(f"daily market update completed: {session_date.isoformat()} ({processed} session(s))", flush=True)
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the completed NQ session for today")
    parser.add_argument("--session-date", type=date.fromisoformat, default=session_date_today())
    args = parser.parse_args()
    asyncio.run(ingest_daily(args.session_date))


if __name__ == "__main__":
    main()
