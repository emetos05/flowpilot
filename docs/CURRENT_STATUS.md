# Current status

Updated: September 21, 2026.

- Approved day: **Day 3 - Business tools**.
- Status: **Complete**. Typed tools, model-selected execution, automated tests, and live acceptance checks pass.
- Completed days: **Days 1, 2, and 3**.
- Gate: **Day 3 passed**. Day 4 awaits approval and has not started.

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
