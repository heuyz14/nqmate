from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from nqmate_api.config import Settings
from nqmate_api.news.providers import FedRSSNewsProvider, ForexFactoryCalendarProvider, MarketauxNewsProvider
from nqmate_api.news.repository import SupabaseNewsRepository
from nqmate_api.news.nlp import CachedNewsExtractor, GeminiNewsExtractor, NewsEventExtractor
from nqmate_api.news.service import persist_articles, persist_calendar

DEFAULT_FED_RSS_URL = "https://www.federalreserve.gov/feeds/press_all.xml"


async def ingest_once() -> tuple[int, int]:
    settings = Settings()
    repository = SupabaseNewsRepository.from_settings(settings)
    article_count = 0
    calendar_count = 0
    articles_to_persist = []
    extractor: NewsEventExtractor | None = None
    if settings.news_nlp_enabled and settings.gemini_api_key:
        extractor = CachedNewsExtractor(GeminiNewsExtractor(settings.gemini_api_key, settings.gemini_model).extract)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    if settings.marketaux_enabled and settings.marketaux_api_key:
        articles = await MarketauxNewsProvider(settings.marketaux_api_key).fetch(published_after=recent_cutoff)
        articles_to_persist.extend(articles)
    if settings.federal_reserve_enabled:
        articles = await FedRSSNewsProvider(settings.fed_rss_url or DEFAULT_FED_RSS_URL).fetch()
        articles_to_persist.extend(articles)
    article_count = persist_articles(repository, articles_to_persist, extractor)
    if settings.forex_factory_enabled and settings.forex_factory_calendar_url:
        events = await ForexFactoryCalendarProvider(
            settings.forex_factory_calendar_url,
            timezone_name=settings.forex_factory_timezone,
        ).fetch()
        calendar_count += persist_calendar(repository, events)
    return article_count, calendar_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll configured news and economic-calendar providers once")
    parser.parse_args()
    articles, calendar = asyncio.run(ingest_once())
    print(f"news update completed: {articles} articles, {calendar} calendar events", flush=True)


if __name__ == "__main__":
    main()
