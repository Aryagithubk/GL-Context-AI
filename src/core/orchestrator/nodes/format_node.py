"""
Format node — Final formatting of the response.
"""

from src.core.orchestrator.state import OmniQueryState
from src.utils.logger import setup_logger

logger = setup_logger("FormatNode")


def format_node(state: OmniQueryState) -> dict:
    """Format the final response"""
    answer = state.get("synthesized_answer", "No answer available.")
    return {
        "formatted_response": answer,
    }
