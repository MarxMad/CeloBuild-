from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configura claves y endpoints necesarios para los agentes."""

    google_api_key: str
    tavily_api_key: str
    celo_rpc_url: str
    celo_explorer_api: str | None = None
    farcaster_hub_api: str
    farcaster_api_token: str | None = None
    neynar_api_key: str | None = None
    minipay_tool_url: str
    minipay_project_id: str
    agent_webhook_secret: str
    
    # Contracts
    lootbox_vault_address: str
    registry_address: str
    minter_address: str
    celo_private_key: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()


