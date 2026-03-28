from __future__ import annotations

from app.datastore import DataStore
from app.utility.errors import MCPError


def create_optimize_job(store: DataStore, account_id: str, idempotency_key: str) -> dict:
    cached = store.idempotency_store.get(idempotency_key)
    if cached:
        return cached

    job = store.create_job(
        {
            "account_id": account_id,
            "idempotency_key": idempotency_key,
            "tool": "optimize_campaign",
        }
    )
    payload = {
        "job_id": job.job_id,
        "status": job.status,
        "accepted_at": job.created_at.isoformat(),
        "estimated_completion": job.created_at.isoformat(),
        "poll_resource": f"sf://org/{{org_id}}/jobs/{job.job_id}",
    }
    store.idempotency_store[idempotency_key] = payload
    return payload


def read_job(store: DataStore, job_id: str) -> dict:
    if job_id not in store.jobs:
        raise MCPError(
            code="SERVICE_UNAVAILABLE",
            message=f"Job '{job_id}' not found.",
            category="dependency",
            layer="jobs",
        )
    job = store.advance_job(job_id)
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "result": job.result,
        "error": job.error,
    }

