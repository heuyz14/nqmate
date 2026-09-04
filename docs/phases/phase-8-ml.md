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

The historical baseline runner adds `jobs/evaluate_ml_baselines.py` and `nqmate_api.ml.evaluation`. It reads stored analogue vectors/outcomes, builds 30-minute direction rows from pre-session numeric features, evaluates chronological folds, and registers the dataset plus inactive baseline model metadata. It returns no results when there are not enough rows for the requested training window.

The first stored baseline run covered 151 out-of-sample rows from the available 2026 analogue history. The majority baseline scored 52.98% accuracy; always-long scored 52.98%; overnight-direction scored 49.67%; and the dependency-light logistic baseline scored 49.01%. These are benchmark results only; no model is promoted based on this run.

The XGBoost challenger adds `nqmate_api.ml.boosted` and the optional `ml` dependency extra. It uses the same chronological folds and metadata registry as the baselines. On the first 151-row run it scored 49.67% accuracy, below the majority baseline, so it remains inactive and is not promoted.

The target-contract slice adds `nqmate_api.ml.targets`. It explicitly names 5m, 15m, 30m, 60m, 120m, 240m, and close direction targets and builds exact-time forward target matrices from canonical bars. Missing future timestamps remain absent.

The historical-outcome expansion adds 5m, 15m, 120m, and 240m return fields when exact bars exist. The current stored history contains 95 sessions with 5m/15m outcomes, 2 with 120m, and 0 with 240m. Initial short-horizon comparisons are registered but not promoted: 5m XGBoost/LightGBM tied at 51.89% while always-long reached 50.00%; 15m scikit-learn Gradient Boosting led challengers at 54.30% while the simple baselines reached 56.29%.

The evaluation runner now accepts horizon-specific stored outcomes and creates separate target/dataset/model identities. The first 60-minute run also covered 151 out-of-sample rows: always-long scored 56.29%, XGBoost 54.30%, majority 54.97%, and logistic 44.37%. XGBoost remains inactive because it did not beat the relevant simple baseline.

The three-way boosting comparison found that for 30m, XGBoost scored 49.67%, scikit-learn Gradient Boosting 43.71%, and LightGBM 45.03%; none beat the 52.98% majority baseline. For 60m, scikit-learn Gradient Boosting scored 58.94%, XGBoost 54.30%, and LightGBM 54.30%; scikit-learn Gradient Boosting is the current best candidate over the 56.29% always-long baseline. It remains inactive pending multiple-window validation and calibration.

The calibration slice adds `nqmate_api.ml.calibration`. It provides expected calibration error, multiple expanding walk-forward windows, and a promotion gate requiring accuracy improvement plus no worse Brier score than the baseline. These safeguards prevent selecting the 60m candidate from one window alone.

The multi-window runner adds `jobs/evaluate_ml_windows.py`. It evaluates the stored 60m target with configurable expanding training sizes and test windows, including all boosting implementations, and prints JSON for review without activating or overwriting model records.

The first multi-window report used 10-row test windows with training sizes 20, 40, and 60. scikit-learn Gradient Boosting led accuracy in every window (59.44%, 61.80%, and 63.92%), but its Brier scores (0.321, 0.296, and 0.270) were worse than the majority baseline (about 0.248). It therefore fails the calibration-aware promotion gate and remains inactive.

The candle-horizon slice adds deterministic persistence for `5m`, `15m`, `1h`, `2h`, `4h`, and `1d` bars in `jobs/populate_market_timeframes.py`. It derives every requested candle only from stored `1min` bars, with `2h`/`4h` corresponding to the `120m`/`240m` ML horizons. The job is historical and resumable by date range; it does not add a live market feed.

The post-population 5m and 15m evaluations each produced 151 out-of-sample rows. The 5m XGBoost and LightGBM challengers both scored 53.64% accuracy but were not activated; the 15m majority baseline scored 56.29%, so no challenger was promoted.

# Acceptance Criteria

Models beat relevant simple baselines out of sample across multiple windows without leakage; calibrated probabilities and metrics are visible; artifacts are immutable and reproducible. The baseline slice is the prerequisite measurement layer and does not claim Phase 8 acceptance by itself.

# Tests

Feature availability/leakage, label horizons, purging/embargo where needed, walk-forward splits, calibration, registry, and model API tests.

# Explicitly Out of Scope

Deep learning, multimodal fusion, RL, live weight updates, and direct brokerage execution.

# Next Phase

[Phase 9 — Evaluation](phase-9-evaluation.md).
