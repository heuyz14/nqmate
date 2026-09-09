"""Populate immutable NQ-primary feature snapshots with optional ES context."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal, Sequence
from zoneinfo import ZoneInfo

from nqmate_api.config import Settings
from nqmate_api.market.models import MarketBar, MarketContract
from nqmate_api.market.repository import SupabaseMarketRepository
from nqmate_api.market.snapshots import build_point_in_time_snapshots, market_feature_function
from nqmate_api.ml.models import SessionFeatureSnapshot
from nqmate_api.ml.repository import SupabaseMlRepository

EASTERN = ZoneInfo("America/New_York")
FEATURE_VERSION = "market-features-v2.1"
AvailabilityPolicy = Literal["strict", "event_time_reconstructed"]


def build_session_snapshots(
    nq_bars: Sequence[MarketBar], es_bars: Sequence[MarketBar], session_date: date,
    contract: MarketContract, availability_policy: AvailabilityPolicy,
) -> tuple[SessionFeatureSnapshot, ...]:
    features = market_feature_function(es_bars, availability_policy=availability_policy)
    built = build_point_in_time_snapshots(
        nq_bars, session_date, contract.raw_contract_symbol, FEATURE_VERSION,
        features, availability_policy,
    )
    return tuple(SessionFeatureSnapshot(
        item.session_date, item.snapshot_timestamp, item.symbol, item.contract,
        item.feature_version, dict(item.features), item.available_at, item.availability_policy,
    ) for item in built)


def populate(start: date, end: date, availability_policy: AvailabilityPolicy) -> int:
    settings = Settings()
    market = SupabaseMarketRepository.from_settings(settings)
    ml = SupabaseMlRepository.from_settings(settings)
    count = 0
    day = start
    while day <= end:
        session = market.get_session(day, "NQ")
        if session is not None:
            window_start = datetime.combine(day - timedelta(days=1), time(18), EASTERN).astimezone(timezone.utc)
            window_end = datetime.combine(day, time(16), EASTERN).astimezone(timezone.utc)
            nq_bars = market.get_bars(window_start, window_end, symbol=session.contract.raw_contract_symbol)
            es_session = market.get_session(day, "ES")
            es_bars = market.get_bars(window_start, window_end, symbol=es_session.contract.raw_contract_symbol) if es_session else ()
            for snapshot in build_session_snapshots(nq_bars, es_bars, day, session.contract, availability_policy):
                ml.create_snapshot(snapshot)
                count += 1
        day += timedelta(days=1)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--availability-policy", choices=("strict", "event_time_reconstructed"),
                        default="strict")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(populate(args.start, args.end, args.availability_policy), flush=True)


if __name__ == "__main__":
    main()
