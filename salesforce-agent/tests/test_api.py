from fastapi.testclient import TestClient

from agents.api import create_app


class FakeSystem:
    async def run(self, user_input: str, thread_id: str = "default"):
        return {"phase": "done", "final_response": f"handled: {user_input}", "thread_id": thread_id}

    async def resume_approval(self, decision: str, approval_token: str, thread_id: str = "default"):
        return {
            "phase": "done",
            "approval_token": approval_token,
            "decision": decision,
            "thread_id": thread_id,
        }


class FakeRegistry:
    def __init__(self):
        self.system = FakeSystem()
        self.saved_thread_ids = []

    async def create_or_replace(self, **kwargs):
        return self.system

    async def get(self, thread_id: str):
        return self.system if thread_id == "demo-1" else None

    def save(self, thread_id: str):
        self.saved_thread_ids.append(thread_id)


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-api-token"}


def test_healthz() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_run_endpoint(monkeypatch) -> None:
    app = create_app()
    registry = FakeRegistry()
    app.state.registry = registry
    monkeypatch.setattr("agents.api.ensure_openai_key", lambda model: None)
    monkeypatch.setattr("agents.api.get_api_token", lambda: "test-api-token")
    client = TestClient(app)

    response = client.post(
        "/run",
        headers=auth_headers(),
        json={
            "user_input": "Analyze Nike account",
            "thread_id": "demo-1",
            "mcp_url": "http://127.0.0.1:8000/mcp",
            "model": "openai:gpt-5.3-codex",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "demo-1"
    assert body["result"]["final_response"] == "handled: Analyze Nike account"
    assert registry.saved_thread_ids == ["demo-1"]


def test_resume_approval_endpoint(monkeypatch) -> None:
    app = create_app()
    registry = FakeRegistry()
    app.state.registry = registry
    monkeypatch.setattr("agents.api.get_api_token", lambda: "test-api-token")
    client = TestClient(app)

    response = client.post(
        "/resume-approval",
        headers=auth_headers(),
        json={
            "thread_id": "demo-1",
            "decision": "approve",
            "approval_token": "apv_123",
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["approval_token"] == "apv_123"
    assert registry.saved_thread_ids == ["demo-1"]


def test_resume_approval_not_found(monkeypatch) -> None:
    app = create_app()
    app.state.registry = FakeRegistry()
    monkeypatch.setattr("agents.api.get_api_token", lambda: "test-api-token")
    client = TestClient(app)

    response = client.post(
        "/resume-approval",
        headers=auth_headers(),
        json={
            "thread_id": "missing-thread",
            "decision": "approve",
            "approval_token": "apv_123",
        },
    )
    assert response.status_code == 404


def test_run_endpoint_requires_auth(monkeypatch) -> None:
    app = create_app()
    app.state.registry = FakeRegistry()
    monkeypatch.setattr("agents.api.get_api_token", lambda: "test-api-token")
    monkeypatch.setattr("agents.api.ensure_openai_key", lambda model: None)
    client = TestClient(app)

    response = client.post(
        "/run",
        json={
            "user_input": "Analyze Nike account",
            "thread_id": "demo-1",
            "mcp_url": "http://127.0.0.1:8000/mcp",
            "model": "openai:gpt-5.3-codex",
        },
    )
    assert response.status_code == 401
