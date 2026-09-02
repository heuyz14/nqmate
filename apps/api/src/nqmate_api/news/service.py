from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from nqmate_api.news.models import (
    ImpactHorizon, NewsDirection, NewsEvent, NewsEventType, NewsStance,
    NewsArticle, EconomicCalendarEvent,
)
from nqmate_api.news.relevance import nq_relevance_score
from nqmate_api.news.repository import NewsRepository


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
    )


def persist_articles(repository: NewsRepository, articles: Sequence[NewsArticle]) -> int:
    created = 0
    for article in articles:
        event = classify_article(article)
        repository.upsert_event(event)
        created += 1
    return created


def persist_calendar(repository: NewsRepository, events: Sequence[EconomicCalendarEvent]) -> int:
    for event in events:
        repository.upsert_calendar_event(event)
    return len(events)
