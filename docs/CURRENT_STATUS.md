# Current status

Updated: September 23, 2026.

- Approved day: **Day 4 - Bounded agent loop**.
- Status: **Complete**. All Day 4 acceptance criteria pass.
- Completed days: **Days 1, 2, 3, and 4**.
- Gate: **Day 4 passed**. Day 5 awaits approval and has not started.

## Day 4 acceptance criteria

- [x] Tool selection, execution, observation, and next-decision stages repeat with explicit request-local state.
- [x] State transitions are visible in running Docker API logs and testable through immutable transition events.
- [x] The loop ends with validated output or a sanitized, persisted failure.
- [x] A configured decision cap prevents unlimited calls. Deadline checks and reduced provider timeouts stop further work and reject late results.

## Day 4 files changed

- `apps/api/app/services/model.py`: iterative model/tool conversation, deadline and decision limits, invalid-call checks, safe tool failures, and chained lookup instructions.
- `apps/api/app/services/state.py` (new): execution state, allowed transitions, immutable observation events, and safe console logging.
- `apps/api/app/core/config.py`, `apps/api/.env.example`: validated `AGENT_MAX_STEPS` and `AGENT_TIMEOUT_SECONDS` settings.
- `apps/api/app/errors.py`: public step-limit, agent-timeout, invalid-tool, and tool-failure errors.
- `apps/api/app/tools/registry.py`: tool descriptions permit IDs obtained from earlier observations.
- `apps/api/tests/test_agent_loop.py` (new): chained history, exact step exhaustion, deadline behavior, invalid tools, exceptions, state transitions, and concurrent execution isolation.
- `apps/api/tests/test_tool_calling.py`: update Day 3 expectations for iterative decisions; retain SDK protocol and malformed-response coverage.
- `apps/api/tests/test_agent_api.py`, `apps/api/tests/test_postgres.py`: verify all new failures return safe HTTP errors and persist failed records.
- `apps/api/tests/test_live_tools.py`: add real order-to-customer/policy chained acceptance check.
- `README.md`, `docs/ROADMAP.md`, `docs/CURRENT_STATUS.md`: settings, operational behavior, limitations, and completion evidence.

## Day 4 commands and verification

Backend commands ran from `apps/api` using the existing virtual environment. No dependencies were added.

- `.venv/Scripts/ruff.exe check app tests --fix` and `.venv/Scripts/ruff.exe format app tests`: formatting applied. Final `ruff check` and `ruff format --check` passed (20 files).
- `docker compose up -d db --wait` (root): PostgreSQL started and became healthy. Docker access required execution outside the restricted sandbox.
- With `TEST_DATABASE_URL` configured, `.venv/Scripts/python.exe -m pytest -q -m 'not live' -p no:cacheprovider --tb=short`: **98 passed, 5 deselected**. Includes independent-connection PostgreSQL success and failure checks.
- With `RUN_LIVE_OPENAI=1`, `.venv/Scripts/python.exe -m pytest -q -s -m live -p no:cacheprovider --tb=short`: **5 passed, 98 deselected**. Existing structured-output and three single-tool checks pass; the chained case uses four decisions and three correct tools.
- `docker compose up --build -d --wait api web` (root): API rebuilt; unchanged frontend production build reused its cache. All three services are healthy.
- Python/httpx HTTP smoke check against the running Docker services: `/health` returned `{"status":"ok"}`, the web page displayed `Backend is healthy`, and a chained `POST /agent/run` returned HTTP 200 with customer, order, and policy facts. A separate PostgreSQL connection verified exact persisted output and succeeded status.
- `docker compose logs api --tail 40` and `docker compose ps`: confirmed all execution stages followed by success at decision four, and healthy API/web/database containers.
- `git diff --check`: passed.

One upstream Starlette/AnyIO deprecation warning remains; no application failures remain.

## Day 4 live evidence

| Check | Successful persisted run ID |
| --- | --- |
| Existing structured output | `08d99ce5-c631-4959-9196-132d2462b578` |
| Customer lookup | `e3a769d4-0992-4ecf-9ddb-25f14f6ef723` |
| Order lookup | `5717f36c-667f-4455-b218-715a74066904` |
| Refund-policy lookup | `b5d9db95-7bc8-44bd-bb6f-1dcfbea0c424` |
| Chained order/customer/policy test | `a317782c-72e8-4833-9036-fc8dce7ada88` |
| Running Docker HTTP chained request | `da31f9b0-deb0-4c55-8bbf-10279c2e094d` |

The Docker request logged execution ID `d57407ed-1071-4264-8b2b-b205856b1e49` with three execute/observe cycles and a successful fourth decision. Execution IDs group in-memory loop events; database run IDs remain a separate identifier.

## Day 4 decisions and limitations

- Preserve the existing synchronous Responses API service, structured response contract, synthetic read-only tools, and durable PostgreSQL run lifecycle. Model-selected tools remain selected from descriptions and strict schemas, with no intent keyword branches.
- Default maximum is six model decisions, including the final answer; at most five tools execute. A tool selected on the last decision fails before dispatch. Limits are configuration-validated (1-20 decisions).
- The default 90-second deadline applies to orchestration, not database commits. Check monotonic time around provider/tool execution and cap each request timeout to the remaining budget. This is a cooperative deadline, not forced cancellation of synchronous code; transport operations can exceed a wall-clock budget before control returns. Late results are rejected. Current tools are immediate in-memory lookups; future blocking tools need cancellable execution.
- Invalid tool names/arguments now terminate the loop safely; missing records remain valid observations. Reused call IDs, parallel calls, refusals, malformed model output, and exceptions cannot cause indefinite execution.
- Request-local state avoids cross-request contamination. Logs contain only execution ID, phase, step, and safe error code; prompts, arguments, results, and credentials are excluded. Persistent tool traces and business tables remain Day 5 work.
- State `succeeded` means the model produced validated output. The existing runner still requires a successful database commit before reporting HTTP success.

## Manual configuration and blockers

None for Day 4. Existing credentials and billing worked. Optional settings in `apps/api/.env` are `AGENT_MAX_STEPS=6` and `AGENT_TIMEOUT_SECONDS=90`; defaults apply without edits. Restart the API after configuration changes. Docker services remain running at http://localhost:3000 and http://localhost:8000, with PostgreSQL on localhost:5432. Day 5 has not started.

---

## Historical Day 3 completion report (September 21, 2026)

The sections below record the prior milestone; Day 4 behavior and current verification above supersede Day 3's single-lookup limit.

## Day 3 acceptance criteria

- [x] `get_customer`, `get_order`, and `get_refund_policy` have strict typed inputs and typed found/not-found outputs.
- [x] The live model selects the correct tool and arguments for three representative requests without a forced tool name.
- [x] Tests cover successful lookups, invalid input, missing records, registry dispatch, and the provider function-calling protocol.

## Files changed

- `apps/api/app/tools/business.py`: immutable typed synthetic customer, order, and policy fixtures and three lookup methods.
- `apps/api/app/tools/registry.py`: strict tool definitions, validated arguments, fixed-name dispatch, and safe error results.
- `apps/api/app/services/model.py`: optional model-selected lookup, correlated tool result, and final structured response.
- `apps/api/tests/test_business_tools.py`: lookup, input validation, missing-record, schema, and registry tests.
- `apps/api/tests/test_tool_calling.py`: real SDK parser with mocked HTTP responses; tool execution, final response persistence, and failure cases.
- `apps/api/tests/test_live_tools.py`: three opt-in live tool-selection checks with independent PostgreSQL verification.
- `apps/api/tests/test_model.py`: existing provider contract updated to include available tools.
- `README.md`, `docs/ROADMAP.md`, `docs/CURRENT_STATUS.md`: tool contracts, usage, scope, and completion evidence.

## Commands and verification

Backend commands ran from `apps/api` using the existing virtual environment; Docker commands ran from the repository root. No dependencies or environment variables were added.

- `.venv/Scripts/ruff.exe check app tests --fix` and `.venv/Scripts/ruff.exe format app tests`: applied formatting; subsequent lint and format checks passed.
- With `TEST_DATABASE_URL` pointing to local PostgreSQL, `.venv/Scripts/python.exe -m pytest -q -m 'not live' -p no:cacheprovider --tb=short`: **75 passed, 4 deselected**.
- With `RUN_LIVE_OPENAI=1`, `.venv/Scripts/python.exe -m pytest -q -s -m live -p no:cacheprovider --tb=short`: the existing Day 2 live case and customer/order selections passed; the initial policy case failed because the model skipped its lookup. Clarified the tool description and instructions to require a lookup for return-policy questions without requiring customer/order IDs.
- Final `.venv/Scripts/python.exe -m pytest -q -s tests/test_live_tools.py -p no:cacheprovider --tb=short`: **3 passed**. Each test observed the exact tool name and arguments, a found record, a relevant fact in the answer, and exact persisted output through a new database connection.
- `docker compose up -d db --wait`: restored PostgreSQL.
- `docker compose up --build -d --wait api web`: built and started the final implementation. PostgreSQL, API, and web health checks passed; the Next.js production build succeeded.
- Direct HTTP `POST http://127.0.0.1:8000/agent/run` asking whether `ord_1001` arrived returned a successful structured answer stating delivered. An independent PostgreSQL connection verified the committed output and succeeded status.
- Direct HTTP `/health` returned `{"status":"ok"}`; the running frontend at port 3000 displayed `Backend is healthy`.
- `git diff --check`: passed.

One upstream Starlette/AnyIO deprecation warning remains; no application test failures remain.

## Live acceptance evidence

| Check | Successful run ID |
| --- | --- |
| Customer lookup | `1a52cd0f-5e61-45b3-83fd-a75ccd38c1af` |
| Order lookup | `1c6f73ac-9b72-4680-b9f0-cc97267d08c8` |
| Refund-policy lookup | `e080b196-bc73-4663-bce7-bf30dbfb7464` |
| Running Docker API order request | `9dfcbe22-a48b-4144-9f08-c558322e647d` |
| Existing Day 2 live regression | `50d5ce23-ed14-48cb-b468-a96e62a99c32` |

These runs remain stored as evidence. Representative live cases demonstrate current selection behavior; they are not an exhaustive model-quality evaluation.

## Decisions and tradeoffs

- Preserve the existing OpenAI Responses API service and structured `AgentOutput` contract. Selection uses `tool_choice: auto`, tool descriptions, and schemas; there are no intent keyword branches.
- Allow at most one lookup and two provider calls. The final request disables tools. Multiple or repeated tool calls fail safely. The configured timeout and token cap apply per provider call, not to the entire run.
- Use explicitly labelled synthetic, read-only fixtures for Day 3. Integer cents avoid floating-point money. Full business tables, migrations, and tool-call audit records remain Day 5 work.
- Keep durable run persistence unchanged: commit before the model call, then commit final output or safe failure. Only final output is stored; no persistent tool trace is claimed.
- Tool results are data, not instructions. Missing records and malformed arguments produce typed outcomes. No refunds or other business actions are executed.
- Day 4 iterative orchestration, Day 5 agent UI, authentication, and approvals remain outside this implementation.

## Manual configuration and blockers

None for Day 3. Existing backend credentials and billing worked; credentials were not printed or committed. Docker services remain running at http://localhost:3000 (web), http://localhost:8000 (API), and localhost:5432 (PostgreSQL). Live checks consume API credits and require explicit opt-in.

## Prior milestones

Day 1 established and verified the Next.js/FastAPI monorepo and Docker health connection. Day 2 completed September 20, 2026 with 36 non-live tests and a real structured OpenAI response persisted in PostgreSQL (run `74c2d23b-e855-4b8e-9ae9-6351551d9cc1`). The earlier billing blocker was resolved by the user. Day 3 retains these contracts and verifies them through the expanded suite and running application.
