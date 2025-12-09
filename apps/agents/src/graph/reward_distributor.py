from __future__ import annotations

import logging
from typing import Any

from ..config import Settings
from ..stores.leaderboard import LeaderboardStore
from ..tools.celo import CeloToolbox
from ..tools.minipay import MiniPayToolbox

logger = logging.getLogger(__name__)


class RewardDistributorAgent:
    """Coordina pagos MiniPay y minteo de cNFTs."""

    def __init__(self, settings: Settings, leaderboard: LeaderboardStore) -> None:
        self.settings = settings
        self.leaderboard = leaderboard
        self.celo_tool = CeloToolbox(
            rpc_url=settings.celo_rpc_url,
            private_key=settings.celo_private_key,
        )
        self.minipay_tool = (
            MiniPayToolbox(
                base_url=settings.minipay_tool_url,
                project_id=settings.minipay_project_id,
                project_secret=settings.minipay_project_secret,
            )
            if settings.minipay_project_id and settings.minipay_project_secret
            else None
        )

    async def handle(self, eligibility: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta la distribución de recompensas on-chain."""
        self.last_mint_error = None


        recipients = eligibility.get("recipients", [])
        campaign_id = eligibility.get("campaign_id", "demo-campaign")
        rankings = eligibility.get("rankings", [])
        metadata = eligibility.get("metadata", {})
        
        # Configurar campaña automáticamente si no es "demo-campaign"
        # En producción, el agente debe ser owner para poder configurar campañas dinámicamente
        if campaign_id != "demo-campaign":
            try:
                logger.info("Configurando campaña real automáticamente: %s", campaign_id)
                
                # 1. Configurar en LootAccessRegistry
                try:
                    self.celo_tool.configure_campaign_registry(
                        registry_address=self.settings.registry_address,
                        campaign_id=campaign_id,
                        cooldown_seconds=86400,  # 1 día
                    )
                except Exception as reg_exc:  # noqa: BLE001
                    error_str = str(reg_exc)
                    # Si la campaña ya existe, continuar (no es un error fatal)
                    if "replacement transaction underpriced" in error_str.lower():
                        logger.warning("Transacción pendiente detectada para Registry, continuando...")
                    else:
                        logger.warning("Error configurando Registry (puede que ya exista): %s", reg_exc)
                
                # 2. Configurar en LootBoxMinter
                try:
                    self.celo_tool.configure_campaign_minter(
                        minter_address=self.settings.minter_address,
                        campaign_id=campaign_id,
                        base_uri=self.settings.reward_metadata_uri or "ipfs://QmExample/",
                    )
                except Exception as minter_exc:  # noqa: BLE001
                    error_str = str(minter_exc)
                    if "replacement transaction underpriced" in error_str.lower():
                        logger.warning("Transacción pendiente detectada para Minter, continuando...")
                    else:
                        logger.warning("Error configurando Minter (puede que ya exista): %s", minter_exc)
                
                # 3. Inicializar en LootBoxVault (solo si se va a usar para cUSD)
                # Nota: Esto requiere que el vault tenga fondos depositados después
                try:
                    reward_amount_wei = int(self.settings.minipay_reward_amount * 1e18)
                    self.celo_tool.initialize_campaign_vault(
                        vault_address=self.settings.lootbox_vault_address,
                        campaign_id=campaign_id,
                        token_address=self.settings.cusd_address,
                        reward_per_recipient=reward_amount_wei,
                    )
                    logger.info("Campaña %s inicializada en LootBoxVault", campaign_id)
                except Exception as vault_exc:  # noqa: BLE001
                    # Si falla, la campaña puede seguir funcionando para NFT y XP
                    # Solo fallará si intenta distribuir cUSD desde el vault
                    error_str = str(vault_exc)
                    error_repr = repr(vault_exc)
                    
                    # Detectar diferentes tipos de errores
                    if "replacement transaction underpriced" in error_str.lower() or "nonce too low" in error_str.lower():
                        logger.debug("Transacción pendiente detectada para Vault, continuando...")
                    elif (
                        "already initialized" in error_str.lower() or 
                        "0xb4fa3fb3" in error_str or 
                        "0xb4fa3fb3" in error_repr or
                        "CampaignAlreadyInitialized" in error_str or
                        "InvalidInput" in error_str
                    ):
                        # La campaña ya está inicializada - esto es normal y esperado
                        logger.debug("Campaña %s ya está inicializada en LootBoxVault (esto es normal)", campaign_id)
                    else:
                        # Otro tipo de error - loguear como warning
                        logger.warning(
                            "No se pudo inicializar campaña en Vault (puede que ya esté inicializada): %s",
                            vault_exc
                        )
                
                logger.info("✅ Campaña %s configurada (o ya existía)", campaign_id)
            except Exception as exc:  # noqa: BLE001
                # Si falla completamente, usar demo-campaign como fallback
                logger.error(
                    "Error crítico configurando la campaña %s: %s",
                    campaign_id, exc
                )
                logger.warning("Usando 'demo-campaign' como fallback")
                campaign_id = "demo-campaign"
        
        # Si reward_type viene del request, usarlo; si no, determinar automáticamente según score
        requested_reward_type = (
            metadata.get("reward_type")
            or eligibility.get("reward_type")
        )
        
        if requested_reward_type:
            # Normalizar reward_type si fue proporcionado manualmente
            reward_type = requested_reward_type.lower()
            if reward_type in {"token", "cusd", "minipay"}:
                reward_type = "cusd"
            elif reward_type in {"xp", "reputation"}:
                reward_type = "xp"
            elif reward_type == "analysis":
                logger.info("Modo análisis solicitado. Saltando distribución.")
                return {"mode": "analysis_only", "tx_hash": None, "campaign_id": campaign_id, "reward_type": "analysis"}
            else:
                reward_type = "nft"
        else:
            # Determinar automáticamente según score (sistema de tiers dinámico)
            reward_type = None  # Se asignará por usuario según su score
        
        if not recipients:
            return {"mode": "noop", "tx_hash": None, "campaign_id": campaign_id}

        # Validaciones de seguridad: verificar duplicados y límites
        unique_addresses = set()
        for recipient in recipients:
            if recipient in unique_addresses:
                logger.warning("Dirección duplicada detectada: %s. Ignorando duplicado.", recipient)
                continue
            unique_addresses.add(recipient)
        
        # Aplicar límites de seguridad
        max_recipients = min(self.settings.max_reward_recipients, 50)  # Límite máximo de 50 por batch
        if len(unique_addresses) > max_recipients:
            logger.warning(
                "Número de recipients (%d) excede el límite (%d). Limitando a los primeros %d.",
                len(unique_addresses), max_recipients, max_recipients
            )
            recipients = list(unique_addresses)[:max_recipients]
        else:
            recipients = list(unique_addresses)

        minted: dict[str, str] = {}
        micropayments: dict[str, str] = {}
        xp_awards: dict[str, str] = {}
        
        # Si reward_type no fue determinado, asignar por usuario según score (tiers)
        if reward_type is None:
            # Distribuir recompensas según tiers dinámicos
            for entry in rankings:
                address = entry["address"]
                user_score = entry.get("score", 0.0)
                
                if user_score >= self.settings.tier_nft_threshold:
                    # Tier 1: NFT para scores altos
                    try:
                        logger.info("Minteando NFT (tier 1) para %s (score: %.2f)...", address, user_score)
                        tx_hash = self.celo_tool.mint_nft(
                            minter_address=self.settings.minter_address,
                            campaign_id=campaign_id,
                            recipient=address,
                            metadata_uri=metadata.get("metadata_uri") or self.settings.reward_metadata_uri,
                        )
                        minted[address] = tx_hash
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fallo minteando NFT: %s", exc)
                
                elif user_score >= self.settings.tier_cusd_threshold:
                    # Priorizar distribución vía contrato como solicitó el usuario
                    try:
                        logger.info("Enviando cUSD via contrato (LootBoxVault) a %s (score: %.2f)...", address, user_score)
                        tx_hash = self.celo_tool.distribute_cusd(
                            vault_address=self.settings.lootbox_vault_address,
                            campaign_id=campaign_id,
                            recipients=[address],
                        )
                        micropayments[address] = tx_hash
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fallo distribuyendo cUSD via contrato: %s", exc)
                        
                        # Fallback opcional a MiniPay Tool
                        if self.settings.minipay_tool_url:
                            try:
                                logger.info("Intentando fallback a MiniPay Tool API...")
                                resp = await self.minipay.send_micropayment(
                                    recipient=address,
                                    amount=self.settings.cusd_reward_amount,
                                    note=f"Premio {campaign_id}",
                                )
                                micropayments[address] = resp.get("tx_hash") or resp.get("id") or "micropayment"
                            except Exception as exc2:
                                logger.error("Fallo fallback MiniPay Tool: %s", exc2)
                
                else:
                    # Tier 3: XP para scores bajos pero elegibles
                    try:
                        logger.info("Otorgando XP (tier 3) a %s (score: %.2f)...", address, user_score)
                        tx_hash = self.celo_tool.grant_xp(
                            registry_address=self.settings.registry_address,
                            campaign_id=campaign_id,
                            participant=address,
                            amount=self.settings.xp_reward_amount,
                        )
                        xp_awards[address] = tx_hash
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fallo otorgando XP: %s", exc)
            
            # Determinar modo principal basado en qué tipo de recompensa se dio más
            if minted:
                reward_type = "nft"
            elif micropayments:
                reward_type = "cusd"
            elif xp_awards:
                reward_type = "xp"
            else:
                reward_type = "noop"
        
        elif reward_type == "xp":
            for address in recipients:
                try:
                    logger.info("Otorgando XP a %s...", address)
                    tx_hash = self.celo_tool.grant_xp(
                        registry_address=self.settings.registry_address,
                        campaign_id=campaign_id,
                        participant=address,
                        amount=self.settings.xp_reward_amount,
                    )
                    xp_awards[address] = tx_hash
                except Exception as exc:  # noqa: BLE001
                    logger.error("Fallo otorgando XP: %s", exc)
        elif reward_type == "cusd":
            if self.minipay_tool:
                # Opción 1: Usar MiniPay Tool API (si está configurada)
                for address in recipients:
                    try:
                        logger.info("Enviando MiniPay Tool API a %s...", address)
                        resp = await self.minipay_tool.send_micropayment(
                            recipient=address,
                            amount=self.settings.minipay_reward_amount,
                            note=f"Premio {campaign_id}",
                        )
                        micropayments[address] = resp.get("tx_hash") or resp.get("id") or "micropayment"
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fallo en micropago MiniPay Tool: %s", exc)
            else:
                # Opción 2: Usar contrato LootBoxVault directamente (fallback)
                # Nota: Esto requiere que la campaña esté inicializada en el vault
                # Si falla, intentamos con "demo-campaign" que ya está configurada
                try:
                    logger.info("Usando LootBoxVault para distribuir cUSD (campaña: %s)...", campaign_id)
                    tx_hash = self.celo_tool.distribute_cusd(
                        vault_address=self.settings.lootbox_vault_address,
                        campaign_id=campaign_id,
                        recipients=recipients,
                    )
                    # Asignamos el mismo tx_hash a todos los recipients (es una transacción batch)
                    for address in recipients:
                        micropayments[address] = tx_hash
                except Exception as exc:  # noqa: BLE001
                    error_str = str(exc)
                    # Si la campaña no está inicializada, intentar con demo-campaign
                    if "0x477a3e50" in error_str or "InvalidCampaign" in error_str or "CampaignInactive" in error_str:
                        if campaign_id != "demo-campaign":
                            logger.warning(
                                "Campaña %s no inicializada en LootBoxVault. "
                                "Intentando con 'demo-campaign' como fallback...",
                                campaign_id
                            )
                            try:
                                tx_hash = self.celo_tool.distribute_cusd(
                                    vault_address=self.settings.lootbox_vault_address,
                                    campaign_id="demo-campaign",
                                    recipients=recipients,
                                )
                                for address in recipients:
                                    micropayments[address] = tx_hash
                                logger.info("cUSD distribuido exitosamente usando 'demo-campaign'")
                            except Exception as fallback_exc:  # noqa: BLE001
                                logger.error(
                                    "Fallo distribuyendo cUSD incluso con 'demo-campaign': %s. "
                                    "Verifica que la campaña esté inicializada en LootBoxVault.",
                                    fallback_exc
                                )
                        else:
                            logger.error(
                                "Fallo distribuyendo cUSD desde contrato: %s. "
                                "Verifica que 'demo-campaign' esté inicializada en LootBoxVault.",
                                exc
                            )
                    else:
                        logger.error("Fallo distribuyendo cUSD desde contrato: %s", exc)
        else:
            onchain_targets = recipients[: self.settings.max_onchain_rewards]
            
            # Inicializar generador de arte
            from ..tools.art_generator import ArtGenerator
            art_gen = ArtGenerator(self.settings)
            
            for address in onchain_targets:
                try:
                    logger.info("Generando arte AI y minteando Loot Box NFT para %s...", address)
                    
                    # 1. Generar Metadata con AI
                    # Buscar info del usuario para personalizar
                    user_info = next((r for r in rankings if r["address"] == address), {})
                    username = user_info.get("username", "Unknown")
                    # Usar el texto de la tendencia o un default
                    cast_text = metadata.get("source_text") or f"Reward for {username}"
                    
                    card_meta = await art_gen.generate_card_metadata(cast_text, username)
                    
                    # 2. Generar Imagen
                    art_image = art_gen.generate_image(card_meta.get("prompt", "Abstract art"))
                    
                    # 3. Componer Carta
                    card_data_uri = art_gen.compose_card(art_image, card_meta)
                    
                    # 4. Construir Metadata JSON final
                    nft_metadata = {
                        "name": card_meta.get("title"),
                        "description": card_meta.get("description"),
                        "image": card_data_uri, # Data URI directo (nota: puede ser largo para on-chain, idealmente IPFS)
                        "attributes": [
                            {"trait_type": "Rarity", "value": card_meta.get("rarity")},
                            {"trait_type": "Type", "value": card_meta.get("type")},
                            {"trait_type": "Artist", "value": "Gemini AI"},
                        ]
                    }
                    
                    # Codificar metadata a data URI para pasar al contrato
                    import json
                    import base64
                    meta_json = json.dumps(nft_metadata)
                    meta_b64 = base64.b64encode(meta_json.encode()).decode()
                    token_uri = f"data:application/json;base64,{meta_b64}"
                    
                    tx_hash = self.celo_tool.mint_nft(
                        minter_address=self.settings.minter_address,
                        campaign_id=campaign_id,
                        recipient=address,
                        metadata_uri=token_uri, # Usar dynamic URI
                    )
                    minted[address] = tx_hash
                except Exception as exc:  # noqa: BLE001
                    logger.error("Fallo al generar/mintear NFT: %s", exc)
                    self.last_mint_error = str(exc)

            extra_targets = recipients[self.settings.max_onchain_rewards :]
            if self.minipay_tool and extra_targets:
                for address in extra_targets:
                    try:
                        logger.info("Enviando micropago MiniPay a %s...", address)
                        resp = await self.minipay_tool.send_micropayment(
                            recipient=address,
                            amount=self.settings.minipay_reward_amount,
                            note=f"Premio {campaign_id}",
                        )
                        micropayments[address] = resp.get("tx_hash") or resp.get("id") or "micropayment"
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fallo en micropago MiniPay: %s", exc)

        self._record_leaderboard(rankings, minted, micropayments, xp_awards, campaign_id, metadata, reward_type)

        primary_tx = (
            next(iter(minted.values()), None)
            or next(iter(micropayments.values()), None)
            or next(iter(xp_awards.values()), None)
        )
        if reward_type == "xp":
            mode = "xp_granted" if xp_awards else "failed"
        elif reward_type == "cusd":
            mode = "micropayments" if micropayments else "failed"
        else:
            mode = "nft_minted" if minted else "failed"

        return {
            "mode": mode,
            "tx_hash": primary_tx,
            "recipients": recipients,
            "campaign_id": campaign_id,
            "minted": minted,
            "micropayments": micropayments,
            "xp_awards": xp_awards,
            "reward_type": reward_type,
            "error": self.last_mint_error if hasattr(self, "last_mint_error") else None,
        }

    def _record_leaderboard(
        self,
        rankings: list[dict[str, Any]],
        minted: dict[str, str],
        micropayments: dict[str, str],
        xp_awards: dict[str, str],
        campaign_id: str,
        metadata: dict[str, Any],
        reward_type: str,
    ) -> None:
        """Registra cada ganador en el leaderboard con su reward_type específico."""
        for entry in rankings:
            address = entry["address"]
            tx_hash = None
            entry_reward_type = reward_type  # Default al tipo general
            
            # Determinar reward_type específico de este usuario
            if address in minted:
                tx_hash = minted[address]
                entry_reward_type = "nft"
            elif address in micropayments:
                tx_hash = micropayments[address]
                entry_reward_type = "cusd"
            elif address in xp_awards:
                tx_hash = xp_awards[address]
                entry_reward_type = "xp"
            else:
                # Si no recibió recompensa, no lo registramos
                continue

            self.leaderboard.record(
                {
                    "username": entry.get("username"),
                    "address": address,
                    "fid": entry.get("fid"),
                    "score": entry.get("score"),
                    "reward_type": entry_reward_type,
                    "tx_hash": tx_hash,
                    "campaign_id": campaign_id,
                    "topic_tags": metadata.get("topic_tags", []),
                    "ai_analysis": metadata.get("ai_analysis"),
                    "participation": entry.get("participation", {}),
                }
            )
