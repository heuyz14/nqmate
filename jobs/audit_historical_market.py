"""Read-only canonical NQ minute audit. JSON goes to stdout; no market writes."""

import argparse
import json
from dataclasses import asdict
from datetime import date
from typing import Any

from jobs.ingest_market import trading_dates
from nqmate_api.config import Settings
from nqmate_api.market.quality import QUALITY_VERSION, audit_session_bars, session_window
from nqmate_api.market.repository import MarketRepository, SupabaseMarketRepository


def audit_history(repository: MarketRepository, start: date, end: date) -> dict[str, Any]:
    if end < start:
        raise ValueError("end must be on or after start")
    sessions: list[dict[str, Any]] = []
    for day in trading_dates(start, end):
        session = repository.get_session(day)
        issue = ("missing_session" if session is None else
                 "contract_mismatch" if session.contract.product != "NQ" else None)
        if issue:
            sessions.append({"session_date": day, "eligible": False, "issue_counts": {issue: 1}})
            continue
        window_start, window_end = session_window(day)
        bars = repository.get_bars(window_start, window_end, symbol=session.contract.raw_contract_symbol)
        result = audit_session_bars(bars, day, session.contract)
        sessions.append({**asdict(result), "eligible": result.eligible})
    eligible = sum(row["eligible"] for row in sessions)
    return {
        "quality_version": QUALITY_VERSION,
        "start_date": start, "end_date": end,
        "candidate_sessions": len(sessions),
        "eligible_sessions": eligible,
        "quarantined_sessions": len(sessions) - eligible,
        "scope": "minute coverage only; not dataset, rollover or point-in-time certification",
        "schedule": "weekday candidates, 18:00 previous day to 16:00 ET; holidays/short days require review",
        "sessions": sessions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    repository = SupabaseMarketRepository.from_settings(Settings())
    report = audit_history(repository, args.start, args.end)
    print(json.dumps(report, default=lambda value: value.isoformat(), indent=2))
    return 1 if report["quarantined_sessions"] or not report["candidate_sessions"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
