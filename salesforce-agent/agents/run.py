from __future__ import annotations

import argparse
import asyncio
import json
import os

import httpx

from agents.context import AgentContext
from agents.system import build_agent_system


async def ensure_mcp_reachable(mcp_url: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(mcp_url)
    except httpx.HTTPError as exc:
        raise SystemExit(
            f"MCP server not reachable at {mcp_url}. "
            "Start the mock Salesforce MCP server first and retry. "
            f"Underlying error: {exc}"
        ) from exc


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Run Salesforce MCP LangGraph agent system")
    parser.add_argument("--mcp-url", default=os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp"))
    parser.add_argument("--model", default=os.getenv("AGENT_MODEL", os.getenv("OPENAI_MODEL", "gemini:gemini-2.5-flash")))
    parser.add_argument("--session-token", default=os.getenv("SESSION_TOKEN", "tok_alice_us"))
    parser.add_argument("--user-id", default=os.getenv("USER_ID", "alice"))
    parser.add_argument("--org-id", default=os.getenv("ORG_ID", "US"))
    parser.add_argument("--region", default=os.getenv("REGION", "US"))
    parser.add_argument("--account-scope", default=os.getenv("ACCOUNT_SCOPE", "acct_us_001"))
    parser.add_argument(
        "--approved-tools",
        default=os.getenv(
            "APPROVED_TOOLS",
            "search_advertiser,create_support_case,update_campaign_budget,optimize_campaign",
        ),
    )
    parser.add_argument("--thread-id", default=os.getenv("THREAD_ID", "session-1"))
    parser.add_argument(
        "--input",
        required=True,
        help="User request text",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="If interrupted for approval, auto-resume with approval token",
    )
    args = parser.parse_args()

    if args.model.startswith("gemini:") and not os.getenv("GEMINI_API_KEY"):
        raise SystemExit(
            "GEMINI_API_KEY is required when using a Gemini model. "
            "Set it in the environment and retry."
        )

    if args.model.startswith("openai:") and not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is required when using an OpenAI model. "
            "Set it in the environment and retry."
        )

    await ensure_mcp_reachable(args.mcp_url)

    context = AgentContext(
        user_id=args.user_id,
        org_id=args.org_id,
        region=args.region,
        approved_tool_set=[s.strip() for s in args.approved_tools.split(",") if s.strip()],
        account_scope=args.account_scope,
    )

    system = await build_agent_system(
        session_token=args.session_token,
        mcp_url=args.mcp_url,
        model=args.model,
        agent_context=context,
    )

    result = await system.run(user_input=args.input, thread_id=args.thread_id)
    print(json.dumps(result, indent=2, default=str))

    interrupt_payload = result.get("__interrupt__")
    if interrupt_payload and args.approve:
        resumed = await system.resume_approval(
            decision="approve",
            approval_token="apv_auto_approved",
            thread_id=args.thread_id,
        )
        print(json.dumps(resumed, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(_main())
