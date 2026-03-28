from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from agents.context import AgentContext
from agents.service import (
    AgentSystemRegistry,
    ensure_openai_key,
    ensure_model_key,
    get_api_token,
    serialize_context,
)


class RunRequest(BaseModel):
    user_input: str = Field(..., description="User request text")
    thread_id: str = Field(default="session-1")
    mcp_url: str = Field(default_factory=lambda: os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp"))
    model: str = Field(default_factory=lambda: os.getenv("AGENT_MODEL", os.getenv("OPENAI_MODEL", "gemini:gemini-2.5-flash")))
    session_token: str = Field(default_factory=lambda: os.getenv("SESSION_TOKEN", "tok_alice_us"))
    user_id: str = Field(default_factory=lambda: os.getenv("USER_ID", "alice"))
    org_id: str = Field(default_factory=lambda: os.getenv("ORG_ID", "US"))
    region: str = Field(default_factory=lambda: os.getenv("REGION", "US"))
    account_scope: str | None = Field(default_factory=lambda: os.getenv("ACCOUNT_SCOPE", "acct_us_001"))
    approved_tools: list[str] = Field(
        default_factory=lambda: [
            item.strip()
            for item in os.getenv(
                "APPROVED_TOOLS",
                "search_advertiser,search_global,resolve_company_context,create_support_case,update_campaign_budget,optimize_campaign",
            ).split(",")
            if item.strip()
        ]
    )


class ResumeApprovalRequest(BaseModel):
    thread_id: str
    decision: str = "approve"
    approval_token: str


bearer_scheme = HTTPBearer(auto_error=False)


def require_api_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    expected = get_api_token()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    if credentials.credentials != expected:
        raise HTTPException(status_code=403, detail="Invalid API token.")
    return credentials.credentials


def create_app() -> FastAPI:
    app = FastAPI(title="Salesforce Agent API", version="0.1.0")
    app.state.registry = AgentSystemRegistry()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "gemini_key_configured": bool(os.getenv("GEMINI_API_KEY")),
            "auth_enabled": bool(os.getenv("AGENT_API_TOKEN")),
        }

    @app.post("/run")
    async def run_agent(
        request: RunRequest,
        _: str = Depends(require_api_auth),
    ) -> dict[str, Any]:
        try:
            ensure_openai_key(request.model)
            registry = app.state.registry
            context = AgentContext(
                user_id=request.user_id,
                org_id=request.org_id,
                region=request.region,
                approved_tool_set=request.approved_tools,
                account_scope=request.account_scope,
            )
            system = await registry.create_or_replace(
                thread_id=request.thread_id,
                session_token=request.session_token,
                mcp_url=request.mcp_url,
                model=request.model,
                agent_context=context,
            )
            result = await system.run(request.user_input, thread_id=request.thread_id)
            registry.save(request.thread_id)
            return {
                "thread_id": request.thread_id,
                "agent_context": serialize_context(context),
                "result": result,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/resume-approval")
    async def resume_approval(
        request: ResumeApprovalRequest,
        _: str = Depends(require_api_auth),
    ) -> dict[str, Any]:
        registry = app.state.registry
        system = await registry.get(request.thread_id)
        if system is None:
            raise HTTPException(status_code=404, detail="No workflow found for thread_id.")
        try:
            result = await system.resume_approval(
                decision=request.decision,
                approval_token=request.approval_token,
                thread_id=request.thread_id,
            )
            registry.save(request.thread_id)
            return {"thread_id": request.thread_id, "result": result}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()
