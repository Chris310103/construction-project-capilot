# Construction Project Intelligence Copilot

An API-first construction intelligence platform that combines
document ingestion, Retrieval-Augmented Generation (RAG), SQL
analytics, and LLM tool calling to answer project questions
with traceable evidence.

## Tech Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- Database: PostgreSQL 16, pgvector
- AI: OpenAI API, text-embedding-3-small, GPT-4.1-mini
- Retrieval: Vector Search, PostgreSQL Full-Text Search,
  Reciprocal Rank Fusion (RRF), Cross-Encoder Reranking
- Infrastructure: Docker Compose, GitHub Actions, pytest

## Core Features

### Document Ingestion

- CSV ingestion for RFIs, Change Orders, Daily Reports,
  Schedule Activities, and Cost Records
- PDF text extraction, chunking, and indexing
- Structured field extraction for supported RFI PDF templates
- Pydantic validation and PostgreSQL upsert operations
- Automated embedding generation after file upload

### Hybrid RAG

- Semantic search using OpenAI embeddings and pgvector
- Keyword search using PostgreSQL Full-Text Search
- RRF rank fusion and Cross-Encoder reranking
- Document-type filtering and exact identifier retrieval
- Source citations with file, page, or CSV row references

### Agentic SQL Analytics

The LLM agent selects tools for:

- Document retrieval and multi-document reasoning
- Open RFI analysis
- Approved Change Order aggregation
- Cost variance analysis
- Preliminary schedule risk assessment
- RFI-to-schedule activity associations

SQL responses include source-table provenance.

## Architecture

Document Upload
    → FastAPI
    → Document Classification
    → Pydantic Validation
    → PostgreSQL / Document Chunks
    → OpenAI Embeddings / pgvector
    → Hybrid Retrieval + Reranking
    → LLM Agent + SQL Tools
    → Answer + Sources

## Local Setup

Requirements: Docker Desktop and an OpenAI API key.

Create a `.env` file using `.env.example` as a starting point.
Set your own OPENAI_API_KEY and database configuration.

Start the services:

```bash
docker compose -f docker-compose.yaml -f compose.api.yaml up -d --build
```

Initialize the demonstration database:

```bash
docker compose -f docker-compose.yaml -f compose.api.yaml exec api python -m scripts.create_tables
docker compose -f docker-compose.yaml -f compose.api.yaml exec api python -m scripts.seed_demo
docker compose -f docker-compose.yaml -f compose.api.yaml exec api python -m scripts.seed_business_demo
docker compose -f docker-compose.yaml -f compose.api.yaml exec api python -m scripts.seed_rfi_activity_link
```

Open Swagger UI:

http://127.0.0.1:8001/docs

## API Endpoints

| Endpoint | Description |
|---|---|
| GET /health | API health check |
| GET /health/db | Database health check |
| POST /ask | Agent-powered project Q&A |
| POST /projects/{project_id}/documents/upload | Upload and ingest documents |
| GET /projects/{project_id}/documents/{document_id}/index-status | Embedding index status |

## Evaluation

A 120-query synthetic evaluation suite covers:

| Category | Basic Checks Passed |
|---|---|
| Factual Retrieval | 30/30 |
| Multi-document Reasoning | 30/30 |
| SQL Aggregation | 30/30 |
| Schedule / Cost Analysis | 30/30 |
| Total | 120/120 |

Overall average answer latency: 2.912 seconds.

Results represent post-fix keyword and source-presence checks
on synthetic evaluation data. They do not establish 100% semantic
answer accuracy or real-world generalization.

Evaluation results are stored under `eval/results/`.

## Testing and CI

Run local automated tests:

```bash
python -m pytest -v
```

GitHub Actions executes tests on Ubuntu with Python 3.12,
PostgreSQL, and pgvector.

## Current Limitations

- Structured PDF extraction currently supports a specific RFI format.
- Other PDFs are indexed primarily as unstructured documents.
- Citation identifiers are validated, but full claim-level
  entailment verification is not implemented.
- Background embedding tasks are not backed by a durable queue.
- File uploads require authentication before public deployment.
- Current evaluation uses synthetic data and basic checks.
- Full token-cost tracking and independent holdout evaluation
  remain future improvements.

## Project Status

Functional backend MVP with Docker deployment, automated
testing, Hybrid RAG, SQL analytics, and document ingestion.
Not intended for public production deployment without
additional security and reliability controls.