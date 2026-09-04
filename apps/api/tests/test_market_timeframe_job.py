import unittest
from datetime import date, datetime, timezone

from jobs.populate_market_timeframes import parse_timeframes, source_window


class MarketTimeframeJobTests(unittest.TestCase):
    def test_default_horizon_names_are_accepted(self) -> None:
        self.assertEqual(parse_timeframes("5m,15m,1h,2h,4h,1d"), ("5m", "15m", "1h", "2h", "4h", "1d"))

    def test_alias_horizons_are_accepted(self) -> None:
        self.assertEqual(parse_timeframes("120m,240m"), ("120m", "240m"))

    def test_source_window_is_point_in_time_bounded(self) -> None:
        start, end = source_window(date(2026, 9, 1), date(2026, 9, 2))
        self.assertEqual(start, datetime(2026, 8, 31, 22, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2026, 9, 2, 20, 1, tzinfo=timezone.utc))

    def test_unknown_horizon_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_timeframes("5m,3m")
