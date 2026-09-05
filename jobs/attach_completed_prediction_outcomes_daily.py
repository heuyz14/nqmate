"""Attach realized outcomes for completed session-linked predictions."""

from __future__ import annotations

import asyncio

from jobs.attach_completed_prediction_outcomes import run


async def attach_daily(limit: int = 100) -> int:
    """Run the bounded, idempotent Phase 9 attachment workflow."""
    return await run(limit)


def main() -> None:
    attached = asyncio.run(attach_daily())
    print(f"daily prediction outcome attachment completed: {attached} outcome(s)", flush=True)


if __name__ == "__main__":
    main()
