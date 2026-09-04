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
