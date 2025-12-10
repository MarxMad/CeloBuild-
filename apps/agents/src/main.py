import logging
import re
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .graph.supervisor import SupervisorOrchestrator
from .scheduler import lifespan, supervisor as scheduler_supervisor
from .services.leaderboard_sync import LeaderboardSyncer

logger = logging.getLogger(__name__)


class LootboxEvent(BaseModel):
    """Payload mínimo para detonar un flujo de loot box."""

    frame_id: str | None = Field(default=None, max_length=100)  # Opcional: None para análisis automático de tendencias
    channel_id: str = Field(..., min_length=1, max_length=100)
    trend_score: float = Field(..., ge=0.0, le=1.0)
    thread_id: str | None = Field(None, max_length=100)
    target_address: str | None = Field(None, max_length=42)  # Campo opcional para demos manuales
    target_fid: int | None = Field(None, ge=1)  # FID del usuario de Farcaster (si está disponible desde el contexto)
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
        allowed = {"nft", "cusd", "xp", "token", "minipay", "reputation", "analysis"}
        if v.lower() not in allowed:
            raise ValueError(f"reward_type debe ser uno de: {allowed}")
        return v.lower()


# En Vercel serverless, el lifespan puede causar problemas, así que lo hacemos opcional
import os

# Detectar si estamos en Vercel serverless
is_vercel = os.getenv("VERCEL") is not None

if is_vercel:
    # En Vercel, no usar lifespan (causa problemas en serverless)
    app = FastAPI(title="Lootbox Multi-Agent Service")
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Vercel serverless detectado - usando app sin lifespan")
else:
    # En otros entornos (Railway, Render, local), usar lifespan con scheduler
    try:
        app = FastAPI(title="Lootbox Multi-Agent Service", lifespan=lifespan)
    except Exception as exc:
        # Si el lifespan falla, crear app sin lifespan
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("No se pudo inicializar con lifespan, usando app básica: %s", exc)
        app = FastAPI(title="Lootbox Multi-Agent Service")

# Inicializar supervisor con manejo de errores
_supervisor_error = None
try:
    supervisor = SupervisorOrchestrator.from_settings(settings)
except Exception as exc:
    import logging
    logger = logging.getLogger(__name__)
    logger.error("Error inicializando supervisor: %s", exc, exc_info=True)
    supervisor = None
    _supervisor_error = {
        "error": str(exc),
        "type": type(exc).__name__,
    }

# Inicializar Syncer (lazy init en startup)
leaderboard_syncer = None

# Rate limiting simple: almacenar últimos requests por IP
# En producción, usar Redis o un middleware más robusto
_request_timestamps: dict[str, list[int]] = {}
_REQUEST_LIMIT_GET = 60  # Máximo 60 requests GET por minuto (para polling del frontend)
_REQUEST_LIMIT_POST = 10  # Máximo 10 requests POST por minuto
_REQUEST_WINDOW = 60  # Ventana de 60 segundos


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware simple de rate limiting por IP con ventana deslizante."""
    # Excluir health check, docs y endpoints GET de lectura del rate limiting
    # Los endpoints GET de lectura (leaderboard, trends) son consultas frecuentes del frontend
    excluded_paths = [
        "/healthz", 
        "/docs", 
        "/openapi.json", 
        "/redoc",
        "/api/lootbox/leaderboard",  # GET - lectura frecuente del frontend
        "/api/lootbox/trends",       # GET - lectura frecuente del frontend
    ]
    
    # Excluir todos los GET de lectura (solo aplicar rate limiting a POST)
    if request.url.path in excluded_paths or request.method == "GET":
        return await call_next(request)
    
    # Solo aplicar rate limiting a POST (operaciones que consumen recursos)
    # Declarar que usamos la variable global
    global _request_timestamps
    
    client_ip = request.client.host if request.client else "unknown"
    current_time = int(__import__("time").time())
    
    # Inicializar lista de timestamps para esta IP si no existe
    if client_ip not in _request_timestamps:
        _request_timestamps[client_ip] = []
    
    # Limpiar timestamps fuera de la ventana de tiempo
    _request_timestamps[client_ip] = [
        ts for ts in _request_timestamps[client_ip]
        if (current_time - ts) < _REQUEST_WINDOW
    ]
    
    # Aplicar límite solo a POST (operaciones que consumen recursos)
    limit = _REQUEST_LIMIT_POST
    
    # Verificar si excede el límite
    if len(_request_timestamps[client_ip]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit: {limit} requests per {_REQUEST_WINDOW} seconds."
        )
    
    # Registrar este request
    _request_timestamps[client_ip].append(current_time)
    
    # Limpiar IPs antiguas (más de 5 minutos sin actividad)
    # Modificar in-place en lugar de reasignar para evitar problemas de scope
    if len(_request_timestamps) > 1000:  # Limpiar si hay muchas IPs
        cutoff_time = current_time - 300  # 5 minutos
        ips_to_remove = [
            ip for ip, timestamps in _request_timestamps.items()
            if not timestamps or (timestamps and max(timestamps) <= cutoff_time)
        ]
        for ip in ips_to_remove:
            _request_timestamps.pop(ip, None)
    
    response = await call_next(request)
    return response


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """Middleware global para capturar excepciones no manejadas y mostrar traceback."""
    try:
        return await call_next(request)
    except Exception as exc:
        import traceback
        error_detail = f"Unhandled Server Error: {str(exc)}\nTraceback: {traceback.format_exc()}"
        logger.error(error_detail)
        return JSONResponse(
            status_code=500,
            content={"detail": error_detail, "error": "Internal Server Error"}
        )


@app.on_event("startup")
async def startup_event():
    """Inicializa servicios adicionales al arrancar."""
    global leaderboard_syncer
    
    # Inicializar syncer si tenemos supervisor
    active_supervisor = scheduler_supervisor or supervisor
    if active_supervisor:
        try:
            leaderboard_syncer = LeaderboardSyncer(active_supervisor.leaderboard)
            # Ejecutar sync inicial en background
            import asyncio
            if settings.auto_scan_on_startup:
                asyncio.create_task(leaderboard_syncer.sync())
        except Exception as e:
            logger.error("Error inicializando LeaderboardSyncer: %s", e)


@app.get("/")
async def root():
    """Endpoint raíz para verificar que el servicio está funcionando."""
    return {
        "service": "Lootbox Multi-Agent Service",
        "status": "running",
        "endpoints": {
            "health": "/healthz",
            "leaderboard": "/api/lootbox/leaderboard",
            "trends": "/api/lootbox/trends",
            "run": "/api/lootbox/run",
            "scan": "/api/lootbox/scan",
            "docs": "/docs",
            "debug": "/debug",
        }
    }


@app.get("/debug")
async def debug() -> dict[str, object]:
    """Debug endpoint que muestra el estado de inicialización del servicio."""
    import os
    
    return {
        "supervisor_initialized": supervisor is not None,
        "supervisor_error": _supervisor_error,
        "is_vercel": is_vercel,
        "env_vars": {
            "GOOGLE_API_KEY": "SET" if os.getenv("GOOGLE_API_KEY") else "MISSING",
            "TAVILY_API_KEY": "SET" if os.getenv("TAVILY_API_KEY") else "MISSING",
            "CELO_RPC_URL": "SET" if os.getenv("CELO_RPC_URL") else "MISSING",
            "CELO_PRIVATE_KEY": "SET" if os.getenv("CELO_PRIVATE_KEY") else "MISSING",
            "LOOTBOX_VAULT_ADDRESS": "SET" if os.getenv("LOOTBOX_VAULT_ADDRESS") else "MISSING",
            "REGISTRY_ADDRESS": "SET" if os.getenv("REGISTRY_ADDRESS") else "MISSING",
            "MINTER_ADDRESS": "SET" if os.getenv("MINTER_ADDRESS") else "MISSING",
            "NEYNAR_API_KEY": "SET" if os.getenv("NEYNAR_API_KEY") else "MISSING",
            "ALLOW_MANUAL_TARGET": "SET" if os.getenv("ALLOW_MANUAL_TARGET") else "MISSING",
        }
    }



@app.get("/healthz")
async def healthcheck() -> dict[str, object]:
    """Health check endpoint que verifica el estado del servicio."""
    import os
    
    try:
        # Verificar variables de entorno críticas
        missing_vars = []
        critical_vars = [
            "GOOGLE_API_KEY",
            "TAVILY_API_KEY", 
            "CELO_RPC_URL",
            "CELO_PRIVATE_KEY",
            "LOOTBOX_VAULT_ADDRESS",
            "REGISTRY_ADDRESS",
            "MINTER_ADDRESS",
            "NEYNAR_API_KEY",
        ]
        
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        # Verificar supervisor de forma segura
        supervisor_status = False
        try:
            supervisor_status = supervisor is not None
        except Exception:
            supervisor_status = False
        
        status = "ok" if not missing_vars and supervisor_status else "degraded"
        
        response = {
            "status": status,
            "supervisor_initialized": supervisor_status,
        }
        
        if missing_vars:
            response["missing_env_vars"] = missing_vars
            response["message"] = f"Faltan {len(missing_vars)} variables de entorno críticas"
        
        return response
    except Exception as exc:
        # Si hay cualquier error, retornar estado degradado pero funcional
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Error en healthcheck: %s", exc, exc_info=True)
        return {
            "status": "error",
            "supervisor_initialized": False,
            "error": str(exc),
            "message": "Health check falló pero el servicio puede estar funcionando"
        }



@app.get("/api/lootbox/xp/{wallet_address}")
async def get_xp(wallet_address: str, campaign_id: str = Query(default="demo-campaign")):
    """
    Lee el balance de XP de una wallet desde blockchain.
    
    Args:
        wallet_address: Dirección de la wallet del usuario
        campaign_id: ID de la campaña (default: "demo-campaign")
    
    Returns:
        {"xp": 100, "wallet": "0x...", "campaign_id": "demo-campaign"}
    """
    try:
        from .tools.celo import CeloToolbox
        
        # Inicializar CeloToolbox
        celo_tool = CeloToolbox(
            rpc_url=settings.celo_rpc_url,
            private_key=None,  # Solo lectura, no necesita private key
        )
        
        # Leer XP on-chain
        xp_balance = celo_tool.get_xp_balance(
            registry_address=settings.registry_address,
            campaign_id=campaign_id,
            participant=wallet_address,
        )
        
        # Obtener rango del leaderboard
        rank = None
        try:
            active_supervisor = scheduler_supervisor or supervisor
            if active_supervisor:
                rank = active_supervisor.leaderboard.get_rank(wallet_address)
        except Exception as e:
            logger.warning("Error obteniendo rango para %s: %s", wallet_address, e)

        return {
            "xp": xp_balance,
            "wallet": wallet_address,
            "campaign_id": campaign_id,
            "rank": rank,
        }
    except Exception as exc:
        logger.error("Error leyendo XP para %s: %s", wallet_address, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error leyendo XP: {str(exc)}"
        )


@app.get("/api/lootbox/leaderboard")
async def leaderboard(limit: int = Query(50, ge=1, le=100)) -> dict[str, list[dict[str, object]]]:
    """Devuelve el top de ganadores recientes."""
    try:
        # Usar supervisor del scheduler si está disponible, sino el global
        active_supervisor = scheduler_supervisor or supervisor
        if not active_supervisor:
            logger.warning("Supervisor no inicializado, retornando leaderboard vacío")
            return {"items": []}
        items = active_supervisor.leaderboard.top(limit)
        return {"items": items}
    except Exception as exc:
        logger.error("Error obteniendo leaderboard: %s", exc, exc_info=True)
        return {"items": []}
        return {"items": []}


@app.post("/api/lootbox/leaderboard/sync")
async def sync_leaderboard():
    """Fuerza una sincronización del leaderboard con la blockchain."""
    try:
        active_supervisor = scheduler_supervisor or supervisor
        if not active_supervisor:
            raise HTTPException(status_code=500, detail="Supervisor no inicializado")
            
        # Crear syncer on-the-fly si no existe (ej. en Vercel serverless)
        syncer = LeaderboardSyncer(active_supervisor.leaderboard)
        
        # Ejecutar sync (esto puede tardar, idealmente debería ser background task)
        count = await syncer.sync()
        
        return {"status": "success", "updated_entries": count}
    except Exception as exc:
        logger.error("Error en sync manual: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/lootbox/trends")
async def get_trends(limit: int = Query(10, ge=1, le=50)) -> dict[str, list[dict[str, object]]]:
    """Devuelve las tendencias detectadas recientemente por TrendWatcherAgent."""
    try:
        # Usar supervisor del scheduler si está disponible, sino el global
        active_supervisor = scheduler_supervisor or supervisor
        if not active_supervisor:
            logger.warning("Supervisor no inicializado, retornando trends vacío")
            return {"items": []}
        trends = active_supervisor.trends_store.recent(limit)
        return {"items": trends}
    except Exception as exc:
        logger.error("Error obteniendo trends: %s", exc, exc_info=True)
        return {"items": []}


@app.post("/api/lootbox/scan")
async def trigger_scan():
    """Endpoint para ejecutar un scan manual de tendencias (útil para Vercel Cron Jobs)."""
    try:
        active_supervisor = scheduler_supervisor or supervisor
        if not active_supervisor:
            raise HTTPException(status_code=500, detail="Supervisor no inicializado")
        
        # Ejecutar scan automático
        payload = {
            "frame_id": "",
            "channel_id": "global",
            "trend_score": 0.0,
        }
        
        result = await active_supervisor.run(payload)
        return {
            "status": "success",
            "summary": result.summary,
            "tx_hash": result.tx_hash,
            "explorer_url": result.explorer_url,
            "mode": result.mode,
            "reward_type": result.reward_type,
        }
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Error en scan manual: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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

    # Validación de seguridad: target_address está permitido cuando:
    # 1. ALLOW_MANUAL_TARGET=true (configuración explícita)
    # 2. O cuando viene del frontend (usuario conectado desde Farcaster) - esto es el caso normal
    # En producción, target_address viene del usuario conectado desde Farcaster, así que es seguro
    # El bloqueo solo aplica si explícitamente se deshabilita para prevenir abusos de admin
    # NOTA: En el flujo normal (usuario conectado desde Farcaster), target_address siempre viene del frontend
    # y debería estar permitido. ALLOW_MANUAL_TARGET=false solo bloquea casos de testing/admin.
    if event.target_address and not settings.allow_manual_target:
        logger.warning(
            "target_address recibido pero ALLOW_MANUAL_TARGET=false. "
            "Si esto es un usuario conectado desde Farcaster, configura ALLOW_MANUAL_TARGET=true en .env"
        )
        raise HTTPException(
            status_code=403,
            detail="Manual target addresses are disabled for security. Set ALLOW_MANUAL_TARGET=true to enable. "
                   "Note: This is required when users connect their wallet from Farcaster."
        )

    try:
        # Usar supervisor del scheduler si está disponible
        active_supervisor = scheduler_supervisor or supervisor
        
        if not active_supervisor:
            # Verificar qué variables faltan para dar un mensaje útil
            import os
            missing_vars = []
            critical_vars = [
                "GOOGLE_API_KEY", "TAVILY_API_KEY", "CELO_RPC_URL", 
                "CELO_PRIVATE_KEY", "LOOTBOX_VAULT_ADDRESS"
            ]
            for var in critical_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            error_msg = "Service not initialized."
            if missing_vars:
                error_msg += f" Missing environment variables: {', '.join(missing_vars)}"
            
            logger.error(error_msg)
            raise HTTPException(
                status_code=503,
                detail=error_msg
            )
            
        result = await active_supervisor.run(event.model_dump())
    except ValueError as exc:
        # Errores de validación (direcciones inválidas, etc.)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - logging pendiente
        # No exponer detalles internos en producción
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error("Error interno en run_lootbox: %s", exc, exc_info=True)
        # Exponer el error real para debugging (revertir en producción estricta)
        error_detail = f"Internal server error: {str(exc)}\nTraceback: {traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from exc
    
    return {
        "thread_id": result.thread_id,
        "summary": result.summary,
        "tx_hash": result.tx_hash,
        "explorer_url": result.explorer_url,
        "mode": result.mode,
        "reward_type": result.reward_type,
        "user_analysis": result.user_analysis,  # Información del usuario analizado
        "trend_info": result.trend_info,  # Información de la tendencia
        "eligible": result.eligible,  # Si el usuario es elegible
        "eligibility_message": result.eligibility_message,  # Mensaje de elegibilidad
        "error": result.error,  # Mensaje de error si hubo fallo
        "nft_images": result.nft_images,  # Imágenes de NFTs minteados
    }


def run_cli() -> None:
    """Permite ejecutar pruebas rápidas sin servidor HTTP."""

    import asyncio

    sample_event = LootboxEvent(frame_id="sample", channel_id="test", trend_score=0.91)
    asyncio.run(supervisor.run(sample_event.model_dump()))


# Webhook para notificaciones de Farcaster
@app.post("/api/webhook")
async def farcaster_webhook(request: Request):
    """Maneja eventos de webhooks de Farcaster (miniapp_added, notifications_enabled, etc)."""
    try:
        data = await request.json()
        event_type = data.get("event")
        
        logger.info("🔔 Webhook recibido: %s", event_type)
        logger.debug("Payload: %s", data)
        
        # TODO: Verificar firma del evento (X-Farcaster-Signature)
        # Por ahora confiamos en que viene del proxy de Next.js
        
        from .stores.notifications import get_notification_store
        store = get_notification_store()
        
        if event_type == "miniapp_added" or event_type == "notifications_enabled":
            details = data.get("notificationDetails", {})
            token = details.get("token")
            url = details.get("url")
            
            # El FID debería venir en el evento, pero Neynar/Farcaster a veces lo ponen en header o signer
            # Si usamos Neynar managed, el evento tiene estructura específica.
            # Si es directo de Farcaster, necesitamos decodificar el signer o confiar en el payload si trae fid.
            # Asumimos que el payload trae 'fid' o lo extraemos del header en el futuro.
            # FIX: Por ahora, logueamos para ver qué trae y guardamos si hay fid.
            # En la spec de Farcaster, el evento viene firmado y el FID está en el signer.
            # Para este MVP, si no podemos extraer FID fácilmente, solo logueamos.
            
            # Intentar extraer FID del payload si existe (algunos clientes lo mandan)
            fid = data.get("fid") 
            if not fid and "user" in data:
                fid = data["user"].get("fid")
                
            if fid and token and url:
                store.add_token(int(fid), token, url)
                logger.info("✅ Token guardado para FID %s", fid)
            else:
                logger.warning("⚠️ Datos incompletos en webhook: fid=%s, token=%s", fid, bool(token))
                
        elif event_type == "miniapp_removed" or event_type == "notifications_disabled":
            fid = data.get("fid")
            if fid:
                store.remove_token(int(fid))
                logger.info("🗑️ Token eliminado para FID %s", fid)
                
        return {"status": "success"}
        
    except Exception as exc:
        logger.error("Error procesando webhook: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

