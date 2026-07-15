# IELTS Tutor Backend

Single-port FastAPI backend for AI-powered IELTS learning platform with all services as route prefixes under `/api/*`.

## Architecture

- **FastAPI** on port 8000
- **PostgreSQL** on port 5432 (via Docker)
- **Redis** on port 6379 (via Docker)
- **LM Studio** (or similar Ollama) on port 1234 for local LLM inference

## Quick Start (Local Development)

### 1. Start Docker Services

```powershell
cd D:\IELTS_Tutor\backend
docker compose up -d
```

This starts PostgreSQL and Redis containers.

### 2. Set Up Python Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\pip.exe install -r requirements.txt
```

### 3. Seed Database

```powershell
.venv\Scripts\python.exe -m shared.seed
```

### 4. Start Backend

```powershell
.venv\Scripts\python.exe main.py
```

Backend runs at **http://localhost:8000**

### 5. Start LM Studio

1. Open LM Studio
2. Load MiniMax-M2.5 model
3. Start server on port 1234

## API Endpoints

All services are mounted under `/api` prefix:

| Endpoint | Description |
|----------|-------------|
| `/api/profile` | User profile, band scores, milestones, roadmap |
| `/api/reading` | Passages, questions, sessions, scoring |
| `/api/listening` | Audio tests, questions, scoring |
| `/api/writing` | Essay submission, AI scoring |
| `/api/vocabulary` | Word list, spaced repetition |
| `/api/grammar` | Topics, mistakes, exercises |
| `/api/import` | OCR processing for exam import |
| `/api/analytics` | Progress, predictions |
| `/api/agent` | AI chat, scoring, vocab enrichment |

## Example Calls

```bash
# Health check
curl http://localhost:8000/health

# Get profile (requires auth - returns demo user)
curl http://localhost:8000/api/profile

# Get reading passages
curl http://localhost:8000/api/reading/passages

# Get vocabulary
curl http://localhost:8000/api/vocabulary

# Get analytics
curl http://localhost:8000/api/analytics/band-scores
```

## Environment Variables

Create `.env` file (already configured for local dev):

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ielts
POSTGRES_PASSWORD=ielts_secret
POSTGRES_DB=ieltsdb
DATABASE_URL=postgresql+asyncpg://ielts:ielts_secret@localhost:5432/ieltsdb

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# LLM (LM Studio / OpenAI compatible)
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=MiniMax-M2.5
LLM_API_KEY=lm-studio
```

## Service Structure

```
services/
├── profile/      # User profile, band scores
├── reading/      # Reading passages & questions
├── listening/    # Audio practice
├── writing/      # Essay evaluation
├── vocabulary/   # Flashcards, spaced repetition
├── grammar/      # Grammar skills tracking
├── import_svc/   # OCR exam import
├── analytics/    # Progress & predictions
└── ai_agent/     # LangGraph agents for AI features
```

## Development

```bash
# Run tests
pytest

# Run with auto-reload
.venv\Scripts\python.exe -m uvicorn main:app --reload
```

## Docker Production

```bash
# Build and run
docker compose up -d --build

# View logs
docker compose logs -f backend
```