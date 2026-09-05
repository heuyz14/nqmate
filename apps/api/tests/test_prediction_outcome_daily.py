import unittest
from unittest.mock import AsyncMock, patch

from jobs.attach_completed_prediction_outcomes_daily import attach_daily


class DailyPredictionOutcomeTests(unittest.IsolatedAsyncioTestCase):
    async def test_daily_attachment_delegates_to_bounded_idempotent_job(self) -> None:
        with patch("jobs.attach_completed_prediction_outcomes_daily.run", new=AsyncMock(return_value=5)) as attach:
            result = await attach_daily()

        self.assertEqual(result, 5)
        attach.assert_awaited_once_with(100)
