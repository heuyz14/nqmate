import unittest
from datetime import datetime, timedelta, timezone

from nqmate_api.market.models import MarketBar
from nqmate_api.ml.dataset import build_direction_targets, build_feature_matrix


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bar(index: int, close: float) -> MarketBar:
    timestamp = BASE + timedelta(minutes=index)
    return MarketBar("NQ", timestamp, "1min", close, close, close, close, 1, "test", timestamp, timestamp)


class MlDatasetTests(unittest.TestCase):
    def test_builds_forward_direction_without_imputing_missing_horizons(self) -> None:
        targets = build_direction_targets((bar(0, 100), bar(5, 101), bar(10, 99)), (5, 10))
        self.assertEqual(targets[(BASE, 5)], 1)
        self.assertEqual(targets[(BASE, 10)], 0)

    def test_feature_matrix_is_versioned_and_rejects_leaky_rows(self) -> None:
        snapshots = [
            {"feature_timestamp": BASE, "available_at": BASE, "session_date": "2026-01-01", "features": {"gap": 1.0}},
            {"feature_timestamp": BASE + timedelta(minutes=5), "available_at": BASE + timedelta(minutes=6), "session_date": "2026-01-01", "features": {"gap": 2.0}},
        ]
        targets = {(BASE, 5): 1}
        dataset = build_feature_matrix(snapshots, targets, horizon_minutes=5, feature_version="v1")
        self.assertEqual(dataset.version, "v1")
        self.assertEqual(len(dataset.rows), 1)
        self.assertEqual(dataset.rows[0].target, 1)

