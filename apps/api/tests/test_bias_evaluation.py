import unittest

from nqmate_api.bias.evaluation import summarize_prediction_outcomes


class BiasEvaluationTests(unittest.TestCase):
    def test_summarizes_accuracy_returns_and_coverage_by_horizon(self) -> None:
        result = summarize_prediction_outcomes([
            {"horizon": "return_5m", "realized_return": 0.01, "correct": True},
            {"horizon": "return_5m", "realized_return": -0.02, "correct": False},
            {"horizon": "return_15m", "realized_return": 0.0, "correct": None},
        ])
        self.assertEqual(result["sample_size"], 3)
        self.assertEqual(result["horizons"]["return_5m"]["accuracy"], 0.5)
        self.assertAlmostEqual(result["horizons"]["return_5m"]["average_return"], -0.005)
        self.assertEqual(result["horizons"]["return_15m"]["evaluated_size"], 0)
        self.assertIsNone(result["horizons"]["return_15m"]["accuracy"])
