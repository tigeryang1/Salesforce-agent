from __future__ import annotations

import json

from agents.context import WorkflowState
from agents.utils import classify_intent, extract_text


def make_supervisor_node(supervisor_agent):
    async def supervisor_node(state: WorkflowState) -> WorkflowState:
        phase = state.get("phase", "route")
        if phase == "route":
            intent = classify_intent(state["user_input"])
            return {**state, "intent": intent}

        if state.get("error"):
            return {
                **state,
                "final_response": f"Request failed: {json.dumps(state['error'])}",
                "phase": "done",
            }

        summary_payload = {
            "entity_id": state.get("entity_id"),
            "entity_confidence": state.get("entity_confidence"),
            "primary_object": state.get("primary_object"),
            "related_objects": state.get("related_objects"),
            "discovery_candidates": state.get("discovery_candidates"),
            "clarification_question": state.get("clarification_question"),
            "account_context": state.get("account_context"),
            "recommendations": state.get("recommendations"),
            "proposed_action": state.get("proposed_action"),
        }
        result = await supervisor_agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"User request: {state.get('user_input')}\n"
                            f"Workflow outputs: {json.dumps(summary_payload, default=str)}\n"
                            "Produce a concise final response for the user."
                        ),
                    }
                ]
            }
        )
        return {**state, "final_response": extract_text(result), "phase": "done"}

    return supervisor_node
