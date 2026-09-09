import pytest

from jobs.report_research_coverage import summarize


def row(product="NQ", eligible=False, missing=None):
    return {"product": product, "session_date": "2025-01-03", "contract": product + "H5",
            "quality_version": "v1", "eligible": eligible,
            "session_reconstructed": eligible and product == "NQ",
            "missing_timestamps": missing or [], "issue_counts": {} if eligible else {"missing_minutes": len(missing or [])}}


def test_retries_do_not_inflate_independent_dates():
    report = summarize([{"sessions": [row()]}, {"sessions": [row(eligible=True), row("ES", True)]}])
    assert report["products"]["NQ"]["processed_dates"] == 1
    assert report["paired_eligible_dates"] == 1
    assert report["products"]["NQ"]["excluded_dates"] == 0


def test_missing_minutes_are_classified_in_eastern_time():
    report = summarize([{"sessions": [row(missing=["2025-01-03T13:00:00+00:00", "2025-01-03T14:30:00+00:00"])]}])
    exclusion = report["products"]["NQ"]["exclusions"][0]
    assert exclusion["overnight_missing_minutes"] == 1
    assert exclusion["regular_missing_minutes"] == 1
    assert report["paired_eligible_dates"] == 0


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError):
        summarize([{"sessions": [row(missing=["2025-01-03T13:00:00"])]}])


def test_failure_records_are_retained():
    assert summarize([{"status": "failed", "error_type": "ConnectError"}])["failures"] == ["ConnectError"]
