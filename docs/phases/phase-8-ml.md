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

# Acceptance Criteria

Models beat relevant simple baselines out of sample across multiple windows without leakage; calibrated probabilities and metrics are visible; artifacts are immutable and reproducible.

# Tests

Feature availability/leakage, label horizons, purging/embargo where needed, walk-forward splits, calibration, registry, and model API tests.

# Explicitly Out of Scope

Deep learning, multimodal fusion, RL, live weight updates, and direct brokerage execution.

# Next Phase

[Phase 9 — Evaluation](phase-9-evaluation.md).

