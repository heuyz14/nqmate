"""Classify historical backfill evidence against a reviewed CME exception calendar.

This is report-only. It never changes raw bars or persisted sessions. A schedule
exception is accepted only when its missing-minute pattern exactly matches the
declared exception; all other rows remain quarantined for investigation.
"""

import argparse
import json
from datetime import datetime, time
from pathlib import Path

from nqmate_api.market.calculations import EASTERN


FULL_CLOSURES = {
    "2025-01-01": "New Year's Day", "2025-04-18": "Good Friday",
    "2025-12-25": "Christmas Day", "2026-01-01": "New Year's Day",
    "2026-04-03": "Good Friday",
}

# Equity-index Globex early-close schedules reviewed from CME holiday notices.
# The time is Eastern and represents the first expected absent minute.
EARLY_CLOSES = {
    "2025-01-20": (time(13), "Martin Luther King Jr. Day"),
    "2025-02-17": (time(13), "Presidents' Day"),
    "2025-05-26": (time(13), "Memorial Day"),
    "2025-07-03": (time(13, 15), "Independence Day eve"),
    "2025-07-04": (time(13), "Independence Day"),
    "2025-09-01": (time(13), "Labor Day"),
    "2025-11-27": (time(13), "Thanksgiving Day"),
    "2025-11-28": (time(13), "Day after Thanksgiving"),
    "2025-12-24": (time(13, 15), "Christmas Eve"),
    "2026-01-19": (time(13), "Martin Luther King Jr. Day"),
    "2026-02-16": (time(13), "Presidents' Day"),
    "2026-05-25": (time(13), "Memorial Day"),
    "2026-06-19": (time(13), "Juneteenth"),
    "2026-07-03": (time(13), "Independence Day observed"),
    "2026-09-07": (time(13), "Labor Day"),
}


def _missing_times(row: dict) -> list[datetime]:
    result = []
    for raw in row.get("missing_timestamps", []):
        timestamp = datetime.fromisoformat(raw)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Missing timestamps must be timezone-aware")
        result.append(timestamp.astimezone(EASTERN))
    return result


def classify_session(row: dict) -> dict:
    """Return a conservative certification disposition for one latest-attempt row."""
    day = row["session_date"]
    issues = row.get("issue_counts", {})
    missing = _missing_times(row)
    base = {"product": row["product"], "session_date": day, "contract": row["contract"]}
    if row.get("eligible"):
        return {**base, "classification": "full_session_complete", "certification_status": "eligible"}
    if (day in FULL_CLOSURES and issues == {"missing_minutes": 1320}
            and len(missing) == 1320 and len(set(missing)) == 1320):
        return {**base, "classification": "scheduled_full_closure",
                "certification_status": "not_a_trading_session", "schedule_name": FULL_CLOSURES[day]}
    if day in EARLY_CLOSES and set(issues) == {"missing_minutes"}:
        cutoff, name = EARLY_CLOSES[day]
        expected_missing = (16 * 60) - (cutoff.hour * 60 + cutoff.minute)
        if len(missing) == expected_missing and all(value.time() >= cutoff for value in missing):
            return {**base, "classification": "scheduled_early_close",
                    "certification_status": "schedule_adjusted_complete", "schedule_name": name,
                    "early_close_et": cutoff.isoformat()}
    return {**base, "classification": "data_gap", "certification_status": "quarantined",
            "issue_counts": issues, "missing_minutes": len(missing)}


def certify(batches: list[dict]) -> dict:
    latest: dict[tuple[str, str], dict] = {}
    for batch in batches:
        for row in batch.get("sessions", []):
            if row.get("product") in ("NQ", "ES"):
                latest[row["product"], row["session_date"]] = row
    sessions = [classify_session(row) for _, row in sorted(latest.items())]
    summary = {status: sum(item["certification_status"] == status for item in sessions)
               for status in ("eligible", "schedule_adjusted_complete", "not_a_trading_session", "quarantined")}
    return {"calendar_version": "cme-equity-index-2025-2026-reviewed-v1",
            "scope": "Coverage certification only; point-in-time and rollover certification remain separate.",
            "summary": summary, "sessions": sessions}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="+", help="JSONL reports in attempt order")
    args = parser.parse_args()
    batches = []
    for path in args.report:
        with path.open() as source:
            batches.extend(json.loads(line) for line in source if line.strip())
    print(json.dumps(certify(batches), indent=2))


if __name__ == "__main__":
    main()
