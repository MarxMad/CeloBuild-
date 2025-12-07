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

        # Check if a manual target was provided in the payload
        manual_target = context.get("target_address")
        
        if manual_target:
             recipients = [manual_target]
             logger.info(f"Usando objetivo manual para demo: {manual_target}")
        
        # Si venimos de la prueba manual sin target específico (donde trend_watcher devuelve stats completos)
        elif "stats" in context:
            # Simulamos que los "active_users" son candidatos potenciales
            logger.info("Generando candidatos desde stats del frame...")
            active_users = context["stats"].get("active_users", 0)
            # Usamos direcciones dummy válidas para evitar errores de ENS/Checksum
            # Estas son direcciones generadas aleatoriamente para propósitos de demo
            dummy_addresses = [
                "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
                "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
                "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
                "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"
            ]
            recipients = dummy_addresses[:min(active_users, 5)]
        else:
             recipients = context.get("candidates", ["0x70997970C51812dc3A010C7d01b50e0d17dc79C8"])

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
