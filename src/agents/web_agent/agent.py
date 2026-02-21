"""
WebSearchAgent — Web search fallback agent.
Uses DuckDuckGo search (free, no API key) and summarizes results using the LLM.
"""

import time
from typing import Any, Dict, List
from src.agents.base_agent import BaseAgent, AgentContext, AgentResponse, AgentStatus
from src.utils.logger import setup_logger

logger = setup_logger("WebSearchAgent")


class WebSearchAgent(BaseAgent):
    """Agent that searches the web using DuckDuckGo as a universal fallback"""

    def __init__(self, config: Dict[str, Any], llm_provider: Any):
        super().__init__(config, llm_provider)
        self._name = "WebSearchAgent"
        self.max_results = config.get("max_results", 5)

    @property
    def description(self) -> str:
        return "Searches the web using DuckDuckGo to answer general knowledge questions."

    @property
    def supported_intents(self) -> List[str]:
        return ["web_search", "general", "current_events"]

    async def initialize(self) -> None:
        """Verify DuckDuckGo search library is available"""
        try:
            from duckduckgo_search import DDGS
            self._status = AgentStatus.READY
            logger.info("WebSearchAgent initialized — DuckDuckGo ready.")
        except ImportError:
            self._status = AgentStatus.ERROR
            logger.error("WebSearchAgent requires 'duckduckgo-search'. "
                        "Install with: pip install duckduckgo-search")

    async def can_handle(self, context: AgentContext) -> float:
        """
        Low baseline confidence — acts as universal fallback.
        Boost for explicit web/search-related keywords.
        """
        if self._status != AgentStatus.READY:
            return 0.0

        score = 0.3  # Low baseline — fallback agent
        query_lower = context.query.lower()

        web_keywords = [
            "search", "google", "web", "internet", "latest",
            "current", "news", "trending", "today", "2024", "2025", "2026",
            "who is", "what is", "tell me about",
        ]
        matches = sum(1 for kw in web_keywords if kw in query_lower)
        if matches >= 2:
            score += 0.3
        elif matches == 1:
            score += 0.15

        if context.intent in ["web_search", "current_events"]:
            score += 0.2

        return min(score, 1.0)

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Search the web and summarize results"""
        start = time.time()

        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(
                    context.query,
                    max_results=self.max_results,
                ))

            if not results:
                return AgentResponse(
                    success=False,
                    answer=None,
                    confidence=0.0,
                    error="No web search results found.",
                    execution_time_ms=(time.time() - start) * 1000,
                )

            # Build context from search results
            search_context = []
            sources = []
            for i, result in enumerate(results):
                title = result.get("title", "")
                body = result.get("body", "")
                href = result.get("href", "")

                search_context.append(f"[{i+1}] {title}\n{body}")
                sources.append({
                    "agent_name": self.name,
                    "source_type": "web",
                    "source_identifier": href,
                    "relevance_score": round(0.8 - (i * 0.1), 2),
                    "excerpt": body[:200],
                })

            context_text = "\n\n".join(search_context)

            prompt = (
                f"Based on these web search results, answer the question.\n\n"
                f"SEARCH RESULTS:\n{context_text}\n\n"
                f"QUESTION: {context.query}\n\n"
                f"Provide a clear, accurate answer based on the search results. "
                f"Cite source numbers [1], [2], etc. where relevant."
            )

            llm_response = await self.llm.generate(prompt)

            return AgentResponse(
                success=True,
                answer=llm_response.text,
                confidence=0.6,
                sources=sources,
                token_usage=llm_response.usage,
                execution_time_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            logger.error(f"WebSearchAgent error: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )
