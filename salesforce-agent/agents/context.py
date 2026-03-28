from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict


@dataclass
class AgentContext:
    user_id: str
    org_id: str
    region: str
    approved_tool_set: list[str]
    account_scope: str | None = None
    risk_tier: str = "standard"
    auth_state: str = "authenticated"

    def is_write_permitted(self) -> bool:
        return self.auth_state == "authenticated"

    def is_tool_approved(self, tool_name: str) -> bool:
        return tool_name in self.approved_tool_set


class WorkflowState(TypedDict, total=False):
    user_input: str
    intent: str
    # Session binding
    agent_context: AgentContext
    # Resolved data
    entity_id: str | None
    entity_confidence: float | None
    primary_object: str | None
    related_objects: list[str] | None
    discovery_candidates: list[dict[str, Any]] | None
    discovery_validation: dict[str, Any] | None
    clarification_question: str | None
    account_context: dict[str, Any] | None
    recommendations: list[dict[str, Any]] | None
    # Write execution
    proposed_action: dict[str, Any] | None
    idempotency_key: str | None
    approval_token: str | None
    compliance_cleared: bool
    # Control
    phase: str
    # Output
    final_response: str | None
    error: dict[str, Any] | None
