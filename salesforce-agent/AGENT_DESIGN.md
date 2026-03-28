# Salesforce Agent Design

## Purpose

This document describes the implemented design of the `salesforce-agent` project in [`C:\Users\tiger\project\salesforce-agent`](C:\Users\tiger\project\salesforce-agent). It reflects the current codebase, not just the earlier Appendix B concept.

The project is a LangGraph-based multi-agent backend that:

- accepts user requests through FastAPI
- uses OpenAI models through `ChatOpenAI(...)`
- connects to the Salesforce MCP server over streamable HTTP
- separates read, analysis, compliance, approval, and execution concerns
- persists workflow state for approval resume

## Goals

The current implementation is designed to validate these behaviors:

- multi-agent orchestration over an MCP backend
- clear read vs write separation
- approval gating for high-risk write operations
- resumable workflows
- API-first integration for UI or other services

It is not yet a production-hardened enterprise agent platform. Several areas are still mock or simplified by design.

## System Context

The runtime shape is:

```text
User / UI
  -> FastAPI agent backend
  -> LangGraph workflow
  -> MCP client adapter
  -> Salesforce MCP server
```

In this repository, the agent backend is the system boundary. It does not access Salesforce directly. All business operations are expected to flow through the MCP server.

## Repository Structure

Key modules:

- [`agents/api.py`](C:\Users\tiger\project\salesforce-agent\agents\api.py): FastAPI app and HTTP contract
- [`agents/server.py`](C:\Users\tiger\project\salesforce-agent\agents\server.py): Uvicorn entrypoint
- [`agents/system.py`](C:\Users\tiger\project\salesforce-agent\agents\system.py): graph assembly and model initialization
- [`agents/service.py`](C:\Users\tiger\project\salesforce-agent\agents\service.py): workflow registry and persistence
- [`agents/context.py`](C:\Users\tiger\project\salesforce-agent\agents\context.py): `AgentContext` and `WorkflowState`
- [`agents/mcp_client.py`](C:\Users\tiger\project\salesforce-agent\agents\mcp_client.py): MCP adapter wiring and tool scoping
- [`agents/routing.py`](C:\Users\tiger\project\salesforce-agent\agents\routing.py): graph routing rules
- [`agents/prompts.py`](C:\Users\tiger\project\salesforce-agent\agents\prompts.py): role prompts
- [`agents/utils.py`](C:\Users\tiger\project\salesforce-agent\agents\utils.py): text extraction and intent classification
- [`agents/nodes/supervisor.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\supervisor.py): supervisor node
- [`agents/nodes/discovery.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\discovery.py): discovery node
- [`agents/nodes/context_agent.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\context_agent.py): context retrieval and summarization node
- [`agents/nodes/analysis.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\analysis.py): recommendation and proposed action node
- [`agents/nodes/compliance.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\compliance.py): scope and approval policy node
- [`agents/nodes/approval.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\approval.py): human approval interrupt node
- [`agents/nodes/execution.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\execution.py): write execution node

## Core Design Principles

The implemented design follows these rules:

- The supervisor does not call Salesforce tools directly.
- Discovery is limited to search-style MCP tools.
- Context gathering is read-only.
- Analysis may recommend actions but does not execute them.
- Compliance evaluates whether a write may proceed.
- High-risk writes must stop for human approval.
- Execution is the only node allowed to invoke write-capable MCP tools.

This keeps the most dangerous capability isolated to a narrow part of the graph.

## Agent Roles

### Supervisor

The supervisor is responsible for:

- classifying the user request as `read` or `write`
- deciding whether the workflow should continue or finalize
- producing the final end-user response from accumulated workflow state

Implementation:

- [`agents/nodes/supervisor.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\supervisor.py)
- intent classification uses [`agents/utils.py`](C:\Users\tiger\project\salesforce-agent\agents\utils.py)

Behavior:

- on initial `phase=route`, it classifies intent locally
- on completion, it asks the LLM to summarize workflow outputs into a concise answer
- if an error exists in state, it returns a failure response and ends the workflow

### Discovery Agent

The discovery agent resolves the business entity referenced by the user.

Implementation:

- [`agents/nodes/discovery.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\discovery.py)

Expected tools:

- `search_advertiser`
- `search_global`

Behavior:

- invokes the discovery subagent with search-only tools
- extracts an `acct_*` identifier from model output
- sets `entity_id` and `entity_confidence` in workflow state

Current limitation:

- entity extraction is string-based and heuristic
- the node currently assumes identifiers are present in model output rather than parsing a strict structured schema

### Context Agent

The context agent fetches read-only business context and summarizes it for the rest of the workflow.

Implementation:

- [`agents/nodes/context_agent.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\context_agent.py)

Behavior:

- uses resolved `entity_id` or falls back to `agent_context.account_scope`
- reads account summary, campaigns, and opportunities through MCP resource URIs
- summarizes fetched resources through the context LLM
- returns normalized `account_context` into workflow state

Resource URI pattern used by the current implementation:

- `sf://org/{org_id}/session/{session_token}/account/{entity_id}/summary`
- `sf://org/{org_id}/session/{session_token}/account/{entity_id}/campaigns`
- `sf://org/{org_id}/session/{session_token}/account/{entity_id}/opportunities`

Fallback behavior:

- if resource reads fail and a context tool exists, the node attempts a tool-based fallback
- otherwise it emits `SERVICE_DEGRADED`

Current limitation:

- the agent expects a read tool named `get_advertiser_context`, but the current mock MCP server does not expose that tool
- in practice, this means the primary path is MCP resources, not a context tool fallback

### Analysis Agent

The analysis agent transforms account context into recommendations and, for write requests, a proposed action.

Implementation:

- [`agents/nodes/analysis.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\analysis.py)

Behavior:

- summarizes context into a recommendation list
- for write intent, synthesizes a `proposed_action`
- generates an `idempotency_key` if one does not already exist

Current write proposal behavior:

- proposed tool is hard-coded to `update_campaign_budget`
- campaign id and budget are currently mock values

This is acceptable for the prototype but not sufficient for real execution planning.

### Compliance Agent

The compliance node validates whether the proposed write can proceed.

Implementation:

- [`agents/nodes/compliance.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\compliance.py)

Checks performed:

- write action exists
- tool is in the approved tool set
- session auth state permits writes
- resolved entity matches `account_scope` when scope is pinned
- high-risk tools and actions require human approval

High-risk tools:

- `update_campaign_budget`
- `optimize_campaign`

Behavior:

- returns `compliance_cleared=True` for low-risk allowed writes
- routes high-risk writes to approval
- returns structured errors for denied cases

### Human Approval Node

The approval node is the pause point for high-risk actions.

Implementation:

- [`agents/nodes/approval.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\approval.py)

Behavior:

- builds a review packet
- interrupts the graph before execution
- expects a later resume command with `decision` and `approval_token`
- rejects the workflow if the human decision is not `approve`

This node is what enables the `/resume-approval` API path.

### Execution Agent

The execution node is the only write-capable node.

Implementation:

- [`agents/nodes/execution.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\execution.py)

Behavior:

- validates that a tool name exists
- validates presence of `idempotency_key`
- requires `approval_token` for high-risk tools
- injects the session token
- asks the execution subagent to perform the approved write

Design rule:

- execution never decides whether a write should happen
- it only performs a write that has already passed prior gates

## State Model

The workflow state lives in [`agents/context.py`](C:\Users\tiger\project\salesforce-agent\agents\context.py).

### AgentContext

`AgentContext` is the session-bound policy and identity envelope.

Fields:

- `user_id`
- `org_id`
- `region`
- `approved_tool_set`
- `account_scope`
- `risk_tier`
- `auth_state`

Important helpers:

- `is_write_permitted()`
- `is_tool_approved(tool_name)`

### WorkflowState

`WorkflowState` is the LangGraph state object.

Key fields:

- `user_input`
- `intent`
- `agent_context`
- `entity_id`
- `entity_confidence`
- `account_context`
- `recommendations`
- `proposed_action`
- `idempotency_key`
- `approval_token`
- `compliance_cleared`
- `phase`
- `final_response`
- `error`

The state is intentionally compact. It is designed more for orchestration than for full audit reconstruction.

## Graph Design

The graph is assembled in [`agents/system.py`](C:\Users\tiger\project\salesforce-agent\agents\system.py) using `StateGraph`.

Flow:

```text
supervisor
  -> discovery
  -> context
  -> analysis
  -> compliance (write only)
  -> approval (high risk only)
  -> execution
  -> supervisor
  -> end
```

Actual routing rules:

- supervisor:
  - `read` -> discovery
  - `write` -> discovery
  - terminal phases -> end
- analysis:
  - error -> end
  - read intent -> supervisor
  - write intent -> compliance
- compliance:
  - blocked -> end
  - approved -> execution
  - needs human -> approval

The graph is compiled with:

- a checkpointer
- `interrupt_before=["approval"]`

That interrupt configuration is what allows approval to be resumed later through persisted state.

## LLM Model Design

The project uses OpenAI explicitly through `ChatOpenAI`.

Implementation:

- [`agents/system.py`](C:\Users\tiger\project\salesforce-agent\agents\system.py)

Model construction:

- input model name may be `openai:gpt-5.3-codex` or a raw OpenAI model name
- the `openai:` prefix is stripped before constructing `ChatOpenAI(...)`
- API key is read from `OPENAI_API_KEY`
- temperature is fixed at `0`

This is more explicit than relying on provider-prefixed model routing inside LangChain.

## MCP Integration

MCP integration lives in [`agents/mcp_client.py`](C:\Users\tiger\project\salesforce-agent\agents\mcp_client.py).

### Transport

The agent connects to the MCP server using:

- `MultiServerMCPClient`
- transport `streamable_http`

The MCP URL is passed through request payload or environment.

### Auth Header

The MCP client sends:

- `Authorization: Bearer {session_token}`

The current design treats the session token as the upstream identity binding used by the MCP server.

### Tool Scoping

The agent narrows tool visibility by role:

- read roles:
  - `search_advertiser`
  - `search_global`
  - `get_advertiser_context`
- execution role:
  - `create_support_case`
  - `update_campaign_budget`
  - `log_sales_activity`
  - `optimize_campaign`
  - `resolve_advertiser_issue`

Then it intersects these sets with `AgentContext.approved_tool_set`.

Current limitation:

- not every declared read or write tool exists in the current mock MCP server
- the design is broader than the current server implementation

## Prompts

Role prompts are defined in [`agents/prompts.py`](C:\Users\tiger\project\salesforce-agent\agents\prompts.py).

Prompt strategy:

- supervisor prompt defines orchestration role
- discovery prompt enforces search-only behavior
- context prompt enforces read-only context building
- analysis prompt allows recommendations but not writes
- execution prompt requires idempotency and approval discipline

The prompts are short and directional. Most control is implemented in graph structure and code, not prompt text alone.

## API Design

The FastAPI application is in [`agents/api.py`](C:\Users\tiger\project\salesforce-agent\agents\api.py).

### Endpoints

`GET /healthz`

- returns process health
- indicates whether `OPENAI_API_KEY` is configured
- indicates whether API auth is enabled

`POST /run`

- starts a workflow
- creates or replaces workflow state for `thread_id`
- returns the resulting workflow output and serialized agent context

`POST /resume-approval`

- reloads stored workflow state for `thread_id`
- resumes the graph from the approval interrupt

### Request Model

`/run` accepts:

- `user_input`
- `thread_id`
- `mcp_url`
- `model`
- `session_token`
- `user_id`
- `org_id`
- `region`
- `account_scope`
- `approved_tools`

This makes the API easy to test, but it also means identity and scope are currently client-supplied rather than server-derived.

## API Authentication

HTTP auth is implemented with FastAPI `HTTPBearer`.

Behavior:

- `/run` and `/resume-approval` require a bearer token
- the token must equal `AGENT_API_TOKEN`
- `/healthz` is intentionally open

This is a minimal service-to-service protection layer, not end-user authentication.

## Persistence Design

Workflow persistence lives in [`agents/service.py`](C:\Users\tiger\project\salesforce-agent\agents\service.py).

### Registry

`AgentSystemRegistry` manages:

- active in-memory systems
- workflow metadata
- SQLite persistence

### Storage

Default database path:

- [`C:\Users\tiger\project\salesforce-agent\agent_state.db`](C:\Users\tiger\project\salesforce-agent\agent_state.db)

Stored values per `thread_id`:

- `session_token`
- `mcp_url`
- `model`
- serialized `AgentContext`
- serialized checkpointer blob
- `updated_at`

### Resume Behavior

When `/resume-approval` is called:

- the registry checks in-memory systems first
- if not present, it loads state from SQLite
- it rebuilds the agent system using the persisted checkpointer

Current limitation:

- the checkpointer is persisted by pickling LangGraph `MemorySaver`
- this is adequate for a prototype but weak for multi-process or horizontally scaled deployment

## Error Handling

The current design uses a mix of:

- workflow-level structured error dictionaries in state
- FastAPI `HTTPException` at the API boundary

Representative workflow errors:

- `ENTITY_DISAMBIGUATION_REQUIRED`
- `SERVICE_DEGRADED`
- `VALIDATION_SCHEMA_MISMATCH`
- `PERMISSION_DENIED_SCOPE`
- `AUTH_REAUTH_REQUIRED`
- `APPROVAL_REJECTED`
- `APPROVAL_REQUIRED`

The agent backend does not yet normalize all failures into one shared error schema across API, graph, and MCP layers.

## Deployment Model

The project is built to run as a backend service.

Runtime shape:

- FastAPI app
- served by Uvicorn
- Dockerized separately from the MCP server

Key files:

- [`Dockerfile`](C:\Users\tiger\project\salesforce-agent\Dockerfile)
- [`agents/server.py`](C:\Users\tiger\project\salesforce-agent\agents\server.py)

Default service settings:

- host: `0.0.0.0`
- port: `8080`
- state DB path: `/data/agent_state.db` in containerized deployment

This makes the service suitable for local container runs and the first Kubernetes deployment pass.

## Testing Strategy

The project includes both unit and mocked graph/API tests.

Test files:

- [`tests/test_routing.py`](C:\Users\tiger\project\salesforce-agent\tests\test_routing.py)
- [`tests/test_compliance.py`](C:\Users\tiger\project\salesforce-agent\tests\test_compliance.py)
- [`tests/test_approval.py`](C:\Users\tiger\project\salesforce-agent\tests\test_approval.py)
- [`tests/test_execution.py`](C:\Users\tiger\project\salesforce-agent\tests\test_execution.py)
- [`tests/test_graph.py`](C:\Users\tiger\project\salesforce-agent\tests\test_graph.py)
- [`tests/test_api.py`](C:\Users\tiger\project\salesforce-agent\tests\test_api.py)
- [`tests/test_service.py`](C:\Users\tiger\project\salesforce-agent\tests\test_service.py)

Coverage areas:

- intent routing
- compliance checks
- approval handling
- execution guards
- mocked graph transitions
- API authentication and request handling
- persistence and reload behavior

The tests intentionally avoid live OpenAI and live MCP dependencies.

## Known Gaps

The current implementation is functional, but these gaps should be treated as intentional prototype limits:

- discovery uses heuristic text extraction rather than structured tool output parsing
- analysis proposes a mostly hard-coded write action
- some tool names in the agent code are broader than the current mock MCP server implementation
- the context fallback expects `get_advertiser_context`, which the current MCP server does not expose
- API request context is client-supplied rather than derived from authenticated identity
- persisted checkpointer storage is pickle-based and not robust for multi-instance deployment
- no distributed queue, retry policy, or background job worker exists yet
- no end-user auth or RBAC layer exists on top of `AGENT_API_TOKEN`

## Recommended Next Steps

The next upgrades should be:

1. Replace heuristic node outputs with structured schemas for discovery, analysis, and execution planning.
2. Align the agent tool catalog exactly with the MCP server surface.
3. Replace pickled `MemorySaver` persistence with a durable shared checkpoint backend.
4. Move identity, org, region, and scope derivation to the server side.
5. Add observability for request IDs, workflow steps, tool calls, and approval events.
6. Add a background execution mode for long-running workflows.

## Summary

The implemented `salesforce-agent` project is a backend-oriented, LangGraph-based multi-agent system that uses OpenAI models and an MCP server to execute a controlled Salesforce workflow. The design is strongest where it separates read, analysis, compliance, approval, and execution responsibilities. Its main weaknesses are in prototype simplifications: heuristic parsing, partial MCP surface mismatch, and non-production persistence.
