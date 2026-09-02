import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx

from nqmate_api.macro.models import MacroObservation
from nqmate_api.macro.providers import BLSProvider, BLSReleaseCalendarProvider, BEAProvider, FREDProvider
from nqmate_api.macro.service import release_to_calendar_event
from nqmate_api.news.models import EconomicCalendarEvent, CalendarImpact


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
        self.assertIn("User-Agent", client.get.await_args.kwargs["headers"])

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

    def test_bls_release_maps_to_high_impact_usd_calendar_event(self) -> None:
        from nqmate_api.news.models import CalendarImpact
        from nqmate_api.macro.models import ScheduledRelease

        release = ScheduledRelease("employment-1", "Employment Situation", datetime(2026, 9, 4, 12, 30, tzinfo=timezone.utc))
        event = release_to_calendar_event(release)
        self.assertEqual(event.source, "bls")
        self.assertEqual(event.currency, "USD")
        self.assertEqual(event.impact, CalendarImpact.HIGH)
        self.assertEqual(event.scheduled_at, release.scheduled_at)

    def test_bls_release_mapping_does_not_mark_every_release_high_impact(self) -> None:
        from nqmate_api.news.models import CalendarImpact
        from nqmate_api.macro.models import ScheduledRelease

        release = ScheduledRelease("other-1", "Import and Export Price Indexes", datetime(2026, 9, 10, 12, 30, tzinfo=timezone.utc))
        self.assertEqual(release_to_calendar_event(release).impact, CalendarImpact.MEDIUM)

    def test_persist_observations_returns_count(self) -> None:
        from nqmate_api.macro.service import persist_observations

        class FakeRepository:
            def __init__(self): self.items = []
            def upsert(self, observation): self.items.append(observation)

        observations = [MacroObservation("CPI", "2026-08", 1.0, None, datetime.now(timezone.utc), None)]
        repository = FakeRepository()
        self.assertEqual(persist_observations(repository, observations), 1)
        self.assertEqual(repository.items, observations)

    def test_event_surprise_is_actual_minus_forecast(self) -> None:
        from nqmate_api.macro.service import event_surprise
        event = EconomicCalendarEvent("CPI", "USD", CalendarImpact.HIGH, datetime.now(timezone.utc), "bls", actual=3.4, forecast=3.1)
        self.assertEqual(event_surprise(event), 0.3)
        self.assertIsNone(event_surprise(EconomicCalendarEvent("CPI", "USD", CalendarImpact.HIGH, datetime.now(timezone.utc), "bls")))

    def test_release_link_updates_only_explicit_observation(self) -> None:
        from nqmate_api.macro.models import ScheduledRelease
        from nqmate_api.macro.service import link_release_timestamp

        class FakeRepository:
            def set_released_at(self, series_id, period, released_at):
                self.value = (series_id, period, released_at)

        observation = MacroObservation("CPI", "2026-08", 3.4, None, datetime.now(timezone.utc), None)
        release = ScheduledRelease("cpi-1", "Consumer Price Index", datetime(2026, 9, 11, 12, 30, tzinfo=timezone.utc))
        repository = FakeRepository(); link_release_timestamp(repository, observation, release)
        self.assertEqual(repository.value, ("CPI", "2026-08", release.scheduled_at))

    def test_surprise_interpretation_is_event_specific_for_inflation(self) -> None:
        from nqmate_api.macro.service import interpret_surprise
        self.assertEqual(interpret_surprise("CPI", 0.2)["expected_nq_direction"], "BEARISH")
        self.assertEqual(interpret_surprise("CPI", -0.2)["expected_nq_direction"], "BULLISH")

    def test_surprise_interpretation_handles_zero_and_unknown_events(self) -> None:
        from nqmate_api.macro.service import interpret_surprise
        self.assertEqual(interpret_surprise("CPI", 0)["expected_nq_direction"], "NEUTRAL")
        self.assertEqual(interpret_surprise("Unknown Release", 1)["expected_nq_direction"], "UNKNOWN")

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
