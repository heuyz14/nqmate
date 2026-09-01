## When to read this file

Read only for post-V1 sequence, Transformer, multimodal, or experimental reinforcement-learning research.

# Deep Learning

Deep learning is post-V1 and must not delay the usable deterministic/news/macro product. Before serious experiments, require multiple years of minute data, clean roll handling, stable features, point-in-time news/macro, and walk-forward infrastructure; correlated minute rows are not independent samples.

## Sequence dataset

Build reproducible code for 30m/60m/120m histories, preferably a 120×minute feature matrix containing OHLCV, candle/range features, VWAP/EMA/ATR context, cross-market changes, event flags, and session/time embeddings. Store dataset-building code rather than giant duplicated sequence blobs.

## Research progression

1. LSTM/GRU classifier for 60m direction.
2. Temporal Transformer encoder with multi-target heads.
3. Multi-task shared encoder for 30m, 60m, close, ONH/ONL-first, trend-day, and related targets.
4. Multimodal fusion of market sequence, engineered features, news text, macro events, and graph features.

Compare every stage against XGBoost using identical walk-forward periods. Adopt only with out-of-sample improvement in Brier score, log loss, calibration, and directional utility.

## Text and reaction context

Do not train a language model from scratch. Progress from structured LLM extraction to pretrained embeddings, FinBERT, and an NQ-specific news-impact encoder. Compare expected news direction with observed market reaction, but treat reaction divergence as statistical association rather than permanent causal logic.

## Experimental reinforcement learning

Reinforcement learning is the final research stage only, never V1 and never direct brokerage control. Use a simulated state/action/reward environment with transaction costs, slippage, non-stationarity, reward-hacking, overfit, impact, survivorship, and look-ahead safeguards. Evaluate in simulation and forward paper testing.
