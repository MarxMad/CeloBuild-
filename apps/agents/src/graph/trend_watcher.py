from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Settings
from ..tools.farcaster import FarcasterToolbox

logger = logging.getLogger(__name__)


class TrendWatcherAgent:
    """Consulta señales de Farcaster y construye contexto de campaña usando AI."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.farcaster = FarcasterToolbox(
            base_url=settings.farcaster_hub_api,
            api_token=settings.farcaster_api_token,
            neynar_key=settings.neynar_api_key,
        )
        # LLM se inicializará de forma lazy (solo cuando se necesite)
        # Esto evita errores al iniciar el servidor si el modelo no está disponible
        self.llm = None
        self.llm_initialized = False
        self.google_api_key = settings.google_api_key

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Detecta tendencias o analiza un frame específico si se provee."""
        
        channel_id = payload.get("channel_id") or "global"
        base_context = {
            "target_address": payload.get("target_address"),
            "target_fid": payload.get("target_fid"),
            "channel_id": channel_id,
            "reward_type": payload.get("reward_type") or self.settings.default_reward_type,
        }
        
        frame_id = payload.get("frame_id")
        if frame_id:
            logger.info("Analizando frame específico: %s", frame_id)
            stats = await self.farcaster.fetch_frame_stats(frame_id)
            score = self._calculate_score(stats)
            return {
                **base_context,
                "frame_id": frame_id,
                "trend_score": min(score, 1.0),
                "stats": stats,
                "status": "analyzed",
            }

        # --- ESTRATEGIA DUAL: Viral + Comunitario ---
        # --- ESTRATEGIA MIXTA: Viral + Community + Fresh ---
        # 1. Fetch Viral Trends (High Score Candidates)
        logger.info("Consultando tendencias virales de Neynar (canal=%s)...", channel_id)
        viral_casts = []
        try:
            # Reducir límite a 15 para evitar errores 400 y ahorrar créditos
            viral_casts = await self.farcaster.fetch_trending_feed(
                channel_id=channel_id, 
                limit=15, 
                time_window="24h"
            )
        except Exception as exc:
            logger.warning("⚠️ Error obteniendo trending feed: %s", exc)

        # 2. Fetch Community Targets (Mid Score Candidates)
        target_users = ["oyealmond.base.eth", "celopg", "muchogang", "kmacb.eth", "jesse.xyz"]
        logger.info("Consultando casts de usuarios comunitarios: %s", target_users)
        community_casts = []
        try:
            # Seleccionar 3 usuarios al azar
            import random
            selected_users = random.sample(target_users, min(3, len(target_users)))
            community_casts = await self.farcaster.fetch_casts_from_users(selected_users, limit_per_user=3)
        except Exception as exc:
            logger.warning("⚠️ Error obteniendo community casts: %s", exc)

        # 3. Fetch Recent Casts (Low Score / Fresh Candidates)
        # Always fetch recent to allow "new/low score" discovery
        logger.info("Consultando casts recientes (Fresh/Low score)...")
        recent_casts = []
        try:
            # OPTIMIZATION: Reducir límite de 20 a 10 para ahorrar créditos API
            recent_casts = await self.farcaster.fetch_recent_casts(channel_id=channel_id, limit=10)
        except Exception as exc:
             logger.warning("⚠️ Error obteniendo recent casts: %s", exc)
        
        # Combinar pools
        all_candidates = viral_casts + community_casts + recent_casts
        
        if not all_candidates:
            return {"status": "no_trends_found", **base_context}
            
        # Scoring para unificar criterios
        scored_casts = []
        seen_hashes = set()

        for candidate in all_candidates:
            c_hash = candidate.get("hash")
            if c_hash in seen_hashes:
                continue
            seen_hashes.add(c_hash)

            # Si es targeted, ya tiene flag. Si no, calcular score.
            is_targeted = candidate.get("is_targeted", False)
            candidate_score = self._score_cast(candidate)
            
            # Boost artificial a los targeted
            final_score = candidate_score
            if is_targeted:
                final_score = max(candidate_score, 0.45) 

            scored_casts.append(
                {
                    **candidate,
                    "trend_score": final_score,
                    "is_targeted": is_targeted
                }
            )

        # --- SELECCIÓN POR NIVELES (TIERS) ---
        # Clasificar
        high_tier = [c for c in scored_casts if c["trend_score"] >= 0.7]
        mid_tier = [c for c in scored_casts if 0.3 <= c["trend_score"] < 0.7]
        low_tier = [c for c in scored_casts if c["trend_score"] < 0.3]

        # Ordenar cada tier
        high_tier.sort(key=lambda x: x["trend_score"], reverse=True)
        mid_tier.sort(key=lambda x: x["trend_score"], reverse=True)
        low_tier.sort(key=lambda x: x["trend_score"], reverse=True)

        final_selection = []
        
        # Objetivos: 3 High, 4 Mid, 3 Low = 10 Total
        # High (Virales Top)
        final_selection.extend(high_tier[:3])
        
        # Mid (Comunidad/Viral Medio)
        final_selection.extend(mid_tier[:4])
        
        # Low (Nuevos/Emergentes)
        final_selection.extend(low_tier[:3])

        # Rellenar si faltan (backfill)
        current_count = len(final_selection)
        target_count = 10
        
        if current_count < target_count:
            remaining = target_count - current_count
            # Prioridad para rellenar: Mid -> High -> Low
            backfill_pool = mid_tier[4:] + high_tier[3:] + low_tier[3:]
            final_selection.extend(backfill_pool[:remaining])
            
        # Ordenar selección final por score para visualización coherente (o shuffle si se prefiere mezcla)
        # El usuario pidió "mostrar unos 10 post, entre virales de alto puntaje, bajo puntaje y medio"
        # Ordenar descendente es lo estándar.
        final_selection.sort(key=lambda x: x["trend_score"], reverse=True)

        # Procesar selección final
        detected_trends = []
        for cast in final_selection:
            # No usamos AI summary para rapidez
            topic_tags = self._extract_tags(cast.get("text", ""))
            frame_identifier = "cast-" + (cast.get("hash") or "unknown")[:8]
            
            detected_trends.append({
                "frame_id": frame_identifier,
                "cast_hash": cast.get("hash"),
                "trend_score": round(cast["trend_score"], 3),
                "source_text": cast.get("text"),
                "ai_analysis": cast.get("text", ""), # Direct text
                "ai_enabled": False,
                "topic_tags": topic_tags,
                "channel_id": cast.get("channel_id") or channel_id,
                "author": cast.get("author", {}),
                "is_promoted": cast.get("is_targeted", False) # Flag for UI if needed
            })
            
        logger.info("Retornando %d tendencias (%d virales + %d comunitarias)", 
                   len(detected_trends), 
                   len([t for t in detected_trends if not t.get("is_promoted")]),
                   len([t for t in detected_trends if t.get("is_promoted")]))
        
        # Notificar al usuario si se detectó una tendencia fuerte y hay un target_fid
        top_trend = detected_trends[0] if detected_trends else None
        is_strong_trend = any(t["trend_score"] >= self.settings.min_trend_score for t in detected_trends)
        
        if is_strong_trend and top_trend and payload.get("target_fid"):
            try:
                target_fid = int(payload["target_fid"])
                topic = top_trend.get("topic_tags", ["General"])[0] if top_trend.get("topic_tags") else "General"
                
                # Verificar cooldown de 48 horas
                from ..stores.notifications import get_notification_store
                store = get_notification_store()
                can_send, seconds_remaining = store.can_send_notification(target_fid)
                
                if not can_send:
                    hours_remaining = seconds_remaining / 3600
                    logger.debug(f"⏳ FID {target_fid} en cooldown. Restan {hours_remaining:.1f} horas. Saltando notificación de tendencia...")
                    return
                
                logger.info("🔔 Enviando notificación de tendencia a FID %d...", target_fid)
                
                # Intentar obtener token del store (Self-hosted)
                token_data = store.get_token(target_fid)
                
                if token_data:
                    # Enviar usando token directo (bypass Neynar managed)
                    import uuid
                    notif_id = str(uuid.uuid4())
                    result = await self.farcaster.send_notification_custom(
                        token=token_data["token"],
                        url=token_data["url"],
                        title="🔥 Tendencia Detectada",
                        body=f"Nuevo tema viral: #{topic}. ¡Crea tu Lootbox ahora!",
                        target_url=f"https://celo-build-web-8rej.vercel.app/?trend={top_trend['frame_id']}",
                        notification_id=notif_id
                    )
                    if result.get("status") == "success":
                        store.record_notification_sent(target_fid)
                else:
                    # Fallback a Neynar Managed (si el usuario configuró el webhook en Neynar)
                    result = await self.farcaster.publish_frame_notification(
                        target_fids=[target_fid],
                        title="🔥 Tendencia Detectada",
                        body=f"Nuevo tema viral: #{topic}. ¡Crea tu Lootbox ahora!",
                        target_url=f"https://celo-build-web-8rej.vercel.app/?trend={top_trend['frame_id']}"
                    )
                    if result.get("status") == "success":
                        store.record_notification_sent(target_fid)
            except Exception as exc:
                logger.warning("Error enviando notificación: %s", exc)
        
        return {
            **base_context,
            "status": "trend_detected" if any(t["trend_score"] >= self.settings.min_trend_score for t in detected_trends) else "trend_below_threshold",
            "trends": detected_trends,
            # Mantener compatibilidad con campos legacy usando la primera tendencia
            "frame_id": detected_trends[0]["frame_id"],
            "cast_hash": detected_trends[0]["cast_hash"],
            "trend_score": detected_trends[0]["trend_score"],
            "source_text": detected_trends[0]["source_text"],
            "ai_analysis": detected_trends[0]["ai_analysis"],
            "ai_enabled": detected_trends[0]["ai_enabled"],
            "topic_tags": detected_trends[0]["topic_tags"],
            "channel_id": detected_trends[0]["channel_id"],
            "author": detected_trends[0]["author"],
        }

    def _get_llm(self) -> ChatGoogleGenerativeAI | None:
        """Inicializa el LLM de forma lazy solo cuando se necesite."""
        if self.llm_initialized:
            return self.llm
        
        if not self.google_api_key:
            self.llm_initialized = True
            return None
        
        # Intentar inicializar con modelos disponibles en el plan gratuito
        # Nota: Los modelos con "-live" no funcionan con langchain, usar versiones sin sufijo
        models_to_try = [
            "gemini-2.0-flash-lite", # Versión solicitada por usuario
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        
        for model_name in models_to_try:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=self.google_api_key,
                    temperature=0.5,
                    max_retries=0,  # Deshabilitar retries automáticos para evitar loops infinitos
                )
                # No hacemos llamada de prueba para evitar consumir cuota innecesariamente
                # El LLM se probará cuando se use por primera vez
                self.llm_initialized = True
                logger.info("✅ Gemini LLM inicializado con modelo: %s (se probará al primer uso)", model_name)
                return self.llm
            except Exception as exc:  # noqa: BLE001
                logger.debug("Modelo %s no disponible al inicializar: %s", model_name, exc)
                continue
        
        # Si ningún modelo funciona, marcar como inicializado pero sin LLM
        self.llm_initialized = True
        logger.warning("⚠️ No se pudo inicializar ningún modelo de Gemini. Usando análisis básico.")
        return None

    async def _summarize_cast(self, cast: dict[str, Any]) -> tuple[str, bool]:
        """
        Genera un análisis del cast.
        MODIFICADO: Se ha deshabilitado Gemini por petición del usuario para maximizar velocidad.
        Retorna siempre texto vacío y False.
        """
        # Ya no usamos Gemini ni análisis básico de texto.
        # El frontend mostrará directamente el cast original.
        return ("", False)

    def _score_cast(self, cast: dict[str, Any]) -> float:
        reactions = cast.get("reactions", {})
        likes = reactions.get("likes", 0)
        recasts = reactions.get("recasts", 0)
        replies = reactions.get("replies", 0)

        engagement_score = (likes * 1.0 + recasts * 2.0 + replies * 0.6) / 200.0
        recency_hours = self.farcaster.timestamp_age_hours(cast.get("timestamp"))
        recency_bonus = max(0.0, 12 - recency_hours) / 12.0
        combined = engagement_score + recency_bonus * 0.3
        return min(combined, 1.0)

    @staticmethod
    def _extract_tags(text: str) -> list[str]:
        tags = set(tag.lower() for tag in re.findall(r"#(\w+)", text))
        return sorted(tags)[:4]

    def _calculate_score(self, stats: dict[str, Any]) -> float:
        likes = stats.get("likes", 0)
        recasts = stats.get("recasts", 0)
        replies = stats.get("replies", 0)
        return (likes * 1.0 + recasts * 2.0 + replies * 0.5) / 100.0

    def build_thread_id(self, payload: dict[str, Any]) -> str:
        seed = f"{payload.get('frame_id', 'global')}:{payload.get('channel_id', 'general')}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return f"lootbox-{digest[:16]}"

