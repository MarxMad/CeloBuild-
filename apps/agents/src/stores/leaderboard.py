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
        with self._lock:
            data = self._read()
            data.append(entry)
            data.sort(key=lambda item: item.get("score", 0), reverse=True)
            self._write(data[: self.max_entries])

    def top(self, limit: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            data = self._read()
        return data[:limit]


def default_store(max_entries: int = 100) -> LeaderboardStore:
    base_path = Path(__file__).resolve().parents[1] / "data"
    return LeaderboardStore(base_path / "leaderboard.json", max_entries=max_entries)


