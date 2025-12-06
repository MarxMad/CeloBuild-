from __future__ import annotations

import hashlib
import logging
from typing import Any

from ..config import Settings
from ..tools.farcaster import FarcasterToolbox

logger = logging.getLogger(__name__)

class TrendWatcherAgent:
    """Consulta señales de Farcaster y construye contexto de campaña."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.farcaster = FarcasterToolbox(
            base_url=settings.farcaster_hub_api,
            api_token=settings.farcaster_api_token
        )

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Detecta tendencias o analiza un frame específico si se provee."""
        
        # Si nos dan un frame_id específico, analizamos ese.
        frame_id = payload.get("frame_id")
        
        if frame_id:
            logger.info(f"Analizando frame específico: {frame_id}")
            stats = await self.farcaster.fetch_frame_stats(frame_id)
            return {
                "frame_id": frame_id,
                "channel_id": payload.get("channel_id", "unknown"),
                "trend_score": self._calculate_score(stats),
                "stats": stats,
                "status": "analyzed"
            }
        
        # Si no, buscamos trending
        logger.info("Buscando trending frames...")
        trending = await self.farcaster.get_trending_frames(limit=1)
        
        if not trending:
            return {"status": "no_trends_found"}
            
        top_trend = trending[0]
        return {
            "frame_id": top_trend["frame_id"],
            "channel_id": top_trend.get("channel_id", "general"),
            "trend_score": top_trend.get("trend_score", 0.0),
            "status": "trend_detected"
        }

    def _calculate_score(self, stats: dict) -> float:
        """Calcula un score simple basado en likes y recasts."""
        likes = stats.get("likes", 0)
        recasts = stats.get("recasts", 0)
        replies = stats.get("replies", 0)
        # Ponderación arbitraria
        return (likes * 1.0 + recasts * 2.0 + replies * 0.5) / 100.0

    def build_thread_id(self, payload: dict[str, Any]) -> str:
        """Genera un thread determinístico para LangGraph."""
        seed = f"{payload.get('frame_id', 'global')}:{payload.get('channel_id', 'general')}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return f"lootbox-{digest[:16]}"
