import logging
import re
import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
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

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://celo-build-web-8rej.vercel.app",
        "https://celo-build-web.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Inicializar Farcaster Toolbox
from .tools.farcaster import FarcasterToolbox
farcaster_toolbox = FarcasterToolbox(
    base_url=settings.farcaster_hub_api or "https://api.neynar.com/v2",
    neynar_key=settings.neynar_api_key
)

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



@app.get("/api/lootbox/energy")
async def get_energy_status(address: str = Query(...)):
    """
    Obtiene el estado de energía de un usuario con información detallada de cada rayo.
    
    Args:
        address: Dirección de la wallet del usuario
    
    Returns:
        {
            "current_energy": int,      # 0-3
            "max_energy": int,          # 3
            "next_refill_at": float,    # Timestamp o None
            "seconds_to_refill": int,   # Segundos hasta la próxima recarga
            "bolts": [                  # Array con estado de cada rayo
                {
                    "index": int,       # 0, 1, 2
                    "available": bool,  # Si está disponible
                    "seconds_to_refill": int,  # Segundos hasta recargar (0 si está disponible)
                    "refill_at": float  # Timestamp de recarga (None si está disponible)
                }
            ]
        }
    """
    try:
        from .services.energy import energy_service
        
        # CRITICAL: get_status ya recarga los datos del archivo/Redis y calcula todo correctamente
        # No necesitamos duplicar la lógica aquí
        logger.info(f"🔋 [Energy API] Consultando energía para {address}")
        
        # get_status ya hace todo: recarga datos, calcula estado, filtra rayos recargados, y devuelve bolts
        status = energy_service.get_status(address)
        
        logger.info(f"🔋 [Energy API] Estado obtenido: {status['current_energy']}/{status['max_energy']} rayos")
        logger.info(f"🔋 [Energy API] Rayos disponibles: {sum(1 for b in status.get('bolts', []) if b.get('available', False))}")
        logger.info(f"🔋 [Energy API] Rayos recargando: {sum(1 for b in status.get('bolts', []) if not b.get('available', False))}")
        
        # Verificar que bolts esté presente
        if 'bolts' not in status or not status['bolts']:
            logger.warning(f"🔋 [Energy API] ⚠️ No se encontraron bolts en la respuesta, creando array por defecto")
            status['bolts'] = [
                {"index": i, "available": True, "seconds_to_refill": 0, "refill_at": None}
                for i in range(energy_service.MAX_ENERGY)
            ]
        
        return status
    except Exception as exc:
        logger.error("Error obteniendo estado de energía para %s: %s", address, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error leyendo energía: {str(exc)}"
        )


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
                
                # Self-healing: Si tenemos XP pero no rank (cold start), actualizar leaderboard local
                if rank is None and xp_balance > 0:
                    logger.info("Self-healing leaderboard for %s with %d XP", wallet_address, xp_balance)
                    active_supervisor.leaderboard.record({
                        "address": wallet_address,
                        "xp": xp_balance,
                        "score": 0  # Default score
                    })
                    # Re-intentar obtener rank
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


from fastapi import BackgroundTasks

@app.get("/api/lootbox/leaderboard")
async def leaderboard(background_tasks: BackgroundTasks, limit: int = Query(50, ge=1, le=100)) -> dict[str, list[dict[str, object]]]:
    """Devuelve el top de ganadores recientes.
    
    Si el leaderboard está vacío (cold start), dispara una sincronización en background.
    """
    try:
        # Usar supervisor del scheduler si está disponible, sino el global
        active_supervisor = scheduler_supervisor or supervisor
        if not active_supervisor:
            logger.warning("Supervisor no inicializado, retornando leaderboard vacío")
            return {"items": []}
            
        items = active_supervisor.leaderboard.top(limit)
        
        # COLD START HANDLER: Si no hay items, disparar sync en background
        if len(items) == 0:
            logger.info("❄️ Cold Start detectado (Leaderboard vacío). Iniciando sync en background...")
            
            async def _bg_sync():
                try:
                    global leaderboard_syncer
                    if not leaderboard_syncer:
                        leaderboard_syncer = LeaderboardSyncer(active_supervisor.leaderboard)
                    await leaderboard_syncer.sync()
                except Exception as e:
                    logger.error("Error en background sync: %s", e)
            
            background_tasks.add_task(_bg_sync)
            
        return {"items": items}
    except Exception as exc:
        logger.error("Error obteniendo leaderboard: %s", exc, exc_info=True)
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



from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi.responses import JSONResponse

class VerifyRechargeRequest(BaseModel):
    address: str
    fid: Optional[int] = None

@app.post("/api/lootbox/verify-recharge")
async def verify_recharge(req: VerifyRechargeRequest):
    """Verifica si el usuario ha compartido un cast reciente sobre la campaña."""
    verify_start = datetime.now()
    try:
        if not req.fid:
            # Try to resolve FID from address if not provided
            user = await farcaster_toolbox.fetch_user_by_address(req.address)
            if user:
                req.fid = user.get("fid")
        
        if not req.fid:
            return JSONResponse(
                status_code=400, 
                content={"verified": False, "message": "No se pudo encontrar tu FID de Farcaster."}
            )

        # 1. Fetch recent casts (last 5) - OPTIMIZATION: Reducir para ahorrar créditos API
        casts = await farcaster_toolbox.fetch_user_recent_casts(req.fid, limit=5)
        
        # 2. Check for campaign keywords/links
        verified = False
        target_domains = ["premio.xyz", "celo-build-web"] # Add your domain
        
        for cast in casts:
            text = cast.get("text", "").lower()
            embeds = cast.get("embeds", [])
            
            # Check text
            if any(domain in text for domain in target_domains):
                verified = True
                break
                
            # Check embeds (urls)
            for embed in embeds:
                url = embed.get("url", "").lower()
                if any(domain in url for domain in target_domains):
                    verified = True
                    break
            
            if verified:
                break
        
        # 3. Refill Energy if verified
        if verified:
            from .services.energy import energy_service
            energy_service.refill_energy(req.address)

        # 4. Return result
        return {
            "verified": verified,
            "message": "¡Verificado! Recargando energía... ⚡" if verified else "No encontramos un cast reciente con el enlace. ¡Intenta compartir de nuevo!",
            "execution_time_ms": (datetime.now() - verify_start).total_seconds() * 1000
        }

    except Exception as e:
        logger.error(f"Error verifying recharge: {e}")
        return JSONResponse(status_code=500, content={"verified": False, "message": str(e)})

@app.post("/api/lootbox/trigger")
async def trigger_scan(req: LootboxEvent):
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
        
        import time
        start_time = time.time()
        
        result = await active_supervisor.run(payload)
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"⏱️ Total Execution Time: {duration:.2f} seconds")
        
        # Handle result whether it's an object or a dict
        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        return {
            "status": "success",
            "summary": get_attr(result, "summary"),
            "tx_hash": get_attr(result, "tx_hash"),
            "explorer_url": get_attr(result, "explorer_url"),
            "mode": get_attr(result, "mode"),
            "reward_type": get_attr(result, "reward_type"),
            "execution_time_ms": int(duration * 1000),
            "error": get_attr(result, "error"), # Pass error to frontend
        }
    except Exception as exc:
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
            
            
        # Guardar mapeo dirección -> FID si está disponible
        if event.target_address and event.target_fid:
            from .stores.notifications import get_notification_store
            store = get_notification_store()
            store.add_address_mapping(event.target_address, event.target_fid)
            logger.info(f"💾 Mapeo guardado: {event.target_address} -> FID {event.target_fid}")
        
        # Ejecutar el supervisor
        payload = event.model_dump()
        result = await active_supervisor.run(payload)

        from fastapi.encoders import jsonable_encoder
        
        response_data = {
            "thread_id": result.thread_id,
            "summary": result.summary,
            "tx_hash": result.tx_hash,
            "explorer_url": result.explorer_url,
            "mode": result.mode,
            "reward_type": result.reward_type,
            "user_analysis": result.user_analysis,
            "trend_info": result.trend_info,
            "eligible": result.eligible,
            "eligibility_message": result.eligibility_message,
            "error": result.error,
            "nft_images": result.nft_images,
            "best_cast": result.best_cast,
            "cast_text": getattr(result, "cast_text", None),
            "cast_hash": getattr(result, "cast_hash", None),
            "xp_granted": getattr(result, "xp_granted", 0),
            "trace_logs": getattr(result, "trace_logs", []),
            "energy_status": getattr(result, "energy_status", None),  # Estado de energía después de consumir
        }
        
        # Forzar serialización aquí para capturar errores
        return jsonable_encoder(response_data)

    except ValueError as exc:
        # Errores de validación (direcciones inválidas, etc.)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - logging pendiente
        # No exponer detalles internos en producción
        import traceback
        # logger ya está definido al inicio del archivo, no redefinir aquí
        logger.error("Error interno en run_lootbox: %s", exc, exc_info=True)
        # Exponer el error real para debugging (revertir en producción estricta)
        error_detail = f"Internal server error: {str(exc)}\nTraceback: {traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from exc


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


@app.get("/api/lootbox/notify-energy")
async def notify_energy_reminder():
    """Endpoint para enviar notificaciones diarias a usuarios recordándoles usar sus rayos de energía.
    
    Este endpoint se ejecuta automáticamente cada 24 horas mediante Vercel Cron Jobs.
    Envía notificaciones a usuarios que tienen al menos 1 rayo disponible o que están recargando.
    """
    try:
        from .services.energy import energy_service
        from .tools.farcaster import FarcasterToolbox
        from .config import settings
        
        logger.info("🔔 Iniciando envío de notificaciones de energía...")
        
        # Obtener todas las direcciones con estado de energía
        addresses = energy_service.get_all_addresses()
        logger.info(f"📋 Encontradas {len(addresses)} direcciones con estado de energía")
        
        if not addresses:
            return {"status": "success", "notifications_sent": 0, "message": "No hay usuarios con energía registrada"}
        
        # Inicializar Farcaster toolbox
        farcaster = FarcasterToolbox(neynar_key=settings.neynar_api_key)
        
        notifications_sent = 0
        notifications_failed = 0
        
        # Obtener store de notificaciones para mapeo dirección -> FID
        from .stores.notifications import get_notification_store
        store = get_notification_store()
        
        # Para cada dirección, buscar su FID y enviar notificación
        for address in addresses:
            try:
                # Obtener estado de energía
                energy_status = energy_service.get_status(address)
                current_energy = energy_status.get("current_energy", 0)
                max_energy = energy_status.get("max_energy", 3)
                seconds_to_refill = energy_status.get("seconds_to_refill", 0)
                
                # Solo notificar si el usuario tiene todos los rayos disponibles (3/3) o está recargando
                # No notificar si tiene 1-2 rayos disponibles
                if current_energy > 0 and current_energy < max_energy:
                    # Usuario con algunos rayos pero no todos, saltar
                    continue
                
                if current_energy == 0 and seconds_to_refill == 0:
                    # Usuario sin energía y sin recargas pendientes, saltar
                    continue
                
                # Buscar FID usando el mapeo guardado
                fid = store.get_fid_by_address(address)
                if not fid:
                    logger.debug(f"⚠️ No se encontró FID para dirección {address}, saltando...")
                    continue
                
                # Verificar cooldown de 48 horas
                can_send, seconds_remaining = store.can_send_notification(fid)
                if not can_send:
                    hours_remaining = seconds_remaining / 3600
                    logger.debug(f"⏳ FID {fid} en cooldown. Restan {hours_remaining:.1f} horas. Saltando...")
                    continue
                
                logger.info(f"📨 Enviando notificación a FID {fid} (dirección: {address}, energía: {current_energy}/{max_energy})")
                
                # Preparar mensaje según estado de energía
                if current_energy == max_energy:
                    title = "⚡ ¡Tus Rayos Están Listos!"
                    body = f"Tienes {current_energy} rayos disponibles. ¡Obtén tu recompensa ahora!"
                else:
                    # Usuario sin energía pero recargando
                    hours = seconds_to_refill // 3600
                    minutes = (seconds_to_refill % 3600) // 60
                    title = "⚡ Rayos Recargando"
                    body = f"Tu próximo rayo estará listo en {hours}h {minutes}m. ¡Vuelve pronto!"
                
                # Enviar notificación
                result = await farcaster.publish_frame_notification(
                    target_fids=[fid],
                    title=title,
                    body=body,
                    target_url="https://celo-build-web-8rej.vercel.app/"
                )
                
                if result.get("status") == "success" or "status" not in result:
                    notifications_sent += 1
                    # Registrar que se envió la notificación
                    store.record_notification_sent(fid)
                    logger.info(f"✅ Notificación enviada a FID {fid}")
                else:
                    notifications_failed += 1
                    logger.warning(f"❌ Error enviando notificación a FID {fid}: {result}")
                    
            except Exception as exc:
                logger.error(f"Error procesando dirección {address}: {exc}")
                notifications_failed += 1
                continue
        
        logger.info(f"✅ Notificaciones completadas: {notifications_sent} enviadas, {notifications_failed} fallidas")
        
        return {
            "status": "success",
            "notifications_sent": notifications_sent,
            "notifications_failed": notifications_failed,
            "total_addresses": len(addresses)
        }
        
    except Exception as exc:
        logger.error("Error en notificaciones de energía: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# ENDPOINTS PARA GENERACIÓN Y PROGRAMACIÓN DE CASTS
# ============================================================================

from .services.cast_generator import CastGeneratorService
from .services.cast_scheduler import CastSchedulerService
from .tools.celo import CeloToolbox
from datetime import datetime
from web3 import Web3

# Inicializar servicios
cast_generator = CastGeneratorService(settings)
celo_toolbox = CeloToolbox(
    rpc_url=settings.celo_rpc_url,
    private_key=settings.celo_private_key
)
cast_scheduler = CastSchedulerService(
    farcaster_toolbox=farcaster_toolbox,
    celo_toolbox=celo_toolbox,
    registry_address=settings.registry_address
)

# Iniciar scheduler si no estamos en Vercel
if not is_vercel:
    cast_scheduler.start()


class GenerateCastRequest(BaseModel):
    topic: str = Field(..., description="Tema del cast: tech, musica, motivacion, chistes, frases_celebres")
    user_address: str | None = Field(None, description="Dirección del usuario (opcional para preview)")
    user_fid: int | None = Field(None, description="FID del usuario en Farcaster (opcional para preview)")


class PublishCastRequest(BaseModel):
    topic: str
    cast_text: str = Field(..., max_length=320)
    user_address: str
    user_fid: int
    payment_tx_hash: str
    scheduled_time: str | None = Field(None, description="ISO 8601 datetime para programar, o null para publicar ahora")


class CancelCastRequest(BaseModel):
    cast_id: str
    user_address: str

class VerifyPublicationRequest(BaseModel):
    user_fid: int
    user_address: str
    cast_text: str
    payment_tx_hash: str


@app.get("/api/casts/topics")
async def get_available_topics():
    """Obtiene todos los temas disponibles para generar casts."""
    topics = CastGeneratorService.get_available_topics()
    return {"topics": topics}


@app.get("/api/casts/agent-address")
async def get_agent_address():
    """Obtiene la dirección de la wallet del agente para pagos."""
    try:
        address = celo_toolbox.get_agent_address()
        return {
            "agent_address": address,
            "message": "Envía cUSD a esta dirección para pagar por publicar casts"
        }
    except Exception as exc:
        logger.error("Error obteniendo dirección del agente: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/casts/generate")
async def generate_cast(request: GenerateCastRequest):
    """Genera un cast usando IA basado en el tema (sin publicar, solo preview)."""
    try:
        user_context = None
        if request.user_fid:
            # Obtener información del usuario si tenemos FID
            user_info = await farcaster_toolbox.fetch_user_by_fid(request.user_fid)
            if user_info:
                user_context = {"username": user_info.get("username", "usuario")}
        
        result = await cast_generator.generate_cast(request.topic, user_context)
        return result
    except Exception as exc:
        logger.error("Error generando cast: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/casts/publish")
async def publish_cast(request: PublishCastRequest):
    """Publica un cast después de validar el pago.
    
    Flujo:
    1. Valida que el pago on-chain es correcto
    2. Publica el cast (ahora o programado)
    3. Otorga XP al usuario
    """
    try:
        # Obtener dirección del agente
        agent_address = celo_toolbox.get_agent_address()
        
        # Precio: 0.5 CELO nativo = 500000000000000000 wei (18 decimales)
        PRICE_WEI = int(0.5 * 10**18)
        
        # Validar pago en CELO nativo
        payment_validation = celo_toolbox.validate_native_payment(
            tx_hash=request.payment_tx_hash,
            expected_recipient=agent_address,
            expected_amount=PRICE_WEI
        )
        
        if not payment_validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Pago inválido: {payment_validation['message']}"
            )
        
        # Verificar que el sender es el usuario
        if payment_validation["sender"].lower() != request.user_address.lower():
            raise HTTPException(
                status_code=400,
                detail="El pago no proviene de la dirección del usuario"
            )
        
        logger.info(f"✅ Pago validado para usuario {request.user_address}: {payment_validation['amount']} wei")
        
        # Verificar si el usuario tiene un signer aprobado ANTES de intentar publicar
        from .stores.signers import get_signer_store
        signer_store = get_signer_store()
        signer_data = signer_store.get_signer(str(request.user_fid))
        
        # Si no hay signer o no está aprobado, crear uno automáticamente
        if not signer_data or signer_data.get("status") != "approved":
            # Si ya existe un signer pendiente, usar ese en lugar de crear uno nuevo
            if signer_data and signer_data.get("status") == "pending_approval":
                approval_url = signer_data.get("approval_url")
                if approval_url:
                    logger.info(f"🔑 Usuario {request.user_fid} tiene signer pendiente de aprobación. Usando existente...")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Se requiere aprobar un signer para publicar casts. Por favor, aprueba el signer en Warpcast usando este enlace: {approval_url}",
                        headers={"X-Approval-URL": approval_url}
                    )
            
            logger.info(f"🔑 Usuario {request.user_fid} no tiene signer aprobado. Creando uno automáticamente...")
            
            # Crear signer
            create_result = await farcaster_toolbox.create_signer()
            if create_result.get("status") != "success":
                raise HTTPException(
                    status_code=500,
                    detail=f"Error creando signer: {create_result.get('message', 'Error desconocido')}"
                )
            
            signer_uuid = create_result.get("signer_uuid")
            public_key = create_result.get("public_key")
            
            # Guardar en store
            signer_store.add_signer(
                user_id=str(request.user_fid),
                signer_uuid=signer_uuid,
                status="generated",
                public_key=public_key
            )
            signer_store.add_signer(
                user_id=request.user_address.lower(),
                signer_uuid=signer_uuid,
                status="generated",
                public_key=public_key
            )
            
            # Registrar signed key (requiere app mnemonic)
            if not settings.neynar_app_fid or not settings.neynar_app_mnemonic:
                raise HTTPException(
                    status_code=500,
                    detail="NEYNAR_APP_FID y NEYNAR_APP_MNEMONIC deben estar configurados para registrar signers"
                )
            
            # Obtener app_fid
            app_fid = settings.neynar_app_fid
            if not app_fid and settings.neynar_app_mnemonic:
                # Intentar obtener desde mnemonic
                try:
                    from eth_account import Account
                    Account.enable_unaudited_hdwallet_features()
                    account = Account.from_mnemonic(settings.neynar_app_mnemonic)
                    custody_address = account.address
                    
                    lookup_url = f"https://api.neynar.com/v2/farcaster/user/by_custody_address?custody_address={custody_address}"
                    lookup_headers = {
                        "accept": "application/json",
                        "x-api-key": farcaster_toolbox.neynar_key
                    }
                    async with httpx.AsyncClient(timeout=30) as client:
                        lookup_resp = await client.get(lookup_url, headers=lookup_headers)
                        if lookup_resp.status_code == 200:
                            lookup_data = lookup_resp.json()
                            app_fid = lookup_data.get("result", {}).get("fid")
                            if app_fid:
                                logger.info(f"✅ FID encontrado desde custody address: {app_fid}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo obtener FID desde mnemonic: {e}")
            
            if not app_fid:
                raise HTTPException(
                    status_code=500,
                    detail="NEYNAR_APP_FID debe estar configurado o NEYNAR_APP_MNEMONIC debe corresponder a una cuenta Farcaster válida"
                )
            
            # Crear deadline (24 horas desde ahora)
            deadline = int(time.time()) + (24 * 60 * 60)
            
            # Firmar usando el método correcto
            try:
                from eth_account import Account
                from eth_account.messages import encode_defunct
                from web3 import Web3
                
                Account.enable_unaudited_hdwallet_features()
                account = Account.from_mnemonic(settings.neynar_app_mnemonic)
                
                # Crear mensaje según formato EIP-712 de Farcaster
                public_key_bytes = bytes.fromhex(public_key.replace("0x", ""))
                
                import hashlib
                message_data = (
                    app_fid.to_bytes(32, 'big') +
                    public_key_bytes +
                    deadline.to_bytes(32, 'big')
                )
                message_hash = hashlib.sha256(message_data).digest()
                
                # Firmar el hash
                signed_message = account.signHash(message_hash)
                signature = signed_message.signature.hex()
                
            except Exception as e:
                logger.error(f"Error generando firma: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Error generando firma: {str(e)}. Asegúrate de que NEYNAR_APP_MNEMONIC sea válido."
                )
            
            # Registrar signed key
            register_result = await farcaster_toolbox.register_signed_key(
                signer_uuid=signer_uuid,
                app_fid=app_fid,
                deadline=deadline,
                signature=signature
            )
            
            if register_result.get("status") != "success":
                raise HTTPException(
                    status_code=500,
                    detail=register_result.get("message", "Error registrando signed key")
                )
            
            approval_url = register_result.get("approval_url")
            
            # Actualizar store
            signer_store.update_signer_status(
                user_id=str(request.user_fid),
                status="pending_approval"
            )
            signer_store.add_signer(
                user_id=str(request.user_fid),
                signer_uuid=signer_uuid,
                status="pending_approval",
                public_key=public_key,
                approval_url=approval_url
            )
            
            # Devolver error con approval URL para que el frontend lo muestre
            raise HTTPException(
                status_code=400,
                detail=f"Se requiere aprobar un signer para publicar casts. Por favor, aprueba el signer en Warpcast usando este enlace: {approval_url}",
                headers={"X-Approval-URL": approval_url}
            )
        
        # Parsear scheduled_time si existe
        scheduled_time = None
        if request.scheduled_time:
            try:
                scheduled_time = datetime.fromisoformat(request.scheduled_time.replace("Z", "+00:00"))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {e}")
        
        # Publicar o programar
        if scheduled_time is None:
            # Publicar ahora (await porque ahora es async)
            result = await cast_scheduler.publish_now(
                user_address=request.user_address,
                user_fid=request.user_fid,
                topic=request.topic,
                cast_text=request.cast_text,
                payment_tx_hash=request.payment_tx_hash
            )
            
            # Si falló la publicación, lanzar error
            if result.get("status") != "published":
                error_msg = result.get("error_message", "Error desconocido al publicar cast")
                logger.error(f"❌ Error publicando cast: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )
            
            # Publicación exitosa
            xp_granted = result.get("xp_granted", 0)
            return {
                "status": "published",
                **result,
                "xp_granted": xp_granted,
                "message": f"Cast publicado exitosamente. Ganaste {xp_granted} XP" if xp_granted > 0 else "Cast publicado exitosamente"
            }
        else:
            # Programar
            cast_id = cast_scheduler.schedule_cast(
                user_address=request.user_address,
                user_fid=request.user_fid,
                topic=request.topic,
                cast_text=request.cast_text,
                scheduled_time=scheduled_time,
                payment_tx_hash=request.payment_tx_hash
            )
            return {
                "cast_id": cast_id,
                "status": "scheduled",
                "scheduled_time": scheduled_time.isoformat(),
                "xp_granted": 0,
                "message": "Cast programado exitosamente. Recibirás XP cuando se publique."
            }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error publicando cast: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/casts/scheduled")
async def get_scheduled_casts(user_address: str = Query(..., description="Dirección del usuario")):
    """Obtiene todos los casts programados de un usuario."""
    try:
        casts = cast_scheduler.get_user_scheduled_casts(user_address)
        return {"casts": casts}
    except Exception as exc:
        logger.error("Error obteniendo casts programados: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/casts/cancel")
async def cancel_cast(request: CancelCastRequest):
    """Cancela un cast programado."""
    try:
        success = cast_scheduler.cancel_cast(request.cast_id, request.user_address)
        if not success:
            raise HTTPException(status_code=404, detail="Cast no encontrado o no se puede cancelar")
        return {"status": "success", "message": "Cast cancelado exitosamente"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error cancelando cast: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/casts/verify-publication")
async def verify_publication(request: VerifyPublicationRequest):
    """Verifica si el usuario publicó el cast en Farcaster y otorga XP si es así.
    
    Flujo:
    1. Valida que el pago on-chain es correcto
    2. Busca el cast en los casts recientes del usuario
    3. Si encuentra el cast, otorga XP
    """
    try:
        # Obtener dirección del agente
        agent_address = celo_toolbox.get_agent_address()
        
        # Precio: 0.5 CELO nativo = 500000000000000000 wei (18 decimales)
        PRICE_WEI = int(0.5 * 10**18)
        
        # Validar pago en CELO nativo
        payment_validation = celo_toolbox.validate_native_payment(
            tx_hash=request.payment_tx_hash,
            expected_recipient=agent_address,
            expected_amount=PRICE_WEI
        )
        
        if not payment_validation["valid"]:
            return {
                "verified": False,
                "message": f"Pago inválido: {payment_validation['message']}"
            }
        
        # Verificar que el sender es el usuario
        if payment_validation["sender"].lower() != request.user_address.lower():
            return {
                "verified": False,
                "message": "El pago no proviene de la dirección del usuario"
            }
        
        logger.info(f"✅ Pago validado para usuario {request.user_address}")
        
        # Buscar el cast en los casts recientes del usuario
        casts = await farcaster_toolbox.fetch_user_recent_casts(request.user_fid, limit=5)
        
        # Normalizar el texto del cast para comparación (sin espacios extra, lowercase)
        cast_text_normalized = " ".join(request.cast_text.split()).lower()
        
        verified = False
        cast_hash = None
        
        for cast in casts:
            cast_text = cast.get("text", "")
            cast_text_normalized_check = " ".join(cast_text.split()).lower()
            
            # Comparar textos normalizados (permitir variaciones menores)
            if cast_text_normalized in cast_text_normalized_check or cast_text_normalized_check in cast_text_normalized:
                verified = True
                cast_hash = cast.get("hash")
                logger.info(f"✅ Cast encontrado: {cast_hash}")
                break
        
        if verified:
            # Otorgar XP
            xp_amount = 100
            xp_result = celo_toolbox.grant_xp(request.user_address, xp_amount)
            
            if xp_result.get("success"):
                logger.info(f"✅ XP otorgado: {xp_amount} XP a {request.user_address}")
                return {
                    "verified": True,
                    "xp_granted": xp_amount,
                    "cast_hash": cast_hash,
                    "message": f"Cast verificado exitosamente. Ganaste {xp_amount} XP"
                }
            else:
                logger.warning(f"⚠️ No se pudo otorgar XP: {xp_result.get('message')}")
                return {
                    "verified": True,
                    "xp_granted": 0,
                    "cast_hash": cast_hash,
                    "message": "Cast verificado, pero no se pudo otorgar XP"
                }
        else:
            return {
                "verified": False,
                "message": "No se encontró el cast en tus publicaciones recientes. Asegúrate de haber publicado el cast en Warpcast."
            }
        
    except Exception as exc:
        logger.error("Error verificando publicación: %s", exc, exc_info=True)
        return {
            "verified": False,
            "message": f"Error interno: {str(exc)}"
        }


# ============================================================================
# ENDPOINTS PARA GESTIÓN DE SIGNERS (Neynar)
# ============================================================================

from .stores.signers import get_signer_store
from datetime import datetime, timezone
import time

class CreateSignerRequest(BaseModel):
    user_fid: int = Field(..., description="FID del usuario")
    user_address: str | None = Field(None, description="Dirección del usuario (opcional)")

class RegisterSignedKeyRequest(BaseModel):
    signer_uuid: str = Field(..., description="UUID del signer creado")
    user_fid: int = Field(..., description="FID del usuario")

@app.post("/api/casts/signer/create")
async def create_signer_endpoint(request: CreateSignerRequest):
    """Crea un nuevo signer para un usuario."""
    try:
        # Crear signer usando Neynar API
        result = await farcaster_toolbox.create_signer()
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Error creando signer"))
        
        signer_uuid = result.get("signer_uuid")
        public_key = result.get("public_key")
        
        # Guardar en store
        signer_store = get_signer_store()
        user_id = str(request.user_fid)
        signer_store.add_signer(
            user_id=user_id,
            signer_uuid=signer_uuid,
            status="generated",
            public_key=public_key
        )
        
        # Si hay address, también guardar mapeo
        if request.user_address:
            signer_store.add_signer(
                user_id=request.user_address.lower(),
                signer_uuid=signer_uuid,
                status="generated",
                public_key=public_key
            )
        
        return {
            "status": "success",
            "signer_uuid": signer_uuid,
            "public_key": public_key,
            "message": "Signer creado exitosamente. Ahora necesitas registrar la signed key."
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creando signer: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creando signer: {exc}")


@app.post("/api/casts/signer/register")
async def register_signed_key_endpoint(request: RegisterSignedKeyRequest):
    """Registra una signed key (requiere que la app firme con su mnemonic)."""
    try:
        if not settings.neynar_app_fid or not settings.neynar_app_mnemonic:
            raise HTTPException(
                status_code=500,
                detail="NEYNAR_APP_FID y NEYNAR_APP_MNEMONIC deben estar configurados para registrar signed keys"
            )
        
        # Obtener signer del store
        signer_store = get_signer_store()
        signer_data = signer_store.get_signer(str(request.user_fid))
        if not signer_data or signer_data.get("signer_uuid") != request.signer_uuid:
            raise HTTPException(status_code=404, detail="Signer no encontrado")
        
        public_key = signer_data.get("public_key")
        if not public_key:
            raise HTTPException(status_code=400, detail="Public key no encontrada para este signer")
        
        # Obtener FID de la app desde el mnemonic si no está configurado
        app_fid = settings.neynar_app_fid
        if not app_fid and settings.neynar_app_mnemonic:
            # Buscar FID usando el custody address del mnemonic
            try:
                from eth_account import Account
                Account.enable_unaudited_hdwallet_features()
                account = Account.from_mnemonic(settings.neynar_app_mnemonic)
                custody_address = account.address
                
                # Buscar usuario por custody address usando Neynar API
                lookup_url = f"https://api.neynar.com/v2/farcaster/user/by_custody_address?custody_address={custody_address}"
                lookup_headers = {
                    "accept": "application/json",
                    "x-api-key": farcaster_toolbox.neynar_key
                }
                async with httpx.AsyncClient(timeout=30) as client:
                    lookup_resp = await client.get(lookup_url, headers=lookup_headers)
                    if lookup_resp.status_code == 200:
                        lookup_data = lookup_resp.json()
                        app_fid = lookup_data.get("result", {}).get("fid")
                        if app_fid:
                            logger.info(f"✅ FID encontrado desde custody address: {app_fid}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo obtener FID desde mnemonic: {e}")
        
        if not app_fid:
            raise HTTPException(
                status_code=500,
                detail="NEYNAR_APP_FID debe estar configurado o NEYNAR_APP_MNEMONIC debe corresponder a una cuenta Farcaster válida"
            )
        
        # Crear deadline (24 horas desde ahora)
        deadline = int(time.time()) + (24 * 60 * 60)
        
        # Firmar usando el método correcto según documentación de Neynar
        # Necesitamos usar @farcaster/hub-nodejs equivalente en Python
        # Por ahora, usamos una implementación simplificada
        try:
            from eth_account import Account
            from eth_account.messages import encode_defunct
            from web3 import Web3
            
            Account.enable_unaudited_hdwallet_features()
            account = Account.from_mnemonic(settings.neynar_app_mnemonic)
            
            # Crear mensaje según formato EIP-712 de Farcaster
            # El formato es: requestFid (uint256) + key (bytes) + deadline (uint256)
            # Convertir public_key de hex string a bytes
            public_key_bytes = bytes.fromhex(public_key.replace("0x", ""))
            
            # Crear mensaje estructurado (simplificado - en producción usar @farcaster/hub-nodejs)
            # Por ahora, usamos un hash simple
            import hashlib
            message_data = (
                app_fid.to_bytes(32, 'big') +
                public_key_bytes +
                deadline.to_bytes(32, 'big')
            )
            message_hash = hashlib.sha256(message_data).digest()
            
            # Firmar el hash
            signed_message = account.signHash(message_hash)
            signature = signed_message.signature.hex()
            
        except Exception as e:
            logger.error(f"Error generando firma: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error generando firma: {str(e)}. Asegúrate de que NEYNAR_APP_MNEMONIC sea válido."
            )
        
        # Registrar signed key
        result = await farcaster_toolbox.register_signed_key(
            signer_uuid=request.signer_uuid,
            app_fid=app_fid,  # Usar app_fid calculado (puede ser el configurado o el obtenido desde mnemonic)
            deadline=deadline,
            signature=signature
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Error registrando signed key"))
        
        approval_url = result.get("approval_url")
        
        # Actualizar store
        signer_store.update_signer_status(
            user_id=str(request.user_fid),
            status="pending_approval"
        )
        signer_store.add_signer(
            user_id=str(request.user_fid),
            signer_uuid=request.signer_uuid,
            status="pending_approval",
            public_key=public_key,
            approval_url=approval_url
        )
        
        return {
            "status": "success",
            "approval_url": approval_url,
            "message": "Signed key registrada. Usa el approval_url para que el usuario apruebe en Warpcast."
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error registrando signed key: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error registrando signed key: {exc}")


@app.get("/api/casts/signer/status")
async def get_signer_status_endpoint(signer_uuid: str = Query(..., description="UUID del signer")):
    """Obtiene el estado actual de un signer (para polling)."""
    try:
        result = await farcaster_toolbox.get_signer_status(signer_uuid)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Error obteniendo estado del signer"))
        
        # Actualizar store si el signer fue aprobado
        if result.get("status") == "approved" and result.get("fid"):
            signer_store = get_signer_store()
            # Buscar usuario por signer_uuid
            for user_id, signer_data in signer_store._data.items():
                if signer_data.get("signer_uuid") == signer_uuid:
                    signer_store.update_signer_status(
                        user_id=user_id,
                        status="approved",
                        fid=result.get("fid")
                    )
                    break
        
        return {
            "status": "success",
            "signer_uuid": result.get("signer_uuid"),
            "status": result.get("status"),
            "fid": result.get("fid"),
            "approval_url": result.get("approval_url")
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error obteniendo estado del signer: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado del signer: {exc}")


@app.get("/api/casts/signer/check")
async def check_signer_endpoint(
    user_fid: int = Query(..., description="FID del usuario"),
    user_address: str = Query(..., description="Dirección del usuario")
):
    """
    Verifica si el usuario tiene un signer aprobado.
    Si no lo tiene, crea uno automáticamente y devuelve el approval_url.
    Este endpoint debe llamarse ANTES de procesar el pago.
    """
    try:
        signer_store = get_signer_store()
        signer_data = signer_store.get_signer(str(user_fid))
        
        # Si ya tiene signer aprobado, devolver éxito
        if signer_data and signer_data.get("status") == "approved":
            return {
                "status": "approved",
                "signer_uuid": signer_data.get("signer_uuid"),
                "message": "Signer ya está aprobado"
            }
        
        # Si tiene signer pendiente, devolver approval_url
        if signer_data and signer_data.get("status") == "pending_approval":
            approval_url = signer_data.get("approval_url")
            if approval_url:
                return {
                    "status": "pending_approval",
                    "approval_url": approval_url,
                    "signer_uuid": signer_data.get("signer_uuid"),
                    "message": "Signer pendiente de aprobación"
                }
        
        # Si no tiene signer o no está aprobado, crear uno automáticamente
        logger.info(f"🔑 Usuario {user_fid} no tiene signer aprobado. Creando uno automáticamente...")
        
        # Crear signer
        create_result = await farcaster_toolbox.create_signer()
        logger.info(f"🔑 Resultado de create_signer: {create_result}")
        
        # Verificar que el signer se creó correctamente
        # Neynar devuelve status: 'generated' cuando se crea exitosamente, no 'success'
        signer_uuid = create_result.get("signer_uuid")
        public_key = create_result.get("public_key")
        result_status = create_result.get("status")
        
        # Validar que tenemos los datos necesarios
        if not signer_uuid or not public_key:
            error_message = create_result.get("message", "Respuesta incompleta: falta signer_uuid o public_key")
            logger.error(f"❌ Respuesta de create_signer incompleta: signer_uuid={signer_uuid}, public_key={'presente' if public_key else 'ausente'}")
            raise HTTPException(
                status_code=500,
                detail=f"Error creando signer: {error_message}"
            )
        
        # Verificar que el status no sea 'error'
        if result_status == "error":
            error_message = create_result.get("message", "Error desconocido al crear signer")
            logger.error(f"❌ Error creando signer: {error_message}. Resultado completo: {create_result}")
            raise HTTPException(
                status_code=500,
                detail=f"Error creando signer: {error_message}"
            )
        
        # Si llegamos aquí, el signer se creó exitosamente (status puede ser 'generated' o 'success')
        logger.info(f"✅ Signer creado exitosamente: {signer_uuid[:8]}...")
        
        # Guardar en store
        signer_store.add_signer(
            user_id=str(user_fid),
            signer_uuid=signer_uuid,
            status="generated",
            public_key=public_key
        )
        signer_store.add_signer(
            user_id=user_address.lower(),
            signer_uuid=signer_uuid,
            status="generated",
            public_key=public_key
        )
        
        # Registrar signed key (requiere app mnemonic)
        if not settings.neynar_app_fid or not settings.neynar_app_mnemonic:
            raise HTTPException(
                status_code=500,
                detail="NEYNAR_APP_FID y NEYNAR_APP_MNEMONIC deben estar configurados para registrar signers"
            )
        
        # Obtener app_fid
        app_fid = settings.neynar_app_fid
        if not app_fid and settings.neynar_app_mnemonic:
            # Intentar obtener desde mnemonic
            try:
                from eth_account import Account
                Account.enable_unaudited_hdwallet_features()
                account = Account.from_mnemonic(settings.neynar_app_mnemonic)
                custody_address = account.address
                
                lookup_url = f"https://api.neynar.com/v2/farcaster/user/by_custody_address?custody_address={custody_address}"
                lookup_headers = {
                    "accept": "application/json",
                    "x-api-key": farcaster_toolbox.neynar_key
                }
                async with httpx.AsyncClient(timeout=30) as client:
                    lookup_resp = await client.get(lookup_url, headers=lookup_headers)
                    if lookup_resp.status_code == 200:
                        lookup_data = lookup_resp.json()
                        app_fid = lookup_data.get("result", {}).get("fid")
                        if app_fid:
                            logger.info(f"✅ FID encontrado desde custody address: {app_fid}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo obtener FID desde mnemonic: {e}")
        
        if not app_fid:
            raise HTTPException(
                status_code=500,
                detail="NEYNAR_APP_FID debe estar configurado o NEYNAR_APP_MNEMONIC debe corresponder a una cuenta Farcaster válida"
            )
        
        # Crear deadline (24 horas desde ahora)
        deadline = int(time.time()) + (24 * 60 * 60)
        
        # Firmar usando el método correcto
        try:
            from eth_account import Account
            from eth_account.messages import encode_defunct
            from web3 import Web3
            
            Account.enable_unaudited_hdwallet_features()
            account = Account.from_mnemonic(settings.neynar_app_mnemonic)
            
            # Crear mensaje según formato EIP-712 de Farcaster
            public_key_bytes = bytes.fromhex(public_key.replace("0x", ""))
            
            import hashlib
            message_data = (
                app_fid.to_bytes(32, 'big') +
                public_key_bytes +
                deadline.to_bytes(32, 'big')
            )
            message_hash = hashlib.sha256(message_data).digest()
            
            # Firmar el hash
            signed_message = account.signHash(message_hash)
            signature = signed_message.signature.hex()
            
        except Exception as e:
            logger.error(f"Error generando firma: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error generando firma: {str(e)}. Asegúrate de que NEYNAR_APP_MNEMONIC sea válido."
            )
        
        # Registrar signed key
        register_result = await farcaster_toolbox.register_signed_key(
            signer_uuid=signer_uuid,
            app_fid=app_fid,
            deadline=deadline,
            signature=signature
        )
        
        if register_result.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=register_result.get("message", "Error registrando signed key")
            )
        
        approval_url = register_result.get("approval_url")
        
        # Actualizar store
        signer_store.update_signer_status(
            user_id=str(user_fid),
            status="pending_approval"
        )
        signer_store.add_signer(
            user_id=str(user_fid),
            signer_uuid=signer_uuid,
            status="pending_approval",
            public_key=public_key,
            approval_url=approval_url
        )
        
        logger.info(f"🔑 Signer creado y registrado para FID {user_fid}. Approval URL: {approval_url}")
        
        return {
            "status": "pending_approval",
            "approval_url": approval_url,
            "signer_uuid": signer_uuid,
            "message": "Signer creado. Por favor, aprueba el signer en Warpcast antes de continuar."
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error verificando/creando signer: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error verificando signer: {exc}")


@app.get("/api/casts/app-fid")
async def get_app_fid_endpoint():
    """Obtiene el FID de la app desde el mnemonic configurado."""
    try:
        if not settings.neynar_app_mnemonic:
            raise HTTPException(
                status_code=400,
                detail="NEYNAR_APP_MNEMONIC no está configurado"
            )
        
        if not farcaster_toolbox.neynar_key or farcaster_toolbox.neynar_key == "NEYNAR_API_DOCS":
            raise HTTPException(
                status_code=400,
                detail="NEYNAR_API_KEY no está configurado o es inválido"
            )
        
        # Obtener custody address desde mnemonic
        from eth_account import Account
        Account.enable_unaudited_hdwallet_features()
        account = Account.from_mnemonic(settings.neynar_app_mnemonic)
        custody_address = account.address
        
        # Buscar FID usando Neynar API
        lookup_url = f"https://api.neynar.com/v2/farcaster/user/by_custody_address"
        params = {"custody_address": custody_address}
        headers = {
            "accept": "application/json",
            "x-api-key": farcaster_toolbox.neynar_key
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(lookup_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                fid = result.get("fid")
                
                if fid:
                    return {
                        "status": "success",
                        "fid": fid,
                        "custody_address": custody_address,
                        "username": result.get("username"),
                        "display_name": result.get("display_name"),
                        "message": f"Tu NEYNAR_APP_FID es: {fid}"
                    }
                else:
                    raise HTTPException(
                        status_code=404,
                        detail="No se encontró cuenta Farcaster para este mnemonic. Asegúrate de que la wallet tenga una cuenta Farcaster registrada."
                    )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontró cuenta Farcaster para este mnemonic. Necesitas crear una cuenta Farcaster primero."
                )
            else:
                error_text = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error obteniendo FID: {error_text}"
                )
                
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error obteniendo FID de la app: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo FID: {exc}")

