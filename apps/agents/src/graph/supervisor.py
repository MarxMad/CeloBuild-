from dataclasses import dataclass
from typing import Any

from ..config import Settings
from ..stores.leaderboard import LeaderboardStore, default_store
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


class SupervisorOrchestrator:
    """Coordina la ejecución secuencial de agentes LangGraph."""

    def __init__(
        self,
        trend_watcher: TrendWatcherAgent,
        eligibility: EligibilityAgent,
        distributor: RewardDistributorAgent,
        leaderboard: LeaderboardStore,
        settings: Settings | None = None,
    ) -> None:
        self.trend_watcher = trend_watcher
        self.eligibility = eligibility
        self.distributor = distributor
        self.leaderboard = leaderboard
        self.settings = settings

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupervisorOrchestrator":
        """Factory que instancia sub-agentes con las mismas credenciales."""

        trend = TrendWatcherAgent(settings)
        eligibility = EligibilityAgent(settings)
        leaderboard = default_store(settings.leaderboard_max_entries)
        distributor = RewardDistributorAgent(settings, leaderboard)
        return cls(trend, eligibility, distributor, leaderboard, settings)

    async def run(self, payload: dict[str, Any]) -> RunResult:
        """Ejecución mínima: detectar tendencia -> filtrar usuarios -> recompensar."""

        trend_context = await self.trend_watcher.handle(payload)
        eligible_users = await self.eligibility.handle(trend_context)
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
            # Construir URL del explorer para Celo Sepolia
            # Asumimos Sepolia por defecto para el link si no está en config
            base_explorer = "https://celo-sepolia.blockscout.com"
            explorer_url = f"{base_explorer}/tx/{tx_hash}"

        thread_id = payload.get("thread_id") or self.trend_watcher.build_thread_id(payload)
        
        return RunResult(
            thread_id=thread_id,
            summary=summary,
            tx_hash=tx_hash,
            explorer_url=explorer_url,
            mode=mode,
            reward_type=reward_type,
        )

