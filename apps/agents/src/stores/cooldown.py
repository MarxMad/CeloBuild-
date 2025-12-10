from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class CooldownStore:
    """Persistencia simple para controlar el cooldown de recompensas por usuario."""

    def __init__(self, storage_path: Path, cooldown_seconds: int = 86400) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.cooldown_seconds = cooldown_seconds
        self._lock = Lock()

    def _read(self) -> dict[str, int]:
        if not self.storage_path.exists():
            return {}
        try:
            return json.loads(self.storage_path.read_text("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Cooldown store corrupto, reiniciando.")
            return {}

    def _write(self, data: dict[str, int]) -> None:
        self.storage_path.write_text(json.dumps(data, indent=2), "utf-8")

    def check_cooldown(self, address: str) -> float:
        """
        Verifica si una dirección está en cooldown.
        Retorna el tiempo restante en segundos, o 0 si puede reclamar.
        """
        with self._lock:
            data = self._read()
            last_claim = data.get(address.lower(), 0)
            
            now = int(time.time())
            elapsed = now - last_claim
            
            if elapsed < self.cooldown_seconds:
                return self.cooldown_seconds - elapsed
            
            return 0.0

    def record_claim(self, address: str) -> None:
        """Registra un reclamo exitoso para una dirección."""
        with self._lock:
            data = self._read()
            data[address.lower()] = int(time.time())
            self._write(data)


def default_cooldown_store(cooldown_seconds: int = 86400) -> CooldownStore:
    import os
    # En Vercel serverless, usar /tmp que es writable
    if os.getenv("VERCEL"):
        base_path = Path("/tmp/lootbox")
    else:
        base_path = Path(__file__).resolve().parents[1] / "data"
    
    return CooldownStore(base_path / "cooldowns.json", cooldown_seconds=cooldown_seconds)
