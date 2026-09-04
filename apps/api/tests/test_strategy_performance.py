import unittest

from nqmate_api.strategies.performance import calculate_performance


class StrategyPerformanceTests(unittest.TestCase):
    def test_calculates_sample_win_rate_expectancy_and_sharpe_like_ratio(self) -> None:
        stats = calculate_performance([{"return_pct": 0.02}, {"return_pct": -0.01}, {"return_pct": 0.03}])

        self.assertEqual(stats["sample_size"], 3.0)
        self.assertAlmostEqual(stats["win_rate"], 2 / 3)
        self.assertAlmostEqual(stats["mean_return"], 0.0133333333)
        self.assertGreater(stats["sharpe_like"], 0)

    def test_ignores_missing_returns_and_leaves_unavailable_mfe_mae_unset(self) -> None:
        stats = calculate_performance([{"return_pct": None}, {"return_pct": 0.01}])

        self.assertEqual(stats["sample_size"], 1.0)
        self.assertIsNone(stats["mfe_mean"])
        self.assertIsNone(stats["mae_mean"])
