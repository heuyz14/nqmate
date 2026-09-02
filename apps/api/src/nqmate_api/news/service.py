from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from nqmate_api.news.models import (
    ImpactHorizon, NewsDirection, NewsEvent, NewsEventType, NewsStance,
    NewsArticle, EconomicCalendarEvent,
)
from nqmate_api.news.relevance import nq_relevance_score
from nqmate_api.news.repository import NewsRepository
from nqmate_api.news.clustering import cluster_key
from nqmate_api.news.nlp import NewsEventExtractor, apply_extraction


def economic_surprise(actual: float | None, forecast: float | None) -> float | None:
    """Return raw release surprise; missing values remain unavailable."""
    if actual is None or forecast is None:
        return None
    return round(actual - forecast, 10)


def pre_event_risk(scheduled_at: datetime, now: datetime) -> str:
    """Classify the documented catalyst window around a scheduled release."""
    minutes_until = (scheduled_at - now).total_seconds() / 60
    if 0 < minutes_until <= 5:
        return "CRITICAL_EVENT_RISK"
    if 5 < minutes_until <= 30:
        return "EVENT_RISK"
    if -5 <= minutes_until <= 0:
        return "INITIAL_REACTION"
    if -30 <= minutes_until < -5:
        return "CONTINUATION_REVERSAL"
    if minutes_until > 30:
        return "SCHEDULED"
    return "OBSERVED"


def classify_article(article: NewsArticle) -> NewsEvent:
    text = f"{article.headline} {article.summary or ''}".lower()
    if "fed" in text or "fomc" in text or "federal reserve" in text:
        event_type = NewsEventType.FED
    elif any(term in text for term in ("earnings", "revenue", "guidance")):
        event_type = NewsEventType.EARNINGS
    elif any(term in text for term in ("semiconductor", "chip", "ai", "artificial intelligence")):
        event_type = NewsEventType.TECHNOLOGY
    elif any(term in text for term in ("inflation", "cpi", "ppi", "jobs", "payroll", "gdp")):
        event_type = NewsEventType.MACRO
    else:
        event_type = NewsEventType.OTHER
    score = nq_relevance_score(article)
    return NewsEvent(
        article=article, event_type=event_type, event_subtype=None,
        event_timestamp=article.published_at, stance=NewsStance.NEUTRAL,
        sentiment=None, nq_direction=NewsDirection.UNKNOWN, impact=None,
        nq_relevance_score=score, impact_horizon=ImpactHorizon.UNKNOWN,
        themes=article.topics, confidence=None, summary=article.summary,
        reason="Baseline deterministic classification; NLP extraction is optional.",
        model_version="rules-v1", created_at=datetime.now(timezone.utc),
        logical_event_key=cluster_key_from_article(article, event_type),
    )


def cluster_key_from_article(article: NewsArticle, event_type: NewsEventType) -> str:
    """Build the same cluster identity used for persisted normalized events."""
    provisional = NewsEvent(
        article=article, event_type=event_type, event_subtype=None,
        event_timestamp=article.published_at, stance=NewsStance.NEUTRAL,
        sentiment=None, nq_direction=NewsDirection.UNKNOWN, impact=None,
        nq_relevance_score=0, impact_horizon=ImpactHorizon.UNKNOWN, themes=article.topics,
        confidence=None, summary=None, reason=None, model_version="", created_at=article.published_at,
    )
    return cluster_key(provisional)


def persist_articles(repository: NewsRepository, articles: Sequence[NewsArticle], extractor: NewsEventExtractor | None = None) -> int:
    created = 0
    for article in articles:
        event = classify_article(article)
        if extractor is not None:
            event = apply_extraction(event, extractor.extract(article))
        repository.upsert_event(event)
        created += 1
    return created


def persist_calendar(repository: NewsRepository, events: Sequence[EconomicCalendarEvent]) -> int:
    for event in events:
        repository.upsert_calendar_event(event)
    return len(events)
