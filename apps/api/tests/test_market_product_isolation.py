from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from nqmate_api.market.models import MarketBar, MarketContract, MarketSession
from nqmate_api.market.repository import SupabaseMarketRepository
from nqmate_api.market.store import MarketBarStore


def test_store_defaults_to_nq_and_allows_explicit_es():
    now = datetime(2026, 9, 1, tzinfo=timezone.utc)
    nq = MarketBar("NQU6", now, "1min", 100, 102, 99, 101, 10, "massive", now, now)
    es = replace(nq, symbol="ESU6", close=100)
    store = MarketBarStore()
    store.add_bars([nq, es])
    assert store.get_bars(now, now + timedelta(minutes=1)) == [nq]
    assert store.get_bars(now, now + timedelta(minutes=1), "ESU6") == [es]


@pytest.mark.parametrize("repository", [MarketBarStore(), SupabaseMarketRepository(MagicMock())])
def test_unknown_product_cannot_write_session(repository):
    session = MagicMock()
    session.contract = MarketContract("BAD", "BADU6", "BAD_CONT")
    with pytest.raises(ValueError, match="NQ"):
        repository.upsert_session(session)


def session(product, day=date(2025, 1, 2)):
    return MarketSession(day, 100, 110, 90, 105, 101, 108, 95, 100,
                         None, None, None, None, None, -.01, 13, 2,
                         MarketContract(product, product + "H5", product + "_CONT"))


def test_es_session_is_separate_and_nq_remains_default():
    store = MarketBarStore()
    nq, es = session("NQ"), session("ES")
    store.upsert_session(nq)
    store.upsert_session(es)
    assert store.get_session(nq.session_date) == nq
    assert store.get_session(es.session_date, "ES") == es
    assert store.get_previous_session(date(2025, 1, 3), "ES") == es
    assert store.get_previous_session(date(2025, 1, 3)) == nq


def test_es_repository_payload_uses_supporting_table_and_neutral_names():
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {"id": "contract-id"}
    SupabaseMarketRepository(client).upsert_session(session("ES"))
    assert client.table.call_args.args == ("market_supporting_sessions",)
    payload = client.table.return_value.upsert.call_args.args[0]
    assert payload["regular_open"] == 100
    assert "nq_open" not in payload
    assert payload["product"] == "ES"
    assert client.table.return_value.upsert.call_args.kwargs["on_conflict"] == "product,session_date"
