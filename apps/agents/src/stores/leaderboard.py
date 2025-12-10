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
        self.storage_path.write_text(json.dumps(entries, indent=2), "utf-8")

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

    def top(self, limit: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            data = self._read()
        return data[:limit]

    def get_rank(self, address: str) -> int | None:
        """Retorna el rango (1-based) de una dirección, o None si no está en el leaderboard."""
        address = address.lower()
        with self._lock:
            data = self._read()
            # Asegurar que está ordenado (aunque _read lee lo que _write escribió ordenado, 
            # es mejor prevenir si se editó manualmente)
            # data.sort(key=lambda item: (item.get("xp", 0), item.get("score", 0)), reverse=True)
            
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
