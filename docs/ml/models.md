## When to read this file

Read for the ML progression, model families, ensembles, attribution, registry, and promotion rules.

# Models

## Required progression

Start with majority-class, always-long, overnight-direction, and logistic-regression baselines. The first serious tabular model is XGBoost or LightGBM. A model is accepted only when it improves walk-forward out-of-sample performance over simpler baselines.

## Multi-target and ensembles

Train separate models for direction horizons, structure, and strategy outcomes. Once validated, combine logistic, boosted-tree, historical-analogue, and regime-specific probabilities. An initial example is `.20 logistic + .45 XGBoost + .20 analogue + .15 regime`; weights must later be learned rather than permanently hardcoded. Store all component probabilities.

## Regime-specific models

Possible models cover high/low volatility, macro/non-event, gap-up/down, overnight-trend, and range-bound regimes. Require sufficient samples; otherwise fall back to the global model.

## Explainability

For tree models track gain importance, permutation importance, and SHAP. Show global importance, today’s factors, regime-specific importance, and model-version changes. SHAP is explanatory evidence, not causality.

## Advanced capabilities

Preserve the roadmap for NQ-specific news impact, embeddings, similar-news retrieval, post-news labels, graph-derived numeric features, model drift, calibration, champion/challenger operation, model registry, and dataset versioning. See [deep-learning.md](deep-learning.md) for later sequence and multimodal research.

## Registry and API

`ml_models` stores ID, name, target, algorithm/version, training dates, feature/dataset versions, metrics, hyperparameters, artifact path, creation time, and active state. Never replace artifacts in place. Later protected endpoints include model/prediction/feature/calibration/performance reads and `/ml/train`/`/ml/backtest`; training must not be public frontend functionality.

General directional models and strategy-specific models are separate concerns. The current Phase 8 models use session/pre-session features and directional session outcomes; they are not used by the PB strategy evaluator. A PB model may be added later only after enough valid PB setup occurrences and strategy outcomes exist, with its own target and dataset version.
