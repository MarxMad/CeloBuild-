"""
Entry point para Vercel Serverless Functions.
Este archivo expone la aplicación FastAPI para Vercel.
"""
import os
import sys

# Asegurar que el path incluye el directorio raíz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Deshabilitar scheduler en Vercel (serverless)
os.environ["VERCEL"] = "1"

try:
    # Intentar importar la app
    from src.main import app
    _app_loaded = True
    _app_error = None
except Exception as e:
    # Si falla, crear una app básica para debugging
    from fastapi import FastAPI
    import logging
    import traceback
    
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Error importando app: {e}", exc_info=True)
    
    _app_loaded = False
    _app_error = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }
    
    # Crear app mínima para debugging
    app = FastAPI(title="Lootbox Multi-Agent Service (Error Mode)")
    
    @app.get("/healthz")
    async def healthcheck():
        return {
            "status": "error",
            "message": "Failed to initialize app",
            "error": _app_error["error"],
            "type": _app_error["type"],
            "traceback": _app_error["traceback"]
        }
    
    @app.get("/")
    async def root():
        return {
            "error": "Failed to initialize app",
            "details": _app_error
        }

# Exportar app para Vercel
__all__ = ["app"]
