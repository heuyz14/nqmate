from __future__ import annotations

import argparse
from datetime import date, timedelta

from nqmate_api.config import Settings
from nqmate_api.graph.repository import GraphRepository, Neo4jGraphRepository
from nqmate_api.graph.regimes import classify_market_regime
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository


def sync_sessions(start: date, end: date, market: MarketRepository, graph: GraphRepository) -> int:
    graph.ensure_schema()
    count = 0
    day = start
    while day <= end:
        session = market.get_session(day)
        if session is not None:
            graph.sync_session(day.isoformat(), classify_market_regime(session))
            count += 1
        day += timedelta(days=1)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync semantic market sessions and regimes to Neo4j")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    settings = Settings()
    market = SupabaseMarketRepository.from_settings(settings)
    graph = Neo4jGraphRepository.from_settings(settings)
    try:
        print(f"graph sessions synced: {sync_sessions(args.start, args.end, market, graph)}", flush=True)
    finally:
        graph.close()


if __name__ == "__main__":
    main()
