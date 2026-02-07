from typing import List
from langchain_core.documents import Document
from src.vector_db.chroma import VectorStore
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Retriever:
    def __init__(self, vector_store: VectorStore, top_k: int = 3):
        self.vector_store = vector_store
        self.top_k = top_k
        
        # Verify DB has documents on startup
        try:
            db = self.vector_store.get_db()
            collection = db._collection
            doc_count = collection.count()
            logger.info(f"*** VECTOR DB INITIALIZED: {doc_count} documents in collection ***")
            if doc_count == 0:
                logger.warning("*** WARNING: Vector DB is EMPTY! Run ingestion_pipeline.py first! ***")
        except Exception as e:
            logger.error(f"Could not verify DB document count: {e}")

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
