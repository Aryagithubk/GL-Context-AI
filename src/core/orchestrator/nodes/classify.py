"""
Classify node — classifies the query intent and routes to agents.
Uses the AgentRouter to score agents and build an execution plan.
"""

from src.core.orchestrator.state import OmniQueryState
from src.utils.logger import setup_logger

logger = setup_logger("ClassifyNode")


def make_classify_node(router):
    """Factory that creates classify node with access to the router"""

    async def classify_node(state: OmniQueryState) -> dict:
        """Classify intent and build agent routing plan"""
        from src.agents.base_agent import AgentContext

        query = state["query"]
        logger.info(f"Classifying query: '{query[:80]}...'")

        # Simple keyword-based intent classification
        intent = _classify_intent(query)

        # Build agent context
        context = AgentContext(
            query=query,
            original_query=state.get("original_query", query),
            intent=intent,
            session_id=state.get("session_id", ""),
        )

        # Route to agents
        plans = await router.route(context)

        if not plans:
            logger.warning("No agents matched — will use fallback.")

        return {
            "intent": intent,
            "agent_plans": plans,
            "current_agent_index": 0,
        }

    return classify_node


def _classify_intent(query: str) -> str:
    """Simple keyword-based intent classification"""
    q = query.lower()

    if any(kw in q for kw in ["summarize", "summary", "explain", "what does"]):
        return "summarization"

    if any(kw in q for kw in ["how many", "count", "total", "average", "salary", "employee", "database", "table"]):
        return "data_query"

    if any(kw in q for kw in ["wiki", "confluence", "knowledge base", "runbook"]):
        return "wiki_search"

    if any(kw in q for kw in ["search", "latest", "news", "who is", "what is"]):
        return "web_search"

    if any(kw in q for kw in ["document", "policy", "procedure", "guideline", "file", "report"]):
        return "document_search"

    return "general"
