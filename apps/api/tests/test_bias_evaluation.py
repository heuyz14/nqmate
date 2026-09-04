import unittest

from nqmate_api.bias.evaluation import confidence_calibration, feature_drift, grouped_outcome_metrics, observability_summary, summarize_prediction_outcomes


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

    def test_confidence_calibration_compares_probability_and_accuracy(self) -> None:
        result = confidence_calibration([
            {"confidence": 0.8, "correct": True}, {"confidence": 0.8, "correct": False},
        ])
        self.assertEqual(result[0]["sample_size"], 2)
        self.assertAlmostEqual(result[0]["observed_accuracy"], 0.5)
        self.assertAlmostEqual(result[0]["calibration_gap"], 0.3)

    def test_feature_drift_classifies_large_shift(self) -> None:
        result = feature_drift(({"gap": 0.0}, {"gap": 0.1}), ({"gap": 1.0}, {"gap": 1.1}))
        self.assertEqual(result["gap"]["status"], "DRIFT")

    def test_grouped_metrics_skip_missing_labels(self) -> None:
        result = grouped_outcome_metrics([
            {"regime": "TREND_UP", "correct": True, "realized_return": 0.01},
            {"regime": "TREND_UP", "correct": False, "realized_return": -0.02},
            {"correct": True, "realized_return": 0.03},
        ], "regime")
        self.assertEqual(result["TREND_UP"]["sample_size"], 2)
        self.assertEqual(result["TREND_UP"]["accuracy"], 0.5)

    def test_observability_reports_coverage(self) -> None:
        result = observability_summary(
            [{"id": "p1", "model_version": "rules-v1", "feature_version": "f1", "input_snapshot": {}}],
            {"p1": 2},
        )
        self.assertEqual(result["outcome_count"], 2)
        self.assertEqual(result["predictions_with_outcomes"], 1)
        self.assertEqual(result["missing_reconstruction_count"], 1)
