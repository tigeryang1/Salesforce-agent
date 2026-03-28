from __future__ import annotations

from app.utility.errors import MCPError, compliance_region_block, permission_denied_scope
from app.models import Session


def enforce_tool_scope(session: Session, tool_name: str) -> None:
    if tool_name not in session.approved_tool_set:
        raise permission_denied_scope(tool_name)


def enforce_account_scope(session: Session, account_id: str) -> None:
    if account_id not in session.account_scope:
        raise MCPError(
            code="PERMISSION_DENIED_SCOPE",
            message=f"Account '{account_id}' is outside session scope.",
            category="authorization",
            layer="policy",
            recommended_action="Use an account in your assigned scope.",
        )


def enforce_region(session: Session, target_region: str) -> None:
    if session.region != target_region:
        raise compliance_region_block(session.region, target_region)


def requires_budget_approval(old_budget: float, new_budget: float, threshold_pct: float = 20.0) -> bool:
    if old_budget <= 0:
        return True
    pct = ((new_budget - old_budget) / old_budget) * 100.0
    return pct > threshold_pct

