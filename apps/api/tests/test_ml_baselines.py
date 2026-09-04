import unittest
from datetime import datetime, timedelta, timezone

from nqmate_api.ml.baselines import (
    LabeledRow,
    always_long_probability,
    fit_logistic,
    majority_probability,
    overnight_direction_probability,
    predict_logistic,
)
from nqmate_api.ml.validation import point_in_time_rows, walk_forward_splits


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def row(index: int, target: int, overnight: float | None = None, available_offset: int = 0) -> LabeledRow:
    timestamp = BASE + timedelta(days=index)
    return LabeledRow(timestamp, timestamp + timedelta(minutes=available_offset), (float(index),), target, overnight)


class MlBaselineTests(unittest.TestCase):
    def test_baselines_are_deterministic(self) -> None:
        labels = (0, 1, 1, 1)
        self.assertEqual(majority_probability(labels), 0.75)
        self.assertEqual(always_long_probability(labels), 1.0)
        self.assertEqual(overnight_direction_probability(0.02), 1.0)
        self.assertEqual(overnight_direction_probability(-0.02), 0.0)
        self.assertIsNone(overnight_direction_probability(None))

    def test_logistic_learns_simple_direction(self) -> None:
        model = fit_logistic(((0.0,), (1.0,), (2.0,), (3.0,)), (0, 0, 1, 1))
        probabilities = predict_logistic(model, ((0.0,), (3.0,)))
        self.assertLess(probabilities[0], 0.5)
        self.assertGreater(probabilities[1], 0.5)

    def test_point_in_time_filter_excludes_future_available_rows(self) -> None:
        rows = (row(0, 1), row(1, 0, available_offset=60))
        eligible = point_in_time_rows(rows, BASE + timedelta(days=1, minutes=30))
        self.assertEqual(len(eligible), 1)

    def test_walk_forward_is_ordered_and_has_no_overlap(self) -> None:
        rows = tuple(row(index, index % 2) for index in range(6))
        splits = list(walk_forward_splits(rows, min_train_size=3, test_size=1))
        self.assertEqual([(len(train), len(test)) for train, test in splits], [(3, 1), (4, 1), (5, 1)])
        self.assertLess(splits[0][0][-1].feature_timestamp, splits[0][1][0].feature_timestamp)

