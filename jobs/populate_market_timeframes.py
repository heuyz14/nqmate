"""Persist deterministic candles derived from the canonical 1-minute history."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from nqmate_api.config import Settings
from nqmate_api.market.calculations import DERIVED_TIMEFRAMES, aggregate_bars
from nqmate_api.market.repository import SupabaseMarketRepository


EASTERN = ZoneInfo("America/New_York")
DEFAULT_TIMEFRAMES = ("5m", "15m", "1h", "2h", "4h", "1d")


def parse_timeframes(value: str) -> tuple[str, ...]:
    requested = tuple(item.strip() for item in value.split(",") if item.strip())
    invalid = sorted(set(requested) - set(DERIVED_TIMEFRAMES))
    if invalid:
        raise ValueError(f"Unsupported derived timeframe(s): {', '.join(invalid)}")
    if not requested:
        raise ValueError("At least one timeframe is required")
    return requested


def source_window(start: date, end: date) -> tuple[datetime, datetime]:
    """Cover the overnight before start through the regular close after end."""
    window_start = datetime.combine(start - timedelta(days=1), time(18), EASTERN)
    window_end = datetime.combine(end, time(16), EASTERN) + timedelta(minutes=1)
    return window_start.astimezone(timezone.utc), window_end.astimezone(timezone.utc)


def populate(start: date, end: date, timeframes: tuple[str, ...]) -> dict[str, int]:
    settings = Settings()
    repository = SupabaseMarketRepository.from_settings(settings)
    window_start, window_end = source_window(start, end)
    # Stored bars retain the raw active contract symbol (for example NQU6),
    # so do not filter this query to the product name NQ.
    stored = repository.get_bars(window_start, window_end)
    minute_bars = [bar for bar in stored if bar.timeframe == "1min"]
    if not minute_bars:
        return {timeframe: 0 for timeframe in timeframes}

    counts: dict[str, int] = {}
    for timeframe in timeframes:
        derived = aggregate_bars(minute_bars, timeframe)
        counts[timeframe] = repository.upsert_bars(derived)
        print(f"stored {counts[timeframe]} {timeframe} bars", flush=True)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate derived NQ candle horizons from stored minute bars")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--timeframes", default=",".join(DEFAULT_TIMEFRAMES))
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    try:
        timeframes = parse_timeframes(args.timeframes)
    except ValueError as exc:
        parser.error(str(exc))
    counts = populate(args.start, args.end, timeframes)
    print(f"market timeframe population complete: {counts}", flush=True)


if __name__ == "__main__":
    main()
