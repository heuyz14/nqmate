from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class XGBoostConfig:
    n_estimators: int = 100
    max_depth: int = 3
    learning_rate: float = 0.05
    random_state: int = 42


class XGBoostClassifier:
    """Small adapter that keeps the external model behind a stable project API."""

    def __init__(self, config: XGBoostConfig | None = None) -> None:
        self.config = config or XGBoostConfig()
        self._model = None

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> "XGBoostClassifier":
        try:
            from xgboost import XGBClassifier
        except ImportError as error:
            raise RuntimeError("XGBoost is required; install the API ml extra") from error
        self._model = XGBClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            random_state=self.config.random_state,
            eval_metric="logloss",
            n_jobs=1,
        )
        self._model.fit(features, labels)
        return self

    def predict_probability(self, features: Sequence[Sequence[float]]) -> tuple[float, ...]:
        if self._model is None:
            raise RuntimeError("XGBoostClassifier must be fitted before prediction")
        return tuple(float(row[1]) for row in self._model.predict_proba(features))


class SklearnGradientBoostingClassifier:
    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self._model = None

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> "SklearnGradientBoostingClassifier":
        try:
            from sklearn.ensemble import GradientBoostingClassifier
        except ImportError as error:
            raise RuntimeError("scikit-learn is required; install the API ml extra") from error
        self._model = GradientBoostingClassifier(random_state=self.random_state)
        self._model.fit(features, labels)
        return self

    def predict_probability(self, features: Sequence[Sequence[float]]) -> tuple[float, ...]:
        if self._model is None:
            raise RuntimeError("SklearnGradientBoostingClassifier must be fitted before prediction")
        return tuple(float(row[1]) for row in self._model.predict_proba(features))


class LightGBMClassifier:
    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self._model = None

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> "LightGBMClassifier":
        try:
            from lightgbm import LGBMClassifier
        except ImportError as error:
            raise RuntimeError("LightGBM is required; install the API ml extra") from error
        self._model = LGBMClassifier(
            n_estimators=100, learning_rate=0.05, max_depth=3,
            random_state=self.random_state, verbosity=-1, n_jobs=1,
        )
        self._model.fit(features, labels)
        return self

    def predict_probability(self, features: Sequence[Sequence[float]]) -> tuple[float, ...]:
        if self._model is None:
            raise RuntimeError("LightGBMClassifier must be fitted before prediction")
        return tuple(float(row[1]) for row in self._model.predict_proba(features))
