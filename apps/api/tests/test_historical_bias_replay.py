import unittest

from jobs.generate_historical_bias_predictions import snapshot_from_features


class HistoricalBiasReplayTests(unittest.TestCase):
    def test_replay_mapping_is_bounded_and_keeps_unavailable_context_neutral(self) -> None:
        snapshot = snapshot_from_features({
            "overnight_return": 0.0025,
            "gap_pct": -0.001,
            "overnight_range": 250.0,
            "atr_14": 20.0,
            "prior_day_high_distance": -10.0,
            "prior_day_low_distance": 40.0,
        })

        self.assertEqual(snapshot.overnight_structure, 0.5)
        self.assertEqual(snapshot.gap, -0.2)
        self.assertEqual(snapshot.technical_location, 0.0)
        self.assertEqual(snapshot.relative_strength, 0.0)
        self.assertEqual(snapshot.macro_context, 0.0)
        self.assertEqual(snapshot.news_context, 0.0)
