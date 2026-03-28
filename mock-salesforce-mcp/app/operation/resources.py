from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from app.utility.auth import get_session
from app.datastore import DataStore
from app.utility.errors import MCPError
from app.jobs import read_job
from app.policy import enforce_account_scope, enforce_region


class ResourcesService:
    def __init__(self, store: DataStore) -> None:
        self.store = store

    def metadata(self, account_id: str | None = None) -> dict:
        return {
            "tenant_isolated": account_id is not None,
            "account_scope": account_id,
            "stale": bool(self.store.degraded_components),
            "as_of": datetime.now(timezone.utc).isoformat(),
            "degraded_components": list(self.store.degraded_components),
        }

    def account_summary(self, token: str, org_id: str, account_id: str) -> dict:
        session = get_session(self.store, token)
        enforce_account_scope(session, account_id)
        account = self.store.accounts.get(account_id)
        if not account:
            raise MCPError(
                code="VALIDATION_SCHEMA_MISMATCH",
                message=f"Account '{account_id}' not found.",
                category="validation",
                layer="resources",
            )
        if account.org_id != org_id:
            raise MCPError(
                code="PERMISSION_DENIED_SCOPE",
                message=f"Account '{account_id}' is not in org '{org_id}'.",
                category="authorization",
                layer="resources",
            )
        enforce_region(session, account.region)
        payload = asdict(account)
        payload.update(self.metadata(account_id=account_id))
        return payload

    def account_campaigns(self, token: str, org_id: str, account_id: str) -> dict:
        _ = self.account_summary(token, org_id, account_id)
        campaigns = [asdict(c) for c in self.store.get_account_campaigns(account_id)]
        return {"items": campaigns, **self.metadata(account_id=account_id)}

    def account_opportunities(self, token: str, org_id: str, account_id: str) -> dict:
        _ = self.account_summary(token, org_id, account_id)
        items = [asdict(o) for o in self.store.get_account_opportunities(account_id)]
        return {"items": items, **self.metadata(account_id=account_id)}

    def case_by_id(self, token: str, org_id: str, case_id: str) -> dict:
        session = get_session(self.store, token)
        case = self.store.cases.get(case_id)
        if not case:
            raise MCPError(
                code="VALIDATION_SCHEMA_MISMATCH",
                message=f"Case '{case_id}' not found.",
                category="validation",
                layer="resources",
            )
        enforce_account_scope(session, case.account_id)
        account = self.store.accounts[case.account_id]
        if account.org_id != org_id:
            raise MCPError(
                code="PERMISSION_DENIED_SCOPE",
                message=f"Case '{case_id}' is not in org '{org_id}'.",
                category="authorization",
                layer="resources",
            )
        enforce_region(session, account.region)
        payload = asdict(case)
        payload.update(self.metadata(account_id=case.account_id))
        return payload

    def job_status(self, token: str, org_id: str, job_id: str) -> dict:
        session = get_session(self.store, token)
        if session.org_id != org_id:
            raise MCPError(
                code="PERMISSION_DENIED_SCOPE",
                message=f"Session org '{session.org_id}' cannot read org '{org_id}'.",
                category="authorization",
                layer="resources",
            )
        payload = read_job(self.store, job_id)
        payload.update(self.metadata())
        return payload

