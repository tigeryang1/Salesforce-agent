from __future__ import annotations

import json

from agents.context import WorkflowState
from agents.nodes.compliance import HIGH_RISK_TOOLS
from agents.utils import extract_text


def make_execution_node(*, execution_agent, session_token: str):
    async def execution_node(state: WorkflowState) -> WorkflowState:
        action = state.get("proposed_action") or {}
        args = dict(action.get("arguments", {}))
        tool_name = action.get("tool")
        if not tool_name:
            return {
                **state,
                "error": {
                    "code": "VALIDATION_SCHEMA_MISMATCH",
                    "message": "No tool specified.",
                },
            }

        if "idempotency_key" not in args:
            return {
                **state,
                "error": {
                    "code": "VALIDATION_SCHEMA_MISMATCH",
                    "message": "idempotency_key is required.",
                },
            }
        if tool_name in HIGH_RISK_TOOLS:
            if not state.get("approval_token"):
                return {
                    **state,
                    "error": {
                        "code": "APPROVAL_REQUIRED",
                        "message": "approval_token is required for high-risk writes.",
                    },
                }
            args["approval_token"] = state["approval_token"]

        args["token"] = session_token
        execution_prompt = (
            "Execute the approved write now. "
            f"Tool: {tool_name}. Arguments: {json.dumps(args, default=str)}. "
            "Return execution result."
        )
        result = await execution_agent.ainvoke(
            {"messages": [{"role": "user", "content": execution_prompt}]}
        )
        text = extract_text(result)
        return {**state, "recommendations": [{"execution_result": text}], "phase": "finalize"}

    return execution_node

