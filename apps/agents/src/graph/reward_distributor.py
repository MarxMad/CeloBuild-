from __future__ import annotations

import logging
from typing import Any

from ..config import Settings
from ..tools.celo import CeloToolbox

logger = logging.getLogger(__name__)


class RewardDistributorAgent:
    """Coordina pagos MiniPay y minteo de cNFTs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.celo_tool = CeloToolbox(
            rpc_url=settings.celo_rpc_url,
            private_key=settings.celo_private_key
        )

    async def handle(self, eligibility: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta la distribución de recompensas on-chain."""

        recipients = eligibility.get("recipients", [])
        campaign_id = eligibility.get("campaign_id", "demo-campaign")
        
        if not recipients:
            return {"mode": "noop", "tx_hash": None}

        tx_hashes = []
        
        # Por ahora, para no gastar todo el gas en demos masivas, 
        # solo recompensamos al primer usuario de la lista si hay varios.
        target_user = recipients[0]
        
        try:
            logger.info(f"Minteando Loot Box NFT para {target_user} en campaña {campaign_id}...")
            tx_hash = self.celo_tool.mint_nft(
                minter_address=self.settings.minter_address,
                campaign_id=campaign_id,
                recipient=target_user
            )
            tx_hashes.append(tx_hash)
            mode = "nft_minted"
        except Exception as e:
            logger.error(f"Fallo al mintear NFT: {e}")
            mode = "failed"
            tx_hashes.append(str(e))

        return {
            "mode": mode,
            "tx_hash": tx_hashes[0] if tx_hashes else None,
            "recipients": recipients,
            "campaign_id": campaign_id,
        }
