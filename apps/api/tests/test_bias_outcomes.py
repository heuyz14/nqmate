import unittest
from datetime import date, datetime, timezone

from nqmate_api.bias.outcomes import attach_outcomes


class BiasOutcomeTests(unittest.TestCase):
    def test_attaches_numeric_horizons_and_evaluates_direction(self) -> None:
        outcomes = attach_outcomes(
            {"id": "p1", "direction": "BULLISH"}, date(2026, 9, 2),
            {"return_5m": 0.01, "return_15m": None, "open_close": -0.02},
            datetime(2026, 9, 2, 20, tzinfo=timezone.utc),
        )
        self.assertEqual([item.horizon for item in outcomes], ["return_5m", "open_close"])
        self.assertTrue(outcomes[0].correct)
        self.assertFalse(outcomes[1].correct)

    def test_neutral_prediction_has_no_directional_correctness(self) -> None:
        result = attach_outcomes(
            {"id": "p1", "direction": "NEUTRAL"}, date(2026, 9, 2), {"return_5m": 0.01},
            datetime(2026, 9, 2, 20, tzinfo=timezone.utc),
        )
        self.assertIsNone(result[0].correct)

    def test_missing_prediction_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            attach_outcomes({}, date(2026, 9, 2), {"return_5m": 0.01}, datetime.now(timezone.utc))
