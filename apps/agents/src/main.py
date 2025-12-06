from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import settings
from .graph.supervisor import SupervisorOrchestrator


class LootboxEvent(BaseModel):
    """Payload mínimo para detonar un flujo de loot box."""

    frame_id: str
    channel_id: str
    trend_score: float
    thread_id: str | None = None


app = FastAPI(title="Lootbox Multi-Agent Service")
supervisor = SupervisorOrchestrator.from_settings(settings)


@app.post("/api/lootbox/run")
async def run_lootbox(event: LootboxEvent):
    """Expone el grafo supervisor como endpoint HTTP."""

    try:
        result = await supervisor.run(event.model_dump())
    except Exception as exc:  # pragma: no cover - logging pendiente
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"thread_id": result.thread_id, "summary": result.summary}


def run_cli() -> None:
    """Permite ejecutar pruebas rápidas sin servidor HTTP."""

    import asyncio

    sample_event = LootboxEvent(frame_id="sample", channel_id="test", trend_score=0.91)
    asyncio.run(supervisor.run(sample_event.model_dump()))


