import unittest
from datetime import date

from jobs.sync_graph_sources import sync_sources


class GraphSourceSyncTests(unittest.TestCase):
    def test_sync_sources_forwards_normalized_news_and_predictions(self) -> None:
        class FakeNews:
            def list_events(self, **kwargs):
                return [{
                    "event_type": "technology", "event_timestamp": "2026-09-02T13:00:00+00:00",
                    "nq_relevance_score": 0.9, "nq_direction": "bullish", "themes": ["AI"],
                    "news_articles": {"provider": "marketaux", "provider_id": "a1", "available_at": "2026-09-02T13:00:00+00:00", "entities": ["NVDA"]},
                }]

            def list_calendar_events(self, *args, **kwargs):
                return []

        class FakeBias:
            def history(self, limit=100):
                return [{"id": "p1", "created_at": "2026-09-02T14:00:00+00:00", "direction": "BULLISH", "score": 0.4, "confidence": 0.4}]

        class FakeGraph:
            def ensure_schema(self): self.schema = True
            def sync_news_event(self, **kwargs): self.news = kwargs
            def sync_prediction(self, **kwargs): self.prediction = kwargs

        graph = FakeGraph()
        counts = sync_sources(date(2026, 9, 1), date(2026, 9, 3), FakeNews(), FakeBias(), graph)

        self.assertEqual(counts, {"news": 1, "macro": 0, "predictions": 1})
        self.assertEqual(graph.news["companies"], ("NVDA",))
        self.assertEqual(graph.prediction["prediction_id"], "p1")
