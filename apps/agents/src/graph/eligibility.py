from __future__ import annotations

import logging
from typing import Any

from ..config import Settings
from ..tools.celo import CeloToolbox
from ..tools.farcaster import FarcasterToolbox

logger = logging.getLogger(__name__)


class EligibilityAgent:
    """Valida participación on-chain y filtros sociales."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.farcaster = FarcasterToolbox(
            base_url=settings.farcaster_hub_api,
            api_token=settings.farcaster_api_token,
            neynar_key=settings.neynar_api_key,
        )
        self.celo_tool = CeloToolbox(rpc_url=settings.celo_rpc_url, private_key=settings.celo_private_key)

    async def handle(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evalúa usuarios analizando su participación en tendencias globales."""

        campaign_id = f"{context.get('frame_id', 'global')}-loot"
        trend_score = context.get("trend_score", 0.0)
        cast_hash = context.get("cast_hash")
        topic_tags = context.get("topic_tags", [])

        manual_target = context.get("target_address")
        allow_manual = bool(self.settings.allow_manual_target and manual_target)

        rankings: list[dict[str, Any]] = []

        # Analizar participación en la tendencia global
        if cast_hash:
            participants = await self.farcaster.fetch_cast_engagement(cast_hash, limit=100)
            
            for participant in participants:
                try:
                    checksum = self.celo_tool.checksum(participant["custody_address"])
                    user_fid = participant.get("fid")
                except (ValueError, KeyError):
                    continue

                # Analizar participación detallada del usuario en esta tendencia
                participation_data = await self.farcaster.analyze_user_participation_in_trend(
                    user_fid=user_fid,
                    cast_hash=cast_hash,
                    topic_tags=topic_tags,
                )

                # Calcular score usando ponderaciones configuradas
                score = self._score_user_advanced(
                    participant=participant,
                    trend_score=trend_score,
                    participation_data=participation_data,
                )

                rankings.append(
                    {
                        "fid": user_fid,
                        "username": participant.get("username"),
                        "address": checksum,
                        "score": score,
                        "reasons": participant.get("reasons", []),
                        "follower_count": participant.get("follower_count", 0),
                        "power_badge": participant.get("power_badge", False),
                        "participation": participation_data,
                    }
                )

        fallback_manual = manual_target and (allow_manual or not rankings)
        if fallback_manual:
            try:
                manual_address = self.celo_tool.checksum(manual_target)  # type: ignore[arg-type]
            except ValueError:
                logger.warning("Dirección manual inválida: %s", manual_target)
            else:
                rankings.append(
                    {
                        "fid": None,
                        "username": "manual_override",
                        "address": manual_address,
                        "score": max(trend_score * 100, 50.0),
                        "reasons": ["manual"],
                        "follower_count": 0,
                        "power_badge": False,
                    }
                )

        rankings.sort(key=lambda user: user["score"], reverse=True)
        shortlisted: list[dict[str, Any]] = []

        for candidate in rankings:
            if len(shortlisted) >= self.settings.max_reward_recipients:
                break

            try:
                can_claim = self.celo_tool.can_claim(
                    registry_address=self.settings.registry_address,
                    campaign_id=campaign_id,
                    participant=candidate["address"],
                )
            except Exception as exc:  # noqa: BLE001
                error_str = str(exc)
                # Si la campaña no está configurada (error 0x050aad92), intentar con demo-campaign
                if "0x050aad92" in error_str or "CampaignNotConfigured" in error_str:
                    if campaign_id != "demo-campaign":
                        logger.warning(
                            "Campaña %s no configurada en LootAccessRegistry. "
                            "Verificando con 'demo-campaign' como fallback...",
                            campaign_id
                        )
                        try:
                            can_claim = self.celo_tool.can_claim(
                                registry_address=self.settings.registry_address,
                                campaign_id="demo-campaign",
                                participant=candidate["address"],
                            )
                            # Si funciona con demo-campaign, actualizar el campaign_id para esta ejecución
                            campaign_id = "demo-campaign"
                        except Exception as fallback_exc:  # noqa: BLE001
                            logger.warning(
                                "Error consultando LootAccessRegistry incluso con 'demo-campaign' (asumiendo que puede reclamar): %s",
                                fallback_exc
                            )
                            can_claim = True
                    else:
                        logger.warning(
                            "Error consultando LootAccessRegistry (asumiendo que puede reclamar): %s. "
                            "Registry: %s, Campaign: %s",
                            exc, self.settings.registry_address, campaign_id
                        )
                        can_claim = True
                else:
                    # Otro tipo de error, asumir que puede reclamar para no bloquear el flujo
                    logger.warning(
                        "Error consultando LootAccessRegistry (asumiendo que puede reclamar): %s. "
                        "Registry: %s, Campaign: %s, Participant: %s",
                        exc, self.settings.registry_address, campaign_id, candidate["address"]
                    )
                    can_claim = True

            if not can_claim:
                continue

            shortlisted.append(candidate)

        recipients = [entry["address"] for entry in shortlisted]

        logger.info(
            "Elegibilidad: %s candidatos -> %s seleccionados (score trend=%.2f)",
            len(rankings),
            len(shortlisted),
            trend_score,
        )

        return {
            "campaign_id": campaign_id,
            "recipients": recipients,
            "rankings": shortlisted,
            "metadata": {
                "channel_id": context.get("channel_id"),
                "trend_score": trend_score,
                "ai_analysis": context.get("ai_analysis"),
                "topic_tags": context.get("topic_tags"),
                "cast_hash": cast_hash,
                "reward_type": context.get("reward_type"),
            },
        }

    def _score_user_advanced(
        self,
        participant: dict[str, Any],
        trend_score: float,
        participation_data: dict[str, Any],
    ) -> float:
        """Calcula score usando ponderaciones configuradas y análisis de participación."""
        
        # 1. Componente de trend_score (40% por defecto)
        trend_component = trend_score * 100 * self.settings.weight_trend_score

        # 2. Componente de followers (20% por defecto)
        follower_count = participant.get("follower_count", 0)
        # Normalizar: 1000 followers = 20 puntos máximos
        follower_score_raw = min(follower_count / 50, 20)  # 1000 followers = 20 puntos
        follower_component = follower_score_raw * self.settings.weight_follower_count * 5

        # 3. Componente de power badge (15% por defecto)
        badge_component = 0.0
        if participant.get("power_badge"):
            badge_component = 15.0 * self.settings.weight_power_badge

        # 4. Componente de engagement (25% por defecto)
        # Incluye participación directa + casts relacionados sobre el tema
        total_engagement = participation_data.get("total_engagement", 0.0)
        # Normalizar engagement: máximo 25 puntos
        engagement_normalized = min(total_engagement / 10, 25)  # 10 engagement = 25 puntos
        engagement_component = engagement_normalized * self.settings.weight_engagement

        # Calcular total
        total = trend_component + follower_component + badge_component + engagement_component
        
        # Asegurar que está en rango 0-100
        return round(min(max(total, 0.0), 100.0), 2)
