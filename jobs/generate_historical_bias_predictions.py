"""Generate evaluation-only, session-linked bias predictions from stored pre-session inputs."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, time
from typing import Mapping
from zoneinfo import ZoneInfo

from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.bias.models import BiasSnapshot
from nqmate_api.bias.repository import SupabaseBiasRepository
from nqmate_api.bias.service import score_bias
from nqmate_api.config import Settings

EASTERN = ZoneInfo("America/New_York")


def clamp(value: float) -> float:
    return max(-1.0, min(1.0, value))


def snapshot_from_features(features: Mapping[str, float]) -> BiasSnapshot:
    """Map only stored pre-session fields; unavailable context stays neutral."""
    return BiasSnapshot(
        overnight_structure=clamp(float(features.get("overnight_return", 0.0)) / 0.005),
        gap=clamp(float(features.get("gap_pct", 0.0)) / 0.005),
        technical_location=0.0,
        relative_strength=0.0,
        macro_context=0.0,
        news_context=0.0,
        minutes_to_high_impact_event=None,
    )


async def replay(start: date, end: date, limit: int = 100) -> int:
    settings = Settings()
    analogue = SupabaseAnalogueRepository.from_settings(settings)
    bias = SupabaseBiasRepository.from_settings(settings)
    existing = {str(item.get("session_date")) for item in bias.history(100)}
    created = 0
    for session in sorted(analogue.list(limit), key=lambda item: item.session_date):
        if not start.isoformat() <= session.session_date <= end.isoformat() or session.session_date in existing:
            continue
        snapshot = snapshot_from_features(session.features)
        bias.create(snapshot, score_bias(snapshot), date.fromisoformat(session.session_date))
        created += 1
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Create evaluation-only historical bias predictions")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.end < args.start or args.limit < 1 or args.limit > 1000:
        parser.error("end must be on or after start and limit must be between 1 and 1000")
    print(f"historical bias predictions created: {asyncio.run(replay(args.start, args.end, args.limit))}", flush=True)


if __name__ == "__main__":
    main()
