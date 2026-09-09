# NQMATE --- Historical Research & Validation V2 Specification

**Status:** Proposed next-stage specification\
**Project:** NQMATE --- Quantitative NQ Futures Research Platform\
**Primary objective:** Expand NQMATE from a strong V1 research
foundation into a statistically credible, point-in-time historical
research and forward-testing system.

------------------------------------------------------------------------

## 1. Purpose

NQMATE currently combines deterministic NQ market calculations,
macro/news context, historical analogues, regime relationships, strategy
memory, machine-learning experiments, and LLM explanations.

The current system should remain **research-only**. This specification
does not introduce automated trade execution.

The highest-priority limitation is insufficient evaluation data. Current
evidence includes roughly 72 scored samples for most major horizons,
only one scored 120-minute sample, calibration gaps, and no ML model
that has passed the existing promotion gates.

The next development cycle should therefore prioritize:

1.  Expanding historical coverage to approximately two years.
2.  Creating point-in-time feature snapshots.
3.  Building richer trading-relevant targets.
4.  Improving PB/ICT strategy definitions.
5.  Performing stronger chronological walk-forward evaluation.
6.  Adding statistical significance and confidence intervals.
7.  Adding model explainability.
8.  Building historical replay.
9.  Establishing immutable forward paper testing.

------------------------------------------------------------------------

## 2. Guiding Principles

### 2.1 No look-ahead bias

For every historical prediction timestamp `t`, features may contain only
information that was available at or before `t`.

Future data may be used only for outcome/target construction.

Example:

``` text
Prediction timestamp: 2025-04-04 09:25 ET

Allowed:
- Prior session data
- Overnight NQ/ES data through 09:25
- News published by 09:25
- Economic releases published by 09:25
- Events scheduled in advance
- Historical regime statistics available at that time

Not allowed:
- 10:15 headline
- Closing price
- Future intraday candles
- Later economic revisions
- Statistics calculated using future sessions
```

### 2.2 Deterministic calculations remain in Python

Python/FastAPI remains responsible for:

-   Market calculations
-   Feature engineering
-   Strategy detection
-   Target construction
-   Statistical evaluation
-   ML inference
-   Model comparison

The LLM may explain supplied evidence but must not invent or calculate
market statistics.

### 2.3 Raw numerical truth remains in PostgreSQL/Supabase

Continue using:

-   **Supabase/PostgreSQL:** candles, features, predictions, outcomes,
    numerical statistics.
-   **Neo4j:** regimes, semantic relationships, strategy relationships,
    historical connections.
-   **LLM:** evidence-grounded explanation.

Do not duplicate raw candle history into Neo4j.

### 2.4 Manual model promotion

No model should automatically become production/champion based on one
evaluation.

Promotion remains manually approved and evidence-gated.

------------------------------------------------------------------------

# 3. Phase 10 --- Historical Research Dataset V2

## Goal

Create a clean, approximately two-year historical research dataset
suitable for strategy evaluation and machine-learning experiments.

## 3.1 Historical coverage

Target initial range:

``` text
Approximately September 2024 → September 2026
```

Exact start date may move slightly depending on data-provider
availability.

Target:

-   \~500 NQ trading sessions
-   Corresponding ES data where available
-   Complete 1-minute source history
-   Correct futures contract metadata
-   Correct rollover handling
-   No duplicate sessions/bars

Do not generate synthetic bars to fill unavailable history.

## 3.2 Source of truth

Continue treating stored 1-minute history as the canonical market-data
source.

Higher-timeframe candles should be deterministically reconstructed from
1-minute data:

-   5m
-   15m
-   1h
-   2h
-   4h
-   Daily

## 3.3 Historical session reconstruction

For each completed session:

1.  Verify raw bars.
2.  Resolve active contract.
3.  Construct overnight session.
4.  Construct RTH session.
5.  Calculate deterministic levels.
6.  Calculate features.
7.  Create feature snapshots.
8.  Calculate future outcomes.
9.  Run strategy detectors.
10. Persist versioned results.

## 3.4 Feature snapshots

Create immutable point-in-time feature snapshots.

Recommended initial snapshot times:

``` text
08:30 ET
09:00 ET
09:25 ET
09:30 ET
10:00 ET
12:00 ET
```

The architecture should support additional snapshot times later without
changing historical records.

Suggested entity:

``` text
session_feature_snapshot

id
session_date
snapshot_timestamp
symbol
contract
feature_version
data_version

overnight_return
overnight_range
gap_pct
atr_14
distance_pdh
distance_pdl
distance_onh
distance_onl
distance_overnight_midpoint
vwap_distance
ema_relationships
ema_slopes

nq_momentum
es_momentum
nq_es_relative_strength

economic_event_pending
economic_event_category
economic_surprise
news_sentiment
news_relevance
news_event_category

volatility_regime
trend_regime
gap_regime
macro_regime

created_at
```

Actual fields should reuse existing project models where possible rather
than unnecessarily duplicating schema.

## Acceptance Criteria

-   At least \~450 valid historical sessions after filtering bad/missing
    sessions.
-   Every snapshot passes point-in-time validation.
-   Historical feature generation is deterministic and reproducible.
-   Dataset version is stored.
-   Re-running a dataset version produces equivalent values.
-   Missing inputs remain explicitly missing rather than silently
    fabricated.

------------------------------------------------------------------------

# 4. Phase 11 --- Point-in-Time Historical Context

## Goal

Ensure historical research represents what NQMATE could actually have
known at each timestamp.

## 4.1 Information cutoff

Every historical reconstruction must receive:

``` text
as_of_timestamp
```

All data retrieval must obey:

``` text
record.available_at <= as_of_timestamp
```

where applicable.

## 4.2 News

Historical news features must use publication timestamps.

Do not allow:

-   Articles published after prediction time
-   Later summaries describing earlier events
-   Retrospective news classifications that leak future market outcomes

Store:

``` text
published_at
retrieved_at
source
event_category
relevance
sentiment
```

## 4.3 Macro data

Preserve existing vintage-aware design.

Historical macro features should distinguish:

``` text
release_timestamp
observation_period
initial_value
revised_value
retrieved_at
```

Historical predictions must use the value available at that point in
time.

## 4.4 Economic calendar

Scheduled future events may be known before release and therefore may
appear as risk features.

Example:

``` text
CPI scheduled in 15 minutes
FOMC scheduled this afternoon
Powell speech scheduled at 13:00
```

The actual result/surprise must remain unavailable until its release
timestamp.

## Acceptance Criteria

Automated tests must prove that inserting a future news item, future
candle, or later macro revision cannot alter an earlier historical
feature snapshot.

------------------------------------------------------------------------

# 5. Phase 12 --- Target System V2

## Goal

Move beyond simple UP/DOWN classification toward targets that correspond
more directly to trading decisions.

## 5.1 Directional targets

Retain existing horizons:

``` text
return_5m > 0
return_15m > 0
return_30m > 0
return_60m > 0
return_120m > 0
open_to_close_return > 0
```

## 5.2 Continuous-return targets

Add:

``` text
return_5m
return_15m
return_30m
return_60m
return_120m
return_open_close
```

These allow regression experiments later.

## 5.3 Excursion targets

Add:

``` text
MFE_30m
MAE_30m

MFE_60m
MAE_60m

MFE_120m
MAE_120m
```

Store both raw-point and normalized forms where useful.

Recommended normalized representation:

``` text
MFE / ATR
MAE / ATR
```

## 5.4 Barrier targets

Introduce deterministic barrier outcomes.

Examples:

``` text
+0.50 ATR before -0.25 ATR
+0.75 ATR before -0.50 ATR
+1.00 ATR before -0.50 ATR
```

Parameters must be versioned.

## 5.5 Liquidity targets

Add:

``` text
ONH_hit_before_ONL
ONL_hit_before_ONH
PDH_hit_before_PDL
PDL_hit_before_PDH
```

Clearly define behavior when neither level is reached.

Recommended states:

``` text
UPPER_FIRST
LOWER_FIRST
NEITHER
SIMULTANEOUS_OR_AMBIGUOUS
```

Do not silently force ambiguous sessions into a binary label.

------------------------------------------------------------------------

# 6. Phase 13 --- Regime-Conditional Research

## Goal

Determine whether model/strategy performance changes meaningfully across
market environments.

## 6.1 Regime dimensions

Continue treating regimes as independent dimensions rather than one
giant label.

Examples:

``` text
trend_regime
volatility_regime
gap_regime
overnight_regime
macro_event_regime
news_regime
```

## 6.2 Conditional evaluation

For every model and strategy calculate:

``` text
overall performance
performance | volatility regime
performance | trend regime
performance | gap regime
performance | macro-event state
performance | PB setup state
```

## 6.3 Specialized models

Do not immediately deploy specialized models.

Research challengers such as:

``` text
general_model
trend_model
range_model
high_volatility_model
macro_event_model
gap_up_model
gap_down_model
pb_setup_model
```

A specialized model is retained only when there are sufficient
independent samples to evaluate it.

------------------------------------------------------------------------

# 7. Phase 14 --- PB Strategy Engine V2

## Goal

Convert the PB/ICT-style strategy record from partially defined concepts
into deterministic, testable rules.

## 7.1 Definitions required

Explicitly define and version:

-   Fair Value Gap (FVG)
-   Inverse FVG / inversion
-   Liquidity pool
-   Liquidity sweep
-   Displacement
-   CISD
-   SMT divergence
-   Higher-timeframe bias
-   Higher-timeframe tap
-   Entry window
-   Entry confirmation
-   Stop/invalidation
-   Profit target
-   Session/time restrictions

## 7.2 State machine

Recommended architecture:

``` text
WAITING_FOR_CONTEXT
        ↓
HTF_CONTEXT_VALID
        ↓
WAITING_FOR_LIQUIDITY
        ↓
LIQUIDITY_SWEPT
        ↓
WAITING_FOR_DISPLACEMENT
        ↓
DISPLACEMENT_CONFIRMED
        ↓
FVG_OR_IFVG_CONFIRMED
        ↓
ENTRY_VALID
        ↓
ACTIVE
       ↙ ↘
TARGET_HIT  INVALIDATED
```

A setup should fail closed whenever required evidence is missing.

## 7.3 Strategy-event persistence

Persist every state transition.

Example:

``` text
strategy_id
strategy_version
session_id
timestamp
previous_state
new_state
evidence
invalidation_reason
```

This allows historical debugging.

## 7.4 Strategy statistics

Calculate:

``` text
setup_count
win_rate
loss_rate
average_R
expectancy
profit_factor
average_MFE
average_MAE
median_MFE
median_MAE
Sharpe-like metric
max_drawdown
```

Also calculate these conditional on regime.

------------------------------------------------------------------------

# 8. Phase 15 --- Machine Learning Research V2

## Goal

Retrain and evaluate tabular ML models after the historical dataset
reaches sufficient size.

## 8.1 Baselines

Always retain:

-   Majority class
-   Always long
-   Overnight direction
-   Other simple deterministic baselines already implemented

A complex model is not valuable merely because its standalone accuracy
appears high.

It must beat relevant baselines out-of-sample.

## 8.2 Candidate models

Initial candidates:

``` text
Logistic Regression
Random Forest
Scikit-learn Gradient Boosting
XGBoost
LightGBM
```

Do not prioritize deep learning or reinforcement learning in this phase.

## 8.3 Feature sets

Version feature sets independently from model configuration.

Example:

``` text
features_v1_market
features_v2_market_regime
features_v3_market_regime_macro
features_v4_market_regime_macro_news
features_v5_strategy_context
```

This permits ablation testing.

## 8.4 Ablation studies

Measure whether each feature family actually improves out-of-sample
performance.

Compare:

``` text
Market only
Market + regime
Market + regime + macro
Market + regime + macro + news
Market + regime + macro + news + strategy
```

Do not assume additional data improves the model.

------------------------------------------------------------------------

# 9. Phase 16 --- Walk-Forward Validation V2

## Goal

Replace reliance on limited validation windows with repeated
chronological evaluation.

## 9.1 Expanding-window example

``` text
Train: Sep 2024 → Feb 2025
Test:  Mar 2025

Train: Sep 2024 → Mar 2025
Test:  Apr 2025

Train: Sep 2024 → Apr 2025
Test:  May 2025

...
```

Also support rolling windows later.

## 9.2 Grouping

When multiple snapshots/horizons originate from one session, evaluation
must account for within-session dependence.

Never report hundreds of correlated horizon observations as though they
were hundreds of independent trading days.

## 9.3 Classification metrics

Track:

``` text
accuracy
balanced_accuracy
precision
recall
F1
ROC-AUC
log_loss
Brier_score
ECE
```

## 9.4 Trading metrics

Where a prediction maps to a defined strategy/action, track:

``` text
expectancy
average_R
profit_factor
maximum_drawdown
Sharpe-like ratio
positive_return_rate
MFE
MAE
```

------------------------------------------------------------------------

# 10. Phase 17 --- Statistical Evidence Layer

## Goal

Make it harder to mistake noise for a trading edge.

## 10.1 Sample counts

Every performance metric must show its sample count.

Example:

``` text
Accuracy: 58.2%
n = 487
```

## 10.2 Confidence intervals

Add session-level confidence intervals for:

-   Accuracy
-   Positive-return rate
-   Win rate
-   Mean return
-   Strategy expectancy where appropriate

Prefer bootstrap methods that respect session grouping when multiple
observations originate from one trading day.

## 10.3 Baseline comparison

Display:

``` text
Model accuracy
Majority baseline
Absolute improvement
Relative improvement
Confidence interval
Significance statistic / bootstrap probability
```

## 10.4 Minimum evidence gates

Create configurable research gates.

Example:

``` text
minimum_independent_sessions
minimum_regime_samples
minimum_strategy_setups
maximum_ECE
maximum_Brier
minimum_baseline_improvement
```

Do not choose final thresholds solely to make the current best model
pass.

------------------------------------------------------------------------

# 11. Phase 18 --- Explainability

## Goal

Explain why a model produced a probability without allowing the LLM to
invent causal explanations.

## 11.1 Global importance

Store model-level feature importance.

## 11.2 Local explanations

For supported tree models, add SHAP-based local explanations.

Example UI:

``` text
60m bullish probability: 67%

Positive contributors:
+ NQ/ES relative strength
+ Overnight direction
+ Trend regime

Negative contributors:
- Extended distance from VWAP
- High-volatility regime
```

Prefer relative contribution displays unless a mathematically valid
probability contribution is available.

## 11.3 LLM integration

Flow:

``` text
Deterministic evidence
        ↓
Model probability
        ↓
SHAP / explainability output
        ↓
LLM explanation
```

The LLM may translate the explanation into readable language but may not
alter model values or feature contributions.

------------------------------------------------------------------------

# 12. Phase 19 --- Historical Research Replay

## Goal

Allow a user to experience a historical session without seeing future
information.

## 12.1 Replay controls

User selects:

``` text
date
time
snapshot
```

Example:

``` text
2025-03-13
09:25 ET
```

## 12.2 Replay display

Before outcome reveal, display only information available at that
timestamp:

-   Market context
-   Important levels
-   Overnight structure
-   Higher-timeframe structure
-   Macro context
-   Known news
-   Scheduled events
-   Regime
-   Historical analogues
-   PB strategy state
-   ML probabilities
-   Deterministic bias
-   Bull/bear evidence
-   Invalidation conditions

## 12.3 Hidden future

Do not initially display:

-   Future candles
-   Session high/low formed later
-   Outcome
-   MFE/MAE
-   Future headlines

Provide an explicit:

``` text
Reveal Outcome
```

action.

## 12.4 Replay integrity

Replay must query the same point-in-time feature snapshot used by the
research dataset rather than recalculating with unrestricted current
data.

------------------------------------------------------------------------

# 13. Phase 20 --- Forward Paper Testing

## Goal

Evaluate the complete system on truly unseen future sessions.

## 13.1 Immutable predictions

At configured timestamps, persist:

``` text
prediction_id
timestamp
model_version
dataset_version
feature_version
strategy_version

bias
confidence

probability_5m
probability_15m
probability_30m
probability_60m
probability_120m

strategy_state
evidence
invalidation
```

Once created, the prediction must not be edited.

Corrections require a new record/version.

## 13.2 Outcome attachment

After each horizon/session completes, automatically attach outcomes.

Maintain existing automation behavior and extend it to all supported
targets.

## 13.3 Forward-only dashboard

Separate:

``` text
Historical backtest
```

from:

``` text
Forward paper test
```

Never mix their performance numbers.

Forward performance should eventually become the strongest evidence for
whether NQMATE provides useful signal.

------------------------------------------------------------------------

# 14. Data Quality Framework

Add automated validation for historical and forward data.

Checks should include:

``` text
missing minutes
duplicate bars
invalid OHLC
contract mismatch
rollover discontinuity
timezone mismatch
session-boundary errors
future-data leakage
missing target horizon
duplicate prediction
feature-version mismatch
```

Generate a quality report for each backfill batch.

Bad sessions should be quarantined rather than silently included.

------------------------------------------------------------------------

# 15. Dataset Versioning

Every training run must reference an immutable dataset version.

Suggested metadata:

``` text
dataset_version
created_at
start_date
end_date
session_count
snapshot_count
feature_version
target_version
data_quality_version
git_commit
```

The model registry should retain this reference.

A result must therefore be reproducible as:

``` text
Git commit
+
Dataset version
+
Feature version
+
Target version
+
Model configuration
```

------------------------------------------------------------------------

# 16. Dashboard Improvements

## Evaluation Dashboard

Add:

-   Independent session count
-   Confidence intervals
-   Baseline comparison
-   Calibration chart
-   Brier score
-   ECE
-   Walk-forward results
-   Regime breakdown
-   Event-type breakdown
-   Historical vs forward distinction

## Strategy Dashboard

Add:

-   Setup count
-   Strategy version
-   Win rate
-   Expectancy
-   Average R
-   MFE/MAE
-   Regime performance
-   Confidence intervals
-   Setup-state history

## Model Registry

Show:

``` text
model
model_version
dataset_version
feature_version
training period
validation period
sample size
baseline
accuracy
Brier
ECE
promotion status
```

## Historical Dashboard

Add the replay workflow defined in Phase 19.

------------------------------------------------------------------------

# 17. Recommended Implementation Order

Do not implement all phases simultaneously.

### Priority 1 --- Data

``` text
Two-year NQ/ES backfill
→ validate bars
→ reconstruct sessions
→ create point-in-time snapshots
→ attach outcomes
```

### Priority 2 --- Evaluation integrity

``` text
Dataset versioning
→ session-level sample accounting
→ confidence intervals
→ statistical baseline comparison
```

### Priority 3 --- Strategy

``` text
Finalize PB definitions
→ state machine
→ historical detector
→ strategy outcomes
→ regime-conditioned statistics
```

### Priority 4 --- ML

``` text
Rebuild training dataset
→ rerun baselines
→ Logistic Regression
→ Gradient Boosting
→ XGBoost
→ LightGBM
→ walk-forward comparison
→ calibration
```

### Priority 5 --- Research UX

``` text
SHAP
→ historical replay
→ improved evaluation dashboard
```

### Priority 6 --- Forward validation

``` text
Immutable daily predictions
→ automatic outcomes
→ forward paper-test dashboard
```

------------------------------------------------------------------------

# 18. Milestones

## Milestone A --- Historical Dataset

Target:

``` text
~2 years
~500 sessions
complete NQ history
ES context where available
validated snapshots
complete major-horizon outcomes
```

## Milestone B --- PB Dataset

Target:

``` text
deterministic PB definitions
versioned detector
historical setup inventory
sufficient setup count for evaluation
```

Do not set an arbitrary minimum count solely to declare success.

## Milestone C --- ML Evaluation

Requirements:

-   Repeated walk-forward validation
-   Baseline comparisons
-   Calibration metrics
-   Confidence intervals
-   No leakage
-   Reproducible dataset/model versions

## Milestone D --- Forward Research

Requirements:

-   Immutable predictions
-   Automatic outcomes
-   No manual retroactive editing
-   Historical and forward results separated

------------------------------------------------------------------------

# 19. Explicit Non-Goals

Do **not** add during these phases:

-   Automated order execution
-   Brokerage execution integration
-   Reinforcement-learning trading agents
-   Autonomous strategy modification
-   LLM-generated numerical market features
-   Unversioned model promotion
-   Retrospective modification of predictions
-   Future information in historical features

Deep learning should remain post-V2 research unless the available
dataset and experiments provide a concrete reason to introduce it.

------------------------------------------------------------------------

# 20. Definition of Success

NQMATE V2 is successful when it can answer:

> Given only information available at this exact historical timestamp,
> what did the deterministic system, strategy engine, analogue engine,
> and ML models believe --- and how did those beliefs perform across
> hundreds of genuinely out-of-sample sessions?

The goal is **not** to maximize backtest accuracy.

The goal is to establish whether any component demonstrates a
repeatable, calibrated, statistically credible out-of-sample edge.

------------------------------------------------------------------------

# 21. Immediate Next Task

The immediate implementation task should be:

``` text
Implement the Historical Research Dataset V2 backfill pipeline.

1. Extend NQ historical coverage to approximately two years.
2. Backfill corresponding ES history required by relative-strength features.
3. Validate minute-bar completeness and futures rollover handling.
4. Reconstruct completed sessions from canonical 1-minute data.
5. Generate versioned point-in-time feature snapshots.
6. Generate all supported outcome horizons.
7. Add MFE/MAE and barrier/liquidity targets.
8. Produce a data-quality report.
9. Do not retrain/promote models until the rebuilt dataset passes validation.
10. Preserve strict point-in-time correctness and fail closed when required evidence is unavailable.
```

------------------------------------------------------------------------

# 22. Codex Handoff Prompt

``` text
Continue NQMATE using this V2 specification.

First read AGENTS.md, docs/PROJECT.md, docs/CURRENT_STATE.md, the existing ML/target documentation, and this specification. Inspect existing implementations before creating new abstractions.

Begin with Phase 10: Historical Research Dataset V2.

Backfill approximately two years of NQ 1-minute history and the corresponding ES data required by existing relative-strength features. Preserve existing contract/rollover handling and treat stored 1-minute bars as market-data truth.

Do not simply generate retrospective AI predictions. Instead, reconstruct immutable point-in-time feature snapshots using only information available at each snapshot timestamp, then calculate future outcomes separately.

Add/extend dataset versioning, data-quality validation, point-in-time leakage tests, major directional horizons, continuous returns, MFE/MAE, barrier targets, and liquidity-first outcomes.

Reuse existing schemas/services whenever possible. Do not duplicate functionality solely to match this specification.

Do not promote an ML model as part of the backfill. After the dataset is validated, later phases will rerun baselines and challengers with repeated chronological walk-forward validation.

Preserve these invariants:
- Research only; no automated trade execution.
- No look-ahead bias.
- Deterministic calculations remain in Python.
- LLMs explain supplied evidence only.
- Raw candles remain in Supabase/PostgreSQL rather than Neo4j.
- Missing historical evidence remains missing; never fabricate it.
- Model promotion remains manual and evidence-gated.
- Preserve intentional existing user changes.

Add tests for all new deterministic behavior, run relevant tests/builds, and update docs/CURRENT_STATE.md concisely after meaningful completed work.
```
