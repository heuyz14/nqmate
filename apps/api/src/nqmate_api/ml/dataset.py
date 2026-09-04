from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

from nqmate_api.market.models import MarketBar
from nqmate_api.ml.baselines import LabeledRow


@dataclass(frozen=True)
class VersionedDataset:
    version: str
    target_name: str
    rows: tuple[LabeledRow, ...]


def build_direction_targets(
    bars: Sequence[MarketBar], horizons_minutes: Sequence[int]
) -> dict[tuple[datetime, int], int]:
    """Create exact-timestamp forward direction labels; missing bars are skipped."""
    ordered = sorted(bars, key=lambda item: item.timestamp)
    by_timestamp = {bar.timestamp: bar for bar in ordered}
    targets: dict[tuple[datetime, int], int] = {}
    for current in ordered:
        for horizon in horizons_minutes:
            future = by_timestamp.get(current.timestamp + timedelta(minutes=horizon))
            if future is None or future.timestamp <= current.timestamp:
                continue
            targets[(current.timestamp, horizon)] = int(future.close > current.close)
    return targets


def build_feature_matrix(
    snapshots: Sequence[Mapping[str, Any]],
    targets: Mapping[tuple[datetime, int], int],
    horizon_minutes: int,
    feature_version: str,
) -> VersionedDataset:
    rows: list[LabeledRow] = []
    for snapshot in sorted(snapshots, key=lambda item: item["feature_timestamp"]):
        feature_timestamp = snapshot["feature_timestamp"]
        available_at = snapshot["available_at"]
        target = targets.get((feature_timestamp, horizon_minutes))
        if target is None or available_at > feature_timestamp:
            continue
        features = snapshot["features"]
        values = tuple(float(features[name]) for name in sorted(features))
        if not values:
            continue
        rows.append(LabeledRow(feature_timestamp, available_at, values, int(target)))
    return VersionedDataset(feature_version, f"direction_{horizon_minutes}m", tuple(rows))
