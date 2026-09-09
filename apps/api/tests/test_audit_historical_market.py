from datetime import date
from unittest.mock import MagicMock

import pytest

from jobs.audit_historical_market import audit_history
from nqmate_api.market.models import MarketContract


def test_missing_sessions_are_reported_without_querying_unscoped_bars():
    repository = MagicMock()
    repository.get_session.return_value = None
    report = audit_history(repository, date(2026, 9, 3), date(2026, 9, 6))
    assert report["candidate_sessions"] == report["quarantined_sessions"] == 2
    assert report["eligible_sessions"] == 0
    assert report["sessions"][0]["issue_counts"] == {"missing_session": 1}
    repository.get_bars.assert_not_called()


def test_existing_session_audits_only_its_raw_contract():
    repository = MagicMock()
    repository.get_session.return_value.contract = MarketContract("NQ", "NQU6", "NQ_CONT")
    repository.get_bars.return_value = []
    report = audit_history(repository, date(2026, 9, 3), date(2026, 9, 3))
    assert report["quarantined_sessions"] == 1
    assert report["sessions"][0]["issue_counts"] == {"missing_minutes": 1320}
    assert repository.get_bars.call_args.kwargs["symbol"] == "NQU6"
    repository.upsert_session.assert_not_called()
    repository.upsert_bars.assert_not_called()


def test_invalid_date_range_is_rejected_before_repository_access():
    repository = MagicMock()
    with pytest.raises(ValueError):
        audit_history(repository, date(2026, 9, 4), date(2026, 9, 3))
    repository.get_session.assert_not_called()


def test_es_session_cannot_be_certified_as_nq():
    repository = MagicMock()
    repository.get_session.return_value.contract = MarketContract("ES", "ESU6", "ES_CONT")
    report = audit_history(repository, date(2026, 9, 3), date(2026, 9, 3))
    assert report["sessions"][0]["issue_counts"] == {"contract_mismatch": 1}
    repository.get_bars.assert_not_called()
