from __future__ import annotations

import argparse
import os
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from app.datastore import DataStore
from app.utility.errors import MCPError
from app.operation.discover import DiscoveryService
from app.operation.resources import ResourcesService
from app.operation.tools import ToolsService
from app.prompts import PromptsService

store = DataStore()
tools = ToolsService(store)
discovery = DiscoveryService(store)
resources = ResourcesService(store)
prompts = PromptsService()

DEFAULT_HOST = os.getenv("MCP_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("MCP_PORT", "8000"))
DEFAULT_PATH = os.getenv("MCP_PATH", "/mcp")

mcp = FastMCP(
    "mock-salesforce-mcp",
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
    streamable_http_path=DEFAULT_PATH,
)


def safe_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return {"ok": True, "data": fn(*args, **kwargs)}
    except MCPError as err:
        return {"ok": False, "error": err.to_dict()}


@mcp.tool()
def search_advertiser(token: str, query: str) -> dict[str, Any]:
    return safe_call(discovery.search_advertiser, token, query)


@mcp.tool()
def search_global(token: str, query: str, limit: int = 10) -> dict[str, Any]:
    return safe_call(discovery.search_global, token, query, limit)


@mcp.tool()
def resolve_company_context(token: str, query: str) -> dict[str, Any]:
    return safe_call(discovery.resolve_company_context, token, query)


@mcp.tool()
def create_support_case(
    token: str,
    account_id: str,
    subject: str,
    priority: str,
    description: str = "",
) -> dict[str, Any]:
    return safe_call(
        tools.create_support_case, token, account_id, subject, priority, description or None
    )


@mcp.tool()
def update_campaign_budget(
    token: str,
    campaign_id: str,
    new_budget: float,
    idempotency_key: str,
    review_packet_id: str = "",
    approval_token: str = "",
) -> dict[str, Any]:
    return safe_call(
        tools.update_campaign_budget,
        token,
        campaign_id,
        new_budget,
        idempotency_key,
        review_packet_id or None,
        approval_token or None,
    )


@mcp.tool()
def optimize_campaign(token: str, account_id: str, idempotency_key: str) -> dict[str, Any]:
    return safe_call(tools.optimize_campaign, token, account_id, idempotency_key)


@mcp.resource("sf://org/{org_id}/session/{token}/account/{account_id}/summary")
def account_summary(token: str, org_id: str, account_id: str) -> dict[str, Any]:
    return safe_call(resources.account_summary, token, org_id, account_id)


@mcp.resource("sf://org/{org_id}/session/{token}/account/{account_id}/campaigns")
def account_campaigns(token: str, org_id: str, account_id: str) -> dict[str, Any]:
    return safe_call(resources.account_campaigns, token, org_id, account_id)


@mcp.resource("sf://org/{org_id}/session/{token}/account/{account_id}/opportunities")
def account_opportunities(token: str, org_id: str, account_id: str) -> dict[str, Any]:
    return safe_call(resources.account_opportunities, token, org_id, account_id)


@mcp.resource("sf://org/{org_id}/session/{token}/case/{case_id}")
def case_by_id(token: str, org_id: str, case_id: str) -> dict[str, Any]:
    return safe_call(resources.case_by_id, token, org_id, case_id)


@mcp.resource("sf://org/{org_id}/session/{token}/jobs/{job_id}")
def job_status(token: str, org_id: str, job_id: str) -> dict[str, Any]:
    return safe_call(resources.job_status, token, org_id, job_id)


@mcp.prompt()
def campaign_optimization_review(account_id: str) -> dict[str, Any]:
    return prompts.campaign_optimization_review(account_id)


@mcp.prompt()
def support_case_triage(case_id: str) -> dict[str, Any]:
    return prompts.support_case_triage(case_id)


@mcp.prompt()
def advertiser_health_summary(account_id: str) -> dict[str, Any]:
    return prompts.advertiser_health_summary(account_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run mock Salesforce MCP server")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport mode",
    )
    parser.add_argument(
        "--mount-path",
        default=None,
        help="Optional mount path override for HTTP transports",
    )
    args = parser.parse_args()
    mcp.run(transport=args.transport, mount_path=args.mount_path)
