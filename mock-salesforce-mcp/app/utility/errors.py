from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class MCPError(Exception):
    code: str
    message: str
    category: str
    layer: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    recommended_action: str | None = None
    correlation_id: str = field(default_factory=lambda: f"req_{uuid4().hex[:10]}")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "category": self.category,
            "layer": self.layer,
            "details": self.details,
            "correlation_id": self.correlation_id,
        }
        if self.recommended_action:
            payload["recommended_action"] = self.recommended_action
        return payload


def auth_expired() -> MCPError:
    return MCPError(
        code="AUTH_SESSION_EXPIRED",
        message="Session is expired or missing.",
        category="auth",
        layer="auth",
        recommended_action="Re-authenticate and retry.",
    )


def permission_denied_scope(tool_name: str) -> MCPError:
    return MCPError(
        code="PERMISSION_DENIED_SCOPE",
        message=f"Tool '{tool_name}' is not in approved_tool_set.",
        category="authorization",
        layer="policy",
        recommended_action="Use an approved tool or request access.",
    )


def compliance_region_block(session_region: str, target_region: str) -> MCPError:
    return MCPError(
        code="COMPLIANCE_REGION_BLOCK",
        message=(
            f"Session region '{session_region}' cannot access target region "
            f"'{target_region}'."
        ),
        category="compliance",
        layer="policy",
        recommended_action="Use a session bound to the target region.",
    )


def entity_disambiguation_required(query: str, candidates: list[dict[str, Any]]) -> MCPError:
    return MCPError(
        code="ENTITY_DISAMBIGUATION_REQUIRED",
        message=f"Multiple advertisers matched '{query}'.",
        category="validation",
        layer="intent",
        retryable=True,
        details={"candidates": candidates},
        recommended_action="Select a candidate id and retry.",
    )


def approval_required(review_packet_id: str, expires_at: str) -> MCPError:
    return MCPError(
        code="APPROVAL_REQUIRED",
        message="Human approval is required before this write can execute.",
        category="workflow",
        layer="policy",
        retryable=True,
        details={"review_packet_id": review_packet_id, "expires_at": expires_at},
        recommended_action="Present review packet and retry with approval_token.",
    )

