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

    def __init__(self, base_url: str, api_token: str | None = None, neynar_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.neynar_key = neynar_key

    async def fetch_recent_casts(self, channel_id: str = "global", limit: int = 10) -> list[dict[str, Any]]:
        """Busca casts recientes usando Neynar API (Producción)."""
        
        # 1. Intentar con Neynar API si tenemos Key
        if self.neynar_key and self.neynar_key != "NEYNAR_API_DOCS":
            try:
                headers = {"accept": "application/json", "api_key": self.neynar_key}
                # Endpoint para Trending Global (Feed)
                url = "https://api.neynar.com/v2/farcaster/feed/trending"
                params = {"limit": limit}
                
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # Normalizar datos de Neynar
                    return [
                        {
                            "hash": cast["hash"],
                            "text": cast["text"],
                            "author": {
                                "username": cast["author"]["username"],
                                "pfp_url": cast["author"]["pfp_url"]
                            },
                            "reactions": {
                                "likes": cast["reactions"]["likes_count"],
                                "recasts": cast["reactions"]["recasts_count"]
                            },
                            "timestamp": cast["timestamp"]
                        }
                        for cast in data.get("casts", [])
                    ]
            except Exception as e:
                logger.error(f"Error Neynar API: {e}")
                # Fallback abajo...

        # 2. Fallback: Simulación realista si no hay API Key configurada
        # (Para evitar que la demo rompa si el usuario no tiene key aún)
        logger.warning("Usando fallback de datos (Sin Neynar Key válida).")
        return [
             {
                "hash": "0xRealMock1",
                "text": "¡MiniPay está cambiando el juego en Celo! 🟡🚀 #ReFi",
                "author": {"username": "celo_whale", "pfp_url": "https://i.imgur.com/example.jpg"},
                "reactions": {"likes": 150, "recasts": 42},
                "timestamp": "2024-03-20T10:00:00Z"
            },
            {
                "hash": "0xRealMock2",
                "text": "Construyendo la próxima gran app social en Farcaster frames. 🎩✨",
                "author": {"username": "builder_bob", "pfp_url": "https://i.imgur.com/example2.jpg"},
                "reactions": {"likes": 89, "recasts": 12},
                "timestamp": "2024-03-20T10:05:00Z"
            }
        ]
