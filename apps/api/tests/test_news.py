import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx

from nqmate_api.news.models import CalendarImpact, EconomicCalendarEvent, NewsArticle
from nqmate_api.news.polling import polling_interval_seconds
from nqmate_api.news.providers import ForexFactoryCalendarProvider, MarketauxNewsProvider
from nqmate_api.news.relevance import nq_relevance_score
from nqmate_api.news.store import NewsStore
from nqmate_api.news.clustering import cluster_key, select_canonical_event, consolidate_events
from nqmate_api.news.nlp import CachedNewsExtractor, NewsExtraction
from nqmate_api.news.service import classify_article, economic_surprise, pre_event_risk


def article() -> NewsArticle:
    timestamp = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
    return NewsArticle("marketaux", "1", "https://example.test/1", "NVDA rises after Fed comments", "Example", timestamp, timestamp, "summary", ("NVDA",), ("monetary policy",))


class NewsTests(unittest.IsolatedAsyncioTestCase):
    def test_economic_surprise_is_actual_minus_forecast(self) -> None:
        self.assertEqual(economic_surprise(3.4, 3.1), 0.3)
        self.assertIsNone(economic_surprise(None, 3.1))
        self.assertIsNone(economic_surprise(3.4, None))

    def test_pre_event_risk_uses_release_windows(self) -> None:
        now = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)
        self.assertEqual(pre_event_risk(now + timedelta(minutes=30), now), "EVENT_RISK")
        self.assertEqual(pre_event_risk(now + timedelta(minutes=5), now), "CRITICAL_EVENT_RISK")
        self.assertEqual(pre_event_risk(now + timedelta(minutes=2), now), "CRITICAL_EVENT_RISK")
        self.assertEqual(pre_event_risk(now - timedelta(minutes=3), now), "INITIAL_REACTION")
        self.assertEqual(pre_event_risk(now - timedelta(minutes=15), now), "CONTINUATION_REVERSAL")
    def test_baseline_classifier_preserves_point_in_time_article(self) -> None:
        event = classify_article(article())
        self.assertEqual(event.event_type.value, "fed")
        self.assertEqual(event.event_timestamp, event.article.available_at)
        self.assertEqual(event.nq_direction.value, "unknown")

    def test_cross_source_reports_share_a_cluster_key(self) -> None:
        first = classify_article(article())
        second_article = NewsArticle(
            "fed", "2", "https://example.test/2", "Federal Reserve comments as NVDA rises",
            "Federal Reserve", first.event_timestamp + timedelta(minutes=10),
            first.event_timestamp + timedelta(minutes=10), "Fed comments", ("NVDA",), ("monetary policy",),
        )
        second = classify_article(second_article)
        self.assertEqual(cluster_key(first), cluster_key(second))

    def test_canonical_cluster_event_prefers_official_source(self) -> None:
        market_event = classify_article(article())
        official_article = NewsArticle(
            "fed", "3", "https://example.test/3", "Federal Reserve issues statement",
            "Federal Reserve", market_event.event_timestamp + timedelta(minutes=2),
            market_event.event_timestamp + timedelta(minutes=2), "Statement", (), (),
        )
        official_event = classify_article(official_article)
        self.assertIs(select_canonical_event([market_event, official_event]), official_event)

    def test_consolidation_keeps_one_canonical_event_per_cluster(self) -> None:
        first = classify_article(article())
        second = classify_article(NewsArticle(
            "fed", "4", "https://example.test/4", "Federal Reserve comments as NVDA rises",
            "Federal Reserve", first.event_timestamp + timedelta(minutes=10),
            first.event_timestamp + timedelta(minutes=10), "Fed comments", ("NVDA",), ("monetary policy",),
        ))
        clusters = consolidate_events([first, second])
        self.assertEqual(len(clusters), 1)
        self.assertIs(clusters[0]["canonical"], second)
        self.assertEqual(len(clusters[0]["events"]), 2)

    def test_nlp_extraction_is_cached_by_provider_identity(self) -> None:
        calls = []

        def extract(article):
            calls.append(article.provider_id)
            return NewsExtraction(event_subtype="RATE_DECISION", confidence=0.9)

        cached = CachedNewsExtractor(extract)
        first = cached.extract(article())
        second = cached.extract(article())
        self.assertEqual(first, second)
        self.assertEqual(calls, ["1"])

    def test_gemini_adapter_parses_structured_output(self) -> None:
        from nqmate_api.news.nlp import GeminiNewsExtractor

        def handler(request):
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"event_subtype":"AI","nq_direction":"bullish","confidence":0.8,"themes":["AI"]}'}]}}]}, request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = GeminiNewsExtractor("test-key", client=client).extract(article())
        self.assertEqual(result.event_subtype, "AI")
        self.assertEqual(result.confidence, 0.8)

    def test_calendar_event_upsert_uses_stable_identity(self) -> None:
        from unittest.mock import MagicMock
        from nqmate_api.news.repository import SupabaseNewsRepository
        timestamp = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
        event = EconomicCalendarEvent("CPI", "USD", CalendarImpact.HIGH, timestamp, "forex_factory", forecast=0.3)
        client = MagicMock()

        SupabaseNewsRepository(client).upsert_calendar_event(event)

        call = client.table.return_value.upsert.call_args
        self.assertEqual(call.kwargs["on_conflict"], "provider,provider_event_id")
        self.assertEqual(call.args[0]["impact"], "HIGH")

    async def test_forex_factory_filters_usd_and_maps_values(self) -> None:
        response = httpx.Response(200, json=[
            {"event": "CPI", "currency": "USD", "impact": "HIGH", "scheduledAt": "2026-09-01T12:30:00Z", "forecast": "0.3", "previous": "0.2"},
            {"event": "GDP", "currency": "EUR", "impact": "HIGH", "scheduledAt": "2026-09-01T12:30:00Z"},
        ], request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await ForexFactoryCalendarProvider("https://example.test", client=client).fetch()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].actual, None)
        self.assertEqual(result[0].forecast, 0.3)

    async def test_forex_factory_maps_csv_export(self) -> None:
        response = httpx.Response(200, text="Title,Country,Date,Time,Impact,Forecast,Previous,URL\nCPI,USD,09-02-2026,8:30am,High,0.3%,0.2%,https://example.test/cpi\n", request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await ForexFactoryCalendarProvider("https://example.test", client=client).fetch()
        self.assertEqual(result[0].event, "CPI")
        self.assertEqual(result[0].impact.value, "HIGH")
        self.assertEqual(result[0].forecast, 0.3)

    def test_adaptive_polling_windows(self) -> None:
        from datetime import datetime, timezone
        self.assertEqual(polling_interval_seconds(datetime(2026, 9, 1, 13, 0, tzinfo=timezone.utc)), 60)
        self.assertEqual(polling_interval_seconds(datetime(2026, 9, 1, 17, 0, tzinfo=timezone.utc)), 300)

    async def test_marketaux_maps_article_and_publication_availability(self) -> None:
        response = httpx.Response(200, json={"data": [{"uuid": "1", "url": "https://example.test/1", "title": "Headline", "source": "Example", "published_at": "2026-09-01T12:00:00Z", "description": "Summary", "entities": [{"symbol": "NVDA"}], "topics": [{"name": "technology"}]}]}, request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await MarketauxNewsProvider("key", client=client, base_url="https://example.test").fetch(
            published_after=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(result[0].available_at, result[0].published_at)
        self.assertEqual(result[0].entities, ("NVDA",))
        self.assertNotIn("published_before", client.get.await_args.kwargs["params"])
        self.assertEqual(client.get.await_args.kwargs["params"]["published_after"], "2026-09-01T12:00:00")

    def test_relevance_and_deduplication(self) -> None:
        item = article(); store = NewsStore()
        self.assertGreater(nq_relevance_score(item), 0)
        self.assertTrue(store.upsert_article(item))
        self.assertFalse(store.upsert_article(item))

    def test_news_endpoint_reads_repository(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_news_repository

        fake = type("FakeNewsRepository", (), {"list_events": lambda self, high_impact_only=False, limit=50, start=None, end=None: [{"id": "event-1"}]})()
        app.dependency_overrides[get_news_repository] = lambda: fake
        try:
            response = TestClient(app).get("/api/v1/news/high-impact?limit=1")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"][0]["id"], "event-1")

    def test_upcoming_macro_endpoint_returns_minutes_and_risk(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_news_repository

        class FakeNewsRepository:
            def list_calendar_events(self, start, end, high_impact_only=False, limit=100):
                return [{
                    "event": "CPI", "currency": "USD", "impact": "HIGH",
                    "scheduled_at": (datetime.now(timezone.utc) + timedelta(minutes=3)).isoformat(),
                    "actual": None, "forecast": 3.1, "previous": 3.0,
                }]

        app.dependency_overrides[get_news_repository] = FakeNewsRepository
        try:
            response = TestClient(app).get("/api/v1/macro/upcoming")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["event"]["event"], "CPI")
        self.assertEqual(body["risk_state"], "CRITICAL_EVENT_RISK")
        self.assertGreater(body["minutes_until_event"], 2)
