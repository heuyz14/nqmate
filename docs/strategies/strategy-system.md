## When to read this file

Read when implementing saved strategies, rule schemas, setup detection, performance statistics, or strategy relevance in bias/research views.

# Strategy System

## Structured strategy

```python
Strategy:
    id
    name
    description
    allowed_regimes
    required_conditions
    confirmation_conditions
    invalidation_conditions
    entry_logic
    target_logic
    stop_logic
    active
```

An example is an ONH Breakout Retest requiring price above overnight midpoint and positive NQ relative strength, triggering on an ONH break and holding retest, and invalidating on a five-minute close below ONH.

## Memory and outcomes

Associate strategies with setups, sessions, regimes, predictions, and outcomes. Track sample count, win rate, mean/median return, expectancy, MFE, MAE, Sharpe-like ratio, and confidence calibration by strategy, regime, event, time of day, and direction. Expose best/worst regimes and sufficient-sample safeguards.

## Self-learning boundary

“Self-learning” means recording outcomes, updating controlled statistics, retrieving similar regimes, and periodically retraining offline models. It does not mean letting an LLM modify itself or updating models during a session.

