from __future__ import annotations

from math import log
from statistics import mean
from typing import Sequence

from nqmate_api.ml.baselines import LabeledRow, always_long_probability, fit_logistic, majority_probability, overnight_direction_probability, predict_logistic
from nqmate_api.ml.boosted import XGBoostClassifier
from nqmate_api.ml.validation import walk_forward_splits


def classification_metrics(labels: Sequence[int], probabilities: Sequence[float]) -> dict[str, float | None]:
    if len(labels) != len(probabilities):
        raise ValueError("labels and probabilities must be aligned")
    if not labels:
        return {"sample_size": 0.0, "accuracy": None, "precision": None, "recall": None, "brier_score": None, "log_loss": None, "roc_auc": None}
    predicted = [int(probability >= 0.5) for probability in probabilities]
    true_positive = sum(actual == predicted_value == 1 for actual, predicted_value in zip(labels, predicted))
    false_positive = sum(actual == 0 and predicted_value == 1 for actual, predicted_value in zip(labels, predicted))
    false_negative = sum(actual == 1 and predicted_value == 0 for actual, predicted_value in zip(labels, predicted))
    positives = sum(label == 1 for label in labels)
    negatives = len(labels) - positives
    positive_values = [probability for actual, probability in zip(labels, probabilities) if actual == 1]
    negative_values = [probability for actual, probability in zip(labels, probabilities) if actual == 0]
    wins = sum(positive > negative for positive in positive_values for negative in negative_values)
    ties = sum(positive == negative for positive in positive_values for negative in negative_values)
    return {
        "sample_size": float(len(labels)),
        "accuracy": sum(actual == predicted_value for actual, predicted_value in zip(labels, predicted)) / len(labels),
        "precision": true_positive / (true_positive + false_positive) if true_positive + false_positive else None,
        "recall": true_positive / (true_positive + false_negative) if true_positive + false_negative else None,
        "brier_score": mean((probability - label) ** 2 for label, probability in zip(labels, probabilities)),
        "log_loss": mean(-(label * log(max(probability, 1e-15)) + (1 - label) * log(max(1 - probability, 1e-15))) for label, probability in zip(labels, probabilities)),
        "roc_auc": (wins + 0.5 * ties) / (positives * negatives) if positives and negatives else None,
    }


def _merge_predictions(labels: list[int], predictions: list[float], values: Sequence[tuple[Sequence[int], Sequence[float]]]) -> None:
    for test_labels, test_predictions in values:
        labels.extend(test_labels)
        predictions.extend(test_predictions)


def evaluate_walk_forward(rows: Sequence[LabeledRow], min_train_size: int, test_size: int = 1, include_xgboost: bool = False) -> dict[str, dict[str, float | None]]:
    names = ("majority", "always_long", "overnight_direction", "logistic", "xgboost") if include_xgboost else ("majority", "always_long", "overnight_direction", "logistic")
    predictions: dict[str, list[tuple[Sequence[int], Sequence[float]]]] = {name: [] for name in names}
    for train, test in walk_forward_splits(rows, min_train_size, test_size):
        train_labels = tuple(row.target for row in train)
        test_labels = [row.target for row in test]
        predictions["majority"].append((test_labels, [majority_probability(train_labels)] * len(test)))
        predictions["always_long"].append((test_labels, [always_long_probability()] * len(test)))
        overnight = [overnight_direction_probability(row.overnight_return) for row in test]
        predictions["overnight_direction"].append((test_labels, [value if value is not None else majority_probability(train_labels) for value in overnight]))
        model = fit_logistic(tuple(row.features for row in train), train_labels)
        predictions["logistic"].append((test_labels, predict_logistic(model, tuple(row.features for row in test))))
        if include_xgboost:
            if len(set(train_labels)) < 2:
                boosted_predictions = [majority_probability(train_labels)] * len(test)
            else:
                boosted = XGBoostClassifier().fit(tuple(row.features for row in train), train_labels)
                boosted_predictions = boosted.predict_probability(tuple(row.features for row in test))
            predictions["xgboost"].append((test_labels, boosted_predictions))
    result: dict[str, dict[str, float | None]] = {}
    for name, folds in predictions.items():
        labels: list[int] = []
        probabilities: list[float] = []
        _merge_predictions(labels, probabilities, folds)
        result[name] = classification_metrics(labels, probabilities)
    return result
