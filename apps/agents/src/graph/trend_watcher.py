from __future__ import annotations

import hashlib
from typing import Any

from ..config import Settings


class TrendWatcherAgent:
    """Consulta señales de Farcaster y construye contexto de campaña."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Placeholder que simula la detección de una conversación trending."""

        # TODO: integrar Warpcast API + Tavily para validar trending real.
        return {
            "frame_id": payload["frame_id"],
            "channel_id": payload["channel_id"],
            "trend_score": payload["trend_score"],
            "candidates": ["0x123", "0x456"],  # se reemplazará por handles reales
        }

    def build_thread_id(self, payload: dict[str, Any]) -> str:
        """Genera un thread determinístico para LangGraph."""

        seed = f"{payload['frame_id']}:{payload['channel_id']}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return f"lootbox-{digest[:16]}"

