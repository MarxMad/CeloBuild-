from __future__ import annotations

import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

class FarcasterToolbox:
    """Cliente para consultar Warpcast / Hubs con soporte de Mock."""

    def __init__(self, base_url: str, api_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    async def fetch_frame_stats(self, frame_id: str) -> dict[str, Any]:
        """Obtiene métricas de un frame. Si falla la API, retorna mock."""
        headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10) as client:
                resp = await client.get(f"/frames/{frame_id}")
                resp.raise_for_status()
                return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Fallo al consultar Farcaster API ({e}), usando mock.")
            # Mock data para desarrollo
            return {
                "id": frame_id,
                "likes": 150,
                "recasts": 45,
                "replies": 12,
                "view_count": 1200,
                "active_users": 300
            }

    async def get_trending_frames(self, limit: int = 5) -> list[dict[str, Any]]:
        """Busca frames populares recientemente."""
        headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10) as client:
                # Endpoint hipotetico de Warpcast
                resp = await client.get("/farcaster-frames/trending", params={"limit": limit})
                resp.raise_for_status()
                return resp.json().get("frames", [])
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Fallo al consultar Trending Frames ({e}), usando mock.")
            return [
                {
                    "frame_id": "frame-mock-001",
                    "url": "https://cool-frame.xyz",
                    "title": "Super LootBox Drop",
                    "channel_id": "minipay-devs",
                    "trend_score": 0.95
                },
                {
                    "frame_id": "frame-mock-002",
                    "url": "https://survey.xyz",
                    "title": "Community Survey",
                    "channel_id": "general",
                    "trend_score": 0.82
                }
            ]
