# Documentation Assistant — Full Build Plan (Python + PostgreSQL, Enterprise Structure)

## 1. What You're Building

A production-style RAG (Retrieval-Augmented Generation) system where users upload docs (PDF/MD/TXT/URL), the system chunks + embeds them into PostgreSQL (pgvector), and a chat interface answers questions grounded only in that content, with source citations.

---

## 2. Full Tech Stack & Required Libraries

### Backend (Python)
| Purpose | Library |
|---|---|
| Web framework | `fastapi` |
| ASGI server | `uvicorn[standard]` |
| ORM | `sqlalchemy` (2.x) |
| Migrations | `alembic` |
| PostgreSQL driver | `psycopg2-binary` (or `asyncpg` if going async) |
| Vector type support | `pgvector` (python package, works with SQLAlchemy) |
| Config/env | `python-dotenv`, `pydantic-settings` |
| Data validation | `pydantic` (v2) |
| PDF parsing | `pymupdf` (fitz) |
| Markdown parsing | `markdown-it-py` or `python-markdown` |
| HTML/web scraping | `beautifulsoup4`, `httpx` |
| Text chunking | custom, or `langchain-text-splitters` |
| Tokenizer (for chunk sizing) | `tiktoken` |
| Embeddings/LLM client | `openai` (or `google-generativeai`, or `anthropic`) |
| Auth | `python-jose[cryptography]`, `passlib[bcrypt]` |
| File uploads | built into FastAPI (`python-multipart`) |
| Testing | `pytest`, `pytest-asyncio`, `httpx` (for test client) |
| Background tasks (optional) | `celery` + `redis`, or FastAPI `BackgroundTasks` for MVP |
| Logging | `loguru` or stdlib `logging` |
| Rate limiting (optional) | `slowapi` |

Install (MVP set):
```bash
pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary pgvector \
  pydantic pydantic-settings python-dotenv pymupdf beautifulsoup4 httpx \
  tiktoken openai python-jose[cryptography] passlib[bcrypt] python-multipart pytest pytest-asyncio
```

### Database
- **PostgreSQL 15+**
- **pgvector extension** (`CREATE EXTENSION vector;`)

### Frontend
- HTML5, CSS3, vanilla JavaScript (Fetch API)
- No framework required; optionally add `marked.js` (CDN) for rendering markdown answers and `highlight.js` for code blocks

### DevOps
- `Docker` + `docker-compose` (app + postgres containers)
- `.env` for secrets
- `pytest` + GitHub Actions (optional CI)

---

## 3. System Architecture

```
Browser (HTML/CSS/JS)
        │ HTTP/JSON
        ▼
FastAPI Backend (routers → services → repositories)
        │
   ┌────┼─────────────┬──────────────┐
   ▼    ▼              ▼              ▼
Document  RAG        Chat        Auth
Service   Service     Service     Service
   │        │            │           │
   └────────┴─────┬──────┴───────────┘
                   ▼
       PostgreSQL + pgvector
   (users, documents, chunks, conversations, messages)
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  Embedding API             LLM API
```

**Layering rule (enterprise pattern):**
`API route → Service (business logic) → Repository (DB access) → Model (SQLAlchemy)`
Never put DB queries or LLM calls directly in route handlers.

---

## 4. Enterprise-Style Folder Structure

```
documentation-assistant/
│
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app entrypoint
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── router.py           # aggregates all v1 routes
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── documents.py
│   │   │   │   │   ├── chat.py
│   │   │   │   │   ├── conversations.py
│   │   │   │   │   ├── auth.py
│   │   │   │   │   └── health.py
│   │   │   │   └── deps.py             # shared FastAPI dependencies (auth, db session)
│   │   │
│   │   ├── core/
│   │   │   ├── config.py               # pydantic-settings, env vars
│   │   │   ├── security.py             # JWT, password hashing
│   │   │   ├── logging.py
│   │   │   └── exceptions.py           # custom exception classes + handlers
│   │   │
│   │   ├── db/
│   │   │   ├── base.py                 # SQLAlchemy Base
│   │   │   ├── session.py              # engine + SessionLocal
│   │   │   └── init_db.py
│   │   │
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── chunk.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   │
│   │   ├── schemas/                    # Pydantic request/response models
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   └── conversation.py
│   │   │
│   │   ├── repositories/               # raw DB queries, isolated from business logic
│   │   │   ├── document_repository.py
│   │   │   ├── chunk_repository.py
│   │   │   └── conversation_repository.py
│   │   │
│   │   ├── services/                   # business logic
│   │   │   ├── document_service.py
│   │   │   ├── ingestion_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── retrieval_service.py
│   │   │   ├── chat_service.py
│   │   │   └── auth_service.py
│   │   │
│   │   ├── rag/                        # RAG pipeline internals
│   │   │   ├── chunker.py
│   │   │   ├── retriever.py
│   │   │   ├── reranker.py
│   │   │   ├── prompts.py
│   │   │   └── pipeline.py
│   │   │
│   │   ├── loaders/                    # document parsing
│   │   │   ├── pdf_loader.py
│   │   │   ├── markdown_loader.py
│   │   │   ├── txt_loader.py
│   │   │   └── url_loader.py
│   │   │
│   │   └── utils/
│   │       ├── text_cleaner.py
│   │       └── token_counter.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   ├── migrations/                     # alembic
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── index.html                      # dashboard
│   ├── chat.html
│   ├── documents.html
│   ├── login.html
│   │
│   ├── css/
│   │   ├── base.css
│   │   ├── layout.css
│   │   ├── chat.css
│   │   └── components.css
│   │
│   ├── js/
│   │   ├── api.js                      # fetch wrapper
│   │   ├── auth.js
│   │   ├── documents.js
│   │   ├── chat.js
│   │   └── utils.js
│   │
│   └── assets/
│       └── icons/
│
├── data/
│   ├── uploads/
│   └── sample_docs/
│
├── docker-compose.yml
├── .gitignore
├── README.md
└── LICENSE
```

---

## 5. Database Schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR NOT NULL,
    file_type VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size INTEGER,
    status VARCHAR DEFAULT 'processing',  -- processing | ready | failed
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER,
    page_number INTEGER,
    embedding VECTOR(1536),   -- match your embedding model's dimension
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,   -- user | assistant
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 6. RAG Pipeline (Core Logic)

```
Upload → Extract text → Clean → Chunk (500–1000 tokens, 50–150 overlap)
→ Embed each chunk → Store in pgvector

Question → Embed question → Vector similarity search (top K)
→ (optional) hybrid keyword search + rerank → Build context
→ Prompt LLM with context-only instructions → Answer + cited sources
```

Prompt template (`rag/prompts.py`):
```
You are a documentation assistant.
Answer ONLY using the provided context.
If the answer isn't in the context, say: "I don't have this information in the documentation."
Do not fabricate information.

Context:
{context}

Question:
{question}
```

---

## 7. API Endpoints

```
GET    /api/health
POST   /api/auth/register
POST   /api/auth/login

POST   /api/documents/upload
GET    /api/documents
GET    /api/documents/{id}
DELETE /api/documents/{id}

POST   /api/chat
GET    /api/conversations
GET    /api/conversations/{id}
DELETE /api/conversations/{id}
```

---

## 8. Build Order — Phase by Phase

### Phase 1 — Environment Setup
- Create project folder + venv
- Install core packages: `fastapi uvicorn sqlalchemy python-dotenv`
- Set up `.env`, `core/config.py` (pydantic-settings)
- Basic FastAPI app that runs (`/api/health` returns OK)

### Phase 2 — PostgreSQL + pgvector Setup
- Install PostgreSQL locally (or via Docker)
- Create database `documentation_assistant`
- Run `CREATE EXTENSION vector;`
- Connect SQLAlchemy (`db/session.py`, `db/base.py`)
- Verify connection with a test query

### Phase 3 — Database Models & Migrations
- Create SQLAlchemy models: `User`, `Document`, `DocumentChunk`, `Conversation`, `Message`
- Set up Alembic, generate first migration
- Apply migration, confirm tables exist in Postgres

### Phase 4 — Document Upload
- `POST /api/documents/upload` endpoint
- Accept `.pdf`, `.md`, `.txt`
- Save file to `data/uploads/`, insert row into `documents` table (`status = processing`)
- `GET /api/documents`, `GET /api/documents/{id}`, `DELETE /api/documents/{id}`

### Phase 5 — Text Extraction & Cleaning
- `loaders/pdf_loader.py` (PyMuPDF)
- `loaders/markdown_loader.py`, `loaders/txt_loader.py`
- `utils/text_cleaner.py` — strip noise, normalize whitespace

### Phase 6 — Chunking
- `rag/chunker.py` — split text into 500–1000 token chunks, 50–150 token overlap
- Store chunks in `document_chunks` (no embedding yet)
- Test chunking on a sample PDF, inspect chunk boundaries

### Phase 7 — Embeddings
- `services/embedding_service.py` — call embedding API (OpenAI/Gemini/HF)
- Generate embedding per chunk, store in `embedding` column (pgvector)
- Update `documents.status = ready` once all chunks are embedded

### Phase 8 — Retrieval (Vector Search)
- `rag/retriever.py` — embed the question, run cosine similarity search via pgvector
- Return top-K chunks with similarity scores
- Test retrieval quality manually against a few known questions

### Phase 9 — RAG Pipeline & LLM Integration
- `rag/prompts.py` — the context-only prompt template
- `rag/pipeline.py` — glue: question → retrieve → build context → call LLM → answer
- `POST /api/chat` endpoint wired to the pipeline
- Handle "no relevant chunks found" case explicitly

### Phase 10 — Source Citations
- Return `document`, `page_number`/`section`, `chunk_id` alongside each answer
- Display citations in the API response shape (`sources: [...]`)

### Phase 11 — Frontend (Dashboard + Upload UI)
- `index.html` + `css/base.css`, `css/layout.css`
- Sidebar nav, dashboard stats (doc count, chunk count)
- `documents.html` — upload form, document list, delete button
- `js/api.js` (fetch wrapper), `js/documents.js`

### Phase 12 — Frontend (Chat UI)
- `chat.html`, `css/chat.css`
- Chat bubbles, source badges under each answer, loading state
- `js/chat.js` — send question to `/api/chat`, render response + sources

### Phase 13 — Conversations & Chat History
- `conversations` + `messages` tables wired into chat flow
- `GET/DELETE /api/conversations`, `GET /api/conversations/{id}`
- Persist each Q&A pair, load history when reopening a conversation

### Phase 14 — Auth (Optional but Recommended)
- `POST /api/auth/register`, `POST /api/auth/login` (JWT)
- Protect document/chat routes with `deps.py` auth dependency
- Scope documents/conversations to `user_id`

### Phase 15 — Advanced Features & Hardening
- Streaming responses (SSE) for chat
- Website URL ingestion (`loaders/url_loader.py`)
- Hybrid search (keyword + vector) and reranking (`rag/reranker.py`)
- RAG evaluation set (20–30 QA pairs) + basic metrics (recall@K, faithfulness)
- Dockerize (backend + Postgres via `docker-compose.yml`)
- README, `.env.example`, final polish, deploy

**Rule of thumb:** don't start a phase until the previous one has a working, testable result. Each phase should leave you with something you can run and verify — not just code that "should work."

---

## 9. Milestone 1 (Start Here — Smallest Working Version)

```
PDF → Extract text → Chunk → Embed → Store in pgvector
→ Ask question → Retrieve top 5 chunks → LLM answer
```

Get this working as a script first (no FastAPI, no frontend) before wiring up the API and UI. This proves the RAG core works before you add architecture around it.

---

## 10. Recommendation

Build the RAG pipeline yourself first (loader → chunker → embedder → pgvector → retriever → prompt → LLM) before introducing LangChain/LlamaIndex. Once it works, optionally reimplement with LangChain and compare — that comparison is where the real learning happens.
