import unittest
from datetime import datetime, timedelta, timezone

from nqmate_api.ml.baselines import LabeledRow
from nqmate_api.ml.calibration import expected_calibration_error, evaluate_multiple_windows, promotion_eligible


class MlCalibrationTests(unittest.TestCase):
    def test_expected_calibration_error_is_zero_for_perfect_bins(self) -> None:
        self.assertAlmostEqual(expected_calibration_error((1, 0), (0.99, 0.01)), 0.01)

    def test_promotion_requires_accuracy_gain_and_brier_not_worse(self) -> None:
        self.assertTrue(promotion_eligible({"accuracy": 0.60, "brier_score": 0.20}, {"accuracy": 0.55, "brier_score": 0.20}))
        self.assertFalse(promotion_eligible({"accuracy": 0.60, "brier_score": 0.21}, {"accuracy": 0.55, "brier_score": 0.20}))

    def test_multiple_windows_returns_one_result_per_window(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = tuple(LabeledRow(base + timedelta(days=i), base + timedelta(days=i), (float(i),), i % 2, None) for i in range(12))
        result = evaluate_multiple_windows(rows, train_sizes=(4, 6), test_size=2)
        self.assertEqual(tuple(result), (4, 6))
        self.assertEqual(result[4]["majority"]["sample_size"], 14.0)

    def test_multiple_windows_can_include_boosting_models(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = tuple(LabeledRow(base + timedelta(days=i), base + timedelta(days=i), (float(i),), i % 2, None) for i in range(12))
        result = evaluate_multiple_windows(rows, train_sizes=(4,), test_size=2, include_all_boosting=True)
        self.assertIn("lightgbm", result[4])
