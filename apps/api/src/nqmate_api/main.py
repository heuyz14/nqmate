from datetime import date
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from nqmate_api.config import Settings
from nqmate_api.health import check_neo4j, check_supabase, health_payload
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository

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
