from __future__ import annotations

from dataclasses import asdict

from app.approvals import create_review_packet, validate_approval_token
from app.utility.auth import get_session
from app.datastore import DataStore
from app.utility.errors import MCPError, approval_required
from app.jobs import create_optimize_job
from app.policy import (
    enforce_account_scope,
    enforce_region,
    enforce_tool_scope,
    requires_budget_approval,
)


class ToolsService:
    def __init__(self, store: DataStore) -> None:
        self.store = store

    def create_support_case(
        self,
        token: str,
        account_id: str,
        subject: str,
        priority: str,
        description: str | None = None,
    ) -> dict:
        session = get_session(self.store, token)
        enforce_tool_scope(session, "create_support_case")
        enforce_account_scope(session, account_id)
        account = self.store.accounts[account_id]
        enforce_region(session, account.region)

        case = self.store.create_case(account_id=account_id, subject=subject, priority=priority)
        payload = asdict(case)
        if description:
            payload["description"] = description
        return payload

    def update_campaign_budget(
        self,
        token: str,
        campaign_id: str,
        new_budget: float,
        idempotency_key: str,
        review_packet_id: str | None = None,
        approval_token: str | None = None,
    ) -> dict:
        cached = self.store.idempotency_store.get(idempotency_key)
        if cached:
            return cached

        session = get_session(self.store, token)
        enforce_tool_scope(session, "update_campaign_budget")
        campaign = self.store.campaigns.get(campaign_id)
        if not campaign:
            raise MCPError(
                code="VALIDATION_SCHEMA_MISMATCH",
                message=f"Campaign '{campaign_id}' was not found.",
                category="validation",
                layer="tools",
            )

        enforce_account_scope(session, campaign.account_id)
        account = self.store.accounts[campaign.account_id]
        enforce_region(session, account.region)

        if requires_budget_approval(campaign.budget, new_budget):
            if not review_packet_id or not approval_token:
                packet = create_review_packet(
                    self.store,
                    "update_campaign_budget",
                    {
                        "campaign_id": campaign_id,
                        "old_budget": campaign.budget,
                        "new_budget": new_budget,
                    },
                )
                raise approval_required(packet["review_packet_id"], packet["expires_at"])
            validate_approval_token(self.store, review_packet_id, approval_token)

        old_budget = campaign.budget
        campaign.budget = float(new_budget)
        result = {
            "campaign_id": campaign.id,
            "old_budget": old_budget,
            "new_budget": campaign.budget,
            "updated": True,
        }
        self.store.idempotency_store[idempotency_key] = result
        return result

    def optimize_campaign(self, token: str, account_id: str, idempotency_key: str) -> dict:
        session = get_session(self.store, token)
        enforce_tool_scope(session, "optimize_campaign")
        enforce_account_scope(session, account_id)
        account = self.store.accounts[account_id]
        enforce_region(session, account.region)
        return create_optimize_job(self.store, account_id=account_id, idempotency_key=idempotency_key)
