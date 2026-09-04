import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from nqmate_api.strategies.setups import SetupOccurrence
from nqmate_api.strategies.setups_repository import SupabaseSetupRepository


class SetupRepositoryTests(unittest.TestCase):
    def test_upsert_is_idempotent_by_strategy_and_session(self) -> None:
        client = MagicMock()
        occurrence = SetupOccurrence("strategy-1", "2026-09-02", datetime(2026, 9, 2, 14, tzinfo=timezone.utc), ("onh_break",))

        SupabaseSetupRepository(client).upsert(occurrence)

        call = client.table.return_value.upsert.call_args
        self.assertEqual(call.kwargs["on_conflict"], "strategy_id,session_date")
        self.assertEqual(call.args[0]["conditions"], ["onh_break"])
