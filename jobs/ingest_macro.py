from __future__ import annotations

import argparse
import asyncio

from nqmate_api.config import Settings
from nqmate_api.macro.providers import BLSReleaseCalendarProvider
from nqmate_api.macro.service import release_to_calendar_event
from nqmate_api.news.repository import SupabaseNewsRepository


async def ingest_once() -> int:
    settings = Settings()
    repository = SupabaseNewsRepository.from_settings(settings)
    releases = await BLSReleaseCalendarProvider(settings.bls_release_calendar_url).fetch()
    for release in releases:
        repository.upsert_calendar_event(release_to_calendar_event(release))
    return len(releases)


def main() -> None:
    argparse.ArgumentParser(description="Ingest the official BLS release calendar").parse_args()
    count = asyncio.run(ingest_once())
    print(f"macro calendar update completed: {count} BLS releases", flush=True)


if __name__ == "__main__":
    main()
