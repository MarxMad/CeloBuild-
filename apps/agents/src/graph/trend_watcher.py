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

        logger.info("Analizando conversaciones recientes en Farcaster (canal=%s)...", channel_id)
        casts = await self.farcaster.fetch_recent_casts(channel_id=channel_id, limit=self.settings.max_recent_casts)
        if not casts:
            return {"status": "no_trends_found", **base_context}
            
        scored_casts = []
        for candidate in casts:
            candidate_score = self._score_cast(candidate)
            scored_casts.append(
                {
                    **candidate,
                    "trend_score": candidate_score,
                }
            )

        scored_casts.sort(key=lambda cast: cast["trend_score"], reverse=True)
        
        # Filtrar casts que pasen el umbral mínimo
        valid_casts = [
            cast for cast in scored_casts
            if cast["trend_score"] >= self.settings.min_trend_score
        ]
        
        # Deduplicar por usuario/autor para asegurar diversidad
        # Seleccionar hasta 5 tendencias de diferentes usuarios
        seen_users: set[int | str] = set()
        valid_trends = []
        
        for cast in valid_casts:
            # Obtener identificador único del usuario (FID o username)
            author = cast.get("author", {})
            user_id = author.get("fid") or author.get("username") or "unknown"
            
            # Solo agregar si no hemos visto este usuario antes
            if user_id not in seen_users and len(valid_trends) < 5:
                seen_users.add(user_id)
                valid_trends.append(cast)
            
            # Si ya tenemos 5 tendencias de diferentes usuarios, parar
            if len(valid_trends) >= 5:
                break
        
        if not valid_trends:
            # Si no hay tendencias válidas, usar las top 5 de bajo umbral
            top_cast = scored_casts[0]
            logger.info(
                "Trend encontrado pero bajo el umbral (%.2f < %.2f)",
                top_cast["trend_score"],
                self.settings.min_trend_score,
            )
            
            # Recopilar top 5 tendencias débiles para mostrar en el frontend
            weak_trends = []
            seen_users_weak: set[int | str] = set()
            
            for cast in scored_casts:
                author = cast.get("author", {})
                user_id = author.get("fid") or author.get("username") or "unknown"
                
                if user_id not in seen_users_weak and len(weak_trends) < 5:
                    seen_users_weak.add(user_id)
                    
                    # Formatear tendencia débil
                    weak_trends.append({
                        "frame_id": "cast-" + (cast.get("hash") or "unknown")[:8],
                        "cast_hash": cast.get("hash"),
                        "trend_score": round(cast["trend_score"], 3),
                        "source_text": cast.get("text"),
                        "ai_analysis": cast.get("text"), # Sin análisis AI profundo para ahorrar tokens
                        "ai_enabled": False,
                        "topic_tags": self._extract_tags(cast.get("text", "")),
                        "channel_id": cast.get("channel_id") or channel_id,
                        "author": cast.get("author", {}),
                    })
                
                if len(weak_trends) >= 5:
                    break

            # Generar frame_id incluso para tendencias bajo el umbral
            frame_identifier = "cast-" + (top_cast.get("hash") or "unknown")[:8]
            # Generar análisis (puede usar AI o fallback)
            analysis_text, uses_ai = await self._summarize_cast(top_cast)
            
            return {
                **base_context,
                "status": "trend_below_threshold",
                "frame_id": frame_identifier,  # Incluir frame_id para que el pipeline funcione
                "cast_hash": top_cast.get("hash"),
                "trend_score": top_cast["trend_score"],
                "source_text": top_cast.get("text"),
                "ai_analysis": analysis_text,
                "ai_enabled": uses_ai,  # Indicador si se usó AI o fallback
                "topic_tags": self._extract_tags(top_cast.get("text", "")),
                "trends": weak_trends,  # Retornar las tendencias débiles
            }
        
        # Procesar cada tendencia válida
        detected_trends = []
        for cast in valid_trends:
            analysis_text, uses_ai = await self._summarize_cast(cast)
            topic_tags = self._extract_tags(cast.get("text", ""))
            frame_identifier = "cast-" + (cast.get("hash") or "unknown")[:8]
            
            detected_trends.append({
                "frame_id": frame_identifier,
                "cast_hash": cast.get("hash"),
                "trend_score": round(cast["trend_score"], 3),
                "source_text": cast.get("text"),
                "ai_analysis": analysis_text,
                "ai_enabled": uses_ai,  # Indicador si se usó AI o fallback
                "topic_tags": topic_tags,
                "channel_id": cast.get("channel_id") or channel_id,
                "author": cast.get("author", {}),
            })
        
        logger.info("Detectadas %d tendencias válidas (score >= %.2f)", len(detected_trends), self.settings.min_trend_score)
        
        return {
            **base_context,
            "status": "trend_detected",
            "trends": detected_trends,  # Lista de tendencias detectadas
            # Mantener compatibilidad: también retornar la primera tendencia en campos individuales
            "frame_id": detected_trends[0]["frame_id"],
            "cast_hash": detected_trends[0]["cast_hash"],
            "trend_score": detected_trends[0]["trend_score"],
            "source_text": detected_trends[0]["source_text"],
            "ai_analysis": detected_trends[0]["ai_analysis"],
            "ai_enabled": detected_trends[0]["ai_enabled"],  # Indicador si se usó AI o fallback
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
            "gemini-2.5-flash",  # Versión sin -live que debería funcionar con langchain
            "gemini-2.0-flash",  # Versión sin -live que debería funcionar con langchain
            "gemini-1.5-flash",  # Fallback
            "gemini-1.0-pro",  # Fallback
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
        """Genera un análisis del cast usando IA si está disponible, sino genera uno básico.
        
        Retorna: (análisis_texto, usa_ai)
        - usa_ai: True si se usó Gemini, False si se usó fallback
        """
        llm = self._get_llm()
        if not llm:
            # Análisis básico sin IA basado en keywords y engagement
            logger.info("🤖 AI no disponible - usando análisis básico (fallback)")
            text = cast.get("text", "")
            author = cast.get("author", {}).get("username", "usuario")
            reactions = cast.get("reactions", {})
            likes = reactions.get("likes", 0)
            recasts = reactions.get("recasts", 0)
            
            keywords = ["celo", "minipay", "web3", "defi", "crypto", "blockchain", "nft", "rewards"]
            has_keywords = any(kw in text.lower() for kw in keywords)
            
            if has_keywords and (likes > 10 or recasts > 5):
                analysis = f"Cast relevante de {author} sobre Web3/Celo con alto engagement ({likes} likes, {recasts} recasts). Potencial para recompensar participación activa."
            elif has_keywords:
                analysis = f"Cast de {author} mencionando temas de Celo/Web3. Considerar recompensa para fomentar más participación."
            else:
                analysis = f"Cast de {author} con engagement moderado. Evaluar relevancia para la comunidad Celo."
            
            return (analysis, False)  # False = no usa AI
        
        # Intentar usar IA si está disponible
        logger.info("🤖 Intentando análisis con Gemini AI...")
        prompt = ChatPromptTemplate.from_template(
            (
                "Eres un estratega de growth para comunidades Web3. Resume en 1 frase por qué este cast es "
                "relevante para la comunidad de Celo/MiniPay y qué acción recomienda tomar."
                "\n\nCast: {text}\nAutor: {author}"
            )
        )
        chain = prompt | llm
        try:
            result = await chain.ainvoke(
                {
                    "text": cast.get("text", ""),
                    "author": cast.get("author", {}).get("username"),
                }
            )
            logger.info("✅ Análisis generado con Gemini AI")
            return (result.content, True)  # True = usa AI
        except Exception as exc:  # noqa: BLE001
            # Detectar si es error de cuota (429) o cualquier otro error
            error_str = str(exc).lower()
            is_quota_error = "429" in error_str or "quota" in error_str or "resourceexhausted" in error_str
            
            if is_quota_error:
                logger.warning(
                    "⚠️ Cuota de Gemini agotada (usando análisis básico). "
                    "El sistema funcionará normalmente sin IA."
                )
                # Deshabilitar LLM para evitar más intentos
                self.llm = None
            else:
                logger.warning("⚠️ Error analizando con Gemini (usando análisis básico): %s", exc)
            
            # Fallback al análisis básico (sin IA)
            logger.info("🔄 Cambiando a análisis básico (fallback)")
            text = cast.get("text", "")
            author = cast.get("author", {}).get("username", "usuario")
            reactions = cast.get("reactions", {})
            likes = reactions.get("likes", 0)
            recasts = reactions.get("recasts", 0)
            
            keywords = ["celo", "minipay", "web3", "defi", "crypto", "blockchain", "nft", "rewards"]
            has_keywords = any(kw in text.lower() for kw in keywords)
            
            if has_keywords and (likes > 10 or recasts > 5):
                analysis = f"Cast relevante de {author} sobre Web3/Celo con alto engagement ({likes} likes, {recasts} recasts). Potencial para recompensar participación activa."
            elif has_keywords:
                analysis = f"Cast de {author} mencionando temas de Celo/Web3. Considerar recompensa para fomentar más participación."
            else:
                analysis = f"Cast de {author} con engagement moderado. Evaluar relevancia para la comunidad Celo."
            
            return (analysis, False)  # False = no usa AI

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

