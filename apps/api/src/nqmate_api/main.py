from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from nqmate_api.config import Settings
from nqmate_api.health import check_neo4j, check_supabase, health_payload
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository
from nqmate_api.market.calculations import EASTERN, REGULAR_END, REGULAR_START, aggregate_bars, technical_features
from nqmate_api.market.calculations import weekly_opening_gaps
from nqmate_api.news.repository import NewsRepository, SupabaseNewsRepository
from nqmate_api.news.service import economic_surprise, pre_event_risk

app = FastAPI(title="NQmate API", version="0.1.0")


@lru_cache(maxsize=1)
def get_market_repository() -> MarketRepository:
    return SupabaseMarketRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_news_repository() -> NewsRepository:
    return SupabaseNewsRepository.from_settings(Settings())


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


@app.get("/api/v1/market/nq/features", tags=["market"])
async def get_nq_features(
    session_date: date,
    repository: MarketRepository = Depends(get_market_repository),
) -> dict[str, object]:
    session = repository.get_session(session_date)
    if session is None:
        raise HTTPException(status_code=404, detail="Market session not found")
    bars = repository.get_bars(
        datetime.combine(session_date, REGULAR_START, EASTERN).astimezone(timezone.utc),
        datetime.combine(session_date, REGULAR_END, EASTERN).astimezone(timezone.utc),
    )
    return {"session_date": session_date.isoformat(), "features": technical_features(
        bars, session.prior_day_high, session.prior_day_low,
    )}


@app.get("/api/v1/news", tags=["news"])
async def get_news(
    limit: int = 50,
    start: datetime | None = None,
    end: datetime | None = None,
    repository: NewsRepository = Depends(get_news_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    end = end or datetime.now(timezone.utc)
    start = start or end - timedelta(days=14)
    if end < start:
        raise HTTPException(status_code=422, detail="end must be on or after start")
    return {"start": start.isoformat(), "end": end.isoformat(), "events": repository.list_events(limit=limit, start=start.isoformat(), end=end.isoformat())}


@app.get("/api/v1/news/high-impact", tags=["news"])
async def get_high_impact_news(
    limit: int = 50,
    start: datetime | None = None,
    end: datetime | None = None,
    repository: NewsRepository = Depends(get_news_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    end = end or datetime.now(timezone.utc)
    start = start or end - timedelta(days=14)
    if end < start:
        raise HTTPException(status_code=422, detail="end must be on or after start")
    return {"start": start.isoformat(), "end": end.isoformat(), "events": repository.list_events(high_impact_only=True, limit=limit, start=start.isoformat(), end=end.isoformat())}


@app.get("/api/v1/macro/calendar", tags=["macro"])
async def get_macro_calendar(
    start: datetime,
    end: datetime,
    high_impact_only: bool = False,
    limit: int = 100,
    repository: NewsRepository = Depends(get_news_repository),
) -> dict[str, object]:
    if end < start:
        raise HTTPException(status_code=422, detail="end must be on or after start")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return {"start": start.isoformat(), "end": end.isoformat(), "events": repository.list_calendar_events(
        start.isoformat(), end.isoformat(), high_impact_only, limit,
    )}


@app.get("/api/v1/macro/upcoming", tags=["macro"])
async def get_upcoming_macro_event(
    repository: NewsRepository = Depends(get_news_repository),
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    events = repository.list_calendar_events(
        now.isoformat(), (now + timedelta(days=14)).isoformat(), True, 100,
    )
    if not events:
        return {"event": None, "minutes_until_event": None, "risk_state": None}

    event = events[0]
    scheduled_at = datetime.fromisoformat(str(event["scheduled_at"]).replace("Z", "+00:00"))
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    minutes_until = (scheduled_at - now).total_seconds() / 60
    result = dict(event)
    result["surprise"] = economic_surprise(event.get("actual"), event.get("forecast"))
    result["minutes_until_event"] = round(minutes_until, 2)
    return {
        "event": result,
        "minutes_until_event": round(minutes_until, 2),
        "risk_state": pre_event_risk(scheduled_at, now),
    }
