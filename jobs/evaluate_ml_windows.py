from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date

from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.config import Settings
from nqmate_api.ml.calibration import evaluate_multiple_windows
from nqmate_api.ml.evaluation import rows_from_sessions


async def run(start: date, end: date, train_sizes: tuple[int, ...], test_size: int, outcome_name: str = "return_60m") -> dict[int, dict[str, dict[str, float | None]]]:
    sessions = [item for item in SupabaseAnalogueRepository.from_settings(Settings()).list(1000) if start.isoformat() <= item.session_date <= end.isoformat()]
    rows = rows_from_sessions(sessions, outcome_name)
    return evaluate_multiple_windows(rows, train_sizes, test_size, include_all_boosting=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-window ML validation on stored historical rows")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--train-sizes", default="20,40,60")
    parser.add_argument("--test-size", type=int, default=10)
    parser.add_argument("--outcome-name", default="return_60m")
    args = parser.parse_args()
    if args.end < args.start or args.test_size < 1:
        parser.error("invalid date range or test size")
    train_sizes = tuple(int(value) for value in args.train_sizes.split(",") if value)
    if not train_sizes or any(value < 1 for value in train_sizes):
        parser.error("--train-sizes must contain positive integers")
    print(json.dumps(asyncio.run(run(args.start, args.end, train_sizes, args.test_size, args.outcome_name)), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
