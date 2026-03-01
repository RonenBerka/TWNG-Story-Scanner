# TWNG Story Scanner — Phase 0–1 Backlog + Agent Prompts (v1.0)
Date: 2026-02-28

This file contains 10 implementation tasks for the TWNG Story Scanner MVP (FastAPI + Celery/Redis + Postgres + React/Vite),
plus ready-to-paste prompts for:
- **Codex** (build/execute tasks inside the repo)
- **Claude** (diff review + QA)

Core constraints (apply to ALL tasks)
- Compliance-first: **no scraping circumvention**, no VPN/IP rotation/UA spoofing, no ToS-evasion.
- Store minimal data by default: **URL/ID + metadata + short excerpt + our summary/tags**, avoid storing full third‑party text long-term.
- Secrets: **never hardcode**. Use `.env` + `.env.example`.
- Definition of Done (DoD): must include runnable commands + tests/smoke checks.


---

## Task 1 — Bootstrap repo + Docker Compose

Goal
- Bring up local dev stack: Postgres + Redis + backend + frontend.

Inputs
- Empty repo.

Outputs
- `docker compose up --build` brings everything up.
- Backend health endpoint works.
- Frontend loads.

DoD
- `docker compose up --build` succeeds.
- `GET http://localhost:8000/health` returns `200` JSON.
- Frontend loads at `http://localhost:5173`.

Expected files
- `docker-compose.yml`
- `backend/app/main.py`
- `backend/pyproject.toml` (or `requirements.txt`)
- `backend/Dockerfile`
- `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`
- `.env.example`

CODEx prompt (Task 1)
You are working inside this repository. Implement **Task 1** ONLY.

Create a Docker Compose-based local dev environment for:
- Postgres 16
- Redis
- Backend: Python 3.11 + FastAPI, exposed on port 8000, with `GET /health`
- Frontend: React + TypeScript + Vite, exposed on port 5173

Requirements:
- Add `.env.example` for all required environment variables (DB URL, Redis URL, etc).
- Provide minimal backend app with `/health` returning `{"status":"ok"}`.
- Provide minimal frontend app that renders a simple page like “TWNG Story Scanner Admin”.

Definition of Done:
- `docker compose up --build` works.
- `curl -s http://localhost:8000/health` returns 200 with JSON.
- Frontend loads at http://localhost:5173.

Do not implement any other tasks. After changes, show:
1) commands you ran
2) key files created/edited
3) how to verify locally

CLAUDE prompt (Task 1 Review)
Review the diff as a senior engineer. Check:
- docker-compose correctness, ports, volumes
- safe secret handling (.env.example)
- backend health endpoint
- minimal frontend boot
Provide a prioritized list of fixes and quick improvements.


---

## Task 2 — Postgres schema + Alembic migrations

Goal
- Add DB models and first migration for CandidateStory, TWNGStoryRecord, AuditLog.

Inputs
- Task 1 baseline running.

Outputs
- SQLAlchemy models + Alembic migration.

DoD
- `alembic upgrade head` works on a clean DB.
- Unique constraint on `(source_type, source_id)`.
- Indices appropriate for MVP.

Expected files
- `backend/app/db/models.py`
- `backend/app/db/session.py`
- `backend/alembic/versions/*.py`

CODEx prompt (Task 2)
Implement **Task 2** ONLY: database schema and migrations.

Stack:
- SQLAlchemy 2.x + Alembic
- Postgres 16

Create models + Alembic migration for:
1) CandidateStory
2) TWNGStoryRecord
3) AuditLog

CandidateStory (MVP fields)
- id (uuid pk)
- source_type (text)  # 'reddit'|'web'
- source_id (text)    # reddit post id or url hash
- source_url (text)
- title (text, nullable)
- raw_text (text, nullable)  # allowed for TEMP retention; will be cleaned later
- excerpt (text, nullable)
- created_at_source (timestamptz, nullable)
- ingested_at (timestamptz, default now)
- language (text, nullable)
- prefilter_flags (jsonb, default {})
- story_score (double precision, nullable)
- score_components (jsonb, default {})
- category_pred (text, nullable)
- category_confidence (double precision, nullable)
- entities (jsonb, default {})
- summary_draft (text, nullable)
- tags_pred (text[], nullable)
- status (text, default 'new')  # new|reviewed|approved|rejected
- reviewer_notes (text, nullable)

TWNGStoryRecord (MVP fields)
- id (uuid pk)
- candidate_id (uuid fk nullable)
- source_url (text)
- source_type (text)
- credit_text (text, nullable)
- summary_final (text)
- category (text, nullable)
- tags (text[], nullable)
- language (text, nullable)
- published_at (timestamptz, default now)
- visibility (text, default 'internal')  # internal|public|private
- takedown_status (text, default 'active')  # active|removed

AuditLog
- id (uuid pk)
- actor (text)
- action (text)
- target_type (text)
- target_id (uuid nullable)
- timestamp (timestamptz, default now)
- details (jsonb, default {})

Must-haves:
- Unique constraint on CandidateStory (source_type, source_id)
- Basic indexes on status, story_score, created_at_source

Definition of Done:
- Add Alembic config and create initial migration
- `alembic upgrade head` runs successfully in docker environment

Do not implement API endpoints yet. After changes, show migration file name and verification commands.

CLAUDE prompt (Task 2 Review)
Review models and migration for:
- correct types, constraints, indexes
- uuid handling
- sane defaults
- future-proofing for search (tsvector can be later)
Give a short prioritized fix list.


---

## Task 3 — Backend API (Curation endpoints)

Goal
- Provide admin endpoints to list candidates, read one, approve/reject, and list records.

Inputs
- DB models exist.

Outputs
- FastAPI routes + schemas + tests.

DoD
- Endpoints work and are documented in `/docs`.
- Pytest covers approve/reject.

Expected files
- `backend/app/api/routes/candidates.py`
- `backend/app/api/routes/records.py`
- `backend/app/schemas/*.py`
- `backend/tests/test_candidates.py`

CODEx prompt (Task 3)
Implement **Task 3** ONLY: FastAPI endpoints for curation (no auth yet).

Add routes:
- GET `/candidates` with query params:
  - `status` (default 'new')
  - `min_score` (float optional)
  - `source` (text optional)
  - `lang` (text optional)
  - `q` (search optional; MVP simple ILIKE on title/excerpt/summary_draft)
  - `limit` (default 50, max 200)
  - `offset` (default 0)
- GET `/candidates/{id}`
- POST `/candidates/{id}/approve` (creates TWNGStoryRecord using candidate summary_draft -> summary_final; sets candidate status=approved)
- POST `/candidates/{id}/reject` (sets candidate status=rejected; stores optional reason)
- GET `/records` (list TWNGStoryRecord; basic filters optional)

Requirements:
- Use Pydantic schemas.
- Use SQLAlchemy session dependency.
- Return JSON without internal DB errors leaking.

Testing:
- Add pytest tests that:
  1) create a candidate in DB
  2) approve it -> record created, candidate status updated
  3) reject it -> status updated

Definition of Done:
- `pytest` passes in backend container.
- `GET /docs` shows endpoints.

Do not implement auth in this task.

CLAUDE prompt (Task 3 Review)
Review API design for:
- correctness and idempotency
- error handling (404, double-approve)
- pagination and filtering
- test quality
Suggest improvements and edge cases.


---

## Task 4 — Admin Auth (JWT) for API + Frontend login

Goal
- Lock curation endpoints behind admin login.

Inputs
- API endpoints exist.

Outputs
- `/auth/login` returns JWT; protected routes require it; frontend login page.

DoD
- Protected endpoints reject missing/invalid token.
- Frontend stores token and uses it on API calls.

Expected files
- `backend/app/api/routes/auth.py`
- `backend/app/core/security.py`
- `frontend/src/pages/Login.tsx`

CODEx prompt (Task 4)
Implement **Task 4** ONLY: minimal admin auth with JWT.

Backend:
- Add POST `/auth/login` accepting username+password.
- For MVP, store a single admin user in DB seeded from env vars:
  - `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` (or `ADMIN_PASSWORD` for MVP ONLY if you hash on startup; prefer hash)
- Issue JWT with short expiry (e.g., 8 hours) using `JWT_SECRET` env.
- Protect all `/candidates*` and `/records*` endpoints with dependency requiring valid JWT.

Frontend:
- Add `/login` page and route guard.
- Store JWT in memory + localStorage and attach as `Authorization: Bearer <token>`.

Definition of Done:
- Unauthorized requests to protected endpoints return 401.
- Logging in returns token and then inbox endpoints work.

Do not add external auth providers.

CLAUDE prompt (Task 4 Review)
Review auth for:
- password storage and hashing
- token expiry and validation
- route protection coverage
- frontend token handling security basics
Provide prioritized fixes.


---

## Task 5 — Reddit collector (ingest) into CandidateStory

Goal
- Ingest Reddit posts via API with dedupe.

Inputs
- Reddit API credentials in env.
- Config: subreddits + queries.

Outputs
- CLI command or script to ingest.
- Data saved to Postgres.

DoD
- Saves required fields, dedupes by (source_type, source_id).
- Logs and basic backoff.

Expected files
- `backend/app/collectors/reddit_collector.py`
- `backend/app/cli.py` or `scripts/ingest_reddit.py`

CODEx prompt (Task 5)
Implement **Task 5** ONLY: Reddit ingest using PRAW.

Requirements:
- Read env vars:
  - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- Config file `backend/app/core/collector_config.py` with:
  - list of subreddits (e.g., guitars, Guitar, VintageGuitars)
  - list of queries (e.g., "guitar story", "my first guitar", "stolen guitar", plus Hebrew terms)
- Implement `ingest_reddit(limit_per_query=20)` that:
  - searches each subreddit for each query
  - creates CandidateStory rows with:
    - source_type='reddit'
    - source_id=post.id
    - source_url=permalink
    - title=post.title
    - raw_text=post.selftext (nullable)
    - excerpt: first 300–500 chars of selftext or title fallback
    - created_at_source from created_utc
    - language guessed naive (he/en/other) ok for MVP
- Dedupe: skip insert if unique constraint hit.
- Add simple backoff on network errors (sleep and continue).
- Provide a CLI command: `python -m app.cli ingest-reddit` or similar.

Definition of Done:
- Running the ingest command inserts rows in CandidateStory.
- Running it again does not create duplicates.

Do not implement scoring or Celery in this task.

CLAUDE prompt (Task 5 Review)
Review collector for:
- correct PRAW usage (subreddit loop, rate limits)
- dedupe reliability
- minimal data principles (excerpt vs full text)
- error handling and logging
Provide fix suggestions.


---

## Task 6 — Pre-filter + StoryScore v0 (heuristics) + tests

Goal
- Compute story_score and flags using cheap rules.

Inputs
- CandidateStory rows.

Outputs
- Scoring module + unit tests + CLI command to score new items.

DoD
- Tests cover at least 10 fixtures.
- Updates DB fields (score, components, flags).

Expected files
- `backend/app/scoring/prefilter.py`
- `backend/app/scoring/story_score.py`
- `backend/tests/test_scoring.py`

CODEx prompt (Task 6)
Implement **Task 6** ONLY: prefilter rules and StoryScore v0.

Create:
- `prefilter(text) -> flags dict`
- `story_score(text) -> (score float 0..1, components dict, flags dict)`

Rules (MVP):
- Minimum length (words): <80 => heavy penalty
- Sales/spam indicators: ["for sale","fs","ft","price","$","₪","shipping","dm me"] => strong penalty
- Ownership cues: ["my guitar","my first","i bought","i sold","knew it","שלי","קניתי","מכרתי","הגיטרה שלי"] => boost
- Timeline cues: ["years ago","when i was","in 19","in 20","לפני","בשנת"] => boost
- Guitar relevance cues: ["guitar","fender","gibson","tele","strat","les paul","martin","גיטרה","פנדר","גיבסון"] => boost

Store:
- CandidateStory.story_score
- CandidateStory.score_components (breakdown)
- CandidateStory.prefilter_flags

Add CLI: `score-candidates` that scores rows with null score.

Testing:
- Provide fixtures for “for sale ad” -> low score
- “inheritance story” -> high score
- “technical question” -> medium/low
- Hebrew story example -> boosted

Definition of Done:
- `pytest` passes
- CLI updates DB rows

Do not implement GPT/enrichment here.

CLAUDE prompt (Task 6 Review)
Review scoring rules for:
- precision bias (avoid sales spam)
- multilingual robustness
- test coverage adequacy
Suggest improved heuristics and edge cases.


---

## Task 7 — Celery + Redis worker + scheduled jobs

Goal
- Async tasks for ingest and processing.

Inputs
- Redis running.
- Ingest and scoring implemented.

Outputs
- Celery worker + tasks `ingest_reddit` and `process_candidates`.

DoD
- Worker runs in docker.
- Tasks can be triggered manually.

Expected files
- `backend/app/worker/celery_app.py`
- `backend/app/worker/tasks.py`
- docker-compose updates

CODEx prompt (Task 7)
Implement **Task 7** ONLY: Celery worker and tasks.

Requirements:
- Configure Celery with Redis broker and result backend.
- Add tasks:
  1) `ingest_reddit_task()` calls the Reddit collector ingest.
  2) `process_candidates_task()` runs scoring on unscored candidates.
- Add retry/backoff for network errors in ingest task.
- Update docker-compose to run a `worker` service.

Add a small CLI or endpoint to trigger tasks manually (choose ONE):
- CLI: `enqueue-ingest` and `enqueue-process`
OR
- API endpoints under `/admin/tasks/*` (protected if auth exists)

Definition of Done:
- `docker compose up` starts worker.
- Triggering ingest task inserts candidates.
- Triggering process task scores them.

Do not implement enrichment (GPT) here.

CLAUDE prompt (Task 7 Review)
Review task architecture for:
- idempotency
- retries/backoff
- separation of concerns
- docker-compose correctness
Suggest improvements.


---

## Task 8 — Enrichment after threshold (provider abstraction + optional OpenAI)

Goal
- Summarize + categorize + tags only when `story_score >= threshold`.

Inputs
- Scored candidates.

Outputs
- `summary_draft`, `category_pred`, `tags_pred`, `entities` populated.

DoD
- Provider abstraction implemented.
- Works with and without OpenAI key.

Expected files
- `backend/app/enrichment/provider.py`
- `backend/app/enrichment/openai_provider.py`
- `backend/app/enrichment/local_provider.py`

CODEx prompt (Task 8)
Implement **Task 8** ONLY: enrichment after score threshold.

Requirements:
- Add config `ENRICHMENT_SCORE_THRESHOLD` default 0.65.
- Create interface `EnrichmentProvider` with methods:
  - `summarize(text, lang) -> str`
  - `classify_category(text, lang) -> (category, confidence)`
  - `extract_tags(text, lang) -> list[str]`
  - `extract_entities(text, lang) -> dict` (brand/model/year if possible)
- Implement:
  - `LocalProvider` fallback (simple summary = first 2–3 sentences; tags = naive keyword extraction)
  - `OpenAIProvider` OPTIONAL if `OPENAI_API_KEY` exists:
    - single call is preferred; keep temperature low
    - return structured JSON (category, tags, summary, entities) and validate
    - guardrails: do not include private addresses/phone/email in summary
- Add process function `enrich_candidates()` that processes candidates above threshold with missing enrichment fields.

Definition of Done:
- Works without OPENAI key (LocalProvider).
- With OPENAI key, uses OpenAI provider.
- Unit test(s) for LocalProvider output shape.

Do not change UI in this task.

CLAUDE prompt (Task 8 Review)
Review enrichment for:
- prompt safety and PII avoidance
- JSON parsing robustness
- cost control (call minimization)
- fallback behavior
Provide fix list.


---

## Task 9 — React Admin Inbox UI (Curation)

Goal
- Inbox table with filters, preview, approve/reject.

Inputs
- Protected API endpoints exist (auth from Task 4).

Outputs
- React page `/inbox` with table + side panel preview + actions.

DoD
- Uses TanStack Query + Table.
- Approve/reject works with optimistic update.
- Loading/error states present.

Expected files
- `frontend/src/pages/Inbox.tsx`
- `frontend/src/components/CandidateTable.tsx`
- `frontend/src/components/CandidatePreview.tsx`
- `frontend/src/lib/queries.ts`

CODEx prompt (Task 9)
Implement **Task 9** ONLY: the React admin Inbox UI.

Stack:
- React + TypeScript + Vite
- Tailwind + shadcn/ui
- TanStack Query + TanStack Table

Build:
- Route `/inbox` (guarded; redirect to `/login` if no token)
- Table columns: score, source, date, category_pred, language, title, status
- Filters: status (dropdown), min score (number), source (dropdown), language (dropdown), search (input)
- Row click opens side panel showing:
  - excerpt
  - summary_draft
  - metadata (source_url, created_at_source)
- Buttons:
  - Approve (calls POST /candidates/{id}/approve)
  - Reject (calls POST /candidates/{id}/reject with optional reason)
- Use optimistic updates so the row disappears or status updates.

Definition of Done:
- Runs locally and talks to backend.
- Approve/reject updates UI without full page reload.
- Handles loading and error states.

Do not add new backend endpoints in this task.

CLAUDE prompt (Task 9 Review)
Review frontend for:
- query key design and caching
- auth token handling
- UI edge cases (empty states, errors)
- minimal but clean component structure
Give fixes and improvements.


---

## Task 10 — End-to-end happy path + seed + docs

Goal
- One-command dev run + seed admin + README.

Inputs
- Tasks 1–9 complete.

Outputs
- `README.md`, seed script, and a simple “happy path” checklist.

DoD
- A developer can run: up -> ingest -> process -> approve -> view records.

Expected files
- `README.md`
- `backend/app/db/seed.py`
- `Makefile` or `scripts/dev.sh`

CODEx prompt (Task 10)
Implement **Task 10** ONLY: end-to-end developer experience improvements.

Requirements:
- Add seed script to create admin user if missing (based on env vars).
- Add a top-level command helper:
  - `make dev` OR `scripts/dev.sh` that starts docker compose.
- Add `README.md` with:
  - prerequisites
  - how to run the stack
  - how to ingest Reddit candidates
  - how to process/score
  - how to login and approve a story
  - where to view approved records (API endpoint or UI)

Definition of Done:
- Following README on a clean machine yields a working happy path.
- No secrets committed; `.env.example` updated.

Do not add new features beyond docs/seed/dev scripts.

CLAUDE prompt (Task 10 Review)
Review docs and seed for:
- reproducibility
- security and secret handling
- correctness of commands
- clarity and brevity
Provide improvements.
