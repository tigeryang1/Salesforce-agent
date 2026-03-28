from __future__ import annotations

import json
from typing import Any

from agents.context import AgentContext, WorkflowState
from agents.utils import extract_text


def make_context_node(
    *,
    client,
    context_agent,
    context_tools: list,
    agent_context: AgentContext,
    session_token: str,
):
    async def context_node(state: WorkflowState) -> WorkflowState:
        if state.get("error"):
            return state

        entity_id = state.get("entity_id") or agent_context.account_scope
        if not entity_id:
            return {
                **state,
                "error": {
                    "code": "ENTITY_DISAMBIGUATION_REQUIRED",
                    "message": "No advertiser ID resolved.",
                },
            }

        summary_uri = (
            f"sf://org/{agent_context.org_id}/session/{session_token}"
            f"/account/{entity_id}/summary"
        )
        campaigns_uri = (
            f"sf://org/{agent_context.org_id}/session/{session_token}"
            f"/account/{entity_id}/campaigns"
        )
        opps_uri = (
            f"sf://org/{agent_context.org_id}/session/{session_token}"
            f"/account/{entity_id}/opportunities"
        )

        resources_payload: dict[str, Any] = {"summary_uri": summary_uri}
        try:
            blobs = await client.get_resources(uris=[summary_uri, campaigns_uri, opps_uri])
            decoded = []
            for blob in blobs:
                if hasattr(blob, "as_string"):
                    decoded.append(blob.as_string())
                elif hasattr(blob, "data"):
                    data = blob.data
                    decoded.append(data.decode("utf-8") if isinstance(data, bytes) else str(data))
                else:
                    decoded.append(str(blob))
            resources_payload["resources"] = decoded
        except Exception as exc:  # noqa: BLE001
            if context_tools:
                tool_result = await context_agent.ainvoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Get advertiser context for {entity_id}.",
                            }
                        ]
                    }
                )
                resources_payload["fallback_context"] = extract_text(tool_result)
            else:
                return {
                    **state,
                    "error": {
                        "code": "SERVICE_DEGRADED",
                        "message": f"Context fetch failed: {exc}",
                    },
                }

        summary_result = await context_agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Summarize this account context for decision making. "
                            "Include stale/degraded flags if present.\n"
                            f"{json.dumps(resources_payload, default=str)}"
                        ),
                    }
                ]
            }
        )
        return {
            **state,
            "account_context": {
                "raw": resources_payload,
                "summary": extract_text(summary_result),
                "primary_object": state.get("primary_object"),
                "related_objects": state.get("related_objects"),
            },
        }

    return context_node
