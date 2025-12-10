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

        # Usar 'demo-campaign' fijo para que todo el XP se acumule en una sola campaña
        # y sea visible en el frontend (que consulta 'demo-campaign' por defecto).
        # En el futuro, esto podría ser dinámico si el frontend soporta múltiples campañas.
        campaign_id = "demo-campaign"
        trend_score = context.get("trend_score", 0.0)
        cast_hash = context.get("cast_hash")
        topic_tags = context.get("topic_tags", [])

        target_address = context.get("target_address")
        allow_manual = bool(self.settings.allow_manual_target and target_address)

        rankings: list[dict[str, Any]] = []

        # PRIORIDAD 1: Si hay target_fid, buscar usuario por FID (más confiable que por address)
        target_fid = context.get("target_fid")
        # Asegurar que target_fid sea un entero si viene como string
        if target_fid is not None:
            try:
                target_fid = int(target_fid)
            except (ValueError, TypeError):
                logger.warning("⚠️ target_fid inválido recibido: %s", target_fid)
                target_fid = None

        if target_fid:
            # Verificar configuración de API Key
            if not self.settings.neynar_api_key:
                logger.error("❌ NEYNAR_API_KEY no configurada en backend")
                return {
                    "recipients": [],
                    "rankings": [],
                    "eligible": False,
                    "reason": "config_error",
                    "message": "Error de configuración del sistema: Falta API Key de Farcaster en el backend.",
                }

            try:
                logger.info("🎯 Analizando usuario específico por FID: %d", target_fid)
                
                # Obtener información del usuario de Farcaster por su FID
                user_info = await self.farcaster.fetch_user_by_fid(target_fid)
                
                if user_info and user_info.get("fid"):
                    user_fid = user_info.get("fid")
                    username = user_info.get("username", "unknown")
                    custody_address = user_info.get("custody_address", "").lower()
                    
                    logger.info("✅ Usuario encontrado en Farcaster por FID: @%s (FID: %d, Custody: %s, Followers: %d)", 
                               username, user_fid, custody_address, user_info.get("follower_count", 0))
                    
                    # Usar la custody_address del usuario para análisis on-chain por defecto
                    recipient_address = user_info.get("custody_address")
                    target_checksum = self.celo_tool.checksum(recipient_address) if recipient_address else None
                    
                    # Si hay target_address (wallet conectada en frontend), PRIORIZARLA para la recompensa
                    # Esto asegura que el usuario reciba el XP en la wallet que está usando
                    if target_address:
                        target_checksum = self.celo_tool.checksum(target_address)
                        logger.info("   Usando target_address (wallet conectada) para recompensa: %s", target_checksum)
                    
                    # Analizar participación del usuario en la tendencia (si hay cast_hash)
                    participation_data = {}
                    engagement_weight = 0.0
                    username = user_info.get("username")
                    
                    # Analizar participación en la tendencia
                    participation_data = await self.farcaster.analyze_user_participation_in_trend(
                        target_fid, cast_hash, topic_tags
                    )
                    
                    engagement_weight = participation_data.get("total_engagement", 0.0)
                    
                    # Calcular score final
                    # Base score (por ser usuario válido) + Engagement
                    score = (trend_score * 100) + (engagement_weight * 10)
                    
                    # Bonus por Power Badge
                    if user_info.get("power_badge"):
                        score *= 1.2
                        
                    rankings.append(
                        {
                            "fid": target_fid,
                            "username": username,
                            "address": target_checksum, # Usar la dirección priorizada (target_address si existe)
                            "score": round(score, 2),
                            "reasons": ["Usuario verificado por FID", f"Engagement: {engagement_weight}"],
                            "follower_count": user_info.get("follower_count", 0),
                            "power_badge": user_info.get("power_badge", False),
                            "participation": participation_data,
                        }
                    )
                    logger.info(
                        "📈 Usuario analizado: @%s - Score: %.2f, Followers: %d, Power Badge: %s, Engagement: %.2f",
                        username,
                        score,
                        user_info.get("follower_count", 0),
                        user_info.get("power_badge", False),
                        engagement_weight
                    )
                else:
                    # Usuario no encontrado por FID - esto no debería pasar si el FID es válido
                    logger.warning("❌ Usuario no encontrado en Farcaster para FID: %d", target_fid)
                    
                    # Modo demo: permitir usuarios sin Farcaster con score reducido
                    if self.settings.demo_mode and target_address:
                        logger.info("🎭 MODO DEMO: Permitiendo usuario sin Farcaster para demostración")
                        target_checksum = self.celo_tool.checksum(target_address)
                        
                        # Crear usuario demo con score reducido
                        demo_score = trend_score * 100 * 0.3  # 30% del score normal
                        rankings.append({
                            "fid": None,
                            "username": f"demo-{target_checksum[:8]}",
                            "address": target_checksum,
                            "score": round(demo_score, 2),
                            "reasons": ["Modo demo: usuario sin Farcaster"],
                            "follower_count": 0,
                            "power_badge": False,
                            "participation": {
                                "directly_participated": False,
                                "related_casts": [],
                                "total_engagement": 0.0,
                            },
                        })
                        logger.info("✅ Usuario demo agregado: %s (score: %.2f)", target_checksum, demo_score)
                    else:
                        return {
                            "recipients": [],
                            "rankings": [],
                            "eligible": False,
                            "reason": "user_not_found",
                            "message": f"Usuario con FID {target_fid} no encontrado en Farcaster. Verifica tu conexión.",
                        }
            except Exception as exc:  # noqa: BLE001
                logger.error("❌ Error analizando usuario por FID %d: %s", target_fid, exc, exc_info=True)
                return {
                    "recipients": [],
                    "rankings": [],
                    "eligible": False,
                    "reason": "api_error",
                    "message": f"Error consultando Farcaster API: {str(exc)}",
                }

        # PRIORIDAD 2: Si hay target_address (y no se encontró por FID), analizar específicamente a ese usuario
        if target_address and not rankings:
            try:
                # Normalizar dirección: usar lowercase para buscar en Farcaster
                # Neynar API requiere lowercase, no checksummed
                target_normalized = target_address.lower().strip()
                target_checksum = self.celo_tool.checksum(target_address)  # Para uso on-chain
                
                logger.info("🎯 Analizando usuario específico que activó recompensa: %s (normalized: %s)", 
                           target_checksum, target_normalized)
                
                # Obtener información del usuario de Farcaster por su wallet address
                # Usar dirección normalizada (lowercase) para buscar en Neynar
                user_info = await self.farcaster.fetch_user_by_address(target_normalized)
                
                if user_info and user_info.get("fid"):
                    user_fid = user_info.get("fid")
                    username = user_info.get("username", "unknown")
                    logger.info("✅ Usuario encontrado en Farcaster: @%s (FID: %s, Followers: %d)", 
                               username, user_fid, user_info.get("follower_count", 0))
                    
                    # Analizar participación del usuario en la tendencia (si hay cast_hash)
                    participation_data = {}
                    engagement_weight = 0.0
                    reasons = []
                    
                    # Buscar el MEJOR cast del usuario sobre el tema
                    best_cast = await self.farcaster.fetch_user_best_cast(user_fid, topic_tags)
                    if best_cast:
                        logger.info("🌟 Mejor cast encontrado: %s (Score: %.2f)", best_cast["hash"], best_cast["engagement_score"])
                        participation_data["best_cast"] = best_cast
                        reasons.append(f"Autor de cast relevante ({int(best_cast['engagement_score'])} pts)")
                    
                    if cast_hash:
                        logger.info("📊 Analizando participación de @%s en cast: %s", username, cast_hash[:16])
                        
                        # Analizar participación detallada
                        trend_participation = await self.farcaster.analyze_user_participation_in_trend(
                            user_fid=user_fid,
                            cast_hash=cast_hash,
                            topic_tags=topic_tags,
                        )
                        participation_data.update(trend_participation)
                        
                        # Verificar si participó directamente en el cast
                        participants = await self.farcaster.fetch_cast_engagement(cast_hash, limit=100)
                        for p in participants:
                            if p.get("fid") == user_fid:
                                engagement_weight = p.get("engagement_weight", 0.0)
                                reasons.extend(p.get("reasons", []))
                                logger.info("  - Participación directa: %s (weight: %.2f)", p.get("reasons", []), engagement_weight)
                                break
                    else:
                        logger.info("⚠️ No hay cast_hash disponible, analizando solo perfil del usuario")
                        # Sin cast_hash, dar score base basado en perfil y best_cast
                        participation_data.update({
                            "directly_participated": False,
                            "related_casts": [],
                            "total_engagement": best_cast["engagement_score"] if best_cast else 0.0,
                        })
                    
                    # Crear objeto participant con la información del usuario
                    participant = {
                        "fid": user_fid,
                        "username": username,
                        "custody_address": target_checksum,
                        "follower_count": user_info.get("follower_count", 0),
                        "power_badge": user_info.get("power_badge", False),
                        "engagement_weight": engagement_weight,
                        "reasons": reasons if reasons else ["user_activated"],
                    }
                    
                    # Calcular score usando ponderaciones configuradas
                    score = self._score_user_advanced(
                        participant=participant,
                        trend_score=trend_score,
                        participation_data=participation_data,
                    )
                    
                    rankings.append(
                        {
                            "fid": user_fid,
                            "username": username,
                            "address": target_checksum,
                            "score": score,
                            "reasons": participant.get("reasons", []),
                            "follower_count": participant.get("follower_count", 0),
                            "power_badge": participant.get("power_badge", False),
                            "participation": participation_data,
                        }
                    )
                    logger.info(
                        "📈 Usuario analizado: @%s - Score: %.2f, Followers: %d, Power Badge: %s, Best Cast: %s",
                        username,
                        score,
                        participant.get("follower_count", 0),
                        participant.get("power_badge", False),
                        bool(best_cast)
                    )
                elif user_info is None:
                    # Usuario no encontrado en Farcaster (user_info es None)
                    logger.warning("❌ Usuario no encontrado en Farcaster para address: %s (normalized: %s)", 
                                 target_checksum, target_normalized)
                    logger.warning("   Esto significa que la wallet no está vinculada a una cuenta de Farcaster")
                    
                    # Modo demo: permitir usuarios sin Farcaster con score reducido
                    if self.settings.demo_mode:
                        logger.info("🎭 MODO DEMO: Permitiendo usuario sin Farcaster para demostración")
                        
                        # Crear usuario demo con score reducido
                        demo_score = trend_score * 100 * 0.3  # 30% del score normal
                        rankings.append({
                            "fid": None,
                            "username": f"demo-{target_checksum[:8]}",
                            "address": target_checksum,
                            "score": round(demo_score, 2),
                            "reasons": ["Modo demo: usuario sin Farcaster"],
                            "follower_count": 0,
                            "power_badge": False,
                            "participation": {
                                "directly_participated": False,
                                "related_casts": [],
                                "total_engagement": 0.0,
                            },
                        })
                        logger.info("✅ Usuario demo agregado: %s (score: %.2f)", target_checksum, demo_score)
                    else:
                        # NO ES ELEGIBLE (modo normal)
                        logger.warning("   NO ES ELEGIBLE para recompensas (solo usuarios de Farcaster)")
                        return {
                            "recipients": [],
                            "rankings": [],
                            "eligible": False,
                            "reason": "user_not_in_farcaster",
                            "message": f"La wallet {target_checksum} no está vinculada a una cuenta de Farcaster. Solo usuarios de Farcaster son elegibles para recompensas.",
                        }
            except ValueError as exc:
                logger.warning("❌ Dirección inválida: %s - %s", target_address, exc)
                # Retornar error de elegibilidad para dirección inválida
                return {
                    "recipients": [],
                    "rankings": [],
                    "eligible": False,
                    "reason": "invalid_address",
                    "message": f"Dirección de wallet inválida: {target_address}. Verifica que sea una dirección Ethereum válida.",
                }
            except Exception as exc:  # noqa: BLE001
                logger.error("❌ Error analizando usuario específico %s: %s", target_address, exc, exc_info=True)
                # En caso de error, retornar como no elegible con mensaje de error
                error_msg = str(exc)
                # Si el error contiene "Not Found" o 404, es porque no se encontró en Farcaster
                if "not found" in error_msg.lower() or "404" in error_msg.lower() or "user_not_in_farcaster" in error_msg.lower():
                    logger.warning("❌ Error 404/Not Found al buscar usuario en Farcaster: %s", error_msg[:200])
                    # Modo demo: permitir usuarios sin Farcaster
                    if self.settings.demo_mode:
                        logger.info("🎭 MODO DEMO: Permitiendo usuario sin Farcaster (error 404) para demostración")
                        target_checksum = self.celo_tool.checksum(target_address)
                        demo_score = trend_score * 100 * 0.3  # 30% del score normal
                        rankings.append({
                            "fid": None,
                            "username": f"demo-{target_checksum[:8]}",
                            "address": target_checksum,
                            "score": round(demo_score, 2),
                            "reasons": ["Modo demo: usuario sin Farcaster"],
                            "follower_count": 0,
                            "power_badge": False,
                            "participation": {
                                "directly_participated": False,
                                "related_casts": [],
                                "total_engagement": 0.0,
                            },
                        })
                        logger.info("✅ Usuario demo agregado: %s (score: %.2f)", target_checksum, demo_score)
                    else:
                        return {
                            "recipients": [],
                            "rankings": [],
                            "eligible": False,
                            "reason": "user_not_in_farcaster",
                            "message": (
                                f"La wallet {target_checksum if 'target_checksum' in locals() else target_address} no está vinculada a una cuenta de Farcaster (Custody Address).\n"
                                "💡 Si usas una 'Verified Address', asegúrate de abrir la app desde un cliente Farcaster para detectar tu FID automáticamente."
                            ),
                        }
                # Para otros errores, retornar mensaje genérico
                return {
                    "recipients": [],
                    "rankings": [],
                    "eligible": False,
                    "reason": "error_analyzing_user",
                    "message": f"Error al analizar usuario: {error_msg[:100]}. Por favor, intenta de nuevo.",
                }

        # PRIORIDAD 2: Si no hay target_address o no se encontró, analizar participantes del cast
        if not rankings and cast_hash:
            logger.info("Analizando participantes del cast: %s", cast_hash)
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
        
        # Bonus por MEJOR CAST (si existe)
        best_cast = participation_data.get("best_cast")
        if best_cast:
            # Si tiene un cast popular (ej. >10 likes), dar bonus masivo
            best_cast_score = best_cast.get("engagement_score", 0)
            if best_cast_score > 10:
                total_engagement += 50  # Bonus masivo para asegurar NFT
            else:
                total_engagement += best_cast_score * 2
        
        # Normalizar engagement: máximo 40 puntos (aumentado para dar más peso al contenido)
        engagement_normalized = min(total_engagement / 5, 40)
        engagement_component = engagement_normalized * self.settings.weight_engagement

        # Calcular total
        total = trend_component + follower_component + badge_component + engagement_component
        
        # Asegurar que está en rango 0-100
        return round(min(max(total, 0.0), 100.0), 2)
