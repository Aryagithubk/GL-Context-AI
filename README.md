# KnowledgeHub AI

A local, privacy-focused RAG system for querying company documents.

## Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Pull Models**:
    Since you have limited RAM (approx 2GB), we use the 1B model.
    ```bash
    ollama pull llama3.2:1b
    ollama pull nomic-embed-text
    ```

3.  **Add Data**:
    Place your PDF, TXT, or JSON files in the `data/` folder.

4.  **Ingest Data**:
    Run the ingestion pipeline to process documents and save them to the vector database.
    ```bash
    python src/ingestion_pipeline.py
    ```

5.  **Run Server**:
    Start the backend API.
    ```bash
    python src/main.py
    ```

6.  **Access UI**:
    Open `web/index.html` in your browser.

## Architecture
- **LLM**: Llama 3.2 (1B) via Ollama
- **Embeddings**: Nomic-Embed-Text via Ollama
- **Vector DB**: ChromaDB (Local)
- **Backend**: FastAPI
- **Frontend**: HTML/JS
