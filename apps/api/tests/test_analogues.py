import unittest
from datetime import datetime, timezone

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.analogues.service import rank_analogues


class AnalogueTests(unittest.TestCase):
    def test_ranking_is_deterministic_and_excludes_future_data(self) -> None:
        now = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)
        current = {"overnight_return": 0.1, "gap": 0.2, "strength": 0.3}
        history = [
            HistoricalSession("2026-09-01", {"overnight_return": 0.1, "gap": 0.2, "strength": 0.3}, now, {"return_30m": 1.0}),
            HistoricalSession("2026-09-02", {"overnight_return": 0.9, "gap": 0.8, "strength": 0.7}, now, {"return_30m": -1.0}),
            HistoricalSession("2026-09-04", {"overnight_return": 0.1, "gap": 0.2, "strength": 0.3}, now, {"return_30m": 5.0}),
        ]
        result = rank_analogues("2026-09-03", current, history, now, top_k=2)
        self.assertEqual([match.session_date for match in result], ["2026-09-01", "2026-09-02"])
        self.assertEqual(result, rank_analogues("2026-09-03", current, history, now, top_k=2))

    def test_missing_features_are_not_imputed(self) -> None:
        now = datetime.now(timezone.utc)
        history = [HistoricalSession("2026-09-01", {"gap": 0.1}, now, {})]
        self.assertEqual(rank_analogues("2026-09-03", {"gap": 0.1, "strength": 0.2}, history, now), [])

    def test_outcomes_are_aggregated(self) -> None:
        now = datetime.now(timezone.utc)
        history = [
            HistoricalSession("2026-09-01", {"gap": 0.1}, now, {"return_30m": 1.0, "onh_first": True}),
            HistoricalSession("2026-09-02", {"gap": 0.2}, now, {"return_30m": -1.0, "onh_first": False}),
        ]
        result = rank_analogues("2026-09-03", {"gap": 0.15}, history, now, top_k=2)
        self.assertEqual(result[0].outcome_summary["return_30m_mean"], 0.0)
        self.assertEqual(result[0].outcome_summary["onh_first_rate"], 0.5)

    def test_similar_regimes_endpoint_returns_bounded_matches(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_analogue_repository

        class FakeRepository:
            def list(self, limit=500):
                return [HistoricalSession("2026-09-01", {"gap": 0.1}, datetime(2026, 9, 2, tzinfo=timezone.utc), {})]

        app.dependency_overrides[get_analogue_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).post("/api/v1/regimes/similar", json={"sessionDate": "2026-09-03", "features": {"gap": 0.1}, "predictionTime": "2026-09-03T12:00:00Z", "topK": 20})
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["matches"][0]["session_date"], "2026-09-01")
