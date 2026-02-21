"""
DocAgent — Document retrieval agent.
Wraps the existing RAG pipeline (loader, chunker, embedder, vector store, retriever)
to answer questions from company documents.
"""

import time
from typing import Any, Dict, List
from src.agents.base_agent import BaseAgent, AgentContext, AgentResponse, AgentStatus
from src.ingestion.embedder import Embedder
from src.vector_db.chroma import VectorStore
from src.utils.logger import setup_logger

logger = setup_logger("DocAgent")

RELEVANCE_THRESHOLD = 0.35


class DocAgent(BaseAgent):
    """Agent that answers questions from company documents using RAG"""

    def __init__(self, config: Dict[str, Any], llm_provider: Any):
        super().__init__(config, llm_provider)
        self._name = "DocAgent"
        self.vector_store = None
        self.embedder = None

    @property
    def description(self) -> str:
        return "Retrieves and answers questions from indexed company documents (PDF, TXT, etc.)"

    @property
    def supported_intents(self) -> List[str]:
        return ["summarization", "explanation", "document_search", "general"]

    async def initialize(self) -> None:
        """Set up the vector store and embedder"""
        try:
            embedding_model = self.config.get("embedding_model", "nomic-embed-text")
            persist_dir = self.config.get("persist_directory", "./vector_store")

            self.embedder = Embedder(model_name=embedding_model)
            self.vector_store = VectorStore(
                persist_directory=persist_dir,
                embedding_function=self.embedder.get_embedding_function()
            )
            self._status = AgentStatus.READY
            logger.info("DocAgent initialized — vector store ready.")
        except Exception as e:
            self._status = AgentStatus.ERROR
            logger.error(f"DocAgent init failed: {e}")
            raise

    async def can_handle(self, context: AgentContext) -> float:
        """
        Confidence scoring:
        - 0.9 if intent is summarization/explanation
        - 0.7 if query has doc-related keywords
        - 0.5 baseline
        """
        if self._status != AgentStatus.READY:
            return 0.0

        score = 0.5
        query_lower = context.query.lower()

        doc_keywords = [
            "document", "report", "file", "pdf", "policy", "manual",
            "guideline", "procedure", "handbook", "standard", "leave",
            "expense", "onboarding", "company", "rules", "internal",
        ]
        if any(kw in query_lower for kw in doc_keywords):
            score += 0.2

        if context.intent in ["summarization", "explanation", "document_search"]:
            score += 0.2

        return min(score, 1.0)

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Retrieve docs and generate answer"""
        start = time.time()
        try:
            db = self.vector_store.get_db()
            scored_results = db.similarity_search_with_relevance_scores(
                context.query, k=self.config.get("top_k", 3)
            )

            # Filter by relevance threshold
            good_docs = [
                (doc, score) for doc, score in scored_results
                if score >= RELEVANCE_THRESHOLD
            ]

            if not good_docs:
                return AgentResponse(
                    success=False,
                    answer=None,
                    confidence=0.0,
                    error="No relevant documents found.",
                    execution_time_ms=(time.time() - start) * 1000,
                )

            # Build context from relevant docs
            context_text = "\n\n---\n\n".join(
                [doc.page_content for doc, _ in good_docs]
            )

            prompt = (
                f"You are a helpful assistant answering questions based on company documents.\n\n"
                f"Context:\n{context_text}\n\n"
                f"Question: {context.query}\n\n"
                f"Answer clearly and concisely based on the documents above."
            )

            response = await self.llm.generate(prompt)

            # Build source citations
            sources = []
            for doc, score in good_docs:
                source_path = doc.metadata.get("source", "Unknown")
                sources.append({
                    "agent_name": self.name,
                    "source_type": "document",
                    "source_identifier": source_path,
                    "relevance_score": round(score, 3),
                    "excerpt": doc.page_content[:200] + "...",
                })

            avg_score = sum(s for _, s in good_docs) / len(good_docs)

            return AgentResponse(
                success=True,
                answer=response.text,
                confidence=round(avg_score, 3),
                sources=sources,
                token_usage=response.usage,
                execution_time_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            logger.error(f"DocAgent execution error: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )
