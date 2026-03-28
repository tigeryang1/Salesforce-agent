import asyncio

from agents.context import AgentContext
from agents.nodes.compliance import make_compliance_node


def test_compliance_blocks_unapproved_tool() -> None:
    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=["create_support_case"],
        account_scope="acct_us_001",
    )
    node = make_compliance_node(context)

    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "update_campaign_budget",
                    "arguments": {"campaign_id": "camp_us_001"},
                },
                "entity_id": "acct_us_001",
            }
        )
    )
    assert result["error"]["code"] == "PERMISSION_DENIED_SCOPE"


def test_compliance_blocks_unauthenticated_write() -> None:
    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=["update_campaign_budget"],
        account_scope="acct_us_001",
        auth_state="reauth_required",
    )
    node = make_compliance_node(context)

    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "update_campaign_budget",
                    "arguments": {"campaign_id": "camp_us_001"},
                    "risk_tier": "high",
                },
                "entity_id": "acct_us_001",
            }
        )
    )
    assert result["error"]["code"] == "AUTH_REAUTH_REQUIRED"


def test_compliance_requires_human_for_high_risk() -> None:
    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=["update_campaign_budget"],
        account_scope="acct_us_001",
    )
    node = make_compliance_node(context)

    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "update_campaign_budget",
                    "arguments": {"campaign_id": "camp_us_001"},
                    "risk_tier": "high",
                },
                "entity_id": "acct_us_001",
            }
        )
    )
    assert result["compliance_cleared"] is False
    assert result["phase"] == "needs_human"


def test_compliance_allows_low_risk_write() -> None:
    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=["create_support_case"],
        account_scope="acct_us_001",
    )
    node = make_compliance_node(context)

    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "create_support_case",
                    "arguments": {"account_id": "acct_us_001"},
                    "risk_tier": "medium",
                },
                "entity_id": "acct_us_001",
            }
        )
    )
    assert result["compliance_cleared"] is True
    assert result["phase"] == "approved"

