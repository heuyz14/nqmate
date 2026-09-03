import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.analogues.repository import SupabaseAnalogueRepository


class AnalogueRepositoryTests(unittest.TestCase):
    def test_upsert_persists_features_outcomes_and_identity(self) -> None:
        client = MagicMock()
        session = HistoricalSession(
            "2026-09-02", {"gap_pct": 0.01}, datetime(2026, 9, 2, 13, 30, tzinfo=timezone.utc),
            {"return_60m": 0.002},
        )

        SupabaseAnalogueRepository(client).upsert(session)

        call = client.table.return_value.upsert.call_args
        self.assertEqual(call.kwargs["on_conflict"], "session_date")
        self.assertEqual(call.args[0]["features"], {"gap_pct": 0.01})
        self.assertEqual(call.args[0]["outcomes"], {"return_60m": 0.002})

    def test_list_maps_supabase_rows_to_historical_sessions(self) -> None:
        client = MagicMock()
        client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [{
            "session_date": "2026-09-02", "features": {"gap_pct": 0.01},
            "outcomes": {"return_60m": 0.002}, "available_at": "2026-09-02T13:30:00+00:00",
        }]

        sessions = SupabaseAnalogueRepository(client).list()

        self.assertEqual(sessions[0].session_date, "2026-09-02")
        self.assertEqual(sessions[0].outcomes["return_60m"], 0.002)
        self.assertEqual(sessions[0].available_at.tzinfo, timezone.utc)
