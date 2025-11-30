from __future__ import annotations

import httpx


class FarcasterToolbox:
    """Cliente mínimo para consultar Warpcast / Hubs."""

    def __init__(self, base_url: str, api_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    async def fetch_frame_stats(self, frame_id: str) -> dict:
        """Obtiene métricas de un frame (placeholder)."""

        headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
        # TODO: definir endpoint real /frames/{id}
        async with httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10) as client:
            resp = await client.get(f"/frames/{frame_id}")
            if resp.status_code >= 400:
                return {"engagement": 0}
            return resp.json()

