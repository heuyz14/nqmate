"""Attach outcomes for predictions that explicitly stored a historical session date."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.bias.outcomes import attach_outcomes
from nqmate_api.bias.repository import SupabaseBiasRepository
from nqmate_api.config import Settings


async def run(limit: int = 100) -> int:
    settings = Settings()
    bias = SupabaseBiasRepository.from_settings(settings)
    sessions = {item.session_date: item for item in SupabaseAnalogueRepository.from_settings(settings).list(1000)}
    attached = 0
    for prediction in bias.history(limit):
        session_date = prediction.get("session_date")
        if not session_date or str(session_date) not in sessions:
            continue
        session = sessions[str(session_date)]
        observed_at = datetime.combine(date.fromisoformat(str(session_date)), time(16), ZoneInfo("America/New_York"))
        for outcome in attach_outcomes(prediction, date.fromisoformat(str(session_date)), session.outcomes, observed_at):
            bias.create_outcome(outcome)
            attached += 1
    return attached


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach completed outcomes to session-linked predictions")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        parser.error("--limit must be between 1 and 100")
    print(f"attached {asyncio.run(run(args.limit))} outcomes", flush=True)


if __name__ == "__main__":
    main()
