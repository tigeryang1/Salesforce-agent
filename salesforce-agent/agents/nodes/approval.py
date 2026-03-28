from __future__ import annotations

from langgraph.types import interrupt

from agents.context import WorkflowState


async def human_approval_node(state: WorkflowState) -> WorkflowState:
    proposed = state.get("proposed_action") or {}
    review_packet = {
        "request_id": state.get("idempotency_key"),
        "escalation_trigger": "high_risk_write",
        "risk_level": proposed.get("risk_tier", "high").upper(),
        "agent": "ExecutionAgent",
        "account_scope": state["agent_context"].account_scope,
        "proposed_action": proposed,
        "reviewer_actions": ["approve", "reject", "modify", "request_info"],
    }
    approval_response = interrupt(review_packet)
    if approval_response.get("decision") != "approve":
        return {
            **state,
            "error": {
                "code": "APPROVAL_REJECTED",
                "message": "Human reviewer rejected request.",
            },
        }
    return {
        **state,
        "approval_token": approval_response.get("approval_token"),
        "compliance_cleared": True,
    }

