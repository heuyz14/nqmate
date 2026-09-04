## When to read this file

Read to implement saved strategies, setup detection, associations, and performance memory. Also read [strategy-system.md](../strategies/strategy-system.md) and [ontology.md](../graph/ontology.md).

# Goal

Turn user strategies into structured, measurable, regime-aware memory.

# Dependencies

[Phase 6](phase-6-knowledge-graph.md), sessions, regimes, levels, and outcome calculations.

# Tasks

- Implement strategy CRUD and structured rules.
- Detect/setup occurrences and associate strategy/session/regime/prediction/news/outcome records.
- Calculate sample count, win rate, expectancy, MFE, MAE, Sharpe-like ratio, calibration, and best/worst regimes.
- Expose strategy performance and graph-backed research.

The foundation slice adds `strategies/models.py`, validation, `SupabaseStrategyRepository`, migration `014_strategies.sql`, and `POST/GET/PATCH/DELETE /strategies`. Strategy rules are stored as structured JSON arrays and explicit entry/target/stop logic; DELETE is a soft deactivation, and performance statistics/graph relationships require completed setup/outcome records in later slices. Migration `014` has been applied; no strategies are currently stored.

The setup-detection slice adds `strategies/setups.py`, `SupabaseSetupRepository`, migration `015_strategy_setups.sql`, and `jobs/detect_setups.py`. The initial deterministic registry supports `price_above_overnight_midpoint`, `onh_break`, and `onl_break`; unknown conditions produce no setup.

# Acceptance Criteria

Each strategy displays required conditions and reliable statistics with sample context; statistics update from completed sessions and never mutate historical predictions.

# Tests

Rule validation, setup detection, association integrity, outcome/statistic calculations, and API tests.

# Explicitly Out of Scope

Online model retraining, deep learning, RL, and automated order execution.

# Next Phase

[Phase 8 — ML](phase-8-ml.md).
