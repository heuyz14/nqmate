# NQ Directional Bias AI — Agent Guide

## What this project is

NQ Directional Bias AI is a personal research and decision-support application for Nasdaq-100 futures. It combines market structure, overnight behavior, cross-market context, macroeconomic events, financial news, historical outcomes, regime similarity, strategies, a temporal knowledge graph, and statistical models into an explainable directional brief. It is not an autonomous trading or execution system.

## Core architecture

```text
Data
→ clean session model
→ deterministic features
→ news/macro events
→ historical outcomes
→ regime similarity
→ knowledge graph
→ ML probabilities
→ LLM explanation
```

## Reading rules

Always read [PROJECT.md](docs/PROJECT.md) and [CURRENT_STATE.md](docs/CURRENT_STATE.md) first. Do not automatically read every file under `docs/`; read only the smallest relevant set below. Consult the archived [full specification](nq_directional_bias_ai_spec_updated.md) only when the modular documentation is ambiguous or missing necessary information.

| Task | Read |
|---|---|
| Market data / futures | [market-data.md](docs/data/market-data.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| News / NLP | [news-data.md](docs/data/news-data.md) |
| Macroeconomic data | [macro-data.md](docs/data/macro-data.md) |
| Feature engineering | [features.md](docs/ml/features.md) |
| ML targets | [targets.md](docs/ml/targets.md) |
| Machine learning | [models.md](docs/ml/models.md), [validation.md](docs/ml/validation.md) |
| Deep learning | [deep-learning.md](docs/ml/deep-learning.md) |
| Knowledge graph | [ontology.md](docs/graph/ontology.md), [knowledge-memory.md](docs/graph/knowledge-memory.md) |
| API | [endpoints.md](docs/api/endpoints.md) |
| Frontend | [dashboard.md](docs/frontend/dashboard.md) |
| Strategies | [strategy-system.md](docs/strategies/strategy-system.md) |
| Current development phase | The relevant file under [phases](docs/phases/) |

## Non-negotiable engineering rules

- Do not implement future phases unless explicitly requested.
- Deterministic calculations belong in Python/code and must not be delegated to an LLM.
- Preserve point-in-time correctness and prevent look-ahead bias: every feature has `available_at`, and prediction time may use only data available by then.
- Keep provider interfaces swappable and keep PostgreSQL/Supabase as numerical truth; Neo4j is for semantic relationships.
- The LLM explains supplied evidence; it must not invent prices, events, statistics, or historical outcomes.
- Never expose secrets or service keys to the browser, and do not add automated trade execution to V1.
- After meaningful implementation work, update [CURRENT_STATE.md](docs/CURRENT_STATE.md) concisely. It is a handoff, not a development journal.

