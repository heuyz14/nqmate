import unittest
from datetime import date, datetime, time, timezone

from nqmate_api.market.models import MarketBar, MarketContract, MarketSession
from nqmate_api.strategies.models import Strategy
from nqmate_api.strategies.setups import detect_setup


def session() -> MarketSession:
    return MarketSession(date(2026, 9, 2), 100, 110, 90, 105, 100, 104, 98, 101, 107, 91, 104, 0, 0, 0, 5, 2, MarketContract("NQ", "NQU6", "NQ_CONT"))


def bar(minute: int, high: float, low: float) -> MarketBar:
    timestamp = datetime(2026, 9, 2, 13, minute, tzinfo=timezone.utc)
    return MarketBar("NQU6", timestamp, "1min", 101, high, low, 102, 1, "massive", timestamp, timestamp)


class SetupTests(unittest.TestCase):
    def test_detects_onh_break_when_all_supported_conditions_occur(self) -> None:
        strategy = Strategy("ONH Break", "", (), ("onh_break", "price_above_overnight_midpoint"), (), (), "entry", "target", "stop", True)

        occurrence = detect_setup("strategy-1", strategy, session(), [bar(30, 103, 99), bar(31, 109, 100)])

        self.assertIsNotNone(occurrence)
        self.assertEqual(occurrence.strategy_id, "strategy-1")
        self.assertEqual(occurrence.trigger_at, datetime(2026, 9, 2, 13, 31, tzinfo=timezone.utc))

    def test_unknown_condition_fails_closed(self) -> None:
        strategy = Strategy("Unknown", "", (), ("llm_decides",), (), (), "entry", "target", "stop", True)

        self.assertIsNone(detect_setup("strategy-1", strategy, session(), [bar(30, 109, 100)]))
