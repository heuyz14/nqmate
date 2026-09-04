import unittest
from datetime import datetime, timedelta, timezone

from nqmate_api.market.models import MarketBar
from nqmate_api.strategies.pb_blake import LiquidityEvent
from nqmate_api.strategies.pb_blake_data import detect_fvgs, detect_post_liquidity_inversions


BASE = datetime(2026, 9, 4, 14, tzinfo=timezone.utc)


def bar(index: int, open_: float, high: float, low: float, close: float) -> MarketBar:
    timestamp = BASE + timedelta(minutes=index)
    return MarketBar("NQ", timestamp, "5m", open_, high, low, close, 1, "test", timestamp, timestamp)


class PbBlakeDataTests(unittest.TestCase):
    def test_detects_bearish_fvg(self) -> None:
        gaps = detect_fvgs((bar(0, 100, 105, 99, 104), bar(1, 104, 106, 103, 105), bar(2, 108, 110, 107, 109)), "5m")
        self.assertEqual(gaps[0].direction, "bullish")
        self.assertEqual((gaps[0].lower, gaps[0].upper), (105, 107))

    def test_detects_short_inversion_after_liquidity(self) -> None:
        bars = (bar(0, 100, 105, 99, 104), bar(1, 104, 106, 103, 105), bar(2, 108, 110, 107, 109), bar(3, 106, 108, 101, 102))
        event = LiquidityEvent("PDH", 111, BASE - timedelta(minutes=1))
        inversions = detect_post_liquidity_inversions(bars, "5m", event)
        self.assertEqual(inversions[0].direction, "SHORT")
        self.assertEqual(inversions[0].confirmed_at, BASE + timedelta(minutes=3))

    def test_excludes_bars_not_available_at_observation_time(self) -> None:
        delayed = bar(2, 108, 110, 107, 109)
        delayed = MarketBar(**{**delayed.__dict__, "available_at": BASE + timedelta(minutes=10)})
        self.assertEqual(detect_fvgs((bar(0, 100, 105, 99, 104), bar(1, 104, 106, 103, 105), delayed), "5m"), ())
