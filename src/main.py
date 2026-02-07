import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.config.config_loader import load_config
from src.ingestion.embedder import Embedder
from src.vector_db.chroma import VectorStore
from src.retrieval.retriever import Retriever
from src.llm.factory import LLMFactory
from src.tools.web_search import WebSearch
from src.utils.logger import setup_logger
from src.prompts.system_prompts import DATABASE_RAG_PROMPT, WEB_SEARCH_PROMPT, NO_ANSWER_PHRASE

logger = setup_logger("API")

app = FastAPI(title="KnowledgeHub AI API")

# Global variables for components
config = {}
llm_client = None
retriever = None
web_search_tool = None

def initialize_system():
    global config, llm_client, retriever, web_search_tool
    try:
        config_path = "config.yaml"
        if not os.path.exists(config_path) and os.path.exists("../config.yaml"):
            config_path = "../config.yaml"
            
        config = load_config(config_path)

        # 1. LLM Client
        llm_client = LLMFactory.create_llm(config)
        logger.info(f"LLM initialized: {llm_client.get_model_name()}")

        # 2. Web Search
        web_search_tool = WebSearch()

        # 3. Vector Store & Retriever
        embedder = Embedder(model_name=config['embedding']['model'])
        
        # Use absolute path - MUST match ingestion pipeline
        vector_db_path = os.path.abspath(config['vector_db']['persist_directory'])
        logger.info(f"Vector DB Path (absolute): {vector_db_path}")
              
        vector_store = VectorStore(
            persist_directory=vector_db_path,
            embedding_function=embedder.get_embedding_function()
        )
        retriever = Retriever(vector_store, top_k=config['app']['top_k'])

        logger.info("System initialized successfully.")

    except Exception as e:
        logger.critical(f"Failed to initialize system: {e}")
        raise e

# Initialize on startup
initialize_system()

# Request Models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    source_type: str  # 'db' or 'web'

# API Endpoints
@app.get("/")
async def read_root():
    return FileResponse("web/index.html")

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    logger.info(f"=== NEW QUERY: {request.query} ===")
    
    answer = ""
    sources = []
    source_type = "db"

    # Helper function to detect if LLM couldn't answer
    def is_no_answer(text: str) -> bool:
        """Check if the response indicates no answer was found."""
        no_answer_patterns = [
            "could not find",
            "couldn't find",
            "unable to find",
            "no information",
            "not found in",
            "don't have information",
            "do not have information",
            "cannot find",
            "can't find",
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in no_answer_patterns)

    # 0. Simple Typo Correction (no LLM needed)
    logger.info(f"STEP 0: Raw Query: {request.query}")
    
    # Common typos dictionary
    TYPO_FIXES = {
        "waht": "what",
        "wht": "what",
        "teh": "the",
        "adn": "and",
        "taht": "that",
        "hwo": "who",
        "woh": "who",
        "si": "is",
        "ti": "it",
        "fo": "of",
        "tis": "this",
        "thsi": "this",
        "abotu": "about",
        "aobut": "about",
    }
    
    # Apply typo fixes
    refined_query = request.query.lower()
    words = refined_query.split()
    corrected_words = [TYPO_FIXES.get(word, word) for word in words]
    refined_query = " ".join(corrected_words)
    
    if refined_query != request.query.lower():
        logger.info(f"STEP 0: Corrected typos: '{request.query}' -> '{refined_query}'")

    # 1. Attempt RAG (Vector DB)
    logger.info(f"STEP 1: Attempting RAG retrieval with query: '{refined_query}'")
    docs = retriever.retrieve(refined_query)
    
    logger.info(f"STEP 2: Retriever returned {len(docs) if docs else 0} documents.")
    
    rag_success = False
    
    if docs:
        context_text = retriever.format_docs(docs)
        logger.info(f"STEP 3: Context preview (first 300 chars): {context_text[:300]}")
        
        prompt = DATABASE_RAG_PROMPT.format(
            context=context_text, 
            query=refined_query, 
            no_answer_phrase=NO_ANSWER_PHRASE
        )
        
        logger.info("STEP 4: Sending prompt to LLM...")
        answer = llm_client.generate(prompt).strip()
        logger.info(f"STEP 5: LLM Response preview: {answer[:200]}")
        
        # Check if LLM indicated it couldn't find the answer
        if is_no_answer(answer):
            logger.info("STEP 6: LLM could not answer from context. FALLBACK to Web...")
            rag_success = False
        else:
            logger.info("STEP 6: RAG SUCCESS!")
            rag_success = True
            sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
            source_type = "db"
    else:
        logger.info("STEP 3: No documents found in DB. FALLBACK to Web...")
        rag_success = False

    # 2. Fallback to Web Search
    if not rag_success:
        if config['brain']['use_web_search']:
            logger.info("FALLBACK: Performing Web Search...")
            source_type = "web"
            # Use refined query for web search too
            search_results = web_search_tool.search_query(refined_query)
            prompt = WEB_SEARCH_PROMPT.format(query=refined_query, search_results=search_results)
            answer = llm_client.generate(prompt)
            sources = ["Web Search"]
        else:
            answer = "I could not find this information in the internal documents, and Web Search is disabled."
            source_type = "none"

    logger.info(f"=== FINAL: source_type={source_type} ===")
    return QueryResponse(answer=answer, sources=sources, source_type=source_type)

# Mount Static Files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['server']['host'], port=config['server']['port'])
