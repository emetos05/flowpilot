# Senior AI Engineer Portfolio Roadmap

## Objective

Build and publish two production-oriented AI applications and one reusable evaluation toolkit in six weeks. The portfolio should demonstrate senior-level applied AI engineering through working code, deployment, evaluation, observability, security, cost control, and documented architectural decisions.

The primary hiring target is Senior AI Engineer or Applied AI Engineer at an AI-native startup.

## Schedule and constraints

- Start date: September 15, 2026
- Target finish: October 26, 2026
- Weekdays: 2 hours per day
- Weekends: 4 hours per day
- Total engineering time: approximately 108 hours
- Job search: 14 tailored applications per week
- Infrastructure target: lowest practical cost
- Repositories should remain public unless they contain secrets or licensed material.

## Execution contract

These rules apply to every coding agent and human contributor:

1. Read this file and the current repository state before making changes.
2. Work only on the currently approved day.
3. Do not begin the next day until every acceptance criterion for the current day passes.
4. Preserve working behavior unless the current task explicitly changes it.
5. Keep secrets out of source control. Update `.env.example` when configuration changes.
6. Run the affected application, tests, linters, and type checks whenever they exist.
7. Fix errors introduced or discovered within the current day's scope.
8. Prefer the smallest implementation that proves the required engineering capability.
9. At completion, report files changed, commands run, verification results, decisions, tradeoffs, and remaining blockers.
10. Update the checkbox and status only after acceptance criteria pass.

Status values: `Not Started`, `In Progress`, `Blocked`, `Complete`.

## Portfolio projects

| Project | Purpose | Target |
|---|---|---:|
| FlowPilot | Production agentic workflow SaaS | Day 21 |
| DocOps AI | Document-to-action automation platform | Day 35 |
| AgentEval | Reusable agent evaluation toolkit | Day 39 |
| Portfolio | GitHub positioning, demos, case studies, gap audit | Day 42 |

## Milestone gates

| Day | Target date | Hiring signal |
|---:|---|---|
| 7 | September 21 | Working, authenticated, tool-using FlowPilot agent |
| 14 | September 28 | Deployed agent with RAG, evaluations, AWS and CI/CD |
| 21 | October 5 | LangGraph, tracing, memory, model routing and architecture documentation |
| 28 | October 12 | Two deployed AI applications |
| 35 | October 19 | MCP integration, security hardening and adversarial evaluations |
| 42 | October 26 | Two flagship systems plus reusable open-source evaluation tooling |

---

## Week 1: FlowPilot foundations

### Day 1 — Monorepo and verified local development

- Date: September 15, 2026
- Time budget: 2 hours
- Status: **Complete**
- Priority: Critical
- Skills: repository design, Next.js, FastAPI, Docker

Tasks:

- [x] Inspect the existing repository and any `AGENTS.md` instructions.
- [x] Create a monorepo with `apps/web` for Next.js, TypeScript and App Router.
- [x] Create `apps/api` for FastAPI and Python.
- [x] Add `GET /health` with a simple JSON health response.
- [x] Connect the frontend to the backend health endpoint.
- [x] Add development Dockerfiles and a root `docker-compose.yml`.
- [x] Add `.gitignore`, `.env.example` and the initial README.
- [x] Document the business problem, architecture, repository structure, local setup, Docker setup and environment variables.
- [x] Run both applications and fix errors within Day 1 scope.

Acceptance criteria:

- [x] The Next.js application starts successfully.
- [x] The FastAPI application starts successfully.
- [x] Calling `/health` directly returns a successful response.
- [x] The frontend visibly displays health data retrieved from FastAPI.
- [x] Browser requests succeed without a CORS or environment-variable error.
- [x] `docker compose up --build` starts both services successfully.
- [x] No secrets or generated dependency directories are tracked.
- [x] A new developer can follow the README to run the system.
- [x] The completion summary lists files changed, commands run, verification results and architectural decisions.

Out of scope:

- OpenAI integration
- `/agent/run`
- PostgreSQL or Supabase
- Authentication
- Agent tools
- Production deployment

Deliverable: a public repository with both applications running locally, a verified frontend-to-backend connection, Docker support and an architecture-first README.

### Day 2 — Structured agent endpoint

- Date: September 16, 2026
- Time budget: 2 hours
- Status: **Complete**
- Priority: Critical

Tasks:

- [x] Implement FastAPI `POST /agent/run`.
- [x] Add the OpenAI integration behind a service interface.
- [x] Use Pydantic schemas for request and structured model output.
- [x] Persist `agent_run` records in PostgreSQL.

Acceptance criteria:

- [x] A valid request produces schema-validated structured output. Live OpenAI and PostgreSQL verification passed September 20, 2026; evidence is recorded in docs/CURRENT_STATUS.md.
- [x] Each request creates a durable agent-run record.
- [x] Configuration and API secrets come from environment variables.
- [x] Error responses do not expose secrets or raw internal exceptions.

Deliverable: a request produces validated structured output and a stored run record.

### Day 3 — Business tools

- Date: September 17, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

Tasks:

- [ ] Implement `get_customer`.
- [ ] Implement `get_order`.
- [ ] Implement `get_refund_policy`.
- [ ] Allow the model to select tools rather than hard-coding intent branches.
- [ ] Add unit tests for success, invalid input and missing records.

Acceptance criteria:

- [ ] All three tools use typed inputs and outputs.
- [ ] The model can select the correct tool for representative requests.
- [ ] Tool tests pass.

Deliverable: three tested tools invoked through model tool selection.

### Day 4 — Bounded agent loop

- Date: September 18, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

Tasks:

- [ ] Implement tool selection, execution, observation and next-decision stages.
- [ ] Add explicit run state.
- [ ] Add maximum-step, timeout and invalid-tool safeguards.

Acceptance criteria:

- [ ] State transitions are visible and testable.
- [ ] The loop terminates successfully or with a controlled failure.
- [ ] An agent cannot call tools indefinitely.

Deliverable: a bounded agent loop with visible state transitions and safe termination.

### Day 5 — Database schema and agent interface

- Date: September 19, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: High

Tasks:

- [ ] Create Supabase tables for users, customers, orders, policies, agent runs, tool calls and approvals.
- [ ] Add migrations and realistic seed data.
- [ ] Build the initial Next.js agent request interface.

Acceptance criteria:

- [ ] Schema creation is repeatable through migrations.
- [ ] Seed data supports the primary refund scenario.
- [ ] A user can submit an agent request and see its result.

Deliverable: a seeded database and usable agent request screen.

### Day 6 — Human approval and audit history

- Date: September 20, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

Tasks:

- [ ] Make the agent propose a refund without executing it immediately.
- [ ] Display the proposed action in the UI.
- [ ] Add approve and reject operations.
- [ ] Add retry handling and an audit trail.

Acceptance criteria:

- [ ] Restricted actions wait for explicit approval.
- [ ] Approval executes an action once only.
- [ ] Rejection leaves business records unchanged.
- [ ] The audit trail records proposal, reviewer decision and result.

Deliverable: an end-to-end approval workflow with retries and audit history.

### Day 7 — Authentication and Week 1 presentation

- Date: September 21, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

Tasks:

- [ ] Add Auth0 to the frontend.
- [ ] Protect FastAPI routes and validate bearer tokens.
- [ ] Clean the repository and remove unused scaffold code.
- [ ] Add screenshots and an architecture diagram to the README.

Acceptance criteria:

- [ ] Anonymous callers cannot access protected operations.
- [ ] An authenticated user can complete the demonstrated workflow.
- [ ] The repository contains no committed secrets.
- [ ] Week 1 architecture and setup are understandable from the README.

Deliverable: an authenticated working agent and recruiter-ready Week 1 README.

---

## Week 2: Production FlowPilot

### Day 8 — Embeddings and knowledge ingestion

- Date: September 22, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Add refund, shipping and warranty source documents.
- [ ] Create an ingestion pipeline with explicit chunk metadata.
- [ ] Generate embeddings and store them in Supabase pgvector.
- [ ] Verify repeatable ingestion without duplicate chunks.

Deliverable: a searchable policy knowledge base in Supabase pgvector.

### Day 9 — Traceable retrieval

- Date: September 23, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Implement query, candidate retrieval, relevance filtering and context construction.
- [ ] Return source citations with grounded results.
- [ ] Record retrieved chunks with each agent run.
- [ ] Test queries with relevant and irrelevant policies.

Deliverable: a traceable retrieval pipeline with stored evidence.

### Day 10 — Golden evaluation dataset

- Date: September 24, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Create at least 20 versioned scenarios.
- [ ] Record expected intent, expected tools, forbidden actions and expected result.
- [ ] Include ordinary, ambiguous and unsafe requests.

Deliverable: a versioned golden evaluation dataset with at least 20 cases.

### Day 11 — Automated evaluation runner

- Date: September 25, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Measure tool-selection accuracy and argument accuracy.
- [ ] Measure action success and answer quality.
- [ ] Record latency, token usage and approximate cost.
- [ ] Produce a repeatable report.

Deliverable: an automated evaluation report generated from the golden dataset.

### Day 12 — CI/CD and production container hardening

- Date: September 26, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Harden the Day 1 Docker images for production use.
- [ ] Add GitHub Actions for linting, type checking, tests, frontend checks and Docker builds.
- [ ] Deploy the frontend and backend.
- [ ] Document rollback and configuration steps.

Deliverable: a green CI pipeline plus live frontend and API endpoints.

### Day 13 — Asynchronous execution and telemetry

- Date: September 27, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Add SQS-backed execution for longer runs.
- [ ] Add CloudWatch logging with bounded retention.
- [ ] Add timeouts, retries and idempotency protection.
- [ ] Record model, token, latency and cost telemetry.
- [ ] Run the complete evaluation suite.

Deliverable: an observable asynchronous workflow with a current evaluation baseline.

### Day 14 — Public demo and portfolio conversion

- Date: September 28, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Record a two-to-three-minute demo.
- [ ] Rewrite the README around the business problem, architecture, evaluations and tradeoffs.
- [ ] Add live links and current benchmark results.
- [ ] Pin the repository to the GitHub profile.

Deliverable: a live demo, short video and polished pinned repository.

---

## Week 3: Agent engineering depth

### Day 15 — LangGraph orchestration

- Date: September 29, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Model one production workflow with LangGraph state, nodes, edges and conditional routing.
- [ ] Preserve existing behavior and evaluations.
- [ ] Document why the workflow benefits from graph orchestration.

Deliverable: one production path running through a documented LangGraph graph.

### Day 16 — Checkpoint and resume

- Date: September 30, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Add durable checkpoints.
- [ ] Interrupt execution while waiting for human approval.
- [ ] Resume without repeating completed tool calls.

Deliverable: a workflow that resumes correctly after approval.

### Day 17 — Memory boundaries

- Date: October 1, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Separate short-term execution state from persistent business memory.
- [ ] Define retention and user-isolation rules.
- [ ] Test memory isolation and persistence.

Deliverable: a documented memory model with isolation and persistence tests.

### Day 18 — Model routing

- Date: October 2, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Use a lower-cost model for classification and extraction.
- [ ] Route difficult decisions to a stronger model.
- [ ] Record route, rationale, latency and cost.
- [ ] Confirm quality using the evaluation suite.

Deliverable: a configurable model router with recorded model choice and cost.

### Day 19 — Tracing and failure analysis

- Date: October 3, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Trace prompts, model responses, retrieval, tool calls, tokens and latency.
- [ ] Create three deliberate failure cases.
- [ ] Diagnose root causes and document mitigations.

Deliverable: a trace view and concise failure-analysis document.

### Day 20 — RAG experiments

- Date: October 4, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Compare chunking strategies.
- [ ] Compare top-k settings and relevance filtering.
- [ ] Evaluate reranking and citation quality.
- [ ] Publish before-and-after quality, latency and cost measurements.

Deliverable: a RAG experiment report showing measured tradeoffs.

### Day 21 — Architecture document

- Date: October 5, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Write `ARCHITECTURE.md`.
- [ ] Cover reliability, security, authorization, idempotency, scaling and cost.
- [ ] Document failure modes and rejected alternatives.
- [ ] Link it from the README.

Deliverable: a senior-level architecture document.

---

## Week 4: DocOps AI

### Day 22 — Repository and event-driven architecture

- Date: October 6, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Create the DocOps AI repository.
- [ ] Define upload, S3, processing job, extraction, database and approval components.
- [ ] Add a runnable skeleton and architecture documentation.

Deliverable: a public repository with a clear event-driven architecture.

### Day 23 — Secure document upload

- Date: October 7, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Implement S3 pre-signed uploads.
- [ ] Persist document metadata and ownership.
- [ ] Validate file type, size and upload state.

Deliverable: a secure direct-upload flow with stored document metadata.

### Day 24 — Structured invoice extraction

- Date: October 8, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Define typed Pydantic invoice schemas.
- [ ] Extract fields without manual regex-based model-output parsing.
- [ ] Return validation issues explicitly.

Deliverable: a validated extraction endpoint returning typed invoice fields.

### Day 25 — Deterministic business validation

- Date: October 9, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Validate totals, missing values, suppliers and duplicate invoices.
- [ ] Keep deterministic rules separate from AI reasoning.
- [ ] Add boundary and failure tests.

Deliverable: a tested deterministic validation engine.

### Day 26 — Lookup tools and recommendation

- Date: October 10, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Add vendor lookup, purchase-order lookup and policy-search tools.
- [ ] Generate an explainable recommendation.
- [ ] Require human review for policy-defined risk conditions.

Deliverable: a tool-using workflow that produces an explainable approval recommendation.

### Day 27 — Reliable SQS processing

- Date: October 11, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Build the SQS processing pipeline.
- [ ] Implement idempotent consumers.
- [ ] Add retry policy and dead-letter handling.
- [ ] Verify duplicate messages do not duplicate business records.

Deliverable: reliable asynchronous document processing with failure recovery.

### Day 28 — Deploy the second application

- Date: October 12, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Deploy DocOps AI.
- [ ] Add live links and setup instructions.
- [ ] Update GitHub and application materials to reference both systems.

Deliverable: a second live AI application and updated portfolio links.

---

## Week 5: MCP, security and adversarial evaluation

### Day 29 — MCP foundations

- Date: October 13, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Learn MCP hosts, clients, servers, tools, resources, transports and permissions.
- [ ] Map MCP capabilities to DocOps use cases.

Deliverable: concise MCP notes mapped to the application.

### Day 30 — MCP server

- Date: October 14, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Expose vendor and invoice capabilities through a small MCP server.
- [ ] Use narrow, validated tool schemas.
- [ ] Add positive and negative tests.

Deliverable: a tested MCP server with business-safe tool contracts.

### Day 31 — MCP client integration

- Date: October 15, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Connect the agent to the MCP server.
- [ ] Demonstrate equivalent capabilities through local tools and MCP.
- [ ] Document deployment, trust and maintenance tradeoffs.

Deliverable: a working MCP integration and architectural comparison.

### Day 32 — AI security hardening

- Date: October 16, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Defend against prompt injection in documents and retrieved content.
- [ ] Enforce tool authorization and argument validation.
- [ ] Define PII-safe logging behavior.
- [ ] Add a threat model and security tests.

Deliverable: a documented threat model with implemented guardrails.

### Day 33 — DocOps evaluation dataset

- Date: October 17, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Build a versioned golden dataset.
- [ ] Prefer deterministic validators where ground truth is explicit.
- [ ] Use model-based grading only where necessary.

Deliverable: a versioned evaluation dataset and grading strategy.

### Day 34 — Adversarial tests

- Date: October 18, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Test malformed documents.
- [ ] Test embedded prompt injection.
- [ ] Test duplicates, missing values and tool failures.
- [ ] Record expected safe behavior and actual results.

Deliverable: an adversarial test suite with failure-handling results.

### Day 35 — Model and configuration benchmark

- Date: October 19, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Compare quality, latency and estimated cost across configurations.
- [ ] Make the benchmark reproducible.
- [ ] Publish the result in the README or a linked case study.

Deliverable: a reproducible quality, latency and cost benchmark.

---

## Week 6: AgentEval and portfolio conversion

### Day 36 — AgentEval package architecture

- Date: October 20, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Extract reusable evaluation concepts from FlowPilot.
- [ ] Create modules for scenarios, evaluators, graders, runners and reporters.
- [ ] Define a minimal stable public API.

Deliverable: an installable AgentEval package skeleton.

### Day 37 — Reusable graders

- Date: October 21, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Implement graders for tool selection, arguments, structured output and final result.
- [ ] Return clear diagnostics rather than only pass/fail values.
- [ ] Add unit tests.

Deliverable: tested reusable graders with actionable diagnostics.

### Day 38 — Reports and open-source release

- Date: October 22, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Generate Markdown and JSON evaluation reports.
- [ ] Add installation and usage documentation.
- [ ] Publish the public repository.

Deliverable: a public package repository with sample reports.

### Day 39 — FlowPilot integration and CI

- Date: October 23, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: High

- [ ] Add a copyable FlowPilot integration example.
- [ ] Add tests and GitHub Actions.
- [ ] Confirm the example generates a report from a small dataset.

Deliverable: green CI and an end-to-end integration example.

### Day 40 — GitHub overhaul

- Date: October 24, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Pin FlowPilot, DocOps AI and AgentEval.
- [ ] Improve READMEs, architecture diagrams, screenshots, demos, badges and setup instructions.
- [ ] Reduce the visibility of weak or irrelevant repositories.
- [ ] Verify every public link in a signed-out browser session.

Deliverable: a focused GitHub profile with three strong pinned projects.

### Day 41 — Demonstrations and case studies

- Date: October 25, 2026
- Time budget: 4 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Create short project demonstration videos.
- [ ] Write case studies covering problem, architecture, decisions, failures, evaluations, results and lessons.
- [ ] Make each artifact understandable without running the code.

Deliverable: recruiter-friendly demonstrations and two technical case studies.

### Day 42 — Market-alignment audit

- Date: October 26, 2026
- Time budget: 2 hours
- Status: **Not Started**
- Priority: Critical

- [ ] Audit the portfolio against 15 Senior AI Engineer job descriptions.
- [ ] Count repeated missing requirements.
- [ ] Add only recurring gaps to the next backlog.
- [ ] Record the final portfolio links and current evaluation results.

Deliverable: a gap-frequency matrix and prioritized post-plan backlog.

---

## Daily job-search routine

- Submit two tailored applications per day, targeting approximately 14 per week.
- Prioritize Senior Applied AI Engineer, Senior AI Engineer, AI Product Engineer, Senior Agent Engineer, Senior Software Engineer — AI, AI Platform Engineer and Founding AI Engineer roles.
- Link the strongest live project, architecture document and short demonstration available that day.
- Record the company, role, link, date, contact, application status and next follow-up date.

## Completion-report template

Use this format at the end of every day:

```markdown
## Day N completion report

Status: Complete | Blocked

### Acceptance criteria
- [x] Criterion that passed
- [ ] Criterion that remains blocked

### Files changed
- `path/to/file`: reason

### Commands run
- `command`: result

### Verification
- Check performed: evidence and outcome

### Decisions and tradeoffs
- Decision: rationale

### Manual configuration
- Required user action, or `None`

### Next step
- Day N+1 may begin | Do not begin Day N+1 because ...
```

## Current status

- Active day: Day 2 (approved by user on September 19, 2026)
- Overall status: Day 2 Complete - awaiting approval for Day 3
- Completed days: 2 of 42
- Current gate: Day 2 acceptance criteria passed. Day 3 may begin when approved; it has not started. See docs/CURRENT_STATUS.md for verification evidence.
