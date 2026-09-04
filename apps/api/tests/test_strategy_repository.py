import unittest
from unittest.mock import MagicMock

from nqmate_api.strategies.models import Strategy
from nqmate_api.strategies.repository import SupabaseStrategyRepository


class StrategyRepositoryTests(unittest.TestCase):
    def test_create_serializes_structured_rules(self) -> None:
        client = MagicMock()
        strategy = Strategy("Test", "Description", ("GAP_UP",), ("gap",), ("break",), ("close",), "entry", "target", "stop", True)

        SupabaseStrategyRepository(client).create(strategy)

        payload = client.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload["name"], "Test")
        self.assertEqual(payload["required_conditions"], ["gap"])
