# OmniQuery AI - Multi-Agent Intelligent Query System

## Complete Architecture Document

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [High-Level Design (HLD)](#3-high-level-design-hld)
4. [Architectural Diagrams](#4-architectural-diagrams)
5. [Folder Structure](#5-folder-structure)
6. [Low-Level Design (LLD)](#6-low-level-design-lld)
7. [Additional Data Sources & Agents](#7-additional-data-sources--agents)
8. [Configuration System](#8-configuration-system)
9. [Security Architecture](#9-security-architecture)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Observability & Monitoring](#11-observability--monitoring)
12. [Scalability & Performance](#12-scalability--performance)

---

## 1. Executive Summary

**OmniQuery** is a modular, multi-agent AI system that unifies querying across heterogeneous data sources — documents, databases, wikis, the web, and more — through a single natural language interface. It uses LangGraph as the orchestration layer to route user queries to specialized agents, each optimized for a specific data domain. The system is LLM-agnostic (OpenAI, Gemini, Anthropic, Grok, local models), supports role-based access control, and outputs responses in configurable formats.

### Core Principles

| Principle | Description |
|---|---|
| **Modularity** | Each agent is a self-contained unit; new agents can be added without modifying existing code |
| **LLM Agnosticism** | Swap LLMs via configuration — no code changes required |
| **Security First** | RBAC at every layer; query sandboxing; credential isolation |
| **Extensibility** | Plugin architecture for new data sources, output formats, and middleware |
| **Observability** | End-to-end tracing, cost tracking, and audit logging |


---

## 2. System Overview

### 2.1 What the System Does

```
User (Natural Language Query)
        │
        ▼
┌──────────────────────────┐
│   API Gateway / Interface │  ←  REST / WebSocket / CLI / SDK
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   Query Preprocessor      │  ←  Intent classification, entity extraction, query rewrite
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   Orchestrator (LangGraph) │  ←  Stateful graph routing, multi-agent coordination
└──────────┬───────────────┘
           │
     ┌─────┼─────┬──────┬──────┬──────┬──────┐
     ▼     ▼     ▼      ▼      ▼      ▼      ▼
   Doc   DB   Confluence Web  Email  API   Slack
   Agent Agent  Agent   Agent Agent Agent Agent  ...
           │
           ▼
┌──────────────────────────┐
│   Response Synthesizer    │  ←  Merge multi-agent results, resolve conflicts
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   Output Formatter        │  ←  Markdown / HTML / JSON / PDF / Plain Text
└──────────┘
```

### 2.2 Key Actors

| Actor | Description |
|---|---|
| **End User** | Asks natural language questions |
| **Admin** | Configures agents, manages RBAC, monitors system |
| **Super Admin** | Full control including destructive DB operations |
| **Developer** | Extends system with new agents/plugins |
| **System** | Background jobs — indexing, embedding, cache refresh |

---

## 3. High-Level Design (HLD)

### 3.1 Component Architecture

#### Layer 1: Interface Layer
- **REST API Server** (FastAPI) — Primary interface for external clients
- **WebSocket Server** — Streaming responses for real-time UX
- **CLI Interface** — Developer/admin tooling
- **SDK** — Python/JS client libraries for programmatic access

#### Layer 2: Processing Pipeline
- **Authentication & Authorization** — JWT/OAuth2 + RBAC engine
- **Query Preprocessor** — Intent detection, entity extraction, query rewriting, language detection
- **Rate Limiter** — Per-user, per-role, per-agent throttling
- **Session Manager** — Conversation history, context window management

#### Layer 3: Orchestration Layer (Brain)
- **LangGraph Orchestrator** — The central state machine that:
  - Classifies the query intent
  - Routes to one or more agents (parallel or sequential)
  - Handles agent failures with fallback strategies
  - Merges multi-agent responses
  - Manages conversation state across turns

#### Layer 4: Agent Layer
Each agent follows a uniform interface (`BaseAgent`):

```
┌─────────────────────────────────────┐
│              BaseAgent              │
├─────────────────────────────────────┤
│ + name: str                         │
│ + description: str                  │
│ + supported_query_types: List[str]  │
│ + required_config: Dict             │
├─────────────────────────────────────┤
│ + initialize() -> None              │
│ + can_handle(query) -> float        │   confidence score 0-1
│ + execute(query, context) -> Result │
│ + health_check() -> HealthStatus    │
└─────────────────────────────────────┘
```

**Core Agents:**

| Agent | Data Source | Key Capabilities |
|---|---|---|
| `DocAgent` | Local/Cloud files (PDF, DOCX, TXT, CSV, etc.) | Embedding creation, vector search, chunk management, multi-format parsing |
| `DBAgent` | SQL/NoSQL databases | NL-to-SQL, query execution, RBAC-gated operations, schema introspection |
| `ConfluenceAgent` | Atlassian Confluence | API-based search, space/page filtering, permission-aware retrieval |
| `WebAgent` | Internet | Web search, URL scraping, content summarization |

#### Layer 5: Infrastructure Layer
- **Vector Database** — ChromaDB / Pinecone / Weaviate / Qdrant / pgvector
- **Cache Layer** — Redis for query caching, embedding caching, session state
- **Message Queue** — Celery + Redis/RabbitMQ for async indexing jobs
- **Object Storage** — S3/MinIO/GCS for document storage
- **Relational DB** — PostgreSQL for system metadata, audit logs, user management

#### Layer 6: Cross-Cutting Concerns
- **LLM Provider Abstraction** — Unified interface for OpenAI, Gemini, Anthropic, Grok, Ollama, vLLM, etc.
- **Output Formatter** — Pluggable formatters (MD, HTML, JSON, PDF, plain text, structured tables)
- **Observability Stack** — OpenTelemetry + Prometheus + Grafana + LangSmith
- **Audit Logger** — Every query, every agent call, every DB operation logged

### 3.2 Data Flow (Happy Path)

```
1. User sends query: "What were our Q3 revenue numbers?"
2. API Gateway authenticates user (JWT), extracts role (admin)
3. Query Preprocessor:
   a. Detects intent: "data_retrieval"
   b. Extracts entities: {metric: "revenue", period: "Q3"}
   c. Detects ambiguity: multiple possible sources
4. Orchestrator (LangGraph):
   a. Evaluates agent confidence scores:
      - DBAgent: 0.85 (financial data likely in DB)
      - DocAgent: 0.60 (might be in reports)
      - ConfluenceAgent: 0.40 (wiki might have summaries)
   b. Routes to DBAgent (primary) + DocAgent (secondary) in parallel
5. DBAgent:
   a. Loads schema context (tables: revenue, quarters, departments)
   b. Generates SQL: SELECT SUM(revenue) FROM financials WHERE quarter = 'Q3'
   c. RBAC check: admin can execute SELECT → ✅
   d. Executes query → returns {total_revenue: 4200000}
6. DocAgent:
   a. Vector search on "Q3 revenue" → retrieves quarterly report chunks
   b. Extracts supporting context
7. Response Synthesizer:
   a. Primary answer from DBAgent: "$4.2M"
   b. Enhanced with DocAgent context: quarterly report narrative
   c. Conflict resolution: numbers match → high confidence
8. Output Formatter:
   a. User config says "markdown"
   b. Formats response with tables, highlights, sources
9. Response returned to user with citations
```

### 3.3 Error & Fallback Flow

```
1. Agent fails (timeout, API error, no results)
        │
        ▼
2. Orchestrator checks fallback strategy:
   ├── RETRY: Retry same agent with modified query (max 2 retries)
   ├── FALLBACK: Route to next-best agent
   ├── DEGRADE: Return partial answer with disclaimer
   └── ESCALATE: Notify admin, return "unable to answer"
        │
        ▼
3. All attempts exhausted?
   ├── YES → WebAgent as last resort (if enabled)
   └── NO  → Continue fallback chain
```

---

## 4. Architectural Diagrams

### 4.1 System Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL ACTORS                              │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│   │ End User │  │  Admin   │  │Developer │  │ External System  │   │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│        │              │              │                 │             │
└────────┼──────────────┼──────────────┼─────────────────┼─────────────┘
         │              │              │                 │
         ▼              ▼              ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    OmniQuery System                                  │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    API Gateway                               │   │
│   │              (Auth, Rate Limit, Routing)                     │   │
│   └──────────────────────┬──────────────────────────────────────┘   │
│                          │                                          │
│   ┌──────────────────────▼──────────────────────────────────────┐   │
│   │              Orchestration Engine (LangGraph)                 │   │
│   │         ┌────────┬────────┬─────────┬──────────┐             │   │
│   │         ▼        ▼        ▼         ▼          ▼             │   │
│   │      DocAgent  DBAgent ConfAgent WebAgent  ...Agent          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                          │                                          │
│   ┌──────────────────────▼──────────────────────────────────────┐   │
│   │              Infrastructure Layer                            │   │
│   │   VectorDB │ Cache │ Queue │ Storage │ SystemDB │ LLMs      │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         │              │              │                 │
         ▼              ▼              ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL DATA SOURCES                           │
│                                                                     │
│  ┌────────┐ ┌─────┐ ┌──────────┐ ┌─────┐ ┌───────┐ ┌──────────┐  │
│  │  Docs  │ │ DBs │ │Confluence│ │ Web │ │ Email │ │   APIs   │  │
│  └────────┘ └─────┘ └──────────┘ └─────┘ └───────┘ └──────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 LangGraph Orchestrator — State Machine

```
                        ┌──────────────┐
                        │  START_NODE  │
                        │  (receive    │
                        │   query)     │
                        └──────┬───────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │  PREPROCESS_NODE │
                     │  - intent detect │
                     │  - entity extract│
                     │  - query rewrite │
                     └────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  CLASSIFY_NODE    │
                    │  - score agents   │
                    │  - select targets │
                    │  - plan execution │
                    └────────┬──────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ AGENT_1  │ │ AGENT_2  │ │ AGENT_N  │   (parallel execution)
        │  (exec)  │ │  (exec)  │ │  (exec)  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             ▼             ▼             ▼
          ┌────┐        ┌────┐        ┌────┐
          │ OK │        │FAIL│        │ OK │
          └──┬─┘        └──┬─┘        └──┬─┘
             │             │             │
             │        ┌────▼─────┐       │
             │        │ FALLBACK │       │
             │        │  NODE    │       │
             │        └────┬─────┘       │
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │  SYNTHESIZE_NODE │
                 │  - merge results │
                 │  - resolve conf. │
                 │  - rank sources  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   FORMAT_NODE    │
                 │  - apply format  │
                 │  - add citations │
                 │  - add metadata  │
                 └────────┬─────────┘
                          │
                          ▼
                   ┌────────────┐
                   │  END_NODE  │
                   │  (return)  │
                   └────────────┘
```

### 4.3 Agent Internal Architecture (DocAgent Example)

```
┌─────────────────────────────────────────────────────────────────┐
│                         DocAgent                                 │
│                                                                  │
│  ┌───────────────┐    ┌──────────────────┐                      │
│  │ Document       │    │  Ingestion        │                      │
│  │ Loader         │───▶│  Pipeline         │                      │
│  │                │    │                    │                      │
│  │ - LocalLoader  │    │ ┌──────────────┐  │                      │
│  │ - S3Loader     │    │ │  Parser      │  │  Parsers:            │
│  │ - GCSLoader    │    │ │  (Unstructured│  │  - PDF (PyMuPDF)     │
│  │ - AzureBlobLdr │    │ │   / custom)  │  │  - DOCX (docx2txt)   │
│  │ - URLLoader    │    │ └──────┬───────┘  │  - CSV/XLSX (pandas) │
│  │ - GitLoader    │    │        │          │  - TXT/MD (raw)      │
│  └───────────────┘    │        ▼          │  - HTML (BeautifulSoup│
│                        │ ┌──────────────┐  │  - Code files        │
│                        │ │  Chunker     │  │                      │
│                        │ │  - Recursive │  │                      │
│                        │ │  - Semantic  │  │                      │
│                        │ │  - Fixed     │  │                      │
│                        │ └──────┬───────┘  │                      │
│                        │        │          │                      │
│                        │        ▼          │                      │
│                        │ ┌──────────────┐  │                      │
│                        │ │  Embedder    │  │                      │
│                        │ │  (model from │  │                      │
│                        │ │   config)    │  │                      │
│                        │ └──────┬───────┘  │                      │
│                        │        │          │                      │
│                        └────────┼──────────┘                      │
│                                 │                                 │
│                                 ▼                                 │
│                        ┌──────────────────┐                      │
│                        │   Vector Store    │                      │
│                        │   (ChromaDB /     │                      │
│                        │    Pinecone /     │                      │
│                        │    Qdrant)        │                      │
│                        └────────┬─────────┘                      │
│                                 │                                 │
│  ┌───────────────┐              │                                 │
│  │ Query Engine  │◀─────────────┘                                 │
│  │               │                                                │
│  │ - Retriever   │  Retrieval Strategies:                        │
│  │   (k-NN +     │  - Dense retrieval (embeddings)               │
│  │    reranker)  │  - Hybrid (dense + BM25 sparse)               │
│  │               │  - Multi-query (LLM generates variants)       │
│  │ - Reranker    │  - HyDE (hypothetical doc embeddings)         │
│  │   (Cohere /   │                                                │
│  │    cross-enc) │                                                │
│  └───────┬───────┘                                                │
│          │                                                        │
│          ▼                                                        │
│  ┌───────────────┐                                                │
│  │ Context       │                                                │
│  │ Builder       │  Builds prompt with retrieved chunks           │
│  │ + LLM Call    │  + user query → natural language answer        │
│  └───────────────┘                                                │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 4.4 DBAgent Internal Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          DBAgent                                 │
│                                                                  │
│  ┌─────────────────┐                                            │
│  │ Schema Loader   │  Sources:                                  │
│  │                 │  - Live DB introspection (SQLAlchemy)       │
│  │                 │  - SQL DDL files                            │
│  │                 │  - Manual schema config                     │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Schema Context  │  Contains:                                 │
│  │ Builder         │  - Table names, columns, types              │
│  │                 │  - Foreign keys, relationships              │
│  │                 │  - Sample data (optional)                   │
│  │                 │  - Business glossary mapping                │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐     ┌──────────────────┐                   │
│  │ NL-to-SQL       │────▶│ Query Validator   │                   │
│  │ Generator       │     │                    │                   │
│  │ (LLM + schema)  │     │ - Syntax check     │                   │
│  └─────────────────┘     │ - Injection guard   │                   │
│                          │ - RBAC policy check │                   │
│                          └─────────┬──────────┘                   │
│                                    │                              │
│                          ┌─────────▼──────────┐                   │
│                          │  RBAC Engine        │                   │
│                          │                      │                   │
│                          │  Role Permissions:   │                   │
│                          │  ┌─────────────────┐ │                   │
│                          │  │ viewer:         │ │                   │
│                          │  │   SELECT only   │ │                   │
│                          │  │ admin:          │ │                   │
│                          │  │   SELECT, INSERT│ │                   │
│                          │  │   CREATE TABLE  │ │                   │
│                          │  │ superuser:      │ │                   │
│                          │  │   ALL (DROP,    │ │                   │
│                          │  │   DELETE, ALTER)│ │                   │
│                          │  └─────────────────┘ │                   │
│                          └─────────┬──────────┘                   │
│                                    │                              │
│                          ┌─────────▼──────────┐                   │
│                          │  SQL Executor       │                   │
│                          │  (Sandboxed)        │                   │
│                          │                      │                   │
│                          │ - Connection pool    │                   │
│                          │ - Read replica pref  │                   │
│                          │ - Timeout limits     │                   │
│                          │ - Row limit (1000)   │                   │
│                          │ - Query explain plan │                   │
│                          └─────────┬──────────┘                   │
│                                    │                              │
│                          ┌─────────▼──────────┐                   │
│                          │ Result Interpreter  │                   │
│                          │ (LLM)               │                   │
│                          │ - Tabular → NL      │                   │
│                          │ - Aggregation desc  │                   │
│                          │ - Chart suggestions │                   │
│                          └────────────────────┘                   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 5. Folder Structure

```
omniquery/
│
├── README.md
├── LICENSE
├── pyproject.toml                    # Project metadata, dependencies (Poetry/PDM)
├── Makefile                          # Common commands: lint, test, run, docker
├── docker-compose.yml                # Local dev stack (Redis, Postgres, ChromaDB)
├── Dockerfile                        # Production container
├── .env.example                      # Environment variable template
├── .gitignore
│
├── config/                           # All configuration files
│   ├── __init__.py
│   ├── settings.py                   # Pydantic Settings — loads from env/yaml
│   ├── default.yaml                  # Default configuration
│   ├── llm_providers.yaml            # LLM provider configs (OpenAI, Gemini, etc.)
│   ├── agents.yaml                   # Agent-specific configs (enabled/disabled, params)
│   ├── rbac_policies.yaml            # Role-based access control definitions
│   ├── vector_store.yaml             # Vector DB connection and collection configs
│   ├── database_sources.yaml         # DB connections for DBAgent
│   └── logging.yaml                  # Logging configuration
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/                          # Interface Layer
│   │   ├── __init__.py
│   │   ├── app.py                    # FastAPI application factory
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── query.py              # POST /query — main query endpoint
│   │   │   ├── agents.py             # GET /agents — list agents, health
│   │   │   ├── admin.py              # Admin endpoints (indexing, config)
│   │   │   ├── auth.py               # Login, token refresh, user management
│   │   │   └── websocket.py          # WS /ws/query — streaming responses
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py     # JWT validation, role extraction
│   │   │   ├── rate_limiter.py       # Token bucket rate limiting
│   │   │   ├── cors.py               # CORS configuration
│   │   │   └── request_logger.py     # Request/response logging
│   │   ├── schemas/                  # Pydantic request/response models
│   │   │   ├── __init__.py
│   │   │   ├── query_schema.py       # QueryRequest, QueryResponse
│   │   │   ├── agent_schema.py       # AgentInfo, AgentHealth
│   │   │   └── auth_schema.py        # LoginRequest, TokenResponse
│   │   └── dependencies.py           # FastAPI dependency injection
│   │
│   ├── core/                         # Core Business Logic
│   │   ├── __init__.py
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py              # LangGraph state machine definition
│   │   │   ├── state.py              # OmniQueryState (TypedDict for graph state)
│   │   │   ├── router.py             # Agent routing logic (confidence scoring)
│   │   │   ├── nodes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── preprocess.py     # Query preprocessing node
│   │   │   │   ├── classify.py       # Intent classification node
│   │   │   │   ├── execute.py        # Agent execution node
│   │   │   │   ├── synthesize.py     # Response synthesis node
│   │   │   │   ├── format.py         # Output formatting node
│   │   │   │   └── fallback.py       # Error handling / fallback node
│   │   │   └── edges.py              # Conditional edge functions
│   │   │
│   │   ├── preprocessor/
│   │   │   ├── __init__.py
│   │   │   ├── intent_classifier.py  # Classifies query intent
│   │   │   ├── entity_extractor.py   # Extracts entities (dates, names, etc.)
│   │   │   ├── query_rewriter.py     # Rewrites ambiguous queries
│   │   │   └── language_detector.py  # Detects query language
│   │   │
│   │   ├── synthesizer/
│   │   │   ├── __init__.py
│   │   │   ├── response_merger.py    # Merges multi-agent results
│   │   │   ├── conflict_resolver.py  # Handles contradictory answers
│   │   │   └── citation_builder.py   # Adds source citations
│   │   │
│   │   └── session/
│   │       ├── __init__.py
│   │       ├── session_manager.py    # Conversation history management
│   │       ├── context_window.py     # Token-aware context truncation
│   │       └── memory_store.py       # Short-term + long-term memory
│   │
│   ├── agents/                       # All Agent Implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Abstract BaseAgent class
│   │   ├── agent_registry.py         # Dynamic agent registration & discovery
│   │   │
│   │   ├── doc_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # DocAgent implementation
│   │   │   ├── loaders/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── local_loader.py   # Load from local filesystem
│   │   │   │   ├── s3_loader.py      # Load from AWS S3
│   │   │   │   ├── gcs_loader.py     # Load from Google Cloud Storage
│   │   │   │   ├── azure_blob_loader.py  # Load from Azure Blob
│   │   │   │   ├── git_loader.py     # Load from Git repositories
│   │   │   │   └── url_loader.py     # Load from URLs
│   │   │   ├── parsers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pdf_parser.py     # PDF parsing (PyMuPDF / pdfplumber)
│   │   │   │   ├── docx_parser.py    # DOCX parsing
│   │   │   │   ├── csv_parser.py     # CSV/XLSX parsing
│   │   │   │   ├── html_parser.py    # HTML parsing
│   │   │   │   ├── markdown_parser.py # Markdown parsing
│   │   │   │   ├── code_parser.py    # Source code parsing
│   │   │   │   └── image_parser.py   # OCR-based image text extraction
│   │   │   ├── chunkers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── recursive_chunker.py    # Recursive text splitting
│   │   │   │   ├── semantic_chunker.py     # Semantic-boundary chunking
│   │   │   │   └── fixed_chunker.py        # Fixed-size chunking
│   │   │   ├── retrievers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dense_retriever.py      # Pure embedding search
│   │   │   │   ├── hybrid_retriever.py     # Dense + BM25 sparse
│   │   │   │   ├── multi_query_retriever.py # LLM-generated query variants
│   │   │   │   └── hyde_retriever.py       # Hypothetical Document Embeddings
│   │   │   └── rerankers/
│   │   │       ├── __init__.py
│   │   │       ├── cross_encoder_reranker.py
│   │   │       └── cohere_reranker.py
│   │   │
│   │   ├── db_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # DBAgent implementation
│   │   │   ├── schema_loader.py      # Load schema from DB / DDL files
│   │   │   ├── schema_context.py     # Build schema context for LLM
│   │   │   ├── nl_to_sql.py          # Natural language to SQL generator
│   │   │   ├── query_validator.py    # SQL syntax + injection validation
│   │   │   ├── sql_executor.py       # Sandboxed SQL execution engine
│   │   │   ├── rbac_engine.py        # Role-based query authorization
│   │   │   ├── result_interpreter.py # Tabular results → NL narrative
│   │   │   └── connectors/
│   │   │       ├── __init__.py
│   │   │       ├── postgres_connector.py
│   │   │       ├── mysql_connector.py
│   │   │       ├── sqlite_connector.py
│   │   │       ├── mssql_connector.py
│   │   │       ├── mongodb_connector.py  # NoSQL support
│   │   │       └── bigquery_connector.py # Cloud warehouse
│   │   │
│   │   ├── confluence_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # ConfluenceAgent implementation
│   │   │   ├── confluence_client.py  # Atlassian API wrapper
│   │   │   ├── search_engine.py      # CQL query builder
│   │   │   ├── content_extractor.py  # Extract text from Confluence pages
│   │   │   └── space_filter.py       # Permission-aware space filtering
│   │   │
│   │   ├── web_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # WebAgent implementation
│   │   │   ├── search_providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── google_search.py  # Google Custom Search / SerpAPI
│   │   │   │   ├── bing_search.py    # Bing Search API
│   │   │   │   ├── duckduckgo_search.py  # DuckDuckGo (no API key)
│   │   │   │   └── tavily_search.py  # Tavily (AI-optimized search)
│   │   │   ├── scraper.py            # Web page content extractor
│   │   │   └── summarizer.py         # Summarize scraped content
│   │   │
│   │   ├── email_agent/              # Future: Email data source
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── imap_client.py
│   │   │   └── email_parser.py
│   │   │
│   │   ├── api_agent/                # Future: REST API data source
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── api_registry.py
│   │   │   └── response_mapper.py
│   │   │
│   │   ├── slack_agent/              # Future: Slack data source
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── slack_client.py
│   │   │
│   │   ├── jira_agent/               # Future: Jira data source
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── jira_client.py
│   │   │
│   │   └── notion_agent/             # Future: Notion data source
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       └── notion_client.py
│   │
│   ├── llm/                          # LLM Provider Abstraction
│   │   ├── __init__.py
│   │   ├── base_provider.py          # Abstract LLM provider interface
│   │   ├── provider_factory.py       # Factory to instantiate providers
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── openai_provider.py    # OpenAI (GPT-4, GPT-4o, etc.)
│   │   │   ├── anthropic_provider.py # Anthropic (Claude)
│   │   │   ├── gemini_provider.py    # Google Gemini
│   │   │   ├── grok_provider.py      # xAI Grok
│   │   │   ├── ollama_provider.py    # Ollama (local models)
│   │   │   ├── vllm_provider.py      # vLLM (local serving)
│   │   │   ├── azure_openai_provider.py  # Azure OpenAI
│   │   │   └── huggingface_provider.py   # HuggingFace Inference
│   │   ├── embedding/
│   │   │   ├── __init__.py
│   │   │   ├── base_embedding.py
│   │   │   ├── openai_embedding.py
│   │   │   ├── sentence_transformer_embedding.py
│   │   │   └── cohere_embedding.py
│   │   ├── prompt_templates/
│   │   │   ├── __init__.py
│   │   │   ├── system_prompts.py
│   │   │   ├── agent_prompts.py
│   │   │   ├── synthesis_prompts.py
│   │   │   └── classification_prompts.py
│   │   └── token_manager.py          # Token counting, budget management
│   │
│   ├── vectorstore/                  # Vector Database Abstraction
│   │   ├── __init__.py
│   │   ├── base_store.py             # Abstract vector store interface
│   │   ├── store_factory.py          # Factory for vector store backends
│   │   ├── chroma_store.py           # ChromaDB implementation
│   │   ├── pinecone_store.py         # Pinecone implementation
│   │   ├── qdrant_store.py           # Qdrant implementation
│   │   ├── weaviate_store.py         # Weaviate implementation
│   │   └── pgvector_store.py         # pgvector (PostgreSQL) implementation
│   │
│   ├── auth/                         # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── jwt_handler.py            # JWT token generation/validation
│   │   ├── rbac.py                   # Role-based access control engine
│   │   ├── user_manager.py           # User CRUD operations
│   │   └── permission_models.py      # Permission & role definitions
│   │
│   ├── utils/                        # Shared Utilities
│   │   ├── __init__.py
│   │   ├── output_formatter/
│   │   │   ├── __init__.py
│   │   │   ├── base_formatter.py     # Abstract formatter interface
│   │   │   ├── markdown_formatter.py # Markdown output
│   │   │   ├── html_formatter.py     # HTML output
│   │   │   ├── json_formatter.py     # Structured JSON output
│   │   │   ├── pdf_formatter.py      # PDF generation
│   │   │   ├── table_formatter.py    # ASCII/Unicode table output
│   │   │   └── plain_formatter.py    # Plain text output
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   ├── cache_manager.py      # Unified cache interface
│   │   │   ├── redis_cache.py        # Redis backend
│   │   │   ├── in_memory_cache.py    # In-memory (for dev/testing)
│   │   │   └── semantic_cache.py     # Embedding-based semantic caching
│   │   ├── logging/
│   │   │   ├── __init__.py
│   │   │   ├── structured_logger.py  # JSON structured logging
│   │   │   ├── audit_logger.py       # Audit trail for compliance
│   │   │   └── cost_tracker.py       # LLM API cost tracking
│   │   ├── telemetry/
│   │   │   ├── __init__.py
│   │   │   ├── tracer.py             # OpenTelemetry tracing
│   │   │   ├── metrics.py            # Prometheus metrics
│   │   │   └── langsmith_tracer.py   # LangSmith integration
│   │   ├── crypto.py                 # Encryption utilities for credentials
│   │   ├── validators.py             # Input validation helpers
│   │   └── helpers.py                # Misc utility functions
│   │
│   └── tasks/                        # Background Tasks
│       ├── __init__.py
│       ├── celery_app.py             # Celery application configuration
│       ├── indexing_tasks.py         # Document indexing background jobs
│       ├── cache_refresh_tasks.py    # Periodic cache refresh
│       └── health_check_tasks.py     # Periodic health checks
│
├── tests/                            # Test Suite
│   ├── __init__.py
│   ├── conftest.py                   # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── agents/
│   │   │   ├── test_doc_agent.py
│   │   │   ├── test_db_agent.py
│   │   │   ├── test_confluence_agent.py
│   │   │   └── test_web_agent.py
│   │   ├── core/
│   │   │   ├── test_orchestrator.py
│   │   │   ├── test_preprocessor.py
│   │   │   └── test_synthesizer.py
│   │   ├── llm/
│   │   │   └── test_providers.py
│   │   └── utils/
│   │       ├── test_output_formatter.py
│   │       └── test_cache.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_doc_agent_e2e.py
│   │   ├── test_db_agent_e2e.py
│   │   └── test_orchestrator_e2e.py
│   └── fixtures/
│       ├── sample_docs/
│       ├── sample_schemas/
│       └── mock_responses/
│
├── scripts/                          # Operational Scripts
│   ├── setup_dev.sh                  # Local dev environment setup
│   ├── seed_data.py                  # Seed test data
│   ├── migrate_db.py                 # Database migrations
│   └── benchmark.py                  # Performance benchmarking
│
├── docs/                             # Project Documentation
│   ├── architecture.md
│   ├── api_reference.md
│   ├── deployment_guide.md
│   ├── adding_new_agent.md           # Guide for extending with new agents
│   └── configuration_guide.md
│
└── deployments/                      # Deployment Configs
    ├── kubernetes/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── ingress.yaml
    │   ├── configmap.yaml
    │   └── secrets.yaml
    ├── terraform/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── helm/
        └── omniquery/
            ├── Chart.yaml
            ├── values.yaml
            └── templates/
```

---

## 6. Low-Level Design (LLD)

### 6.1 Core Interfaces & Data Models

#### 6.1.1 Query Flow Data Models

```python
# ──────────────────────────────────────────────
# src/api/schemas/query_schema.py
# ──────────────────────────────────────────────

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PLAIN = "plain"
    PDF = "pdf"
    TABLE = "table"


class QueryRequest(BaseModel):
    """Incoming query from user"""
    query: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    output_format: OutputFormat = OutputFormat.MARKDOWN
    target_agents: Optional[List[str]] = None  # Force specific agents
    max_sources: int = Field(default=3, ge=1, le=10)
    include_citations: bool = True
    language: Optional[str] = None  # Response language
    metadata: Optional[Dict[str, Any]] = None


class SourceCitation(BaseModel):
    """Citation for a piece of retrieved information"""
    agent_name: str
    source_type: str          # "document", "database", "confluence", "web"
    source_identifier: str    # File path, URL, table name, page title
    relevance_score: float
    excerpt: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentResult(BaseModel):
    """Result from a single agent"""
    agent_name: str
    status: str               # "success", "partial", "failed"
    answer: Optional[str] = None
    confidence: float = 0.0
    citations: List[SourceCitation] = []
    execution_time_ms: float
    token_usage: Dict[str, int] = {}  # {"prompt": N, "completion": M}
    error: Optional[str] = None
    raw_data: Optional[Any] = None    # SQL results, doc chunks, etc.


class QueryResponse(BaseModel):
    """Final response to user"""
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    answer: str
    confidence: float
    sources: List[SourceCitation]
    agents_used: List[str]
    output_format: OutputFormat
    execution_time_ms: float
    total_token_usage: Dict[str, int]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
```

#### 6.1.2 LangGraph Orchestrator State

```python
# ──────────────────────────────────────────────
# src/core/orchestrator/state.py
# ──────────────────────────────────────────────

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentPlan(TypedDict):
    """Execution plan for a single agent"""
    agent_name: str
    confidence: float
    priority: int           # 1 = primary, 2 = secondary, etc.
    modified_query: str     # Agent-specific query variant
    timeout_ms: int


class OmniQueryState(TypedDict):
    """Complete state flowing through the LangGraph"""
    # Input
    query_id: str
    original_query: str
    user_id: str
    user_role: str
    session_id: str
    output_format: str

    # Preprocessing results
    intent: str                           # "data_retrieval", "analysis", etc.
    entities: Dict[str, Any]              # Extracted entities
    rewritten_query: str                  # LLM-improved query
    detected_language: str

    # Routing
    agent_plans: List[AgentPlan]          # Ordered list of agents to execute
    current_agent_index: int

    # Execution
    agent_results: List[Dict[str, Any]]   # Results from each agent
    failed_agents: List[str]
    retry_count: int

    # Synthesis
    synthesized_answer: str
    citations: List[Dict[str, Any]]
    overall_confidence: float

    # Output
    formatted_response: str
    total_token_usage: Dict[str, int]
    execution_start_time: float

    # Conversation
    messages: Annotated[List[BaseMessage], add_messages]
```

#### 6.1.3 LangGraph State Machine Definition

```python
# ──────────────────────────────────────────────
# src/core/orchestrator/graph.py
# ──────────────────────────────────────────────

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import OmniQueryState
from .nodes import (
    preprocess_node,
    classify_node,
    execute_agents_node,
    synthesize_node,
    format_node,
    fallback_node,
)
from .edges import (
    should_execute_more_agents,
    needs_fallback,
    route_after_execution,
)


def build_orchestrator_graph() -> StateGraph:
    """Build the LangGraph state machine for query orchestration"""

    graph = StateGraph(OmniQueryState)

    # ── Add nodes ──
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("classify", classify_node)
    graph.add_node("execute_agent", execute_agents_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("format", format_node)
    graph.add_node("fallback", fallback_node)

    # ── Add edges ──
    graph.set_entry_point("preprocess")
    graph.add_edge("preprocess", "classify")
    graph.add_edge("classify", "execute_agent")

    # After agent execution, decide next step
    graph.add_conditional_edges(
        "execute_agent",
        route_after_execution,
        {
            "execute_more": "execute_agent",   # More agents to run
            "fallback": "fallback",            # Agent failed, try fallback
            "synthesize": "synthesize",        # All agents done
        }
    )

    graph.add_conditional_edges(
        "fallback",
        needs_fallback,
        {
            "retry": "execute_agent",          # Retry with modified query
            "synthesize": "synthesize",        # Give up, use what we have
        }
    )

    graph.add_edge("synthesize", "format")
    graph.add_edge("format", END)

    # ── Compile with checkpointing ──
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
```

#### 6.1.4 Base Agent Interface

```python
# ──────────────────────────────────────────────
# src/agents/base_agent.py
# ──────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from enum import Enum
import time


class AgentStatus(str, Enum):
    READY = "ready"
    INITIALIZING = "initializing"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class HealthStatus(BaseModel):
    agent_name: str
    status: AgentStatus
    message: str = "OK"
    last_check: float
    dependencies: Dict[str, str] = {}  # {"vector_db": "healthy", "llm": "healthy"}


class AgentContext(BaseModel):
    """Context passed to every agent execution"""
    query: str
    original_query: str
    user_id: str
    user_role: str
    session_id: str
    intent: str
    entities: Dict[str, Any]
    conversation_history: List[Dict[str, str]] = []
    max_results: int = 5
    timeout_ms: int = 30000


class AgentResponse(BaseModel):
    """Standardized agent response"""
    success: bool
    answer: Optional[str] = None
    confidence: float = 0.0
    sources: List[Dict[str, Any]] = []
    raw_data: Optional[Any] = None
    token_usage: Dict[str, int] = {"prompt": 0, "completion": 0}
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, config: Dict[str, Any], llm_provider: Any):
        self.config = config
        self.llm = llm_provider
        self._status = AgentStatus.INITIALIZING
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this agent does"""
        ...

    @property
    @abstractmethod
    def supported_intents(self) -> List[str]:
        """List of query intents this agent can handle"""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """One-time setup (connect to DBs, load indices, etc.)"""
        ...

    @abstractmethod
    async def can_handle(self, context: AgentContext) -> float:
        """
        Return confidence score (0.0 - 1.0) that this agent
        can handle the given query.
        """
        ...

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResponse:
        """Execute the query and return results"""
        ...

    async def health_check(self) -> HealthStatus:
        """Check if the agent and its dependencies are healthy"""
        return HealthStatus(
            agent_name=self.name,
            status=self._status,
            last_check=time.time(),
        )

    async def shutdown(self) -> None:
        """Cleanup resources"""
        self._status = AgentStatus.DISABLED
```

#### 6.1.5 Agent Router (Confidence-Based Scoring)

```python
# ──────────────────────────────────────────────
# src/core/orchestrator/router.py
# ──────────────────────────────────────────────

from typing import List, Dict, Any
from src.agents.base_agent import BaseAgent, AgentContext
from src.core.orchestrator.state import AgentPlan
import asyncio


class AgentRouter:
    """Routes queries to the most appropriate agents based on confidence scoring"""

    def __init__(
        self,
        agents: List[BaseAgent],
        min_confidence: float = 0.3,
        max_parallel_agents: int = 3,
    ):
        self.agents = agents
        self.min_confidence = min_confidence
        self.max_parallel_agents = max_parallel_agents

    async def route(self, context: AgentContext) -> List[AgentPlan]:
        """
        Score all agents and return an execution plan ordered by confidence.

        Strategy:
        1. Ask each agent for confidence score (parallel)
        2. Filter out agents below min_confidence
        3. Sort by confidence descending
        4. Take top N agents
        5. Assign priority levels
        """
        # Score all agents in parallel
        scoring_tasks = [
            self._score_agent(agent, context) for agent in agents
        ]
        scores = await asyncio.gather(*scoring_tasks, return_exceptions=True)

        # Build plans, filtering failures and low-confidence
        plans: List[AgentPlan] = []
        for agent, score in zip(self.agents, scores):
            if isinstance(score, Exception):
                continue
            if score >= self.min_confidence:
                plans.append(AgentPlan(
                    agent_name=agent.name,
                    confidence=score,
                    priority=0,  # Will be assigned below
                    modified_query=context.query,
                    timeout_ms=context.timeout_ms,
                ))

        # Sort by confidence and assign priorities
        plans.sort(key=lambda p: p["confidence"], reverse=True)
        for i, plan in enumerate(plans[:self.max_parallel_agents]):
            plan["priority"] = i + 1

        return plans[:self.max_parallel_agents]

    async def _score_agent(
        self, agent: BaseAgent, context: AgentContext
    ) -> float:
        try:
            return await asyncio.wait_for(
                agent.can_handle(context),
                timeout=5.0,  # 5s timeout for scoring
            )
        except asyncio.TimeoutError:
            return 0.0
```

### 6.2 DocAgent - Detailed LLD

#### 6.2.1 Document Ingestion Pipeline

```python
# ──────────────────────────────────────────────
# src/agents/doc_agent/agent.py (simplified)
# ──────────────────────────────────────────────

class DocAgent(BaseAgent):

    @property
    def description(self) -> str:
        return "Answers questions from documents (PDF, DOCX, TXT, CSV, HTML, etc.)"

    @property
    def supported_intents(self) -> List[str]:
        return ["data_retrieval", "summarization", "comparison", "explanation"]

    async def initialize(self) -> None:
        """
        Initialization flow:
        1. Connect to vector store
        2. Check if collections exist
        3. If first run → trigger ingestion pipeline
        4. If collections exist → verify integrity (optional)
        """
        self.vector_store = StoreFactory.create(self.config["vector_store"])
        self.embedder = EmbeddingFactory.create(self.config["embedding"])
        self.retriever = self._build_retriever()

        # Check if we need to index
        if not await self.vector_store.collection_exists(self.config["collection_name"]):
            await self._run_ingestion_pipeline()

        self._status = AgentStatus.READY

    async def _run_ingestion_pipeline(self) -> None:
        """
        Full ingestion pipeline:
        
        ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
        │  Load    │──▶│  Parse   │──▶│  Chunk   │──▶│  Embed   │──▶│  Store   │
        │  Files   │   │  Content │   │  Text    │   │  Chunks  │   │  Vectors │
        └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
        
        Step Details:
        1. LOAD: Discover files from configured sources (local/S3/GCS/Azure)
        2. PARSE: Extract text using format-specific parsers
        3. CHUNK: Split text into optimal chunks (recursive/semantic)
        4. EMBED: Generate embeddings using configured model
        5. STORE: Upsert into vector database with metadata
        """
        loader = LoaderFactory.create(self.config["source_type"])
        documents = await loader.load(self.config["source_path"])

        parsed_docs = []
        for doc in documents:
            parser = ParserFactory.create(doc.file_type)
            parsed_docs.append(await parser.parse(doc))

        chunker = ChunkerFactory.create(self.config.get("chunking_strategy", "recursive"))
        chunks = []
        for doc in parsed_docs:
            chunks.extend(chunker.chunk(
                doc,
                chunk_size=self.config.get("chunk_size", 1000),
                chunk_overlap=self.config.get("chunk_overlap", 200),
            ))

        # Batch embed and store
        batch_size = self.config.get("embedding_batch_size", 100)
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = await self.embedder.embed_batch([c.text for c in batch])
            await self.vector_store.upsert(
                collection=self.config["collection_name"],
                documents=batch,
                embeddings=embeddings,
            )

    async def can_handle(self, context: AgentContext) -> float:
        """
        Confidence scoring logic:
        - 0.9 if intent is 'summarization' or 'explanation'
        - 0.7 if query mentions document-related keywords
        - 0.5 baseline for general queries
        - Boost if similar queries were previously answered by DocAgent
        """
        score = 0.5  # baseline
        doc_keywords = ["document", "report", "file", "pdf", "policy", "manual"]
        if any(kw in context.query.lower() for kw in doc_keywords):
            score += 0.2
        if context.intent in ["summarization", "explanation"]:
            score += 0.2
        return min(score, 1.0)

    async def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execution flow:
        1. Retrieve relevant chunks via vector search
        2. Optionally rerank results
        3. Build context prompt with chunks
        4. Call LLM with query + context
        5. Return structured response with citations
        """
        start = time.time()

        # Retrieve
        results = await self.retriever.retrieve(
            query=context.query,
            k=context.max_results * 2,  # Over-retrieve for reranking
        )

        # Rerank
        if self.reranker:
            results = await self.reranker.rerank(context.query, results)

        top_results = results[:context.max_results]

        # Build prompt and call LLM
        prompt = self._build_prompt(context.query, top_results)
        llm_response = await self.llm.generate(prompt)

        return AgentResponse(
            success=True,
            answer=llm_response.text,
            confidence=self._calculate_confidence(top_results),
            sources=[{
                "source_type": "document",
                "identifier": r.metadata.get("source", "unknown"),
                "relevance_score": r.score,
                "excerpt": r.text[:200],
            } for r in top_results],
            token_usage=llm_response.usage,
            execution_time_ms=(time.time() - start) * 1000,
        )
```

### 6.3 DBAgent - Detailed LLD

#### 6.3.1 NL-to-SQL Pipeline

```python
# ──────────────────────────────────────────────
# src/agents/db_agent/nl_to_sql.py
# ──────────────────────────────────────────────

class NLToSQLGenerator:
    """
    Converts natural language queries to SQL using LLM + schema context.
    
    Pipeline:
    ┌──────────┐   ┌───────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Schema  │──▶│ Prompt Build  │──▶│  LLM Call    │──▶│  SQL Parse   │
    │  Context │   │ (NL + Schema) │   │  (Generate)  │   │  & Validate  │
    └──────────┘   └───────────────┘   └──────────────┘   └──────────────┘
    """

    def __init__(self, llm_provider, schema_context: SchemaContext):
        self.llm = llm_provider
        self.schema = schema_context

    async def generate(
        self, 
        query: str, 
        user_role: str,
        max_retries: int = 2
    ) -> SQLGenerationResult:
        """
        1. Build schema-aware prompt
        2. Generate SQL with LLM
        3. Parse and validate generated SQL
        4. If invalid, retry with error feedback
        """
        schema_prompt = self.schema.to_prompt()

        role_constraints = RBAC_CONSTRAINTS[user_role]

        prompt = f"""You are a SQL expert. Generate a SQL query for the following request.

DATABASE SCHEMA:
{schema_prompt}

USER ROLE CONSTRAINTS:
- Allowed operations: {role_constraints['allowed_operations']}
- Restricted tables: {role_constraints.get('restricted_tables', 'none')}
- Max row limit: {role_constraints.get('max_rows', 1000)}

USER QUERY: {query}

RULES:
1. Only use tables and columns that exist in the schema above
2. Always use aliases for readability
3. Add LIMIT clause (max {role_constraints.get('max_rows', 1000)})
4. For aggregations, include meaningful column aliases
5. Never generate DROP, TRUNCATE, or ALTER unless the role allows it

Respond with ONLY the SQL query, nothing else.
"""
        for attempt in range(max_retries + 1):
            response = await self.llm.generate(prompt)
            sql = self._extract_sql(response.text)

            validation = self._validate_sql(sql, user_role)
            if validation.is_valid:
                return SQLGenerationResult(
                    sql=sql,
                    explanation=await self._explain_sql(sql),
                    confidence=validation.confidence,
                )

            # Retry with error feedback
            prompt += f"\n\nPrevious attempt had error: {validation.error}\nPlease fix."

        raise SQLGenerationError(f"Failed to generate valid SQL after {max_retries} retries")
```

#### 6.3.2 RBAC Engine

```python
# ──────────────────────────────────────────────
# src/agents/db_agent/rbac_engine.py
# ──────────────────────────────────────────────

class RBACEngine:
    """
    Role-Based Access Control for database operations.
    
    Role Hierarchy:
    ┌──────────────────────────────────────────┐
    │              SUPERUSER                    │
    │  ALL operations (SELECT, INSERT, UPDATE,  │
    │  DELETE, DROP, ALTER, CREATE, TRUNCATE)   │
    ├──────────────────────────────────────────┤
    │              ADMIN                        │
    │  SELECT, INSERT, UPDATE, CREATE TABLE     │
    │  Cannot: DROP, DELETE, ALTER, TRUNCATE    │
    ├──────────────────────────────────────────┤
    │              ANALYST                      │
    │  SELECT only (read-only)                  │
    │  Can use: JOINs, aggregations, subqueries │
    ├──────────────────────────────────────────┤
    │              VIEWER                       │
    │  SELECT on whitelisted tables only        │
    │  Max 100 rows per query                   │
    └──────────────────────────────────────────┘
    """

    ROLE_PERMISSIONS = {
        "superuser": {
            "allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE",
                                    "CREATE", "DROP", "ALTER", "TRUNCATE"],
            "max_rows": 10000,
            "restricted_tables": [],
            "can_execute_procedures": True,
        },
        "admin": {
            "allowed_operations": ["SELECT", "INSERT", "UPDATE", "CREATE"],
            "max_rows": 5000,
            "restricted_tables": ["audit_logs", "system_config"],
            "can_execute_procedures": False,
        },
        "analyst": {
            "allowed_operations": ["SELECT"],
            "max_rows": 1000,
            "restricted_tables": ["users", "credentials", "audit_logs"],
            "can_execute_procedures": False,
        },
        "viewer": {
            "allowed_operations": ["SELECT"],
            "max_rows": 100,
            "restricted_tables": ["users", "credentials", "audit_logs",
                                   "financial_raw", "employee_salary"],
            "can_execute_procedures": False,
        },
    }

    def authorize(self, sql: str, user_role: str) -> AuthorizationResult:
        """
        Validates SQL against role permissions.

        Checks:
        1. Operation type (SELECT/INSERT/UPDATE/DELETE/etc.)
        2. Target tables (against restricted list)
        3. Row limit enforcement
        4. Subquery depth limit
        5. No system table access
        6. No data exfiltration patterns (COPY, INTO OUTFILE)
        """
        parsed = sqlparse.parse(sql)
        operation = self._detect_operation(parsed)
        tables = self._extract_tables(parsed)
        permissions = self.ROLE_PERMISSIONS.get(user_role)

        if not permissions:
            return AuthorizationResult(
                authorized=False,
                reason=f"Unknown role: {user_role}"
            )

        # Check operation
        if operation not in permissions["allowed_operations"]:
            return AuthorizationResult(
                authorized=False,
                reason=f"Role '{user_role}' cannot perform {operation}"
            )

        # Check tables
        for table in tables:
            if table in permissions["restricted_tables"]:
                return AuthorizationResult(
                    authorized=False,
                    reason=f"Role '{user_role}' cannot access table '{table}'"
                )

        # Enforce row limit
        sql = self._enforce_row_limit(sql, permissions["max_rows"])

        return AuthorizationResult(authorized=True, modified_sql=sql)
```

#### 6.3.3 SQL Executor (Sandboxed)

```python
# ──────────────────────────────────────────────
# src/agents/db_agent/sql_executor.py
# ──────────────────────────────────────────────

class SQLExecutor:
    """
    Sandboxed SQL execution engine with safety guardrails.

    Safety measures:
    ┌──────────────────────────────────────┐
    │         SQLExecutor Sandbox          │
    ├──────────────────────────────────────┤
    │ ✓ Statement timeout (30s default)    │
    │ ✓ Read-only connection (for viewers) │
    │ ✓ Row limit enforcement              │
    │ ✓ Connection pooling                 │
    │ ✓ Read replica preference            │
    │ ✓ Query cost estimation (EXPLAIN)    │
    │ ✓ Concurrent query limiting          │
    │ ✓ Audit logging                      │
    └──────────────────────────────────────┘
    """

    def __init__(self, db_config: Dict, audit_logger: AuditLogger):
        self.engine = create_async_engine(
            db_config["url"],
            pool_size=db_config.get("pool_size", 5),
            max_overflow=db_config.get("max_overflow", 10),
            pool_timeout=db_config.get("pool_timeout", 30),
        )
        self.audit = audit_logger
        self.semaphore = asyncio.Semaphore(
            db_config.get("max_concurrent_queries", 10)
        )

    async def execute(
        self,
        sql: str,
        user_id: str,
        user_role: str,
        timeout_seconds: int = 30,
    ) -> ExecutionResult:
        """Execute SQL with full safety and audit trail"""

        async with self.semaphore:
            # 1. Log before execution
            await self.audit.log_query(
                user_id=user_id,
                role=user_role,
                sql=sql,
                status="executing",
            )

            start = time.time()
            try:
                async with self.engine.connect() as conn:
                    # Set statement timeout
                    await conn.execute(
                        text(f"SET statement_timeout = {timeout_seconds * 1000}")
                    )

                    # Set read-only if viewer/analyst
                    if user_role in ("viewer", "analyst"):
                        await conn.execute(
                            text("SET TRANSACTION READ ONLY")
                        )

                    result = await conn.execute(text(sql))
                    rows = result.fetchall()
                    columns = list(result.keys())

                    execution_time = (time.time() - start) * 1000

                    await self.audit.log_query(
                        user_id=user_id,
                        role=user_role,
                        sql=sql,
                        status="success",
                        row_count=len(rows),
                        execution_time_ms=execution_time,
                    )

                    return ExecutionResult(
                        success=True,
                        columns=columns,
                        rows=[dict(zip(columns, row)) for row in rows],
                        row_count=len(rows),
                        execution_time_ms=execution_time,
                    )

            except Exception as e:
                await self.audit.log_query(
                    user_id=user_id,
                    role=user_role,
                    sql=sql,
                    status="error",
                    error=str(e),
                )
                return ExecutionResult(success=False, error=str(e))
```

### 6.4 LLM Provider Abstraction

```python
# ──────────────────────────────────────────────
# src/llm/base_provider.py
# ──────────────────────────────────────────────

class LLMResponse(BaseModel):
    text: str
    usage: Dict[str, int]    # {"prompt_tokens": N, "completion_tokens": M}
    model: str
    finish_reason: str
    latency_ms: float


class BaseLLMProvider(ABC):
    """
    Unified interface for all LLM providers.
    
    Implementations:
    ┌─────────────────────┬──────────────────────────────────────┐
    │ Provider            │ Models                               │
    ├─────────────────────┼──────────────────────────────────────┤
    │ OpenAIProvider      │ gpt-4o, gpt-4-turbo, gpt-3.5-turbo  │
    │ AnthropicProvider   │ claude-3.5-sonnet, claude-3-opus     │
    │ GeminiProvider      │ gemini-1.5-pro, gemini-1.5-flash     │
    │ GrokProvider        │ grok-2, grok-2-mini                  │
    │ OllamaProvider      │ llama3, mistral, phi-3 (local)       │
    │ VLLMProvider        │ Any HF model via vLLM (local)        │
    │ AzureOpenAIProvider │ Azure-deployed OpenAI models         │
    │ HuggingFaceProvider │ Inference API models                 │
    └─────────────────────┴──────────────────────────────────────┘
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        ...


# ──────────────────────────────────────────────
# src/llm/provider_factory.py
# ──────────────────────────────────────────────

class LLMProviderFactory:
    """Factory to create LLM providers from configuration"""

    _registry: Dict[str, Type[BaseLLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[BaseLLMProvider]):
        cls._registry[name] = provider_class

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseLLMProvider:
        provider_name = config["provider"]
        if provider_name not in cls._registry:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

        provider_class = cls._registry[provider_name]
        return provider_class(
            model=config["model"],
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            **config.get("extra_params", {}),
        )

# Auto-register providers
LLMProviderFactory.register("openai", OpenAIProvider)
LLMProviderFactory.register("anthropic", AnthropicProvider)
LLMProviderFactory.register("gemini", GeminiProvider)
LLMProviderFactory.register("grok", GrokProvider)
LLMProviderFactory.register("ollama", OllamaProvider)
LLMProviderFactory.register("vllm", VLLMProvider)
LLMProviderFactory.register("azure_openai", AzureOpenAIProvider)
LLMProviderFactory.register("huggingface", HuggingFaceProvider)
```

### 6.5 Output Formatter

```python
# ──────────────────────────────────────────────
# src/utils/output_formatter/base_formatter.py
# ──────────────────────────────────────────────

class BaseFormatter(ABC):
    """
    Pluggable output formatting system.
    
    ┌─────────────────────┬──────────────────────────────────┐
    │ Format              │ Use Case                         │
    ├─────────────────────┼──────────────────────────────────┤
    │ MarkdownFormatter   │ Chat UIs, documentation          │
    │ HTMLFormatter       │ Web apps, email responses        │
    │ JSONFormatter       │ API consumers, structured data   │
    │ TableFormatter      │ CLI tools, tabular data          │
    │ PDFFormatter        │ Reports, formal documents        │
    │ PlainFormatter      │ Minimal output, logging          │
    └─────────────────────┴──────────────────────────────────┘
    """

    @abstractmethod
    def format(
        self,
        answer: str,
        citations: List[SourceCitation],
        metadata: Dict[str, Any],
    ) -> str:
        ...

    def _add_citations(self, citations: List[SourceCitation]) -> str:
        """Format citation section — override per formatter"""
        ...


class FormatterFactory:
    """Create formatter based on requested output format"""

    _formatters = {
        "markdown": MarkdownFormatter,
        "html": HTMLFormatter,
        "json": JSONFormatter,
        "table": TableFormatter,
        "pdf": PDFFormatter,
        "plain": PlainFormatter,
    }

    @classmethod
    def create(cls, format_type: str) -> BaseFormatter:
        formatter_class = cls._formatters.get(format_type, PlainFormatter)
        return formatter_class()
```

### 6.6 Semantic Cache

```python
# ──────────────────────────────────────────────
# src/utils/cache/semantic_cache.py
# ──────────────────────────────────────────────

class SemanticCache:
    """
    Embedding-based cache that returns cached results for
    semantically similar queries, not just exact matches.
    
    Flow:
    1. Embed incoming query
    2. Search cache vector store for similar queries (cosine > threshold)
    3. If hit → return cached response (skip all agents)
    4. If miss → execute normally, then cache the result
    
    Benefits:
    - "What's our Q3 revenue?" and "Q3 revenue numbers" → same cache hit
    - Reduces LLM API costs significantly
    - Configurable similarity threshold (default 0.95)
    """

    def __init__(
        self,
        embedding_provider,
        vector_store,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600,
    ):
        self.embedder = embedding_provider
        self.store = vector_store
        self.threshold = similarity_threshold
        self.ttl = ttl_seconds

    async def get(self, query: str) -> Optional[CachedResponse]:
        embedding = await self.embedder.embed(query)
        results = await self.store.search(
            embedding=embedding,
            top_k=1,
            score_threshold=self.threshold,
        )
        if results and not self._is_expired(results[0]):
            return CachedResponse.from_stored(results[0])
        return None

    async def put(self, query: str, response: QueryResponse) -> None:
        embedding = await self.embedder.embed(query)
        await self.store.upsert(
            embedding=embedding,
            metadata={
                "query": query,
                "response": response.model_dump_json(),
                "cached_at": time.time(),
                "ttl": self.ttl,
            },
        )
```

---

## 7. Additional Data Sources & Agents

### 7.1 Recommended Additional Agents

| # | Agent | Data Source | Description | Priority |
|---|---|---|---|---|
| 1 | **JiraAgent** | Atlassian Jira | Search issues, track projects, sprint status | High |
| 2 | **SlackAgent** | Slack | Search messages, channels, threads | High |
| 3 | **NotionAgent** | Notion | Search pages, databases, workspaces | High |
| 4 | **EmailAgent** | IMAP/Exchange/Gmail | Search emails, attachments | Medium |
| 5 | **APIAgent** | REST/GraphQL APIs | Query registered APIs as data sources | Medium |
| 6 | **GitAgent** | GitHub/GitLab/Bitbucket | Search code, PRs, issues, commits | High |
| 7 | **CalendarAgent** | Google Calendar/Outlook | Meeting search, schedule queries | Medium |
| 8 | **SharePointAgent** | Microsoft SharePoint | Document libraries, lists, sites | High |
| 9 | **GoogleDriveAgent** | Google Drive | Search files, sheets, docs | Medium |
| 10 | **S3Agent** | AWS S3 / MinIO | Query structured data in object storage | Low |
| 11 | **ElasticAgent** | Elasticsearch/OpenSearch | Search indexed logs, analytics data | High |
| 12 | **GraphDBAgent** | Neo4j/Amazon Neptune | Knowledge graph queries (Cypher/SPARQL) | Medium |
| 13 | **DataWarehouseAgent** | Snowflake/BigQuery/Redshift | Analytics queries on warehouse | High |
| 14 | **TeamsAgent** | Microsoft Teams | Search chats, channels, files | Medium |
| 15 | **CRMAgent** | Salesforce/HubSpot | Customer data, deals, contacts | Medium |
| 16 | **MonitoringAgent** | Datadog/Grafana/PagerDuty | DevOps metrics, incidents, alerts | Low |
| 17 | **TicketAgent** | ServiceNow/Zendesk | IT tickets, support cases | Medium |
| 18 | **SpreadsheetAgent** | Google Sheets/Excel | Query tabular data in spreadsheets | Medium |
| 19 | **WikiAgent** | MediaWiki/Internal Wikis | Internal knowledge base search | Low |
| 20 | **VideoAgent** | YouTube/Vimeo/internal video | Transcript search, timestamp-based Q&A | Low |

### 7.2 Agent Compatibility Matrix

```
┌───────────────────┬───────┬────────┬─────────┬──────────┬──────────┐
│ Agent             │ RAG   │ API    │ NL→Query│ Realtime │ Auth     │
│                   │ Based │ Based  │ Convert │ Capable  │ Required │
├───────────────────┼───────┼────────┼─────────┼──────────┼──────────┤
│ DocAgent          │  ✓    │        │         │          │ Optional │
│ DBAgent           │       │        │    ✓    │          │    ✓     │
│ ConfluenceAgent   │       │   ✓    │         │          │    ✓     │
│ WebAgent          │       │   ✓    │         │    ✓     │ Optional │
│ JiraAgent         │       │   ✓    │         │          │    ✓     │
│ SlackAgent        │  ✓*   │   ✓    │         │    ✓     │    ✓     │
│ GitAgent          │  ✓*   │   ✓    │         │          │    ✓     │
│ EmailAgent        │  ✓*   │   ✓    │         │          │    ✓     │
│ ElasticAgent      │       │   ✓    │    ✓    │    ✓     │    ✓     │
│ GraphDBAgent      │       │        │    ✓    │          │    ✓     │
│ DataWarehouseAgent│       │        │    ✓    │          │    ✓     │
│ SharePointAgent   │  ✓*   │   ✓    │         │          │    ✓     │
│ NotionAgent       │       │   ✓    │         │          │    ✓     │
│ SpreadsheetAgent  │  ✓    │   ✓    │         │          │ Optional │
│ CRMAgent          │       │   ✓    │    ✓    │          │    ✓     │
└───────────────────┴───────┴────────┴─────────┴──────────┴──────────┘

✓* = Optionally uses RAG (can index historical data for faster retrieval)
```

---

## 8. Configuration System

### 8.1 Master Configuration

```yaml
# config/default.yaml

app:
  name: "OmniQuery"
  version: "1.0.0"
  environment: "development"    # development | staging | production
  debug: true
  log_level: "INFO"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins: ["*"]
  request_timeout_ms: 60000

auth:
  enabled: true
  jwt_secret: "${JWT_SECRET}"
  jwt_algorithm: "HS256"
  token_expiry_minutes: 60
  default_role: "viewer"

session:
  max_history_turns: 20
  context_window_tokens: 8000
  ttl_minutes: 30

orchestrator:
  min_agent_confidence: 0.3
  max_parallel_agents: 3
  max_retries_per_agent: 2
  agent_timeout_ms: 30000
  fallback_to_web: true          # Use WebAgent as last resort
  enable_semantic_cache: true
  semantic_cache_ttl_seconds: 3600
  semantic_cache_threshold: 0.95

output:
  default_format: "markdown"     # markdown | html | json | plain | table | pdf
  include_citations: true
  include_confidence: true
  max_response_tokens: 4096
```

### 8.2 LLM Provider Configuration

```yaml
# config/llm_providers.yaml

# Active provider (switch this to change LLM globally)
active_provider: "openai"

# Active embedding provider
active_embedding: "openai"

providers:
  openai:
    provider: "openai"
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"
    temperature: 0.0
    max_tokens: 4096
    extra_params:
      top_p: 1.0
      frequency_penalty: 0.0

  anthropic:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    api_key: "${ANTHROPIC_API_KEY}"
    temperature: 0.0
    max_tokens: 4096

  gemini:
    provider: "gemini"
    model: "gemini-1.5-pro"
    api_key: "${GOOGLE_API_KEY}"
    temperature: 0.0

  grok:
    provider: "grok"
    model: "grok-2"
    api_key: "${XAI_API_KEY}"
    base_url: "https://api.x.ai/v1"

  ollama:
    provider: "ollama"
    model: "llama3:70b"
    base_url: "http://localhost:11434"
    temperature: 0.0

  vllm:
    provider: "vllm"
    model: "meta-llama/Llama-3-70b-chat-hf"
    base_url: "http://localhost:8000/v1"

  azure_openai:
    provider: "azure_openai"
    model: "gpt-4o"
    api_key: "${AZURE_OPENAI_KEY}"
    base_url: "${AZURE_OPENAI_ENDPOINT}"
    extra_params:
      api_version: "2024-02-01"
      deployment_name: "gpt-4o-deploy"

embeddings:
  openai:
    provider: "openai"
    model: "text-embedding-3-large"
    api_key: "${OPENAI_API_KEY}"
    dimensions: 3072

  sentence_transformers:
    provider: "sentence_transformers"
    model: "all-MiniLM-L6-v2"
    # Runs locally, no API key needed

  cohere:
    provider: "cohere"
    model: "embed-english-v3.0"
    api_key: "${COHERE_API_KEY}"
```

### 8.3 Agent Configuration

```yaml
# config/agents.yaml

agents:
  doc_agent:
    enabled: true
    source_type: "local"           # local | s3 | gcs | azure_blob | git | url
    source_path: "./documents"
    cloud_credentials:
      aws_access_key: "${AWS_ACCESS_KEY}"
      aws_secret_key: "${AWS_SECRET_KEY}"
      bucket_name: "company-docs"
    collection_name: "documents"
    chunking_strategy: "recursive"  # recursive | semantic | fixed
    chunk_size: 1000
    chunk_overlap: 200
    embedding_batch_size: 100
    retrieval_strategy: "hybrid"    # dense | hybrid | multi_query | hyde
    reranker: "cross_encoder"       # cross_encoder | cohere | none
    top_k: 5

  db_agent:
    enabled: true
    databases:
      - name: "primary_db"
        type: "postgresql"
        url: "${DATABASE_URL}"
        schema_source: "introspection"   # introspection | ddl_file | manual
        ddl_file_path: "./schemas/primary.sql"
        read_replica_url: "${READ_REPLICA_URL}"
        pool_size: 5
        max_rows_default: 1000
        statement_timeout_seconds: 30
      - name: "analytics_db"
        type: "bigquery"
        project_id: "${GCP_PROJECT_ID}"
        credentials_file: "${GCP_CREDENTIALS_PATH}"

  confluence_agent:
    enabled: true
    base_url: "${CONFLUENCE_URL}"
    username: "${CONFLUENCE_USER}"
    api_token: "${CONFLUENCE_TOKEN}"
    spaces: ["DEV", "OPS", "PRODUCT"]   # Limit to specific spaces
    max_results: 10

  web_agent:
    enabled: true
    search_provider: "tavily"       # google | bing | duckduckgo | tavily
    api_key: "${TAVILY_API_KEY}"
    max_results: 5
    scraping_enabled: true
    domains_whitelist: []            # Empty = all domains allowed
    domains_blacklist: ["reddit.com"]

  # Future agents (disabled by default)
  jira_agent:
    enabled: false
  slack_agent:
    enabled: false
  email_agent:
    enabled: false
  git_agent:
    enabled: false
  notion_agent:
    enabled: false
```

### 8.4 RBAC Configuration

```yaml
# config/rbac_policies.yaml

roles:
  superuser:
    description: "Full access to all operations"
    db_operations: ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE"]
    db_max_rows: 10000
    restricted_tables: []
    can_modify_config: true
    can_manage_users: true
    rate_limit_per_minute: 100

  admin:
    description: "Administrative access, no destructive DB ops"
    db_operations: ["SELECT", "INSERT", "UPDATE", "CREATE"]
    db_max_rows: 5000
    restricted_tables: ["audit_logs", "system_config"]
    can_modify_config: true
    can_manage_users: false
    rate_limit_per_minute: 60

  analyst:
    description: "Read-only access to most data"
    db_operations: ["SELECT"]
    db_max_rows: 1000
    restricted_tables: ["users", "credentials", "audit_logs"]
    can_modify_config: false
    can_manage_users: false
    rate_limit_per_minute: 30

  viewer:
    description: "Limited read-only access"
    db_operations: ["SELECT"]
    db_max_rows: 100
    restricted_tables: ["users", "credentials", "audit_logs", "financial_raw", "employee_salary"]
    can_modify_config: false
    can_manage_users: false
    rate_limit_per_minute: 10

default_role: "viewer"
```

---

## 9. Security Architecture

### 9.1 Security Layers

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 1: Network Security                                         │
│ - TLS/HTTPS everywhere                                            │
│ - API Gateway (rate limiting, DDoS protection)                    │
│ - IP whitelisting (optional)                                      │
│ - VPN/Private endpoints for DB connections                        │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 2: Authentication                                           │
│ - JWT tokens with refresh rotation                                │
│ - OAuth2/OIDC integration (Azure AD, Okta, Google)               │
│ - API key authentication for service-to-service                  │
│ - Session timeout and revocation                                  │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 3: Authorization (RBAC)                                     │
│ - Role-based operation restrictions                               │
│ - Table-level access control                                      │
│ - Row-level security (optional)                                   │
│ - Agent-level permissions (which agents a role can use)           │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 4: Data Security                                            │
│ - SQL injection prevention (parameterized queries)               │
│ - Prompt injection detection and sanitization                     │
│ - PII detection and masking in responses                          │
│ - Credential encryption at rest (AES-256)                         │
│ - Audit logging of all data access                                │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 5: LLM Security                                            │
│ - Prompt injection guardrails                                     │
│ - Output filtering (no credential leakage)                        │
│ - Token budget limits per user/role                               │
│ - Model output validation                                         │
│ - Content safety filters                                          │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 Threat Model

| Threat | Mitigation |
|---|---|
| SQL Injection via NL query | LLM output validated by parser; parameterized execution; RBAC enforcement |
| Prompt Injection | Input sanitization; system prompt hardening; output validation |
| Credential Leakage | Env vars only; never in logs; encrypted at rest; never in LLM context |
| Unauthorized Data Access | RBAC at API + agent + DB levels; table-level restrictions |
| DDoS / Abuse | Rate limiting per user/role; token budgets; request size limits |
| Data Exfiltration | Row limits; no COPY/INTO OUTFILE; audit trail; anomaly detection |
| PII Exposure | PII detection in responses; masking pipeline; data classification |

---

## 10. Deployment Architecture

### 10.1 Production Deployment

```
                        ┌──────────────────┐
                        │   Load Balancer   │
                        │   (Nginx/ALB)     │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
          ┌────────────┐ ┌────────────┐ ┌────────────┐
          │ OmniQuery  │ │ OmniQuery  │ │ OmniQuery  │
          │ Instance 1 │ │ Instance 2 │ │ Instance 3 │
          │ (FastAPI)  │ │ (FastAPI)  │ │ (FastAPI)  │
          └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
                 │               │               │
          ┌──────┴───────────────┴───────────────┴──────┐
          │              Shared Infrastructure           │
          │                                              │
          │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
          │  │  Redis    │  │ Postgres │  │ ChromaDB │  │
          │  │  (Cache   │  │ (System  │  │ /Qdrant  │  │
          │  │  + Queue) │  │  Meta)   │  │ (Vectors)│  │
          │  └──────────┘  └──────────┘  └──────────┘  │
          │                                              │
          │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
          │  │ Celery    │  │  MinIO   │  │Prometheus│  │
          │  │ Workers   │  │  (Docs)  │  │ +Grafana │  │
          │  └──────────┘  └──────────┘  └──────────┘  │
          └──────────────────────────────────────────────┘
```

### 10.2 Docker Compose (Dev)

```yaml
# docker-compose.yml
version: "3.9"

services:
  app:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [redis, postgres, chromadb]
    volumes:
      - ./documents:/app/documents

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: omniquery
      POSTGRES_USER: omniquery
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
    volumes:
      - chromadata:/chroma/chroma

  celery_worker:
    build: .
    command: celery -A src.tasks.celery_app worker -l info
    env_file: .env
    depends_on: [redis, postgres]

volumes:
  pgdata:
  chromadata:
```

---

## 11. Observability & Monitoring

### 11.1 Observability Stack

```
┌──────────────────────────────────────────────────────┐
│                  Observability                        │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │   Tracing    │  │   Metrics   │  │   Logging    │ │
│  │             │  │             │  │              │ │
│  │ OpenTelemetry│  │ Prometheus  │  │ Structured   │ │
│  │ + LangSmith │  │ + Grafana   │  │ JSON Logs    │ │
│  │             │  │             │  │ (ELK/Loki)   │ │
│  └─────────────┘  └─────────────┘  └──────────────┘ │
│                                                       │
│  Key Metrics:                                         │
│  • Query latency (p50, p95, p99) per agent            │
│  • Agent success/failure rates                        │
│  • LLM token usage and cost per user/agent            │
│  • Cache hit ratio (exact + semantic)                 │
│  • Active sessions and concurrent queries             │
│  • Vector DB query latency                            │
│  • Document indexing throughput                       │
│  • RBAC authorization accept/reject rates             │
│                                                       │
│  Alerts:                                              │
│  • Agent error rate > 10% for 5 min                   │
│  • p99 latency > 30s                                  │
│  • LLM cost exceeds daily budget                      │
│  • Failed RBAC attempts > threshold                   │
│  • Vector DB disk usage > 80%                         │
└──────────────────────────────────────────────────────┘
```

### 11.2 Audit Trail Schema

```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id         VARCHAR(255) NOT NULL,
    user_role       VARCHAR(50) NOT NULL,
    query_id        UUID NOT NULL,
    session_id      UUID,
    action          VARCHAR(50) NOT NULL,    -- 'query', 'sql_execute', 'doc_retrieve', etc.
    agent_name      VARCHAR(100),
    input_query     TEXT NOT NULL,
    generated_sql   TEXT,                    -- For DBAgent
    operation_type  VARCHAR(20),             -- SELECT, INSERT, etc.
    target_tables   TEXT[],                  -- Tables accessed
    result_status   VARCHAR(20) NOT NULL,    -- 'success', 'denied', 'error'
    row_count       INTEGER,
    token_usage     JSONB,
    execution_ms    FLOAT,
    error_message   TEXT,
    ip_address      INET,
    user_agent      TEXT,
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_audit_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_query ON audit_log(query_id);
CREATE INDEX idx_audit_action ON audit_log(action, timestamp DESC);
```

---

## 12. Scalability & Performance

### 12.1 Performance Optimization Strategy

```
┌───────────────────────────────────────────────────────────────────┐
│                    Performance Layers                              │
│                                                                    │
│  LAYER 1: Request Caching                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ • Exact match cache (Redis) — TTL 1h                        │  │
│  │ • Semantic cache (Vector similarity > 0.95) — TTL 1h        │  │
│  │ • Expected hit rate: 30-50% for enterprise usage            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  LAYER 2: Parallel Agent Execution                                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ • Top 2-3 agents execute in parallel (asyncio.gather)       │  │
│  │ • Independent from each other — no cross-agent dependency   │  │
│  │ • Timeout per agent (30s default)                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  LAYER 3: Streaming Responses                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ • WebSocket streaming for LLM output                        │  │
│  │ • Server-Sent Events (SSE) as fallback                      │  │
│  │ • Reduces perceived latency for users                       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  LAYER 4: Infrastructure Scaling                                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ • Horizontal scaling of API servers (stateless)             │  │
│  │ • Read replicas for DB operations                           │  │
│  │ • Connection pooling for all external services              │  │
│  │ • Background indexing via Celery workers                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  LAYER 5: LLM Optimization                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ • Prompt compression (minimize token usage)                 │  │
│  │ • Model routing (fast model for classification, powerful    │  │
│  │   model for synthesis)                                      │  │
│  │ • Batch embedding for document ingestion                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### 12.2 Capacity Planning

| Component | Small (1-10 users) | Medium (10-100 users) | Large (100-1000 users) |
|---|---|---|---|
| API Servers | 1 instance | 2-3 instances | 5-10 instances + LB |
| Redis | Single node | Single node (4GB) | Cluster (3 nodes) |
| PostgreSQL | Single node | Primary + 1 replica | Primary + 2 replicas |
| Vector DB | Embedded (ChromaDB) | Standalone (Qdrant) | Cluster (Qdrant/Pinecone) |
| Celery Workers | 1 worker | 2-3 workers | 5-10 workers |
| LLM Strategy | Single provider | Primary + fallback | Multi-provider with routing |

---

## Appendix A: Technology Stack Summary

| Category | Technology | Rationale |
|---|---|---|
| **Language** | Python 3.11+ | LangChain/LangGraph ecosystem; AI/ML library support |
| **Web Framework** | FastAPI | Async-first, auto-docs (OpenAPI), high performance |
| **Orchestration** | LangGraph | Stateful agent orchestration, conditional routing, checkpointing |
| **LLM Framework** | LangChain | Tool use, prompt management, provider abstraction |
| **Vector DB** | ChromaDB (dev) / Qdrant (prod) | ChromaDB for simplicity; Qdrant for production scale |
| **Cache** | Redis | Sub-ms latency, pub/sub, session storage |
| **Task Queue** | Celery + Redis | Proven async task execution, retries, scheduling |
| **System DB** | PostgreSQL | ACID compliance, JSONB support, pgvector option |
| **Doc Parsing** | Unstructured / PyMuPDF | Multi-format support, battle-tested |
| **Auth** | PyJWT + python-jose | Industry-standard JWT implementation |
| **Observability** | OpenTelemetry + LangSmith | E2E tracing for both infra and LLM chains |
| **Testing** | pytest + pytest-asyncio | De facto standard, excellent async support |
| **Containerization** | Docker + Docker Compose | Universal deployment; k8s-ready |
| **IaC** | Terraform / Helm | Production deployment automation |

---

## Appendix B: API Endpoint Reference

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/query` | Submit a query | JWT |
| WS | `/api/v1/ws/query` | Streaming query (WebSocket) | JWT |
| GET | `/api/v1/agents` | List all agents + status | JWT |
| GET | `/api/v1/agents/{name}/health` | Agent health check | JWT |
| POST | `/api/v1/admin/index` | Trigger document re-indexing | Admin+ |
| POST | `/api/v1/admin/config` | Update runtime config | Admin+ |
| GET | `/api/v1/admin/audit` | View audit logs | Admin+ |
| POST | `/api/v1/auth/login` | Get JWT token | Public |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | JWT |
| GET | `/api/v1/sessions/{id}` | Get session history | JWT |
| DELETE | `/api/v1/sessions/{id}` | Clear session | JWT |
| GET | `/api/v1/health` | System health check | Public |

---

*Document Version: 1.0.0 | Last Updated: 2026-02-13*
Note: The project is currently under active development; several features have been implemented while others are in progress.
