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

# Acceptance Criteria

A query for high-volatility gap-up sessions with rising yields returns graph-backed strategy evidence; raw candles remain in PostgreSQL only.

# Tests

Ontology constraints, idempotent sync, temporal validity, relationship traversal, and graph query integration tests. The foundation tests verify separate dimensions and ensure sync Cypher contains no candle node or raw-bar write.

# Explicitly Out of Scope

ML training, arbitrary database access for LLMs, deep learning, and RL.

# Next Phase

[Phase 7 — Strategy memory](phase-7-strategy-memory.md).
