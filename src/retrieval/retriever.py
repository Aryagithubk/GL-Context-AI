from typing import List, Tuple
from langchain_core.documents import Document
from src.vector_db.chroma import VectorStore
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Retriever:
    def __init__(self, vector_store: VectorStore, top_k: int = 3):
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str) -> List[Document]:
        """Retrieves relevant documents for a given query."""
        logger.info(f"Retrieving top {self.top_k} documents for query: {query}")
        db = self.vector_store.get_db()
        results = db.similarity_search(query, k=self.top_k)
        logger.info(f"Found {len(results)} relevant documents.")
        return results

    def format_docs(self, docs: List[Document]) -> str:
        """Formats retrieved documents into a single context string."""
        return "\n\n".join(doc.page_content for doc in docs)
