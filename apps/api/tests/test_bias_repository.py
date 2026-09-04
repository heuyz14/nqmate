import unittest
from unittest.mock import MagicMock

from nqmate_api.bias.models import BiasResult, BiasSnapshot
from nqmate_api.bias.repository import SupabaseBiasRepository


class BiasRepositoryTests(unittest.TestCase):
    def test_create_persists_exact_input_snapshot(self) -> None:
        client = MagicMock()
        snapshot = BiasSnapshot(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 12)
        result = BiasResult("BULLISH", 0.4, 0.7, "TRADE", "LOW")

        SupabaseBiasRepository(client).create(snapshot, result)

        payload = client.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload["input_snapshot"]["gap"], 0.2)
        self.assertEqual(payload["input_snapshot"]["minutes_to_high_impact_event"], 12)
