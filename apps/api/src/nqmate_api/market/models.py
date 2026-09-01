from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    timestamp: datetime
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    provider: str
    ingested_at: datetime
    available_at: datetime


@dataclass(frozen=True)
class MarketContract:
    product: str
    raw_contract_symbol: str
    continuous_symbol: str
    expiration: Optional[date] = None
    roll_date: Optional[date] = None


@dataclass(frozen=True)
class ContractRollover:
    product: str
    from_contract: str
    to_contract: str
    roll_date: date
    provider: str


@dataclass(frozen=True)
class WeeklyOpeningGap:
    week_start: date
    session_date: date
    opening_price: float
    prior_close: float
    gap_points: float
    gap_pct: Optional[float]
    contract: MarketContract


@dataclass(frozen=True)
class MarketSession:
    session_date: date
    nq_open: float
    nq_high: float
    nq_low: float
    nq_close: float
    overnight_open: float
    overnight_high: float
    overnight_low: float
    overnight_close: float
    prior_day_high: Optional[float]
    prior_day_low: Optional[float]
    prior_day_close: Optional[float]
    gap_points: Optional[float]
    gap_pct: Optional[float]
    overnight_return: Optional[float]
    overnight_range: float
    atr_14: Optional[float]
    contract: MarketContract
