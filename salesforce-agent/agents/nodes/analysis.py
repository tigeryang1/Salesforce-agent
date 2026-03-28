from __future__ import annotations

import json
import uuid

from agents.context import WorkflowState
from agents.utils import extract_text


def make_analysis_node(analysis_agent):
    async def analysis_node(state: WorkflowState) -> WorkflowState:
        if state.get("error"):
            return state

        account_context = state.get("account_context")
        result = await analysis_agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Analyze this Salesforce account context and return recommendations. "
                            "Provide a write proposal only if requested by user.\n"
                            f"User request: {state.get('user_input')}\n"
                            f"Primary object: {state.get('primary_object')}\n"
                            f"Related objects: {state.get('related_objects')}\n"
                            f"Context: {json.dumps(account_context, default=str)}"
                        ),
                    }
                ]
            }
        )
        analysis_text = extract_text(result)
        recommendations = [{"summary": analysis_text, "risk_tier": "medium"}]

        proposed_action = None
        if state.get("intent") == "write":
            proposed_action = {
                "tool": "update_campaign_budget",
                "arguments": {
                    "campaign_id": "camp_us_001",
                    "new_budget": 120000,
                    "idempotency_key": state.get("idempotency_key")
                    or f"idem_{uuid.uuid4().hex[:8]}",
                },
                "risk_tier": "high",
            }

        return {
            **state,
            "recommendations": recommendations,
            "proposed_action": proposed_action,
            "idempotency_key": (proposed_action or {})
            .get("arguments", {})
            .get("idempotency_key", state.get("idempotency_key")),
            "phase": "analyzed",
        }

    return analysis_node
