import unittest

from nqmate_api.strategies.models import Strategy
from nqmate_api.strategies.service import validate_strategy


class StrategyTests(unittest.TestCase):
    def test_structured_strategy_validates_required_logic(self) -> None:
        strategy = Strategy(
            name="ONH Breakout Retest", description="Test", allowed_regimes=("GAP_UP",),
            required_conditions=("price_above_overnight_midpoint",), confirmation_conditions=("onh_break",),
            invalidation_conditions=("close_below_onh",), entry_logic="enter_on_retest",
            target_logic="prior_range_extension", stop_logic="close_below_onh", active=True,
        )
        self.assertIsNone(validate_strategy(strategy))

    def test_strategy_requires_name_and_entry_exit_rules(self) -> None:
        strategy = Strategy("", "", (), (), (), (), "", "", "", True)
        with self.assertRaises(ValueError):
            validate_strategy(strategy)
