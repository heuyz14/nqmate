from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Sequence


@dataclass(frozen=True)
class LabeledRow:
    feature_timestamp: object
    available_at: object
    features: tuple[float, ...]
    target: int
    overnight_return: float | None = None


@dataclass(frozen=True)
class LogisticModel:
    coefficients: tuple[float, ...]
    intercept: float


def majority_probability(labels: Sequence[int]) -> float:
    if not labels:
        return 0.5
    return sum(1 for label in labels if label == 1) / len(labels)


def always_long_probability(labels: Sequence[int] | None = None) -> float:
    return 1.0


def overnight_direction_probability(overnight_return: float | None) -> float | None:
    if overnight_return is None or overnight_return == 0:
        return None
    return 1.0 if overnight_return > 0 else 0.0


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + exp(-value))
    positive = exp(value)
    return positive / (1 + positive)


def fit_logistic(features: Sequence[Sequence[float]], labels: Sequence[int], iterations: int = 2000, learning_rate: float = 0.1) -> LogisticModel:
    if not features or len(features) != len(labels):
        raise ValueError("features and labels must be non-empty and aligned")
    width = len(features[0])
    if width == 0 or any(len(row) != width for row in features):
        raise ValueError("all feature rows must have the same non-zero width")
    coefficients = [0.0] * width
    intercept = 0.0
    count = float(len(features))
    for _ in range(iterations):
        gradient = [0.0] * width
        intercept_gradient = 0.0
        for values, label in zip(features, labels):
            error = _sigmoid(intercept + sum(weight * value for weight, value in zip(coefficients, values))) - label
            intercept_gradient += error
            for index, value in enumerate(values):
                gradient[index] += error * value
        intercept -= learning_rate * intercept_gradient / count
        coefficients = [weight - learning_rate * delta / count for weight, delta in zip(coefficients, gradient)]
    return LogisticModel(tuple(coefficients), intercept)


def predict_logistic(model: LogisticModel, features: Sequence[Sequence[float]]) -> tuple[float, ...]:
    return tuple(_sigmoid(model.intercept + sum(weight * value for weight, value in zip(model.coefficients, values))) for values in features)
