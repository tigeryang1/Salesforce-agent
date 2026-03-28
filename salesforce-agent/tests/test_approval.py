import asyncio

from agents.context import AgentContext
from agents.nodes import approval as approval_module


def test_human_approval_node_rejects(monkeypatch) -> None:
    monkeypatch.setattr(
        approval_module,
        "interrupt",
        lambda review_packet: {"decision": "reject"},
    )

    state = {
        "idempotency_key": "idem_123",
        "agent_context": AgentContext(
            user_id="alice",
            org_id="US",
            region="US",
            approved_tool_set=["update_campaign_budget"],
            account_scope="acct_us_001",
        ),
        "proposed_action": {
            "tool": "update_campaign_budget",
            "risk_tier": "high",
            "arguments": {"campaign_id": "camp_us_001"},
        },
    }

    result = asyncio.run(approval_module.human_approval_node(state))
    assert result["error"]["code"] == "APPROVAL_REJECTED"


def test_human_approval_node_approves(monkeypatch) -> None:
    monkeypatch.setattr(
        approval_module,
        "interrupt",
        lambda review_packet: {"decision": "approve", "approval_token": "apv_123"},
    )

    state = {
        "idempotency_key": "idem_123",
        "agent_context": AgentContext(
            user_id="alice",
            org_id="US",
            region="US",
            approved_tool_set=["update_campaign_budget"],
            account_scope="acct_us_001",
        ),
        "proposed_action": {
            "tool": "update_campaign_budget",
            "risk_tier": "high",
            "arguments": {"campaign_id": "camp_us_001"},
        },
    }

    result = asyncio.run(approval_module.human_approval_node(state))
    assert result["approval_token"] == "apv_123"
    assert result["compliance_cleared"] is True

