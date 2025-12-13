import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class NotificationStore:
    """Almacena tokens de notificación de Farcaster."""

    def __init__(self, file_path: str = "notifications.json") -> None:
        self.file_path = Path(file_path)
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Carga datos del archivo JSON."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r") as f:
                    self._data = json.load(f)
            except Exception as exc:
                logger.error("Error cargando notifications store: %s", exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Guarda datos al archivo JSON."""
        try:
            # En Vercel serverless, esto solo persiste en /tmp y se borra
            # Pero para desarrollo local funciona
            with open(self.file_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as exc:
            logger.error("Error guardando notifications store: %s", exc)

    def add_token(self, fid: int, token: str, url: str) -> None:
        """Registra un token para un FID."""
        fid_str = str(fid)
        self._data[fid_str] = {
            "token": token,
            "url": url,
            "updated_at": os.getenv("VERCEL_REGION", "local")  # Timestamp o flag
        }
        self._save()
        logger.info("Token registrado para FID %s", fid)

    def remove_token(self, fid: int) -> None:
        """Elimina token de un FID."""
        fid_str = str(fid)
        if fid_str in self._data:
            del self._data[fid_str]
            self._save()
            logger.info("Token eliminado para FID %s", fid)

    def get_token(self, fid: int) -> dict[str, str] | None:
        """Obtiene token y url para un FID."""
        return self._data.get(str(fid))
    
    def add_address_mapping(self, address: str, fid: int) -> None:
        """Guarda mapeo dirección -> FID."""
        if "address_map" not in self._data:
            self._data["address_map"] = {}
        self._data["address_map"][address.lower()] = fid
        self._save()
        logger.info("Mapeo guardado: %s -> FID %s", address, fid)
    
    def get_fid_by_address(self, address: str) -> int | None:
        """Obtiene FID por dirección."""
        address_map = self._data.get("address_map", {})
        return address_map.get(address.lower())

# Instancia global (singleton simple)
# En producción real, usar Redis/Postgres
_store = None

def get_notification_store() -> NotificationStore:
    global _store
    if _store is None:
        # Usar /tmp en Vercel si es necesario, pero idealmente persistente
        path = "/tmp/notifications.json" if os.getenv("VERCEL") else "notifications.json"
        _store = NotificationStore(path)
    return _store
