from __future__ import annotations

from agents.context import WorkflowState
from agents.utils import extract_text, parse_json_object


def make_discovery_node(discovery_agent):
    async def discovery_node(state: WorkflowState) -> WorkflowState:
        result = await discovery_agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Resolve the Salesforce company and object intent in: {state['user_input']}. "
                            "Use resolve_company_context when possible. "
                            "Return JSON with fields: entity_id, primary_object, primary_confidence, "
                            "related_objects, candidates, validation, needs_clarification, clarification_question."
                        ),
                    }
                ]
            }
        )
        text = extract_text(result)
        payload = parse_json_object(text) or {}
        entity_id = payload.get("entity_id", state.get("entity_id"))
        confidence = payload.get("primary_confidence", state.get("entity_confidence"))
        primary_object = payload.get("primary_object")
        related_objects = payload.get("related_objects")
        candidates = payload.get("candidates")
        validation = payload.get("validation")
        clarification_question = payload.get("clarification_question")

        error = state.get("error")
        if payload.get("needs_clarification"):
            error = {
                "code": "ENTITY_DISAMBIGUATION_REQUIRED",
                "message": clarification_question or "Discovery requires clarification before proceeding.",
                "details": {
                    "entity_id": entity_id,
                    "primary_object": primary_object,
                    "candidates": candidates or [],
                },
            }
        elif validation and not validation.get("ok", True):
            error = {
                "code": "VALIDATION_SCHEMA_MISMATCH",
                "message": "Discovery validation failed for the selected Salesforce object.",
                "details": validation,
            }

        return {
            **state,
            "entity_id": entity_id,
            "entity_confidence": confidence,
            "primary_object": primary_object,
            "related_objects": related_objects,
            "discovery_candidates": candidates,
            "discovery_validation": validation,
            "clarification_question": clarification_question,
            "error": error,
        }

    return discovery_node
