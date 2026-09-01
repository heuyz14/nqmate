import unittest
from datetime import date

from jobs.backfill_market_weeks import week_ranges


class WeeklyBackfillTests(unittest.TestCase):
    def test_ranges_are_inclusive_and_clipped(self) -> None:
        self.assertEqual(
            week_ranges(date(2026, 1, 1), date(2026, 1, 14)),
            [
                (date(2026, 1, 1), date(2026, 1, 4)),
                (date(2026, 1, 5), date(2026, 1, 11)),
                (date(2026, 1, 12), date(2026, 1, 14)),
            ],
        )
