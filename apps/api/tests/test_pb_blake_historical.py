import unittest
from datetime import datetime, timezone

from nqmate_api.market.models import MarketBar, MarketContract, MarketSession
from nqmate_api.strategies.pb_blake_historical import build_pb_inputs


class PbHistoricalInputTests(unittest.TestCase):
    def test_builder_only_uses_available_timeframes_and_fails_closed_without_liquidity(self) -> None:
        session = MarketSession(
            session_date=datetime(2026, 9, 2, tzinfo=timezone.utc).date(), nq_open=100, nq_high=105, nq_low=95, nq_close=102,
            overnight_open=99, overnight_high=101, overnight_low=98, overnight_close=100, prior_day_high=104,
            prior_day_low=96, prior_day_close=100, gap_points=0, gap_pct=0, overnight_return=0, overnight_range=3,
            atr_14=2, contract=MarketContract("NQ", "NQU6", "NQ_CONT", datetime(2026, 9, 18, tzinfo=timezone.utc).date(), None),
        )
        bars = [MarketBar("NQU6", datetime(2026, 9, 2, 13, 30, tzinfo=timezone.utc), "1m", 100, 100.5, 99.5, 100, 1, "massive", datetime.now(timezone.utc), datetime(2026, 9, 2, 13, 30, tzinfo=timezone.utc))]

        result = build_pb_inputs(session, bars, datetime(2026, 9, 2, 14, tzinfo=timezone.utc))

        self.assertIsNone(result["liquidity"])
        self.assertEqual(result["inversions"], ())
        self.assertIsNone(result["entry"])
