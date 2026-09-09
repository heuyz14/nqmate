import unittest
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from nqmate_api.main import app, get_market_repository
from nqmate_api.market.models import MarketBar, MarketContract, MarketSession


class MarketApiTests(unittest.TestCase):
    def test_api_allows_local_web_origin(self) -> None:
        response = TestClient(app).options(
            "/api/v1/strategies",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    def test_bars_endpoint_does_not_reaggregate_persisted_timeframes(self) -> None:
        timestamp = datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc)

        class FakeRepository:
            def get_session(self, session_date):
                return None

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

    def test_chart_excludes_old_contract_after_session_recovery(self) -> None:
        from nqmate_api.market.store import MarketBarStore
        store = MarketBarStore()
        day = date(2025, 3, 21)
        store.save_session(MarketSession(day, 100, 110, 90, 105, 101, 108, 95, 100,
                                        None, None, None, None, None, -.01, 13, 2,
                                        MarketContract("NQ", "NQM5", "NQ_CONT")))
        timestamp = datetime(2025, 3, 21, 12, 0, tzinfo=timezone.utc)
        store.add_bars([MarketBar(symbol, timestamp, "1min", 100, 102, 99, 101, 10,
                                 "massive", timestamp, timestamp) for symbol in ("NQH5", "NQM5")])
        app.dependency_overrides[get_market_repository] = lambda: store
        try:
            result = TestClient(app).get("/api/v1/market/nq/bars?start=2025-03-20&end=2025-03-21").json()
        finally:
            app.dependency_overrides.clear()
        self.assertEqual([bar["symbol"] for bar in result["bars"]], ["NQM5"])

    def test_features_use_only_selected_contract_minute_bars(self) -> None:
        from nqmate_api.market.store import MarketBarStore
        store = MarketBarStore()
        day = date(2025, 3, 21)
        store.save_session(MarketSession(day, 100, 110, 90, 105, 101, 108, 95, 100,
                                        None, None, None, None, None, -.01, 13, 2,
                                        MarketContract("NQ", "NQM5", "NQ_CONT")))
        timestamp = datetime(2025, 3, 21, 14, 0, tzinfo=timezone.utc)
        store.add_bars([
            MarketBar("NQM5", timestamp, "1min", 100, 100, 100, 100, 10, "massive", timestamp, timestamp),
            MarketBar("NQH5", timestamp, "1min", 200, 200, 200, 200, 10, "massive", timestamp, timestamp),
            MarketBar("NQM5", timestamp, "5m", 300, 300, 300, 300, 10, "massive", timestamp, timestamp),
        ])
        app.dependency_overrides[get_market_repository] = lambda: store
        try:
            result = TestClient(app).get("/api/v1/market/nq/features?session_date=2025-03-21").json()
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(result["features"]["vwap"], 100)

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
