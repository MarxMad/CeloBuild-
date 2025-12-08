"""
Scheduler automático para ejecutar el pipeline de agentes cada 30 minutos.
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings
from .graph.supervisor import SupervisorOrchestrator

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
supervisor: SupervisorOrchestrator | None = None


async def run_automatic_scan() -> None:
    """Ejecuta el pipeline completo de agentes buscando tendencias automáticamente."""
    if not supervisor:
        logger.warning("Supervisor no inicializado, saltando scan automático")
        return

    logger.info("🔄 Iniciando scan automático de tendencias...")
    try:
        # Ejecutamos sin target_address específico para buscar tendencias globales
        payload = {
            "frame_id": "",  # Vacío para buscar tendencias globales
            "channel_id": "global",
            "trend_score": 0.0,  # Se calculará automáticamente
        }

        result = await supervisor.run(payload)
        logger.info(
            "✅ Scan automático completado: %s (tx: %s)",
            result.summary[:100],
            result.tx_hash or "N/A",
        )
    except Exception as exc:
        logger.error("❌ Error en scan automático: %s", exc, exc_info=True)


@asynccontextmanager
async def lifespan(app):
    """Lifecycle manager para FastAPI que inicia/detiene el scheduler."""
    global supervisor

    # Inicializar supervisor
    supervisor = SupervisorOrchestrator.from_settings(settings)

    # Verificar si estamos en un entorno serverless (Vercel)
    # En serverless, el scheduler no funciona porque las funciones son efímeras
    is_serverless = os.getenv("VERCEL") is not None or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
    
    if is_serverless:
        logger.info("⚠️ Entorno serverless detectado - scheduler deshabilitado")
        logger.info("💡 Para ejecución automática, usa Vercel Cron Jobs o despliega en Railway/Render")
    else:
        try:
            # Configurar scheduler para ejecutar cada 30 minutos
            scheduler.add_job(
                run_automatic_scan,
                trigger=IntervalTrigger(minutes=30),
                id="auto_scan_trends",
                name="Scan automático de tendencias Farcaster",
                replace_existing=True,
            )

            # Ejecutar un scan inmediato al iniciar (opcional)
            if settings.auto_scan_on_startup:
                logger.info("🚀 Ejecutando scan inicial...")
                asyncio.create_task(run_automatic_scan())

            # Iniciar scheduler
            scheduler.start()
            logger.info("⏰ Scheduler iniciado: ejecutando scans cada 30 minutos")
        except Exception as exc:
            logger.warning("⚠️ No se pudo iniciar el scheduler: %s", exc)
            logger.info("💡 El sistema funcionará sin scheduler automático")

    yield

    # Detener scheduler al cerrar (solo si está corriendo)
    if scheduler.running:
        try:
            scheduler.shutdown()
            logger.info("⏹️ Scheduler detenido")
        except Exception as exc:
            logger.warning("Error deteniendo scheduler: %s", exc)

