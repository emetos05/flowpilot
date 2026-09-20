# FlowPilot

## Business problem

Routine business workflows involve repetitive work across disconnected tools. FlowPilot aims to provide one place to coordinate that work. Day 1 established the connected web and API foundation. Day 2 adds structured recommendations with durable run history; it does not execute business actions.

## Day 1 scope

Next.js with TypeScript and App Router, FastAPI with `GET /health` returning `{"status":"ok"}`, a live backend status page, locked dependencies, and Docker Compose.

The pre-existing `/api/agent/run` echo endpoint is preserved for compatibility. It is separate from the Day 2 endpoint and does not call a model or persist records.

## Day 2 scope

`POST /agent/run` validates a request, commits a PostgreSQL `agent_runs` record, calls OpenAI through a service interface, validates structured output, and commits the result before returning success. Failed model calls are recorded with a safe error code. No tools, agent loop, authentication, or agent UI are implemented; those remain later roadmap work.

## Architecture

```text
Browser -> Next.js :3000 -> FastAPI :8000 /health
API caller -> FastAPI /agent/run -> OpenAI Responses API
                               -> PostgreSQL agent_runs
```

The page's server component fetches the API on every request with caching disabled and a five-second timeout. Only a successful response with `status: ok` shows a healthy connection. Failures show an unavailable state, with a button to retry. Server-side fetching requires no CORS configuration or public backend URL. Compose uses `http://api:8000` internally.

Each app owns its dependency lockfile. Docker uses a Next.js standalone production build and locked Python dependencies. Both containers run as non-root users. Compose waits for API health and checks the connection through the web page.

The model service uses the SDK's Pydantic parsing helper and strict structured outputs, following the [official OpenAI guide](https://developers.openai.com/api/docs/guides/structured-outputs). Model choice, timeout, token limit, database URL, and key are environment configuration. Provider retries are disabled to keep one request bounded. The API uses synchronous endpoints, which FastAPI runs in its worker thread pool, and short PostgreSQL transactions so no transaction stays open during a model call.

Run statuses are `running`, `succeeded`, and `failed`. Records contain the submitted message, configured model, structured output or safe error code, and timestamps. Only schema-valid submissions to `/agent/run` create records; invalid requests return 422 before execution. If the initial database write fails, the model is not called. If the final write fails, the API returns 503 and the original `running` row remains. A process crash can also leave a `running` row; automatic recovery and idempotency are not part of Day 2. Do not automatically retry submissions: each creates a new run.

## Repository structure

```text
apps/
  api/
    app/main.py          # FastAPI routes
    app/core/config.py   # Environment settings
    app/schemas.py       # Typed request, output, and responses
    app/services/        # Model interface and run orchestration
    app/db.py            # PostgreSQL persistence and schema initialization
    app/schema.sql       # Day 2 agent_runs table only
    tests/               # Unit, PostgreSQL, and opt-in live tests
    pyproject.toml
    uv.lock
    Dockerfile
    .dockerignore
    .env.example
  web/
    app/                 # App Router page, layout, styles
    public/
    package.json
    pnpm-lock.yaml
    next.config.ts
    Dockerfile
    .dockerignore
    .env.example
.env.example             # Compose host ports
docker-compose.yml
```

## Local setup

Prerequisites: Python 3.14+, uv, Node.js 24+, pnpm 12.4.2 (`npm install --global pnpm@12.4.2`), and Docker Desktop with Linux containers (or an existing PostgreSQL instance). An OpenAI API key with model access and billing is needed for successful agent requests. Run these commands starting from the repository root.

Database and configuration:

```powershell
docker compose up -d db --wait
# Skip copying if you already have this file, to preserve your credentials.
Copy-Item apps/api/.env.example apps/api/.env
```

Edit `apps/api/.env` locally and set `OPENAI_API_KEY`. Never put the key in a frontend environment file or commit it. The example database URL matches the local Compose database. If you change the database host port or password, update that URL too.

Backend:

```powershell
cd apps/api
uv sync --frozen
uv run python -m app.db
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd apps/web
Copy-Item .env.example .env.local
pnpm install --frozen-lockfile
pnpm dev --hostname 127.0.0.1
```

Open http://localhost:3000 and expect **Backend is healthy**. API docs: http://127.0.0.1:8000/docs. Stop each server with Ctrl+C.

Verify in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$page = Invoke-WebRequest http://127.0.0.1:3000 -UseBasicParsing
if ($page.StatusCode -ne 200 -or $page.Content -notmatch 'Backend is healthy') {
    throw 'Frontend could not verify the backend'
}
```

Stop the backend and refresh to verify **Backend is unavailable**. Restart it and select **Check again** to verify recovery.

Frontend checks, from `apps/web`:

```powershell
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

## Docker setup

Start Docker Desktop with Linux containers. From the repository root:

```powershell
# Copy apps/api/.env.example to apps/api/.env and set OPENAI_API_KEY first.
# Optional: copy the root .env.example to .env to change ports or the DB password.
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

Open http://localhost:3000 and http://localhost:8000/health. Stop local servers first to free ports 3000 and 8000, or set alternate Compose host ports in `.env`. Container ports stay unchanged.

Compose reads model settings from `apps/api/.env` and overrides `DATABASE_URL` with the internal database address. The API initializes the Day 2 table on startup using repeatable `CREATE TABLE IF NOT EXISTS`; full migration tooling remains Day 5 work. PostgreSQL data lives in the named `postgres_data` volume and survives container recreation and `docker compose down`. Do not use `down -v` unless you intend to delete it. Changing `POSTGRES_PASSWORD` after initial database creation does not change the existing database role's password.

Without an OpenAI key, the health page still works. Agent requests return a sanitized 503 and persist a failed run. Services bind to localhost; authentication is scheduled for Day 7, so this setup is for local development.

```powershell
docker compose logs api web
docker compose down
```

## Environment variables

| Variable | Location | Default | Purpose |
| --- | --- | --- | --- |
| `API_BASE_URL` | `apps/web/.env.local` | `http://127.0.0.1:8000` | Server-side API URL; Compose sets `http://api:8000`. |
| `WEB_PORT` | Root `.env` | `3000` | Compose web host port. |
| `API_PORT` | Root `.env` | `8000` | Compose API host port. |
| `POSTGRES_PORT` | Root `.env` | `5432` | PostgreSQL host port. |
| `POSTGRES_PASSWORD` | Root `.env` | `flowpilot-local` | Local-only database password. Use a URL-safe value for Compose. |
| `DATABASE_URL` | `apps/api/.env` | None | PostgreSQL connection URL; required for agent requests. |
| `OPENAI_API_KEY` | `apps/api/.env` | None | Backend-only OpenAI credential. |
| `OPENAI_MODEL` | `apps/api/.env` | `gpt-4o-mini` | Model supporting the Responses API and structured output. |
| `OPENAI_TIMEOUT_SECONDS` | `apps/api/.env` | `30` | Model request timeout, greater than 0 and at most 120. |
| `OPENAI_MAX_OUTPUT_TOKENS` | `apps/api/.env` | `1000` | Response token cap, between 100 and 4096. |
| `UVICORN_HOST` | Shell environment | `127.0.0.1` | Optional local API bind address. |
| `UVICORN_PORT` | Shell environment | `8000` | Optional local API port. |

API settings load from `apps/api/.env` regardless of the working directory; shell variables take precedence. Restart the API after changing settings. Uvicorn's own host/port settings must be passed in the shell or as command-line options. Restart Next.js after changing its environment. Real environment files, dependencies, and build output are excluded from Git and Docker. Model requests use `store=False`; local run records still contain submitted messages and results, so use synthetic data for local demos.

## Agent API example

```powershell
$body = @{ message = 'A customer asks about a refund, but we have no order details. Suggest next steps.' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/agent/run -Method Post -ContentType 'application/json' -Body $body
```

The 200 response contains `run_id`, `status: succeeded`, `created_at`, and `output`:

```json
{
  "summary": "A customer is asking about a refund without order details.",
  "suggested_next_steps": ["Ask for the order number and have a human review the policy."],
  "needs_human_review": true
}
```

The example output is illustrative; model wording varies. Messages must be nonblank UTF-8 text without null characters and at most 10,000 characters. Extra request fields are rejected. Errors return `{"error":{"code":"...","message":"...","run_id":"..."}}`; the ID is null if execution did not create a record. HTTP codes: 422 invalid request or refusal, 502 invalid output/provider error, 503 missing model configuration or storage unavailable, 504 model timeout, 500 unexpected failure. Raw model refusals, exception details, and credentials are not returned.

Inspect stored run metadata:

```powershell
docker compose exec db psql -U flowpilot -d flowpilot -c "SELECT id, status, error_code, created_at, completed_at FROM agent_runs ORDER BY created_at DESC LIMIT 10;"
```

## Backend verification

From `apps/api`:

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
uv run pytest -q
# Include real PostgreSQL tests (use a development/test database):
$env:TEST_DATABASE_URL = 'postgresql://flowpilot:flowpilot-local@127.0.0.1:5432/flowpilot'
uv run pytest -q
# Explicitly opt in to one billable OpenAI request, using apps/api/.env:
$env:RUN_LIVE_OPENAI = '1'
uv run pytest -q -s -m live
Remove-Item Env:RUN_LIVE_OPENAI
```

Default tests replace the model provider and do not spend API credits. The SDK contract test uses the real parser with a mocked HTTP transport. PostgreSQL tests use independent connections and delete only their own uniquely identified rows. The live test keeps its run as acceptance evidence. Integration/live checks are explicitly skipped when not enabled; skipped checks do not establish live acceptance. Current acceptance evidence and blockers are in [CURRENT_STATUS.md](docs/CURRENT_STATUS.md).
