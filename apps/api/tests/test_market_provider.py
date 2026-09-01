import unittest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import httpx

from nqmate_api.market.contracts import ContinuousContractResolver
from nqmate_api.market.models import MarketContract
from nqmate_api.market.providers import MassiveMarketDataProvider
from nqmate_api.market.store import MarketBarStore
from nqmate_api.market.models import MarketBar


class ContractTests(unittest.TestCase):
    def test_resolver_selects_nearest_unexpired_contract(self) -> None:
        contracts = [
            MarketContract("NQ", "NQZ6", "NQ_CONT", date(2026, 12, 18)),
            MarketContract("NQ", "NQU6", "NQ_CONT", date(2026, 9, 18)),
        ]

        result = ContinuousContractResolver().resolve("NQ", date(2026, 9, 1), contracts)

        self.assertEqual(result.raw_contract_symbol, "NQU6")

    def test_resolver_rejects_missing_contract(self) -> None:
        with self.assertRaises(LookupError):
            ContinuousContractResolver().resolve("NQ", date(2027, 1, 1), [])


class StoreTests(unittest.TestCase):
    def test_store_deduplicates_provider_bar_identity(self) -> None:
        from datetime import datetime, timezone
        from nqmate_api.market.models import MarketBar

        timestamp = datetime(2026, 9, 1, tzinfo=timezone.utc)
        item = MarketBar("NQ", timestamp, "1min", 1, 2, 0, 1, 10, "massive", timestamp, timestamp)
        store = MarketBarStore()

        self.assertEqual(store.add_bars([item, item]), 1)


class MassiveProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_maps_massive_response_to_market_bars(self) -> None:
        response = httpx.Response(
            200,
            json={"results": [{"window_start": 1756733400000, "open": 100, "high": 103, "low": 99, "close": 102, "volume": 42}]},
            request=httpx.Request("GET", "https://example.test"),
        )
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = response
        provider = MassiveMarketDataProvider("test-key", base_url="https://example.test", client=client)

        bars = await provider.get_bars("NQU6", date(2026, 9, 1), date(2026, 9, 1))

        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].close, 102)
        self.assertEqual(bars[0].provider, "massive")
        client.get.assert_awaited_once()


class MarketEndpointTests(unittest.TestCase):
    def test_session_endpoint_returns_session_contract_and_levels(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_market_repository
        from nqmate_api.market.models import MarketSession

        session_date = date(2026, 9, 1)
        contract = MarketContract("NQ", "NQU6", "NQ_CONT", date(2026, 9, 18))
        session = MarketSession(
            session_date, 100, 110, 90, 105, 98, 108, 96, 104,
            109, 89, 99, 1, 0.01, 0.02, 12, 3, contract,
        )
        fake_repository = MarketBarStore()
        fake_repository.save_session(session)
        app.dependency_overrides[get_market_repository] = lambda: fake_repository

        try:
            response = TestClient(app).get(f"/api/v1/market/nq/session/{session_date.isoformat()}")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["overnight_high"], 108)
        self.assertEqual(response.json()["contract"]["raw_contract_symbol"], "NQU6")
