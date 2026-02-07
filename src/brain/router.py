import json
from src.llm.base import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Router:
    def __init__(self, llm_client: BaseLLMClient, context_summary: str):
        self.llm = llm_client
        self.context_summary = context_summary

    def route(self, query: str) -> str:
        """Decides whether to use 'db' (Vector Store) or 'web' (Web Search)."""
        
        prompt = f"""You are an intelligent routing agent.
        
        Knowledge Base Context: {self.context_summary}
        User Query: "{query}"
        
        Task: Decide where to find the answer.
        - If the query is related to the Knowledge Base (company documents, policies, internal info), choose "db".
        - If the query is about current events, general world knowledge, or clearly outside the scope of company docs, choose "web".
        - If unsure, default to "db".

        Return only one word: "db" or "web".
        """
        
        try:
            decision = self.llm.generate(prompt).strip().lower()
            # Clean up response just in case
            if "web" in decision:
                return "web"
            return "db"
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return "db" # Default fail-safe
