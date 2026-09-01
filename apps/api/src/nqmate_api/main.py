from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from nqmate_api.config import Settings
from nqmate_api.health import check_neo4j, check_supabase, health_payload
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository
from nqmate_api.market.calculations import aggregate_bars
from nqmate_api.market.calculations import weekly_opening_gaps

app = FastAPI(title="NQmate API", version="0.1.0")


@lru_cache(maxsize=1)
def get_market_repository() -> MarketRepository:
    return SupabaseMarketRepository.from_settings(Settings())


@app.get("/health", tags=["health"])
async def health() -> dict[str, object]:
    settings = Settings()
    return health_payload(
        database=check_supabase(settings),
        graph=check_neo4j(settings),
    )


@app.get("/api/v1/market/nq/session/{session_date}", tags=["market"])
async def get_nq_session(session_date: date, repository: MarketRepository = Depends(get_market_repository)) -> dict[str, object]:
    session = repository.get_session(session_date)
    if session is None:
        raise HTTPException(status_code=404, detail="Market session not found")
    return {
        "session_date": session.session_date.isoformat(),
        "nq_open": session.nq_open,
        "nq_high": session.nq_high,
        "nq_low": session.nq_low,
        "nq_close": session.nq_close,
        "overnight_open": session.overnight_open,
        "overnight_high": session.overnight_high,
        "overnight_low": session.overnight_low,
        "overnight_close": session.overnight_close,
        "prior_day_high": session.prior_day_high,
        "prior_day_low": session.prior_day_low,
        "prior_day_close": session.prior_day_close,
        "gap_points": session.gap_points,
        "gap_pct": session.gap_pct,
        "overnight_return": session.overnight_return,
        "overnight_range": session.overnight_range,
        "atr_14": session.atr_14,
        "contract": {
            "product": session.contract.product,
            "raw_contract_symbol": session.contract.raw_contract_symbol,
            "continuous_symbol": session.contract.continuous_symbol,
            "expiration": session.contract.expiration.isoformat() if session.contract.expiration else None,
            "roll_date": session.contract.roll_date.isoformat() if session.contract.roll_date else None,
        },
    }


@app.get("/api/v1/market/nq/bars", tags=["market"])
async def get_nq_bars(
    start: date,
    end: date,
    timeframe: str = "1min",
    repository: MarketRepository = Depends(get_market_repository),
) -> dict[str, object]:
    if end <= start:
        raise HTTPException(status_code=422, detail="end must be after start")
    if timeframe not in {"1min", "1h", "4h", "1d"}:
        raise HTTPException(status_code=422, detail="timeframe must be 1min, 1h, 4h, or 1d")
    bars = repository.get_bars(
        datetime.combine(start, time.min, timezone.utc),
        datetime.combine(end + timedelta(days=1), time.min, timezone.utc),
    )
    output_bars = bars if timeframe == "1min" else aggregate_bars(bars, timeframe)
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timeframe": timeframe,
        "bars": [
            {"timestamp": bar.timestamp.isoformat(), "open": bar.open, "high": bar.high,
             "low": bar.low, "close": bar.close, "volume": bar.volume,
             "symbol": bar.symbol, "provider": bar.provider}
            for bar in output_bars
        ],
    }


@app.get("/api/v1/market/nq/levels", tags=["market"])
async def get_nq_levels(
    session_date: date,
    repository: MarketRepository = Depends(get_market_repository),
) -> dict[str, object]:
    session = repository.get_session(session_date)
    if session is None:
        raise HTTPException(status_code=404, detail="Market session not found")
    return {
        "session_date": session_date.isoformat(),
        "pdh": session.prior_day_high,
        "pdl": session.prior_day_low,
        "pdc": session.prior_day_close,
        "onh": session.overnight_high,
        "onl": session.overnight_low,
        "overnight_midpoint": (session.overnight_high + session.overnight_low) / 2,
    }


@app.get("/api/v1/market/nq/weekly-gaps", tags=["market"])
async def get_nq_weekly_gaps(
    start: date,
    end: date,
    repository: MarketRepository = Depends(get_market_repository),
) -> dict[str, object]:
    if end < start:
        raise HTTPException(status_code=422, detail="end must be on or after start")
    sessions = []
    current = start
    while current <= end:
        session = repository.get_session(current)
        if session is not None:
            sessions.append(session)
        current += timedelta(days=1)
    gaps = weekly_opening_gaps(sessions)
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "gaps": [
            {"week_start": gap.week_start.isoformat(), "session_date": gap.session_date.isoformat(),
             "opening_price": gap.opening_price, "prior_close": gap.prior_close,
             "gap_points": gap.gap_points, "gap_pct": gap.gap_pct,
             "contract": gap.contract.raw_contract_symbol}
            for gap in gaps
        ],
    }
