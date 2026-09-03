import unittest

from nqmate_api.bias.models import BiasSnapshot
from nqmate_api.bias.service import score_bias


class BiasTests(unittest.TestCase):
    def test_identical_snapshot_produces_identical_score(self) -> None:
        snapshot = BiasSnapshot(0.8, 0.2, 0.6, 0.4, -0.2, 0.3, None)
        self.assertEqual(score_bias(snapshot), score_bias(snapshot))

    def test_positive_structure_produces_bullish_bias(self) -> None:
        result = score_bias(BiasSnapshot(1, 0.5, 0.8, 0.7, 0.2, 0.4, None))
        self.assertEqual(result.direction, "BULLISH")
        self.assertGreater(result.score, 0)

    def test_critical_catalyst_caps_confidence_and_waits(self) -> None:
        result = score_bias(BiasSnapshot(1, 1, 1, 1, 1, 1, 10))
        self.assertEqual(result.confidence, 0.55)
        self.assertEqual(result.recommendation, "WAIT_FOR_RELEASE")

    def test_inputs_must_be_normalized(self) -> None:
        with self.assertRaises(ValueError):
            score_bias(BiasSnapshot(2, 0, 0, 0, 0, 0, None))

    def test_result_contains_deterministic_evidence_and_invalidation(self) -> None:
        result = score_bias(BiasSnapshot(0.2, 0.1, 0.2, -0.1, 0.1, 0.1, None))
        self.assertTrue(result.evidence)
        self.assertTrue(result.bull_case)
        self.assertTrue(result.bear_case)
        self.assertTrue(result.invalidation)
        self.assertTrue(result.uncertainty)
