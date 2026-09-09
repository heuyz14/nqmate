from jobs.certify_market_sessions import classify_session


def row(day: str, missing: list[str], product: str = "NQ") -> dict:
    return {
        "product": product,
        "session_date": day,
        "contract": "NQH5",
        "eligible": False,
        "issue_counts": {"missing_minutes": len(missing)},
        "missing_timestamps": missing,
    }


def test_known_full_closure_is_classified_only_when_the_entire_session_is_absent():
    missing = [f"2024-12-31T{hour:02d}:{minute:02d}:00+00:00"
               for hour in range(22, 24) for minute in range(60)]
    missing += [f"2025-01-01T{hour:02d}:{minute:02d}:00+00:00"
                for hour in range(24) for minute in range(60)]
    missing = missing[:1320]
    classified = classify_session(row("2025-01-01", missing))
    assert classified["classification"] == "scheduled_full_closure"
    assert classified["certification_status"] == "not_a_trading_session"


def test_known_early_close_is_classified_only_when_all_missing_minutes_follow_cutoff():
    missing = [f"2025-01-20T{hour:02d}:{minute:02d}:00+00:00"
               for hour in range(18, 21) for minute in range(60)]
    classified = classify_session(row("2025-01-20", missing))
    assert classified["classification"] == "scheduled_early_close"
    assert classified["certification_status"] == "schedule_adjusted_complete"


def test_unexpected_missing_minute_on_known_early_close_remains_a_data_gap():
    missing = ["2025-01-20T14:00:00+00:00"]
    classified = classify_session(row("2025-01-20", missing))
    assert classified["classification"] == "data_gap"
    assert classified["certification_status"] == "quarantined"
