"""
Entry point para Vercel Serverless Functions.
Este archivo expone la aplicación FastAPI para Vercel.
"""
import os
import sys
import logging

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Asegurar que el path incluye el directorio raíz
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

logger.info(f"Python path: {sys.path}")
logger.info(f"Current directory: {current_dir}")
logger.info(f"Parent directory: {parent_dir}")

# Deshabilitar scheduler en Vercel (serverless)
os.environ["VERCEL"] = "1"

_app_loaded = False
_app_error = None
app = None

try:
    logger.info("Intentando importar src.main...")
    from src.main import app
    _app_loaded = True
    logger.info("✅ App importada correctamente")
except Exception as e:
    import traceback
    _app_loaded = False
    _app_error = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }
    logger.error(f"❌ Error importando app: {e}", exc_info=True)
    
    # Crear app mínima para debugging
    from fastapi import FastAPI
    app = FastAPI(title="Lootbox Multi-Agent Service (Error Mode)")
    
    @app.get("/healthz")
    async def healthcheck():
        return {
            "status": "error",
            "message": "Failed to initialize app",
            "error": _app_error["error"],
            "type": _app_error["type"],
            "traceback": _app_error["traceback"],
            "python_path": sys.path,
            "current_dir": current_dir,
            "parent_dir": parent_dir
        }
    
    @app.get("/")
    async def root():
        return {
            "error": "Failed to initialize app",
            "details": _app_error,
            "python_path": sys.path
        }
    
    @app.get("/debug")
    async def debug():
        return {
            "app_loaded": _app_loaded,
            "error": _app_error,
            "python_path": sys.path,
            "current_dir": current_dir,
            "parent_dir": parent_dir,
            "env_vars": {
                "GOOGLE_API_KEY": "SET" if os.getenv("GOOGLE_API_KEY") else "MISSING",
                "TAVILY_API_KEY": "SET" if os.getenv("TAVILY_API_KEY") else "MISSING",
                "CELO_RPC_URL": "SET" if os.getenv("CELO_RPC_URL") else "MISSING",
                "CELO_PRIVATE_KEY": "SET" if os.getenv("CELO_PRIVATE_KEY") else "MISSING",
                "LOOTBOX_VAULT_ADDRESS": "SET" if os.getenv("LOOTBOX_VAULT_ADDRESS") else "MISSING",
                "REGISTRY_ADDRESS": "SET" if os.getenv("REGISTRY_ADDRESS") else "MISSING",
                "MINTER_ADDRESS": "SET" if os.getenv("MINTER_ADDRESS") else "MISSING",
            }
        }

# Asegurar que siempre hay una app
if app is None:
    from fastapi import FastAPI
    app = FastAPI(title="Lootbox Multi-Agent Service (Fallback)")
    
    @app.get("/healthz")
    async def healthcheck():
        return {
            "status": "error",
            "message": "App is None - critical initialization error"
        }

# Exportar app para Vercel
__all__ = ["app"]
