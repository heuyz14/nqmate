import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from nqmate_api.market.models import MarketBar, MarketContract, MarketSession
from nqmate_api.market.repository import SupabaseMarketRepository


class MarketRepositoryTests(unittest.TestCase):
    def test_upsert_bars_uses_provider_identity_conflict_key(self) -> None:
        client = MagicMock()
        repository = SupabaseMarketRepository(client)
        timestamp = datetime(2026, 9, 1, tzinfo=timezone.utc)
        item = MarketBar("NQU6", timestamp, "1min", 100, 102, 99, 101, 10, "massive", timestamp, timestamp)

        self.assertEqual(repository.upsert_bars([item]), 1)
        client.table.assert_called_with("market_bars")
        client.table.return_value.upsert.assert_called_once()
        self.assertEqual(
            client.table.return_value.upsert.call_args.kwargs["on_conflict"],
            "symbol,timestamp,timeframe,provider",
        )

    def test_upsert_empty_bars_does_not_call_database(self) -> None:
        client = MagicMock()

        self.assertEqual(SupabaseMarketRepository(client).upsert_bars([]), 0)
        client.table.assert_not_called()

    def test_get_session_returns_none_when_supabase_has_no_response(self) -> None:
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = None

        result = SupabaseMarketRepository(client).get_session(date(2026, 9, 1))

        self.assertIsNone(result)
