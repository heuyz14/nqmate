from __future__ import annotations

from datetime import date
from typing import Iterable

from nqmate_api.market.models import MarketContract


class ContinuousContractResolver:
    """Chooses the first unexpired contract without mixing raw contract prices."""

    def resolve(self, product: str, as_of: date, contracts: Iterable[MarketContract]) -> MarketContract:
        candidates = sorted(
            (contract for contract in contracts if contract.product == product and contract.expiration and contract.expiration >= as_of),
            key=lambda contract: contract.expiration,
        )
        if not candidates:
            raise LookupError(f"No {product} contract available for {as_of}")
        selected = candidates[0]
        return MarketContract(
            product=selected.product,
            raw_contract_symbol=selected.raw_contract_symbol,
            continuous_symbol=selected.continuous_symbol,
            expiration=selected.expiration,
            roll_date=selected.roll_date or as_of,
        )
