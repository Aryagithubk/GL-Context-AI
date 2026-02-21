"""
Preprocess node — cleans and normalizes the incoming query.
"""

from src.core.orchestrator.state import OmniQueryState
from src.utils.logger import setup_logger

logger = setup_logger("PreprocessNode")


def preprocess_node(state: OmniQueryState) -> dict:
    """Clean and normalize the query"""
    query = state["query"].strip()
    logger.info(f"Preprocessing query: '{query[:80]}...'")

    return {
        "query": query,
        "original_query": query,
        "agent_results": [],
        "failed_agents": [],
        "agents_used": [],
        "final_sources": [],
        "current_agent_index": 0,
        "error": None,
    }
