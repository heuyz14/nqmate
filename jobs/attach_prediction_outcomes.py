"""Attach explicitly selected historical session outcomes to a bias prediction."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.bias.outcomes import attach_outcomes
from nqmate_api.bias.repository import SupabaseBiasRepository
from nqmate_api.config import Settings


async def run(prediction_id: str, session_date: date) -> int:
    settings = Settings()
    bias = SupabaseBiasRepository.from_settings(settings)
    prediction = bias.get(prediction_id)
    if prediction is None:
        raise ValueError("bias prediction not found")
    session = next((item for item in SupabaseAnalogueRepository.from_settings(settings).list(1000)
                    if item.session_date == session_date.isoformat()), None)
    if session is None:
        raise ValueError("historical session outcome not found")
    observed_at = datetime.combine(session_date, time(16), ZoneInfo("America/New_York"))
    attached = attach_outcomes(prediction, session_date, session.outcomes, observed_at)
    for outcome in attached:
        bias.create_outcome(outcome)
    return len(attached)


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach historical outcomes to one bias prediction")
    parser.add_argument("--prediction-id", required=True)
    parser.add_argument("--session-date", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    print(f"attached {asyncio.run(run(args.prediction_id, args.session_date))} outcomes", flush=True)


if __name__ == "__main__":
    main()
