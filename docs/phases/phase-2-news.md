## When to read this file

Read to implement financial-news ingestion and event extraction. Also read [news-data.md](../data/news-data.md) and [endpoints.md](../api/endpoints.md).

# Goal

Normalize relevant financial news into deduplicated, point-in-time `NewsArticle` and `NewsEvent` records.

# Dependencies

[Phase 1](phase-1-market-engine.md), provider configuration, and `LLMProvider` abstraction.

# Tasks

- Add Marketaux and Fed RSS adapters, scheduled/manual polling, deduplication, and storage.
- Add strict event taxonomy, entities/topics, stance, directional impact, horizon, confidence, and reason schema.
- Implement the initial NQ relevance heuristic and dashboard news endpoints/card.
- Add Gemini provider behind the LLM abstraction; keep extraction optional and cached.

# Acceptance Criteria

A new story creates one article and structured event with entities, impact, relevance, confidence, source, and timestamps; repeated fetches do not duplicate it; publication availability is preserved.

# Tests

Adapter parsing, deduplication, schema validation, relevance scoring, timestamp availability, and mocked extraction/storage integration tests.

# Explicitly Out of Scope

Macro release pipeline, bias generation, embeddings/news-impact ML, graph, and automated trading.

# Next Phase

[Phase 3 — Macro pipeline](phase-3-macro.md).

