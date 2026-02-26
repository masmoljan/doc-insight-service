# Document Ingestion Service

FastAPI service that ingests PDFs/images, stores embeddings in vector database and answers questions about them using OpenAI.

## Features
- Upload PDFs or images and extract text (PyMuPDF4LLM + EasyOCR fallback)
- Chunk and embed documents, store in Postgres + pgvector
- Ask questions and retrieve relevant chunks before answering
- Question classifier to reject vague or placeholder questions
- Session-based (anonymous) and user-based (JWT) document scoping
- JWT auth + rate limiting
- Embedding cache (Redis)
- Encrypted document chunk content at rest (AES-256-GCM)
- Structured JSON logging (structlog)
- Streamlit demo UI
- CI: lint + Docker build

## Setup
Before running the api, create the `.env` file with the required variables:
```
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/postgres
JWT_SECRET=example-secret
OPENAI_API_KEY=example-key
DATA_ENCRYPTION_KEY=32-char-secret-key-here
REDIS_PASSWORD=change-me
```

Optional variables (override defaults):
```
JWT_EXPIRES_MINUTES=1440
SESSION_EXPIRES_MINUTES=1440
SESSION_CLEANUP_INTERVAL_MINUTES=60
DATABASE_URL_DOCKER=postgresql+psycopg://user:password@db:5432/postgres
RATE_LIMIT_REDIS_URL=redis://:change-me@localhost:6379/0
RATE_LIMIT_DEFAULT=120/minute
RATE_LIMIT_AUTH_TOKEN=5/minute
RATE_LIMIT_AUTH_REGISTER=3/minute
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_ASK=60/minute
EMBEDDING_CACHE_REDIS_URL=redis://:change-me@localhost:6379/1
EMBEDDING_CACHE_DOC_TTL_SECONDS=43200
UPLOAD_MAX_FILES=5
UPLOAD_MAX_FILE_SIZE_BYTES=10485760
PORT=8000
API_BASE_URL=http://localhost:8000
```

## Installation and running
Local (venv):
```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Docker:
```bash
docker compose up --build
```
Docker requires `REDIS_PASSWORD` to be set in `.env`.
Docker uses `DATABASE_URL_DOCKER` (if set) or defaults to the `db` hostname.

## Streamlit demo
```bash
streamlit run ui/streamlit.py
```
Start the API first, then open `http://localhost:8501`.

## API Endpoints

FastAPI auto-generates interactive API docs at `http://localhost:8000/docs`

### Health
```bash
curl -X GET "http://localhost:8000/health"
```
Response:
```json
{"status":"Document ingestion service is available."}
```

### Upload (anonymous)
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@./path/to/file.pdf"
```
Response:
```json
{
  "message":"Files uploaded successfully",
  "document_ids":["<doc-id>"],
  "session_id":"<session-id>"
}
```

### Upload (authenticated)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer <token>" \
  -F "files=@./path/to/file.pdf"
```
Response:
```json
{
  "message":"Files uploaded successfully",
  "document_ids":["<doc-id>"]
}
```

### Ask (anonymous session)
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the invoice total?","session_id":"<session-id>"}'
```
Response:
```json
{"answer":"$1,245.00"}
```

### Register + token (authenticated)
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```
Response:
```json
{
  "user_id":"<user-id>",
  "access_token":"<token>",
  "token_type":"Bearer",
  "expires_in_minutes":1440
}
```

### Ask (authenticated)
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the invoice total?"}'
```
Response:
```json
{"answer":"$1,245.00"}
```

## Notes
- File size is limited 10 MB per file with max upload of 5 files per API call (configurable)
- Supported file types: PDF, PNG, JPG, JPEG
- Redis is required for rate limiting; embedding cache is optional. Docker uses `REDIS_PASSWORD`.
- Database migrations run automatically on app startup

## Approach & Tools
<details>
  <summary><strong>Expand for full details</strong></summary></br>

**PDF extraction and OCR fallback**</br> 
The initial idea started with building a small service that extracts text from PDF files. I experimented with PyMuPDF as suggested and did a small research to find out that there is an LLM optimized version of that package named PyMuPDF4LLM. I compared the `/ask` endpoint with the same uploaded PDF (text mixed with bullet points, headers, and some text formatting) using both packages and logged the response details from OpenAI. In my local test this resulted in ~53% fewer tokens used with PyMuPDF4LLM, so it seemed like a good choice. There was the same amount of chunks generated in the DB for that specific PDF regardless of the package used.
Once I got that covered I moved on to testing image upload and PDFs with pages containing an image, so for simplicity I opted for EasyOCR with custom logic to handle that.

**Document analysis**</br> 
For analysis I decided to use LangChain, which provides useful utilities for interacting with the LLM like chat capabilities, text splitting, and features that could be used in further expansion and improvement in this service. For context analysis I used the GPT-4.1 model as it provided good answer quality for the questions I tested.

**DB/Embeddings/Migrations**</br> 
For the database I used PostgreSQL with the pgvector extension. Although there are better vector storage options, I opted for this one due to experience, simplicity, and integration with the rest of the functionalities like having Users, Sessions, and Documents. Initially, for proof of concept, I started with raw SQL migration files and decided to implement the SQLModel ORM to interact with the database while providing parameterized queries. For migrations I went with Alembic as a tool to handle database migrations since it is compatible with this model.

**Rate limiting and caching**</br>
I used Redis for caching the embeddings during upload, which also enabled me to integrate the SlowAPI package for rate limiting and avoid relying on server memory or DB storage for repeated requests.

**Logging**</br>
Structlog is used as a middleware to log requests with three log levels based on status codes.

**Configuration**</br>
For configuration I used pydantic-settings to simplify configuration handling, since it has built-in checks to fail fast on missing env variables.

**UI prototype**</br>
I used Streamlit to quickly prototype a simple UI for uploading documents and asking questions against the API endpoints.


</details>

## Ideas for future improvements
<details>
  <summary><strong>Expand for full details</strong></summary></br>
- Store conversations and messages for authenticated users to enable conversation storage and follow-up conversations</br>
- Upgrade `/ask` endpoint to be history-aware: given chat history and the latest user question that might reference it, reformulate a standalone question (do not answer yet), retrieve relevant chunks, then answer using the retrieved context plus chat history</br>
- Implement a hybrid user/session flow: a user starts anonymously, then logs in and the session is bound to their account</br>
</details>
