import unittest
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from nqmate_api.main import app, get_market_repository
from nqmate_api.market.models import MarketBar, MarketContract, MarketSession


class MarketApiTests(unittest.TestCase):
    def test_bars_endpoint_does_not_reaggregate_persisted_timeframes(self) -> None:
        timestamp = datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc)

        class FakeRepository:
            def get_bars(self, start, end, symbol=None):
                return [
                    MarketBar("NQU6", timestamp, "1min", 100, 101, 99, 100.5, 1, "massive", timestamp, timestamp),
                    MarketBar("NQU6", timestamp, "5m", 100, 105, 99, 104, 5, "massive", timestamp, timestamp),
                ]

        app.dependency_overrides[get_market_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/market/nq/bars?start=2026-09-01&end=2026-09-02&timeframe=5m")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["bars"]), 1)
        self.assertEqual(response.json()["bars"][0]["close"], 104)

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
