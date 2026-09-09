from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from postgrest.exceptions import APIError

from jobs.backfill_research_market import backfill
from nqmate_api.market.models import MarketBar, MarketContract
from nqmate_api.market.quality import session_window
from nqmate_api.market.calculations import build_market_session
from nqmate_api.market.store import MarketBarStore


@pytest.mark.asyncio
async def test_paired_batches_preserve_contract_state_and_report_missing_data():
    provider = MagicMock()
    provider.get_contract = AsyncMock(side_effect=lambda product, day: MarketContract(
        product, product + ("U6" if day < date(2026, 9, 4) else "Z6"),
        product + "_CONT", date(2026, 9, 4) if day < date(2026, 9, 4) else date(2026, 12, 18),
    ))
    provider.get_bars = AsyncMock(return_value=[])
    repository = MarketBarStore()
    reports = await backfill(date(2026, 9, 4), date(2026, 9, 7), provider, repository)
    assert len(reports) == 2
    assert all(len(batch["sessions"]) == 2 for batch in reports)
    assert all(not row["eligible"] for batch in reports for row in batch["sessions"])
    assert {roll.product for roll in repository._rollovers.values()} == {"NQ", "ES"}
    assert all(roll.roll_date == date(2026, 9, 4) for roll in repository._rollovers.values())
    assert repository.get_session(date(2026, 9, 4)) is None


@pytest.mark.asyncio
async def test_reversed_range_rejected_before_external_calls():
    provider = MagicMock()
    with pytest.raises(ValueError):
        await backfill(date(2026, 9, 4), date(2026, 9, 3), provider, MarketBarStore())
    provider.get_contract.assert_not_called()


@pytest.mark.asyncio
async def test_wrong_product_metadata_fails_closed():
    provider = MagicMock()
    provider.get_contract = AsyncMock(return_value=MarketContract("ES", "ESU6", "ES_CONT"))
    with pytest.raises(ValueError, match="contract"):
        await backfill(date(2026, 9, 4), date(2026, 9, 4), provider, MarketBarStore())


@pytest.mark.asyncio
async def test_paired_raw_minutes_are_idempotent_and_do_not_create_sessions():
    day = date(2026, 9, 4)
    start, end = session_window(day)
    provider = MagicMock()
    provider.get_contract = AsyncMock(side_effect=lambda product, day: MarketContract(
        product, product + "U6", product + "_CONT", date(2026, 9, 18),
    ))
    provider.get_bars = AsyncMock(side_effect=lambda symbol, start_day, end_day: [
        MarketBar(symbol, start + timedelta(minutes=i), "1min", 100, 102, 99, 101,
                  10, "massive", end, start + timedelta(minutes=i + 1))
        for i in range(1320)
    ])
    repository = MarketBarStore()
    first = await backfill(day, day, provider, repository)
    assert first[0]["eligible_product_sessions"] == 2
    assert len(repository.get_bars(start, end)) == 1320
    assert len(repository.get_bars(start, end, "ESU6")) == 1320
    second = await backfill(day, day, provider, repository)
    assert second[0]["eligible_product_sessions"] == 2
    assert len(repository._bars) == 2640
    assert repository.get_session(day) is None
    prior_day = day - timedelta(days=1)
    prior_start, prior_end = session_window(prior_day)
    prior_bars = [MarketBar(
        "NQM6", prior_start + timedelta(minutes=i), "1min", 90, 92, 89, 91,
        10, "massive", prior_end, prior_end,
    ) for i in range(1320)]
    repository.upsert_session(build_market_session(
        prior_bars, prior_day, MarketContract("NQ", "NQM6", "NQ_CONT"),
    ))
    await backfill(day, day, provider, repository, reconstruct_nq=True)
    assert repository.get_session(day).contract.product == "NQ"
    assert repository.get_session(day).nq_close == 101
    assert repository.get_session(day).gap_points is None
    assert repository.get_session(day).prior_day_high is None
    await backfill(day, day, provider, repository, reconstruct_es=True)
    assert repository.get_session(day, "ES").contract.product == "ES"
    assert repository.get_session(day).contract.product == "NQ"


@pytest.mark.asyncio
async def test_incomplete_minutes_never_create_session():
    provider = MagicMock()
    provider.get_contract = AsyncMock(side_effect=lambda product, day: MarketContract(
        product, product + "U6", product + "_CONT", date(2026, 9, 18)))
    provider.get_bars = AsyncMock(return_value=[])
    repository = MarketBarStore()
    await backfill(date(2026, 9, 4), date(2026, 9, 4), provider, repository, reconstruct_nq=True)
    assert repository.get_session(date(2026, 9, 4)) is None


@pytest.mark.asyncio
async def test_transient_database_failure_retries_entire_day_idempotently():
    day = date(2026, 9, 4)
    start, end = session_window(day)
    provider = MagicMock()
    provider.get_contract = AsyncMock(side_effect=lambda product, _: MarketContract(
        product, product + "U6", product + "_CONT", date(2026, 9, 18)))
    provider.get_bars = AsyncMock(side_effect=lambda symbol, *_: [
        MarketBar(symbol, start + timedelta(minutes=i), "1min", 100, 102, 99, 101,
                  10, "massive", end, end) for i in range(1320)])
    repository = MarketBarStore()
    original = repository.upsert_bars
    attempts = 0
    def flaky(items):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise APIError({"code": "500", "message": "temporary"})
        return original(items)
    repository.upsert_bars = flaky
    reports = await backfill(day, day, provider, repository, retries=1, retry_delay_seconds=0)
    assert reports[0]["eligible_product_sessions"] == 2
    assert attempts >= 3
    assert len(repository._bars) == 2640
