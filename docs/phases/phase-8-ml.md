## When to read this file

Read to implement baseline and first serious tabular ML. Also read [features.md](../ml/features.md), [targets.md](../ml/targets.md), [models.md](../ml/models.md), and [validation.md](../ml/validation.md).

# Goal

Train calibrated, versioned, walk-forward models that add measurable value beyond simple baselines and analogue retrieval.

# Dependencies

[Phase 7](phase-7-strategy-memory.md), sufficient point-in-time feature/outcome data, and versioned dataset tooling.

# Tasks

- Build 30m/60m/close and structure labels and majority/always-long/overnight-direction baselines.
- Train logistic regression, then XGBoost or LightGBM with walk-forward evaluation, calibration, SHAP, and model registry.
- Add multi-target outputs, graph/analogue features, and ensemble probabilities only after component validation.
- Store model/dataset/feature/label versions and component predictions.

The baseline slice adds `nqmate_api.ml.baselines` and `nqmate_api.ml.validation`. It provides deterministic majority-class, always-long, overnight-direction, and logistic-regression baselines plus chronological walk-forward splits and point-in-time row filtering. The logistic implementation is intentionally small and dependency-light; it is a benchmark, not the first serious production model.

The dataset slice adds `nqmate_api.ml.dataset`. It creates exact-timestamp forward direction labels, skips missing future bars, and builds versioned feature matrices only from snapshots available at their feature timestamp. The target timestamp remains historical outcome information for training, never an input feature.

The evaluation slice adds `nqmate_api.ml.metrics`. It calculates accuracy, precision, recall, Brier score, log loss, and ROC-AUC, then compares all four baselines on chronological out-of-sample folds. Missing overnight direction falls back to the training-fold majority rate and is never fabricated as a signal.

The metadata slice adds `ml_datasets`, `ml_models`, migration `018_ml_metadata.sql`, and `nqmate_api.ml.repository`. Dataset versions are idempotent and model records use insert-only artifact registration so a trained artifact is never silently replaced. Records retain target, feature/dataset versions, training dates, metrics, hyperparameters, and artifact path.

# Acceptance Criteria

Models beat relevant simple baselines out of sample across multiple windows without leakage; calibrated probabilities and metrics are visible; artifacts are immutable and reproducible. The baseline slice is the prerequisite measurement layer and does not claim Phase 8 acceptance by itself.

# Tests

Feature availability/leakage, label horizons, purging/embargo where needed, walk-forward splits, calibration, registry, and model API tests.

# Explicitly Out of Scope

Deep learning, multimodal fusion, RL, live weight updates, and direct brokerage execution.

# Next Phase

[Phase 9 — Evaluation](phase-9-evaluation.md).
