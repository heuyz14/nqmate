import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from nqmate_api.strategies.outcomes import StrategyOutcome
from nqmate_api.strategies.outcomes_repository import SupabaseOutcomeRepository


class StrategyOutcomeRepositoryTests(unittest.TestCase):
    def test_upsert_is_idempotent_by_setup(self) -> None:
        client = MagicMock()
        outcome = StrategyOutcome("setup-1", "strategy-1", "2026-09-02", datetime(2026, 9, 2, 15, tzinfo=timezone.utc), 0.01, 0.02, -0.005, "TREND_UP")

        SupabaseOutcomeRepository(client).upsert(outcome)

        call = client.table.return_value.upsert.call_args
        self.assertEqual(call.kwargs["on_conflict"], "setup_id")
        self.assertEqual(call.args[0]["return_pct"], 0.01)
        self.assertEqual(call.args[0]["regime"], "TREND_UP")

    def test_list_returns_outcome_payloads(self) -> None:
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [{"return_pct": 0.02}]

        result = SupabaseOutcomeRepository(client).list_for_strategy("strategy-1")

        self.assertEqual(result, [{"return_pct": 0.02}])
