# 📚 Documentation AI Assistant

An intelligent, full-stack **Retrieval-Augmented Generation (RAG)** documentation assistant that parses, indexes, and queries technical documentation (PDFs, Markdown, Web/HTML) using **FastAPI**, **PostgreSQL + pgvector**, and **Google Gemini**.

---

## 🚀 Features

- **Multi-Format Document Ingestion:** Supports uploading and extracting text from:
  - 📄 **PDFs** (via PyMuPDF)
  - 📝 **Markdown files** (`.md`)
  - 🌐 **Web URLs / HTML** (via BeautifulSoup + HTTPX)
- **Token-Aware Chunking:** Smart text splitting using `tiktoken` with configurable chunk sizes and overlap to preserve context across boundaries.
- **Vector Search with pgvector:** Uses PostgreSQL's `pgvector` extension for efficient cosine similarity semantic search.
- **AI Chat with Source Citations:** Generates accurate answers using Google Gemini (`gemini-2.0-flash`) grounded in retrieved document context, complete with source references.
- **Built-in Web Interface:** Clean and responsive UI for uploading documents, monitoring processing status, and querying the knowledge base.

---

## 🏗️ Architecture & How It Works

```
 ┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
 │   User / Web    │ ────> │     FastAPI Backend    │ ────> │  PostgreSQL+pgvector │
 │    Interface    │ <──── │ (API, Parsers, RAG)    │ <──── │   (Docs & Vectors)   │
 └─────────────────┘       └────────────────────────┘       └──────────────────────┘
                                       │
                                       ▼
                           ┌────────────────────────┐
                           │    Google Gemini API   │
                           │  (Embeddings & LLM)    │
                           └────────────────────────┘
```

### Ingestion Workflow:
1. **Upload / Submit:** User uploads a document (PDF, Markdown) or provides a web URL.
2. **Extraction:** Specialized parsers extract clean text and metadata.
3. **Chunking:** Text is split into token-based chunks with overlap.
4. **Embedding Generation:** Google Gemini (`text-embedding-004`) computes vector representations for each chunk.
5. **Database Storage:** Document metadata, chunks, and vector embeddings are stored in PostgreSQL.

### Query Workflow:
1. **User Prompt:** A question is submitted via the chat interface or `/api/chat` endpoint.
2. **Retrieval:** The question is embedded and `pgvector` performs a cosine similarity search to retrieve top relevant chunks.
3. **Context Augmentation:** Retrieved chunks and system prompts are assembled.
4. **Answer Generation:** Gemini LLM generates a response with citations referencing source documents and chunk excerpts.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic
- **Database:** PostgreSQL with `pgvector`
- **RAG & NLP:** Google Gemini API (`text-embedding-004`, `gemini-2.0-flash`), PyMuPDF, BeautifulSoup4, tiktoken
- **Frontend:** Vanilla HTML5, CSS3, JavaScript
- **Infrastructure:** Docker & Docker Compose

---

## 📋 Prerequisites

Before running the project locally, ensure you have installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [Docker & Docker Desktop](https://www.docker.com/) (for PostgreSQL with `pgvector`)
- A [Google Gemini API Key](https://aistudio.google.com/apikey) (free tier available)

---

## ⚙️ Local Setup Guide

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "documentation-ai-assistant"
```

### 2. Start PostgreSQL with pgvector (via Docker)
Start the database container configured with `pgvector`:
```bash
docker compose up -d
```
> **Note:** The database will be accessible locally on port `5434` (mapped to PostgreSQL's default `5432` internally to avoid port conflicts with any local PostgreSQL instance).

---

### 3. Set Up the Python Backend

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to create `.env` in the `backend/` directory:
   - **Windows (PowerShell):**
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS:**
     ```bash
     cp .env.example .env
     ```

---

## 🔐 Environment Variables Reference (`backend/.env`)

Make sure your `backend/.env` file contains the following configurations:

```env
# --- Application Configuration ---
APP_NAME=Documentation Assistant
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api

# --- Server Configuration ---
HOST=0.0.0.0
PORT=8000

# --- Database (PostgreSQL + pgvector) ---
DATABASE_URL=postgresql+psycopg2://postgres:12345@localhost:5434/documentation_assistant

# --- LLM & Vector Embeddings (Gemini) ---
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=768
LLM_MODEL=gemini-2.0-flash

# --- File Storage & Upload Limits ---
UPLOAD_DIR=data/uploads
MAX_UPLOAD_SIZE_MB=25
```

### Key Variables Explained

| Variable | Description | Default / Example Value |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL (port `5434` matches `docker-compose.yml`) | `postgresql+psycopg2://postgres:12345@localhost:5434/documentation_assistant` |
| `GEMINI_API_KEY` | Your Google Gemini API Key used for embeddings and generation | Get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `EMBEDDING_MODEL` | Gemini embedding model name | `text-embedding-004` |
| `EMBEDDING_DIMENSION` | Dimensions corresponding to the embedding model | `768` |
| `LLM_MODEL` | Gemini model used to generate chat answers | `gemini-2.0-flash` |
| `UPLOAD_DIR` | Local directory where uploaded files are temporarily saved | `data/uploads` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed file upload size in megabytes | `25` |

---

### 4. Run Database Migrations

Run database initialization or Alembic migrations:
```bash
alembic upgrade head
```

---

### 5. Run the Application

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Accessing the Application

Once running, access the services at:

- **Web UI:** [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)
- **Chat Assistant:** [http://localhost:8000/static/chat.html](http://localhost:8000/static/chat.html)
- **Document Management:** [http://localhost:8000/static/documents.html](http://localhost:8000/static/documents.html)
- **Interactive API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative API Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health and database status check |
| `POST` | `/api/documents/upload` | Upload & ingest a PDF/Markdown file |
| `POST` | `/api/documents/url` | Ingest web documentation from a URL |
| `GET` | `/api/documents` | List indexed documents and metadata |
| `DELETE`| `/api/documents/{id}` | Delete a document and its embeddings |
| `POST` | `/api/chat` | Query documents with natural language (RAG) |

---

## 🧪 Running Tests

To run the automated test suite:
```bash
pytest
```
