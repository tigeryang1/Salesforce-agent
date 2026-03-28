# Mock Salesforce MCP Server

Starter repository for a contract-first mock MCP server based on `Appendix A`.

## What this provides

- Mock `tools`, `resources`, and `prompts`
- Session and policy simulation (`auth_state`, tool scope, account scope, region checks)
- Structured errors (`APPROVAL_REQUIRED`, `ENTITY_DISAMBIGUATION_REQUIRED`, etc.)
- Idempotency for write tools
- Async job simulation for `optimize_campaign`
- Degraded mode metadata on resource responses

## Project layout

`app/` contains the server and business logic.

`fixtures/` contains deterministic sample data.

`tests/` contains first-pass unit tests for policy and tool behavior.

## Quick start

```powershell
cd C:\Users\tiger\project\mock-salesforce-mcp
python -m pip install -e .[dev]
python -m app.server
```

Run as HTTP MCP endpoint (browser-friendly for inspector setups):

```powershell
python -m app.server --transport streamable-http
```

Default MCP endpoint:

`http://127.0.0.1:8000/mcp`

Override host/port/path:

```powershell
$env:MCP_HOST="127.0.0.1"
$env:MCP_PORT="9000"
$env:MCP_PATH="/mcp"
python -m app.server --transport streamable-http
```

## Session tokens for testing

Use one of the tokens in `fixtures/users.json`:

- `tok_alice_us`
- `tok_eva_eu`

## First-pass tools

- `search_advertiser`
- `search_global`
- `create_support_case`
- `update_campaign_budget`
- `optimize_campaign`

## First-pass resource URIs

- `sf://org/{org_id}/session/{token}/account/{account_id}/summary`
- `sf://org/{org_id}/session/{token}/account/{account_id}/campaigns`
- `sf://org/{org_id}/session/{token}/account/{account_id}/opportunities`
- `sf://org/{org_id}/session/{token}/case/{case_id}`
- `sf://org/{org_id}/session/{token}/jobs/{job_id}`

## Notes

- This mock intentionally does not call Salesforce.
- The implementation is stable enough for client integration and workflow demos.
- It is not production-hardening or full protocol compliance work.

## LangGraph agent project

The Appendix B multi-agent implementation is in a separate project:

`C:\Users\tiger\project\salesforce-agent`

That project connects to this MCP server over:

`http://127.0.0.1:8000/mcp`

## Browser-based MCP Inspector

`@modelcontextprotocol/inspector` opens a browser UI and can connect to this server.

Stdio mode:

```powershell
npx @modelcontextprotocol/inspector python -m app.server
```

HTTP mode:

1. Start server:
```powershell
python -m app.server --transport streamable-http
```
2. Start inspector and point it at:
`http://127.0.0.1:8000/mcp`
