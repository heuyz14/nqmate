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

The foundation slice adds `strategies/models.py`, validation, `SupabaseStrategyRepository`, migration `014_strategies.sql`, and `POST/GET/PATCH/DELETE /strategies`. Strategy rules are stored as structured JSON arrays and explicit entry/target/stop logic; DELETE is a soft deactivation, and performance statistics/graph relationships require completed setup/outcome records in later slices. Migration `014` has been applied.

The setup-detection slice adds `strategies/setups.py`, `SupabaseSetupRepository`, migration `015_strategy_setups.sql`, and `jobs/detect_setups.py`. The initial deterministic registry supports `price_above_overnight_midpoint`, `onh_break`, and `onl_break`; unknown conditions produce no setup.

The performance foundation adds `strategies/performance.py`. It calculates sample size, win rate, mean/median return, expectancy, MFE/MAE means when supplied, and a Sharpe-like ratio from completed outcome records. Missing outcome fields are not imputed.

The outcome slice adds `strategies/outcomes.py`, `SupabaseOutcomeRepository`, migration `016_strategy_outcomes.sql`, and `GET /strategies/{id}/performance`. Outcomes are idempotent per setup and performance is derived from persisted completed outcomes.

The dashboard slice adds `/strategies` with structured strategy creation, saved-strategy selection, rule detail, and outcome-backed performance metrics. Empty strategy/outcome states are explicit.

The PB Blake / ICT evaluator adds `strategies/pb_blake.py` and tests. It accepts already-normalized HTF context, a liquidity event, post-event lower-timeframe inversions, and explicit entry/stop/targets. It preserves event order, filters observations after the requested analysis timestamp, selects the highest valid inversion among 1m/2m/3m/5m, and returns `VALID`, `DEVELOPING`, or `NO_SETUP`. It fails closed for invalid sequence, unreasonable stops, or sub-1R targets; it does not fetch data or force a trade.

The historical input slice adds `strategies/pb_blake_data.py` and tests. It detects three-bar FVGs and the first close-through inversion on normalized historical bars, requiring each bar to have been available at its timestamp. A bearish FVG close-through produces a long inversion; a bullish FVG close-through produces a short inversion. Higher-timeframe context, liquidity, entry, stops, and targets remain explicit inputs rather than invented by this detector.

The PB assessment API slice adds `POST /api/v1/strategies/{id}/assess`. It accepts a point-in-time, normalized PB evidence packet and persists only valid setup occurrences; developing and no-setup assessments remain non-trade results. This endpoint is suitable for a backtest runner and intentionally does not claim that missing HTF context, liquidity, or trade levels exist.

# Acceptance Criteria

Each strategy displays required conditions and reliable statistics with sample context, including best and worst regimes when regime-labeled outcomes exist; statistics update from completed sessions and never mutate historical predictions. The PB assessment endpoint returns a conservative status and persists only valid setup occurrences.

# Tests

Rule validation, setup detection, association integrity, outcome/statistic calculations, and API tests.

# Explicitly Out of Scope

Online model retraining, deep learning, RL, and automated order execution.

# Next Phase

[Phase 8 — ML](phase-8-ml.md), after applying migration `017_strategy_outcome_regime.sql`.
