"""Register the available versioned feature/target datasets in Supabase."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date

from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.config import Settings
from nqmate_api.ml.evaluation import dataset_records_for_sessions
from nqmate_api.ml.repository import SupabaseMlRepository


async def run(start: date, end: date) -> int:
    settings = Settings()
    analogue = SupabaseAnalogueRepository.from_settings(settings)
    sessions = [item for item in analogue.list(1000) if start.isoformat() <= item.session_date <= end.isoformat()]
    records = dataset_records_for_sessions(sessions, start, end)
    registry = SupabaseMlRepository.from_settings(settings)
    for record in records:
        registry.upsert_dataset(record)
        print(f"registered {record.target}: {record.row_count} rows", flush=True)
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Register available versioned ML datasets")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(f"registered {asyncio.run(run(args.start, args.end))} datasets", flush=True)


if __name__ == "__main__":
    main()
