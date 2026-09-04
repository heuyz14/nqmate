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


def feature_drift(
    reference: Sequence[Mapping[str, Any]], current: Sequence[Mapping[str, Any]], watch_threshold: float = 1.0,
    drift_threshold: float = 2.0,
) -> dict[str, dict[str, float | str]]:
    """Compare numeric input snapshots without treating missing values as drift."""
    if watch_threshold <= 0 or drift_threshold <= watch_threshold:
        raise ValueError("drift thresholds must be positive and ordered")
    names = sorted({name for row in (*reference, *current) for name, value in row.items()
                    if isinstance(value, (int, float))})
    result: dict[str, dict[str, float | str]] = {}
    for name in names:
        before = [float(row[name]) for row in reference if isinstance(row.get(name), (int, float))]
        after = [float(row[name]) for row in current if isinstance(row.get(name), (int, float))]
        if not before or not after:
            continue
        baseline = mean(before)
        latest = mean(after)
        scale = max((max(before) - min(before)) / 2, 1e-9)
        score = abs(latest - baseline) / scale
        status = "DRIFT" if score >= drift_threshold else "WATCH" if score >= watch_threshold else "STABLE"
        result[name] = {"reference_mean": baseline, "current_mean": latest, "score": score, "status": status}
    return result


def grouped_outcome_metrics(
    outcomes: Sequence[Mapping[str, Any]], group_key: str,
) -> dict[str, dict[str, float | None]]:
    """Summarize attached outcomes by an explicitly stored regime/event label."""
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for outcome in outcomes:
        group = outcome.get(group_key)
        if group is None:
            continue
        groups.setdefault(str(group), []).append(outcome)
    result: dict[str, dict[str, float | None]] = {}
    for group, items in sorted(groups.items()):
        correctness = [bool(item["correct"]) for item in items if isinstance(item.get("correct"), bool)]
        returns = [float(item["realized_return"]) for item in items if isinstance(item.get("realized_return"), (int, float))]
        result[group] = {
            "sample_size": float(len(items)),
            "accuracy": mean(correctness) if correctness else None,
            "average_return": mean(returns) if returns else None,
        }
    return result
