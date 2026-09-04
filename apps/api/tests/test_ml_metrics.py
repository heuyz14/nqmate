import unittest

from nqmate_api.ml.baselines import LabeledRow
from nqmate_api.ml.metrics import classification_metrics, evaluate_walk_forward
from datetime import datetime, timedelta, timezone


class MlMetricsTests(unittest.TestCase):
    def test_classification_metrics_are_deterministic(self) -> None:
        metrics = classification_metrics((0, 1, 1, 0), (0.1, 0.8, 0.7, 0.2))
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertAlmostEqual(metrics["brier_score"], 0.045)
        self.assertIsNotNone(metrics["roc_auc"])
        self.assertAlmostEqual(metrics["expected_calibration_error"], 0.2)

    def test_walk_forward_compares_all_baselines(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = tuple(
            LabeledRow(base + timedelta(days=index), base + timedelta(days=index), (float(index),), index % 2, 0.01 if index % 2 else -0.01)
            for index in range(8)
        )
        result = evaluate_walk_forward(rows, min_train_size=4, test_size=2)
        self.assertEqual(set(result), {"majority", "always_long", "overnight_direction", "logistic"})
        self.assertEqual(result["logistic"]["sample_size"], 6.0)

    def test_walk_forward_can_include_xgboost_challenger(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = tuple(LabeledRow(base + timedelta(days=index), base + timedelta(days=index), (float(index),), index % 2, None) for index in range(8))
        result = evaluate_walk_forward(rows, min_train_size=4, test_size=2, include_xgboost=True)
        self.assertEqual(result["xgboost"]["sample_size"], 6.0)

    def test_walk_forward_can_compare_all_boosting_implementations(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = tuple(LabeledRow(base + timedelta(days=index), base + timedelta(days=index), (float(index),), index % 2, None) for index in range(8))
        result = evaluate_walk_forward(rows, min_train_size=4, test_size=2, include_all_boosting=True)
        self.assertEqual(set(("xgboost", "sklearn_gradient_boosting", "lightgbm")) - set(result), set())
