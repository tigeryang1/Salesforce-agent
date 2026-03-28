from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.datastore import DataStore
from app.utility.errors import MCPError


def create_review_packet(store: DataStore, tool_name: str, payload: dict) -> dict:
    review_packet_id = f"pkt_{uuid4().hex[:8]}"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
    approval_token = f"apv_{uuid4().hex[:10]}"
    packet = {
        "review_packet_id": review_packet_id,
        "tool_name": tool_name,
        "status": "pending",
        "expires_at": expires_at,
        "payload": payload,
        "approval_token": approval_token,
    }
    store.approval_packets[review_packet_id] = packet
    return packet


def validate_approval_token(store: DataStore, review_packet_id: str, approval_token: str) -> None:
    packet = store.approval_packets.get(review_packet_id)
    if not packet:
        raise MCPError(
            code="APPROVAL_REQUIRED",
            message="Review packet not found.",
            category="workflow",
            layer="policy",
            retryable=True,
        )
    if packet["approval_token"] != approval_token:
        raise MCPError(
            code="APPROVAL_REQUIRED",
            message="Invalid approval token.",
            category="workflow",
            layer="policy",
            retryable=True,
            recommended_action="Use a valid approval token from review workflow.",
        )
    packet["status"] = "approved"

