## When to read this file

Read for leakage prevention, walk-forward evaluation, calibration, drift, retraining, and model promotion.

# Validation

## Walk-forward evaluation

Use expanding or rolling time splits, for example train months 1–6 and validate month 7, then train 1–7 and validate month 8. Never randomly shuffle time-series rows. For overlapping forward-return labels, use purging and embargo periods where needed.

## Metrics

Track accuracy, precision, recall, ROC-AUC, Brier score, log loss, conditional return, MFE, and MAE. Accuracy alone is insufficient. Evaluate across multiple windows, regimes, event types, and cost/slippage assumptions.

## Calibration

Test Platt scaling and isotonic regression. Track Brier score, expected calibration error, and reliability curves. The dashboard should show calibrated probability; confidence bins such as 50–55 through 80+ must correspond to observed outcomes.

## Leakage and reproducibility

Every feature must satisfy `available_at <= prediction_time`; use point-in-time macro vintages and news publication times. Record dataset, feature, label, model, prompt, provider, contract, and Git versions so predictions can be reconstructed.

## Drift and promotion

Monitor feature/prediction distributions, accuracy, Brier score, conditional return, and SHAP distributions. Classify drift as NORMAL, WATCH, or DEGRADED; do not auto-retrain solely on drift. Start with monthly or manual retraining. A challenger promotes only if it beats the champion out of sample across multiple windows, does not materially degrade calibration, and passes leakage tests. Never update weights during a trading session.

