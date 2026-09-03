import unittest
from datetime import date

from nqmate_api.graph.regimes import classify_market_regime
from nqmate_api.market.models import MarketContract, MarketSession


class GraphRegimeTests(unittest.TestCase):
    def test_classifies_market_dimensions_independently(self) -> None:
        session = MarketSession(
            date(2026, 9, 2), 100, 112, 90, 108, 101, 110, 95, 105,
            107, 91, 104, 1, 0.01, 0.006, 5, 2, MarketContract("NQ", "NQU6", "NQ_CONT"),
        )

        dimensions = classify_market_regime(session, yield_change=0.02, high_impact_events=1, minutes_to_event=10)

        self.assertEqual(dimensions.overnight_direction, "STRONG_UP")
        self.assertEqual(dimensions.overnight_volatility, "HIGH")
        self.assertEqual(dimensions.gap, "GAP_UP")
        self.assertEqual(dimensions.location, "INSIDE_PRIOR_RANGE")
        self.assertEqual(dimensions.yield_regime, "YIELDS_UP")
        self.assertEqual(dimensions.catalyst_regime, "PRE_EVENT")

    def test_missing_macro_context_uses_neutral_defaults(self) -> None:
        session = MarketSession(
            date(2026, 9, 2), 100, 110, 90, 105, 100, 104, 98, 101,
            107, 91, 104, 0, 0.0, 0.0, 5, 2, MarketContract("NQ", "NQU6", "NQ_CONT"),
        )

        dimensions = classify_market_regime(session)

        self.assertEqual(dimensions.yield_regime, "YIELDS_FLAT")
        self.assertEqual(dimensions.catalyst_regime, "NO_MAJOR_EVENT")
