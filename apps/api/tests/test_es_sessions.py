from datetime import date, timedelta

from fastapi.testclient import TestClient

from jobs.reconstruct_es_sessions import reconstruct
from nqmate_api.main import app, get_market_repository
from nqmate_api.market.models import MarketBar, MarketContract, MarketSession
from nqmate_api.market.quality import session_window
from nqmate_api.market.store import MarketBarStore


def test_reconstruct_es_reuses_stored_minutes_and_keeps_nq_separate():
    day = date(2025, 1, 2)
    start, end = session_window(day)
    store = MarketBarStore()
    store.add_bars([MarketBar("ESH5", start + timedelta(minutes=i), "1min", 100, 102, 99, 101,
                             10, "massive", end, end) for i in range(1320)])
    result = reconstruct(store, day, MarketContract("ES", "ESH5", "ES_CONT"))
    assert result["session_reconstructed"]
    assert store.get_session(day) is None
    assert store.get_session(day, "ES").supporting_payload()["regular_close"] == 101
    assert reconstruct(store, day, MarketContract("ES", "ESH5", "ES_CONT")) == result


def test_incomplete_es_cannot_create_session():
    store = MarketBarStore()
    result = reconstruct(store, date(2025, 1, 2), MarketContract("ES", "ESH5", "ES_CONT"))
    assert not result["session_reconstructed"]
    assert store.get_session(date(2025, 1, 2), "ES") is None


def test_es_is_supporting_completed_context_and_missing_is_explicit():
    day = date(2025, 1, 2)
    store = MarketBarStore()
    def save(product, close):
        store.save_session(MarketSession(day, 100, 110, 90, close, 101, 108, 95, 100,
                                         None, None, None, None, None, -.01, 13, 2,
                                         MarketContract(product, product + "H5", product + "_CONT")))
    save("NQ", 105)
    app.dependency_overrides[get_market_repository] = lambda: store
    try:
        client = TestClient(app)
        url = "/api/v1/market/nq/supporting-context?session_date=2025-01-02"
        assert client.get(url).json()["status"] == "missing_es_session"
        save("ES", 103)
        result = client.get(url).json()
        assert result["primary_symbol"] == "NQ"
        assert result["context_type"] == "completed_session"
        assert abs(result["nq_es_relative_strength"] - .02) < 1e-10
        assert result["es_session"]["regular_close"] == 103
        assert "nq_close" not in result["es_session"]
    finally:
        app.dependency_overrides.clear()
