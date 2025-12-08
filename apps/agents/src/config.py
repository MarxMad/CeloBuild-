from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configura claves y endpoints necesarios para los agentes."""

    google_api_key: str
    tavily_api_key: str
    celo_rpc_url: str
    celo_explorer_api: str | None = None
    farcaster_hub_api: str = "https://api.warpcast.com"
    farcaster_api_token: str | None = None
    neynar_api_key: str | None = None
    minipay_tool_url: str = "https://api.minipay.celo.org"
    minipay_project_id: str | None = None
    minipay_project_secret: str | None = None
    agent_webhook_secret: str | None = None
    minipay_reward_amount: float = 0.15
    xp_reward_amount: int = 50
    max_recent_casts: int = 8
    min_trend_score: float = 0.35
    max_reward_recipients: int = 5
    max_onchain_rewards: int = 2
    leaderboard_max_entries: int = 100
    allow_manual_target: bool = False
    reward_metadata_uri: str = "ipfs://QmExample"
    default_reward_type: str = "nft"
    
    # Scheduler
    auto_scan_on_startup: bool = True
    auto_scan_interval_minutes: int = 30
    
    # Sistema de Tiers y Ponderaciones
    tier_nft_threshold: float = 85.0  # Score mínimo para NFT
    tier_cusd_threshold: float = 60.0  # Score mínimo para cUSD
    # XP se otorga a todos los que pasan el umbral mínimo
    
    # Ponderaciones para calcular user_score
    weight_trend_score: float = 0.40  # 40% del score viene del trend_score
    weight_follower_count: float = 0.20  # 20% de followers
    weight_power_badge: float = 0.15  # 15% bonus por power badge
    weight_engagement: float = 0.25  # 25% de engagement en el cast específico
    
    # Contracts
    lootbox_vault_address: str
    registry_address: str
    minter_address: str
    celo_private_key: str
    # Token addresses (Celo Sepolia)
    cusd_address: str = "0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1"  # cUSD en Sepolia

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Inicializar settings con manejo de errores robusto
import os
import logging

logger = logging.getLogger(__name__)

try:
    settings = Settings()
    logger.info("✅ Settings cargados correctamente")
except Exception as e:
    logger.warning("⚠️ Error cargando configuración completa: %s", e)
    logger.info("🔄 Intentando cargar con valores por defecto...")
    
    # Crear settings con valores por defecto para que el health check funcione
    # Esto permite que el backend arranque incluso si faltan algunas variables
    try:
        settings = Settings(
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            celo_rpc_url=os.getenv("CELO_RPC_URL", ""),
            lootbox_vault_address=os.getenv("LOOTBOX_VAULT_ADDRESS", ""),
            registry_address=os.getenv("REGISTRY_ADDRESS", ""),
            minter_address=os.getenv("MINTER_ADDRESS", ""),
            celo_private_key=os.getenv("CELO_PRIVATE_KEY", ""),
            neynar_api_key=os.getenv("NEYNAR_API_KEY", ""),
        )
        logger.info("✅ Settings cargados con valores por defecto")
    except Exception as e2:
        logger.error("❌ Error crítico cargando settings: %s", e2, exc_info=True)
        # Crear un objeto settings mínimo para evitar que el import falle
        # Esto permite que el health check al menos funcione
        from types import SimpleNamespace
        settings = SimpleNamespace(
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            celo_rpc_url=os.getenv("CELO_RPC_URL", ""),
            lootbox_vault_address=os.getenv("LOOTBOX_VAULT_ADDRESS", ""),
            registry_address=os.getenv("REGISTRY_ADDRESS", ""),
            minter_address=os.getenv("MINTER_ADDRESS", ""),
            celo_private_key=os.getenv("CELO_PRIVATE_KEY", ""),
            neynar_api_key=os.getenv("NEYNAR_API_KEY", ""),
            min_trend_score=0.35,
            max_reward_recipients=5,
            allow_manual_target=False,
        )
        logger.warning("⚠️ Usando settings mínimos - algunas funciones pueden no funcionar")



