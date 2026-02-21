"""
Fallback node — Handles cases where no agent could answer.
"""

from src.core.orchestrator.state import OmniQueryState
from src.utils.logger import setup_logger

logger = setup_logger("FallbackNode")


def make_fallback_node(llm_provider):
    """Factory that creates fallback node with LLM access"""

    async def fallback_node(state: OmniQueryState) -> dict:
        """Generate answer from LLM general knowledge as last resort"""
        query = state["query"]
        logger.info(f"Fallback triggered for query: '{query[:80]}...'")

        try:
            prompt = (
                f"You are a helpful assistant. Answer this question using your general knowledge.\n\n"
                f"Question: {query}\n\n"
                f"Answer concisely and accurately."
            )

            response = await llm_provider.generate(prompt)

            disclaimer = (
                "ℹ️ This answer is from general knowledge — "
                "no matching data was found in documents, databases, or configured sources.\n\n"
            )

            return {
                "synthesized_answer": disclaimer + response.text,
                "overall_confidence": 0.2,
                "final_sources": [{
                    "agent_name": "Fallback",
                    "source_type": "general_knowledge",
                    "source_identifier": "LLM General Knowledge",
                    "relevance_score": 0.2,
                }],
                "agents_used": list(state.get("agents_used", [])) + ["Fallback"],
            }

        except Exception as e:
            logger.error(f"Fallback error: {e}")
            return {
                "synthesized_answer": "I was unable to process your question. Please try again.",
                "overall_confidence": 0.0,
                "error": str(e),
            }

    return fallback_node
