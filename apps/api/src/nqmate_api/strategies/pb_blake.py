from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True)
class HtfContext:
    timeframe: str
    direction: str
    key_level_valid: bool


@dataclass(frozen=True)
class LiquidityEvent:
    swept_level: str
    price: float
    swept_at: datetime


@dataclass(frozen=True)
class Inversion:
    timeframe: str
    direction: str
    lower: float
    upper: float
    confirmed_at: datetime


@dataclass(frozen=True)
class PbSetupAssessment:
    status: str
    direction: str | None
    inversion_timeframe: str | None
    entry: float | None
    stop: float | None
    stop_distance: float | None
    targets: tuple[float, ...]
    risk_rewards: tuple[float, ...]
    missing: tuple[str, ...]


_TIMEFRAME_ORDER = {"1m": 1, "2m": 2, "3m": 3, "5m": 5}


def assess_pb_setup(
    contexts: Sequence[HtfContext],
    liquidity: LiquidityEvent | None,
    inversions: Sequence[Inversion],
    entry: float | None,
    stop: float | None,
    targets: Sequence[float],
    analyzed_at: datetime,
) -> PbSetupAssessment:
    missing: list[str] = []
    valid_contexts = [context for context in contexts if context.key_level_valid and context.direction in {"bullish", "bearish"}]
    if not valid_contexts:
        missing.append("valid higher-timeframe context/key level")
    if liquidity is None:
        missing.append("identifiable liquidity event")
    eligible = [
        item
        for item in inversions
        if item.timeframe in _TIMEFRAME_ORDER
        and liquidity is not None
        and liquidity.swept_at < item.confirmed_at <= analyzed_at
        and item.direction in {"LONG", "SHORT"}
    ]
    if liquidity is not None and inversions and not eligible:
        missing.append("inversion must occur after liquidity event")
    if not eligible:
        missing.append("post-liquidity lower-timeframe inversion")
    if entry is None:
        missing.append("entry level")
    if stop is None:
        missing.append("logical stop")
    if not targets:
        missing.append("at least one target")
    if missing:
        sequence_invalid = liquidity is not None and bool(inversions) and not eligible
        status = "NO_SETUP" if sequence_invalid else ("DEVELOPING" if valid_contexts and (eligible or liquidity is not None) else "NO_SETUP")
        return PbSetupAssessment(status, None, None, entry, stop, None, tuple(targets), (), tuple(dict.fromkeys(missing)))
    selected = max(eligible, key=lambda item: _TIMEFRAME_ORDER[item.timeframe])
    direction = selected.direction
    if (direction == "LONG" and stop >= entry) or (direction == "SHORT" and stop <= entry):
        return PbSetupAssessment("NO_SETUP", direction, None, entry, stop, None, tuple(targets), (), ("stop must be beyond the local manipulation extreme",))
    risk = abs(entry - stop)
    risk_rewards = tuple(round(abs(target - entry) / risk, 4) for target in targets)
    if any(value < 1 for value in risk_rewards):
        return PbSetupAssessment("NO_SETUP", direction, None, entry, stop, risk, tuple(targets), risk_rewards, ("target reward is below 1R",))
    return PbSetupAssessment("VALID", direction, selected.timeframe, entry, stop, risk, tuple(targets), risk_rewards, ())
