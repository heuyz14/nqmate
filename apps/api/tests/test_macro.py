import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx

from nqmate_api.macro.models import MacroObservation
from nqmate_api.macro.providers import BLSProvider, BLSReleaseCalendarProvider, BEAProvider, FREDProvider


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

    async def test_bls_calendar_parses_release_timestamp(self) -> None:
        ics = "BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:employment-2026-09-04\nDTSTART;TZID=America/New_York:20260904T083000\nSUMMARY:Employment Situation\nEND:VEVENT\nEND:VCALENDAR"
        response = httpx.Response(200, text=ics, request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await BLSReleaseCalendarProvider("https://example.test", client=client).fetch()
        self.assertEqual(result[0].title, "Employment Situation")
        self.assertEqual(result[0].release_id, "employment-2026-09-04")
        self.assertEqual(result[0].scheduled_at.isoformat(), "2026-09-04T12:30:00+00:00")

    async def test_fred_provider_preserves_vintage_boundary(self) -> None:
        response = httpx.Response(200, json={"observations": [{
            "realtime_start": "2026-09-01", "realtime_end": "2026-09-02",
            "date": "2026-08-01", "value": "4.25"
        }]}, request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await FREDProvider("test-key", client=client).fetch("DFF", realtime_start="2026-09-01", realtime_end="2026-09-02")
        self.assertEqual(result[0].period, "2026-08-01")
        self.assertEqual(result[0].value, 4.25)
        self.assertEqual(result[0].vintage_date.isoformat(), "2026-09-01T00:00:00+00:00")

    async def test_bea_provider_maps_official_data(self) -> None:
        response = httpx.Response(200, json={"BEAAPI": {"Results": {"Data": [{
            "LineDescription": "Personal consumption expenditures", "TimePeriod": "2026Q2", "DataValue": "123.4"
        }]}}}, request=httpx.Request("GET", "https://example.test"))
        client = AsyncMock(spec=httpx.AsyncClient); client.get.return_value = response
        result = await BEAProvider("test-key", client=client).fetch("NIPA", "T10101", "1", "2026Q2")
        self.assertEqual(result[0].period, "2026Q2")
        self.assertEqual(result[0].value, 123.4)

    def test_observation_is_point_in_time_eligible_only_with_release_or_retrieval_timestamp(self) -> None:
        observation = MacroObservation("CPI", "2026-08", 324.123, None, datetime.now(timezone.utc), None)
        self.assertIsNotNone(observation.retrieved_at)

    def test_macro_repository_persists_timestamp_fields(self) -> None:
        from unittest.mock import MagicMock
        from nqmate_api.macro.repository import SupabaseMacroRepository

        observation = MacroObservation("CUUR0000SA0", "2026-08", 324.123, None, datetime.now(timezone.utc), None)
        client = MagicMock()
        SupabaseMacroRepository(client).upsert(observation)
        payload = client.table.return_value.upsert.call_args.args[0]
        self.assertEqual(payload["series_id"], "CUUR0000SA0")
        self.assertIsNone(payload["released_at"])
        self.assertIn("retrieved_at", payload)

    def test_macro_observations_endpoint_reads_repository(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_macro_repository

        class FakeMacroRepository:
            def list(self, series_id=None, limit=100):
                return [{"series_id": series_id, "period": "2026-08", "value": 324.123}]

        app.dependency_overrides[get_macro_repository] = lambda: FakeMacroRepository()
        try:
            response = TestClient(app).get("/api/v1/macro/observations?series_id=CUUR0000SA0&limit=1")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["observations"][0]["period"], "2026-08")
