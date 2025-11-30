from __future__ import annotations

from typing import Any

from ..config import Settings


class EligibilityAgent:
    """Valida participación on-chain y filtros sociales."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def handle(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evalúa reglas básicas mientras se integra la lógica real."""

        # TODO: consultar contratos LootAccessRegistry y pruebas ZK.
        recipients = context.get("candidates", [])
        filtered = recipients[:1] if context["trend_score"] < 0.9 else recipients
        return {
            "campaign_id": f"{context['frame_id']}-loot",
            "recipients": filtered,
            "metadata": {
                "channel_id": context["channel_id"],
                "trend_score": context["trend_score"],
            },
        }

