import unittest
from datetime import datetime, timezone

from nqmate_api.strategies.pb_blake import HtfContext, Inversion, LiquidityEvent, assess_pb_setup


NOW = datetime(2026, 9, 4, 14, tzinfo=timezone.utc)


class PbBlakeTests(unittest.TestCase):
    def test_valid_setup_requires_post_liquidity_highest_timeframe_inversion(self) -> None:
        result = assess_pb_setup(
            contexts=(HtfContext("1H", "bullish", True), HtfContext("4H", "bullish", True)),
            liquidity=LiquidityEvent("PDL", 100.0, NOW),
            inversions=(Inversion("1m", "LONG", 101.0, 102.0, NOW.replace(minute=2)), Inversion("5m", "LONG", 101.0, 103.0, NOW.replace(minute=5))),
            entry=101.0, stop=99.0, targets=(105.0, 110.0), analyzed_at=NOW.replace(minute=10),
        )

        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.inversion_timeframe, "5m")
        self.assertEqual(result.stop_distance, 2.0)
        self.assertEqual(result.risk_rewards, (2.0, 4.5))

    def test_inversion_before_liquidity_event_is_not_valid(self) -> None:
        result = assess_pb_setup(
            contexts=(HtfContext("1H", "bearish", True),),
            liquidity=LiquidityEvent("PDH", 110.0, NOW),
            inversions=(Inversion("5m", "SHORT", 108.0, 109.0, NOW.replace(hour=13, minute=59)),),
            entry=108.0, stop=111.0, targets=(105.0,), analyzed_at=NOW.replace(minute=10),
        )

        self.assertEqual(result.status, "NO_SETUP")
        self.assertIn("inversion must occur after liquidity event", result.missing)

    def test_missing_stop_or_target_is_developing_not_valid(self) -> None:
        result = assess_pb_setup(
            contexts=(HtfContext("1H", "bullish", True),),
            liquidity=LiquidityEvent("PDL", 100.0, NOW),
            inversions=(Inversion("5m", "LONG", 101.0, 103.0, NOW.replace(minute=5)),),
            entry=101.0, stop=None, targets=(), analyzed_at=NOW.replace(minute=10),
        )

        self.assertEqual(result.status, "DEVELOPING")
