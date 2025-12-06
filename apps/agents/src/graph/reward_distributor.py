from __future__ import annotations

from typing import Any

from ..config import Settings


class RewardDistributorAgent:
    """Coordina pagos MiniPay y minteo de cNFTs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def handle(self, eligibility: dict[str, Any]) -> dict[str, Any]:
        """Simula la distribución; más adelante llamará herramientas reales."""

        recipients = eligibility.get("recipients", [])
        if not recipients:
            return {"mode": "noop", "tx_hash": None}

        # TODO: invocar herramientas MiniPay + contratos Foundry.
        return {
            "mode": "micropayment+cnft",
            "tx_hash": None,
            "recipients": recipients,
            "campaign_id": eligibility["campaign_id"],
        }


