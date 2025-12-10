from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class LeaderboardStore:
    """Persistencia simple basada en archivo para el scoreboard."""

    def __init__(self, storage_path: Path, max_entries: int = 100) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self._lock = Lock()

    def _read(self) -> list[dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            return json.loads(self.storage_path.read_text("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Leaderboard store corrupto, reiniciando buffer.")
        return []

    def _write(self, entries: list[dict[str, Any]]) -> None:
        """Escribe el archivo de forma atómica para evitar lecturas corruptas."""
        import os
        import tempfile
        
        # Crear archivo temporal en el mismo directorio para asegurar que el rename sea atómico
        dir_path = self.storage_path.parent
        with tempfile.NamedTemporaryFile("w", dir=dir_path, delete=False, encoding="utf-8") as tmp:
            json.dump(entries, tmp, indent=2)
            tmp_path = Path(tmp.name)
            
        # Renombrar atómicamente (POSIX)
        try:
            tmp_path.replace(self.storage_path)
        except Exception as e:
            logger.error("Error en escritura atómica del leaderboard: %s", e)
            # Intentar borrar el temporal si falló
            try:
                os.unlink(tmp_path)
            except:
                pass

    def record(self, entry: dict[str, Any]) -> None:
        """Guarda un nuevo ganador y mantiene el límite configurado."""
        entry.setdefault("timestamp", int(time.time()))
        address = entry.get("address", "").lower()
        
        with self._lock:
            data = self._read()
            
            # Rebuild list using a dictionary to enforce uniqueness by address
            user_map = {}
            
            # 1. Process existing data
            for item in data:
                item_addr = item.get("address", "").lower()
                if not item_addr:
                    continue
                
                if item_addr in user_map:
                    # Merge with existing: keep max XP
                    existing = user_map[item_addr]
                    existing["xp"] = max(existing.get("xp", 0), item.get("xp", 0))
                    # Keep the most recent timestamp if available
                    existing["timestamp"] = max(existing.get("timestamp", 0), item.get("timestamp", 0))
                else:
                    user_map[item_addr] = item
            
            # 2. Process the new entry
            if address:
                if address in user_map:
                    current = user_map[address]
                    # Merge new entry data
                    new_xp = max(current.get("xp", 0), entry.get("xp", 0))
                    current.update(entry)
                    current["xp"] = new_xp
                else:
                    user_map[address] = entry
            
            # Convert back to list
            data = list(user_map.values())
            
            # Sort by XP (descending), then Score (descending)
            data.sort(key=lambda item: (item.get("xp", 0), item.get("score", 0)), reverse=True)
            self._write(data[: self.max_entries])
        with self._lock:
            data = self._read()
            
            # Normalizar dirección a minúsculas para consistencia
            address = entry.get("address", "").lower()
            if not address:
                return

            # Buscar si ya existe
            user_map = {item["address"].lower(): item for item in data if "address" in item}
            
            if address in user_map:
                current = user_map[address]
                # Merge new entry data
                # Mantener el XP más alto (on-chain truth vs local accumulation)
                new_xp = max(current.get("xp", 0), entry.get("xp", 0))
                
                current.update(entry)
                current["address"] = address # Asegurar que se guarde en lowercase
                current["xp"] = new_xp
            else:
                # Add new
                entry["address"] = address # Asegurar que se guarde en lowercase
                data.append(entry)
            
            # Sort by XP (desc) then Score (desc)
            data.sort(key=lambda x: (x.get("xp", 0), x.get("score", 0)), reverse=True)
            
            # Trim to max entries
            if len(data) > self.max_entries:
                data = data[:self.max_entries]
                
            self._write(data)

    def increment_score(self, entry: dict[str, Any], xp_increment: int) -> None:
        """Incrementa el XP de un usuario existente o crea uno nuevo."""
        entry.setdefault("timestamp", int(time.time()))
        address = entry.get("address", "").lower()
        if not address:
            return

        with self._lock:
            data = self._read()
            user_map = {}
            
            # 1. Load existing
            for item in data:
                item_addr = item.get("address", "").lower()
                if item_addr:
                    user_map[item_addr] = item
            
            # 2. Update or Create
            if address in user_map:
                current = user_map[address]
                # Accumulate XP
                current["xp"] = current.get("xp", 0) + xp_increment
                # Update other metadata
                current.update({k: v for k, v in entry.items() if k != "xp"})
            else:
                # New entry
                entry["xp"] = xp_increment
                user_map[address] = entry
            
            # 3. Save
            data = list(user_map.values())
            data.sort(key=lambda item: (item.get("xp", 0), item.get("score", 0)), reverse=True)
            self._write(data[: self.max_entries])

    def top(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retorna el top N del leaderboard."""
        with self._lock:
            return self._read()[:limit]

    def get_rank(self, address: str) -> int | None:
        """Retorna el ranking (1-based) de una dirección."""
        if not address:
            return None
            
        address = address.lower()
        with self._lock:
            data = self._read()
            for index, entry in enumerate(data):
                if entry.get("address", "").lower() == address:
                    return index + 1
        return None


def default_store(max_entries: int = 100) -> LeaderboardStore:
    import os
    # En Vercel serverless, usar /tmp que es writable
    if os.getenv("VERCEL"):
        base_path = Path("/tmp/lootbox")
    else:
        base_path = Path(__file__).resolve().parents[1] / "data"
    return LeaderboardStore(base_path / "leaderboard.json", max_entries=max_entries)
