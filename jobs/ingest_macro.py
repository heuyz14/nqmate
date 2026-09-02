from __future__ import annotations

import argparse
import asyncio
from datetime import date

from nqmate_api.config import Settings
from nqmate_api.macro.providers import BLSProvider, BLSReleaseCalendarProvider
from nqmate_api.macro.service import persist_observations, release_to_calendar_event
from nqmate_api.macro.repository import SupabaseMacroRepository
from nqmate_api.news.repository import SupabaseNewsRepository


async def ingest_once(series_ids: list[str], start_year: int, end_year: int, skip_calendar: bool) -> tuple[int, int]:
    settings = Settings()
    news_repository = SupabaseNewsRepository.from_settings(settings)
    observation_repository = SupabaseMacroRepository.from_settings(settings)
    release_count = 0
    observation_count = 0
    if not skip_calendar:
        releases = await BLSReleaseCalendarProvider(settings.bls_release_calendar_url).fetch()
        for release in releases:
            news_repository.upsert_calendar_event(release_to_calendar_event(release))
        release_count = len(releases)
    if series_ids:
        provider = BLSProvider(settings.bls_api_key)
        for series_id in series_ids:
            observations = await provider.fetch(series_id, start_year, end_year)
            observation_count += persist_observations(observation_repository, observations)
    return release_count, observation_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest official BLS releases and observations")
    parser.add_argument("--series-id", action="append", default=[])
    parser.add_argument("--start-year", type=int, default=date.today().year)
    parser.add_argument("--end-year", type=int, default=date.today().year)
    parser.add_argument("--skip-calendar", action="store_true")
    args = parser.parse_args()
    releases, observations = asyncio.run(ingest_once(args.series_id, args.start_year, args.end_year, args.skip_calendar))
    print(f"macro update completed: {releases} BLS releases, {observations} observations", flush=True)


if __name__ == "__main__":
    main()
