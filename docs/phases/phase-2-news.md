## When to read this file

Read to implement financial-news ingestion and event extraction. Also read [news-data.md](../data/news-data.md) and [endpoints.md](../api/endpoints.md).

# Goal

Provide fast, zero-cost awareness of scheduled high-impact economic events and unscheduled breaking news affecting NQ, while keeping the two ingestion strategies separate and preserving point-in-time truth.

# Dependencies

[Phase 1](phase-1-market-engine.md), provider configuration, and `LLMProvider` abstraction.

# Tasks

1. Ingest Forex Factory calendar exports and normalize upcoming USD events, prioritizing HIGH impact.
2. Add Marketaux breaking-news ingestion with adaptive configurable polling.
3. Add official Fed feeds and preserve official-source priority; official BLS/BEA verification belongs to [macro-data.md](../data/macro-data.md) and Phase 3.
4. Normalize articles/events with strict taxonomy, subtype, themes, sentiment, expected NQ direction, impact, confidence, and reason.
5. Add deterministic NQ relevance scoring and event-specific economic surprise fields.
6. Deduplicate repeated reports across providers into logical events.
7. Add Supabase persistence and news/calendar API endpoints.
8. Add optional cached Gemini extraction behind the provider abstraction.
9. Add next-event/pre-event risk retrieval for the future bias engine.

# Acceptance Criteria

- A calendar query returns upcoming USD events with schedule, impact, forecast, previous, and nullable actual values.
- A new story creates one article and structured event with entities, subtype, impact, relevance, confidence, source, and timestamps; repeated fetches do not duplicate it.
- Official source values override aggregator facts, and publication/release availability is preserved.
- The system can return the next HIGH-impact event and minutes until release.

# Tests

Adapter parsing, calendar normalization, deduplication/clustering, schema validation, relevance and surprise scoring, timestamp availability, adaptive polling configuration, pre-event windows, and mocked extraction/storage integration tests.

# Explicitly Out of Scope

Macro release pipeline, bias generation, embeddings/news-impact ML, graph, and automated trading.

# Next Phase

[Phase 3 — Macro pipeline](phase-3-macro.md).
