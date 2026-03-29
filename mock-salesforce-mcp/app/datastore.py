from __future__ import annotations

import os
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from uuid import uuid4

from app.utility.fixtures import load_json
from app.models import Account, Campaign, Case, Job, Opportunity, Session


class DataStore:
    def __init__(self, fixtures_dir: Path | None = None) -> None:
        base = fixtures_dir or (Path(__file__).resolve().parents[1] / "fixtures")
        self.sessions = {
            s["token"]: Session(**s) for s in load_json(base, "users.json")
        }

        neo4j_requested = self._truthy_env("MOCK_SF_PREFER_NEO4J")
        graph_payload = self._load_graph_payload()
        using_neo4j = graph_payload is not None
        if graph_payload is None:
            graph_payload = self._load_fixture_payload(base)

        self.accounts = {a["id"]: Account(**a) for a in graph_payload["accounts"]}
        self.campaigns = {c["id"]: Campaign(**c) for c in graph_payload["campaigns"]}
        self.opportunities = {o["id"]: Opportunity(**o) for o in graph_payload["opportunities"]}
        self.cases = {c["id"]: Case(**c) for c in graph_payload["cases"]}

        self.idempotency_store: dict[str, dict[str, Any]] = {}
        self.approval_packets: dict[str, dict[str, Any]] = {}
        self.jobs: dict[str, Job] = {}
        self.degraded_components: list[str] = []
        if neo4j_requested and not using_neo4j:
            self.degraded_components.append("neo4j_data")

    @staticmethod
    def _load_fixture_payload(base: Path) -> dict[str, list[dict[str, Any]]]:
        return {
            "accounts": load_json(base, "accounts.json"),
            "campaigns": load_json(base, "campaigns.json"),
            "opportunities": load_json(base, "opportunities.json"),
            "cases": load_json(base, "cases.json"),
        }

    @staticmethod
    def _truthy_env(name: str) -> bool:
        return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}

    def _load_graph_payload(self) -> dict[str, list[dict[str, Any]]] | None:
        if not self._truthy_env("MOCK_SF_PREFER_NEO4J"):
            return None
        try:
            return self._fetch_from_local_api()
        except Exception:  # noqa: BLE001
            return None

    def _request_json(self, path: str) -> dict[str, Any]:
        base_url = os.getenv("MOCK_SF_GRAPH_API_URL", "http://127.0.0.1:8001").rstrip("/")
        target = f"{base_url}{path}"
        try:
            with urlopen(target, timeout=5) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"Graph API request failed for {target}: {exc}") from exc

    def _fetch_from_local_api(self) -> dict[str, list[dict[str, Any]]]:
        accounts_payload = self._request_json("/accounts")
        campaigns_payload = self._request_json("/campaigns")
        opportunities_payload = self._request_json("/opportunities")
        cases_payload = self._request_json("/cases")

        accounts = [
            {
                "id": row["id"],
                "name": row["name"],
                "org_id": "EU" if row.get("region") == "EU" else "US",
                "region": row.get("region", "US"),
                "tier": row.get("tier", "SMB"),
                "risk_score": 0.82
                if row.get("tier") == "Enterprise"
                else 0.58
                if row.get("tier") == "Mid-Market"
                else 0.35,
            }
            for row in accounts_payload.get("accounts", [])
        ]

        campaigns = [
            {
                "id": row["id"],
                "account_id": self._account_id(row),
                "name": row["name"],
                "status": row.get("status", "Planned"),
                "budget": float(row.get("budget") or 0),
                "monthly_spend": float(row.get("budget") or 0) * 0.65,
            }
            for row in campaigns_payload.get("campaigns", [])
            if self._account_id(row)
        ]

        opportunities = [
            {
                "id": row["id"],
                "account_id": self._account_id(row),
                "stage": row.get("stage", "Qualification"),
                "close_date": row.get("close_date", "2026-12-31"),
            }
            for row in opportunities_payload.get("opportunities", [])
            if self._account_id(row)
        ]

        cases = [
            {
                "id": row["id"],
                "account_id": self._account_id(row),
                "subject": row.get("subject", "No subject"),
                "priority": row.get("priority", "Medium"),
                "status": row.get("status", "Open"),
            }
            for row in cases_payload.get("cases", [])
            if self._account_id(row)
        ]

        if not accounts:
            raise ValueError("Graph API is enabled for mock-salesforce-mcp, but no accounts were returned.")

        return {
            "accounts": accounts,
            "campaigns": campaigns,
            "opportunities": opportunities,
            "cases": cases,
        }

    @staticmethod
    def _account_id(row: dict[str, Any]) -> str | None:
        account = row.get("account")
        if isinstance(account, dict) and account.get("id"):
            return str(account["id"])
        if row.get("account_id"):
            return str(row["account_id"])
        return None

    def next_case_id(self) -> str:
        return f"case_{uuid4().hex[:8]}"

    def create_case(self, account_id: str, subject: str, priority: str, status: str = "Open") -> Case:
        case = Case(
            id=self.next_case_id(),
            account_id=account_id,
            subject=subject,
            priority=priority,
            status=status,
        )
        self.cases[case.id] = case
        return case

    def get_account_campaigns(self, account_id: str) -> list[Campaign]:
        return [c for c in self.campaigns.values() if c.account_id == account_id]

    def get_account_opportunities(self, account_id: str) -> list[Opportunity]:
        return [o for o in self.opportunities.values() if o.account_id == account_id]

    def create_job(self, payload: dict[str, Any]) -> Job:
        now = datetime.now(UTC)
        job = Job(
            job_id=f"job_{uuid4().hex[:8]}",
            status="queued",
            created_at=now,
            updated_at=now,
            payload=payload,
            stages=[
                "queued",
                "entity_resolved",
                "security_validated",
                "context_built",
                "write_executed",
                "completed",
            ],
            stage_index=0,
        )
        self.jobs[job.job_id] = job
        return job

    def advance_job(self, job_id: str) -> Job:
        job = self.jobs[job_id]
        if job.stage_index < len(job.stages) - 1:
            job.stage_index += 1
            job.status = job.stages[job.stage_index]
            job.updated_at = datetime.now(UTC)
            if job.status == "completed":
                job.result = {
                    "recommendation": "Shift 12% budget from low CTR ad groups to top performers.",
                    "optimized": True,
                }
        return job

    @staticmethod
    def serialize(obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return obj
