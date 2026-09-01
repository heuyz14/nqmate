## When to read this file

Read to implement deterministic bias scoring and evidence-constrained LLM explanation. Also read [features.md](../ml/features.md), [news-data.md](../data/news-data.md), [macro-data.md](../data/macro-data.md), and [endpoints.md](../api/endpoints.md).

# Goal

Generate a reproducible, conservative V0 bias without ML.

# Dependencies

[Phase 3](phase-3-macro.md), current snapshots, news/macro context, and `LLMProvider`.

# Tasks

- Build snapshot input and deterministic weighted score from overnight structure, gap, strength, technical location, macro risk, and news.
- Add bias states, catalyst guardrail, bull/bear cases, invalidation, uncertainty, and strict JSON prompt contract.
- Persist immutable predictions with evidence IDs, scores, model/feature/prompt versions; add current/history UI.

# Acceptance Criteria

Identical inputs produce the same score; high-impact events within 15 minutes cap confidence at .55 and recommend waiting; LLM output uses only supplied evidence and contains required fields.

# Tests

Scoring, thresholds, catalyst guardrail, deterministic reproducibility, schema validation, immutable persistence, and mocked LLM integration tests.

# Explicitly Out of Scope

ML probabilities, historical analogues, graph, strategy memory, and execution.

# Next Phase

[Phase 5 — Historical analogues](phase-5-analogues.md).

