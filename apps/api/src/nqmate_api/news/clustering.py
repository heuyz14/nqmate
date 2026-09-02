from __future__ import annotations

import hashlib
from typing import Sequence

from nqmate_api.news.models import NewsEvent

_OFFICIAL_SOURCES = {"federal reserve", "bureau of labor statistics", "bureau of economic analysis"}


def cluster_key(event: NewsEvent) -> str:
    """Create a stable baseline key for near-duplicate reports.

    The 30-minute bucket and shared event/entity vocabulary limit clustering to
    reports that were available close together in point-in-time order. Headline
    wording is intentionally not part of the identity because providers phrase
    the same event differently.
    """
    bucket = int(event.event_timestamp.timestamp() // (30 * 60))
    entities = tuple(sorted(entity.lower() for entity in event.article.entities))
    topics = tuple(sorted(topic.lower() for topic in event.article.topics))
    payload = "|".join((event.event_type.value, ",".join(entities), ",".join(topics), str(bucket)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def select_canonical_event(events: Sequence[NewsEvent]) -> NewsEvent:
    """Select the highest-authority event without changing availability time."""
    if not events:
        raise ValueError("at least one event is required")
    return min(events, key=lambda event: (
        0 if event.article.source.lower() in _OFFICIAL_SOURCES else 1,
        event.article.published_at,
        event.article.provider,
    ))
