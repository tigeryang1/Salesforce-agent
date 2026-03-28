from __future__ import annotations

from agents.context import AgentContext, WorkflowState

HIGH_RISK_TOOLS = {"update_campaign_budget", "optimize_campaign"}


def make_compliance_node(agent_context: AgentContext):
    async def compliance_node(state: WorkflowState) -> WorkflowState:
        action = state.get("proposed_action")
        if not action:
            return {
                **state,
                "error": {
                    "code": "VALIDATION_SCHEMA_MISMATCH",
                    "message": "No proposed write action.",
                },
            }

        tool_name = action["tool"]
        if not agent_context.is_tool_approved(tool_name):
            return {
                **state,
                "error": {
                    "code": "PERMISSION_DENIED_SCOPE",
                    "message": f"Tool {tool_name} not approved.",
                },
            }
        if not agent_context.is_write_permitted():
            return {
                **state,
                "error": {
                    "code": "AUTH_REAUTH_REQUIRED",
                    "message": "Session not authenticated for writes.",
                },
            }
        entity_id = state.get("entity_id") or agent_context.account_scope
        if agent_context.account_scope and agent_context.account_scope != entity_id:
            return {
                **state,
                "error": {
                    "code": "PERMISSION_DENIED_SCOPE",
                    "message": "Tenant scope mismatch.",
                },
            }

        needs_human = tool_name in HIGH_RISK_TOOLS or action.get("risk_tier") in {
            "high",
            "critical",
        }
        return {
            **state,
            "compliance_cleared": not needs_human,
            "phase": "needs_human" if needs_human else "approved",
        }

    return compliance_node

