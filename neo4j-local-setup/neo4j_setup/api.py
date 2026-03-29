from __future__ import annotations

from fastapi import FastAPI, HTTPException

from neo4j_setup.config import get_settings
from neo4j_setup.db import build_driver
from neo4j_setup.repository import SalesforceGraphRepository


def create_app() -> FastAPI:
    app = FastAPI(title="Neo4j Salesforce Mock API", version="0.1.0")

    @app.on_event("startup")
    def startup() -> None:
        settings = get_settings()
        driver = build_driver(settings)
        app.state.repo = SalesforceGraphRepository(driver, settings.database)

    @app.on_event("shutdown")
    def shutdown() -> None:
        repo = getattr(app.state, "repo", None)
        if repo is not None:
            repo.close()

    @app.get("/healthz")
    def healthz() -> dict:
        return app.state.repo.health()

    @app.get("/accounts")
    def accounts() -> dict:
        return {"accounts": app.state.repo.get_accounts()}

    @app.get("/accounts/{account_id}")
    def account_by_id(account_id: str) -> dict:
        account = app.state.repo.get_account(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found.")
        return {"account": account}

    @app.get("/accounts/{account_id}/contacts")
    def account_contacts(account_id: str) -> dict:
        return {"contacts": app.state.repo.get_account_contacts(account_id)}

    @app.get("/accounts/{account_id}/opportunities")
    def account_opportunities(account_id: str) -> dict:
        return {"opportunities": app.state.repo.get_account_opportunities(account_id)}

    @app.get("/accounts/{account_id}/cases")
    def account_cases(account_id: str) -> dict:
        return {"cases": app.state.repo.get_account_cases(account_id)}

    @app.get("/opportunities")
    def opportunities() -> dict:
        return {"opportunities": app.state.repo.get_opportunities()}

    @app.get("/cases")
    def cases() -> dict:
        return {"cases": app.state.repo.get_cases()}

    @app.get("/campaigns")
    def campaigns() -> dict:
        return {"campaigns": app.state.repo.get_campaigns()}

    return app


app = create_app()

