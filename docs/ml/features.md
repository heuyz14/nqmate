## When to read this file

Read when implementing session calculations, feature snapshots, feature matrices, or feature-versioned deterministic inputs.

# Features

## Snapshot contract

Create snapshots at important times such as 08:00, 08:30, 09:00, 09:25, 09:35, 10:00, 12:00, 14:00, and 15:30. A snapshot includes timestamp, NQ price, distances from PDH/PDL/ONH/ONL/VWAP, overnight return/range percent, gap percent, ATR-normalized move, ES return, NQ/ES relative strength, 10Y/2Y changes, VIX/DXY changes, breadth score, minutes to upcoming event, news sentiment, and news relevance. Missing provider fields remain nullable.

## V1 deterministic features

Implement and unit-test previous-day high/low/close; overnight high/low/midpoint/range/return; opening gap; 5m/15m/30m returns; ATR(14); EMA 9/20/50; VWAP and distance from VWAP; range position; and relative NQ-vs-ES strength. Later features include volume/value/market profile, breadth, advance/decline, TICK, order flow, delta, and DOM imbalance; do not build order-flow features without a suitable real-time/tick feed.

## ML feature row

Each immutable row contains market structure, levels, momentum/volatility, cross-market, news, macro, retrieval, and graph features such as overnight return/range, gap, level distances, returns, ATR percentile, ES/yields/DXY/VIX, news relevance/surprise/direction/count, event timing/importance, analogue rates/returns, and best strategy expectancy. It must also include `feature_timestamp`, `available_at`, `feature_version`, `session_date`, and `contract`.

## Availability rule

At prediction time T, training and inference may use only rows where `available_at <= T`. Reject any future indicator, final daily OHLC, revised macro value, later article, or complete-session label. The backtest must assert this rule.

