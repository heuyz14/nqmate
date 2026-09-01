## When to read this file

Read this first for product intent, scope, constraints, and roadmap. Pair it with [CURRENT_STATE.md](CURRENT_STATE.md) for the present phase.

# Project

## Product vision

NQ Directional Bias AI is an AI-assisted research application that produces a structured, evidence-backed directional bias for Nasdaq-100 futures before and during the U.S. session.

## Problem solved

Market context is distributed across price structure, overnight behavior, cross-market signals, macro releases, breaking news, historical regimes, and strategy history. The system normalizes those inputs so a trader can inspect one explainable brief instead of relying on an unexplained `BUY` or `SELL` call.

## Major capabilities

- Deterministic NQ session and feature analysis.
- News and macro event ingestion with structured impact interpretation.
- Historical outcomes, nearest-session analogues, and regime context.
- Saved strategies, setup occurrences, and performance memory.
- Knowledge-graph relationships across sessions, events, setups, strategies, and outcomes.
- Calibrated multi-horizon ML probabilities and an LLM explanation layer.
- Dashboard, research questions, journal, bias history, and model diagnostics.

## Decision-support philosophy

The product is decision support, not autonomous execution. Every bias must expose direction, confidence, evidence, counter-evidence, important levels, catalysts, uncertainty, and invalidation conditions. Numerical truth comes from deterministic code and statistical models; the LLM explains supplied evidence.

## V1 definition of done

On a trading morning, the dashboard shows current NQ context, overnight structure, key levels, important news, the next macro event, regime, 20 similar sessions, historical statistics, strategy relevance, bull and bear cases, bias, confidence, and invalidation. After the session, predictions are evaluated, outcomes stored, and strategy statistics updated.

## Major constraints

- Target approximately $0/month using free tiers and public data.
- Free futures data is historical/delayed rather than a true zero-latency feed; V1 is research, premarket, and delayed-data focused.
- Preserve point-in-time data and prevent look-ahead bias.
- No automated execution, brokerage credentials, RL, deep neural networks, online retraining, or heavy infrastructure in V1.
- Provider interfaces must permit later upgrades without rewriting feature logic.

## High-level roadmap

Deterministic dashboard → news and macro rule-based bias → historical regime retrieval → knowledge graph and strategy memory → logistic/XGBoost or LightGBM models → calibrated multi-target ensemble → NQ-specific news-impact ML → deep-learning research → multimodal research → experimental RL.

See [ARCHITECTURE.md](ARCHITECTURE.md) for system boundaries and [phases](phases/) for executable delivery plans.

