# FlowPilot

## Business problem

Routine business workflows involve repetitive work across disconnected tools. FlowPilot aims to provide one place to coordinate that work. Day 1 establishes the connected web and API foundation; workflow automation is not implemented yet.

## Day 1 scope

Next.js with TypeScript and App Router, FastAPI with `GET /health` returning `{"status":"ok"}`, a live backend status page, locked dependencies, and Docker Compose.

No database, OpenAI integration, authentication, or agent tools are added. The pre-existing `/api/agent/run` echo endpoint is preserved and is not used by the frontend.

## Architecture

```text
Browser -> Next.js :3000 -> FastAPI :8000 /health
```

The page's server component fetches the API on every request with caching disabled and a five-second timeout. Only a successful response with `status: ok` shows a healthy connection. Failures show an unavailable state, with a button to retry. Server-side fetching requires no CORS configuration or public backend URL. Compose uses `http://api:8000` internally.

Each app owns its dependency lockfile. Docker uses a Next.js standalone production build and locked Python dependencies. Both containers run as non-root users. Compose waits for API health and checks the connection through the web page.

## Repository structure

```text
apps/
  api/
    app/main.py          # FastAPI routes
    app/core/            # Existing placeholders
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

Prerequisites: Python 3.14+, uv, Node.js 24+, and pnpm 12.4.2 (`npm install --global pnpm@12.4.2`). Run these commands in separate terminals, starting from the repository root.

Backend:

```powershell
cd apps/api
uv sync --frozen
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
# Optional: copy .env.example to .env to change host ports.
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

Open http://localhost:3000 and http://localhost:8000/health. Stop local servers first to free ports 3000 and 8000, or set alternate Compose host ports in `.env`. Container ports stay unchanged.

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
| `UVICORN_HOST` | Shell environment | `127.0.0.1` | Optional local API bind address. |
| `UVICORN_PORT` | Shell environment | `8000` | Optional local API port. |

No secrets or external accounts are needed. The API requires no `.env` file. Its `.env.example` documents optional shell settings; Uvicorn does not load those settings from that file automatically. Command-line host and port options override shell settings. Restart Next.js after changing its environment. Real environment files, dependencies, and build output are excluded from Git and Docker.
