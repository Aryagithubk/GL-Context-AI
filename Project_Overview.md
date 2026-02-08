# 📘 KnowledgeHub AI

### Intelligent Document Intelligence System for GlobalLogic–Hitachi

---

## 1. Introduction

**KnowledgeHub AI** is a local, privacy-focused **Retrieval-Augmented Generation (RAG)** based system designed to enable intelligent querying over internal company documents of **GlobalLogic–Hitachi**.

Organizations typically store knowledge across large volumes of PDFs, Word documents, text files, and internal documentation. Searching such data manually is inefficient and time-consuming. KnowledgeHub AI addresses this problem by allowing users to ask questions in **natural language** and receive **accurate, context-aware answers** derived strictly from company documents.

The system is designed to be **modular, configurable, model-agnostic**, and **scalable**, supporting both local LLMs (via Ollama) and future cloud-based models.

---

## 2. Problem Statement

* Internal company knowledge is spread across multiple document formats.
* Traditional keyword-based search lacks semantic understanding.
* Manual document exploration wastes time and reduces productivity.
* Cloud-based AI solutions pose **privacy and cost concerns**.

---

## 3. Proposed Solution

KnowledgeHub AI uses a **Retrieval-Augmented Generation (RAG)** architecture that:

* Converts documents into semantic embeddings.
* Stores them in a vector database.
* Retrieves only the most relevant document segments.
* Uses a Large Language Model (LLM) to generate answers **only from retrieved context**, avoiding hallucination.

---

## 4. High-Level RAG Flow

### Data Ingestion Flow

```
Documents
→ Parsing
→ Chunking
→ Embedding
→ Vector Storage
```

### Runtime Query Flow

```
User Query
→ Query Embedding
→ Vector DB Similarity Search (Top-K)
→ Context Assembly
→ LLM Prompting
→ Final Answer
```

📌 No agent is required initially. Agentic behavior is planned in future versions.

EXPLANATIONS FOR ABOVE FLOWS:

# 🔁 High-Level RAG Flow (Backend Working – Simple Explanation)

Tumhare project me **do alag phases** hote hain:

1️⃣ **Data Ingestion (Ek baar ya jab new files aayen)**
2️⃣ **Runtime Query (Har user question pe)**

Main dono ko **step-by-step backend ke point of view se** samjhaata hoon.

---

## 🟦 PART 1: Data Ingestion Flow

👉 *Ye process tab hota hai jab tum documents add karti ho*
(example: GlobalLogic–Hitachi PDFs, HR policies, guidelines)

### Step 1: Documents

📂 `data/` folder me files hoti hain:

* PDF
* Word
* TXT
* JSON

💡 Example:

```
data/
 └── hr_policy.pdf
 └── company_overview.txt
```

---

### Step 2: Parsing (Text nikalna)

Backend kya karta hai?

* Har file open karta hai
* Uske andar ka **actual text extract** karta hai
* PDF ka page text, Word ka paragraph text

📌 Output:

```text
"GlobalLogic follows a hybrid work policy..."
```

❗ Is stage pe **AI involved nahi hota** — sirf text reading.

---

### Step 3: Chunking (Text todna)

Problem:

* Document bahut lamba hota hai
* LLM ek baar me sab nahi padh sakta

Solution:

* Text ko **small pieces (chunks)** me tod diya jaata hai

⚙️ Tumhare config ke according:

```yaml
chunk_size: 500
chunk_overlap: 50
```

💡 Example:

```
Chunk 1 → "GlobalLogic follows hybrid work..."
Chunk 2 → "Employees must be available during core hours..."
```

📌 Overlap isliye hota hai taaki meaning break na ho.

---

### Step 4: Embedding (Meaning ko numbers me badalna)

Ab AI ka first use hota hai 👇

* Har chunk ko **embedding model (nomic-embed-text)** ko diya jaata hai
* Model uska **semantic meaning** nikalta hai
* Meaning ko **numbers (vector)** me convert karta hai

📌 Example:

```
"Hybrid work policy" → [0.12, 0.98, 0.44, ...]
```

❗ Ye **LLM nahi**, embedding model hota hai.

---

### Step 5: Vector Storage (ChromaDB)

* Ye vectors + text **Vector DB (Chroma)** me store hote hain
* Har chunk ke saath metadata hota hai:

  * source file
  * page number

📦 Final result:

```
Vector DB = company knowledge ka brain
```

🟢 **Data Ingestion yahin complete ho jaata hai**

---

## 🟩 PART 2: Runtime Query Flow

👉 *Ye har baar hota hai jab user question poochta hai*

---

### Step 1: User Query

User frontend me type karta hai:

> “What is the work from home policy?”

---

### Step 2: Query Embedding

Backend:

* Same embedding model ko **user question** deta hai
* Question ka bhi vector ban jaata hai

📌 Example:

```
"What is the work from home policy?"
→ [0.11, 0.97, 0.40, ...]
```

---

### Step 3: Vector DB Similarity Search (Top-K)

Ab magic hota hai 🔥

* ChromaDB:

  * Question vector
  * Sab stored document vectors
* **Similarity compare karta hai**

💡 Matlab:

> Kaunsa document chunk is question ke meaning ke sabse paas hai?

⚙️ Tumhare config:

```yaml
top_k: 3
```

📌 Output:

```
Top 3 most relevant chunks:
- Chunk about hybrid policy
- Chunk about core working hours
- Chunk about remote approval
```

❗ **LLM abhi tak involved nahi hai**

---

### Step 4: Context Assembly (Prompt banana)

Backend ab ek **prompt build** karta hai:

```
Context:
- GlobalLogic follows a hybrid work policy...
- Employees must be available from 11AM–4PM...
- Remote work requires manager approval...

Question:
What is the work from home policy?
```

📌 Is context me **sirf relevant text hota hai**, poora document nahi.

---

### Step 5: LLM Prompting (LLaMA via Ollama)

Ab LLaMA ko kaam diya jaata hai:

* Ollama ke through
* LLaMA ko **sirf ye context + question** milta hai

⚠️ Important:

> LLaMA documents ko search nahi karta
> LLaMA sirf **diye gaye context ko read karta hai**

---

### Step 6: Final Answer

LLM output deta hai:

✅

> “GlobalLogic follows a hybrid work policy where employees work remotely with defined core hours and managerial approval.”

Agar context me answer nahi hota:

❌

> “I don’t know.”

📌 **No hallucination — industry best practice**

---

## 🧠 Ek Line me Samjho

> **Vector DB batata hai “kya padhna hai”**
> **LLM batata hai “kaise jawab likhna hai”**

---

## 5. System Architecture (End-to-End)

### Backend Architecture

```
Dataset (PDF, DOCX, TXT, JSON)
        ↓
Document Loader & Parser
        ↓
Chunker (Recursive / Semantic)
        ↓
Embedding Generator (Ollama)
        ↓
Vector Database (ChromaDB)
        ↓
Retriever
        ↓
LLM (LLaMA via Ollama)
        ↓
Answer to User
```
# 🧩 System Architecture (End-to-End) – Simple Explanation

*(How backend actually works in KnowledgeHub AI)*

Is architecture ko samajhne ka easiest tareeqa hai:
👉 **“Data andar kaise jaata hai, store hota hai, aur user ko answer kaise milta hai”**

## 1️⃣ Dataset (PDF, DOCX, TXT, JSON)

📂 Ye tumhara **raw input** hai.

* Company policies
* HR documents
* Guidelines
* Technical docs

📌 Tumhare project me:

* Ye files `data/` folder me hoti hain
* Backend directly yahin se documents uthata hai

Example:

```
data/
 ├── hr_policy.pdf
 ├── company_overview.txt
```

---

## 2️⃣ Document Loader & Parser

🧠 Backend ka first kaam: **files padhna**

* PDF → text nikaala
* Word → paragraphs nikaale
* TXT → direct text

❗ Yahan **AI use nahi hota**
Sirf file reading hoti hai.

📌 Output:

```text
"GlobalLogic follows a hybrid work policy..."
```

---

## 3️⃣ Chunker (Recursive / Semantic)

Problem:

* Documents bahut bade hote hain
* LLM ek baar me sab nahi padh sakta

Solution:

* Text ko **chhote-chhote pieces (chunks)** me tod diya jaata hai

⚙️ Tumhare config ke according:

```yaml
chunk_size: 500
chunk_overlap: 50
```

📌 Result:

```
Chunk 1 → Hybrid policy
Chunk 2 → Core working hours
Chunk 3 → Remote work approval
```

---

## 4️⃣ Embedding Generator (Ollama)

Yahan pe **meaning capture hota hai**

* Har chunk ko **embedding model** diya jaata hai
* Model text ka **semantic meaning** samajhta hai
* Meaning ko numbers (vectors) me convert karta hai

📌 Example:

```
"Hybrid work policy"
→ [0.21, 0.89, 0.43, ...]
```

⚠️ Ye LLaMA nahi hota
Ye **nomic-embed-text** model hota hai (via Ollama)

---

## 5️⃣ Vector Database (ChromaDB)

📦 Ab sab knowledge store hoti hai

* Chunk text
* Uska vector
* Metadata (file name, page no.)

📌 ChromaDB:

* Local
* Fast
* Lightweight
* Tumhare laptop ke liye perfect

💡 Isko samjho:

> **Vector DB = company documents ka brain**

---

## 6️⃣ Retriever

👀 Ye component decide karta hai:

> *“Is question ke liye kaunsa data relevant hai?”*

Flow:

* User ka question aata hai
* Uska bhi embedding banta hai
* Vector DB se **Top-K similar chunks** nikale jaate hain

⚙️ Example:

```yaml
top_k: 3
```

📌 Output:

```
3 sabse relevant chunks
```

---

## 7️⃣ LLM (LLaMA via Ollama)

🤖 Ab actual answer writing hoti hai

* Retriever ke chunks ko **context** banaya jaata hai
* Question + context LLaMA ko diya jaata hai

⚠️ Important:

> LLaMA documents ko search nahi karta
> Sirf **jo context diya gaya hai wahi padhta hai**

---

## 8️⃣ Answer to User

🎯 Final result frontend pe dikh jaata hai

✅ Agar answer context me hai:

> “GlobalLogic follows a hybrid work policy with defined core hours.”

❌ Agar context me nahi hai:

> “I don’t know.”

📌 **No hallucination — professional AI behavior**

---

## 🧠 One-Line Summary (Interview Ready)

> *In KnowledgeHub AI, documents are converted into embeddings and stored in a vector database. During runtime, relevant content is retrieved using similarity search and passed to a local LLaMA model via Ollama to generate accurate, context-aware answers.*

---

## 📌 Simple Analogy (Best for PPT)

* **ChromaDB** → Book index
* **Retriever** → Relevant page finder
* **LLaMA** → Answer writer
* **Ollama** → Local AI engine

---

## 6. Technology Stack & Rationale

### Programming Language

**Python**

* Best ecosystem for RAG
* Strong NLP & AI libraries
* Easy extensibility

---

### Document Loading

Using **LangChain Loaders**:

* PyPDFLoader (PDF)
* TextLoader (TXT)
* JSONLoader (JSON)
* Word Loaders (DOCX)

**Reason:**
They normalize output into `Document(page_content, metadata)` format and handle encoding safely.

---

### Chunking Strategy

* **Chunk Size:** 500 tokens
* **Chunk Overlap:** 50 tokens

**Why Chunking?**

* LLM context window is limited.
* Smaller chunks improve semantic embeddings.
* Overlap ensures contextual continuity.

## 🧠 Why Python (and not Node.js) for KnowledgeHub AI?

### 1️⃣ Python is the **Industry Standard for AI & RAG**

**Reason:**

* Almost **all AI research + production RAG systems** Python me likhe jaate hain.
* LangChain, ChromaDB, embedding models — sab Python-first hain.

👉 Node.js AI ke liye bana hi nahi tha, wo **web servers** ke liye bana hai.

---

### 2️⃣ Best Library Ecosystem (Biggest Reason)

Tumhare project me ye cheezein core hain:

| Requirement                  | Python           | Node.js     |
| ---------------------------- | ---------------- | ----------- |
| Document loaders (PDF, DOCX) | ✅ Excellent      | ❌ Limited   |
| Embeddings & NLP             | ✅ Best-in-class  | ❌ Weak      |
| Vector DB clients            | ✅ Native support | ⚠️ Partial  |
| LLM integration              | ✅ Direct         | ⚠️ Indirect |
| AI research tools            | ✅ Massive        | ❌ Minimal   |

📌 Example:

* **LangChain** → Python-first
* **ChromaDB** → Python-first
* **Sentence Transformers** → Python-only

---

### 3️⃣ Easier RAG Pipeline Development

RAG flow me heavy processing hoti hai:

* Text parsing
* Chunking
* Vector math
* Similarity search

Python:

* Built for **data processing**
* Clean, readable code
* Less boilerplate

Node.js:

* Async-heavy
* Complex for data pipelines
* Debugging RAG logic becomes messy

---

### 4️⃣ Local LLM + Ollama Integration is Better in Python

Tum local LLaMA use kar rahe ho via **Ollama**.

Python:

* Simple HTTP client
* Stable wrappers (langchain-ollama)
* Easy fallback to OpenAI/Gemini later

Node.js:

* Less mature wrappers
* Less community examples
* Debugging harder

---

### 5️⃣ Performance Reality (Important Truth)

Myth:
❌ “Node.js is faster than Python”

Reality:

* **LLM inference time** dominates (not Python/Node)
* Vector search time dominates
* Python speed is **not a bottleneck**

So choosing Node gives **no real performance gain** here.

---

### 6️⃣ Scalability & Future-Proofing

Python allows:

* Easy switch to cloud LLMs
* Easy agent frameworks
* Easy research upgrades (rerankers, hybrid search)

Node.js would block:

* Research-level features
* Advanced RAG upgrades
* Agentic systems

---

## 🧠 PPT-Friendly One-Liner

> **Python was chosen over Node.js because it is the industry standard for AI and RAG systems, offering superior NLP libraries, native vector database support, and seamless integration with local and cloud-based LLMs.**

---

## 🔥 Interview Killer Answer (Short)

> *Node.js is great for frontend and APIs, but for AI-heavy workloads like document parsing, embeddings, and retrieval pipelines, Python offers a far richer and more mature ecosystem, making it the correct engineering choice.*

---

### Embedding Model

**nomic-embed-text (via Ollama)**

**Why?**

* Lightweight
* CPU-friendly
* Designed specifically for embeddings
* Free & local

---

### Vector Database

**ChromaDB**

**Why ChromaDB?**

* Local & file-based
* Zero configuration
* Ideal for MVP and offline usage

**Why not others (currently)?**

* FAISS: In-memory only
* Qdrant: Heavier setup
* Pinecone: Paid & cloud-based

---

### Large Language Model

**LLaMA 3.2 (1B) via Ollama**

**Reason for 1B model:**

* System RAM constraint (~2GB)
* Smooth CPU execution
* Sufficient for factual Q&A

Larger models (3B+) and other model apis can be enabled and used later.

---
## 7. Configuration-Driven Design

All system behavior is controlled via `config.yaml`.

### Key Parameters

```yaml
chunk_size: 500
chunk_overlap: 50
vector_db: chroma
embedding_provider: ollama
llm_provider: ollama
```

**Benefits:**

* No hardcoding
* Easy model switching
* Clean separation of concerns

## 🔹 What is `chunk_size` and `chunk_overlap`?

In KnowledgeHub AI, **documents ko directly LLM ko nahi dete**.
Pehle unhe **small meaningful pieces (chunks)** me todte hain.

---

## 📌 `chunk_size: 500`

### 👉 Meaning:

* Har document ko **500 tokens ke blocks** me divide kiya jaata hai
* 1 token ≈ ¾ word (roughly)

### 🔍 Example:

Original document:

```
Company follows a hybrid work policy.
Employees must work 3 days from office.
Core hours are 10 AM to 4 PM.
Manager approval is required for full remote work.
```

Chunking:

```
Chunk 1 (500 tokens max):
Hybrid work policy + office days + core hours + approvals
```

### ✅ Why 500?

* LLM context limit hota hai
* Embeddings **best quality** 200–800 tokens ke beech aati hain
* 500 = **balanced choice**

  * Not too small (loss of meaning)
  * Not too big (noise)

---

## 📌 `chunk_overlap: 50`

### 👉 Meaning:

* Har next chunk me **50 tokens pichhle chunk se repeat** hote hain

### 🔍 Example:

```
Chunk 1:
"... core hours are 10 AM to 4 PM ..."

Chunk 2:
"10 AM to 4 PM ... manager approval required ..."
```

👉 “10 AM to 4 PM” dono chunks me aayega

---

## ❓ Why Overlap is Needed?

### 🚫 Without overlap (bad):

* Sentence aadha ek chunk me
* Baaki aadha next chunk me
* Meaning toot jaata hai

### ✅ With overlap (good):

* Context continuity bana rehta hai
* Similarity search better hoti hai
* Answers zyada accurate aate hain

---

## 🧠 Real Backend Flow (Tumhare Project Me)

1. PDF read hota hai
2. Text → chunks of 500 tokens
3. Har chunk me 50 tokens overlap
4. Har chunk ka embedding banta hai
5. Vector DB me store hota hai

During query:

* Question embedding banta hai
* Similar chunks retrieve hote hain
* LLM ko **complete context** milta hai

---

## 🧾 PPT-Ready Explanation (Short)

> **Chunk Size (500)** ensures each text segment is small enough for efficient embeddings while retaining semantic meaning.
> **Chunk Overlap (50)** preserves contextual continuity across chunks, preventing loss of information at boundaries and improving retrieval accuracy.

---

## 🎯 One-Line Analogy (Best for Understanding)

> Chunk size = page size
> Chunk overlap = page ka thoda overlap taaki sentence toot na jaaye

---

## 8. Backend Working (Step-by-Step)

1. Documents are read from the `data/` directory.
2. Text is extracted and split into chunks.
3. Each chunk is converted into an embedding via Ollama.
4. Embeddings are stored in ChromaDB.
5. On user query:

   * Query embedding is generated.
   * Vector DB performs similarity search.
   * Top-K chunks are retrieved.
   * Backend assembles context.
   * LLM generates answer using only provided context.

📌 The LLM **does not search documents directly**.

---

## 9. Role of Ollama in the System

**Ollama acts as a local AI server running on `localhost`.**

* Hosts LLaMA and embedding models.
* Exposes REST APIs for:

  * Embedding generation
  * Text generation

### Benefits

* Complete data privacy
* No internet dependency
* No API cost
* Lightweight and CPU-friendly

---

## 10. Frontend Overview

* Web-based UI (HTML, CSS, JavaScript)
* Dark-themed, premium look
* Chat-style interface
* Communicates with backend via FastAPI

### User Flow

```
User → Ask Question → Backend → Answer Displayed
```

---

## 11. Current Limitations (Intentional)

* Single LLM provider (Ollama) in my project case. Can we use multiple providers in future. 
* No LLM-based intelligent routing (Rule-based routing implemented)

User Question
   ↓
Vector DB Search
   ↓
Context Found?
   ↓ Yes           ↓ No
LLM (Docs)    Web Search → LLM

* Smart web fallback when documents lack answers
* Uses controlled web search
* LLM answers strictly from search context
* Maintains accuracy + expands coverage

These limitations are part of the **MVP scope**.

1️⃣ Single LLM Provider (Ollama Only)

What it means:

Abhi system sirf Ollama ke through local LLaMA model use karta hai
OpenAI, Gemini, Claude jaise cloud models abhi connected nahi hain

Why this is intentional:

Project ka focus local + privacy-first AI par hai
Internet dependency avoid ki gayi
Limited RAM (2GB) ke liye safe choice

Simple Example:

Jaise pehle sirf ek engine wali car banana,
multi-engine baad me upgrade hota hai.

Local LLMs (e.g., Ollama) run on your own hardware, ensuring complete privacy, zero API costs, and offline functionality, making them ideal for sensitive data and local prototyping. In contrast, Gemini APIs offer superior, cloud-powered reasoning, massive context windows, and multimodal (image/video/text) capabilities, but require internet connectivity and usage-based payments. 

---

## 12. Web Search Integration (Planned & Implemented Idea)

### Motivation

Some queries fall outside company knowledge.

Example:

> “Who is Elon Musk?”

### Approach

* Detect non-company queries
* Perform web search (DuckDuckGo / Google)
* Summarize results using LLM

---

## 13. Debugging & Quality Improvements

Identified issues:

* Over-restrictive system prompts
* Empty retrieval results
* Vector DB inconsistency

Fixes:

* Full vector DB reset
* Re-ingestion of documents
* Prompt refinement
* Debug logging in retriever and search tools

---

## 14. Upgrade Plan – KnowledgeHub AI v2.0

### Vision: **The Brain (Agentic System)**

The system will evolve into an intelligent agent that can:

* Decide whether to use:

  * Vector DB
  * Web Search
* Support multiple LLM providers
* Provide contextual UI greetings

---

## 15. The Brain – High-Level Flow

```
User Query
   ↓
The Brain (Router)
   ↓
Decision
 ┌──────────────┐
 │ Vector DB    │
 │ Web Search   │
 └──────────────┘
   ↓
LLM (Multi-provider)
   ↓
Final Answer
```

---

## 16. Multi-Model Support (Future)

Planned providers:

* Ollama (Local)
* OpenAI (GPT-4)
* Gemini
* Claude

Switching controlled via config:

```yaml
llm:
  active_provider: gemini
```

---

## 17. Future Enhancements

* Agent-based routing
* Metadata-based filtering (HR, Finance, Engineering)
* Chat history memory
* UI personalization
* Enterprise-scale ingestion pipelines

---

## 18. Conclusion

KnowledgeHub AI demonstrates a **modern, industry-aligned RAG architecture** that securely leverages internal company knowledge. The project focuses on privacy, modularity, and scalability while maintaining a clear roadmap toward a fully agentic, multi-model AI system.

