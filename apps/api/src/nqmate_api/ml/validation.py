from __future__ import annotations

from typing import Sequence

from nqmate_api.ml.baselines import LabeledRow


def point_in_time_rows(rows: Sequence[LabeledRow], prediction_time: object) -> tuple[LabeledRow, ...]:
    return tuple(row for row in sorted(rows, key=lambda item: item.feature_timestamp) if row.available_at <= prediction_time)


def walk_forward_splits(rows: Sequence[LabeledRow], min_train_size: int, test_size: int = 1, step: int = 1) -> tuple[tuple[tuple[LabeledRow, ...], tuple[LabeledRow, ...]], ...]:
    if min_train_size < 1 or test_size < 1 or step < 1:
        raise ValueError("split sizes and step must be positive")
    ordered = tuple(sorted(rows, key=lambda item: item.feature_timestamp))
    result = []
    start = min_train_size
    while start + test_size <= len(ordered):
        result.append((ordered[:start], ordered[start:start + test_size]))
        start += step
    return tuple(result)
