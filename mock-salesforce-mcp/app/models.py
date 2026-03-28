from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Session:
    token: str
    session_id: str
    principal_id: str
    org_id: str
    region: str
    auth_state: str
    approved_tool_set: list[str]
    account_scope: list[str]


@dataclass
class Account:
    id: str
    name: str
    org_id: str
    region: str
    tier: str
    risk_score: float


@dataclass
class Campaign:
    id: str
    account_id: str
    name: str
    status: str
    budget: float
    monthly_spend: float


@dataclass
class Opportunity:
    id: str
    account_id: str
    stage: str
    close_date: str


@dataclass
class Case:
    id: str
    account_id: str
    subject: str
    priority: str
    status: str


@dataclass
class ApprovalPacket:
    review_packet_id: str
    tool_name: str
    status: str
    expires_at: str
    payload: dict[str, Any]
    approval_token: str | None = None


@dataclass
class Job:
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    stages: list[str] = field(default_factory=list)
    stage_index: int = 0

