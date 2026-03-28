# Salesforce Monorepo

This repository packages the Salesforce agent stack into one place:

- `mock-salesforce-mcp`: mock MCP server for Salesforce-style tools, resources, and discovery flows
- `salesforce-agent`: backend agent orchestration and API service
- `salesforce-agent-ui`: frontend UI for running the agent locally

## Quick Start

```powershell
cd C:\Users\tiger\project\salesforce-monorepo
.\scripts\setup.ps1
```

Create local env files from examples before starting the services:

```powershell
Copy-Item .\salesforce-agent\.env.example .\salesforce-agent\.env
Copy-Item .\salesforce-agent-ui\.env.example .\salesforce-agent-ui\.env
```

Then use:

```powershell
.\scripts\run-dev.ps1
```

## Suggested Layout

```text
salesforce-monorepo/
  mock-salesforce-mcp/
  salesforce-agent/
  salesforce-agent-ui/
```

## Notes

- Generated artifacts such as `node_modules`, `dist`, local state databases, logs, and pytest temp folders are ignored at the repo root.
- The checked-in agent project now uses `.env.example` instead of carrying a local secret-bearing `.env`.
- Each project still keeps its own package metadata and local README.
- The original `C:\Users\tiger\project\salesforce-agent` folder still exists because the active workspace was locked during move; the copied version under this folder is the one to use for the new GitHub repo.

## Next Steps

1. Review whether any project-specific `.env` files should be replaced with `.env.example`.
2. Add a root-level developer setup guide or script.
3. Create the GitHub remote and push this folder as the new repository.
