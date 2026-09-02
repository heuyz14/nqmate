import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx

from nqmate_api.news.models import NewsArticle
from nqmate_api.news.providers import MarketauxNewsProvider
from nqmate_api.news.relevance import nq_relevance_score
from nqmate_api.news.store import NewsStore


def article() -> NewsArticle:
    timestamp = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
    return NewsArticle("marketaux", "1", "https://example.test/1", "NVDA rises after Fed comments", "Example", timestamp, timestamp, "summary", ("NVDA",), ("monetary policy",))


class NewsTests(unittest.IsolatedAsyncioTestCase):
    async def test_marketaux_maps_article_and_publication_availability(self) -> None:
        response = httpx.Response(200, json={"data": [{"uuid": "1", "url": "https://example.test/1", "title": "Headline", "source": "Example", "published_at": "2026-09-01T12:00:00Z", "description": "Summary", "entities": [{"symbol": "NVDA"}], "topics": [{"name": "technology"}]}]}, request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await MarketauxNewsProvider("key", client=client, base_url="https://example.test").fetch()
        self.assertEqual(result[0].available_at, result[0].published_at)
        self.assertEqual(result[0].entities, ("NVDA",))

    def test_relevance_and_deduplication(self) -> None:
        item = article(); store = NewsStore()
        self.assertGreater(nq_relevance_score(item), 0)
        self.assertTrue(store.upsert_article(item))
        self.assertFalse(store.upsert_article(item))

    def test_news_endpoint_reads_repository(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_news_repository

        fake = type("FakeNewsRepository", (), {"list_events": lambda self, high_impact_only=False, limit=50: [{"id": "event-1"}]})()
        app.dependency_overrides[get_news_repository] = lambda: fake
        try:
            response = TestClient(app).get("/api/v1/news/high-impact?limit=1")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"][0]["id"], "event-1")
