import unittest
from datetime import date, datetime, timedelta, timezone

from nqmate_api.market.calculations import aggregate_bars, atr, build_market_session, has_complete_session_bars, weekly_opening_gaps
from nqmate_api.market.models import MarketBar, MarketContract, MarketSession


def bar(timestamp: datetime, value: float, provider: str = "test") -> MarketBar:
    return MarketBar(
        symbol="NQ",
        timestamp=timestamp,
        timeframe="1min",
        open=value,
        high=value + 2,
        low=value - 1,
        close=value + 1,
        volume=10,
        provider=provider,
        ingested_at=timestamp,
        available_at=timestamp,
    )


class MarketCalculationTests(unittest.TestCase):
    def test_weekly_opening_gap_uses_prior_session_close(self) -> None:
        contract = MarketContract("NQ", "NQU6", "NQ_CONT")
        friday = MarketSession(date(2026, 8, 28), 100, 110, 90, 105, 0, 0, 0, 0, None, None, None, None, None, None, 0, None, contract)
        monday = MarketSession(date(2026, 8, 31), 110, 115, 100, 112, 0, 0, 0, 0, None, None, 105, None, None, None, 0, None, contract)

        result = weekly_opening_gaps([monday, friday])

        self.assertEqual(result[0].gap_points, 5)
        self.assertAlmostEqual(result[0].gap_pct, 5 / 105)

    def test_aggregate_bars_preserves_ohlcv_and_point_in_time_availability(self) -> None:
        first = bar(datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc), 100)
        second = bar(datetime(2026, 9, 1, 13, 31, tzinfo=timezone.utc), 105)

        result = aggregate_bars([second, first], "1h")

        self.assertEqual(len(result), 1)
        self.assertEqual((result[0].open, result[0].high, result[0].low, result[0].close), (100, 107, 99, 106))
        self.assertEqual(result[0].available_at, second.available_at)

    def test_aggregate_rejects_unknown_timeframe(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_bars([], "15m")

    def test_holiday_with_prior_day_bars_is_not_a_complete_session(self) -> None:
        bars = [bar(datetime(2025, 12, 31, 15, 0, tzinfo=timezone.utc), 100)]

        self.assertFalse(has_complete_session_bars(bars, date(2026, 1, 1)))

    def test_session_calculates_overnight_levels_and_gap(self) -> None:
        session_date = date(2026, 9, 1)
        bars = [
            bar(datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc), 100),
            bar(datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc), 110),
        ]
        prior = MarketSession(
            session_date=date(2026, 8, 31), nq_open=95, nq_high=108, nq_low=92, nq_close=105,
            overnight_open=94, overnight_high=107, overnight_low=93, overnight_close=104,
            prior_day_high=None, prior_day_low=None, prior_day_close=None, gap_points=None,
            gap_pct=None, overnight_return=None, overnight_range=14, atr_14=None,
            contract=MarketContract("NQ", "NQU6", "NQ_CONT"),
        )
        result = build_market_session(bars, session_date, prior.contract, prior)

        self.assertEqual(result.overnight_high, 102)
        self.assertEqual(result.overnight_low, 99)
        self.assertEqual(result.nq_open, 110)
        self.assertEqual(result.gap_points, 5)
        self.assertAlmostEqual(result.gap_pct, 5 / 105)
        self.assertAlmostEqual(result.overnight_return, 1 / 100)

    def test_atr_requires_period_bars_and_uses_true_ranges(self) -> None:
        bars = [bar(datetime(2026, 9, 1, 13, i, tzinfo=timezone.utc), 100 + i) for i in range(14)]

        self.assertIsNone(atr(bars[:13], period=14))
        self.assertAlmostEqual(atr(bars, period=14), 3)

    def test_session_rejects_missing_regular_bars(self) -> None:
        with self.assertRaisesRegex(ValueError, "No regular-session bars"):
            build_market_session(
                [bar(datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc), 100)],
                date(2026, 9, 1),
                MarketContract("NQ", "NQU6", "NQ_CONT"),
            )
