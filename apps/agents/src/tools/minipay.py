from __future__ import annotations

import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class MiniPayToolbox:
    """Cliente HTTP para interactuar con MiniPay Tool backend con reintentos."""

    def __init__(self, base_url: str, project_id: str, project_secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.project_id = project_id
        self.project_secret = project_secret

    async def send_micropayment(
        self, recipient: str, amount: float, note: str | None = None, retries: int = 3
    ) -> dict:
        """Envía micropagos usando el Tool. Reintenta en caso de fallos de red."""

        payload = {
            "projectId": self.project_id,
            "recipient": recipient,
            "amount": amount,
            "note": note,
            "signature": self.project_secret,  # TODO: Usar HMAC real si el backend lo requiere
        }

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(base_url=self.base_url, timeout=10) as client:
                    logger.info("Enviando micropago a %s (intento %s)", recipient, attempt + 1)
                    resp = await client.post("/micropay", json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.warning("Error en micropago (%s). Reintentando en 1s...", exc)
                if attempt == retries - 1:
                    logger.error("Se agotaron los reintentos para micropago.")
                    raise
                await asyncio.sleep(1)
        
        return {}

