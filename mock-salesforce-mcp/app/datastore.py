from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.utility.fixtures import load_json
from app.models import Account, Campaign, Case, Job, Opportunity, Session


class DataStore:
    def __init__(self, fixtures_dir: Path | None = None) -> None:
        base = fixtures_dir or (Path(__file__).resolve().parents[1] / "fixtures")
        self.accounts = {a["id"]: Account(**a) for a in load_json(base, "accounts.json")}
        self.campaigns = {c["id"]: Campaign(**c) for c in load_json(base, "campaigns.json")}
        self.opportunities = {
            o["id"]: Opportunity(**o) for o in load_json(base, "opportunities.json")
        }
        self.cases = {c["id"]: Case(**c) for c in load_json(base, "cases.json")}
        self.sessions = {
            s["token"]: Session(**s) for s in load_json(base, "users.json")
        }

        self.idempotency_store: dict[str, dict[str, Any]] = {}
        self.approval_packets: dict[str, dict[str, Any]] = {}
        self.jobs: dict[str, Job] = {}
        self.degraded_components: list[str] = []

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
