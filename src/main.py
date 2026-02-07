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
from src.llm.ollama import OllamaClient
from src.utils.logger import setup_logger

logger = setup_logger("API")

app = FastAPI(title="KnowledgeHub AI API")

# Load Config & Initialize Components
try:
    config = load_config("config.yaml")

    # Components
    embedder = Embedder(model_name=config['embedding']['model'])
    vector_store = VectorStore(
        persist_directory=config['vector_db']['persist_directory'],
        embedding_function=embedder.get_embedding_function()
    )
    retriever = Retriever(vector_store, top_k=config['app']['top_k'])
    llm_client = OllamaClient(
        model_name=config['llm']['model'],
        temperature=config['llm']['temperature']
    )

    logger.info("System initialized successfully.")

except Exception as e:
    logger.critical(f"Failed to initialize system: {e}")
    sys.exit(1)

# Request Models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

# API Endpoints
@app.get("/")
async def read_root():
    return FileResponse("web/index.html")

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    logger.info(f"Received query: {request.query}")
    
    # 1. Retrieve Context
    docs = retriever.retrieve(request.query)
    context = retriever.format_docs(docs)
    
    # 2. Build Prompt
    prompt = f"""You are a helpful assistant answering questions based strictly on the following company documents.
    
    Context:
    {context}
    
    Question:
    {request.query}
    
    Answer clearly and concisely. If the answer is not in the context, say "I don't know based on the available documents."
    """
    
    # 3. Generate Answer
    answer = llm_client.generate(prompt)
    
    # 4. Extract Sources
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
    
    return QueryResponse(answer=answer, sources=sources)

# Mount Static Files (CSS/JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['server']['host'], port=config['server']['port'])
