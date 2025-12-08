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
except Exception as e:
    # Si falla, crear una app básica para debugging
    from fastapi import FastAPI
    import logging
    
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Error importando app: {e}", exc_info=True)
    
    # Crear app mínima para debugging
    app = FastAPI(title="Lootbox Multi-Agent Service (Error Mode)")
    
    @app.get("/healthz")
    async def healthcheck():
        return {"status": "error", "message": str(e)}
    
    @app.get("/")
    async def root():
        return {"error": "Failed to initialize app", "details": str(e)}

# Exportar app para Vercel
__all__ = ["app"]
