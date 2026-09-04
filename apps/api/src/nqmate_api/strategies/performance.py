from __future__ import annotations

from statistics import mean, median, pstdev
from typing import Any, Sequence


def calculate_performance(outcomes: Sequence[dict[str, Any]]) -> dict[str, float | None]:
    returns = [float(item["return_pct"]) for item in outcomes if isinstance(item.get("return_pct"), (int, float))]
    mfe = [float(item["mfe"]) for item in outcomes if isinstance(item.get("mfe"), (int, float))]
    mae = [float(item["mae"]) for item in outcomes if isinstance(item.get("mae"), (int, float))]
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
    }
