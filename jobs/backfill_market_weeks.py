from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta

from jobs.ingest_market import run


def week_ranges(start: date, end: date) -> list[tuple[date, date]]:
    """Return inclusive Monday-Sunday ranges clipped to the requested dates."""
    ranges: list[tuple[date, date]] = []
    current = start
    while current <= end:
        days_until_sunday = 6 - current.weekday()
        chunk_end = min(current + timedelta(days=days_until_sunday), end)
        ranges.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return ranges


async def backfill(start: date, end: date) -> int:
    total = 0
    for week_start, week_end in week_ranges(start, end):
        processed = await run(week_start, week_end)
        total += processed
        print(
            f"completed {week_start.isoformat()} through {week_end.isoformat()} "
            f"({processed} trading sessions)"
        )
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NQ historical backfill in resumable weekly batches")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    total = asyncio.run(backfill(args.start, args.end))
    print(f"completed {total} trading sessions total")


if __name__ == "__main__":
    main()
