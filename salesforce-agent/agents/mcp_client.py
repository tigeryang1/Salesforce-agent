from __future__ import annotations

from langchain_mcp_adapters.client import MultiServerMCPClient

from agents.context import AgentContext

READ_TOOLS = {
    "search_advertiser",
    "search_global",
    "resolve_company_context",
    "get_advertiser_context",
}

WRITE_TOOLS = {
    "create_support_case",
    "update_campaign_budget",
    "log_sales_activity",
    "optimize_campaign",
    "resolve_advertiser_issue",
}


async def build_mcp_client(session_token: str, mcp_url: str) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "salesforce": {
                "transport": "streamable_http",
                "url": mcp_url,
                "headers": {"Authorization": f"Bearer {session_token}"},
            }
        }
    )


def scope_tools_for_agent(all_tools: list, agent_type: str, context: AgentContext) -> list:
    allowed = READ_TOOLS if agent_type != "execution" else WRITE_TOOLS
    approved = set(context.approved_tool_set)
    return [t for t in all_tools if t.name in (allowed & approved)]
