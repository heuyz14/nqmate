## When to read this file

Read to implement Neo4j ontology and synchronization. Also read [ontology.md](../graph/ontology.md) and [knowledge-memory.md](../graph/knowledge-memory.md).

# Goal

Create semantic, temporal relationships among sessions, regimes, events, strategies, setups, predictions, and outcomes.

# Dependencies

[Phase 5](phase-5-analogues.md), Neo4j connectivity, relational source records, and defined graph ontology.

# Tasks

- Create node labels, relationship constraints, and regime dimensions.
- Sync sessions, regimes, events, strategies, setups, and outcomes from PostgreSQL.
- Add graph-backed research query and reproducible graph-derived feature extraction.

The foundation slice adds `apps/api/src/nqmate_api/graph/ontology.py` and `graph/repository.py`. It defines unique constraints for semantic identifiers and an idempotent `MarketSession` → `MarketRegime` synchronization boundary. Regime dimensions are supplied explicitly; this slice does not invent thresholds or copy numerical candles into Neo4j.

The classification slice adds `graph/regimes.py`, with isolated v0 thresholds for overnight direction, overnight volatility, gap, location, yield regime, and catalyst regime. Thresholds are documented in [ontology.md](../graph/ontology.md) and covered by unit tests so they can be calibrated without changing graph storage.

The synchronization slice adds `jobs/sync_graph.py`. It initializes constraints, reads a bounded date range of stored sessions, applies the deterministic classifier, and idempotently merges semantic session/regime nodes. A live run synced 171 sessions into Neo4j; verification found 171 `MarketSession` nodes and 12 shared `MarketRegime` nodes.

The source-record slice adds `jobs/sync_graph_sources.py` and semantic repository methods for news, macro calendar events, and predictions. A live bounded run synchronized 23 news events, 13 macro events, and 0 predictions (no stored predictions existed in the selected date window); verification found 23 `NewsEvent`, 13 `MacroEvent`, and 2 `Company` nodes. Raw article bodies and macro observations remain in Supabase.

The traversal slice adds `Neo4jGraphRepository.query_regimes` and `GET /knowledge/regimes`. Filters remain independently queryable and are applied in Neo4j with a bounded result size; live verification returned 20 GAP_UP sessions.

The completion slice adds idempotent `Prediction-[:RESULTED_IN]->Outcome` synchronization and `GET /knowledge/strategy-evidence`, which traverses strategy performance relationships for the independently filtered regime. It is intentionally empty until Phase 7 creates strategy-memory records.

# Acceptance Criteria

A query for high-volatility gap-up sessions with rising yields returns graph-backed strategy evidence once strategy records and performance relationships exist; raw candles remain in PostgreSQL only. The Phase 6 query contract is implemented, but live evidence remains pending Phase 7 strategy-memory records.

# Tests

Ontology constraints, idempotent sync, temporal validity, relationship traversal, and graph query integration tests. The foundation tests verify separate dimensions and ensure sync Cypher contains no candle node or raw-bar write; sync-job tests verify bounded iteration and missing-session handling; completion tests verify outcome links and strategy traversal.

# Explicitly Out of Scope

ML training, arbitrary database access for LLMs, deep learning, and RL.

# Next Phase

[Phase 7 — Strategy memory](phase-7-strategy-memory.md).
