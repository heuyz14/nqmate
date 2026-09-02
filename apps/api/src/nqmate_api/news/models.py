from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Optional


class NewsEventType(StrEnum):
    FED = "fed"
    MACRO = "macro"
    EARNINGS = "earnings"
    TECHNOLOGY = "technology"
    GEOPOLITICAL = "geopolitical"
    MARKET_MOVE = "market_move"
    OTHER = "other"


class NewsStance(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class NewsDirection(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class ImpactHorizon(StrEnum):
    INTRADAY = "intraday"
    SHORT_TERM = "short_term"
    MULTI_DAY = "multi_day"
    UNKNOWN = "unknown"


class CalendarImpact(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class EconomicCalendarEvent:
    event: str
    currency: str
    impact: CalendarImpact
    scheduled_at: datetime
    source: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None


@dataclass(frozen=True)
class NewsArticle:
    provider: str
    provider_id: str
    url: str
    headline: str
    source: str
    published_at: datetime
    available_at: datetime
    summary: Optional[str] = None
    entities: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()


@dataclass(frozen=True)
class NewsEvent:
    article: NewsArticle
    event_type: NewsEventType
    event_subtype: Optional[str]
    event_timestamp: datetime
    stance: NewsStance
    sentiment: Optional[float]
    nq_direction: NewsDirection
    impact: Optional[str]
    nq_relevance_score: float
    impact_horizon: ImpactHorizon
    themes: tuple[str, ...]
    confidence: Optional[float]
    summary: Optional[str]
    reason: Optional[str]
    model_version: str
    created_at: datetime
    logical_event_key: Optional[str] = None
