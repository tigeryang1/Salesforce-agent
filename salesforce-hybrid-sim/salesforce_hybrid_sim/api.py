from __future__ import annotations

from fastapi import FastAPI, HTTPException

from salesforce_hybrid_sim.config import get_settings
from salesforce_hybrid_sim.neo4j_projector import Neo4jProjector
from salesforce_hybrid_sim.seed_data import SEED_DATA
from salesforce_hybrid_sim.sqlite_store import SQLiteStore


def _account_ref(row: dict) -> dict:
    return {
        "id": row["account_id"],
        "name": row.get("account_name"),
    }


def _owner_ref(row: dict) -> dict | None:
    owner_id = row.get("owner_user_id")
    if not owner_id:
        return None
    return {
        "id": owner_id,
        "name": row.get("owner_name"),
        "role": row.get("owner_role"),
    }


def _format_opportunity(row: dict) -> dict:
    payload = dict(row)
    payload["account"] = _account_ref(row)
    payload["owner"] = _owner_ref(row)
    return payload


def _format_case(row: dict) -> dict:
    payload = dict(row)
    payload["account"] = _account_ref(row)
    payload["owner"] = _owner_ref(row)
    return payload


def _format_campaign(row: dict) -> dict:
    payload = dict(row)
    payload["account"] = _account_ref(row)
    return payload


def create_app() -> FastAPI:
    app = FastAPI(title="Salesforce Hybrid Sim", version="0.1.0")
    settings = get_settings()
    store = SQLiteStore(settings.sqlite_path)

    @app.get("/healthz")
    def healthz() -> dict:
        status = store.health()
        return {"ok": True, "sqlite": status["sqlite"], "sqlite_path": str(settings.sqlite_path), "neo4j_uri": settings.neo4j_uri}

    @app.post("/admin/init-db")
    def init_db() -> dict:
        store.init_schema()
        return {"initialized": True}

    @app.post("/admin/seed")
    def seed() -> dict:
        store.seed(SEED_DATA)
        return {"seeded": True, "accounts": len(SEED_DATA["accounts"])}

    @app.post("/admin/sync-graph")
    def sync_graph() -> dict:
        projector = Neo4jProjector(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password, settings.neo4j_database)
        return {"synced": True, "counts": projector.sync_all(store.projection_bundle())}

    @app.get("/accounts")
    def accounts() -> dict:
        return {"accounts": store.get_accounts()}

    @app.get("/accounts/{account_id}")
    def account(account_id: str) -> dict:
        payload = store.get_account(account_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Account not found.")
        return {"account": payload}

    @app.get("/opportunities")
    def opportunities() -> dict:
        return {"opportunities": [_format_opportunity(row) for row in store.get_opportunities()]}

    @app.get("/cases")
    def cases() -> dict:
        return {"cases": [_format_case(row) for row in store.get_cases()]}

    @app.get("/campaigns")
    def campaigns() -> dict:
        return {"campaigns": [_format_campaign(row) for row in store.get_campaigns()]}

    return app


app = create_app()
