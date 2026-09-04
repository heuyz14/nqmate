from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from nqmate_api.config import Settings
from nqmate_api.health import check_neo4j, check_supabase, health_payload
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository
from nqmate_api.market.calculations import EASTERN, REGULAR_END, REGULAR_START, aggregate_bars, technical_features
from nqmate_api.market.calculations import weekly_opening_gaps
from nqmate_api.news.repository import NewsRepository, SupabaseNewsRepository
from nqmate_api.news.service import economic_surprise, pre_event_risk
from nqmate_api.macro.repository import MacroRepository, SupabaseMacroRepository
from nqmate_api.bias.models import BiasSnapshot, BiasResult
from nqmate_api.bias.llm import GeminiBiasExplainer, LLMProvider
from nqmate_api.bias.repository import BiasRepository, SupabaseBiasRepository
from nqmate_api.bias.evaluation import confidence_calibration, feature_drift, summarize_prediction_outcomes
from nqmate_api.bias.service import score_bias
from nqmate_api.analogues.repository import AnalogueRepository, SupabaseAnalogueRepository
from nqmate_api.analogues.service import rank_analogues, session_features
from nqmate_api.graph.repository import GraphRepository, Neo4jGraphRepository
from nqmate_api.strategies.models import Strategy
from nqmate_api.strategies.repository import StrategyRepository, SupabaseStrategyRepository
from nqmate_api.strategies.service import validate_strategy
from nqmate_api.strategies.outcomes_repository import OutcomeRepository, SupabaseOutcomeRepository
from nqmate_api.strategies.performance import calculate_performance
from nqmate_api.strategies.setups import SetupOccurrence
from nqmate_api.strategies.setups_repository import SetupRepository, SupabaseSetupRepository
from nqmate_api.strategies.pb_blake import HtfContext, Inversion, LiquidityEvent, assess_pb_setup

app = FastAPI(title="NQmate API", version="0.1.0")


@lru_cache(maxsize=1)
def get_market_repository() -> MarketRepository:
    return SupabaseMarketRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_news_repository() -> NewsRepository:
    return SupabaseNewsRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_macro_repository() -> MacroRepository:
    return SupabaseMacroRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_bias_repository() -> BiasRepository:
    return SupabaseBiasRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_analogue_repository() -> AnalogueRepository:
    return SupabaseAnalogueRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_graph_repository() -> GraphRepository:
    return Neo4jGraphRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_strategy_repository() -> StrategyRepository:
    return SupabaseStrategyRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_outcome_repository() -> OutcomeRepository:
    return SupabaseOutcomeRepository.from_settings(Settings())


@lru_cache(maxsize=1)
def get_setup_repository() -> SetupRepository:
    return SupabaseSetupRepository.from_settings(Settings())


class AnalogueQueryRequest(BaseModel):
    sessionDate: date
    features: dict[str, float]
    predictionTime: datetime
    topK: int = Field(default=20, ge=1, le=20)
    metric: str = "euclidean"


class BiasSnapshotRequest(BaseModel):
    overnightStructure: float = Field(ge=-1, le=1)
    gap: float = Field(ge=-1, le=1)
    technicalLocation: float = Field(ge=-1, le=1)
    relativeStrength: float = Field(ge=-1, le=1)
    macroContext: float = Field(ge=-1, le=1)
    newsContext: float = Field(ge=-1, le=1)
    minutesToHighImpactEvent: float | None = None
    analogueBullRate: float | None = Field(default=None, ge=0, le=1)
    analogueAvg30mReturn: float | None = None
    analogueAvg60mReturn: float | None = None
    analogueSampleSize: int | None = Field(default=None, ge=0)
    analogue: AnalogueQueryRequest | None = None


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
    supported_timeframes = {"1min", "5m", "15m", "1h", "2h", "4h", "1d", "120m", "240m"}
    if timeframe not in supported_timeframes:
        raise HTTPException(
            status_code=422,
            detail="timeframe must be 1min, 5m, 15m, 1h, 2h, 4h, 1d, 120m, or 240m",
        )
    bars = repository.get_bars(
        datetime.combine(start, time.min, timezone.utc),
        datetime.combine(end + timedelta(days=1), time.min, timezone.utc),
    )
    minute_bars = [bar for bar in bars if bar.timeframe == "1min"]
    if timeframe == "1min":
        output_bars = minute_bars
    else:
        persisted_bars = [bar for bar in bars if bar.timeframe == timeframe]
        output_bars = persisted_bars or aggregate_bars(minute_bars, timeframe)
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


@app.get("/api/v1/market/nq/analogue-features", tags=["market"])
async def get_nq_analogue_features(
    session_date: date,
    repository: MarketRepository = Depends(get_market_repository),
) -> dict[str, object]:
    session = repository.get_session(session_date)
    if session is None:
        raise HTTPException(status_code=404, detail="Market session not found")
    return {"session_date": session_date.isoformat(), "feature_version": "analogue-v1", "features": session_features(session)}


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


@app.get("/api/v1/news/clusters", tags=["news"])
async def get_news_clusters(
    limit: int = 50,
    repository: NewsRepository = Depends(get_news_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return {"clusters": repository.list_clusters(limit)}


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


@app.get("/api/v1/macro/observations", tags=["macro"])
async def get_macro_observations(
    series_id: str | None = None,
    limit: int = 100,
    repository: MacroRepository = Depends(get_macro_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    return {"series_id": series_id, "observations": repository.list(series_id, limit)}


@app.get("/api/v1/macro/events/{event_id}/reactions", tags=["macro"])
async def get_macro_reactions(
    event_id: str,
    limit: int = 100,
    repository: MacroRepository = Depends(get_macro_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    return {"event_id": event_id, "reactions": repository.list_reactions(event_id, limit)}


@app.post("/api/v1/bias/generate", tags=["bias"])
async def generate_bias(
    request: BiasSnapshotRequest,
    repository: BiasRepository = Depends(get_bias_repository),
    analogue_repository: AnalogueRepository = Depends(get_analogue_repository),
) -> dict[str, Any]:
    analogue_matches = []
    analogue_summary: dict[str, float] = {}
    if request.analogue is not None:
        if request.analogue.metric not in {"euclidean", "cosine"}:
            raise HTTPException(status_code=422, detail="analogue metric must be euclidean or cosine")
        matches = rank_analogues(
            request.analogue.sessionDate.isoformat(), request.analogue.features,
            analogue_repository.list(), request.analogue.predictionTime,
            request.analogue.topK, request.analogue.metric,
        )
        analogue_matches = [
            {"session_date": match.session_date, "distance": match.distance, "outcome_summary": match.outcome_summary}
            for match in matches
        ]
        if matches:
            analogue_summary = matches[0].outcome_summary
    snapshot = BiasSnapshot(
        request.overnightStructure, request.gap, request.technicalLocation,
        request.relativeStrength, request.macroContext, request.newsContext,
        request.minutesToHighImpactEvent,
        request.analogueBullRate if request.analogueBullRate is not None else analogue_summary.get("analogue_bull_rate"),
        request.analogueAvg30mReturn if request.analogueAvg30mReturn is not None else analogue_summary.get("return_30m_mean"),
        request.analogueAvg60mReturn if request.analogueAvg60mReturn is not None else analogue_summary.get("return_60m_mean"),
        request.analogueSampleSize if request.analogueSampleSize is not None else int(analogue_summary["sample_size"]) if "sample_size" in analogue_summary else None,
    )
    result = score_bias(snapshot)
    response = repository.create(snapshot, result)
    if analogue_matches:
        response["analogue_matches"] = analogue_matches
    return response


@app.get("/api/v1/bias/current", tags=["bias"])
async def get_current_bias(
    repository: BiasRepository = Depends(get_bias_repository),
) -> dict[str, Any]:
    prediction = repository.latest()
    if prediction is None:
        raise HTTPException(status_code=404, detail="No bias prediction found")
    return prediction


class SimilarRegimeRequest(BaseModel):
    sessionDate: date
    features: dict[str, float]
    predictionTime: datetime
    topK: int = Field(default=20, ge=1, le=20)
    metric: str = "euclidean"


@app.post("/api/v1/regimes/similar", tags=["regimes"])
async def get_similar_regimes(
    request: SimilarRegimeRequest,
    repository: AnalogueRepository = Depends(get_analogue_repository),
) -> dict[str, object]:
    if request.metric not in {"euclidean", "cosine"}:
        raise HTTPException(status_code=422, detail="metric must be euclidean or cosine")
    matches = rank_analogues(request.sessionDate.isoformat(), request.features, repository.list(), request.predictionTime, request.topK, request.metric)
    return {"session_date": request.sessionDate.isoformat(), "metric": request.metric, "matches": [
        {"session_date": match.session_date, "distance": match.distance, "outcome_summary": match.outcome_summary}
        for match in matches
    ]}


@app.get("/api/v1/knowledge/regimes", tags=["knowledge"])
async def query_knowledge_regimes(
    overnight_direction: str | None = None,
    overnight_volatility: str | None = None,
    gap: str | None = None,
    location: str | None = None,
    yield_regime: str | None = None,
    catalyst_regime: str | None = None,
    limit: int = 20,
    repository: GraphRepository = Depends(get_graph_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    filters = {key: value for key, value in {
        "overnight_direction": overnight_direction, "overnight_volatility": overnight_volatility,
        "gap": gap, "location": location, "yield_regime": yield_regime,
        "catalyst_regime": catalyst_regime,
    }.items() if value is not None}
    return {"filters": filters, "sessions": repository.query_regimes(filters, limit)}


@app.get("/api/v1/knowledge/strategy-evidence", tags=["knowledge"])
async def query_strategy_evidence(
    overnight_direction: str | None = None,
    overnight_volatility: str | None = None,
    gap: str | None = None,
    location: str | None = None,
    yield_regime: str | None = None,
    catalyst_regime: str | None = None,
    limit: int = 20,
    repository: GraphRepository = Depends(get_graph_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    filters = {key: value for key, value in {
        "overnight_direction": overnight_direction, "overnight_volatility": overnight_volatility,
        "gap": gap, "location": location, "yield_regime": yield_regime,
        "catalyst_regime": catalyst_regime,
    }.items() if value is not None}
    return {"filters": filters, "strategies": repository.query_strategy_evidence(filters, limit)}


class StrategyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    allowedRegimes: list[str] = Field(default_factory=list, max_length=20)
    requiredConditions: list[str] = Field(default_factory=list, max_length=50)
    confirmationConditions: list[str] = Field(default_factory=list, max_length=50)
    invalidationConditions: list[str] = Field(default_factory=list, max_length=50)
    entryLogic: str = Field(min_length=1, max_length=2000)
    targetLogic: str = Field(min_length=1, max_length=2000)
    stopLogic: str = Field(min_length=1, max_length=2000)
    active: bool = True


class PbContextRequest(BaseModel):
    timeframe: str
    direction: str
    keyLevelValid: bool


class PbLiquidityRequest(BaseModel):
    sweptLevel: str
    price: float
    sweptAt: datetime


class PbInversionRequest(BaseModel):
    timeframe: str
    direction: str
    lower: float
    upper: float
    confirmedAt: datetime


class PbAssessmentRequest(BaseModel):
    sessionDate: date
    analyzedAt: datetime
    contexts: list[PbContextRequest] = Field(default_factory=list, max_length=20)
    liquidity: PbLiquidityRequest | None = None
    inversions: list[PbInversionRequest] = Field(default_factory=list, max_length=100)
    entry: float | None = None
    stop: float | None = None
    targets: list[float] = Field(default_factory=list, max_length=10)


def _strategy_from_request(request: StrategyRequest) -> Strategy:
    return Strategy(
        request.name, request.description, tuple(request.allowedRegimes), tuple(request.requiredConditions),
        tuple(request.confirmationConditions), tuple(request.invalidationConditions), request.entryLogic,
        request.targetLogic, request.stopLogic, request.active,
    )


@app.post("/api/v1/strategies", tags=["strategies"])
async def create_strategy(
    request: StrategyRequest,
    repository: StrategyRepository = Depends(get_strategy_repository),
) -> dict[str, Any]:
    strategy = _strategy_from_request(request)
    try:
        validate_strategy(strategy)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return repository.create(strategy)


@app.get("/api/v1/strategies", tags=["strategies"])
async def list_strategies(
    active: bool | None = None,
    repository: StrategyRepository = Depends(get_strategy_repository),
) -> dict[str, object]:
    return {"strategies": repository.list(active)}


@app.post("/api/v1/strategies/{strategy_id}/assess", tags=["strategies"])
async def assess_strategy(
    strategy_id: str,
    request: PbAssessmentRequest,
    strategy_repository: StrategyRepository = Depends(get_strategy_repository),
    setup_repository: SetupRepository = Depends(get_setup_repository),
) -> dict[str, object]:
    strategy = strategy_repository.get(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    liquidity = LiquidityEvent(
        request.liquidity.sweptLevel, request.liquidity.price, request.liquidity.sweptAt
    ) if request.liquidity else None
    result = assess_pb_setup(
        tuple(HtfContext(item.timeframe, item.direction, item.keyLevelValid) for item in request.contexts),
        liquidity,
        tuple(Inversion(item.timeframe, item.direction, item.lower, item.upper, item.confirmedAt) for item in request.inversions),
        request.entry, request.stop, request.targets, request.analyzedAt,
    )
    persisted = None
    if result.status == "VALID" and result.inversion_timeframe:
        confirmation_candidates = [
            item.confirmedAt for item in request.inversions
            if item.timeframe == result.inversion_timeframe
            and item.direction in {"LONG", "SHORT"}
            and (liquidity is None or item.confirmedAt > liquidity.swept_at)
            and item.confirmedAt <= request.analyzedAt
        ]
        confirmation = max(
            confirmation_candidates,
            default=request.analyzedAt,
        )
        persisted = setup_repository.upsert(SetupOccurrence(
            strategy_id, request.sessionDate.isoformat(), confirmation,
            ("pb_blake_valid", f"inversion_{result.inversion_timeframe}"),
        ))
    return {
        "strategyId": strategy_id,
        "sessionDate": request.sessionDate.isoformat(),
        "analyzedAt": request.analyzedAt.isoformat(),
        "status": result.status,
        "direction": result.direction,
        "inversionTimeframe": result.inversion_timeframe,
        "entry": result.entry,
        "stop": result.stop,
        "stopDistance": result.stop_distance,
        "targets": list(result.targets),
        "riskRewards": list(result.risk_rewards),
        "missing": list(result.missing),
        "persistedSetup": persisted,
    }


@app.get("/api/v1/strategies/{strategy_id}/performance", tags=["strategies"])
async def get_strategy_performance(
    strategy_id: str,
    strategy_repository: StrategyRepository = Depends(get_strategy_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
) -> dict[str, object]:
    if strategy_repository.get(strategy_id) is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"strategy_id": strategy_id, "statistics": calculate_performance(outcome_repository.list_for_strategy(strategy_id))}


@app.get("/api/v1/strategies/{strategy_id}", tags=["strategies"])
async def get_strategy(strategy_id: str, repository: StrategyRepository = Depends(get_strategy_repository)) -> dict[str, Any]:
    strategy = repository.get(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@app.patch("/api/v1/strategies/{strategy_id}", tags=["strategies"])
async def update_strategy(
    strategy_id: str,
    request: StrategyRequest,
    repository: StrategyRepository = Depends(get_strategy_repository),
) -> dict[str, Any]:
    strategy = _strategy_from_request(request)
    try:
        validate_strategy(strategy)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if repository.get(strategy_id) is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return repository.update(strategy_id, strategy)


@app.delete("/api/v1/strategies/{strategy_id}", tags=["strategies"])
async def deactivate_strategy(strategy_id: str, repository: StrategyRepository = Depends(get_strategy_repository)) -> dict[str, Any]:
    if repository.get(strategy_id) is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return repository.deactivate(strategy_id)


@app.get("/api/v1/bias/history", tags=["bias"])
async def get_bias_history(
    limit: int = 50,
    repository: BiasRepository = Depends(get_bias_repository),
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return {"predictions": repository.history(limit)}


def get_bias_llm_provider() -> LLMProvider:
    settings = Settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Gemini configuration is required for explanations")
    return GeminiBiasExplainer(settings.gemini_api_key, settings.gemini_model)


@app.post("/api/v1/bias/{prediction_id}/explain", tags=["bias"])
async def explain_bias(
    prediction_id: str,
    repository: BiasRepository = Depends(get_bias_repository),
    provider: LLMProvider = Depends(get_bias_llm_provider),
) -> dict[str, Any]:
    prediction = repository.get(prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Bias prediction not found")
    result = BiasResult(
        prediction["direction"], prediction["score"], prediction["confidence"], prediction["recommendation"], prediction.get("catalyst_risk"),
        tuple(prediction.get("evidence") or ()), tuple(prediction.get("bull_case") or ()),
        tuple(prediction.get("bear_case") or ()), tuple(prediction.get("invalidation") or ()),
        tuple(prediction.get("uncertainty") or ()),
    )
    explanation = provider.explain(result)
    return repository.create_explanation(prediction_id, explanation)


@app.get("/api/v1/bias/{prediction_id}/evaluation", tags=["bias"])
async def evaluate_bias(
    prediction_id: str,
    repository: BiasRepository = Depends(get_bias_repository),
) -> dict[str, Any]:
    prediction = repository.get(prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Bias prediction not found")
    return {
        "prediction_id": prediction_id,
        "model_version": prediction.get("model_version"),
        "feature_version": prediction.get("feature_version"),
        "evaluation": summarize_prediction_outcomes(repository.list_outcomes(prediction_id)),
    }


@app.get("/api/v1/bias/evaluation", tags=["bias"])
async def evaluate_bias_history(
    limit: int = 100,
    repository: BiasRepository = Depends(get_bias_repository),
) -> dict[str, Any]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    records: list[dict[str, Any]] = []
    predictions = repository.history(limit)
    for prediction in predictions:
        prediction_id = prediction.get("id")
        if not prediction_id:
            continue
        for outcome in repository.list_outcomes(str(prediction_id)):
            if isinstance(outcome.get("correct"), bool):
                records.append({"confidence": prediction.get("confidence"), "correct": outcome["correct"]})
    return {"prediction_count": len(predictions), "outcome_count": len(records),
            "confidence_calibration": confidence_calibration(records)}


@app.get("/api/v1/bias/drift", tags=["bias"])
async def get_bias_drift(
    limit: int = 100,
    repository: BiasRepository = Depends(get_bias_repository),
) -> dict[str, Any]:
    if limit < 4 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 4 and 100")
    predictions = list(repository.history(limit))
    ordered = list(reversed(predictions))
    midpoint = len(ordered) // 2
    reference = [item.get("input_snapshot") or {} for item in ordered[:midpoint]]
    current = [item.get("input_snapshot") or {} for item in ordered[midpoint:]]
    return {"prediction_count": len(predictions), "reference_count": len(reference),
            "current_count": len(current), "features": feature_drift(reference, current)}


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
