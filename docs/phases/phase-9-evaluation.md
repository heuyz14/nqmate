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

The reconstruction slice adds migration `019_prediction_reconstruction.sql` and stores the exact deterministic `BiasSnapshot` in each new bias prediction as `input_snapshot`, alongside the model and feature versions. Apply migration 019 before creating predictions against the hosted database.

The outcome-attachment slice adds migration `020_prediction_outcomes.sql`, `nqmate_api.bias.outcomes`, and `jobs/attach_prediction_outcomes.py`. It attaches only numeric realized outcomes from an explicitly selected historical session, idempotently by prediction and horizon. It never infers a session date from prediction creation time or imputes a missing horizon. Apply migration 020 before using the job.

The diagnostics slice adds `nqmate_api.bias.evaluation` and `GET /api/v1/bias/{prediction_id}/evaluation`. It reports sample coverage, accuracy for directional predictions, average realized return, and positive-return rate by horizon without mutating the prediction.

The calibration slice adds `GET /api/v1/bias/evaluation`, which reads a bounded prediction history and attached outcomes to report fixed confidence-bin sample sizes, mean confidence, observed accuracy, and calibration gaps. Neutral predictions are excluded from correctness bins.

The drift slice adds deterministic feature-window comparison and `GET /api/v1/bias/drift`. It compares numeric `input_snapshot` means between older and newer bounded prediction windows and reports `STABLE`, `WATCH`, or `DRIFT`; missing fields are skipped.

The champion/challenger slice adds `champion_challenger_report` and `jobs/report_model_comparisons.py`. It deterministically prefers the majority baseline, excludes all simple baselines from challenger output, and marks eligibility only when accuracy improves and Brier score does not regress. The report is read-only; activation remains manual and gated.

The registry visibility slice adds bounded `GET /api/v1/ml/models`, optionally filtered by target. It exposes stored algorithm, version, metrics, dataset identity, and active state for dashboards and manual review; it does not activate or modify models.

The comparison API adds read-only `GET /api/v1/ml/models/comparison`, optionally filtered by target, using the same deterministic baseline and Brier-score gate as the CLI report.

The grouped-diagnostics slice adds `grouped_outcome_metrics`, which summarizes accuracy and average return by an explicitly stored regime or event label and skips unlabeled outcomes. Persistence of those labels is deferred until the source fields are available.

The reconstruction verification slice adds read-only `GET /api/v1/bias/{prediction_id}/reconstruction`, returning the exact persisted input snapshot, result fields, model/feature versions, creation time, and attached outcomes.

The observability slice adds `observability_summary` and bounded `GET /api/v1/bias/observability`, reporting prediction/outcome coverage, reconstruction completeness, and model/feature version sets without returning secrets or mutating records.

The automatic attachment slice adds migration `021_prediction_session_date.sql` and `jobs/attach_completed_prediction_outcomes.py`. Predictions generated with an explicit analogue session context retain that session date, allowing the job to attach completed historical outcomes idempotently. Predictions without explicit session context remain safely unattached.

The daily attachment slice adds `jobs/attach_completed_prediction_outcomes_daily.py` and `ops/com.nqmate.prediction-outcomes-daily.plist`. When installed as a macOS LaunchAgent, it runs at 4:15 PM America/New_York after the daily market update and reuses the bounded, idempotent attachment job. Installation remains an operator action; it does not create predictions or infer missing session dates.

The dashboard slice adds the responsive `/evaluation` page. It reads the evaluation, drift, registry, and champion/challenger APIs and presents coverage metrics, confidence calibration, drift statuses, and manual promotion state with loading, error, and empty states. The primary historical market desk is available at `/dashboard`; its visual contract is documented in [dashboard.md](../frontend/dashboard.md). It displays stored completed-session candles and deterministic levels only, with no live-feed or execution claim.

# Acceptance Criteria

An old prediction can be reconstructed from exact inputs and versions; confidence bins compare predicted and observed results; drift is visible; challenger promotion requires out-of-sample and calibration evidence.

# Tests

Outcome attachment, metric/calibration calculations, reconstruction, drift classification, champion/challenger rules, and end-to-end evaluation tests.

# Explicitly Out of Scope

Deep-learning adoption, RL, autonomous execution, and live in-session model updates.

# Next Phase

Post-V1 research: [deep-learning.md](../ml/deep-learning.md), followed by multimodal research and experimental RL under its stated safeguards.
