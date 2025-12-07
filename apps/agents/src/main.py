from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .config import settings
from .graph.supervisor import SupervisorOrchestrator
from .scheduler import lifespan, supervisor as scheduler_supervisor


class LootboxEvent(BaseModel):
    """Payload mínimo para detonar un flujo de loot box."""

    frame_id: str
    channel_id: str
    trend_score: float
    thread_id: str | None = None
    target_address: str | None = None  # Campo opcional para demos manuales
    reward_type: str | None = None  # Si se proporciona, se usa; si no, los agentes deciden


app = FastAPI(title="Lootbox Multi-Agent Service", lifespan=lifespan)
supervisor = SupervisorOrchestrator.from_settings(settings)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/lootbox/leaderboard")
async def leaderboard(limit: int = Query(5, ge=1, le=25)) -> dict[str, list[dict[str, object]]]:
    """Devuelve el top de ganadores recientes."""
    # Usar supervisor del scheduler si está disponible, sino el global
    active_supervisor = scheduler_supervisor or supervisor
    items = active_supervisor.leaderboard.top(limit)
    return {"items": items}


@app.post("/api/lootbox/run")
async def run_lootbox(event: LootboxEvent):
    """Expone el grafo supervisor como endpoint HTTP.
    
    Si reward_type no se proporciona, los agentes determinan automáticamente
    según el score del usuario (NFT para top, cUSD para medio, XP para resto).
    """

    try:
        # Usar supervisor del scheduler si está disponible
        active_supervisor = scheduler_supervisor or supervisor
        result = await active_supervisor.run(event.model_dump())
    except Exception as exc:  # pragma: no cover - logging pendiente
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "thread_id": result.thread_id,
        "summary": result.summary,
        "tx_hash": result.tx_hash,
        "explorer_url": result.explorer_url,
        "mode": result.mode,
        "reward_type": result.reward_type,
    }


def run_cli() -> None:
    """Permite ejecutar pruebas rápidas sin servidor HTTP."""

    import asyncio

    sample_event = LootboxEvent(frame_id="sample", channel_id="test", trend_score=0.91)
    asyncio.run(supervisor.run(sample_event.model_dump()))

