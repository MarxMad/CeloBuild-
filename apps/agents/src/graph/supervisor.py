from dataclasses import dataclass
from typing import Any

from ..config import Settings
from ..stores.leaderboard import LeaderboardStore, default_store
from ..stores.trends import TrendsStore, default_trends_store
from .eligibility import EligibilityAgent
from .reward_distributor import RewardDistributorAgent
from .trend_watcher import TrendWatcherAgent


@dataclass
class RunResult:
    thread_id: str
    summary: str
    tx_hash: str | None = None
    explorer_url: str | None = None
    mode: str | None = None
    reward_type: str | None = None
    user_analysis: dict[str, Any] | None = None  # Información del usuario analizado
    trend_info: dict[str, Any] | None = None  # Información de la tendencia detectada
    eligible: bool | None = None  # Si el usuario es elegible (None = no verificado, True/False = resultado)
    eligibility_message: str | None = None  # Mensaje explicando por qué no es elegible
    error: str | None = None  # Mensaje de error específico si falla la transacción
    nft_images: dict[str, str] | None = None  # URLs de las imágenes generadas/minteadas
    best_cast: dict[str, Any] | None = None # El cast más viral del usuario


class SupervisorOrchestrator:
    """Coordina la ejecución secuencial de agentes LangGraph."""

    def __init__(
        self,
        trend_watcher: TrendWatcherAgent,
        eligibility: EligibilityAgent,
        distributor: RewardDistributorAgent,
        leaderboard: LeaderboardStore,
        trends_store: TrendsStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.trend_watcher = trend_watcher
        self.eligibility = eligibility
        self.distributor = distributor
        self.leaderboard = leaderboard
        self.trends_store = trends_store or default_trends_store()
        self.settings = settings

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupervisorOrchestrator":
        """Factory que instancia sub-agentes con las mismas credenciales."""

        trend = TrendWatcherAgent(settings)
        eligibility = EligibilityAgent(settings)
        leaderboard = default_store(settings.leaderboard_max_entries)
        trends_store = default_trends_store()
        distributor = RewardDistributorAgent(settings, leaderboard)
        return cls(trend, eligibility, distributor, leaderboard, trends_store, settings)

    async def run(self, payload: dict[str, Any]) -> RunResult:
        """Ejecución mínima: detectar tendencia -> filtrar usuarios -> recompensar."""
        mode = None
        trend_context = await self.trend_watcher.handle(payload)
        
        # Guardar todas las tendencias detectadas si es válida o si es la mejor encontrada (aunque sea bajo umbral)
        if trend_context.get("status") in ["trend_detected", "trend_below_threshold"]:
            trends_list = trend_context.get("trends", [])
            
            # Si hay una lista de tendencias, guardar todas
            if trends_list:
                for trend in trends_list:
                    author_info = trend.get("author", {})
                    self.trends_store.record({
                        "frame_id": trend.get("frame_id"),
                        "cast_hash": trend.get("cast_hash"),
                        "trend_score": trend.get("trend_score"),
                        "source_text": trend.get("source_text"),
                        "ai_analysis": trend.get("ai_analysis"),
                        "topic_tags": trend.get("topic_tags", []),
                        "channel_id": trend.get("channel_id"),
                        "author_username": author_info.get("username") if isinstance(author_info, dict) else None,
                        "author_fid": author_info.get("fid") if isinstance(author_info, dict) else None,
                    })
            else:
                # Fallback: guardar la tendencia individual (compatibilidad)
                author_info = trend_context.get("author", {})
                self.trends_store.record({
                    "frame_id": trend_context.get("frame_id"),
                    "cast_hash": trend_context.get("cast_hash"),
                    "trend_score": trend_context.get("trend_score"),
                    "source_text": trend_context.get("source_text"),
                    "ai_analysis": trend_context.get("ai_analysis"),
                    "topic_tags": trend_context.get("topic_tags", []),
                    "channel_id": trend_context.get("channel_id"),
                    "author_username": author_info.get("username") if isinstance(author_info, dict) else None,
                    "author_fid": author_info.get("fid") if isinstance(author_info, dict) else None,
                })
        
        eligible_users = await self.eligibility.handle(trend_context)
        
        # Verificar si el usuario no es elegible (no está en Farcaster)
        if eligible_users.get("eligible") is False:
            # Usuario no es elegible - retornar error sin distribuir recompensa
            thread_id = payload.get("thread_id") or self.trend_watcher.build_thread_id(payload)
            return RunResult(
                thread_id=thread_id,
                summary=eligible_users.get("message", "Usuario no elegible"),
                tx_hash=None,
                explorer_url=None,
                mode="not_eligible",
                reward_type=None,
                user_analysis=None,
                trend_info={
                    "source_text": trend_context.get("source_text"),
                    "ai_analysis": trend_context.get("ai_analysis"),
                    "trend_score": trend_context.get("trend_score"),
                    "topic_tags": trend_context.get("topic_tags", []),
                } if trend_context.get("status") == "trend_detected" or trend_context.get("status") == "trend_below_threshold" else None,
                eligible=False,
                eligibility_message=eligible_users.get("message"),
            )
        
        distribution = await self.distributor.handle(eligible_users)

        mode = distribution.get('mode', 'unknown')
        tx_hash = distribution.get('tx_hash')
        reward_type = distribution.get('reward_type')
        top_user = None
        if eligible_users.get("rankings"):
            winner = eligible_users["rankings"][0]
            top_user = f"{winner.get('username')} ({winner.get('score')} pts)"
        
        summary = (
            f"Trend detectado: '{trend_context.get('source_text', 'N/A')[:30]}...'. "
            f"IA Insight: {trend_context.get('ai_analysis', 'N/A')}. "
            f"Usuarios elegibles: {len(eligible_users.get('recipients', []))}. "
            f"Top: {top_user or 'sin ganadores'}. "
            f"Recompensa: {reward_type or 'n/a'} -> {mode}."
        )
        
        explorer_url = None
        if tx_hash and self.settings:
            # Determine explorer based on RPC URL
            rpc_url = self.settings.celo_rpc_url.lower()
            if "alfajores" in rpc_url:
                base_explorer = "https://alfajores.celoscan.io"
            elif "sepolia" in rpc_url:
                base_explorer = "https://celo-sepolia.blockscout.com"
            else:
                # Default to Mainnet (celoscan.io is the standard for Celo Mainnet)
                base_explorer = "https://celoscan.io"
            
            # Ensure tx_hash has 0x prefix
            if not tx_hash.startswith("0x"):
                tx_hash = f"0x{tx_hash}"
            
            explorer_url = f"{base_explorer}/tx/{tx_hash}"

        thread_id = payload.get("thread_id") or self.trend_watcher.build_thread_id(payload)
        
        # Extraer información del usuario analizado para el frontend
        user_analysis = None
        if eligible_users.get("rankings") and len(eligible_users["rankings"]) > 0:
            top_user_data = eligible_users["rankings"][0]
            user_analysis = {
                "username": top_user_data.get("username"),
                "score": top_user_data.get("score"),
                "follower_count": top_user_data.get("follower_count", 0),
                "power_badge": top_user_data.get("power_badge", False),
                "reasons": top_user_data.get("reasons", []),
                "participation": top_user_data.get("participation", {}),
            }
        
        # BUSCAR CAST MÁS VIRAL (si hay un ganador)
        best_cast = None
        if eligible_users.get("rankings") and len(eligible_users["rankings"]) > 0:
            try:
                top_user_data = eligible_users["rankings"][0]
                fid = top_user_data.get("fid")
                if fid:
                    # Usar el toolbox de Farcaster que ya tenemos en trend_watcher
                    logger.info("🔍 Buscando cast más viral para FID %d...", fid)
                    recent_casts = await self.trend_watcher.farcaster.fetch_user_recent_casts(fid, limit=10)
                    
                    if recent_casts:
                        # Calcular score para cada cast
                        for cast in recent_casts:
                            reactions = cast.get("reactions", {})
                            likes = reactions.get("likes", 0)
                            recasts = reactions.get("recasts", 0)
                            replies = reactions.get("replies", 0)
                            # Score simple de engagement
                            cast["score"] = (likes * 1.0) + (recasts * 2.0) + (replies * 0.5)
                        
                        # Ordenar por score descendente
                        recent_casts.sort(key=lambda x: x["score"], reverse=True)
                        best_cast = recent_casts[0]
                        logger.info("✅ Cast más viral encontrado: %s (Score: %.1f)", best_cast.get("hash"), best_cast.get("score"))
            except Exception as e:
                logger.warning("Error buscando best cast: %s", e)
        
        return RunResult(
            thread_id=thread_id,
            summary=summary,
            tx_hash=tx_hash,
            explorer_url=explorer_url,
            mode=mode,
            reward_type=reward_type,
            user_analysis=user_analysis,  # Nueva información del usuario
            trend_info={  # Información de la tendencia detectada
                "source_text": trend_context.get("source_text"),
                "ai_analysis": trend_context.get("ai_analysis"),
                "ai_enabled": trend_context.get("ai_enabled", False),  # Indicador si se usó AI
                "trend_score": trend_context.get("trend_score"),
                "topic_tags": trend_context.get("topic_tags", []),
            } if trend_context.get("status") in ("trend_detected", "trend_below_threshold") else None,
            eligible=True,
            eligibility_message=eligible_users.get("message"),
            error=distribution.get("error"),
            nft_images=distribution.get("nft_images"),
            best_cast=best_cast,
        )

