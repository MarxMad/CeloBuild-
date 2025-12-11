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
        # 1. Fetch Viral Trends (Top Score)
        logger.info("Consultando tendencias virales de Neynar (canal=%s)...", channel_id)
        viral_casts = []
        try:
            viral_casts = await self.farcaster.fetch_trending_feed(
                channel_id=channel_id, 
                limit=10, 
                time_window="24h"
            )
        except Exception as exc:
            logger.warning("⚠️ Error obteniendo trending feed: %s", exc)

        # 2. Fetch Community Targets (Low Score / Verified Users)
        target_users = ["oyealmond.base.eth", "celopg", "muchogang", "kmacb.eth"]
        logger.info("Consultando casts de usuarios comunitarios: %s", target_users)
        community_casts = []
        try:
            # Seleccionar 2 usuarios al azar cada vez para variedad
            import random
            selected_users = random.sample(target_users, min(2, len(target_users)))
            community_casts = await self.farcaster.fetch_casts_from_users(selected_users, limit_per_user=2)
        except Exception as exc:
            logger.warning("⚠️ Error obteniendo community casts: %s", exc)

        # 3. Fallback: Recent Casts (si falla todo lo anterior)
        fallback_casts = []
        if not viral_casts and not community_casts:
             logger.warning("⚠️ Fallback a recent casts.")
             fallback_casts = await self.farcaster.fetch_recent_casts(channel_id=channel_id, limit=20)
        
        # Combinar pools
        all_candidates = viral_casts + community_casts + fallback_casts
        
        if not all_candidates:
            return {"status": "no_trends_found", **base_context}
            
        # Scoring para unificar criterios
        scored_casts = []
        for candidate in all_candidates:
            # Si es targeted, ya tiene flag. Si no, calcular score.
            is_targeted = candidate.get("is_targeted", False)
            candidate_score = self._score_cast(candidate)
            
            # Boost artificial a los targeted para que no queden muy abajo en validaciones internas,
            # aunque la selección final forzará su inclusión.
            final_score = candidate_score
            if is_targeted:
                final_score = max(candidate_score, 0.4) # Asegurar un mínimo de respetabilidad

            scored_casts.append(
                {
                    **candidate,
                    "trend_score": final_score,
                    "is_targeted": is_targeted
                }
            )

        # Ordenar por score real para los virales
        viral_pool = sorted([c for c in scored_casts if not c.get("is_targeted")], key=lambda x: x["trend_score"], reverse=True)
        target_pool = [c for c in scored_casts if c.get("is_targeted")]
        
        # --- SELECCIÓN MIXTA (Top 3 Virales + 2 Comunitarios) ---
        final_selection = []
        seen_ids = set()

        def add_cast(cast):
            # Deduplicar por hash y autor
            auth_id = cast.get("author", {}).get("fid")
            cast_hash = cast.get("hash")
            if cast_hash not in seen_ids and auth_id not in seen_ids: # Evitar repetir usuario en la misma lista
                final_selection.append(cast)
                seen_ids.add(cast_hash)
                seen_ids.add(auth_id)

        # 1. Agregar Top 3 Virales
        for cast in viral_pool:
            if len(final_selection) >= 3:
                break
            add_cast(cast)
            
        # 2. Agregar 2 Comunitarios (Targeted)
        # Randomize community pool to show different targeted casts
        random.shuffle(target_pool)
        for cast in target_pool:
            if len(final_selection) >= 5:
                break
            add_cast(cast)
            
        # 3. Rellenar si falta (backfill con más virales)
        for cast in viral_pool:
            if len(final_selection) >= 5:
                break
            add_cast(cast)

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
                
                logger.info("🔔 Enviando notificación de tendencia a FID %d...", target_fid)
                
                # Intentar obtener token del store (Self-hosted)
                from ..stores.notifications import get_notification_store
                store = get_notification_store()
                token_data = store.get_token(target_fid)
                
                if token_data:
                    # Enviar usando token directo (bypass Neynar managed)
                    import uuid
                    notif_id = str(uuid.uuid4())
                    await self.farcaster.send_notification_custom(
                        token=token_data["token"],
                        url=token_data["url"],
                        title="🔥 Tendencia Detectada",
                        body=f"Nuevo tema viral: #{topic}. ¡Crea tu Lootbox ahora!",
                        target_url=f"https://celo-build-web-8rej.vercel.app/?trend={top_trend['frame_id']}",
                        notification_id=notif_id
                    )
                else:
                    # Fallback a Neynar Managed (si el usuario configuró el webhook en Neynar)
                    await self.farcaster.publish_frame_notification(
                        target_fids=[target_fid],
                        title="🔥 Tendencia Detectada",
                        body=f"Nuevo tema viral: #{topic}. ¡Crea tu Lootbox ahora!",
                        target_url=f"https://celo-build-web-8rej.vercel.app/?trend={top_trend['frame_id']}"
                    )
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

