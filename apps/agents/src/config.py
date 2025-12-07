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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()



