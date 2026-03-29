# Salesforce Monorepo

This repository packages the local Salesforce simulation and agent stack into one place.

## Projects

- `mock-salesforce-mcp`: mock MCP server for Salesforce-style tools, resources, and discovery flows
- `salesforce-agent`: backend agent orchestration and API service
- `salesforce-agent-ui`: frontend UI for running the agent locally
- `salesforce-hybrid-sim`: hybrid simulator with SQLite as source of truth, FastAPI operational endpoints, and Neo4j graph projection
- `neo4j-local-setup`: standalone Neo4j seeding and read-only API project aligned with the hybrid simulator dataset

## Quick Start

```powershell
cd C:\Users\tiger\project\salesforce-monorepo
.\scripts\setup.ps1
```

Create local env files from examples before starting the services:

```powershell
Copy-Item .\salesforce-agent\.env.example .\salesforce-agent\.env
Copy-Item .\salesforce-agent-ui\.env.example .\salesforce-agent-ui\.env
Copy-Item .\salesforce-hybrid-sim\.env.example .\salesforce-hybrid-sim\.env
Copy-Item .\neo4j-local-setup\.env.example .\neo4j-local-setup\.env
```

Then use the helper script for the main agent stack:

```powershell
.\scripts\run-dev.ps1
```

## Suggested Layout

```text
salesforce-monorepo/
  mock-salesforce-mcp/
  neo4j-local-setup/
  salesforce-agent/
  salesforce-agent-ui/
  salesforce-hybrid-sim/
```

## Recommended Local Flows

### 1. Main Agent Stack

Use this when you want the UI, agent backend, and MCP server running together.

```powershell
.\scripts\run-dev.ps1
```

This starts or documents:
- `mock-salesforce-mcp`
- `salesforce-agent`
- `salesforce-agent-ui`

### 2. Hybrid Salesforce Simulation

Use this when you want SQLite-backed operational data plus optional Neo4j graph projection.

Initialize and seed the local SQLite database:

```powershell
cd C:\Users\tiger\project\salesforce-monorepo\salesforce-hybrid-sim
python -m salesforce_hybrid_sim.main --init-db --seed
```

Start the hybrid API:

```powershell
uvicorn salesforce_hybrid_sim.api:app --reload --port 8010
```

If local Neo4j is available, project the SQLite data into Neo4j:

```powershell
python -m salesforce_hybrid_sim.main --sync-graph
```

### 3. Standalone Neo4j Setup

Use this when you want to seed only Neo4j or run the standalone Neo4j-backed mock API.

```powershell
cd C:\Users\tiger\project\salesforce-monorepo\neo4j-local-setup
python -m neo4j_setup.main --reset
uvicorn neo4j_setup.api:app --reload --port 8001
```

## Data Model Notes

- `salesforce-hybrid-sim` is the recommended source-of-truth simulator.
- SQLite is the operational store for Accounts, Contacts, Opportunities, Cases, Campaigns, Users, and Tasks.
- Neo4j is a graph projection used for relationship traversal, graph context, and future Graph RAG flows.
- `neo4j-local-setup` uses the same IDs and seed shape as `salesforce-hybrid-sim` so the two projects stay aligned.
- `mock-salesforce-mcp` can load business data from a local HTTP API instead of fixture JSON when configured.

## Integration Notes

- `mock-salesforce-mcp` uses fixture-based sessions and policy data from `fixtures/users.json`.
- When `MOCK_SF_PREFER_NEO4J=true`, the MCP server tries to load Accounts, Campaigns, Opportunities, and Cases from a local HTTP API defined by `MOCK_SF_GRAPH_API_URL`.
- The hybrid simulator API now returns nested `account` references on related resources so the MCP adapter can consume it directly.

## Repository Notes

- Generated artifacts such as `node_modules`, `dist`, local state databases, logs, and pytest temp folders are ignored at the repo root.
- Each project keeps its own package metadata, local README, and test suite.
- The checked-in projects use `.env.example` templates instead of storing local secret-bearing `.env` files in Git.

## Testing

Representative local test commands:

```powershell
cd C:\Users\tiger\project\salesforce-monorepo\salesforce-hybrid-sim
C:\Users\tiger\project\.venv\Scripts\python.exe -m pytest tests\test_sqlite_store.py tests\test_api.py
```

```powershell
cd C:\Users\tiger\project\salesforce-monorepo\mock-salesforce-mcp
C:\Users\tiger\project\.venv\Scripts\python.exe -m pytest tests\test_datastore.py tests\test_hybrid_integration.py
```

```powershell
cd C:\Users\tiger\project\salesforce-monorepo\neo4j-local-setup
C:\Users\tiger\project\.venv\Scripts\python.exe -m pytest tests\test_seed.py tests\test_api.py
```
