from __future__ import annotations

from statistics import mean, median, pstdev
from typing import Any, Sequence


def calculate_performance(outcomes: Sequence[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(item["return_pct"]) for item in outcomes if isinstance(item.get("return_pct"), (int, float))]
    mfe = [float(item["mfe"]) for item in outcomes if isinstance(item.get("mfe"), (int, float))]
    mae = [float(item["mae"]) for item in outcomes if isinstance(item.get("mae"), (int, float))]
    regime_returns: dict[str, list[float]] = {}
    for item in outcomes:
        regime = item.get("regime")
        value = item.get("return_pct")
        if isinstance(regime, str) and regime and isinstance(value, (int, float)):
            regime_returns.setdefault(regime, []).append(float(value))
    regime_means = {regime: mean(values) for regime, values in regime_returns.items()}
    best_regime = max(regime_means, key=lambda regime: (regime_means[regime], regime)) if regime_means else None
    worst_regime = min(regime_means, key=lambda regime: (regime_means[regime], regime)) if regime_means else None
    average = mean(returns) if returns else None
    deviation = pstdev(returns) if len(returns) > 1 else None
    return {
        "sample_size": float(len(returns)),
        "win_rate": sum(value > 0 for value in returns) / len(returns) if returns else 0.0,
        "mean_return": average,
        "median_return": median(returns) if returns else None,
        "expectancy": average,
        "mfe_mean": mean(mfe) if mfe else None,
        "mae_mean": mean(mae) if mae else None,
        "sharpe_like": average / deviation if average is not None and deviation else None,
        "best_regime": best_regime,
        "worst_regime": worst_regime,
    }
