import unittest
from datetime import date

from fastapi.testclient import TestClient

from nqmate_api.main import app, get_market_repository
from nqmate_api.market.models import MarketContract, MarketSession


class MarketApiTests(unittest.TestCase):
    def test_analogue_features_endpoint_returns_pre_session_features(self) -> None:
        class FakeRepository:
            def get_session(self, session_date):
                return MarketSession(
                    session_date, 100, 110, 90, 105, 101, 108, 95, 100,
                    107, 91, 104, 1, 0.01, -0.01, 13,
                    2, MarketContract("NQ", "NQU6", "NQ_CONT"),
                )

        app.dependency_overrides[get_market_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/market/nq/analogue-features?session_date=2026-09-02")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["features"]["overnight_range"], 13)
        self.assertEqual(response.json()["features"]["prior_day_high_distance"], 1)
