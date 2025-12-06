from __future__ import annotations

import logging
from typing import Any

from ..config import Settings

logger = logging.getLogger(__name__)

class EligibilityAgent:
    """Valida participación on-chain y filtros sociales."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def handle(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evalúa reglas básicas mientras se integra la lógica real."""

        # TODO: consultar contratos LootAccessRegistry y pruebas ZK.
        
        # Si venimos de la prueba manual (donde trend_watcher devuelve stats completos)
        if "stats" in context:
            # Simulamos que los "active_users" son candidatos potenciales
            # En realidad aquí consultaríamos la API de Farcaster para obtener FIDs/addresses
            logger.info("Generando candidatos desde stats del frame...")
            active_users = context["stats"].get("active_users", 0)
            recipients = [f"0xUser{i}" for i in range(min(active_users, 5))] # Limitamos a 5 para demo
        else:
             recipients = context.get("candidates", ["0xDemo1", "0xDemo2"])

        # Lógica simple de filtrado basada en trend_score
        trend_score = context.get("trend_score", 0)
        filtered = recipients[:1] if trend_score < 0.5 else recipients
        
        logger.info(f"Elegibilidad: {len(recipients)} candidatos -> {len(filtered)} seleccionados (Score: {trend_score})")

        return {
            "campaign_id": f"{context['frame_id']}-loot",
            "recipients": filtered,
            "metadata": {
                "channel_id": context.get("channel_id"),
                "trend_score": trend_score,
            },
        }
