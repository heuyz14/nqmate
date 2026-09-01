## When to read this file

Read to implement automatic prediction evaluation, calibration/drift reporting, and research diagnostics. Also read [validation.md](../ml/validation.md), [targets.md](../ml/targets.md), and [dashboard.md](../frontend/dashboard.md).

# Goal

Close the learning loop with reconstructable prediction outcomes, calibration, model/regime analysis, and controlled promotion.

# Dependencies

[Phase 8](phase-8-ml.md), completed session outcomes, immutable predictions, model registry, and dashboard foundations.

# Tasks

- Automatically attach realized outcomes to every prediction across all horizons.
- Build calibration, accuracy by confidence/regime/event, feature importance, drift indicators, and performance dashboards.
- Add observability for prediction ID, timestamps, providers, counts, similar sessions, model/prompt versions, runtime, and errors.
- Add champion/challenger comparisons and controlled monthly/manual retraining promotion checks.

# Acceptance Criteria

An old prediction can be reconstructed from exact inputs and versions; confidence bins compare predicted and observed results; drift is visible; challenger promotion requires out-of-sample and calibration evidence.

# Tests

Outcome attachment, metric/calibration calculations, reconstruction, drift classification, champion/challenger rules, and end-to-end evaluation tests.

# Explicitly Out of Scope

Deep-learning adoption, RL, autonomous execution, and live in-session model updates.

# Next Phase

Post-V1 research: [deep-learning.md](../ml/deep-learning.md), followed by multimodal research and experimental RL under its stated safeguards.

