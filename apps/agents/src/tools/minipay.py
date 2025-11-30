from __future__ import annotations

import httpx


class MiniPayToolbox:
    """Cliente HTTP para interactuar con MiniPay Tool backend."""

    def __init__(self, base_url: str, project_id: str, secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.project_id = project_id
        self.secret = secret

    async def send_micropayment(self, recipient: str, amount: float) -> dict:
        """Envía micropagos usando el Tool (se implementará con auth real)."""

        payload = {
            "projectId": self.project_id,
            "recipient": recipient,
            "amount": amount,
            "signature": self.secret,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10) as client:
            resp = await client.post("/micropay", json=payload)
            resp.raise_for_status()
            return resp.json()

