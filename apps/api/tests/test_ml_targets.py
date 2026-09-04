import unittest

from nqmate_api.ml.targets import DIRECTION_HORIZONS_MINUTES, direction_target_names


class MlTargetContractTests(unittest.TestCase):
    def test_required_direction_horizons_are_explicit(self) -> None:
        self.assertEqual(DIRECTION_HORIZONS_MINUTES, (5, 15, 30, 60, 120, 240))
        self.assertEqual(direction_target_names(), ("direction_5m", "direction_15m", "direction_30m", "direction_60m", "direction_120m", "direction_240m", "direction_close"))
