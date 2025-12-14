import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class SignerStore:
    """Almacena signers de Neynar por usuario (fid o address)."""

    def __init__(self, file_path: str = "signers.json") -> None:
        if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            self.file_path = Path("/tmp") / file_path
        else:
            self.file_path = Path("data") / file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Carga datos del archivo JSON."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r") as f:
                    self._data = json.load(f)
            except Exception as exc:
                logger.error("Error cargando signers store: %s", exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Guarda datos al archivo JSON."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as exc:
            logger.error("Error guardando signers store: %s", exc)

    def add_signer(self, user_id: str, signer_uuid: str, status: str, public_key: str | None = None, fid: int | None = None, approval_url: str | None = None) -> None:
        """Registra un signer para un usuario (puede ser fid o address)."""
        user_id_lower = user_id.lower()
        self._data[user_id_lower] = {
            "signer_uuid": signer_uuid,
            "status": status,  # generated | pending_approval | approved | revoked
            "public_key": public_key,
            "fid": fid,
            "approval_url": approval_url,
            "updated_at": os.getenv("VERCEL_REGION", "local")
        }
        self._save()
        logger.info("Signer registrado para %s: %s (status: %s)", user_id, signer_uuid[:8], status)

    def get_signer(self, user_id: str) -> dict[str, Any] | None:
        """Obtiene signer para un usuario."""
        return self._data.get(user_id.lower())

    def update_signer_status(self, user_id: str, status: str, fid: int | None = None) -> None:
        """Actualiza el estado de un signer."""
        user_id_lower = user_id.lower()
        if user_id_lower in self._data:
            self._data[user_id_lower]["status"] = status
            if fid is not None:
                self._data[user_id_lower]["fid"] = fid
            self._save()
            logger.info("Signer actualizado para %s: status=%s", user_id, status)

    def remove_signer(self, user_id: str) -> None:
        """Elimina signer de un usuario."""
        user_id_lower = user_id.lower()
        if user_id_lower in self._data:
            del self._data[user_id_lower]
            self._save()
            logger.info("Signer eliminado para %s", user_id)

    def get_approved_signer_uuid(self, user_id: str) -> str | None:
        """Obtiene el signer_uuid aprobado de un usuario, o None si no está aprobado."""
        signer = self.get_signer(user_id)
        if signer and signer.get("status") == "approved":
            return signer.get("signer_uuid")
        return None


# Instancia global (singleton simple)
_store = None

def get_signer_store() -> SignerStore:
    global _store
    if _store is None:
        _store = SignerStore()
    return _store

