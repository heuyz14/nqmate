from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from datetime import date, datetime


@dataclass(frozen=True)
class DatasetRecord:
    version: str
    target: str
    feature_version: str
    row_count: int
    start_date: str
    end_date: str


@dataclass(frozen=True)
class SessionFeatureSnapshot:
    session_date: date
    snapshot_timestamp: datetime
    symbol: str
    contract: str
    feature_version: str
    features: dict[str, float]
    available_at: datetime


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
