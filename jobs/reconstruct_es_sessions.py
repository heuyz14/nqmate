"""Reconstruct supporting ES sessions from stored minutes and saved backfill reports."""

import argparse
import json
from datetime import date
from pathlib import Path

from nqmate_api.config import Settings
from nqmate_api.market.calculations import build_market_session
from nqmate_api.market.models import MarketContract
from nqmate_api.market.quality import audit_session_bars, session_window
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository


def reconstruct(repository: MarketRepository, day: date, contract: MarketContract) -> dict:
    if contract.product != "ES":
        raise ValueError("Supporting reconstruction requires an ES contract")
    start, end = session_window(day)
    bars = [bar for bar in repository.get_bars(start, end, symbol=contract.raw_contract_symbol)
            if bar.timeframe == "1min"]
    quality = audit_session_bars(bars, day, contract)
    if quality.eligible:
        prior = repository.get_previous_session(day, "ES")
        if prior and prior.contract.raw_contract_symbol != contract.raw_contract_symbol:
            prior = None
        repository.upsert_session(build_market_session(bars, day, contract, prior))
    return {"session_date": day.isoformat(), "product": "ES", "contract": contract.raw_contract_symbol,
            "session_reconstructed": quality.eligible, "issue_counts": quality.issue_counts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="+", help="Original and recovery JSONL files in attempt order")
    args = parser.parse_args()
    latest = {}
    for path in args.reports:
        with path.open() as source:
            for line in source:
                if not line.strip():
                    continue
                for row in json.loads(line).get("sessions", []):
                    if row["product"] == "ES":
                        latest[date.fromisoformat(row["session_date"])] = row["contract"]
    repo = SupabaseMarketRepository.from_settings(Settings())
    # Readiness check before processing or writing anything.
    repo.client.table("market_supporting_sessions").select("session_date").limit(1).execute()
    for day, symbol in sorted(latest.items()):
        response = repo.client.table("market_contracts").select(
            "product,raw_contract_symbol,continuous_symbol,expiration,roll_date"
        ).eq("product", "ES").eq("raw_contract_symbol", symbol).single().execute()
        metadata = response.data
        for field in ("expiration", "roll_date"):
            metadata[field] = date.fromisoformat(metadata[field]) if metadata.get(field) else None
        print(json.dumps(reconstruct(repo, day, MarketContract(**metadata))), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__}), flush=True)
        raise SystemExit(2) from None
