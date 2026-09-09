from jobs.build_research_manifest import build_manifest


def test_manifest_fails_closed_when_quarantines_remain():
    manifest = build_manifest(
        {"summary": {"eligible": 3, "schedule_adjusted_complete": 1,
                      "not_a_trading_session": 1, "quarantined": 2},
         "sessions": [{"product": "NQ", "session_date": "2025-01-03"}]},
        source_hash="abc123", git_commit="deadbeef",
    )
    assert manifest["certified"] is False
    assert manifest["quarantined_sessions"] == 2
    assert manifest["source_hash"] == "abc123"


def test_manifest_is_certified_only_with_zero_quarantines():
    manifest = build_manifest(
        {"summary": {"eligible": 4, "schedule_adjusted_complete": 1,
                      "not_a_trading_session": 1, "quarantined": 0},
         "sessions": [{"product": "NQ", "session_date": "2025-01-03"},
                      {"product": "ES", "session_date": "2025-01-03"}]},
        source_hash="abc123", git_commit="deadbeef",
    )
    assert manifest["certified"] is True
    assert manifest["session_count"] == 2
