## When to read this file

Read when implementing temporal memory, analogue retrieval, graph-backed research, or graph features for ML.

## Temporal memory

Graphiti (Apache-2.0) may support knowledge that changes over time, such as Fed regimes transitioning from hawkish to neutral to dovish. Do not use it for raw candle ingestion. Relationships must preserve temporal validity.

## Historical analogues

V1 uses structured nearest neighbors, not graph-only similarity. Normalize a vector containing overnight return/range, gap, ATR percentile, NQ/ES strength, yield change, level distances, macro flag, and news score. Use `StandardScaler` with cosine or Euclidean distance and return the top 20 sessions. Aggregate 30m/60m returns, open-to-close, ONH/ONL break rates, and trend-day probability.

## Strategy memory

Retrieve strategies historically successful in the current regime. Strategy performance is grouped by strategy, regime, event, time of day, and direction, with sample count, win rate, mean/median return, expectancy, MFE, MAE, Sharpe-like ratio, and calibration.

## Graph-derived ML features

Materialize reproducible numeric features such as similar-regime bull rate/average return, strategy expectancy/sample size, similar-news average return/positive rate, event-type historical impact, company-sector weight score, and regime-strategy match score. Generate these before training; ML must not query Neo4j ad hoc during training.

## Narrow internal tools

Expose normalized internal tools such as `get_current_market_snapshot`, `get_overnight_structure`, `get_key_levels`, `get_upcoming_macro_events`, `get_relevant_news`, `get_similar_sessions`, `get_strategy_stats`, `get_regime`, and `get_prediction_history`. A later MCP server should access these internal services rather than let an LLM call third-party APIs or arbitrary database operations.

