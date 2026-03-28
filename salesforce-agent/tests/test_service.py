import asyncio
from pathlib import Path

from agents.context import AgentContext
from agents.service import AgentSystemRegistry


class FakeSystem:
    def __init__(self, checkpointer):
        self.checkpointer = checkpointer


def test_registry_persists_and_restores_workflow(monkeypatch) -> None:
    created = []

    async def fake_build_agent_system(
        *,
        session_token: str,
        mcp_url: str,
        model: str,
        agent_context: AgentContext,
        checkpointer=None,
    ):
        cp = checkpointer or {"writes": []}
        created.append(
            {
                "session_token": session_token,
                "mcp_url": mcp_url,
                "model": model,
                "agent_context": agent_context,
                "checkpointer": cp,
            }
        )
        return FakeSystem(cp)

    monkeypatch.setattr("agents.service.build_agent_system", fake_build_agent_system)

    state_dir = Path("test-state")
    state_dir.mkdir(exist_ok=True)
    db_path = state_dir / "agent_state.db"
    if db_path.exists():
        db_path.unlink()
    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=["search_advertiser"],
        account_scope="acct_us_001",
    )

    registry = AgentSystemRegistry(db_path=str(db_path))
    system = asyncio.run(
        registry.create_or_replace(
            thread_id="thread-1",
            session_token="tok_alice_us",
            mcp_url="http://127.0.0.1:8000/mcp",
            model="openai:gpt-5.3-codex",
            agent_context=context,
        )
    )
    system.checkpointer["writes"].append("step-1")
    registry.save("thread-1")

    fresh_registry = AgentSystemRegistry(db_path=str(db_path))
    restored = asyncio.run(fresh_registry.get("thread-1"))

    assert restored is not None
    assert restored.checkpointer["writes"] == ["step-1"]
    assert created[-1]["checkpointer"]["writes"] == ["step-1"]
