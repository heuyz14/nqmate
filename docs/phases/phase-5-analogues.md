## When to read this file

Read to implement structured historical similarity. Also read [knowledge-memory.md](../graph/knowledge-memory.md), [features.md](../ml/features.md), and [targets.md](../ml/targets.md).

# Goal

Retrieve the 20 most similar historical sessions and summarize their outcomes.

# Dependencies

[Phase 4](phase-4-bias-engine.md), historical feature matrix, sessions, and outcome labels.

# Tasks

- Backfill normalized feature vectors.
- Implement StandardScaler and cosine/Euclidean nearest neighbors.
- Store/retrieve top 20 sessions and aggregate 30m/60m/open-close returns, ONH/ONL break rates, and trend-day probability.
- Add `/regimes/similar` and analogue UI; feed results into bias evidence.

# Acceptance Criteria

For a current session, the endpoint returns 20 comparable sessions with reproducible distances and outcome aggregates without future data leakage.

# Tests

Scaling, nearest-neighbor determinism, missing data, outcome aggregation, and point-in-time retrieval tests.

# Explicitly Out of Scope

Neo4j ontology, strategy memory, advanced ML, deep learning, and RL.

# Next Phase

[Phase 6 — Knowledge graph](phase-6-knowledge-graph.md).

