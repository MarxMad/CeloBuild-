from __future__ import annotations

import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class MiniPayToolbox:
    """Cliente HTTP para interactuar con MiniPay Tool backend con reintentos."""

    def __init__(self, base_url: str, project_id: str, secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.project_id = project_id
        self.secret = secret

    async def send_micropayment(self, recipient: str, amount: float, retries: int = 3) -> dict:
        """Envía micropagos usando el Tool. Reintenta en caso de fallos de red."""

        payload = {
            "projectId": self.project_id,
            "recipient": recipient,
            "amount": amount,
            "signature": self.secret, # TODO: Implement real HMAC signing if needed by backend
        }

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(base_url=self.base_url, timeout=10) as client:
                    logger.info(f"Enviando micropago a {recipient} (intento {attempt + 1})")
                    resp = await client.post("/micropay", json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Error en micropago ({e}). Reintentando en 1s...")
                if attempt == retries - 1:
                    logger.error("Se agotaron los reintentos para micropago.")
                    raise e
                await asyncio.sleep(1)
        
        return {} # Should not reach here
