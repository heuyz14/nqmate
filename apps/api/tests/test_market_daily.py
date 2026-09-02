import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from jobs.ingest_market_daily import ingest_daily


class DailyMarketUpdateTests(unittest.IsolatedAsyncioTestCase):
    async def test_daily_update_delegates_to_bounded_ingestion(self) -> None:
        with patch("jobs.ingest_market_daily.run", new=AsyncMock(return_value=1)) as ingest:
            result = await ingest_daily(date(2026, 8, 31))

        self.assertEqual(result, 1)
        ingest.assert_awaited_once_with(date(2026, 8, 31), date(2026, 8, 31))
