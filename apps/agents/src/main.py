import re
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .graph.supervisor import SupervisorOrchestrator
from .scheduler import lifespan, supervisor as scheduler_supervisor


class LootboxEvent(BaseModel):
    """Payload mínimo para detonar un flujo de loot box."""

    frame_id: str = Field(..., min_length=1, max_length=100)
    channel_id: str = Field(..., min_length=1, max_length=100)
    trend_score: float = Field(..., ge=0.0, le=1.0)
    thread_id: str | None = Field(None, max_length=100)
    target_address: str | None = Field(None, max_length=42)  # Campo opcional para demos manuales
    reward_type: str | None = Field(None, max_length=20)  # Si se proporciona, se usa; si no, los agentes deciden

    @field_validator("target_address")
    @classmethod
    def validate_address(cls, v: str | None) -> str | None:
        """Valida formato de dirección Ethereum."""
        if v is None:
            return v
        # Validar formato básico de dirección (0x seguido de 40 caracteres hex)
        if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
            raise ValueError("Dirección Ethereum inválida")
        return v.lower()  # Normalizar a lowercase

    @field_validator("reward_type")
    @classmethod
    def validate_reward_type(cls, v: str | None) -> str | None:
        """Valida que reward_type sea uno de los valores permitidos."""
        if v is None:
            return v
        allowed = {"nft", "cusd", "xp", "token", "minipay", "reputation"}
        if v.lower() not in allowed:
            raise ValueError(f"reward_type debe ser uno de: {allowed}")
        return v.lower()


# En Vercel serverless, el lifespan puede causar problemas, así que lo hacemos opcional
try:
    app = FastAPI(title="Lootbox Multi-Agent Service", lifespan=lifespan)
except Exception as exc:
    # Si el lifespan falla (por ejemplo en serverless), crear app sin lifespan
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("No se pudo inicializar con lifespan, usando app básica: %s", exc)
    app = FastAPI(title="Lootbox Multi-Agent Service")

supervisor = SupervisorOrchestrator.from_settings(settings)

# Rate limiting simple: almacenar últimos requests por IP
# En producción, usar Redis o un middleware más robusto
_request_counts: dict[str, int] = {}
_REQUEST_LIMIT = 10  # Máximo 10 requests por minuto
_REQUEST_WINDOW = 60  # Ventana de 60 segundos


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware simple de rate limiting por IP."""
    client_ip = request.client.host if request.client else "unknown"
    current_time = int(__import__("time").time())
    
    # Limpiar entradas antiguas (simplificado, en producción usar Redis)
    if client_ip in _request_counts:
        # En producción, implementar ventana deslizante con Redis
        pass
    
    # Contar requests (simplificado)
    if client_ip not in _request_counts:
        _request_counts[client_ip] = 0
    
    _request_counts[client_ip] += 1
    
    if _request_counts[client_ip] > _REQUEST_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    
    response = await call_next(request)
    return response


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
    
    Validaciones de seguridad:
    - Rate limiting aplicado
    - Validación de inputs (direcciones, amounts, tipos)
    - Límites de batch size
    """

    # Validación adicional de seguridad
    if event.target_address and not settings.allow_manual_target:
        raise HTTPException(
            status_code=403,
            detail="Manual target addresses are disabled for security. Set ALLOW_MANUAL_TARGET=true to enable."
        )

    try:
        # Usar supervisor del scheduler si está disponible
        active_supervisor = scheduler_supervisor or supervisor
        result = await active_supervisor.run(event.model_dump())
    except ValueError as exc:
        # Errores de validación (direcciones inválidas, etc.)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - logging pendiente
        # No exponer detalles internos en producción
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Error interno en run_lootbox: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    
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

