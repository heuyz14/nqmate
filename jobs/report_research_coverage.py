"""Summarize saved backfill JSONL without database/provider calls or mutations."""

import argparse
import json
from datetime import date, datetime, time
from pathlib import Path

from nqmate_api.market.calculations import EASTERN


def summarize(batches: list[dict]) -> dict:
    latest: dict[tuple[str, str], dict] = {}
    failures = []
    for batch in batches:
        if batch.get("status") == "failed":
            failures.append(batch.get("error_type", "unknown"))
        for row in batch.get("sessions", []):
            date.fromisoformat(row["session_date"])
            if row["product"] not in ("NQ", "ES"):
                raise ValueError("Unexpected product")
            latest[row["product"], row["session_date"]] = row
    products = {}
    eligible_dates = {}
    for product in ("NQ", "ES"):
        rows = sorted((row for (p, _), row in latest.items() if p == product),
                      key=lambda row: row["session_date"])
        eligible_dates[product] = {row["session_date"] for row in rows if row["eligible"]}
        exclusions = []
        for row in rows:
            if row["eligible"]:
                continue
            overnight = regular = 0
            for raw in row["missing_timestamps"]:
                timestamp = datetime.fromisoformat(raw)
                if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    raise ValueError("Missing timestamps must be timezone-aware")
                local = timestamp.astimezone(EASTERN)
                if local.date().isoformat() == row["session_date"] and time(9, 30) <= local.time() < time(16):
                    regular += 1
                else:
                    overnight += 1
            exclusions.append({"date": row["session_date"], "contract": row["contract"],
                               "issues": row["issue_counts"],
                               "overnight_missing_minutes": overnight,
                               "regular_missing_minutes": regular})
        products[product] = {
            "processed_dates": len(rows), "eligible_dates": len(eligible_dates[product]),
            "excluded_dates": len(exclusions),
            "reconstructed_dates": sum(bool(row.get("session_reconstructed")) for row in rows),
            "exclusions": exclusions,
        }
    dates = sorted(day for _, day in latest)
    return {"first_date": dates[0] if dates else None, "last_date": dates[-1] if dates else None,
            "products": products, "paired_eligible_dates": len(eligible_dates["NQ"] & eligible_dates["ES"]),
            "failures": failures,
            "scope": "Latest logged attempt per product/date; coverage only. Holiday and rollover causes require separate verification."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="+",
                        help="JSONL reports in attempt order; later attempts replace earlier product/date results")
    args = parser.parse_args()
    batches = []
    for path in args.report:
        with path.open() as source:
            batches.extend(json.loads(line) for line in source if line.strip())
    print(json.dumps(summarize(batches), indent=2))


if __name__ == "__main__":
    main()
