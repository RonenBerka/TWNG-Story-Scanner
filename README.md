# TWNG Story Scanner

Curate guitar-related stories from Reddit (and future sources) into a reviewable pipeline. Built with FastAPI, Celery/Redis, Postgres, and React.

## Prerequisites

- **Docker Desktop** (Docker Compose v2)
- **Git**
- Ports available: `5432` (Postgres), `6379` (Redis), `8000` (API), `5173` (Frontend)

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd TWNG-Story-Scanner

# 2. Create your env file
cp .env.example .env          # edit secrets for production

# 3. Start everything
make dev                      # docker compose up --build -d

# 4. Run migrations + see admin credentials
make seed
```

After `make seed` you'll see:

```
[2/2] Admin credentials (from environment):
  Username : admin
  Password : admin
```

## Running the Pipeline

```bash
# Ingest Reddit posts (uses public JSON endpoints; no API key required)
make ingest

# Score unscored candidates with heuristic rules
make score

# Enrich candidates above the score threshold (summary, category, tags)
make enrich

# Or run all three in sequence:
make pipeline
```

## Using the Admin UI

1. Open **http://localhost:5173**
2. Log in with admin credentials (default: `admin` / `admin`)
3. Browse candidates in the **Inbox** — filter by status, score, source, language
4. Click a row to preview the story (excerpt, summary, tags, entities)
5. **Approve** moves the story to the TWNG Story Records collection
6. **Reject** with an optional reason removes it from the queue

## API Docs

Interactive Swagger docs: **http://localhost:8000/docs**

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/candidates` | List candidates (filterable) |
| `POST` | `/candidates/{id}/approve` | Approve → create TWNG record |
| `POST` | `/candidates/{id}/reject` | Reject with optional reason |
| `GET` | `/records` | List approved TWNG records |
| `POST` | `/admin/tasks/ingest-reddit` | Trigger async ingest (Celery) |
| `POST` | `/admin/tasks/process-candidates` | Trigger async scoring |
| `GET` | `/admin/tasks/status/{task_id}` | Check async task status |
| `GET` | `/health` | Health check |

All endpoints except `/health` and `/auth/login` require `Authorization: Bearer <token>`.

## Make Targets

```
make dev             Start the full stack (build + up)
make down            Stop all services
make clean           Stop services AND remove volumes (DB data lost)
make seed            Run migrations + show admin credentials
make ingest          Ingest Reddit posts
make score           Score unscored candidates
make enrich          Enrich candidates above threshold
make pipeline        Run full pipeline: ingest → score → enrich
make test            Run backend tests
make logs            Tail all service logs
```

## Running Tests

```bash
make test
# or directly:
docker compose exec backend pytest -q
```

## Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Frontend │───▶│ Backend  │───▶│ Postgres │
│ React    │    │ FastAPI  │    │          │
│ :5173    │    │ :8000    │    │ :5432    │
└──────────┘    └────┬─────┘    └──────────┘
                     │
                     ▼
                ┌──────────┐    ┌──────────┐
                │  Worker  │───▶│  Redis   │
                │  Celery  │    │  :6379   │
                └──────────┘    └──────────┘
```

**Data flow:** Reddit → CandidateStory → Score → Enrich → Admin Review → TWNGStoryRecord

## Configuration

All config is via environment variables (`.env` file). See `.env.example` for the full list.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Postgres connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET` | Yes | Secret key for JWT tokens (change in production!) |
| `ADMIN_USERNAME` | Yes | Admin login username |
| `ADMIN_PASSWORD` | Yes | Admin login password |
| `REDDIT_CLIENT_ID` | No | Reddit API client ID (enables PRAW mode) |
| `REDDIT_CLIENT_SECRET` | No | Reddit API secret |
| `REDDIT_USER_AGENT` | No | Reddit API user agent |
| `ENRICHMENT_SCORE_THRESHOLD` | No | Min score for enrichment (default: 0.65) |
| `OPENAI_API_KEY` | No | Enables GPT-based enrichment (otherwise local heuristics) |

**Reddit ingestion works without API credentials** using Reddit's public JSON endpoints. Setting `REDDIT_CLIENT_ID` upgrades to the official PRAW library with higher rate limits.

## Project Structure

```
backend/
├── app/
│   ├── api/routes/       # FastAPI endpoints (auth, candidates, records, tasks)
│   ├── collectors/       # Reddit collector (dual-mode: JSON + PRAW)
│   ├── core/             # Security, collector config
│   ├── db/               # Models, session, seed, migrations
│   ├── enrichment/       # Provider abstraction (local + OpenAI)
│   ├── scoring/          # Prefilter rules + StoryScore heuristics
│   ├── worker/           # Celery app + async tasks
│   ├── cli.py            # CLI entry points
│   └── main.py           # FastAPI app
├── tests/                # Pytest suite
├── alembic/              # Database migrations
└── Dockerfile

frontend/
├── src/
│   ├── components/       # CandidateTable, CandidatePreview, Filters
│   ├── lib/              # API client, TanStack Query hooks, auth context
│   └── pages/            # Login, Inbox
├── package.json
└── Dockerfile
```

## License

Private — TWNG internal use.
