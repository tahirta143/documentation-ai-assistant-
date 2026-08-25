# 📚 Documentation AI Assistant — Technical Deep Dive

A comprehensive breakdown of what we built, the techniques and technologies used, and how each component works together to create an intelligent documentation assistant.

---

## 📌 What We Built

A **full-stack AI-powered documentation assistant** that lets users upload technical documents (PDFs, Markdown, plain text), automatically processes and indexes them using vector embeddings, and then answers natural language questions about the content — citing exact sources.

The system uses **Retrieval-Augmented Generation (RAG)**, a technique where an LLM generates answers grounded **only** in the user's own documents, eliminating hallucinations and ensuring factual accuracy.

---

## 🧠 Core Techniques & Concepts

### 1. RAG (Retrieval-Augmented Generation)

RAG is the backbone of this project. Instead of relying on a language model's pre-trained knowledge (which can hallucinate or be outdated), RAG works in two phases:

- **Retrieval Phase:** When a user asks a question, the system searches the document database for the most semantically relevant text passages.
- **Generation Phase:** The retrieved passages are injected as context into the LLM prompt, and the model generates an answer using **only** that context.

This ensures every answer is traceable back to a specific document and page number.

```
User Question → Embed Question → Vector Search → Top-K Chunks → LLM Prompt → Grounded Answer
```

---

### 2. Text Extraction (Document Parsing)

Before any AI processing, raw documents must be converted into clean text. We built dedicated loaders for each format:

| Format | Library Used | How It Works |
|---|---|---|
| **PDF** | `PyMuPDF` (`fitz`) | Opens the PDF, iterates page-by-page, and extracts plain text using `page.get_text("text")`. Preserves page numbers for accurate citations. |
| **Markdown** | `markdown-it-py` | Parses Markdown syntax and strips formatting to produce clean plaintext while preserving content structure. |
| **Plain Text** | Built-in Python | Reads `.txt` files with encoding detection. |

All extracted text goes through a **text cleaner** utility that normalizes whitespace, removes control characters, and standardizes line breaks.

**Code:** `backend/app/loaders/` — Factory pattern dispatches to the right loader based on file extension.

---

### 3. Token-Aware Chunking

LLMs and embedding models have **context window limits**. A 50-page PDF cannot be embedded as one piece. We split documents into overlapping chunks using a **sliding window** approach:

**How it works:**

```
Full Document (e.g., 5000 tokens)
│
├─ Chunk 1: tokens[0:800]       ← 800 tokens
├─ Chunk 2: tokens[700:1500]    ← overlaps by 100 tokens
├─ Chunk 3: tokens[1400:2200]   ← overlaps by 100 tokens
├─ ...
└─ Chunk N: tokens[...end]
```

**Key parameters:**
- **Chunk size:** 800 tokens (fits comfortably in embedding models)
- **Overlap:** 100 tokens (~12%) — ensures sentences split at chunk boundaries still have context in both chunks
- **Tokenizer:** `tiktoken` with `cl100k_base` encoding (same tokenizer used by OpenAI and many modern LLMs)

**Why token-based, not character-based?**
Character counts are misleading — "the" is 3 characters but 1 token, while "photosynthesis" is 14 characters but also ~1 token. Token-based chunking guarantees each chunk fits within the embedding model's limit.

**Code:** `backend/app/rag/chunker.py`

---

### 4. Vector Embeddings

Embeddings are the mathematical core of semantic search. They convert text into **high-dimensional numeric vectors** where semantically similar texts are geometrically close together.

**Model used:** Google Gemini `gemini-embedding-001` → produces a **3072-dimensional float vector** per text chunk.

**Example (simplified to 3D):**

```
"How to install Python"     → [0.82, 0.15, 0.43]
"Python installation guide" → [0.80, 0.17, 0.41]  ← very close (similar meaning)
"Recipe for chocolate cake" → [0.12, 0.91, 0.03]  ← far away (different meaning)
```

**Batch processing with retry logic:**
- Chunks are processed in batches of 100
- Transient API errors are retried up to 3 times with exponential back-off (2s, 4s, 8s)

**Code:** `backend/app/services/embedding_service.py`

---

### 5. Vector Storage & Cosine Similarity Search (pgvector)

We store embeddings directly inside **PostgreSQL** using the `pgvector` extension, which adds native vector data types and distance operators to SQL.

**How similarity search works:**

```sql
-- pgvector cosine distance operator: <=>
-- similarity = 1 - distance (higher = more similar)

SELECT
    dc.content,
    1 - (dc.embedding <=> CAST(:query_vector AS vector)) AS score
FROM document_chunks dc
WHERE dc.embedding IS NOT NULL
ORDER BY dc.embedding <=> CAST(:query_vector AS vector)
LIMIT 5;
```

**Cosine similarity** measures the angle between two vectors:
- **1.0** = identical direction (same meaning)
- **0.0** = perpendicular (unrelated)
- The top-K (default: 5) most similar chunks are retrieved

**Why pgvector instead of a dedicated vector DB (Pinecone, Qdrant)?**
- One fewer service to manage — everything lives in PostgreSQL
- Documents, chunks, metadata, conversations, AND vectors all in one database
- Simplifies backup, migrations, and deployment

**Code:** `backend/app/rag/retriever.py`

---

### 6. Context-Grounded LLM Generation

After retrieval, the top-K chunks are assembled into a structured prompt and sent to **Google Gemini `gemini-3.6-flash`** for answer generation.

**System prompt (anti-hallucination guardrail):**

```
You are a documentation assistant.
Answer ONLY using the provided context below.
If the answer is not present in the context, respond with exactly:
"I don't have this information in the documentation."
Do not make up information, speculate, or use knowledge outside the provided context.
```

**User prompt structure:**

```
Context:
[Source 1: manual.pdf, page 3]
PostgreSQL supports JSONB data types for storing...

---

[Source 2: guide.pdf, page 7]
To configure the database connection, set the DATABASE_URL...

Question:
How do I configure the database?
```

**Key LLM settings:**
- `temperature=0.0` — deterministic output, no creative variations
- `max_output_tokens=1024` — prevents excessively long answers
- System instruction support — the anti-hallucination prompt is injected as a system-level instruction

**Code:** `backend/app/rag/pipeline.py` and `backend/app/rag/prompts.py`

---

### 7. Conversation Persistence

The chat system maintains **multi-turn conversation history** stored in the database:

- Each conversation has a title (auto-generated from the first question)
- User messages and assistant responses are persisted with timestamps
- Source citations are stored as JSON alongside assistant messages
- Users can list, view, and delete past conversations

**Code:** `backend/app/services/chat_service.py`

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Frontend (Vanilla HTML/CSS/JS)               │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Login   │    │  Dashboard   │    │ Documents│    │   Chat   │  │
│  └──────────┘    └──────────────┘    └──────────┘    └──────────┘  │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP REST API
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    API Layer (v1 Router)                     │   │
│  │  /api/health  ·  /api/documents  ·  /api/chat              │   │
│  │  /api/conversations                                         │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                              │                                      │
│  ┌──────────────┐  ┌────────▼───────┐  ┌──────────────────────┐   │
│  │   Loaders    │  │   Services     │  │    RAG Pipeline      │   │
│  │  PDF / MD /  │  │  Document      │  │  Chunker             │   │
│  │  TXT         │  │  Ingestion     │  │  Retriever           │   │
│  │              │  │  Chat          │  │  Pipeline + Prompts  │   │
│  │              │  │  Embedding     │  │                      │   │
│  └──────────────┘  └────────────────┘  └──────────────────────┘   │
│                              │                                      │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │              Data Layer (SQLAlchemy ORM + Alembic)           │   │
│  │  Models: Document · DocumentChunk · Conversation · Message  │   │
│  │  Repositories: document · chunk · conversation              │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────┐
│  PostgreSQL + pgvector│          │  Google Gemini API   │
│  (Data + Vectors)     │          │  Embeddings + LLM    │
│  Docker Container     │          │  (Cloud Service)     │
└──────────────────────┘          └──────────────────────┘
```

---

## 📂 Project Structure

```
documentation-ai-assistant/
├── docker-compose.yml              # PostgreSQL + pgvector container
├── README.md                       # Setup & usage guide
│
├── backend/
│   ├── .env / .env.example         # Environment configuration
│   ├── requirements.txt            # Python dependencies
│   ├── alembic.ini                 # Database migration config
│   ├── migrations/                 # Alembic migration scripts
│   │
│   └── app/
│       ├── main.py                 # FastAPI app factory + lifespan
│       ├── core/config.py          # Pydantic settings (env vars)
│       │
│       ├── api/v1/
│       │   ├── router.py           # API router registration
│       │   ├── deps.py             # Dependency injection (DB session)
│       │   └── endpoints/
│       │       ├── health.py       # Health check endpoint
│       │       ├── documents.py    # Upload, list, delete documents
│       │       └── chat.py         # Chat + conversation endpoints
│       │
│       ├── models/                 # SQLAlchemy ORM models
│       ├── schemas/                # Pydantic request/response schemas
│       ├── repositories/           # Database query layer
│       ├── services/               # Business logic layer
│       │
│       ├── loaders/                # Document text extractors
│       │   ├── pdf_loader.py       # PyMuPDF-based PDF parser
│       │   ├── markdown_loader.py  # Markdown parser
│       │   └── txt_loader.py       # Plain text reader
│       │
│       ├── rag/                    # RAG pipeline components
│       │   ├── chunker.py          # Token-aware text splitting
│       │   ├── retriever.py        # pgvector cosine similarity search
│       │   ├── pipeline.py         # Orchestrates retrieval + generation
│       │   └── prompts.py          # System & context prompt templates
│       │
│       └── utils/                  # Text cleaning utilities
│
└── frontend/
    ├── index.html                  # Dashboard page
    ├── documents.html              # Document upload & management
    ├── chat.html                   # AI chat interface
    ├── login.html                  # Authentication page
    ├── css/                        # Stylesheets (base, layout, components, chat)
    └── js/                         # Frontend JavaScript logic
```

---

## 🔧 Technology Stack Summary

| Layer | Technology | Purpose |
|---|---|---|
| **Web Framework** | FastAPI | Async REST API with auto-generated OpenAPI docs |
| **ORM** | SQLAlchemy 2.0 | Database models, queries, and relationships |
| **Migrations** | Alembic | Schema versioning and database migrations |
| **Validation** | Pydantic v2 | Request/response serialization and validation |
| **Database** | PostgreSQL 18 | Relational data storage (documents, conversations) |
| **Vector Search** | pgvector | Native vector column type + cosine distance operator |
| **Containerization** | Docker Compose | PostgreSQL container with pgvector extension |
| **PDF Parsing** | PyMuPDF (fitz) | Page-by-page text extraction from PDFs |
| **Markdown Parsing** | markdown-it-py | Markdown → plaintext conversion |
| **HTML Parsing** | BeautifulSoup4 | Web page content extraction |
| **HTTP Client** | HTTPX | Async HTTP requests for URL fetching |
| **Tokenization** | tiktoken | Token-based text chunking (cl100k_base encoding) |
| **Embeddings** | Gemini `gemini-embedding-001` | 3072-dimensional semantic vector embeddings |
| **LLM** | Gemini `gemini-3.6-flash` | Context-grounded answer generation |
| **AI SDK** | google-genai | Python client for Google Gemini APIs |
| **Frontend** | HTML5, CSS3, JavaScript | Dashboard, document manager, and chat UI |
| **Testing** | pytest + pytest-asyncio | Automated unit and integration tests |

---

## 🔄 Complete Data Flow

### Document Ingestion Pipeline

```
User uploads PDF
        │
        ▼
┌─ Document Service ──────────────────────────────────────────┐
│  1. Save file to disk (data/uploads/)                       │
│  2. Create DB record (status: "processing")                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─ Ingestion Service ─────────────────────────────────────────┐
│  3. Load & extract text (PyMuPDF → page-by-page)            │
│  4. Clean text (normalize whitespace, strip artifacts)       │
│  5. Chunk into 800-token windows (100-token overlap)         │
│  6. Store chunks in document_chunks table                    │
│  7. Generate embeddings (Gemini API → 3072-dim vectors)      │
│  8. Store embeddings in pgvector column                      │
│  9. Update status → "ready"                                  │
└─────────────────────────────────────────────────────────────┘
```

### Question-Answer Pipeline

```
User asks: "How do I configure the database?"
        │
        ▼
┌─ Chat Service ──────────────────────────────────────────────┐
│  1. Create/resume conversation                               │
│  2. Persist user message                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─ RAG Pipeline ──────────────────────────────────────────────┐
│  3. Embed the question → 3072-dim query vector               │
│  4. pgvector cosine search → top 5 matching chunks           │
│  5. Build context: "[Source 1: file.pdf, page 3]\n..."       │
│  6. Send system prompt + context + question to Gemini        │
│  7. Gemini generates grounded answer with citations          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─ Response ──────────────────────────────────────────────────┐
│  8. Persist assistant message + source citations             │
│  9. Return answer + sources to frontend                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Design Decisions & Why

| Decision | Why |
|---|---|
| **pgvector over Pinecone/Qdrant** | Single database for everything — simpler ops, easier backup, no external vector DB cost |
| **Token-based chunking over character-based** | Guarantees chunks fit within model context windows regardless of word length |
| **Overlap between chunks (100 tokens)** | Prevents information loss at chunk boundaries — sentences split across chunks still have context |
| **temperature=0.0 for LLM** | Factual Q&A needs deterministic, reproducible answers — no creative variation |
| **System prompt anti-hallucination guard** | Forces the model to say "I don't know" rather than fabricate answers from training data |
| **Lazy imports for heavy libraries** | PyMuPDF, tiktoken, and google-genai are imported only when needed, keeping startup fast |
| **Repository pattern for DB access** | Clean separation between business logic (services) and database queries (repositories) |
| **Factory pattern for loaders** | Adding a new file format (e.g., DOCX) requires only writing a new loader — no changes to the pipeline |
