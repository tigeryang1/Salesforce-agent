# Salesforce Agent

LangGraph multi-agent client that follows `Appendix B` and connects to the mock Salesforce MCP server.

## What this project contains

- `SupervisorAgent` routing flow
- `DiscoveryAgent`, `ContextAgent`, `AnalysisAgent`
- `ComplianceAgent` + human approval interrupt
- `ExecutionAgent` with write-only tooling path
- `AgentContext` policy binding

## Prerequisites

1. A running MCP server endpoint, for example:
`http://127.0.0.1:8000/mcp`
2. LLM API key for model execution:
`GEMINI_API_KEY` for Gemini models or `OPENAI_API_KEY` for OpenAI models
3. API bearer token for protected endpoints:
`AGENT_API_TOKEN`

## Install

```powershell
cd C:\Users\tiger\project\salesforce-agent
python -m pip install -e .
```

## Run

Backend server:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:AGENT_MODEL="gemini:gemini-2.5-flash"
$env:AGENT_API_TOKEN="your_agent_api_token"
python -m agents.server
```

Server endpoints:

- `GET /healthz`
- `POST /run`
- `POST /resume-approval`

Example:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/run" -ContentType "application/json" -Body '{
  "user_input": "Analyze Nike account and suggest optimizations",
  "thread_id": "demo-1",
  "mcp_url": "http://127.0.0.1:8000/mcp",
  "model": "gemini:gemini-2.5-flash"
}' -Headers @{ Authorization = "Bearer your_agent_api_token" }
```

CLI runner for local debugging:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:AGENT_MODEL="gemini:gemini-2.5-flash"
$env:AGENT_API_TOKEN="your_agent_api_token"
python -m agents.run --mcp-url "http://127.0.0.1:8000/mcp" --input "Analyze Nike account and suggest optimizations"
```

Write flow with auto approval resume:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:AGENT_MODEL="gemini:gemini-2.5-flash"
$env:AGENT_API_TOKEN="your_agent_api_token"
python -m agents.run --mcp-url "http://127.0.0.1:8000/mcp" --input "Increase Nike Spring Sale campaign budget" --approve
```

## Notes

- Session token defaults to `tok_alice_us`.
- For a different tenant/org/session, pass CLI flags in `python -m agents.run --help`.
- The runtime supports both `gemini:...` and `openai:...` model prefixes.
- Workflow registry state is persisted to `agent_state.db` by default. Override with `AGENT_STATE_DB`.
