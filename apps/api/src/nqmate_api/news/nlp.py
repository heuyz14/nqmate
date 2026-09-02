from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Callable, Protocol

import httpx

from nqmate_api.news.models import NewsArticle, NewsDirection, NewsEvent


@dataclass(frozen=True)
class NewsExtraction:
    event_subtype: str | None = None
    sentiment: float | None = None
    nq_direction: str | None = None
    impact: str | None = None
    confidence: float | None = None
    themes: tuple[str, ...] = ()
    summary: str | None = None
    reason: str | None = None


class NewsEventExtractor(Protocol):
    def extract(self, article: NewsArticle) -> NewsExtraction: ...


class CachedNewsExtractor:
    """Cache structured extraction by immutable provider identity."""

    def __init__(self, extractor: Callable[[NewsArticle], NewsExtraction]) -> None:
        self._extractor = extractor
        self._cache: dict[tuple[str, str], NewsExtraction] = {}

    def extract(self, article: NewsArticle) -> NewsExtraction:
        key = (article.provider, article.provider_id)
        if key not in self._cache:
            self._cache[key] = self._extractor(article)
        return self._cache[key]


class GeminiNewsExtractor:
    """Minimal structured-output adapter; callers should wrap it in the cache."""

    def __init__(self, api_key: str, model: str = "gemini-3.6-flash", client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=30)
        self._url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self._api_key = api_key

    def extract(self, article: NewsArticle) -> NewsExtraction:
        prompt = (
            "Classify this financial news item for Nasdaq-100 futures. Return JSON only with "
            "event_subtype, sentiment (-1 to 1), nq_direction (bullish/bearish/neutral/unknown), "
            "impact, confidence (0 to 1), themes (array), summary, and reason. "
            f"Headline: {article.headline}\nSummary: {article.summary or ''}"
        )
        response = self._client.post(
            self._url, params={"key": self._api_key},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}},
        )
        response.raise_for_status()
        payload: Any = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        values = json.loads(text)
        if not isinstance(values, dict):
            raise ValueError("Gemini extraction must be a JSON object")
        sentiment = values.get("sentiment")
        confidence = values.get("confidence")
        if sentiment is not None and (not isinstance(sentiment, (int, float)) or not -1 <= sentiment <= 1):
            raise ValueError("Gemini sentiment must be between -1 and 1")
        if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
            raise ValueError("Gemini confidence must be between 0 and 1")
        themes = values.get("themes") or ()
        if not isinstance(themes, list) or not all(isinstance(theme, str) for theme in themes):
            raise ValueError("Gemini themes must be a string array")
        return NewsExtraction(
            event_subtype=values.get("event_subtype"), sentiment=sentiment,
            nq_direction=values.get("nq_direction"), impact=values.get("impact"),
            confidence=confidence, themes=tuple(themes),
            summary=values.get("summary"), reason=values.get("reason"),
        )


def apply_extraction(event: NewsEvent, extraction: NewsExtraction) -> NewsEvent:
    """Apply only supplied structured fields; deterministic defaults remain intact."""
    return replace(
        event,
        event_subtype=extraction.event_subtype or event.event_subtype,
        sentiment=extraction.sentiment if extraction.sentiment is not None else event.sentiment,
        nq_direction=NewsDirection(extraction.nq_direction) if extraction.nq_direction else event.nq_direction,
        impact=extraction.impact or event.impact,
        confidence=extraction.confidence if extraction.confidence is not None else event.confidence,
        themes=extraction.themes or event.themes,
        summary=extraction.summary or event.summary,
        reason=extraction.reason or event.reason,
        model_version="nlp-v1",
    )
