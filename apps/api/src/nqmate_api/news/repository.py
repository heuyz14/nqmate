from __future__ import annotations

from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.news.models import EconomicCalendarEvent, NewsArticle, NewsEvent
from nqmate_api.macro.service import event_surprise


class NewsRepository(Protocol):
    def upsert_article(self, article: NewsArticle) -> None: ...
    def upsert_event(self, event: NewsEvent) -> None: ...
    def upsert_cluster(self, logical_event_key: str, canonical: NewsEvent, events: Sequence[NewsEvent]) -> None: ...
    def list_clusters(self, limit: int = 50) -> Sequence[dict[str, Any]]: ...
    def list_events(self, high_impact_only: bool = False, limit: int = 50,
                    start: str | None = None, end: str | None = None) -> Sequence[dict[str, Any]]: ...
    def upsert_calendar_event(self, event: EconomicCalendarEvent) -> None: ...
    def list_calendar_events(self, start: str, end: str, high_impact_only: bool = False, limit: int = 100) -> Sequence[dict[str, Any]]: ...


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


class SupabaseNewsRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseNewsRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert_article(self, article: NewsArticle) -> None:
        self.client.table("news_articles").upsert({
            "provider": article.provider, "provider_id": article.provider_id, "url": article.url,
            "headline": article.headline, "source": article.source,
            "published_at": _iso(article.published_at), "available_at": _iso(article.available_at),
            "summary": article.summary, "entities": list(article.entities), "topics": list(article.topics),
        }, on_conflict="provider,provider_id").execute()

    def upsert_event(self, event: NewsEvent) -> None:
        self.upsert_article(event.article)
        article = self.client.table("news_articles").select("id").eq(
            "provider", event.article.provider
        ).eq("provider_id", event.article.provider_id).single().execute()
        self.client.table("news_events").upsert({
            "article_id": article.data["id"], "event_type": event.event_type.value,
            "event_subtype": event.event_subtype, "event_timestamp": _iso(event.event_timestamp),
            "stance": event.stance.value, "sentiment": event.sentiment,
            "nq_direction": event.nq_direction.value, "impact": event.impact,
            "nq_relevance_score": event.nq_relevance_score, "impact_horizon": event.impact_horizon.value,
            "themes": list(event.themes), "confidence": event.confidence, "summary": event.summary,
            "reason": event.reason, "model_version": event.model_version, "created_at": _iso(event.created_at),
            "logical_event_key": event.logical_event_key,
        }, on_conflict="article_id").execute()

    def upsert_cluster(self, logical_event_key: str, canonical: NewsEvent, events: Sequence[NewsEvent]) -> None:
        available = [event.article.available_at for event in events]
        self.client.table("news_event_clusters").upsert({
            "logical_event_key": logical_event_key,
            "canonical_provider": canonical.article.provider,
            "canonical_provider_id": canonical.article.provider_id,
            "event_count": len(events),
            "providers": sorted({event.article.provider for event in events}),
            "first_available_at": _iso(min(available)), "last_available_at": _iso(max(available)),
        }, on_conflict="logical_event_key").execute()

    def list_clusters(self, limit: int = 50) -> Sequence[dict[str, Any]]:
        return self.client.table("news_event_clusters").select("*").order(
            "last_available_at", desc=True
        ).limit(min(limit, 100)).execute().data or []

    def list_events(self, high_impact_only: bool = False, limit: int = 50,
                    start: str | None = None, end: str | None = None) -> Sequence[dict[str, Any]]:
        query = self.client.table("news_events").select("*, news_articles(*)").order(
            "event_timestamp", desc=True
        ).limit(min(limit, 100))
        if start:
            query = query.gte("event_timestamp", start)
        if end:
            query = query.lte("event_timestamp", end)
        if high_impact_only:
            query = query.gte("nq_relevance_score", 0.75)
        return query.execute().data or []

    def upsert_calendar_event(self, event: EconomicCalendarEvent) -> None:
        provider_event_id = f"{event.event}:{event.currency}:{event.scheduled_at.isoformat()}"
        self.client.table("economic_calendar_events").upsert({
            "provider": event.source, "provider_event_id": provider_event_id,
            "event": event.event, "currency": event.currency, "impact": event.impact.value,
            "scheduled_at": _iso(event.scheduled_at), "actual": event.actual,
            "forecast": event.forecast, "previous": event.previous,
            "surprise": event.surprise if event.surprise is not None else event_surprise(event),
            "available_at": _iso(event.scheduled_at),
        }, on_conflict="provider,provider_event_id").execute()

    def list_calendar_events(self, start: str, end: str, high_impact_only: bool = False, limit: int = 100) -> Sequence[dict[str, Any]]:
        query = self.client.table("economic_calendar_events").select("*").gte(
            "scheduled_at", start
        ).lte("scheduled_at", end).order("scheduled_at").limit(min(limit, 100))
        if high_impact_only:
            query = query.eq("impact", "HIGH")
        return query.execute().data or []
