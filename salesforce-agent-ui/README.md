# Salesforce Agent UI

Separate React UI for the `salesforce-agent` FastAPI backend.

## Prerequisites

- Agent backend running at `http://127.0.0.1:8080`
- MCP backend running at `http://127.0.0.1:8000/mcp`
- Matching API bearer token configured in the UI and backend via `AGENT_API_TOKEN`

## Install

```powershell
cd C:\Users\tiger\project\salesforce-agent-ui
npm.cmd install
```

## Run

```powershell
npm.cmd run dev
```

Open:

`http://127.0.0.1:5173`

## What the UI does

- checks `GET /healthz`
- submits agent workflow requests to `POST /run`
- resumes approval workflows with `POST /resume-approval`
