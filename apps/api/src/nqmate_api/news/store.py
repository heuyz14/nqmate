from __future__ import annotations

from nqmate_api.news.models import NewsArticle, NewsEvent


class NewsStore:
    def __init__(self) -> None:
        self._articles: dict[tuple[str, str], NewsArticle] = {}
        self._events: dict[tuple[str, str], NewsEvent] = {}

    def upsert_article(self, article: NewsArticle) -> bool:
        key = (article.provider, article.provider_id)
        created = key not in self._articles
        self._articles[key] = article
        return created

    def upsert_event(self, event: NewsEvent) -> bool:
        key = (event.article.provider, event.article.provider_id)
        created = key not in self._events
        self._events[key] = event
        return created

    def articles(self) -> list[NewsArticle]:
        return list(self._articles.values())
