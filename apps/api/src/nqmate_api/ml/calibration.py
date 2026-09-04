from __future__ import annotations

from statistics import mean
from typing import Any, Mapping, Sequence

from nqmate_api.ml.baselines import LabeledRow, majority_probability
from nqmate_api.ml.metrics import classification_metrics, evaluate_walk_forward
from nqmate_api.ml.validation import walk_forward_splits


def expected_calibration_error(labels: Sequence[int], probabilities: Sequence[float], bins: int = 10) -> float | None:
    if len(labels) != len(probabilities):
        raise ValueError("labels and probabilities must be aligned")
    if not labels or bins < 1:
        return None
    total = 0.0
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        members = [(label, probability) for label, probability in zip(labels, probabilities) if lower <= probability < upper or (index == bins - 1 and probability == upper)]
        if members:
            total += len(members) / len(labels) * abs(mean(label for label, _ in members) - mean(probability for _, probability in members))
    return total


def promotion_eligible(candidate: dict[str, float | None], baseline: dict[str, float | None], minimum_accuracy_gain: float = 0.0) -> bool:
    candidate_accuracy, baseline_accuracy = candidate.get("accuracy"), baseline.get("accuracy")
    candidate_brier, baseline_brier = candidate.get("brier_score"), baseline.get("brier_score")
    return bool(
        candidate_accuracy is not None and baseline_accuracy is not None
        and candidate_accuracy > baseline_accuracy + minimum_accuracy_gain
        and candidate_brier is not None and baseline_brier is not None
        and candidate_brier <= baseline_brier
    )


def evaluate_multiple_windows(rows: Sequence[LabeledRow], train_sizes: Sequence[int], test_size: int = 1, include_all_boosting: bool = False) -> dict[int, dict[str, dict[str, float | None]]]:
    result: dict[int, dict[str, dict[str, float | None]]] = {}
    for train_size in train_sizes:
        splits = walk_forward_splits(rows, min_train_size=train_size, test_size=test_size)
        window_rows = tuple(item for split in splits for item in (*split[0], *split[1]))
        if len(window_rows) <= train_size:
            continue
        result[train_size] = evaluate_walk_forward(rows, min_train_size=train_size, test_size=test_size, include_all_boosting=include_all_boosting)
    return result


def champion_challenger_report(models: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Return baseline-gated registry comparisons without changing model state."""
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for model in models:
        target = str(model.get("target", ""))
        if target:
            grouped.setdefault(target, []).append(model)
    report: dict[str, list[dict[str, Any]]] = {}
    for target, candidates in grouped.items():
        baseline = next((item for item in candidates if item.get("algorithm") == "majority"), None)
        if baseline is None:
            baseline = next((item for item in candidates if item.get("algorithm") == "always_long"), None)
        if baseline is None:
            report[target] = []
            continue
        baseline_metrics = baseline.get("metrics") or {}
        comparisons = []
        for candidate in candidates:
            if candidate.get("algorithm") in {"majority", "always_long"}:
                continue
            metrics = candidate.get("metrics") or {}
            comparisons.append({
                "name": candidate.get("name"), "algorithm": candidate.get("algorithm"),
                "eligible": promotion_eligible(metrics, baseline_metrics),
                "accuracy": metrics.get("accuracy"), "brier_score": metrics.get("brier_score"),
            })
        report[target] = sorted(comparisons, key=lambda item: float(item["accuracy"] or -1), reverse=True)
    return report
