from __future__ import annotations

from statistics import mean
from typing import Any, Mapping, Sequence


def summarize_prediction_outcomes(outcomes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build deterministic, read-only diagnostics grouped by realized horizon."""
    by_horizon: dict[str, list[Mapping[str, Any]]] = {}
    for outcome in outcomes:
        horizon = str(outcome.get("horizon", ""))
        if horizon:
            by_horizon.setdefault(horizon, []).append(outcome)

    horizons: dict[str, dict[str, float | None]] = {}
    for horizon, items in sorted(by_horizon.items()):
        returns = [float(item["realized_return"]) for item in items if isinstance(item.get("realized_return"), (int, float))]
        correctness = [bool(item["correct"]) for item in items if isinstance(item.get("correct"), bool)]
        horizons[horizon] = {
            "sample_size": float(len(items)),
            "evaluated_size": float(len(correctness)),
            "accuracy": mean(correctness) if correctness else None,
            "average_return": mean(returns) if returns else None,
            "win_rate": mean(value > 0 for value in returns) if returns else None,
        }
    return {"sample_size": float(len(outcomes)), "horizons": horizons}


def confidence_calibration(records: Sequence[Mapping[str, Any]], bins: int = 10) -> list[dict[str, float]]:
    """Compare stored confidence with observed correctness in fixed bins."""
    if bins < 1:
        raise ValueError("bins must be positive")
    result: list[dict[str, float]] = []
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        members = [item for item in records
                   if isinstance(item.get("confidence"), (int, float))
                   and isinstance(item.get("correct"), bool)
                   and lower <= float(item["confidence"]) < upper
                   or (index == bins - 1 and isinstance(item.get("confidence"), (int, float))
                       and isinstance(item.get("correct"), bool) and float(item["confidence"]) == upper)]
        if members:
            observed = mean(bool(item["correct"]) for item in members)
            predicted = mean(float(item["confidence"]) for item in members)
            result.append({"lower": lower, "upper": upper, "sample_size": float(len(members)),
                           "mean_confidence": predicted, "observed_accuracy": observed,
                           "calibration_gap": abs(predicted - observed)})
    return result
