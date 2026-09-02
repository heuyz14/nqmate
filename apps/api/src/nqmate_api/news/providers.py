from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Protocol, Sequence
from xml.etree import ElementTree

import httpx

from nqmate_api.news.models import CalendarImpact, EconomicCalendarEvent, NewsArticle


class NewsProvider(Protocol):
    async def fetch(self, query: str | None = None) -> Sequence[NewsArticle]: ...


class EconomicCalendarProvider(Protocol):
    async def fetch(self) -> Sequence[EconomicCalendarEvent]: ...


def _published(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class MarketauxNewsProvider:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None, base_url: str = "https://api.marketaux.com") -> None:
        if not api_key:
            raise ValueError("Marketaux API key is required")
        self.api_key, self.client, self.base_url = api_key, client, base_url.rstrip("/")

    async def fetch(self, query: str | None = None) -> Sequence[NewsArticle]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient()
        try:
            response = await client.get(f"{self.base_url}/v1/news/all", params={
                "api_token": self.api_key, "search": query or "Nasdaq NQ futures",
                "language": "en", "limit": 3,
            }, timeout=30)
            response.raise_for_status()
            now = datetime.now(timezone.utc)
            result = []
            for item in response.json().get("data", []):
                published = _published(item["published_at"])
                result.append(NewsArticle(
                    provider="marketaux", provider_id=str(item.get("uuid") or item.get("url")),
                    url=item["url"], headline=item["title"], source=item.get("source", ""),
                    published_at=published, available_at=published,
                    summary=item.get("description"),
                    entities=tuple(entity.get("symbol", "") for entity in item.get("entities", []) if entity.get("symbol")),
                    topics=tuple(topic.get("name", "") for topic in item.get("topics", []) if topic.get("name")),
                ))
            return result
        finally:
            if close_client:
                await client.aclose()


class FedRSSNewsProvider:
    def __init__(self, feed_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.feed_url, self.client = feed_url, client

    async def fetch(self, query: str | None = None) -> Sequence[NewsArticle]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient()
        try:
            response = await client.get(self.feed_url, timeout=30)
            response.raise_for_status()
            root = ElementTree.fromstring(response.text)
            now = datetime.now(timezone.utc)
            result = []
            for item in root.findall(".//item"):
                raw_date = item.findtext("pubDate", "")
                published = parsedate_to_datetime(raw_date).astimezone(timezone.utc) if raw_date else now
                title = item.findtext("title", "")
                url = item.findtext("link", "")
                result.append(NewsArticle("fed_rss", url, url, title, "Federal Reserve", published, published, item.findtext("description"), (), ("monetary policy",)))
            return result
        finally:
            if close_client:
                await client.aclose()


class ForexFactoryCalendarProvider:
    """Adapter for a configured machine-readable Forex Factory calendar export."""

    def __init__(self, export_url: str, client: httpx.AsyncClient | None = None) -> None:
        if not export_url:
            raise ValueError("Forex Factory export URL is required")
        self.export_url, self.client = export_url, client

    async def fetch(self) -> Sequence[EconomicCalendarEvent]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient()
        try:
            response = await client.get(self.export_url, timeout=30)
            response.raise_for_status()
            result = []
            for item in response.json():
                currency = str(item.get("currency", "")).upper()
                if currency != "USD":
                    continue
                scheduled = item.get("scheduledAt") or item.get("date")
                if not scheduled:
                    continue
                result.append(EconomicCalendarEvent(
                    event=str(item.get("event", "")), currency=currency,
                    impact=CalendarImpact(str(item.get("impact", "LOW")).upper()),
                    scheduled_at=_published(str(scheduled)), source="forex_factory",
                    actual=_number(item.get("actual")), forecast=_number(item.get("forecast")),
                    previous=_number(item.get("previous")),
                ))
            return result
        finally:
            if close_client:
                await client.aclose()


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return None
