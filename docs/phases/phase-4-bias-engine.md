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

The initial implementation slice provides `BiasSnapshot` and deterministic `score_bias` in `apps/api/src/nqmate_api/bias/`. Inputs are normalized to `[-1, 1]`; weights are overnight .20, gap .10, technical location .20, relative strength .15, macro .20, and news .15. A high-impact event within 15 minutes caps confidence at .55 and returns `WAIT_FOR_RELEASE`.

The current result also includes deterministic evidence factors, bull and bear cases, invalidation conditions, and uncertainty notes. These are generated from the supplied snapshot only and are not LLM-generated.

The API/persistence slice adds `POST /api/v1/bias/generate` and `GET /api/v1/bias/current`. Predictions are inserted, never updated, and store model/feature versions plus deterministic evidence fields. Migration `011_bias_predictions.sql` creates the table.

# Acceptance Criteria

Identical inputs produce the same score; high-impact events within 15 minutes cap confidence at .55 and recommend waiting; LLM output uses only supplied evidence and contains required fields.

# Tests

Scoring, thresholds, catalyst guardrail, deterministic reproducibility, schema validation, immutable persistence, and mocked LLM integration tests.

# Explicitly Out of Scope

ML probabilities, historical analogues, graph, strategy memory, and execution.

# Next Phase

[Phase 5 — Historical analogues](phase-5-analogues.md).
