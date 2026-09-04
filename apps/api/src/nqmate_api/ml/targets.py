from __future__ import annotations

from typing import Sequence

from nqmate_api.market.models import MarketBar
from nqmate_api.ml.dataset import build_direction_targets


DIRECTION_HORIZONS_MINUTES = (5, 15, 30, 60, 120, 240)


def direction_target_names() -> tuple[str, ...]:
    return tuple(f"direction_{minutes}m" for minutes in DIRECTION_HORIZONS_MINUTES) + ("direction_close",)


def build_direction_target_matrix(bars: Sequence[MarketBar]) -> dict[str, dict[object, int]]:
    """Build separate exact-time direction targets for every supported horizon."""
    return {
        f"direction_{minutes}m": {
            timestamp: value for (timestamp, horizon), value in build_direction_targets(bars, (minutes,)).items()
            if horizon == minutes
        }
        for minutes in DIRECTION_HORIZONS_MINUTES
    }
