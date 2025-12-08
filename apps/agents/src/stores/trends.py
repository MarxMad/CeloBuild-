from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class TrendsStore:
    """Almacena las tendencias detectadas recientemente por TrendWatcherAgent."""

    def __init__(self, storage_path: Path, max_entries: int = 50) -> None:
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
            logger.warning("Trends store corrupto, reiniciando buffer.")
        return []

    def _write(self, entries: list[dict[str, Any]]) -> None:
        self.storage_path.write_text(json.dumps(entries, indent=2), "utf-8")

    def record(self, trend_data: dict[str, Any]) -> None:
        """Guarda una nueva tendencia detectada."""
        trend_data.setdefault("timestamp", int(time.time()))
        with self._lock:
            data = self._read()
            # Evitar duplicados basados en cast_hash
            cast_hash = trend_data.get("cast_hash")
            if cast_hash:
                data = [e for e in data if e.get("cast_hash") != cast_hash]
            data.insert(0, trend_data)  # Agregar al inicio
            self._write(data[: self.max_entries])

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retorna las tendencias más recientes."""
        with self._lock:
            data = self._read()
        return data[:limit]

    def active_trends(self, max_age_hours: int = 24) -> list[dict[str, Any]]:
        """Retorna tendencias activas (dentro de las últimas N horas)."""
        current_time = int(time.time())
        max_age_seconds = max_age_hours * 3600
        
        with self._lock:
            data = self._read()
        
        active = [
            trend for trend in data
            if (current_time - trend.get("timestamp", 0)) <= max_age_seconds
        ]
        return active


def default_trends_store(max_entries: int = 50) -> TrendsStore:
    base_path = Path(__file__).resolve().parents[1] / "data"
    return TrendsStore(base_path / "trends.json", max_entries=max_entries)

