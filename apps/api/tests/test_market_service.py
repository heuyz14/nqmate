import unittest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from nqmate_api.market.models import MarketContract
from nqmate_api.market.service import ingest_session


class MarketIngestionTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_provider_day_is_skipped(self) -> None:
        provider = MagicMock()
        provider.get_bars = AsyncMock(return_value=[])
        repository = MagicMock()
        contract = MarketContract("NQ", "NQU6", "NQ_CONT")

        result = await ingest_session(provider, repository, date(2026, 1, 1), contract)

        self.assertIsNone(result)
        repository.upsert_bars.assert_not_called()
        repository.upsert_session.assert_not_called()
