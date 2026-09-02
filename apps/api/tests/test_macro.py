import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx

from nqmate_api.macro.models import MacroObservation
from nqmate_api.macro.providers import BLSProvider


class MacroTests(unittest.IsolatedAsyncioTestCase):
    async def test_bls_provider_normalizes_observation_without_inventing_release_time(self) -> None:
        response = httpx.Response(200, json={"status": "REQUEST_SUCCEEDED", "Results": {"series": [{
            "seriesID": "CUUR0000SA0", "data": [{"year": "2026", "period": "M08", "periodName": "August", "value": "324.123"}]
        }]}}, request=httpx.Request("POST", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient)
        client.post.return_value = response

        result = await BLSProvider(client=client).fetch("CUUR0000SA0", 2026, 2026)

        self.assertEqual(result[0].series_id, "CUUR0000SA0")
        self.assertEqual(result[0].period, "2026-08")
        self.assertEqual(result[0].value, 324.123)
        self.assertIsNone(result[0].released_at)
        self.assertIsNotNone(result[0].retrieved_at)

    async def test_bls_provider_rejects_unsuccessful_response(self) -> None:
        response = httpx.Response(200, json={"status": "REQUEST_FAILED", "message": ["bad series"]}, request=httpx.Request("POST", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient)
        client.post.return_value = response
        with self.assertRaises(ValueError):
            await BLSProvider(client=client).fetch("bad", 2026, 2026)

    def test_observation_is_point_in_time_eligible_only_with_release_or_retrieval_timestamp(self) -> None:
        observation = MacroObservation("CPI", "2026-08", 324.123, None, datetime.now(timezone.utc), None)
        self.assertIsNotNone(observation.retrieved_at)
