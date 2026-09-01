## When to read this file

Read before creating labels, evaluation tables, prediction schemas, or multi-horizon models.

# Targets

## Direction targets

Train separate targets for NQ higher in 5m, 15m, 30m, 60m, 120m, and at session close. Also support close-vs-prediction-time direction, 60-minute forward return direction, and first 1-ATR move direction.

## Structure targets

Include ONH breaks before ONL, ONL before ONH, PDH break, PDL break, opening-range breakout success/failure, trend day, reversal day, balanced day, and first-break direction.

## Strategy targets

For each strategy, label whether +1R occurs before -1R, whether target is reached, expected MFE, expected MAE, and expected R.

## Session outcomes

At close calculate open-to-close return, high/low after open, morning/afternoon return, maximum up/down excursion, ONH/ONL/PDH/PDL breaks, first break direction, and trend/balanced/reversal labels. Store multiple horizons: 5m, 15m, 30m, 60m, 120m, and close.

## Prediction records

Every immutable `BiasPrediction` stores creation time, session date, seven-state direction (`STRONG_BEARISH` through `STRONG_BULLISH`), confidence, bull/bear scores, catalyst risk, evidence IDs, counter-evidence IDs, invalidations, model, prompt version, and feature version. Never overwrite predictions; attach realized outcomes later.

