from dataclasses import dataclass
from typing import Any

from ..config import Settings
from .eligibility import EligibilityAgent
from .reward_distributor import RewardDistributorAgent
from .trend_watcher import TrendWatcherAgent


@dataclass
class RunResult:
    thread_id: str
    summary: str


class SupervisorOrchestrator:
    """Coordina la ejecución secuencial de agentes LangGraph."""

    def __init__(
        self,
        trend_watcher: TrendWatcherAgent,
        eligibility: EligibilityAgent,
        distributor: RewardDistributorAgent,
    ) -> None:
        self.trend_watcher = trend_watcher
        self.eligibility = eligibility
        self.distributor = distributor

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupervisorOrchestrator":
        """Factory que instancia sub-agentes con las mismas credenciales."""

        trend = TrendWatcherAgent(settings)
        eligibility = EligibilityAgent(settings)
        distributor = RewardDistributorAgent(settings)
        return cls(trend, eligibility, distributor)

    async def run(self, payload: dict[str, Any]) -> RunResult:
        """Ejecución mínima: detectar tendencia -> filtrar usuarios -> recompensar."""

        trend_context = await self.trend_watcher.handle(payload)
        eligible_users = await self.eligibility.handle(trend_context)
        distribution = await self.distributor.handle(eligible_users)

        summary = (
            f"Frame {payload['frame_id']} procesado. "
            f"Usuarios elegibles: {len(eligible_users['recipients'])}. "
            f"Moda de recompensa: {distribution['mode']}."
        )
        thread_id = payload.get("thread_id") or self.trend_watcher.build_thread_id(payload)
        return RunResult(thread_id=thread_id, summary=summary)

