"""
AgentRouter — Scores agents by confidence and builds an execution plan.
"""

import asyncio
from typing import List
from src.agents.base_agent import BaseAgent, AgentContext, AgentStatus
from src.core.orchestrator.state import AgentPlan
from src.utils.logger import setup_logger

logger = setup_logger("AgentRouter")


class AgentRouter:
    """Routes queries to the most confident agents"""

    def __init__(
        self,
        agents: List[BaseAgent],
        min_confidence: float = 0.3,
        max_parallel: int = 3,
    ):
        self.agents = agents
        self.min_confidence = min_confidence
        self.max_parallel = max_parallel

    async def route(self, context: AgentContext) -> List[AgentPlan]:
        """
        Score all agents and return an execution plan ordered by confidence.
        1. Ask each agent for confidence (parallel)
        2. Filter below min_confidence
        3. Sort descending
        4. Take top N
        """
        scoring_tasks = []
        for agent in self.agents:
            if agent._status == AgentStatus.DISABLED:
                continue
            scoring_tasks.append(self._score_agent(agent, context))

        scores = await asyncio.gather(*scoring_tasks, return_exceptions=True)

        plans: List[AgentPlan] = []
        enabled_agents = [a for a in self.agents if a._status != AgentStatus.DISABLED]

        for agent, score in zip(enabled_agents, scores):
            if isinstance(score, Exception):
                logger.warning(f"Scoring error for {agent.name}: {score}")
                continue
            if score >= self.min_confidence:
                plans.append(AgentPlan(
                    agent_name=agent.name,
                    confidence=round(score, 3),
                    priority=0,
                ))

        # Sort by confidence descending
        plans.sort(key=lambda p: p["confidence"], reverse=True)

        # Assign priority
        for i, plan in enumerate(plans[:self.max_parallel]):
            plan["priority"] = i + 1

        selected = plans[:self.max_parallel]
        logger.info(
            f"Router selected {len(selected)} agent(s): "
            f"{[(p['agent_name'], p['confidence']) for p in selected]}"
        )
        return selected

    async def _score_agent(self, agent: BaseAgent, context: AgentContext) -> float:
        return await agent.can_handle(context)
