from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetRecord:
    version: str
    target: str
    feature_version: str
    row_count: int
    start_date: str
    end_date: str


@dataclass(frozen=True)
class ModelRecord:
    name: str
    target: str
    algorithm: str
    algorithm_version: str
    feature_version: str
    dataset_version: str
    metrics: dict[str, Any]
    hyperparameters: dict[str, Any]
    artifact_path: str
    training_start: str
    training_end: str
    active: bool = False
