# Current status

Updated: September 20, 2026.

- Approved day: **Day 2 - Structured agent endpoint**.
- Status: **Complete**. All Day 2 acceptance criteria pass, including live OpenAI output and durable PostgreSQL persistence.
- Completed days: **Days 1 and 2**. Its previously stale roadmap checkboxes have been reconciled with the completed implementation and verification from September 16, plus current Docker/health regression checks.
- Gate: **Day 2 passed**. Day 3 may begin when approved; it has not started.

## Week 1 progress

- [x] Repository initialized
- [x] FastAPI service
- [x] Next.js frontend
- [x] Frontend to API health communication
- [x] OpenAI service interface and structured-output implementation
- [x] PostgreSQL agent-run persistence
- [x] Live OpenAI acceptance check (passed September 20, 2026)
- [ ] Tool calling (Day 3; not started)

## Day 2 acceptance criteria

- [x] A valid request produces schema-validated structured output from live OpenAI. Live run `74c2d23b-e855-4b8e-9ae9-6351551d9cc1` returned HTTP 200 and its successful output was verified through a separate PostgreSQL connection.
- [x] Each valid agent submission creates a durable agent-run record before the model call; successful outputs and provider failures are committed. Malformed requests are rejected before creating a run. A database outage rejects execution without calling the model.
- [x] Configuration and API secrets come from environment variables or the ignored backend `.env`; settings represent credentials as secret values.
- [x] Error responses do not expose secrets or raw internal exceptions. Validation, provider failure, timeout, missing configuration, invalid output, refusal, and storage errors are tested.

## Files changed

- `apps/api/app/main.py`: `/agent/run`, dependency injection, typed responses, sanitized errors; preserved `/health` and the existing `/api/agent/run` echo route.
- `apps/api/app/core/config.py`: environment-backed model and database settings.
- `apps/api/app/schemas.py`, `app/errors.py`: input/output contracts and public error codes.
- `apps/api/app/services/model.py`: model interface and OpenAI Responses/Pydantic adapter.
- `apps/api/app/services/agent.py`: commit-before-call orchestration and final result persistence.
- `apps/api/app/db.py`, `app/schema.sql`: parameterized PostgreSQL repository and repeatable Day 2 table initialization.
- `apps/api/tests/`: API, provider SDK, configuration, PostgreSQL integration, and explicitly enabled live acceptance tests.
- `apps/api/pyproject.toml`, `uv.lock`: OpenAI, psycopg, settings, pytest, and Ruff dependencies/configuration.
- `apps/api/Dockerfile`, `.dockerignore`, root `docker-compose.yml`: PostgreSQL service with named volume, backend environment configuration, and schema initialization.
- Root `.env.example`, `apps/api/.env.example`, `.gitignore`: configuration examples and generated-cache exclusions.
- `README.md`, `docs/ROADMAP.md`, `docs/CURRENT_STATUS.md`: setup, endpoint contract, verification, decisions, and accurate day/gate status.
- Local ignored `apps/api/.env`: now configured locally by the user; the key was checked without displaying it and remains outside source control.

## Commands and verification

Commands run from `apps/api` unless otherwise noted. Windows verification used `.venv/Scripts/python.exe -m ...` / `.venv/Scripts/ruff.exe` directly where sandbox cache permissions prevented `uv run`; the documented equivalents below use uv.

- `uv add openai 'psycopg[binary]' pydantic-settings` and `uv add --dev pytest ruff`: installed dependencies and updated the lockfile.
- `uv run python -m app.db`: initialized the real PostgreSQL table; repeated initialization also passed.
- `uv run ruff check app tests` and `uv run ruff format --check app tests`: passed.
- `uv run pytest -q -p no:cacheprovider` with `TEST_DATABASE_URL` configured: **36 passed, 1 skipped**. Only the explicitly gated live OpenAI test was skipped. One upstream Starlette/AnyIO deprecation warning remains; no test failures.
- `uv run uvicorn app.main:app --host 127.0.0.1 --port 8002`: ran the local API and verified `/health`, request validation, and sanitized missing-key errors over HTTP.
- `docker compose up -d db --wait` and `docker compose up --build -d --wait` (root): built and ran PostgreSQL, FastAPI, and Next.js; all health checks passed.
- Next.js production build and TypeScript compilation passed inside Docker. `pnpm lint` and `pnpm exec tsc --noEmit` also passed from `apps/web`.
- Direct API `/health` and frontend HTTP checks passed; rendered page contains `Backend is healthy` retrieved from FastAPI.
- With no OpenAI key, a real HTTP `/agent/run` request returned 503 `model_not_configured` and committed failed run `9603c1a9-5668-4e48-b4f0-3a974dad3a47`.
- `docker compose stop db`: a controlled database outage returned sanitized 503 `storage_unavailable` with no run ID; no model was called.
- `docker compose up -d db --wait`: restored PostgreSQL; a new connection confirmed the committed run above survived restart.
- PostgreSQL integration tests separately confirmed successful structured outputs and failed provider calls are visible through independent database connections.
- Final Docker endpoint and frontend checks passed after rebuilding the final code. Docker services remain running on ports 3000 (web), 8000 (API), and 5432 (PostgreSQL). The temporary local API on port 8002 was stopped after verification.

## Decisions and tradeoffs

- One model call per submission through a replaceable interface. No tools, loops, approvals, authentication, or agent UI were added.
- Typed structured output includes a summary, suggested next steps, and a human-review flag. Recommendations do not execute actions.
- Use direct psycopg and one small repeatable SQL schema for the Day 2 table. Full migration tooling and business tables remain Day 5 work.
- Commit a `running` row before the provider call, then commit `succeeded` or `failed`. Do not hold a transaction open while waiting on OpenAI.
- Refuse to report success if the final database write fails. A crash or final-write outage can leave a durable `running` row; crash recovery/idempotency are later work.
- No fake production model mode. Automated tests substitute the provider; the running endpoint requires a real key for success.
- Preserve the earlier echo endpoint unchanged; it is not the new `/agent/run` endpoint and does not persist runs.

## Manual configuration and blockers

None remaining for Day 2. The user configured the key and resolved billing. Credentials remain in the ignored backend `.env` and were not printed or committed. The Docker API was recreated to load current configuration.

## Day 2 completion verification - September 20, 2026

- Started Docker Desktop and restored the Compose services after the first test encountered a stopped database; that attempt did not reach OpenAI.
- Ran `docker desktop start` and `docker compose up -d --wait --force-recreate api web`; PostgreSQL, API, and web health checks passed.
- With `RUN_LIVE_OPENAI=1`, ran `.venv/Scripts/python.exe -m pytest -q -s -m live -p no:cacheprovider --tb=short` outside the restricted network sandbox: **1 passed, 36 deselected**. The previously passing 36 non-live tests were not rerun because application code was unchanged.
- Real OpenAI request through `POST /agent/run` produced a schema-validated response and committed run `74c2d23b-e855-4b8e-9ae9-6351551d9cc1`. A new PostgreSQL connection verified status `succeeded` and exact stored output equality.
- Verified the running API `/health` and the frontend's backend-health display over HTTP.
- One upstream Starlette/AnyIO deprecation warning remains; it does not fail the test.
- Files changed in this completion step: `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`. Application code and architecture were unchanged. Day 3 was not started.

## Prior live verification failure - September 19, 2026 (resolved)

- Ran `.venv/Scripts/python.exe -m pytest -q -s -m live -p no:cacheprovider --tb=short` with `RUN_LIVE_OPENAI=1`, including a retry outside the network sandbox. The live test failed with sanitized API 502 `model_unavailable`.
- Used the OpenAI Developers troubleshooting skill to diagnose the provider safely: HTTP 429 with quota/credit-exhaustion indicators, not transient rate-limit indicators. No plaintext credential or raw provider error was printed.
- Verified failed run `57fb6715-2c77-4d96-affe-0de20edfb28f` is durably stored as `failed` / `model_unavailable`.
- Application code was unchanged. Updated this status file and the roadmap to replace the missing-key blocker with the observed provider quota/credit blocker. Day 3 remains unstarted.
