"""Backfill paired NQ/ES raw minutes; emit weekly quality reports as JSON lines."""

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import date, datetime, timedelta
from typing import Callable

from postgrest.exceptions import APIError
from jobs.backfill_market_weeks import week_ranges
from jobs.ingest_market import trading_dates
from nqmate_api.config import Settings
from nqmate_api.market.calculations import EASTERN, build_market_session
from nqmate_api.market.models import ContractRollover, MarketContract
from nqmate_api.market.providers import MarketDataProvider, MassiveMarketDataProvider
from nqmate_api.market.quality import QUALITY_VERSION, audit_session_bars, session_window
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository


async def _backfill_day(
    day: date, provider: MarketDataProvider, repository: MarketRepository,
    previous: dict[str, MarketContract], *, reconstruct_nq: bool, reconstruct_es: bool,
) -> list[dict]:
    """Write one paired day; caller retries the whole idempotent day on API failure."""
    next_previous = dict(previous)
    rows: list[dict] = []
    for product in ("NQ", "ES"):
        prior = next_previous.get(product)
        if prior is None:
            prior_day = day - timedelta(days=1)
            while prior_day.weekday() >= 5:
                prior_day -= timedelta(days=1)
            prior = await provider.get_contract(product, prior_day)
        contract = prior
        if contract.expiration is None or day >= contract.expiration:
            contract = await provider.get_contract(product, day)
        if (prior.product != product or contract.product != product
                or not contract.raw_contract_symbol.startswith(product)
                or (contract.expiration is not None and contract.expiration <= day)):
            raise ValueError("Unexpected or expired contract metadata")
        repository.upsert_contract(contract)
        if prior.raw_contract_symbol != contract.raw_contract_symbol:
            repository.upsert_rollover(ContractRollover(
                product, prior.raw_contract_symbol, contract.raw_contract_symbol, day, "massive",
            ))
        next_previous[product] = contract
        bars = await provider.get_bars(contract.raw_contract_symbol, day - timedelta(days=1), day)
        quality = audit_session_bars(bars, day, contract)
        stored = 0
        if not (set(quality.issue_counts) - {"missing_minutes"}):
            window_start, window_end = session_window(day)
            stored = repository.upsert_bars([
                bar for bar in bars if bar.timeframe == "1min" and window_start <= bar.timestamp < window_end
            ])
        reconstructed = False
        if quality.eligible and ((product == "NQ" and reconstruct_nq) or (product == "ES" and reconstruct_es)):
            prior_session = repository.get_previous_session(day, product)
            if prior_session is not None and prior_session.contract.raw_contract_symbol != contract.raw_contract_symbol:
                prior_session = None
            repository.upsert_session(build_market_session(
                [bar for bar in bars if bar.timeframe == "1min"], day, contract, prior_session,
            ))
            reconstructed = True
        rows.append({**asdict(quality), "product": product, "eligible": quality.eligible,
                     "stored_minutes": stored, "session_reconstructed": reconstructed})
    previous.update(next_previous)
    return rows


async def backfill(
    start: date, end: date, provider: MarketDataProvider, repository: MarketRepository,
    emit: Callable[[dict], None] | None = None,
    *, reconstruct_nq: bool = False, reconstruct_es: bool = False, retries: int = 2,
    retry_delay_seconds: float = 5.0,
) -> list[dict]:
    if end < start:
        raise ValueError("end must be on or after start")
    if retries < 0:
        raise ValueError("retries cannot be negative")
    previous: dict[str, MarketContract] = {}
    reports: list[dict] = []
    for week_start, week_end in week_ranges(start, end):
        rows: list[dict] = []
        for day in trading_dates(week_start, week_end):
            for attempt in range(retries + 1):
                try:
                    rows.extend(await _backfill_day(
                        day, provider, repository, previous,
                        reconstruct_nq=reconstruct_nq, reconstruct_es=reconstruct_es,
                    ))
                    break
                except APIError:
                    if attempt == retries:
                        raise
                    await asyncio.sleep(retry_delay_seconds * (attempt + 1))
        report = {"start_date": week_start, "end_date": week_end,
                  "contract_policy": "equity-full-session-expiry-exclusive-v2",
                  "quality_version": QUALITY_VERSION, "sessions": rows,
                  "eligible_product_sessions": sum(row["eligible"] for row in rows),
                  "quarantined_product_sessions": sum(not row["eligible"] for row in rows)}
        reports.append(report)
        if emit:
            emit(report)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--reconstruct-nq-sessions", action="store_true",
                        help="Persist NQ sessions only when full canonical minute coverage passes")
    parser.add_argument("--reconstruct-es-sessions", action="store_true",
                        help="Persist supporting ES sessions; requires migration 022")
    parser.add_argument("--retries", type=int, default=2,
                        help="Retry each idempotent paired day after transient database API errors")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    if args.end >= datetime.now(EASTERN).date():
        parser.error("--end must be before today; this job processes historical sessions")
    if args.retries < 0:
        parser.error("--retries cannot be negative")
    settings = Settings()
    provider = MassiveMarketDataProvider(settings.massive_api_key)
    repository = SupabaseMarketRepository.from_settings(settings)
    reports = asyncio.run(backfill(
        args.start, args.end, provider, repository,
        lambda report: print(json.dumps(report, default=lambda value: value.isoformat()), flush=True),
        reconstruct_nq=args.reconstruct_nq_sessions,
        reconstruct_es=args.reconstruct_es_sessions,
        retries=args.retries,
    ))
    return int(not any(report["sessions"] for report in reports)
               or any(report["quarantined_product_sessions"] for report in reports))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # HTTP exception strings can contain the credential-bearing request URL.
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__}), flush=True)
        raise SystemExit(2) from None
